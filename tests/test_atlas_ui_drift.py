from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.atlas.ui_observe.drift import (
    UI_DRIFT_REPORT_CONTRACT_VERSION,
    UI_OBSERVATION_RESIDUE_CONTRACT_VERSION,
    default_drift_schema_path,
    validate_drift_report_payload,
    validate_observation_residue_payload,
    validate_drift_schema_definition,
    validate_fitness_ui_drift,
)
from ops.atlas.ui_observe.fitness import (
    default_capture_map_schema_path,
    default_schema_path,
    observe_fitness_ui,
)
from tests.test_atlas_ui_observe import write_fixture_stack

ROOT = Path(__file__).resolve().parents[1]


class AtlasUiDriftTests(unittest.TestCase):
    def test_default_drift_schema_validates(self) -> None:
        schema = json.loads(default_drift_schema_path(ROOT).read_text(encoding="utf-8"))
        self.assertEqual([], validate_drift_schema_definition(schema))

    def test_default_expected_observation_set_covers_expanded_history_session_workout_card_settings_detail_support_and_chooser_routes(self) -> None:
        report = validate_fitness_ui_drift(
            root=ROOT,
            schema_path=default_drift_schema_path(ROOT),
            observation_schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )

        self.assertEqual(37, report["summary"]["expected_capture_count"])

    def test_validator_is_clean_for_compliant_observations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture_stack(root)
            observe_fitness_ui(
                root=root,
                schema_path=default_schema_path(ROOT),
                capture_map_schema_path=default_capture_map_schema_path(ROOT),
                output_root=root / "runtime" / "atlas" / "ui-observe" / "fitness",
            )

            report = validate_fitness_ui_drift(
                root=root,
                observation_root=root / "runtime" / "atlas" / "ui-observe" / "fitness",
                report_root=root / "runtime" / "atlas" / "ui-observe" / "drift" / "fitness",
                schema_path=default_drift_schema_path(ROOT),
                observation_schema_path=default_schema_path(ROOT),
                capture_map_schema_path=default_capture_map_schema_path(ROOT),
                dry_run=True,
            )

            self.assertEqual(UI_DRIFT_REPORT_CONTRACT_VERSION, report["contract_version"])
            self.assertEqual([], validate_drift_report_payload(report))
            self.assertEqual("clean", report["summary"]["status"])
            self.assertEqual(0, report["summary"]["finding_count"])

    def test_validator_detects_seeded_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture_stack(root)
            observe_fitness_ui(
                root=root,
                schema_path=default_schema_path(ROOT),
                capture_map_schema_path=default_capture_map_schema_path(ROOT),
                output_root=root / "runtime" / "atlas" / "ui-observe" / "fitness",
            )

            latest_path = (
                root
                / "runtime"
                / "atlas"
                / "ui-observe"
                / "fitness"
                / "today-overview-default"
                / "latest.json"
            )
            payload = json.loads(latest_path.read_text(encoding="utf-8"))
            payload["traits"]["section_layout"]["variant_id"] = "drifted"
            payload["traits"]["section_layout"]["token_refs"] = ["spacing.99"]
            latest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

            report = validate_fitness_ui_drift(
                root=root,
                observation_root=root / "runtime" / "atlas" / "ui-observe" / "fitness",
                report_root=root / "runtime" / "atlas" / "ui-observe" / "drift" / "fitness",
                schema_path=default_drift_schema_path(ROOT),
                observation_schema_path=default_schema_path(ROOT),
                capture_map_schema_path=default_capture_map_schema_path(ROOT),
                dry_run=True,
            )

            self.assertEqual("drift_detected", report["summary"]["status"])
            self.assertGreater(report["summary"]["finding_count"], 0)
            self.assertTrue(any(item["dimension"] == "section_layout" for item in report["findings"]))

    def test_superseded_residue_is_retained_without_counting_as_active_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture_stack(root)
            observe_fitness_ui(
                root=root,
                schema_path=default_schema_path(ROOT),
                capture_map_schema_path=default_capture_map_schema_path(ROOT),
                output_root=root / "runtime" / "atlas" / "ui-observe" / "fitness",
            )

            stale_root = root / "runtime" / "atlas" / "ui-observe" / "fitness" / "exercise-log-active"
            stale_root.mkdir(parents=True)
            stale_payload = json.loads(
                (
                    root
                    / "runtime"
                    / "atlas"
                    / "ui-observe"
                    / "fitness"
                    / "today-overview-default"
                    / "latest.json"
                ).read_text(encoding="utf-8")
            )
            stale_payload["comparison_key"] = "fitness:exercise-log-active"
            stale_payload["capture"]["capture_id"] = "exercise-log-active"
            stale_payload["capture"]["screen_key"] = "exerciseLog"
            stale_payload["capture"]["screen_label"] = "Exercise log"
            stale_payload["capture"]["state_key"] = "active"
            stale_payload["capture"]["state_label"] = "Active session"
            (stale_root / "latest.json").write_text(json.dumps(stale_payload, indent=2) + "\n", encoding="utf-8")

            residue_marker = {
                "contract_version": UI_OBSERVATION_RESIDUE_CONTRACT_VERSION,
                "capture_id": "exercise-log-active",
                "status": "superseded_residue",
                "reason": "Split into explicit workout-entry capture coverage.",
                "superseded_by": [
                    "exercise-log-session-header-card",
                    "exercise-log-entry-section",
                    "exercise-log-form-section-card",
                    "exercise-log-compact-row",
                    "exercise-log-sticky-footer",
                ],
                "recorded_at": "2026-04-21T02:30:00Z",
            }
            self.assertEqual([], validate_observation_residue_payload(residue_marker, capture_id="exercise-log-active"))
            (stale_root / "residue.json").write_text(json.dumps(residue_marker, indent=2) + "\n", encoding="utf-8")

            report = validate_fitness_ui_drift(
                root=root,
                observation_root=root / "runtime" / "atlas" / "ui-observe" / "fitness",
                report_root=root / "runtime" / "atlas" / "ui-observe" / "drift" / "fitness",
                schema_path=default_drift_schema_path(ROOT),
                observation_schema_path=default_schema_path(ROOT),
                capture_map_schema_path=default_capture_map_schema_path(ROOT),
                dry_run=True,
            )

            self.assertEqual("clean", report["summary"]["status"])
            self.assertEqual(1, report["summary"]["expected_capture_count"])
            self.assertEqual(1, report["summary"]["observed_capture_count"])
            self.assertEqual(0, report["summary"]["finding_count"])


if __name__ == "__main__":
    unittest.main()
