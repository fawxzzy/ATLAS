# Stack Lock Decision - Fitness Discord Route Decomposition

Date: 2026-05-25
Lane: Discord OS Infrastructure Separation
Mode: stack-lock decision
Status: accepted into root truth

## Decision

Accept the canonical Fitness repo commit for Discord route decomposition into ATLAS stack truth **without** changing `stack.lock.yaml`.

Accepted Fitness commit:

- `fbd1f65d29fe857598ffd1579653cd20a0f1e188`
- `refactor: decompose discord interaction route dispatch`

## Why No Stack-Lock Repin Happened

`stack.lock.yaml` remains unchanged because the current root lock intentionally tracks only the repo ids listed under `stack.yaml#stack_lock.include_repo_ids`.

`fitness` is still outside that explicit inclusion set, so this package records the canonical Fitness HEAD movement through:

- the Fitness repo commit itself
- `docs/ops/DISCORD-ROUTE-DECOMPOSITION-PACKAGE-1-2026-05-25.md`
- root validation

This decision preserves the current lock policy instead of silently widening lock membership during a bounded Discord route package.

## Scope

This decision accepts only:

- the canonical Fitness HEAD movement for route decomposition
- the no-repin stack-lock posture tied to the current explicit include list

It does not:

- add `fitness` to `stack.lock.yaml`
- regenerate lock membership broadly
- mutate DiscordOS, Supabase, or Vercel surfaces
- change deploy authority or runtime ownership

## Verification

Root validation command:

- `python .\\ops\\validation\\validate_stack.py --allow-missing-locked-repos`
