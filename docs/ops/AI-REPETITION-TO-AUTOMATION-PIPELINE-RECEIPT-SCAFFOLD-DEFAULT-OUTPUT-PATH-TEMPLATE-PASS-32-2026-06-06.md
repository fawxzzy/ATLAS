# AI Repetition-to-Automation Pipeline Receipt Scaffold Default Output-Path Template Pass 32 - 2026-06-06

- Date: `2026-06-06`
- Lane: `AI Repetition-to-Automation Pipeline`
- Mode: `root capability slice`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-RECEIPT-SCAFFOLD-DEFAULT-TITLE-TEMPLATE-PASS-31-2026-06-06.md`
  - `ops/atlas/receipt_scaffold.py`
  - `tests/test_atlas_receipt_scaffold.py`
  - `repos/_stack/scripts/receipt-package.mjs`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`

## Objective

Remove the remaining routine file-path burden from the live receipt scaffold path by allowing one explicit opt-in flag to write the scaffold to a deterministic `docs/ops/` path whenever the operator omits `--output`.

## Why This Is The Next Honest Capability Slice

After PR `#78` merged, the live helper no longer required routine manual title entry, but the durable-write path still required the operator to invent a file path every time a persisted scaffold was wanted:

- `--output`

That was the next repeated manual seam in the operator path. Adding one explicit opt-in deterministic write path improves the live draft scaffold surface without widening into doctrine authority, publication authority, deploy authority, or silent default mutation.

## Implementation

- `ops/atlas/receipt_scaffold.py`
  - add `--write-default-output`
  - when that flag is set and `--output` is omitted, derive one deterministic `docs/ops/<TITLE-SLUG>.md` path
  - keep default stdout-only behavior unchanged when neither `--output` nor `--write-default-output` is supplied
- `tests/test_atlas_receipt_scaffold.py`
  - prove the CLI writes a valid scaffold to the deterministic `docs/ops/` path when `--write-default-output` is used

## Verification

- `python -m unittest tests.test_atlas_receipt_scaffold -v`
- `node .\repos\_stack\scripts\receipt-package.mjs --format json --lane "AI Repetition-to-Automation Pipeline"`
- `python .\ops\atlas\receipt_scaffold.py scaffold --lane "AI Repetition-to-Automation Pipeline"`
- `python .\ops\validation\validate_stack.py --ratchet`

## Expected Live Consequence

- default stdout scaffold output remains unchanged
- explicit `--write-default-output` can now persist the scaffold without forcing manual path invention
- the deterministic write path stays bounded to `docs/ops/`

## Marker Decision

- `AI Repetition-to-Automation Pipeline: no movement`

Why:

- this is a real operator-surface improvement
- but it still lands inside draft-only helper behavior rather than broader governed adoption

## Protected Surfaces Not Touched

- `repos/fawxzzy-fitness`
- `archive/`
- `.vercel`
- `.env`
- secret surfaces
- deployment surfaces
- owner-repo implementation code

## Exact Next Package

- `AI Repetition-to-Automation Pipeline receipt-scaffold default output-path template review-surface audit pass 1`
