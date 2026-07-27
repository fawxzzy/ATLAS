import tempfile
import time
import unittest
from pathlib import Path

from ops.atlas.atlas_runtime import AtlasRuntime


class AtlasRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.runtime = AtlasRuntime(Path(self.tmp.name) / "atlas.db")

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

    def test_expired_worker_cannot_heartbeat_or_complete(self):
        self.runtime.enqueue("a", lane="lane", scope="repo:x")
        lease = self.runtime.claim(worker_id="w", run_id="r", lease_seconds=0.001)
        time.sleep(0.01)
        with self.assertRaises(KeyError):
            self.runtime.heartbeat(task_id="a", worker_id="w", run_id="r")
        with self.assertRaises(KeyError):
            self.runtime.complete(task_id="a", worker_id="w", run_id="r")


if __name__ == "__main__":
    unittest.main()
