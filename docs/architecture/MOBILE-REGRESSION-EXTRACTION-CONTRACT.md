# Mobile Regression Extraction Contract

## Status

- Reviewed: `2026-04-11`
- Posture: `repo-local contract established`
- ATLAS role: lineage, boundary summary, and phase tracking only

## Source of truth

- Implementation contract: `repos/fawxzzy-fitness/docs/MOBILE-REGRESSION-EXTRACTION-CONTRACT.md`
- ATLAS should defer implementation details, file inventories, and migration notes to that repo-local document.

## Live boundary snapshot

- TypeScript ownership lives under `repos/fawxzzy-fitness/src/features/mobile-regression/*`.
- Board-generation implementation lives in `repos/fawxzzy-fitness/scripts/mobile_regression/board_builder.py`.
- `repos/fawxzzy-fitness/scripts/build-mobile-regression-boards.py` remains the stable public wrapper behind `npm run qa:boards` until an explicit CLI cutover.
- Active proof surface lives under `repos/fawxzzy-fitness/tests/mobile-regression/*`.

## Stack guidance

- Treat the repo-local contract as implementation truth for this slice.
- Keep ATLAS references short and pointer-oriented to avoid contract drift.
- Do not mix unrelated repo work into mobile-regression consolidation.
- Keep stack-level tracking focused on lineage and phase status, not duplicate repo inventories.
