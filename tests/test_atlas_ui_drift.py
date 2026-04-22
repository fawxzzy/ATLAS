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

    def test_default_expected_observation_set_covers_expanded_history_log_audit_workout_card_settings_detail_support_chooser_auth_entry_and_curated_routes(self) -> None:
        report = validate_fitness_ui_drift(
            root=ROOT,
            schema_path=default_drift_schema_path(ROOT),
            observation_schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )

        self.assertEqual(59, report["summary"]["expected_capture_count"])

    def test_dry_run_keeps_exercise_discovery_and_detail_on_existing_validator_lane(self) -> None:
        report = validate_fitness_ui_drift(
            root=ROOT,
            schema_path=default_drift_schema_path(ROOT),
            observation_schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )
        expected = observe_fitness_ui(
            root=ROOT,
            schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )

        comparison_keys = {item["comparison_key"] for item in expected["observations"]}

        self.assertIn("fitness:history-exercises-default", comparison_keys)
        self.assertIn("fitness:detail-support-exercise-info-sheet", comparison_keys)
        self.assertFalse(any(key.startswith("fitness:exercise-detail-") for key in comparison_keys))
        self.assertEqual(len(comparison_keys), report["summary"]["expected_capture_count"])
        self.assertEqual("clean", report["summary"]["status"])
        self.assertEqual(0, report["summary"]["finding_count"])

    def test_dry_run_keeps_chooser_family_on_existing_validator_lane(self) -> None:
        report = validate_fitness_ui_drift(
            root=ROOT,
            schema_path=default_drift_schema_path(ROOT),
            observation_schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )
        expected = observe_fitness_ui(
            root=ROOT,
            schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )

        comparison_keys = {item["comparison_key"] for item in expected["observations"]}

        for comparison_key in {
            "fitness:exercise-chooser-picker",
            "fitness:exercise-chooser-tag-filter-control",
            "fitness:exercise-chooser-search-filters",
            "fitness:exercise-chooser-picker-panel",
            "fitness:exercise-chooser-filter-panel",
            "fitness:exercise-chooser-goal-panel",
        }:
            self.assertIn(comparison_key, comparison_keys)

        self.assertFalse(any(key.startswith("fitness:exercise-picker-") for key in comparison_keys))
        self.assertFalse(any(key.startswith("fitness:exercise-search-filters-") for key in comparison_keys))
        self.assertFalse(any(key.startswith("fitness:picker-list-viewport-") for key in comparison_keys))
        self.assertFalse(any(key.startswith("fitness:chooser-panel-") for key in comparison_keys))
        self.assertFalse(any(key.startswith("fitness:filter-shell-") for key in comparison_keys))
        self.assertEqual(len(comparison_keys), report["summary"]["expected_capture_count"])
        self.assertEqual("clean", report["summary"]["status"])
        self.assertEqual(0, report["summary"]["finding_count"])

    def test_dry_run_keeps_auth_recovery_family_on_existing_validator_lane(self) -> None:
        report = validate_fitness_ui_drift(
            root=ROOT,
            schema_path=default_drift_schema_path(ROOT),
            observation_schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )
        expected = observe_fitness_ui(
            root=ROOT,
            schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )

        comparison_keys = {item["comparison_key"] for item in expected["observations"]}

        for comparison_key in {
            "fitness:auth-recovery-shell",
            "fitness:auth-recovery-login-screen",
            "fitness:auth-recovery-signup-form",
            "fitness:auth-recovery-forgot-password-form",
            "fitness:auth-recovery-reset-password-form",
            "fitness:auth-recovery-recovery-bridge",
            "fitness:auth-recovery-message-chrome",
            "fitness:auth-recovery-account-panel",
            "fitness:auth-recovery-action-chrome",
        }:
            self.assertIn(comparison_key, comparison_keys)

        self.assertFalse(any(key.startswith("fitness:auth-footer-") for key in comparison_keys))
        self.assertFalse(any(key.startswith("fitness:auth-message-") for key in comparison_keys))
        self.assertFalse(any(key.startswith("fitness:auth-account-") for key in comparison_keys))
        self.assertFalse(any(key.startswith("fitness:auth-action-") for key in comparison_keys))
        self.assertFalse(any(key.startswith("fitness:remembered-login-") for key in comparison_keys))
        self.assertFalse(any(key.startswith("fitness:login-state-") for key in comparison_keys))
        self.assertEqual(len(comparison_keys), report["summary"]["expected_capture_count"])
        self.assertEqual("clean", report["summary"]["status"])
        self.assertEqual(0, report["summary"]["finding_count"])

    def test_dry_run_keeps_today_overview_token_bridge_on_existing_validator_lane(self) -> None:
        report = validate_fitness_ui_drift(
            root=ROOT,
            schema_path=default_drift_schema_path(ROOT),
            observation_schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )
        expected = observe_fitness_ui(
            root=ROOT,
            schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )

        comparison_keys = {item["comparison_key"] for item in expected["observations"]}

        self.assertIn("fitness:today-overview-default", comparison_keys)
        self.assertFalse(any(key.startswith("fitness:today-list-") for key in comparison_keys))
        self.assertFalse(any(key.startswith("fitness:today-feedback-") for key in comparison_keys))
        self.assertEqual(len(comparison_keys), report["summary"]["expected_capture_count"])
        self.assertEqual("clean", report["summary"]["status"])
        self.assertEqual(0, report["summary"]["finding_count"])

    def test_dry_run_keeps_shared_history_family_on_existing_validator_lane(self) -> None:
        report = validate_fitness_ui_drift(
            root=ROOT,
            schema_path=default_drift_schema_path(ROOT),
            observation_schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )
        expected = observe_fitness_ui(
            root=ROOT,
            schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )

        comparison_keys = {item["comparison_key"] for item in expected["observations"]}

        for comparison_key in {
            "fitness:history-overview-default",
            "fitness:history-exercises-default",
            "fitness:history-sessions-list-default",
            "fitness:history-log-detail-surface",
            "fitness:history-log-edit-mode-header-panel",
            "fitness:history-log-note-empty-state-chrome",
        }:
            self.assertIn(comparison_key, comparison_keys)

        self.assertFalse(any(key.startswith("fitness:history-shared-") for key in comparison_keys))
        self.assertFalse(any(key.startswith("fitness:history-control-") for key in comparison_keys))
        self.assertEqual(len(comparison_keys), report["summary"]["expected_capture_count"])
        self.assertEqual("clean", report["summary"]["status"])
        self.assertEqual(0, report["summary"]["finding_count"])

    def test_dry_run_keeps_route_loading_family_on_existing_route_and_entry_lanes(self) -> None:
        report = validate_fitness_ui_drift(
            root=ROOT,
            schema_path=default_drift_schema_path(ROOT),
            observation_schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )
        expected = observe_fitness_ui(
            root=ROOT,
            schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )

        comparison_keys = {item["comparison_key"] for item in expected["observations"]}

        for comparison_key in {
            "fitness:today-overview-default",
            "fitness:routines-overview-default",
            "fitness:routines-overview-selected-routine",
            "fitness:settings-overview-default",
            "fitness:entry-handoff-card",
            "fitness:entry-handoff-status-panel",
            "fitness:history-overview-default",
            "fitness:history-exercises-default",
            "fitness:history-sessions-list-default",
            "fitness:history-log-detail-surface",
        }:
            self.assertIn(comparison_key, comparison_keys)

        self.assertFalse(any(key.startswith("fitness:route-loading-") for key in comparison_keys))
        self.assertFalse(any(key.startswith("fitness:boot-loading-") for key in comparison_keys))
        self.assertEqual(len(comparison_keys), report["summary"]["expected_capture_count"])
        self.assertEqual("clean", report["summary"]["status"])
        self.assertEqual(0, report["summary"]["finding_count"])

    def test_dry_run_keeps_routine_editor_detail_family_on_existing_editor_lanes(self) -> None:
        report = validate_fitness_ui_drift(
            root=ROOT,
            schema_path=default_drift_schema_path(ROOT),
            observation_schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )
        expected = observe_fitness_ui(
            root=ROOT,
            schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )

        comparison_keys = {item["comparison_key"] for item in expected["observations"]}

        for comparison_key in {
            "fitness:edit-day-default",
            "fitness:edit-routine-days-section-default",
            "fitness:edit-day-add-exercise-default",
        }:
            self.assertIn(comparison_key, comparison_keys)

        self.assertFalse(any(key.startswith("fitness:routine-editor-") for key in comparison_keys))
        self.assertFalse(any(key.startswith("fitness:routine-detail-") for key in comparison_keys))
        self.assertEqual(len(comparison_keys), report["summary"]["expected_capture_count"])
        self.assertEqual("clean", report["summary"]["status"])
        self.assertEqual(0, report["summary"]["finding_count"])

    def test_dry_run_keeps_session_log_set_family_on_existing_session_and_workout_lanes(self) -> None:
        report = validate_fitness_ui_drift(
            root=ROOT,
            schema_path=default_drift_schema_path(ROOT),
            observation_schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )
        expected = observe_fitness_ui(
            root=ROOT,
            schema_path=default_schema_path(ROOT),
            capture_map_schema_path=default_capture_map_schema_path(ROOT),
            dry_run=True,
        )

        comparison_keys = {item["comparison_key"] for item in expected["observations"]}

        for comparison_key in {
            "fitness:exercise-log-session-header-card",
            "fitness:exercise-log-entry-section",
            "fitness:exercise-log-compact-row",
            "fitness:exercise-log-sticky-footer",
            "fitness:workout-card-disclosure-expanded",
        }:
            self.assertIn(comparison_key, comparison_keys)

        self.assertNotIn("fitness:exercise-log-active", comparison_keys)
        self.assertFalse(any(key.startswith("fitness:active-session-") for key in comparison_keys))
        self.assertFalse(any(key.startswith("fitness:session-log-") for key in comparison_keys))
        self.assertFalse(any(key.startswith("fitness:log-set-") for key in comparison_keys))
        self.assertFalse(any(key.startswith("fitness:session-timer-") for key in comparison_keys))
        self.assertEqual(len(comparison_keys), report["summary"]["expected_capture_count"])
        self.assertEqual("clean", report["summary"]["status"])
        self.assertEqual(0, report["summary"]["finding_count"])

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
