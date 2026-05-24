# Stack Lock Trove Docs QA Decision

Date: 2026-05-24
Lane: Trove docs and QA package lock governance
Mode: Narrow lock repair
Status: Accepted for lock truth

## Decision

Accept Trove commit `865d62e4cef9d17141971ffc3baef86fecf9ac90` (`docs: package trove qa surfaces`) as current stack truth and refresh the Trove pin in `stack.lock.yaml`.

## Why

- The commit is not unrelated local churn.
- It is the isolated Trove docs and QA package that followed the ATLAS split plan.
- Repo-local verification passed from `repos/fawxzzy-trove` before the package commit:
  - `npm run verify`
- The package scope was limited to:
  - `docs/qa.md`
  - `qa/adapters/trove.web.json`
  - `qa/scenarios/trove.home-smoke.json`
- Trove public brand assets remained intentionally untouched.
- Vendored Fitness icons remained intentionally untouched.

## Lock drift observed

Root validation failed only because:

- `stack.lock.yaml#trove` still pinned `9a0f575c5e03723bd04c9b77fda42df128c1bc04`
- current Trove HEAD is `865d62e4cef9d17141971ffc3baef86fecf9ac90`

## Accepted repair shape

- Update only the `trove` component pin inside `stack.lock.yaml`
- Recompute the lockfile digest from the normalized payload
- Revalidate with:
  - `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`

## What this decision does not do

- does not accept Trove brand sync
- does not accept vendored Fitness icon drift
- does not modify `branding/**`
- does not touch Fitness brand consumers

## Follow-up

After this repin, the remaining Trove-local buckets should be:

1. vendored Fitness icon package
2. Trove public brand sync package
