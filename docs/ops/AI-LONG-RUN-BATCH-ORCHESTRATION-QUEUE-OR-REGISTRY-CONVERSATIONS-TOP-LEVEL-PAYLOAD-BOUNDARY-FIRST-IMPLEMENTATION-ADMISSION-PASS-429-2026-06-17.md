# AI Long-Run Batch Orchestration Queue-Or-Registry Conversations Top-Level Payload Boundary First-Implementation Admission Pass 429 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONVERSATIONS-TOP-LEVEL-PAYLOAD-BOUNDARY-CONTRACT-FREEZE-PASS-426-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONVERSATIONS-TOP-LEVEL-PAYLOAD-BOUNDARY-OWNER-SURFACE-ADMISSION-PASS-427-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONVERSATIONS-TOP-LEVEL-PAYLOAD-BOUNDARY-SUPPORTING-LANE-ADMISSION-PASS-428-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-CONVERSATION-ACTION-REQUEST-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-16.md`
  - `docs/ops/ATLAS-STATUS-RUNBOOK.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@ec1a43d5`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned top-level `conversations` payload boundary plus one proof matrix for validating that slice without crossing the no-queue-change, no-`proposal_only`-widening, no-transcript-hydration, no-Awareness-widening, no-world-model-mutation, and no-runtime-mutation boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one explicit descriptor scan for `artifact_type = "conversation_manifest"` only
2. one bounded `item_count` layer counting all qualifying conversation manifests
3. one bounded `active_count` layer counting only qualifying manifests whose `state.status = "active"`
4. one deterministic descending sort layer by `state.updated_at`, then `identity.conversation_id`
5. one bounded `recent_items[:5]` projector preserving the admitted top-level recent conversation-state fields only
6. one unchanged top-level `render_status_payload(...)` handoff through `conversations`
7. one preserved separation layer where the fuller top-level `conversations` payload remains distinct from the narrower queue-side `conversation_action_request` family and the filtered queue-derived top-level `proposal_only` subset

The first-slice top-level projector may distinguish only:

- qualifying `conversation_manifest` descriptors that survive into counts and recent-item projection
- qualifying manifests whose `state.status = "active"` for `active_count`
- non-qualifying descriptors that fail closed to omission

## Exact Preserved Payload Surface

The worker must preserve only:

- `item_count`
- `active_count`
- `recent_items`

Top-level recent-item fields may preserve only:

- `conversation_id`
- `mode`
- `status`
- `turn_count`
- `last_turn_at`
- `recent_turn_refs`
- `active_initiative_refs`
- `active_session_refs`
- `source_ref`

Top-level payload rules remain:

- only `conversation_manifest` descriptors participate
- `item_count` counts all qualifying manifests
- `active_count` counts only manifests whose `state.status = "active"`
- `recent_items` sort by descending `state.updated_at`, then descending `identity.conversation_id`
- `recent_items` remain capped at `[:5]`
- the payload remains separate from the narrower queue-side `conversation_action_request` family and the queue-derived top-level `proposal_only` subset

## Exact Mandatory Proof Cases

1. no qualifying conversation manifests
   - preserve top-level `conversations.item_count` as `0`
   - preserve top-level `conversations.active_count` as `0`
   - preserve top-level `conversations.recent_items` as `[]`

2. non-conversation descriptors
   - omit descriptors whose `artifact_type` is not `conversation_manifest`

3. one active conversation manifest
   - preserve one top-level recent item with the exact admitted field set
   - preserve `item_count` as `1`
   - preserve `active_count` as `1`

4. one non-active conversation manifest
   - preserve `item_count` as `1`
   - preserve `active_count` as `0`
   - preserve the admitted recent-item fields without adding queue, transcript, or derived initiative/session meaning

5. multiple qualifying conversation manifests
   - preserve deterministic descending ordering by `updated_at`, then `conversation_id`
   - preserve only the top five recent items

6. top-level versus queue and proposal-only separation
   - preserve the fuller top-level `conversations` payload unchanged while `attention_queue` may still emit only the narrower `conversation_action_request` family and `proposal_only` may still remain the filtered queue-derived subset

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry conversations top-level payload boundary prompt-pack and handoff contract pass 430`

## Marker Decision

- `none`

Why:

- this pass freezes the smallest exact implementation slice and proof matrix only
- no code landing, proof execution, or broader operator adoption occurs here

## Rule

Freeze the smallest top-level conversations payload slice and proof matrix before admitting implementation or widening into queue semantics, transcript hydration, Awareness delivery widening, world-model semantics, or doctrine semantics.
