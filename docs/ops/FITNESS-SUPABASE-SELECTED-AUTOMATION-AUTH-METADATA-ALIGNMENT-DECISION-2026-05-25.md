# Fitness Supabase Selected Automation Auth-Metadata Alignment Decision

Date: 2026-05-25  
Mode: read-only decision packet  
Project: Fitness Supabase (`lpswxoyfniocuhljgzbc`)

## Objective

Decide whether any selected automation-classified profiles should receive auth metadata alignment after Pass 1 and the automation identity consolidation review.

No Supabase write happened in this lane.

## Inputs

- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-MUTATION-PASS-1-2026-05-25.md`
- `docs/ops/FITNESS-SUPABASE-PASS-1-AUTOMATION-HEURISTIC-DECISION-2026-05-25.md`
- `docs/ops/FITNESS-SUPABASE-AUTOMATION-METADATA-QA-VISIBILITY-DECISION-2026-05-25.md`
- `docs/ops/FITNESS-SUPABASE-AUTOMATION-IDENTITY-CONSOLIDATION-REVIEW-2026-05-25.md`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/`

## Current State

### Canonical automation anchor

The governed export `canonical-automation-identity.redacted.json` still shows exactly one explicit automation auth anchor:

- `automation-anchor-01`

That row is already auth-metadata aligned as `account_kind = automation`.

### Pass 1 additions

Pass 1 created profile rows for:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`

All four:

- remain `user_kind = automation`
- remain `user_number = null`
- remain `show_qa_llel_data = false`
- remain auth-side `account_kind = unknown`

### Mismatch posture

After Pass 1:

- automation profiles moved `12 -> 16`
- automation-profile/auth-unknown mismatches moved `11 -> 15`

The current policy already decided:

- keep the four new rows
- do not roll them back
- do not align their auth metadata yet
- exclude future heuristic-automation rows from normal human-style create-profile repair

## Decision Options Considered

1. no-op: do not align any auth metadata yet
2. align only canonical writable automation identity
3. align `candidate-01` through `candidate-04`
4. align selected subset after owner review
5. defer all auth metadata alignment to DiscordOS separation / future profile hygiene

## Selected Policy

`No-op now, with explicit future-eligibility rules`

More precisely:

1. do not run any new auth metadata alignment mutation now
2. keep the canonical writable automation identity as the only already-aligned automation auth row
3. keep `candidate-01` through `candidate-04` as profile-side automation only for now
4. require a later row-scoped owner-aware review before any additional auth metadata retagging

This is a real policy decision, not a stall. It narrows the next safe mutation boundary.

## Review Answers

### 1. Should `candidate-01` through `candidate-04` get auth metadata alignment now?

No.

Reason:

- they are currently tolerated heuristic automation identities, not ratified named automation identities
- immediate auth-metadata alignment would convert a trigger-created tolerated class into intentionally retained automation accounts without the narrower row-purpose review
- the current policy explicitly avoided broadening canonical automation authority to all Codex/example heuristic rows

### 2. Should only the canonical writable automation identity get auth metadata alignment?

It already does.

That means there is no mutation to run for the canonical anchor in this lane.

### 3. Should heuristic-only automation profiles remain profile-side only until owner review?

Yes.

Recommended policy:

- keep heuristic-only automation rows as profile-side automation until they are reviewed into one of these classes:
  - retained named automation identity
  - tolerated heuristic automation artifact
  - cleanup / metadata-alignment candidate

### 4. What metadata keys would be written if alignment is approved later?

If a future alignment pass is approved, the expected auth metadata shape should be limited to:

- `raw_app_meta_data.account_kind = automation`

Optional secondary keys, only if the future packet explicitly approves them:

- `raw_app_meta_data.owner`
- `raw_app_meta_data.purpose`

Avoid using `raw_user_meta_data` as the canonical governance surface.

### 5. Is alignment reversible?

Yes, but only with row-scoped export and rollback artifacts.

Minimum rollback posture for a future mutation pass:

1. export the exact pre-mutation auth metadata for each selected row
2. store a redacted manifest in docs
3. keep raw row-level rollback data only under `runtime/exports/`
4. restore the exact prior `raw_app_meta_data.account_kind` state if needed

### 6. Does alignment change QA/LLEL visibility?

Not by itself.

Current product logic separates auth metadata from profile visibility behavior:

- `show_qa_llel_data` is profile-side
- explicit `show_qa_llel_data = false` still wins
- the four Pass 1 rows therefore remain non-QA-visible even if auth metadata were later aligned

Any QA visibility repair would be a separate mutation class.

### 7. Does alignment affect Discord/Music Sesh data?

No direct effect is justified in this lane.

No Discord or Music Sesh table mutation is required for auth-metadata alignment policy, and none should be coupled to it.

### 8. Does alignment require export artifacts beyond the existing runtime exports?

Yes, if a later mutation is approved.

The current export lane is enough for policy review, but a future mutation pass should add:

1. exact pre-mutation auth metadata snapshots for the selected row subset
2. exact proposed auth metadata patch manifest
3. exact rollback map for the selected row subset

These should remain under:

- `runtime/exports/fitness-supabase-profile-data-hygiene/<dated-pass>/`

### 9. What exact row subset would be eligible for a future mutation pass?

Approved now:

- none

Eligible for future review-driven mutation:

- `automation-anchor-01`
  - governance anchor only
  - already aligned, so no write needed
- a future named reviewed subset drawn from the `15` automation-profile/auth-unknown mismatches
  - but only after row-purpose review

Explicitly excluded from immediate auth-metadata alignment:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`

