# Fitness Supabase Remaining Auth-Only Manual Review

Date: 2026-05-25  
Mode: read-only review packet  
Project: Fitness Supabase (`lpswxoyfniocuhljgzbc`)

## Objective

Review the remaining `19` older sign-in-bearing auth-only users and classify the next safe action before any future mutation.

No Supabase write happened in this lane.

## Current Auth-Only Counts

Live read-only snapshot:

- auth-only users: `20`
- sign-in-bearing auth-only users: `19`
- never-signed-in auth-only users: `1`

Redacted live review artifact:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/remaining-auth-only-manual-review.redacted.json`

## Scope Reviewed

Reviewed:

- the `19` older sign-in-bearing auth-only users only

Explicitly excluded:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`
- the `1` never-signed-in delete-later candidate
- unknown profiles
- automation-profile/auth-unknown mismatch class
- Discord tables
- Music Sesh tables
- trigger changes
- RLS or policy changes

## Review Result

The key finding is stronger than the earlier class-level assumption:

- all `19` reviewed auth-only users currently match the automation heuristic
- no reviewed row currently qualifies as a clean human-style profile-create candidate

Observed redacted heuristic pattern:

- `18` rows match:
  - `codex`
  - `example`
- `1` row matches:
  - `qa`
  - `example`

## Redacted Row Labels

- `auth-only-01`
- `auth-only-02`
- `auth-only-03`
- `auth-only-04`
- `auth-only-05`
- `auth-only-06`
- `auth-only-07`
- `auth-only-08`
- `auth-only-09`
- `auth-only-10`
- `auth-only-11`
- `auth-only-12`
- `auth-only-13`
- `auth-only-14`
- `auth-only-15`
- `auth-only-16`
- `auth-only-17`
- `auth-only-18`
- `auth-only-19`

## Classification Table

| Class | Count | Decision | Reason |
| --- | ---: | --- | --- |
| possible automation heuristic exclusion | `19` | manual owner review / automation exclusion | all rows currently hit `is_automation_auth_user()` by email heuristic |
| profile-create candidate | `0` | none approved | no clean human-style create-profile subset exists |
| retain auth-only for now | `19` | temporary hold | no write should happen until automation meaning is decided |
| possible stale user | `0` | not proven as separate class | current evidence is stronger for automation/test-style identity than stale-human identity |
| possible test/user-seed artifact | `0` as separate final class | folded into automation heuristic exclusion | the automation heuristic signal is the controlling fact |

## Trigger-Side-Effect Precheck

For all `19` reviewed rows:

- would hit `is_automation_auth_user()`: `yes`
- would become human-style profile: `no`
- would receive `user_number`: `no`
- QA/LLEL visibility if profile were created:
  - `automation-default unless explicit override`

Meaning:

- none of the `19` should move into a normal human-style create-profile lane
- any future profile creation for this class would be an automation-targeted lane, not a human repair lane

## Proposed Next Mutation Class

No exact mutation subset is approved from this review.

Recommended next package:

`Fitness Supabase Remaining Auth-Only Heuristic Automation Governance Packet`

That lane should decide, for the `19` reviewed rows:

1. whether they should remain auth-only and tolerated
2. whether any should be converted into named retained automation identities
3. whether any should be moved into delete-later review
4. whether any should be grouped with the already-governed heuristic automation profile class

## Manual-Review Holdouts

All `19` reviewed rows remain manual-review holdouts.

Reason:

- every row currently matches the automation heuristic
- none should be treated as missing human profiles by default
- there is no row-scoped evidence yet that any one should be promoted into a named automation identity or deleted

## Unchanged / Deferred Classes

Still unchanged and deferred:

- `candidate-01` through `candidate-04`
- the `1` never-signed-in delete-later candidate
- the `3` unknown profiles
- Discord tables
- Music Sesh tables
- trigger changes
- RLS or policy changes

## Explicit Exclusions

This review does **not** approve:

- profile creation for any of the `19`
- auth deletion for any of the `19`
- auth metadata alignment for any of the `19`
- profile deletion
- Discord or Music Sesh mutation

## No-Mutation Confirmation

This packet performed:

- no Supabase writes
- no profile creation
- no auth deletion
- no profile deletion
- no metadata updates
- no trigger, RLS, or policy changes
- no Discord or Music Sesh mutation

## Marker Recommendation

- `Fitness Supabase Profile/Data Hygiene`: `88% -> 91%`
- `Inventory & Truth Map`: `68% -> 69%`
- `Full Stack Re-sync, Clean & Closeout`: `79% -> 80%`

## Next Package

`Fitness Supabase Remaining Auth-Only Heuristic Automation Governance Packet`

This is a better next lane than a human-style create-profile approval packet, because the current review found no eligible human-style subset.

## Validation

Expected validation after this packet:

- `python .\\ops\\validation\\validate_stack.py`
