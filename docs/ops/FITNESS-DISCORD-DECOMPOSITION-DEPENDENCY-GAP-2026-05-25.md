# Fitness Discord Decomposition Dependency Gap

Date: 2026-05-25
Lane: Discord OS Infrastructure Separation
Mode: docs-only dependency classification
Status: recorded

## Goal

Record and classify the local Fitness dependency and tooling gaps that blocked full repo verification after Discord Route Decomposition Package 1.

## Inputs Reviewed

- `docs/ops/DISCORD-ROUTE-DECOMPOSITION-PACKAGE-1-2026-05-25.md`
- `repos/fawxzzy-fitness/package.json`
- `repos/fawxzzy-fitness/package-lock.json`
- `repos/fawxzzy-fitness/scripts/next-cli.mjs`
- `repos/fawxzzy-fitness/scripts/tsc-cli.mjs`
- current `repos/fawxzzy-fitness` git status
- route-domain test output from the decomposition package

## Findings

### Missing `next` binary

- failing command: `npm run sanity:quick`
- direct failure: `Cannot find module 'next/dist/bin/next'`
- package declaration state:
  - declared in `package.json`
  - present in `package-lock.json`
- local install state:
  - `node_modules/next` absent
- classification: install-state only

### Missing TypeScript binary

- failing command: `npm run typecheck`
- direct failure: `Cannot find module 'typescript/bin/tsc'`
- package declaration state:
  - declared in `package.json`
  - present in `package-lock.json`
- local install state:
  - `node_modules/typescript` absent
- classification: install-state only

### Missing `sharp`

- failing command: `npm run build`
- direct failure: `Cannot find package 'sharp'`
- package declaration state:
  - declared in `package.json`
  - present in `package-lock.json`
- local install state:
  - `node_modules/sharp` absent
- classification: install-state only

### Missing `tweetnacl`

- failing command:
  - `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts`
- direct failure: `Cannot find package 'tweetnacl'`
- package declaration state:
  - declared in `package.json`
  - present in `package-lock.json`
- local install state:
  - `node_modules/tweetnacl` absent
- classification: install-state only

### Unrelated tracked Fitness changes

Current unrelated tracked modifications remain in:

- `repos/fawxzzy-fitness/package.json`
- `repos/fawxzzy-fitness/public/app/icon-192.png`
- `repos/fawxzzy-fitness/public/app/icon-512.png`
- `repos/fawxzzy-fitness/public/favicon-16x16.png`
- `repos/fawxzzy-fitness/public/favicon-32x32.png`
- `repos/fawxzzy-fitness/public/favicon.ico`
- `repos/fawxzzy-fitness/public/sw.js`
- `repos/fawxzzy-fitness/scripts/mobile_regression/__pycache__/__init__.cpython-313.pyc`
- `repos/fawxzzy-fitness/scripts/mobile_regression/__pycache__/board_builder.cpython-313.pyc`
- `repos/fawxzzy-fitness/src/generated/appBuildManifest.json`
- `repos/fawxzzy-fitness/src/lib/stretch-library-details.ts`
- `repos/fawxzzy-fitness/src/lib/stretch-library-summaries.ts`

Classification:

- not caused by the Discord decomposition package
- requires awareness during verification restore so the repo is not misread as clean-after-package
- manual review for ownership, but not evidence of a dependency declaration failure by itself

## Overall Classification

The dependency gap is currently best explained as:

- local `node_modules` install-state gap
- not a missing dependency declaration problem
- not package-lock omission for the named blockers
- not a Discord route decomposition source-code regression

## Decision

Decision:

- safe to run `npm ci` and retry full verification

Not indicated by current evidence:

- package dependency fix
- source-code rollback
- DiscordOS extraction continuation before verification restore

## Blocking Effect

Keep the next Discord runtime utility extraction blocked until the Fitness verification baseline is restored through:

1. `npm ci`
2. `npm run sanity:quick`
3. `npm run typecheck`
4. `npm run build`
5. `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/runtime/route-domains.test.ts`
6. existing route test retry once `tweetnacl` is restored

## Notes

- `package-lock.json` is present and already includes `next`, `typescript`, `sharp`, and `tweetnacl`
- the problem is that the corresponding installed packages are absent from `node_modules`
- this receipt does not approve any DiscordOS code movement, Supabase mutation, Vercel mutation, or deploy activity
