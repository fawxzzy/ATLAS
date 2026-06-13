# Discord OS Feedback Workflow Live Human Proof-Only Recheck and Provenance Fix - 2026-06-12

## Decision

`Discord OS Feedback Workflow Canonicalization` holds at `98%`.

This pass proved that a real human Fitness-origin Discord feedback submission reached DiscordOS, but it did not create the required human non-proof row.

## Live Submission Proof

User-submitted card:

- visible user label: `test 06-12-26`
- persisted report id: `fitness-live-transfer-1515148121418629341`
- report type: `bug`
- forum title: `Bug: Fitness - Test 06/12/26`
- reporter user kind: `human`
- reporter Discord user id present: `552278941159784460`
- created at: `2026-06-13T00:17:43.254Z`

Live transfer status after the submission:

- `fitnessLiveTransferCount: 2`
- `humanFitnessLiveTransferCount: 1`
- `nonProofFitnessLiveTransferCount: 0`
- `humanNonProofFitnessLiveTransferCount: 0`
- `latestHumanNonProofTransferRow: null`
- latest live row remained proof-only

Runtime warnings on the live row:

- `edge_persist_writer_proof_only`
- `discordos_fitness_live_transfer_proof`
- `discordos_persisted_writer_no_discord_write`

## Root Cause

DiscordOS Vercel authenticated the Fitness transfer and forwarded it to the Supabase Edge writer with the shared transfer secret, but the Vercel-to-Edge row payload stripped the original Fitness provenance fields:

- `transferSource: fitness-discord-interaction`
- `sourceProof: discord-signature-verified-by-fitness`

The Edge writer accepted the request, but without those fields it fell back to proof-only classification.

## Fix Landed

DiscordOS:

- branch: `codex/path-discipline-warning-slice-discordos`
- commit: `7cc0720 Preserve Fitness transfer provenance`
- receipt commit: `ba6ecb6 Record Fitness transfer provenance fix`
- owner receipt: `repos/DiscordOS/docs/ops/discordos-fitness-transfer-provenance-edge-hop-fix-2026-06-12.md`

Production deployment:

- DiscordOS deployment: `https://fawxzzy-discordos-46qhobmd7-fawxzzy.vercel.app`
- production alias: `https://fawxzzy-discordos.vercel.app`

Verification:

- `npm run verify:feedback-persist`
- `npm run verify`
- Vercel production build passed `npm run verify`

## Forum Cleanup

The regular `feedback` forum and dedicated `fawxzzy-fitness` forum were checked live under the `Project Feedback Boards` category.

Cleanup result:

- selected archived locked Fitness duplicate source threads in regular `feedback`: `19`
- deleted duplicate source threads: `19`
- deletion failures: `0`
- regular `feedback` post-cleanup count: `2`
- remaining title overlap with `fawxzzy-fitness`: `0`

The two remaining regular `feedback` threads are non-Fitness:

- `Feature: Discord Feedback - Separate general feedback intake from main-chat command flow`
- `Feature: Discord Os - A modular main-channel Discord story game called Wine or Cheese`

## Boundary

This pass does not rewrite the earlier proof-only live row.

This pass does not create a synthetic live row.

This pass does not set `DISCORDOS_LIVE_TRAFFIC_PROOF_ID`.

This pass does not set `DISCORDOS_LIVE_PARITY_PROOF_ID`.

This pass does not claim `100%`.

## Exact Remaining Blocker

The exact remaining blocker class is:

`one new real Discord-signed Fitness-origin feedback interaction after DiscordOS deployment fawxzzy-discordos-46qhobmd7-fawxzzy.vercel.app that creates a human non-proof DiscordOS transfer row, followed by live traffic and live workflow parity proof ID capture`

## Result

`Discord OS Feedback Workflow Canonicalization: 98%`

Hold below `100%` until the exact remaining blocker above is cleared by live evidence.
