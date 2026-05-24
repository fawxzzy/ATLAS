# Preview Cache Surface Consistency Verification

Date: 2026-05-24
Lane: Preview Cache & Surface Consistency
Mode: verification only
Status: pass 1 complete

## Scope

This pass verifies file-level consistency across:

- canonical ATLAS branding source and generated outputs
- `_stack` launcher icon consumer
- Trove public brand, app icon, and favicon consumers
- Fitness public brand, app icon, public icon, and favicon consumers

This pass does not deploy, mutate Vercel, mutate Supabase, or write into `tmp/`.

## Inputs

- `branding/manifest.json`
- `docs/ops/PREVIEW-CACHE-SURFACE-CONSISTENCY-PLAN-2026-05-24.md`
- `docs/ops/BRAND-STACK-LAUNCHER-SYNC-2026-05-23.md`
- `docs/ops/BRAND-TROVE-SYNC-2026-05-24.md`
- `docs/ops/BRAND-FITNESS-SYNC-2026-05-24.md`

## Canonical Source And Generated Output Proof

### Canonical source proof

| Surface | Path | SHA256 |
| --- | --- | --- |
| Brand master PNG | `branding/source/atlas-sigil-master.png` | `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51` |
| Launcher ICO source variant | `branding/generated/ico/atlas-sigil-core-launcher.ico` | `49EF6E187208C643A1345EE71C658F2EC99AFF68BB906DFB09C0BA859A50485B` |

### Generated output proof

| Output | Path | SHA256 |
| --- | --- | --- |
| `atlas-sigil-png-1024` | `branding/generated/png/atlas-sigil-1024.png` | `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51` |
| `atlas-sigil-png-512` | `branding/generated/png/atlas-sigil-512.png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` |
| `atlas-sigil-png-256` | `branding/generated/png/atlas-sigil-256.png` | `9C6481CC7FE120EE117A375E702C6BFA434BCBC55E98F2BE51695DBE0CF7B16F` |
| `atlas-sigil-app-192` | `branding/generated/app/icon-192.png` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` |
| `atlas-sigil-app-512` | `branding/generated/app/icon-512.png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` |
| `atlas-sigil-apple-touch` | `branding/generated/favicon/apple-touch-icon.png` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` |
| `atlas-sigil-favicon-32` | `branding/generated/favicon/favicon-32x32.png` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` |
| `atlas-sigil-favicon-16` | `branding/generated/favicon/favicon-16x16.png` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` |
| `atlas-sigil-core-launcher-ico` | `branding/generated/ico/atlas-sigil-core-launcher.ico` | `49EF6E187208C643A1345EE71C658F2EC99AFF68BB906DFB09C0BA859A50485B` |
| `atlas-sigil-favicon-ico` | `branding/generated/favicon/favicon.ico` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` |

## Consumer Target Proof

### `_stack`

| Consumer | Target | Expected SHA256 | Actual SHA256 | Result |
| --- | --- | --- | --- | --- |
| `stack-launcher-icon` | `repos/_stack/ops/assets/release-launcher.ico` | `49EF6E187208C643A1345EE71C658F2EC99AFF68BB906DFB09C0BA859A50485B` | `49EF6E187208C643A1345EE71C658F2EC99AFF68BB906DFB09C0BA859A50485B` | match |

### Trove

| Consumer | Target | Expected SHA256 | Actual SHA256 | Result |
| --- | --- | --- | --- | --- |
| `trove-brand-master` | `repos/fawxzzy-trove/public/brand/atlas-sigil-master.png` | `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51` | `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51` | match |
| `trove-app-icon-192` | `repos/fawxzzy-trove/public/app/icon-192.png` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | match |
| `trove-app-icon-512` | `repos/fawxzzy-trove/public/app/icon-512.png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | match |
| `trove-apple-touch` | `repos/fawxzzy-trove/public/icons/apple-touch-icon.png` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` | match |
| `trove-favicon-32` | `repos/fawxzzy-trove/public/favicon-32x32.png` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` | match |
| `trove-favicon-16` | `repos/fawxzzy-trove/public/favicon-16x16.png` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` | match |
| `trove-favicon-ico` | `repos/fawxzzy-trove/public/favicon.ico` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` | match |

