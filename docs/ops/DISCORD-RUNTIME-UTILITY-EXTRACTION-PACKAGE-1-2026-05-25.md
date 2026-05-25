# Discord Runtime Utility Extraction Package 1 - 2026-05-25

## Scope

- Repo: `repos/fawxzzy-fitness`
- Mode: bounded implementation inside Fitness only
- No code movement to `repos/DiscordOS`
- No Supabase mutation
- No Vercel mutation
- No Discord runtime restart

## Goal

Extract low-risk shared Discord runtime utilities from the decomposed Fitness-owned Discord interaction route so later DiscordOS extraction can target cleaner seams without changing current runtime ownership.

## Files Changed

- `repos/fawxzzy-fitness/src/lib/discord/runtime/helpers.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/helpers.test.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/domains/feedback.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/domains/spotify.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/domains/verification.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/domains/moderation.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/domains/operations.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/domains/updates.ts`
- `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`

## Utilities Extracted

Shared runtime helpers were centralized under `src/lib/discord/runtime/helpers.ts`:

- interaction command-name reader
- interaction custom-id reader
- application-command matcher
- message-component matcher
- message-component prefix matcher
- modal-submit matcher
- modal-submit prefix matcher
- JSON-body-to-`Response` normalizer
- first-hit domain-dispatch loop normalizer

## What Changed

- repeated low-level interaction-shape checks were removed from the runtime domain modules and replaced with shared helpers
- Spotify response normalization was moved into the shared runtime helper layer
- the route entrypoint still owns dispatcher ordering, but the first-hit dispatch loop is now normalized through one utility
- a new helper-focused runtime test was added so the extracted utility surface has direct coverage

## Behavior Preservation

Behavior was intentionally preserved by:

- keeping `src/app/api/discord/interactions/route.ts` as the stable public entrypoint
- keeping dispatcher order unchanged
- keeping all command names, custom IDs, modal IDs, and current handler ownership unchanged
- not changing any Discord-facing payload builder logic
- not introducing DiscordOS imports, env changes, database changes, or new contracts

## Verification

From `repos/fawxzzy-fitness`:

```text
npm run typecheck
npm run sanity:quick
npm run build
node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/runtime/helpers.test.ts
node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/runtime/route-domains.test.ts
node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts
```

Results:

- `npm run typecheck`: passed
- `npm run sanity:quick`: passed with preexisting lint warnings only
- `npm run build`: passed
- `helpers.test.ts`: passed
- `route-domains.test.ts`: passed
- `interactions-route.test.ts`: passed

From ATLAS root:

```text
python .\ops\validation\validate_stack.py --allow-missing-locked-repos
```

Result:

- root validation passed: `critical=0 error=0 warning=289`

## Why No DiscordOS Migration Happened

This package follows the approved extraction sequence:

1. decompose in the current owner
2. extract low-risk shared utilities in the current owner
3. verify current-owner behavior
4. move real runtime domains later only after the seams are cleaner

That means this package improves extractability without changing who owns the live Discord runtime today.

## Unrelated Repo State

The Fitness repo still contains unrelated preexisting tracked changes outside this package, including:

- `package.json`
- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/favicon-16x16.png`
- `public/favicon-32x32.png`
- `public/favicon.ico`
- `public/sw.js`
- `scripts/mobile_regression/__pycache__/__init__.cpython-313.pyc`
- `scripts/mobile_regression/__pycache__/board_builder.cpython-313.pyc`
- `src/generated/appBuildManifest.json`
- `src/lib/stretch-library-details.ts`
- `src/lib/stretch-library-summaries.ts`

Those changes remained separate from this utility extraction package.

## Next Extraction Candidate

The next clean implementation package remains:

- first low-risk domain-adjacent runtime utility cleanup inside Fitness if needed, or
- the first bounded real domain slice after utilities, with feedback still the most suitable candidate before broader Spotify or moderation extraction

This package does **not** justify code movement into `repos/DiscordOS` yet.
