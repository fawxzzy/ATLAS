# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Registry-Drift First-Implementation Admission Pass 380 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-REGISTRY-DRIFT-CONTRACT-FREEZE-PASS-377-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-REGISTRY-DRIFT-OWNER-SURFACE-ADMISSION-PASS-378-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-REGISTRY-DRIFT-SUPPORTING-LANE-ADMISSION-PASS-379-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@6c845c69`

## Objective

Freeze the smallest exact first implementation slice for the root-local `registry_drift` queue seam without widening beyond the already-live active-session plus registry-summary helper boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one root-local active-session plus registry-state qualification layer inside `attention_queue(...)` using admitted `active_session.registry_digest`, `registry_state.ok`, and `registry_state.registry_digest` only
2. one root-local `registry_drift` emission branch inside `attention_queue(...)`
3. one inherited final merge and deterministic `attention_item_sort_key(...)` ordering layer against the already-admitted broader queue families
4. one top-level broader `attention_queue` payload handoff through `render_status_payload(...)` plus the unchanged top-level `active_session` read-model handoff

The worker may distinguish only:

- truthy healthy registry versus falsey unhealthy registry
- truthy active-session digest versus missing or falsey active-session digest
- truthy current registry digest versus missing or falsey current registry digest
- unequal digest values versus equal digest values
- fixed `high` severity for `registry_drift`
- admitted `details.session_id`, `details.session_registry_digest`, and `details.current_registry_digest` only
- inherited queue-level `clear` versus `needs_review`
- inherited severity-first ordering and `highest_severity` calculation

## Exact Preserved Payload Surface

The worker must preserve the inherited queue payload surface only:

- `status`
- `item_count`
- `highest_severity`
- `items`

For the `registry_drift` queue item itself, the worker must preserve only:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details.session_id`
- `details.session_registry_digest`
- `details.current_registry_digest`

For the top-level active-session handoff, the worker must preserve only the existing `active_session` payload already produced by `render_status_payload(...)`.

## Exact Mandatory Proof Cases

1. healthy-registry mismatched-digest emission
   - emit one `registry_drift` when `registry_state.ok` is truthy, the admitted active-session digest is truthy, the admitted current registry digest is truthy, and the two digests differ
   - preserve admitted `session_id`, `session_registry_digest`, and `current_registry_digest` detail fields only
   - preserve fixed `high` severity

2. equal-digest omission
   - omit `registry_drift` when both admitted digests are present but equal

3. missing-active-session-digest omission
   - omit `registry_drift` when `active_session.registry_digest` is missing or falsey

4. missing-current-registry-digest omission
   - omit `registry_drift` when `registry_state.registry_digest` is missing or falsey even if the active-session digest is present

5. unhealthy-registry omission and fail-closed split
   - omit `registry_drift` when `registry_state.ok` is falsey
   - preserve separate `registry_error` coexistence only
   - preserve omission of registry-health-dependent contradiction families

6. coexistence with admitted active-session state families
   - preserve separate coexistence with `session_needs_resume`
   - preserve separate coexistence with `resume_failed`
   - preserve separate coexistence with `session_failed`
   - do not widen the digest-mismatch payload into resume, retry, repair, or failure semantics

7. mixed registry-drift plus other broader queue families
   - preserve all admitted families in one queue
   - preserve final deterministic ordering by `attention_item_sort_key(...)`
   - preserve queue-level `highest_severity` from the first sorted item

8. top-level render-status handoff
   - preserve the bounded `attention_queue` payload at top-level `render_status_payload(...)`
   - preserve the unchanged top-level `active_session` payload
   - do not widen those handoffs into repair authority, retry authority, resume authority, merge authority, or doctrine semantics

9. pass-290 overflow noninteraction
   - preserve `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP` behavior for provenance items only
   - do not let `registry_drift` emit, suppress, or reinterpret `provenance_alert_overflow`

## Exact Allowed Touch Surfaces

The future worker may touch only:

- `ops/cortex/render_status.py`
- `tests/test_cortex_render_status_provenance.py`

## Exact Forbidden Touch Surfaces

The future worker must not touch:

- `_stack` surfaces
- `ops/atlas/*`
- owner repos
- queue, registry, runtime, session, manifest, execution-receipt, deploy, repair, retry, resume, merge, or contradiction-mutation surfaces
- protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, `.playwright-mcp/`

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue registry_drift prompt-pack and handoff contract pass 381`

## Marker Decision

- `none`

## Rule

Admit the narrowest live digest-mismatch slice first: active-session plus registry qualification, bounded queue emission, inherited deterministic merge, and top-level handoff, before reopening registry repair, retry execution, resume execution, merge execution, contradiction doctrine, or owner-repo authority.

## Pattern

registry drift contract freeze -> owner admission -> support hold at none yet -> first implementation admission -> prompt-pack -> readiness closeout -> bounded proof landing

## Failure Mode

`Registry Drift Slice Inflation`

If the first slice widens beyond bounded digest qualification, queue emission, inherited ordering, and top-level handoff, the family turns into premature registry repair, retry execution, resume execution, merge execution, contradiction, or broader session-runtime work.
