# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Session-Failed First-Implementation Admission Pass 373 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-SESSION-FAILED-CONTRACT-FREEZE-PASS-370-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-SESSION-FAILED-OWNER-SURFACE-ADMISSION-PASS-371-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-SESSION-FAILED-SUPPORTING-LANE-ADMISSION-PASS-372-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@784eb74a`

## Objective

Freeze the smallest exact first implementation slice for the root-local `session_failed` queue seam without widening beyond the already-live active-session helper boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one root-local active-session qualification layer inside `attention_queue(...)` using admitted `session_state` plus `final_status` only
2. one root-local `session_failed` emission branch inside `attention_queue(...)`
3. one inherited final merge and deterministic `attention_item_sort_key(...)` ordering layer against the already-admitted broader queue families
4. one top-level broader `attention_queue` payload handoff through `render_status_payload(...)` plus the unchanged top-level `active_session` read-model handoff

The worker may distinguish only:

- `session_state == "failed"` versus `final_status == "failed"` versus neither admitted field qualifying
- fixed `high` severity for `session_failed`
- admitted `details.session_id` and `details.task_id` only
- inherited queue-level `clear` versus `needs_review`
- inherited severity-first ordering and `highest_severity` calculation

## Exact Preserved Payload Surface

The worker must preserve the inherited queue payload surface only:

- `status`
- `item_count`
- `highest_severity`
- `items`

For the `session_failed` queue item itself, the worker must preserve only:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details.session_id`
- `details.task_id`

For the top-level active-session handoff, the worker must preserve only the existing `active_session` payload already produced by `render_status_payload(...)`.

## Exact Mandatory Proof Cases

1. `session_state`-qualified emission
   - emit one `session_failed` when `session_state == "failed"`
   - preserve admitted `session_id` and `task_id` detail fields only
   - preserve fixed `high` severity

2. `final_status`-qualified emission
   - emit one `session_failed` when `final_status == "failed"` even if `session_state` is different
   - preserve the same bounded payload shape

3. non-qualifying omission
   - omit `session_failed` when neither admitted active-session state field equals `failed`

4. registry-unavailable coexistence
   - preserve `session_failed` when the admitted active-session state qualifies even if registry health is unavailable
   - preserve separate `registry_error` coexistence only
   - do not widen into contradiction, retry, or repair semantics

5. registry-drift coexistence
   - preserve `session_failed` when the admitted active-session state qualifies and the active-session registry digest differs from the current registry digest
   - preserve separate `registry_drift` coexistence only
   - do not widen the terminal-failure payload

6. mixed session-failed plus other broader queue families
   - preserve all admitted families in one queue
   - preserve final deterministic ordering by `attention_item_sort_key(...)`
   - preserve queue-level `highest_severity` from the first sorted item

7. top-level render-status handoff
   - preserve the bounded `attention_queue` payload at top-level `render_status_payload(...)`
   - preserve the unchanged top-level `active_session` payload
   - do not widen those handoffs into retry authority, resume authority, merge authority, or doctrine semantics

8. pass-290 overflow noninteraction
   - preserve `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP` behavior for provenance items only
   - do not let `session_failed` emit, suppress, or reinterpret `provenance_alert_overflow`

## Exact Allowed Touch Surfaces

The future worker may touch only:

- `ops/cortex/render_status.py`
- `tests/test_cortex_render_status_provenance.py`

## Exact Forbidden Touch Surfaces

The future worker must not touch:

- `_stack` surfaces
- `ops/atlas/*`
- owner repos
- queue, registry, runtime, session, manifest, execution-receipt, deploy, repair, retry, or contradiction-mutation surfaces
- protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, `.playwright-mcp/`

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue session_failed prompt-pack and handoff contract pass 374`

## Marker Decision

- `none`

## Rule

Admit the narrowest live terminal-failure slice first: active-session qualifier, bounded queue emission, inherited deterministic merge, and top-level handoff, before reopening retry execution, resume execution, merge execution, registry repair, or broader session-failure doctrine.

## Pattern

session failed contract freeze -> owner admission -> support hold at none yet -> first implementation admission -> prompt-pack -> readiness closeout -> bounded proof landing

## Failure Mode

`Session Failed Slice Inflation`

If the first slice widens beyond bounded active-session qualification, queue emission, inherited ordering, and top-level handoff, the family turns into premature retry execution, resume execution, merge execution, repair, or broader session-failure work.
