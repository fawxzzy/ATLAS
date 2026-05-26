# Fitness Supabase Automation Mismatch Row-Purpose Review

Date: 2026-05-25  
Mode: read-only review packet  
Project: Fitness Supabase (`lpswxoyfniocuhljgzbc`)

## Objective

Review the automation-profile/auth-unknown mismatch class after Pass 1 and classify which automation identities are purposeful, tolerated, stale, manual-review, or future mutation candidates.

No Supabase write happened in this lane.

## Inputs

- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-MUTATION-PASS-1-2026-05-25.md`
- `docs/ops/FITNESS-SUPABASE-PASS-1-AUTOMATION-HEURISTIC-DECISION-2026-05-25.md`
- `docs/ops/FITNESS-SUPABASE-AUTOMATION-METADATA-QA-VISIBILITY-DECISION-2026-05-25.md`
- `docs/ops/FITNESS-SUPABASE-AUTOMATION-IDENTITY-CONSOLIDATION-REVIEW-2026-05-25.md`
- `docs/ops/FITNESS-SUPABASE-SELECTED-AUTOMATION-AUTH-METADATA-ALIGNMENT-DECISION-2026-05-25.md`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/`

## Scope Reviewed

Mismatch class reviewed: `15`

- legacy automation-profile/auth-unknown mismatches: `11`
- Pass 1 additions:
  - `candidate-01`
  - `candidate-02`
  - `candidate-03`
  - `candidate-04`

Comparison-only anchor:

- `automation-anchor-01`

Out of scope:

- Discord tables
- Music Sesh tables
- unknown profile cleanup
- auth or profile mutation

## Durable Facts Used For Classification

### Canonical anchor

- one explicit automation auth/profile pair already exists
- the governed export identifies it as:
  - `automation-anchor-01`
- this remains the canonical writable automation identity

### Legacy mismatch pool

From the existing inventory and decision receipts:

- `11` profile-side automation rows are backed by auth-side `unknown`
- all `11` are QA-visible (`show_qa_llel_data = true`)
- the class owns real QA/LLEL workout data
- the class has no current Discord member-link usage
- the class has no current verification-token usage

### Pass 1 mismatch additions

The four new Pass 1 profiles:

- were created through approved create-profile repair
- were classified as automation by `044_real_user_numbers.sql`
- matched the current heuristic path, not explicit auth metadata
- were inserted with:
  - `show_qa_llel_data = false`
- are retained but excluded from immediate auth-metadata alignment

## Classification Table

| Reviewed unit | Count | Purpose classification | Retention posture | Future metadata alignment? | Future QA/LLEL visibility? | Cleanup candidate? | Notes |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| `automation-anchor-01` | 1 | purposeful retained automation identity | retain | already aligned | already canonical | no | canonical writable automation identity |
| `legacy-mismatch-pool` | 11 | purposeful retained automation identities by class | retain | yes, selected subset later | yes, already QA-visible | not as a bulk pass | owns real QA/LLEL data; row-purpose split still may need later owner review |
| `candidate-01` | 1 | tolerated heuristic automation identity | retain temporarily | not yet | no, keep false | not now | trigger-created automation identity, not a canonical anchor |
| `candidate-02` | 1 | tolerated heuristic automation identity | retain temporarily | not yet | no, keep false | not now | same class as `candidate-01` |
| `candidate-03` | 1 | tolerated heuristic automation identity | retain temporarily | not yet | no, keep false | not now | same class as `candidate-01` |
| `candidate-04` | 1 | tolerated heuristic automation identity | retain temporarily | not yet | no, keep false | not now | same class as `candidate-01` |

## Row-Purpose Read

### Purposeful retained automation identities

Purposeful retained set:

1. `automation-anchor-01`
2. `legacy-mismatch-pool` (`11`)

Why this class stays:

- these rows already express intentional automation use in the live product model
- the legacy `11` are not inert drift; they own real QA/LLEL workout data
- the mismatch is currently governance drift between profile-side classification and auth-side metadata, not proof that the rows are disposable

### Tolerated heuristic automation identities

Temporarily tolerated set:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`

Why they are tolerated, not promoted:

- they were created by a bounded repair pass
- the trigger classified them according to current DB policy
- they are not yet named or purposeful QA identities
- turning them immediately into aligned auth-side automation accounts would widen the intentional automation set too early

### Stale automation residue

No stale automation residue is proven by this review packet.

Important boundary:

- no evidence in the durable receipts shows that the legacy `11` are abandoned or unused
- the four new Pass 1 rows are recent and intentionally retained pending policy resolution

So no row is being classified as stale-cleanup-ready in this packet.

### Manual owner review

Manual owner review remains relevant for:

1. any future attempt to split the `legacy-mismatch-pool` into narrower named automation identities
2. any mismatch row that could challenge the canonical anchor
3. any automation row that later shows mixed human-facing or Discord-linked behavior

This packet does not claim a finer row-by-row purpose split inside the legacy `11` beyond the current durable class evidence.

## Review Answers

### 1. Which automation identities are known-purpose and should stay?

Should stay:

- `automation-anchor-01`
- the `11` legacy mismatches as a purposeful retained class

### 2. Which are only tolerated because current trigger policy created them?

Only tolerated because of current trigger policy:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`

