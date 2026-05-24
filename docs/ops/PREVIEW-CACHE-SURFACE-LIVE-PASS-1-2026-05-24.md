# Preview Cache Surface Live Pass 1

Date: 2026-05-24
Lane: Preview Cache & Surface Consistency
Mode: verification only
Status: partial pass with one local runtime blocker

## Goal

Verify live or runtime-facing brand surfaces for already-synced consumers without deploying and without mutating assets.

This pass covers:

1. `_stack` launcher runtime classification
2. Trove local browser-facing surface proof
3. Fitness local browser-facing surface proof
4. unfurl and remote-cache classification

## Constraints

- no deploy
- no Vercel mutation
- no Supabase mutation
- no asset writes
- no `tmp` fallback
- no Discord posting

## Method

### Browser path attempted

The in-app browser automation path was attempted through the Browser skill runtime and timed out twice while attaching to the `iab` browser surface.

Result:

- direct visual screenshot proof was not available through the expected browser-control path in this session
- this pass falls back to the next-best live proof:
  - local HTTP responses
  - root HTML metadata inspection
  - manifest resolution
  - runtime asset fetches and hash checks

This is sufficient to classify runtime asset routing and manifest behavior, but not enough to claim literal pixel-level favicon or launcher rendering screenshots.

### Local runtime surfaces used

- Trove local server on `http://127.0.0.1:3101`
- Fitness local server on `http://127.0.0.1:3002`

These temporary local servers were stopped after verification.

## `_stack` Launcher Surface

### Proven now

- `repos/_stack/ops/assets/release-launcher.ico` exists
- file hash matches canonical launcher output:
  - `49EF6E187208C643A1345EE71C658F2EC99AFF68BB906DFB09C0BA859A50485B`
- the `_stack` operator-surface lane already carries prior sync and verification receipts

### Not proven in this pass

- actual Windows launcher icon rendering in a visible launcher surface
- OS-level icon cache behavior

### Classification

- file-level launcher truth: proven
- launcher visual/runtime rendering: pending local visual proof

## Trove Local Browser-Facing Surface

### Root HTML metadata proof

Local Trove root at `http://127.0.0.1:3101/` advertises:

- manifest: `/manifest.webmanifest`
- favicon ICO: `/favicon.ico`
- favicon PNGs:
  - `/favicon-32x32.png`
  - `/favicon-16x16.png`
- app icons:
  - `/app/icon-192.png`
  - `/app/icon-512.png`
- apple-touch icon:
  - `/icons/apple-touch-icon.png`

Trove local metadata also exposes:

- `og:image=https://fawxzzy-trove.vercel.app/brand/atlas-sigil-master.png`
- `twitter:image=https://fawxzzy-trove.vercel.app/brand/atlas-sigil-master.png`

### Manifest proof

`http://127.0.0.1:3101/manifest.webmanifest` returns valid JSON with:

- `name=Trove`
- `short_name=Trove`
- `start_url=/`
- `display=standalone`
- icons:
  - `/app/icon-192.png`
  - `/app/icon-512.png`

### Runtime asset proof

The following Trove runtime asset routes returned `200` and matched expected canonical hashes:

- `/favicon.ico`
- `/favicon-32x32.png`
- `/favicon-16x16.png`
- `/app/icon-192.png`
- `/app/icon-512.png`
- `/icons/apple-touch-icon.png`

### Classification

- local favicon and icon routing: proven
- local manifest routing: proven
- local PWA icon references: proven
- deployed unfurl or remote-cache surface: deploy-backed proof still required

## Fitness Local Browser-Facing Surface

### Root HTML metadata proof

Local Fitness root at `http://127.0.0.1:3002/` advertises:

- manifest: `/manifest.webmanifest`
- shortcut icon: `/icons/icon-192.png`
- favicon ICO: `/favicon.ico`
- favicon PNGs:
  - `/favicon-32x32.png`
  - `/favicon-16x16.png`
- app icons:
  - `/app/icon-192.png`
  - `/app/icon-512.png`
- apple-touch icon:
  - `/icons/apple-touch-icon.png`

Fitness local metadata also exposes:

- `og:image=http://localhost:3002/brand/atlas-sigil-master.png`
- `twitter:image=http://localhost:3002/brand/atlas-sigil-master.png`

### Runtime asset proof

The following Fitness runtime asset routes returned `200` and matched expected canonical hashes:

- `/favicon.ico`
- `/favicon-32x32.png`
- `/favicon-16x16.png`
- `/app/icon-192.png`
- `/app/icon-512.png`
- `/icons/icon-192.png`
- `/icons/icon-512.png`
- `/icons/apple-touch-icon.png`
- `/brand/atlas-sigil-master.png`

### Local manifest blocker

`http://127.0.0.1:3002/manifest.webmanifest` did not return manifest JSON.

Observed result:

- status: `200`
- content type: `text/html; charset=utf-8`
- body prefix: `<!DOCTYPE html>...`

Meaning:

- the manifest route currently resolves to the app HTML shell in local dev instead of a web app manifest document
- favicon and icon asset routing is good
- local manifest and PWA install-surface proof is blocked by this runtime behavior

### Classification

- local favicon routing: proven
- local icon asset routing: proven
- local brand master route for preview image: proven
- local manifest routing: blocked by runtime issue
- local install-surface proof: blocked until manifest route is fixed

## Unfurl And Remote Cache Classification

### Trove

Trove local metadata points OG and Twitter images to the deployed host:

- `https://fawxzzy-trove.vercel.app/brand/atlas-sigil-master.png`

Classification:

- local metadata presence: proven
- actual external unfurl result: deploy-backed verification still required
- stale remote preview, if observed later while hashes still match, should be treated as cache-only drift candidate first

### Fitness

Fitness local metadata points OG and Twitter images to local host:

- `http://localhost:3002/brand/atlas-sigil-master.png`

Classification:

- local metadata presence: proven
- external unfurl proof is impossible from this local host reference
- deploy-backed proof is required to evaluate real remote preview behavior

## No-Deploy And No-`tmp` Confirmation

Confirmed for this pass:

- no deploy occurred
- no Vercel mutation occurred
- no Supabase mutation occurred
- no assets were rewritten
- no `tmp` path was used as source, consumer, or workaround

## Result Summary

### Proven in Live Pass 1

- `_stack` launcher file remains aligned to canonical launcher output
- Trove local root HTML references the expected favicon, app icon, apple-touch, and manifest surfaces
- Trove local manifest route returns valid JSON
- Trove local runtime asset routes resolve and hash-match canonical outputs
- Fitness local root HTML references the expected favicon, app icon, shortcut icon, apple-touch, and manifest surfaces
- Fitness local runtime asset routes resolve and hash-match canonical outputs

### Blocked or still pending

- `_stack` visual launcher rendering proof
- Trove screenshot-level favicon or PWA visual proof
- Fitness screenshot-level favicon or PWA visual proof
- Fitness local manifest route is wrong in local dev and blocks install-surface proof
- all remote or deployed unfurl proof remains deploy-required

## Lane Interpretation

This pass moves the lane beyond pure file alignment and into real runtime classification:

- Trove local browser-facing surfaces are materially healthy
- Fitness local asset routing is healthy, but manifest routing is not
- `_stack` launcher file truth is healthy, but visual launcher proof still needs a governed local capture path
- remaining unfurl and remote preview checks are not failed; they are deploy-required
