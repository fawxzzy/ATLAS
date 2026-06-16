# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Blocked-Worker Contract Freeze Pass 328 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-REGISTRY-ERROR-CONTRACT-FREEZE-PASS-321-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-POST-BROADER-ATTENTION-QUEUE-REGISTRY-ERROR-NEXT-SLICE-SELECTION-PASS-327-2026-06-16.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@e0d07368`

## Objective

Freeze the exact bounded contract for the already-live `blocked_worker` item family inside the broader root-owned `attention_queue` surface while preserving the queue behavior already landed on canonical `main`.

This pass does not:

- admit code or test changes
- widen `attention_queue` families beyond the already-frozen broader queue set
- mutate queue, registry, runtime, session, manifest, merge, trust, or owner-repo state
- reinterpret blocked-worker visibility as launch, dispatch, claim, done, pause, resume, or merge authority
- reopen active-session, open-merge-request, closure-record, or broader contradiction-family doctrine
- infer worker truth from hidden transcript state, operator memory, or uncited residue

## Inherited Chain

The following remain frozen and are inherited without change:

- pass 290 provenance-derived queue signal cap and overflow sentinel behavior
- pass 300 broader `attention_queue` contract and admitted item-family set
- the reconciled `registry_error` slice proving one compact root-local sentinel can land cleanly
- pass 327 selection of `blocked_worker` as the next bounded live worker-state follow-on

## Exact Admitted Item Family

One already-live broader queue family is now frozen precisely:

- `blocked_worker`

It qualifies only when all of these are true:

1. `attention_queue(...)` receives one item from `blocked_workers_payload`
2. `blocked_workers_payload` itself is derived only from `blocked_workers(descriptors)`
3. `blocked_workers(descriptors)` selects only the latest `worker_status` descriptor per worker through `latest_worker_states(...)`
4. the selected worker state is one of the already-live blocked-worker states:
   - `blocked`
   - `paused`
   - `merge_wait`
5. the family is describing worker blockage visibility only, not performing worker mutation, dispatch, resume, merge, or registry repair

If those conditions do not hold, this family is not emitted.

## Exact Admitted Source Surfaces

Allowed producing surfaces are root-local only:

- `latest_worker_states(descriptors)`
- `blocked_workers(descriptors)`
- `worker_status` descriptors consumed by those helpers
- descriptor `identity.worker_id`
- descriptor `identity.assignment_id`
- descriptor `identity.tool_id`
- descriptor `identity.extension_id`
- descriptor `state.worker_state`
- descriptor `state.blocked_reason`
- descriptor `state.registry_digest`
- descriptor `source_ref`

Allowed consuming surfaces already visible from the same root-owned contract are:

- `ops/cortex/render_status.py` inside `render_status_payload(...)`
- `ops/cortex/render_status.py` inside `attention_queue(...)`

## Forbidden Source Surfaces

This family is not allowed to originate from:

- active-session manifests or governed-session state
- merge-request, closure-receipt, or trust-posture payloads
- owner-repo proof, deploy, or publication surfaces
- hidden transcript-state inference about whether a worker is blocked
- repair commands, queue mutation, runtime mutation, or live operator intervention state

## Exact Admitted Payload Fields

