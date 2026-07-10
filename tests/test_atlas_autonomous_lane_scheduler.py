from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops.atlas import autonomous_lane_scheduler as scheduler
from ops.atlas import marker_aware_next_packet_planner as planner


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _program_payload() -> dict[str, object]:
    return {
        "schema_version": scheduler.PROGRAM_SCHEMA_VERSION,
        "name": "atlas-root-autocomplete",
        "max_docs_only_streak": 2,
        "max_file_overlap_risk": "medium",
        "allow_reselection": True,
        "allowed_markers": [
            "Cortex Simulation Substrate Readiness",
            "Vercel Platform Observability Governance",
            "Cortex Dual-Mode Replacement Readiness",
            "AI Long-Run Batch Orchestration",
            "AI Repetition-to-Automation Pipeline",
            "Cortex Readiness",
            "Playbook Everywhere + Cortex Interface",
            "AI Work Session Stability & Auto-Sync Loop",
        ],
        "excluded_markers": ["Sandbox Simulation Readiness"],
        "forbidden_owner_lanes": ["fitness", "mazer", "discordos", "foundation", "trove", "playbook", "stream"],
        "phase_priority": [
            "worker_reconciliation",
            "worker_implementation",
            "implementation_readiness",
            "prompt_pack",
            "first_implementation_admission",
            "contract_freeze",
            "selector",
        ],
        "stop_on": ["critical_validation", "error_validation", "owner_repo_required", "secret_required", "deploy_required", "no_safe_candidate"],
    }


def _preflight_payload(*, critical: int = 0, error: int = 0) -> dict[str, object]:
    return {
        "status": "ok" if critical == 0 and error == 0 else "blocker",
        "validation": {"critical": critical, "error": error, "warning": 0, "info": 0},
        "projection_freshness": {"status": "ok", "inventory_matches_live_working_set": True},
        "local_residue": {"root_dirty_paths": []},
        "markers": {"active_lane": "Sandbox Simulation Readiness", "active_lane_is_held": True},
    }


def _selector_payload(*, active_lane_is_held: bool = True, action: str = "hold_current_lane", current_packet: str | None = None) -> dict[str, object]:
    return {
        "selected_marker": "Sandbox Simulation Readiness",
        "active_lane_is_held": active_lane_is_held,
        "operator_action": action,
        "selected_current_packet": current_packet,
        "selected_current_packet_mode": "docs-only root-bounded hold",
    }


def _planner_payload(items: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": planner.SCHEMA_VERSION,
        "status": "ok",
        "selected_marker": items[0]["marker"] if items else None,
        "selected_packet": items[0]["packet"] if items else None,
        "candidate_count": len(items),
        "candidate_scores": items,
    }


