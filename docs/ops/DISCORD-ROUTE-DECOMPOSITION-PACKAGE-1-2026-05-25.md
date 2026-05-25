# Discord Route Decomposition Package 1

Date: 2026-05-25
Lane: Discord OS Infrastructure Separation
Mode: bounded implementation inside Fitness only
Status: accepted into canonical Fitness truth

## Goal

Decompose the monolithic Fitness-owned Discord interaction route by domain without migrating code to `repos/DiscordOS`, changing runtime ownership, or mutating live Discord, Vercel, or Supabase surfaces.

## Accepted Fitness Commit

- repo: `repos/fawxzzy-fitness`
- branch: `main`
- commit: `fbd1f65d29fe857598ffd1579653cd20a0f1e188`
- subject: `refactor: decompose discord interaction route dispatch`

## Files Changed

- `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/types.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/domains/feedback.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/domains/spotify.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/domains/verification.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/domains/moderation.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/domains/operations.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/domains/updates.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/route-domains.test.ts`

## Domains Isolated

- feedback submit, manage, update, completion-review, and withdraw interaction dispatch
- Spotify Club, Jam Lobby, Jam Queue, and Spotify modal/button dispatch
- verification command, verify-button, and verify-modal dispatch
- moderation, warnings, and purgatory dispatch
- release, mod-log, and server-inventory operations dispatch
- update latest, publish, skip, and publish-modal dispatch
- shared Discord runtime interaction type reused through `src/lib/discord/runtime/types.ts`

## What Changed

- the public route entrypoint remains `src/app/api/discord/interactions/route.ts`
- the route still owns signature verification, payload parsing, `PING`, unsupported fallback, and unhandled-error wrapping
- domain routing moved into internal Fitness-owned runtime modules under `src/lib/discord/runtime/domains/`
- existing business logic handlers stayed in the current owner file so this package reduces coupling without starting extraction

## Behavior Preservation

Behavior was intentionally preserved by:

- keeping the route path and exported `POST` entrypoint stable
- continuing to call the same existing handler and response-builder functions
- not changing Discord command names, custom IDs, modal IDs, or response payload builders
- not introducing new tables, contracts, runtime dependencies, or DiscordOS imports

## Verification

Passed:

- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/runtime/route-domains.test.ts`

Blocked by local dependency gaps:

- `npm run sanity:quick`
  - failed because `next/dist/bin/next` is not present in the local repo dependency state
- `npm run typecheck`
  - failed because `typescript/bin/tsc` is not present in the local repo dependency state
- `npm run build`
  - failed during `build:prepare` because `sharp` is not present in the local repo dependency state
- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts`
  - failed because `tweetnacl` is not present in the local repo dependency state

## Why No DiscordOS Migration Happened

This package follows the approved sequencing rule:

- decompose in the current owner first
- verify domain seams before extraction
- do not copy a monolithic Fitness-hosted route into `repos/DiscordOS`

The package reduces hidden Fitness coupling without changing live ownership, data location, or runtime control.

## First Future Extraction Candidate

This package makes the next extraction order explicit:

1. low-risk shared Discord runtime utilities inside Fitness
2. feedback runtime as the first real DiscordOS domain slice

It does **not** make direct route-file copy into `repos/DiscordOS` acceptable.
