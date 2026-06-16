# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Registry-Error First-Implementation Admission Pass 324 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-REGISTRY-ERROR-CONTRACT-FREEZE-PASS-321-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-REGISTRY-ERROR-OWNER-SURFACE-ADMISSION-PASS-322-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-REGISTRY-ERROR-SUPPORTING-LANE-ADMISSION-PASS-323-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@4c1b9eb0`

## Objective

Freeze the smallest exact first implementation slice for the root-local `registry_error` queue seam without widening beyond the already-live `render_status` helper boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one root-local `registry_error` emission branch inside `attention_queue(...)`
2. one inherited final merge and deterministic `attention_item_sort_key(...)` ordering layer against the already-admitted broader queue families
3. one root-local fail-closed interaction layer that keeps `unknown_tool_surface`, `unknown_extension_surface`, and `registry_drift` omitted when registry health is unavailable
4. one top-level broader `attention_queue` payload handoff through `render_status_payload(...)` with no new summary or projection surface beyond the existing queue contract

The worker may distinguish only:

- falsey `registry_state.ok` with one optional `registry_state.error`
- truthy `registry_state.ok` with no registry-error emission
- inherited queue-level `clear` versus `needs_review`
- inherited severity-first ordering and `highest_severity` calculation

## Exact Preserved Payload Surface

The worker must preserve the inherited queue payload surface only:

- `status`
- `item_count`
- `highest_severity`
- `items`

For the `registry_error` item itself, the worker must preserve only:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details.error`

## Exact Mandatory Proof Cases

1. falsey registry health and no higher-severity queue items
   - emit queue `status` as `needs_review`
   - emit one `registry_error`
   - preserve `highest_severity` as `critical`
   - preserve `details.error`

2. truthy registry health
   - omit `registry_error`
   - fail closed to no new queue item from registry-health state alone

3. falsey registry health plus surfaces that would otherwise qualify for registry-health-dependent contradiction families
   - preserve `registry_error`
   - omit `unknown_tool_surface`
   - omit `unknown_extension_surface`
   - omit `registry_drift`
   - preserve the fail-closed split between registry failure and contradiction-family emission

4. mixed `registry_error` plus lower-severity broader queue families
   - preserve all admitted families in one queue
   - preserve final deterministic ordering by `attention_item_sort_key(...)`
   - preserve queue-level `highest_severity` from the first sorted item

5. top-level render-status handoff
   - preserve the bounded `attention_queue` payload at top-level `render_status_payload(...)`
   - do not widen that handoff into repair, session-runtime, or doctrine semantics

6. pass-290 overflow noninteraction
   - preserve `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP` behavior for provenance items only
   - do not let `registry_error` emit, suppress, or reinterpret `provenance_alert_overflow`

## Exact Allowed Touch Surfaces

The future worker may touch only:

- `ops/cortex/render_status.py`
- `tests/test_cortex_render_status_provenance.py`

## Exact Forbidden Touch Surfaces

The future worker must not touch:

- `_stack` surfaces
- `ops/atlas/*`
- owner repos
- queue, registry, runtime, manifest, session, merge, deploy, repair, or contradiction-mutation surfaces
- protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, `.playwright-mcp/`

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue registry_error prompt-pack and handoff contract pass 325`

## Marker Decision

- `none`

## Rule

Admit the narrowest live registry-failure slice first: queue emission, inherited deterministic merge, fail-closed contradiction omission, and top-level queue handoff, before reopening repair, runtime, or doctrine semantics.

## Pattern

registry error contract freeze -> owner admission -> support hold at none yet -> first implementation admission -> prompt-pack -> readiness closeout -> bounded proof landing

## Failure Mode

`Registry Error Slice Inflation`

If the first slice widens beyond `render_status.py` sentinel emission, contradiction omission, inherited ordering, and top-level queue handoff, the family turns into premature repair, runtime, or queue-mutation work.
