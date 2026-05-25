# Discord OS Shared Contract Decision Pass 1

Date: 2026-05-24
Lane: Discord OS Infrastructure Separation
Mode: docs-only decision pass
Status: first shared-contract seam routing recorded

## Goal

Define the explicit shared contract seams between Fitness and future DiscordOS before any repo creation, code movement, Supabase migration, env split, Vercel cutover, or runtime migration begins.

This pass does not:

- move code
- create `repos/DiscordOS`
- mutate either Supabase project
- mutate Vercel
- post to Discord
- restart the bot
- pull env
- print secrets
- change Fitness product code

## Inputs

- `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-INVENTORY-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-CLEANUP-PLAN-1-2026-05-24.md`
- `docs/ops/UNIFIED-DISCORD-OS-WORKFLOW-BOUNDARY-2026-05-24.md`
- `docs/ops/UNIFIED-RELEASE-DEPLOY-UPDATE-HANDOFF-2026-05-24.md`

## Governing Rules

- Fitness remains the canonical owner of Fitness account identity and core product data.
- DiscordOS should eventually own Discord runtime and Discord-first workflow state.
- No cross-system seam should rely on hidden shared tables by default once separation begins.
- No Discord publication should outrun Fitness proof or release-ledger evidence.
- Verification proves possession of a valid Fitness session, not just Discord presence.
- Music Sesh runtime continuity must survive separation without silently changing queue, room, or connection semantics.

## Shared Contract Decision Labels

- `move later`
- `stay and expose contract`
- `shared mirror later`
- `defer`

## Canonical Contract Posture

The first separation wave should prefer:

1. keep Fitness-owned identity and product truth in Fitness
2. move clearly Discord-owned operational state into DiscordOS later
3. expose narrow service or data contracts where DiscordOS must consume Fitness-owned truth
4. avoid mirrored truth unless a single canonical writer is still obvious

## Seam Matrix

| Seam | Current owner | Future owner | Data direction | Source of truth | Migration risk | Move data? | Contract choice | First safe migration step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| verification bridge | Fitness | split: Fitness issues, DiscordOS consumes | Fitness -> DiscordOS | Fitness | high | verification token history stays | `stay and expose contract` | define token-issue and token-consume contract |
| Discord member/profile link | Fitness | split | DiscordOS -> Fitness or shared lookup | Fitness for profile identity; link bridge explicit | high | no blind move | `stay and expose contract` first | define canonical link owner and lookup API |
| member-number sync | Fitness | split | Fitness -> DiscordOS | Fitness `profiles.user_number` | medium to high | no | `stay and expose contract` | define member-number read/sync contract |
| feedback card lifecycle | Fitness-hosted Discord OS | DiscordOS | DiscordOS internal, optional downstream exports | DiscordOS after migration | medium | yes, later | `move later` | define feedback export/import boundary and id continuity |
| updates / release-ledger handoff | Fitness | split | Fitness -> DiscordOS | Fitness release proof and ledger | medium | update drafts may move; ledger stays | `stay and expose contract` | define deployment-event and publish-draft contract |
| Spotify / Music Sesh runtime | Fitness-hosted Discord OS | DiscordOS | DiscordOS internal; provider callbacks may involve both | DiscordOS after migration for room/queue runtime | high | yes, later | `move later` with narrow Fitness callback contract if needed | define room/queue/connection contract and cutover invariants |
| moderation / cases / purgatory | Fitness-hosted Discord OS | DiscordOS | DiscordOS internal | DiscordOS after migration | medium | yes, later | `move later` | define moderation data ownership and minimal exports |
| Fitness-owned account/product data | Fitness | Fitness | Fitness -> DiscordOS on read-only needs | Fitness | high | no | `stay and expose contract` | name exact read-only identity surfaces DiscordOS can consume |
| DiscordOS-owned runtime/workflow data | Fitness-hosted Discord OS | DiscordOS | DiscordOS internal | DiscordOS after migration | medium | yes, later | `move later` | define target schema ownership before any row movement |
| shared IDs / immutable keys | mixed | split | bi-directional reference only | depends by seam | medium | no standalone move | `stay and expose contract` | freeze canonical ids and cross-system references |
| env / secret ownership | Fitness | split | none; ownership split | per-system | high | secrets split, not copied casually | `move later` by class | define exact Fitness-only, DiscordOS-only, and paired-secret lists |
| Vercel / runtime ownership | Fitness | split | Fitness proof -> DiscordOS publish/runtime | per service | high | project/runtime move later | `move later` with proof contract | define runtime cutover order and webhook boundary |

## 1. Verification Bridge

### Current owner

- Fitness issues verification tokens through authenticated app sessions
- Fitness currently consumes the verification token and writes the linked result in the same hosted stack

### Future owner

- Fitness should continue issuing verification tokens because token issuance proves Fitness account ownership
- DiscordOS should eventually own the Discord-facing verification runtime that consumes the proof and applies Discord-side behavior

### Data direction

- Fitness -> DiscordOS

### Source of truth

