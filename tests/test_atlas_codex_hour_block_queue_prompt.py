from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import codex_hour_block_queue_prompt as hour_block
from ops.atlas import marker_aware_next_packet_planner as planner


def _selector_payload(
    *,
    action: str = "no_immediate_root_packet",
    current_packet: str | None = None,
    next_packet: str | None = None,
) -> dict:
    return {
        "selected_marker": "Sandbox Simulation Readiness",
        "selected_percentage": 99,
        "operator_action": action,
        "operator_action_reason": "All eligible open markers are manifest-held.",
        "selected_current_packet": current_packet,
        "next_after_current_packet": next_packet,
        "open_markers": [
            {
                "marker": "AI Long-Run Batch Orchestration",
                "percentage": 69,
                "category": "admissible after current lane",
                "priority": 1,
            }
        ],
    }


def _planner_payload(
    *,
    safe: bool = False,
    selected_packet: str | None = None,
    classification: str | None = None,
    mode: str | None = None,
) -> dict:
    packet = selected_packet or ("Executable packet" if safe else None)
    candidate_packet = selected_packet or ("Executable packet" if safe else "No immediate AI Long-Run Batch Orchestration same-lane packet")
    candidate_classification = classification or (planner.CLASS_IMMEDIATE if safe else planner.CLASS_HELD)
    return {
        "schema_version": planner.SCHEMA_VERSION,
        "status": planner.STATUS_ADVISORY_RECOMMENDATION,
        "selected_marker": "AI Long-Run Batch Orchestration" if safe else None,
        "selected_packet": packet,
        "candidate_count": 1,
        "candidate_scores": [
            {
                "marker": "AI Long-Run Batch Orchestration",
                "percent": 69,
                "manifest_id": "continuity-manifest-ai-long-run-batch-orchestration",
                "source_ref": "docs/memory/initiatives/continuity-manifest-ai-long-run-batch-orchestration.json",
                "classification": candidate_classification,
                "score": 90 if safe else 10,
                "packet": candidate_packet,
                "mode": mode or ("implementation-ready" if safe else "hold-flat"),
                "reason": "test",
                "safe_to_select": safe,
            }
        ],
    }


def _closeout_payload(*, root_clean: bool = True, critical: int = 0, error: int = 0) -> dict:
    return {
        "root_clean": root_clean,
        "validation_state": {"critical": critical, "error": error, "warning": 0, "info": 0},
        "owner_lane_fallback_forbidden": True,
    }


def _check_output(*args: object, **kwargs: object) -> str:
    return json.dumps(_selector_payload(action="continue_current_lane", current_packet="Sandbox exact packet"))


