from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.atlas.ui_observe.fitness import (
    UI_CAPTURE_INPUTS_CONTRACT_VERSION,
    UI_CAPTURE_MAP_CONTRACT_VERSION,
    UI_OBSERVATION_CONTRACT_VERSION,
    default_capture_inputs_path,
    default_capture_map_path,
    default_capture_map_schema_path,
    default_schema_path,
    observe_fitness_ui,
    validate_capture_inputs,
    validate_capture_map,
    validate_capture_map_contract_bindings,
    validate_capture_map_schema_definition,
    validate_observation_payload,
    validate_schema_definition,
)

ROOT = Path(__file__).resolve().parents[1]


def write_fixture_stack(root: Path) -> tuple[Path, Path, Path]:
    design_root = root / "repos" / "fawxzzy-fitness" / "truth-pack" / "fitness" / "design-system"
    app_root = root / "repos" / "fawxzzy-fitness" / "src" / "components" / "ui" / "app"
    design_root.mkdir(parents=True)
    app_root.mkdir(parents=True)
    (root / "ops" / "atlas" / "ui_observe").mkdir(parents=True)
    (root / "runtime").mkdir(parents=True)

    for name in ("AppHeader.tsx", "AppPanel.tsx", "AppBadge.tsx", "SharedSectionShell.tsx"):
        (app_root / name).write_text("// fixture\n", encoding="utf-8")

    tokens = {
        "packId": "fitness.design-system.tokens",
        "packVersion": "v1",
        "status": "frozen",
        "ownerRepoId": "fawxzzy-fitness",
        "tokenGroups": {
            "spacing": {"0": "0rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem"},
            "typography": {"title": "title", "subtitle": "subtitle", "badge": "badge"},
            "colors": {
                "background": {"card": "card"},
                "surface": {"3": "surface-3"},
                "text": {"primary": "primary", "secondary": "secondary", "muted": "muted"},
                "accent": {"base": "accent"},
                "border": {"strong": "border-strong"}
            },
            "radii": {"lg": "1.5rem", "pill": "999px", "xl": "1.875rem"},
            "shadows": {"glassBase": "shadow", "glassRaised": "shadow-raised"},
            "borders": {"strong": "border-strong"}
        }
    }
    primitives = {
        "packId": "fitness.design-system.primitives",
        "packVersion": "v1",
        "status": "frozen",
        "ownerRepoId": "fawxzzy-fitness",
        "tokensPackRef": "truth-pack/fitness/design-system/tokens.v1.json",
        "primitiveContracts": [
            {
                "id": "header",
                "variants": [
                    {
                        "id": "shared",
                        "semanticRefs": {
                            "horizontalPadding": "spacing.4",
                            "title": "typography.title",
                            "subtitle": "typography.subtitle",
                            "textPrimary": "colors.text.primary"
                        }
                    },
                    {
                        "id": "standalone",
                        "semanticRefs": {
                            "panelRadius": "radii.xl",
                            "panelShadow": "shadows.glassRaised",
                            "panelPaddingX": "spacing.4"
                        }
                    }
                ]
            },
            {
                "id": "card",
                "variants": [
                    {
                        "id": "panel",
                        "semanticRefs": {
                            "radius": "radii.lg",
                            "shadow": "shadows.glassBase",
                            "surface": "colors.background.card",
                            "border": "colors.border.strong",
                            "padding": "spacing.4"
                        }
                    }
                ]
            },
            {
                "id": "badge",
                "variants": [
                    {
                        "id": "default",
                        "semanticRefs": {
                            "radius": "radii.pill",
                            "text": "typography.badge",
                            "surface": "colors.surface.3",
                            "border": "colors.border.strong"
                        }
                    },
                    {
                        "id": "today",
                        "semanticRefs": {
                            "surface": "colors.accent.base"
                        }
                    }
                ]
            },
            {
                "id": "section-layout",
                "variants": [
                    {
                        "id": "dense",
                        "semanticRefs": {
                            "headerRow": "spacing.3",
                            "shellPadding": "spacing.0",
                            "bodyGap": "spacing.2"
                        }
                    },
                    {
                        "id": "standard",
                        "semanticRefs": {
                            "headerRow": "spacing.3",
                            "shellPadding": "spacing.4",
                            "bodyGap": "spacing.3"
                        }
                    }
                ]
            }
        ]
    }
    capture_map = {
        "contract_version": UI_CAPTURE_MAP_CONTRACT_VERSION,
        "owner_repo_id": "fitness",
        "owner_repo_path": "repos/fawxzzy-fitness",
        "captures": [
            {
                "capture_id": "today-overview-default",
                "screen_key": "todayOverview",
                "screen_label": "Today overview",
                "state_key": "default",
                "state_label": "Default",
                "route_family": "overview",
                "owner_surface_refs": [
                    "repos/fawxzzy-fitness/src/components/ui/app/AppHeader.tsx",
                    "repos/fawxzzy-fitness/src/components/ui/app/AppPanel.tsx",
                    "repos/fawxzzy-fitness/src/components/ui/app/AppBadge.tsx",
                    "repos/fawxzzy-fitness/src/components/ui/app/SharedSectionShell.tsx"
                ],
                "primitive_variants": {
                    "header": {"primitive_id": "header", "variant_id": "shared"},
                    "card": {"primitive_id": "card", "variant_id": "panel"},
                    "tag": {"primitive_id": "badge", "variant_id": "today"},
                    "section_layout": {"primitive_id": "section-layout", "variant_id": "dense"}
                }
            }
        ]
    }
    inputs = {
        "contract_version": UI_CAPTURE_INPUTS_CONTRACT_VERSION,
        "owner_repo_id": "fitness",
        "owner_repo_path": "repos/fawxzzy-fitness",
        "owner_contract_refs": {
            "tokens_ref": "repos/fawxzzy-fitness/truth-pack/fitness/design-system/tokens.v1.json",
            "primitives_ref": "repos/fawxzzy-fitness/truth-pack/fitness/design-system/primitives.v1.json"
        },
        "capture_map_ref": "ops/atlas/ui_observe/fitness_capture_map.v1.json",
        "capture_set": [
            {"screen_key": "todayOverview", "state_key": "default"}
        ]
    }

    tokens_path = design_root / "tokens.v1.json"
    primitives_path = design_root / "primitives.v1.json"
    capture_map_path = root / "ops" / "atlas" / "ui_observe" / "fitness_capture_map.v1.json"
    inputs_path = root / "ops" / "atlas" / "ui_observe" / "fitness_capture_inputs.v1.json"
    tokens_path.write_text(json.dumps(tokens, indent=2) + "\n", encoding="utf-8")
    primitives_path.write_text(json.dumps(primitives, indent=2) + "\n", encoding="utf-8")
    capture_map_path.write_text(json.dumps(capture_map, indent=2) + "\n", encoding="utf-8")
    inputs_path.write_text(json.dumps(inputs, indent=2) + "\n", encoding="utf-8")
    return tokens_path, primitives_path, capture_map_path


