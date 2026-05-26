## Fitness Brand Generator Contract Decision - 2026-05-25

- Date: `2026-05-25`
- Lane: `Fitness Brand Generator Contract Decision Pass`
- Mode: `decision pass only`

## Goal

Decide the correct generation authority for Fitness app icons and favicons after the Fitness brand consumer re-sync proved that `npm run build` reintroduces non-canonical outputs.

## Inputs

- `docs/ops/FITNESS-BRAND-PREVIEW-RESIDUE-PASS-2026-05-25.md`
- `docs/ops/FITNESS-BRAND-CONSUMER-RESYNC-2026-05-25.md`
- `docs/ops/BRAND-CANONICAL-SOURCE-PACKAGE-2026-05-23.md`
- `docs/ops/BRAND-FITNESS-SYNC-2026-05-24.md`
- `docs/ops/PREVIEW-CACHE-SURFACE-CONSISTENCY-VERIFICATION-2026-05-24.md`
- `branding/manifest.json`
- `branding/source/**`
- `branding/generated/**`
- `repos/fawxzzy-fitness/scripts/generate-icons.mjs`
- `repos/fawxzzy-fitness/public/**`
- `repos/fawxzzy-fitness/package.json`

## Problem Statement

The current system has one canonical brand source image but two active generation authorities:

1. ATLAS root brand generator
2. Fitness repo-local icon generator

The consumer re-sync pass proved:

- direct consumer copy from ATLAS outputs restores canonical hashes immediately
- `npm run build` in Fitness regenerates those same files back to different hashes

So the problem is not source ownership. It is duplicated generation authority.

## Current Generator Comparison

### ATLAS root contract

Declared canonical contract in `branding/manifest.json`:

- canonical source:
  - `branding/source/atlas-sigil-master.png`
  - `branding/source/atlas-sigil-master.ico`
- canonical generated outputs:
  - `branding/generated/app/icon-192.png`
  - `branding/generated/app/icon-512.png`
  - `branding/generated/favicon/apple-touch-icon.png`
  - `branding/generated/favicon/favicon-32x32.png`
  - `branding/generated/favicon/favicon-16x16.png`
  - `branding/generated/favicon/favicon.ico`
  - other non-Fitness outputs
- canonical Fitness consumers are explicitly declared to consume those generated files

ATLAS generator implementation:

- script: `branding/scripts/build-brand-assets.mjs`
- source image:
  - canonical manifest source / variant source
- library:
  - `sharp` when available
  - PowerShell/System.Drawing fallback otherwise
- PNG resize behavior:
  - `fit: "contain"`
  - background: `{ r: 0, g: 0, b: 0, alpha: 1 }`
  - `png({ quality: 100, compressionLevel: 9 })`
- ICO behavior:
  - multi-frame ICO built from generated PNG frames
  - favicon ICO sizes: `16, 32, 48`
  - launcher ICO sizes differ for `_stack`

### Fitness repo-local contract

Fitness generator implementation:

- script: `repos/fawxzzy-fitness/scripts/generate-icons.mjs`
- source image:
  - `public/brand/atlas-sigil-master.png`
- source hash enforcement:
  - requires the same canonical master PNG hash:
    - `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51`
- build integration:
  - runs during `build:prepare`
  - `prebuild -> build:prepare -> scripts/generate-icons.mjs`
  - therefore runs during normal `npm run build`
- output targets:
  - `public/icons/icon-512.png`
  - `public/icons/icon-192.png`
  - `public/icons/apple-touch-icon.png`
  - `public/app/icon-512.png`
  - `public/app/icon-192.png`
  - `public/favicon-32x32.png`
  - `public/favicon-16x16.png`
  - `public/favicon.ico`
- library:
  - `sharp`
- PNG resize behavior:
  - `fit: "contain"`
  - background: `FITNESS_ICON_BG ?? "#07111b"`
  - `png({ quality: 100, compressionLevel: 9 })`
- ICO behavior:
  - multi-frame ICO built from generated PNG frames
  - favicon ICO sizes: `16, 32, 48`

## Source Of Divergence

### Primary divergence

The current hash divergence is explained by generator setting mismatch, not by source image mismatch:

- both systems use the same canonical master PNG
- both enforce the same master-source hash
- both output the same nominal target sizes
- both use `sharp`
- both use the same favicon ICO frame set

The key settings difference is:

- ATLAS root generator background: solid black `#000000`
- Fitness generator default background: `#07111b`

That alone is sufficient to produce different PNG and ICO hashes even when all other inputs are the same.

### Secondary governance divergence

Fitness generation is mutable at runtime through:

- `FITNESS_ICON_BG`

That means Fitness can produce output variants without changing canonical ATLAS brand contract files.

So the divergence is both:

1. concrete current hash mismatch from different default background color
2. structural future drift risk from repo-local env-configurable generation

## Rejected Explanations

These are not the primary root cause in the current evidence:

- source image mismatch
  - rejected; both systems use the same master PNG and Fitness validates the source hash
- output size mismatch
  - rejected; sizes match for all disputed consumers
- ICO size-set mismatch
  - rejected for favicon ICO; both use `16, 32, 48`
- compression mismatch
  - not the main evidence; both use `quality 100` and `compressionLevel 9`
