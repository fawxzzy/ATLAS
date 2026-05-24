# Trove Product Preview Board Package

Date: 2026-05-23
Lane: Trove repo-local split
Mode: Product package only
Status: Product lane isolated

## Goal

Package the Trove product preview board work without mixing:

- Trove public brand consumer drift
- vendored Fitness icon drift
- docs and QA surfaces

## Repo identity

- Repo: `repos/fawxzzy-trove`
- Branch: `codex/trove-brand-asset-sync`
- Base product commit already on branch:
  - `bce14fc Add layered Fitness preview board`

## Package scope

Included source files in this package:

- `src/app/layout.tsx`
- `src/components/catalog/app-section.tsx`

Scope intent:

- finalize metadata and preview behavior wiring for the layered Fitness preview board lane
- keep Trove brand consumer assets untouched
- keep vendored Fitness icon files untouched
- keep docs and QA surfaces untouched

## Explicit exclusions

Not included:

- `public/brand/atlas-sigil-master.png`
- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/icons/apple-touch-icon.png`
- `public/favicon-32x32.png`
- `public/favicon-16x16.png`
- `public/favicon.ico`
- `public/apps/fitness/icon-192.png`
- `public/apps/fitness/icon-512.png`
- `docs/qa.md`
- `qa/**`

## Verification

Repo-local verification run from `repos/fawxzzy-trove`:

```powershell
npm run verify
```

Result:

- passed

Verification covered:

- `npm run lint`
- `npm run build`
- `npm run smoke:lifeline`

## Outcome

- Trove product/source lane is now packageable separately from brand drift
- Trove brand sync remains blocked until the remaining non-product buckets are isolated
- the next Trove-local lanes remain:
  1. docs / QA package
  2. vendored Fitness icon package
  3. Trove public brand sync package
