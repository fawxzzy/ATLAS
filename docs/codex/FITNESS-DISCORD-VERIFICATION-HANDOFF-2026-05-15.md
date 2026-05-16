# Fawxzzy Fitness Discord Verification Handoff

Date:
- 2026-05-15

Workspace:
- `repos/fawxzzy-fitness`

Canonical implementation proof:
- Fitness PR #21: Fitness-hosted Discord interactions endpoint
- Fitness PR #22: final member-number, durable link, nickname sync, audit, and resync implementation

ATLAS stack posture:
- ATLAS currently registers Fitness as an application surface and still marks it `unmanaged` in `stack.yaml`.
- This receipt documents the production Discord/Fitness integration without treating the old standalone bot as active infrastructure.

Scope covered in this receipt:
- final active production architecture
- source-of-truth correction for the old Gateway prototype
- production endpoints and Supabase surfaces
- member-number semantics and nickname-sync limits
- operator commands, migration lessons, and final Discord community tools
- reusable rules, patterns, and failure modes

## Goal

Build Discord server verification where Fitness owns identity proof, Discord consumes that proof, and the final production path stays available without a locally running Gateway bot.

## Source-of-truth correction

Old prototype repo:
- `repos/fawxzzy-fitness-discord-bot`

Status:
- Gateway bot prototype and fallback/debug lane only
- not the final active production path

Final active production path:

```text
Discord
-> signed HTTP interaction POST to Fitness /api/discord/interactions
-> Fitness verifies Discord Ed25519 signature before JSON parsing
-> Fitness handles PING, /setup-verify, button click, and modal submit
-> Fitness consumes one-time token proof
-> Fitness persists Discord/Fitness link state
-> Fitness calls Discord REST for role and nickname side effects
```

Current truth to preserve:
- Active: Fitness-hosted Discord HTTP interactions endpoint
- Prototype/fallback only: `fawxzzy-fitness-discord-bot` Gateway bot
- Identity authority: Fitness plus Supabase profiles
- Discord responsibilities: signed interaction transport, modal UI, role display, nickname display
- Playbook and ATLAS responsibilities: patterns, receipts, triage, reviewed promotion, not noisy automatic writes

## Final active integration architecture

Fitness is the identity authority.

Discord consumes Fitness proof.

Discord Developer App sends signed HTTP interactions to the Fitness app.

Fitness verifies Discord Ed25519 signatures before JSON parsing and handles:
- `PING`
- `/setup-verify`
- `Verify Fitness Account` button
- token modal submit
- Verified role grant
- member-number nickname sync

The old Gateway bot remains useful only as a prototype/fallback reference. It is not active production infrastructure after the Interactions Endpoint URL is saved in the Discord Developer Portal.

## Final production Discord community system

Active community surfaces now proven in production:
- Fitness-hosted Discord interactions endpoint
- verification token generation and signed verify modal flow
- compact member numbers with durable `discord_member_links`
- member-number nickname sync queue plus audit and resync scripts
- Feedback Bot with persistent panel and button-first user UX
- feedback attachments stored as Discord-hosted evidence links with bounded Supabase metadata only
- feedback status sync
- feedback withdraw cleanup that prunes details and attachment metadata while removing the Discord thread
- Curated Production Update Bot
- Vercel deployment webhook -> bounded update draft -> curated publish
- `@everyone` standard for public update posts

Community-system rule:
- Discord is the community surface.
- Fitness and Supabase keep the bounded system truth.
- ATLAS and Playbook receive reviewed promotion only.

## Production endpoints

Active Fitness app surfaces:

- `POST /api/discord/verification-token`
  - authenticated Fitness user creates a one-time token
- `POST /api/discord/verify`
  - legacy or server verification endpoint protected by shared secret
- `POST /api/discord/interactions`
  - active Discord Interactions Endpoint URL

## Production data surfaces

Supabase production tables and functions:

- `public.discord_verification_tokens`
  - stores hashed one-time tokens
  - stores no raw token values
- `public.discord_member_links`
  - durable Discord/Fitness link
  - stores Discord user id, Fitness user id, `user_number` snapshot, and nickname sync status
- `public.discord_feedback_reports`
  - bounded queue for Bug and Feature reports
  - stores duplicate counts, forum thread ids, bounded attachment metadata, and prune state
- `public.discord_update_drafts`
  - bounded queue for production deployment drafts and curated publish history
