# Brand Root Residue Classification

Date: 2026-05-23
Lane: Brand Asset Canonicalization
Mode: Inventory and classification only
Status: Residue classified

## Purpose

This pass classifies the remaining modified `branding/**` files in the ATLAS root so later brand packages can separate:

- canonical source updates
- generated outputs intended for downstream consumers
- consumer sync inputs already used by a narrow package
- preview or cache verification inputs
- residue that still needs explicit review before commit

No assets were regenerated, overwritten, deleted, or synced in this pass.

## Inputs checked

- `git status --short`
- `branding/manifest.json`
- `docs/ops/BRAND-STACK-LAUNCHER-SYNC-2026-05-23.md`
- `docs/ops/BRAND-ASSET-CANONICALIZATION-INVENTORY-2026-05-23.md`
- `docs/ops/BRAND-CONSUMER-VALIDITY-PREFLIGHT-2026-05-23.md`
- `docs/ops/BRAND-ASSET-CANONICALIZATION-DECISION-PASS-1-2026-05-23.md`

## Current residue set

Modified `branding/**` paths:

- `branding/source/atlas-sigil-master.png`
- `branding/source/atlas-sigil-master.ico`
- `branding/generated/png/atlas-sigil-1024.png`
- `branding/generated/png/atlas-sigil-512.png`
- `branding/generated/png/atlas-sigil-256.png`
- `branding/generated/app/icon-192.png`
- `branding/generated/app/icon-512.png`
- `branding/generated/favicon/apple-touch-icon.png`
- `branding/generated/favicon/favicon-32x32.png`
- `branding/generated/favicon/favicon-16x16.png`
- `branding/generated/favicon/favicon.ico`
- `branding/generated/ico/atlas-sigil-core-launcher.ico`

Out-of-scope local residue remains:

- `archive/`

## Classification table

| Path | Manifest role | Classification | Why | Downstream relevance |
| --- | --- | --- | --- | --- |
| `branding/source/atlas-sigil-master.png` | canonical source | canonical source | Declared in `brand.canonical.png` and reused by Fitness/Trove brand-master consumers | Direct source for live app brand images, preview surfaces, and downstream vendored brand copies |
| `branding/source/atlas-sigil-master.ico` | canonical source | canonical source | Declared in `brand.canonical.ico` and used for launcher/ico lineage | Direct source for generated ico outputs and launcher surface lineage |
| `branding/generated/png/atlas-sigil-1024.png` | output | generated output | Declared in `outputs` and derived from canonical source | Large shared output for downstream packaging and preview-capable surfaces |
| `branding/generated/png/atlas-sigil-512.png` | output | generated output | Declared in `outputs` and derived from canonical source | Shared app and preview-support asset lineage |
| `branding/generated/png/atlas-sigil-256.png` | output | generated output | Declared in `outputs` and derived from canonical source | Shared medium-size generated asset for downstream use |
| `branding/generated/app/icon-192.png` | output | generated output; preview/cache verification input | Declared output and direct source for Fitness/Trove app/public icon consumers | Affects PWA install/icon surfaces and later client cache verification |
| `branding/generated/app/icon-512.png` | output | generated output; preview/cache verification input | Declared output and direct source for Fitness/Trove app/public icon consumers | Affects PWA install/icon surfaces and later client cache verification |
| `branding/generated/favicon/apple-touch-icon.png` | output | generated output; preview/cache verification input | Declared output and direct source for consumer apple-touch targets | Affects iOS/home-screen surfaces and later cache verification |
| `branding/generated/favicon/favicon-32x32.png` | output | generated output; preview/cache verification input | Declared output and direct source for consumer favicon targets | Affects browser/favicon/share-adjacent surfaces |
| `branding/generated/favicon/favicon-16x16.png` | output | generated output; preview/cache verification input | Declared output and direct source for consumer favicon targets | Affects browser/favicon surfaces |
| `branding/generated/favicon/favicon.ico` | output | generated output; preview/cache verification input | Declared output and direct source for consumer favicon targets | Affects browser/favicon chip and unfurl-adjacent surfaces |
| `branding/generated/ico/atlas-sigil-core-launcher.ico` | output | generated output; consumer sync input | Declared output and already used as the exact source for the narrow `_stack` launcher sync package | Affects `_stack` launcher/operator icon surface |

