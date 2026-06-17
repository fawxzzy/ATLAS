# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Legacy-Compatibility-Payload First-Implementation Admission Pass 401 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-LEGACY-COMPATIBILITY-PAYLOAD-CONTRACT-FREEZE-PASS-398-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-LEGACY-COMPATIBILITY-PAYLOAD-OWNER-SURFACE-ADMISSION-PASS-399-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-LEGACY-COMPATIBILITY-PAYLOAD-SUPPORTING-LANE-ADMISSION-PASS-400-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@72ea4145`

## Objective

Freeze the smallest exact first implementation slice for the root-local `legacy_compatibility_payload` queue seam without widening beyond the already-rendered descriptor-backed compatibility payload boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one root-local iteration layer inside `attention_queue(...)` over the already-derived `legacy_compatibility_payload`
2. one root-local `legacy_compatibility_signal` emission branch using admitted `session_id`, `source_ref`, `epoch`, `original_session_ref`, and `missing_governed_requirements` only
3. one inherited final merge and deterministic `attention_item_sort_key(...)` ordering layer against the already-admitted broader queue families
4. one top-level broader `attention_queue` payload handoff through `render_status_payload(...)` plus the unchanged top-level `legacy_compatibility` payload handoff

The worker may distinguish only:

- payload entries with truthy `source_ref` versus missing or empty `source_ref`
- `epoch = "legacy_pre_registry"` versus any other epoch value
- fixed `low` severity for `legacy_compatibility_signal`
- admitted `details.session_id`, `details.epoch`, `details.original_session_ref`, and `details.missing_governed_requirements` only
- inherited queue-level `clear` versus `needs_review`
- inherited severity-first ordering and `highest_severity` calculation

## Exact Preserved Payload Surface

The worker must preserve the inherited queue payload surface only:

- `status`
- `item_count`
- `highest_severity`
- `items`

For the `legacy_compatibility_signal` queue item itself, the worker must preserve only:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details.session_id`
- `details.epoch`
- `details.original_session_ref`
- `details.missing_governed_requirements`

For the top-level legacy handoff, the worker must preserve only the existing `legacy_compatibility` payload already produced by `render_status_payload(...)`.

## Exact Mandatory Proof Cases

1. legacy-pre-registry emission
   - emit one `legacy_compatibility_signal` when one legacy payload entry has truthy `source_ref` and `epoch = "legacy_pre_registry"`
   - preserve admitted detail fields only
   - preserve fixed `low` severity

2. non-qualifying legacy omission
   - omit `legacy_compatibility_signal` when the payload entry has missing or empty `source_ref`
   - omit `legacy_compatibility_signal` when the payload entry does not carry `epoch = "legacy_pre_registry"`

3. coexistence with admitted higher-severity broader queue families
   - preserve all admitted families in one queue
   - preserve final deterministic ordering by `attention_item_sort_key(...)`
   - preserve queue-level `highest_severity` from the first sorted item
   - preserve the non-blocking `low` severity placement for legacy compatibility

4. top-level render-status handoff
   - preserve the bounded `attention_queue` payload at top-level `render_status_payload(...)`
   - preserve the unchanged top-level `legacy_compatibility` payload
   - do not widen those handoffs into archive, repair, governed-v1 blocker, or doctrine semantics

5. non-admitted legacy fields stay out of queue payload
   - do not project `cutover_at`
   - do not project `observed_at`
   - do not project `recorded_at`
   - do not project `governed_identity`

6. pass-290 overflow noninteraction
   - preserve `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP` behavior for provenance items only
   - do not let `legacy_compatibility_signal` emit, suppress, or reinterpret `provenance_alert_overflow`

## Exact Allowed Touch Surfaces

The future worker may touch only:

- `ops/cortex/render_status.py`
- `tests/test_cortex_render_status_provenance.py`

## Exact Forbidden Touch Surfaces

The future worker must not touch:

- `_stack` surfaces
- `ops/atlas/*`
- owner repos
- queue, registry, runtime, session, manifest, merge, deploy, archive-mutation, repair, or governed-v1 blocker surfaces
- protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, `.playwright-mcp/`

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue legacy_compatibility_payload prompt-pack and handoff contract pass 402`

## Marker Decision

- `none`

## Rule

Admit the narrowest not-yet-live legacy-compatibility slice first: payload iteration, bounded queue emission, inherited deterministic merge, and top-level handoff, before reopening archive doctrine, repair doctrine, governed-v1 blocker doctrine, or owner-repo authority.

## Pattern

legacy compatibility contract freeze -> owner admission -> support hold at none yet -> first implementation admission -> prompt-pack -> readiness closeout -> bounded proof landing

## Failure Mode

`Legacy Compatibility Slice Inflation`

If the first slice widens beyond payload iteration, bounded queue emission, inherited ordering, and top-level handoff, the family turns into premature archive doctrine, repair doctrine, governed-v1 blocker, or broader legacy payload redesign work.
