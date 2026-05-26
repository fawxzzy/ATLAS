# Fitness Supabase Unknown Profile Case Review

Date: 2026-05-25  
Mode: read-only review packet  
Project: Fitness Supabase (`lpswxoyfniocuhljgzbc`)

## Objective

Review the remaining `3` unknown profiles and classify each into the next safe action before any future mutation.

No Supabase write happened in this lane.

## Current Unknown Profile Count

Live read-only snapshot:

- unknown profiles: `3`

Redacted review artifact:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/unknown-profile-case-review.redacted.json`

## Scope Reviewed

Reviewed:

- the `3` unknown profiles only

Explicitly excluded:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`
- the `19` sign-in-bearing auth-only heuristic rows
- `automation-anchor-01`
- legacy automation identities
- Discord tables as mutation targets
- Music Sesh tables as mutation targets
- auth deletion
- profile deletion
- profile updates
- auth metadata updates
- RLS or policy changes
- trigger changes

## Redacted Row Labels

- `unknown-profile-01`
- `unknown-profile-02`
- `unknown-profile-03`

## Live Auth Mapping Result

All `3` unknown profiles still map to live auth users.

Per-row auth result:

- `unknown-profile-01`: live auth user
- `unknown-profile-02`: live auth user
- `unknown-profile-03`: live auth user

Additional durable facts across the class:

- all `3` have sign-in history
- auth-side `account_kind` is still effectively missing or unset
- none hit the automation heuristic by current email-token rules

## Dependent-Data Scan Result

The review scanned these app-owned user-linked tables for each profile id:

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

Result:

- `unknown-profile-01`: `0` app-owned dependent rows
- `unknown-profile-02`: `0` app-owned dependent rows
- `unknown-profile-03`: `0` app-owned dependent rows

So none of the three currently own workout, routine, exercise, progression, or follow-up job state.

## Discord / Music Sesh Reference Result

The review scanned these Discord-linked tables for each profile id:

- `discord_verification_tokens`
- `discord_member_links`
- `discord_feedback_reports`
- `discord_moderation_cases`

Result:

- `unknown-profile-01`: `0` Discord-linked references
- `unknown-profile-02`: `0` Discord-linked references
- `unknown-profile-03`: `0` Discord-linked references

Music Sesh result:

- no direct Fitness-user-id reference was found for this class
- no Music Sesh mutation is implicated by these profiles

## QA / LLEL Visibility Result

All `3` unknown profiles currently have:

- `show_qa_llel_data = false`

That means:

- none currently present a QA/LLEL visibility repair pressure
- any future mutation for this class is a classification question first, not a visibility question

## Classification Table

| Profile | Auth mapping | Heuristic automation hit | App-owned data | Discord-linked refs | Classification | Proposed next action |
| --- | --- | --- | ---: | ---: | --- | --- |
| `unknown-profile-01` | live auth user | no | `0` | `0` | possible human profile needing classification | future metadata repair candidate |
| `unknown-profile-02` | live auth user | no | `0` | `0` | possible human profile needing classification | future metadata repair candidate |
| `unknown-profile-03` | live auth user | no | `0` | `0` | possible human profile needing classification | future metadata repair candidate |

## Review Read

This class is not behaving like stale profile residue.

Why:

- all `3` still map to live auth users
- all `3` have signed in before
- none hit the current automation heuristic
- none currently own app state
- none currently appear in Discord-linked tables

So the strongest current interpretation is:

- low-volume human-profile classification drift

not:

- automation drift
- cleanup-ready profile residue
- no-op governed final state

## Proposed Next Action Per Profile

### `unknown-profile-01`

- hold mutation in this packet
- treat as future metadata repair candidate
- require explicit approval before any profile classification change

### `unknown-profile-02`

- hold mutation in this packet
- treat as future metadata repair candidate
- require explicit approval before any profile classification change

### `unknown-profile-03`

- hold mutation in this packet
- treat as future metadata repair candidate
- require explicit approval before any profile classification change

## Manual-Review Holdouts

All `3` remain manual-review holdouts for one reason:

- the correct future action is probably classification repair, but the exact repair class should still be approved explicitly rather than inferred from this review alone

This packet does **not** approve:

- flipping `user_kind`
- assigning `user_number`
- changing QA visibility
- deleting profiles
- deleting auth users

## Future Mutation Candidates

Strongest future mutation candidate:

- metadata repair approval packet for the `3` unknown profiles as one exact small class

Likely mutation shape if later approved:

- classify them as human-style profiles under current policy
- do not mix that lane with deletion, automation alignment, or Discord-owned data

No future delete-later candidate is approved from this review.

## Explicit Exclusions

Still excluded from this packet:

- `candidate-01` through `candidate-04`
- the `19` sign-in-bearing auth-only heuristic rows
- `automation-anchor-01`
- legacy automation identities
- Discord-owned tables as mutation targets
- Music Sesh-owned tables as mutation targets
- any auth deletion
- any profile deletion
- any auth metadata update
- any profile update

## No-Mutation Confirmation

This packet performed:

- no Supabase writes
- no profile updates
- no profile deletion
- no auth deletion
- no auth metadata updates
- no trigger, RLS, or policy changes
- no Discord or Music Sesh mutation

## Marker Recommendation

- `Fitness Supabase Profile/Data Hygiene`: `96% -> 98%`
- `Inventory & Truth Map`: `71% -> 72%`
- `Full Stack Re-sync, Clean & Closeout`: `82% -> 83%`

## Next Package

`Fitness Supabase Unknown Profile Metadata Repair Approval Packet`

That lane should:

1. keep exact row scope to `unknown-profile-01` through `unknown-profile-03`
2. define the precise profile-side repair shape
3. define rollback posture before any profile mutation
4. keep Discord and Music Sesh tables out of scope

## Validation

Expected validation after this packet:

- `python .\\ops\\validation\\validate_stack.py`
