## Fitness Brand Consumer Re-sync - 2026-05-25

- Date: `2026-05-25`
- Lane: `Fitness Brand Consumer Re-sync Pass`
- Mode: `narrow brand consumer sync only`

## Goal

Re-sync Fitness app icons, favicons, and ignored icon consumers from canonical ATLAS branding outputs without touching product code, Vercel, Supabase, Discord, or deploy surfaces.

## Inputs

- `docs/ops/FITNESS-BRAND-PREVIEW-RESIDUE-PASS-2026-05-25.md`
- `docs/ops/BRAND-CANONICAL-SOURCE-PACKAGE-2026-05-23.md`
- `docs/ops/BRAND-FITNESS-SYNC-2026-05-24.md`
- `docs/ops/PREVIEW-CACHE-SURFACE-CONSISTENCY-VERIFICATION-2026-05-24.md`
- `branding/manifest.json`
- `branding/generated/**`
- `repos/fawxzzy-fitness`

## Fitness Repo Start State

- branch: `main`
- HEAD: `3f48f9c26135cbce46c487e64e0ce1ccbad3f793`
- remote: `origin https://github.com/fawxzzy/fawxzzy-fitness.git`
- repo status before sync:
  - tracked brand consumer drift:
    - `public/app/icon-192.png`
    - `public/app/icon-512.png`
    - `public/favicon-16x16.png`
    - `public/favicon-32x32.png`
    - `public/favicon.ico`
  - tracked generated residue:
    - `public/sw.js`
    - `src/generated/appBuildManifest.json`
  - tracked manual-review/worktree noise:
    - `src/lib/stretch-library-details.ts`
    - `src/lib/stretch-library-summaries.ts`
  - ignored local consumer drift:
    - `public/icons/icon-192.png`
    - `public/icons/icon-512.png`
    - `public/icons/apple-touch-icon.png`

## Canonical Source / Output Hashes

