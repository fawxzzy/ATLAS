# Stack Lock Decision: Trove Deploy Identity Hardening

Date: 2026-05-24
Lane: Manual Deploy Exception Burn-Down
Package: Trove deploy identity hardening

## Decision

Accept the `_stack` local-only commit `7e3be85` (`ops: harden trove deploy identity preflight`) as current stack truth and repin `stack.lock.yaml`.

## Why this is in lock truth

- The change is an operator-layer hardening package inside `repos/_stack`.
- It does not alter live deploy behavior by itself; it adds a fail-closed preflight before Trove preview/prod wrappers can reach Vercel.
- The package closes a known deploy governance gap documented in `docs/ops/TROVE-DEPLOY-IDENTITY-HARDENING-INVENTORY-2026-05-24.md`.

## Repin scope

- `stack.lock.yaml`
  - `_stack.commit`: `6c47304a5be8a77d2e5ba0194ab9771bd293b3a9` -> `7e3be8533f4e179be81777a7d1c9cc95c1656702`

## Lock refresh note

The full canonical lockfile generator remains blocked in this session because `repos/fawxzzy-foundation` is absent from disk while `stack.yaml` still registers it. This package therefore performs the same narrow `_stack` repin pattern used in earlier governance repairs instead of a full stack-wide regeneration.

## Verification

- `_stack` Trove preflight passed locally.
- `_stack` operator surface validation passed locally.
- Root validation must pass after the lock repin.

## Explicit non-actions

- No deploy was run.
- No Vercel settings were mutated.
- No environment data was pulled.
- No downstream app/source code was changed.
