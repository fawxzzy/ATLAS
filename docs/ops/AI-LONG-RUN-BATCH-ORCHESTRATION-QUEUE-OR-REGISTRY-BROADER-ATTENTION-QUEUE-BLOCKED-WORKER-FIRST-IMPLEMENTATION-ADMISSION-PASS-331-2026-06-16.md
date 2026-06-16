# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Blocked-Worker First-Implementation Admission Pass 331 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-BLOCKED-WORKER-CONTRACT-FREEZE-PASS-328-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-BLOCKED-WORKER-OWNER-SURFACE-ADMISSION-PASS-329-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-BLOCKED-WORKER-SUPPORTING-LANE-ADMISSION-PASS-330-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@6461b42c`

## Objective

Freeze the smallest exact first implementation slice for the root-local `blocked_worker` queue seam without widening beyond the already-live worker-state helper boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one root-local latest-descriptor selection layer inside `latest_worker_states(...)`
2. one root-local `blocked_workers(...)` read-model derivation layer that keeps only the admitted blocked-worker states
3. one root-local `blocked_worker` emission branch inside `attention_queue(...)`
4. one inherited final merge and deterministic `attention_item_sort_key(...)` ordering layer against the already-admitted broader queue families
5. one root-local registry-health interaction layer that preserves `blocked_worker` emission even when registry health is unavailable while keeping registry-health-dependent contradiction follow-ons fail-closed
6. one top-level broader `attention_queue` payload handoff through `render_status_payload(...)` plus the unchanged top-level `blocked_workers` read-model payload handoff

The worker may distinguish only:

- latest versus superseded `worker_status` descriptors per `worker_id`
- the admitted worker states `blocked`, `paused`, and `merge_wait`
- non-admitted latest states that fail closed to omission
- `high` severity for `blocked` and `medium` severity for `paused` or `merge_wait`
- healthy versus unhealthy registry state only for contradiction-follow-on omission, not for blocked-worker visibility itself
- inherited queue-level `clear` versus `needs_review`
- inherited severity-first ordering and `highest_severity` calculation

## Exact Preserved Payload Surface

The worker must preserve the inherited queue payload surface only:

- `status`
- `item_count`
- `highest_severity`
- `items`

For the `blocked_worker` queue item itself, the worker must preserve only:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details.worker_id`
- `details.assignment_id`
- `details.state`
- `details.blocked_reason`

For the top-level blocked-worker read-model handoff, the worker must preserve only the existing `blocked_workers` payload already produced by `blocked_workers(...)`.

## Exact Mandatory Proof Cases

1. latest-descriptor qualification
   - preserve only the latest `worker_status` descriptor per `worker_id`
   - omit a worker when the latest descriptor is non-blocking even if an older descriptor was blocking
   - preserve a worker when the latest descriptor is one of the admitted blocked-worker states

2. blocked state emission
   - emit one `blocked_worker`
   - preserve `high` severity when `state == "blocked"`
   - preserve only the admitted detail fields

3. paused or merge-wait emission
   - emit one `blocked_worker`
   - preserve `medium` severity when `state == "paused"` or `state == "merge_wait"`

4. unhealthy registry plus blocked worker
   - preserve `blocked_worker`
   - omit `unknown_tool_surface`
   - omit `unknown_extension_surface`
   - preserve the fail-closed split between blocked-worker visibility and registry-health-dependent contradiction emission

5. mixed blocked-worker plus other broader queue families
   - preserve all admitted families in one queue
   - preserve final deterministic ordering by `attention_item_sort_key(...)`
   - preserve queue-level `highest_severity` from the first sorted item

6. top-level render-status handoff
   - preserve the bounded `attention_queue` payload at top-level `render_status_payload(...)`
   - preserve the unchanged top-level `blocked_workers` payload
   - do not widen those handoffs into launch, dispatch, claim, done, pause, resume, merge, or repair semantics

7. pass-290 overflow noninteraction
   - preserve `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP` behavior for provenance items only
   - do not let `blocked_worker` emit, suppress, or reinterpret `provenance_alert_overflow`

## Exact Allowed Touch Surfaces

The future worker may touch only:

- `ops/cortex/render_status.py`
- `tests/test_cortex_render_status_provenance.py`

## Exact Forbidden Touch Surfaces

The future worker must not touch:

- `_stack` surfaces
- `ops/atlas/*`
- owner repos
- queue, registry, runtime, manifest, session, worker-control, merge, deploy, repair, or contradiction-mutation surfaces
- protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, `.playwright-mcp/`

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue blocked_worker prompt-pack and handoff contract pass 332`

## Marker Decision

- `none`

## Rule

Admit the narrowest live blocked-worker slice first: latest-worker selection, blocked-worker read-model derivation, queue emission, inherited deterministic merge, fail-closed contradiction omission, and top-level handoff, before reopening worker-control, repair, or doctrine semantics.

## Pattern

blocked worker contract freeze -> owner admission -> support hold at none yet -> first implementation admission -> prompt-pack -> readiness closeout -> bounded proof landing

## Failure Mode

`Blocked Worker Slice Inflation`

If the first slice widens beyond latest-worker selection, blocked-worker derivation, queue emission, contradiction omission, inherited ordering, and top-level handoff, the family turns into premature worker-control, repair, or queue-mutation work.
