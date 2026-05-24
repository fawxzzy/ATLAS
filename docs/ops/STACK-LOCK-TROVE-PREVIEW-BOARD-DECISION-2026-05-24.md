# Stack Lock Trove Preview Board Decision

Date: 2026-05-24
Lane: Trove product package lock governance
Mode: Narrow lock repair
Status: Accepted for lock truth

## Decision

Accept Trove commit `9a0f575` (`feat: package trove preview board updates`) as current stack truth and refresh the Trove pin in `stack.lock.yaml`.

## Why

- The commit is not random local dirt.
- It is the isolated Trove product/source package that followed the ATLAS split decision and package plan.
- Repo-local verification passed from `repos/fawxzzy-trove`:
  - `npm run verify`
- The commit scope is limited to:
  - `src/app/layout.tsx`
  - `src/components/catalog/app-section.tsx`
- Public Trove brand consumer assets remained intentionally untouched.
- Vendored Fitness icons remained intentionally untouched.
- Docs and QA surfaces remained intentionally untouched.

## Lock drift observed

Root validation failed only because:

- `stack.lock.yaml#trove` still pinned `bce14fcc1ad6e826b0c0eac37e13af6707ee3a8e`
- current Trove HEAD is `9a0f575c5e03723bd04c9b77fda42df128c1bc04`

## Accepted repair shape

- Update only the `trove` component pin inside `stack.lock.yaml`
- Recompute the lockfile digest from the normalized payload
- Revalidate with:
  - `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`

## What this decision does not do

- does not accept Trove brand sync
- does not accept vendored Fitness icon drift
- does not accept Trove docs or QA residue
- does not modify `branding/**`
- does not reopen Fitness canonical-source questions

## Follow-up

After this repin, the Trove brand lane remains blocked until the remaining Trove-local buckets are isolated and a narrow public-brand consumer package can be reviewed on its own.
