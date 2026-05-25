# Fitness Supabase Profile/Data Hygiene Export Packet 1

Date: 2026-05-24
Lane: Fitness Supabase Profile/Data Hygiene
Mode: read-only export packet
Status: pre-mutation export and rollback packet prepared

## Goal

Prepare the exact export and rollback packet required before any approval-gated Fitness Supabase cleanup mutation.

This packet does not:

- mutate Supabase
- delete users or profiles
- update auth metadata
- change RLS or policies
- print tokens, OAuth values, or secret values
- migrate Discord OS data
- deploy code

Canonical project:

- Fitness Supabase project ref: `lpswxoyfniocuhljgzbc`

## Inputs

- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-CLEANUP-PLAN-1-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-CLEANUP-PASS-1-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-WARNING-DELTA-2026-05-24.md`

## Current Gate Status

### Secret-path blocker

Confirmed:

- the specific repo-root blocker `repos/fawxzzy-fitness/.env.discord-worker` is cleared
- the governed destination now lives under `secrets/local/`
- warning inspection confirmed no secret leakage and no tracked secret residue from that cleanup

Interpretation:

- the immediate secret-path blocker for this lane is cleared
- mutation is still blocked by export, rollback, and approval gates

### Mutation status

Confirmed:

- no Supabase mutation has occurred
- no auth rows have been deleted
- no profiles have been created, merged, deleted, or relabeled
- no Discord or Music Sesh rows have been touched

## Scope

This export packet covers the current reviewed classes:

- `24` auth-only users
- `11` automation-profile/auth-unknown mismatches
- `3` unknown profiles
- `1` current explicit automation auth user
- the canonical automation identity policy
- dependent data required for rollback if any future mutation touches these classes

## Exact Tables And Classes To Export Before Mutation

### Core identity surfaces

Always export before any identity mutation:

- `auth.users`
- `auth.identities`
- `public.profiles`

Export classes within those tables:

1. auth-only user class
2. automation-profile/auth-unknown mismatch class
3. unknown profile class
4. explicit automation auth user

### Core Fitness dependency surfaces

Export for any candidate profile row selected for mutation:

- `public.routines`
- `public.sessions`
- `public.progression_events`
- custom `public.exercises` rows where `user_id` is not null

### Conditional Discord and Music Sesh dependency surfaces

Export only if a candidate class touches them:

- `public.discord_member_links`
- `public.discord_verification_tokens`
- `public.discord_feedback_reports`
- `public.discord_moderation_cases`
- `public.discord_update_drafts`
- `public.discord_message_command_claims`
- `public.discord_spotify_connections`
- `public.discord_spotify_lobbies`
- `public.discord_spotify_room_members`
- `public.discord_spotify_queue_items`

Default posture:

- these remain deferred to Discord OS Infrastructure Separation
- include them in the export packet only as a conditional rollback boundary, not as default first-pass mutation scope

## Redaction Policy

The export packet must preserve reversibility without leaking sensitive data into stack docs.

### Allowed in exported governed local artifacts

- stable internal IDs where required for rollback
- timestamps
- classification fields such as `user_kind` and auth `account_kind`
- member-number state
- row-to-row linkage needed for restore

### Not allowed in docs receipts

- raw emails
- access tokens
- refresh tokens
- OAuth payloads
- secret values
- token hashes
- verification token material

### Doc-layer rule

- docs may describe classes, counts, and artifact names
- docs should redact or avoid user identifiers wherever practical
- raw row-level exports should stay outside committed source truth

## Export Artifact Paths And Names

Governed local artifact root for the future export pass:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/`

Recommended artifact set:

### Manifest

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/export-manifest.json`

Purpose:

- records export run metadata, class selection, row counts, and artifact inventory

### Auth-only class exports

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/auth-only-users.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/auth-only-users.rollback-map.json`

### Automation mismatch exports

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/automation-mismatch-auth-profile.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/automation-mismatch-owned-fitness-data.redacted.json`

### Unknown profile exports

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/unknown-profiles.redacted.json`

### Canonical automation identity export

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/canonical-automation-identity.redacted.json`

### Conditional dependency exports

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/discord-dependent-rows.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/music-sesh-dependent-rows.redacted.json`

Only generate these if the reviewed mutation candidate set touches those classes.

