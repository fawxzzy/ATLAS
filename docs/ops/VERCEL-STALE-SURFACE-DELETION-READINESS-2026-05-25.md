# Vercel Stale Surface Deletion Readiness

Date: 2026-05-25
Lane: Duplicate Surface Decommission / Manual Deploy Exception Burn-Down
Mode: read-only dependency check
Status: delete approved

## Goal

Confirm whether the two known stale Spotify/board Vercel projects can be deleted without breaking current Fitness, Discord, OAuth, or release flows.

## Targets

- `spotify-club-phase-7-interaction-reliability`
- `spotify-club-phase-7-interaction-re.vercel.app`
- `spotify-board-hygiene-main`
- `spotify-board-hygiene-main.vercel.app`

## Canonical Active Project

Current canonical Fitness project:

- name: `fawxzzy-fitness`
- project id: `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- production alias: `fawxzzy-fitness-local.vercel.app`

## Dependency Check Scope

Inspected:

- ATLAS docs
- Fitness repo code and docs
- DiscordOS repo bootstrap surface
- current Vercel project metadata
- known canonical Fitness project references

## Findings

### 1. Current code references

No current code references were found for either stale project name or alias in:

- `repos/fawxzzy-fitness`
- `repos/DiscordOS`

### 2. Current active docs references

References to the stale surfaces were found only in:

- ATLAS inventory receipts
- ATLAS current-state/system-map pressure notes

These are historical or planning references, not live runtime dependencies.

### 3. Canonical active surface references

Current active references continue to point at:

- `fawxzzy-fitness-local.vercel.app`
- `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`

### 4. OAuth / bot / Discord dependency

No current repo or docs evidence was found that:

- Spotify OAuth callbacks depend on the stale aliases
- Discord update or feedback workflows depend on the stale aliases
- bot/runtime flows depend on the stale aliases

### 5. Vercel state

Both stale projects were still real Vercel projects with READY production deployments, but they were already identified as:

- non-canonical
- `live=false`
- old Spotify/board work outside the canonical Fitness deploy surface

## Decision

- `spotify-club-phase-7-interaction-reliability`: delete approved
- `spotify-board-hygiene-main`: delete approved

## Why Delete Is Safe

- no current code dependency found
- no current canonical docs or release path dependency found
- canonical production truth is already elsewhere
- the remaining references are historical receipts that can be updated or preserved as history after deletion

## Follow-On Requirement

After deletion:

- update current-state and approval-gate book surfaces so they no longer describe stale Vercel deletion as a still-open gate
- preserve the inventory receipts as historical evidence
