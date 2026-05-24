# Fitness Brand Sync Readiness

Date: 2026-05-24
Lane: Brand Asset Canonicalization
Mode: read-only
Status: safe to sync

## Goal

Confirm that Fitness can safely receive canonical brand assets from the ATLAS root after the canonical child repo path repair.

## Canonical Repo Checks

Verified at `repos/fawxzzy-fitness`:

- path exists:
  - yes
- branch:
  - `main`
- remote:
  - `https://github.com/fawxzzy/fawxzzy-fitness.git`
- HEAD:
  - `7ceebde9d71564614df98e391b245a836d15c401`
- working tree before sync:
  - clean

## Local Vercel Link Check

Verified locally:

- `.vercel/project.json`
  - exists
  - ignored by `.gitignore`
  - points to project `fawxzzy-fitness`
  - project id `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`

## Manifest Consumer Path Check

All declared Fitness consumer target paths from `branding/manifest.json` exist:

- `public/brand/atlas-sigil-master.png`
- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/icons/icon-192.png`
- `public/icons/icon-512.png`
- `public/icons/apple-touch-icon.png`
- `public/favicon-32x32.png`
- `public/favicon-16x16.png`
- `public/favicon.ico`

## Drift Check

Using a Fitness-only manifest slice against `branding/scripts/sync-brand-assets.mjs --dry-run`:

- current:
  - `public/brand/atlas-sigil-master.png`
  - `public/app/icon-192.png`
  - `public/app/icon-512.png`
  - `public/favicon-32x32.png`
  - `public/favicon-16x16.png`
  - `public/favicon.ico`
- stale:
  - `public/icons/icon-192.png`
  - `public/icons/icon-512.png`
  - `public/icons/apple-touch-icon.png`

## Tmp Check

- no `tmp` surface is needed
- `tmp` remains forbidden as a brand sync target

## Decision

- `safe to sync`

## Scope for Next Package

The narrow Fitness brand sync package should update only the manifest-declared stale Fitness consumer targets and no product code:

- `public/icons/icon-192.png`
- `public/icons/icon-512.png`
- `public/icons/apple-touch-icon.png`