### Rollback guide

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/rollback-guide.md`

Purpose:

- exact restore order for any approved mutation pass

## Rollback Plan Per Action Class

### Action class: create missing profile

Required exports:

- selected auth-only user export
- resulting profile insert plan
- member-number assignment restore map

Rollback:

1. remove only newly created profile rows
2. restore any assigned member-number state if needed
3. leave original auth rows untouched

### Action class: tag auth row as automation

Required exports:

- exact auth/profile pair export
- prior auth metadata snapshot
- owned Fitness data export for the reviewed automation rows

Rollback:

1. restore prior auth metadata from snapshot
2. confirm `user_kind`, QA/LLEL visibility, and access behavior align with the previous state

### Action class: delete one never-signed-in auth-only row

Required exports:

- exact auth row export
- proof that no profile exists
- proof that no dependent app-facing usage was identified in review

Rollback:

1. restore the auth row from the export record if deletion was incorrect
2. confirm no unintended downstream loss occurred

### Action class: merge or delete profile

Not in first mutation scope.

If later approved, required exports must include:

- profile row snapshot
- member-number restore map
- core Fitness ownership export
- conditional Discord/Music Sesh dependency export

## Approval Gate Before Any Write

No write is authorized until all of the following are true:

1. the exact candidate class is named
2. the exact rows are selected
3. the export artifacts above exist
4. the rollback guide exists
5. the mutation manifest exists
6. the owner explicitly approves the exact write scope

Default rule:

- aggregate counts are not enough
- mutation must be based on row-level export evidence

## First Mutation Candidate Scope

The first approved mutation pass should stay narrow.

Recommended first candidate set:

1. the single never-signed-in auth-only row as a review-only delete-later candidate
2. a small approved subset of sign-in-bearing auth-only rows for possible `create profile`
3. the explicit automation auth user as the canonical automation anchor

Do not include by default:

- the full `11` automation mismatches
- the `3` unknown profiles
- Discord-linked tables
- Music Sesh tables

## Records And Classes Still Manual Review

Still manual-review only:

- `23` sign-in-bearing auth-only rows
- `11` automation-profile/auth-unknown mismatches
- `3` unknown profiles
- any candidate row that owns routines, sessions, progression events, or custom exercises
- any candidate row that touches Discord or Music Sesh tables

Reason:

- these classes still require exact row-level review before any safe write

## Discord And Music Sesh Deferral Boundary

The export packet confirms the deferral boundary remains intact.

Default rule:

- Discord and Music Sesh tables are not first-pass mutation surfaces for Fitness profile/data hygiene

Exception rule:

- if a reviewed profile-core mutation candidate depends on those tables, export them as rollback support only and record the exception explicitly before any write

## Canonical Automation Identity Policy

Export Packet 1 carries forward the current recommended policy:

- one verified AI automation profile should be the default writable automation identity
- the owner profile should be used only when explicitly requested

Operational implication:

- export artifacts for the explicit automation auth user should be prepared first
- broader automation retagging should remain deferred until that canonical row is ratified

## Confirmation That `.env.discord-worker` Blocker Is Cleared

Confirmed from the completed secret cleanup pass:

- `repos/fawxzzy-fitness/.env.discord-worker` is gone
- the governed replacement exists under `secrets/local/`
- the warning-delta inspection closed cleanly

Interpretation:

- export preparation is now safe to proceed
- mutation is still approval-gated

## Confirmation That No Mutation Happened

Export Packet 1 is planning-only.

Confirmed non-actions:

- no auth row updates
- no profile row updates
- no auth deletions
- no profile deletions
- no policy changes
- no Discord or Music Sesh data changes

## Recommended Next Package

Next clean package after this export packet:

- `Fitness Supabase Profile/Data Hygiene Mutation Pass 1 Approval Packet`

That packet should:

1. name the exact rows in first-pass scope
2. confirm export artifacts exist
3. confirm rollback artifacts exist
4. request explicit approval for the smallest safe mutation set

## Non-Goals

This export packet does not:

- generate live export files yet
- authorize cleanup
- imply approval for deletion or relabeling
- reopen Discord OS Infrastructure Separation

## Marker Interpretation

This package justifies:

- Fitness Supabase Profile/Data Hygiene: `45%`

It does not yet justify movement for:

- Operator Secret Path Hygiene
- Discord OS Infrastructure Separation
