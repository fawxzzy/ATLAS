from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ops" / "atlas" / "workstation_resource_snapshot.ps1"


class AtlasWorkstationResourceSnapshotTests(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(SCRIPT),
                *args,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            cwd=ROOT,
        )

    def test_json_summary_is_sanitized_and_structured(self) -> None:
        completed = self._run("-JsonSummary", "-WorkflowOnly", "-Top", "5")

        self.assertEqual(0, completed.returncode, msg=completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual("atlas.workstation_resource_snapshot.summary.v1", payload["contract_version"])
        self.assertTrue(payload["workflow_only"])
        self.assertFalse(payload["include_path"])
        self.assertEqual(5, payload["top"])
        self.assertIn("workflow_summary", payload)
        self.assertIn("workflow_processes", payload)
        self.assertNotIn("top_cpu_processes", payload)
        self.assertNotIn("top_memory_processes", payload)
        self.assertIn("review_guidance", payload)
        self.assertIsInstance(payload["workflow_summary"]["workflow_names"], list)
        self.assertLessEqual(len(payload["workflow_processes"]), 5)
        self.assertTrue(
            all("path" not in process for process in payload["workflow_processes"]),
            msg=completed.stdout,
        )

    def test_json_summary_rejects_include_path(self) -> None:
        completed = self._run("-JsonSummary", "-IncludePath")

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("cannot be combined with -IncludePath", completed.stderr)


if __name__ == "__main__":
    unittest.main()
