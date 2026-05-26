# Fitness Supabase Never-Signed-In Auth-Only Delete-Later Approval

Date: 2026-05-25  
Mode: read-only approval packet  
Project: Fitness Supabase (`lpswxoyfniocuhljgzbc`)

## Objective

Prepare the exact approval packet for the single never-signed-in auth-only delete-later candidate without mutating Supabase.

No Supabase write happened in this lane.

## Current State

Live read-only snapshot:

- auth-only users: `20`
- sign-in-bearing auth-only users: `19`
- never-signed-in auth-only users: `1`

Redacted approval artifact:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/never-signed-in-auth-only-delete-later-approval.redacted.json`

## Scope

Reviewed:

- the single never-signed-in auth-only row only

Explicitly excluded:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`
- the `19` sign-in-bearing auth-only heuristic rows
- the `3` unknown profiles
- Discord tables
- Music Sesh tables
- profile creation
- auth-metadata alignment
- trigger changes
- RLS or policy changes

## Exact Eligible Row Count

- eligible never-signed-in delete-later candidate count: `1`

Redacted row label:

- `never-signed-in-01`

## Read-Only Recheck

Confirmed true for `never-signed-in-01`:

- auth user still exists
- no matching profile exists
- `last_sign_in_at` remains null
- auth-side `account_kind` remains `unknown`
- the row is not one of the four governed heuristic automation profiles
- the row is not part of the `19` sign-in-bearing auth-only holdout class

Additional redacted facts:

- created at: `2026-04-28T11:04:03.330657Z`
- heuristic token hits:
  - `codex`
  - `example`

## Approval Decision

Selected posture:

- `delete-later approval only`

Why:

- the row has never signed in
- no profile was ever created
- no named retained-purpose evidence exists
- the row does not belong to the already-governed sign-in-bearing heuristic automation class

This packet does **not** delete the row. It only approves the class and row scope for a later destructive mutation pass if the owner wants to proceed.

## Approved Mutation Class

If reopened later, the only approved mutation class from this packet is:

- delete the single auth-only never-signed-in row `never-signed-in-01`

Not approved:

- any bulk auth deletion
- any profile deletion
- any metadata update
- any mutation touching the `19` sign-in-bearing auth-only rows
- any mutation touching `candidate-01` through `candidate-04`
- any Discord or Music Sesh table mutation

## Export Artifact Requirements Before Mutation

Required before any later delete-later mutation pass:

1. pre-delete auth snapshot for `never-signed-in-01`
2. rollback note confirming the row can only be restored by recreating auth state, not by profile-side rollback
3. unchanged-class confirmation for:
   - the `19` sign-in-bearing auth-only rows
   - `candidate-01` through `candidate-04`
   - unknown profiles
   - Discord tables
   - Music Sesh tables

Current redacted export artifact is sufficient for approval-only review, but a mutation pass should also generate a pre-delete raw snapshot locally and keep it out of Git.

## Rollback Posture

Rollback is destructive-class and should be treated accordingly:

- no profile rollback exists because no profile exists
- no metadata rollback exists because no metadata change is approved
- post-delete restoration would require recreating the auth user if deletion is later judged incorrect

That means the later delete pass must stay explicit, single-row, and approval-gated.

## Heuristic Interpretation

Important nuance:

- the row does hit the automation heuristic by email token pattern
- but unlike the `19` sign-in-bearing rows, it has no sign-in history and no retained-purpose evidence

So the controlling fact for this lane is:

- low-signal never-signed-in residue

not:

- tolerated retained automation identity

## Approval Checklist

- exact row scope identified: `yes`
- row count narrowed to one: `yes`
- no profile exists: `yes`
- never signed in: `yes`
- excluded from other governed classes: `yes`
- Discord and Music Sesh out of scope: `yes`
- no mutation happened in this packet: `yes`

## No-Mutation Confirmation

This packet performed:

- no Supabase writes
- no auth deletion
- no profile deletion
- no profile creation
- no metadata update
- no trigger, RLS, or policy changes
- no Discord or Music Sesh mutation

## Marker Recommendation

- `Fitness Supabase Profile/Data Hygiene`: `94% -> 95%`
- `Inventory & Truth Map`: `70% -> 71%`
- `Full Stack Re-sync, Clean & Closeout`: stays `81%`

## Exact Next Package

`Fitness Supabase Never-Signed-In Auth-Only Delete-Later Mutation Pass`

That later pass should remain:

- single-row only
- auth-delete only
- export-backed
- rollback-documented
- explicitly rechecked live before mutation

## Validation

Expected validation after this packet:

- `python .\\ops\\validation\\validate_stack.py`
