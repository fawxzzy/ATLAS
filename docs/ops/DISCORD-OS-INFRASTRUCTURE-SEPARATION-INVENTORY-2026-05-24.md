# Discord OS Infrastructure Separation Inventory

Date: 2026-05-24
Lane: Discord OS Infrastructure Separation
Mode: inventory only
Status: baseline separation inventory recorded

## Goal

Map how Discord OS can separate from the current Fitness-hosted stack into governed infrastructure surfaces without losing runtime state, breaking live Discord behavior, or silently severing Fitness-facing identity and release contracts.

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

## Canonical Future Surfaces

- GitHub repo: `https://github.com/fawxzzy/DiscordOS.git`
- local target repo: `repos/DiscordOS`
- Supabase project: `DiscordOS`
- Supabase ref: `nwexsktuuenfdegzrbut`
- Supabase URL: `https://nwexsktuuenfdegzrbut.supabase.co`

## Inputs

- `docs/ops/UNIFIED-DISCORD-OS-WORKFLOW-BOUNDARY-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-CLEANUP-PLAN-1-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-UPDATES.md`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-VERIFICATION.md`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-SPOTIFY-CLUB.md`
- `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`
- `repos/fawxzzy-fitness/src/app/api/discord/verification-token/route.ts`
- `repos/fawxzzy-fitness/src/app/api/discord/verify/route.ts`
- `repos/fawxzzy-fitness/scripts/discord-feedback-gateway-worker.mjs`
- `repos/fawxzzy-fitness/src/lib/discord/**`
- `repos/fawxzzy-fitness/src/lib/spotify/**`
- read-only Supabase project inspection for:
  - Fitness: `lpswxoyfniocuhljgzbc`
  - DiscordOS: `nwexsktuuenfdegzrbut`

## High-Level Findings

1. Discord OS is currently a Fitness-hosted runtime, not just a bot pointed at a Fitness webhook.
   The main Discord interaction route, gateway worker, feedback logic, update drafting, verification handling, moderation, and Music Sesh logic all live in `repos/fawxzzy-fitness`.

2. Fitness Supabase currently holds all live Discord OS operational tables.
   The Fitness project contains the full Discord feedback, verification, moderation, update-draft, message-claim, and Music Sesh state surface.

3. The new DiscordOS Supabase project exists and is healthy, but it is currently empty.
   Read-only inspection of `nwexsktuuenfdegzrbut` returned no public tables yet.

4. Not every Discord-adjacent surface should move.
   Fitness account-bound identity surfaces such as Discord verification token generation and Fitness profile numbering should remain Fitness-owned or become explicit cross-system contracts, not silent table copies.

5. The largest current technical blocker is not data export.
   It is architectural coupling inside the Fitness route and env model, where Discord feedback, verification, moderation, updates, and Music Sesh are all wired through one Fitness-hosted runtime seam.

## Current Hosted Shape

### Runtime and webhook ownership today

| Surface | Current owner | Current location | Current dependency |
| --- | --- | --- | --- |
| Discord interaction webhook | Fitness | `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts` | Fitness Vercel project |
| Discord gateway worker | Fitness | `repos/fawxzzy-fitness/scripts/discord-feedback-gateway-worker.mjs` | calls Fitness `/api/discord/interactions` |
| Discord request signature verification | Fitness | `repos/fawxzzy-fitness/src/lib/discord/interaction-signature.ts` | Discord app secret material in Fitness env |
| Verification token generation | Fitness | `repos/fawxzzy-fitness/src/app/api/discord/verification-token/route.ts` | authenticated Fitness user session + Fitness Supabase |
| Verification token consume endpoint | Fitness | `repos/fawxzzy-fitness/src/app/api/discord/verify/route.ts` | Fitness Supabase + verification secret |
| Update draft ingest | Fitness | `repos/fawxzzy-fitness/src/app/api/vercel/deployment-webhook/route.ts` | Fitness Vercel production deployment events |
| Music Sesh public panel and controls | Fitness | `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts` + `src/lib/spotify/**` | Fitness Vercel + Fitness Supabase + Spotify env |

### Supabase project posture today

