# Discord OS Supabase Schema Landing Plan

Date: 2026-05-24
Lane: Discord OS Infrastructure Separation
Mode: docs-only planning
Status: first schema landing plan recorded

## Goal

Plan how the future DiscordOS Supabase project should receive Discord-owned runtime and workflow data without breaking the current Fitness-hosted Discord runtime, losing state continuity, or collapsing Fitness-owned identity and release-proof boundaries.

This pass does not:

- mutate either Supabase project
- create migrations
- create tables
- move data
- cut over the bot runtime
- post to Discord
- create `repos/DiscordOS`

## Target Future Project

- Supabase ref: `nwexsktuuenfdegzrbut`
- URL: `https://nwexsktuuenfdegzrbut.supabase.co`

Operational prep note only:

```txt
codex mcp add supabase --url https://mcp.supabase.com/mcp?project_ref=nwexsktuuenfdegzrbut
codex mcp login supabase
optional: npx skills add supabase/agent-skills
```

## Inputs

- `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-INVENTORY-2026-05-24.md`
- `docs/ops/DISCORD-OS-SHARED-CONTRACT-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/DISCORD-OS-ENV-RUNTIME-OWNERSHIP-MATRIX-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-DECISION-PASS-1-2026-05-24.md`

## Governing Rules

- Fitness remains canonical for Fitness auth, profiles, verification-token issuance, and release proof.
- DiscordOS later becomes canonical for Discord-first runtime/workflow state.
- No shared table should silently become dual-writer during separation.
- No live data should move until target schema, export posture, rollback posture, and cutover order are explicit.
- No bot runtime cutover happens in the schema lane.
- No Discord posting or workflow mutation happens from this lane.

## Current Posture

### Fitness currently hosts live Discord OS data

Current Discord- and Music Sesh-adjacent tables in Fitness Supabase:

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

### DiscordOS Supabase is healthy but empty

The current DiscordOS project exists, is healthy, and currently has no public tables.

Implication:

- this lane is designing the landing zone, not migrating into an already-live schema

## Schema Landing Classes

### 1. Tables / Classes That Move Later

These become DiscordOS-owned schema classes after the schema landing plan is implemented in a future lane.

| Class | Current table(s) in Fitness | Future owner | Why it moves |
| --- | --- | --- | --- |
| feedback runtime state | `discord_feedback_reports` | DiscordOS | feedback board, forum thread linkage, audit lifecycle, and card workflow are Discord-first operational state |
| moderation / cases / purgatory | `discord_moderation_cases` | DiscordOS | moderation runtime and community enforcement are Discord OS operations |
| update drafts / publish state | `discord_update_drafts` | DiscordOS | Discord publication draft state belongs with Discord runtime, while proof remains upstream in Fitness |
| bot dedupe / runtime command state | `discord_message_command_claims` | DiscordOS | this is pure bot operational state |
| Music Sesh runtime state | `discord_spotify_connections`, `discord_spotify_lobbies`, `discord_spotify_room_members`, `discord_spotify_queue_items` | DiscordOS | room, queue, provider connection, and playback orchestration are DiscordOS runtime concerns |

### 2. Tables / Classes That Stay Fitness-Owned

These do not land in DiscordOS as canonical truth.

| Class | Current location | Why it stays |
| --- | --- | --- |
| verification token issuance truth | `discord_verification_tokens` in Fitness | token issuance proves Fitness session/account ownership |
| Fitness auth data | `auth.users`, `auth.identities` | core Fitness account ownership |
| Fitness profile data | `public.profiles` | canonical Fitness identity, `user_number`, QA/LLEL visibility |
| Fitness release proof | Fitness repo/docs and deploy truth surfaces | Discord updates must consume proof, not replace it |
| core workout/product data | Fitness product tables | not Discord infrastructure |

### 3. Contract Tables / Keys

These seams need explicit contracts instead of blind table moves.

| Seam | Current surface | Planned posture |
| --- | --- | --- |
| verification bridge | `discord_verification_tokens` + verify consume flow | Fitness-owned token issuance and consume contract |
| Discord member/profile link | `discord_member_links` | explicit bridge contract; canonical owner remains to be enforced |
| member-number sync | `profiles.user_number` + member-link sync state | Fitness-owned source with DiscordOS read/sync contract |
| deploy-to-update handoff | deployment proof + `discord_update_drafts` linkage | Fitness proof upstream, DiscordOS draft/runtime downstream |

## Proposed DiscordOS Schema Domains

The future DiscordOS schema should be grouped by domain rather than copying Fitness’s mixed hosted layout blindly.

### Feedback domain

Planned landing scope:

- report identity
- reporter Discord identity
- reporter-kind metadata
- forum channel/thread/message linkage
- status and completion-review workflow metadata
- thread audit-support metadata
- attachment metadata pointers

Rule:

- retain existing report ids and public thread linkage where possible

### Moderation domain

Planned landing scope:

