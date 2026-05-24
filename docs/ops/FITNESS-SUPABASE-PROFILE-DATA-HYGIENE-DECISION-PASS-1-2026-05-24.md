# Fitness Supabase Profile/Data Hygiene Decision Pass 1

Date: 2026-05-24
Lane: Fitness Supabase Profile/Data Hygiene
Mode: read-only decision pass
Status: first decision routing recorded

## Goal

Turn the Fitness Supabase profile/data hygiene inventory into exact review actions before any cleanup of auth users, profiles, automation identities, or Discord-linked data.

This pass does not:

- mutate Supabase
- delete users or profiles
- update auth metadata
- rotate keys
- change Discord OS routing
- deploy code

## Inputs

- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- Fitness Supabase project `lpswxoyfniocuhljgzbc`
- `repos/fawxzzy-fitness/supabase/migrations/044_real_user_numbers.sql`
- `repos/fawxzzy-fitness/supabase/migrations/20260509103000_profile_qa_visibility.sql`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-LLEL-CHECKLIST.md`
- Discord OS Infrastructure Separation marker docs

## Governing Decision Rule

No Supabase mutation should occur until all three are explicit:

1. exact record or class ownership
2. backup/export and rollback posture
3. secret/runtime posture around `repos/fawxzzy-fitness/.env.discord-worker`

This decision pass names proposed actions only. It does not authorize cleanup by itself.

## Decision Labels

- `retain`
- `merge`
- `disable`
- `delete later`
- `tag as automation`
- `create profile`
- `manual owner review`
- `defer to Discord OS separation`

## Canonical Automation Policy Recommendation

Recommended policy for later cleanup and future governance:

1. one verified AI automation profile should be the default writable QA/LLEL automation identity
2. Zac’s owner profile should be used only when explicitly requested
3. additional automation-tagged profiles should be retained only if they can be tied to a named testing or operational purpose

This is still a policy recommendation, not an executed change.

## Class 1: Auth Users With No Matching Profile

Current class:

- total auth-only users: `24`
- signed in older than 30 days: `19`
- signed in and created in the last 30 days: `4`
- never signed in: `1`

### Proposed action

Split this class into three actions:

| Subclass | Proposed action | Risk | Required backup/export | Rollback posture | Explicit approval required? | Depends on `.env.discord-worker` cleanup? | Automation policy dependency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `1` never-signed-in auth-only row | `delete later` | medium | export exact auth row metadata and creation timestamp only | restore auth row from export if misclassified | yes | yes | no |
| `4` signed-in created-last-30d auth-only rows | `manual owner review` with likely `create profile` or `retain` | high | export exact auth rows, sign-in timestamps, and any downstream linked usage before mutation | create missing profiles or restore deleted profiles without touching auth row first | yes | yes | no |
| `19` signed-in older auth-only rows | `manual owner review` with likely `create profile` or `retain` | high | export exact auth rows and any dependent app usage before mutation | same as above; no auth delete before profile decision | yes | yes | no |

### Rationale

- `23` of `24` auth-only rows have signed in before, so they are not safe bulk-delete candidates
- auth-only rows may represent legitimate users who never completed profile creation or legacy onboarding drift
- only the never-signed-in row is a plausible low-signal deletion candidate, and even that should remain approval-gated

### Decision

- no auth-only signed-in row should be deleted in the first cleanup pass
- the first likely safe mutation in this class, if approved later, is `create profile` for a reviewed subset
- auth deletion should come last, not first

## Class 2: Automation-Profile / Auth-Unknown Mismatches

Current class:

- total mismatches: `11`
- all `11` are QA-visible (`show_qa_llel_data = true`)
- none have Discord member links
- none have verification-token history

### Proposed action

| Class | Proposed action | Risk | Required backup/export | Rollback posture | Explicit approval required? | Depends on `.env.discord-worker` cleanup? | Automation policy dependency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `11` automation profiles backed by auth rows still tagged unknown | `tag as automation` later, with `retain` until then | medium to high | export exact auth/profile pairs, routine/session ownership, and custom exercise ownership for these profiles | restore prior auth metadata classification if relabel causes policy or UI regression | yes | yes | yes, should converge to one verified automation policy first |

### Rationale

- profile-side classification and QA/LLEL behavior strongly imply intentional automation use
- these rows own real QA/LLEL workout data
- the mismatch is mostly metadata drift between `public.profiles` and `auth.users`

### Decision

- retain these rows now
- do not delete or merge them in the first mutation lane
- the first likely mutation later is auth-side `tag as automation` for reviewed rows, not profile deletion
- before tagging all `11`, require a class-by-class owner check so the final state does not preserve too many automation identities by accident

## Class 3: Unknown Profiles

Current class:

- unknown profiles: `3`
- no Discord member links
- no verification-token history
- no observed ownership of routines, sessions, or custom exercises in the inspected aggregate

### Proposed action

| Class | Proposed action | Risk | Required backup/export | Rollback posture | Explicit approval required? | Depends on `.env.discord-worker` cleanup? | Automation policy dependency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `3` unknown profiles | `manual owner review` with likely `retain`, `merge`, or `delete later` depending on exact row facts | medium | export exact profile rows and confirm no dependent ownership before mutation | restore profile rows and member-number state if misclassified | yes | yes | no |

### Rationale

- these are lower-risk than the auth-only signed-in class because they show no observed core Fitness or Discord-linked usage in the aggregate
- but they are still real profiles and may have local meaning not visible in the aggregate counts alone

### Decision

- keep all three for now
- likely first cleanup action later is case-by-case review, not batch deletion

## Class 4: Current Explicit Automation Auth User

Current class:

- explicit automation auth users: `1`
- explicit automation auth user mapped to profile-side automation: `1`

### Proposed action

| Class | Proposed action | Risk | Required backup/export | Rollback posture | Explicit approval required? | Depends on `.env.discord-worker` cleanup? | Automation policy dependency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `1` explicit automation auth user | `retain` as current canonical automation baseline | low to medium | export exact auth/profile pair before any future mutation touching automation policy | restore metadata and profile linkage if future convergence changes the canonical automation account | yes for any surrounding mutation lane | yes | yes; this is the likely seed for the one verified AI automation profile policy |

### Decision

- this row should remain the safest candidate for the canonical verified automation identity
- do not mutate it in the first cleanup pass

## Class 5: Discord/Music Sesh Tables Inside Fitness Supabase

Current class includes:

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

### Proposed action

| Table class | Proposed action | Risk | Required backup/export | Rollback posture | Explicit approval required? | Depends on `.env.discord-worker` cleanup? | Depends on Discord OS Infrastructure Separation? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Discord identity/history tables | `defer to Discord OS separation` unless a specific profile-core repair requires them | high | export table subsets for any touched user/profile class before mutation | restore rows from export; do not rely on aggregate counts | yes | yes | yes |
| Music Sesh connection/room tables | `defer to Discord OS separation` | high | full class export before any mutation | restore from export and preserve live room/runtime continuity | yes | yes | yes |
| Message-claim operational table | `defer to Discord OS separation` unless runtime-only cleanup is separately approved | medium | export rows if touched | restore dedupe state only if runtime breakage occurs | yes | yes | yes |

### Decision

- no Discord- or Music Sesh-adjacent table should be part of the first Fitness profile cleanup mutation by default
- profile-core cleanup should only touch those tables later if a reviewed exact user/profile class makes it unavoidable

## Class 6: Data Classes Requiring Backup/Export Before Cleanup

The following classes require export before any mutation:

### Required export set

1. exact auth-only user rows selected for review
2. exact profile rows selected for review
3. auth/profile pairs for automation mismatches
4. member-number and `user_kind` state for any candidate profile
5. dependent core Fitness ownership for any candidate profile:
   - routines
   - sessions
   - progression events
   - custom exercises
6. dependent Discord/Music Sesh rows if any candidate profile or user touches:
   - member links
   - verification tokens
   - moderation cases
   - feedback reports
   - update drafts
   - Spotify/Music Sesh connection or room data

### Rollback posture

For any future mutation lane, rollback must explicitly support:

- auth row restore or re-enable path
- profile row restore
- member-number restore
- `user_kind` restore
- QA/LLEL visibility restore
- Discord member-link restore if touched
- Music Sesh connection/room restore if touched

## Mutation Approval Routing

### Requires explicit approval before mutation

- any auth deletion
- any profile deletion
- any profile merge
- any auth metadata retagging
- any Discord-linked row cleanup
- any Music Sesh row cleanup

### Likely safe first mutation shapes later, but still approval-gated

1. create missing profiles for a reviewed subset of signed-in auth-only users
2. tag reviewed automation mismatches as automation in auth metadata
3. delete the single never-signed-in auth-only row only after export and manual confirmation

## `.env.discord-worker` Dependency

Every cleanup class in this pass remains blocked by the current secret-path decision rule.

Reason:

- `repos/fawxzzy-fitness/.env.discord-worker` is still classified as secret-bearing repo-root residue
- no cleanup lane should normalize identities or move Discord-related Supabase state while that operator/runtime path remains ambiguous

Decision consequence:

- no first mutation pass should start until the secret-path lane explicitly clears this blocker or grants a narrow exception with receipt

## Recommended Next Package

Next clean package:

- `Fitness Supabase Profile/Data Hygiene Cleanup Plan 1`

That plan should still be docs-only and should name:

1. exact export artifact set
2. exact rollback steps
3. exact first mutation scope
4. exact approval gate
5. whether the first mutation is:
   - create missing profiles
   - auth metadata retag for automation
   - delete one never-signed-in auth-only user
   - or some narrower subset

Do not execute cleanup in that plan yet unless explicitly approved afterward.

## Non-Goals

This pass does not:

- delete any auth user
- create any profile
- merge any profile
- retag any auth metadata
- move Discord OS data
- change QA/LLEL code or docs

## Marker Interpretation

This package justifies:

- Fitness Supabase Profile/Data Hygiene: `20%`

It does not yet justify movement for:

- Operator Secret Path Hygiene
- Discord OS Infrastructure Separation
