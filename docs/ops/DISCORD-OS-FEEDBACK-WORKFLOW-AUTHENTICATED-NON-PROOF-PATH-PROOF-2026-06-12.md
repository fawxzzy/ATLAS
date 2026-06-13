# Discord OS Feedback Workflow Authenticated Non-Proof Path Proof - 2026-06-12

## Decision

`Discord OS Feedback Workflow Canonicalization` moves from `96%` to `98%`.

This is not final closeout. It clears the `non-proof DiscordOS persistence path` sub-blocker by deploying a shared-secret authenticated Fitness-to-DiscordOS transfer path.

## Owner Commits

DiscordOS:

- branch: `codex/path-discipline-warning-slice-discordos`
- commit: `1db8b1b Require authenticated Fitness live transfer`
- receipt: `repos/DiscordOS/docs/ops/discordos-authenticated-fitness-live-transfer-path-2026-06-12.md`

Fitness:

- branch: `codex/logged-session-screen-pass`
- commits:
  - `8e05d300 Require DiscordOS feedback transfer secret`
  - `4f413d8d Refine logged session progression tags`
  - `d49094e6 Record authenticated DiscordOS handoff`
- receipt: `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORDOS-AUTHENTICATED-LIVE-TRANSFER-HANDOFF-2026-06-12.md`

## Runtime Contract

For `fitness-live-transfer-*` payloads:

- Fitness now requires `DISCORDOS_FEEDBACK_TRANSFER_SECRET` when `DISCORDOS_FEEDBACK_TRANSFER_MODE=discordos-primary`
- Fitness sends `X-DiscordOS-Feedback-Transfer-Secret` only from the Discord interaction handler after Ed25519 request signature verification
- Fitness marks the payload with `transferSource: fitness-discord-interaction`
- Fitness marks the payload with `sourceProof: discord-signature-verified-by-fitness`
- DiscordOS Vercel rejects `fitness-live-transfer-*` payloads without the matching secret
- DiscordOS Supabase Edge Function rejects `fitness-live-transfer-*` payloads without the matching secret
- authenticated human Fitness-origin transfer rows are no longer stamped with `edge_persist_writer_proof_only`

## Secret Handling

A new `DISCORDOS_FEEDBACK_TRANSFER_SECRET` was generated and provisioned without printing or committing the value.

Provisioned targets:

- DiscordOS Vercel production
- Fitness Vercel production
- DiscordOS Supabase Edge Function secrets

## Deployment Proof

Supabase Edge Function deployed:

`discordos-feedback-persist`

DiscordOS production deployed:

- project: `fawxzzy-discordos`
- deployment URL: `https://fawxzzy-discordos-kihfz90or-fawxzzy.vercel.app`
- production alias: `https://fawxzzy-discordos.vercel.app`

Fitness production deployed:

- project: `fawxzzy-fitness`
- deployment URL: `https://fawxzzy-fitness-ornettp9k-fawxzzy.vercel.app`
- production alias: `https://fawxzzy-fitness-local.vercel.app`

## Verification

DiscordOS local verification passed:

- `npm run verify`

Fitness local verification passed:

- `npm run typecheck`
- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/discordos-feedback-transfer.test.ts src/lib/discord/interactions-route.test.ts`
- `npm run build`

Fitness build completed with existing React hook dependency warnings only.

Vercel production builds completed successfully for DiscordOS and Fitness.

## Live Proof

Live readiness after deployment:

- `writerMode: active`
- `trafficTransferMode: active`
- `rollbackMode: discordos-primary-with-fitness-rollback`
- `rollbackExecutionProofIdPresent: true`
- `liveParityProofIdPresent: false`
- `liveTrafficProofIdPresent: false`
- `writerActivationAllowed: false`
- `liveCutover: false`

Live transfer status after deployment:

- `liveSignedTransferReady: false`
- `fitnessLiveTransferCount: 1`
- `humanFitnessLiveTransferCount: 0`
- `nonProofFitnessLiveTransferCount: 0`
- `humanNonProofFitnessLiveTransferCount: 0`
- latest row remains `fitness-live-transfer-direct-discordos-writer-proof-20260612-173002`
- latest row remains proof-only automation

Spoof check:

- direct no-secret POST to `https://fawxzzy-discordos.vercel.app/api/feedback-persist`
- payload id: `fitness-live-transfer-spoof-check-20260612`
- result: `401`

Supabase query after the spoof check:

- `fitness_live_transfer_count: 1`
- `human_fitness_live_transfer_count: 0`
- `non_proof_fitness_live_transfer_count: 0`
- `human_non_proof_fitness_live_transfer_count: 0`
- `latest_fitness_live_transfer_at: 2026-06-12 21:30:03.085+00`

## Boundary

This receipt does not create a synthetic live row.

This receipt does not prove a real Discord-signed Fitness-origin feedback interaction occurred after deployment.

This receipt does not set `DISCORDOS_LIVE_TRAFFIC_PROOF_ID`.

This receipt does not set `DISCORDOS_LIVE_PARITY_PROOF_ID`.

This receipt does not open cutover.

This receipt does not claim `100%`.

## Exact Remaining Blocker

The exact remaining blocker class is:

`one real Discord-signed Fitness-origin feedback interaction that creates a human non-proof DiscordOS transfer row, followed by live traffic and live workflow parity proof ID capture`

## Result

`Discord OS Feedback Workflow Canonicalization: 98%`

Hold below `100%` until the exact remaining blocker above is cleared by live evidence.
