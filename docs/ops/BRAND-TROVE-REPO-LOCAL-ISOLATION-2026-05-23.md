# Trove Repo-Local Brand Drift Isolation

Date: 2026-05-23
Lane: Brand Asset Canonicalization
Mode: Inventory and isolation only
Status: Trove drift classified

## Goal

Separate Trove brand asset drift from unrelated Trove repo-local changes so a future Trove brand sync can be reviewed as a narrow package.

## Repo identity

- Path: `repos/fawxzzy-trove`
- Branch: `codex/trove-brand-asset-sync`
- HEAD: `bce14fcc1ad6e826b0c0eac37e13af6707ee3a8e`
- Ahead of upstream: `1` commit
- Ahead commit:
  - `bce14fc Add layered Fitness preview board`
- Remote:
  - `origin https://github.com/fawxzzy/fawxzzy-trove.git`

## Source inputs

- `git status --short`
- `git status --branch --short`
- `git diff --name-only`
- `git ls-files --others --exclude-standard`
- `docs/ops/BRAND-TROVE-DRIFT-ISOLATION-2026-05-23.md`

## Current Trove drift

### Modified tracked files

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

### Untracked files

- `docs/qa.md`
- `public/apps/fitness/icon-512.png`
- `qa/adapters/trove.web.json`
- `qa/scenarios/trove.home-smoke.json`

## Isolation classification

### Brand asset drift

These are the manifest-declared Trove public consumer targets and represent direct brand consumer drift:

- `public/brand/atlas-sigil-master.png`
- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/icons/apple-touch-icon.png`
- `public/favicon-32x32.png`
- `public/favicon-16x16.png`
- `public/favicon.ico`

Classification:

- `brand asset drift`

### App or source code changes

These files are not consumer assets and therefore cannot be silently bundled into a narrow brand sync:

- `src/app/layout.tsx`
- `src/components/catalog/app-section.tsx`

Observed intent:

- `src/app/layout.tsx`
  - adds `metadataBase`
  - adds explicit preview image metadata pointing at `/brand/atlas-sigil-master.png`
  - changes OG/Twitter metadata behavior
- `src/components/catalog/app-section.tsx`
  - replaces inline screenshot details markup with `AppPreview`

Classification:

- `app/source code changes`

### Vendored Fitness icon drift

These files sit outside the manifest-declared Trove public brand targets but still move icon-facing catalog surfaces:

- `public/apps/fitness/icon-192.png`
- `public/apps/fitness/icon-512.png`

Classification:

- `vendored Fitness icon drift`

### Docs and QA surfaces

These files are unrelated to the narrow brand-target sync surface:

- `docs/qa.md`
- `qa/adapters/trove.web.json`
- `qa/scenarios/trove.home-smoke.json`

Classification:

- `docs / QA surfaces`

### Generated residue

None identified inside the Trove repo root for this pass beyond the intentionally modified public consumer files.

Classification:

- `none`

### Unknown or manual review

No additional unknown files were found in this pass beyond the mixed categories above.

Classification:

- `none`

## Isolation assessment

### Can Trove brand drift be separated cleanly right now?

Not yet from the current repo state.

### Why

1. The brand-target files are already mixed with application behavior changes.
   The branch contains metadata and preview-surface code changes, not just stale asset files.

2. Vendored Fitness icon drift is bundled into the same local branch.
   That is a distinct catalog surface and should not be silently normalized as part of a public favicon or app-icon sync.

3. Docs and QA files are also untracked in the same workspace.
   They are not blocking by themselves, but they confirm the repo is carrying broader lane-local work than a narrow root-driven brand sync should absorb.

## Decision

- `defer Trove brand sync`

## Practical meaning

- Do not sync Trove brand assets from the ATLAS root yet.
- First run a Trove repo-local cleanup or isolation package that separates:
  - manifest brand consumer assets
  - vendored Fitness icon surfaces
  - source-code changes
  - docs and QA residue

## Recommended next Trove-local package

Run a Trove repo-local cleanup decision pass that answers:

1. whether the current code changes belong in this branch or should be split out
2. whether vendored Fitness icon changes belong in the same package as public brand assets
3. whether the branch should be narrowed before any ATLAS-root brand sync touches Trove at all
