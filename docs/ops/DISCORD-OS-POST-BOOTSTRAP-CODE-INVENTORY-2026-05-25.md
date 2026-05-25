# DiscordOS Post-Bootstrap Code Inventory

Date: 2026-05-25
Lane: Discord OS Infrastructure Separation
Mode: inventory only
Status: post-bootstrap code surface inventory recorded

## Goal

Identify the exact Fitness-hosted DiscordOS code surfaces that are candidates for later extraction into `repos/DiscordOS` now that the canonical local repo surface exists.

This pass does not:

- move code
- copy Fitness code into `repos/DiscordOS`
- mutate Supabase
- mutate Vercel
- post to Discord
- restart the bot
- pull env
- print secrets
- change Fitness behavior

## Inputs

- `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-INVENTORY-2026-05-24.md`
- `docs/ops/DISCORD-OS-SHARED-CONTRACT-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/DISCORD-OS-ENV-RUNTIME-OWNERSHIP-MATRIX-2026-05-24.md`
- `docs/ops/DISCORD-OS-SUPABASE-SCHEMA-LANDING-PLAN-2026-05-24.md`
- `docs/ops/DISCORD-OS-RUNTIME-VERCEL-CUTOVER-PLAN-2026-05-24.md`
- `docs/ops/DISCORD-OS-REPO-BOOTSTRAP-RECEIPT-2026-05-25.md`
- `repos/fawxzzy-fitness/src/app/api/discord/**`
- `repos/fawxzzy-fitness/src/app/api/vercel/deployment-webhook/route.ts`
- `repos/fawxzzy-fitness/src/lib/discord/**`
- `repos/fawxzzy-fitness/src/lib/spotify/**`
- `repos/fawxzzy-fitness/scripts/**`
- `repos/fawxzzy-fitness/src/lib/env.ts`
- `repos/DiscordOS/**`

## Current Posture

- `repos/DiscordOS` now exists as the governed local landing surface, but it is still scaffold-only.
- All live Discord interaction, feedback, moderation, update-draft, and Music Sesh behavior still runs from `repos/fawxzzy-fitness`.
- The main extraction challenge is not file count; it is that Discord runtime, Fitness-owned identity seams, Spotify runtime, and Vercel update ingestion are still bundled inside one Fitness-hosted route and one Fitness env surface.

## Classification Labels

- `move later`
- `stay Fitness`
- `shared contract`
- `manual review`

## Surface Inventory

