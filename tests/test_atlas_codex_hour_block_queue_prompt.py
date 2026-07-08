from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import codex_hour_block_queue_prompt as hour_block
from ops.atlas import marker_aware_next_packet_planner as planner


def _selector_payload() -> dict:
    return {
        "selected_marker": "Sandbox Simulation Readiness",
        "selected_percentage": 99,
        "operator_action": "no_immediate_root_packet",
        "operator_action_reason": "All eligible open markers are manifest-held.",
        "selected_current_packet": "Sandbox hold packet",
        "next_after_current_packet": None,
        "open_markers": [
            {
                "marker": "AI Long-Run Batch Orchestration",
                "percentage": 69,
                "category": "admissible after current lane",
                "priority": 1,
            }
        ],
    }


def _planner_payload(*, safe: bool = False) -> dict:
    return {
        "schema_version": planner.SCHEMA_VERSION,
        "status": planner.STATUS_ADVISORY_RECOMMENDATION,
        "selected_marker": "AI Long-Run Batch Orchestration" if safe else None,
        "selected_packet": "Executable packet" if safe else None,
        "candidate_count": 1,
        "candidate_scores": [
            {
                "marker": "AI Long-Run Batch Orchestration",
                "percent": 69,
                "manifest_id": "continuity-manifest-ai-long-run-batch-orchestration",
                "source_ref": "docs/memory/initiatives/continuity-manifest-ai-long-run-batch-orchestration.json",
                "classification": planner.CLASS_IMMEDIATE if safe else planner.CLASS_HELD,
                "score": 90 if safe else 10,
                "packet": "Executable packet" if safe else "No immediate AI Long-Run Batch Orchestration same-lane packet",
                "mode": "implementation-ready" if safe else "hold-flat",
                "reason": "test",
                "safe_to_select": safe,
            }
        ],
    }


def _check_output(*args: object, **kwargs: object) -> str:
    return json.dumps(_selector_payload())


class CodexHourBlockQueuePromptTests(unittest.TestCase):
    def test_build_report_generates_safe_hour_block_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(hour_block, "_branch_state", return_value=("main", "abc123")):
                with mock.patch.object(hour_block, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                    with mock.patch.object(hour_block.planner, "build_report", return_value=_planner_payload()):
                        with mock.patch.object(hour_block.subprocess, "check_output", side_effect=_check_output):
                            payload = hour_block.build_report(root=root)

        self.assertEqual(hour_block.STATUS_OK, payload["status"])
        self.assertTrue(payload["safe_to_use"])
        self.assertEqual("no_immediate_root_packet", payload["selector"]["operator_action"])
        self.assertEqual(0, payload["planner"]["safe_candidate_count"])
        self.assertIn("SCOPE LOCK:", payload["prompt_text"])
        self.assertIn("This is an ATLAS-root-only packet.", payload["prompt_text"])
        self.assertIn("Do not switch to Fitness or Mazer as a fallback.", payload["prompt_text"])
        self.assertIn("Attempt up to 7 bundles", payload["prompt_text"])
        self.assertIn("Fitness app implementation", payload["prompt_text"])
        self.assertIn("Mazer game implementation", payload["prompt_text"])
        self.assertIn("Do not move markers for wording refresh", payload["prompt_text"])

    def test_safe_planner_candidate_is_summarized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(hour_block, "_branch_state", return_value=("main", "abc123")):
                with mock.patch.object(hour_block, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                    with mock.patch.object(hour_block.planner, "build_report", return_value=_planner_payload(safe=True)):
                        with mock.patch.object(hour_block.subprocess, "check_output", side_effect=_check_output):
                            payload = hour_block.build_report(root=root)

        self.assertEqual(1, payload["planner"]["safe_candidate_count"])
        self.assertEqual("Executable packet", payload["planner"]["safe_candidates"][0]["packet"])
        self.assertIn("Planner safe candidates: `1`", payload["prompt_text"])

    def test_selector_unavailable_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(hour_block, "_branch_state", return_value=("main", "abc123")):
                with mock.patch.object(hour_block, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                    with mock.patch.object(hour_block.planner, "build_report", return_value=_planner_payload()):
                        with mock.patch.object(hour_block.subprocess, "check_output", side_effect=RuntimeError("boom")):
                            payload = hour_block.build_report(root=root)

        self.assertEqual(hour_block.STATUS_BLOCKED, payload["status"])
        self.assertFalse(payload["safe_to_use"])
        self.assertIn("selector_unavailable", {item["code"] for item in payload["blockers"]})

    def test_main_writes_json_and_prompt_outputs_under_tmp(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(hour_block, "atlas_root", return_value=root):
                with mock.patch.object(hour_block, "_branch_state", return_value=("main", "abc123")):
                    with mock.patch.object(hour_block, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                        with mock.patch.object(hour_block.planner, "build_report", return_value=_planner_payload()):
                            with mock.patch.object(hour_block.subprocess, "check_output", side_effect=_check_output):
                                stdout = io.StringIO()
                                with mock.patch("sys.stdout", stdout):
                                    code = hour_block.main(["--json", "--output", "tmp/hour-block.json", "--prompt-output", "tmp/hour-block.md"])

            report = json.loads((root / "tmp" / "hour-block.json").read_text(encoding="utf-8"))
            prompt = (root / "tmp" / "hour-block.md").read_text(encoding="utf-8")

        self.assertEqual(0, code)
        self.assertEqual(hour_block.SCHEMA_VERSION, report["schema_version"])
        self.assertIn("CODEX-MSG-ID", prompt)

    def test_prompt_output_must_be_tmp_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for output in ["docs/hour-block.md", "tmp/hour-block.json", "../tmp/hour-block.md", str(root / "tmp" / "hour-block.md")]:
                with mock.patch.object(hour_block, "atlas_root", return_value=root):
                    with mock.patch.object(hour_block, "_branch_state", return_value=("main", "abc123")):
                        with mock.patch.object(hour_block, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                            with mock.patch.object(hour_block.planner, "build_report", return_value=_planner_payload()):
                                with mock.patch.object(hour_block.subprocess, "check_output", side_effect=_check_output):
                                    stdout = io.StringIO()
                                    with mock.patch("sys.stdout", stdout):
                                        code = hour_block.main(["--json", "--prompt-output", output])
                self.assertEqual(2, code, output)

    def test_deterministic_top_level_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(hour_block, "_branch_state", return_value=("main", "abc123")):
                with mock.patch.object(hour_block, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                    with mock.patch.object(hour_block.planner, "build_report", return_value=_planner_payload()):
                        with mock.patch.object(hour_block.subprocess, "check_output", side_effect=_check_output):
                            payload = hour_block.build_report(root=root)

        self.assertEqual(
            [
                "schema_version",
                "status",
                "root",
                "branch",
                "head",
                "parity",
                "source_refs",
                "selector",
                "planner",
                "queue_stages",
                "allowed_root_marker_lanes",
                "excluded_surfaces",
                "boundaries",
                "baseline_commands",
                "optional_helper_commands",
                "blockers",
                "warnings",
                "safe_to_use",
                "prompt_text",
            ],
            list(payload.keys()),
        )


if __name__ == "__main__":
    unittest.main()
