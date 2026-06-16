# Preview Cache Remote And Unfurl Verification

Date: 2026-06-16
Lane: Preview Cache & Surface Consistency
Mode: deploy-backed verification and closeout
Status: closed

## Goal

Finish the remaining preview/cache lane by verifying the live deployed Trove and Fitness surfaces against the canonical ATLAS brand outputs, classifying cache behavior from live evidence, and deciding whether any real unfurl/cache blocker still remains.

This pass does not deploy, mutate Vercel settings, mutate Supabase, rewrite brand assets, or use `tmp/` as a source of truth.

## Inputs

- `docs/ops/PREVIEW-CACHE-SURFACE-CONSISTENCY-VERIFICATION-2026-05-24.md`
- `docs/ops/PREVIEW-CACHE-SURFACE-LIVE-PASS-1-2026-05-24.md`
- `docs/ops/PREVIEW-CACHE-REMOTE-UNFURL-PLAN-2026-05-24.md`
- `docs/ops/FITNESS-BRAND-GENERATOR-ALIGNMENT-2026-05-25.md`
- `branding/source/atlas-sigil-master.png`
- `branding/generated/app/icon-192.png`
- `branding/generated/app/icon-512.png`
- `branding/generated/favicon/apple-touch-icon.png`
- `branding/generated/favicon/favicon-32x32.png`
- `branding/generated/favicon/favicon-16x16.png`
- `branding/generated/favicon/favicon.ico`
- `branding/generated/ico/atlas-sigil-core-launcher.ico`
- `repos/trove/src/app/layout.tsx`
- `repos/trove/src/app/manifest.ts`
- `repos/fawxzzy-fitness/src/app/layout.tsx`
- `repos/fawxzzy-fitness/src/app/manifest.ts`

## Canonical Remote Bases

Verified live deployed bases in this pass:

- Trove:
  - `https://fawxzzy-trove.vercel.app`
- Fitness:
  - `https://fawxzzy-fitness-local.vercel.app`

Also checked and rejected as current verification bases:

- `https://fawxzzy-fitness.vercel.app`
  - returned `404`
- `https://fawxzzy-fitness-preview.vercel.app`
  - returned `404`
- `https://fawxzzy-fitness-production.vercel.app`
  - returned `404`

Interpretation:

- the live remote proof base for this lane is the current Trove production alias plus the current Fitness deployed alias at `fawxzzy-fitness-local.vercel.app`
- no additional stale Fitness public alias family is acting as the current preview-proof surface

## Live Remote Proof

### Trove

Deployed root proof:

- page title: `Trove`
- manifest link: `/manifest.webmanifest`
- `og:image`: `https://fawxzzy-trove.vercel.app/brand/atlas-sigil-master.png`
- `twitter:image`: `https://fawxzzy-trove.vercel.app/brand/atlas-sigil-master.png`

Deployed route parity:

| Route | Content type | SHA256 | Verdict |
| --- | --- | --- | --- |
| `/manifest.webmanifest` | `application/manifest+json; charset=utf-8` | `BF849C6767FE1CD7479D5E69EBD892F52CA593124AE53B632C8EBA2E130AD316` | valid deployed manifest |
| `/favicon.ico` | `image/vnd.microsoft.icon` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` | matches canonical |
| `/favicon-32x32.png` | `image/png` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` | matches canonical |
| `/favicon-16x16.png` | `image/png` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` | matches canonical |
| `/app/icon-192.png` | `image/png` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | matches canonical |
| `/app/icon-512.png` | `image/png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | matches canonical |
| `/icons/apple-touch-icon.png` | `image/png` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` | matches canonical |
| `/brand/atlas-sigil-master.png` | `image/png` | `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51` | matches canonical |

Manifest content observed:

- `name`: `Trove`
- `short_name`: `Trove`
- `start_url`: `/`
- `display`: `standalone`
- icons:
  - `/app/icon-192.png`
  - `/app/icon-512.png`

### Fitness

Deployed root proof:

- page title: `FawxzzyFitness`
- manifest link: `/manifest.webmanifest`
- `og:image`: `https://fawxzzy-fitness-local.vercel.app/brand/atlas-sigil-master.png`
- `twitter:image`: `https://fawxzzy-fitness-local.vercel.app/brand/atlas-sigil-master.png`

Deployed route parity:

