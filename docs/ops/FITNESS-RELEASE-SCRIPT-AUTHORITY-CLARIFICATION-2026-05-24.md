# Fitness Release-Script Authority Clarification

Date: 2026-05-24
Lane: Manual Deploy Exception Burn-Down
Mode: docs and script-label clarity only
Status: complete

## Goal

Clarify that repo-local Fitness release helpers are not deploy authority, while `_stack` remains the only approved preview and production deploy path.

This package does not deploy, rename scripts, mutate Vercel, mutate Supabase, or change runtime behavior.

## Scope

Changed in `repos/fawxzzy-fitness`:

- `README.md`
- `docs/COMMANDS.md`
- `docs/LOCAL-PROD-DATA-SYNC.md`

## Clarifications Added

The package now states explicitly that:

- repo-local Fitness commands can verify, build, version, and prepare release artifacts
- repo-local Fitness commands do not authorize preview or production deployment by themselves
- `_stack` owns the approved Fitness preview and production deploy orchestration path
- direct repo-local `vercel` or `vercel --prod` use is recovery-only, not the default release workflow

## Why This Package Comes First

This is the narrowest burn-down slice with the highest immediate value:

- it reduces operator confusion in the strongest governed deploy lane
- it addresses the historical wrong-repo or wrong-path deploy failure mode
- it does not widen into deploy script changes, Vercel identity changes, or runtime behavior changes

## Verification

Ran from `repos/fawxzzy-fitness`:

- `npm run sanity:quick`
- `npm run typecheck`
- `npm run build`

Result:

- all passed
- existing React hook lint warnings remain warnings only and are unrelated to this package

## What Did Not Change

- no deploy command behavior changed
- no script names changed
- no Vercel project settings changed
- no Supabase settings changed
- no `tmp` fallback was introduced

## Outcome

Fitness now separates:

- release preparation
- release readiness
- deploy authority

more explicitly in repo-local docs.

The approved production rule remains:

- repo-local helpers may prepare, verify, or build
- `_stack` owns preview and production deploy authority
