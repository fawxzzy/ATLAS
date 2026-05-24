# Stack Lock Decision: Fitness Discord Greeting Dedupe

Date: `2026-05-24`

## Decision

Accept Fitness commit `632520bf104aeb9556e219fa1a4fe425700bf8b8` into ATLAS root truth.

## Why

This package fixes a live Discord operator defect:

- a single greeting trigger could produce two bot replies

The accepted fix adds a durable message-command claim boundary in production before any greeting or message-command side effect is posted.

## Accepted surfaces

- `src/app/api/discord/interactions/route.ts`
- `src/lib/discord/message-command-claims.ts`
- `src/lib/discord/message-command-claims.test.ts`
- `src/lib/discord/interactions-route.test.ts`
- `supabase/migrations/20260524131000_discord_message_command_claims.sql`

## Production proof

- Supabase migration applied to project `lpswxoyfniocuhljgzbc`
- governed `_stack` production deploy completed
- production alias remains `https://fawxzzy-fitness-local.vercel.app`

## Verification

- `npm run verify`
- `npm run sanity:quick`
- `npm run build`
- root validation after repin
