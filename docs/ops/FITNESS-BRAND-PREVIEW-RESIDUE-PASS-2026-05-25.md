## Fitness Brand Preview Residue Pass - 2026-05-25

- Date: `2026-05-25`
- Lane: `Fitness Brand Preview Residue Pass`
- Mode: `inventory/classification only`

## Goal

Classify the remaining Fitness brand and preview residue so Brand Asset Canonicalization, Preview Cache & Surface Consistency, and Full Stack Re-sync / Clean can move forward without mixing product work, deploy work, or Discord lanes.

## Inputs

- `docs/ops/FULL-STACK-RESYNC-CLEAN-CLOSEOUT-BASELINE-PASS-2-2026-05-25.md`
- `docs/ops/QUEUED-WORK-REVIEW-PACKET-2026-05-25.md`
- `docs/ops/PREVIEW-CACHE-SURFACE-CONSISTENCY-PLAN-2026-05-24.md`
- `docs/ops/PREVIEW-CACHE-SURFACE-CONSISTENCY-VERIFICATION-2026-05-24.md`
- `docs/ops/PREVIEW-CACHE-SURFACE-LIVE-PASS-1-2026-05-24.md`
- `docs/ops/PREVIEW-CACHE-REMOTE-UNFURL-PLAN-2026-05-24.md`
- `docs/ops/BRAND-FITNESS-SYNC-2026-05-24.md`
- `docs/ops/BRAND-CANONICAL-SOURCE-PACKAGE-2026-05-23.md`
- `branding/manifest.json`
- `stack.lock.yaml`
- `repos/fawxzzy-fitness`

## Fitness Repo State

- branch: `main`
- HEAD: `3f48f9c26135cbce46c487e64e0ce1ccbad3f793`
- remote: `origin https://github.com/fawxzzy/fawxzzy-fitness.git`
- working tree: dirty

### Tracked dirty files

| Path | Classification | Notes |
| --- | --- | --- |
| `public/app/icon-192.png` | canonical brand consumer asset | tracked asset drift; does not match canonical current hash |
| `public/app/icon-512.png` | canonical brand consumer asset | tracked asset drift; does not match canonical current hash |
| `public/favicon-16x16.png` | canonical brand consumer asset | tracked asset drift; does not match canonical current hash |
| `public/favicon-32x32.png` | canonical brand consumer asset | tracked asset drift; does not match canonical current hash |
| `public/favicon.ico` | canonical brand consumer asset | tracked asset drift; does not match canonical current hash |
| `public/sw.js` | preview/cache generated residue | build-id drift only |
| `src/generated/appBuildManifest.json` | preview/cache generated residue | build-id / generatedAt drift only |
| `scripts/mobile_regression/__pycache__/__init__.cpython-313.pyc` | ignored-but-intentional local generated asset | ignored Python bytecode residue |
| `scripts/mobile_regression/__pycache__/board_builder.cpython-313.pyc` | ignored-but-intentional local generated asset | ignored Python bytecode residue |
| `src/lib/stretch-library-details.ts` | manual review | no textual diff surfaced; likely line-ending/worktree noise |
| `src/lib/stretch-library-summaries.ts` | manual review | no textual diff surfaced; likely line-ending/worktree noise |

### Ignored generated surfaces visible in status

| Path | Classification | Notes |
| --- | --- | --- |
| `.next/` | ignored-but-intentional local generated asset | local build output |
| `.playbook/**` | ignored-but-intentional local generated asset | repo-local Playbook runtime state |
| `.vercel/` | ignored-but-intentional local generated asset | local Vercel linkage/runtime state |
| `node_modules/` | ignored-but-intentional local generated asset | local dependency install |
| `public/icons/*.png` | canonical brand consumer asset | ignored local consumer surfaces; currently drifted from canonical |

## Brand / Preview Residue Table

