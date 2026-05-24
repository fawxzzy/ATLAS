# Fitness Discord Greeting Dedupe

Date: `2026-05-24`

## Scope

Fix duplicate Discord greeting replies for main-channel greeting triggers such as:

- `good morning computa`
- `goodnight computa`

## Observed failure

The bot replied twice to a single greeting trigger in the main Discord channel.

## Root cause

The greeting path depended on local worker memory plus a processed reaction on the source message.

That was not a global claim boundary.

If a second poller or second process hit `/api/discord/interactions` before the first pass had become visible as processed, the same Discord message could be handled twice and post two greeting replies.

## Fix

Added a durable command-claim seam for Discord message commands:

- new helper: `src/lib/discord/message-command-claims.ts`
- new migration: `supabase/migrations/20260524131000_discord_message_command_claims.sql`
- route-level claim before side effects in `src/app/api/discord/interactions/route.ts`

Behavior now:

1. Classify the message command once.
2. Claim `(channel_id, message_id)` in Supabase before posting any greeting or command output.
3. Skip processing if the message is already claimed.
4. Finalize the claim after success or failure.

This closes the duplicate-response failure even if more than one worker or poll path sees the same Discord message.

## Production operations

Supabase production project:

- `lpswxoyfniocuhljgzbc`

Applied migration:

- `discord_message_command_claims`

Deployment path:

- governed `_stack` production deploy
- command: `pnpm run fitness:deploy:prod`

Production deployment:

- deployment id: `dpl_J8yLPcm9Kci46eaLtYnsznpKyP9W`
- deployment url: `https://fawxzzy-fitness-ntsadbvf7-fawxzzy.vercel.app`
- production alias: `https://fawxzzy-fitness-local.vercel.app`

## Verification

Repo-local verification:

- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/message-command-claims.test.ts`
- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts`
- `node --test scripts/discord-feedback-gateway-worker.test.mjs`
- `npm run verify`
- `npm run sanity:quick`
- `npm run build`

Supabase verification:

- confirmed `public.discord_message_command_claims` exists in production

## Notes

- No change was made to the greeting copy itself.
- No change was required in the worker script for the live fix; the durable claim boundary lives in the deployed route.
- Preexisting unrelated Fitness repo residue remained untouched.
