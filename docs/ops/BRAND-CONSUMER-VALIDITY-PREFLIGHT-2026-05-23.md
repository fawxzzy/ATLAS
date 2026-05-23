# Brand Consumer Validity Preflight

Date: 2026-05-23
Lane: Brand Asset Canonicalization
Mode: Read-only preflight
Status: Initial consumer validity check complete

## Purpose

This preflight determines which declared brand consumers are valid sync targets from the current ATLAS root without writing any assets.

## Inputs checked

- `branding/manifest.json`
- `branding/scripts/sync-brand-assets.mjs --dry-run`
- `repos/_stack`
- `repos/fawxzzy-trove`
- `repos/fawxzzy-fitness`
- current root residue

## Current root facts

- `branding/**` is the active local lane residue.
- `archive/` remains intentionally untracked and out of scope.
- `repos/fawxzzy-fitness` is not present under `C:/ATLAS/repos` in this root session.
- `_stack` and Trove consumer targets do exist locally.

## Consumer validity table

| Consumer group | Path valid? | Repo exists? | Repo clean? | Consumer status | Safe to sync now? | Blocked reason if not |
| --- | --- | --- | --- | --- | --- | --- |
| `_stack` launcher ico | yes | yes | no | stale | conditional yes | `repos/_stack` is already dirty in `ops/assets/release-launcher.ico`, so sync is technically possible but should be packaged as a narrow `_stack` asset update, not silently written from the root |
| Trove brand master | yes | yes | no | stale | no | `repos/fawxzzy-trove` already has broader local residue beyond the stale assets, including code and docs changes, so asset sync would mix with unrelated repo-local drift unless isolated there |
| Trove app icons and favicons | yes | yes | no | stale | no | same reason as Trove brand master; consumer targets exist, but the repo is already dirty outside the sync surface |
| Trove Fitness vendored icons | partial | yes | no | mixed | no | `public/apps/fitness/icon-192.png` is modified and `icon-512.png` is untracked, so vendored consumer state is already mid-drift and should be handled in a dedicated Trove package |
| Fitness brand master | no | no | n/a | missing | no | declared target path is absent because `repos/fawxzzy-fitness` is missing from this root session |
| Fitness app icons and favicons | no | no | n/a | missing | no | same as above; do not redirect sync into `tmp/` or alternate checkouts |

## Dry-run consumer results

From `node branding/scripts/sync-brand-assets.mjs --dry-run`:

- stale:
  - `repos/_stack/ops/assets/release-launcher.ico`
  - `repos/fawxzzy-trove/public/brand/atlas-sigil-master.png`
  - `repos/fawxzzy-trove/public/app/icon-192.png`
  - `repos/fawxzzy-trove/public/app/icon-512.png`
  - `repos/fawxzzy-trove/public/icons/apple-touch-icon.png`
  - `repos/fawxzzy-trove/public/favicon-32x32.png`
  - `repos/fawxzzy-trove/public/favicon-16x16.png`
  - `repos/fawxzzy-trove/public/favicon.ico`
- missing:
  - all declared `repos/fawxzzy-fitness/public/**` consumer targets in the manifest

## Repo cleanliness and target validity

### `_stack`

- Exists: yes
- Branch: `main`
- Dirty state:
  - `M ops/assets/release-launcher.ico`
- Interpretation:
  - consumer target exists and is exactly the stale output the branding manifest expects to replace
  - repo-local state is narrow enough that a later `_stack` asset-sync package is viable

### Trove

- Exists: yes
- Branch: `codex/trove-brand-asset-sync`
- Dirty state includes:
  - stale public asset targets
  - modified code files:
    - `src/app/layout.tsx`
    - `src/components/catalog/app-section.tsx`
  - untracked and docs surfaces:
    - `docs/qa.md`
    - `public/apps/fitness/icon-512.png`
    - `qa/`
- Interpretation:
  - target asset paths are valid
  - repo is not clean enough to call sync safe from the ATLAS root without first isolating the Trove lane

### Fitness

- Exists under `repos/`: no
- Interpretation:
  - the manifest target declarations are fine, but they are not currently actionable from this root session
  - brand sync must not write into `tmp/` or alternate checkouts just to satisfy the manifest
  - this is now a consumer-validity blocker, not a source-asset blocker

## Preflight conclusion

1. Brand source truth is ready; consumer validity is not.
   The canonical brand source and generator surfaces are already defined and present.

2. `_stack` is the only consumer that looks close to syncable from current root.
   Even there, sync should happen as a narrow `_stack` package, not as an implicit root-side write.

3. Trove is blocked by mixed local repo drift.
   The stale consumer assets are real, but they are sitting inside an already-dirty repo branch with additional code and doc changes.

4. Fitness is blocked by target absence in this root.
   From this root session, any attempt to satisfy the manifest by writing into `tmp/` would violate the canonical-source rules.

## Recommended next package

Run a `Brand Asset Canonicalization Decision Pass` that decides:

1. whether to package `_stack` launcher icon sync separately now
2. whether Trove brand sync must wait for a repo-local isolation package in `repos/fawxzzy-trove`
3. whether the missing `repos/fawxzzy-fitness` consumer target should reopen a root-path availability check before any Fitness brand sync is allowed
