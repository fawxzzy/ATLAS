# Fitness Supabase Profile/Data Hygiene Cleanup Plan 1

Date: 2026-05-24
Lane: Fitness Supabase Profile/Data Hygiene
Mode: docs-only cleanup plan
Status: first approval-gated cleanup plan recorded

## Goal

Define the first safe, approval-gated Fitness Supabase cleanup scope without mutating Supabase.

This plan translates the current inventory and decision pass into:

- required export artifacts
- rollback posture
- exact first mutation boundaries
- explicit non-goals
- approval gates

This plan does not:

- mutate Supabase
- delete auth users
- update auth metadata
- create profiles
- merge profiles
- update RLS or policies
- rotate keys
- change Discord OS routing
- deploy app or worker code

## Inputs

- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- Fitness Supabase project `lpswxoyfniocuhljgzbc`

## Governing Rule

No cleanup mutation should start until all three conditions are satisfied:

1. export artifacts for the exact candidate class are captured
2. rollback steps are named for that exact class
3. the current secret-path blocker around `repos/fawxzzy-fitness/.env.discord-worker` is either cleared or explicitly excepted for the approved pass

## Current Cleanup Classes

The plan continues to use the current reviewed classes:

- `1` low-signal auth-only delete-later candidate
- `23` sign-in-bearing auth-only rows
- `11` automation-profile/auth-unknown mismatches
- `3` unknown profiles
- Discord and Music Sesh tables deferred to Discord OS Infrastructure Separation unless a narrow profile-core repair requires a direct touch

## Canonical Automation Policy

Planned policy:

- default to one verified AI automation profile as the canonical writable automation identity
- use the owner profile only when explicitly requested
- do not preserve multiple automation identities by accident just because they already exist

Operational consequence:

- the `11` automation-profile/auth-unknown mismatches should not be batch-retagged until the final canonical automation row is named and retained with intent
- the first mutation pass should prefer metadata normalization or reviewed profile creation over destructive automation cleanup

## Export And Backup Artifacts Required Before Mutation

Before any future mutation pass, prepare governed local exports for the exact rows in scope.

### Artifact set A: auth-only candidate export

For any auth-only row selected for review:

- auth row identifier set
- created timestamp
- last sign-in timestamp
- confirmed/deleted/anonymous flags
- app/user metadata shape summary

Purpose:

- determine whether the row is a real user without profile creation, legacy drift, or a low-signal stale auth record

### Artifact set B: profile candidate export

For any profile selected for review:

- profile identifier set
- `user_kind`
- `user_number`
- `user_number_assigned_at`
- `show_qa_llel_data`
- timestamps

Purpose:

- restore profile-core identity state if a profile is later merged, relabeled, or deleted

### Artifact set C: profile-owned Fitness data export

For any candidate profile:

- owned routine identifiers
- owned session identifiers
- owned progression event identifiers
- owned custom exercise identifiers

Purpose:

- prove whether the candidate is disposable, merge-only, or must be retained because it owns real workout data

### Artifact set D: Discord and Music Sesh dependency export

Only when the candidate class touches these surfaces:

- `discord_member_links`
- `discord_verification_tokens`
- `discord_feedback_reports`
- `discord_moderation_cases`
- `discord_update_drafts`
- `discord_spotify_connections`
- `discord_spotify_lobbies`
- `discord_spotify_room_members`
- `discord_spotify_queue_items`
- `discord_message_command_claims`

Purpose:

- prevent profile cleanup from silently breaking Discord or Music Sesh continuity

### Artifact set E: mutation manifest

For the approved pass, create a manifest that names:

- exact class in scope
- exact rows selected
- exact SQL shape intended later
- expected post-mutation counts
- rollback artifact paths

Purpose:

- make the first mutation pass traceable and reversible

## Rollback Posture By Proposed Action

### Action: create missing profile

Rollback requirements:

- delete only the newly created profile row if the creation was incorrect
- restore any member-number assignment state if auto-assigned
- preserve original auth row untouched

Safe target:

- selected signed-in auth-only rows only

### Action: tag auth row as automation

Rollback requirements:

- restore prior auth metadata snapshot
- verify QA/LLEL access behavior returns to pre-change state if reverted
- verify no unintended policy or UI gating changes occur

Safe target:

- reviewed automation-profile/auth-unknown mismatches only

### Action: delete low-signal auth-only row

Rollback requirements:

- restore the exact auth export if deletion is determined to be wrong
- verify no profile or dependent data existed before deletion

Safe target:

- only the single never-signed-in auth-only candidate after explicit approval

### Action: merge or delete profile

Rollback requirements:

- restore profile row
- restore member-number state
- restore any linked Fitness-owned or Discord-owned dependent rows

Safe target:

- none in Cleanup Plan 1; this remains later and higher risk