- `public.compact_human_member_numbers_preserving_zero()`
  - compacts positive human member numbers
  - preserves Zac as `#0`
- `profiles_compact_human_member_numbers_after_delete`
  - trigger that compacts human member slots after deletes

## Build history and decision sequence

### Phase 1: Fitness token backend

- built `public.discord_verification_tokens` with hash-only storage
- kept token display-once in UI state instead of durable profile data
- added token pepper
- added shared-secret path for legacy/server verification
- added `/api/discord/verification-token`
- added `/api/discord/verify`

### Phase 2: Gateway bot prototype

- built the first Discord flow as a Gateway bot for speed
- proved `/setup-verify`, button, modal, and role assignment interactions
- learned that a local Gateway bot creates an availability dependency on an always-running process

### Phase 3: Fitness-hosted HTTP interactions endpoint

- moved the active production path into `/api/discord/interactions`
- verified Discord Ed25519 signatures before JSON parse
- handled `PING`
- handled `/setup-verify`
- handled verify button and token modal submit
- granted the Verified role through Discord REST from Fitness-hosted logic
- confirmed the local Gateway bot was no longer required for the production path

### Phase 4: Production hardening

- fixed auth middleware and auth-session route classification so Discord probes no longer redirected to `/login`
- hardened malformed signatures to fail closed with `401`
- verified unsigned `POST` returns `{ error: "Invalid request signature." }` with HTTP `401`

### Phase 5: Member Number Bot v1 production reality

- durable Discord/Fitness links moved into `public.discord_member_links`
- member-number nickname sync happens during verification-time linking
- audit and resync scripts were added for drift handling
- compact public member slots replaced any assumption that member numbers are stable identity history

## Member-number semantics

Current product rule:

- Zac is always Member `#0`.
- No one else gets `#0`.
- Human users compact from `#1`.
- Automation, Codex, and QA users do not receive public member numbers.
- If a human member is deleted, higher positive numbers shift down.
- Discord nicknames may need a resync after compaction.
- The number is a compact public member slot, not permanent identity history.

Previous wording that implied member numbers were stable identity numbers is incorrect for the production system and should not be reused.

## Discord nickname limitation learned

Fitness can verify a user and persist the `discord_member_links` row even if nickname sync fails.

Discord can reject nickname updates with `403` when:
- the target user is the server owner
- the target user has a role equal to or higher than the bot or app role
- the bot lacks `Manage Nicknames`

Operational consequence:
- Zac's `#0` owner nickname may need to be set manually
- non-owner users are the valid proof case for automated nickname sync

## Env vars checklist

Fitness production env names only:

- `DISCORD_PUBLIC_KEY`
- `DISCORD_APPLICATION_ID`
- `DISCORD_GUILD_ID`
- `DISCORD_VERIFY_CHANNEL_ID`
- `DISCORD_VERIFIED_ROLE_ID`
- `DISCORD_UNVERIFIED_ROLE_ID` optional
- `DISCORD_BOT_TOKEN`
- `DISCORD_VERIFICATION_BOT_SECRET`
- `DISCORD_VERIFICATION_TOKEN_PEPPER`
- `SUPABASE_SERVICE_ROLE_KEY`
- `FITNESS_ZAC_EMAIL` optional but recommended for audit confirmation

Manual Discord portal:
- Interactions Endpoint URL:
  `https://<fitness-domain>/api/discord/interactions`

## Ops commands and scripts

Use the Fitness repo commands:

- `npm run audit:member-numbers`
- `npm run sync:discord-member-numbers`
- `npm run sync:discord-member-numbers -- --dry-run`
- `npm run discord:commands:register`
- `npm run doctor:discord-community`

Final active command surface:
- `/setup-verify`
- `/setup-feedback`
- `/feedback`
- `/feedback-status`
- `/feedback-withdraw`
- `/update-latest`
- `/update-publish`
- `/update-skip`

Removed command families:
- `/bug`
- `/bug-status`
- `/feature`
- `/fix`

Clarifications:

- `audit:member-numbers` is read-only
- `sync:discord-member-numbers` requires a real Discord bot token in env
- the old Gateway bot `npm run dev` process is not required after the Interactions Endpoint URL is saved

## Operational test checklist

