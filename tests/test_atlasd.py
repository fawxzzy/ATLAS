import json
import subprocess
import sys
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

    def test_health_excludes_expired_lease(self):
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "atlasd.db"
            runtime = AtlasRuntime(database)
            runtime.enqueue("running", lane="atlas", scope="atlas-root:runtime")
            runtime.claim(worker_id="worker", run_id="run", lease_seconds=0.001)
            runtime.close()
            import time
            time.sleep(0.01)
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--database", str(database), "health"]), 0)
            self.assertEqual(json.loads(output.getvalue())["running_worker_count"], 0)

    def test_documented_direct_script_command_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "atlasd.db"
            root = Path(__file__).resolve().parents[1]
            result = subprocess.run(
                [sys.executable, "ops/atlas/atlasd.py", "--database", str(database), "init"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(json.loads(result.stdout)["running_worker_count"], 0)

    def test_watchdog_command_observes_without_launching_a_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "atlasd.db"
            runtime = AtlasRuntime(database)
            runtime.enqueue("ready", lane="atlas", scope="repo:atlas")
            runtime.close()
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--database", str(database), "watchdog", "--event"]), 0)
            result = json.loads(output.getvalue())
            self.assertFalse(result["worker_launch_enabled"])
            self.assertEqual(result["watchdog"]["decisions"][0]["action"], "WAKE_NEEDED")


if __name__ == "__main__":
    unittest.main()
