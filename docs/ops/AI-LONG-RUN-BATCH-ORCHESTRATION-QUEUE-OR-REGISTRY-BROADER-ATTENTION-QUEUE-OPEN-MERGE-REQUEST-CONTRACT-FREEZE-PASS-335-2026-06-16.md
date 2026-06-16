# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Open-Merge-Request Contract Freeze Pass 335 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-POST-BROADER-ATTENTION-QUEUE-BLOCKED-WORKER-NEXT-SLICE-SELECTION-PASS-334-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@9c87bb1c`

## Objective

Freeze the exact bounded contract for the already-live `open_merge_request` item family inside the broader root-owned `attention_queue` surface while preserving the queue behavior already landed on canonical `main`.

This pass does not:

- admit code or test changes
- widen `attention_queue` families beyond the already-frozen broader queue set
- mutate queue, registry, runtime, session, manifest, merge, trust, or owner-repo state
- reinterpret open-merge visibility as merge execution, merge completion, repair, worker mutation, or owner-repo authority
- reopen active-session, closure-record, or broader contradiction-family doctrine
- infer merge truth from hidden transcript state, operator memory, or uncited residue

## Inherited Chain

The following remain frozen and are inherited without change:

- pass 290 provenance-derived queue signal cap and overflow sentinel behavior
- pass 300 broader `attention_queue` contract and admitted item-family set
- the reconciled `blocked_worker` slice proving one compact root-local worker-state sentinel can land cleanly
- pass 334 selection of `open_merge_request` as the next bounded live merge-request follow-on

## Exact Admitted Item Family

One already-live broader queue family is now frozen precisely:

- `open_merge_request`

It qualifies only when all of these are true:

1. `attention_queue(...)` receives one item from `open_merge_requests_payload`
2. `open_merge_requests_payload` itself is derived only from `open_merge_requests(descriptors)`
3. `open_merge_requests(descriptors)` delegates only to `classify_merge_requests(descriptors)` and returns only the active side of that canonical merge-request read model
4. `classify_merge_requests(descriptors)` groups only `merge_request` descriptors by one lineage key, chooses one canonical descriptor per group, and omits active emission when that group is already completed
5. the family is describing open merge-request visibility only, not performing merge execution, merge completion, worker mutation, receipt repair, or owner-repo mutation

If those conditions do not hold, this family is not emitted.

## Exact Admitted Source Surfaces

Allowed producing surfaces are root-local only:

- `open_merge_requests(descriptors)`
- `classify_merge_requests(descriptors)`
- `merge_request` descriptors consumed by those helpers
- `supervisor_merge_completion` descriptors used for completion gating
- `session_manifest` link refs used for canonical selection only
- descriptor `identity.merge_request_id`
- descriptor `identity.tool_id`
- descriptor `identity.extension_id`
- descriptor `identity.lineage_key`
- descriptor `identity.conflict_key`
- descriptor `links.conflicting_workers`
- descriptor `state.registry_digest`
- descriptor `source_ref`

Allowed consuming surfaces already visible from the same root-owned contract are:

- `ops/cortex/render_status.py` inside `render_status_payload(...)`
- `ops/cortex/render_status.py` inside `attention_queue(...)`

## Forbidden Source Surfaces

This family is not allowed to originate from:

- active-session state branches directly
- closure-receipt, trust-posture, or initiative payloads
- owner-repo proof, deploy, or publication surfaces
- hidden transcript-state inference about whether a merge request remains open
- merge execution commands, worker mutation, receipt repair, or live operator intervention state

## Exact Admitted Payload Fields

