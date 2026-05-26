# Fitness Supabase Never-Signed-In Auth-Only Deletion

Date: 2026-05-25  
Mode: approval-gated destructive Supabase mutation  
Project: Fitness Supabase (`lpswxoyfniocuhljgzbc`)

## Objective

Delete exactly the approved never-signed-in auth-only row:

- `never-signed-in-01`

No other auth rows, profile rows, metadata, or app tables were mutated.

## Exact Mutation Class

Performed mutation class:

- delete one auth-only never-signed-in row only

Deleted candidate label:

- `never-signed-in-01`

Rows updated:

- auth rows deleted: `1`
- profile rows deleted: `0`
- auth metadata rows updated: `0`
- profile rows updated: `0`

## Preflight Result

Final preflight passed immediately before write.

Confirmed true for `never-signed-in-01`:

- the auth row still existed
- no matching profile existed
- `last_sign_in_at` remained null
- auth-side `account_kind` remained `unknown`
- the row was not one of:
  - `candidate-01`
  - `candidate-02`
  - `candidate-03`
  - `candidate-04`
  - the `19` sign-in-bearing auth-only rows
  - `automation-anchor-01`
  - any legacy automation mismatch row
  - any unknown profile row

Additional redacted preflight facts:

- created at: `2026-04-28T11:04:03.330657Z`
- heuristic token hits:
  - `codex`
  - `example`

## Reference-Scan Result

Final dependency scan found zero candidate references across the user-linked app and Discord-owned tables scanned before deletion.

Scanned app-owned tables:

- `profiles`
- `sessions`
- `session_exercises`
- `sets`
- `routines`
- `routine_days`
- `routine_day_exercises`
- `exercises`
- `exercise_stats`
- `session_follow_up_jobs`
- `progression_events`

Scanned Discord-owned tables:

- `discord_verification_tokens`
- `discord_member_links`
- `discord_feedback_reports`
- `discord_moderation_cases`

Scan verdict:

- app-owned dependent rows: `0`
- Discord-table references: `0`
- Music Sesh references requiring action in this pass: `0`

## Export Artifact Paths

Local-only export and rollback artifacts created or refreshed under:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/never-signed-in-delete-candidate.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/never-signed-in-delete-candidate.rollback-map.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/never-signed-in-delete-preflight.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/never-signed-in-delete-reference-scan.redacted.json`

These remain local runtime artifacts and were not committed to Git.

## Rollback Posture

Rollback posture remains destructive-class:

- no profile rollback exists because no profile existed
- no metadata rollback exists because no metadata changed
- post-delete restoration would require recreating the auth user explicitly if this deletion were later judged incorrect

This is why the pass stayed:

- single-row only
- export-backed
- preflight-gated

## Before / After Counts

### Before

- auth-only users: `20`
- sign-in-bearing auth-only users: `19`
- never-signed-in auth-only users: `1`
- profiles: `37`
- automation profiles: `16`
- unknown profiles: `3`

### After

- auth-only users: `19`
- sign-in-bearing auth-only users: `19`
- never-signed-in auth-only users: `0`
- profiles: `37`
- automation profiles: `16`
- unknown profiles: `3`

## Unchanged Classes

Confirmed unchanged:

- `candidate-01` through `candidate-04` remain the only automation-profile/auth-unknown mismatch class
- automation-profile/auth-unknown mismatches remain `4`
- the `19` sign-in-bearing auth-only heuristic rows remain untouched
- profile count remains `37`
- automation profile count remains `16`
- unknown profile count remains `3`
- no profile rows were created, updated, or deleted
- no auth metadata alignment changed

## Discord / Music Sesh Untouched Confirmation

Confirmed unchanged in this pass:

- no Discord-owned table mutation
- no Music Sesh table mutation
- no Discord runtime or publication surface mutation

The deletion proceeded only because the final reference scan stayed clean.

## Validation Result

Root validation after deletion:

- `python .\\ops\\validation\\validate_stack.py`
- result: `critical=0 error=0 warning=306`

## Marker Recommendation

- `Fitness Supabase Profile/Data Hygiene`: `94% -> 96%`
- `Inventory & Truth Map`: `70% -> 71%`
- `Full Stack Re-sync, Clean & Closeout`: `81% -> 82%`

## Next Package

`Fitness Supabase Unknown Profile Case Review Packet`

After that:

1. `Fitness Supabase Profile/Data Hygiene Final Closeout`
2. `Playbook/Lifeline external smoke disposal decision`
3. `Preview Cache Remote And Unfurl Verification`
4. `Full Stack Re-sync Closeout Consolidation`
