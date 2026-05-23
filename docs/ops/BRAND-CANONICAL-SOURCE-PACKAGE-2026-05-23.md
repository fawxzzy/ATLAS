# Brand Canonical Source Package

Date: 2026-05-23
Lane: Brand Asset Canonicalization
Mode: Root branding package only
Status: Packaged canonical source and generated outputs

## Scope

- Root-owned branding package only.
- Includes canonical source files under `branding/source/**`.
- Includes manifest-declared generated outputs under `branding/generated/**`.
- Does not include downstream consumer syncs for Trove or Fitness.
- Does not include `_stack` consumer assets.
- Does not use `tmp/`.

## Source of truth

Manifest:

- `branding/manifest.json`

Declared canonical source files:

- `branding/source/atlas-sigil-master.png`
- `branding/source/atlas-sigil-master.ico`

Declared generated outputs in scope:

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

## Why this package exists

The remaining `branding/**` residue was previously classified as a coherent root-owned source-and-generated set, not as random downstream drift. This package commits that governed ATLAS brand source state without pulling Trove, Fitness, or any other consumer sync into the same change set.

Related governance receipts:

- `docs/ops/BRAND-ASSET-CANONICALIZATION-INVENTORY-2026-05-23.md`
- `docs/ops/BRAND-CONSUMER-VALIDITY-PREFLIGHT-2026-05-23.md`
- `docs/ops/BRAND-ASSET-CANONICALIZATION-DECISION-PASS-1-2026-05-23.md`
- `docs/ops/BRAND-ROOT-RESIDUE-CLASSIFICATION-2026-05-23.md`
- `docs/ops/BRAND-STACK-LAUNCHER-SYNC-2026-05-23.md`

## Hash ledger

### Canonical source

- `branding/source/atlas-sigil-master.png`
  - `sha256:e20a9fe2e42585ed1ec818d13ec80aa8ced89f15f82a35c51269c1b794f07f51`
- `branding/source/atlas-sigil-master.ico`
  - `sha256:2413de0e524ea11e1aa49e7e9a8871b270aa4b62b35205d78ebc359462db013f`

### Generated outputs

- `branding/generated/png/atlas-sigil-1024.png`
  - `sha256:e20a9fe2e42585ed1ec818d13ec80aa8ced89f15f82a35c51269c1b794f07f51`
- `branding/generated/png/atlas-sigil-512.png`
  - `sha256:70bf6051a83da294ff87738d843d8a533d7fbfb1608af78d800a56f90d83005b`
- `branding/generated/png/atlas-sigil-256.png`
  - `sha256:9c6481cc7fe120ee117a375e702c6bfa434bcbc55e98f2be51695dbe0cf7b16f`
- `branding/generated/app/icon-192.png`
  - `sha256:829f6539b8821c24710d06c42b54dd1cc5cc2fc273a5094502c4e040ed452070`
- `branding/generated/app/icon-512.png`
  - `sha256:70bf6051a83da294ff87738d843d8a533d7fbfb1608af78d800a56f90d83005b`
- `branding/generated/favicon/apple-touch-icon.png`
  - `sha256:ef27ff93a31c24f88bf86a9ab4e45b5222cab7aa882f2fe35bb32612be3a3e0c`
- `branding/generated/favicon/favicon-32x32.png`
  - `sha256:4cd4bf7818a3e975b12d7675e9225c61c34e205fcd9edad1cf0c7f5ae8a64138`
- `branding/generated/favicon/favicon-16x16.png`
  - `sha256:01548bcbeaa9dd7f73844ad38d7d68efcc1543ad96a546db85cbfa779d1d7916`
- `branding/generated/favicon/favicon.ico`
  - `sha256:ec98fd07b3cbdf1e649419f616721641bf0903ebb2b49aa3dcdea1ac18523f87`
- `branding/generated/ico/atlas-sigil-core-launcher.ico`
  - `sha256:49ef6e187208c643a1345ee71c658f2ec99aff68bb906dfb09c0ba859a50485b`

## Explicit exclusions

This package does not include:

- Trove public brand/icon/favicon assets
- Fitness public brand/icon/favicon assets
- `_stack` consumer asset path `repos/_stack/ops/assets/release-launcher.ico`
- `tmp/**`
- `archive/**`
- `stack.lock.yaml`
- Vercel, Supabase, or Discord changes

## Validation

Run after staging only this package:

```powershell
python .\ops\validation\validate_stack.py --allow-missing-locked-repos
```

Expected:

- `critical=0`
- `error=0`
- warning budget may remain

## Next lane split

After this package:

1. `_stack` consumer sync remains complete.
2. Trove brand sync stays blocked until repo-local drift is isolated.
3. Fitness brand sync stays blocked until `repos/fawxzzy-fitness` is visible and clean in the active root session.
4. Preview/cache verification stays downstream of those consumer-specific packages.
