from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import held_lane_unlock_matrix as matrix
from ops.atlas import held_lane_unlock_matrix_validator as validator


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _matrix_payload() -> dict:
    return {
        "schema_version": matrix.SCHEMA_VERSION,
        "status": matrix.STATUS_ADVISORY_MATRIX,
        "candidate_count": 1,
        "held_count": 1,
        "unlockable_count": 0,
        "blocker_classes": matrix.BLOCKER_CLASSES,
        "candidates": [
            {
                "marker": "AI Long-Run Batch Orchestration",
                "percent": 68,
                "source_ref": "docs/memory/initiatives/continuity-manifest-ai-long-run-batch-orchestration.json",
                "planner_classification": "held_lane",
                "packet": "No immediate packet",
                "mode": "hold-flat",
                "safe_to_select": False,
                "unlockable": False,
                "blocker_classes": ["held_by_manifest", "no_action_hold"],
                "required_proofs": [],
                "required_receipts": ["docs/ops/CHECKPOINT.md"],
                "operator_actions": ["hold until state changes"],
                "reason": "held",
            }
        ],
        "required_proofs": [],
        "required_receipts": ["docs/ops/CHECKPOINT.md"],
        "operator_actions": ["hold until state changes"],
        "owner_lane_boundaries": matrix.OWNER_LANE_BOUNDARIES,
        "playbook_rule_refs": matrix.PLAYBOOK_RULE_REFS,
        "authority_risks": matrix.AUTHORITY_RISKS,
        "recommended_next_selection": None,
        "safe_to_continue": True,
        "blockers": [],
        "branch": "main",
        "head": "abc",
    }


class HeldLaneUnlockMatrixValidatorTests(unittest.TestCase):
    def test_live_matrix_validates(self) -> None:
        report = validator.build_report(root=Path.cwd())
        self.assertEqual(validator.SCHEMA_VERSION, report["schema_version"])
        self.assertEqual(validator.STATUS_VALID, report["status"])
        self.assertTrue(report["safe_to_use"])
        self.assertEqual(matrix.SCHEMA_VERSION, report["matrix_schema"])
        self.assertFalse(report["blockers"])

    def test_advisory_all_held_matrix_validates(self) -> None:
        report = validator.validate_report(root=Path.cwd(), report=_matrix_payload())
        self.assertEqual(validator.STATUS_VALID, report["status"])
        self.assertEqual(0, report["unlockable_count"])
        self.assertIsNone(report["recommended_next_selection"])

    def test_mismatched_candidate_count_blocks(self) -> None:
        payload = _matrix_payload()
        payload["candidate_count"] = 2
        report = validator.validate_report(root=Path.cwd(), report=payload)
        self.assertEqual(validator.STATUS_BLOCKED, report["status"])
        self.assertIn("invalid_matrix_count", [blocker["code"] for blocker in report["blockers"]])

    def test_selection_must_match_unlockable_count(self) -> None:
        payload = _matrix_payload()
        payload["unlockable_count"] = 1
        report = validator.validate_report(root=Path.cwd(), report=payload)
        self.assertEqual(validator.STATUS_BLOCKED, report["status"])
        self.assertIn("invalid_selection_state", [blocker["code"] for blocker in report["blockers"]])

    def test_missing_owner_lane_boundary_blocks(self) -> None:
        payload = _matrix_payload()
        payload["owner_lane_boundaries"] = [item for item in payload["owner_lane_boundaries"] if "Fitness" not in item]
        report = validator.validate_report(root=Path.cwd(), report=payload)
        self.assertEqual(validator.STATUS_BLOCKED, report["status"])
        self.assertIn("missing_owner_lane_boundary", [blocker["code"] for blocker in report["blockers"]])

    def test_input_must_be_tmp_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "docs" / "matrix.json", "{}")
            report = validator.build_report(root=root, input_path="docs/matrix.json")
        self.assertEqual(validator.STATUS_BLOCKED, report["status"])
        self.assertIn("protected_input_path", [blocker["code"] for blocker in report["blockers"]])

    def test_main_validates_tmp_input_and_writes_tmp_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "tmp" / "matrix.json", json.dumps(_matrix_payload(), indent=2) + "\n")
            output_path = root / "tmp" / "validation.json"
            with mock.patch.object(validator, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = validator.main(["--json", "--input", "tmp/matrix.json", "--output", "tmp/validation.json"])
            written = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(0, code)
        self.assertEqual(validator.SCHEMA_VERSION, written["schema_version"])
        self.assertEqual(validator.STATUS_VALID, written["status"])

    def test_main_rejects_protected_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "tmp" / "matrix.json", json.dumps(_matrix_payload(), indent=2) + "\n")
            with mock.patch.object(validator, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = validator.main(["--json", "--input", "tmp/matrix.json", "--output", "docs/validation.json"])

        self.assertEqual(2, code)

    def test_deterministic_top_level_ordering(self) -> None:
        report = validator.validate_report(root=Path.cwd(), report=_matrix_payload())
        self.assertEqual(
            [
                "schema_version",
                "status",
                "matrix_schema",
                "matrix_status",
                "candidate_count",
                "held_count",
                "unlockable_count",
                "recommended_next_selection",
                "field_results",
                "candidate_results",
                "count_results",
                "selection_result",
                "owner_lane_boundary_results",
                "safe_to_use",
                "root",
                "branch",
                "head",
                "input_ref",
                "blockers",
                "warnings",
            ],
            list(report.keys()),
        )


if __name__ == "__main__":
    unittest.main()
