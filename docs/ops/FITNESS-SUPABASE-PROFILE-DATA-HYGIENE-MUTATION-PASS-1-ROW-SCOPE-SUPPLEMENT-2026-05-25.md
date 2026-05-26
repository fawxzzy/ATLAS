# Fitness Supabase Profile/Data Hygiene Mutation Pass 1 Row-Scope Supplement

- Date: `2026-05-25`
- Lane: `Fitness Supabase Profile/Data Hygiene`
- Mode: `read-only / approval supplement`
- Status: `exact row scope prepared, no mutation executed`

## Goal

Turn the class-level `Mutation Pass 1` approval into an exact row-scoped approval boundary that can later support a narrow `create profile` write and nothing else.

Canonical Fitness Supabase project:

- `lpswxoyfniocuhljgzbc`

## Why This Supplement Was Required

The durable approval chain previously stopped at class level:

- `create missing profile records only for a reviewed subset of sign-in-bearing auth-only users`

That was not sufficient to authorize a write because the exact subset was not yet named and the export lane did not yet exist.

This supplement closes that approval gap without mutating Supabase.

## Preflight Confirmation

Confirmed before row-scope selection:

- the old repo-root secret blocker `repos/fawxzzy-fitness/.env.discord-worker` remains cleared
- no Supabase mutation had occurred before this supplement
- no export lane existed yet under `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/`

## Exact Approved Mutation Class

The only mutation class approved by this supplement for a later Pass 1 execution is:

- `create missing profile rows only for the exact row-scoped sign-in-bearing auth-only subset named below`

No other mutation class is approved by this supplement.

## Exact Pass 1 Row-Scoped Subset

Selection rule used during live read-only inspection:

1. auth user exists
2. profile row does not exist
3. auth user has sign-in history
4. auth user is not the single never-signed-in delete-later candidate
5. auth user is not automation-tagged
6. no core Fitness ownership rows were detected for that auth user in:
   - `routines`
   - `sessions`
   - `progression_events`
   - custom `exercises`
7. no excluded direct dependency rows were detected for that auth user in:
   - `discord_member_links`
   - `discord_feedback_reports`
   - `discord_moderation_cases`
   - `discord_verification_tokens`
8. candidate stays outside all explicitly deferred Discord and Music Sesh mutation scope
9. candidate belongs to the small recent sign-in-bearing auth-only subclass, not the older retained manual-review class

### Exact approved labels

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`

### Exact count

- approved Pass 1 row-scoped subset: `4`

### Deferred from the same auth-only class

- sign-in-bearing auth-only rows still deferred: `19`
- never-signed-in auth-only delete-later candidate still excluded: `1`

## Export Artifact Paths

Local governed export root:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/`

Created during this supplement:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/export-manifest.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/auth-only-candidates.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/proposed-create-profile-rows.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/auth-only-candidates.rollback-map.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/unchanged-deferred-classes.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/canonical-automation-identity.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/rollback-guide.md`

Raw row-level identifiers remain local in `runtime/exports/` and are not committed in docs.

## Proposed Create-Profile Shape

The later mutation pass should not invent a bespoke insert contract.

It should follow the existing Fitness profile bootstrap contract used by `src/lib/profile-core.ts`:

- `id`: exact `auth.users.id` from the rollback map
- `timezone`: runtime default used by `ensureProfileWithClient`
- `preferred_weight_unit`: `lbs`
- `preferred_distance_unit`: `mi`
- `show_qa_llel_data`: `false`

Expected database/default behavior:

- `active_routine_id`: `null`
- `user_kind`: database default `unknown`
- `user_number`: assigned by the existing database trigger
- `user_number_assigned_at`: assigned by the existing database trigger

## Rollback Posture Per Approved Row

Rollback posture is identical for `candidate-01` through `candidate-04`:

1. resolve the label to the underlying `auth.users.id` using `auth-only-candidates.rollback-map.json`
2. delete only the newly created `public.profiles` row whose `id` matches that auth user
3. do not delete or alter the `auth.users` row
4. confirm no unselected profile rows changed
5. confirm deferred classes remained untouched

Rollback instructions are recorded locally in:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/rollback-guide.md`

## Explicit Exclusions

Still out of scope for Pass 1:

- auth deletion
- profile deletion
- the single low-signal delete-later candidate
- the `11` automation-profile/auth-unknown mismatches
- the `3` unknown profiles
- any auth metadata retagging
- Discord tables
- Music Sesh tables
- RLS or policy changes

## Unchanged / Deferred Classes

Unchanged by this supplement:

- the `19` older sign-in-bearing auth-only rows remain manual-review/deferred
- the `1` never-signed-in auth-only row remains delete-later review only
- the `11` automation-profile/auth-unknown mismatches remain retained for a later lane
- the `3` unknown profiles remain retained for a later lane
- the canonical automation anchor remains separate and unchanged

## Owner Approval Statement

This supplement is the exact row-scoped approval boundary for a later `Mutation Pass 1` execution.

If `Mutation Pass 1` is reopened after this supplement, the only approved write scope is:

- `create profile rows for candidate-01 through candidate-04 only`

Any attempt to:

- add more auth-only users
- delete auth rows
- touch deferred classes
- touch Discord or Music Sesh tables
- or change policy/RLS

must stop and return for a new approval packet.

## No-Mutation Confirmation

Confirmed:

- no Supabase mutation happened in this supplement
- no auth users were deleted
- no profiles were created
- no metadata was updated
- no Discord or Music Sesh rows changed

## Validation

Root validation should run after recording this supplement.

## Next Package

`Fitness Supabase Mutation Pass 1`

Allowed scope for that next package:

- create profile rows only for `candidate-01` through `candidate-04`

Everything else remains excluded.

## Marker Recommendation

This supplement justifies:

- `Fitness Supabase Profile/Data Hygiene`: `50% -> 55%`
- `Inventory & Truth Map`: `62% -> 63%`

It does not yet justify movement for:

- `Full Stack Re-sync, Clean & Closeout`

because no data mutation has happened yet.
