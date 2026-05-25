# Stack Lock Decision - Fitness Discord Verification Restore

Date: 2026-05-25
Lane: Discord OS Infrastructure Separation
Mode: stack-lock decision
Status: accepted into root truth

## Decision

Accept the canonical Fitness repo verification-restore commit into ATLAS stack truth **without** changing `stack.lock.yaml`.

Accepted Fitness commit:

- `e14ccc1f73d2ded033e0f214c9071082a7d1d94c`
- `fix: restore discord route import coverage`

## Why

This was a narrow follow-up fix discovered during verification restore after the Discord route decomposition package:

- it restores still-needed imports inside the current Fitness-owned Discord route
- it does not move code to `repos/DiscordOS`
- it does not mutate Supabase, Vercel, Discord runtime ownership, or deploy state
- it returns the existing full Discord route test suite to green once install state is restored

## Why No Stack-Lock Repin Happened

`stack.lock.yaml` remains unchanged because `fitness` is still outside the explicit `stack.yaml#stack_lock.include_repo_ids` member set.

This package therefore records root truth through:

- the canonical Fitness repo commit
- `docs/ops/FITNESS-DISCORD-DECOMPOSITION-VERIFICATION-RESTORE-2026-05-25.md`
- root validation

It does not widen stack-lock membership during a bounded verification-restore lane.

## Scope

This decision accepts only:

- the canonical Fitness HEAD movement for the verification-restore import fix
- the no-repin posture tied to the current explicit lock include list

It does not:

- add `fitness` to `stack.lock.yaml`
- reopen DiscordOS code migration
- treat the remaining `src/lib/discord/interactions.test.ts` type errors as resolved

## Verification

Root validation command:

- `python .\\ops\\validation\\validate_stack.py --allow-missing-locked-repos`
