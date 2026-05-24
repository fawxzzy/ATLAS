# Stack Lock Decision - Fitness Music Sesh Phase 8 Card Alignment

Date: 2026-05-24
Decision owner: ATLAS root
Affected component: `fitness`

## Decision

Accept Fitness commit `2d77069f521bd2f0794165442183454d9bfd95fd` into ATLAS lock truth for the Music Sesh Phase 8 card-alignment package.

## Why

The repo change is narrow and stack-relevant:

- it fixes the shared Discord feedback-card formatter so feature `User Story` lines preserve proper-name casing
- it directly supports the live Music Sesh Phase 8 card correction on the dedicated project board
- it does not change deploy behavior, product runtime behavior, or production data contracts

## Evidence

- `docs/ops/FITNESS-MUSIC-SESH-PHASE-8-CARD-ALIGNMENT-2026-05-24.md`
- `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`
- `repos/fawxzzy-fitness/src/lib/discord/bug-reports.test.ts`

## Verification

- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/bug-reports.test.ts`
- `npm run verify`
- root validation after repin
