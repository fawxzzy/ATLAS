# Stack Lock Decision - Fitness Feedback Board Project Split And Status Alignment

Date: 2026-05-24
Decision owner: ATLAS root
Affected component: `fitness`

## Decision

Accept Fitness commit `edd8d734d8fb42c36b6728948c62fedd4910a6aa` into ATLAS lock truth.

## Why

This package changes governed workflow surfaces, not product behavior:

- feature done-state display is now `Resolved` instead of `Completed`
- Music Sesh Phase 7 cards were corrected to done-state truth and resolved-reaction visibility
- the dedicated `fawxzzy-fitness` project board now owns the two current Fitness app cards instead of the general intake forum
- archived duplicate source threads were removed once canonical project-board copies existed

## Evidence

- `docs/ops/FITNESS-FEEDBACK-BOARD-PROJECT-SPLIT-STATUS-ALIGNMENT-2026-05-24.md`
- `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`
- `repos/fawxzzy-fitness/scripts/export-feedback-board.mjs`
- `repos/fawxzzy-fitness/scripts/generate-feedback-task-packets.mjs`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-FEEDBACK-BOARD.md`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`

## Verification

- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/bug-reports.test.ts`
- `node --test scripts/export-feedback-board.test.mjs`
- `npm run verify`
- root validation after repin
