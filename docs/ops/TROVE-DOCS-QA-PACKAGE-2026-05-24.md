# Trove Docs QA Package

Date: 2026-05-24
Lane: Trove repo-local split
Mode: Docs and QA package only
Status: Docs and QA lane isolated

## Goal

Package only the Trove docs and QA bucket without mixing:

- Trove public brand consumer drift
- vendored Fitness icon drift
- remaining brand-target assets

## Repo identity

- Repo: `repos/fawxzzy-trove`
- Branch: `codex/trove-brand-asset-sync`

## Package scope

Included files:

- `docs/qa.md`
- `qa/adapters/trove.web.json`
- `qa/scenarios/trove.home-smoke.json`

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
- `src/app/layout.tsx`
- `src/components/catalog/app-section.tsx`

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

- Trove docs and QA surfaces are now packageable separately from product work, vendored icon drift, and brand-target drift.
- Remaining Trove-local buckets after this package:
  1. vendored Fitness icon package
  2. Trove brand sync package

## Lock impact

This package moves Trove HEAD again, so ATLAS root must repin the `trove` entry in `stack.lock.yaml` after the Trove commit lands.
