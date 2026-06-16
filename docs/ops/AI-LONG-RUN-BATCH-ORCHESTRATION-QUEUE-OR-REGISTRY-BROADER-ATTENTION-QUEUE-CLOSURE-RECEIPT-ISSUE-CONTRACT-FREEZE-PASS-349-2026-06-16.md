# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Closure-Receipt-Issue Contract Freeze Pass 349 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-POST-BROADER-ATTENTION-QUEUE-MISSING-CLOSURE-RECEIPT-NEXT-SLICE-SELECTION-PASS-348-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-CONTRACT-FREEZE-PASS-300-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@080dce40`

## Objective

Freeze the exact bounded contract for the already-live `closure_receipt_issue` item family inside the broader root-owned `attention_queue` surface while preserving the queue behavior already landed on canonical `main`.

This pass does not:

- admit code or test changes
- widen `attention_queue` families beyond the already-frozen broader queue set
- mutate queue, registry, runtime, session, manifest, execution-receipt, trust, or owner-repo state
- reinterpret closure receipt result visibility as closure repair, receipt reconciliation authority, execution mutation, or owner-repo authority
- reopen broader active-session or contradiction-family doctrine
- infer closure truth from hidden transcript state, operator memory, or uncited residue

## Inherited Chain

The following remain frozen and are inherited without change:

- pass 290 provenance-derived queue signal cap and overflow sentinel behavior
- pass 300 broader `attention_queue` contract and admitted item-family set
- the reconciled `missing_closure_receipt` slice proving the bounded close-receipt read model, unhealthy-registry coexistence split, and top-level handoff already land cleanly on canonical `main`
- pass 348 selection of `closure_receipt_issue` as the next bounded live closure follow-on

## Exact Admitted Item Family

One already-live broader queue family is now frozen precisely:

- `closure_receipt_issue`

It qualifies only when all of these are true:

1. `attention_queue(...)` receives one item from `closure_receipts_payload`
2. that `closure_receipts_payload` item is produced only by `closure_receipts(descriptors, session_descriptor=target_session)`
3. `closure_receipts(...)` is processing only `links.close_receipt_refs` from the currently selected target `session_manifest`
4. the referenced close receipt resolves successfully through the bounded closure read model and is therefore not marked `missing`
5. the resolved close receipt carries a non-empty `result`
6. that `result` is not equal to `succeeded`
7. the family is describing closure receipt result visibility only, not performing closure repair, receipt reconciliation, execution mutation, or owner-repo mutation

If those conditions do not hold, this family is not emitted.

## Exact Admitted Source Surfaces

Allowed producing surfaces are root-local only:

- `closure_receipts(descriptors, session_descriptor=target_session)`
- `session_manifest` `links.close_receipt_refs`
- resolved `execution_receipt` descriptors already carried by the bounded closure read model
- resolved descriptor `source_ref`
- resolved descriptor `identity.receipt_id`
- resolved descriptor `state.result`

Allowed consuming surfaces already visible from the same root-owned contract are:

- `ops/cortex/render_status.py` inside `render_status_payload(...)`
- `ops/cortex/render_status.py` inside `attention_queue(...)`

## Forbidden Source Surfaces

This family is not allowed to originate from:

- unresolved close-receipt refs
- active-session state branches directly
- merge-request, trust-posture, or initiative payloads
- owner-repo proof, deploy, or publication surfaces
- hidden transcript-state inference about what closure result should exist
- closure repair commands, execution mutation, receipt mutation, or live operator intervention state

## Exact Admitted Payload Fields