- Fitness for:
  - authenticated user identity
  - automation-account disallow rule
  - token issuance policy
- DiscordOS for:
  - Discord-side role grant workflow
  - Discord-side panel/runtime handling

### Decision

- `public.discord_verification_tokens` should stay Fitness-owned by default
- the bridge should become an explicit Fitness-issued token verification contract, not a duplicated token table

### First safe migration step

Define a contract for:

- Fitness token issue
- DiscordOS token consume request
- one-time consume result
- error/result codes
- no direct exposure of auth or token secrets across the seam

### Non-goals

- moving Fitness auth ownership
- duplicating token truth in both Supabase projects
- changing public verification UX in this pass

## 2. Discord Member / Profile Link

### Current owner

- `public.discord_member_links` lives in Fitness
- the link currently bridges Discord users to Fitness profile identity, member number, and sync status

### Future owner

- Fitness should remain canonical for profile identity
- the bridge itself should become explicit and governed, even if later stored or mirrored elsewhere

### Data direction

- mostly DiscordOS -> Fitness on new link events
- Fitness -> DiscordOS for profile readbacks and member-number context

### Source of truth

- Fitness for:
  - `fitness_user_id`
  - profile `user_kind`
  - `user_number`
- bridge ownership should stay single-writer

### Decision

- do not blindly move `discord_member_links` first
- treat it as a cross-system contract seam
- initial posture: `stay and expose contract`

### First safe migration step

Define:

- canonical row owner
- immutable keys:
  - `fitness_user_id`
  - `discord_user_id`
- write path for successful verification consumption
- read path for DiscordOS to fetch member context and nickname sync state

### Non-goals

- dual-write without a lock plan
- mirrored link truth without canonical owner

## 3. Member-Number Sync

### Current owner

- Fitness owns `profiles.user_number`
- Discord sync is best-effort and currently runs through Fitness-hosted routes

### Future owner

- Fitness keeps canonical numbering
- DiscordOS may eventually perform the Discord-side nickname sync action

### Data direction

- Fitness -> DiscordOS

### Source of truth

- Fitness `public.profiles.user_number`

### Decision

- no data move
- explicit read/sync contract only

### First safe migration step

Define contract for:

- reading `user_number`
- reading display-name components needed for nickname formatting
- reporting sync outcome/failure code back to canonical link state

### Non-goals

- moving `user_number` into DiscordOS
- making DiscordOS authoritative for member numbering

## 4. Feedback Card Lifecycle

### Current owner

- Fitness-hosted Discord OS runtime
- `public.discord_feedback_reports`

### Future owner

- DiscordOS should own this lifecycle and storage after migration

### Data direction

- DiscordOS internal after cutover
- optional downstream reviewed exports to ATLAS/Playbook or repo lanes

### Source of truth

- DiscordOS after migration

### Decision

- `discord_feedback_reports` is a move-later class
- this is not a shared long-term Fitness table

### First safe migration step

Define:

- immutable `report_id` continuity
- reporter kind mapping rules
- how existing board thread ids and message ids survive migration
- how reviewed board exports keep the same downstream format

### Non-goals

- changing card structure during separation
- changing public board workflow during this pass

## 5. Updates / Release-Ledger Handoff

### Current owner

- Fitness deploy webhook handling and `discord_update_drafts` live in Fitness
- release-ledger truth is already conceptually Fitness/repo-owned

### Future owner

- Fitness should remain canonical for deploy proof and release evidence
- DiscordOS should eventually own Discord publication drafting and posting

### Data direction

- Fitness -> DiscordOS

### Source of truth

- Fitness release ledger and deploy proof

### Decision

- release ledger stays Fitness-owned
- update publication/runtime can move later
- seam posture: `stay and expose contract`

### First safe migration step

Define contract for:

- deployment event payload normalization
- minimal release-proof fields DiscordOS needs
- draft creation idempotency
- publish-state callback if Fitness must retain audit visibility

### Non-goals

- moving Fitness release ledger into DiscordOS
- letting DiscordOS announce updates without Fitness proof

## 6. Spotify Club / Music Sesh Data Boundary

### Current owner

- Fitness-hosted Discord OS runtime
- `discord_spotify_connections`
- `discord_spotify_lobbies`
- `discord_spotify_room_members`
- `discord_spotify_queue_items`

### Future owner

- DiscordOS should own Music Sesh runtime/workflow state

### Data direction

- mostly DiscordOS internal after cutover
- possible narrow Fitness callback for app-account-linked actions only if still needed

### Source of truth

- DiscordOS after migration for:
  - room state
  - membership
  - queue state
  - provider connection state related to Discord identity

### Decision

- move later
- do not keep these as hidden Fitness tables long-term

### First safe migration step

Define invariants that must survive:

- active room continuity
- queue ordering semantics
- approval history semantics
- Spotify connection uniqueness by `discord_user_id`
- no duplicate room/member/queue writers during cutover

### Non-goals

- redesigning Music Sesh product behavior
- changing Spotify OAuth scope policy in this pass

## 7. Moderation / Cases / Purgatory Boundary