- unknown drift
  - rejected; the background-color contract difference is explicit and sufficient

## Decision Options

### Option 1

ATLAS canonical generated outputs are the required truth, and the Fitness generator must be updated to match them.

### Option 2

Fitness generator outputs become the accepted truth, and ATLAS generated outputs are regenerated from the Fitness process.

### Option 3

A shared generator replaces both output paths, with ATLAS owning source and generator contract.

## Selected Authority Model

Selected:

- ownership model: **Option 1**
  - ATLAS owns canonical source and canonical generated output contract
- implementation shape: **Option 3**
  - a shared single generator or shared deterministic rendering contract should replace duplicate logic over time

Short version:

- ATLAS is the authority
- Fitness should not remain an independent brand generator with its own visual contract

## Why This Authority Wins

### Reason 1: manifest already declares ATLAS-generated outputs as canonical

`branding/manifest.json` already states that the Fitness consumers should consume:

- `branding/generated/app/icon-192.png`
- `branding/generated/app/icon-512.png`
- `branding/generated/favicon/apple-touch-icon.png`
- `branding/generated/favicon/favicon-32x32.png`
- `branding/generated/favicon/favicon-16x16.png`
- `branding/generated/favicon/favicon.ico`

Changing ATLAS to follow Fitness would reverse the declared topology instead of repairing the consumer to match it.

### Reason 2: other consumers already align to ATLAS outputs

The preview/cache verification receipts already proved file-level alignment for:

- `_stack`
- Trove
- Fitness, before the Fitness build reintroduced drift

So ATLAS outputs are already the broader shared contract across consumers.

### Reason 3: Fitness repo-local env configurability weakens determinism

`FITNESS_ICON_BG` lets Fitness mutate visual output without changing ATLAS brand governance.

That is incompatible with a single governed generated-output contract.

### Reason 4: accepting Fitness outputs would widen drift globally

If Fitness became the accepted generator authority:

- ATLAS generated hashes would need rebasing
- Trove and `_stack` governance would need re-validation
- the central manifest would become downstream of one app consumer

That is the wrong ownership direction.

## Rejected Options And Why

### Reject Option 2

Do not make Fitness generator outputs the accepted truth.

Why:

- reverses the already-declared ATLAS manifest authority
- broadens a local app-specific generator into a stack-wide source of truth
- preserves env-configurable output drift risk
- would force needless re-baselining of already-governed consumers

### Reject pure Option 1 without shared-contract follow-through

Do not stop at “Fitness must match ATLAS” as a policy sentence only.

Why:

- the current Fitness script would still be a second implementation of the contract
- duplicated implementations tend to drift again

So the right near-term move is Option 1 ownership with Option 3 implementation direction.

## Smallest Safe Implementation Package

### Package name

- `Fitness Brand Generator Alignment Package`

### Package boundary

Only one mutation class:

- generator contract alignment

### What that package should do

Smallest safe path:

1. update `repos/fawxzzy-fitness/scripts/generate-icons.mjs`
2. make its rendering settings deterministic against ATLAS contract
3. remove independent visual drift by:
   - changing default background from `#07111b` to canonical black `#000000`
   - or, better, reading a governed brand-generation contract from a shared root module or checked-in contract file
4. keep the same output target paths
5. keep build integration, but make build output match ATLAS hashes

### Preferred implementation direction

Near-term:

- align Fitness generator settings exactly with ATLAS build contract

Longer-term:

- extract a shared brand rendering helper or shared brand output build contract so both ATLAS and Fitness call the same implementation

## Verification Plan

For the implementation package:

1. run the aligned generator directly or via build prepare
2. compare hashes for:
   - `public/app/icon-192.png`
   - `public/app/icon-512.png`
   - `public/icons/icon-192.png`
   - `public/icons/icon-512.png`
   - `public/icons/apple-touch-icon.png`
   - `public/favicon-32x32.png`
   - `public/favicon-16x16.png`
   - `public/favicon.ico`
3. verify `public/brand/atlas-sigil-master.png` still matches canonical source hash
4. run:
   - `npm run sanity:quick`
   - `npm run typecheck`
   - `npm run build`
5. confirm hashes remain canonical **after** build
6. run root validation:
   - `python .\ops\validation\validate_stack.py`

Success condition:

- Fitness consumer hashes match ATLAS canonical outputs before and after `npm run build`

## Rollback Plan

If the alignment package produces unexpected regressions:

1. revert only the generator-alignment package in `repos/fawxzzy-fitness`
2. restore prior tracked icon files from Git if needed
3. re-run:
   - `npm run typecheck`
   - `npm run build`
4. keep the ATLAS decision receipt
   - the policy decision remains valid even if the first implementation needs revision

## Marker Recommendation

Decision-only result:

- `Brand Asset Canonicalization`: stays `80%`
- `Preview Cache & Surface Consistency`: stays `70%`
- `Full Stack Re-sync, Clean & Closeout`: stays `69%`
- `Inventory & Truth Map`: `58% -> 59%`

Why:

- the exact generator mismatch is now explicit and packageable
- but no convergence has happened yet

## Files Changed In This Pass

- `docs/ops/FITNESS-BRAND-GENERATOR-CONTRACT-DECISION-2026-05-25.md`

## Next Package

- `Fitness Brand Generator Alignment Package`
