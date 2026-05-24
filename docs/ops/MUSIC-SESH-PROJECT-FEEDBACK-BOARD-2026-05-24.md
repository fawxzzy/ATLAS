# Music Sesh Project Feedback Board

Date: 2026-05-24
Lane: Discord Workflow, Publication & Docs Reliability
Mode: Discord board split and card migration
Status: complete

## Goal

Keep `feedback` as the general intake forum, but split clustered project cards into a dedicated project board once a project has enough active history.

This pass applied that rule to the existing Spotify Club card cluster and renamed the project-facing card scope to `Music Sesh`.

## Discord Board Changes

Confirmed category:

- `Project Feedback Boards`
- category id: `1508057063874629684`

Source intake forum:

- `feedback`
- forum id: `1504673475489562744`

New project board:

- `music-sesh`
- forum id: `1508139160853286942`

The new `music-sesh` forum was created under `Project Feedback Boards` with:

- the same permission-overwrite count as `feedback`
- the same forum tag set as `feedback`
- the same forum layout and baseline posting behavior as `feedback`

General intake remains in `feedback`.

## Card Migration

The current Spotify Club card cluster was moved to the new board and renamed to `Music Sesh`.

Bounded row changes:

- area renamed from `Fawx Den / Spotify Club` to `Fawx Den / Music Sesh`
- summary titles renamed from `Spotify Club ...` to `Music Sesh ...`
- forum pointers updated from the general `feedback` board to the new `music-sesh` board

Moved cards:

- `f31e1150` -> `Music Sesh Phase 1 - Connect + Premium Check`
- `1e185453` -> `Music Sesh Phase 2 - Public Jam Panel + Lobby State`
- `b3483cf2` -> `Music Sesh Phase 3 - Queue Suggestions + Host Approval`
- `b58590af` -> `Music Sesh Phase 4 - Playback Readiness + Device Handoff`
- `0ea4e2be` -> `Music Sesh Phase 5 - Rooms + Search + Cleaner Panel UX`
- `c3450339` -> `Music Sesh Phase 6 - Live Queue + Smart Search`
- `7acc4522` -> `Music Sesh Phase 7 - Playback Continuity + Queue Hygiene`
- `4b2d72f8` -> `Music Sesh Phase 7 Stabilization - Queue Authority + Hub Hygiene`

## Old Thread Handling

For each migrated card:

- a new canonical starter thread was created in `music-sesh`
- the old `feedback` thread received a pointer comment to the new Music Sesh thread
- the old thread was archived and locked to avoid duplicate live card truth

Fixed Music Sesh cards also received the configured success reaction on the new starter post so the resolved-state visual signal stayed consistent.

## Boundaries Preserved

- no repo code changed for this operation
- no deploy ran
- no Vercel or Supabase schema state changed
- `feedback` remains the general intake board
- the project split changed Discord board topology and bounded row pointers only

## Operational Rule Confirmed

The current working rule is now:

1. feedback starts in the general `feedback` board
2. once a project accumulates a real cluster of cards, create a project board under `Project Feedback Boards`
3. copy the forum shape from `feedback`
4. move the clustered cards into the project board
5. keep the general board as intake rather than long-term project storage
