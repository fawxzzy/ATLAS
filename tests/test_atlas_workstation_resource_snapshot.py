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

    def test_json_closeout_is_sanitized_and_ties_closeout_to_residue_summary(self) -> None:
        completed = self._run(
            "-JsonCloseout",
            "-WorkflowOnly",
            "-Top",
            "5",
            "-ProcessesStarted",
            "codex",
            "-ProcessesStillRunning",
            "none",
            "-DevServerStatus",
            "not-run-in-this-pass",
            "-BrowserPlaywrightStatus",
            "not-run-in-this-pass",
            "-WatchTestStatus",
            "not-run-in-this-pass",
            "-StopCommandsRun",
            "none",
            "-AnythingLeftIntentionallyRunning",
            "none",
            "-NextChatServiceAction",
            "restart",
            "-NextChatServiceNote",
            "restart services only if needed",
        )

        self.assertEqual(0, completed.returncode, msg=completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual("atlas.workstation_resource_closeout.v1", payload["contract_version"])
        self.assertIn("closeout", payload)
        self.assertIn("residue_summary", payload)
        self.assertEqual("atlas.workstation_closeout_fields.v1", payload["closeout"]["closeout_fields_version"])
        self.assertEqual(["codex"], payload["closeout"]["processes_started"])
        self.assertEqual(["none"], payload["closeout"]["processes_still_running"])
        self.assertEqual("not-run-in-this-pass", payload["closeout"]["dev_server_status"])
        self.assertEqual("restart", payload["closeout"]["next_chat_service_action"])
        self.assertEqual(
            "atlas.workstation_resource_snapshot.summary.v1",
            payload["residue_summary"]["contract_version"],
        )
        self.assertTrue(payload["residue_summary"]["workflow_only"])
        self.assertTrue(
            all("path" not in process for process in payload["residue_summary"]["workflow_processes"]),
            msg=completed.stdout,
        )
        self.assertNotIn("top_cpu_processes", payload["residue_summary"])
        self.assertNotIn("top_memory_processes", payload["residue_summary"])

    def test_json_closeout_rejects_include_path(self) -> None:
        completed = self._run(
            "-JsonCloseout",
            "-IncludePath",
            "-DevServerStatus",
            "stopped",
            "-BrowserPlaywrightStatus",
            "stopped",
            "-WatchTestStatus",
            "stopped",
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("cannot be combined with -IncludePath", completed.stderr)

    def test_json_closeout_requires_status_fields(self) -> None:
        completed = self._run(
            "-JsonCloseout",
            "-BrowserPlaywrightStatus",
            "stopped",
            "-WatchTestStatus",
            "stopped",
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("-DevServerStatus is required", completed.stderr)

    def test_markdown_closeout_renders_paste_ready_contract_and_summary(self) -> None:
        completed = self._run(
            "-MarkdownCloseout",
            "-WorkflowOnly",
            "-Top",
            "5",
            "-ProcessesStarted",
            "codex",
            "-ProcessesStillRunning",
            "none",
            "-DevServerStatus",
            "stopped",
            "-BrowserPlaywrightStatus",
            "stopped",
            "-WatchTestStatus",
            "stopped",
            "-StopCommandsRun",
            "Stop-Process codex",
            "-AnythingLeftIntentionallyRunning",
            "none",
            "-NextChatServiceAction",
            "restart",
            "-NextChatServiceNote",
            "restart services only if needed",
        )

        self.assertEqual(0, completed.returncode, msg=completed.stderr)
        self.assertIn("# Workstation Closeout", completed.stdout)
        self.assertIn("## Closeout Contract", completed.stdout)
        self.assertIn("- Processes started: `codex`", completed.stdout)
        self.assertIn("- Browser/Playwright status: `stopped`", completed.stdout)
        self.assertIn("- Should the next chat inherit or restart local services: `restart`", completed.stdout)
        self.assertIn("## Sanitized Residue Summary", completed.stdout)
        self.assertIn("atlas.workstation_resource_snapshot.summary.v1", completed.stdout)
        self.assertNotIn("Path", completed.stdout)
        self.assertNotIn("\\", completed.stdout)

    def test_markdown_closeout_rejects_include_path(self) -> None:
        completed = self._run(
            "-MarkdownCloseout",
            "-IncludePath",
            "-DevServerStatus",
            "stopped",
            "-BrowserPlaywrightStatus",
            "stopped",
            "-WatchTestStatus",
            "stopped",
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("cannot be combined with -IncludePath", completed.stderr)

    def test_markdown_closeout_requires_status_fields(self) -> None:
        completed = self._run(
            "-MarkdownCloseout",
            "-DevServerStatus",
            "stopped",
            "-WatchTestStatus",
            "stopped",
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("-BrowserPlaywrightStatus is required", completed.stderr)


if __name__ == "__main__":
    unittest.main()
