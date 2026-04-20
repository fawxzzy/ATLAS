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

The first capture set is intentionally small and fixed:

- `today-overview-default`
- `routines-overview-default`
- `exercise-log-active`
- `edit-day-default`

The mapping contract defines:

- screen key and state key
- stable capture id
- owner surface refs used for lineage
- explicit primitive variants for each slot

The input contract selects which screen/state pairs are active for a run. This keeps the observer deterministic by rule instead of by inline assumptions.

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
