# AI Long-Run Batch Orchestration Queue-Or-Registry Conversations Top-Level Payload Boundary Contract Freeze Pass 426 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/ATLAS-STATUS-RUNBOOK.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-CONVERSATION-ACTION-REQUEST-CONTRACT-FREEZE-PASS-307-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-CONVERSATION-ACTION-REQUEST-OWNER-SURFACE-ADMISSION-PASS-308-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-CONVERSATION-ACTION-REQUEST-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-POST-TRUST-SURFACES-TOP-LEVEL-PAYLOAD-BOUNDARY-NEXT-SLICE-SELECTION-PASS-425-2026-06-17.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `stack.yaml`
  - `AGENTS.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@c46a8bd1`

## Objective

Freeze one exact root-bounded contract for the top-level `conversations` payload so the already-rendered conversation status surface becomes restart-safe without reopening queue mutation, conversation-turn queue routing, Awareness read-model widening, world-model mutation, runtime mutation, or owner-repo work.

This pass does not implement code, change queue behavior, widen conversation semantics, or move any marker.

## Root Health Baseline

- pass 425 already selected the top-level `conversations` payload boundary as the smallest honest follow-on after the completed top-level `trust_surfaces` branch
- pass 307 and its follow-on chain already froze and proved:
  - the narrower queue-side `conversation_action_request` family
  - the explicit separation between proposal-required conversation-turn attention and the fuller top-level conversation state surface
- `ATLAS-STATUS-RUNBOOK.md` already promotes `conversations` as an explicit operator-facing status surface
- `ops/cortex/render_status.py` already expresses the unfrozen adjacent seam in `conversation_summary(...)`
- root validation is currently clean at `critical=0 error=0 warning=3 info=0`

## Frozen Family Contract

### `family_name`

- `conversations top-level payload boundary`

### `trigger`

- the narrower queue-side `conversation_action_request` seam is already decided, integrated, and restart-safe
- status output still retains a separate top-level `conversations` payload whose contract is only implicit in `conversation_summary(...)`
- the smallest remaining bounded seam is the explicit meaning of that top-level conversation-state payload, not residue-aware write selection, cross-artifact inventory, registry summary, runtime-snapshot summary, or broader Awareness doctrine

### `stable_inputs`

- the bounded queue-side conversation request contract and proof from the pass-307 through pass-312 chain
- the status-runbook conversation surface rule that status exposes root conversation state from conversation descriptors only
- the current helper and test surfaces in:
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
- the retained stack-governance doctrine in:
  - `stack.yaml`
  - `AGENTS.md`

### `expected_artifact`

- one exact bounded top-level `conversations` payload contract only
- the contract may freeze only:
  - the top-level payload surface as one dictionary with:
    - `item_count`
    - `active_count`
    - `recent_items`
  - the item qualifier:
    - only descriptors with `artifact_type = "conversation_manifest"` participate
  - the count rules:
    - `item_count` counts all qualifying `conversation_manifest` descriptors
    - `active_count` counts only qualifying descriptors whose `state.status = "active"`
  - the top-level item fields inside `recent_items[*]`:
    - `conversation_id`
    - `mode`
    - `status`
    - `turn_count`
    - `last_turn_at`
    - `recent_turn_refs`
    - `active_initiative_refs`
    - `active_session_refs`
    - `source_ref`
  - the deterministic ordering rule for `recent_items`:
    - sort qualifying conversation manifests by `state.updated_at`
    - then `identity.conversation_id`
    - in descending order
  - the bounded window rule:
    - only `recent_items[:5]` are admitted into the top-level payload
  - the top-level meaning rule:
    - this payload remains the fuller descriptor-backed conversation-state surface
    - it may preserve counts plus bounded recent conversation-state summaries only
    - it may not add queue severity, proposal-needed routing, transcript hydration, derived initiative/session status meaning, or world-model summary meaning
  - the separation rule:
    - top-level `conversations` remains the fuller bounded conversation-state payload
    - `attention_queue` remains the separate derived operator-signal surface that may emit only the narrower `conversation_action_request` subset
    - top-level `proposal_only` remains the separate filtered queue-derived payload and does not replace the fuller conversation-state surface

### `failure_boundary`

- the top-level payload starts acting like the narrower queue-side request family and adds severity, request-only routing, or proposal-needed meaning
- the top-level payload starts hydrating transcript bodies, terminal output, or hidden chat state rather than bounded descriptor-backed conversation manifests
- the top-level payload widens beyond the admitted counts and bounded `recent_items[:5]` record shape
- the item contract widens beyond `conversation_manifest` descriptors

### `safe_fallback`

- keep the top-level payload separate from queue routing and from `proposal_only` filtering
- keep the payload descriptor-backed, bounded, and deterministic
- preserve only the existing counts and direct recent conversation-state item fields
- fail closed to:
  - `item_count = 0`
  - `active_count = 0`
  - `recent_items = []`
  when no qualifying conversation manifests exist
- stop below transcript hydration, initiative/session derivation, runtime mutation, or Awareness widening claims

### `owner_boundary`

- ATLAS root owns this contract freeze, restart projection, and non-claim boundaries
- exact code-level helper changes or proof-hardening changes remain a separate next-pass owner-surface question
- owner repos keep mutation truth, verification truth, and implementation truth

### `non_claim_boundary`

- no code or test implementation change
- no queue-family, queue-ordering, or queue-severity change
- no transcript hydration or transcript-derived inference claim
- no Awareness API, world-model, registry, session, merge, deployment, or runtime mutation claim
- no conversation-turn production or turn-classification claim beyond already-frozen descriptor-backed inputs
- no supervisor/operator proof claim

## Supporting Dependency Decision

- `none yet`

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry conversations top-level payload boundary owner-surface admission pass 427`

## Marker Decision

- `none`

## Rule

Freeze the fuller top-level `conversations` payload boundary after its narrower queue-side request sibling is reconciled, before reopening residue-aware, registry-backed, runtime-snapshot-backed, or broader Awareness-adjacent status families.
