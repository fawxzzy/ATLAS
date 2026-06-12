# Discord OS Feedback Workflow Fitness History Analytics Production Preservation Proof - 2026-06-12

## Decision

`Discord OS Feedback Workflow Canonicalization` holds at `96%`.

This is not final closeout. It proves the current Fitness history/analytics production deploy preserved the DiscordOS feedback transfer seam, but it does not clear the remaining live signed-event blocker.

## Fitness Owner-Repo Proof

Fitness branch:

`codex/fitness-history-analytics-discordos-transfer`

Pushed commits:

- `b72e0b68` - `Refine history analytics surfaces`
- `8d2d46c0` - `Add DiscordOS feedback transfer seam`
- `55b4cb8c` - `Unblock Fitness transfer deployment build`
- `102f6c8f` - `Align history analytics build contracts`

The branch combines the ready history/analytics work with the DiscordOS feedback transfer seam so a Fitness production deploy does not regress the active DiscordOS writer path.

## Verification

Repo-local verification passed before deployment:

- `npm run typecheck`
- `node --import ./scripts/register-test-aliases.mjs --test src/lib/history-scope-summary.test.ts src/lib/history-sessions-page-loader.test.ts src/lib/history-weekly-progress.test.ts src/lib/progression-event-analytics.test.ts src/lib/progression-lifeline-summary.test.ts src/lib/workout-card-view-models.test.ts src/lib/exercise-info-client.test.ts`
- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/discordos-feedback-transfer.test.ts src/lib/discord/interactions-route.test.ts`

Commit-hook lint also passed with pre-existing React hook dependency warnings only.

## Fitness Production Deployment

Vercel production deploy:

`vercel deploy --prod --yes --scope fawxzzy`

Result:

- deployment id: `dpl_DHtXDYBLVL9o8XxWCYCNa37Gmz2Q`
- deployment URL: `https://fawxzzy-fitness-om0fllcsz-fawxzzy.vercel.app`
- ready state: `READY`
- target: `production`
- build completed successfully

Production aliases on the deployment:

- `https://fawxzzy-fitness-local.vercel.app`
- `https://fawxzzy-fitness-fawxzzy.vercel.app`
- `https://fawxzzy-fitness-zachariahredfield-fawxzzy.vercel.app`

Vercel build proof:

- restored build cache from the prior transfer deployment `dpl_DfEFZezEfryECX8nhRdd4BUaQntX`
- ran `npm run build`
- compiled successfully
- lint/type validity completed with the same pre-existing React hook dependency warnings
- generated all static pages and deployed outputs successfully

## Live DiscordOS Status After Fitness Deployment

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
- `liveWorkflowParityProved: false`
- `liveTrafficProofIdPresent: false`
- `fitnessLiveTransferCount: 1`
- `humanFitnessLiveTransferCount: 0`
- `nonProofFitnessLiveTransferCount: 0`
- `humanNonProofFitnessLiveTransferCount: 0`
- latest row: `fitness-live-transfer-direct-discordos-writer-proof-20260612-173002`
- latest row remains `proof_only: true`
- latest row reporter remains `automation`

## Boundary

This receipt does not prove a real Discord-signed Fitness-origin feedback event.

This receipt does not prove live traffic receipt ID capture.

This receipt does not prove live workflow parity receipt ID capture.

This receipt does not open cutover.

This receipt does not claim that the marker may move to `100%`.

## Exact Remaining Blocker

The exact remaining blocker class is:

`real Discord-signed Fitness-origin feedback traffic through deployed Fitness plus live traffic and live workflow parity receipt ID capture`

## Result

`Discord OS Feedback Workflow Canonicalization: 96%`

Hold below `100%` until the exact remaining blocker class above is cleared by a real Discord-signed Fitness-origin transfer and live parity proof event.
