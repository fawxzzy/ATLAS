# Preview Cache Remote And Unfurl Verification Plan

Date: 2026-05-24
Lane: Preview Cache & Surface Consistency
Mode: docs-only planning
Status: planned

## Goal

Define the deploy-required checks needed to finish preview, cache, and unfurl verification after local source, generated-output, and consumer-target alignment has already been proven.

This plan does not deploy, mutate Vercel, mutate Supabase, post to Discord, or write assets.

## Current Proven Baseline

Already proven before this plan:

- canonical ATLAS brand source and generated outputs are hash-stable
- `_stack`, Trove, and Fitness consumer targets match canonical source or generated outputs
- local Trove favicon, manifest, and app-icon routing are healthy
- local Fitness favicon, manifest, and app-icon routing are healthy after the manifest repair
- no `tmp` path was used as a source, consumer, or workaround

What remains is deploy-backed surface proof, remote cache classification, unfurl proof, and launcher visual capture.

## Inputs

- `branding/manifest.json`
- `docs/ops/PREVIEW-CACHE-SURFACE-CONSISTENCY-PLAN-2026-05-24.md`
- `docs/ops/PREVIEW-CACHE-SURFACE-CONSISTENCY-VERIFICATION-2026-05-24.md`
- `docs/ops/PREVIEW-CACHE-SURFACE-LIVE-PASS-1-2026-05-24.md`
- `docs/ops/FITNESS-MANIFEST-SURFACE-REPAIR-2026-05-24.md`
- `repos/fawxzzy-trove/src/app/layout.tsx`
- `repos/fawxzzy-fitness/src/app/layout.tsx`

## Canonical Hash Reference

Use these hashes as the remote truth baseline when deployed surfaces are checked:

| Surface | Canonical path | SHA256 |
| --- | --- | --- |
| Brand master PNG | `branding/source/atlas-sigil-master.png` | `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51` |
| App icon 192 | `branding/generated/app/icon-192.png` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` |
| App icon 512 | `branding/generated/app/icon-512.png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` |
| Apple touch icon | `branding/generated/favicon/apple-touch-icon.png` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` |
| Favicon 32 | `branding/generated/favicon/favicon-32x32.png` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` |
| Favicon 16 | `branding/generated/favicon/favicon-16x16.png` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` |
| Favicon ICO | `branding/generated/favicon/favicon.ico` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` |
| `_stack` launcher icon | `branding/generated/ico/atlas-sigil-core-launcher.ico` | `49EF6E187208C643A1345EE71C658F2EC99AFF68BB906DFB09C0BA859A50485B` |

## Deploy-Required Surface Inventory

### `_stack` launcher visual proof

Expected file:

- `repos/_stack/ops/assets/release-launcher.ico`

Expected hash:

- `49EF6E187208C643A1345EE71C658F2EC99AFF68BB906DFB09C0BA859A50485B`

Needed proof:

- capture the actual Windows launcher or operator-entry visual surface
- confirm the rendered icon matches the canonical launcher output
- if the file hash matches but the shell still shows the old icon, classify that as OS icon-cache drift first

No deploy is required for this slice, but a governed local visual capture path is required.

### Trove deployed routes

Primary deployed base:

- `https://fawxzzy-trove.vercel.app`

Routes to verify after deploy-backed approval:

- `https://fawxzzy-trove.vercel.app/favicon.ico`
- `https://fawxzzy-trove.vercel.app/favicon-32x32.png`
- `https://fawxzzy-trove.vercel.app/favicon-16x16.png`
- `https://fawxzzy-trove.vercel.app/app/icon-192.png`
- `https://fawxzzy-trove.vercel.app/app/icon-512.png`
- `https://fawxzzy-trove.vercel.app/icons/apple-touch-icon.png`
- `https://fawxzzy-trove.vercel.app/brand/atlas-sigil-master.png`
- `https://fawxzzy-trove.vercel.app/manifest.webmanifest`

Metadata-backed preview route already declared by the app:

- `og:image=https://fawxzzy-trove.vercel.app/brand/atlas-sigil-master.png`
- `twitter:image=https://fawxzzy-trove.vercel.app/brand/atlas-sigil-master.png`

### Fitness deployed routes

Canonical metadata fallback base:

- `https://fawxzzy-fitness.vercel.app`

Known deployment-style or production-linked bases that may also require confirmation before a live pass:

