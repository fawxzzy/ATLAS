# Preview Cache & Surface Consistency Plan

Date: 2026-05-24
Lane: Preview Cache & Surface Consistency
Mode: docs-only planning
Status: planned

## Goal

Define how to verify that the canonical ATLAS brand source and generated outputs appear consistently across `_stack`, Trove, and Fitness consumer surfaces without using deploys by default and without ever writing into `tmp/`.

## Current Brand Baseline

Canonical source and generated outputs are already aligned to consumers as follows:

- `_stack` launcher icon sync
  - committed and accepted into stack truth
- Trove public brand targets
  - committed and accepted into stack truth
- Fitness icon targets
  - aligned locally from canonical outputs
  - did not require a Fitness repo commit because `public/icons/*.png` is intentionally ignored

This lane begins after asset sync and focuses on proof that visible surfaces match the governed source.

## Canonical Hash Set

The current canonical ATLAS outputs to verify against are:

| Surface | Canonical path | SHA256 |
| --- | --- | --- |
| `_stack` launcher icon | `branding/generated/ico/atlas-sigil-core-launcher.ico` | `49EF6E187208C643A1345EE71C658F2EC99AFF68BB906DFB09C0BA859A50485B` |
| Brand master PNG | `branding/source/atlas-sigil-master.png` | `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51` |
| App icon 192 | `branding/generated/app/icon-192.png` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` |
| App icon 512 | `branding/generated/app/icon-512.png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` |
| Apple touch icon | `branding/generated/favicon/apple-touch-icon.png` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` |
| Favicon 32 | `branding/generated/favicon/favicon-32x32.png` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` |
| Favicon 16 | `branding/generated/favicon/favicon-16x16.png` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` |
| Favicon ICO | `branding/generated/favicon/favicon.ico` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` |

## Consumer Hash Baseline

Known current consumer matches:

### `_stack`

- `repos/_stack/ops/assets/release-launcher.ico`
  - matches canonical launcher hash `49EF6E187208C643A1345EE71C658F2EC99AFF68BB906DFB09C0BA859A50485B`

### Trove

- `repos/fawxzzy-trove/public/brand/atlas-sigil-master.png`
  - matches canonical brand master hash
- `repos/fawxzzy-trove/public/app/icon-192.png`
  - matches canonical app icon 192 hash
- `repos/fawxzzy-trove/public/app/icon-512.png`
  - matches canonical app icon 512 hash
- `repos/fawxzzy-trove/public/icons/apple-touch-icon.png`
  - matches canonical apple-touch hash
- `repos/fawxzzy-trove/public/favicon-32x32.png`
  - matches canonical favicon 32 hash
- `repos/fawxzzy-trove/public/favicon-16x16.png`
  - matches canonical favicon 16 hash
- `repos/fawxzzy-trove/public/favicon.ico`
  - matches canonical favicon ICO hash

### Fitness

- `repos/fawxzzy-fitness/public/brand/atlas-sigil-master.png`
  - matches canonical brand master hash
- `repos/fawxzzy-fitness/public/app/icon-192.png`
  - matches canonical app icon 192 hash
- `repos/fawxzzy-fitness/public/app/icon-512.png`
  - matches canonical app icon 512 hash
- `repos/fawxzzy-fitness/public/icons/icon-192.png`
  - matches canonical app icon 192 hash
- `repos/fawxzzy-fitness/public/icons/icon-512.png`
  - matches canonical app icon 512 hash
- `repos/fawxzzy-fitness/public/icons/apple-touch-icon.png`
  - matches canonical apple-touch hash
- `repos/fawxzzy-fitness/public/favicon-32x32.png`
  - matches canonical favicon 32 hash
- `repos/fawxzzy-fitness/public/favicon-16x16.png`
  - matches canonical favicon 16 hash
- `repos/fawxzzy-fitness/public/favicon.ico`
  - matches canonical favicon ICO hash

## Verification Tracks

This lane should verify four distinct surface types:

1. file-level consumer alignment
2. browser-visible favicon and PWA icon surfaces
3. launcher or install-entry surfaces
4. share or unfurl surfaces that may lag due to cache

## Consumer Verification Plan

### `_stack` launcher icon

Evidence needed:

- file hash match against `branding/generated/ico/atlas-sigil-core-launcher.ico`
- operator-surface test already passing
- if Windows launcher verification is needed later:
  - capture actual launcher icon rendering from the operator entry surface
  - confirm no stale icon cache is masking the file-level truth

Preferred path:

- file hash proof first
- operator launch or screenshot proof second

### Trove browser and share surfaces

Surfaces:

- browser favicon
- PWA app icons
- public brand master usage
- Trove landing surfaces
- potential unfurl or social preview surfaces if the app emits them

Evidence needed:

- file hash matches for current public targets
- browser load against the relevant local or preview route
- favicon/network inspection or screenshot
- if unfurl is tested later:
  - one explicit evidence path for how Trove cards or external share previews are rendered

Preferred path:

1. local file hashes
2. browser verification against local Trove route
3. unfurl-specific verification only if the app actually emits that surface

### Fitness browser and install surfaces

Surfaces:

- browser favicon
- app manifest icons
- PWA install icon surfaces
- any route using `public/icons/**`

Evidence needed:

- file hash matches for current public targets
- browser verification against local Fitness route
- manifest and icon response inspection if needed
- if install-surface proof is needed later:
  - local browser evidence first
  - device-specific install evidence only if explicitly required

Preferred path:

1. local file hashes
2. browser verification on a local Fitness route
3. install-prompt or launcher verification only when explicitly needed

## Browser and PWA Verification Path

Default path:

1. verify consumer files by hash
2. open the local consumer route in browser automation
3. confirm favicon, manifest, and icon references resolve to the expected files
4. capture screenshots only when the surface is visually meaningful

Suggested future checks:

- `_stack`
  - operator launch icon surface or equivalent UI surface
- Trove
  - root route favicon and app icon references
- Fitness
  - root route favicon
  - `/manifest.webmanifest`
  - any install-facing route or metadata surface

No deploy should occur by default for this lane.

## Discord and Unfurl Verification Path

This lane should treat unfurls as their own cache-sensitive verification track.

Required evidence before calling an unfurl surface consistent:

1. source and consumer file hashes are already current
2. the app is known to emit the preview image or metadata being checked
3. one captured external result or bot-observed result matches the expected surface
4. if stale, the stale result can be classified as cache drift rather than source drift

Examples:

- Discord update posts that embed app links
- Trove cards or external share previews
- any OG image route if one exists later

## Cache vs Source Drift Decision Tree

Use this decision tree whenever a visible surface looks wrong:

1. Do source hashes match the canonical ATLAS outputs?
   - no -> source drift, repair the consumer file package
   - yes -> continue

2. Does the consumer target hash match the expected source hash?
   - no -> consumer drift, repair the consumer package
   - yes -> continue

3. Does the local browser surface still look stale?
   - yes -> likely local cache or generated-surface issue, inspect favicon, manifest, and cached assets
   - no -> continue

4. Does an external share or unfurl still look stale?
   - yes -> likely remote cache or preview-surface cache, classify as cache-only drift until proven otherwise
   - no -> mark consistent

5. Is someone proposing `tmp` as a workaround?
   - reject immediately
   - `tmp` is never a valid fix for preview or cache consistency

## Evidence Threshold For Consistent

A surface should not be marked consistent until all applicable evidence is present:

- canonical source hash recorded
- consumer target hash recorded
- visible local surface checked when relevant
- cache-only drift classified if the visible surface still lags despite matching files
- no `tmp` fallback or alternate checkout was used

## No-Deploy Default

This lane is no-deploy by default.

Do not:

- deploy for a first-pass consistency check
- mutate Vercel project settings
- mutate Supabase
- rewrite consumer assets in `tmp/`
- treat cache drift as a reason to bypass canonical consumer paths

Deploy or remote cache invalidation should happen only if a later explicit package approves it.

## Future Package Order

1. docs-only verification plan
2. `_stack` local launcher verification if additional visible proof is needed
3. Trove browser/favicon verification
4. Fitness browser/manifest/favicon verification
5. optional unfurl verification package
6. only then decide whether any cache invalidation or deploy-backed proof is required

## Current Lane Interpretation

Preview Cache & Surface Consistency is now no longer about syncing assets.

It is about proving:

- synced files really match the canonical source
- visible browser and launcher surfaces reflect those files
- stale external previews can be classified as cache-only drift when the source and consumer files are already correct

## Current Marker Implication

After this plan is packaged:

- `Preview Cache & Surface Consistency`
  - `45%`
- `Brand Asset Canonicalization`
  - remains `80%`
