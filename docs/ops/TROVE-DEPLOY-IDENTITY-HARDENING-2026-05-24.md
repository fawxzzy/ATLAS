# Trove Deploy Identity Hardening

Date: 2026-05-24
Lane: Manual Deploy Exception Burn-Down
Package: Trove deploy identity hardening
Mode: Narrow `_stack` operator hardening only

## Goal

Fail closed before any `_stack` Trove preview or production deploy path can reach Vercel unless the local Trove repo is linked to the pinned canonical Vercel project identity.

## Pinned identity

- `orgId`: `team_CMJn7MvzFZZBnhNnjVUZF2RD`
- `projectId`: `prj_vhUyajI4AL6BgCF40VnKtdxrBLuV`
- `projectName`: `fawxzzy-trove`

## Operator surfaces changed

- `_stack` pinned Trove deploy identity config:
  - `repos/_stack/config/trove-deploy.identity.json`
- `_stack` Trove preflight script:
  - `repos/_stack/ops/Test-TroveDeployLink.ps1`
- `_stack` package scripts:
  - `trove:deploy:preflight`
  - `trove:build:vercel`
  - `trove:deploy:preview`
  - `trove:deploy:prod`
- `_stack` operator docs and launcher metadata:
  - `repos/_stack/README.md`
  - `repos/_stack/config/release-targets.json`
  - `repos/_stack/ops/codex/Test-StackOperatorSurface.ps1`

## Behavior

1. Read `repos/fawxzzy-trove/.vercel/project.json`.
2. Fail closed if the file is missing.
3. Fail closed if `orgId`, `projectId`, or `projectName` differ from the pinned identity.
4. Print a clear operator fix command that relinks the local repo without attempting a deploy.
5. Require the preflight before the standard Trove preview, prod, and Vercel build wrapper paths.

## Verification

From `repos/_stack`:

- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\Test-TroveDeployLink.ps1 -ConfigPath .\config\trove-deploy.identity.json`
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\Test-StackOperatorSurface.ps1`

Observed result:

- Trove deploy preflight passed against the pinned local Vercel link.
- `_stack` operator surface validation passed.

From the ATLAS root (`.`) after root repin:

- `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`

## Explicit non-actions

- No deploy was run.
- No `vercel deploy` command was run.
- No Vercel settings were mutated.
- No env was pulled.
- No Supabase state was touched.
- No Trove app/source code or brand assets were changed.
- No Fitness surfaces were touched.
- No `tmp` fallback was used.

## Outcome

Trove now matches Fitness in one critical way: `_stack` no longer treats local Trove deploy wrappers as sufficient by themselves. The operator path now validates immutable local Vercel identity first, then proceeds to repo-local verification and deploy only if that identity is correct.
