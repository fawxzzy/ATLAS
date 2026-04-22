# ATLAS UI Observation

## Purpose

ATLAS owns deterministic UI observation for stack comparison. It does not own the Fitness design system itself.

- Rule: owner repos define tokens and primitive contracts; ATLAS only captures normalized observations against those contracts.
- Pattern: snapshot first, infer second, enforce third.
- Failure Mode: copying live drift into root as a second source of truth makes the observer compete with the owner repo instead of validating it.

## Current lane

This lane is observation only.

- No pass/fail gate is attached yet.
- No drift enforcement is attached yet.
- Root artifacts must stay rebuildable and comparable over time.

## Owner boundary

Fitness remains the source of truth at:

- `repos/fawxzzy-fitness/truth-pack/fitness/design-system/tokens.v1.json`
- `repos/fawxzzy-fitness/truth-pack/fitness/design-system/primitives.v1.json`
- `repos/fawxzzy-fitness/truth-pack/fitness/design-system/README.md`

ATLAS points at those files through:

- `ops/atlas/ui_observe/fitness_capture_inputs.v1.json`
- `ops/atlas/ui_observe/fitness_capture_map.v1.json`

The input contract names the active capture-set. The capture-map contract owns the explicit screen/state/variant mapping. Root capture infrastructure may not restate token values or primitive truth.

## Deterministic capture model

The active capture set stays narrow but expands immediately after each adoption tranche:

- `today-overview-default`
- `routines-overview-default`
- `routines-overview-selected-routine`
- `exercise-log-session-header-card`
- `exercise-log-entry-section`
- `exercise-log-form-section-card`
- `exercise-log-compact-row`
- `exercise-log-sticky-footer`
- `workout-card-exercise-card`
- `workout-card-disclosure-expanded`
- `workout-card-chip-row`
- `workout-card-exercise-details`
- `workout-card-metric-item`
- `workout-card-session-summary-card`
- `settings-overview-default`
- `settings-account-form`
- `settings-glass-effects`
- `settings-legacy-migration-row`
- `settings-legacy-migration-panel`
- `detail-support-surface`
- `detail-support-day-state-card`
- `detail-support-exercise-info-sheet`
- `detail-support-media-card`
- `detail-support-history-row`
- `exercise-chooser-picker`
- `exercise-chooser-tag-filter-control`
- `exercise-chooser-search-filters`
- `exercise-chooser-picker-panel`
- `exercise-chooser-filter-panel`
- `exercise-chooser-goal-panel`
- `auth-recovery-shell`
- `auth-recovery-login-screen`
- `auth-recovery-signup-form`
- `auth-recovery-forgot-password-form`
- `auth-recovery-reset-password-form`
- `auth-recovery-recovery-bridge`
- `auth-recovery-message-chrome`
- `auth-recovery-account-panel`
- `auth-recovery-action-chrome`
- `entry-handoff-card`
- `entry-handoff-status-panel`
- `entry-handoff-stage-list`
- `entry-handoff-install-manual-panel`
- `curated-onboarding-shell`
- `curated-onboarding-progress-panel`
- `curated-onboarding-option-card`
- `curated-onboarding-review-panel`
- `curated-onboarding-handoff-panel`
- `edit-day-default`
- `edit-routine-days-section-default`
- `edit-day-add-exercise-default`
- `history-overview-default`
- `history-exercises-default`
- `history-sessions-list-default`
- `history-log-detail-surface`
- `history-log-edit-mode-header-panel`
- `history-log-field-input-state`
- `history-log-disclosure-expanded`
- `history-log-note-empty-state-chrome`

The mapping contract defines:

- screen key and state key
- stable capture id
- owner surface refs used for lineage
- explicit primitive variants for each slot

The input contract selects which screen/state pairs are active for a run. This keeps the observer deterministic by rule instead of by inline assumptions.

- Pattern: expand capture coverage immediately after each adoption tranche so validation lands before the next wider rewrite.
- Failure Mode: assuming clean drift on old captures proves validator coverage for newly adopted surfaces.
- Pattern: when a newly adopted family splits from one broad capture into several narrower states, replace the broad selector immediately instead of carrying both.
- Failure Mode: leaving a newly adopted detail family collapsed under one legacy capture id hides which sub-surface actually drifted.
- Pattern: when a tranche lands on already-covered routine editor/detail surfaces, reconcile against `edit-day-default`, `edit-routine-days-section-default`, and `edit-day-add-exercise-default` before inventing new capture ids.
- Failure Mode: adding redundant routine-editor or routine-detail capture ids creates validator sprawl and weakens proof clarity.
- Pattern: when a tranche lands on the chooser family already represented by `exercise-chooser-picker`, `exercise-chooser-tag-filter-control`, `exercise-chooser-search-filters`, `exercise-chooser-picker-panel`, `exercise-chooser-filter-panel`, and `exercise-chooser-goal-panel`, widen lineage on those captures before inventing component-specific ids.
- Failure Mode: adding redundant `ExercisePicker`, `ExerciseSearchFilters`, `PickerListViewport`, chooser-panel, or filter-shell capture ids creates validator sprawl and weakens proof clarity.
- Pattern: when a tranche lands on the active session/log-set family already represented by `exercise-log-session-header-card`, `exercise-log-entry-section`, `exercise-log-compact-row`, `exercise-log-sticky-footer`, and shared `workout-card-disclosure-expanded`, widen lineage on those existing captures before inventing active-session or log-set ids.
- Failure Mode: minting dedicated `active-session-*`, `session-log-*`, `log-set-*`, or `session-timer-*` capture ids for shell, focus, or timer chrome that is already covered widens validator surface without improving drift signal.
- Pattern: the F13 history-log adoption tranche stays represented by the five split `history-log-*` captures, while the retained `history-log-detail-default` artifact remains residue only.
- Failure Mode: treating the retained legacy history-detail artifact as active proof would let residue masquerade as current validator coverage.
- Pattern: when a new owner tranche lands on already-covered exercise discovery/detail surfaces, reconcile against the active `history-exercises-default` and `detail-support-exercise-info-sheet` captures before adding selectors.
- Failure Mode: inventing a second exercise-detail capture lane in root when the changed family is already represented creates validator sprawl instead of better coverage.
- Pattern: when a new owner tranche lands on shared main-tab chrome already exercised by Today, Routines, History, and Settings captures, reconcile lineage on those existing captures first instead of minting nav-only ids.
- Failure Mode: adding a second root capture lane for shared chrome widens validator surface without increasing proof clarity.
- Pattern: when a new owner tranche lands on the shared history summary/control family already exercised by `history-overview-default`, `history-exercises-default`, `history-sessions-list-default`, and the active `history-log-*` captures, reconcile those existing selectors and lineage before minting new ids.
- Failure Mode: adding redundant capture ids for shared history header, control, or section chrome creates validator sprawl and weakens proof clarity.
- Pattern: when a tranche lands on shared transient route-loading chrome, widen `RouteLoading.tsx` plus the owning `app/**/loading.tsx` entrypoints onto the existing Today, Routines, Settings, History, and adjacent entry-handoff captures before minting loading-specific ids.
- Failure Mode: inventing a root `routeLoading` screen key, `route-loading-*` capture id, or root-side loading primitive slot before the owner truth pack freezes that family copies owner truth into root and makes the semantic rail dishonest.

