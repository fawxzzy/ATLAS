## Discord Completed Feedback Duplicate Delete

Date:
- 2026-05-25

Goal:
- remove duplicate completed feedback cards from non-completed boards
- do not leave them merely archived under older posts when a completed-board copy already exists

Why this follow-up was required:
- the previous duplicate cleanup archived and locked source-board duplicates
- archived duplicates still remained visible under older posts in the original board surfaces
- correct behavior for completed-board duplicates is delete, not archive

Implementation:
- updated `scripts/archive-duplicate-completed-feedback-threads.mjs`
- kept the existing command surface for continuity:
  - `npm run discord:feedback:archive-completed-duplicates -- --apply`
- changed behavior:
  - scans archived source-board forum threads as well as active threads
  - deletes duplicate source-board completed threads instead of archiving them
  - keeps completed-board copies intact

Tests:
- `node --test C:\ATLAS\repos\fawxzzy-fitness\scripts\archive-duplicate-completed-feedback-threads.test.mjs`

Live runs:
1. Dry-run before delete:
   - completed board short ids: `12`
   - duplicate completed targets: `8`
   - candidate thread ids:
     - `1508139413308444722`
     - `1508139419452965016`
     - `1508139424263962765`
     - `1508139429515231402`
     - `1508139434309062758`
     - `1508139438105038890`
     - `1508139447428976791`
     - `1508139450503528451`
2. Apply pass:
   - deleted threads: `8`
   - failures: `0`
3. Follow-up dry-run after Discord propagation:
   - duplicate completed targets: `0`
   - deleted threads: `0`
   - failures: `0`

Outcome:
- completed-board duplicates no longer remain on other board surfaces
- completed board remains the single visible board surface for those finished cards

No-change notes:
- no Supabase mutation
- no Vercel cutover
- no DiscordOS runtime migration
- no bot restart
- `archive/` remained untouched