| Surface | Current local path | Canonical / governing source | Classification | Verdict |
| --- | --- | --- | --- | --- |
| Fitness brand master | `repos/fawxzzy-fitness/public/brand/atlas-sigil-master.png` | `branding/source/atlas-sigil-master.png` | canonical brand consumer asset | still aligned |
| Fitness app icon 192 | `repos/fawxzzy-fitness/public/app/icon-192.png` | `branding/generated/app/icon-192.png` | canonical brand consumer asset | drifted |
| Fitness app icon 512 | `repos/fawxzzy-fitness/public/app/icon-512.png` | `branding/generated/app/icon-512.png` | canonical brand consumer asset | drifted |
| Fitness ignored icon 192 | `repos/fawxzzy-fitness/public/icons/icon-192.png` | `branding/generated/app/icon-192.png` | canonical brand consumer asset | drifted |
| Fitness ignored icon 512 | `repos/fawxzzy-fitness/public/icons/icon-512.png` | `branding/generated/app/icon-512.png` | canonical brand consumer asset | drifted |
| Fitness apple touch icon | `repos/fawxzzy-fitness/public/icons/apple-touch-icon.png` | `branding/generated/favicon/apple-touch-icon.png` | canonical brand consumer asset | drifted |
| Fitness favicon 32 | `repos/fawxzzy-fitness/public/favicon-32x32.png` | `branding/generated/favicon/favicon-32x32.png` | canonical brand consumer asset | drifted |
| Fitness favicon 16 | `repos/fawxzzy-fitness/public/favicon-16x16.png` | `branding/generated/favicon/favicon-16x16.png` | canonical brand consumer asset | drifted |
| Fitness favicon ico | `repos/fawxzzy-fitness/public/favicon.ico` | `branding/generated/favicon/favicon.ico` | canonical brand consumer asset | drifted |
| Fitness manifest metadata | `repos/fawxzzy-fitness/src/app/manifest.ts` | local app runtime contract | preview/cache verification artifact | routing contract still present; no change in this pass |
| Fitness page metadata refs | `repos/fawxzzy-fitness/src/app/layout.tsx` | local app runtime contract | preview/cache verification artifact | icon/apple/shortcut/OG refs still point at expected paths |
| Fitness service worker build id | `repos/fawxzzy-fitness/public/sw.js` | local generated runtime state | preview/cache generated residue | build-id drift only |
| Fitness build manifest | `repos/fawxzzy-fitness/src/generated/appBuildManifest.json` | local generated runtime state | preview/cache generated residue | build timestamp drift only |

## Hash Consistency Verdict

### Canonical brand source still aligned

| Surface | Path | SHA256 | Result |
| --- | --- | --- | --- |
| brand master | `branding/source/atlas-sigil-master.png` | `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51` | canonical |
| Fitness brand master | `repos/fawxzzy-fitness/public/brand/atlas-sigil-master.png` | `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51` | match |

### Canonical generated outputs vs current Fitness consumers

| Consumer | Fitness SHA256 | Expected canonical SHA256 | Result |
| --- | --- | --- | --- |
| `public/app/icon-192.png` | `9F9B1073525FCEE36612AC227788BE89C63016CB53438037135EF2F0345B1954` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | drift |
| `public/app/icon-512.png` | `732A7DD730B6FDB4298CB5BFAB7FC603D90143592496874C93670646ED838817` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | drift |
| `public/icons/icon-192.png` | `9F9B1073525FCEE36612AC227788BE89C63016CB53438037135EF2F0345B1954` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | drift |
| `public/icons/icon-512.png` | `732A7DD730B6FDB4298CB5BFAB7FC603D90143592496874C93670646ED838817` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | drift |
| `public/icons/apple-touch-icon.png` | `E3E19E1023686E6E5E5496670D15193E2BD8EDC8CBDFD94CB988DA7E7E461179` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` | drift |
| `public/favicon-32x32.png` | `C0B0D141EAB792248F57532E12B14A77A40B341730352F31DC7D7C9798351A7A` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` | drift |
| `public/favicon-16x16.png` | `92FBA4EA602D9CAF42EC130CF2356547C8F215E476B0EDAF232B77CE266625CD` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` | drift |
| `public/favicon.ico` | `C90CB9D9D5A53B8F358E41C19C2DCD0CE2601705DD92C71CDA91A67C37881153` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` | drift |

### Verdict

- canonical ATLAS brand source is still healthy
- Fitness consumer brand surfaces are **not** currently hash-aligned to canonical outputs
- the prior local Fitness sync receipt is now stale as an operational truth statement
- this is real consumer drift, not only cache drift

## Preview / Cache Residue Verdict

### Service worker / build-manifest residue

`public/sw.js` and `src/generated/appBuildManifest.json` show only timestamp/build-id drift:

- `public/sw.js`
  - `APP_BUILD_ID` moved from `1.0.0-2026-05-09T23:43:06.601Z` to `1.0.0-2026-05-25T16:26:55.510Z`
- `src/generated/appBuildManifest.json`
  - `buildId` / `generatedAt` moved to `2026-05-25T16:26:55.510Z`

Classification:

- generated preview/cache residue
- should be handled in the same narrow Fitness residue package as any future brand resync or reverted in a dedicated generated-residue cleanup pass

### Metadata / manifest posture

Current metadata contract still points to expected icon and preview paths:

