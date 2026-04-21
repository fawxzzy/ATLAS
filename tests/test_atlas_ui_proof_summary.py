from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from ops.atlas.ui_proof.fitness import (
    UI_PROOF_SUMMARY_CONTRACT_VERSION,
    default_schema_path,
    derive_ui_proof_summary,
    validate_schema_definition,
    validate_ui_proof_summary_payload,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _fixture_root(root: Path) -> tuple[Path, Path]:
    drift_path = root / "runtime" / "atlas" / "ui-observe" / "drift" / "fitness" / "latest.json"
    visual_path = root / "runtime" / "atlas" / "ui-visual-proof" / "fitness" / "latest.json"
    return drift_path, visual_path


class AtlasUiProofSummaryTests(unittest.TestCase):
    def test_schema_definition_is_valid(self) -> None:
        schema = json.loads(default_schema_path(ROOT).read_text(encoding="utf-8"))
        self.assertEqual([], validate_schema_definition(schema))

    def test_combined_summary_is_ready_when_both_proof_lanes_are_clean(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            drift_path, visual_path = _fixture_root(root)
            _write_json(
                drift_path,
                {
                    "contract_version": "atlas.ui.drift.report.v1",
                    "report_id": "sha256:" + ("1" * 64),
                    "generated_at": "2026-04-21T12:00:00Z",
                    "owner_repo_id": "fitness",
                    "owner_contract_refs": {},
                    "capture_map_ref": "ops/atlas/ui_observe/fitness_capture_map.v1.json",
                    "summary": {
                        "status": "clean",
                        "expected_capture_count": 46,
                        "observed_capture_count": 46,
                        "finding_count": 0,
                        "mismatch_count": 0,
                        "missing_count": 0,
                        "unexpected_count": 0
                    },
                    "findings": [],
                    "operator_summary": ["No UI drift detected across 46 captures."]
                },
            )
            _write_json(
                visual_path,
                {
                    "contract_version": "atlas.ui.visual-proof.report.v1",
                    "report_id": "sha256:" + ("2" * 64),
                    "generated_at": "2026-04-21T12:01:00Z",
                    "runner_version": "atlas.ui.visual-proof.fitness.v1",
                    "owner_repo_id": "fitness",
                    "manifest_ref": "ops/atlas/ui_visual_proof/fitness_visual_proof.v1.json",
                    "capture_map_ref": "ops/atlas/ui_observe/fitness_capture_map.v1.json",
                    "summary": {
                        "status": "clean",
                        "capture_count": 2,
                        "passing_count": 2,
                        "failing_count": 0
                    },
                    "results": [
                        {"capture_id": "settings-overview-default", "status": "pass"},
                        {"capture_id": "today-overview-default", "status": "pass"}
                    ],
                    "operator_summary": ["Visual proof passed across 2 captures."]
                },
            )

            report = derive_ui_proof_summary(root=root, schema_path=default_schema_path(ROOT), dry_run=True)
            self.assertEqual(UI_PROOF_SUMMARY_CONTRACT_VERSION, report["contract_version"])
            self.assertEqual([], validate_ui_proof_summary_payload(report))
            self.assertTrue(report["completion_ready"])
            self.assertEqual("completion_ready", report["summary"]["status"])
            self.assertEqual(2, report["summary"]["gated_capture_count"])

    def test_missing_visual_report_blocks_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            drift_path, _ = _fixture_root(root)
            _write_json(
                drift_path,
                {
                    "contract_version": "atlas.ui.drift.report.v1",
                    "report_id": "sha256:" + ("3" * 64),
                    "generated_at": "2026-04-21T12:00:00Z",
                    "owner_repo_id": "fitness",
                    "owner_contract_refs": {},
                    "capture_map_ref": "ops/atlas/ui_observe/fitness_capture_map.v1.json",
                    "summary": {
                        "status": "clean",
                        "expected_capture_count": 46,
                        "observed_capture_count": 46,
                        "finding_count": 0,
                        "mismatch_count": 0,
                        "missing_count": 0,
                        "unexpected_count": 0
                    },
                    "findings": [],
                    "operator_summary": ["No UI drift detected across 46 captures."]
                },
            )

            report = derive_ui_proof_summary(root=root, schema_path=default_schema_path(ROOT), dry_run=True)
            self.assertFalse(report["completion_ready"])
            self.assertEqual("missing_report", report["summary"]["visual_status"])
            self.assertTrue(any("missing" in item.lower() for item in report["blocking_reasons"]))

    def test_visual_zero_capture_report_blocks_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            drift_path, visual_path = _fixture_root(root)
            _write_json(
                drift_path,
                {
                    "contract_version": "atlas.ui.drift.report.v1",
                    "report_id": "sha256:" + ("4" * 64),
                    "generated_at": "2026-04-21T12:00:00Z",
                    "owner_repo_id": "fitness",
                    "owner_contract_refs": {},
                    "capture_map_ref": "ops/atlas/ui_observe/fitness_capture_map.v1.json",
                    "summary": {
                        "status": "clean",
                        "expected_capture_count": 46,
                        "observed_capture_count": 46,
                        "finding_count": 0,
                        "mismatch_count": 0,
                        "missing_count": 0,
                        "unexpected_count": 0
                    },
                    "findings": [],
                    "operator_summary": ["No UI drift detected across 46 captures."]
                },
            )
            _write_json(
                visual_path,
                {
                    "contract_version": "atlas.ui.visual-proof.report.v1",
                    "report_id": "sha256:" + ("5" * 64),
                    "generated_at": "2026-04-21T12:01:00Z",
                    "runner_version": "atlas.ui.visual-proof.fitness.v1",
                    "owner_repo_id": "fitness",
                    "manifest_ref": "ops/atlas/ui_visual_proof/fitness_visual_proof.v1.json",
                    "capture_map_ref": "ops/atlas/ui_observe/fitness_capture_map.v1.json",
                    "summary": {
                        "status": "clean",
                        "capture_count": 0,
                        "passing_count": 0,
                        "failing_count": 0
                    },
                    "results": [],
                    "operator_summary": ["Visual proof passed across 0 captures."]
                },
            )

            report = derive_ui_proof_summary(root=root, schema_path=default_schema_path(ROOT), dry_run=True)
            self.assertFalse(report["completion_ready"])
            self.assertTrue(any("zero gated captures" in item.lower() for item in report["blocking_reasons"]))

    def test_drift_and_visual_failures_are_projected_into_failed_capture_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            drift_path, visual_path = _fixture_root(root)
            _write_json(
                drift_path,
                {
                    "contract_version": "atlas.ui.drift.report.v1",
                    "report_id": "sha256:" + ("6" * 64),
                    "generated_at": "2026-04-21T12:00:00Z",
                    "owner_repo_id": "fitness",
                    "owner_contract_refs": {},
                    "capture_map_ref": "ops/atlas/ui_observe/fitness_capture_map.v1.json",
                    "summary": {
                        "status": "drift_detected",
                        "expected_capture_count": 46,
                        "observed_capture_count": 46,
                        "finding_count": 1,
                        "mismatch_count": 1,
                        "missing_count": 0,
                        "unexpected_count": 0
                    },
                    "findings": [
                        {
                            "finding_id": "sha256:" + ("7" * 64),
                            "kind": "trait_drift",
                            "severity": "warning",
                            "comparison_key": "fitness:today",
                            "capture_id": "today-overview-default",
                            "message": "Observed layout drifted."
                        }
                    ],
                    "operator_summary": ["UI drift detected."]
                },
            )
            _write_json(
                visual_path,
                {
                    "contract_version": "atlas.ui.visual-proof.report.v1",
                    "report_id": "sha256:" + ("8" * 64),
                    "generated_at": "2026-04-21T12:01:00Z",
                    "runner_version": "atlas.ui.visual-proof.fitness.v1",
                    "owner_repo_id": "fitness",
                    "manifest_ref": "ops/atlas/ui_visual_proof/fitness_visual_proof.v1.json",
                    "capture_map_ref": "ops/atlas/ui_observe/fitness_capture_map.v1.json",
                    "summary": {
                        "status": "proof_failed",
                        "capture_count": 2,
                        "passing_count": 1,
                        "failing_count": 1
                    },
                    "results": [
                        {"capture_id": "settings-overview-default", "status": "pass"},
                        {"capture_id": "today-overview-default", "status": "fail"}
                    ],
                    "operator_summary": ["Visual proof failed."]
                },
            )

            report = derive_ui_proof_summary(root=root, schema_path=default_schema_path(ROOT), dry_run=True)
            self.assertFalse(report["completion_ready"])
            self.assertEqual(["today-overview-default"], report["failed_capture_ids"])
            self.assertEqual("drift_detected", report["summary"]["semantic_status"])
            self.assertEqual("proof_failed", report["summary"]["visual_status"])

    def test_cli_exits_non_zero_when_proof_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            completed = subprocess.run(
                [
                    "python",
                    str(ROOT / "ops" / "atlas" / "ui_proof" / "fitness.py"),
                    "--root",
                    str(root),
                    "--schema-file",
                    str(default_schema_path(ROOT))
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, completed.returncode)


if __name__ == "__main__":
    unittest.main()
