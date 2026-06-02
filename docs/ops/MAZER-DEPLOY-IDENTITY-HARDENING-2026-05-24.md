# Mazer Deploy Identity Hardening

Date: 2026-05-24
Lane: Manual Deploy Exception Burn-Down
Package: Mazer deploy identity hardening
Mode: Narrow `_stack` operator hardening only

## Goal

Fail closed before any `_stack` Mazer preview or production deploy path can reach Vercel unless the local Mazer repo is linked to the pinned canonical Vercel project identity.

## Pinned identity

- `orgId`: `team_CMJn7MvzFZZBnhNnjVUZF2RD`
- `projectId`: `prj_t3zothbtj9DExrh3FjMsH98hwwSZ`
- `projectName`: `fawxzzy-mazer`

## Operator surfaces changed

- `_stack` pinned Mazer deploy identity config:
  - `repos/_stack/config/mazer-deploy.identity.json`
- `_stack` Mazer local-link preflight:
  - `repos/_stack/ops/Test-MazerDeployLink.ps1`
- `_stack` Mazer deploy wrapper and preflight wiring:
  - `repos/_stack/ops/Invoke-MazerDeploy.ps1`
  - `repos/_stack/package.json`
- `_stack` operator docs and launcher metadata:
  - `repos/_stack/README.md`
  - `repos/_stack/config/release-targets.json`
  - `repos/_stack/ops/codex/Test-StackOperatorSurface.ps1`

## Behavior

1. Read `repos/mazer/.vercel/project.json`.
2. Fail closed if the file is missing.
3. Fail closed if `orgId`, `projectId`, or `projectName` differ from the pinned identity.
4. Print a clear operator message that includes expected and observed identity values plus the corrective local `vercel link` command.
5. Keep the existing Mazer author-identity preflight in place.
6. Require both preflights before `_stack` Mazer preview or production wrappers can reach Vercel.

## Verification

From `repos/_stack`:

- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\Test-MazerDeployLink.ps1 -ConfigPath .\config\mazer-deploy.identity.json`
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\Test-StackOperatorSurface.ps1`

Observed result:

- Mazer deploy link preflight passed against the current local Mazer Vercel link.
- `_stack` operator surface validation passed.
- Operator-surface coverage now includes:
  - positive proof against the real local `.vercel/project.json`
  - negative proof using a temporary git fixture with a mismatched `projectId`

From `C:\ATLAS` after root repin:

- `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`

## Explicit non-actions

- No deploy was run.
- No `vercel deploy` command was run.
- No `vercel link` command was run.
- No Vercel settings were mutated.
- No env was pulled.
- No Supabase state was touched.
- No Mazer app/source code or assets were changed.
- No Fitness or Trove surfaces were touched.
- No `tmp` fallback was used.

## Outcome

Mazer now matches the current deploy-governance standard more closely:

- author identity remains enforced
- immutable local Vercel project identity is now also enforced
- `_stack` preview and prod wrappers no longer rely on author identity alone before reaching Vercel