class CodexHourBlockQueuePromptTests(unittest.TestCase):
    def test_build_report_generates_safe_hour_block_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(hour_block, "_branch_state", return_value=("main", "abc123")):
                with mock.patch.object(hour_block, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                    with mock.patch.object(hour_block, "_closeout_report", return_value=_closeout_payload()):
                        with mock.patch.object(hour_block.planner, "build_report", return_value=_planner_payload()):
                            with mock.patch.object(hour_block.subprocess, "check_output", side_effect=_check_output):
                                payload = hour_block.build_report(root=root)

        self.assertEqual(hour_block.STATUS_OK, payload["status"])
        self.assertTrue(payload["safe_to_use"])
        self.assertTrue(payload["should_generate_queue"])
        self.assertEqual("continue_current_lane", payload["selector"]["operator_action"])
        self.assertEqual("allow_exact_packet", payload["suppression_decision"])
        self.assertEqual(0, payload["planner"]["safe_candidate_count"])
        self.assertEqual("selector_current_packet", payload["selected_packet_source"])
        self.assertEqual("none", payload["packet_authority_risk"])
        self.assertIn("SCOPE LOCK:", payload["prompt_text"])
        self.assertIn("This is an ATLAS-root-only packet.", payload["prompt_text"])
        self.assertIn("Do not switch to Fitness or Mazer as a fallback.", payload["prompt_text"])
        self.assertIn("Attempt up to 7 bundles", payload["prompt_text"])
        self.assertIn("Fitness app implementation", payload["prompt_text"])
        self.assertIn("Mazer game implementation", payload["prompt_text"])
        self.assertIn("Do not move markers for wording refresh", payload["prompt_text"])
        self.assertIn("Vercel Platform Observability Governance", payload["allowed_root_marker_lanes"])

    def test_clean_held_root_emits_suppression_state_and_hold_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(hour_block, "_branch_state", return_value=("main", "abc123")):
                with mock.patch.object(hour_block, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                    with mock.patch.object(hour_block, "_closeout_report", return_value=_closeout_payload()):
                        with mock.patch.object(hour_block.planner, "build_report", return_value=_planner_payload()):
                            with mock.patch.object(hour_block.subprocess, "check_output", return_value=json.dumps(_selector_payload())):
                                payload = hour_block.build_report(root=root)

        self.assertEqual(hour_block.STATUS_OK, payload["status"])
        self.assertEqual("suppress_continuation", payload["suppression_decision"])
        self.assertFalse(payload["should_generate_queue"])
        self.assertFalse(payload["suppression"]["safe_to_continue"])
        self.assertIn(hour_block.HOLD_HEADER, payload["prompt_text"])
        self.assertIn("Root is clean: `True`", payload["prompt_text"])
        self.assertIn("Exact root packet exists: `False`", payload["prompt_text"])
        self.assertIn("Owner-lane fallback is forbidden: `True`", payload["prompt_text"])
        self.assertIn("Choose a new bounded ATLAS-root packet before continuing.", payload["prompt_text"])
        self.assertNotIn("Attempt up to 7 bundles", payload["prompt_text"])

    def test_safe_planner_candidate_is_summarized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(hour_block, "_branch_state", return_value=("main", "abc123")):
                with mock.patch.object(hour_block, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                    with mock.patch.object(hour_block, "_closeout_report", return_value=_closeout_payload()):
                        with mock.patch.object(hour_block.planner, "build_report", return_value=_planner_payload(safe=True)):
                            with mock.patch.object(hour_block.subprocess, "check_output", return_value=json.dumps(_selector_payload())):
                                payload = hour_block.build_report(root=root)

        self.assertEqual(1, payload["planner"]["safe_candidate_count"])
        self.assertEqual("Executable packet", payload["planner"]["safe_candidates"][0]["packet"])
        self.assertEqual("allow_exact_packet", payload["suppression_decision"])
        self.assertEqual(planner.CLASS_IMMEDIATE, payload["selected_packet_classification"])
        self.assertTrue(payload["should_generate_queue"])
        self.assertIn("Planner safe candidates: `1`", payload["prompt_text"])
        self.assertIn("Packet authority risk: `none`", payload["prompt_text"])

    def test_safe_docs_only_marker_ratchet_packet_generates_queue(self) -> None:
        selected_packet = "AI Long-Run Batch Orchestration cross-marker ratchet opportunity first-implementation admission"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(hour_block, "_branch_state", return_value=("main", "abc123")):
                with mock.patch.object(hour_block, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                    with mock.patch.object(hour_block, "_closeout_report", return_value=_closeout_payload()):
                        with mock.patch.object(
                            hour_block.planner,
                            "build_report",
                            return_value=_planner_payload(
                                safe=True,
                                selected_packet=selected_packet,
                                classification=planner.CLASS_DOCS_ONLY,
                                mode="docs-only first-implementation admission",
                            ),
                        ):
                            with mock.patch.object(hour_block.subprocess, "check_output", return_value=json.dumps(_selector_payload())):
                                payload = hour_block.build_report(root=root)

        self.assertEqual(hour_block.STATUS_OK, payload["status"])
        self.assertEqual("allow_exact_packet", payload["suppression_decision"])
        self.assertEqual("planner_selected_packet", payload["selected_packet_source"])
        self.assertEqual(planner.CLASS_DOCS_ONLY, payload["selected_packet_classification"])
        self.assertEqual("none", payload["packet_authority_risk"])
        self.assertTrue(payload["should_generate_queue"])
        self.assertIn(selected_packet, payload["prompt_text"])

    def test_operator_selected_packet_bypasses_suppression(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(hour_block, "_branch_state", return_value=("main", "abc123")):
                with mock.patch.object(hour_block, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                    with mock.patch.object(hour_block, "_closeout_report", return_value=_closeout_payload()):
                        with mock.patch.object(hour_block.planner, "build_report", return_value=_planner_payload()):
                            with mock.patch.object(hour_block.subprocess, "check_output", return_value=json.dumps(_selector_payload())):
                                payload = hour_block.build_report(root=root, operator_selected_packet="AI Repetition bounded root packet")

        self.assertEqual("allow_operator_selected_packet", payload["suppression_decision"])
        self.assertEqual("AI Repetition bounded root packet", payload["operator_selected_packet"])
        self.assertTrue(payload["should_generate_queue"])

    def test_validation_cleanup_bypasses_suppression(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(hour_block, "_branch_state", return_value=("main", "abc123")):
                with mock.patch.object(hour_block, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                    with mock.patch.object(hour_block, "_closeout_report", return_value=_closeout_payload(root_clean=False, error=1)):
                        with mock.patch.object(hour_block.planner, "build_report", return_value=_planner_payload()):
                            with mock.patch.object(hour_block.subprocess, "check_output", return_value=json.dumps(_selector_payload())):
                                payload = hour_block.build_report(root=root)

        self.assertEqual("allow_validation_cleanup", payload["suppression_decision"])
        self.assertTrue(payload["should_generate_queue"])

    def test_worker_reconciliation_packet_bypasses_suppression(self) -> None:
        planner_payload = _planner_payload()
        planner_payload["selected_packet"] = "AI Repetition held-lane prompt suppression worker packet 2"
        planner_payload["candidate_scores"][0]["packet"] = planner_payload["selected_packet"]
        planner_payload["candidate_scores"][0]["safe_to_select"] = True

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(hour_block, "_branch_state", return_value=("main", "abc123")):
                with mock.patch.object(hour_block, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                    with mock.patch.object(hour_block, "_closeout_report", return_value=_closeout_payload()):
                        with mock.patch.object(hour_block.planner, "build_report", return_value=planner_payload):
                            with mock.patch.object(hour_block.subprocess, "check_output", return_value=json.dumps(_selector_payload())):
                                payload = hour_block.build_report(root=root)

        self.assertEqual("allow_worker_reconciliation", payload["suppression_decision"])
        self.assertTrue(payload["should_generate_queue"])

    def test_fitness_and_mazer_fallbacks_remain_forbidden(self) -> None:
        for selected_packet in ("Fitness cleanup fallback", "Mazer browser parity fallback"):
            planner_payload = _planner_payload()
            planner_payload["selected_packet"] = selected_packet
            planner_payload["candidate_scores"][0]["packet"] = selected_packet
            planner_payload["candidate_scores"][0]["safe_to_select"] = True
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                with mock.patch.object(hour_block, "_branch_state", return_value=("main", "abc123")):
                    with mock.patch.object(hour_block, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                        with mock.patch.object(hour_block, "_closeout_report", return_value=_closeout_payload()):
                            with mock.patch.object(hour_block.planner, "build_report", return_value=planner_payload):
                                with mock.patch.object(hour_block.subprocess, "check_output", return_value=json.dumps(_selector_payload())):
                                    payload = hour_block.build_report(root=root)

            self.assertEqual(hour_block.STATUS_BLOCKED, payload["status"])
            self.assertFalse(payload["safe_to_use"])
            self.assertFalse(payload["should_generate_queue"])
            self.assertIn("suppression_blocked", {item["code"] for item in payload["blockers"]})

    def test_selector_unavailable_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(hour_block, "_branch_state", return_value=("main", "abc123")):
                with mock.patch.object(hour_block, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                    with mock.patch.object(hour_block, "_closeout_report", return_value=_closeout_payload()):
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
                        with mock.patch.object(hour_block, "_closeout_report", return_value=_closeout_payload()):
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
                            with mock.patch.object(hour_block, "_closeout_report", return_value=_closeout_payload()):
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
                    with mock.patch.object(hour_block, "_closeout_report", return_value=_closeout_payload()):
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
                "suppression",
                "suppression_decision",
                "suppression_reason",
                "selected_packet_source",
                "selected_packet_classification",
                "packet_authority_risk",
                "allowed_next_actions",
                "should_generate_queue",
                "operator_selected_packet",
                "scope_lock",
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
