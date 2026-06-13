# Discord OS Feedback Workflow Fitness Forum Post Preservation Fix - 2026-06-12

## Decision

`Discord OS Feedback Workflow Canonicalization` holds at `98%`.

This pass cleared the newly found Fitness-side defect where `DISCORDOS_FEEDBACK_TRANSFER_MODE=discordos-primary` could mirror a feedback submission to DiscordOS before creating the normal visible Discord feedback forum card.

## User Correction

The expected product behavior is:

`Feedback created from feedback submission is supposed to post to the feedback channel.`

That means DiscordOS mirroring must not bypass the regular Fitness feedback board.

## Fix Landed

Fitness:

- branch: `codex/logged-session-screen-pass`
- commit: `93dbbbb1 Keep Discord feedback forum posts during transfer`
- full commit: `93dbbbb1e1f5983812ce7170b07855a0c12d9370`

Changed behavior:

- the normal Fitness feedback row plus Discord forum thread is created first
- the DiscordOS transfer mirror runs after the visible feedback card path
- DiscordOS transfer failures are logged after the forum path succeeds instead of blocking the visible board post
- the DiscordOS transfer payload now carries forum metadata: `forumChannelId`, `forumThreadId`, `forumMessageId`, and `forumTitle`

Production deployment:

- Fitness deployment: `https://fawxzzy-fitness-88482z8ue-fawxzzy.vercel.app`
- production alias: `https://fawxzzy-fitness-local.vercel.app`

## Verification

Owner-repo verification passed:

- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/discordos-feedback-transfer.test.ts`
- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts`
- `npm run typecheck`
- `npm run build`
- production Vercel deployment build

The route test now proves the order explicitly: create the Fitness feedback forum post first, then mirror to DiscordOS with forum metadata.

## Boundary

This pass does not rewrite the earlier `test 06-12-26` row.

This pass does not create a new post-fix live Discord-signed submission.

This pass does not create a human non-proof DiscordOS transfer row.

This pass does not set `DISCORDOS_LIVE_TRAFFIC_PROOF_ID`.

This pass does not set `DISCORDOS_LIVE_PARITY_PROOF_ID`.

This pass does not claim `100%`.

## Exact Remaining Blocker

The exact remaining blocker class is:

`one new real Discord-signed Fitness-origin feedback interaction after Fitness deployment fawxzzy-fitness-88482z8ue-fawxzzy.vercel.app and DiscordOS deployment fawxzzy-discordos-46qhobmd7-fawxzzy.vercel.app that creates both a visible regular feedback forum card and a human non-proof DiscordOS transfer row, followed by live traffic and live workflow parity proof ID capture`

## Result

`Discord OS Feedback Workflow Canonicalization: 98%`

Hold below `100%` until the exact remaining blocker above is cleared by live evidence.
