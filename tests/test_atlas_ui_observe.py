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

    def test_default_capture_set_covers_today_history_detail_workout_card_settings_detail_support_chooser_auth_entry_and_curated_families(self) -> None:
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
            ("historyLog", "detailSurface"),
            ("historyLog", "editModeHeaderPanel"),
            ("historyLog", "fieldInputState"),
            ("historyLog", "disclosureExpanded"),
            ("historyLog", "noteEmptyStateChrome"),
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
            "history-log-detail-surface",
            capture_ids_by_selector[("historyLog", "detailSurface")],
        )
        self.assertEqual(
            "history-log-edit-mode-header-panel",
            capture_ids_by_selector[("historyLog", "editModeHeaderPanel")],
        )
        self.assertEqual(
            "history-log-field-input-state",
            capture_ids_by_selector[("historyLog", "fieldInputState")],
        )
        self.assertEqual(
            "history-log-disclosure-expanded",
            capture_ids_by_selector[("historyLog", "disclosureExpanded")],
        )
        self.assertEqual(
            "history-log-note-empty-state-chrome",
            capture_ids_by_selector[("historyLog", "noteEmptyStateChrome")],
        )

    def test_exercise_discovery_and_detail_family_reuses_existing_capture_ids(self) -> None:
        inputs = json.loads(default_capture_inputs_path(ROOT).read_text(encoding="utf-8"))
        capture_map = json.loads(default_capture_map_path(ROOT).read_text(encoding="utf-8"))

        selectors = {(item["screen_key"], item["state_key"]) for item in inputs["capture_set"]}
        captures_by_id = {item["capture_id"]: item for item in capture_map["captures"]}
        capture_ids = set(captures_by_id)

        self.assertIn(("historyExercises", "default"), selectors)
        self.assertIn(("detailSupport", "exerciseInfoSheet"), selectors)
        self.assertEqual("history-exercises-default", captures_by_id["history-exercises-default"]["capture_id"])
        self.assertEqual(
            "detail-support-exercise-info-sheet",
            captures_by_id["detail-support-exercise-info-sheet"]["capture_id"],
        )
        self.assertIn(
            "repos/fawxzzy-fitness/src/app/history/exercises/ExerciseBrowserClient.tsx",
            captures_by_id["history-exercises-default"]["owner_surface_refs"],
        )
        self.assertIn(
            "repos/fawxzzy-fitness/src/components/ExerciseInfoSheet.tsx",
            captures_by_id["detail-support-exercise-info-sheet"]["owner_surface_refs"],
        )
        self.assertFalse(any(capture_id.startswith("exercise-detail-") for capture_id in capture_ids))
        self.assertFalse(any(item["screen_key"] == "exerciseDetail" for item in capture_map["captures"]))

    def test_chooser_family_reuses_existing_capture_ids_and_lineage(self) -> None:
        inputs = json.loads(default_capture_inputs_path(ROOT).read_text(encoding="utf-8"))
        capture_map = json.loads(default_capture_map_path(ROOT).read_text(encoding="utf-8"))

        selectors = {(item["screen_key"], item["state_key"]) for item in inputs["capture_set"]}
        captures_by_id = {item["capture_id"]: item for item in capture_map["captures"]}
        exercise_picker_ref = "repos/fawxzzy-fitness/src/components/ExercisePicker.tsx"
        session_add_exercise_form_ref = "repos/fawxzzy-fitness/src/components/SessionAddExerciseForm.tsx"
        routine_day_add_exercise_form_ref = (
            "repos/fawxzzy-fitness/src/app/routines/[id]/edit/day/[dayId]/RoutineDayAddExerciseForm.tsx"
        )
        exercise_search_filters_ref = "repos/fawxzzy-fitness/src/components/exercises/ExerciseSearchFilters.tsx"
        picker_list_viewport_ref = "repos/fawxzzy-fitness/src/components/ui/PickerListViewport.tsx"
        tag_filter_control_ref = "repos/fawxzzy-fitness/src/components/ExerciseTagFilterControl.tsx"
        shared_goal_form_ref = "repos/fawxzzy-fitness/src/components/ui/measurements/SharedExerciseGoalForm.tsx"

        for selector in {
            ("exerciseChooser", "picker"),
            ("exerciseChooser", "tagFilterControl"),
            ("exerciseChooser", "searchFilters"),
            ("exerciseChooser", "pickerPanel"),
            ("exerciseChooser", "filterPanel"),
            ("exerciseChooser", "goalPanel"),
        }:
            self.assertIn(selector, selectors)

        self.assertIn(exercise_picker_ref, captures_by_id["exercise-chooser-picker"]["owner_surface_refs"])
        self.assertIn(session_add_exercise_form_ref, captures_by_id["exercise-chooser-picker"]["owner_surface_refs"])
        self.assertIn(
            routine_day_add_exercise_form_ref,
            captures_by_id["exercise-chooser-picker"]["owner_surface_refs"],
        )
        self.assertIn(
            tag_filter_control_ref,
            captures_by_id["exercise-chooser-tag-filter-control"]["owner_surface_refs"],
        )
        self.assertIn(
            exercise_search_filters_ref,
            captures_by_id["exercise-chooser-search-filters"]["owner_surface_refs"],
        )
        self.assertIn(
            tag_filter_control_ref,
            captures_by_id["exercise-chooser-search-filters"]["owner_surface_refs"],
        )
        self.assertIn(exercise_picker_ref, captures_by_id["exercise-chooser-picker-panel"]["owner_surface_refs"])
        self.assertIn(
            picker_list_viewport_ref,
            captures_by_id["exercise-chooser-picker-panel"]["owner_surface_refs"],
        )
        self.assertIn(
            exercise_search_filters_ref,
            captures_by_id["exercise-chooser-filter-panel"]["owner_surface_refs"],
        )
        self.assertIn(
            tag_filter_control_ref,
            captures_by_id["exercise-chooser-filter-panel"]["owner_surface_refs"],
        )
        self.assertIn(exercise_picker_ref, captures_by_id["exercise-chooser-goal-panel"]["owner_surface_refs"])
        self.assertIn(
            shared_goal_form_ref,
            captures_by_id["exercise-chooser-goal-panel"]["owner_surface_refs"],
        )

        self.assertFalse(any(capture_id.startswith("exercise-picker-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("exercise-search-filters-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("picker-list-viewport-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("chooser-panel-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("filter-shell-") for capture_id in captures_by_id))
        self.assertFalse(any(item["screen_key"] == "exercisePicker" for item in capture_map["captures"]))
        self.assertFalse(any(item["screen_key"] == "exerciseSearchFilters" for item in capture_map["captures"]))
        self.assertFalse(any(item["screen_key"] == "pickerListViewport" for item in capture_map["captures"]))
        self.assertFalse(any(item["screen_key"] == "chooserPanel" for item in capture_map["captures"]))
        self.assertFalse(any(item["screen_key"] == "filterShell" for item in capture_map["captures"]))

    def test_auth_recovery_family_reuses_existing_capture_ids_and_lineage(self) -> None:
        inputs = json.loads(default_capture_inputs_path(ROOT).read_text(encoding="utf-8"))
        capture_map = json.loads(default_capture_map_path(ROOT).read_text(encoding="utf-8"))

        selectors = {(item["screen_key"], item["state_key"]) for item in inputs["capture_set"]}
        captures_by_id = {item["capture_id"]: item for item in capture_map["captures"]}
        auth_shell_ref = "repos/fawxzzy-fitness/src/components/auth/AuthShell.tsx"
        login_page_ref = "repos/fawxzzy-fitness/src/app/login/page.tsx"
        login_screen_ref = "repos/fawxzzy-fitness/src/app/login/LoginScreen.tsx"
        login_screen_state_ref = "repos/fawxzzy-fitness/src/app/login/loginScreenState.ts"
        signup_page_ref = "repos/fawxzzy-fitness/src/app/signup/page.tsx"
        signup_form_ref = "repos/fawxzzy-fitness/src/components/auth/SignupForm.tsx"
        auth_copy_ref = "repos/fawxzzy-fitness/src/components/auth/authCopy.ts"
        forgot_password_page_ref = "repos/fawxzzy-fitness/src/app/forgot-password/page.tsx"
        forgot_password_client_ref = "repos/fawxzzy-fitness/src/app/forgot-password/ForgotPasswordFormClient.tsx"
        reset_password_page_ref = "repos/fawxzzy-fitness/src/app/reset-password/page.tsx"
        recovery_bridge_ref = "repos/fawxzzy-fitness/src/app/reset-password/RecoverySessionBridge.tsx"
        app_button_ref = "repos/fawxzzy-fitness/src/components/ui/AppButton.tsx"
        remembered_login_ref = "repos/fawxzzy-fitness/src/lib/remembered-login.ts"

        for selector in {
            ("authRecovery", "shell"),
            ("authRecovery", "login"),
            ("authRecovery", "signup"),
            ("authRecovery", "forgotPassword"),
            ("authRecovery", "resetPassword"),
            ("authRecovery", "recoveryBridge"),
            ("authRecovery", "messageChrome"),
            ("authRecovery", "accountChrome"),
            ("authRecovery", "actionChrome"),
        }:
            self.assertIn(selector, selectors)

        for capture_id in {
            "auth-recovery-shell",
            "auth-recovery-login-screen",
            "auth-recovery-signup-form",
            "auth-recovery-forgot-password-form",
            "auth-recovery-reset-password-form",
            "auth-recovery-recovery-bridge",
            "auth-recovery-message-chrome",
            "auth-recovery-action-chrome",
        }:
            self.assertIn(auth_shell_ref, captures_by_id[capture_id]["owner_surface_refs"])

        self.assertIn(login_page_ref, captures_by_id["auth-recovery-login-screen"]["owner_surface_refs"])
        self.assertIn(login_screen_ref, captures_by_id["auth-recovery-login-screen"]["owner_surface_refs"])
        self.assertIn(login_screen_state_ref, captures_by_id["auth-recovery-login-screen"]["owner_surface_refs"])
        self.assertIn(auth_copy_ref, captures_by_id["auth-recovery-login-screen"]["owner_surface_refs"])
        self.assertIn(remembered_login_ref, captures_by_id["auth-recovery-login-screen"]["owner_surface_refs"])
        self.assertIn(signup_page_ref, captures_by_id["auth-recovery-signup-form"]["owner_surface_refs"])
        self.assertIn(signup_form_ref, captures_by_id["auth-recovery-signup-form"]["owner_surface_refs"])
        self.assertIn(remembered_login_ref, captures_by_id["auth-recovery-signup-form"]["owner_surface_refs"])
        self.assertIn(
            forgot_password_page_ref,
            captures_by_id["auth-recovery-forgot-password-form"]["owner_surface_refs"],
        )
        self.assertIn(
            forgot_password_client_ref,
            captures_by_id["auth-recovery-forgot-password-form"]["owner_surface_refs"],
        )
        self.assertIn(reset_password_page_ref, captures_by_id["auth-recovery-reset-password-form"]["owner_surface_refs"])
        self.assertIn(reset_password_page_ref, captures_by_id["auth-recovery-recovery-bridge"]["owner_surface_refs"])
        self.assertIn(recovery_bridge_ref, captures_by_id["auth-recovery-recovery-bridge"]["owner_surface_refs"])

        for owner_surface_ref in {
            login_screen_ref,
            login_screen_state_ref,
            signup_form_ref,
            auth_copy_ref,
            forgot_password_client_ref,
            reset_password_page_ref,
            recovery_bridge_ref,
            remembered_login_ref,
        }:
            self.assertIn(owner_surface_ref, captures_by_id["auth-recovery-message-chrome"]["owner_surface_refs"])
            self.assertIn(owner_surface_ref, captures_by_id["auth-recovery-action-chrome"]["owner_surface_refs"])

        self.assertIn(login_screen_ref, captures_by_id["auth-recovery-account-panel"]["owner_surface_refs"])
        self.assertIn(login_screen_state_ref, captures_by_id["auth-recovery-account-panel"]["owner_surface_refs"])
        self.assertIn(auth_copy_ref, captures_by_id["auth-recovery-account-panel"]["owner_surface_refs"])
        self.assertIn(remembered_login_ref, captures_by_id["auth-recovery-account-panel"]["owner_surface_refs"])
        self.assertIn(app_button_ref, captures_by_id["auth-recovery-action-chrome"]["owner_surface_refs"])
        self.assertFalse(any(capture_id.startswith("auth-footer-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("auth-message-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("auth-account-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("auth-action-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("remembered-login-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("login-state-") for capture_id in captures_by_id))
        self.assertFalse(any(item["screen_key"] == "authFooter" for item in capture_map["captures"]))
        self.assertFalse(any(item["screen_key"] == "authMessage" for item in capture_map["captures"]))
        self.assertFalse(any(item["screen_key"] == "authAccount" for item in capture_map["captures"]))
        self.assertFalse(any(item["screen_key"] == "authAction" for item in capture_map["captures"]))
        self.assertFalse(any(item["screen_key"] == "rememberedLogin" for item in capture_map["captures"]))
        self.assertFalse(any(item["screen_key"] == "loginState" for item in capture_map["captures"]))

    def test_install_flow_removal_reuses_existing_entry_handoff_capture_ids_and_entry_resolution_lineage(self) -> None:
        inputs = json.loads(default_capture_inputs_path(ROOT).read_text(encoding="utf-8"))
        capture_map = json.loads(default_capture_map_path(ROOT).read_text(encoding="utf-8"))

        selectors = {(item["screen_key"], item["state_key"]) for item in inputs["capture_set"]}
        captures_by_id = {item["capture_id"]: item for item in capture_map["captures"]}
        initial_experience_gate_ref = "repos/fawxzzy-fitness/src/components/auth/InitialExperienceGate.tsx"
        entry_resolution_ref = "repos/fawxzzy-fitness/src/lib/resolvePostLoginDestination.ts"
        install_entry_gate_ref = "repos/fawxzzy-fitness/src/components/install/InstallEntryGate.tsx"
        root_page_ref = "repos/fawxzzy-fitness/src/app/page.tsx"

        for selector in {
            ("entryHandoff", "card"),
            ("entryHandoff", "statusPanel"),
            ("entryHandoff", "stageList"),
        }:
            self.assertIn(selector, selectors)

        for capture_id in {
            "entry-handoff-card",
            "entry-handoff-status-panel",
            "entry-handoff-stage-list",
        }:
            self.assertIn(initial_experience_gate_ref, captures_by_id[capture_id]["owner_surface_refs"])
            self.assertIn(entry_resolution_ref, captures_by_id[capture_id]["owner_surface_refs"])
            self.assertNotIn(install_entry_gate_ref, captures_by_id[capture_id]["owner_surface_refs"])
            self.assertNotIn(root_page_ref, captures_by_id[capture_id]["owner_surface_refs"])

        self.assertFalse(any(capture_id.startswith("install-entry-") for capture_id in captures_by_id))
        self.assertFalse(any(item["screen_key"] == "installEntry" for item in capture_map["captures"]))

    def test_today_overview_token_bridge_family_reuses_existing_capture_id_and_lineage(self) -> None:
        inputs = json.loads(default_capture_inputs_path(ROOT).read_text(encoding="utf-8"))
        capture_map = json.loads(default_capture_map_path(ROOT).read_text(encoding="utf-8"))

        selectors = {(item["screen_key"], item["state_key"]) for item in inputs["capture_set"]}
        captures_by_id = {item["capture_id"]: item for item in capture_map["captures"]}
        today_page_ref = "repos/fawxzzy-fitness/src/app/today/page.tsx"
        today_day_picker_ref = "repos/fawxzzy-fitness/src/app/today/TodayDayPicker.tsx"
        today_exercise_rows_ref = "repos/fawxzzy-fitness/src/app/today/TodayExerciseRows.tsx"
        day_list_ref = "repos/fawxzzy-fitness/src/components/day-list/DayList.tsx"

        self.assertIn(("todayOverview", "default"), selectors)
        self.assertIn(today_page_ref, captures_by_id["today-overview-default"]["owner_surface_refs"])
        self.assertIn(today_day_picker_ref, captures_by_id["today-overview-default"]["owner_surface_refs"])
        self.assertIn(today_exercise_rows_ref, captures_by_id["today-overview-default"]["owner_surface_refs"])
        self.assertIn(day_list_ref, captures_by_id["today-overview-default"]["owner_surface_refs"])
        self.assertFalse(any(capture_id.startswith("today-list-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("today-feedback-") for capture_id in captures_by_id))
        self.assertFalse(any(item["screen_key"] == "todayList" for item in capture_map["captures"]))
        self.assertFalse(any(item["screen_key"] == "todayFeedback" for item in capture_map["captures"]))

    def test_main_tab_nav_family_reuses_existing_capture_ids_and_app_nav_lineage(self) -> None:
        inputs = json.loads(default_capture_inputs_path(ROOT).read_text(encoding="utf-8"))
        capture_map = json.loads(default_capture_map_path(ROOT).read_text(encoding="utf-8"))

        selectors = {(item["screen_key"], item["state_key"]) for item in inputs["capture_set"]}
        captures_by_id = {item["capture_id"]: item for item in capture_map["captures"]}
        app_nav_ref = "repos/fawxzzy-fitness/src/components/AppNav.tsx"

        for selector in {
            ("todayOverview", "default"),
            ("routinesOverview", "default"),
            ("routinesOverview", "selectedRoutine"),
            ("settings", "overview"),
            ("historyOverview", "default"),
            ("historyExercises", "default"),
            ("historySessions", "default"),
        }:
            self.assertIn(selector, selectors)

        for capture_id in {
            "today-overview-default",
            "routines-overview-default",
            "routines-overview-selected-routine",
            "settings-overview-default",
            "history-overview-default",
            "history-exercises-default",
            "history-sessions-list-default",
        }:
            self.assertIn(app_nav_ref, captures_by_id[capture_id]["owner_surface_refs"])

        self.assertIn(
            "repos/fawxzzy-fitness/src/app/today/page.tsx",
            captures_by_id["today-overview-default"]["owner_surface_refs"],
        )
        self.assertIn(
            "repos/fawxzzy-fitness/src/app/today/TodayDayPicker.tsx",
            captures_by_id["today-overview-default"]["owner_surface_refs"],
        )
        self.assertIn(
            "repos/fawxzzy-fitness/src/app/today/TodayExerciseRows.tsx",
            captures_by_id["today-overview-default"]["owner_surface_refs"],
        )
        self.assertIn(
            "repos/fawxzzy-fitness/src/components/day-list/DayList.tsx",
            captures_by_id["today-overview-default"]["owner_surface_refs"],
        )
        self.assertFalse(any(capture_id.startswith("main-tab-") for capture_id in captures_by_id))
        self.assertFalse(any(item["screen_key"] == "mainTabNav" for item in capture_map["captures"]))

    def test_history_shared_family_reuses_existing_history_capture_ids_and_lineage(self) -> None:
        inputs = json.loads(default_capture_inputs_path(ROOT).read_text(encoding="utf-8"))
        capture_map = json.loads(default_capture_map_path(ROOT).read_text(encoding="utf-8"))

        selectors = {(item["screen_key"], item["state_key"]) for item in inputs["capture_set"]}
        captures_by_id = {item["capture_id"]: item for item in capture_map["captures"]}
        history_shared_ref = "repos/fawxzzy-fitness/src/components/history/HistoryShared.tsx"
        history_route_scaffold_ref = "repos/fawxzzy-fitness/src/components/history/HistoryRouteScaffold.tsx"
        detail_scaffold_ref = "repos/fawxzzy-fitness/src/components/routines/day-detail/DetailScreenScaffold.tsx"

        for selector in {
            ("historyOverview", "default"),
            ("historyExercises", "default"),
            ("historySessions", "default"),
            ("historyLog", "detailSurface"),
            ("historyLog", "editModeHeaderPanel"),
            ("historyLog", "noteEmptyStateChrome"),
        }:
            self.assertIn(selector, selectors)

        for capture_id in {
            "history-overview-default",
            "history-exercises-default",
            "history-sessions-list-default",
            "history-log-detail-surface",
            "history-log-edit-mode-header-panel",
            "history-log-note-empty-state-chrome",
        }:
            self.assertIn(history_shared_ref, captures_by_id[capture_id]["owner_surface_refs"])

        self.assertIn(
            history_route_scaffold_ref,
            captures_by_id["history-log-detail-surface"]["owner_surface_refs"],
        )
        self.assertNotIn(
            detail_scaffold_ref,
            captures_by_id["history-log-detail-surface"]["owner_surface_refs"],
        )

        self.assertFalse(any(capture_id.startswith("history-shared-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("history-control-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("history-route-") for capture_id in captures_by_id))
        self.assertFalse(any(item["screen_key"] == "historyShared" for item in capture_map["captures"]))
        self.assertFalse(any(item["screen_key"] == "historyControl" for item in capture_map["captures"]))
        self.assertFalse(any(item["screen_key"] == "historyRoute" for item in capture_map["captures"]))

    def test_routine_editor_detail_family_reuses_existing_editor_capture_ids_and_lineage(self) -> None:
        inputs = json.loads(default_capture_inputs_path(ROOT).read_text(encoding="utf-8"))
        capture_map = json.loads(default_capture_map_path(ROOT).read_text(encoding="utf-8"))

        selectors = {(item["screen_key"], item["state_key"]) for item in inputs["capture_set"]}
        captures_by_id = {item["capture_id"]: item for item in capture_map["captures"]}
        edit_day_page_ref = "repos/fawxzzy-fitness/src/app/routines/[id]/edit/day/[dayId]/page.tsx"
        edit_routine_page_ref = "repos/fawxzzy-fitness/src/app/routines/[id]/edit/page.tsx"
        add_exercise_page_ref = "repos/fawxzzy-fitness/src/app/routines/[id]/edit/day/[dayId]/add-exercise/page.tsx"
        routine_editor_shared_ref = "repos/fawxzzy-fitness/src/components/routines/RoutineEditorShared.tsx"
        routine_details_exit_guard_ref = "repos/fawxzzy-fitness/src/components/routines/RoutineDetailsExitGuard.tsx"
        detail_scaffold_ref = "repos/fawxzzy-fitness/src/components/routines/day-detail/DetailScreenScaffold.tsx"
        shared_section_shell_ref = "repos/fawxzzy-fitness/src/components/ui/app/SharedSectionShell.tsx"
        shared_screen_header_ref = "repos/fawxzzy-fitness/src/components/ui/app/SharedScreenHeader.tsx"
        app_panel_ref = "repos/fawxzzy-fitness/src/components/ui/app/AppPanel.tsx"
        app_badge_ref = "repos/fawxzzy-fitness/src/components/ui/app/AppBadge.tsx"
        design_system_ref = "repos/fawxzzy-fitness/src/components/ui/app/designSystem.ts"
        tokens_ref = "repos/fawxzzy-fitness/src/components/ui/app/tokens.ts"
        routine_editor_form_ref = "repos/fawxzzy-fitness/src/components/routines/RoutineEditorForm.tsx"
        reorder_exercise_row_ref = "repos/fawxzzy-fitness/src/app/routines/[id]/edit/day/[dayId]/ReorderExerciseRow.tsx"

        for selector in {
            ("editDay", "default"),
            ("editRoutine", "daysSection"),
            ("editDayAddExercise", "default"),
        }:
            self.assertIn(selector, selectors)

        self.assertIn(routine_editor_shared_ref, captures_by_id["edit-routine-days-section-default"]["owner_surface_refs"])
        self.assertIn(routine_editor_shared_ref, captures_by_id["edit-day-add-exercise-default"]["owner_surface_refs"])
        self.assertIn(detail_scaffold_ref, captures_by_id["edit-day-default"]["owner_surface_refs"])
        self.assertIn(
            routine_details_exit_guard_ref,
            captures_by_id["edit-routine-days-section-default"]["owner_surface_refs"],
        )
        self.assertIn(edit_day_page_ref, captures_by_id["edit-day-default"]["owner_surface_refs"])
        self.assertIn(edit_routine_page_ref, captures_by_id["edit-routine-days-section-default"]["owner_surface_refs"])
        self.assertIn(add_exercise_page_ref, captures_by_id["edit-day-add-exercise-default"]["owner_surface_refs"])

        for capture_id in {
            "edit-day-default",
            "edit-routine-days-section-default",
            "edit-day-add-exercise-default",
        }:
            self.assertIn(shared_screen_header_ref, captures_by_id[capture_id]["owner_surface_refs"])
            self.assertIn(app_panel_ref, captures_by_id[capture_id]["owner_surface_refs"])
            self.assertIn(shared_section_shell_ref, captures_by_id[capture_id]["owner_surface_refs"])

        for capture_id in {
            "edit-day-default",
            "edit-routine-days-section-default",
        }:
            self.assertIn(app_badge_ref, captures_by_id[capture_id]["owner_surface_refs"])

        self.assertIn(
            "repos/fawxzzy-fitness/src/app/routines/[id]/edit/day/[dayId]/EditDaySettingsAutosaveForm.tsx",
            captures_by_id["edit-day-default"]["owner_surface_refs"],
        )
        self.assertIn(
            "repos/fawxzzy-fitness/src/app/routines/[id]/edit/day/[dayId]/EditableRoutineDayExerciseList.tsx",
            captures_by_id["edit-day-default"]["owner_surface_refs"],
        )
        self.assertIn(
            reorder_exercise_row_ref,
            captures_by_id["edit-day-default"]["owner_surface_refs"],
        )
        self.assertIn(
            "repos/fawxzzy-fitness/src/app/routines/[id]/edit/EditRoutineAutosaveForm.tsx",
            captures_by_id["edit-routine-days-section-default"]["owner_surface_refs"],
        )
        self.assertIn(
            "repos/fawxzzy-fitness/src/app/routines/[id]/edit/EditRoutineDaysSection.tsx",
            captures_by_id["edit-routine-days-section-default"]["owner_surface_refs"],
        )
        self.assertIn(
            routine_editor_form_ref,
            captures_by_id["edit-routine-days-section-default"]["owner_surface_refs"],
        )
        self.assertIn(
            "repos/fawxzzy-fitness/src/app/routines/[id]/edit/day/[dayId]/EditDayAddExerciseScreen.tsx",
            captures_by_id["edit-day-add-exercise-default"]["owner_surface_refs"],
        )
        self.assertIn(
            "repos/fawxzzy-fitness/src/app/routines/[id]/edit/day/[dayId]/RoutineDayAddExerciseForm.tsx",
            captures_by_id["edit-day-add-exercise-default"]["owner_surface_refs"],
        )
        for capture_id in {
            "edit-day-default",
            "edit-routine-days-section-default",
            "edit-day-add-exercise-default",
        }:
            self.assertIn(design_system_ref, captures_by_id[capture_id]["owner_surface_refs"])
            self.assertIn(tokens_ref, captures_by_id[capture_id]["owner_surface_refs"])
        self.assertFalse(any(capture_id.startswith("routine-editor-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("routine-detail-") for capture_id in captures_by_id))
        self.assertFalse(any(item["screen_key"] == "routineEditor" for item in capture_map["captures"]))
        self.assertFalse(any(item["screen_key"] == "routineDetail" for item in capture_map["captures"]))

    def test_session_log_set_family_reuses_existing_capture_ids_and_lineage(self) -> None:
        inputs = json.loads(default_capture_inputs_path(ROOT).read_text(encoding="utf-8"))
        capture_map = json.loads(default_capture_map_path(ROOT).read_text(encoding="utf-8"))

        selectors = {(item["screen_key"], item["state_key"]) for item in inputs["capture_set"]}
        captures_by_id = {item["capture_id"]: item for item in capture_map["captures"]}
        session_page_client_ref = "repos/fawxzzy-fitness/src/components/SessionPageClient.tsx"
        session_header_controls_ref = "repos/fawxzzy-fitness/src/components/SessionHeaderControls.tsx"
        session_route_ref = "repos/fawxzzy-fitness/src/app/session/[id]/page.tsx"
        session_focus_ref = "repos/fawxzzy-fitness/src/components/SessionExerciseFocus.tsx"
        session_timers_ref = "repos/fawxzzy-fitness/src/components/SessionTimers.tsx"
        session_block_ref = "repos/fawxzzy-fitness/src/components/session/SessionExerciseBlock.tsx"

        for selector in {
            ("exerciseLog", "sessionHeaderCard"),
            ("exerciseLog", "entrySection"),
            ("exerciseLog", "compactLogRow"),
            ("exerciseLog", "stickyFooter"),
            ("workoutCard", "disclosureExpanded"),
        }:
            self.assertIn(selector, selectors)

        self.assertIn(session_route_ref, captures_by_id["exercise-log-session-header-card"]["owner_surface_refs"])
        self.assertIn(session_page_client_ref, captures_by_id["exercise-log-session-header-card"]["owner_surface_refs"])
        self.assertIn(session_header_controls_ref, captures_by_id["exercise-log-session-header-card"]["owner_surface_refs"])
        self.assertIn(session_focus_ref, captures_by_id["exercise-log-entry-section"]["owner_surface_refs"])
        self.assertIn(session_timers_ref, captures_by_id["exercise-log-entry-section"]["owner_surface_refs"])
        self.assertIn(session_timers_ref, captures_by_id["exercise-log-compact-row"]["owner_surface_refs"])
        self.assertIn(session_page_client_ref, captures_by_id["exercise-log-sticky-footer"]["owner_surface_refs"])
        self.assertIn(session_focus_ref, captures_by_id["workout-card-disclosure-expanded"]["owner_surface_refs"])
        self.assertIn(session_block_ref, captures_by_id["workout-card-disclosure-expanded"]["owner_surface_refs"])

        self.assertFalse(any(capture_id.startswith("active-session-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("session-log-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("log-set-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("session-timer-") for capture_id in captures_by_id))
        self.assertFalse(any(item["screen_key"] == "activeSession" for item in capture_map["captures"]))
        self.assertFalse(any(item["screen_key"] == "logSet" for item in capture_map["captures"]))
        self.assertFalse(any(item["screen_key"] == "sessionTimer" for item in capture_map["captures"]))

    def test_route_loading_family_reuses_existing_route_and_entry_capture_ids(self) -> None:
        inputs = json.loads(default_capture_inputs_path(ROOT).read_text(encoding="utf-8"))
        capture_map = json.loads(default_capture_map_path(ROOT).read_text(encoding="utf-8"))

        selectors = {(item["screen_key"], item["state_key"]) for item in inputs["capture_set"]}
        captures_by_id = {item["capture_id"]: item for item in capture_map["captures"]}
        route_loading_ref = "repos/fawxzzy-fitness/src/components/RouteLoading.tsx"

        for selector in {
            ("todayOverview", "default"),
            ("routinesOverview", "default"),
            ("routinesOverview", "selectedRoutine"),
            ("settings", "overview"),
            ("entryHandoff", "card"),
            ("entryHandoff", "statusPanel"),
            ("historyOverview", "default"),
            ("historyExercises", "default"),
            ("historySessions", "default"),
            ("historyLog", "detailSurface"),
        }:
            self.assertIn(selector, selectors)

        for capture_id in {
            "today-overview-default",
            "routines-overview-default",
            "routines-overview-selected-routine",
            "settings-overview-default",
            "entry-handoff-card",
            "entry-handoff-status-panel",
            "history-overview-default",
            "history-exercises-default",
            "history-sessions-list-default",
            "history-log-detail-surface",
        }:
            self.assertIn(route_loading_ref, captures_by_id[capture_id]["owner_surface_refs"])

        self.assertIn(
            "repos/fawxzzy-fitness/src/app/loading.tsx",
            captures_by_id["entry-handoff-card"]["owner_surface_refs"],
        )
        self.assertIn(
            "repos/fawxzzy-fitness/src/app/loading.tsx",
            captures_by_id["entry-handoff-status-panel"]["owner_surface_refs"],
        )
        self.assertIn(
            "repos/fawxzzy-fitness/src/app/today/loading.tsx",
            captures_by_id["today-overview-default"]["owner_surface_refs"],
        )
        self.assertIn(
            "repos/fawxzzy-fitness/src/app/routines/loading.tsx",
            captures_by_id["routines-overview-default"]["owner_surface_refs"],
        )
        self.assertIn(
            "repos/fawxzzy-fitness/src/app/settings/loading.tsx",
            captures_by_id["settings-overview-default"]["owner_surface_refs"],
        )
        self.assertIn(
            "repos/fawxzzy-fitness/src/app/history/loading.tsx",
            captures_by_id["history-log-detail-surface"]["owner_surface_refs"],
        )
        self.assertFalse(any(capture_id.startswith("route-loading-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("boot-loading-") for capture_id in captures_by_id))
        self.assertFalse(any(item["screen_key"] == "routeLoading" for item in capture_map["captures"]))
        self.assertFalse(any(item["screen_key"] == "bootLoading" for item in capture_map["captures"]))

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
