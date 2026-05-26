## Fitness Brand Generator Alignment - 2026-05-25

- Date: `2026-05-25`
- Lane: `Fitness Brand Generator Alignment Package`
- Mode: `narrow implementation package`

## Goal

Align Fitness icon and favicon generation with the ATLAS canonical generated-output contract so `npm run build` no longer reintroduces brand drift.

## Inputs

- `docs/ops/FITNESS-BRAND-GENERATOR-CONTRACT-DECISION-2026-05-25.md`
- `docs/ops/FITNESS-BRAND-CONSUMER-RESYNC-2026-05-25.md`
- `docs/ops/FITNESS-BRAND-PREVIEW-RESIDUE-PASS-2026-05-25.md`
- `docs/ops/BRAND-CANONICAL-SOURCE-PACKAGE-2026-05-23.md`
- `branding/manifest.json`
- `branding/generated/**`
- `repos/fawxzzy-fitness/scripts/generate-icons.mjs`
- `repos/fawxzzy-fitness/public/**`
- `repos/fawxzzy-fitness/package.json`

## Implementation Summary

Changed:

- `repos/fawxzzy-fitness/scripts/generate-icons.mjs`

No other Fitness source files were edited intentionally.

## Generator Contract Change

Previous Fitness behavior:

- treated `public/brand/atlas-sigil-master.png` as canonical source
- rendered app icons, ignored icons, and favicons locally with a repo-local generator
- allowed a second generation authority to diverge from ATLAS canonical generated outputs
- drift could be reintroduced during `npm run build`

New Fitness behavior:

- keeps the local canonical master-hash guard on `public/brand/atlas-sigil-master.png`
- reads the governed ATLAS branding manifest at `../../branding/manifest.json`
- resolves the declared Fitness consumer entries from that manifest
- copies the ATLAS-governed generated outputs into the Fitness consumer paths
- stops rendering an independent local icon/favicons output family

This makes Fitness a governed consumer of ATLAS generated outputs rather than a second brand generator authority.

## `FITNESS_ICON_BG` Outcome

`FITNESS_ICON_BG` was effectively removed as a drift authority.

Result:

- the script no longer uses `FITNESS_ICON_BG`
- the script no longer uses any repo-local color-based render path
- brand output identity now comes from the ATLAS-generated output contract, not an app-local environment override

## Before / After Hash Verdict

### Canonical ATLAS generated outputs

| Surface | Canonical path | SHA256 |
| --- | --- | --- |
| app icon 192 | `branding/generated/app/icon-192.png` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` |
| app icon 512 | `branding/generated/app/icon-512.png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` |
| apple touch icon | `branding/generated/favicon/apple-touch-icon.png` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` |
| favicon 32 | `branding/generated/favicon/favicon-32x32.png` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` |
| favicon 16 | `branding/generated/favicon/favicon-16x16.png` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` |
| favicon ico | `branding/generated/favicon/favicon.ico` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` |

### Post-build Fitness consumer hashes

| Consumer | Post-build Fitness SHA256 | Expected canonical SHA256 | Result |
| --- | --- | --- | --- |
| `public/app/icon-192.png` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | match |
| `public/app/icon-512.png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | match |
| `public/icons/icon-192.png` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | match |
| `public/icons/icon-512.png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | match |
| `public/icons/apple-touch-icon.png` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` | match |
| `public/favicon-32x32.png` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` | match |
| `public/favicon-16x16.png` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` | match |
| `public/favicon.ico` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` | match |

### Brand master verification

`public/brand/atlas-sigil-master.png` remained aligned to canonical source hash:

- `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51`

## Tracked vs Ignored Consumer Distinction

### Tracked consumers

These remain the tracked repo surfaces governed by the ATLAS contract:

- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/favicon-16x16.png`
- `public/favicon-32x32.png`
- `public/favicon.ico`

Result after build:

- all tracked consumers matched canonical hashes
- tracked icon/favicons did **not** remain as dirty drift after build

### Ignored consumers

These remain ignored local consumers:

- `public/icons/icon-192.png`
- `public/icons/icon-512.png`
- `public/icons/apple-touch-icon.png`

Result after build:

- all ignored consumers also matched canonical hashes

## Verification Results

Ran from `repos/fawxzzy-fitness`:

```powershell
node scripts/generate-icons.mjs
npm run sanity:quick
npm run typecheck
npm run build
```

Ran from root:

```powershell
python .\ops\validation\validate_stack.py
```

Results:

- `node scripts/generate-icons.mjs`
  - passed
- `npm run sanity:quick`
  - passed with the same existing lint warnings
- `npm run typecheck`
  - passed
- `npm run build`
  - passed
- root validation
  - `critical=0 error=0 warning=306`

## Build-After-Sync Verdict

Success.

`npm run build` no longer reintroduces icon/favicon drift.

The brand consumer contract now holds through the normal Fitness build path.

## Out-Of-Scope Residue Kept Separate

Still intentionally not part of this lane:

- `public/sw.js`
- `src/generated/appBuildManifest.json`
- `scripts/mobile_regression/__pycache__/**`
- `src/lib/stretch-library-details.ts`
- `src/lib/stretch-library-summaries.ts`

These remained outside staging and outside the brand-generator package boundary.

## Git / Lock Outcome

Fitness HEAD changed for this package.

No stack lock update was required.

Reason:

- `fitness` is `unmanaged` and not included in `stack.yaml -> stack_lock.include_repo_ids`

## Lane Interpretation

### Can Brand Asset Canonicalization advance

Yes.

Fitness is no longer a second generation authority for these outputs.

### Can Preview Cache & Surface Consistency advance

Yes.

The local Fitness parity blocker is cleared, so the next blocker becomes deploy-backed remote verification and unfurl proof rather than local consumer drift.

## Remaining Blockers

- deploy-backed remote preview / unfurl verification still remains
- generated build-id residue remains a separate Fitness residue lane:
  - `public/sw.js`
  - `src/generated/appBuildManifest.json`
- manual-review / worktree-noise residue remains separate:
  - `src/lib/stretch-library-details.ts`
  - `src/lib/stretch-library-summaries.ts`

## Marker Recommendation

- `Brand Asset Canonicalization`: `80% -> 90%`
- `Preview Cache & Surface Consistency`: `70% -> 78%`
- `Full Stack Re-sync, Clean & Closeout`: `69% -> 72%`
- `Inventory & Truth Map`: `59% -> 60%`

## Files Changed In This Pass

### Fitness

- `repos/fawxzzy-fitness/scripts/generate-icons.mjs`

### ATLAS

- `docs/ops/FITNESS-BRAND-GENERATOR-ALIGNMENT-2026-05-25.md`

## Next Package

1. `Helper Vercel Surface Deletion Decision / Execution Pass`
2. `Fitness Supabase Mutation Pass 1`
3. `Playbook/Lifeline external smoke disposal decision`
4. `Preview Cache Remote And Unfurl Verification`