The emitted `attention_queue` item stays inside the already-frozen top-level item shape:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details`

For this family specifically, the admitted values are:

- `kind = "blocked_worker"`
- `severity = "high"` when `state == "blocked"`
- `severity = "medium"` when `state == "paused"` or `state == "merge_wait"`
- `summary = "Worker '<worker_id>' is <state>."` with the existing helper fallback to `blocked` when the displayed state string is empty
- `source_ref` remains the upstream worker descriptor source reference passed through `blocked_workers(...)`
- `details` may contain only:
  - `worker_id`
  - `assignment_id`
  - `state`
  - `blocked_reason`

No additional top-level queue fields, no new blocked-worker states, and no extra detail keys are admitted from this contract freeze alone.

Important non-admitted read-model-only fields:

- `tool_id`
- `extension_id`
- `registry_digest`

Those fields may remain source-side validation inputs, but they are not admitted `details` payload keys for this queue family.

## Exact Severity And Ordering Rule

This family does not define its own queue-wide routing model beyond the already-frozen deterministic sort discipline.

The exact rule remains:

- emit `high` severity only for the strict blocked state
- emit `medium` severity for the other admitted blocked-worker states
- merge the item into the same `attention_queue` item list as the other admitted families
- preserve final deterministic ordering via `attention_item_sort_key(...)`
- preserve queue-level `highest_severity` as the first sorted item severity

This means `blocked_worker` coexists under the same severity-first then `kind` then `source_ref` then `summary` ordering already frozen for the broader queue.

## Coexistence Decision

The family coexists with current admitted queue behavior exactly as follows:

- `initiative_open_attention` remains admitted and unchanged
- provenance-derived queue items remain admitted and unchanged
- pass-290 overflow behavior remains admitted and unchanged
- `conversation_action_request` remains admitted and unchanged
- `quarantined_trust_surface` remains admitted and unchanged
- `registry_error` remains admitted and unchanged
- the top-level `provenance_alerts` summary remains separate and unchanged
- the top-level `trust_posture` summary remains separate and unchanged
- the top-level `proposal_only` handoff remains separate and unchanged
- active-session, open-merge-request, closure, and contradiction families remain separate broader queue seams

No special family precedence is admitted here beyond the inherited deterministic sort.

## Exact Registry-Interaction Guard

The blocked-worker item itself does not depend on healthy registry state once the admitted blocked-worker payload already exists.

The exact coexistence guard remains:

- `blocked_worker` may still emit under unhealthy registry state
- `validate_surface_ref(...)` may co-emit `unknown_tool_surface` or `unknown_extension_surface` only when `registry_state.ok` is truthy
- when registry health is unavailable, those contradiction-family follow-ons fail closed to omission

This contract freeze names that split only.
It does not freeze the separate contradiction families themselves.

## Overflow And Budget Interaction

The pass-290 overflow boundary remains unchanged and still applies only to the provenance-derived queue subset.

Exact interaction:

- `blocked_worker` does not alter `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP`
- it does not emit or suppress `provenance_alert_overflow`
- it does not widen the top-level queue payload
- it does not reinterpret blocked-worker visibility as queue-budget metadata

This family therefore joins the derived queue without reopening budget or overflow redesign.

## Root-Locality Decision

This item family remains root-local only.

Why:

- its producing truth comes from root-owned descriptor/read-model helpers already summarized inside ATLAS-root control-plane code
- its visible downstream consumers also remain inside ATLAS-root control-plane helpers
- no `_stack`, Playbook, owner-repo, deploy, or external runtime authority is required to define the contract boundary

## Separation Decision

Blocked-worker visibility is not:

- worker launch authority
- worker dispatch authority
- worker claim authority
- worker done or closure authority
- worker pause or resume authority
- worker merge authority
- registry repair authority

This family only surfaces one bounded worker-state sentinel inside the broader operator-review queue.

## Implementation Decision

This pass does not admit implementation yet.

Even though current root-local code already emits this family, the only result of this pass is to freeze the contract boundary around what counts, what fields are admitted, what surfaces may produce or consume it, what severity applies, and what must remain forbidden.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue blocked_worker owner-surface admission pass 329`

Why:

- the contract boundary is now explicit
- the next honest question is whether the producing and consuming surfaces stay entirely inside ATLAS-root control-plane ownership or reopen any shared support or owner-repo boundary

## Marker Decision

- `none`

Why:

- this pass is docs-only contract clarification
- no new implementation, proof-backed adoption, blocker clearance, or broadened restart ratchet landed

## Rule

When a broader `attention_queue` family is already live and root-local, freeze the exact worker-state qualifier, payload boundary, and separation-from-authority rule before reopening ownership, support, or implementation questions.

## Pattern

next-slice selection -> exact family contract freeze -> owner-surface admission -> support check -> first-implementation admission

## Failure Mode

`Blocked Worker Visibility Authority Drift`

If `blocked_worker` is allowed to expand beyond one bounded root-local visibility sentinel, later work can smuggle launch, resume, merge, or broader worker-control doctrine into the queue without a separately admitted packet.
