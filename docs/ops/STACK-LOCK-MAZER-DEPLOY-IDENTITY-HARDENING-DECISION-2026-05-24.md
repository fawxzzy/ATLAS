# Stack Lock Decision: Mazer Deploy Identity Hardening

Date: 2026-05-24
Lane: Manual Deploy Exception Burn-Down
Package: Mazer deploy identity hardening

## Decision

Accept the `_stack` local-only commit `b3f6159` (`ops: harden mazer deploy identity preflight`) as current stack truth and repin `stack.lock.yaml`.

## Why this is in lock truth

- The change is an operator-layer hardening package inside `repos/_stack`.
- It does not alter live deploy state by itself; it adds a fail-closed local Vercel project-identity gate before Mazer preview or production deploy wrappers can reach Vercel.
- The package closes the Mazer deploy governance gap documented in `docs/ops/MAZER-DEPLOY-IDENTITY-HARDENING-INVENTORY-2026-05-24.md`.

## Repin scope

- `stack.lock.yaml`
  - `_stack.commit`: `7e3be8533f4e179be81777a7d1c9cc95c1656702` -> `b3f6159ec1688c787f5c351dc05c013f5882a5c4`

## Lock refresh note

The full canonical lockfile generator remains blocked in this session because `repos/fawxzzy-foundation` is absent from disk while `stack.yaml` still registers it. This package therefore performs the same narrow `_stack` repin pattern used in earlier governance repairs instead of a full stack-wide regeneration.

## Verification

- Mazer deploy link preflight passed locally.
- `_stack` operator surface validation passed locally.
- Root validation must pass after the lock repin.

## Explicit non-actions

- No deploy was run.
- No Vercel settings were mutated.
- No environment data was pulled.
- No downstream app/source code was changed.
