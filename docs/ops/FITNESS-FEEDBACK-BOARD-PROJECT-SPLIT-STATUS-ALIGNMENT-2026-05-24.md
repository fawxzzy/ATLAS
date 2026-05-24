# Fitness Feedback Board Project Split And Status Alignment

Date: 2026-05-24
Owner: ATLAS root coordination
Scope: live Discord feedback boards, bounded feedback rows, and shared Fitness feedback-card display rules

## Why this pass happened

Three feedback-board issues were open at once:

1. the two Music Sesh Phase 7 cards were still `confirmed`, so they had no resolved reaction
2. feature cards still displayed `Completed` while bug cards displayed `Fixed`, which made cross-board done-state language feel inconsistent
3. the general `feedback` intake board still held the two current Fitness app feature cards instead of a dedicated project board

## Live board changes

### Music Sesh status correction

These two cards were moved from `confirmed` to done-state source truth:

- `7acc4522` — `Music Sesh Phase 7 - Playback Continuity + Queue Hygiene`
- `4b2d72f8` — `Music Sesh Phase 7 Stabilization - Queue Authority + Hub Hygiene`

Result:

- both now render as done-state cards
- both now carry the configured resolved reaction

### Feature done-state wording

Shared feedback rendering now treats stored feature status `fixed` as visible status `Resolved`.

This change was applied across:

- forum starter cards
- board exports
- reviewed task packets
- status audit comments

Bug cards still display stored `fixed` as `Fixed`.

### Dedicated Fitness project board

Created a new project forum under `Project Feedback Boards`:

- forum name: `fawxzzy-fitness`
- forum id: `1508144612957622313`

The new board was created by copying the general `feedback` forum shape:

- same permission overwrite shape
- same forum tags
- same baseline forum layout

Moved current Fitness app cards:

- `4309deaf` — `Update history section and upgrade analytics`
- `8ed05d76` — `Add per-day exercise templates for easy copy, paste, and modification`

Result:

- both bounded rows now point at the dedicated `fawxzzy-fitness` board
- the old general-feedback source threads were deleted after the new canonical threads were created

## Archived duplicate cleanup

Deleted archived duplicate source threads from the general `feedback` board for the old Music Sesh / Spotify Club cluster once the dedicated project board was already canonical.

Deleted archived duplicate thread ids:

- `1506736348093222944`
- `1506720630563803186`
- `1506672197349937252`
- `1506370627680993410`
- `1506191836522221700`
- `1506158443311005758`
- `1506118397488922754`
- `1506044953476862146`

## Verification

- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/bug-reports.test.ts`
- `node --test scripts/export-feedback-board.test.mjs`
- `npm run verify`
- live readback of:
  - Music Sesh Phase 7 rows
  - new `fawxzzy-fitness` forum channel
  - moved Fitness app card forum pointers
  - archived `feedback` thread inventory

## Non-goals

- no product runtime changes
- no deploy
- no Vercel or Supabase schema mutation
- no Discord bot command-surface change