- `src/app/layout.tsx`
  - icons:
    - `/favicon.ico`
    - `/favicon-32x32.png`
    - `/favicon-16x16.png`
    - `/app/icon-192.png`
    - `/app/icon-512.png`
  - apple:
    - `/icons/apple-touch-icon.png`
  - shortcut:
    - `/icons/icon-192.png`
  - OG/Twitter image:
    - `/brand/atlas-sigil-master.png`
- `src/app/manifest.ts`
  - PWA icons:
    - `/app/icon-192.png`
    - `/app/icon-512.png`

Classification:

- metadata wiring still matches the expected surface paths
- visible preview and install surfaces remain governed by those paths
- since the underlying assets drifted, deploy-backed remote verification is **not** the immediate next blocker

## Dirty Surface Classification Summary

### Canonical brand consumer assets

- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/favicon-16x16.png`
- `public/favicon-32x32.png`
- `public/favicon.ico`
- ignored:
  - `public/icons/icon-192.png`
  - `public/icons/icon-512.png`
  - `public/icons/apple-touch-icon.png`

Recommended posture:

- do not delete blindly
- package into a narrow `Fitness Brand Consumer Re-sync Pass`
- verify resulting hashes against `branding/manifest.json`
- commit tracked consumer assets in the Fitness repo
- re-sync ignored `public/icons/*.png` locally in the same bounded pass

### Preview/cache generated residue

- `public/sw.js`
- `src/generated/appBuildManifest.json`
- `.next/`

Recommended posture:

- retain for now
- treat as generated residue, not product truth
- clean or regenerate only in a dedicated generated-residue pass tied to a verified Fitness build package

### Ignored-but-intentional local generated assets

- `.playbook/**`
- `.vercel/`
- `node_modules/`
- `scripts/mobile_regression/__pycache__/**`

Recommended posture:

- retain
- no closeout action in this pass

### Manual-review

- `src/lib/stretch-library-details.ts`
- `src/lib/stretch-library-summaries.ts`

Observed posture:

- `git diff` surfaced no textual content changes
- Git warnings indicate line-ending conversion pressure in working copy

Recommended posture:

- do not treat as brand or preview work
- handle in a later tiny manual-review / worktree-noise package

## Brand / Preview Lane Interpretation

### Does Fitness brand sync remain complete

No.

Current truth:

- `public/brand/atlas-sigil-master.png` remains aligned
- the tracked app icon and favicon consumers do not
- the ignored `public/icons/*.png` consumers also do not

### Can Preview Cache & Surface Consistency move forward

Not as the immediate next package.

Reason:

- current Fitness local consumer drift must be repaired first
- deploy-backed remote preview or unfurl verification should remain downstream of that repair

### Should any asset be committed, ignored, deleted, or retained

| Item class | Recommended action |
| --- | --- |
| tracked Fitness brand consumers | commit in a narrow Fitness brand consumer re-sync package after hashes are restored |
| ignored `public/icons/*.png` | retain as ignored local consumers, but resync locally in the same package |
| `public/sw.js`, `src/generated/appBuildManifest.json` | retain for now; handle in generated-residue pass |
| `__pycache__` residue | retain / ignore |
| stretch-library files | retain for manual review; do not mix into brand package |

### Is deploy-backed remote verification still the next blocker

No.

Immediate blocker:

- local Fitness brand consumer drift

Downstream blocker after repair:

- deploy-backed remote preview / unfurl verification

## Validation

Root validation only for this docs/classification pass:

```powershell
python .\ops\validation\validate_stack.py
```

Expected result for this pass:

- `critical=0`
- `error=0`
- warning budget may remain

## Marker Recommendation

This pass reduces ambiguity but does not justify the full optimistic move proposed before inspection.

Recommended movement:

- `Brand Asset Canonicalization`: stays `80%`
  - Fitness consumer drift is now explicit and still needs a repair package
- `Preview Cache & Surface Consistency`: stays `70%`
  - remote verification remains downstream, and local Fitness brand parity is not currently restored
- `Full Stack Re-sync, Clean & Closeout`: `68% -> 69%`
  - one more residue class is bounded and packageable
- `Inventory & Truth Map`: `55% -> 57%`
  - Fitness brand/preview truth is now precise again

## Files Changed In This Pass

- `docs/ops/FITNESS-BRAND-PREVIEW-RESIDUE-PASS-2026-05-25.md`

## Next Package

- `Fitness Brand Consumer Re-sync Pass`

After that:

1. `Helper Vercel Surface Deletion Decision / Execution Pass`
2. `Fitness Supabase Mutation Pass 1`
3. `Playbook / Lifeline external smoke disposal decision`
4. `Preview Cache Remote And Unfurl Verification`