| Project | Ref | Status | Region | Current role in this lane |
| --- | --- | --- | --- | --- |
| FawxzzyFitness | `lpswxoyfniocuhljgzbc` | `ACTIVE_HEALTHY` | `us-west-2` | current live Discord OS database host |
| DiscordOS | `nwexsktuuenfdegzrbut` | `ACTIVE_HEALTHY` | `us-east-1` | future target database, currently empty |

## 1. Code That Belongs In Discord OS

These surfaces are Discord-first workflow/runtime code and should not remain Fitness-owned by default long-term.

| Code surface | Why it belongs in Discord OS |
| --- | --- |
| `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts` | feedback board storage, forum rendering, thread audit history, completion-review sync, and card formatting are Discord workflow concerns |
| `repos/fawxzzy-fitness/src/lib/discord/update-drafts.ts` | update drafting and Discord publication are community-release surfaces, not Fitness product-core logic |
| `repos/fawxzzy-fitness/src/lib/discord/moderation.ts` | purgatory, warning, and moderation case handling are Discord community operations |
| `repos/fawxzzy-fitness/src/lib/discord/rest.ts` | Discord API transport belongs with the Discord runtime layer |
| `repos/fawxzzy-fitness/src/lib/discord/server-inventory.ts` | Discord server diagnostics are Discord OS operations |
| `repos/fawxzzy-fitness/src/lib/discord/message-command-claims.ts` | bot command dedupe is runtime bot state |
| most Discord interaction command handlers inside `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts` | command menus, feedback setup, update publish, moderation, and Music Sesh controls are Discord OS interaction surfaces |
| `repos/fawxzzy-fitness/scripts/discord-feedback-gateway-worker.mjs` | this is the always-on Discord runtime worker and should leave Fitness-hosted default ownership |
| `repos/fawxzzy-fitness/scripts/doctor-discord-community.mjs` | community doctor flow is Discord operations, not Fitness app runtime |
| `repos/fawxzzy-fitness/scripts/setup-discord-testing-board.mjs` and forum sync/export helpers | these are Discord feedback operations and migrations around a Discord board surface |
| `repos/fawxzzy-fitness/src/lib/spotify/lobbies.ts` | Music Sesh room-state ownership is a Discord OS product/runtime concern |
| `repos/fawxzzy-fitness/src/lib/spotify/room-members.ts` | room membership is Discord/Music Sesh state |
| `repos/fawxzzy-fitness/src/lib/spotify/queue.ts` | Discord-owned queue state is Music Sesh runtime logic |
| `repos/fawxzzy-fitness/src/lib/spotify/mirror.ts` | Spotify mirror behavior is Music Sesh runtime orchestration |
| `repos/fawxzzy-fitness/src/lib/spotify/tokens.ts` | Discord-side Spotify connection state is not a Fitness workout-core concern |
| `repos/fawxzzy-fitness/src/lib/spotify/search.ts` and `player.ts` | Music Sesh provider orchestration belongs with the Discord OS runtime |

## 2. Code That Should Remain Fitness-Owned

These surfaces are still Fitness app, account, or core product concerns and should not be extracted by default.

| Code surface | Why it should remain Fitness-owned |
| --- | --- |
| `repos/fawxzzy-fitness/src/app/api/discord/verification-token/route.ts` | token generation requires an authenticated Fitness app session and reflects Fitness account ownership |
| Fitness account settings UI that tells users to use `Settings -> Account -> Discord Connector` | this is Fitness product UX |
| `repos/fawxzzy-fitness/src/lib/profile*` and `public.profiles` ownership logic | Fitness profiles, `user_number`, QA/LLEL visibility, and human/automation identity remain core Fitness concerns |
| core workout and progression tables (`sessions`, `sets`, `routines`, `exercises`, `exercise_stats`, `progression_events`) | unrelated to Discord infrastructure separation |
| QA/LLEL scripts and reusable QA-user flows | these are Fitness product verification lanes |
| Fitness auth/session gating such as `requireUser`, `ensureProfile`, and profile-core repair logic | these remain app-owned identity logic |

## 3. Code That Should Become Shared Contract Or Library

These surfaces are currently embedded in Fitness but should become explicit cross-system seams rather than staying hidden coupling.

