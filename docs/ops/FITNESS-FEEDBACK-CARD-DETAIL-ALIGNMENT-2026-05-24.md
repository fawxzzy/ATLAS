# Fitness Feedback Card Detail Alignment

Date: 2026-05-24
Lane: Discord Workflow, Publication & Docs Reliability
Mode: narrow feedback-workflow consistency repair
Status: complete

## Goal

Eliminate drift between:

- scoped feature decisions written in planning/chat
- bounded Fitness feedback rows in Supabase
- visible Discord forum starter cards
- downstream board exports and task packets

The immediate trigger was feature card `37183bb9` (`Wine or Cheese`), where the live card had been flattened and still lagged the approved main-channel gameplay scope.

## Root Cause

Two separate projection rules were too weak:

1. feature cards always fell back to a generic acceptance-criteria list unless the scoped detail was manually re-explained elsewhere
2. feature descriptions were capped too early in the forum-card renderer, so the Discord card could lose important approved scope even when the bounded row already held the correct detail

That created a real drift:

- chat and planning carried the richer scoped design
- Supabase and Discord could still show a flatter or older version

## What Changed

In `repos/fawxzzy-fitness`:

- `src/lib/discord/bug-reports.ts`
  - feature cards now consume explicit acceptance-criteria lines from the bounded row when they are present
  - feature forum descriptions now use the remaining Discord body budget after metadata, Acceptance Criteria, and Evidence are preserved
  - generic fallback copy still exists only when no scoped criteria are stored
- `src/lib/discord/bug-reports.test.ts`
  - added coverage for stored feature acceptance criteria
  - added coverage proving long feature descriptions do not crowd out Acceptance Criteria or Evidence
- `docs/ops/FITNESS-FEEDBACK-BOARD.md`
  - documented the feature-card detail rule
- `docs/ops/FITNESS-DISCORD-FEEDBACK.md`
  - documented the same projection rule for Discord/forum sync

## Live Card Repair

The bounded Fitness feedback row for `37183bb9` was updated and resynced so the live forum starter card now matches the approved scope:

- trigger wording is `computa`, not `computer`
- gameplay is in the same/main channel
- one live narrator message is the active game surface
- only the starter can choose
- valid numeric replies may be reacted to or deleted
- the narrator message is edited or reposted to keep visibility
- no dedicated gameplay thread is created
- Vercel owns story logic
- no Supabase is required for MVP

## Boundaries Preserved

- no deploy ran
- no Discord bot code path widened beyond the shared card renderer
- no Vercel state changed
- no new second feedback truth surface was introduced
- Discord remains a projection surface; the bounded row remains source truth for the card

## Verification

From `repos/fawxzzy-fitness`:

- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/bug-reports.test.ts`
- `node --test scripts/export-feedback-board.test.mjs`
- `npm run verify`

Live verification:

- the `37183bb9` forum starter post was fetched directly after sync and confirmed to contain the corrected main-channel scope and explicit Acceptance Criteria

## Fitness Commit

- `a89a807d1206f2a70905dcf6b3b32bbc6e650336`
- `fix: align feedback feature card detail`
