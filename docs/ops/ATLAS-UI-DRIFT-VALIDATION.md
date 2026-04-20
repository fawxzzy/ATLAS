# ATLAS UI Drift Validation

## Purpose

ATLAS validates observed Fitness UI artifacts against Fitness owner-truth contracts and reports deltas in contract terms.

- Rule: UI consistency is validated against owner contracts, not judged ad hoc.
- Pattern: report contract deltas, not vague style opinions.
- Failure Mode: over-strict validation before primitive adoption creates noise.

## Inputs

The validator reads:

- Fitness owner truth from `repos/fawxzzy-fitness/truth-pack/fitness/design-system/*`
- active capture selection from `ops/atlas/ui_observe/fitness_capture_inputs.v1.json`
- explicit mapping from `ops/atlas/ui_observe/fitness_capture_map.v1.json`
- runtime observations from `runtime/atlas/ui-observe/fitness/*/latest.json`

## Drift dimensions

The first validator reports deltas for:

- spacing
- typography
- header shape
- card shape
- badge or tag usage
- section layout

## Outputs

Machine-readable reports conform to `schemas/atlas.ui.drift.report.v1.json`.

Runtime outputs land under:

- `runtime/atlas/ui-observe/drift/fitness/latest.json`
- `runtime/atlas/ui-observe/drift/fitness/latest.md`
- stamped JSON and Markdown siblings for each run

## Operation

Run the validator after observation:

```powershell
python ops/atlas/ui_observe/drift.py
```

Dry-run without writing reports:

```powershell
python ops/atlas/ui_observe/drift.py --dry-run
```

## Current posture

This validator reports only.

- It does not fail CI by default.
- It does not replace Fitness owner truth.
- It is intended to guide primitive adoption, starting with the highest-frequency Fitness surfaces.
