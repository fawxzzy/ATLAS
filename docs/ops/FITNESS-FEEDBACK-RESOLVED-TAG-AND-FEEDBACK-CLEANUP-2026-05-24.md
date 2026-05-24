# Fitness Feedback Resolved Tag And Feedback Cleanup

Date: 2026-05-24
Owner: ATLAS root coordination
Scope: Fitness feedback-board status tags, general `feedback` board cleanup, and live Discord forum state

## Why this pass happened

Two live Discord feedback issues remained:

- feature cards still showed the `Fixed` forum tag even after the visible card copy was changed to `Resolved`
- the general `feedback` forum still contained archived older posts that were supposed to be cleared after project-board splits

## What changed

### Feature tag alignment

Shared Fitness feedback-card tag generation now maps stored feature status `fixed` to the visible forum tag `Resolved`.

Bug cards still map stored `fixed` to `Fixed`.

This change affects:

- forum starter-post tags
- tag resync behavior
- future project-board card moves

### Live Discord board state

Added `Resolved` as an available forum tag on the active feedback boards:

- `feedback` (`1504673475489562744`)
- `music-sesh` (`1508139160853286942`)
- `fawxzzy-fitness` (`1508144612957622313`)

Resynced fixed feature cards so active board threads now show `Resolved` instead of `Fixed`.

Verified sample active thread:

- `1508139438105038890`
- applied tags now include `Feature` + `Resolved`

### General feedback cleanup

Deleted the remaining archived older threads from the general `feedback` forum.

Deleted thread ids:

- `1505839925348532286`
- `1505350639343898754`
- `1505741745864966204`
- `1505318951146491934`
- `1505313798989414502`

After deletion, the general `feedback` archive count is `0`.

### Stale pointer cleanup

Because those older threads were intentionally deleted, the corresponding bounded rows were updated to clear their old Discord forum pointers so future sync jobs do not target unknown channels.

## Verification

- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/bug-reports.test.ts`
- `npm run verify`
- root `python .\\ops\\validation\\validate_stack.py --allow-missing-locked-repos`
- live Discord readback:
  - `feedback` archived thread count
  - active forum tag inventory
  - sample fixed feature thread applied tags

## Non-goals

- no product runtime change
- no deploy
- no Vercel or Supabase schema mutation
