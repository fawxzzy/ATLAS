# ATLAS Book Index

Quick summary: Revision 69 puts Fitness and its required shared sign-in and handoff path first. Use the owner repo for implementation, the existing Codex task for execution, and the master plus receipts to check the result.

## Current map

| Scope | Current operating choice | Authority |
|---|---|---|
| Fitness product and shared Supabase account/handoff | **CORE NOW** | [Fitness repo](https://github.com/fawxzzy/fawxzzy-fitness); existing protected Supabase owner for account and migration effects |
| ATLAS coordination, exact task/result delivery, and minimal Book navigation | **CORE NOW** | [Root rules](../../AGENTS.md), [stack map](../../stack.yaml), local master revision 69 |
| Playbook's demonstrated Fitness caller | **CORE NOW**, limited to evidenced value | [Playbook repo](https://github.com/fawxzzy/playbook) |
| `_stack` Fitness deploy wrappers and identity preflight | **KEEP FROZEN** in master revision 69; preserve optional wrapper and identity preflight | [_stack repo](https://github.com/fawxzzy/_stack); activation needs a current owner need and exact preflight |
| Foundation, Lifeline, Mazer features, Registry expansion, Playbook expansion, usage pacing expansion | **KEEP FROZEN** | Preserve current owners and receipts; reopen on a concrete Fitness dependency |
| Standalone Cortex and future research | **TODO LATER** | No current Fitness acceptance dependency established |
| Completed historical helpers and stale board claims | **ARCHIVE / RETIRE only after exact owner and retention check** | No deletion or task archive follows from this map |

These are scope choices, not claims that every product acceptance gate has passed. Historical Book pages below describe earlier states; the local `runtime/atlas/continuity/ACE_DURABLE_MASTER_PLAN.md` at revision 69, current owner repo, and exact accepted receipts govern current status. That local master and the `_stack` audit in the originating task are not part of this published repository. The wrapper is available but not proven required by the latest accepted Fitness release.

## Fitness operating dependencies

- [Fitness CI](https://github.com/fawxzzy/fawxzzy-fitness/blob/main/.github/workflows/ci.yml) builds in the product repo. The local accepted retained-cutover postimage records the `fitness.fawxzzy.com` Vercel binding and uninvoked rollback deployment.
- [Account handoff source](https://github.com/fawxzzy/fawxzzy-fitness/blob/main/src/lib/account-portal.ts) sends Fitness users to `account.fawxzzy.com`. The local accepted portal production postimage records its website Vercel binding. [Fitness Auth actions](https://github.com/fawxzzy/fawxzzy-fitness/blob/main/src/app/auth/actions.ts) call Supabase Auth for recovery. Current DNS operator and recovery-email delivery/SMTP provider are **UNKNOWN** from these source and receipt checks.
- [Billing routes](https://github.com/fawxzzy/fawxzzy-fitness/blob/main/src/app/api/billing/checkout/route.ts) use Stripe; [entitlement logic](https://github.com/fawxzzy/fawxzzy-fitness/blob/main/src/lib/billing/pro-access.ts) reads Stripe and Supabase records. This establishes a source dependency, not live checkout acceptance. Current Stripe configuration and end-to-end entitlement proof remain **UNKNOWN** here; the protected Supabase owner retains actual app acceptance.
## One task and result path

1. Start from one concrete Fitness intent. Check the local master revision 69 and [root rules](../../AGENTS.md), then identify the existing product or shared-service owner. Keep protected owner work with that owner.
2. Send one bounded packet to the existing Codex owner task through the current ATLAS task route. Check the exact task, lease, and delivery correlation before a wake. Do not create a parallel writer for the same effect.
3. The owner works in its repo, runs focused verification and review, and records the actual command, result, and limits in its receipt. Git/CI and provider readback supply source and delivery evidence; a wrapper's presence alone is not invocation.
4. Reconcile that receipt into the local master only through its designated publisher. If a result blocks, preserve its exact failure and resume the same owner at a safe boundary. Use [Restart and Handoff](12-restart-and-handoff-guide.md) for older context.

## Reference pages

1. [Current State](01-current-state.md)
2. [Lanes and Markers](02-lanes-and-markers.md)
3. [Operating Model](03-operating-model.md)
4. [Approval Gates](04-approval-gates.md)
5. [Receipt Index](05-receipt-index.md)
6. [System Ownership](06-system-ownership.md)
7. [Contracts and Seams](07-contracts-and-seams.md)
8. [Workflow Recipes](08-workflow-recipes.md)
9. [Automation Candidates](09-automation-and-command-candidates.md)
10. [Failure Modes and Recovery](10-failure-modes-and-recovery.md)
11. [System Map](11-system-map-graph.md)
12. [Restart and Handoff](12-restart-and-handoff-guide.md)
13. [Vision](13-vision-and-endgames.md)
14. [Lane Split](14-lane-split-execution.md)
15. [Lifeline](15-lifeline.md)
16. [Runtime Placement](16-runtime-placement.md)
17. [Creation OS Target](17-creation-os-target-architecture.md)

The local ATLAS workspace also retains chapters 18 (AI System Map) and 19 (Playbook Integration Map), with a machine companion. They explain the Playbook capability map, owner boundaries, evidence-gated bootstrap and adoption gaps. The Engineering Memory Enforcement, Policy and Task Harness contracts are also local. Those files are not in this published checkout, so their links await separate source publication.