| Surface | Current path | Current owner | Future owner candidate | Classification | Key dependencies | Migration risk | First safe extraction package | No-move-yet reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Discord interaction runtime | `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts` | Fitness-hosted Discord runtime | DiscordOS | `move later` | `src/lib/discord/**`, `src/lib/spotify/**`, `src/lib/env.ts`, Discord REST, Fitness Supabase tables | High | split route by domain handlers before any repo copy | still bundles feedback, moderation, updates, verification consume, message commands, and Music Sesh in one host seam |
| Gateway worker | `repos/fawxzzy-fitness/scripts/discord-feedback-gateway-worker.mjs` | Fitness-hosted Discord runtime | DiscordOS | `move later` | Fitness interaction route, governed root secrets lane, Discord gateway, runtime state file, message-command poll secret | High | extract worker/runtime config layer without retargeting host | worker still points at Fitness `/api/discord/interactions` and encodes current host assumptions |
| Feedback lifecycle library | `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts` | Fitness-hosted Discord runtime | DiscordOS | `move later` | `discord_feedback_reports`, `discord_member_links`, Discord thread/message ids, feedback emoji formatting | High | extract pure report model/formatter layer first, then persistence layer | depends on Fitness-hosted DB tables plus current forum/public card continuity |
| Update draft library | `repos/fawxzzy-fitness/src/lib/discord/update-drafts.ts` | Fitness-hosted Discord runtime | DiscordOS for publish runtime; Fitness for proof source | `shared contract` | `discord_update_drafts`, Discord message posting, Vercel project identity, Fitness deployment proof | Medium | split Fitness proof-ingest contract from Discord publish runtime | publish runtime can move later, but deploy proof and project identity stay upstream in Fitness |
| Moderation library | `repos/fawxzzy-fitness/src/lib/discord/moderation.ts` | Fitness-hosted Discord runtime | DiscordOS | `move later` | `discord_moderation_cases`, `discord_member_links`, guild/role/channel ops, purgatory infra | High | isolate moderation case storage + Discord action adapters | active case continuity and purgatory role/channel semantics must survive cutover intact |
| Message-command claim library | `repos/fawxzzy-fitness/src/lib/discord/message-command-claims.ts` | Fitness-hosted Discord runtime | DiscordOS | `move later` | `discord_message_command_claims` | Low | extract as standalone runtime persistence module | small surface, but still tied to current Supabase host |
| Discord REST helpers | `repos/fawxzzy-fitness/src/lib/discord/rest.ts` | Fitness-hosted Discord runtime | DiscordOS | `move later` | Discord bot token/app ids, guild/channel/message operations | Medium | extract transport layer with env adapter boundary | should move with Discord runtime, not before |
| Interaction payload builders/constants | `repos/fawxzzy-fitness/src/lib/discord/interactions.ts` | Fitness-hosted Discord runtime | DiscordOS | `move later` | command names, custom ids, embed builders, permission helpers | Medium | extract command/component constants and response builders | still referenced by the monolithic Fitness interaction route |
| Feedback emoji helpers | `repos/fawxzzy-fitness/src/lib/discord/feedback-emojis.ts` | Fitness-hosted Discord runtime | DiscordOS | `move later` | Discord emoji ids from Fitness env | Low | fold into feedback extraction package | ownership follows feedback runtime, but env still lives in Fitness today |
| Server inventory / doctor helpers | `repos/fawxzzy-fitness/src/lib/discord/server-inventory.ts`, `repos/fawxzzy-fitness/scripts/doctor-discord-community.mjs`, `repos/fawxzzy-fitness/scripts/discord-server-inventory.mjs` | Fitness-hosted Discord operations | DiscordOS | `move later` | Discord REST, current Fitness table inventory, env ids | Medium | extract Discord ops/doctor package after core runtime split is defined | still assumes Fitness-hosted table layout and current env ownership |
| Verification token issue route | `repos/fawxzzy-fitness/src/app/api/discord/verification-token/route.ts` | Fitness | Fitness | `stay Fitness` | `requireUser`, `ensureProfile`, `discord_verification_tokens`, Fitness auth/session | High | none in DiscordOS lane | token issuance proves Fitness account ownership and is tied to authenticated Fitness app sessions |
| Verification consume route | `repos/fawxzzy-fitness/src/app/api/discord/verify/route.ts` | Fitness-hosted Discord runtime | split: Fitness issues, DiscordOS consumes later | `shared contract` | `DISCORD_VERIFICATION_BOT_SECRET`, `consume_discord_verification_token`, Fitness Supabase RPC | High | define service contract for consume request/response first | current route is the seam between Fitness-issued proof and Discord-side role behavior |
| Verification consume helper | `repos/fawxzzy-fitness/src/lib/discord/verification-server.ts` | Fitness-hosted Discord runtime | split | `shared contract` | `consume_discord_verification_token` RPC, Discord user normalization | Medium | promote to seam contract shape rather than direct cross-host DB assumption | should back a contract, not an unbounded table copy |
| Member link persistence | `repos/fawxzzy-fitness/src/lib/discord/member-links.ts` | Fitness | split | `shared contract` | `upsert_discord_member_link` RPC, `discord_member_links` | High | define canonical write/read contract and immutable key policy | profile identity remains Fitness-owned even if Discord runtime moves |
| Member number formatter and sync route | `repos/fawxzzy-fitness/src/lib/discord/member-number.ts`, `repos/fawxzzy-fitness/src/app/api/discord/member-numbers/sync/route.ts`, `repos/fawxzzy-fitness/scripts/sync-discord-member-numbers.mjs` | Fitness-hosted bridge | split | `shared contract` | `profiles.user_number`, `discord_member_links`, Discord nickname writes, member-sync secret | High | define Fitness-read / Discord-write sync seam | numbering remains canonical in Fitness, so this should not move as standalone Discord truth |
| Vercel deployment webhook ingest | `repos/fawxzzy-fitness/src/app/api/vercel/deployment-webhook/route.ts` | Fitness | split | `shared contract` | `VERCEL_DEPLOYMENT_WEBHOOK_SECRET`, `VERCEL_PROJECT_ID`, `upsertDiscordUpdateDraftFromVercelEvent` | Medium | split normalized deploy-proof event contract from downstream draft publishing | current webhook is proof-ingest, not purely Discord runtime |
| Spotify lobby state | `repos/fawxzzy-fitness/src/lib/spotify/lobbies.ts` | Fitness-hosted Music Sesh runtime | DiscordOS | `move later` | `discord_spotify_lobbies`, panel message ids, approval mode, mirror flags | High | extract lobby state domain as first Music Sesh slice | Music Sesh must move as one bounded runtime slice, not scattered table-by-table |
| Spotify room membership | `repos/fawxzzy-fitness/src/lib/spotify/room-members.ts` | Fitness-hosted Music Sesh runtime | DiscordOS | `move later` | `discord_spotify_room_members`, lobby state | High | keep with Music Sesh domain extraction | room continuity and host/member semantics cannot be split from lobby/queue state |
| Spotify queue state | `repos/fawxzzy-fitness/src/lib/spotify/queue.ts` | Fitness-hosted Music Sesh runtime | DiscordOS | `move later` | `discord_spotify_queue_items`, lobby state, provider connection state | High | keep with Music Sesh domain extraction | queue ordering and approval semantics need one canonical runtime owner |
| Spotify connection/token state | `repos/fawxzzy-fitness/src/lib/spotify/tokens.ts`, `repos/fawxzzy-fitness/src/lib/spotify/oauth.ts`, `repos/fawxzzy-fitness/src/lib/spotify/crypto.ts` | Fitness-hosted Music Sesh runtime | DiscordOS with narrow callback/contract review | `manual review` | `discord_spotify_connections`, Spotify OAuth env, token encryption, redirect URI | High | extract provider-state contract after schema landing plan is implemented | secret ownership and OAuth callback design still need explicit cutover decisions |
| Spotify playback/search/mirror orchestration | `repos/fawxzzy-fitness/src/lib/spotify/player.ts`, `repos/fawxzzy-fitness/src/lib/spotify/search.ts`, `repos\fawxzzy-fitness\src\lib\spotify\mirror.ts`, `repos\fawxzzy-fitness\src\lib\spotify\profile.ts` | Fitness-hosted Music Sesh runtime | DiscordOS | `move later` | Spotify provider env, lobby/queue/connection state | High | move only with the rest of Music Sesh runtime | still coupled to current Fitness-hosted state and bot interaction handlers |
| Discord testing/setup/export scripts | `repos/fawxzzy-fitness/scripts/setup-discord-testing-board.mjs`, `sync-feedback-forum-posts.mjs`, `sync-feedback-resolved-reactions.mjs`, `export-feedback-board.mjs`, `export-discord-bug-reports.mjs`, `generate-feedback-task-packets.mjs`, `bootstrap-discord-emojis.mjs`, `discord-noise-*`, `release-expired-purgatory-cases.mjs`, `cleanup-spotify-club-channel.mjs` | Fitness-hosted Discord operations | DiscordOS later, some ATLAS/manual review | `manual review` | current Fitness table layout, current Discord runtime env, operational receipts | Medium | inventory by script family after core runtime extraction boundaries are landed | many are ops/repair/export tools and should not be copied blindly before runtime ownership is settled |
| Environment ownership surface | `repos/fawxzzy-fitness/src/lib/env.ts` | Fitness | split by class | `manual review` | Fitness auth env, Discord runtime env, Vercel webhook env, Spotify OAuth env | High | create post-bootstrap env-split implementation package, not repo copy | current file intentionally centralizes mixed ownership and cannot be transplanted as-is |