| Surface | Canonical path | SHA256 |
| --- | --- | --- |
| brand master | `branding/source/atlas-sigil-master.png` | `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51` |
| app icon 192 | `branding/generated/app/icon-192.png` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` |
| app icon 512 | `branding/generated/app/icon-512.png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` |
| apple touch icon | `branding/generated/favicon/apple-touch-icon.png` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` |
| favicon 32 | `branding/generated/favicon/favicon-32x32.png` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` |
| favicon 16 | `branding/generated/favicon/favicon-16x16.png` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` |
| favicon ico | `branding/generated/favicon/favicon.ico` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` |

## Files Synced

### Tracked consumer targets

- `repos/fawxzzy-fitness/public/app/icon-192.png`
- `repos/fawxzzy-fitness/public/app/icon-512.png`
- `repos/fawxzzy-fitness/public/favicon-16x16.png`
- `repos/fawxzzy-fitness/public/favicon-32x32.png`
- `repos/fawxzzy-fitness/public/favicon.ico`

### Ignored consumer targets

- `repos/fawxzzy-fitness/public/icons/icon-192.png`
- `repos/fawxzzy-fitness/public/icons/icon-512.png`
- `repos/fawxzzy-fitness/public/icons/apple-touch-icon.png`

### Unchanged aligned consumer

- `repos/fawxzzy-fitness/public/brand/atlas-sigil-master.png`

## Immediate Post-Sync Hash Result

Immediately after copying from canonical outputs, all synced Fitness consumer targets matched the expected canonical hashes:

- tracked app icons matched
- tracked favicons matched
- ignored `public/icons/*.png` matched
- `public/brand/atlas-sigil-master.png` still matched canonical source hash

## Generated Build Residue Classification

Confirmed out of scope for this lane:

- `public/sw.js`
- `src/generated/appBuildManifest.json`

These remain generated build-id residue rather than brand truth.

## Verification Run

Ran from `repos/fawxzzy-fitness`:

```powershell
npm run sanity:quick
npm run typecheck
npm run build
```

Also ran from root:

```powershell
python .\ops\validation\validate_stack.py
```

### Verification result

- `npm run sanity:quick`
  - passed with the same existing lint warnings
- `npm run typecheck`
  - passed
- `npm run build`
  - passed
- root validation
  - `critical=0 error=0 warning=306`

## Critical Outcome

This package did **not** converge cleanly.

Reason:

- `npm run build` runs `scripts/generate-icons.mjs`
- that script regenerates Fitness app icons and favicons from `public/brand/atlas-sigil-master.png`
- the generated outputs from the Fitness repo-local generator do **not** match the canonical ATLAS generated hashes

Observed post-build drift reintroduced:

| Consumer | Post-build Fitness SHA256 | Expected canonical SHA256 | Result |
| --- | --- | --- | --- |
| `public/app/icon-192.png` | `9F9B1073525FCEE36612AC227788BE89C63016CB53438037135EF2F0345B1954` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | drift reintroduced |
| `public/app/icon-512.png` | `732A7DD730B6FDB4298CB5BFAB7FC603D90143592496874C93670646ED838817` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | drift reintroduced |
| `public/icons/icon-192.png` | `9F9B1073525FCEE36612AC227788BE89C63016CB53438037135EF2F0345B1954` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | drift reintroduced |
| `public/icons/icon-512.png` | `732A7DD730B6FDB4298CB5BFAB7FC603D90143592496874C93670646ED838817` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | drift reintroduced |
| `public/icons/apple-touch-icon.png` | `E3E19E1023686E6E5E5496670D15193E2BD8EDC8CBDFD94CB988DA7E7E461179` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` | drift reintroduced |
| `public/favicon-32x32.png` | `C0B0D141EAB792248F57532E12B14A77A40B341730352F31DC7D7C9798351A7A` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` | drift reintroduced |
| `public/favicon-16x16.png` | `92FBA4EA602D9CAF42EC130CF2356547C8F215E476B0EDAF232B77CE266625CD` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` | drift reintroduced |
| `public/favicon.ico` | `C90CB9D9D5A53B8F358E41C19C2DCD0CE2601705DD92C71CDA91A67C37881153` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` | drift reintroduced |

## Tracked vs Ignored Consumer Distinction

### Tracked consumers

- the tracked app icon and favicon files are now dirty again after build
- this means a simple file-copy sync is not durable under the current Fitness build contract

### Ignored consumers

- the ignored `public/icons/*.png` also drift again during the same build process
- they remain outside Git staging policy, but they still prove the same generator mismatch

## Git / Commit Outcome

No Fitness commit was created.

Reason:

- `fitness` is `unmanaged` in current stack policy
- more importantly, this package did not produce a stable converged working tree after verification
- committing only the tracked icon files would preserve a brand state that the current build step immediately undoes
- unrelated Fitness residue remained out of scope and was not mixed into staging

No stack lock update was needed.

Reason:

- Fitness is not currently included in `stack.yaml -> stack_lock.include_repo_ids`
- Fitness HEAD did not change

## Brand / Preview Lane Interpretation

### Can Brand Asset Canonicalization move forward

Not yet.

The lane is blocked by a generator-contract mismatch:

- ATLAS canonical generated assets and Fitness repo-local generated assets are not the same output family

### Can Preview Cache & Surface Consistency move forward

Not yet.

Deploy-backed remote verification is still downstream of local consumer parity, and local consumer parity does not stay stable through build.

## Remaining Blockers

- `repos/fawxzzy-fitness/scripts/generate-icons.mjs` produces non-canonical brand outputs from the same canonical brand master
- tracked icon/favicons re-drift during `npm run build`
- ignored `public/icons/*.png` re-drift during the same build path
- generated build-id residue remains separate:
  - `public/sw.js`
  - `src/generated/appBuildManifest.json`
- manual-review residue remains separate:
  - `src/lib/stretch-library-details.ts`
  - `src/lib/stretch-library-summaries.ts`

## Marker Recommendation

This package improved truth, but it did not resolve the lane.

- `Brand Asset Canonicalization`: stays `80%`
  - generator mismatch still blocks durable Fitness alignment
- `Preview Cache & Surface Consistency`: stays `70%`
  - remote proof remains blocked behind local parity
- `Full Stack Re-sync, Clean & Closeout`: stays `69%`
  - no new residue class was actually closed
- `Inventory & Truth Map`: `57% -> 58%`
  - the exact blocker is now narrowed to the Fitness icon generator contract

## Files Changed In This Pass

- `docs/ops/FITNESS-BRAND-CONSUMER-RESYNC-2026-05-25.md`

## Next Package

- `Fitness Brand Generator Contract Decision Pass`

That next lane should decide whether:

1. ATLAS canonical generated outputs become the required truth and Fitness generator must be updated to match
2. Fitness generator outputs become the accepted truth and ATLAS canonical generated outputs must be regenerated
3. a shared single generator should replace both output paths
