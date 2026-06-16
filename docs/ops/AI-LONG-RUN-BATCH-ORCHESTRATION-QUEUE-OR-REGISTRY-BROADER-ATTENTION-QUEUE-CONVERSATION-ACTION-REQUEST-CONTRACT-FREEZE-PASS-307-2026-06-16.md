# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Conversation-Action-Request Contract Freeze Pass 307 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-CONTRACT-FREEZE-PASS-300-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-IMPLEMENTATION-READINESS-CLOSEOUT-AND-WORKER-ROUTING-PASS-305-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-POST-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-NEXT-SLICE-SELECTION-PASS-306-2026-06-15.md`
  - `ops/cortex/_artifacts.py`
  - `ops/cortex/render_status.py`
  - `ops/atlas/build_turn_context.py`
  - `ops/atlas/converse.py`
  - `ops/atlas/awareness.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@947f5d1d`

## Objective

Freeze the exact bounded contract for the already-admitted `conversation_action_request` item family inside the broader root-owned `attention_queue` surface, while preserving the mixed-family queue behavior that already landed on canonical `main`.

This pass does not:

- admit code or test changes
- widen `attention_queue` families beyond the already-frozen pass-300 set
- mutate queue, registry, runtime, session, manifest, merge, or owner-repo state
- reopen the pass-290 provenance overflow boundary
- collapse the separate top-level `provenance_alerts` summary into `attention_queue`
- infer action requests from transcripts, terminal output, or hidden state

## Inherited Chain

The following remain frozen and are inherited without change:

- pass 290 provenance-derived queue signal cap and overflow sentinel behavior
- pass 300 broader descriptor-backed `attention_queue` contract and admitted item-family set
- pass 305 broader mixed-family implementation-readiness boundary
- the mixed-family worker-cluster reconciliation proving initiative-plus-provenance behavior on canonical `main`
- pass 306 selection of `conversation_action_request` as the next bounded descriptor-backed follow-on

## Exact Admitted Item Family

One additional already-listed broader queue family is now frozen precisely:

- `conversation_action_request`

It qualifies only when all of these are true:

1. the candidate surface is a descriptor with `artifact_type="conversation_turn"`
2. the descriptor `state` payload is a dictionary
3. `state.action_mode == "proposal_required"`
4. the item is emitted from the root-local `attention_queue(...)` helper as a derived operator-review signal rather than as mutable queue state

If any of those conditions fail, this family is not emitted.

## Exact Admitted Source Surfaces

Allowed producing surfaces are root-local and descriptor-backed only:

- `conversation_turn` descriptors built by `ops/cortex/_artifacts.py`
- descriptor `identity` fields carrying `conversation_id` and `turn_id`
- descriptor `state` fields carrying `intent` and `action_mode`
- the descriptor `source_ref` path already loaded by `ops/cortex/render_status.py`
- root-local turn classification inputs that set `action_mode="proposal_required"` inside `ops/atlas/build_turn_context.py`

Allowed consuming surfaces already visible from the same root-owned contract are:

- `ops/cortex/render_status.py` inside `attention_queue(...)`
- `ops/cortex/render_status.py` inside `proposal_only_state(...)`
- `ops/atlas/converse.py` when mapping a known attention ref back to a proposal-required turn
- `ops/atlas/awareness.py` when classifying this item family as operator-visible approval-needed attention

## Forbidden Source Surfaces

This family is not allowed to originate from:

- conversation manifests
- raw transcript text
- terminal output
- imported archives or world-model attention caches
- registry, runtime-session, merge, trust-surface, or closure-receipt records
- owner-repo evidence or deploy surfaces
- inferred operator intent that is not present in the descriptor fields above

## Exact Admitted Payload Fields

The emitted `attention_queue` item stays inside the already-frozen top-level item shape:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details`

For this family specifically, the admitted values are:

- `kind = "conversation_action_request"`
- `severity = "medium"`
- `summary = "Conversation turn '<turn_id>' requested a governed action proposal."`
- `source_ref = descriptor.source_ref` when present
- `details` may contain only:
  - `conversation_id`
  - `turn_id`
  - `intent`

No additional top-level queue fields, no new status values, and no extra detail keys are admitted from this contract freeze alone.

## Exact Severity And Ordering Rule

This family does not define its own routing priority class beyond the frozen queue-wide sort discipline.

The exact rule remains:

- emit the item at fixed severity `medium`
- merge it into the same `attention_queue` item list as the other admitted families
- preserve final deterministic ordering via `attention_item_sort_key(...)`
- preserve queue-level `highest_severity` as the first sorted item severity

This means `conversation_action_request` coexists under the same severity-first then `kind` then `source_ref` then `summary` ordering already frozen for the broader queue.

## Coexistence Decision

The family coexists with current admitted queue behavior exactly as follows:

- `initiative_open_attention` remains admitted and unchanged
- provenance-derived queue items remain admitted and unchanged
- the separate top-level `provenance_alerts` summary remains the fuller provenance-status surface
- `proposal_only_state(...)` may continue filtering only `conversation_action_request` items from the already-rendered queue without widening queue semantics

No special family precedence is admitted here beyond the inherited deterministic sort.

## Overflow And Budget Interaction

The pass-290 overflow boundary remains unchanged and still applies only to the provenance-derived queue subset.

Exact interaction:

- `conversation_action_request` does not alter `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP`
- it does not emit or suppress `provenance_alert_overflow`
- it does not widen the top-level queue payload
- it does not collapse the separate `provenance_alerts` summary

This family therefore joins the derived queue after provenance items are bounded, without reopening budget or overflow redesign.

## Root-Locality Decision

This item family remains root-local only.

Why:

- its producing truth comes from root-owned `conversation_turn` descriptors already built and consumed inside ATLAS-root control-plane code
- its visible downstream consumers also remain inside ATLAS-root control-plane helpers
- no `_stack`, Playbook, owner-repo, deploy, or external runtime authority is required to define the contract boundary

## Implementation Decision

This pass does not admit implementation yet.

Even though current root-local code already emits this family, the only result of this pass is to freeze the contract boundary around what counts, what fields are admitted, what surfaces may produce or consume it, and what must remain forbidden.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue conversation_action_request owner-surface admission pass 308`

Why:

- the contract boundary is now explicit
- the next honest question is whether the producing and consuming surfaces stay entirely inside ATLAS-root control-plane ownership or reopen any shared support or owner-repo boundary

## Marker Decision

- `none`

Why:

- this pass is docs-only contract clarification
- no new implementation, proof-backed adoption, blocker clearance, or broadened restart ratchet landed

## Rule

When a broader `attention_queue` family is already admitted at the queue-taxonomy level, freeze the exact descriptor-backed trigger and payload before reopening ownership, support, or implementation questions.

## Pattern

next-slice selection -> exact family contract freeze -> owner-surface admission -> support check -> first-implementation admission

## Failure Mode

`Conversation Action Request Drift`

If `conversation_action_request` is allowed to expand beyond descriptor-backed `conversation_turn` items with explicit `proposal_required` state, later work can smuggle transcript inference, runtime mutation semantics, or ad hoc approval routing into the queue without a separately admitted packet.
