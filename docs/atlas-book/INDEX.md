# ATLAS Book Index

Quick summary: Revision 69 puts Fitness and its required shared sign-in and handoff path first. Use the owner repo for implementation, the existing Codex task for execution, and the master plus receipts to check the result.

## Current map

| Scope | Current operating choice | Authority |
|---|---|---|
| Fitness product and shared Supabase account/handoff | **CORE NOW** | [Fitness repo](../../repos/fawxzzy-fitness/README.md); existing protected Supabase owner for account and migration effects |
| ATLAS coordination, exact task/result delivery, and minimal Book navigation | **CORE NOW** | [Root rules](../../AGENTS.md), [stack map](../../stack.yaml), [master revision 69](../../runtime/atlas/continuity/ACE_DURABLE_MASTER_PLAN.md) |
| Playbook's demonstrated Fitness caller | **CORE NOW**, limited to evidenced value | [Playbook repo](../../repos/playbook/README.md) |
| `_stack` Fitness deploy wrappers and identity preflight | **KEEP FROZEN** in master revision 69; preserve optional wrapper and identity preflight | [_stack repo](../../repos/_stack/README.md); activation needs a current owner need and exact preflight |
| Foundation, Lifeline, Mazer features, Registry expansion, Playbook expansion, usage pacing expansion | **KEEP FROZEN** | Preserve current owners and receipts; reopen on a concrete Fitness dependency |
| Standalone Cortex and future research | **TODO LATER** | No current Fitness acceptance dependency established |
| Completed historical helpers and stale board claims | **ARCHIVE / RETIRE only after exact owner and retention check** | No deletion or task archive follows from this map |

These are scope choices, not claims that every product acceptance gate has passed. Historical Book pages below describe earlier states; the [master](../../runtime/atlas/continuity/ACE_DURABLE_MASTER_PLAN.md), current owner repo, and exact accepted receipts govern current status. The `_stack` source audit is preserved in the originating task's `fitness-stack-dependency-r001-20261013.md`; its wrapper is available but not proven required by the latest accepted Fitness release. Master revision 69 accepts that frozen disposition.

## Fitness operating dependencies

- [Fitness CI](../../repos/fawxzzy-fitness/.github/workflows/ci.yml) builds in the product repo. Accepted release source and the `fitness.fawxzzy.com` Vercel binding are recorded in the [retained cutover postimage](../../runtime/atlas/continuity/platform-supabase-fitness-retained-cutover-r001-20261012-postimage.json); its retained rollback deployment was not invoked.
- [Account handoff source](../../repos/fawxzzy-fitness/src/lib/account-portal.ts) sends Fitness users to `account.fawxzzy.com`. The [portal production postimage](../../runtime/atlas/continuity/platform-supabase-portal-pr76-production-r001-20261012-postimage.json) binds that domain to the retained website Vercel project. [Fitness Auth actions](../../repos/fawxzzy-fitness/src/app/auth/actions.ts) call Supabase Auth for recovery. Current DNS operator and recovery-email delivery/SMTP provider are **UNKNOWN** from these source and receipt checks.
- [Billing routes](../../repos/fawxzzy-fitness/src/app/api/billing/checkout/route.ts) use Stripe; [entitlement logic](../../repos/fawxzzy-fitness/src/lib/billing/pro-access.ts) reads Stripe and Supabase records. This establishes a source dependency, not a live checkout or payment acceptance. Current Stripe configuration and end-to-end entitlement proof remain **UNKNOWN** here; the protected Supabase owner retains actual app acceptance.
## One task and result path

1. Start from one concrete Fitness intent. Check the [master](../../runtime/atlas/continuity/ACE_DURABLE_MASTER_PLAN.md) and [root rules](../../AGENTS.md), then identify the existing product or shared-service owner. Keep protected owner work with that owner.
2. Send one bounded packet to the existing Codex owner task through the current ATLAS task route. Check the exact task, lease, and delivery correlation before a wake. Do not create a parallel writer for the same effect.
3. The owner works in its repo, runs focused verification and review, and records the actual command, result, and limits in its receipt. Git/CI and provider readback supply source and delivery evidence; a wrapper's presence alone is not invocation.
4. Reconcile that receipt into the [master](../../runtime/atlas/continuity/ACE_DURABLE_MASTER_PLAN.md) only through its designated publisher. If a result blocks, preserve its exact failure and resume the same owner at a safe boundary. Use [Restart and Handoff](12-restart-and-handoff-guide.md) for older context.

## Reference pages

The existing sections remain historical and topical references: [Current State](01-current-state.md), [Lanes and Markers](02-lanes-and-markers.md), [Operating Model](03-operating-model.md), [Approval Gates](04-approval-gates.md), [Receipt Index](05-receipt-index.md), [System Ownership](06-system-ownership.md), [Contracts and Seams](07-contracts-and-seams.md), [Workflow Recipes](08-workflow-recipes.md), [Automation Candidates](09-automation-and-command-candidates.md), [Failure Modes and Recovery](10-failure-modes-and-recovery.md), [System Map](11-system-map-graph.md), [Restart and Handoff](12-restart-and-handoff-guide.md), [Vision](13-vision-and-endgames.md), [Lane Split](14-lane-split-execution.md), [Lifeline](15-lifeline.md), [Runtime Placement](16-runtime-placement.md), [Creation OS Target](17-creation-os-target-architecture.md), [AI System Map](18-ai-system-map.md), and [Playbook Integration Map](19-playbook-integration-map.md).

Machine companion: [ATLAS Book AI System Map v1](AI-SYSTEM-MAP.v1.json). Related contracts: [Engineering Memory Enforcement](../architecture/ATLAS-ENGINEERING-MEMORY-ENFORCEMENT.md), [Engineering Memory Policy](../registry/ATLAS-ENGINEERING-MEMORY-POLICY.v1.json), and [Engineering Memory Task Harness](../prompts/atlas-workflow/atlas.engineering-memory.md).
