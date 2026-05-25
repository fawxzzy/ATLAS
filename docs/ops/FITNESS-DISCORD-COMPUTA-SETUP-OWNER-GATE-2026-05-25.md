# Fitness Discord Computa Setup Owner Gate

Date: 2026-05-25
Owner: Codex
Scope: Fitness Discord command-surface permission tightening and live command-card refresh

## Objective

Remove `computa setup feedback` and `computa setup music sesh` from the `Fawxzzy Commander` role path and from the public `Computa` command card, while keeping both setup commands available to the configured owner account.

## Requested behavior

- `Fawxzzy Commander` should no longer be able to run:
  - `computa setup feedback`
  - `computa setup music sesh`
- the public `Computa` card should no longer display those setup commands
- setup commands should remain owner-only

## Implementation

Fitness repo:

- commit: `3f48f9c26135cbce46c487e64e0ce1ccbad3f793`
- message: `fix: restrict computa setup commands to owner`

Files changed:

- `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`
- `repos/fawxzzy-fitness/src/lib/discord/interactions-route.test.ts`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`

Behavior changes:

- the public `Computa` card now shows only:
  - `computa`
- the `Computa Owner` card still lists the owner-only setup commands
- `computa setup feedback` now rejects non-owner users even if they hold `Fawxzzy Commander`
- `computa setup music sesh` now rejects non-owner users even if they hold `Fawxzzy Commander`
- no commander-role bootstrap path remains for these setup commands

## Verification

Executed in `repos/fawxzzy-fitness`:

- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts`
- `npm run typecheck`
- `npm run sanity:quick`
- `npm run build`

Result:

- route tests: passed
- typecheck: passed
- sanity: passed with the same preexisting lint warnings
- build: passed with the same preexisting lint warnings

## Production rollout

Clean deploy worktree:

- `tmp/fitness-prod-rollout-3f48f9c2`

Production deployment:

- URL: `https://fawxzzy-fitness-yeuymvvlk-fawxzzy.vercel.app`
- status: `Ready`
- target commit: `3f48f9c26135cbce46c487e64e0ce1ccbad3f793`

## Live Discord refresh

Because the public `Computa` card is a persisted bot post, it was refreshed directly after deployment so the visible surface matched the new rule immediately.

Main channel:

- `DISCORD_MAIN_CHANNEL_ID`: `1504674484068552784`

Action taken:

- deleted old public `Computa` card: `1508495867521274008`
- posted replacement public `Computa` card: `1508507946517008494`

Replacement public card now lists only:

- `computa` - Show this command card.

## Outcome

Resolved:

- setup commands no longer ride through the commander-role path
- the public `Computa` card no longer advertises owner-only setup commands
- live Discord command-card state now matches the deployed behavior

Unchanged:

- `Fawxzzy Commander` still governs non-owner computa operator commands such as release checks and feedback maintenance
- no Supabase mutation
- no DiscordOS runtime migration
- no bot restart
- no archive retention change

## State notes

- unrelated preexisting tracked Fitness residue remained separate in the main Fitness worktree
- `archive/` remained untouched at the ATLAS root
