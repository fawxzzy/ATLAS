# Canonical Repo Stack Path Proof

Date: 2026-05-23
Lane: Canonical Repo Restoration + Tmp Dependency Elimination
Status: stack/operator path proof

## Goal

Prove that `_stack` and the active Fitness operator workflow resolve against `repos/fawxzzy-fitness` as the canonical Fitness repo root rather than depending on `tmp` checkouts for current source and operator execution.

## Proof Summary

The `_stack` Fitness operator path now resolves cleanly against `repos/fawxzzy-fitness`.

What passed:

- stack topology still points Fitness to `repos/fawxzzy-fitness`
- `_stack` package scripts point Fitness verify/deploy commands to `../fawxzzy-fitness`
- `_stack` deploy preflight passed against the restored canonical repo root
- repo-local Fitness sanity, typecheck, and build all passed again from `repos/fawxzzy-fitness`
- canonical repo was cleaned back to an empty `git status` after build residue cleanup

What remains:

- `tmp` still exists as retained fallback/reference material
- `tmp` still appears in restoration and recovery receipts
- no active `_stack` operator proof in this pass required `tmp` to execute

## Canonical Stack References

### Root topology

Confirmed stack-level canonical references:

- `stack.yaml`
  - `fitness.path: repos/fawxzzy-fitness`
- `README-STACK.md`
  - `fitness -> repos/fawxzzy-fitness`
  - Fitness normalized on disk at `repos/fawxzzy-fitness`

### `_stack` operator surfaces

Confirmed `_stack` references use the canonical path:

- `repos/_stack/package.json`
  - `fitness:verify -> pnpm --dir ../fawxzzy-fitness verify:strict`
  - `fitness:verify:clean -> pnpm --dir ../fawxzzy-fitness clean:next && pnpm --dir ../fawxzzy-fitness verify:strict`
  - `fitness:build:vercel -> ... --cwd ../fawxzzy-fitness build --yes`
  - `fitness:deploy:* -> ... --cwd ../fawxzzy-fitness ...`
- `repos/_stack/docs/fitness-verify.md`
- `repos/_stack/docs/runbooks/FITNESS-QA-LOCAL-LOOP.md`
- `repos/_stack/docs/dispatcher-protocol.md`
- `repos/_stack/queue/README.md`
- `repos/_stack/templates/child-task-handoff.md`

Verdict:

- intended operator path references are correctly pointed at the restored canonical repo root
- `_stack` did not need to be repointed away from `tmp`

## Remaining Tmp References

### Active operator surfaces

No active `_stack` package-script or runbook path proof in this pass required:

- `tmp/fawxzzy-fitness-main-prod-source-3d00eac7`
- `tmp/fitness-main-post-merge`

### Retained documentary references

`tmp/fawxzzy-fitness-main-prod-source-3d00eac7` still appears in:

- `docs/ops/CANONICAL-REPO-RESTORATION-INVENTORY-2026-05-23.md`
- `docs/ops/CANONICAL-REPO-RESTORATION-RECEIPT-2026-05-23.md`
- `docs/ops/CANONICAL-REPO-RESTORATION-READINESS-2026-05-23.md`
- `docs/ops/CANONICAL-REPO-VERCEL-LINK-READINESS-2026-05-23.md`

`tmp/fitness-main-post-merge` still appears in:

- `docs/ops/CANONICAL-REPO-RESTORATION-INVENTORY-2026-05-23.md`
- `docs/ops/CANONICAL-REPO-RESTORATION-RECEIPT-2026-05-23.md`

Interpretation:

- these are retained restoration receipts
- they are not active proof that `_stack` still depends on `tmp` for current operator execution

## `_stack` Preflight Proof

Command run from `_stack`:

- `pnpm run fitness:deploy:preflight`

Result:

- passed

Observed confirmation:

- repo boundary accepted as a real standalone git toplevel
- local `.vercel/project.json` accepted at the canonical repo root
- expected team id matched `team_CMJn7MvzFZZBnhNnjVUZF2RD`
- expected project id matched `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- expected scope/project matched `fawxzzy/fawxzzy-fitness`
- Vercel Git auto-deploy state remained `disabled`

This is the key operator proof that `_stack` can see and validate the restored canonical repo without needing the prior `tmp` linked checkout.

## Canonical Fitness Repo Proof

Commands rerun from `repos/fawxzzy-fitness`:

- `npm run sanity:quick`
- `npm run typecheck`
- `npm run build`

Result:

- all passed

Observed warnings:

- the same non-blocking React hook lint warnings remained during sanity/build

Post-build hygiene:

- build-generated tracked residue was restored
- canonical repo returned to a clean working tree

## Tmp Dependency Verdict

What `tmp` is no longer needed for:

- canonical source-of-truth Git lineage
- local install and verification
- local Vercel link presence
- `_stack` Fitness deploy preflight path resolution

What `tmp` may still represent for now:

- retained fallback/reference checkout
- historical recovery evidence
- legacy operator receipts that have not yet been rewritten around the canonical path

Current operational verdict:

- no production-critical Fitness operation proven in this pass required `tmp`
- `tmp` has not yet been formally demoted to retained reference only, but its role is now documentary/fallback rather than active canonical execution

## Remaining Work Before 100%

1. classify the live `tmp` production-linked checkout as retained fallback or removable later surface
2. verify any remaining manual deploy or QA runbooks do not quietly bypass `_stack` and re-enter `tmp`
3. begin Manual Deploy Exception Burn-Down so Fitness deploys no longer depend on ad hoc operator memory

## Closeout Verdict

`_stack` and current Fitness operator proofs now work against `repos/fawxzzy-fitness`.

Canonical repo restoration is no longer blocked on path resolution. The remaining work is cleanup/governance:

- formal `tmp` demotion
- manual deploy exception burn-down
- broader convergence of operator documentation and retained receipts