| Route | Content type | SHA256 | Verdict |
| --- | --- | --- | --- |
| `/manifest.webmanifest` | `application/manifest+json` | `0EEC87FFA426E1B6F0CEC156D6A1F331AFD1BF8E409514CFD0F7A51CCC821CA4` | valid deployed manifest |
| `/favicon.ico` | `image/vnd.microsoft.icon` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` | matches canonical |
| `/favicon-32x32.png` | `image/png` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` | matches canonical |
| `/favicon-16x16.png` | `image/png` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` | matches canonical |
| `/app/icon-192.png` | `image/png` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | matches canonical |
| `/app/icon-512.png` | `image/png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | matches canonical |
| `/icons/icon-192.png` | `image/png` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | matches canonical |
| `/icons/icon-512.png` | `image/png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | matches canonical |
| `/icons/apple-touch-icon.png` | `image/png` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` | matches canonical |
| `/brand/atlas-sigil-master.png` | `image/png` | `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51` | matches canonical |

Manifest content observed:

- `id`: `/`
- `name`: `FawxzzyFitness`
- `short_name`: `FawxzzyFitness`
- `start_url`: `/`
- `scope`: `/`
- `display`: `standalone`
- icons:
  - `/app/icon-192.png`
  - `/app/icon-512.png`

## Visible Proof Surfaces

Saved deployed page captures:

- `tmp/trove-deployed-page-proof-2026-06-16.png`
- `tmp/fitness-deployed-page-proof-2026-06-16.png`

These captures prove:

- the deployed Trove host renders normally from the same surface that exposes the canonical favicon, manifest, and preview-image routes
- the deployed Fitness host renders normally from the same surface that exposes the canonical favicon, manifest, and preview-image routes

## `_stack` Launcher Consumer

Current launcher consumer proof:

- `repos/_stack/ops/assets/release-launcher.ico`
  - SHA256 `49EF6E187208C643A1345EE71C658F2EC99AFF68BB906DFB09C0BA859A50485B`
- `branding/generated/ico/atlas-sigil-core-launcher.ico`
  - SHA256 `49EF6E187208C643A1345EE71C658F2EC99AFF68BB906DFB09C0BA859A50485B`

Verdict:

- the current `_stack` launcher consumer still matches the canonical launcher output exactly
- no contradictory launcher-cache symptom is currently evidenced in durable surfaces
- future Windows-shell cache drift, if ever observed, should reopen as one bounded cache-only incident rather than as unresolved brand-source drift

## Cache And Unfurl Classification

Observed now:

- deployed HTML metadata is correct
- deployed manifest routes are correct
- deployed icon and preview-image routes are correct
- deployed route bodies match the canonical brand hashes
- visible deployed page captures succeed
- no contradictory stale remote preview result is currently evidenced in durable surfaces

Therefore:

- no source drift remains
- no consumer drift remains
- no deployed-route drift remains
- no active remote cache-only drift remains open

Unfurl/read-model decision:

- the deployed hosts now expose the exact OG/Twitter preview-image metadata and canonical preview-image route bodies required for external card rendering
- this pass uses the deployed page captures plus deployed metadata and image-route parity as the required equivalent preview capture
- no separate unresolved Discord/share-preview blocker remains open after this proof

## Commands And Tools Used

Shell:

- `curl.exe -L -I -sS https://fawxzzy-trove.vercel.app`
- `curl.exe -L -I -sS https://fawxzzy-fitness-local.vercel.app`
- `curl.exe -L -I -sS https://fawxzzy-fitness.vercel.app`
- `curl.exe -L -sS https://fawxzzy-trove.vercel.app/manifest.webmanifest`
- `curl.exe -L -sS https://fawxzzy-fitness-local.vercel.app/manifest.webmanifest`
- deployed route fetch plus `Get-FileHash` parity checks for the listed Trove and Fitness routes
- `Get-FileHash` on:
  - `repos/_stack/ops/assets/release-launcher.ico`
  - `branding/generated/ico/atlas-sigil-core-launcher.ico`

Browser:

- deployed page screenshots for Trove and Fitness

## No-Deploy And No-`tmp` Confirmation

Confirmed for this pass:

- no deploy occurred
- no Vercel settings were mutated
- no Supabase settings were mutated
- no brand assets were rewritten
- `tmp/` was used only as disposable screenshot output, not as a source of truth or workaround

## Marker Decision

- `Preview Cache & Surface Consistency`: `78% -> 100%`

Why:

- the remaining deploy-backed proof is now real
- deployed route parity is canonical for both live app surfaces
- deployed metadata and manifest contracts are correct
- equivalent preview capture now exists
- no contradictory cache-only drift remains active

## Closure Boundary

This closeout does not claim:

- that future third-party social caches can never go stale
- that Windows shell icon cache can never lag the launcher file
- that deploy authority, Vercel provenance, or publication governance are closed

If a future stale preview, stale launcher cache, or share-card mismatch is actually observed while canonical hashes still match, reopen that as one bounded cache-classification incident rather than reopening brand-source truth.
