# Discord Completed Feedback Duplicate Archive — 2026-05-25

## Goal
- Remove duplicate completed feedback cards from non-completed boards after the `completed` forum restore.
- Keep the `completed` forum as the only visible board surface for already completed non-testing cards.
- Avoid Supabase, Vercel, DiscordOS, or bot-runtime migration work.

## Scope
- Repo: `repos/fawxzzy-fitness`
- Discord-only mutation
- No Supabase mutation
- No Vercel mutation
- No bot restart
- No updates-channel post

## Implementation
- Added `scripts/archive-duplicate-completed-feedback-threads.mjs`
- Added `scripts/archive-duplicate-completed-feedback-threads.test.mjs`
- Added package script:
  - `npm run discord:feedback:archive-completed-duplicates`
- Updated `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`

## Decision Rule
- Resolve the `completed` forum by channel name.
- Read starter-post short report IDs from the `completed` forum.
- Scan guild active threads.
- Archive and lock any active non-completed-board thread whose starter post short ID already exists on `completed`.
- Leave active non-completed cards alone.
- Leave testing cards alone because no completed-board copy exists for them.

## Dry-Run Before Apply
- Mode: `dry-run`
- Completed board short IDs: `12`
- Active threads scanned: `30`
- Duplicate completed targets: `8`
- Failures: `0`

Duplicate source-board threads identified:
- `4b2d72f8` -> `1508139450503528451`
- `c3450339` -> `1508139447428976791`
- `7acc4522` -> `1508139438105038890`
- `0ea4e2be` -> `1508139434309062758`
- `b58590af` -> `1508139429515231402`
- `b3483cf2` -> `1508139424263962765`
- `1e185453` -> `1508139419452965016`
- `f31e1150` -> `1508139413308444722`

All 8 duplicates were under source forum `1508139160853286942`.

## Apply Result
- Mode: `apply`
- Duplicate completed targets: `8`
- Archived threads: `8`
- Failures: `0`

Each duplicate source thread is now:
- `archived: true`
- `locked: true`

## Post-Apply Verification
- Immediate thread fetch verification confirmed all 8 duplicate source threads report `archived=true` and `locked=true`.
- Follow-up dry-run after Discord thread-index lag settled:
  - Active threads scanned: `22`
  - Duplicate completed targets: `0`
  - Failures: `0`

## Residual Notes
- `1505779648250908734` still reports `starter_message_unavailable` during board scans. It was not part of the completed-duplicate target set.
- This package does not retarget Supabase row pointers from source-board threads to completed-board copies. It only removes visible duplicate board presence.
- `archive/` at the ATLAS root remains intentionally untracked and untouched.

## Verification
- `node --test scripts/archive-duplicate-completed-feedback-threads.test.mjs`
- `npm run discord:feedback:archive-completed-duplicates -- --debug`
- `npm run discord:feedback:archive-completed-duplicates -- --apply`
- direct Discord thread-state check for all 8 archived targets
- `npm run discord:feedback:archive-completed-duplicates -- --debug` after apply
- `npm run verify`
- `python .\\ops\\validation\\validate_stack.py --allow-missing-locked-repos`