- `https://fawxzzy-fitness-local.vercel.app`
- `https://fawxzzy-fitness-preview.vercel.app`
- `https://fawxzzy-fitness-production.vercel.app`

Routes to verify against the approved deployed base:

- `/favicon.ico`
- `/favicon-32x32.png`
- `/favicon-16x16.png`
- `/app/icon-192.png`
- `/app/icon-512.png`
- `/icons/icon-192.png`
- `/icons/icon-512.png`
- `/icons/apple-touch-icon.png`
- `/brand/atlas-sigil-master.png`
- `/manifest.webmanifest`

The future live package must record which deployed base was treated as canonical for the verification run.

## Expected Content Types

Accept these content types or strict equivalents when remote checks run:

| Surface kind | Expected content type |
| --- | --- |
| Favicon ICO | `image/x-icon` or equivalent ICO media type |
| PNG icon or preview image | `image/png` |
| Web manifest | `application/manifest+json` |
| HTML root metadata page | `text/html; charset=utf-8` |

If a route returns HTML where manifest or image content is expected, classify that as a routing or deployment issue, not a cache-only drift.

## Remote Verification Sequence

When a deploy-backed verification package is explicitly approved, use this order:

1. confirm the deployed base URL being checked
2. fetch the remote asset route
3. record status code and content type
4. hash the returned body when the asset is binary and compare against canonical reference
5. inspect the deployed root HTML for manifest, favicon, app-icon, apple-touch, and OG/Twitter references
6. only then classify stale-looking results as cache-only drift candidates

## Cache Vs Source Drift Classification

Use this decision order for remote surfaces:

1. Do the ATLAS canonical source and generated-output hashes still match the expected baseline?
   - no -> source drift
   - yes -> continue

2. Do the local consumer targets still match canonical hashes?
   - no -> consumer drift
   - yes -> continue

3. Does the deployed asset route body hash match the expected canonical hash?
   - no -> deploy or route drift
   - yes -> continue

4. Does the deployed HTML or manifest reference the expected route?
   - no -> metadata or route wiring drift
   - yes -> continue

5. Does the visible browser, PWA, or unfurl surface still look stale?
   - yes -> classify as cache-only drift candidate first
   - no -> mark consistent

6. Is someone proposing `tmp` as a fallback?
   - reject immediately
   - `tmp` is never a valid fix path for preview or cache verification

## Unfurl Verification Path

Unfurl proof is a separate surface from raw asset proof.

Future deploy-backed unfurl verification should capture:

- deployed page URL under test
- deployed HTML metadata values for:
  - `og:image`
  - `twitter:image`
  - title
  - description
- remote preview-image route status, content type, and hash
- one observed external unfurl result or equivalent preview capture

Treat these as deploy-required, not failed by default:

- Discord unfurl result for Trove
- Discord unfurl result for Fitness
- any remote share-preview cache behavior

## Browser Cache And PWA Classification

For browser or install surfaces:

- if deployed asset routes and manifest content are correct but the browser still shows stale icons, classify as browser-cache or install-cache drift candidate
- if deployed manifest content is wrong, classify as manifest or routing drift
- if deployed root HTML points to the wrong icon routes, classify as metadata drift

## No-Deploy And No-`tmp` Rules

This plan does not authorize:

- manual deploys
- Vercel project mutation
- Supabase mutation
- Discord posting
- brand asset rewrites
- `tmp` fallback consumption

Any later live remote run must be an explicit package with its own approval boundary.

## Future Receipt Format

The future deploy-backed verification package should create:

- `docs/ops/PREVIEW-CACHE-REMOTE-UNFURL-VERIFICATION-YYYY-MM-DD.md`

Minimum receipt sections:

1. deployed base URLs checked
2. exact routes fetched
3. status code and content type table
4. remote asset hash table
5. deployed HTML and manifest reference proof
6. unfurl or preview capture evidence
7. cache-only drift vs source-drift classification
8. no-deploy or approved-deploy statement
9. no-`tmp` confirmation

## Lane Interpretation

Preview Cache & Surface Consistency is no longer waiting on asset sync.

What remains is controlled proof for:

- deployed asset parity
- browser and install-surface cache behavior
- Discord or share-preview unfurls
- launcher visual rendering

Those are verification and classification tasks, not source-of-truth repair tasks.
