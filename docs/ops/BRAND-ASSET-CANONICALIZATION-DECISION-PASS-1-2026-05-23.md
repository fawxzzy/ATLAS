# Brand Asset Canonicalization Decision Pass 1

Date: 2026-05-23
Lane: Brand Asset Canonicalization
Mode: Decision only
Status: Pass 1 complete

## Purpose

This pass decides which declared brand consumers are valid sync targets from the current ATLAS root and which must wait for lane isolation or root-path availability.

## Inputs used

- `branding/manifest.json`
- `docs/ops/BRAND-ASSET-CANONICALIZATION-INVENTORY-2026-05-23.md`
- `docs/ops/BRAND-CONSUMER-VALIDITY-PREFLIGHT-2026-05-23.md`
- current repo status for `_stack`, Trove, and Fitness
- `node branding/scripts/sync-brand-assets.mjs --dry-run`

## Decision summary

| Consumer | Decision | Why |
| --- | --- | --- |
| `_stack` launcher icon | syncable as narrow package | consumer target exists, drift is narrow, and repo-local dirt is confined to the target asset itself |
| Trove public brand/icon/favicon surfaces | wait | consumer targets exist, but repo already carries broader local code/docs drift, so sync would mix brand updates with unrelated repo-local work |
| Fitness brand/icon/favicon surfaces | blocked | declared consumer targets are absent because `repos/fawxzzy-fitness` is not currently visible from this root session |

## Consumer decisions

### `_stack` launcher icon

- Current target: `repos/_stack/ops/assets/release-launcher.ico`
- Current status: stale
- Repo status:
  - exists: yes
  - branch: `main`
  - dirty delta: `M ops/assets/release-launcher.ico`

#### Decision

- `sync now as narrow package` is allowed

#### Why

- the target exists
- the drift is exactly on the launcher icon surface the manifest intends to own
- there is no evidence here of broader `_stack` repo-local churn that would make a narrow asset-sync package ambiguous

#### Constraint

- do not mix this with Trove or Fitness sync
- package `_stack` launcher asset sync separately if chosen

### Trove public brand/icon/favicon consumers

- Current targets:
  - `repos/fawxzzy-trove/public/brand/atlas-sigil-master.png`
  - `repos/fawxzzy-trove/public/app/icon-192.png`
  - `repos/fawxzzy-trove/public/app/icon-512.png`
  - `repos/fawxzzy-trove/public/icons/apple-touch-icon.png`
  - `repos/fawxzzy-trove/public/favicon-32x32.png`
  - `repos/fawxzzy-trove/public/favicon-16x16.png`
  - `repos/fawxzzy-trove/public/favicon.ico`
- Current status: stale
- Repo status:
  - exists: yes
  - branch: `codex/trove-brand-asset-sync`
  - broader local drift includes:
    - modified app code
    - modified brand targets
    - vendored Fitness icon drift
    - untracked docs and QA surfaces

#### Decision

- `wait for repo-local isolation package`

#### Why

- the asset targets are valid and stale
- but the repo is already in a mixed local state, so root-driven sync would not produce a narrow brand-only change set
- Trove needs its own brand-isolation package or repo-local cleanup decision first

#### Constraint

- do not sync Trove assets from the ATLAS root until the repo-local drift is isolated

### Fitness brand/icon/favicon consumers

- Declared targets:
  - `repos/fawxzzy-fitness/public/brand/atlas-sigil-master.png`
  - `repos/fawxzzy-fitness/public/app/icon-192.png`
  - `repos/fawxzzy-fitness/public/app/icon-512.png`
  - `repos/fawxzzy-fitness/public/icons/icon-192.png`
  - `repos/fawxzzy-fitness/public/icons/icon-512.png`
  - `repos/fawxzzy-fitness/public/icons/apple-touch-icon.png`
  - `repos/fawxzzy-fitness/public/favicon-32x32.png`
  - `repos/fawxzzy-fitness/public/favicon-16x16.png`
  - `repos/fawxzzy-fitness/public/favicon.ico`
- Current status: missing from this root session
- Repo status:
  - `repos/fawxzzy-fitness` does not currently exist under `repos/`

#### Decision

- `blocked pending root-path availability check`

#### Why

- canonical repo restoration is already closed at the governance level, but this root session still does not see the declared Fitness repo target
- sync must not redirect into `tmp/` or an alternate checkout just to satisfy the manifest
- the immediate blocker is session or root-path visibility, not source-truth uncertainty

#### Constraint

- before any Fitness brand sync, re-run a root-path availability check and verify:
  - `repos/fawxzzy-fitness` exists
  - the repo is clean enough for a narrow sync package
  - the manifest target paths are present and valid

## Preview and cache verification implications

Later verification should cover these surfaces separately after any real sync:

- `_stack` launcher icon
- Trove PWA install icons
- Trove favicon/browser preview surfaces
- Trove OG/Twitter preview image via `/brand/atlas-sigil-master.png`
- Fitness PWA and preview surfaces, but only after Fitness target validity is restored in this root

## Decision conclusion

1. `_stack` is the only consumer that is currently eligible for immediate narrow packaging.
2. Trove is a valid but blocked consumer because of mixed repo-local drift.
3. Fitness is a declared but currently unavailable consumer from this root session, so it must not be satisfied via `tmp`.

## Recommended next package

Choose one of these next, without mixing them:

1. `_stack` launcher icon sync package
2. Trove brand-isolation package inside `repos/fawxzzy-trove`
3. Fitness root-path visibility recheck before any Fitness brand sync decision
