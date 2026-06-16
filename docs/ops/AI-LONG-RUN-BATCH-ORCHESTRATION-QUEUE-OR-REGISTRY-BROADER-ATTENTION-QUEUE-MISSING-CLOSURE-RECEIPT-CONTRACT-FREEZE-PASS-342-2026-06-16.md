# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Missing-Closure-Receipt Contract Freeze Pass 342 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-POST-BROADER-ATTENTION-QUEUE-OPEN-MERGE-REQUEST-NEXT-SLICE-SELECTION-PASS-341-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@3ce06123`

## Objective

Freeze the exact bounded contract for the already-live `missing_closure_receipt` item family inside the broader root-owned `attention_queue` surface while preserving the queue behavior already landed on canonical `main`.

This pass does not:

- admit code or test changes
- widen `attention_queue` families beyond the already-frozen broader queue set
- mutate queue, registry, runtime, session, manifest, execution-receipt, trust, or owner-repo state
- reinterpret missing closure receipt visibility as closure repair, receipt reconciliation authority, execution mutation, or owner-repo authority
- reopen broader closure-result, active-session, or contradiction-family doctrine
- infer closure truth from hidden transcript state, operator memory, or uncited residue

## Inherited Chain

The following remain frozen and are inherited without change:

- pass 290 provenance-derived queue signal cap and overflow sentinel behavior
- pass 300 broader `attention_queue` contract and admitted item-family set
- the reconciled `open_merge_request` slice proving one compact root-local merge sentinel can land cleanly
- pass 341 selection of `missing_closure_receipt` as the next bounded live closure follow-on

## Exact Admitted Item Family

One already-live broader queue family is now frozen precisely:

- `missing_closure_receipt`

It qualifies only when all of these are true:

1. `attention_queue(...)` receives one item from `closure_receipts_payload`
2. that `closure_receipts_payload` item is produced only by `closure_receipts(descriptors, session_descriptor=target_session)`
3. `closure_receipts(...)` is processing only `links.close_receipt_refs` from the currently selected target `session_manifest`
4. each referenced close receipt is resolved only through `resolve_execution_receipt_descriptor(...)`
5. `resolve_execution_receipt_descriptor(...)` fails to resolve the referenced receipt even after the bounded supersession check in `execution_receipt_supersession_index(...)`
6. the family is describing unresolved closure-receipt visibility only, not performing closure repair, receipt reconciliation, execution mutation, or owner-repo mutation

If those conditions do not hold, this family is not emitted.

## Exact Admitted Source Surfaces

Allowed producing surfaces are root-local only:

- `execution_receipt_supersession_index(descriptors)`
- `resolve_execution_receipt_descriptor(source_ref, descriptors)`
- `closure_receipts(descriptors, session_descriptor=target_session)`
- `session_manifest` `links.close_receipt_refs`
- `execution_receipt` descriptors consumed by the supersession and resolution helpers
- descriptor `source_ref`

Allowed consuming surfaces already visible from the same root-owned contract are:

- `ops/cortex/render_status.py` inside `render_status_payload(...)`
- `ops/cortex/render_status.py` inside `attention_queue(...)`

## Forbidden Source Surfaces

This family is not allowed to originate from:

- active-session state branches directly
- closure-result severity branching
- merge-request, trust-posture, or initiative payloads
- owner-repo proof, deploy, or publication surfaces
- hidden transcript-state inference about whether a closure receipt should exist
- closure repair commands, execution mutation, receipt mutation, or live operator intervention state

## Exact Admitted Payload Fields

The emitted `attention_queue` item stays inside the already-frozen top-level item shape:

- `kind`
- `severity`
- `summary`
- `source_ref`

For this family specifically, the admitted values are:

- `kind = "missing_closure_receipt"`
- `severity = "high"`
- `summary = "A session closure receipt ref could not be resolved."`
- `source_ref` remains the unresolved close-receipt reference passed through `closure_receipts(...)`