The emitted `attention_queue` item stays inside the already-frozen top-level item shape:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details`

For this family specifically, the admitted values are:

- `kind = "open_merge_request"`
- `severity = "high"`
- `summary = "Merge request '<merge_request_id>' remains open."`
- `source_ref` remains the canonical merge-request descriptor source reference passed through `classify_merge_requests(...)`
- `details` may contain only:
  - `merge_request_id`
  - `conflicting_workers`

No additional top-level queue fields and no extra detail keys are admitted from this contract freeze alone.

Important non-admitted read-model-only fields:

- `tool_id`
- `extension_id`
- `registry_digest`
- `conflict_key`

Those fields may remain source-side validation inputs or read-model inputs, but they are not admitted `details` payload keys for this queue family.

## Exact Severity And Ordering Rule

This family does not define its own queue-wide routing model beyond the already-frozen deterministic sort discipline.

The exact rule remains:

- emit `high` severity only
- merge the item into the same `attention_queue` item list as the other admitted families
- preserve final deterministic ordering via `attention_item_sort_key(...)`
- preserve queue-level `highest_severity` as the first sorted item severity

This means `open_merge_request` coexists under the same severity-first then `kind` then `source_ref` then `summary` ordering already frozen for the broader queue.

## Canonicalization Decision

The open-merge family coexists with the root-local canonical merge-request read model exactly as follows:

- grouping stays bounded to one lineage key per merge-request family
- canonical selection may consider completed ids, session-linked ids, conflicting-worker count, and source-ref tie-breaks only
- completed groups fail closed to omission from `open_merge_requests_payload`
- session-linked refs may affect canonical choice, but they do not by themselves close a merge-request group
- any residue records stay a separate read-model concern; they are not admitted queue-item payload fields for this family

This contract freeze names that split only.
It does not freeze the separate residue payload family.

## Exact Registry-Interaction Guard

The open-merge-request item itself does not depend on healthy registry state once the admitted open-merge payload already exists.

The exact coexistence guard remains:

- `open_merge_request` may still emit under unhealthy registry state
- `validate_surface_ref(...)` may co-emit `unknown_tool_surface` or `unknown_extension_surface` only when `registry_state.ok` is truthy
- when registry health is unavailable, those contradiction-family follow-ons fail closed to omission

This contract freeze names that split only.
It does not freeze the separate contradiction families themselves.

## Overflow And Budget Interaction

The pass-290 overflow boundary remains unchanged and still applies only to the provenance-derived queue subset.

Exact interaction:

- `open_merge_request` does not alter `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP`
- it does not emit or suppress `provenance_alert_overflow`
- it does not widen the top-level queue payload
- it does not reinterpret merge-request visibility as queue-budget metadata

This family therefore joins the derived queue without reopening budget or overflow redesign.

## Root-Locality Decision

This item family remains root-local only.

Why:

- its producing truth comes from root-owned descriptor/read-model helpers already summarized inside ATLAS-root control-plane code
- its visible downstream consumers also remain inside ATLAS-root control-plane helpers
- no `_stack`, Playbook, owner-repo, deploy, or external runtime authority is required to define the contract boundary

## Separation Decision

Open-merge visibility is not:

- merge execution authority
- merge completion authority
- worker mutation authority
- closure-receipt authority
- registry repair authority
- owner-repo mutation authority

This family only surfaces one bounded merge-request sentinel inside the broader operator-review queue.

## Implementation Decision

This pass does not admit implementation yet.

Even though current root-local code already emits this family, the only result of this pass is to freeze the contract boundary around what counts, what fields are admitted, what surfaces may produce or consume it, what severity applies, and what must remain forbidden.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue open_merge_request owner-surface admission pass 336`

Why:

- the contract boundary is now explicit
- the next honest question is whether the producing and consuming surfaces stay entirely inside ATLAS-root control-plane ownership or reopen any shared support or owner-repo boundary

## Marker Decision

- `none`

Why:

- this pass is docs-only contract clarification
- no new implementation, proof-backed adoption, blocker clearance, or broadened restart ratchet landed

## Rule

When a broader `attention_queue` family is already live and root-local, freeze the exact merge-request qualifier, payload boundary, canonical-selection split, and separation-from-authority rule before reopening ownership, support, or implementation questions.

## Pattern

next-slice selection -> exact family contract freeze -> owner-surface admission -> support check -> first-implementation admission

## Failure Mode

`Open Merge Request Visibility Authority Drift`

If `open_merge_request` is allowed to expand beyond one bounded root-local visibility sentinel, later work can smuggle merge execution, repair, or broader merge-control doctrine into the queue without a separately admitted packet.