Those four are not approved for auth-metadata alignment in the next mutation pass.

### 10. Should any candidate be excluded from metadata alignment?

Yes.

Exclude now:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`

Reason:

- they are heuristic-created automation identities
- they are not yet named retained automation accounts
- aligning them now would widen intentional automation identity count without the promised owner-aware review

## Exact Eligible Row Labels

For immediate mutation approval:

- none

For future review-only eligibility:

- `automation-anchor-01` as the canonical reference row
- the remaining mismatch class as a review pool, not an approved mutation set

## Metadata Shape If Future Mutation Is Approved

Required minimum shape:

```json
{
  "account_kind": "automation"
}
```

Optional keys, only if purpose-governance is explicitly approved in the future packet:

```json
{
  "account_kind": "automation",
  "owner": "<named owner>",
  "purpose": "<named purpose>"
}
```

## Export / Rollback Requirements

Any future auth-metadata mutation packet must include:

1. exact row labels and redacted row manifest
2. pre-mutation auth metadata export
3. proposed patch export
4. rollback map
5. confirmation that no profile-side fields are changing
6. confirmation that Discord/Music Sesh tables stay untouched

## Why The Decision Is No-Op / Defer

This lane is safer as a no-op because:

- the canonical automation anchor is already aligned
- the four new Pass 1 rows are intentionally not yet ratified as retained automation identities
- alignment would create a stronger durable intent than the current governance model supports
- the policy now distinguishes:
  - canonical named automation identity
  - tolerated heuristic automation rows
  - future reviewed alignment candidates

## Non-Goals

- auth metadata mutation
- profile metadata mutation
- QA/LLEL visibility repair
- trigger changes
- Discord/Music Sesh cleanup
- broad automation consolidation
- human/automation relabeling outside row-scoped review

## Next Package

`Fitness Supabase Automation Mismatch Row-Purpose Review Packet`

That packet should:

1. review the `15` automation-profile/auth-unknown mismatches by purpose class
2. separate them into:
   - canonical already-aligned anchor
   - tolerated heuristic automation rows
   - named retained automation identities that should later receive auth-metadata alignment
   - manual-review rows
3. produce the first exact mutation-eligible subset, if any

## Marker Recommendation

Because this packet lands as a governed no-op/defer:

- `Fitness Supabase Profile/Data Hygiene`: stays `70%`
- `Inventory & Truth Map`: stays `64%`
- `Full Stack Re-sync, Clean & Closeout`: stays `76%`

The lane is safer and more precise, but it does not yet justify a marker bump by itself.

## Validation

Expected validation after this packet:

- `python .\\ops\\validation\\validate_stack.py`
