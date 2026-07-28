import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
