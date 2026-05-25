# Discord OS Env & Runtime Ownership Matrix

Date: 2026-05-24
Lane: Discord OS Infrastructure Separation
Mode: docs-only ownership matrix
Status: first env/runtime ownership map recorded

## Goal

Define future env, runtime, Vercel, Supabase, and bot-process ownership before any Discord OS repo creation, code extraction, Supabase migration, or runtime cutover starts.

This pass does not:

- create `repos/DiscordOS`
- move code
- mutate Supabase
- mutate Vercel
- restart the bot
- pull env
- print secrets
- change Fitness code

## Canonical Future Targets

- GitHub target: `https://github.com/fawxzzy/DiscordOS.git`
- local target repo: `repos/DiscordOS`
- Fitness Supabase project: `lpswxoyfniocuhljgzbc`
- DiscordOS Supabase project: `nwexsktuuenfdegzrbut`

Supabase MCP setup note for the future DiscordOS lane:

```txt
codex mcp add supabase --url https://mcp.supabase.com/mcp?project_ref=nwexsktuuenfdegzrbut
codex mcp login supabase
optional: npx skills add supabase/agent-skills
```

## Inputs

- `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-INVENTORY-2026-05-24.md`
- `docs/ops/DISCORD-OS-SHARED-CONTRACT-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-CLEANUP-PLAN-1-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-CLEANUP-PASS-1-2026-05-24.md`
- `repos/fawxzzy-fitness/src/lib/env.ts`

## Governing Rules

- Fitness keeps Fitness-owned account, auth, profile, and release-proof env ownership.
- DiscordOS later owns Discord runtime, community workflow, and Music Sesh runtime env ownership.
- Shared seams must use explicit paired secrets or service contracts, not silent shared env reliance.
- Root `secrets/**` remains the only default local secret-bearing lane.
- `.vercel/project.json` remains identity metadata, not secret material.
- No migration should assume repo-local `.env*` is an acceptable long-term secret source.

## High-Level Findings

1. Fitness currently centralizes Discord, Spotify, Supabase, and deploy env in one app env surface.
   `repos/fawxzzy-fitness/src/lib/env.ts` mixes Fitness app auth, Discord bot/runtime, Spotify OAuth/runtime, and Vercel webhook identity in one ownership file.

2. Secret-lane posture improved, but Discord OS separation still lacks a dedicated owner surface.
   `secrets/local/fawxzzy-fitness-discord-worker.env` is now correctly governed, but there is still no local `repos/DiscordOS` repo or DiscordOS-specific secret lane.

3. Supabase ownership is not yet split in runtime.
   Fitness currently owns both the app-facing Supabase env and the Discord runtime’s live data access because all Discord tables still live in Fitness Supabase.

4. Runtime ownership and env ownership must split together.
   A DiscordOS repo or Supabase project without a matching env and worker ownership split would preserve the same hidden coupling under a new name.

## Ownership Matrix

| Class | Current owner | Future owner | Current source surface | Future source surface | Move later? | Shared-contract key? | No-move-yet note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fitness app auth/public Supabase env | Fitness | Fitness | Fitness app env | Fitness app env | no | no | stays Fitness-owned |
| Fitness service-role and admin DB auth | Fitness | Fitness | Fitness app/admin env | Fitness app/admin env | no | no | stays Fitness-owned |
| Discord bot token and Discord app ids | Fitness | DiscordOS | Fitness env + root secrets lane | DiscordOS env + root secrets lane | yes | no | do not split until DiscordOS runtime exists |
| Discord feedback/update/moderation channel and role ids | Fitness | DiscordOS | Fitness env | DiscordOS env | yes | no | move with Discord runtime, not earlier |
| Fitness verification issuance secrets | Fitness | Fitness | Fitness env | Fitness env | no | maybe paired consumer auth later | stay with Fitness token issuance |
| member-sync and verification bridge auth | Fitness | paired seam | Fitness env | split paired secret or service auth | later split | yes | requires seam-specific contract first |
| Spotify OAuth and Music Sesh provider secrets | Fitness | DiscordOS | Fitness env + governed root secrets | DiscordOS env + governed root secrets | yes | maybe narrow callback auth only | move with Music Sesh runtime, not before |
| Vercel deployment webhook secret for update drafting | Fitness | split | Fitness env | Fitness env for proof; DiscordOS env if publish runtime moves | maybe partial | yes for handoff auth | do not move ledger/proof ownership |
| Discord runtime worker env | Fitness-hosted Discord OS | DiscordOS | governed root secret lane targeting Fitness runtime | governed DiscordOS secret lane | yes | no | do not move until worker host target is planned |
| Supabase project ownership | Fitness + empty DiscordOS target | split | Fitness project live; DiscordOS project empty | split by table class | yes for DiscordOS tables only | no | schema landing plan required first |
| Vercel project/runtime ownership | Fitness | split | Fitness Vercel project | Fitness app project + future DiscordOS project | yes | no | cutover plan required first |

