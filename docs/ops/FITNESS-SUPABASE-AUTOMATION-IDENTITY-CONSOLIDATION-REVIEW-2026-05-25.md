# Fitness Supabase Automation Identity Consolidation Review

Date: 2026-05-25  
Mode: read-only review packet  
Project: Fitness Supabase (`lpswxoyfniocuhljgzbc`)

## Objective

Review the broader Fitness automation identity model after Pass 1 created four new automation-classified profiles and decide the canonical automation identity policy before any further Supabase mutation.

No Supabase write happened in this lane.

## Inputs

- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-CLEANUP-PLAN-1-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-MUTATION-PASS-1-2026-05-25.md`
- `docs/ops/FITNESS-SUPABASE-PASS-1-AUTOMATION-HEURISTIC-DECISION-2026-05-25.md`
- `docs/ops/FITNESS-SUPABASE-AUTOMATION-METADATA-QA-VISIBILITY-DECISION-2026-05-25.md`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/`
- `repos/fawxzzy-fitness/supabase/migrations/044_real_user_numbers.sql`
- `repos/fawxzzy-fitness/src/lib/qa-data-visibility.ts`
- `repos/fawxzzy-fitness/scripts/qa/fitness-codex-seed.mjs`

## Current State

### Pre-Pass-1 baseline

- explicit automation auth users: `1`
- automation profiles: `12`
- automation profiles backed by auth rows still tagged `unknown`: `11`

### Pass 1 effect

- created profiles for:
  - `candidate-01`
  - `candidate-02`
  - `candidate-03`
  - `candidate-04`
- trigger result for all four:
  - `user_kind = automation`
  - `user_number = null`
  - `show_qa_llel_data = false`
- automation profiles moved `12 -> 16`
- automation-profile/auth-unknown mismatches moved `11 -> 15`

### Canonical anchor already present

The governed export `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/canonical-automation-identity.redacted.json` still identifies exactly one explicit automation anchor:

- `automation-anchor-01`

That matches the earlier hygiene plan and the QA seed script posture:

- one verified writable automation identity by default
- additional automation identities only when named, purposeful, and governed

## Source Of Current Automation Classification

`044_real_user_numbers.sql` makes automation classification possible through either:

1. auth metadata
   - `raw_app_meta_data.account_kind = automation`
   - `raw_user_meta_data.account_kind = automation`
2. email heuristic
   - regex tokens including `codex`, `test`, `qa`, `example`, `preview`, `local`

That means profile creation is not an isolated mutation class. Any insert into `public.profiles` is also a classification event under current DB policy.

## Review Answers

### 1. Should Fitness allow multiple automation-classified profiles?

Yes, but only by class and intent, not by drift.

Recommended policy:

- allow multiple automation-classified profiles when they map to:
  - the canonical writable automation identity
  - named QA/LLEL automation identities
  - explicit test or operational automation identities
- do not preserve extra automation-classified rows merely because a heuristic created them

### 2. Should there be exactly one canonical AI automation profile?

Yes for the default writable automation identity.

Recommended policy:

- keep exactly one canonical writable AI automation profile as the default automation anchor
- treat any other automation identities as secondary named identities that require a distinct purpose and retention reason

This is consistent with:

- the original hygiene inventory and cleanup plan
- the explicit automation anchor export
- the Codex QA seed contract

### 3. Should Codex/test/example heuristic profiles remain separate automation identities?

Not by default.

Recommended policy:

- heuristic-created automation rows may remain temporarily as tolerated automation identities
- they should not automatically be ratified as durable named automation identities
- any row that remains long-term should later enter one of two classes:
  - retained named automation identity
  - reviewed cleanup / metadata-alignment candidate

### 4. Should automation auth users be tagged explicitly in auth metadata?

Yes for canonical or deliberately retained automation identities. Not yet as a bulk pass.

Recommended policy:

- explicit auth metadata should be the long-term authoritative automation marker
- email heuristic may remain as a defensive fallback, not the main governance surface
- do not bulk-align the current `15` mismatch rows in this lane
- only align rows after class review:
  - canonical anchor
  - named retained QA identities
  - any additional retained automation identities approved by owner review

### 5. Should profile-side automation classification rely on email heuristic, auth metadata, or both?

Both for now, but with different roles.

Recommended policy:

- auth metadata should be the primary durable governance signal
- email heuristic should remain a fallback safety net for obvious automation/test rows
- future approval packets must predict whether the heuristic will fire before any profile-creation write

### 6. Should `show_qa_llel_data = false` remain the default for heuristic-created automation profiles?

Yes.

Reason:

- application logic already separates automation classification from QA/LLEL visibility
- `resolveShowQaLlelDataPreference()` defaults automation to visible only when no explicit override exists
- the four Pass 1 rows were inserted with an explicit `false`
- that keeps QA/LLEL visibility reserved for the canonical automation identity and other named QA identities

### 7. Which automation profiles, if any, should later have QA/LLEL visibility repaired?

Only explicit named QA/LLEL identities should be candidates.

Recommended visibility policy:

- keep `show_qa_llel_data = false` for heuristic-created automation rows, including `candidate-01` through `candidate-04`
- consider `show_qa_llel_data = true` only for:
  - the canonical writable automation identity
  - named QA/LLEL automation identities with an actual operator/testing role

### 8. Which automation-profile/auth-unknown mismatches should remain tolerated?

Temporarily tolerated mismatch classes:

