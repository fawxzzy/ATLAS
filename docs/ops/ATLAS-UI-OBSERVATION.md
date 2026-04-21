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
- `edit-day-default`
- `edit-routine-days-section-default`
- `edit-day-add-exercise-default`
- `history-overview-default`
- `history-exercises-default`
- `history-sessions-list-default`
- `history-log-detail-default`

The mapping contract defines:

- screen key and state key
- stable capture id
- owner surface refs used for lineage
- explicit primitive variants for each slot

The input contract selects which screen/state pairs are active for a run. This keeps the observer deterministic by rule instead of by inline assumptions.

- Pattern: expand capture coverage immediately after each adoption tranche so validation lands before the next wider rewrite.
- Failure Mode: assuming clean drift on old captures proves validator coverage for newly adopted surfaces.

The observer resolves primitive variants from owner contracts, groups referenced tokens by scale, and emits one normalized artifact per capture.

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
