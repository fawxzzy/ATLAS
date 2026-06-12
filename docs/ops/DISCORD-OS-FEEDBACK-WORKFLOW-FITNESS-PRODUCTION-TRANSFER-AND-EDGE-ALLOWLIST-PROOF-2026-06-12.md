# Discord OS Feedback Workflow Fitness Production Transfer And Edge Allowlist Proof - 2026-06-12

## Scope

Lane: `Discord OS Feedback Workflow Canonicalization`

This receipt records the owner-side production transfer unblock for the Fitness-to-DiscordOS feedback path.

It does not claim final workflow cutover.

## Executed State

Fitness production transfer deployment:

- Fitness PR: `https://github.com/fawxzzy/fawxzzy-fitness/pull/95`
- PR state: open, draft, mergeable
- PR head: `b6009b7bffb3b152b84a54197c1b82d996dc6824`
- Fitness production deployment: `dpl_DfEFZezEfryECX8nhRdd4BUaQntX`
- deployment state: `READY`
- target: `production`
- aliases:
  - `https://fawxzzy-fitness-local.vercel.app`
  - `https://fawxzzy-fitness-fawxzzy.vercel.app`
  - `https://fawxzzy-fitness-zachariahredfield-fawxzzy.vercel.app`
- production transfer env now exists:
  - `DISCORDOS_FEEDBACK_TRANSFER_MODE`
  - `DISCORDOS_FEEDBACK_TRANSFER_ENDPOINT_URL`

Fitness verification:

```text
npm run typecheck
node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/discordos-feedback-transfer.test.ts
node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts
node --import ./scripts/register-test-aliases.mjs --test src/lib/history-30-day-summary.test.ts src/lib/progression-lifeline-summary.test.ts src/lib/dal/routine-delete.test.ts src/lib/discord/runtime/feedback/helpers.test.ts
```

Result:

- typecheck passed
- transfer helper tests passed `4/4`
- Discord interactions tests passed `97/97`
- nearby build-unblock tests passed `27/27`

DiscordOS Edge/RPC unblock:

- DiscordOS commit: `d264b50` (`Admit Fitness live transfer proofs in Edge writer`)
- migration applied to Supabase project `nwexsktuuenfdegzrbut`: `discordos_feedback_fitness_live_transfer_proof_rpc`
- Supabase Edge Function `discordos-feedback-persist`: version `4`, `ACTIVE`, `verify_jwt: true`
- the Edge writer and service-role proof RPC now explicitly admit `fitness-live-transfer-*` proof IDs

DiscordOS verification:

```text
npm run verify
```

Result:

- passed

## Live Writer Probe

Direct Vercel-to-DiscordOS-to-Supabase writer probe:

- endpoint: `https://fawxzzy-discordos.vercel.app/api/feedback-persist`
- proof row: `fitness-live-transfer-direct-discordos-writer-proof-20260612-173002`
- `ok: true`
- `persisted: true`
- `persistenceRuntime: supabase-edge-function`
- `trafficMoved: true`
- `liveTrafficMoved: true`
- `writesDiscord: false`
- `writesFitness: false`
- runtime warnings:
  - `edge_persist_writer_proof_only`
  - `discordos_fitness_live_transfer_proof`
  - `discordos_persisted_writer_no_discord_write`

This proves the live DiscordOS persisted-writer path now accepts Fitness-live-transfer-shaped proof rows through the deployed Vercel wrapper and deployed Supabase Edge writer.

It is not a Discord-signed Fitness-origin event.

## Connector Proof

GitHub connector:

- Fitness PR `#95` is open, draft, mergeable, and points at `b6009b7bffb3b152b84a54197c1b82d996dc6824`

Vercel connector:

- Fitness project `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- latest production deployment `dpl_DfEFZezEfryECX8nhRdd4BUaQntX`
- deployment state `READY`
- commit metadata points at `b6009b7bffb3b152b84a54197c1b82d996dc6824`

Supabase connector:

- project `nwexsktuuenfdegzrbut` is `ACTIVE_HEALTHY`
- `discordos-readiness`: version `3`, `ACTIVE`, `verify_jwt: true`
- `discordos-feedback-persist`: version `4`, `ACTIVE`, `verify_jwt: true`

## Activation Guard

Live readiness after the unblock still reports:

- `writerMode: active`
- `trafficTransferMode: active`
- `rollbackMode: discordos-primary-with-fitness-rollback`
- `edgeServiceRoleProbeOk: true`
- `discordBotTokenValid: true`
- `discordBotUserOk: true`
- `writerActivationAllowed: false`
- `liveWorkflowParityProved: false`
- `liveParityProofIdPresent: false`
- `liveTrafficProofIdPresent: false`
- `rollbackExecutionProofIdPresent: false`
- `liveCutover: false`
- `fitnessTrafficMoved: false`

Blocked reasons:

- `missing_live_workflow_parity_proof`
- `missing_live_traffic_transfer_proof`
- `missing_rollback_execution_proof`

## Decision

`Discord OS Feedback Workflow Canonicalization` moves from `90%` to `94%`.

Reason:

- one real production blocker was cleared: Fitness now has a READY production deployment from the transfer branch with active transfer env
- one real owner-side runtime blocker was cleared: DiscordOS Edge/RPC now admits `fitness-live-transfer-*` proof IDs
- one live writer proof now succeeds through Vercel plus Supabase Edge plus Postgres

Not `100%` because the explicit activation gate still blocks on one exact remaining class:

`real Discord-signed Fitness-origin feedback event routed through deployed Fitness to DiscordOS, rollback execution proof, and live parity receipt ID capture`

