# Fitness Brand Path Visibility Check

Date: 2026-05-23
Lane: Brand Asset Canonicalization
Mode: Read-only
Status: Fitness consumer visibility blocked in active root

## Goal

Verify whether `repos/fawxzzy-fitness` is visible and clean from the active ATLAS root session, and whether the declared brand target paths exist.

## Current root-path check

- Checked path: `repos/fawxzzy-fitness`
- Result: missing from the active root session

Because the repo root is absent, the following checks cannot be satisfied from this session:

- `git status`
- branch and HEAD verification
- target-path cleanliness
- manifest consumer target existence under the canonical repo root

## Declared Fitness consumer targets

From `branding/manifest.json`:

- `repos/fawxzzy-fitness/public/brand/atlas-sigil-master.png`
- `repos/fawxzzy-fitness/public/app/icon-192.png`
- `repos/fawxzzy-fitness/public/app/icon-512.png`
- `repos/fawxzzy-fitness/public/icons/icon-192.png`
- `repos/fawxzzy-fitness/public/icons/icon-512.png`
- `repos/fawxzzy-fitness/public/icons/apple-touch-icon.png`
- `repos/fawxzzy-fitness/public/favicon-32x32.png`
- `repos/fawxzzy-fitness/public/favicon-16x16.png`
- `repos/fawxzzy-fitness/public/favicon.ico`

## Visibility result

### Does `repos/fawxzzy-fitness` exist in this active root?

- no

### Are the brand target paths currently valid from this root?

- no

### Is a sync package allowed to fall back to `tmp/`?

- no

## Decision

- `defer Fitness brand sync pending canonical repo visibility`

## Why

1. Canonical repo restoration is already closed at the governance level, so this is not a source-truth dispute.
   The blocker is active root visibility, not canonical identity.

2. The manifest declarations are still correct.
   What is missing is the actual canonical repo path in this session.

3. `tmp/` remains forbidden as a substitute consumer target.
   Brand sync must wait for the canonical repo path to be visible and clean in the active root.

## Required precondition before Fitness brand sync

Re-run a root-path availability check and confirm all of the following:

1. `repos/fawxzzy-fitness` exists in the active root session
2. the repo is clean enough for a narrow brand package
3. the declared `public/**` target paths exist and are valid
4. no fallback path under `tmp/` is being considered