### Fitness

| Consumer | Target | Expected SHA256 | Actual SHA256 | Result |
| --- | --- | --- | --- | --- |
| `fitness-brand-master` | `repos/fawxzzy-fitness/public/brand/atlas-sigil-master.png` | `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51` | `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51` | match |
| `fitness-app-icon-192` | `repos/fawxzzy-fitness/public/app/icon-192.png` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | match |
| `fitness-app-icon-512` | `repos/fawxzzy-fitness/public/app/icon-512.png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | match |
| `fitness-public-icon-192` | `repos/fawxzzy-fitness/public/icons/icon-192.png` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` | match |
| `fitness-public-icon-512` | `repos/fawxzzy-fitness/public/icons/icon-512.png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` | match |
| `fitness-apple-touch` | `repos/fawxzzy-fitness/public/icons/apple-touch-icon.png` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` | match |
| `fitness-favicon-32` | `repos/fawxzzy-fitness/public/favicon-32x32.png` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` | match |
| `fitness-favicon-16` | `repos/fawxzzy-fitness/public/favicon-16x16.png` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` | match |
| `fitness-favicon-ico` | `repos/fawxzzy-fitness/public/favicon.ico` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` | match |

## Verification Result

File-level proof is clean:

- all declared consumer targets match their canonical source or generated-output hashes
- no file-level source drift was found
- no file-level consumer drift was found
- no `tmp` path was used as a source, consumer, or workaround
- no deploy was used or required for this pass

## Remaining Surface Classes Requiring Live Proof

This pass does not prove browser or external-cache presentation by itself. The following surfaces still require live verification or cache-aware classification:

### `_stack`

- launcher or operator-entry visual rendering
- any OS-level icon cache behavior that could mask the correct file-level icon

### Trove

- browser favicon rendering
- any PWA install-icon behavior if the Trove app exposes an install surface
- any OG or share-preview route the app emits
- any Discord or Trove-card unfurl surface backed by cached remote metadata

### Fitness

- browser favicon rendering
- local PWA manifest or install-icon presentation
- any browser route that depends on `public/icons/**`
- any external unfurl or preview surface if one exists in the deployed app

## Deployment And Cache Interpretation

This pass proves local source and consumer alignment, not remote deployment parity.

Current classification rules:

- if source and consumer hashes match but a browser surface still looks stale, classify that as local browser or generated-surface cache until proven otherwise
- if deployed or unfurled surfaces look stale while source and consumer hashes match, classify that as cache-only drift candidate until deployment-backed proof exists
- do not treat cache lag as permission to write into `tmp/`

Reference decision tree:

- `docs/ops/PREVIEW-CACHE-SURFACE-CONSISTENCY-PLAN-2026-05-24.md`

## Evidence Threshold Reached In Pass 1

The following evidence threshold is satisfied now:

- canonical source hashes recorded
- generated output hashes recorded
- consumer target hashes recorded
- no source drift found
- no consumer drift found
- no `tmp` fallback used
- no deploy used

The following evidence threshold is still pending:

- visible browser proof for favicon and PWA surfaces
- launcher visual proof beyond file hash alignment
- any external unfurl proof
- any remote-cache classification tied to deployed surfaces

## Lane Interpretation

Preview Cache & Surface Consistency has moved past asset-sync ambiguity and into surface-proof work.

What is now proven:

- canonical ATLAS brand source and generated outputs are internally consistent
- `_stack`, Trove, and Fitness declared consumers are file-level aligned to the canonical outputs
- the current remaining risk is presentation or cache drift, not source-of-truth drift

What remains to close later:

- browser favicon and manifest proof
- PWA or install-surface proof where applicable
- launcher visual proof where applicable
- OG, share, or Discord unfurl proof where applicable