## Residue interpretation

### Canonical source residue

These files represent canonical source state rather than downstream sync byproducts:

- `branding/source/atlas-sigil-master.png`
- `branding/source/atlas-sigil-master.ico`

They should not be treated as stale consumer drift. Any later package that stages them is implicitly making a canonical branding-source claim.

### Generated output residue

These files are declared manifest outputs and should be treated as generated artifacts derived from the canonical source:

- `branding/generated/png/atlas-sigil-1024.png`
- `branding/generated/png/atlas-sigil-512.png`
- `branding/generated/png/atlas-sigil-256.png`
- `branding/generated/app/icon-192.png`
- `branding/generated/app/icon-512.png`
- `branding/generated/favicon/apple-touch-icon.png`
- `branding/generated/favicon/favicon-32x32.png`
- `branding/generated/favicon/favicon-16x16.png`
- `branding/generated/favicon/favicon.ico`
- `branding/generated/ico/atlas-sigil-core-launcher.ico`

These are not downstream consumer assets themselves. They are upstream generated outputs that downstream repos consume.

### Consumer sync input already exercised

One residue file has already been used in a committed narrow sync package:

- `branding/generated/ico/atlas-sigil-core-launcher.ico`

That file fed the committed `_stack` launcher sync recorded in:

- `docs/ops/BRAND-STACK-LAUNCHER-SYNC-2026-05-23.md`

Its presence as local residue does not indicate unresolved `_stack` consumer drift. It indicates that the root branding lane still contains the uncommitted generated source/output set from which the `_stack` package was derived.

### Preview and cache verification inputs

These generated outputs should be treated as later verification inputs for preview, install, favicon, and unfurl surfaces:

- `branding/generated/app/icon-192.png`
- `branding/generated/app/icon-512.png`
- `branding/generated/favicon/apple-touch-icon.png`
- `branding/generated/favicon/favicon-32x32.png`
- `branding/generated/favicon/favicon-16x16.png`
- `branding/generated/favicon/favicon.ico`

They matter for `Preview Cache & Surface Consistency`, but they should not be committed or synced blindly until each downstream consumer package is explicitly scoped.

## What is not in the current residue

- `branding/source/atlas-sigil-master.svg` is canonical but not currently modified.
- No Trove assets are modified from the ATLAS root in this lane.
- No Fitness consumer targets are modified from the ATLAS root in this lane.
- No `_stack` assets remain modified in the ATLAS root after the narrow launcher sync package was committed.

## Conclusions

1. The remaining `branding/**` residue is not random drift.
   It is a coherent set made of canonical source files plus manifest-declared generated outputs.

2. The residue is still lane-local, not consumer-local.
   None of these files by themselves prove that Trove or Fitness should be synced yet.

3. The next split should be packaging policy, not more consumer sync.
   The real next question is whether the root should commit the canonical source and generated outputs as a branding-source package, or keep them local until Trove and Fitness consumer packages are ready.

4. `_stack` is already handled at the consumer level.
   The remaining `branding/generated/ico/atlas-sigil-core-launcher.ico` residue is upstream output residue, not unresolved `_stack` work.

## Recommended next package

Run a brand packaging decision pass that answers:

1. whether the root should commit the remaining canonical source plus generated outputs as a standalone branding-source package
2. whether those generated outputs should remain local until Trove and Fitness consumer packages are also ready
3. whether preview/cache verification should wait until at least one downstream web consumer is synced from a clean repo target