The emitted `attention_queue` item stays inside the already-frozen top-level item shape:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details`

For this family specifically, the admitted values are:

- `kind = "closure_receipt_issue"`
- `severity = "high"` when `result == "failed"`
- `severity = "medium"` when `result` is any other admitted non-empty non-`succeeded` value
- `summary = "Closure receipt '<receipt_id>' ended with result '<result>'."`
- `source_ref` remains the resolved close-receipt reference carried through `closure_receipts(...)`
- `details` is admitted exactly as:
  - `receipt_id`
  - `result`

No other `details` fields are admitted for this family from this contract freeze alone.
No additional top-level queue fields are admitted.

Important non-admitted read-model-only fields:

- `missing`
- `original_source_ref`
- `tool_id`
- `extension_id`
- `registry_digest`
- `supersedes_receipt_ref`
- `reconciled_at`
- `reconciled_by_tool_version`
- `repair_basis_refs`

Those fields may remain source-side resolution inputs or read-model outputs, but they are not admitted queue-item payload fields for this family.

## Exact Severity And Ordering Rule

This family does not define its own queue-wide routing model beyond the already-frozen deterministic sort discipline.

The exact rule remains:

- emit `high` severity only for resolved closure receipts with `result == "failed"`
- emit `medium` severity for all other admitted non-empty non-`succeeded` results
- merge the item into the same `attention_queue` item list as the other admitted families
- preserve final deterministic ordering via `attention_item_sort_key(...)`
- preserve queue-level `highest_severity` as the first sorted item severity

This means `closure_receipt_issue` coexists under the same severity-first then `kind` then `source_ref` then `summary` ordering already frozen for the broader queue.

## Exact Resolution Decision

The closure-receipt-issue family coexists with the root-local close-receipt read model exactly as follows:

- close receipt refs stay bounded to the current target session only
- unresolved close receipt refs remain a separate `missing_closure_receipt` family
- resolved close receipts with `result == "succeeded"` remain silent for this family
- only resolved close receipts with admitted non-success results emit `closure_receipt_issue`

This contract freeze names that split only.
It does not freeze broader active-session or contradiction families.

## Exact Registry-Interaction Guard

The `closure_receipt_issue` item does not depend on healthy registry state once the resolved close-receipt result already exists.

The exact coexistence guard remains:

- `closure_receipt_issue` may still emit under unhealthy registry state
- no registry-surface contradiction or validation follow-on is required for this family itself
- `registry_error` may coexist separately when registry health is unavailable
- registry-health-dependent `validate_surface_ref(...)` follow-ons remain a separate contradiction-family concern and are not admitted queue payload fields for this family

This contract freeze names that split only.
It does not freeze the separate contradiction families themselves.

## Overflow And Budget Interaction

The pass-290 overflow boundary remains unchanged and still applies only to the provenance-derived queue subset.

Exact interaction:

- `closure_receipt_issue` does not alter `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP`
- it does not emit or suppress `provenance_alert_overflow`
- it does not widen the top-level queue payload
- it does not reinterpret closure result visibility as queue-budget metadata

This family therefore joins the derived queue without reopening budget or overflow redesign.

## Root-Locality Decision

This item family remains root-local only.

Why:

- its producing truth comes from root-owned descriptor/read-model helpers already summarized inside ATLAS-root control-plane code
- its visible downstream consumers also remain inside ATLAS-root control-plane helpers
- no `_stack`, Playbook, owner-repo, deploy, or external runtime authority is required to define the contract boundary

## Separation Decision

Closure receipt result visibility is not:

- closure repair authority
- execution receipt reconciliation authority
- execution mutation authority
- merge-control authority
- registry repair authority
- owner-repo mutation authority

This family only surfaces one bounded non-success closure-result sentinel inside the broader operator-review queue.

## Implementation Decision

This pass does not admit implementation yet.

Even though current root-local code already emits this family, the only result of this pass is to freeze the contract boundary around what counts, what fields are admitted, what severity branches are admitted, what surfaces may produce or consume it, and what must remain forbidden.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue closure_receipt_issue owner-surface admission pass 350`

Why:

- the contract boundary is now explicit
- the next honest question is whether the producing and consuming surfaces stay entirely inside ATLAS-root control-plane ownership or reopen any shared support or owner-repo boundary

## Marker Decision

- `none`

Why:

- this pass is docs-only contract clarification
- no new implementation, proof-backed adoption, blocker clearance, or broadened restart ratchet landed

## Rule

When a broader `attention_queue` family is already live and root-local, freeze the exact non-success closure-result qualifier, admitted detail boundary, bounded severity branch, and separation-from-repair rule before reopening ownership, support, or implementation questions.
