# Fitness Discord Goodnight Alias Expansion

Date: 2026-05-24
Lane: Discord Workflow, Publication & Docs Reliability
Mode: narrow repo-local Discord trigger refinement
Status: complete

## Goal

Expand the exact-match `goodnight` trigger family so the bot can respond to a few more natural night aliases without widening into fuzzy chat interception.

## What Changed

In `repos/fawxzzy-fitness`:

- `src/app/api/discord/interactions/route.ts`
  - expanded the exact-match goodnight trigger set
- `scripts/discord-feedback-gateway-worker.mjs`
  - expanded worker wakeup detection for the new goodnight aliases
- `scripts/discord-feedback-gateway-worker.test.mjs`
  - added coverage for the new aliases
- `docs/ops/FITNESS-DISCORD-FEEDBACK.md`
  - documented the expanded night alias set

## Added Aliases

The night trigger set now includes:

- `good night`
- `goodnight`
- `good night computa`
- `goodnight computa`
- `night`
- `night computa`
- `nite`
- `nite computa`
- `gn`
- `gn computa`

Morning aliases and the scheduled `10:00 PM` goodnight post remain unchanged by structure; this pass only broadens the accepted exact-message night variants.

## Boundaries Preserved

- no deploy ran
- no Discord configuration changed
- no Vercel or Supabase state changed
- no publish or release authority changed
- triggers remain main-channel-only and exact-match only

## Verification

From `repos/fawxzzy-fitness`:

- `node --test scripts/discord-feedback-gateway-worker.test.mjs`
- `npm run verify`

Verification outcome:

- targeted worker tests passed
- repo verify passed

## Fitness Commit

- `fc5c86a95fb4ba7e1c5da919ed0e56fbb81b5d50`
- `feat: expand discord goodnight aliases`
