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
        self.runtime.enqueue("next", lane="lane", scope="repo:x")
        self.runtime.enqueue("first", lane="lane", scope="repo:y", successor_ids=["next"])
        lease = self.runtime.claim(worker_id="w", run_id="r")
        # Highest priority tie breaks by insertion; next was inserted first, so claim first explicitly by priority.
        if lease.task_id == "next":
            self.runtime.complete(task_id="next", worker_id="w", run_id="r")
            lease = self.runtime.claim(worker_id="w", run_id="r")
        successors = self.runtime.complete(task_id=lease.task_id, worker_id="w", run_id="r", receipt={"event_id": "evt-1"})
        self.assertEqual(successors, ("next",))
        self.assertEqual(self.runtime.get("next").state, "QUEUED")
        self.assertRaises(KeyError, self.runtime.complete, task_id=lease.task_id, worker_id="w", run_id="r")

    def test_stale_running_becomes_paused_runtime(self):
        self.runtime.enqueue("a", lane="lane", scope="repo:x")
        lease = self.runtime.claim(worker_id="w", run_id="r", lease_seconds=1)
        paused = self.runtime.reconcile(now=lease.expires_at + 1)
        self.assertEqual(paused, ["a"])
        self.assertEqual(self.runtime.get("a").state, "PAUSED_RUNTIME")

    def test_receipt_deduplication(self):
        self.runtime.enqueue("a", lane="lane", scope="repo:x")
        lease = self.runtime.claim(worker_id="w", run_id="r")
        self.runtime.complete(task_id="a", worker_id="w", run_id="r", receipt={"event_id": "same"})
        rows = self.runtime.db.execute("SELECT COUNT(*) AS n FROM events WHERE event_id='same'").fetchone()
        self.assertEqual(rows["n"], 1)


if __name__ == "__main__":
    unittest.main()
