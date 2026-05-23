# Trove Brand Drift Isolation

Date: 2026-05-23
Lane: Brand Asset Canonicalization
Mode: Read-only
Status: Trove consumer reviewed

## Goal

Determine whether Trove can safely receive ATLAS brand asset sync without mixing unrelated repo-local drift.

## Repo identity

- Path: `repos/fawxzzy-trove`
- Branch: `codex/trove-brand-asset-sync`
- HEAD: `bce14fcc1ad6e826b0c0eac37e13af6707ee3a8e`
- Remote: `https://github.com/fawxzzy/fawxzzy-trove.git`

## Repo-local rules

Trove's repo rules explicitly require:

- use ATLAS branding pipeline outputs that sync into `public/`
- do not create repo-owned canonical app icons
- keep `.vercel/` and pulled env files local-only

## Current drift

Modified files:

- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/apps/fitness/icon-192.png`
- `public/brand/atlas-sigil-master.png`
- `public/favicon-16x16.png`
- `public/favicon-32x32.png`
- `public/favicon.ico`
- `public/icons/apple-touch-icon.png`
- `src/app/layout.tsx`
- `src/components/catalog/app-section.tsx`

Untracked files or directories:

- `docs/qa.md`
- `public/apps/fitness/icon-512.png`
- `qa/`

## Brand-target overlap

Manifest-declared Trove consumer targets:

- `public/brand/atlas-sigil-master.png`
- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/icons/apple-touch-icon.png`
- `public/favicon-32x32.png`
- `public/favicon-16x16.png`
- `public/favicon.ico`

Observed overlap:

- all declared Trove public brand targets are already locally modified

Additional related drift:

- vendored Fitness card icon drift in `public/apps/fitness/**`
- non-brand code drift in:
  - `src/app/layout.tsx`
  - `src/components/catalog/app-section.tsx`
- docs and QA residue outside the manifest consumer set

## Isolation assessment

### Can stale brand assets be isolated from unrelated Trove changes?

Not safely from the current repo state without a dedicated isolation step.

### Why

1. Trove is already on a mixed working branch.
   The branch carries modified public brand assets plus modified application code and untracked QA/docs surfaces.

2. The stale brand assets are not the only local truth in play.
   Any direct root-driven sync would land into a repo that is already carrying unrelated branch work.

3. Vendored Fitness icon drift is already mixed into the same workspace.
   That adds another brand-adjacent surface that should not be silently normalized as part of a simple public-asset sync.

## Decision

- `needs stash/isolation`

## Practical meaning

- Do not sync Trove brand assets from the ATLAS root yet.
- First isolate the Trove repo-local drift into a narrow package or intentionally park the unrelated code/docs/QA changes.
- Only after the repo is narrowed to the manifest consumer targets should a Trove brand sync package run.

## Recommended next Trove-specific package

Run a Trove repo-local isolation pass that decides whether:

1. current code changes stay on `codex/trove-brand-asset-sync`
2. brand-target updates move into their own narrow branch or package
3. vendored Fitness card icons belong in the same package or a separate Trove catalog surface pass