The observer resolves primitive variants from owner contracts, groups referenced tokens by scale, and emits one normalized artifact per capture.

For shared chrome reconciliations, the capture map may widen owner-surface lineage inside an existing capture, such as binding `AppNav` to the active Today, Routines, History, and Settings captures, while the normalized trait digest stays anchored to the frozen primitive slots.
The same rule applies to shared history chrome: root should bind `HistoryShared.tsx` to the existing history overview, sessions, exercises, and detail captures rather than creating synthetic history-header or history-control selectors.
The same rule applies to transient route loading: root may bind `RouteLoading.tsx` and the route `loading.tsx` entrypoints to the active route and entry captures, but it must keep the normalized trait digest anchored to the frozen `header`, `card`, `tag`, and `section_layout` slots until Fitness exposes a dedicated loading primitive contract.
The same rule applies to the routine editor/detail family: root should keep the shared editor shell, section chrome, control/meta wrappers, and detail layout attached to the existing `edit-day-default`, `edit-routine-days-section-default`, and `edit-day-add-exercise-default` captures via owner-surface lineage instead of creating synthetic routine-editor or routine-detail selectors.
The same rule applies to the chooser family: root should bind `ExercisePicker.tsx`, `ExerciseSearchFilters.tsx`, `PickerListViewport.tsx`, the shared filter control, and chooser panel or goal shell surfaces onto the existing `exercise-chooser-*` captures rather than creating synthetic component-level or shell-only selectors.
The same rule applies to the active session/log-set family: root should bind `SessionPageClient.tsx`, `SessionHeaderControls.tsx`, `SessionExerciseFocus.tsx`, `SessionExerciseBlock.tsx`, `SessionTimers.tsx`, and the `app/session/[id]/page.tsx` entrypoint onto the existing `exercise-log-*` and shared `workout-card-disclosure-expanded` captures rather than creating synthetic active-session, log-set, or timer selectors.

## Mapping contract

- Rule: capture-set mappings must be explicit contracts, not hidden in observer code.
- Pattern: deterministic capture depends on deterministic mapping.
- Failure Mode: implicit variant mapping makes drift reports untrustworthy.

The capture-map contract is validated for:

- duplicate `capture_id`
- duplicate `screen_key` + `state_key` pairs
- missing owner surface refs
- missing primitive or variant definitions against Fitness owner truth

## Artifact shape

Machine-readable observations conform to `schemas/atlas.ui.observation.v1.json`.

Each artifact includes:

- stable comparison identifiers
- owner contract refs
- capture metadata
- a raw snapshot of selected primitives and token refs
- normalized traits for spacing, typography, header shape, card shape, tag usage, and section layout

## Storage

Rebuildable outputs belong under:

- `runtime/atlas/ui-observe/fitness/<capture-id>/latest.json`
- `runtime/atlas/ui-observe/fitness/<capture-id>/<timestamp>-<digest>.json`

Do not hand-edit emitted artifacts. If capture output changes, rerun the observer.

Obsolete capture ids that remain valuable for retention or audit must not be hard-deleted by default. Classify them with:

- `runtime/atlas/ui-observe/fitness/<capture-id>/residue.json`

Current-state drift reads ignore capture directories marked as `retained_residue` or `superseded_residue`, but the historical observation payloads remain on disk.

## Operation

Run the observer from the stack root:

```powershell
python ops/atlas/ui_observe/fitness.py
```

Limit to a specific capture while iterating:

```powershell
python ops/atlas/ui_observe/fitness.py --capture-id today-overview-default
```

Use `--dry-run` when validating contract wiring without writing runtime artifacts.

## Residue Rule

- Rule: retained UI observation residue stays visible, but it does not compete as active validator truth.
- Pattern: when a capture id is replaced by narrower active captures, keep the old artifacts and add a `residue.json` sidecar that records the retention reason and any replacement capture ids.
- Failure Mode: deleting old runtime evidence casually or letting stale capture ids keep polluting drift reports.
