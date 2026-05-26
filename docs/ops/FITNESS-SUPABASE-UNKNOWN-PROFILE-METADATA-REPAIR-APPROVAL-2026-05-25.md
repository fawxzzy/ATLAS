# Fitness Supabase Unknown Profile Metadata Repair Approval

Date: 2026-05-25  
Mode: read-only approval packet  
Project: Fitness Supabase (`lpswxoyfniocuhljgzbc`)

## Goal

Prepare an exact approval-gated metadata repair scope for the `3` unknown profiles identified in:

- `docs/ops/FITNESS-SUPABASE-UNKNOWN-PROFILE-CASE-REVIEW-2026-05-25.md`

No Supabase write happened in this lane.

## Eligible Row Count

- exact eligible row count: `3`

Redacted row labels:

- `unknown-profile-01`
- `unknown-profile-02`
- `unknown-profile-03`

## Live Recheck

Fresh read-only inspection reconfirmed that each eligible row still:

- maps to a live auth user
- has prior sign-in history
- does not hit `is_automation_auth_user()`
- has no app-owned dependent rows
- has no Discord-linked references
- has no direct Music Sesh references
- remains `user_kind = 'unknown'`
- remains `user_number = null`
- remains `user_number_assigned_at = null`
- remains `show_qa_llel_data = false`

## Why The Target Repair Class Is Inferable

This packet does not guess the target classification.

It is inferred from the current Fitness schema contract:

- `repos/fawxzzy-fitness/supabase/migrations/044_real_user_numbers.sql`
  - non-automation profiles inserted under current policy become:
    - `user_kind = 'human'`
    - `user_number = nextval('public.real_user_number_seq')`
    - `user_number_assigned_at = now()`
- the same migration reserves null `user_number` for automation-classified rows only
- `repos/fawxzzy-fitness/docs/PLAYBOOK_NOTES.md`
  - automation accounts must not consume public member numbers
- `repos/fawxzzy-fitness/supabase/migrations/20260509103000_profile_qa_visibility.sql`
  - automation profiles are the class that received the QA visibility backfill

These three rows are:

- live auth-backed
- signed in
- non-automation by current heuristic
- dependency-free

So the smallest current-policy-consistent repair class is:

- classify them as human-style profiles
- assign the next human member numbers
- leave QA visibility unchanged in this lane

## Current Classification

| Profile | Current `user_kind` | Current `user_number` | Current `user_number_assigned_at` | Current `show_qa_llel_data` | Current read |
| --- | --- | ---: | --- | --- | --- |
| `unknown-profile-01` | `unknown` | `null` | `null` | `false` | live non-automation profile missing human classification |
| `unknown-profile-02` | `unknown` | `null` | `null` | `false` | live non-automation profile missing human classification |
| `unknown-profile-03` | `unknown` | `null` | `null` | `false` | live non-automation profile missing human classification |

## Proposed Repair Classification

Current max positive human member number at review time:

- `17`

Approved mutation class, if executed later:

- profile metadata repair only
- no auth mutation
- no deletion
- no QA visibility change

Proposed row-shape:

| Profile | Proposed `user_kind` | Proposed `user_number` | Proposed `user_number_assigned_at` | `show_qa_llel_data` |
| --- | --- | ---: | --- | --- |
| `unknown-profile-01` | `human` | `18` | set at mutation time if currently null | unchanged `false` |
| `unknown-profile-02` | `human` | `19` | set at mutation time if currently null | unchanged `false` |
| `unknown-profile-03` | `human` | `20` | set at mutation time if currently null | unchanged `false` |

## Export Artifact Paths

Committed redacted artifacts:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/unknown-profiles.metadata-repair-candidates.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/unknown-profiles.metadata-repair-proposed-rows.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/unknown-profiles.metadata-repair-reference-scan.redacted.json`

Local rollback artifact, intentionally not committed:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/unknown-profiles.metadata-repair-rollback-map.json`

## Rollback Plan

Before any later mutation pass:

1. re-read the `3` rows and confirm the approval scope still matches
2. snapshot the exact pre-mutation profile state again if anything drifted
3. if the mutation is applied and later judged incorrect, restore per row:
   - `user_kind = 'unknown'`
   - `user_number = null`
   - `user_number_assigned_at = null`
   - `show_qa_llel_data = false`

Rollback does not require:

- auth row restore
- Discord row restore
- Music Sesh row restore

because this class has no current references in those surfaces.

## Explicit Exclusions

Still excluded from this approval:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`
- the `19` sign-in-bearing auth-only heuristic rows
- `automation-anchor-01`
- legacy automation identities
- any auth deletion
- any profile deletion
- any auth metadata update
- any Discord-table mutation
- any Music Sesh-table mutation
- any trigger, RLS, or policy change
- any `show_qa_llel_data` change

## Approval Checklist

- exact row scope is named: yes
- rows still exist: yes
- rows still map to live auth users: yes
- automation heuristic exclusion rechecked: yes
- app-owned dependency scan rechecked: yes
- Discord-linked reference scan rechecked: yes
- Music Sesh direct-reference scan rechecked: yes
- target repair class is inferable from current schema contract: yes
- rollback posture exists: yes
- mutation still not executed: yes

## No-Mutation Confirmation

This packet performed:

- no Supabase writes
- no profile updates
- no profile deletion
- no auth deletion
- no auth metadata update
- no trigger, RLS, or policy changes
- no Discord or Music Sesh mutation

## Marker Recommendation

- `Fitness Supabase Profile/Data Hygiene`: `98% -> 99%`
- `Inventory & Truth Map`: `72% -> 73%`
- `Full Stack Re-sync, Clean & Closeout`: `83% -> 84%`

## Next Package

`Fitness Supabase Unknown Profile Metadata Repair Mutation Pass`

That lane should:

1. mutate only `unknown-profile-01` through `unknown-profile-03`
2. update only profile-side metadata
3. set `user_kind = 'human'`
4. assign `user_number = 18`, `19`, and `20` respectively
5. set `user_number_assigned_at` for each row if still null
6. leave `show_qa_llel_data` unchanged
7. verify that no Discord or Music Sesh references appear as a side effect

## Validation

Expected validation after this packet:

- `python .\\ops\\validation\\validate_stack.py`
