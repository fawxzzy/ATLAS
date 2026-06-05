## Fitness Canonical Path Restoration Repair

Date: 2026-05-24
Lane: Canonical Repo Restoration
Mode: canonical path repair only
Status: repaired

## Goal

Restore `repos/fawxzzy-fitness` as the canonical Fitness child repo after the active ATLAS root was found to be missing that path, then repair stack-facing metadata from the restored canonical repo state.

## Starting State

Confirmed before repair:

- `repos/fawxzzy-fitness`
  - missing
- `tmp/fawxzzy-fitness-main-prod-source-3d00eac7`
  - present
  - branch `main`
  - remote `https://github.com/fawxzzy/fawxzzy-fitness.git`
  - HEAD `7ceebde9d71564614df98e391b245a836d15c401`
- `stack.yaml`
  - still registered `repos/fawxzzy-fitness` as canonical
- `stack.lock.yaml`
  - did not carry a live canonical Fitness entry

## Repair Action

Canonical repo was recreated from GitHub, not by promoting `tmp`:

```powershell
git clone https://github.com/fawxzzy/fawxzzy-fitness.git repos/fawxzzy-fitness
```

## Canonical Identity After Repair

Verified from `repos/fawxzzy-fitness`:

- remote:
  - `https://github.com/fawxzzy/fawxzzy-fitness.git`
- branch:
  - `main`
- HEAD:
  - `7ceebde9d71564614df98e391b245a836d15c401`
- working tree after cleanup:
  - clean

Lineage comparison against retained reference:

- canonical repo HEAD matches retained `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` HEAD exactly

## Local Operator Linkage

Local Vercel link was restored without committing machine-local linkage:

- `.vercel/project.json`
  - present locally
  - project `fawxzzy-fitness`
  - project id `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- `.vercel`
  - remains local-only and unstaged

Supabase identity remains:

- `lpswxoyfniocuhljgzbc`

## Repo-Local Verification

Ran from `repos/fawxzzy-fitness`:

```powershell
npm ci
npm run sanity:quick
npm run typecheck
npm run build
```

Result:

- all passed

Observed warnings:

- existing non-blocking React hook lint warnings remain during `sanity:quick` and `build`

Build hygiene:

- tracked build-generated residue was restored after verification
- canonical repo returned to an empty `git status`

## `_stack` Check

Ran from `repos/_stack`:

```powershell
pnpm run fitness:deploy:preflight
```

Result:

- passed

What it proved:

- `_stack` again resolves the canonical `repos/fawxzzy-fitness` path
- local Vercel linkage at the canonical repo root is visible again to the operator path

## Stack Metadata Repair

`stack.lock.yaml` was repaired with a live canonical Fitness entry:

- path:
  - `repos/fawxzzy-fitness`
- ref:
  - `main`
- commit:
  - `7ceebde9d71564614df98e391b245a836d15c401`
- dirty:
  - `false`

This is a narrow metadata repair, not a full lockfile regeneration.

Reason:

- the active root still does not contain `repos/fawxzzy-foundation`, so full stack lock regeneration remains a separate lane

## Tmp Status

`tmp` was not promoted during this repair.

`tmp/fawxzzy-fitness-main-prod-source-3d00eac7` remains:

- retained reference only
- not canonical source truth
- not a brand sync target

## Validation

Ran from the ATLAS root (`.`):

```powershell
python .\ops\validation\validate_stack.py --allow-missing-locked-repos
```

Result:

- `critical=0 error=0`

## What Did Not Happen

- no brand assets were synced
- no deploy was performed
- no Vercel settings were mutated
- no Supabase mutation was performed
- no Fitness product code was edited
- no `tmp` path was treated as canonical

## Repair Verdict

The canonical Fitness child repo path is restored again under `repos/`, verified locally, Vercel-linked locally, visible to `_stack` again, and represented in stack-facing metadata again.

This closes the immediate canonical path regression and reopens the path for a future Fitness brand visibility recheck from the active root.
