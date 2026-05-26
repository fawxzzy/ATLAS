# Fitness Supabase Selected Legacy Automation Auth-Metadata Alignment Approval

Date: 2026-05-25  
Mode: read-only approval packet  
Project: Fitness Supabase (`lpswxoyfniocuhljgzbc`)

## Objective

Prepare the exact approval packet for aligning auth metadata only for the legacy `11` purposeful retained automation mismatch rows.

No Supabase write happened in this lane.

## Inputs

- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-MUTATION-PASS-1-2026-05-25.md`
- `docs/ops/FITNESS-SUPABASE-PASS-1-AUTOMATION-HEURISTIC-DECISION-2026-05-25.md`
- `docs/ops/FITNESS-SUPABASE-AUTOMATION-METADATA-QA-VISIBILITY-DECISION-2026-05-25.md`
- `docs/ops/FITNESS-SUPABASE-AUTOMATION-IDENTITY-CONSOLIDATION-REVIEW-2026-05-25.md`
- `docs/ops/FITNESS-SUPABASE-SELECTED-AUTOMATION-AUTH-METADATA-ALIGNMENT-DECISION-2026-05-25.md`
- `docs/ops/FITNESS-SUPABASE-AUTOMATION-MISMATCH-ROW-PURPOSE-REVIEW-2026-05-25.md`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/`

## Approval Scope

Approved mutation class for the next execution lane:

- align auth metadata only for the legacy `11` purposeful retained automation mismatch rows

Not included:

- profile updates
- QA/LLEL visibility changes
- auth deletion
- profile deletion
- trigger changes
- RLS or policy changes

## Live Read-Only Recheck

This packet re-identified the legacy mismatch approval set through live read-only inspection against the canonical Fitness project.

Durable local redacted export created:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/legacy-automation-mismatch-approval-set.redacted.json`

Current live recheck result:

- exact eligible row count: `11`
- all `11` still auth-side `account_kind = unknown`
- all `11` are legacy mismatch rows, not Pass 1 candidates
- QA visibility is mixed:
  - `8` currently QA-visible
  - `3` currently not QA-visible

That mixed QA visibility does **not** block this approval packet because this lane is metadata-only and explicitly does not change `show_qa_llel_data`.

## Exact Eligible Row Labels

Approved legacy-only alignment set:

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

## Comparison / Reference Rows

Reference only:

- `automation-anchor-01`

Why reference-only:

- it remains the canonical writable automation identity
- it is already auth-metadata aligned
- there is no approved write for it in the next mutation pass

## Explicit Exclusions

Excluded from this approval:

- `automation-anchor-01`
- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`
- the `3` unknown profiles
- the `19` older sign-in-bearing auth-only rows
- the `1` never-signed-in delete-later candidate
- Discord tables
- Music Sesh tables
- any app or product code

## Row-Class Confirmation

The eligible `11` remain approved for metadata alignment because they already satisfy the current purposeful-retained automation read:

- legacy automation mismatch class
- not cleanup-ready drift
- not heuristic-only Pass 1 rows
- not canonical-anchor replacement candidates

This packet therefore approves a metadata-only convergence move for the legacy class while still keeping the four heuristic Pass 1 rows out of scope.

## Metadata Shape To Apply

Required minimum auth metadata shape for each approved row:

```json
{
  "account_kind": "automation"
}
```

Approved governance constraint:

- write to auth metadata only
- do not change profile fields
- do not change `show_qa_llel_data`
- do not change `user_kind`
- do not change `user_number`

Optional metadata keys are **not** approved in this packet:

- `owner`
- `purpose`
- any additional custom fields

If those are desired later, they require a separate decision lane.

## Export Artifact Paths

Existing governed export lane:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/`

Artifacts relevant to the next mutation pass:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/export-manifest.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/unchanged-deferred-classes.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/canonical-automation-identity.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/legacy-automation-mismatch-approval-set.redacted.json`

Required additional artifacts before the actual mutation pass writes:

1. exact pre-mutation auth metadata snapshot for the `11` approved labels
2. exact redacted patch manifest
3. rollback map per label
4. post-mutation verification snapshot

Those should remain under the same governed export lane and stay out of Git if they contain sensitive row-level values.

## Rollback Plan

Rollback posture for each approved row:

1. capture the exact pre-mutation auth metadata before any write
2. if the metadata alignment causes policy or UI regression, restore the prior auth metadata state for the affected labels only
3. do not revert profile rows as part of this rollback class
4. do not touch Discord or Music Sesh data as part of rollback

Approved rollback boundary:

- metadata-only rollback
- no profile rollback
- no auth deletion

## QA/LLEL Visibility Boundary

This packet confirms:

- QA/LLEL visibility remains unchanged in this lane
- the `11` legacy rows may currently be a mixed visibility class
- the next metadata alignment mutation must not couple itself to visibility repair

So the next pass is allowed to update auth metadata only, and nothing else.

## Discord / Music Sesh Boundary

This packet confirms:

- Discord tables stay untouched
- Music Sesh tables stay untouched
- no DiscordOS separation dependency blocks this metadata-only lane

## Approval Checklist

The next mutation pass is approved only if all of these are true at execution time:

1. the exact eligible set is still `11`
2. the exact labels still match:
   - `legacy-mismatch-01` through `legacy-mismatch-11`
3. none of the approved rows collapse into:
   - `candidate-01` through `candidate-04`
4. `automation-anchor-01` remains reference-only
5. the mutation writes only:
   - `raw_app_meta_data.account_kind = automation`
6. no profile fields are updated
7. no QA visibility fields are updated
8. no Discord or Music Sesh rows are touched
9. rollback artifacts exist before the write

## No-Mutation Confirmation

This packet does **not** perform:

- auth metadata updates
- profile updates
- profile deletion
- auth deletion
- trigger changes
- RLS changes
- Discord or Music Sesh mutation

## Exact Next Package

`Fitness Supabase Selected Legacy Automation Auth-Metadata Alignment Mutation Pass`

That execution packet should:

1. re-verify the `11` eligible labels
2. export pre-mutation auth metadata
3. write only `raw_app_meta_data.account_kind = automation`
4. verify that no profile fields changed
5. verify Discord and Music Sesh tables remained untouched
6. emit a rollback-ready mutation receipt

## Marker Recommendation

- `Fitness Supabase Profile/Data Hygiene`: `74% -> 78%`
- `Inventory & Truth Map`: `65% -> 66%`
- `Full Stack Re-sync, Clean & Closeout`: stays `76%`

## Validation

Expected validation after this packet:

- `python .\\ops\\validation\\validate_stack.py`
