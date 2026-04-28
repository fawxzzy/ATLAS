# Cortex Run Result Contract

- Status: Draft
- Date: 2026-04-27
- Scope: Cortex run artifact v0.1 only

## Purpose

`CortexRunResult` is the persisted artifact for one deterministic Cortex decision loop.

It is a structured memory candidate, not a final Lifeline receipt.

The contract exists so Cortex can be run, inspected, and reviewed before any connector, autonomy, or receipt-authority expansion.

## Rule

Cortex run artifacts are structured memory candidates, not final Lifeline receipts.

## Pattern

Serialize one deterministic Cortex decision loop per run artifact.

## Failure Mode

Do not turn the run artifact contract into connector, automation, or broad stack-normalization work.

## Inputs

The run result is derived from explicit inputs only:

- `runtime/cortex/kernel.state-model.seed.v1.json`
- `runtime/cortex/kernel.rule-registry.seed.v1.json`
- `runtime/cortex/kernel.proof-summary.examples.v1.json`
- optional explicit override paths passed to the CLI

The contract does not depend on hidden transcript state, repo mutation, connector calls, or Lifeline writes.

## Output Shape

`CortexRunResult` persists:

- the loaded `posture`
- the classified `rail_state`
- the `selected_next_action`
- the `verification_expectation`
- the bounded `worker_plan`
- the advisory `proof_receipt_draft`
- the preserved `known_ambient_debt`
- the compact `rules_applied`
- the compact `applied_rule_trace`
- the derived `failure_modes_avoided`
- the `receipt_ready` flag
- the `next_required_layer`

The applied-rule trace is compact and deterministic. It must expose:

- decision rule IDs
- plan rule IDs
- rule IDs applied
- pattern IDs applied
- failure-mode IDs avoided
- a short `why_selected` list for why the chosen next action won

## Lifecycle

The loop is:

1. Load explicit posture, rule, and proof-summary inputs.
2. Classify rail state.
3. Select the next bounded action.
4. Build the worker plan.
5. Draft the proof receipt summary.
6. Serialize the run result.
7. Optionally persist JSON and a plain-text summary under ignored `runtime/cortex/**` paths.

Each artifact represents one loop pass. It is inspectable output, not an execution engine.

## Ambient Debt Handling

Known stack validation debt stays on the `CortexRunResult` ledger as ambient debt unless the current tranche introduces a regression.

This means:

- ambient debt is preserved in the run result
- ambient debt can appear in the applied-rule trace
- ambient debt alone does not rewrite the selected next action into a failure path
- ambient debt alone does not become a final Lifeline receipt claim

## Receipt Readiness

`receipt_ready` is a Cortex advisory judgment only.

It can become `false` because of:

- current-tranche verification failures
- new current-tranche validation debt
- dirty owner-boundary status
- inherited ambient debt still being carried on the ledger

Even when a proof receipt draft exists, the artifact is still not a final Lifeline receipt.

## Rules Applied

The run result must show the compact rules that shaped the decision.

This keeps Simple Rule Theory inspectable in runtime behavior instead of burying it inside prose.

The trace should stay small enough to test directly and stable enough to diff across runs.

## Owner Boundaries

The contract is root-owned Cortex surface only.

Boundary expectations:

- Cortex may observe, interpret, plan, and draft proof.
- Cortex may persist ignored runtime artifacts for inspection.
- Cortex may not execute the plan as part of the run-artifact surface.
- Cortex may not mutate owner repos beyond the requested ignored runtime artifact write.
- Cortex may not write final Lifeline receipts.
- Cortex may not smuggle connector semantics into the contract.

## Runtime Surface

The default persisted artifact path is under ignored runtime storage:

- `runtime/cortex/runs/cortex-run-result.latest.json`
- `runtime/cortex/runs/cortex-run-result.latest.txt`

These are product-surface inspection outputs, not tracked canonical truth by default.
