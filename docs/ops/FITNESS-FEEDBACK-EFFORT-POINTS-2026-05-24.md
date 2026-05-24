# Fitness Feedback Effort Points

Date: 2026-05-24
Lane: Discord Workflow, Publication & Docs Reliability
Mode: narrow feedback workflow consistency package
Status: complete

## Goal

Add one consistent effort-estimate field to Fitness feedback cards so Bug and Feature posts, exports, and reviewed task packets share the same sizing signal.

## What Changed

In `repos/fawxzzy-fitness`:

- `src/lib/discord/bug-reports.ts`
  - added stored Fibonacci `effort_points` support to the feedback row model
  - added a deterministic effort estimator
  - added `Points` to the canonical forum starter-post metadata block
  - recalculates points on new report creation, duplicate folding, and content edits
- `supabase/migrations/20260524110000_discord_feedback_effort_points.sql`
  - added the `effort_points` column
  - constrained values to Fibonacci sizing points
- `scripts/export-feedback-board.mjs`
  - includes `effort_points` in board exports and Markdown summaries
- `scripts/generate-feedback-task-packets.mjs`
  - carries points into reviewed task packets and packet summaries
- `scripts/sync-feedback-forum-posts.mjs`
  - syncs the `Points` line into starter posts
  - updates sync audit copy to `Feedback Card Structure v3`
- `docs/ops/FITNESS-FEEDBACK-BOARD.md`
- `docs/ops/FITNESS-DISCORD-FEEDBACK.md`
  - documented the points contract and the v3 card structure

## Points Contract

Allowed values:

- `1`
- `2`
- `3`
- `5`
- `8`
- `13`
- `21`
- `34`
- `55`

Current behavior:

- points are deterministic, not manual free-text
- the estimate is intended to improve over time as implementation history is reviewed
- cards show the points near the top metadata, next to type and status

## Live Data Work

Applied live against the canonical Fitness project:

- Supabase schema updated for `public.discord_feedback_reports.effort_points`
- 29 non-testing feedback rows backfilled with deterministic Fibonacci estimates
- 19 current or historical forum starter posts resynced with the new `Points` line

No `tmp` fallback, deploy, Vercel mutation, or Supabase project switch was used.

## Verification

From `repos/fawxzzy-fitness`:

- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/bug-reports.test.ts`
- `node --test scripts/sync-feedback-forum-posts.test.mjs`
- `node --test scripts/export-feedback-board.test.mjs`
- `node --test scripts/generate-feedback-task-packets.test.mjs`
- `npm run sanity:quick`
- `npm run typecheck`
- `npm run build`

Verification outcome:

- targeted feedback tests passed
- repo lint/type/build passed
- existing repo-wide lint warnings remain, but no new failure was introduced

## Fitness Commit

- `de775e02ef4bee9a190689494890e43b7ce4a45f`
- `feat: add feedback effort points`
