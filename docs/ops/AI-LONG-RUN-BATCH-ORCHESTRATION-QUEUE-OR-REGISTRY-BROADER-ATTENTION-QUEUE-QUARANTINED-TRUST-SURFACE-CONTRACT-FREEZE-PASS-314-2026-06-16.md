# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Quarantined-Trust-Surface Contract Freeze Pass 314 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-CONTRACT-FREEZE-PASS-300-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-CONVERSATION-ACTION-REQUEST-CONTRACT-FREEZE-PASS-307-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-POST-BROADER-ATTENTION-QUEUE-CONVERSATION-ACTION-REQUEST-NEXT-SLICE-SELECTION-PASS-313-2026-06-16.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@25d95728`

## Objective

Freeze the exact bounded contract for the already-live `quarantined_trust_surface` item family inside the broader root-owned `attention_queue` surface while preserving the queue behavior already landed on canonical `main`.

This pass does not:

- admit code or test changes
- widen `attention_queue` families beyond the already-frozen pass-300 set
- mutate trust classification, registry, runtime, session, manifest, merge, or owner-repo state
- reopen the pass-290 provenance overflow boundary
- collapse the separate trust-posture surface into `attention_queue`
- infer trust posture from archive contents, imported knowledge payloads, or hidden state

## Inherited Chain

The following remain frozen and are inherited without change:

- pass 290 provenance-derived queue signal cap and overflow sentinel behavior
- pass 300 broader descriptor-backed `attention_queue` contract and admitted item-family set
- the reconciled conversation-action-request slice proving one compact root-local follow-on family can land cleanly
- pass 313 selection of `quarantined_trust_surface` as the next bounded descriptor-derived follow-on

## Exact Admitted Item Family

One additional already-listed broader queue family is now frozen precisely:

- `quarantined_trust_surface`

It qualifies only when all of these are true:

1. the candidate producing surface is a descriptor with `artifact_type="knowledge_catalog"`
2. the descriptor `trust_class` is not `trusted`, so it remains visible to the root-local `trust_surfaces(...)` helper
3. the derived trust-surface payload presented to `attention_queue(...)` has `trust_class == "untrusted"`
4. the item is emitted from the root-local `attention_queue(...)` helper as a derived quarantine signal rather than as mutable trust-state authority

If any of those conditions fail, this family is not emitted.

## Exact Admitted Source Surfaces

Allowed producing surfaces are root-local and descriptor-backed only:

- `knowledge_catalog` descriptors
- descriptor `identity.archive_id`
- descriptor `trust_class`
- descriptor `state.indexing_profile`
- descriptor `state.promotion_status`
- descriptor `source_ref`
- the derived root-local `trust_surfaces(...)` helper payload

Allowed consuming surfaces already visible from the same root-owned contract are:

- `ops/cortex/render_status.py` inside `trust_surfaces(...)`
- `ops/cortex/render_status.py` inside `trust_posture_summary(...)`
- `ops/cortex/render_status.py` inside `attention_queue(...)`

## Forbidden Source Surfaces

This family is not allowed to originate from:

- imported archive contents
- parsed knowledge body text
- trust-promotion mutations or approval writes
- registry, runtime-session, merge, session, or closure records
- owner-repo evidence or deploy surfaces
- inferred trust posture that is not present in the descriptor fields above

## Exact Admitted Payload Fields

The emitted `attention_queue` item stays inside the already-frozen top-level item shape:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details`

For this family specifically, the admitted values are:

- `kind = "quarantined_trust_surface"`
- `severity = "medium"`
- `summary = "Knowledge surface '<archive_id>' remains untrusted."`
- `source_ref = trust_surface.source_ref` when present
- `details` may contain only:
  - `archive_id`
  - `indexing_profile`
  - `promotion_status`

No additional top-level queue fields, no new status values, and no extra detail keys are admitted from this contract freeze alone.

## Exact Severity And Ordering Rule

This family does not define its own routing priority class beyond the frozen queue-wide sort discipline.

The exact rule remains:

- emit the item at fixed severity `medium`
- merge it into the same `attention_queue` item list as the other admitted families
- preserve final deterministic ordering via `attention_item_sort_key(...)`
- preserve queue-level `highest_severity` as the first sorted item severity

This means `quarantined_trust_surface` coexists under the same severity-first then `kind` then `source_ref` then `summary` ordering already frozen for the broader queue.

## Coexistence Decision

The family coexists with current admitted queue behavior exactly as follows:

- `initiative_open_attention` remains admitted and unchanged
- provenance-derived queue items remain admitted and unchanged
- `conversation_action_request` remains admitted and unchanged
- the separate `trust_posture` surface remains the fuller trust-state summary

No special family precedence is admitted here beyond the inherited deterministic sort.

## Overflow And Budget Interaction

The pass-290 overflow boundary remains unchanged and still applies only to the provenance-derived queue subset.

Exact interaction:

- `quarantined_trust_surface` does not alter `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP`
- it does not emit or suppress `provenance_alert_overflow`
- it does not widen the top-level queue payload
- it does not collapse the separate `trust_posture` summary

This family therefore joins the derived queue without reopening budget or overflow redesign.

## Root-Locality Decision

This item family remains root-local only.

Why:

- its producing truth comes from root-owned `knowledge_catalog` descriptors already summarized inside ATLAS-root control-plane code
- its visible downstream consumers also remain inside ATLAS-root control-plane helpers
- no `_stack`, Playbook, owner-repo, deploy, or external runtime authority is required to define the contract boundary

## Implementation Decision

This pass does not admit implementation yet.

Even though current root-local code already emits this family, the only result of this pass is to freeze the contract boundary around what counts, what fields are admitted, what surfaces may produce or consume it, and what must remain forbidden.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue quarantined_trust_surface owner-surface admission pass 315`

Why:

- the contract boundary is now explicit
- the next honest question is whether the producing and consuming surfaces stay entirely inside ATLAS-root control-plane ownership or reopen any shared support or owner-repo boundary

## Marker Decision

- `none`

Why:

- this pass is docs-only contract clarification
- no new implementation, proof-backed adoption, blocker clearance, or broadened restart ratchet landed

## Rule

When a broader `attention_queue` family is already live and descriptor-derived, freeze the exact descriptor trigger and payload before reopening ownership, support, or implementation questions.

## Pattern

next-slice selection -> exact family contract freeze -> owner-surface admission -> support check -> first-implementation admission

## Failure Mode

`Quarantined Trust Surface Drift`

If `quarantined_trust_surface` is allowed to expand beyond descriptor-derived untrusted `knowledge_catalog` posture, later work can smuggle trust-promotion mutation semantics, archive-content inference, or ad hoc runtime routing into the queue without a separately admitted packet.
