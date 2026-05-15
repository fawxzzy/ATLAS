# Discord Fitness Verification Ops

## Purpose

Short operator runbook for the production Discord verification path where `fawxzzy-fitness` is the identity authority and Discord consumes signed proof through the Fitness-hosted interactions endpoint.

## Stack posture

- Active production path: Fitness-hosted `POST /api/discord/interactions`
- Prototype and fallback only: `repos/fawxzzy-fitness-discord-bot`
- Identity authority: Fitness plus Supabase profiles
- Discord responsibilities: signed interaction transport, modal UI, role display, nickname display
- Playbook and ATLAS responsibilities: patterns, receipts, triage, reviewed promotion, not direct noisy writes

## Active production surfaces

Fitness app endpoints:

- `POST /api/discord/verification-token`
  - authenticated Fitness user creates a one-time token
- `POST /api/discord/verify`
  - legacy or server verification endpoint protected by shared secret
- `POST /api/discord/interactions`
  - active Discord Interactions Endpoint URL

Supabase surfaces:

- `public.discord_verification_tokens`
- `public.discord_member_links`
- `public.compact_human_member_numbers_preserving_zero()`
- `profiles_compact_human_member_numbers_after_delete`

## Operator flow

1. Create the Discord app in the Discord Developer Portal.
2. Create the server roles and channels:
   `Verified`
   `Unverified` if used
   verify channel
3. Add the Fitness production env vars:
   `DISCORD_PUBLIC_KEY`
   `DISCORD_APPLICATION_ID`
   `DISCORD_GUILD_ID`
   `DISCORD_VERIFY_CHANNEL_ID`
   `DISCORD_VERIFIED_ROLE_ID`
   `DISCORD_UNVERIFIED_ROLE_ID` optional
   `DISCORD_BOT_TOKEN`
   `DISCORD_VERIFICATION_BOT_SECRET`
   `DISCORD_VERIFICATION_TOKEN_PEPPER`
   `SUPABASE_SERVICE_ROLE_KEY`
   `FITNESS_ZAC_EMAIL` optional but recommended
4. Deploy the Fitness route surfaces and Supabase objects:
   `POST /api/discord/verification-token`
   `POST /api/discord/verify`
   `POST /api/discord/interactions`
   `public.discord_verification_tokens`
   `public.discord_member_links`
5. Set the Discord Interactions Endpoint URL to:
   `https://<fitness-domain>/api/discord/interactions`
6. Register `/setup-verify` if needed:
   `npm run discord:commands:register`
7. Test the token flow end to end.

## Member-number semantics

- Zac is always Member `#0`.
- No one else gets `#0`.
- Human users compact from `#1`.
- Automation, Codex, and QA users do not receive public member numbers.
- If a human member is deleted, higher positive numbers shift down.
- Discord nicknames may require a resync after compaction.
- Member numbers are compact public display slots, not stable identity history.

## Ops commands

- `npm run audit:member-numbers`
- `npm run sync:discord-member-numbers`
- `npm run sync:discord-member-numbers -- --dry-run`
- `npm run discord:commands:register`

Command notes:

- `audit:member-numbers` is read-only
- `sync:discord-member-numbers` requires a real Discord bot token in env
- the old Gateway bot `npm run dev` process is not required once the Discord Interactions Endpoint URL is saved

## Test token flow

1. Generate a token in `Settings -> Account -> Discord Access`.
2. Click the Discord verify button.
3. Paste the token into the Discord modal.
4. Confirm the Verified role is granted.
5. Confirm the durable link exists in `public.discord_member_links`.
6. Confirm reused tokens fail.
7. Confirm expired tokens fail.
8. Confirm the local Gateway bot is stopped and the flow still works.
9. Confirm nickname sync succeeds for a normal non-owner user.
10. Confirm owner or higher-role nickname failure does not block verification persistence.

## Debug matrix

| Symptom | Likely cause | Check |
| --- | --- | --- |
| Discord rejects endpoint verification | Public key mismatch, auth redirect, endpoint not deployed, or malformed signature handling | Verify `DISCORD_PUBLIC_KEY`, confirm `/api/discord/interactions` is live, confirm unsigned `POST` returns `401` with `{ error: "Invalid request signature." }`, confirm no redirect to `/login` |
| Verify button works but modal submit fails | Token invalid, expired, reused, or consume path broken | Generate a fresh token, verify short TTL logic, verify one-time consume behavior in `public.discord_verification_tokens` |
| Modal submit succeeds but role is not granted | Missing bot token, missing Manage Roles, or role hierarchy issue | Verify `DISCORD_BOT_TOKEN`, confirm the app has Manage Roles, confirm bot role is above Verified |
| Verification persists but nickname does not update | Owner target, higher-role target, or missing Manage Nicknames | Confirm the `public.discord_member_links` row exists, confirm the target is not the server owner, confirm bot role order, confirm `Manage Nicknames` |
| Flow only works while local bot is running | Old Gateway path is still in use | Confirm production path is Fitness-hosted `/api/discord/interactions` and stop the local bot |
| Discord endpoint was previously accepted but later fails | Route classification or deploy drift | Reconfirm authless server-route exception and redeploy after env or middleware changes |
| Member numbers in Discord look stale after deletes | DB compaction ran but Discord nicknames were not resynced | Run `npm run audit:member-numbers`, then `npm run sync:discord-member-numbers -- --dry-run`, then real sync if approved |

## Production migration lesson

- The Supabase project was correct.
- The CLI failed because production migration history had entries missing from the local migrations folder.
- Urgent feature migrations `055` and `056` were applied surgically without migration repair.
- Separate migration-history reconciliation is still needed before normal `supabase db push` health is restored.
- Do not opportunistically repair production migration history during urgent feature deployment.

## Doctrine

- Rule: Fitness owns identity; Discord consumes proof.
- Rule: Email knowledge is not identity proof.
- Rule: Unsigned Discord interactions must never reach role-grant logic.
- Rule: Public member numbers compact from `#1` while Zac remains `#0`.
- Rule: Automation accounts must not consume public member numbers.
- Pattern: Authenticated Fitness session -> one-time token -> signed Discord modal submit -> token consume -> role grant.
- Pattern: Fitness profile number -> Discord member link -> nickname sync.
- Failure Mode: Local Gateway bots make verification unavailable when the process dies.
- Failure Mode: Auth middleware redirects make Discord endpoint verification fail before app logic runs.
- Failure Mode: Discord owner or higher-role users verify correctly but cannot be renamed by the bot.
- Failure Mode: Changing DB member numbers without Discord resync leaves stale nicknames.
