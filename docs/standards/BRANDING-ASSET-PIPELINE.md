# ATLAS Branding Asset Pipeline

The ATLAS sigil is a stack-level asset, not a repo-owned icon.

## Canonical rule

- One canonical source of truth lives in `branding/source/`.
- Generated derivatives live in `branding/generated/`.
- Consumer repos receive synced copies only.
- Drift is a verification failure, not a manual clean-up task.

Pattern:
Master sigil -> generated variants -> declared consumers -> drift detection.

## Current layout

- `branding/source/atlas-sigil-master.svg`
- `branding/source/atlas-sigil-master.png`
- `branding/source/atlas-sigil-master.ico`
- `branding/manifest.json`
- `branding/scripts/build-brand-assets.mjs`
- `branding/scripts/sync-brand-assets.mjs`
- `branding/generated/ico/**`
- `branding/generated/png/**`
- `branding/generated/favicon/**`
- `branding/generated/app/**`

Current note:
The checked-in master in this pass is a traced first-pass source based on the launcher branding direction, not the original uploaded binary. Replace `branding/source/atlas-sigil-master.png` with the raw source asset or a cleaner vector export when the brand pass is ready, then rebuild and sync.

## Commands

From `C:\ATLAS`:

```powershell
node .\branding\scripts\build-brand-assets.mjs
node .\branding\scripts\sync-brand-assets.mjs
node .\branding\scripts\sync-brand-assets.mjs --check
```

From `C:\ATLAS\repos\_stack`:

```powershell
pnpm run atlas:brand:build
pnpm run atlas:brand:sync
pnpm run atlas:brand:verify
```

## Adding a consumer

1. Generate or identify the required derivative under `branding/generated/`.
2. Add a `consumers[]` entry in `branding/manifest.json` with:
   - `id`
   - `repoId`
   - `source`
   - `target`
   - optional `description`
3. Run build and sync.
4. Run the owning repo's verify command.
5. Keep the consumer repo file generated; do not hand-edit it.

## Changing the sigil

1. Replace `branding/source/atlas-sigil-master.png`.
2. If the editable vector changes too, update `branding/source/atlas-sigil-master.svg`.
3. Rebuild generated assets.
4. Sync consumers.
5. Run drift verification and repo-local verify.

## Current consumers

- `_stack` launcher icon: `repos/_stack/ops/assets/release-launcher.ico`
- Fitness PWA icons: `repos/fawxzzy-fitness/public/app/**`
- Fitness public icons and favicons: `repos/fawxzzy-fitness/public/icons/**`, `repos/fawxzzy-fitness/public/favicon*`
- Fitness local brand master: `repos/fawxzzy-fitness/public/brand/atlas-sigil-master.png`

## Product-variant rule

- ATLAS owns the sigil.
- Fitness consumes the sigil as a product variant.
- `_stack` consumes the sigil as an operator-console variant.
- Future product repos should add new consumer entries instead of creating repo-owned icon sources.
