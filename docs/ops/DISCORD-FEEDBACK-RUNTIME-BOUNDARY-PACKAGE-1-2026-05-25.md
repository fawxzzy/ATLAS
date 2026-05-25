# Discord Feedback Runtime Boundary Package 1 - 2026-05-25

## Scope

- Repo: `repos/fawxzzy-fitness`
- Mode: bounded implementation inside Fitness only
- No code movement to `repos/DiscordOS`
- No Supabase mutation
- No Vercel mutation
- No Discord runtime restart

## Goal

Isolate the feedback-card lifecycle domain behind a clearer internal Fitness boundary so it can later become the first DiscordOS-owned domain slice without changing current runtime ownership.

## Files Changed

- `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/helpers.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/forum.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/helpers.test.ts`

## Feedback Boundary Isolated

This package extracted feedback-lifecycle logic into internal Fitness-owned runtime modules for:

- feedback status normalization
- feedback manage-card permission checks
- feedback lookup failure messaging
- feedback picker value resolution
- feedback content-change summaries
- feedback warning composition
- feedback forum starter-message sync
- feedback forum title/tag/state sync
- feedback resolved-reaction sync
- feedback audit comment posting

## What Changed

- `route.ts` remains the stable Discord interactions entrypoint, but it now delegates feedback-specific helper logic to `src/lib/discord/runtime/feedback/helpers.ts`
- Discord forum/starter-message/audit-comment side effects now pass through `src/lib/discord/runtime/feedback/forum.ts`
- the extracted feedback helpers are pure or dependency-injected where possible, so later extraction does not need to lift the whole route with them
- a focused `helpers.test.ts` now covers the new feedback-boundary helper surface directly

## Behavior Preservation

Behavior was intentionally preserved by:

- keeping the existing route path and public interaction contract unchanged
- leaving feedback persistence, Discord post/edit behavior, and current command/custom-id surfaces intact
- not changing database schema, env ownership, runtime ownership, or DiscordOS dependencies
- keeping all work inside the current Fitness owner before any future extraction

## Verification

From `repos/fawxzzy-fitness`:

```text
npm run typecheck
npm run sanity:quick
npm run build
node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/runtime/helpers.test.ts
node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/runtime/route-domains.test.ts
node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts
node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/runtime/feedback/helpers.test.ts
node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/bug-reports.test.ts
node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/feedback-emojis.test.ts
```

Results:

- `npm run typecheck`: passed
- `npm run sanity:quick`: passed with the same preexisting lint warnings only
- `npm run build`: passed
- `runtime/helpers.test.ts`: passed
- `runtime/route-domains.test.ts`: passed
- `interactions-route.test.ts`: passed
- `runtime/feedback/helpers.test.ts`: passed
- `bug-reports.test.ts`: passed
- `feedback-emojis.test.ts`: passed

## Why No DiscordOS Migration Happened

This package follows the approved extraction sequence:

1. decompose the current owner
2. extract shared low-risk utilities in the current owner
3. isolate the first real domain boundary in the current owner
4. verify the current owner stays stable
5. move domains later only after the seams are clean enough to prove

That means feedback is cleaner to extract later, but it is still explicitly Fitness-owned today.

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

Those changes remained separate from this feedback-boundary package.

## Next Extraction Candidate

The next clean implementation package is the first bounded real extraction candidate after feedback-boundary isolation, likely one of:

- a small follow-up feedback runtime utility cleanup if review shows a remaining mixed seam, or
- a later DiscordOS-facing feedback domain extraction package after current-owner boundaries and contracts are judged sufficient

This package does **not** justify broad DiscordOS migration, Supabase mutation, or runtime cutover by itself.
