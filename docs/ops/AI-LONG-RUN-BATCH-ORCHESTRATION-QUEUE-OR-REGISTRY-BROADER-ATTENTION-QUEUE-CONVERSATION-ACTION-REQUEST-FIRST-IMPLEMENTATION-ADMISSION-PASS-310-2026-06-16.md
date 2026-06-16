# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Conversation-Action-Request First-Implementation Admission Pass 310 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-CONVERSATION-ACTION-REQUEST-CONTRACT-FREEZE-PASS-307-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-CONVERSATION-ACTION-REQUEST-OWNER-SURFACE-ADMISSION-PASS-308-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-CONVERSATION-ACTION-REQUEST-SUPPORTING-LANE-ADMISSION-PASS-309-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@1dbfc2c5`

## Objective

Freeze the smallest exact first implementation slice for the root-local `conversation_action_request` queue seam and its paired proposal-only projection without widening beyond the already-live `render_status` helper boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one descriptor-backed `conversation_action_request` emission branch inside `attention_queue(...)`
2. one inherited final merge and deterministic `attention_item_sort_key(...)` ordering layer against the already-admitted broader queue families
3. one bounded `proposal_only_state(...)` projection that filters only `conversation_action_request` items from the already-rendered queue payload
4. one top-level `render_status_payload(...)` handoff of that proposal-only projection as `proposal_only`

The worker may distinguish only:

- `conversation_turn` descriptors with `state.action_mode="proposal_required"`
- `conversation_turn` descriptors that do not qualify and must fail closed to no emitted request item
- queue-level `clear` versus `needs_review`
- proposal-only `clear` versus `pending`

## Exact Preserved Payload Surface

The worker must preserve the inherited queue payload surface only:

- `status`
- `item_count`
- `highest_severity`
- `items`

For the `conversation_action_request` item itself, the worker must preserve only:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details.conversation_id`
- `details.turn_id`
- `details.intent`

For the proposal-only projection, the worker must preserve only:

- `status`
- `item_count`
- `items`

Allowed proposal-only item fields only:

- `summary`
- `severity`
- `source_ref`
- `conversation_id`
- `turn_id`
- `intent`

## Exact Mandatory Proof Cases

1. one proposal-required conversation turn and no higher-severity queue items
   - emit queue `status` as `needs_review`
   - emit one `conversation_action_request`
   - preserve `highest_severity` as `medium`
   - preserve `conversation_id`, `turn_id`, and `intent`

2. one informational or otherwise non-qualifying conversation turn
   - omit `conversation_action_request`
   - fail closed to no new queue item from that descriptor

3. mixed proposal-required turn plus higher-severity provenance-derived queue item
   - preserve both families in one queue
   - preserve final deterministic ordering by `attention_item_sort_key(...)`
   - preserve queue-level `highest_severity` from the first sorted item

4. proposal-only projection with one or more request items
   - emit proposal-only `status` as `pending`
   - preserve `item_count` as the number of qualifying request items
   - preserve only request-family fields
   - ignore all non-request queue families

5. proposal-only projection with no request items
   - emit `status` as `clear`
   - preserve `item_count` as `0`
   - preserve `items` as `[]`

6. proposal-only projection cap
   - preserve `items[:5]`
   - do not widen the projection into queue-budget, conversation-manifest, or world-model semantics

## Exact Allowed Touch Surfaces

The future worker may touch only:

- `ops/cortex/render_status.py`
- `tests/test_cortex_render_status_provenance.py`

## Exact Forbidden Touch Surfaces

The future worker must not touch:

- `_stack` surfaces
- `ops/atlas/converse.py`
- `ops/atlas/awareness.py`
- owner repos
- queue, registry, runtime, manifest, session, merge, or deploy mutation surfaces
- protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, `.playwright-mcp/`

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue conversation_action_request prompt-pack and handoff contract pass 311`

## Marker Decision

- `none`

## Rule

Admit the narrowest live descriptor-backed request slice first: queue emission, inherited deterministic merge, and proposal-only projection, before reopening conversation-runtime or awareness-consumer work.

## Pattern

conversation request contract freeze -> owner admission -> support hold at none yet -> first implementation admission -> prompt-pack -> readiness closeout -> bounded proof landing

## Failure Mode

`Conversation Action Request Slice Inflation`

If the first slice widens beyond `render_status.py` queue emission plus proposal-only projection, the family turns into premature conversation-runtime, awareness-delivery, or queue-mutation work.
