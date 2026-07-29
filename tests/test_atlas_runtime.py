import sqlite3
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from ops.atlas.atlas_runtime import AtlasRuntime, WatchdogReservation


class AtlasRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.database = Path(self.tmp.name) / "atlas.db"
        self.runtime = AtlasRuntime(self.database)

    def tearDown(self):
        self.runtime.close()
        self.tmp.cleanup()

    def test_wal_and_scoped_claim(self):
        self.runtime.enqueue("a", lane="supabase", scope="repo:platform", priority=10)
        self.runtime.enqueue("b", lane="fitness", scope="repo:fitness", priority=9)
        first = self.runtime.claim(worker_id="w1", run_id="r1")
        second = self.runtime.claim(worker_id="w2", run_id="r2")
        self.assertEqual(first.task_id, "a")
        self.assertEqual(second.task_id, "b")

    def test_completion_atomically_queues_successor_and_is_idempotent(self):
        self.runtime.enqueue("next", lane="lane", scope="repo:x", depends_on=["first"])
        self.runtime.enqueue("first", lane="lane", scope="repo:y", successor_ids=["next"])
        lease = self.runtime.claim(worker_id="w", run_id="r")
        self.assertEqual(lease.task_id, "first")
        successors = self.runtime.complete(task_id=lease.task_id, worker_id="w", run_id="r", receipt={"event_id": "evt-1"})
        self.assertEqual(successors, ("next",))
        self.assertEqual(self.runtime.get("next").state, "QUEUED")
        self.assertEqual(
            self.runtime.complete(task_id=lease.task_id, worker_id="w", run_id="r", receipt={"event_id": "evt-1"}),
            ("next",),
        )

    def test_recovery_dispositions_do_not_dispatch_work(self):
        self.runtime.enqueue("ready", lane="lane", scope="repo:ready")
        self.runtime.enqueue("paused", lane="lane", scope="repo:paused")
        lease = self.runtime.claim(worker_id="w", run_id="r", lease_seconds=0.001)
        self.assertEqual(lease.task_id, "ready")
        time.sleep(0.01)
        self.runtime.reconcile()
        dispositions = {item.task_id: item.disposition for item in self.runtime.recovery_dispositions()}
        self.assertEqual(dispositions["ready"], "PAUSED_RUNTIME_REQUIRES_RESUME")
        self.assertEqual(dispositions["paused"], "READY_NOT_DISPATCHED")

    def test_stale_running_becomes_paused_runtime(self):
        self.runtime.enqueue("a", lane="lane", scope="repo:x")
        lease = self.runtime.claim(worker_id="w", run_id="r", lease_seconds=1)
        paused = self.runtime.reconcile(now=lease.expires_at + 1)
        self.assertEqual(paused, ["a"])
        self.assertEqual(self.runtime.get("a").state, "PAUSED_RUNTIME")

    def test_conflicting_receipt_event_fails_closed(self):
        self.runtime.enqueue("a", lane="lane", scope="repo:x")
        lease = self.runtime.claim(worker_id="w", run_id="r")
        self.runtime.complete(task_id="a", worker_id="w", run_id="r", receipt={"event_id": "same"})
        self.runtime.enqueue("b", lane="lane", scope="repo:y")
        other = self.runtime.claim(worker_id="w2", run_id="r2")
        with self.assertRaises(ValueError):
            self.runtime.complete(task_id=other.task_id, worker_id="w2", run_id="r2", receipt={"event_id": "same", "different": True})

    def test_conflicting_enqueue_event_fails_closed_on_topology_drift(self):
        self.runtime.enqueue(
            "a", lane="lane", scope="repo:x", priority=1, successor_ids=["s1"], event_id="enqueue-a"
        )
        with self.assertRaises(ValueError):
            self.runtime.enqueue(
                "a", lane="lane", scope="repo:x", priority=999, successor_ids=["s2"], event_id="enqueue-a"
            )

    def test_scope_conflict_does_not_starve_independent_task(self):
        self.runtime.enqueue("high1", lane="lane", scope="repo:x", priority=10)
        first = self.runtime.claim(worker_id="w1", run_id="r1")
        self.runtime.enqueue("high2", lane="lane", scope="repo:x", priority=9)
        self.runtime.enqueue("low", lane="lane", scope="repo:y", priority=1)
        second = self.runtime.claim(worker_id="w2", run_id="r2")
        self.assertEqual(first.task_id, "high1")
        self.assertEqual(second.task_id, "low")

    def test_waiting_manual_does_not_release_successor(self):
        self.runtime.enqueue("next", lane="lane", scope="repo:x", depends_on=["first"])
        self.runtime.enqueue("first", lane="lane", scope="repo:y", successor_ids=["next"])
        lease = self.runtime.claim(worker_id="w", run_id="r")
        self.runtime.complete(task_id="first", worker_id="w", run_id="r", state="WAITING_MANUAL")
        self.assertEqual(self.runtime.get("next").state, "BLOCKED_DEPENDENCY")

    def test_absent_dependency_does_not_release_successor(self):
        self.runtime.enqueue("next", lane="lane", scope="repo:x", depends_on=["first", "missing"])
        self.runtime.enqueue("first", lane="lane", scope="repo:y", successor_ids=["next"])
        lease = self.runtime.claim(worker_id="w", run_id="r")
        self.runtime.complete(task_id="first", worker_id="w", run_id="r")
        self.assertEqual(self.runtime.get("next").state, "BLOCKED_DEPENDENCY")

    def test_expired_worker_cannot_heartbeat_or_complete(self):
        self.runtime.enqueue("a", lane="lane", scope="repo:x")
        lease = self.runtime.claim(worker_id="w", run_id="r", lease_seconds=0.001)
        time.sleep(0.01)
        with self.assertRaises(KeyError):
            self.runtime.heartbeat(task_id="a", worker_id="w", run_id="r")
        with self.assertRaises(KeyError):
            self.runtime.complete(task_id="a", worker_id="w", run_id="r")

    def test_watchdog_reservation_validation_fails_closed(self):
        for kwargs in (
            {"name": "", "fallback_seconds": 60, "reservation_seconds": 5},
            {"name": "watchdog", "fallback_seconds": 0, "reservation_seconds": 5},
            {"name": "watchdog", "fallback_seconds": float("inf"), "reservation_seconds": 5},
            {"name": "watchdog", "fallback_seconds": 60, "reservation_seconds": 0},
            {"name": "watchdog", "fallback_seconds": 60, "reservation_seconds": float("nan")},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.runtime.reserve_watchdog_tick(
                    now=100,
                    event_observed=False,
                    **kwargs,
                )
        with self.assertRaises(ValueError):
            self.runtime.reserve_watchdog_tick(
                name="watchdog",
                now=float("nan"),
                fallback_seconds=60,
                event_observed=False,
            )
        self.assertFalse(self.runtime.db.in_transaction)

    def test_two_connections_contend_for_one_watchdog_reservation(self):
        barrier = threading.Barrier(2)

        def contend():
            runtime = AtlasRuntime(self.database)
            try:
                barrier.wait()
                return runtime.reserve_watchdog_tick(
                    name="watchdog",
                    now=100,
                    fallback_seconds=60,
                    reservation_seconds=5,
                    event_observed=False,
                )
            finally:
                runtime.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            reservations = list(pool.map(lambda _: contend(), range(2)))

        winners = [item for item in reservations if item is not None]
        self.assertEqual(len(winners), 1)
        self.assertEqual(
            self.runtime.db.execute(
                "SELECT COUNT(*) FROM watchdog_runs WHERE state='IN_PROGRESS'"
            ).fetchone()[0],
            1,
        )

    def test_competitor_cannot_shorten_issued_reservation_expiry(self):
        issued = self.runtime.reserve_watchdog_tick(
            name="watchdog",
            now=100,
            fallback_seconds=1_800,
            reservation_seconds=60,
            event_observed=False,
        )
        competitor = AtlasRuntime(self.database)
        try:
            self.assertIsNone(
                competitor.reserve_watchdog_tick(
                    name="watchdog",
                    now=102,
                    fallback_seconds=1_800,
                    reservation_seconds=1,
                    event_observed=False,
                )
            )
        finally:
            competitor.close()
        row = self.runtime.db.execute(
            "SELECT state,expires_at FROM watchdog_runs WHERE reservation_id=?",
            (issued.reservation_id,),
        ).fetchone()
        self.assertEqual(row["state"], "IN_PROGRESS")
        self.assertEqual(row["expires_at"], issued.expires_at)
        self.assertEqual(row["expires_at"], 160)

    def test_new_in_progress_watchdog_run_requires_issued_expiry(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.runtime.db.execute(
                "INSERT INTO watchdog_runs("
                "reservation_id,name,state,reserved_at,expires_at,terminal_at"
                ") VALUES('missing-expiry','watchdog','IN_PROGRESS',100,NULL,NULL)"
            )

    def test_watchdog_success_starts_cooldown_and_survives_restart(self):
        reservation = self.runtime.reserve_watchdog_tick(
            name="watchdog",
            now=100,
            fallback_seconds=20,
            reservation_seconds=5,
            event_observed=False,
        )
        self.assertIsNotNone(reservation)
        self.runtime.complete_watchdog_tick(reservation=reservation, now=100)
        self.assertFalse(self.runtime.db.in_transaction)
        self.runtime.close()
        self.runtime = AtlasRuntime(self.database)

        self.assertIsNone(
            self.runtime.reserve_watchdog_tick(
                name="watchdog",
                now=119,
                fallback_seconds=20,
                reservation_seconds=5,
                event_observed=False,
            )
        )
        next_reservation = self.runtime.reserve_watchdog_tick(
            name="watchdog",
            now=120,
            fallback_seconds=20,
            reservation_seconds=5,
            event_observed=False,
        )
        self.assertIsNotNone(next_reservation)
        self.assertNotEqual(next_reservation.reservation_id, reservation.reservation_id)

    def test_default_reservation_expiry_is_shorter_than_fallback(self):
        reservation = self.runtime.reserve_watchdog_tick(
            name="watchdog",
            now=100,
            fallback_seconds=1_800,
            event_observed=False,
        )
        self.assertEqual(reservation.expires_at, 160)

    def test_legacy_watchdog_cooldown_state_remains_compatible(self):
        legacy_database = Path(self.tmp.name) / "legacy.db"
        legacy = sqlite3.connect(legacy_database)
        legacy.execute(
            "CREATE TABLE watchdog_state("
            "name TEXT PRIMARY KEY,last_checked_at REAL NOT NULL)"
        )
        legacy.execute(
            "INSERT INTO watchdog_state(name,last_checked_at) VALUES(?,?)",
            ("watchdog", 100),
        )
        legacy.commit()
        legacy.close()
        migrated = AtlasRuntime(legacy_database)
        try:
            self.assertIsNone(
                migrated.reserve_watchdog_tick(
                    name="watchdog",
                    now=119,
                    fallback_seconds=20,
                    reservation_seconds=5,
                    event_observed=False,
                )
            )
            self.assertIsNotNone(
                migrated.reserve_watchdog_tick(
                    name="watchdog",
                    now=120,
                    fallback_seconds=20,
                    reservation_seconds=5,
                    event_observed=False,
                )
            )
        finally:
            migrated.close()

    def test_legacy_in_progress_run_without_expiry_fails_closed(self):
        legacy_database = Path(self.tmp.name) / "legacy-run.db"
        legacy = sqlite3.connect(legacy_database)
        legacy.executescript(
            """
            CREATE TABLE watchdog_runs (
              reservation_id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              state TEXT NOT NULL,
              reserved_at REAL NOT NULL,
              terminal_at REAL
            );
            INSERT INTO watchdog_runs(
              reservation_id,name,state,reserved_at,terminal_at
            ) VALUES('legacy','watchdog','IN_PROGRESS',100,NULL);
            """
        )
        legacy.commit()
        legacy.close()
        migrated = AtlasRuntime(legacy_database)
        try:
            self.assertIsNone(
                migrated.reserve_watchdog_tick(
                    name="watchdog",
                    now=10_000,
                    fallback_seconds=1_800,
                    reservation_seconds=1,
                    event_observed=False,
                )
            )
            row = migrated.db.execute(
                "SELECT state,expires_at FROM watchdog_runs "
                "WHERE reservation_id='legacy'"
            ).fetchone()
            self.assertEqual(row["state"], "IN_PROGRESS")
            self.assertIsNone(row["expires_at"])
        finally:
            migrated.close()

    def test_migrated_watchdog_runs_require_expiry_for_future_active_writes(self):
        legacy_database = Path(self.tmp.name) / "legacy-write-guard.db"
        legacy = sqlite3.connect(legacy_database)
        legacy.executescript(
            """
            CREATE TABLE watchdog_runs (
              reservation_id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              state TEXT NOT NULL,
              reserved_at REAL NOT NULL,
              terminal_at REAL
            );
            INSERT INTO watchdog_runs(
              reservation_id,name,state,reserved_at,terminal_at
            ) VALUES('terminal','watchdog','ABANDONED',100,101);
            """
        )
        legacy.commit()
        legacy.close()
        migrated = AtlasRuntime(legacy_database)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                migrated.db.execute(
                    "INSERT INTO watchdog_runs("
                    "reservation_id,name,state,reserved_at,expires_at,terminal_at"
                    ") VALUES('missing-expiry','other','IN_PROGRESS',100,NULL,NULL)"
                )
            with self.assertRaises(sqlite3.IntegrityError):
                migrated.db.execute(
                    "UPDATE watchdog_runs SET state='IN_PROGRESS',expires_at=NULL "
                    "WHERE reservation_id='terminal'"
                )
            migrated.db.execute(
                "INSERT INTO watchdog_runs("
                "reservation_id,name,state,reserved_at,expires_at,terminal_at"
                ") VALUES('issued','other','IN_PROGRESS',100,105,NULL)"
            )
            self.assertEqual(
                migrated.db.execute(
                    "SELECT state,expires_at FROM watchdog_runs "
                    "WHERE reservation_id='issued'"
                ).fetchone()["expires_at"],
                105,
            )
        finally:
            migrated.close()

    def test_abandoned_watchdog_run_retries_immediately(self):
        reservation = self.runtime.reserve_watchdog_tick(
            name="watchdog",
            now=100,
            fallback_seconds=60,
            reservation_seconds=5,
            event_observed=False,
        )
        self.assertTrue(
            self.runtime.abandon_watchdog_tick(reservation=reservation, now=100)
        )
        retry = self.runtime.reserve_watchdog_tick(
            name="watchdog",
            now=100,
            fallback_seconds=60,
            reservation_seconds=5,
            event_observed=False,
        )
        self.assertIsNotNone(retry)
        self.assertNotEqual(retry.reservation_id, reservation.reservation_id)
        self.assertFalse(self.runtime.db.in_transaction)

    def test_crashed_watchdog_reservation_expires_and_is_recovered(self):
        abandoned = self.runtime.reserve_watchdog_tick(
            name="watchdog",
            now=100,
            fallback_seconds=60,
            reservation_seconds=5,
            event_observed=False,
        )
        self.runtime.close()
        self.runtime = AtlasRuntime(self.database)
        self.assertIsNone(
            self.runtime.reserve_watchdog_tick(
                name="watchdog",
                now=104,
                fallback_seconds=60,
                reservation_seconds=5,
                event_observed=False,
            )
        )
        recovered = self.runtime.reserve_watchdog_tick(
            name="watchdog",
            now=105,
            fallback_seconds=60,
            reservation_seconds=5,
            event_observed=False,
        )
        self.assertIsNotNone(recovered)
        self.assertEqual(
            self.runtime.db.execute(
                "SELECT state FROM watchdog_runs WHERE reservation_id=?",
                (abandoned.reservation_id,),
            ).fetchone()["state"],
            "ABANDONED",
        )

    def test_watchdog_completion_identity_mismatch_rolls_back(self):
        reservation = self.runtime.reserve_watchdog_tick(
            name="watchdog",
            now=100,
            fallback_seconds=60,
            reservation_seconds=5,
            event_observed=False,
        )
        wrong = WatchdogReservation(
            name=reservation.name,
            reservation_id="wrong",
            reserved_at=reservation.reserved_at,
            expires_at=reservation.expires_at,
        )
        with self.assertRaises(KeyError):
            self.runtime.complete_watchdog_tick(reservation=wrong, now=100)
        self.assertEqual(
            self.runtime.db.execute(
                "SELECT state FROM watchdog_runs WHERE reservation_id=?",
                (reservation.reservation_id,),
            ).fetchone()["state"],
            "IN_PROGRESS",
        )
        self.assertIsNone(
            self.runtime.db.execute(
                "SELECT * FROM watchdog_state WHERE name='watchdog'"
            ).fetchone()
        )
        self.assertFalse(self.runtime.db.in_transaction)

    def test_watchdog_completion_rejects_forged_issued_fields(self):
        reservation = self.runtime.reserve_watchdog_tick(
            name="watchdog",
            now=100,
            fallback_seconds=60,
            reservation_seconds=5,
            event_observed=False,
        )
        for forged in (
            WatchdogReservation(
                name="other",
                reservation_id=reservation.reservation_id,
                reserved_at=reservation.reserved_at,
                expires_at=reservation.expires_at,
            ),
            WatchdogReservation(
                name=reservation.name,
                reservation_id=reservation.reservation_id,
                reserved_at=999,
                expires_at=reservation.expires_at,
            ),
            WatchdogReservation(
                name=reservation.name,
                reservation_id=reservation.reservation_id,
                reserved_at=reservation.reserved_at,
                expires_at=999,
            ),
        ):
            with self.subTest(forged=forged), self.assertRaises(KeyError):
                self.runtime.complete_watchdog_tick(reservation=forged, now=101)
        row = self.runtime.db.execute(
            "SELECT state,reserved_at,expires_at FROM watchdog_runs "
            "WHERE reservation_id=?",
            (reservation.reservation_id,),
        ).fetchone()
        self.assertEqual(tuple(row), ("IN_PROGRESS", 100, 105))
        self.assertIsNone(
            self.runtime.db.execute(
                "SELECT * FROM watchdog_state WHERE name='watchdog'"
            ).fetchone()
        )
        self.assertFalse(self.runtime.db.in_transaction)

    def test_expired_watchdog_completion_rejects_without_cooldown_then_recovers(self):
        expired = self.runtime.reserve_watchdog_tick(
            name="watchdog",
            now=100,
            fallback_seconds=60,
            reservation_seconds=5,
            event_observed=False,
        )
        with self.assertRaises(KeyError):
            self.runtime.complete_watchdog_tick(reservation=expired, now=105)
        self.assertEqual(
            self.runtime.db.execute(
                "SELECT state FROM watchdog_runs WHERE reservation_id=?",
                (expired.reservation_id,),
            ).fetchone()["state"],
            "IN_PROGRESS",
        )
        self.assertIsNone(
            self.runtime.db.execute(
                "SELECT * FROM watchdog_state WHERE name='watchdog'"
            ).fetchone()
        )
        replacement = self.runtime.reserve_watchdog_tick(
            name="watchdog",
            now=105,
            fallback_seconds=60,
            reservation_seconds=5,
            event_observed=False,
        )
        self.assertIsNotNone(replacement)
        self.assertNotEqual(replacement.reservation_id, expired.reservation_id)
        self.assertEqual(
            self.runtime.db.execute(
                "SELECT state FROM watchdog_runs WHERE reservation_id=?",
                (expired.reservation_id,),
            ).fetchone()["state"],
            "ABANDONED",
        )
        self.assertIsNone(
            self.runtime.db.execute(
                "SELECT * FROM watchdog_state WHERE name='watchdog'"
            ).fetchone()
        )
        self.assertFalse(self.runtime.db.in_transaction)

    def test_pre_issuance_watchdog_completion_rejects_without_immediate_fallback(self):
        reservation = self.runtime.reserve_watchdog_tick(
            name="watchdog",
            now=100,
            fallback_seconds=60,
            reservation_seconds=5,
            event_observed=False,
        )
        before = self.runtime.db.execute(
            "SELECT state,reserved_at,expires_at,terminal_at FROM watchdog_runs "
            "WHERE reservation_id=?",
            (reservation.reservation_id,),
        ).fetchone()
        with self.assertRaises(KeyError):
            self.runtime.complete_watchdog_tick(reservation=reservation, now=0)
        after = self.runtime.db.execute(
            "SELECT state,reserved_at,expires_at,terminal_at FROM watchdog_runs "
            "WHERE reservation_id=?",
            (reservation.reservation_id,),
        ).fetchone()
        self.assertEqual(tuple(after), tuple(before))
        self.assertIsNone(
            self.runtime.db.execute(
                "SELECT * FROM watchdog_state WHERE name='watchdog'"
            ).fetchone()
        )
        self.assertIsNone(
            self.runtime.reserve_watchdog_tick(
                name="watchdog",
                now=100.1,
                fallback_seconds=60,
                reservation_seconds=5,
                event_observed=False,
            )
        )
        self.assertFalse(self.runtime.db.in_transaction)

    def test_watchdog_receipt_rolls_back_and_deduplicates_after_restart(self):
        payload = {
            "schema": "atlas.watchdog.receipt.v1",
            "action": "HOLD",
            "reason": "TEST",
        }
        with patch.object(self.runtime, "_record_event", side_effect=RuntimeError("disk")):
            with self.assertRaises(RuntimeError):
                self.runtime.record_watchdog_receipt(
                    task_id="task", payload=payload, now=100
                )
        self.assertEqual(
            self.runtime.db.execute(
                "SELECT COUNT(*) FROM events WHERE kind='WATCHDOG'"
            ).fetchone()[0],
            0,
        )
        self.assertFalse(self.runtime.db.in_transaction)
        self.assertTrue(
            self.runtime.record_watchdog_receipt(
                task_id="task", payload=payload, now=100
            )
        )
        event = self.runtime.db.execute(
            "SELECT event_id,payload_digest FROM events WHERE kind='WATCHDOG'"
        ).fetchone()
        self.runtime.close()
        self.runtime = AtlasRuntime(self.database)
        self.assertFalse(
            self.runtime.record_watchdog_receipt(
                task_id="task", payload=payload, now=101
            )
        )
        reread = self.runtime.db.execute(
            "SELECT event_id,payload_digest FROM events WHERE kind='WATCHDOG'"
        ).fetchone()
        self.assertEqual(tuple(event), tuple(reread))

    def test_watchdog_tasks_observe_paused_usage_without_mutation(self):
        self.runtime.enqueue("paused", lane="lane", scope="repo:paused")
        self.runtime.db.execute(
            "UPDATE tasks SET state='PAUSED_USAGE' WHERE task_id='paused'"
        )
        candidates = self.runtime.watchdog_tasks(now=100)
        self.assertEqual([(task.task_id, task.state, leased) for task, leased in candidates],
                         [("paused", "PAUSED_USAGE", False)])
        self.assertEqual(self.runtime.get("paused").state, "PAUSED_USAGE")


if __name__ == "__main__":
    unittest.main()