## Current Route And Runtime Bundling

The largest extraction pressure remains concentrated in one surface:

- `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`

That route currently imports and coordinates:

- feedback lifecycle helpers
- update publish/draft helpers
- moderation helpers
- member-link and member-number helpers
- verification consume helper
- Discord REST transport
- Spotify lobby, queue, room-member, player, search, token, and mirror helpers

Implication:

- the first extraction package should not be "copy the route"
- the first extraction package should split the route into domain-owned handler surfaces inside Fitness first or otherwise define equivalent bounded extraction seams before any move

## Current Database Coupling

Current Fitness-hosted table usage observed from the candidate surfaces:

| Domain | Current Fitness table(s) |
| --- | --- |
| feedback | `discord_feedback_reports` |
| update publication draft state | `discord_update_drafts` |
| moderation | `discord_moderation_cases` |
| verification token issue/consume | `discord_verification_tokens` |
| command dedupe | `discord_message_command_claims` |
| identity bridge | `discord_member_links` |
| Music Sesh connections | `discord_spotify_connections` |
| Music Sesh lobbies | `discord_spotify_lobbies` |
| Music Sesh room membership | `discord_spotify_room_members` |
| Music Sesh queue | `discord_spotify_queue_items` |

## Current Vercel And Host Assumptions

