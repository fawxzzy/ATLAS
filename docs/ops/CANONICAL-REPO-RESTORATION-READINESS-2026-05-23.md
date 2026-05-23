# Canonical Repo Restoration Readiness

Date: 2026-05-23
Lane: Canonical Repo Restoration + Tmp Dependency Elimination
Status: local operator readiness checkpoint

## Goal

Make the restored canonical Fitness repo at `repos/fawxzzy-fitness` usable for local verification without relying on `tmp` checkouts as the active source surface.

## Canonical Repo Identity

Verified from `repos/fawxzzy-fitness`:

- branch: `main`
- remote: `https://github.com/fawxzzy/fawxzzy-fitness.git`
- HEAD: `7ceebde9d71564614df98e391b245a836d15c401`
- working tree after cleanup: clean

This matches the live production-linked checkout at `tmp/fawxzzy-fitness-main-prod-source-3d00eac7`, which is also on:

- branch: `main`
- HEAD: `7ceebde9d71564614df98e391b245a836d15c401`

## Dependency Install Status

Install command used:

- `npm ci`

Result:

- passed
- `node_modules` restored successfully
- repo hooks installed through `scripts/setup-githooks.mjs`

Notes:

- install emitted dependency vulnerability warnings, but it did not block local operator readiness
- no package manifest changes were required

## Vercel Link Status

Checked local canonical repo path:

- `.vercel/project.json`

Result:

- missing

Interpretation:

- canonical Vercel identity is still known and documented:
  - project: `fawxzzy-fitness`
  - project id: `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- local Vercel link state has not yet been restored at the canonical repo root
- this is a local operator-readiness gap, not a source identity gap

## Supabase Identity Status

Canonical production-aligned Supabase identity remains:

- project ref: `lpswxoyfniocuhljgzbc`
- host: `lpswxoyfniocuhljgzbc.supabase.co`

Status:

- documented and unchanged
- no Supabase mutation was performed in this readiness pass

## Verification Results

### 1. Sanity gate

Command:

- `npm run sanity:quick`

Result:

- passed

Observed output:

- lint completed successfully
- pre-existing React hook lint warnings remain, but they did not fail the command

### 2. Typecheck gate

Command:

- `npm run typecheck`

Result:

- passed

### 3. Build gate

Command:

- `npm run build`

Result:

- passed

Observed behavior:

- build prepare completed successfully
- Next.js production build completed successfully
- lint warnings remained non-blocking during build

## Build Residue Cleanup

The build temporarily regenerated tracked repo outputs:

- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/favicon-16x16.png`
- `public/favicon-32x32.png`
- `public/favicon.ico`
- `public/sw.js`
- `src/generated/appBuildManifest.json`
- `src/lib/stretch-library-details.ts`
- `src/lib/stretch-library-summaries.ts`

These changes were local build byproducts from readiness verification, not intended product edits.

Cleanup performed:

- restored all generated file changes
- canonical repo working tree returned to clean

## Tmp Dependency Status

What no longer requires `tmp`:

- local dependency install
- lint/sanity verification
- typecheck verification
- production build verification
- canonical Git lineage comparison

What may still rely on non-canonical local state:

- local Vercel project linkage at the canonical repo root
- any operator flow that expects `.vercel/project.json` to exist locally
- any secrets or env workflow still documented around the previous `tmp` lane

Current verdict:

- `tmp` is no longer required for basic repo-local verification
- `tmp` may still be serving as a fallback reference for local deploy/linkage material until canonical local Vercel linkage is restored

## Blockers Before 100%

1. restore local Vercel link state for `repos/fawxzzy-fitness`
2. confirm `_stack` deploy and verify flows succeed against the restored canonical repo root rather than the `tmp` checkout
3. confirm no remaining production-critical operator lane still resolves Fitness through `tmp`
4. only after those checks pass should the active `tmp` production-linked checkout stop being treated as a live dependency

## Closeout Verdict

Canonical repo restoration is now operator-ready for local verification:

- install works
- sanity works
- typecheck works
- build works
- repo returns to clean after verification cleanup

The remaining gap is not source health. It is local operator linkage and final `tmp` dependency burn-down.
