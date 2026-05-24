# Stack Lock Decision - Fitness Feedback Resolved Tag And Cleanup

Date: 2026-05-24
Decision owner: ATLAS root
Affected component: `fitness`

## Decision

Accept Fitness commit `bee9c87eaf08a77ddce3928ba321cd84558424ce` into ATLAS lock truth.

## Why

This package changes governed feedback-board behavior:

- feature cards now use the visible forum tag `Resolved` instead of `Fixed`
- active boards now expose `Resolved` as an available status tag
- general `feedback` archived older posts were removed
- stale bounded pointers to deleted older forum threads were cleared

## Evidence

- `docs/ops/FITNESS-FEEDBACK-RESOLVED-TAG-AND-FEEDBACK-CLEANUP-2026-05-24.md`
- `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`
- `repos/fawxzzy-fitness/src/lib/discord/bug-reports.test.ts`

## Verification

- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/bug-reports.test.ts`
- `npm run verify`
- root validation after repin
