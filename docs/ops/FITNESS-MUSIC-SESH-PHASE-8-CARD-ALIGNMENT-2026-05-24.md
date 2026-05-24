# Fitness Music Sesh Phase 8 Card Alignment

Date: 2026-05-24
Owner: ATLAS root coordination
Scope: `repos/fawxzzy-fitness` live feedback-card rendering + Music Sesh board row `32a96b1b`

## Why this pass happened

The Music Sesh board split moved the existing Spotify Club cluster into the dedicated `music-sesh` forum, but Phase 8 only existed in continuity planning and had not been created as a live project card.

This pass closed that gap and corrected one shared feature-card rendering drift:

- the missing Phase 8 Music Sesh card now exists on the `music-sesh` project board
- the Phase 8 card now reflects the approved main room-system scope
- the shared feature-card formatter no longer lowercases the first character of feature summaries inside the `User Story` line, which had been degrading proper names like `Music Sesh`

## Live card truth

- Report ID: `32a96b1b`
- Forum channel: `music-sesh` (`1508139160853286942`)
- Starter thread/message: `1508141153835421798`
- Title: `Music Sesh Phase 8 - Multi-Room Sessions + Private Room Keys`
- Status: `Confirmed`
- Points: `13`

## Final scoped card behavior

The live card now states:

- Music Sesh Phase 8 is a multi-room system, not a single-lobby extension
- the default public room remains
- hosts or staff can open additional named rooms
- rooms may be public or key-gated
- the public panel stays compact
- the control hub stays room-aware
- room membership stays separate from Spotify auth
- playback remains Spotify-native on each user's own device
- Discord owns room membership, queue intent, and room visibility only

## Renderer correction

Shared renderer change in `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`:

- feature `User Story` lines now preserve the original summary casing instead of forcing the first character to lowercase

That keeps project names and branded terms intact on current and future feature cards.

## Verification

- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/bug-reports.test.ts`
- `npm run verify`
- live Supabase row `32a96b1b` readback
- live Discord starter post readback for message `1508141153835421798`

## Non-goals

- no deploy
- no Discord bot command changes
- no Music Sesh runtime implementation work
- no board-permission changes beyond the already-completed project board split