## Exact First Cleanup Scope

Cleanup Plan 1 recommends a narrow first mutation scope later, if approved:

### Phase 1 candidate scope

1. review the single never-signed-in auth-only row as the only plausible delete-later candidate
2. review a small approved subset of the `23` sign-in-bearing auth-only rows for `create profile` rather than deletion
3. review the current explicit automation auth user as the canonical automation anchor
4. do not mutate the `11` automation mismatches until the canonical automation policy is explicitly ratified
5. do not mutate the `3` unknown profiles in the first pass

### Why this is the first scope

- it minimizes destructive action
- it reduces auth/profile drift with the least irreversible risk
- it avoids touching Discord and Music Sesh tables by default
- it avoids large automation relabeling before the policy is final

## What Stays Manual Review

The following stay manual-review only in Cleanup Plan 1:

- `23` sign-in-bearing auth-only rows
- `11` automation-profile/auth-unknown mismatches
- `3` unknown profiles
- any row that owns routines, sessions, progression events, or custom exercises
- any row that touches Discord member links, verification, moderation, feedback, updates, or Music Sesh tables

Reason:

- each class still needs exact row-level review before any mutation

## What Stays Deferred To Discord OS Infrastructure Separation

Cleanup Plan 1 does not include:

- `discord_member_links`
- `discord_feedback_reports`
- `discord_update_drafts`
- `discord_moderation_cases`
- `discord_verification_tokens`
- `discord_message_command_claims`
- `discord_spotify_connections`
- `discord_spotify_lobbies`
- `discord_spotify_room_members`
- `discord_spotify_queue_items`

Exception:

- if a future approved profile-core repair requires a narrow dependency touch, that touch must be isolated, exported first, and recorded as an exception in its own receipt

## Handling The 1 Low-Signal Auth-Only Delete-Later Candidate

Planned treatment:

- keep it read-only until export artifact set A is captured
- confirm it has no profile
- confirm it has never signed in
- confirm no dependent app-facing usage is discovered in review
- require explicit owner approval before deletion

Planned first action:

- candidate review only, not automatic deletion

## Handling The 23 Sign-In-Bearing Auth-Only Rows

Planned treatment:

- treat these as likely `retain` or `create profile` candidates first
- do not consider auth deletion as the default outcome
- review exact sign-in-bearing rows in batches small enough to verify safely

Planned first action:

- select a narrow reviewed subset for later `create profile` consideration

Reason:

- sign-in history makes these materially different from low-signal residue

## Handling The 11 Automation-Profile/Auth-Unknown Mismatches

Planned treatment:

- retain now
- define which row becomes the canonical verified automation identity
- review the remaining automation rows against actual QA/LLEL purpose
- later consider auth metadata normalization through `tag as automation`

Planned first action:

- no mutation in Cleanup Plan 1
- policy and owner review first

## Handling The 3 Unknown Profiles

Planned treatment:

- keep read-only for now
- confirm at row level whether they are legacy placeholders, abandoned profiles, or recoverable human/automation records
- do not batch delete

Planned first action:

- manual review only

## `.env.discord-worker` Blocker

Cleanup Plan 1 remains blocked by:

- `repos/fawxzzy-fitness/.env.discord-worker`

Why it matters:

- it keeps Discord/worker runtime secret-bearing residue inside the repo root
- profile/data cleanup should not normalize identity ownership while the operator/runtime secret lane is still ambiguous

What clears this blocker later:

- either move the runtime secret path into the governed root secret lane
- or explicitly document and approve a temporary exception for the exact mutation pass

## Explicit Owner Approval Gates

The following require explicit owner approval before mutation:

- any auth deletion
- any profile deletion
- any profile merge
- any auth metadata relabeling
- any change that touches Discord-linked tables
- any change that touches Music Sesh tables
- any cleanup pass launched before the `.env.discord-worker` blocker is resolved or excepted

## Recommended Sequence After This Plan

1. clear or explicitly except the `.env.discord-worker` blocker
2. prepare export artifact templates and storage location
3. run a narrow reviewed candidate packet for:
   - the single never-signed-in auth-only row
   - a small subset of sign-in-bearing auth-only rows
   - the explicit automation auth user plus reviewed automation mismatches
4. request approval for the first mutation pass
5. only then execute the approved, smallest-possible cleanup

## Non-Goals

Cleanup Plan 1 does not:

- authorize cleanup by itself
- imply approval for deletion
- open Discord OS Infrastructure Separation implementation
- change Fitness app code
- change Supabase RLS or schema

## Marker Interpretation

This package justifies:

- Fitness Supabase Profile/Data Hygiene: `30%`

It does not yet justify movement for:

- Operator Secret Path Hygiene
- Discord OS Infrastructure Separation