## 1. Discord Bot Token Ownership

### Current owner

- Fitness-hosted Discord runtime

### Current surface

- Fitness env model and governed root secret lane

### Future owner

- DiscordOS

### Decision

- `DISCORD_BOT_TOKEN` should move later to DiscordOS-owned runtime ownership
- it should not remain a long-term Fitness app env once Discord interaction/runtime hosting moves

### No-move-yet rule

- do not change token placement or runtime consumer until the DiscordOS worker and webhook target are defined

## 2. Spotify OAuth / Client Ownership

### Current owner

- Fitness-hosted Music Sesh runtime

### Current surface

- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_REDIRECT_URI`
- `SPOTIFY_TOKEN_ENCRYPTION_KEY`
- `SPOTIFY_OAUTH_STATE_SECRET`

### Future owner

- DiscordOS for Music Sesh runtime

### Decision

- these env classes move later with Music Sesh runtime ownership
- Fitness should not remain the default Spotify runtime owner once Music Sesh is extracted

### No-move-yet rule

- do not split Spotify env before the Music Sesh schema landing and runtime cutover plans exist

## 3. Discord Feedback / Update / Moderation Env Ownership

### Current owner

- Fitness-hosted Discord runtime

### Current env classes

- `DISCORD_FEEDBACK_PANEL_CHANNEL_ID`
- `DISCORD_BUG_REPORT_FORUM_CHANNEL_ID`
- `DISCORD_MAIN_CHANNEL_ID`
- `DISCORD_UPDATES_CHANNEL_ID`
- `DISCORD_MOD_LOG_CHANNEL_ID`
- purgatory channel, role, and category ids
- feedback emoji ids
- update-bot enable flags

### Future owner

- DiscordOS

### Decision

- these env classes move later with Discord runtime/workflow ownership
- channel and role ids belong with the system that runs the Discord workflows

### No-move-yet rule

- keep them in Fitness until DiscordOS runtime is real
- do not fork channel/role ownership across two active runtimes

## 4. Fitness Verification Env Ownership

### Current owner

- Fitness

### Current env classes

- `DISCORD_VERIFICATION_TOKEN_PEPPER`
- authenticated Fitness app session and token issuance path

### Future owner

- Fitness remains owner for issuance

### Decision

- verification-token issuance stays Fitness-owned
- DiscordOS may later consume verification proof through a paired contract, but should not own token issuance secrets

### No-move-yet rule

- no verification issuance secret moves as part of early separation

## 5. Supabase Project Ownership

### Fitness project

- project ref: `lpswxoyfniocuhljgzbc`
- future owner: Fitness app data plus any shared contract truth that intentionally remains Fitness-owned

### DiscordOS project

- project ref: `nwexsktuuenfdegzrbut`
- future owner: Discord feedback runtime state, moderation runtime state, update-draft runtime state, Music Sesh runtime state, and bot operational state

### Decision

- Fitness keeps:
  - `auth.users`
  - `auth.identities`
  - `public.profiles`
  - core workout/product tables
  - release-proof source surfaces
  - verification-token issuance truth
- DiscordOS later receives:
  - `discord_feedback_reports`
  - `discord_update_drafts`
  - `discord_moderation_cases`
  - `discord_message_command_claims`
  - Music Sesh runtime tables

### No-move-yet rule

- no table movement until the DiscordOS schema landing plan is written

## 6. Vercel Project / Runtime Ownership

### Current owner

- Fitness Vercel project

### Current runtime surfaces in Fitness

- Discord interaction webhook
- verification token consume route
- update draft ingest
- Music Sesh interaction runtime

### Future owner split

- Fitness keeps:
  - Fitness app routes
  - authenticated account settings and Discord Connector UX
  - release-proof and deployment truth
- DiscordOS later owns:
  - Discord interaction/runtime webhook
  - Discord publication/runtime logic
  - Music Sesh runtime
  - gateway-worker target surface

### Decision

- Vercel ownership must split by runtime responsibility, not by temporary convenience

### No-move-yet rule

- do not create or link a new Vercel project in this pass

## 7. Bot Process Hosting Ownership

### Current owner

- Fitness-hosted Discord OS runtime

### Current process posture

- gateway worker uses governed root secret lane
- worker still targets Fitness `/api/discord/interactions`

### Future owner

- DiscordOS

### Decision

- bot-process hosting should eventually move with the Discord runtime and its env ownership
- the worker should not remain forever pointed at Fitness after separation

### No-move-yet rule

- no bot restart or retarget in this pass

## 8. Secret File Destination Policy

### Canonical rule

- secret-bearing local files belong in `secrets/**`

### Future DiscordOS destination policy

- DiscordOS-specific local secrets should eventually live under a governed root secret lane, not in repo-root `.env*`

### Current acceptable governed local secret lane

- `secrets/local/fawxzzy-fitness-discord-worker.env`
- `secrets/local/fawxzzy-fitness-discord-bot.env`
- `secrets/local/fawxzzy-fitness-discord-prod.env`

### Policy consequence

- future DiscordOS runtime secrets should not reintroduce repo-root env residue
- if a DiscordOS-specific local lane is later added, it should still remain under root `secrets/**`

## 9. Env Variable Classes That Move Later

These classes should move later to DiscordOS ownership:

- Discord bot/app runtime:
  - `DISCORD_BOT_TOKEN`
  - `DISCORD_PUBLIC_KEY`
  - `DISCORD_APPLICATION_ID`
  - `DISCORD_GUILD_ID`
- Discord workflow channel/role ids:
  - feedback
  - updates
  - moderation
  - Music Sesh
  - main-channel command surfaces
- Discord workflow flags and runtime controls:
  - `DISCORD_UPDATE_BOT_ENABLED`
  - `DISCORD_UPDATE_AUTO_PUBLISH_ENABLED`
  - `DISCORD_MESSAGE_COMMAND_POLL_SECRET` or replacement
  - `CRON_SECRET` if still needed for fallback
- Music Sesh / Spotify provider runtime:
  - `SPOTIFY_CLIENT_ID`
  - `SPOTIFY_CLIENT_SECRET`
  - `SPOTIFY_REDIRECT_URI`
  - `SPOTIFY_TOKEN_ENCRYPTION_KEY`
  - `SPOTIFY_OAUTH_STATE_SECRET`

## 10. Env Variable Classes That Stay Fitness-Owned

These classes should remain Fitness-owned:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY` for Fitness app/admin operations
- Fitness auth/session env classes
- `DISCORD_VERIFICATION_TOKEN_PEPPER`
- release-proof and Fitness deployment source env classes
- any app-only feature env not needed by DiscordOS

## 11. Env Variable Classes That Become Shared-Contract Keys

These classes should become paired or seam-specific contract auth rather than staying implicit shared env:

- `DISCORD_VERIFICATION_BOT_SECRET`
  - if DiscordOS later consumes verification proof from Fitness
- `DISCORD_MEMBER_SYNC_SECRET`
  - if DiscordOS later performs nickname/member sync while Fitness remains canonical for `user_number`
- any future service-to-service auth key for:
  - Fitness deploy proof -> DiscordOS update drafting
  - Fitness profile/member lookup -> DiscordOS read access

Decision:

- shared-contract keys should be narrow, seam-specific, and paired only where needed
- they should not become a broad “both systems share all secrets” escape hatch

## 12. No-Move-Yet / No-Secret-Printing Rules

Do not:

- create `repos/DiscordOS` yet
- create or mutate DiscordOS Supabase schema yet
- create or mutate a DiscordOS Vercel project yet
- retarget the gateway worker yet
- split live runtime env files ad hoc
- print secret values
- pull env into repo roots
- move DiscordOS secrets into repo-local `.env*`

## Runtime Ownership Matrix

| Runtime surface | Current owner | Future owner | Current host | Future host | First safe prerequisite |
| --- | --- | --- | --- | --- | --- |
| Discord interaction webhook | Fitness | DiscordOS | Fitness Vercel | DiscordOS Vercel later | runtime cutover plan |
| gateway worker | Fitness-hosted Discord runtime | DiscordOS | local/process lane targeting Fitness route | local/process lane targeting DiscordOS route later | env split + webhook target plan |
| Fitness verification token issue | Fitness | Fitness | Fitness app | Fitness app | none; stays |
| verification consume runtime | Fitness | split | Fitness route | likely DiscordOS runtime with Fitness token contract | verification bridge contract |
| update drafting/publish runtime | Fitness-hosted Discord runtime | split | Fitness Vercel | DiscordOS publish runtime later | release-proof handoff contract |
| Music Sesh runtime | Fitness-hosted Discord runtime | DiscordOS | Fitness Vercel + Fitness Supabase | DiscordOS Vercel + DiscordOS Supabase later | schema landing plan |

## Secret Hygiene Impact

This ownership matrix sharpens the current hygiene lane by making three points explicit:

1. secret-bearing repo-root env files must not be the future DiscordOS pattern
2. `.vercel/project.json` remains identity metadata, not part of secret cleanup
3. legacy secret names such as `secrets/local/spotify-club-prod.env` need later ownership review because the owning runtime is expected to change

## Recommended Next Package

After this matrix:

1. `Discord OS Infrastructure Separation — Supabase Schema Landing Plan`
2. `Discord OS Infrastructure Separation — Runtime/Vercel Cutover Plan`

Do not start repo creation, table movement, or worker retargeting before those two land.

## Marker Interpretation

This package justifies:

- Discord OS Infrastructure Separation: `30%`
- Operator Secret Path Hygiene: `60%`
- Dependency Untangling: `10%`

It does not yet justify:

- repo creation
- Supabase mutation
- Vercel cutover
- bot runtime cutover
