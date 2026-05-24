# Trove Local State Split Package Plan

Date: 2026-05-23
Lane: Brand Asset Canonicalization
Mode: Planning only
Status: Package order defined

## Goal

Turn Trove's mixed working tree into reviewable package boundaries before any Trove brand asset sync is allowed.

## Current repo state

- Path: `repos/fawxzzy-trove`
- Branch: `codex/trove-brand-asset-sync`
- HEAD: `bce14fcc1ad6e826b0c0eac37e13af6707ee3a8e`
- Upstream status: `ahead 1`
- Ahead commit:
  - `bce14fc Add layered Fitness preview board`
- Remote:
  - `origin https://github.com/fawxzzy/fawxzzy-trove.git`

## Confirmed lane ownership

### Ahead commit ownership

`bce14fc Add layered Fitness preview board` belongs to:

- `Trove product preview board package`

It does not belong to the narrow Trove brand sync package.

## Current path assignment

### Trove product preview board package

- `src/app/layout.tsx`
- `src/components/catalog/app-section.tsx`
- existing ahead commit `bce14fc`
- any related preview-board source files already committed by that product lane

Reason:

- these files change metadata behavior, preview behavior, and application rendering
- they are product work, not pure asset normalization

### Trove brand sync package

- `public/brand/atlas-sigil-master.png`
- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/icons/apple-touch-icon.png`
- `public/favicon-32x32.png`
- `public/favicon-16x16.png`
- `public/favicon.ico`

Reason:

- these are the manifest-declared Trove public brand consumer targets
- they should be sourced only from ATLAS canonical branding outputs

### Vendored Fitness icon package

- `public/apps/fitness/icon-192.png`
- `public/apps/fitness/icon-512.png`

Reason:

- these are Trove-local vendored catalog assets, not Trove public brand targets
- they should not be silently bundled into a favicon or app-icon sync package

### Docs / QA package

- `docs/qa.md`
- `qa/adapters/trove.web.json`
- `qa/scenarios/trove.home-smoke.json`

Reason:

- these are repo-level documentation and QA contract surfaces unrelated to brand asset sync

## Safe package order

1. `Trove product preview board package`
2. `Docs / QA package`
3. `Vendored Fitness icon package`
4. `Trove brand sync package`

## Why this order

1. Product behavior changes should settle first.
   The branch is already ahead by one product commit, and the currently modified source files continue that lane.

2. Docs and QA surfaces are independent from brand asset normalization.
   They can be reviewed and parked without entangling icon or favicon diffs.

3. Vendored Fitness icons are catalog content, not Trove public brand surface.
   Their intent should be explicit before public brand assets are refreshed.

4. Brand sync should be last.
   Only after the other lanes are isolated can the Trove public brand assets become a narrow, reviewable consumer-sync package.

## What must be preserved before brand sync

Before any Trove brand sync package is attempted, preserve or isolate:

- current product/source changes on `codex/trove-brand-asset-sync`
- QA files under `docs/qa.md` and `qa/**`
- vendored Fitness icon surfaces under `public/apps/fitness/**`

## What must be stashed or parked first

Brand sync can only proceed once non-brand Trove drift is no longer mixed into the same working state. That means one of these must happen first:

1. commit the product/source lane separately
2. commit or park the docs/QA lane separately
3. commit or park the vendored Fitness icon lane separately
4. or move the remaining public brand-target edits into their own clean working state

## Brand sync decision

- `brand sync cannot proceed now`

## Exact future boundary rule

When the Trove brand sync package finally runs, it should contain only:

- `public/brand/atlas-sigil-master.png`
- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/icons/apple-touch-icon.png`
- `public/favicon-32x32.png`
- `public/favicon-16x16.png`
- `public/favicon.ico`

and no source code, vendored Fitness icons, docs, or QA surfaces.