- moderation case ids
- subject Discord ids
- operator Discord ids
- purgatory timing/state
- warning/release history

Rule:

- preserve historical case ids and timestamps

### Update publication domain

Planned landing scope:

- draft ids
- source deployment identifiers
- user-facing copy fields
- publish/skip state
- published Discord message linkage

Rule:

- keep deploy proof external to the domain; only carry the required proof references

### Runtime command domain

Planned landing scope:

- message-command claim rows
- runtime idempotency markers
- later bot-process operational metadata only if required

Rule:

- treat this as service-role runtime state, not user-facing product data

### Music Sesh domain

Planned landing scope:

- provider connection records
- room/lobby records
- room membership
- queue items
- approval and playback-related state

Rule:

- preserve room, queue, and connection continuity as one domain; do not split these into independent ad hoc migrations

## Schema Landing Order

### Stage 1: schema design only

Design the future DiscordOS target schema without writing it.

Outputs expected from a later lane:

- table list
- column mapping
- canonical primary keys
- foreign-key plan where truly needed
- service-role/runtime access posture

### Stage 2: read-only dual-read proof

Before any row moves:

- prove that DiscordOS can read required Fitness-owned contract data without owning it
- prove that downstream runtime surfaces can map current Fitness rows to future DiscordOS shapes

This stage is still read-only.

### Stage 3: write-shadow if needed

Only if later required:

- a short-lived write-shadow or mirror phase may exist for selected move-later tables
- single canonical writer must remain explicit during any shadow period

Default rule:

- avoid dual-write unless a seam cannot be cut over safely any other way

### Stage 4: cutover

Only after schema, export, rollback, and runtime cutover planning are all approved:

- move canonical writer for a bounded table class
- retarget runtime reads/writes for that class
- verify continuity

### Stage 5: cleanup

Only after successful bounded cutover:

- retire old Fitness-hosted canonical writes for that moved class
- preserve required historical export artifacts

## RLS / Ownership Posture

### DiscordOS future posture

Expected default posture:

- tables in exposed schemas should have RLS enabled
- service-role-only operational tables should still be treated explicitly as operator/runtime-only surfaces
- runtime-owned tables should not silently inherit Fitness policy assumptions

### Fitness retained posture

- Fitness profile/auth surfaces remain governed by Fitness-side policy and app semantics

### Rule

- do not copy the current policy posture blindly
- design DiscordOS policies based on actual DiscordOS runtime ownership, not on current co-hosting shortcuts

## Export / Backup Posture

Before any future mutation or row movement:

### Required export classes

1. full class export for each move-later table class before first mutation
2. key-reference export for every contract seam touching Fitness-owned identity data
3. dependency export for any row set whose ids appear in public Discord threads or messages
4. cutover manifest naming:
   - table/class in scope
   - canonical writer before cutover
   - canonical writer after cutover
   - exact export artifact paths

### Export principle

- export by class and by cutover slice
- do not depend only on aggregate counts

## Rollback Posture

Each moved-later class must have rollback that answers:

- how to restore prior canonical writer
- how to restore rows from exports
- how to re-point runtime reads/writes
- how to preserve public Discord continuity if cutover fails

### Minimum rollback classes

| Class | Minimum rollback requirement |
| --- | --- |
| feedback runtime state | restore report rows and thread/message linkage mapping |
| moderation | restore case rows and active purgatory state |
| update drafts | restore draft rows and published-message linkage |
| message-command claims | restore runtime claim table and idempotency behavior |
| Music Sesh | restore connection, room, member, and queue state as a coherent runtime slice |

## No Live Mutation Rule

This lane does not authorize:

- table creation
- migration file creation
- row export execution
- row copy or delete
- contract table mutation

The schema landing plan is a prerequisite, not an approval packet.

## No Bot Runtime Cutover Rule

This lane does not authorize:

- worker retargeting
- Discord webhook URL change
- Vercel runtime split
- switching canonical readers/writers

Schema readiness and runtime cutover are separate lanes on purpose.

## No Discord Posting Rule

This lane does not authorize:

- update posts
- board sync announcements
- public Discord notices

Any future migration communication should happen only after cutover planning exists.

## First Safe Landing Sequence

1. shared contracts decided
2. env/runtime ownership mapped
3. schema landing plan written
4. runtime/Vercel cutover plan written
5. later approval-gated schema implementation lane
6. later approval-gated export and read-only proof lane
7. later bounded cutover lane by table class

## Recommended No-Move-Yet Conclusion

Do not create DiscordOS schema or migrations yet.
Do not export or move rows yet.
Do not cut over the bot runtime yet.

The next clean package after this is:

- `Discord OS Infrastructure Separation — Runtime/Vercel Cutover Plan`

## Marker Interpretation

This package justifies:

- Discord OS Infrastructure Separation: `40%`
- Dependency Untangling: `15%`

It does not justify:

- Supabase mutation
- data migration
- runtime cutover
- repo creation