- Generate token in `Fitness Settings -> Account -> Discord Access`.
- Click the Discord verify button.
- Paste the token into the Discord modal.
- Verified role is granted.
- `public.discord_member_links` records the durable link.
- Reusing token fails.
- Expired token fails.
- Local Gateway bot is stopped and the flow still works.
- Nickname sync succeeds for a normal non-owner user.
- Nickname sync failure on the owner or a higher-role user does not block verification persistence.

## Migration lesson learned

Production migration drift lesson:

- the Supabase project was correct
- the CLI failed because production migration history had entries missing from the local migrations folder
- urgent feature migrations `055` and `056` were applied surgically without migration repair
- the final Discord gap set `057` through `061` was repaired later by proving production schema effects first and then marking those exact versions applied in the remote ledger
- `npm run migration:validate` now passes again and normal linked migration workflow is healthy
- do not opportunistically "repair" production migration history during urgent feature deployment
- migration ledger repair requires schema evidence first

## Final env map

Names only:
- `DISCORD_PUBLIC_KEY`
- `DISCORD_BOT_TOKEN`
- `DISCORD_APPLICATION_ID`
- `DISCORD_GUILD_ID`
- `DISCORD_VERIFY_CHANNEL_ID`
- `DISCORD_VERIFIED_ROLE_ID`
- `DISCORD_BUG_REPORT_FORUM_CHANNEL_ID`
- `DISCORD_UPDATES_CHANNEL_ID`
- `DISCORD_MEMBER_SYNC_SECRET`
- `DISCORD_FEEDBACK_BUG_EMOJI_ID` optional
- `DISCORD_FEEDBACK_FEATURE_EMOJI_ID` optional
- `VERCEL_DEPLOYMENT_WEBHOOK_SECRET`
- `VERCEL_PROJECT_ID`
- `DISCORD_UPDATE_BOT_ENABLED`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DISCORD_VERIFICATION_TOKEN_PEPPER`
- `DISCORD_VERIFICATION_BOT_SECRET`
- `FITNESS_ZAC_EMAIL` optional

## Rules, patterns, and failure modes

Rules:

- Fitness owns identity; Discord consumes proof.
- Email knowledge is not identity proof.
- Unsigned Discord interactions must never reach role-grant logic.
- Public member numbers compact from `#1` while Zac remains `#0`.
- Automation accounts must not consume public member numbers.
- Discord is the community surface, not engineering truth.
- Feedback reports are signals, not repo truth.
- Deployment metadata is input, not release copy.
- Feedback attachments are Discord-hosted evidence, not app DB blobs.
- Optional Discord decoration must fail soft.
- Database triggers do not call Discord.
- User-facing delete means withdraw, redact, and cleanup rather than unbounded history loss.

Patterns:

- authenticated Fitness session -> one-time token -> signed Discord modal submit -> token consume -> role grant
- Fitness profile number -> Discord member link -> nickname sync
- feedback modal -> bounded row -> forum thread -> status or withdraw sync -> reviewed promotion
- production deploy -> bounded draft -> admin curated publish -> `@everyone` update post
- profile compaction -> stale link marker -> protected member sync path -> nickname update

Failure Modes:

- local-only Gateway bots make verification unavailable when the process dies
- auth middleware redirects make Discord endpoint verification fail before app logic runs
- Discord owner or higher-role users verify correctly but cannot be renamed by the bot
- changing DB member numbers without Discord resync leaves stale nicknames
- optional emoji or tag decoration can surface false failures after a valid feedback post
- Supabase migration drift forces surgical deploy paths
- direct Discord-to-ATLAS writes create noisy, abusive history
- raw release logs are not user communication

## Parked scope

Explicitly parked:
- no routine sharing
- no workout sharing
- no copy-to-app imports
- no Discord workout editor

## References

Reference:
- Fitness PR #20: Discord verification token flow
- Fitness PR #21: Fitness-hosted Discord interactions endpoint
- Fitness PR #22: Discord member link persistence, verification-time nickname sync, compact public member slots, audit, and resync
- Production endpoint path: `/api/discord/interactions`
- Token generation path: `Settings -> Account -> Discord Access`

## High-signal summary

- Rule: Fitness owns identity; Discord consumes proof.
- Pattern: Authenticated Fitness session -> one-time token -> signed Discord interaction -> token consume -> role grant and nickname sync.
- Failure Mode: Mistaking the old Gateway prototype for production techstack hides the real Fitness-hosted endpoint and leads future work down the wrong lane.
