# Tmp Dependency Demotion Receipt

Date: 2026-05-23
Lane: Tmp Dependency Elimination
Status: retained-reference proof

## Goal

Prove that the active Fitness source verification path and `_stack` preflight path no longer require `tmp` checkouts, then classify the highlighted `tmp` surfaces as retained reference, historical evidence, or filesystem residue.

## Proof Summary

The canonical Fitness path is now sufficient for the proven operator loop.

Proven from the canonical path:

- `repos/fawxzzy-fitness` is present, clean, and canonical
- `npm run sanity:quick` passes from the canonical repo
- `npm run typecheck` passes from the canonical repo
- `npm run build` passes from the canonical repo
- `pnpm run fitness:deploy:preflight` passes from `_stack`

Result:

- no production-critical Fitness operation proven in this pass required `tmp`

## Canonical Repo Proof

Verified at `repos/fawxzzy-fitness`:

- branch: `main`
- remote: `https://github.com/fawxzzy/fawxzzy-fitness.git`
- HEAD: `7ceebde9d71564614df98e391b245a836d15c401`
- working tree before proof: clean
- working tree after proof cleanup: clean

Commands run:

- `npm run sanity:quick`
- `npm run typecheck`
- `npm run build`

Result:

- all passed

Observed warnings:

- the same non-blocking React hook lint warnings remain during sanity/build

Build hygiene:

- build-generated tracked residue was restored after the proof run
- canonical repo returned to an empty `git status`

## `_stack` Proof

Command run from `repos/_stack`:

- `pnpm run fitness:deploy:preflight`

Result:

- passed

What it proved:

- `_stack` resolves the canonical Fitness repo boundary correctly
- `_stack` sees the expected local `.vercel/project.json` at the canonical repo root
- `_stack` validates the expected immutable Vercel team/project identity
- Vercel Git auto-deploy state is still `disabled`

This is the active operator proof that `_stack` no longer needs the old `tmp` linked repo path for the current preflight lane.

## Tmp Surface Demotion Classification

### `tmp/fawxzzy-fitness-main-prod-source-3d00eac7`

Observed state:

- git repo on `main`
- HEAD: `7ceebde9d71564614df98e391b245a836d15c401`
- same remote as canonical repo
- same HEAD as canonical repo
- no longer needed for the proven canonical verify or `_stack` preflight path

Classification:

- retained reference only

Reason:

- still useful as a restoration-era fallback/reference surface
- no longer required for active canonical Fitness verification or `_stack` preflight

### `tmp/fitness-main-post-merge`

Observed state:

- detached snapshot at `710c7f20fbe9eeb631690754747e9c82d0202323`
- historical comparison surface
- not used by `_stack` proof or canonical repo verification

Classification:

- historical evidence only

Reason:

- useful for restoration archaeology
- not required for current source truth or operator execution

### `tmp/atlas-qa-release-refresh-pr`

Observed state:

- still exists on disk
- not listed in current `git worktree list`
- not a git root
- prior branch/worktree receipts already classify it as Windows deletion residue

Classification:

- stale filesystem residue only

Reason:

- no longer an active branch/worktree blocker
- no repo truth or operator dependency remains attached to it

## Active Tmp Dependency Verdict

What `tmp` is no longer needed for:

- canonical Fitness source truth
- canonical Fitness local install and verification
- canonical Fitness local Vercel link presence
- `_stack` Fitness deploy preflight

What `tmp` still does:

- preserve retained reference/fallback value
- preserve historical restoration evidence
- hold one unrelated Windows cleanup residue path

Current verdict:

- no production-critical Fitness workflow proven in this pass requires `tmp`
- the highlighted `tmp` surfaces can now be described as retained reference/evidence/residue rather than active execution surfaces

## What This Pass Did Not Do

- did not delete any `tmp` directory
- did not deploy Fitness
- did not mutate Vercel project settings
- did not mutate Supabase
- did not pull env
- did not commit `.vercel`
- did not edit Fitness product code

## Remaining Work Before Tmp Dependency Elimination Reaches 100%

1. document formal demotion language in any remaining canonical restoration summaries that still imply `tmp` is an active fallback
2. decide archive vs later removal timing for the retained Fitness `tmp` surfaces
3. clear the `tmp/atlas-qa-release-refresh-pr` filesystem residue in a later manual-safe cleanup pass
4. expand the duplicate-surface review across the broader historical Fitness-related `tmp` tree
5. verify that no undocumented manual deploy or QA lane still bypasses `_stack` and re-enters a `tmp` checkout

## Closeout Verdict

`tmp` is no longer part of the proven active Fitness verify/preflight path.

The remaining `tmp` work is governance closeout:

- retained reference demotion
- historical evidence retention/removal decisions
- later filesystem cleanup of known residue
