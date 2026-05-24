# Fitness Discord Greeting Triggers

Date: 2026-05-24
Lane: Discord Workflow, Publication & Docs Reliability
Mode: narrow repo-local Discord workflow extension
Status: complete

## Goal

Add a small, explicit set of Discord greeting triggers plus a nightly scheduled post without widening deploy authority, bot admin scope, or broader chat-command behavior.

## What Changed

In `repos/fawxzzy-fitness`:

- `src/app/api/discord/interactions/route.ts`
  - added exact-match main-channel greeting aliases for a morning response
  - added exact-match main-channel greeting aliases for a goodnight response
  - added narrow handlers that post the configured greeting message back into the main channel
  - kept allowed mentions empty so these greetings do not ping roles or `@everyone`
- `scripts/discord-feedback-gateway-worker.mjs`
  - taught the Gateway worker to wake the secured poll route for the new greeting aliases
  - added a scheduled `goodnight` rule with a default `10:00 PM` Eastern window
  - preserved the existing scheduled `Grand Rising` rule at `10:00 AM` Eastern
  - added `DISCORD_GRAND_RISING_CONTENT` and `DISCORD_GOODNIGHT_CONTENT` override support
- `scripts/discord-feedback-gateway-worker.test.mjs`
  - added trigger coverage for the new morning and goodnight aliases
  - added scheduled-window coverage for the `10:00 PM` goodnight rule
- `docs/ops/FITNESS-DISCORD-FEEDBACK.md`
  - documented the greeting aliases, no-mention behavior, and scheduled greeting defaults

## Trigger Shape

Morning aliases:

- `good morning`
- `goodmorning`
- `morning`
- `grand rising`
- `grandrising`
- `good morning computa`
- `goodmorning computa`
- `morning computa`
- `grand rising computa`
- `grandrising computa`

Night aliases:

- `good night`
- `goodnight`
- `good night computa`
- `goodnight computa`

These are exact-message aliases in `DISCORD_MAIN_CHANNEL_ID`, not broad fuzzy phrase interception.

## Default Bot Messages

- morning: `<:GM:1507443437916524675> Grand Rising`
- night: `<:goodnight:1507597897343041700> Goodnight`

Both can be overridden with:

- `DISCORD_GRAND_RISING_CONTENT`
- `DISCORD_GOODNIGHT_CONTENT`

## Scheduled Defaults

- `Grand Rising`: `10:00 AM` Eastern
- `Goodnight`: `10:00 PM` Eastern

Both remain configurable through the `DISCORD_GRAND_RISING_*` and `DISCORD_GOODNIGHT_*` env surfaces.

## Boundaries Preserved

- no deploy ran
- no Discord configuration changed
- no Vercel or Supabase state changed
- no release/update publication authority changed
- no `tmp` fallback was introduced

## Verification

From `repos/fawxzzy-fitness`:

- `node --test scripts/discord-feedback-gateway-worker.test.mjs`
- `npm run verify`

Verification outcome:

- targeted worker tests passed
- repo verify passed

## Fitness Commit

- `f76357846dded35cb9858d8bc2033280cd804dd0`
- `feat: add discord greeting triggers`
