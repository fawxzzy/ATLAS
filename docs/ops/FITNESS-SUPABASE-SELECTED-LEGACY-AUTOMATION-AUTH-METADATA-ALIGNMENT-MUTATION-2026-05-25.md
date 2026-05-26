# Fitness Supabase Selected Legacy Automation Auth-Metadata Alignment Mutation

Date: 2026-05-25  
Mode: approval-gated Supabase mutation  
Project: Fitness Supabase (`lpswxoyfniocuhljgzbc`)

## Exact Mutation Class

Auth metadata alignment only for the approved legacy purposeful retained automation mismatch rows.

Applied auth metadata change:

- `raw_app_meta_data.account_kind = automation`

No other auth metadata keys were intentionally changed.

## Eligible Row Labels

- `legacy-mismatch-01`
- `legacy-mismatch-02`
- `legacy-mismatch-03`
- `legacy-mismatch-04`
- `legacy-mismatch-05`
- `legacy-mismatch-06`
- `legacy-mismatch-07`
- `legacy-mismatch-08`
- `legacy-mismatch-09`
- `legacy-mismatch-10`
- `legacy-mismatch-11`

## Rows Updated

Updated rows: `11`

- `legacy-mismatch-01`
- `legacy-mismatch-02`
- `legacy-mismatch-03`
- `legacy-mismatch-04`
- `legacy-mismatch-05`
- `legacy-mismatch-06`
- `legacy-mismatch-07`
- `legacy-mismatch-08`
- `legacy-mismatch-09`
- `legacy-mismatch-10`
- `legacy-mismatch-11`

Skipped rows: none

## Preflight Result

Preflight confirmed:

- the approved legacy set still existed as `11` rows
- all `11` were still auth-side `unknown`
- all `11` remained part of the legacy purposeful retained automation mismatch class
- none of the approved rows were:
  - `automation-anchor-01`
  - `candidate-01`
  - `candidate-02`
  - `candidate-03`
  - `candidate-04`
  - unknown profiles
  - auth-only cleanup candidates

## Before / After Mismatch Count

Before:

- total automation-profile/auth-unknown mismatches: `15`
- legacy mismatch class: `11`
- tolerated heuristic candidate class: `4`

After:

- total automation-profile/auth-unknown mismatches: `4`

Meaning:

- the legacy purposeful retained mismatch class was fully cleared
- only the four tolerated heuristic rows remain in the mismatch class

## Export Artifact Paths

Local-only governed artifacts created or used:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/legacy-automation-mismatch-approval-set.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/legacy-automation-auth-metadata-pre.raw.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/legacy-automation-auth-metadata-rollback.raw.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/legacy-automation-auth-metadata-post.raw.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/legacy-automation-auth-metadata-mutation-summary.redacted.json`

These artifacts remain out of Git when they contain row-level data.

## Rollback Posture

Rollback remains metadata-only:

1. use `legacy-automation-auth-metadata-rollback.raw.json`
2. restore the prior `raw_app_meta_data` state for the exact approved labels only
3. do not revert profile rows as part of this rollback class
4. do not touch Discord or Music Sesh tables during rollback

## Verification Result

Verified true after mutation:

- all `11` approved legacy rows now resolve to auth-side `account_kind = automation`
- legacy profile rows were unchanged
- QA/LLEL visibility values for the legacy rows were unchanged
- `candidate-01` through `candidate-04` remained unchanged
- `automation-anchor-01` remained unchanged
- no auth users were deleted
- no profiles were deleted

## Discord / Music Sesh Untouched Confirmation

The following counts stayed unchanged:

- `discord_member_links`: `11 -> 11`
- `discord_feedback_reports`: `35 -> 35`
- `discord_update_drafts`: `65 -> 65`
- `discord_moderation_cases`: `8 -> 8`
- `discord_verification_tokens`: `26 -> 26`
- `discord_message_command_claims`: `24 -> 24`
- `discord_spotify_connections`: `1 -> 1`
- `discord_spotify_lobbies`: `14 -> 14`
- `discord_spotify_room_members`: `8 -> 8`
- `discord_spotify_queue_items`: `49 -> 49`

## QA/LLEL Visibility Unchanged Confirmation

This mutation did not update `show_qa_llel_data`.

Verified result:

- approved legacy rows kept their prior visibility values
- the legacy class remains a mixed QA-visibility class
- the four tolerated heuristic candidates remain excluded from any QA visibility change

## Unchanged Classes

Still unchanged and deferred:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`
- `automation-anchor-01`
- unknown profiles
- older auth-only rows
- never-signed-in delete-later candidate
- Discord tables
- Music Sesh tables
- profile-side QA/LLEL visibility repair
- trigger changes
- RLS or policy changes

## Validation Result

Root validation after mutation:

- `python .\\ops\\validation\\validate_stack.py`
- result: `critical=0 error=0 warning=306`

## Next Package

`Fitness Supabase Profile/Data Hygiene Closeout Pass 1`

That pass should decide whether remaining Fitness Supabase work is:

1. another mutation lane
2. manual owner review
3. DiscordOS-separation-deferred
4. governed no-op tolerance

## Marker Recommendation

- `Fitness Supabase Profile/Data Hygiene`: `78% -> 84%`
- `Inventory & Truth Map`: `66% -> 67%`
- `Full Stack Re-sync, Clean & Closeout`: `76% -> 78%`
- `Operator Secret Path Hygiene`: stays `60%`