| Surface | Why it should become a contract |
| --- | --- |
| `repos/fawxzzy-fitness/src/app/api/discord/verify/route.ts` | Discord runtime needs to consume Fitness-issued verification tokens, but the token truth and account proof should stay tied to Fitness auth |
| `repos/fawxzzy-fitness/src/lib/discord/member-links.ts` | durable Discord-to-Fitness identity linking should remain explicit even if the Discord runtime moves |
| member-number sync path `src/app/api/discord/member-numbers/sync/route.ts` | Discord nickname sync depends on Fitness `profiles.user_number`; this should become a governed service contract |
| release/update handoff from Fitness deployment events to Discord publication | Discord release narration depends on Fitness deploy truth, but should not require Discord publication logic to stay inside Fitness |
| shared type definitions for feedback exports, update drafts, and verification payloads | these are safer as contract types than as implicit route-local shapes |

## 4. Data That Should Move To DiscordOS Supabase

These tables are Discord OS operational state and should not stay in Fitness by default once separation begins.

| Table | Why it should move |
| --- | --- |
| `public.discord_feedback_reports` | community board state, forum linkage, and card lifecycle are Discord OS workflow data |
| `public.discord_update_drafts` | Discord publication draft state is OS-owned release narration data |
| `public.discord_moderation_cases` | community moderation records belong with Discord ops |
| `public.discord_message_command_claims` | runtime command dedupe is bot operational state |
| `public.discord_spotify_connections` | Music Sesh provider link state is Discord OS product/runtime data |
| `public.discord_spotify_lobbies` | room state belongs with Music Sesh runtime ownership |
| `public.discord_spotify_room_members` | room membership is Music Sesh operational state |
| `public.discord_spotify_queue_items` | queue history and queue authority are Music Sesh runtime state |

## 5. Data That Should Remain In Fitness Supabase

These surfaces are still Fitness-core product or account truth.

| Table/class | Why it should remain |
| --- | --- |
| `auth.users` and `auth.identities` for Fitness sign-in | canonical Fitness account ownership |
| `public.profiles` | canonical Fitness identity, `user_number`, QA/LLEL visibility, and automation classification |
| core workout/product tables | not Discord infrastructure |
| app session and auth policy surfaces | remain Fitness-owned |

## 6. Data Requiring Explicit Cross-System Contract

These are the most important non-obvious boundaries. They should not be copied or moved casually.

| Table/class | Recommended boundary |
| --- | --- |
| `public.discord_verification_tokens` | remain Fitness-owned or become a tightly scoped Fitness-issued token service; do not move blindly |
| `public.discord_member_links` | treat as a cross-system identity bridge; either keep canonical in Fitness or introduce an explicit mirrored contract with one source of truth |
| `public.profiles.user_number` used for nickname/member sync | Fitness remains canonical source; DiscordOS consumes |
| deployment metadata that drives updates publication | Fitness deploy/release truth upstream, DiscordOS publication downstream |
| any future shared product feedback taxonomy | needs a declared contract if DiscordOS hosts multi-product boards |

## 7. Env / Secrets That Must Move Or Be Split

### Likely DiscordOS-owned env and secret classes

- `DISCORD_BOT_TOKEN`
- `DISCORD_PUBLIC_KEY`
- `DISCORD_APPLICATION_ID`
- `DISCORD_GUILD_ID`
- channel and role IDs for:
  - feedback
  - updates
  - verify
  - main
  - moderation and purgatory
  - Music Sesh
- `DISCORD_MESSAGE_COMMAND_POLL_SECRET` or its future replacement
- `CRON_SECRET` when still used for fallback polling
- DiscordOS Supabase URL, publish key, and service-role secret
- Spotify runtime secrets when Music Sesh moves:
  - `SPOTIFY_CLIENT_ID`
  - `SPOTIFY_CLIENT_SECRET`
  - `SPOTIFY_REDIRECT_URI`
  - `SPOTIFY_TOKEN_ENCRYPTION_KEY`
  - `SPOTIFY_OAUTH_STATE_SECRET`
- Vercel webhook secret for Discord publication/update ingestion if the update bot moves

### Likely Fitness-owned env and secret classes

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Fitness service-role auth for Fitness app operations
- Fitness auth/session secrets
- `DISCORD_VERIFICATION_TOKEN_PEPPER` if verification token issuance stays Fitness-owned

### Shared contract or paired-secret classes

- `DISCORD_VERIFICATION_BOT_SECRET`
- `DISCORD_MEMBER_SYNC_SECRET`
- any future service-to-service auth secret between Fitness and DiscordOS