class AtlasUiObservationTests(unittest.TestCase):
    def test_default_contracts_validate(self) -> None:
        schema = json.loads(default_schema_path(ROOT).read_text(encoding="utf-8"))
        mapping_schema = json.loads(default_capture_map_schema_path(ROOT).read_text(encoding="utf-8"))
        inputs = json.loads(default_capture_inputs_path(ROOT).read_text(encoding="utf-8"))
        capture_map = json.loads(default_capture_map_path(ROOT).read_text(encoding="utf-8"))
        primitives = json.loads(
            (ROOT / "repos" / "fawxzzy-fitness" / "truth-pack" / "fitness" / "design-system" / "primitives.v1.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual([], validate_schema_definition(schema))
        self.assertEqual([], validate_capture_map_schema_definition(mapping_schema))
        self.assertEqual([], validate_capture_inputs(inputs, root=ROOT))
        self.assertEqual([], validate_capture_map(capture_map, root=ROOT))
        self.assertEqual([], validate_capture_map_contract_bindings(capture_map, primitives))

    def test_default_capture_set_covers_today_d2_history_session_workout_card_settings_detail_support_chooser_auth_entry_and_curated_families(self) -> None:
        inputs = json.loads(default_capture_inputs_path(ROOT).read_text(encoding="utf-8"))
        capture_map = json.loads(default_capture_map_path(ROOT).read_text(encoding="utf-8"))

        selectors = {(item["screen_key"], item["state_key"]) for item in inputs["capture_set"]}
        capture_ids_by_selector = {
            (item["screen_key"], item["state_key"]): item["capture_id"]
            for item in capture_map["captures"]
        }

        expected_selectors = {
            ("todayOverview", "default"),
            ("routinesOverview", "default"),
            ("routinesOverview", "selectedRoutine"),
            ("exerciseLog", "sessionHeaderCard"),
            ("exerciseLog", "entrySection"),
            ("exerciseLog", "formSectionCard"),
            ("exerciseLog", "compactLogRow"),
            ("exerciseLog", "stickyFooter"),
            ("workoutCard", "exerciseCard"),
            ("workoutCard", "disclosureExpanded"),
            ("workoutCard", "chipRow"),
            ("workoutCard", "exerciseDetails"),
            ("workoutCard", "metricItem"),
            ("workoutCard", "sessionSummaryCard"),
            ("settings", "overview"),
            ("settings", "accountForm"),
            ("settings", "glassEffects"),
            ("settings", "legacyMigrationRow"),
            ("settings", "legacyMigrationPanel"),
            ("detailSupport", "detailSurface"),
            ("detailSupport", "dayStateCard"),
            ("detailSupport", "exerciseInfoSheet"),
            ("detailSupport", "mediaCard"),
            ("detailSupport", "historyRow"),
            ("exerciseChooser", "picker"),
            ("exerciseChooser", "tagFilterControl"),
            ("exerciseChooser", "searchFilters"),
            ("exerciseChooser", "pickerPanel"),
            ("exerciseChooser", "filterPanel"),
            ("exerciseChooser", "goalPanel"),
            ("authRecovery", "shell"),
            ("authRecovery", "login"),
            ("authRecovery", "signup"),
            ("authRecovery", "forgotPassword"),
            ("authRecovery", "resetPassword"),
            ("authRecovery", "recoveryBridge"),
            ("authRecovery", "messageChrome"),
            ("authRecovery", "accountChrome"),
            ("authRecovery", "actionChrome"),
            ("entryHandoff", "card"),
            ("entryHandoff", "statusPanel"),
            ("entryHandoff", "stageList"),
            ("entryHandoff", "installManualPanel"),
            ("curatedOnboarding", "shell"),
            ("curatedOnboarding", "progress"),
            ("curatedOnboarding", "optionCard"),
            ("curatedOnboarding", "review"),
            ("curatedOnboarding", "handoff"),
            ("editDay", "default"),
            ("editRoutine", "daysSection"),
            ("editDayAddExercise", "default"),
            ("historyOverview", "default"),
            ("historyExercises", "default"),
            ("historySessions", "default"),
            ("historyLog", "default"),
        }

        self.assertEqual(expected_selectors, selectors)
        self.assertEqual(
            "routines-overview-selected-routine",
            capture_ids_by_selector[("routinesOverview", "selectedRoutine")],
        )
        self.assertEqual(
            "edit-routine-days-section-default",
            capture_ids_by_selector[("editRoutine", "daysSection")],
        )
        self.assertEqual(
            "edit-day-add-exercise-default",
            capture_ids_by_selector[("editDayAddExercise", "default")],
        )
        self.assertEqual(
            "exercise-log-session-header-card",
            capture_ids_by_selector[("exerciseLog", "sessionHeaderCard")],
        )
        self.assertEqual(
            "exercise-log-entry-section",
            capture_ids_by_selector[("exerciseLog", "entrySection")],
        )
        self.assertEqual(
            "exercise-log-form-section-card",
            capture_ids_by_selector[("exerciseLog", "formSectionCard")],
        )
        self.assertEqual(
            "exercise-log-compact-row",
            capture_ids_by_selector[("exerciseLog", "compactLogRow")],
        )
        self.assertEqual(
            "exercise-log-sticky-footer",
            capture_ids_by_selector[("exerciseLog", "stickyFooter")],
        )
        self.assertEqual(
            "workout-card-exercise-card",
            capture_ids_by_selector[("workoutCard", "exerciseCard")],
        )
        self.assertEqual(
            "workout-card-disclosure-expanded",
            capture_ids_by_selector[("workoutCard", "disclosureExpanded")],
        )
        self.assertEqual(
            "workout-card-chip-row",
            capture_ids_by_selector[("workoutCard", "chipRow")],
        )
        self.assertEqual(
            "workout-card-exercise-details",
            capture_ids_by_selector[("workoutCard", "exerciseDetails")],
        )
        self.assertEqual(
            "workout-card-metric-item",
            capture_ids_by_selector[("workoutCard", "metricItem")],
        )
        self.assertEqual(
            "workout-card-session-summary-card",
            capture_ids_by_selector[("workoutCard", "sessionSummaryCard")],
        )
        self.assertEqual(
            "settings-overview-default",
            capture_ids_by_selector[("settings", "overview")],
        )
        self.assertEqual(
            "settings-account-form",
            capture_ids_by_selector[("settings", "accountForm")],
        )
        self.assertEqual(
            "settings-glass-effects",
            capture_ids_by_selector[("settings", "glassEffects")],
        )
        self.assertEqual(
            "settings-legacy-migration-row",
            capture_ids_by_selector[("settings", "legacyMigrationRow")],
        )
        self.assertEqual(
            "settings-legacy-migration-panel",
            capture_ids_by_selector[("settings", "legacyMigrationPanel")],
        )
        self.assertEqual(
            "detail-support-surface",
            capture_ids_by_selector[("detailSupport", "detailSurface")],
        )
        self.assertEqual(
            "detail-support-day-state-card",
            capture_ids_by_selector[("detailSupport", "dayStateCard")],
        )
        self.assertEqual(
            "detail-support-exercise-info-sheet",
            capture_ids_by_selector[("detailSupport", "exerciseInfoSheet")],
        )
        self.assertEqual(
            "detail-support-media-card",
            capture_ids_by_selector[("detailSupport", "mediaCard")],
        )
        self.assertEqual(
            "detail-support-history-row",
            capture_ids_by_selector[("detailSupport", "historyRow")],
        )
        self.assertEqual(
            "exercise-chooser-picker",
            capture_ids_by_selector[("exerciseChooser", "picker")],
        )
        self.assertEqual(
            "exercise-chooser-tag-filter-control",
            capture_ids_by_selector[("exerciseChooser", "tagFilterControl")],
        )
        self.assertEqual(
            "exercise-chooser-search-filters",
            capture_ids_by_selector[("exerciseChooser", "searchFilters")],
        )
        self.assertEqual(
            "exercise-chooser-picker-panel",
            capture_ids_by_selector[("exerciseChooser", "pickerPanel")],
        )
        self.assertEqual(
            "exercise-chooser-filter-panel",
            capture_ids_by_selector[("exerciseChooser", "filterPanel")],
        )
        self.assertEqual(
            "exercise-chooser-goal-panel",
            capture_ids_by_selector[("exerciseChooser", "goalPanel")],
        )
        self.assertEqual(
            "auth-recovery-shell",
            capture_ids_by_selector[("authRecovery", "shell")],
        )
        self.assertEqual(
            "auth-recovery-login-screen",
            capture_ids_by_selector[("authRecovery", "login")],
        )
        self.assertEqual(
            "auth-recovery-signup-form",
            capture_ids_by_selector[("authRecovery", "signup")],
        )
        self.assertEqual(
            "auth-recovery-forgot-password-form",
            capture_ids_by_selector[("authRecovery", "forgotPassword")],
        )
        self.assertEqual(
            "auth-recovery-reset-password-form",
            capture_ids_by_selector[("authRecovery", "resetPassword")],
        )
        self.assertEqual(
            "auth-recovery-recovery-bridge",
            capture_ids_by_selector[("authRecovery", "recoveryBridge")],
        )
        self.assertEqual(
            "auth-recovery-message-chrome",
            capture_ids_by_selector[("authRecovery", "messageChrome")],
        )
        self.assertEqual(
            "auth-recovery-account-panel",
            capture_ids_by_selector[("authRecovery", "accountChrome")],
        )
        self.assertEqual(
            "auth-recovery-action-chrome",
            capture_ids_by_selector[("authRecovery", "actionChrome")],
        )
        self.assertEqual(
            "entry-handoff-card",
            capture_ids_by_selector[("entryHandoff", "card")],
        )
        self.assertEqual(
            "entry-handoff-status-panel",
            capture_ids_by_selector[("entryHandoff", "statusPanel")],
        )
        self.assertEqual(
            "entry-handoff-stage-list",
            capture_ids_by_selector[("entryHandoff", "stageList")],
        )
        self.assertEqual(
            "entry-handoff-install-manual-panel",
            capture_ids_by_selector[("entryHandoff", "installManualPanel")],
        )
        self.assertEqual(
            "curated-onboarding-shell",
            capture_ids_by_selector[("curatedOnboarding", "shell")],
        )
        self.assertEqual(
            "curated-onboarding-progress-panel",
            capture_ids_by_selector[("curatedOnboarding", "progress")],
        )
        self.assertEqual(
            "curated-onboarding-option-card",
            capture_ids_by_selector[("curatedOnboarding", "optionCard")],
        )
        self.assertEqual(
            "curated-onboarding-review-panel",
            capture_ids_by_selector[("curatedOnboarding", "review")],
        )
        self.assertEqual(
            "curated-onboarding-handoff-panel",
            capture_ids_by_selector[("curatedOnboarding", "handoff")],
        )
        self.assertEqual(
            "history-overview-default",
            capture_ids_by_selector[("historyOverview", "default")],
        )
        self.assertEqual(
            "history-exercises-default",
            capture_ids_by_selector[("historyExercises", "default")],
        )
        self.assertEqual(
            "history-sessions-list-default",
            capture_ids_by_selector[("historySessions", "default")],
        )
        self.assertEqual(
            "history-log-detail-default",
            capture_ids_by_selector[("historyLog", "default")],
        )

    def test_duplicate_mapping_and_missing_variant_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, primitives_path, capture_map_path = write_fixture_stack(root)
            capture_map = json.loads(capture_map_path.read_text(encoding="utf-8"))
            capture_map["captures"].append(dict(capture_map["captures"][0]))
            errors = validate_capture_map(capture_map, root=root)
            self.assertTrue(any("duplicates mapping key" in item for item in errors))

            primitives = json.loads(primitives_path.read_text(encoding="utf-8"))
            capture_map = json.loads(capture_map_path.read_text(encoding="utf-8"))
            capture_map["captures"][0]["primitive_variants"]["header"]["variant_id"] = "missing"
            binding_errors = validate_capture_map_contract_bindings(capture_map, primitives)
            self.assertTrue(any("missing variant" in item for item in binding_errors))

    def test_invalid_screen_state_pair_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture_stack(root)
            inputs_path = root / "ops" / "atlas" / "ui_observe" / "fitness_capture_inputs.v1.json"
            inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
            inputs["capture_set"] = [{"screen_key": "todayOverview", "state_key": "missing"}]
            inputs_path.write_text(json.dumps(inputs, indent=2) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "does not exist in the capture map"):
                observe_fitness_ui(
                    root=root,
                    schema_path=default_schema_path(ROOT),
                    capture_map_schema_path=default_capture_map_schema_path(ROOT),
                )

    def test_observe_fitness_ui_emits_comparable_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture_stack(root)

            first = observe_fitness_ui(
                root=root,
                schema_path=default_schema_path(ROOT),
                capture_map_schema_path=default_capture_map_schema_path(ROOT),
                output_root=root / "runtime" / "atlas" / "ui-observe" / "fitness",
            )
            second = observe_fitness_ui(
                root=root,
                schema_path=default_schema_path(ROOT),
                capture_map_schema_path=default_capture_map_schema_path(ROOT),
                output_root=root / "runtime" / "atlas" / "ui-observe" / "fitness",
            )

            self.assertEqual(1, first["capture_count"])
            self.assertEqual(1, second["capture_count"])
            first_payload = first["observations"][0]
            second_payload = second["observations"][0]
            self.assertEqual(UI_OBSERVATION_CONTRACT_VERSION, first_payload["contract_version"])
            self.assertEqual([], validate_observation_payload(first_payload))
            self.assertEqual(first_payload["observation_id"], second_payload["observation_id"])
            self.assertEqual(first_payload["comparison_digest"], second_payload["comparison_digest"])
            self.assertEqual(
                first_payload["capture"]["capture_map_ref"],
                "ops/atlas/ui_observe/fitness_capture_map.v1.json",
            )
            latest_path = root / first["outputs"][0]["latest_ref"]
            self.assertTrue(latest_path.exists())


if __name__ == "__main__":
    unittest.main()
