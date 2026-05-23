# Canonical Repo Restoration Receipt

Date: 2026-05-23
Lane: Canonical Repo Restoration + Tmp Dependency Elimination
Status: restoration checkpoint

## Goal

Recreate `repos/fawxzzy-fitness` as the canonical Fitness repo root from the correct GitHub remote, verify that it matches the live production-linked Fitness lineage, and record any remaining local operator gaps before source-of-truth work leaves `tmp/`.

## Restore Result

`repos/fawxzzy-fitness` now exists again as a clean Git checkout.

Restored path:

- `repos/fawxzzy-fitness`

Restore source:

- `https://github.com/fawxzzy/fawxzzy-fitness.git`

Restore mode:

- fresh clone from GitHub `main`
- no source code edits applied during restoration
- no deploy performed
- no Vercel or Supabase mutation performed
- no `tmp` checkout deleted

## Canonical Repo Checks

| Check | Result |
| --- | --- |
| `repos/fawxzzy-fitness` exists | yes |
| current branch | `main` |
| remote | `https://github.com/fawxzzy/fawxzzy-fitness.git` |
| local working tree dirty | no |
| restored HEAD | `7ceebde9d71564614df98e391b245a836d15c401` |

## Comparison With Live Tmp Checkout

Current live production-linked checkout:

- `tmp/fawxzzy-fitness-main-prod-source-3d00eac7`

Comparison result:

| Surface | Branch | HEAD | Verdict |
| --- | --- | --- | --- |
| `repos/fawxzzy-fitness` | `main` | `7ceebde9d71564614df98e391b245a836d15c401` | restored canonical repo |
| `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` | `main` | `7ceebde9d71564614df98e391b245a836d15c401` | live production-linked checkout |

Verdict:

- both surfaces are on the same `main` lineage
- the restored canonical repo is not behind the live production-linked checkout
- the `tmp` production-linked checkout did not need to become canonical truth to restore the owner repo root

## Canonical Identity Checks

### GitHub

- remote: `https://github.com/fawxzzy/fawxzzy-fitness.git`
- result: confirmed

### Vercel

Canonical Vercel identity remains:

- project: `fawxzzy-fitness`
- project id: `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`

Evidence:

- `repos/_stack/config/fitness-deploy.identity.json`
- `tmp/fawxzzy-fitness-main-prod-source-3d00eac7/.vercel/project.json`

Important local gap:

- the fresh clone at `repos/fawxzzy-fitness` does not yet have a local `.vercel/project.json`
- this is local linkage drift, not project identity drift

### Supabase

Canonical production-aligned Supabase identity remains:

- project ref: `lpswxoyfniocuhljgzbc`
- host: `lpswxoyfniocuhljgzbc.supabase.co`

Evidence:

- `tmp/fawxzzy-fitness-main-prod-source-3d00eac7/.env.prod-local-mirror.example`
- `tmp/fawxzzy-fitness-main-prod-source-3d00eac7/README.md`
- `tmp/fawxzzy-fitness-main-prod-source-3d00eac7/scripts/env-file.mjs`

## Repo-Local Verification Attempt

Attempted from:

- `repos/fawxzzy-fitness`

Command:

- `npm run sanity:quick`

Result:

- failed immediately because local dependencies are not installed
- current failure:
  - missing module `next/dist/bin/next`

Interpretation:

- the restored repo is structurally correct as a Git checkout
- repo-local verification is not yet runnable from the restored path until local install/linkage prerequisites are restored
- this is an operator readiness gap, not a source-lineage mismatch

## Remaining Gaps Before Tmp Dependency Elimination

1. restore local dependency install state for `repos/fawxzzy-fitness`
2. restore local Vercel link material for `repos/fawxzzy-fitness` without mutating the live Vercel project
3. confirm any repo-local env and secret lane expectations needed by `_stack` verify/deploy flows
4. re-run repo-local verification from `repos/fawxzzy-fitness`
5. only after the restored canonical repo is operator-ready should the production-linked `tmp` checkout stop being a live dependency

## Non-Goals Completed Intentionally

- did not move the `tmp` checkout into `repos/`
- did not delete `tmp/fawxzzy-fitness-main-prod-source-3d00eac7`
- did not delete `tmp/fitness-main-post-merge`
- did not edit Fitness product code
- did not deploy Fitness
- did not mutate Supabase
- did not mutate Vercel

## Closeout Verdict

Canonical repo restoration is now partially complete:

- the canonical repo root under `repos/` has been restored
- canonical GitHub lineage is confirmed
- canonical Vercel and Supabase identities are confirmed
- the remaining blockers are local operator readiness blockers, not source-of-truth blockers

That moves the lane from “missing canonical repo root” to “restored repo root still needs local operator linkage and install readiness before `tmp` can be eliminated.”
