# Fitness Supabase Profile/Data Hygiene Mutation Blocked: Missing Exact Row Scope

- Date: `2026-05-25`
- Lane: `Fitness Supabase Profile/Data Hygiene`
- Mode: `approval-gated mutation preflight`
- Status: `blocked before write`

## Goal

Attempt to open `Fitness Supabase Mutation Pass 1` using the existing approval packet and stop immediately if the exact approved row subset is missing or ambiguous.

Canonical Fitness Supabase project:

- `lpswxoyfniocuhljgzbc`

## Inputs Checked

- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-CLEANUP-PLAN-1-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-EXPORT-PACKET-1-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-MUTATION-PASS-1-APPROVAL-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-CLEANUP-PASS-1-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-WARNING-DELTA-2026-05-24.md`

## Preflight Results

### 1. Secret-path blocker

Confirmed clear:

- `repos/fawxzzy-fitness/.env.discord-worker` is no longer present

This means the old repo-root secret-path blocker is not what stopped the pass.

### 2. Exact row-scope requirement

The approval packet explicitly requires:

1. the exact reviewed subset of auth-only rows is named
2. the exact intended action for each selected row is named
3. the export artifacts for that exact subset exist

Observed durable state:

- the docs only describe `a small reviewed subset` of the `23` sign-in-bearing auth-only rows
- no committed receipt in the reviewed chain names the exact approved subset
- no durable row-scope manifest naming the approved subset was found

Operational interpretation:

- the current approval posture is class-level only
- it is not row-level enough to support a safe mutation pass

### 3. Export lane posture

Expected export lane:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/`

Observed:

- the `runtime/exports/fitness-supabase-profile-data-hygiene/` tree does not exist yet
- the required export manifest and rollback-map artifacts are not present

This is a second independent stop condition, but the primary blocker is still the missing exact row scope.

## Why Mutation Did Not Run

No write was executed because the governing approval rule was not satisfied.

The current packet authorizes only this shape:

- `create missing profile records only for the exact reviewed subset of sign-in-bearing auth-only users named in the approval packet`

That exact reviewed subset is not currently named in the durable approval chain.

Running a write anyway would require guessing:

- which auth-only users belong in Pass 1
- whether any chosen row unexpectedly touches deferred classes
- what the exact rollback set should be

That would violate the lane rule:

- no approval means no mutation

## What Stayed Unchanged

No Supabase mutation occurred.

Specifically unchanged:

- no auth user deletion
- no profile creation
- no profile deletion
- no auth metadata retagging
- no Discord table mutation
- no Music Sesh table mutation
- no RLS or policy changes

## Required Next Package

The next clean package is:

- `Fitness Supabase Mutation Pass 1 Row-Scope Approval Supplement`

That package should produce:

1. the exact approved row subset for Pass 1
2. the exact intended action per selected row
3. the governed export artifacts for only that subset
4. the rollback manifest for only that subset

Only after that supplement exists should `Fitness Supabase Mutation Pass 1` reopen.

## Recommended Supplement Contents

At minimum, the row-scope supplement should include:

- redacted stable row labels for the selected auth-only users
- exact count in scope
- proof they are sign-in-bearing auth-only rows
- proof they do not require Discord or Music Sesh table mutation in Pass 1
- expected post-mutation profile count delta
- exact export artifact names for the selected subset

## Validation

This stop happened before any external mutation.

Root validation should still be run after recording this receipt.

## Marker Recommendation

No mutation marker advance is justified from this blocked pass.

Keep:

- `Fitness Supabase Profile/Data Hygiene`: `50%`
- `Full Stack Re-sync, Clean & Closeout`: `76%`
- `Inventory & Truth Map`: `62%`

The only safe movement from this pass is stronger approval clarity, not cleanup completion.
