# Fitness Music Sesh Setup Repost Fix

Date: 2026-05-24
Lane: Discord OS / Music Sesh operator surface
Status: complete

## Problem
`computa setup music sesh` refreshed the existing Music Sesh panel in place instead of deleting and reposting it.

That drifted from the setup behavior already used for the feedback launcher and other canonical command surfaces, where rerunning setup should move the fresh canonical panel to the bottom of the channel.

## Root Cause
The Music Sesh setup path reused the general panel upsert function, and that function preferred:
- patch existing panel when present
- recreate only when the message was missing or Discord refused an aged edit

Setup commands never opted into a force-repost path.

## Fix
- added a `forceRepost` option to the Music Sesh panel upsert flow
- wired slash `setup-music-sesh` to force delete/repost when a panel already exists
- wired main-channel `computa setup music sesh` to the same force delete/repost behavior
- kept normal room-state refreshes on patch-in-place behavior so routine queue/lobby updates do not spam the channel

## Verification
- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts`
- `npm run verify`
- `_stack` governed production deploy:
  - deployment id: `dpl_9NnZbXGLKngAzXnuHeuRufSAeZUa`
  - production alias: `https://fawxzzy-fitness-local.vercel.app`

## Result
Rerunning either setup surface now behaves like the other canonical setup commands:
- old Music Sesh panel is deleted
- fresh panel is posted
- command response still reports the panel as updated when it was a repost

## Rules Reinforced
- setup commands should repost canonical launcher surfaces
- live state sync may patch in place, but explicit setup should refresh by reposting
- command-surface behavior should stay consistent across feedback, Music Sesh, and other canonical bot setup lanes
