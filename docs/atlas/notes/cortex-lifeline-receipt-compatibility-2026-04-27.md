# Cortex Lifeline Receipt Compatibility Inventory

- Status: Draft
- Date: 2026-04-27
- Scope: Lane N read-only inventory only

## Purpose

This note maps Cortex receipt handoff drafts to Lifeline's existing proof-backed receipt expectations without adding a write path.

The inventory is read-only. Lifeline remains the final receipt owner.

## Rule

Lifeline owns final receipt truth; Cortex may only prepare compatibility notes and handoff drafts until a human-approved write path exists.

## Pattern

Map Cortex draft fields to Lifeline receipt expectations before implementing writes.

## Failure Mode

Do not mutate Lifeline just because Cortex can now produce receipt-ready handoffs.

## Read-Only Findings

Lifeline's current receipt contract is `atlas.ui.proof-passed.receipt.v1`.

The canonical owner-repo contract and implementation are:

- `repos/fawxzzy-lifeline/docs/contracts/ui-proof-passed-receipt-contract.md`
- `repos/fawxzzy-lifeline/src/core/ui-proof-receipt.ts`

Current Lifeline receipt emission requires:

- an ATLAS proof summary with `completion_ready=true`
- clean semantic proof
- clean visual proof
- `source_repo_id`
- `tranche_id`
- readable proof summary and proof report refs

The receipt is reference-first. It records proof refs and tranche identity; it does not copy full proof truth.

## Field Mapping

| CortexReceiptHandoffDraft field | Lifeline receipt concept | Status | Notes |
| --- | --- | --- | --- |
| `receipt_title` | human-facing label | partial | Useful as review context only; Lifeline does not require this field. |
| `owner_layer` | receipt owner / source identity | blocked | Lifeline expects owner-repo identity such as `source_repo_id`, not a layer like `cortex`. |
| `selected_next_action` | operator guidance | missing | Review guidance is not part of the proof-passed receipt shape. |
| `next_required_layer` | downstream routing hint | missing | Lifeline receipt emission does not consume layer routing hints. |
| `tranche_complete` | tranche completion signal | partial | Similar intent, but Lifeline requires proof-backed completion, not a Cortex-only boolean. |
| `receipt_ready` | readiness gate | partial | Useful as Cortex preflight only; not a substitute for ATLAS proof summary `completion_ready`. |
| `blocked` | emission rejection state | partial | Similar operator meaning, but Lifeline derives rejection from proof/readability checks, not this field. |
| `blocked_reason` | operator failure surface | partial | Could inform a future rejection summary, but is not part of the current proof-passed receipt contract. |
| `known_ambient_debt` | audit context | missing | Not part of Lifeline's current proof receipt shape. |
| `current_validation_debt` | audit context / blocker detail | missing | Not part of the current receipt shape; should stay in review material. |
| `applied_rules` | audit trace | missing | Lifeline receipts do not carry Cortex rule traces. |
| `failure_modes_avoided` | audit trace | missing | Useful for review, not part of current Lifeline receipt emission. |
| `reviewer_action_required` | human gate note | blocked | Human review remains required before any write path; this must not be translated into approval. |

## What Already Maps Cleanly

Very little maps directly today.

The strongest conceptual overlap is:

- `tranche_complete` as a tranche-level completion claim
- `receipt_ready` as a preflight readiness signal
- `blocked` and `blocked_reason` as operator-facing gating context

Even those are only partial because Lifeline requires proof references and owner-repo identity, not a Cortex review artifact alone.

## What Is Missing Or Ambiguous

Before Lane O, Cortex handoff drafts do not provide the full Lifeline receipt inputs:

- no `source_repo_id`
- no `tranche_id`
- no ATLAS proof summary ref
- no semantic proof report ref
- no visual proof report ref
- no proof report IDs
- no normalized `source_refs`
- no explicit human approval artifact

This is the main compatibility result: Cortex handoff drafts are not proof-passed receipts in waiting.

## What Must Remain Human-Reviewed

These decisions must stay human-reviewed before any write path exists:

- whether a Cortex handoff is sufficient to present downstream at all
- which repo and tranche identity the handoff applies to
- which ATLAS proof summary should anchor the receipt
- whether the proof summary is the correct owner-repo truth
- whether a Lifeline receipt should actually be written

## Prerequisites For Lane O

A future human-approved Lifeline write path would require:

- an explicit mapping spec from Cortex handoff review output to Lifeline receipt inputs
- a human approval artifact that is separate from `review_ready`
- source repo and tranche resolution rules
- ATLAS proof summary selection rules
- validation that semantic and visual proof refs are readable
- source-ref normalization rules compatible with Lifeline
- end-to-end tests that prove Cortex review does not bypass Lifeline ownership

Until those prerequisites exist, Cortex should stop at draft readiness and compatibility notes.
