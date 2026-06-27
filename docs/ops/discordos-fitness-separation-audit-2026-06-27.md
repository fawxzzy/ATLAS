# DiscordOS Fitness Separation Audit - 2026-06-27

## Objective

Record the remaining live ownership seams between `repos/DiscordOS` and `repos/fawxzzy-fitness` after the hosted Computa runtime was restored on DiscordOS.

This receipt is the canonical separation checkpoint for the current pass.

## Landed In This Pass

- DiscordOS command polling is live and hosted through:
  - Vercel production: `https://fawxzzy-discordos.vercel.app`
  - GitHub Actions worker: `Discord Message Command Worker`
- DiscordOS feedback launcher buttons no longer publish Fitness-branded custom IDs:
  - current IDs: `discordos_feedback_submit_open`, `discordos_feedback_update_open`
  - legacy Fitness IDs remain detectable for launcher repair and cleanup
- Fitness no longer presents `discord:feedback:worker` as an active command-runtime entrypoint:
  - `repos/fawxzzy-fitness/package.json`
  - `repos/fawxzzy-fitness/scripts/discord-feedback-gateway-worker-deprecated.mjs`

## Remaining Live Coupling

### 1. Fitness still owns the feedback interaction workflow

Fitness retains the live button, modal, report-edit, withdraw, and completion-review handlers in:

- `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`

Concrete evidence:

- `handleFeedbackCreateModalSubmit`
- `handleFeedbackCompletionReviewInteraction`
- `handleFeedbackSubmitPickerSelection`
- `handleFeedbackSubmitCreateButton`
- `handleFeedbackUpdatePickerSelection`
- `handleFeedbackManageLookupModalSubmit`
- `handleFeedbackWithdrawModalSubmit`

This means DiscordOS currently owns the command runtime and persistence surface, but not the full feedback interaction product lane.

### 2. Fitness still owns the original feedback source-of-truth model

Fitness still owns the operational feedback report CRUD logic in:

- `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`

That module still performs the report lifecycle work for:

- create
- duplicate detection
- content update
- status update
- withdraw
- completion review
- forum thread metadata updates

DiscordOS currently has:

- shadow/persist APIs
- schema and contract types
- forum-card helper surfaces

DiscordOS does not yet have feature-complete JS CRUD/runtime parity for the full feedback lifecycle.

### 3. Fitness still contains the old command-runtime implementation

The legacy gateway worker remains present in Fitness history and tests:

- `repos/fawxzzy-fitness/scripts/discord-feedback-gateway-worker.mjs`
- `repos/fawxzzy-fitness/scripts/discord-feedback-gateway-worker.test.mjs`

This is no longer the active hosted owner, but it remains a stale implementation seam until removed or archived.

### 4. DiscordOS still exposes Fitness-era activation and transfer naming

DiscordOS still carries Fitness cutover naming in runtime posture APIs and docs, including:

- `api/activation.js`
- `api/readiness.js`
- `api/live-transfer-status.js`
- `api/runtime-health.js`
- `api/feedback-persist.js`

Examples:

- `fitness-primary`
- `discordos-primary-with-fitness-rollback`
- `fitnessTrafficMoved`
- `fitness-live-transfer-*`

This is naming debt and proof-history debt, not the same thing as the live command-runtime blocker, but it keeps the repos conceptually entangled.

## Separation Status

### Fully separated now

- hosted Computa slash-command handling
- hosted Computa typed-message polling
- hosted command scheduler ownership
- command-card and owner-card publishing
- command-runtime deploy/build path

### Not fully separated yet

- feedback launcher button handling
- feedback create/update/withdraw modal handling
- completion review handling
- feedback source-of-truth CRUD ownership
- Fitness-era cutover naming inside DiscordOS posture APIs

## Next Burn-Down Order

1. Extract the Discord feedback interaction lane from Fitness into DiscordOS.
2. Re-home feedback CRUD/state logic so DiscordOS owns report lifecycle instead of Fitness-owned `bug-reports.ts`.
3. Remove or archive the legacy Fitness gateway worker implementation and tests.
4. Rename DiscordOS activation/readiness terminology away from Fitness-specific cutover language while keeping compatibility shims during rollout.

## Explicit Non-Claims

This pass does not claim that:

- DiscordOS already owns the entire feedback product workflow
- Fitness can already delete its Discord interaction route
- the Fitness report lifecycle code has been removed
- all historical docs/proofs have been renamed away from Fitness terminology
