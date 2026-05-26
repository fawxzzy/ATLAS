# Fitness Supabase Profile/Data Hygiene Mutation Pass 1

- Date: `2026-05-25`
- Lane: `Fitness Supabase Profile/Data Hygiene`
- Mode: `approval-gated Supabase mutation`
- Status: `completed with post-pass classification caveat`

## Goal

Execute the first approved Supabase mutation class:

- create missing profile rows only for the exact approved Pass 1 candidates

Canonical project:

- `lpswxoyfniocuhljgzbc`

Approved candidate labels:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`

## Preflight

Confirmed before write:

1. required export artifacts existed in:
   - `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/`
2. the old repo-root blocker remained cleared:
   - `repos/fawxzzy-fitness/.env.discord-worker` did not exist
3. each approved candidate still:
   - existed as an auth user
   - had sign-in history
   - had no matching `public.profiles` row
   - was not auth-metadata-tagged as automation
4. no Discord or Music Sesh table mutation was required for the approved write scope

## Mutation Class Performed

Performed exactly one mutation class:

- create missing profile rows for `candidate-01` through `candidate-04`

No other mutation class ran.

Not performed:

- auth deletion
- profile deletion
- auth metadata updates
- automation-tagging writes
- unknown-profile mutation
- Discord table mutation
- Music Sesh table mutation
- RLS or policy changes

## Candidate Labels Mutated

Mutated:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`

Skipped:

- none

## Insert Shape Used

The pass used the existing Fitness profile bootstrap contract shape:

- `id`
- `timezone`
- `preferred_weight_unit = 'lbs'`
- `preferred_distance_unit = 'mi'`
- `show_qa_llel_data = false`

Runtime timezone used during insertion:

- `America/New_York`

Database-side defaults/triggers then resolved:

- `active_routine_id`
- `user_kind`
- `user_number`
- `user_number_assigned_at`

## Row Count Before / After

### Auth-only summary

Before:

- auth-only total: `24`
- sign-in-bearing auth-only: `23`
- never-signed-in auth-only: `1`
- recent sign-in-bearing auth-only: `4`
- older sign-in-bearing auth-only: `19`

After:

- auth-only total: `20`
- sign-in-bearing auth-only: `19`
- never-signed-in auth-only: `1`
- recent sign-in-bearing auth-only: `0`
- older sign-in-bearing auth-only: `19`

### Profile count

Before:

- `public.profiles`: `33`

After:

- `public.profiles`: `37`

Net change:

- profile rows created: `4`

## Export Artifact Paths

Pre-mutation and rollback artifacts:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/export-manifest.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/auth-only-candidates.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/proposed-create-profile-rows.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/auth-only-candidates.rollback-map.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/unchanged-deferred-classes.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/canonical-automation-identity.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/rollback-guide.md`

Post-mutation local summary:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/mutation-pass-1-summary.redacted.json`

## Rollback Posture

Rollback remains available through the existing local rollback map and guide.

If this pass must be reverted:

1. resolve `candidate-01` through `candidate-04` through `auth-only-candidates.rollback-map.json`
2. delete only the newly created `public.profiles` rows for those exact auth users
3. do not delete the underlying `auth.users` rows
4. verify deferred classes remain untouched

No rollback was performed in this pass.

## Verification Results

### Candidate integrity

After the write:

- all four candidate auth users still existed
- all four candidate profile rows now existed

### Deferred auth-only classes

Confirmed unchanged:

- older sign-in-bearing auth-only rows remained `19`
- never-signed-in auth-only delete-later candidate remained `1`

### Unknown profiles

Confirmed unchanged:

- unknown profiles remained `3`

### Discord and Music Sesh tables

Confirmed unchanged by count:

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

### Root validation

- `python .\\ops\\validation\\validate_stack.py`
- result: `critical=0 error=0 warning=306`

## Post-Pass Caveat

The write succeeded exactly as a four-row profile creation pass.

However, the post-pass state is **not** a clean match for the original exclusion intent.

Reason:

- the existing database trigger from `044_real_user_numbers.sql` calls `public.is_automation_auth_user(new.id)`
- that function treats auth users as automation not only by auth metadata, but also by email heuristics matching:
  - `codex`
  - `test`
  - `qa`
  - `example`
  - `preview`
  - `local`

Observed effect:

- all four newly created profiles resolved to:
  - `user_kind = automation`
  - `user_number = null`

Net consequence:

- automation profiles increased from `12` to `16`
- automation-profile/auth-unknown mismatches increased from `11` to `15`

So while the pass did **not** update auth metadata and did **not** mutate existing automation rows directly, it did create new rows that now belong to the automation-mismatch class through existing database contract behavior.

## Honest Outcome

What succeeded:

- the bounded four-row profile creation pass
- no Discord or Music Sesh mutation
- no auth deletion
- no policy/RLS change

What did not stay clean:

- the automation-mismatch class did not remain unchanged

That means this pass is durable and reversible, but it should not be treated as a fully clean closure of Pass 1 intent.

## Unchanged / Deferred Classes

Still deferred:

- `19` older sign-in-bearing auth-only rows
- `1` never-signed-in auth-only delete-later candidate
- now `15` automation-profile/auth-unknown mismatches
- `3` unknown profiles
- all Discord tables
- all Music Sesh tables

## Next Supabase Hygiene Package

Next package should be:

- `Fitness Supabase Pass 1 Post-Pass Automation-Heuristic Decision`

That lane should decide whether to:

1. retain these four new automation-classified profiles as correct according to existing DB policy
2. roll them back because Pass 1 was intended for human-style profile repair only
3. refine the candidate-selection or generation contract before any further mutation

Do **not** open `Mutation Pass 2` until that decision exists.

## Marker Recommendation

Do **not** take the full clean-success marker move.

Conservative recommendation:

- `Fitness Supabase Profile/Data Hygiene`: `55% -> 58%`
- `Inventory & Truth Map`: `63% -> 64%`
- `Full Stack Re-sync, Clean & Closeout`: stays `76%`

Reason:

- a real bounded mutation executed with proof
- but the pass introduced new automation-mismatch debt through existing DB trigger behavior
