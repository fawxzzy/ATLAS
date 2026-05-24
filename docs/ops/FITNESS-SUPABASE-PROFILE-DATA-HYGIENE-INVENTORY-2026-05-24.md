# Fitness Supabase Profile/Data Hygiene Inventory

Date: 2026-05-24
Lane: Fitness Supabase Profile/Data Hygiene
Mode: read-only inventory only
Status: first inventory recorded

## Goal

Inventory Fitness Supabase identity, profile, Discord-linked, and automation-owned data surfaces before any cleanup of unknown profiles, AI automation identities, or legacy auth/profile drift.

This pass does not:

- mutate Supabase
- delete users or profiles
- update auth metadata
- rotate keys
- print emails, tokens, OAuth values, or secrets
- change Fitness code, Discord runtime, or Vercel config

Canonical project:

- Supabase project ref: `lpswxoyfniocuhljgzbc`

## Inputs

- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- `repos/fawxzzy-fitness/docs/ARCHITECTURE.md`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-LLEL-CHECKLIST.md`
- `repos/fawxzzy-fitness/supabase/migrations/044_real_user_numbers.sql`
- `repos/fawxzzy-fitness/supabase/migrations/20260509103000_profile_qa_visibility.sql`
- `repos/fawxzzy-fitness/src/types/db.ts`
- read-only Supabase MCP inspection against `lpswxoyfniocuhljgzbc`

## High-Level Findings

1. The current Fitness identity problem is mostly classification drift, not widespread orphan damage.
   Every current `public.profiles` row still maps to a live `auth.users` row.

2. The highest-risk unknown class is not the three `profiles.user_kind = 'unknown'` rows.
   It is the larger set of `auth.users` rows with no matching profile: `24` rows, with `23` of them having signed in before.

3. QA/LLEL automation is an intentional product concept in Fitness.
   Local schema and docs explicitly support automation profiles, null `user_number`, and QA/LLEL visibility defaults for automation users.

4. Auth-side identity tagging is far weaker than profile-side tagging.
   Only `1` auth user is explicitly marked `account_kind = automation`, while `12` profiles are already marked `user_kind = automation`.

5. Discord- and Music Sesh-adjacent tables are present in the Fitness Supabase project and carry real row counts.
   That means later cleanup must distinguish between Fitness-core profile hygiene and tables that may eventually move or be governed by Discord OS Infrastructure Separation.

6. Operator secret cleanup still blocks any mutation lane.
   The classified blocker remains `repos/fawxzzy-fitness/.env.discord-worker`.

## Current Profile/Data Map

### Identity and profile core

| Surface | Purpose | Approx row count | Categories seen | User data caution | Cleanup danger | Notes |
| --- | --- | ---: | --- | --- | --- | --- |
| `auth.users` | canonical auth accounts | 57 | `1` automation-tagged, `56` unknown-tagged | high | high | `24` auth rows have no matching profile |
| `auth.identities` | auth provider identity records | 57 | email provider only in current aggregate | high | high | mirrors auth account surface |
| `public.profiles` | per-user settings and Fitness identity posture | 33 | `18` human, `12` automation, `3` unknown | high | high | every profile still maps to auth |

### Discord- and Music Sesh-adjacent tables

| Surface | Purpose | Approx row count | Main category | User data caution | Depends on Discord OS separation |
| --- | --- | ---: | --- | --- | --- |
| `public.discord_member_links` | Fitness profile to Discord member link snapshot | 11 | human-linked only in current data | high | yes |
| `public.discord_feedback_reports` | Discord feedback card source truth | 34 | 27 human, 3 automation, 4 null reporter kind | high | yes |
| `public.discord_update_drafts` | release/update publication drafts | 65 | mostly draft operator artifacts | medium | yes |
| `public.discord_moderation_cases` | moderation case history | 8 | operator/admin history | high | yes |
| `public.discord_verification_tokens` | Discord verification token history | 26 | all consumed, all expired historical rows | high | yes |
| `public.discord_message_command_claims` | dedupe claims for Discord message commands | 10 | operational runtime state | low to medium | yes |
| `public.discord_spotify_connections` | Music Sesh provider connection state | 1 | provider-linked operational state | high | yes |
| `public.discord_spotify_lobbies` | Music Sesh room state | 14 | operational room records | medium to high | yes |
| `public.discord_spotify_room_members` | Music Sesh room membership | 8 | operational room membership | medium to high | yes |
| `public.discord_spotify_queue_items` | Music Sesh queue history | 49 | operational queue/history state | medium to high | yes |

## Identity Classification Inventory

### Auth-side classification

- total auth users: `57`
- confirmed auth users: `57`
- explicit automation auth users: `1`
- explicit human auth users: `0`
- auth users still effectively `unknown`: `56`
- deleted auth users: `0`
- anonymous auth users: `0`

Current auth metadata categories are therefore too weak to act as the cleanup source of truth by themselves.

### Profile-side classification

- total profiles: `33`
- human profiles: `18`
- automation profiles: `12`
- unknown profiles: `3`
- profiles without `user_number`: `15`
- profiles with QA/LLEL visibility enabled: `12`

Profile-side tagging is stronger than auth-side tagging and currently carries the live product intent for QA/LLEL behavior.

### Auth/profile gap

- auth users without a matching profile: `24`
- profiles without a matching auth user: `0`

Auth/profile mismatch is therefore one-directional in the current data:

- the cleanup risk is mostly extra auth rows and weak auth metadata
- not broken profile rows pointing at deleted users

## AI Automation Profile Inventory

Live counts:

- explicit automation auth users: `1`
- automation profiles: `12`
- automation profiles with Discord member links: `0`
- automation profiles with verification-token history: `0`

Cross-check against auth metadata:

- automation profiles backed by automation-tagged auth users: `1`
- automation profiles backed by auth rows still tagged `unknown`: `11`

Local contract evidence:

- `044_real_user_numbers.sql` defines automation detection and allows `user_kind in ('human', 'automation', 'unknown')`
- automation profiles intentionally keep `user_number = null`
- `20260509103000_profile_qa_visibility.sql` enables `show_qa_llel_data` for automation profiles
- `docs/ops/FITNESS-LLEL-CHECKLIST.md` requires the Codex QA profile to be `user_kind=automation` with `user_number=null`

Implication:

- the Fitness app intentionally supports automation identities
- but the canonical automation identity contract is not yet enforced cleanly at the auth metadata layer

## Unknown Profile Inventory

### Unknown profiles

- unknown profiles: `3`
- unknown profiles with Discord member links: `0`
- unknown profiles with verification-token history: `0`

These look lower-risk than the auth-only unknown rows because they currently show no Discord-linked usage in the inspected tables. They still require review before mutation because they are real profile rows.

### Auth-only unknown users

- auth-only rows total: `24`
- auth-only rows never signed in: `1`
- auth-only rows that have signed in: `23`
- auth-only rows created in the last 30 days: `5`
- auth-only rows tagged automation: `0`
- auth-only rows tagged unknown: `24`

This is the highest-risk review class in the inventory.

Interpretation:

- these are not safe blind-deletion candidates
- most have real sign-in history
- they need a later decision pass to determine whether they represent legitimate users without profile creation, test residue, provider drift, or legacy onboarding gaps

## Core Fitness Data Ownership Risk

Distinct owner counts by profile kind across core Fitness tables:

| Data class | Automation owner profiles | Human owner profiles | Unknown owner profiles |
| --- | ---: | ---: | ---: |
| `routines` | 4 | 3 | 0 |
| `sessions` | 4 | 1 | 0 |
| `progression_events` | 0 | 1 | 0 |
| custom `exercises` | 1 | 1 | 0 |

Interpretation:

- automation profiles are not disposable by default; they own real QA/LLEL workout data
- unknown profiles do not currently appear as owners in the inspected core Fitness data classes
- human profile cleanup is high-risk because at least part of the human surface owns real workout history and progression evidence

## Discord and Verification Profile Usage

Current aggregate posture:

- Discord member links total: `11`
- linked Fitness profiles: `11`
- linked human profiles: `11`
- linked automation profiles: `0`
- linked unknown profiles: `0`

Verification token posture:

- verification token rows: `26`
- consumed: `26`
- open: `0`
- expired: `26`

Feedback and update aggregate posture:

- feedback reports: `34`
  - human reporter kind: `27`
  - automation reporter kind: `3`
  - null reporter kind: `4`
- feedback report types:
  - bug: `16`
  - feature: `18`
- update drafts: `65`
  - draft: `46`
  - published: `16`
  - skipped: `2`
  - ignored: `1`

Interpretation:

- current Discord-linked profile usage is entirely human-facing in the direct member-link surface
- automation usage appears in feedback history, but not in Discord member verification/link rows
- cleanup of Discord-linked tables should wait for a later Discord OS Infrastructure Separation lane unless the change is strictly profile-core and fully reversible

## `repos/fawxzzy-fitness/.env.discord-worker` Reference Check

A repo text scan found no in-repo string references to `repos/fawxzzy-fitness/.env.discord-worker`.

Interpretation:

- this file is acting as operator/runtime residue, not as a documented code-level contract
- that matches the earlier Operator Secret Path Hygiene finding that it is a placement blocker, not a source-of-truth file

## High-Level RLS/Policy Shape

Read-only inspection shows:

- `public.profiles` has RLS enabled with `4` policies
- the inspected Discord- and Music Sesh-adjacent public tables all have RLS enabled
- those same inspected Discord- and Music Sesh-adjacent tables currently show `0` policies in the live catalog

This inventory does not prescribe mutation from that fact.

It does mean later cleanup work must treat these tables carefully and verify whether they are intended to remain service-role-only/operator-only surfaces, or whether they need policy work as part of a different lane.

## One-Profile Policy Recommendation

Recommended direction for the later decision pass:

1. Keep one verified automation identity as the canonical writable QA/LLEL automation profile.
2. Keep Zac’s human profile as the explicit human-owner review/admin surface when requested.
3. Do not create additional automation identities unless a lane can name a distinct owner, runtime, and retention reason.
4. Treat auth users with no profile as manual-review inventory first, not auto-delete candidates.
5. Converge auth-side metadata toward the same classification model already enforced in `public.profiles`.

This is still a recommendation, not a mutation decision.

## Cleanup Risk Levels

### High risk

- `auth.users`
- `auth.identities`
- `public.profiles`
- any human-owned core Fitness data
- `public.discord_member_links`
- `public.discord_feedback_reports`
- `public.discord_moderation_cases`
- `public.discord_verification_tokens`
- `public.discord_spotify_connections`

Reason:

- these surfaces contain user identity, historical audit trails, provider linkage, or real product data

### Medium risk

- `public.discord_update_drafts`
- `public.discord_spotify_lobbies`
- `public.discord_spotify_room_members`
- `public.discord_spotify_queue_items`
- `public.discord_message_command_claims`

Reason:

- these are mostly operational or historical workflow tables, but still can affect live Discord behavior or published history

### Lower-risk review classes

- unknown profiles with no Discord links, no verification-token history, and no observed core Fitness ownership

These are still not safe to mutate without receipt-backed review.

## Required Backup/Export Posture Before Any Mutation

Before any cleanup pass mutates data:

1. export exact candidate auth/profile classes by stable IDs into a governed local artifact outside repo source truth
2. export dependent `profiles`, `routines`, `sessions`, `progression_events`, and custom exercise ownership for any candidate profile class
3. export Discord-linked tables for any candidate user/profile class that touches member links, verification, moderation, feedback, or Music Sesh
4. capture a rollback plan for:
   - profile row restore
   - auth/profile relink
   - member-number restore
   - Discord member-link restore
   - Music Sesh connection restore if touched

No cleanup should start from aggregate counts alone.

## Blockers Before Any Cleanup

Primary blockers remain:

- `repos/fawxzzy-fitness/.env.discord-worker` must stay classified as a secret-path blocker until its governed replacement path is explicit
- the canonical automation identity policy is still not fully decided
- Discord/Music Sesh tables remain coupled to the Fitness Supabase project and should not be treated as profile-only cleanup surfaces

Sequence implication:

- Operator Secret Path Hygiene stays ahead of actual Supabase mutation
- Discord OS Infrastructure Separation may need to own part of the Discord/Music Sesh data routing before broader cleanup of those tables

## Recommended Next Decision Pass

Next clean package:

- `Fitness Supabase Profile/Data Hygiene Decision Pass 1`

That pass should:

1. classify the `24` auth-only unknown users into exact review buckets
2. decide whether the `11` profile-side automation rows backed by auth-side `unknown` metadata should be relabeled at auth level, retained as-is temporarily, or reviewed individually
3. review the `3` unknown profiles as a separate low-volume class
4. define the canonical automation identity policy precisely:
   - one verified AI automation profile by default
   - Zac profile only when explicitly requested
5. define the exact backup/export artifact set required before the first mutation pass
6. park any Discord/Music Sesh-adjacent row cleanup that depends on Discord OS Infrastructure Separation

## Non-Goals

This inventory does not:

- delete users
- disable users
- merge profiles
- relabel auth metadata
- rename automation accounts
- clean Discord tables
- touch Discord OS separation implementation

## Marker Interpretation

This package justifies:

- Fitness Supabase Profile/Data Hygiene: `10%`

It does not yet justify movement for:

- Operator Secret Path Hygiene
- Discord OS Infrastructure Separation