Observed current host assumptions that block blind extraction:

- the gateway worker resolves its poll URL to the current Fitness production URL by default
- the current worker still assumes one live interaction target at Fitness `/api/discord/interactions`
- update-draft ingestion is currently tied to Fitness Vercel deployment events
- the mixed env surface in `src/lib/env.ts` still co-locates:
  - Fitness auth and Supabase
  - Discord runtime env
  - Vercel deployment webhook env
  - Spotify OAuth/runtime env

## Recommended First Extraction Order

Do not start with Music Sesh or verification.

Recommended first bounded extraction order:

1. Discord runtime inventory split inside the current interaction route
   - identify feedback handlers, update handlers, moderation handlers, verification-consume handlers, and Music Sesh handlers as separate domains
2. extract low-risk DiscordOS-owned pure runtime modules
   - message-command claims
   - Discord REST transport
   - interaction constants/builders that are not Fitness-owned seams
3. extract feedback runtime domain
   - feedback lifecycle
   - panel/forum sync helpers
   - feedback export/ops scripts by family
4. extract update publication runtime
   - keep Fitness deployment proof upstream
5. extract moderation runtime
6. move Music Sesh as one bounded runtime slice
7. leave verification token issue and Fitness profile/member-number truth in Fitness

## First Safe Extraction Packages

### Package A: Discord route decomposition inventory

Goal:

- decompose the monolithic interaction route into named domain handler slices without changing runtime behavior

Likely result:

- a clearer extraction map for:
  - feedback
  - updates
  - moderation
  - verification consume
  - Music Sesh
  - message commands

### Package B: DiscordOS core runtime utility extraction

Goal:

- extract the lowest-risk DiscordOS-owned helpers first:
  - `src/lib/discord/rest.ts`
  - `src/lib/discord/message-command-claims.ts`
  - selected response/constant builders from `src/lib/discord/interactions.ts`

### Package C: Feedback runtime extraction

Goal:

- move the feedback lifecycle into DiscordOS after Package A proves the route seam and Package B proves the new repo landing pattern

## Explicit No-Move-Yet Conclusions

Do not move yet:

- `src/app/api/discord/verification-token/route.ts`
- `src/app/api/discord/verify/route.ts`
- `src/app/api/discord/member-numbers/sync/route.ts`
- `src/app/api/vercel/deployment-webhook/route.ts`
- Spotify OAuth/token/provider code as a standalone slice
- the monolithic interaction route as a wholesale file copy

Reason:

- each of those still depends on a Fitness-owned or shared-contract seam that is not yet implemented as an explicit cross-system boundary

## Result

`repos/DiscordOS` now has a post-bootstrap extraction inventory that is specific enough to drive bounded implementation packages later without falling back to vague "move Discord code out of Fitness" intent.

## Marker Interpretation

This package justifies:

- Discord OS Infrastructure Separation: `80%`
- Dependency Untangling: `50%`
- Inventory & Truth Map: `35%`

It does not justify:

- code movement
- schema mutation
- Vercel mutation
- bot runtime cutover
- Fitness behavior change
