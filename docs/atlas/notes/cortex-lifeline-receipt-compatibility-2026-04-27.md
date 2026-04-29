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

## Lane S Update

Lane S adds a Cortex-owned compatibility bridge that prepares a Lifeline-contract-compatible receipt candidate payload from a human-approved Cortex write-ready artifact.

The bridge writes only Cortex-owned candidate artifacts under `runtime/cortex/lifeline-receipt-candidates/` and validates the nested receipt payload structurally against the Lifeline-owned proof-reference receipt schema.

Rule: Cortex may build Lifeline-compatible receipt candidate payloads, but Lifeline remains the final receipt owner.

Pattern: After Lifeline defines the contract, Cortex should validate compatibility before enabling any final write path.

Failure Mode: Do not treat schema-compatible, write-ready, or human-approved candidate payloads as final Lifeline receipts.

## Lane Z Update

Lane Z adds Cortex-owned read-only ingestion for a Lifeline-owned proof-reference receipt audit index artifact.

Cortex reads an explicit Lifeline audit index JSON path, or the conventional Lifeline audit artifact path when present, then validates the owner-produced summary shape without invoking the Lifeline indexer or mutating Lifeline receipts.

The Lane Z summary remains read-only. It reports receipt counts, source repo and tranche grouping, proof-reference totals, invalid receipt entries, ambient debt inventory, current validation debt inventory, missing boundary statements, and `auto_approved` violations.

Connector-backed publication must remain blocked when the Lifeline audit index reports invalid receipts, current validation debt in any final receipt, missing boundary statements, or `auto_approved` drift.

Rule: Cortex may read Lifeline audit indexes, but Lifeline remains the final receipt owner.

Pattern: After Lifeline receipt promotion and indexing are stable, Cortex can ingest audit summaries as read-only receipt truth.

Failure Mode: Do not let Cortex audit-index ingestion become a receipt repair tool, promotion tool, connector publisher, or hidden Lifeline mutator.

## Read-Only Findings

Lifeline's current receipt contract is `atlas.ui.proof-passed.receipt.v1`.

The canonical owner-repo contract and implementation are:

- `repos/fawxzzy-lifeline/docs/contracts/ui-proof-passed-receipt-contract.md`
- `repos/fawxzzy-lifeline/src/core/ui-proof-receipt.ts`

As of 2026-04-28, the owner-side proof-reference receipt contract is also defined at:

- `repos/fawxzzy-lifeline/docs/contracts/proof-reference-receipt-contract.md`
- `repos/fawxzzy-lifeline/schemas/proof-reference-receipt.schema.json`
- `repos/fawxzzy-lifeline/fixtures/contracts/proof-reference-receipt.example.json`

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

Lane R narrows the ambiguity by making the Lifeline-owned proof-reference receipt shape explicit. The remaining gap is implementation compatibility, not owner-side schema ownership.

The Lifeline-owned proof-reference contract requires these mapped inputs for a future final receipt:

- `source_artifacts.proof_reference_pack_ref`
- `source_artifacts.proof_reference_pack_digest`
- `source_artifacts.write_ready_artifact_ref`
- `source_repo_id`
- `tranche_id`
- `proof_summary.owner_repo_id`
- `proof_summary.summary_ref`
- `proof_summary.report_id`
- `proof_refs.semantic_report_ref`
- `proof_refs.visual_report_ref`
- `source_refs`
- `approval.explicit_human_approval=true`
- `approval.auto_approved=false`
- `validation_context.current_validation_debt=[]`

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