1. the four new Pass 1 heuristic automation rows
2. prior automation-profile/auth-unknown rows that:
   - are already automation-classified at profile level
   - have no Discord member linkage
   - have no verification-token history
   - are not being used as canonical human accounts

These are governance debt, but not immediate rollback candidates.

### 9. Which mismatches should become an explicit future mutation scope?

Future mutation scope candidates:

1. explicit auth-metadata alignment for selected retained automation identities
2. canonical automation identity consolidation for rows that should be merged into a named automation set
3. row-level review of any automation mismatch with:
   - conflicting ownership evidence
   - human-account ambiguity
   - future Discord-linked usage

### 10. Should future create-profile repair passes exclude all heuristic automation rows?

Yes.

Recommended policy:

- any auth row predicted to satisfy `is_automation_auth_user()` must be excluded from normal human-style create-profile repair
- such rows belong in a dedicated automation review or automation-targeted mutation lane

### 11. Does DiscordOS separation affect any automation identity policy?

Not directly for this lane.

DiscordOS separation remains a deferral boundary:

- no Discord runtime mutation is required to decide automation identity policy
- no Discord/Music Sesh table mutation is justified by this review
- future DiscordOS separation may change ownership boundaries for Discord-derived records, but it does not decide whether a Supabase auth/profile pair is automation

### 12. What is the first safe mutation package after this review?

Recommended first safe mutation package:

`Fitness Supabase Selected Automation Auth-Metadata Alignment Decision Packet`

That next packet should stay decision-first and answer:

1. which of the `15` automation-profile/auth-unknown mismatches should be explicitly tagged as automation in auth metadata
2. which rows remain tolerated-but-unratified heuristic automation identities
3. which rows require owner review before metadata alignment

## Automation Identity Policy Recommendation

Recommended durable policy:

1. keep one canonical writable automation identity as the default automation anchor
2. allow additional automation identities only when they are named, purposeful, and governed
3. treat heuristic-only automation rows as tolerated interim identities, not automatically canonical identities
4. require trigger-side-effect prediction before any future profile-creation pass
5. exclude heuristic automation rows from normal human repair lanes

## Canonical AI Automation Profile Recommendation

- retain the existing explicit automation anchor as the canonical writable automation baseline
- do not replace the canonical anchor with `candidate-01` through `candidate-04`
- do not broaden “canonical automation identity” to include every Codex/example heuristic row

## Auth Metadata Recommendation

- long-term target: canonical and retained automation identities should be explicitly tagged in auth metadata
- immediate action: no bulk alignment yet
- next review lane should choose a narrow subset of mismatch rows for explicit auth-metadata alignment

## Profile Metadata Recommendation

- keep `user_kind = automation` and `user_number = null` for:
  - canonical automation anchor
  - `candidate-01` through `candidate-04`
  - other reviewed automation identities
- do not reinterpret these four Pass 1 rows as human profiles

## QA/LLEL Visibility Recommendation

- keep `show_qa_llel_data = false` for `candidate-01` through `candidate-04`
- reserve QA/LLEL visibility for:
  - canonical writable automation identity
  - named QA/LLEL automation accounts
- do not run a broad QA visibility repair pass against all automation mismatches

## Tolerated Mismatch Classes

- canonical explicit automation auth/profile pair
- heuristic automation profiles backed by auth-side `unknown` where the row is not yet ratified but also not a human repair target
- Pass 1 created automation rows `candidate-01` through `candidate-04`

## Mutation Candidates

Future mutation candidates, in order:

1. narrow auth-metadata alignment for selected retained automation identities
2. canonical automation identity consolidation review for any retained secondary automation accounts
3. QA/LLEL visibility repair only for named QA identities, not broad heuristic rows

## Manual-Review Classes

- any automation mismatch with unclear ownership or purpose
- any automation mismatch that later gains Discord-linked or human-facing product significance
- any row that looks like a candidate for canonical automation-anchor replacement

## DiscordOS Deferral Boundary

- no DiscordOS runtime change is required for this policy
- no Discord/Music Sesh mutation is in scope
- DiscordOS infrastructure separation remains separate from automation identity consolidation

## Rollback / Non-Rollback Posture

- rollback is still not preferred
- the Pass 1 created rows improved auth-only drift
- the remaining issue is automation-governance classification, not bad row creation mechanics
- the safer path is policy-led metadata review, not destructive reversal

## Pass Acceptance Posture

Pass 1 should remain:

- accepted as a bounded create-profile repair
- partially accepted as a hygiene improvement
- followed by automation-governance review before further mutation

## Non-Goals

- auth deletion
- profile deletion
- trigger changes
- RLS or policy changes
- Discord/Music Sesh cleanup
- QA visibility mutation
- bulk auth-metadata relabeling

## Exact Next Package

`Fitness Supabase Selected Automation Auth-Metadata Alignment Decision Packet`

Scope for that next packet:

- review the `15` automation-profile/auth-unknown mismatches
- separate them into:
  - explicit auth-metadata alignment candidates
  - tolerated heuristic automation rows
  - manual-review rows
- keep it read-only unless a later owner-approved mutation packet names an exact row subset

## Marker Recommendation

- `Fitness Supabase Profile/Data Hygiene`: `66% -> 70%`
- `Inventory & Truth Map`: `64% -> 65%`
- `Full Stack Re-sync, Clean & Closeout`: stays `76%`

## Validation

Expected validation after this packet:

- `python .\\ops\\validation\\validate_stack.py`
