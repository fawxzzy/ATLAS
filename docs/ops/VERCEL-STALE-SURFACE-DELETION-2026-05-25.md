# Vercel Stale Surface Deletion

Date: 2026-05-25
Lane: Duplicate Surface Decommission / Manual Deploy Exception Burn-Down
Mode: bounded project deletion
Status: completed

## Goal

Remove the two dependency-cleared stale Spotify/board Vercel projects so they stop creating deploy-authority noise and duplicate-surface pressure.

## Inputs

- `docs/ops/VERCEL-STALE-SURFACE-DELETION-READINESS-2026-05-25.md`
- canonical active Fitness project:
  - name: `fawxzzy-fitness`
  - id: `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`

## Deleted Targets

- `spotify-club-phase-7-interaction-reliability`
  - project id: `prj_RGLW6lMbxlBbbltdzLHVGpyejI9h`
  - prior alias family included `spotify-club-phase-7-interaction-re.vercel.app`
- `spotify-board-hygiene-main`
  - project id: `prj_UB4thVPyHdZdZdtTC8lDggWauTZE`
  - prior alias family included `spotify-board-hygiene-main.vercel.app`

## Mutation Performed

Deleted both projects through the Vercel API/CLI after the read-only dependency pass approved deletion.

## Verification

Verified deletion in two ways:

1. team project listing no longer includes either project
2. direct Vercel API lookup for each deleted project id returns `404`

## What Did Not Change

- no canonical Fitness Vercel project change
- no OAuth callback change
- no Discord runtime change
- no Supabase mutation
- no bot restart

## Remaining Pressure

This does not fully close duplicate-surface pressure.

Remaining known duplicate-pressure Vercel surface:

- `fitness-deploy-green-panels`

## Result

The two stale Spotify-era Vercel projects are now removed from the live project set. Current-state and approval-gate ATLAS Book surfaces should reflect that stale Vercel deletion is no longer an open gate for these deleted targets.