class AutonomousLaneSchedulerTests(unittest.TestCase):
    def test_validation_cleanup_takes_precedence(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(error=1),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_VALIDATION_CLEANUP, report["status"])
        self.assertEqual(scheduler.DECISION_VALIDATION_CLEANUP, report["decision"])
        self.assertTrue(report["safe_to_execute"])

    def test_worker_reconciliation_selected_before_other_packets(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "Cortex Simulation Substrate Readiness",
                        "classification": planner.CLASS_IMPLEMENTATION_READY,
                        "score": 100,
                        "packet": "Cortex Simulation Substrate Readiness worker cluster reconciliation",
                        "mode": "root-local implementation worker cluster",
                    },
                    {
                        "marker": "Cortex Dual-Mode Replacement Readiness",
                        "classification": planner.CLASS_DOCS_ONLY,
                        "score": 70,
                        "packet": "Cortex Dual-Mode Replacement Readiness synthesis-to-execution bridge schema contract freeze",
                        "mode": "docs-only root-bounded synthesis-to-execution bridge-schema contract freeze",
                    },
                ]
            ),
        )

        self.assertEqual(scheduler.STATUS_EXECUTE, report["status"])
        self.assertEqual(scheduler.DECISION_WORKER_RECONCILIATION, report["decision"])
        self.assertEqual("Cortex Simulation Substrate Readiness worker cluster reconciliation", report["selected_packet"])

    def test_routed_worker_selected(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "Cortex Simulation Substrate Readiness",
                        "classification": planner.CLASS_IMPLEMENTATION_READY,
                        "score": 100,
                        "packet": "Cortex Simulation Substrate Readiness simulation requirements map first-implementation worker packet 1",
                        "mode": "implement one bounded helper",
                    }
                ]
            ),
        )

        self.assertEqual(scheduler.DECISION_ROUTED_WORKER, report["decision"])
        self.assertEqual("worker_implementation", report["packet_phase"])

    def test_exact_manifest_packet_selected_from_selector(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(active_lane_is_held=False, action="continue_current_lane", current_packet="Exact routed root packet"),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.DECISION_EXACT_MANIFEST_PACKET, report["decision"])
        self.assertEqual("Exact routed root packet", report["selected_packet"])

    def test_operator_program_switch_requires_reselection_receipt(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "Cortex Dual-Mode Replacement Readiness",
                        "classification": planner.CLASS_DOCS_ONLY,
                        "score": 70,
                        "packet": "Cortex Dual-Mode Replacement Readiness synthesis-to-execution bridge schema contract freeze",
                        "mode": "docs-only root-bounded synthesis-to-execution bridge-schema contract freeze",
                    }
                ]
            ),
        )

        self.assertEqual(scheduler.DECISION_OPERATOR_PROGRAM_PACKET, report["decision"])
        self.assertTrue(report["requires_reselection_receipt"])
        self.assertIn("CORTEX-DUAL-MODE-REPLACEMENT-READINESS", report["reselection_receipt"])

    def test_owner_lane_candidate_is_blocked(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "AI Long-Run Batch Orchestration",
                        "classification": planner.CLASS_DOCS_ONLY,
                        "score": 70,
                        "packet": "Fitness cleanup fallback",
                        "mode": "docs-only",
                    }
                ]
            ),
        )

        self.assertEqual(scheduler.STATUS_HOLD, report["status"])
        self.assertEqual("owner_lane_forbidden", report["blocked_candidates"][0]["blocked_reason"])

    def test_protected_packet_is_blocked(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "AI Long-Run Batch Orchestration",
                        "classification": planner.CLASS_DOCS_ONLY,
                        "score": 70,
                        "packet": "deploy production and edit .github/workflows/release.yml",
                        "mode": "docs-only",
                    }
                ]
            ),
        )

        self.assertEqual(scheduler.STATUS_HOLD, report["status"])
        self.assertEqual("protected_or_platform_mutation_forbidden", report["blocked_candidates"][0]["blocked_reason"])

    def test_playbook_everywhere_marker_is_not_blocked_by_name_only(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "Playbook Everywhere + Cortex Interface",
                        "classification": planner.CLASS_DOCS_ONLY,
                        "score": 70,
                        "packet": "Playbook Everywhere + Cortex Interface third consumer-class contract freeze",
                        "mode": "docs-only root-bounded contract freeze",
                    }
                ]
            ),
        )

        self.assertEqual(scheduler.STATUS_EXECUTE, report["status"])
        self.assertEqual("Playbook Everywhere + Cortex Interface", report["selected_marker"])

    def test_completed_packet_is_skipped(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "AI Long-Run Batch Orchestration",
                        "classification": planner.CLASS_HELD,
                        "score": 10,
                        "packet": "No immediate AI Long-Run Batch Orchestration same-lane packet",
                        "mode": "held after reconciliation",
                    }
                ]
            ),
        )

        self.assertEqual(scheduler.STATUS_HOLD, report["status"])
        self.assertEqual("held_or_stale_packet", report["skipped_candidates"][0]["stale_reason"])

    def test_cross_marker_signal_selects_cross_marker_decision(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(active_lane_is_held=False, action="continue_current_lane", current_packet=None),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "AI Long-Run Batch Orchestration",
                        "classification": planner.CLASS_DOCS_ONLY,
                        "score": 85,
                        "packet": "AI Long-Run Batch Orchestration planner integration contract freeze",
                        "mode": "docs-only root-bounded contract freeze",
                        "cross_marker_signal_applied": True,
                    }
                ]
            ),
        )

        self.assertEqual(scheduler.DECISION_CROSS_MARKER_OPPORTUNITY, report["decision"])

    def test_docs_only_streak_limit_blocks_docs_candidate(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "Cortex Dual-Mode Replacement Readiness",
                        "classification": planner.CLASS_DOCS_ONLY,
                        "score": 70,
                        "packet": "Cortex Dual-Mode Replacement Readiness synthesis-to-execution bridge schema contract freeze",
                        "mode": "docs-only root-bounded synthesis-to-execution bridge-schema contract freeze",
                    }
                ]
            ),
            recent_docs_only_streak=2,
        )

        self.assertEqual("docs_only_streak_limit", report["blocked_candidates"][0]["blocked_reason"])
        self.assertEqual(scheduler.STATUS_HOLD, report["status"])

    def test_hold_returns_nonzero_in_strict_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "tmp/atlas/program.json", json.dumps(_program_payload(), indent=2) + "\n")
            with patch.object(scheduler, "atlas_root", return_value=root):
                with patch.object(scheduler, "_branch_state", return_value=("main", "abc123")):
                    with patch.object(scheduler, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                        with patch.object(scheduler, "_load_selector", return_value=_selector_payload()):
                            with patch.object(
                                scheduler.ai_work_session_preflight,
                                "build_report",
                                return_value=_preflight_payload(),
                            ):
                                with patch.object(scheduler.planner, "build_report", return_value=_planner_payload([])):
                                    stdout = io.StringIO()
                                    with redirect_stdout(stdout):
                                        exit_code = scheduler.main(
                                            [
                                                "--json",
                                                "--program",
                                                "tmp/atlas/program.json",
                                                "--output",
                                                "tmp/atlas/report.json",
                                                "--prompt-output",
                                                "tmp/atlas/prompt.md",
                                                "--strict",
                                            ]
                                        )

        self.assertEqual(2, exit_code)
        self.assertEqual(scheduler.STATUS_HOLD, json.loads(stdout.getvalue())["status"])

    def test_main_writes_outputs_to_tmp_atlas(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "tmp/atlas/program.json", json.dumps(_program_payload(), indent=2) + "\n")
            with patch.object(scheduler, "atlas_root", return_value=root):
                with patch.object(scheduler, "_branch_state", return_value=("main", "abc123")):
                    with patch.object(scheduler, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                        with patch.object(scheduler, "_load_selector", return_value=_selector_payload()):
                            with patch.object(
                                scheduler.ai_work_session_preflight,
                                "build_report",
                                return_value=_preflight_payload(),
                            ):
                                with patch.object(
                                    scheduler.planner,
                                    "build_report",
                                    return_value=_planner_payload(
                                        [
                                            {
                                                "marker": "Cortex Dual-Mode Replacement Readiness",
                                                "classification": planner.CLASS_DOCS_ONLY,
                                                "score": 70,
                                                "packet": "Cortex Dual-Mode Replacement Readiness synthesis-to-execution bridge schema contract freeze",
                                                "mode": "docs-only root-bounded synthesis-to-execution bridge-schema contract freeze",
                                            }
                                        ]
                                    ),
                                ):
                                    stdout = io.StringIO()
                                    with redirect_stdout(stdout):
                                        exit_code = scheduler.main(
                                            [
                                                "--json",
                                                "--program",
                                                "tmp/atlas/program.json",
                                                "--output",
                                                "tmp/atlas/report.json",
                                                "--prompt-output",
                                                "tmp/atlas/prompt.md",
                                            ]
                                        )

            payload = json.loads((root / "tmp/atlas/report.json").read_text(encoding="utf-8"))
            prompt_text = (root / "tmp/atlas/prompt.md").read_text(encoding="utf-8")

        self.assertEqual(0, exit_code)
        self.assertEqual(scheduler.SCHEMA_VERSION, payload["schema_version"])
        self.assertIn("Selected packet:", prompt_text)
