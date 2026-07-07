from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.atlas import held_lane_unlock_matrix as matrix
from ops.atlas import marker_aware_next_packet_planner as planner


def _candidate(marker: str, classification: str, packet: str, mode: str = "", reason: str = "", percent: int = 50, safe: bool = False) -> dict:
    return {
        "marker": marker,
        "percent": percent,
        "source_ref": f"docs/memory/initiatives/{marker.lower().replace(' ', '-')}.json",
        "classification": classification,
        "score": 10,
        "packet": packet,
        "mode": mode,
        "reason": reason,
        "current_checkpoint_receipt": "docs/ops/CHECKPOINT.md",
        "safe_to_select": safe,
    }


class HeldLaneUnlockMatrixTests(unittest.TestCase):
    def test_live_report_emits_required_shape(self) -> None:
        report = matrix.build_report(root=Path.cwd())
        self.assertEqual(report["schema_version"], matrix.SCHEMA_VERSION)
        self.assertIn(report["status"], {matrix.STATUS_OK, matrix.STATUS_ADVISORY_MATRIX})
        self.assertGreaterEqual(report["candidate_count"], 1)
        self.assertEqual(report["candidate_count"], len(report["candidates"]))
        self.assertIn("Fitness app work is an owner lane and is not mutated by this helper.", report["owner_lane_boundaries"])
        self.assertIn("docs/PLAYBOOK_NOTES.md#marker-ratchet-threshold", report["playbook_rule_refs"])

    def test_deterministic_top_level_ordering(self) -> None:
        report = matrix.build_report(root=Path.cwd(), planner_report={"candidate_scores": [], "blockers": [{"code": "x"}]})
        self.assertEqual(
            list(report.keys()),
            [
                "schema_version",
                "status",
                "candidate_count",
                "held_count",
                "unlockable_count",
                "blocker_classes",
                "candidates",
                "required_proofs",
                "required_receipts",
                "operator_actions",
                "owner_lane_boundaries",
                "playbook_rule_refs",
                "authority_risks",
                "recommended_next_selection",
                "safe_to_continue",
                "blockers",
                "branch",
                "head",
            ],
        )

    def test_all_frozen_blocker_classes_are_classifiable(self) -> None:
        cases = [
            (_candidate("held", planner.CLASS_HELD, "No immediate packet", mode="hold-flat"), "held_by_manifest"),
            (_candidate("proof", planner.CLASS_PROOF_GATED, "protected proof needed"), "proof_gated"),
            (_candidate("external", planner.CLASS_EXTERNAL_PROOF, "external proof needed"), "external_proof_required"),
            (_candidate("owner", planner.CLASS_OWNER_BLOCKED, "owner-side blocker"), "owner_lane_required"),
            (_candidate("operator", planner.CLASS_DOCS_ONLY, "candidate needs separately selected scope"), "operator_selection_required"),
            (_candidate("done", planner.CLASS_HELD, "No further package", mode="closed", percent=100), "already_completed"),
            (_candidate("stale", planner.CLASS_STALE, "stale packet"), "stale_packet"),
            (_candidate("impl", planner.CLASS_IMPLEMENTATION_READY, "first-implementation worker-cluster reconciliation"), "implementation_missing"),
            (_candidate("contract", planner.CLASS_DOCS_ONLY, "contract freeze", mode="docs-only"), "contract_missing"),
            (_candidate("ready", planner.CLASS_DOCS_ONLY, "implementation-readiness closeout", mode="docs-only"), "readiness_missing"),
            (_candidate("unsafe", planner.CLASS_UNSAFE, "final receipt authority"), "authority_risk"),
            (_candidate("protected", planner.CLASS_UNSAFE, "touch secrets deploy workflow"), "protected_surface_risk"),
            (_candidate("hold", planner.CLASS_NO_ACTION, "no action hold"), "no_action_hold"),
        ]
        for candidate, expected in cases:
            with self.subTest(expected=expected):
                self.assertIn(expected, matrix.candidate_blocker_classes(candidate))

    def test_unlockable_candidate_sets_ok_and_recommendation(self) -> None:
        report = matrix.build_report(
            root=Path.cwd(),
            planner_report={
                "status": planner.STATUS_OK,
                "selected_packet": "selected worker",
                "candidate_scores": [_candidate("AI Long-Run", planner.CLASS_IMPLEMENTATION_READY, "selected worker", safe=True)],
                "blockers": [],
                "branch": "main",
                "head": "abc",
            },
        )
        self.assertEqual(report["status"], matrix.STATUS_OK)
        self.assertEqual(report["unlockable_count"], 1)
        self.assertEqual(report["recommended_next_selection"], "selected worker")

    def test_advisory_matrix_when_candidates_are_held(self) -> None:
        report = matrix.build_report(
            root=Path.cwd(),
            planner_report={
                "status": planner.STATUS_ADVISORY_RECOMMENDATION,
                "selected_packet": None,
                "candidate_scores": [_candidate("held", planner.CLASS_HELD, "No immediate packet")],
                "blockers": [],
            },
        )
        self.assertEqual(report["status"], matrix.STATUS_ADVISORY_MATRIX)
        self.assertEqual(report["held_count"], 1)
        self.assertIsNone(report["recommended_next_selection"])
        self.assertIn("hold until state changes", report["operator_actions"])

    def test_blocked_planner_report_blocks_matrix(self) -> None:
        report = matrix.build_report(
            root=Path.cwd(),
            planner_report={
                "status": planner.STATUS_BLOCKED,
                "selected_packet": None,
                "candidate_scores": [],
                "blockers": [{"code": "bad"}],
            },
        )
        self.assertEqual(report["status"], matrix.STATUS_BLOCKED)
        self.assertFalse(report["safe_to_continue"])

    def test_main_rejects_forbidden_source_refs(self) -> None:
        self.assertEqual(matrix.main(["--json", "--source", "repos/fitness/receipt.md"]), 2)
        self.assertEqual(matrix.main(["--json", "--source", "secrets/token.txt"]), 2)
        self.assertEqual(matrix.main(["--json", "--source", "archive/old.md"]), 2)
        self.assertEqual(matrix.main(["--json", "--source", ".github/workflows/build.yml"]), 2)

    def test_main_rejects_absolute_and_parent_source_refs(self) -> None:
        self.assertEqual(matrix.main(["--json", "--source", str(Path.cwd() / "docs/PLAYBOOK_NOTES.md")]), 2)
        self.assertEqual(matrix.main(["--json", "--source", "../outside.md"]), 2)

    def test_main_rejects_protected_output_path(self) -> None:
        self.assertEqual(matrix.main(["--json", "--output", "docs/out.json"]), 2)
        self.assertEqual(matrix.main(["--json", "--output", "tmp/out.txt"]), 2)

    def test_main_writes_output_only_to_tmp_json(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd() / "tmp") as temp_dir:
            output = Path(temp_dir) / "matrix.json"
            relative = output.relative_to(Path.cwd()).as_posix()
            exit_code = matrix.main(["--json", "--output", relative])
            self.assertEqual(exit_code, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], matrix.SCHEMA_VERSION)

    def test_strict_returns_nonzero_for_advisory_matrix(self) -> None:
        self.assertEqual(matrix.report_exit_code(status=matrix.STATUS_ADVISORY_MATRIX, strict=True), 1)
        self.assertEqual(matrix.report_exit_code(status=matrix.STATUS_ADVISORY_MATRIX, strict=False), 0)


if __name__ == "__main__":
    unittest.main()