### Current owner

- Fitness-hosted Discord OS moderation flow
- `discord_moderation_cases`

### Future owner

- DiscordOS

### Data direction

- DiscordOS internal after migration

### Source of truth

- DiscordOS after migration

### Decision

- move later
- no strong reason to keep moderation-case truth in Fitness long-term

### First safe migration step

Define:

- immutable case id continuity
- channel/role dependencies
- purgatory release lifecycle
- minimum export artifact needed before row movement

### Non-goals

- changing moderation policy
- expanding moderator powers during separation

## 8. Fitness-Owned Account / Product Data

### Current owner

- Fitness

### Future owner

- Fitness

### Data direction

- Fitness -> DiscordOS only when DiscordOS needs identity or proof

### Source of truth

- Fitness

### Decision

- keep in Fitness
- expose minimal contracts only

### First safe migration step

Name the exact allowed cross-system reads:

- verification eligibility
- user/profile identity summary needed for member linking
- member number and display-name sync inputs
- release-proof/update inputs

### Non-goals

- copying Fitness app data into DiscordOS
- using DiscordOS as a second user-profile system

## 9. DiscordOS-Owned Runtime / Workflow Data

### Current owner

- Fitness-hosted Discord OS runtime

### Future owner

- DiscordOS

### Data direction

- DiscordOS internal

### Source of truth

- DiscordOS after migration

### Decision

- move later
- define target schema first, then row movement plan

### First safe migration step

Create a follow-on docs-only schema landing plan for:

- feedback
- updates
- moderation
- message-command claims
- Music Sesh tables

### Non-goals

- row export/import in this pass
- creating DiscordOS tables yet

## 10. Shared IDs And Immutable Keys

### Required immutable references

- Fitness user id
- Discord user id
- feedback report id
- update draft id or deployment id linkage
- moderation case id
- Music Sesh lobby id / room slug policy
- Discord channel/thread/message ids where already public-facing

### Decision

- ids should remain stable across migration
- cross-system references should prefer immutable ids over mutable names or titles

### First safe migration step

Publish an id-policy appendix in the later cutover planning lane that freezes:

- canonical ids
- allowed derived aliases
- non-authoritative display names

### Non-goals

- renaming ids during migration
- changing public report ids or room slugs casually

## 11. Env / Secret Ownership

### Future Fitness-owned classes

- Fitness auth/session secrets
- Fitness Supabase keys
- verification-token issuance secrets, unless intentionally split
- Fitness release/deploy proof secrets

### Future DiscordOS-owned classes

- Discord bot app secrets
- Discord guild/channel/role ids
- DiscordOS Supabase keys
- Music Sesh runtime/provider secrets
- Discord publication/runtime secrets

### Paired or service-to-service classes

- verification consume authorization
- member-sync authorization
- any release-proof handoff auth secret

### Decision

- secret split must follow owner split
- no repo should carry the other system’s runtime secrets by default once separation lands

### First safe migration step

Create a later env ownership matrix with:

- owner system
- secret class
- runtime consumer
- whether paired or single-owner

### Non-goals

- rotating or moving secrets in this pass
- pulling env

## 12. Vercel / Runtime Ownership

### Current owner

- Fitness Vercel project hosts:
  - Discord interaction route
  - verification token consume route
  - deployment webhook route
  - Music Sesh interaction runtime
- worker targets Fitness `/api/discord/interactions`

### Future owner

- Fitness keeps app/runtime for app-facing product surfaces
- DiscordOS should eventually own Discord interaction runtime and Discord publication/runtime surfaces

### Data direction

- Fitness -> DiscordOS for release proof and certain identity seams

### Source of truth

- runtime ownership split by system, not by convenience

### Decision

- move later
- no shared forever-hosting assumption

### First safe migration step

Write a later cutover sequence for:

1. contract-ready dual-boundary state
2. DiscordOS Vercel project creation/linking
3. webhook and worker target cutover
4. post-cutover verification

### Non-goals

- changing live webhook URLs now
- moving worker target now
- deploying a DiscordOS project now

## First Safe Migration Order

1. shared-contract seams documented and accepted
2. env ownership matrix documented
3. DiscordOS schema landing plan documented
4. Vercel/runtime cutover plan documented
5. local repo creation and code extraction plan
6. data migration plan
7. runtime cutover plan

## Recommended No-Move-Yet Conclusion

Do not create `repos/DiscordOS` yet.
Do not move Supabase tables yet.
Do not split Vercel runtime yet.

The next clean packages after this decision pass should be:

1. `Discord OS Infrastructure Separation — Env Ownership Matrix`
2. `Discord OS Infrastructure Separation — Supabase Schema Landing Plan`
3. `Discord OS Infrastructure Separation — Runtime/Vercel Cutover Plan`

## Marker Interpretation

This package justifies:

- Discord OS Infrastructure Separation: `20%`
- Dependency Untangling: `5%`

It does not yet justify:

- repo creation
- data migration
- code extraction
- Vercel cutover
- bot runtime cutover
