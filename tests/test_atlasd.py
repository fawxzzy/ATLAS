import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from ops.atlas.atlas_runtime import AtlasRuntime
from ops.atlas.atlasd import main


class AtlasdTests(unittest.TestCase):
    def test_health_is_truthful_and_does_not_launch_workers(self):
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "atlasd.db"
            runtime = AtlasRuntime(database)
            runtime.enqueue("ready", lane="fitness", scope="repo:fitness")
            runtime.close()
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--database", str(database), "health"]), 0)
            health = json.loads(output.getvalue())
            self.assertEqual(health["tasks_by_state"], {"QUEUED": 1})
            self.assertEqual(health["running_worker_count"], 0)
            self.assertEqual(health["stranded_ready_count"], 1)
            self.assertFalse(health["worker_launch_enabled"])

    def test_reconcile_reports_paused_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "atlasd.db"
            runtime = AtlasRuntime(database)
            runtime.enqueue("running", lane="atlas", scope="atlas-root:runtime")
            runtime.claim(worker_id="worker", run_id="run", lease_seconds=0.001)
            runtime.close()
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--database", str(database), "reconcile", "--heartbeat-timeout", "0"]), 0)
            health = json.loads(output.getvalue())
            self.assertEqual(health["paused_runtime_tasks"], ["running"])
            self.assertEqual(health["tasks_by_state"], {"PAUSED_RUNTIME": 1})


if __name__ == "__main__":
    unittest.main()
