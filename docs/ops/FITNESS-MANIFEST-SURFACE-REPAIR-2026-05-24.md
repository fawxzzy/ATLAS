# Fitness Manifest Surface Repair

Date: 2026-05-24
Lane: Preview Cache & Surface Consistency
Mode: narrow repo-local repair
Status: complete

## Goal

Repair the local Fitness manifest surface so `manifest.webmanifest` returns manifest JSON instead of the app HTML shell.

This package is intentionally narrow:

- no brand asset sync
- no product feature work
- no Discord or Spotify changes
- no deploy
- no `tmp` fallback

## Problem

Live preview verification found that local Fitness asset routes were healthy, but:

- `http://127.0.0.1:3002/manifest.webmanifest`

returned:

- status `200`
- content type `text/html; charset=utf-8`
- app HTML shell body

That blocked local PWA install-surface proof even though the synced icon assets themselves were already correct.

## Root Cause

The manifest route implementation at `src/app/manifest.ts` already existed and was correct.

The real issue was the middleware matcher in `src/middleware.ts`:

- it excluded common static asset extensions
- it did not exclude `.webmanifest`

That let `/manifest.webmanifest` fall into the middleware path as if it were a normal app route.

## Repo-Local Fix

Changed in `repos/fawxzzy-fitness`:

- `src/middleware.ts`
  - excluded `manifest.webmanifest` and `.webmanifest` from the middleware matcher
- `src/middleware.test.ts`
  - added a regression test that asserts the matcher excludes the manifest route

Fitness repo commit:

- `fe6cf9e7`
- `fix: exclude web manifest from auth middleware`

## Verification

### Repo-local verification

Ran from `repos/fawxzzy-fitness`:

- `npm run sanity:quick`
- `npm run typecheck`
- `npm run build`

Result:

- all commands passed
- existing lint warnings remained warnings only and were unrelated to this manifest fix

### Local route proof

After the fix, local dev served:

- `http://127.0.0.1:3002/manifest.webmanifest`

with:

- status `200`
- content type `application/manifest+json`

Local dev output also showed:

- `/manifest.webmanifest` compiled successfully
- repeated GET requests to `/manifest.webmanifest` returning `200`

## Stack Truth Update

Because canonical Fitness `main` advanced, ATLAS stack truth must carry the new canonical Fitness commit in `stack.lock.yaml`.

This repair does not change:

- canonical repo ownership
- Vercel project identity
- Supabase identity
- brand source ownership
- `tmp` retention posture

## Outcome

The original local preview blocker from Live Pass 1 is closed:

- Fitness local asset routing was already healthy
- Fitness manifest routing is now healthy as well
- local PWA and install-surface proof is no longer blocked by the manifest route itself

Remaining preview work stays outside this package:

- screenshot-level or browser-visual proof
- remote unfurl or cache proof
- any deploy-backed preview validation
