# Fitness Supabase Profile/Data Hygiene Mutation Pass 1 Approval Packet

Date: 2026-05-24
Lane: Fitness Supabase Profile/Data Hygiene
Mode: docs-only approval packet
Status: pre-mutation approval boundary recorded

## Goal

Create the explicit owner-approval packet for the first Fitness Supabase cleanup mutation pass.

This packet does not:

- mutate Supabase
- delete users or profiles
- update auth metadata
- change RLS or policies
- rotate keys
- change app code
- deploy code

## Inputs

- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-CLEANUP-PLAN-1-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-EXPORT-PACKET-1-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-CLEANUP-PASS-1-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-WARNING-DELTA-2026-05-24.md`

## Gate Status

Confirmed before any future write:

- the repo-root `.env.discord-worker` blocker is cleared
- the warning delta is closed cleanly
- validation is green
- export and rollback structure is documented

Still blocked until explicit approval:

- any Supabase write
- any auth deletion
- any profile creation, merge, delete, or relabel
- any touch to Discord or Music Sesh tables

## Exact Proposed Mutation Classes

Mutation Pass 1 is intentionally narrow.

### Proposed class A: selected sign-in-bearing auth-only users

Allowed action class if explicitly approved later:

- `create profile`

Target posture:

- only a small reviewed subset of the `23` sign-in-bearing auth-only rows
- no auth deletion
- no profile merge

Purpose:

- repair safe profile-core drift for legitimate signed-in users who appear to be missing profile rows

### Proposed class B: explicit automation auth user

Allowed action class if explicitly approved later:

- `retain`

Target posture:

- treat the current explicit automation auth user as the canonical automation anchor
- no mutation required by default in Pass 1

Purpose:

- freeze the canonical automation baseline before any broader automation metadata normalization

### Proposed class C: everything else

Default action in Pass 1:

- `no mutation`

Includes:

- the `11` automation-profile/auth-unknown mismatches
- the `3` unknown profiles
- the single low-signal never-signed-in auth-only row

Reason:

- these stay deferred until the first narrow profile-creation repair either proves safe or reveals missing context

## Exact Non-Goals

Mutation Pass 1 must not:

- delete the single never-signed-in auth-only row
- tag the `11` automation mismatches as automation yet
- touch the `3` unknown profiles
- touch any Discord-linked table
- touch any Music Sesh table
- change RLS or policies
- rotate credentials
- couple this pass to Discord OS Infrastructure Separation work

## Required Export Artifacts

Before any future write, the following artifacts must exist in the governed local export lane:

### Required class exports

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/export-manifest.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/auth-only-users.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/auth-only-users.rollback-map.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/canonical-automation-identity.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/rollback-guide.md`

### Conditional exports

If the selected reviewed subset touches profile-owned Fitness data:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/profile-owned-fitness-data.redacted.json`

If the selected reviewed subset unexpectedly touches deferred Discord or Music Sesh surfaces:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/discord-dependent-rows.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/music-sesh-dependent-rows.redacted.json`

Default expectation:

- the first approved pass should avoid needing those conditional exports

## Rollback Steps

### If the approved action is `create profile`

Rollback steps:

1. remove only the newly created profile rows from the approved subset
2. restore any assigned member-number state from the rollback map
3. confirm original auth rows remain untouched
4. confirm no Discord or Music Sesh linkage was introduced by the pass

### If the approved action touches canonical automation identity posture

Rollback steps:

1. restore the prior auth/profile snapshot from the export artifact
2. confirm QA/LLEL access behavior matches the pre-pass state
3. confirm no broader automation metadata normalization ran

### If an approved pass unexpectedly touches deferred surfaces

Rollback steps:

1. stop the pass
2. use the conditional dependency export for restore
3. record the scope breach in a separate receipt
4. require fresh approval before retrying

## Manual Review Holdouts

The following remain manual-review only after this approval packet:

- `23` sign-in-bearing auth-only rows except the exact small reviewed subset selected for Pass 1
- all `11` automation-profile/auth-unknown mismatches
- all `3` unknown profiles
- the single never-signed-in auth-only candidate
- any row that owns routines, sessions, progression events, or custom exercises unless specifically selected into Pass 1

## Discord And Music Sesh Exclusion

Explicit exclusion for Mutation Pass 1:

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

Rule:

- if the selected row-level mutation scope cannot avoid those tables, Mutation Pass 1 must pause and return for a new approval packet

## Approval Checklist

Before any future Mutation Pass 1 write, all boxes must be explicitly true:

1. exact reviewed subset of auth-only rows is named
2. exact intended action for each selected row is named
3. required export artifacts exist
4. rollback guide exists
5. no deferred Discord or Music Sesh table is in scope
6. the owner approves the exact write scope
7. the operator confirms “no approval means no mutation”

## No Approval Means No Mutation

This packet is not approval.

If the owner does not explicitly approve:

- no SQL should run
- no auth row should be changed
- no profile row should be created
- no cleanup should be inferred from prior planning docs

## Command And Tool Boundary For Future Mutation Pass

If Mutation Pass 1 is later approved:

- use Supabase MCP read/write tools only for the exact approved scope
- keep the write surface as small as possible
- record any SQL or mutation shape in the mutation receipt
- do not mix profile-core cleanup with Discord OS migration work

Not allowed in the future mutation pass unless separately approved:

- broad SQL sweeps
- bulk deletion
- policy changes
- secret rotation
- deploy changes

## Post-Mutation Verification Plan

If Mutation Pass 1 is approved and run later, verify at minimum:

1. selected auth-only rows now have the intended profile-core state
2. no unselected auth-only rows changed
3. no auth deletions occurred unless separately approved
4. canonical automation identity remains intact
5. no Discord or Music Sesh table was touched
6. validation remains green
7. rollback artifacts are still available and accurate

## Recommended Approval Shape

If approval is granted later, it should use this structure:

1. approve the exact row subset only
2. approve `create profile` only for that subset
3. explicitly exclude auth deletion, automation retagging, and Discord/Music Sesh tables
4. require receipt-backed verification immediately after the pass

## Recommended Next Package

The next package after this approval packet should be one of two things:

1. explicit owner approval for the exact Mutation Pass 1 row subset, or
2. additional manual review narrowing the auth-only subset before approval

No other cleanup should be inferred in between.

## Marker Interpretation

This package justifies:

- Fitness Supabase Profile/Data Hygiene: `50%`

It does not yet justify movement for:

- Operator Secret Path Hygiene
- Discord OS Infrastructure Separation
