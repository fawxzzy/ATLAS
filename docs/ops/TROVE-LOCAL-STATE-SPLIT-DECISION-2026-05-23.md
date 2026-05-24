# Trove Local State Split Decision

Date: 2026-05-23
Lane: Brand Asset Canonicalization
Mode: Decision only
Status: Split boundaries defined

## Goal

Decide how to split Trove's mixed local working state before any Trove brand asset sync is allowed.

## Repo identity

- Path: `repos/fawxzzy-trove`
- Branch: `codex/trove-brand-asset-sync`
- HEAD: `bce14fcc1ad6e826b0c0eac37e13af6707ee3a8e`
- Upstream status: `ahead 1`
- Ahead commit:
  - `bce14fc Add layered Fitness preview board`
- Remote:
  - `origin https://github.com/fawxzzy/fawxzzy-trove.git`

## Current changed paths

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

## Path classification

| Path | Classification | Why |
| --- | --- | --- |
| `public/brand/atlas-sigil-master.png` | brand sync candidate | manifest-declared Trove brand master consumer target |
| `public/app/icon-192.png` | brand sync candidate | manifest-declared Trove app icon consumer target |
| `public/app/icon-512.png` | brand sync candidate | manifest-declared Trove app icon consumer target |
| `public/icons/apple-touch-icon.png` | brand sync candidate | manifest-declared Trove apple-touch consumer target |
| `public/favicon-32x32.png` | brand sync candidate | manifest-declared Trove favicon consumer target |
| `public/favicon-16x16.png` | brand sync candidate | manifest-declared Trove favicon consumer target |
| `public/favicon.ico` | brand sync candidate | manifest-declared Trove favicon consumer target |
| `src/app/layout.tsx` | app/source lane | changes metadataBase and OG/Twitter preview behavior; not a pure asset sync |
| `src/components/catalog/app-section.tsx` | app/source lane | replaces inline preview section with `AppPreview`; behavioral UI change |
| `public/apps/fitness/icon-192.png` | vendored Fitness icon lane | Trove-local vendored Fitness card asset, not a manifest public brand target |
| `public/apps/fitness/icon-512.png` | vendored Fitness icon lane | untracked vendored Fitness card asset, not a manifest public brand target |
| `docs/qa.md` | docs / QA lane | repo documentation surface unrelated to narrow brand sync |
| `qa/adapters/trove.web.json` | docs / QA lane | repo-owned QA adapter contract |
| `qa/scenarios/trove.home-smoke.json` | docs / QA lane | repo-owned QA scenario contract |

## Ahead commit classification

### `bce14fc Add layered Fitness preview board`

Changed files in the commit:

- `src/app/apps/fitness/preview/page.tsx`
- `src/components/catalog/app-preview.tsx`
- `src/components/catalog/fitness-preview-board.tsx`
- `src/data/fitness-preview-board.ts`

Decision:

- `product work`, not `brand work`

Why:

- the commit introduces or changes preview-board source surfaces
- it does not represent a narrow public icon/favicon/brand asset sync
- it belongs to Trove product behavior and presentation, even if it is adjacent to the Fitness card surface

## Can brand sync proceed now?

- no

## Why not

1. Trove's working tree is not narrowed to manifest consumer targets.
   Public brand assets are mixed with source behavior changes, vendored Fitness icon drift, and QA surfaces.

2. The ahead commit is product work.
   That means the branch already carries non-brand intent before any new root-driven sync would be added.

3. Vendored Fitness icons are a separate lane from public Trove brand consumers.
   They should not be silently absorbed into a favicon/app-icon sync package.

## What must be isolated first

### Before any Trove brand sync

One of the following must happen:

1. brand-target files move into their own narrow Trove package or branch
2. product/source changes are committed or parked separately
3. vendored Fitness icons are classified into a separate Trove catalog lane
4. docs and QA residue are committed or parked separately

## Exact future package boundaries

### Package A: Trove product/source lane

Scope:

- `src/app/layout.tsx`
- `src/components/catalog/app-section.tsx`
- any related preview-board source files if they are still part of the intended Trove product change
- possibly the ahead commit `bce14fc` if it remains the active product lane

### Package B: Trove public brand consumer sync lane

Scope:

- `public/brand/atlas-sigil-master.png`
- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/icons/apple-touch-icon.png`
- `public/favicon-32x32.png`
- `public/favicon-16x16.png`
- `public/favicon.ico`

Constraint:

- should be sourced from ATLAS canonical branding outputs only

### Package C: Trove vendored Fitness icon lane

Scope:

- `public/apps/fitness/icon-192.png`
- `public/apps/fitness/icon-512.png`

Constraint:

- do not mix with Trove public favicon or app-icon sync unless explicitly governed as one package

### Package D: Trove docs and QA lane

Scope:

- `docs/qa.md`
- `qa/adapters/trove.web.json`
- `qa/scenarios/trove.home-smoke.json`

## Decision summary

- brand sync cannot proceed from the current Trove branch state
- the ahead-by-1 commit belongs to Trove product work, not brand work
- Trove needs a repo-local split before the ATLAS brand lane may touch Trove consumer assets
