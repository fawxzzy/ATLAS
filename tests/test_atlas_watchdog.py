import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from ops.atlas.atlas_runtime import AtlasRuntime
from ops.atlas.atlas_watchdog import AtlasWatchdog


class FakeClock:
    def __init__(self, now=1_800.0):
        self.now = now

    def __call__(self):
        return self.now


class AtlasWatchdogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.runtime = AtlasRuntime(Path(self.tmp.name) / "atlasd.sqlite")
        self.clock = FakeClock()
        self.watchdog = AtlasWatchdog(self.runtime, clock=self.clock)

    def tearDown(self):
        self.runtime.close()
        self.tmp.cleanup()

    def tick(self, *, event=False):
        return self.watchdog.tick(event_observed=event)

    def test_healthy_idle_is_observed_without_receipt(self):
        tick = self.tick(event=True)
        self.assertTrue(tick.checked)
        self.assertEqual(tick.decisions, ())
        self.assertEqual(self.runtime.db.execute("SELECT COUNT(*) FROM events").fetchone()[0], 0)

    def test_stranded_ready_emits_one_idempotent_wake(self):
        self.runtime.enqueue("ready", lane="atlas", scope="repo:atlas")
        first = self.tick(event=True)
        second = self.tick(event=True)
        self.assertEqual(first.decisions[0].action, "WAKE_NEEDED")
        self.assertTrue(first.decisions[0].receipt_recorded)
        self.assertFalse(second.decisions[0].receipt_recorded)
        self.assertEqual(
            self.runtime.db.execute("SELECT COUNT(*) FROM events WHERE kind='WATCHDOG'").fetchone()[0], 1
        )

    def test_expired_lease_is_reconciled_to_hold(self):
        self.runtime.enqueue("expired", lane="atlas", scope="repo:atlas")
        lease = self.runtime.claim(worker_id="worker", run_id="run", lease_seconds=60)
        self.assertIsNotNone(lease)
        self.clock.now = lease.expires_at + 1
        tick = self.tick(event=True)
        self.assertEqual(tick.paused_runtime_tasks, ("expired",))
        self.assertEqual(tick.decisions[0].reason, "PAUSED_RUNTIME_REQUIRES_RESUME")

    def test_missing_dependency_remains_hold(self):
        self.runtime.enqueue("blocked", lane="atlas", scope="repo:atlas", depends_on=["missing"])
        tick = self.tick(event=True)
        self.assertEqual(tick.decisions[0].reason, "UNRESOLVED_DEPENDENCY")
        self.assertEqual(tick.decisions[0].action, "HOLD")

    def test_manual_unknown_provider_and_production_gates_do_not_wake(self):
        self.runtime.enqueue("manual", lane="atlas", scope="repo:manual")
        lease = self.runtime.claim(worker_id="worker", run_id="manual")
        self.runtime.complete(task_id="manual", worker_id="worker", run_id="manual", state="WAITING_MANUAL")
        self.runtime.enqueue("provider", lane="atlas", scope="provider:supabase")
        self.runtime.enqueue("production", lane="atlas", scope="production:vercel")
        self.runtime.enqueue("unknown", lane="atlas", scope="repo:unknown")
        self.runtime.db.execute("UPDATE tasks SET state='UNKNOWN' WHERE task_id='unknown'")
        decisions = {item.task_id: item for item in self.tick(event=True).decisions}
        self.assertEqual(decisions["manual"].reason, "MANUAL_DECISION_REQUIRED")
        self.assertEqual(decisions["provider"].reason, "PROVIDER_OR_PRODUCTION_GATE")
        self.assertEqual(decisions["production"].reason, "PROVIDER_OR_PRODUCTION_GATE")
        self.assertEqual(decisions["unknown"].reason, "UNKNOWN_STATE")
        self.assertTrue(all(item.action == "HOLD" for item in decisions.values()))

    def test_fallback_cooldown_and_repeated_reconciliation_are_deterministic(self):
        self.runtime.enqueue("ready", lane="atlas", scope="repo:atlas")
        first = self.tick(event=False)
        skipped = self.tick(event=False)
        self.assertTrue(first.checked)
        self.assertFalse(skipped.checked)
        self.clock.now += 1_800
        fallback = self.tick(event=False)
        self.assertTrue(fallback.checked)
        self.assertTrue(fallback.decisions[0].receipt_recorded)
        self.assertEqual(first.decisions[0].reason, fallback.decisions[0].reason)

    def test_valid_active_scope_lease_prevents_wake(self):
        self.runtime.enqueue("running", lane="atlas", scope="repo:atlas")
        self.runtime.claim(worker_id="worker", run_id="active", lease_seconds=60)
        self.runtime.enqueue("queued", lane="atlas", scope="repo:atlas")
        decision = self.tick(event=True).decisions[0]
        self.assertEqual(decision.task_id, "queued")
        self.assertEqual(decision.reason, "VALID_ACTIVE_LEASE")

    def test_reconcile_failure_abandons_reservation_for_immediate_retry(self):
        self.runtime.enqueue("ready", lane="atlas", scope="repo:atlas")
        with patch.object(self.runtime, "reconcile", side_effect=RuntimeError("host loss")):
            with self.assertRaisesRegex(RuntimeError, "host loss"):
                self.tick(event=False)
        self.assertEqual(
            self.runtime.db.execute(
                "SELECT state FROM watchdog_runs ORDER BY reserved_at"
            ).fetchone()["state"],
            "ABANDONED",
        )
        retry = self.tick(event=False)
        self.assertTrue(retry.checked)
        self.assertEqual(retry.decisions[0].action, "WAKE_NEEDED")

    def test_receipt_failure_abandons_and_retry_deduplicates_completed_work(self):
        self.runtime.enqueue("first", lane="atlas", scope="repo:first", priority=10)
        self.runtime.enqueue("second", lane="atlas", scope="repo:second")
        original = self.runtime.record_watchdog_receipt
        calls = 0

        def fail_after_one_receipt(**kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("receipt failure")
            return original(**kwargs)

        with patch.object(
            self.runtime,
            "record_watchdog_receipt",
            side_effect=fail_after_one_receipt,
        ):
            with self.assertRaisesRegex(RuntimeError, "receipt failure"):
                self.tick(event=False)
        self.assertEqual(
            self.runtime.db.execute(
                "SELECT state FROM watchdog_runs ORDER BY reserved_at"
            ).fetchone()["state"],
            "ABANDONED",
        )
        with patch.object(
            self.runtime,
            "record_watchdog_receipt",
            wraps=original,
        ) as recorder:
            retry = self.tick(event=False)
        self.assertTrue(retry.checked)
        self.assertEqual(recorder.call_count, 2)
        self.assertFalse(retry.decisions[0].receipt_recorded)
        self.assertTrue(retry.decisions[1].receipt_recorded)

    def test_two_watchdogs_share_one_successful_fallback_window(self):
        database = Path(self.tmp.name) / "concurrent.sqlite"
        AtlasRuntime(database).close()
        barrier = threading.Barrier(2)

        def tick():
            runtime = AtlasRuntime(database)
            try:
                barrier.wait()
                return AtlasWatchdog(
                    runtime,
                    clock=FakeClock(),
                    fallback_seconds=1_800,
                ).tick(event_observed=False)
            finally:
                runtime.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            ticks = list(pool.map(lambda _: tick(), range(2)))
        self.assertEqual(sum(item.checked for item in ticks), 1)
        readback = AtlasRuntime(database)
        try:
            self.assertEqual(
                readback.db.execute(
                    "SELECT COUNT(*) FROM watchdog_runs WHERE state='SUCCEEDED'"
                ).fetchone()[0],
                1,
            )
        finally:
            readback.close()

    def test_non_default_heartbeat_timeout_changes_reconciliation(self):
        self.runtime.enqueue("running", lane="atlas", scope="repo:atlas")
        self.runtime.claim(worker_id="worker", run_id="run", lease_seconds=600)
        self.runtime.db.execute(
            "UPDATE leases SET heartbeat_at=?, expires_at=? WHERE task_id='running'",
            (self.clock.now - 11, self.clock.now + 100),
        )
        tick = AtlasWatchdog(
            self.runtime,
            clock=self.clock,
            heartbeat_timeout=10,
        ).tick(event_observed=True)
        self.assertEqual(tick.paused_runtime_tasks, ("running",))
        self.assertEqual(self.runtime.get("running").state, "PAUSED_RUNTIME")

    def test_default_heartbeat_timeout_remains_stable(self):
        self.runtime.enqueue("running", lane="atlas", scope="repo:atlas")
        self.runtime.claim(worker_id="worker", run_id="run", lease_seconds=600)
        self.runtime.db.execute(
            "UPDATE leases SET heartbeat_at=?, expires_at=? WHERE task_id='running'",
            (self.clock.now - 60, self.clock.now + 100),
        )
        tick = self.tick(event=True)
        self.assertEqual(tick.paused_runtime_tasks, ())
        self.assertEqual(self.runtime.get("running").state, "RUNNING")

    def test_paused_usage_is_observe_only_with_or_without_lease(self):
        self.runtime.enqueue("fresh", lane="atlas", scope="repo:fresh")
        self.runtime.enqueue("stale", lane="atlas", scope="repo:stale")
        self.runtime.enqueue(
            "leased", lane="atlas", scope="repo:leased", priority=10
        )
        self.runtime.claim(worker_id="worker", run_id="lease", lease_seconds=600)
        self.runtime.db.execute(
            "UPDATE tasks SET state='PAUSED_USAGE', updated_at=? "
            "WHERE task_id IN ('fresh','leased')",
            (self.clock.now,),
        )
        self.runtime.db.execute(
            "UPDATE tasks SET state='PAUSED_USAGE', updated_at=? WHERE task_id='stale'",
            (self.clock.now - 86_400,),
        )
        decisions = {item.task_id: item for item in self.tick(event=True).decisions}
        self.assertEqual(decisions["fresh"].reason, "PAUSED_USAGE_OBSERVE_ONLY")
        self.assertEqual(decisions["stale"].reason, "PAUSED_USAGE_OBSERVE_ONLY")
        self.assertEqual(decisions["leased"].reason, "VALID_ACTIVE_LEASE")
        self.assertTrue(all(item.action == "HOLD" for item in decisions.values()))
        self.assertEqual(
            {task_id: self.runtime.get(task_id).state for task_id in decisions},
            {task_id: "PAUSED_USAGE" for task_id in decisions},
        )

    def test_stale_observation_records_only_and_cannot_mutate_or_release(self):
        self.runtime.enqueue("stale", lane="atlas", scope="repo:stale")
        stale_task, has_valid_lease = self.runtime.watchdog_tasks(now=self.clock.now)[0]
        self.assertFalse(has_valid_lease)
        lease = self.runtime.claim(worker_id="worker", run_id="run", lease_seconds=600)
        before = self.runtime.db.execute(
            "SELECT worker_id,run_id,expires_at FROM leases WHERE task_id='stale'"
        ).fetchone()

        decision = self.watchdog._record_decision(
            stale_task,
            has_valid_lease,
            self.clock.now,
        )

        after = self.runtime.db.execute(
            "SELECT worker_id,run_id,expires_at FROM leases WHERE task_id='stale'"
        ).fetchone()
        event = self.runtime.db.execute(
            "SELECT payload FROM events WHERE kind='WATCHDOG'"
        ).fetchone()
        self.assertEqual(decision.reason, "STRANDED_READY_NO_VALID_LEASE")
        self.assertEqual(self.runtime.get("stale").state, "RUNNING")
        self.assertEqual(tuple(before), tuple(after))
        self.assertEqual(after["run_id"], lease.run_id)
        self.assertEqual(json.loads(event["payload"])["execution"], "NOT_STARTED")


if __name__ == "__main__":
    unittest.main()
