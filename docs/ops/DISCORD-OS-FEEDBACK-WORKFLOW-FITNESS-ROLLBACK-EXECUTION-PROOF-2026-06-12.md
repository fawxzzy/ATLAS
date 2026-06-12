# Discord OS Feedback Workflow Fitness Rollback Execution Proof - 2026-06-12

## Decision

`Discord OS Feedback Workflow Canonicalization` moves from `95%` to `96%`.

This is not final closeout. It clears the rollback-execution sub-blocker only.

## Executed Rollback

Fitness production rollback was executed against the Vercel project `fawxzzy-fitness`.

Rollback command:

`vercel rollback fawxzzy-fitness-od74dr9f0-fawxzzy.vercel.app --yes --scope fawxzzy --timeout 3m`

Result:

- rollback succeeded
- rollback target deployment: `dpl_3k19YEKFxSByozpmVKLQtEfwpozS`
- rollback target URL: `https://fawxzzy-fitness-od74dr9f0-fawxzzy.vercel.app`
- Vercel status command reported success for the rollback

## Restored Transfer Deployment

Fitness production was then restored to the DiscordOS transfer deployment.

Promotion command:

`vercel promote fawxzzy-fitness-9eg60y7fa-fawxzzy.vercel.app --yes --scope fawxzzy --timeout 3m`

Result:

- promotion succeeded
- restored transfer deployment: `dpl_DfEFZezEfryECX8nhRdd4BUaQntX`
- restored transfer URL: `https://fawxzzy-fitness-9eg60y7fa-fawxzzy.vercel.app`
- Vercel status command reported success for the promotion
- alias proof after restoration showed `fawxzzy-fitness-fawxzzy.vercel.app` pointing at `fawxzzy-fitness-9eg60y7fa-fawxzzy.vercel.app`

## DiscordOS Proof ID Capture

DiscordOS production env was given the non-secret rollback proof ID:

`DISCORDOS_ROLLBACK_EXECUTION_PROOF_ID=docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-FITNESS-ROLLBACK-EXECUTION-PROOF-2026-06-12.md`

DiscordOS was redeployed to production:

- Vercel deployment: `dpl_41GhxXB37YjnKyaUtRJsxUgftufT`
- URL: `https://fawxzzy-discordos-p8bqxvz52-fawxzzy.vercel.app`
- production alias: `https://fawxzzy-discordos.vercel.app`
- status: `READY`

Vercel build ran `npm run vercel-build`, which ran `npm run verify`, including:

- `verify:feedback-adapters`
- `verify:readiness`
- `verify:activation`
- `verify:feedback-shadow`
- `verify:feedback-persist`
- `verify:feedback-transfer-proof`
- `verify:live-transfer-status`

## Live Readiness After Proof ID Capture

Live GET:

`https://fawxzzy-discordos.vercel.app/api/readiness`

Returned:

- `ok: true`
- `writerMode: active`
- `trafficTransferMode: active`
- `rollbackMode: discordos-primary-with-fitness-rollback`
- `edgeServiceRoleProbeOk: true`
- `discordBotTokenValid: true`
- `discordBotUserOk: true`
- `rollbackExecutionProofIdPresent: true`
- `liveWorkflowParityProved: false`
- `liveParityProofIdPresent: false`
- `liveTrafficProofIdPresent: false`
- `writerActivationAllowed: false`
- `liveCutover: false`
- `fitnessTrafficMoved: false`
- `activationBlockedReasons: ["missing_live_workflow_parity_proof","missing_live_traffic_transfer_proof"]`

Live GET:

`https://fawxzzy-discordos.vercel.app/api/live-transfer-status`

Returned:

- `ok: true`
- `liveSignedTransferReady: false`
- `rollbackExecutionProofIdPresent: true`
- `liveTrafficProofIdPresent: false`
- `liveWorkflowParityProved: false`
- `fitnessLiveTransferCount: 1`
- `humanFitnessLiveTransferCount: 0`
- `nonProofFitnessLiveTransferCount: 0`
- `humanNonProofFitnessLiveTransferCount: 0`
- latest row: `fitness-live-transfer-direct-discordos-writer-proof-20260612-173002`
- latest row remains proof-only automation

## GitHub PR Surface

Fitness PR `#95` remains open, draft, and mergeable.

The PR body now records the rollback execution proof and narrows the remaining blocker to real Discord-signed Fitness feedback traffic plus live traffic and live workflow parity receipt IDs.

## Boundary

This receipt does not prove a real Discord-signed Fitness-origin feedback event.

This receipt does not prove live traffic receipt ID capture.

This receipt does not prove live workflow parity receipt ID capture.

This receipt does not open cutover.

This receipt restores Fitness production to the transfer deployment after rollback proof.

## Exact Remaining Blocker

The exact remaining blocker class is:

`real Discord-signed Fitness-origin feedback traffic through deployed Fitness plus live traffic and live workflow parity receipt ID capture`

## Result

`Discord OS Feedback Workflow Canonicalization: 96%`

Hold below `100%` until the exact remaining blocker class above is cleared by a real Discord-signed Fitness-origin transfer and live parity proof event.