No `details` payload is admitted for this family from this contract freeze alone.
No additional top-level queue fields are admitted.

Important non-admitted read-model-only fields:

- `missing`
- `original_source_ref`
- `receipt_id`
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

- emit `high` severity only
- merge the item into the same `attention_queue` item list as the other admitted families
- preserve final deterministic ordering via `attention_item_sort_key(...)`
- preserve queue-level `highest_severity` as the first sorted item severity

This means `missing_closure_receipt` coexists under the same severity-first then `kind` then `source_ref` then `summary` ordering already frozen for the broader queue.

## Exact Resolution Decision

The missing-closure family coexists with the root-local close-receipt read model exactly as follows:

- close receipt refs stay bounded to the current target session only
- each close receipt ref may resolve directly to one `execution_receipt` descriptor
- each close receipt ref may also resolve indirectly through one bounded supersession chain
- only when that bounded resolution fails closed does `closure_receipts(...)` emit a missing marker
- resolved closure receipts remain a separate read-model concern; they are not admitted queue-item payloads for this family

This contract freeze names that split only.
It does not freeze the separate `closure_receipt_issue` family.

## Exact Registry-Interaction Guard

The `missing_closure_receipt` item does not depend on healthy registry state once the unresolved close-receipt marker already exists.

The exact coexistence guard remains:

- `missing_closure_receipt` may still emit under unhealthy registry state
- no registry-surface contradiction or validation follow-on is required for this family itself
- `registry_error` may coexist separately when registry health is unavailable

This contract freeze names that split only.
It does not freeze the separate contradiction families themselves.

## Overflow And Budget Interaction

The pass-290 overflow boundary remains unchanged and still applies only to the provenance-derived queue subset.

Exact interaction:

- `missing_closure_receipt` does not alter `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP`
- it does not emit or suppress `provenance_alert_overflow`
- it does not widen the top-level queue payload
- it does not reinterpret unresolved closure visibility as queue-budget metadata

This family therefore joins the derived queue without reopening budget or overflow redesign.

## Root-Locality Decision

This item family remains root-local only.

Why:

- its producing truth comes from root-owned descriptor/read-model helpers already summarized inside ATLAS-root control-plane code
- its visible downstream consumers also remain inside ATLAS-root control-plane helpers
- no `_stack`, Playbook, owner-repo, deploy, or external runtime authority is required to define the contract boundary

## Separation Decision

Missing closure-receipt visibility is not:

- closure repair authority
- execution receipt reconciliation authority
- execution mutation authority
- merge-control authority
- registry repair authority
- owner-repo mutation authority

This family only surfaces one bounded unresolved-close-receipt sentinel inside the broader operator-review queue.

## Implementation Decision

This pass does not admit implementation yet.

Even though current root-local code already emits this family, the only result of this pass is to freeze the contract boundary around what counts, what fields are admitted, what surfaces may produce or consume it, what severity applies, and what must remain forbidden.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue missing_closure_receipt owner-surface admission pass 343`

Why:

- the contract boundary is now explicit
- the next honest question is whether the producing and consuming surfaces stay entirely inside ATLAS-root control-plane ownership or reopen any shared support or owner-repo boundary

## Marker Decision

- `none`

Why:

- this pass is docs-only contract clarification
- no new implementation, proof-backed adoption, blocker clearance, or broadened restart ratchet landed

## Rule

When a broader `attention_queue` family is already live and root-local, freeze the exact unresolved-close-receipt qualifier, payload boundary, bounded supersession-aware resolution split, and separation-from-repair rule before reopening ownership, support, or implementation questions.

## Pattern

next-slice selection -> exact family contract freeze -> owner-surface admission -> support check -> first-implementation admission

## Failure Mode

`Missing Closure Receipt Repair Drift`

If `missing_closure_receipt` is allowed to expand beyond one bounded root-local unresolved-reference sentinel, later work can smuggle closure repair, receipt reconciliation, or broader closure doctrine into the queue without a separately admitted packet.