### 3. Which should never become canonical automation identities?

Should not become canonical by default:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`

Reason:

- they are heuristic-created and currently unnamed
- they do not displace the existing canonical anchor

### 4. Which could later receive auth metadata alignment?

Could later receive auth-metadata alignment:

- a selected reviewed subset from the `legacy-mismatch-pool`

Not yet approved for alignment:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`

### 5. Which could later receive QA/LLEL visibility repair?

QA/LLEL visibility candidates:

- the legacy `11` already sit in the QA-visible class
- the four Pass 1 rows are not QA-visibility candidates right now

If future QA visibility repair happens, it should target:

- named QA/LLEL automation identities only
- not all automation mismatches as a bulk class

### 6. Which should remain `show_qa_llel_data = false`?

Keep false:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`

### 7. Which require owner review before any mutation?

Require owner review before mutation:

- any subset chosen from the legacy `11` for auth-metadata alignment
- any automation row proposed for canonical-anchor replacement
- any row proposed for cleanup rather than retention

### 8. Which should be excluded from all future human-style create-profile passes?

Exclude from future human-style create-profile passes:

- all rows predicted to satisfy `is_automation_auth_user()`
- explicitly including:
  - `candidate-01`
  - `candidate-02`
  - `candidate-03`
  - `candidate-04`

### 9. Does any row-purpose decision depend on DiscordOS Infrastructure Separation?

Not for the current `15`.

Reason:

- no Discord or Music Sesh mutation is needed to classify these automation mismatches
- current evidence says the automation mismatch class is not Discord-linked
- DiscordOS separation remains a deferral boundary for Discord-owned tables, not for whether these rows are automation identities

### 10. What is the first safe mutation class after this review?

Recommended first safe mutation class:

`Selected automation auth-metadata alignment approval packet for a reviewed subset of the legacy-mismatch-pool`

That next lane should:

1. remain row-scoped
2. exclude `candidate-01` through `candidate-04`
3. name the exact reviewed legacy labels if any subset is ready
4. carry export + rollback for auth metadata only

## Retained Automation Identities

Retained now:

- `automation-anchor-01`
- `legacy-mismatch-pool` (`11`)
- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`

But not all retained rows share the same governance status:

- canonical retained:
  - `automation-anchor-01`
- purposeful retained by class:
  - `legacy-mismatch-pool`
- tolerated retained:
  - `candidate-01` through `candidate-04`

## Future Mutation Candidates

### Candidate class: future auth-metadata alignment

Best future mutation candidate:

- selected reviewed rows from `legacy-mismatch-pool`

Why:

- they already express intentional automation use
- they already own QA/LLEL data
- the mismatch looks more like metadata lag than wrong profile classification

### Candidate class: future QA/LLEL visibility repair

No immediate QA visibility mutation is recommended from this packet.

Reason:

- legacy purposeful rows are already in the visible class
- the four new heuristic rows are intentionally kept non-visible

### Candidate class: future cleanup

No immediate cleanup mutation is recommended from this packet.

Reason:

- no stale class is proven
- destructive cleanup would be premature

## Unchanged Classes

Still unchanged and deferred:

- Discord tables
- Music Sesh tables
- unknown profiles
- auth deletion
- profile deletion
- trigger changes
- RLS or policy changes

## DiscordOS Deferral Boundary

DiscordOS separation does not block this row-purpose classification.

It still remains the correct defer boundary for:

- Discord-owned tables
- Music Sesh-owned tables
- any later runtime/data-routing migration

It does not decide whether the current `15` mismatch rows are purposeful automation identities.

## Exact Next Package

`Fitness Supabase Selected Legacy Automation Auth-Metadata Alignment Approval Packet`

Scope for that next package:

1. compare the `legacy-mismatch-pool` against the canonical automation-anchor policy
2. pick an exact reviewed subset from the legacy `11`, if any
3. exclude `candidate-01` through `candidate-04`
4. define export, rollback, and no-touch boundaries for a later metadata-only mutation

## Marker Recommendation

- `Fitness Supabase Profile/Data Hygiene`: `70% -> 74%`
- `Inventory & Truth Map`: `64% -> 65%`
- `Full Stack Re-sync, Clean & Closeout`: stays `76%`

## Validation

Expected validation after this packet:

- `python .\\ops\\validation\\validate_stack.py`