### Remaining blockers and residue from hygiene lanes

- `secrets/local/spotify-club-prod.env` still preserves legacy naming/coupling and should be reviewed during separation planning
- repo-local `.vercel/.env*.local` residue in other repos is broader hygiene debt that should not be copied into the DiscordOS lane
- no local `repos/DiscordOS` secret lane exists yet because the repo does not exist yet

## 8. Vercel And Runtime Ownership

### Current assumption

- current canonical project identity under Fitness is `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- local Fitness link file still points to project `fawxzzy-fitness`
- current worker polls or wakes the Fitness interaction route at `/api/discord/interactions`
- current update draft ingestion listens on the Fitness Vercel webhook route

### Target direction

- Discord OS should eventually own its own Vercel project and deployment path for:
  - Discord interaction webhook handling
  - gateway-worker support surfaces
  - feedback board operations
  - Discord publication flows
  - Music Sesh runtime and control surfaces
- Fitness should continue owning app login, account settings, verification-token issuance, and core product routes
- Fitness deployment events should feed Discord publication through an explicit contract, not by requiring Discord publication logic to live in Fitness

## 9. Bot Behavior That Must Not Break

Any separation plan must preserve these behaviors:

- signed Discord interactions must still verify and answer without downtime
- feedback panel `Submit`, `Edit`, update, withdraw, and completion-review flows must keep working
- forum card rendering, sync, audit comments, and status/reaction behavior must remain stable
- public `#updates` posting must preserve the governed green embed contract
- verification panel flow must still connect an authenticated Fitness user to Discord roles and member-number behavior
- command-card and setup-panel behavior in `#main` must keep replacing stale panels instead of leaving duplicates
- greeting triggers and other approved main-channel message commands must keep near-immediate response behavior
- Music Sesh public panel, ephemeral controls, room state, queue state, and Spotify handoff must not lose continuity
- command dedupe must keep preventing double responses

## 10. Migration Blockers

| Blocker | Why it matters |
| --- | --- |
| no local `repos/DiscordOS` repo yet | there is no canonical source surface to extract into |
| DiscordOS Supabase is empty | no schema or data landing zone exists yet |
| Discord runtime logic is concentrated in one large Fitness route | separation requires seam extraction before cutover |
| Fitness env model still groups app, Discord, Spotify, and deploy concerns together in `src/lib/env.ts` | env ownership is not split cleanly yet |
| verification and member-link flows are not yet documented as explicit cross-system APIs | identity bridge could break during migration |
| update drafting is still tied to Fitness deployment webhook handling | release narration and deploy truth are still co-hosted |
| Music Sesh provider/runtime data currently shares Fitness Supabase | state continuity will need deliberate export/import or phased dual-write |
| broader secret hygiene cleanup is not fully complete | the lane is improved, but not fully normalized for a new standalone repo |

## 11. No-Move-Yet Recommendation

Do not move code, data, or secrets yet.

Recommended next sequencing:

1. create a docs-only Discord OS separation decision pass that chooses the explicit shared-contract model for:
   - verification token consume
   - member-link ownership
   - member-number sync
   - Fitness deploy to Discord update handoff
2. inventory the exact env split between Fitness and future DiscordOS runtime
3. define the DiscordOS Supabase schema landing plan before any row movement
4. define the Vercel/runtime cutover plan before any repo extraction
5. only then create `repos/DiscordOS` and begin code extraction in bounded slices

## Initial Separation Recommendation

### Start with Discord OS-owned extraction candidates

- Discord feedback board logic
- Discord publication/update-draft logic
- Discord moderation logic
- gateway worker
- Music Sesh runtime and Spotify orchestration

### Keep Fitness-owned in the first separation wave

- Discord verification token generation
- Fitness account settings and Discord Connector UX
- Fitness profiles and `user_number`
- QA/LLEL and core Fitness data

### Force explicit contracts before any cutover

- verify token consume contract
- member-link contract
- member-number sync contract
- Fitness deploy/update publication contract

## Marker Interpretation

This package justifies:

- Discord OS Infrastructure Separation: `10%`

It does not yet justify:

- repo creation
- Supabase migration
- Vercel cutover
- bot runtime migration
- Fitness code removal
