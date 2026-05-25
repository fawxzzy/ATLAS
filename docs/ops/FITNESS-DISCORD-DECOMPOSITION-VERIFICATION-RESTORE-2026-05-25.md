# Fitness Discord Decomposition Verification Restore

Date: 2026-05-25
Lane: Discord OS Infrastructure Separation
Mode: dependency/install-state repair and verification
Status: partially restored

## Goal

Restore the Fitness repo verification baseline after Discord Route Decomposition Package 1, without moving code to DiscordOS or mutating live Supabase, Vercel, or Discord surfaces.

## Inputs

- `docs/ops/FITNESS-DISCORD-DECOMPOSITION-DEPENDENCY-GAP-2026-05-25.md`
- `docs/ops/DISCORD-ROUTE-DECOMPOSITION-PACKAGE-1-2026-05-25.md`
- `repos/fawxzzy-fitness/package.json`
- `repos/fawxzzy-fitness/package-lock.json`

## Starting Repo State

Preexisting tracked Fitness modifications remained present before this package:

- `repos/fawxzzy-fitness/package.json`
- `repos/fawxzzy-fitness/public/app/icon-192.png`
- `repos/fawxzzy-fitness/public/app/icon-512.png`
- `repos/fawxzzy-fitness/public/favicon-16x16.png`
- `repos/fawxzzy-fitness/public/favicon-32x32.png`
- `repos/fawxzzy-fitness/public/favicon.ico`
- `repos/fawxzzy-fitness/public/sw.js`
- `repos/fawxzzy-fitness/scripts/mobile_regression/__pycache__/__init__.cpython-313.pyc`
- `repos/fawxzzy-fitness/scripts/mobile_regression/__pycache__/board_builder.cpython-313.pyc`
- `repos/fawxzzy-fitness/src/generated/appBuildManifest.json`
- `repos/fawxzzy-fitness/src/lib/stretch-library-details.ts`
- `repos/fawxzzy-fitness/src/lib/stretch-library-summaries.ts`

## Commands Run

1. `npm ci`
2. `npm run sanity:quick`
3. `npm run typecheck`
4. `npm run build`
5. `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/runtime/route-domains.test.ts`
6. `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts`

## Results

### `npm ci`

Status: passed

- restored missing local packages under `node_modules`
- install-state diagnosis from the dependency-gap receipt was correct

### `npm run sanity:quick`

Status: passed with existing lint warnings

- no missing-binary failure remained
- warnings are in existing React hook lint surfaces, not Discord route decomposition regressions

### `npm run typecheck`

Status: failed

Remaining blocker after install restore:

- `src/lib/discord/interactions.test.ts:111`
- `src/lib/discord/interactions.test.ts:113`

Failure class:

- preexisting typing issue in a Discord interaction test surface
- not a missing package problem

This package also surfaced a narrow route import regression from the prior decomposition package. That regression was corrected in canonical Fitness commit:

- `e14ccc1f73d2ded033e0f214c9071082a7d1d94c`
- `fix: restore discord route import coverage`

After that correction, the remaining `typecheck` failure is limited to the test file above.

### `npm run build`

Status: passed

- Next production build completed successfully
- no missing `sharp` or `next` failure remained

### `route-domains.test.ts`

Status: passed

- the decomposition-specific domain dispatch tests remain green

### `interactions-route.test.ts`

Status: passed

- the existing full Discord route test suite no longer fails on missing `tweetnacl`
- route behavior remained intact through the decomposition plus import-coverage fix

## Missing Dependency Issue

Status: resolved

Resolved packages:

- `next`
- `typescript`
- `sharp`
- `tweetnacl`

## Package Metadata Changes

No unexpected dependency metadata changes were introduced by this package.

- `package-lock.json` remained unchanged
- `package.json` still shows a preexisting tracked modification, but this package did not introduce a new package metadata delta

## Fitness Source Changes In This Package

One narrow source fix was required during verification restore:

- `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`

Purpose:

- restore import coverage that the decomposition package had over-pruned
- bring the route back to the same runtime behavior already validated by the restored route test suite

## Current Repo State After Restore

Unrelated preexisting tracked Fitness changes still remain:

- `repos/fawxzzy-fitness/package.json`
- `repos/fawxzzy-fitness/public/app/icon-192.png`
- `repos/fawxzzy-fitness/public/app/icon-512.png`
- `repos/fawxzzy-fitness/public/favicon-16x16.png`
- `repos/fawxzzy-fitness/public/favicon-32x32.png`
- `repos/fawxzzy-fitness/public/favicon.ico`
- `repos/fawxzzy-fitness/public/sw.js`
- `repos/fawxzzy-fitness/scripts/mobile_regression/__pycache__/__init__.cpython-313.pyc`
- `repos/fawxzzy-fitness/scripts/mobile_regression/__pycache__/board_builder.cpython-313.pyc`
- `repos/fawxzzy-fitness/src/generated/appBuildManifest.json`
- `repos/fawxzzy-fitness/src/lib/stretch-library-details.ts`
- `repos/fawxzzy-fitness/src/lib/stretch-library-summaries.ts`

## Verdict

Verification restore is **mostly successful**:

- install-state gap is fixed
- lint command runs
- build passes
- decomposition-specific tests pass
- full Discord route tests pass

But the full Fitness verification baseline is **not yet fully clean** because:

- `npm run typecheck` still fails on `src/lib/discord/interactions.test.ts`

## Extraction Readiness

Next Discord runtime utility extraction remains **blocked** until one of these happens:

1. a narrow package fixes the remaining `src/lib/discord/interactions.test.ts` type errors, or
2. the lane explicitly accepts that test-type debt as a non-blocking baseline exception

Under the current rule, extraction should not resume yet.
