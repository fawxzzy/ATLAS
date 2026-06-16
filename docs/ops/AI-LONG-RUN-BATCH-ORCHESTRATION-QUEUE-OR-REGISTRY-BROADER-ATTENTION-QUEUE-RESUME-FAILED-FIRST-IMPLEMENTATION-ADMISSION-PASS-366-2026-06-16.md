# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Resume-Failed First-Implementation Admission Pass 366 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-RESUME-FAILED-CONTRACT-FREEZE-PASS-363-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-RESUME-FAILED-OWNER-SURFACE-ADMISSION-PASS-364-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-RESUME-FAILED-SUPPORTING-LANE-ADMISSION-PASS-365-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@8565af6c`

## Objective

Freeze the smallest exact first implementation slice for the root-local `resume_failed` queue seam without widening beyond the already-live active-session helper boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one root-local active-session qualification layer inside `attention_queue(...)` using admitted `session_state` plus `final_status` only
2. one root-local `resume_failed` emission branch inside `attention_queue(...)`
3. one inherited final merge and deterministic `attention_item_sort_key(...)` ordering layer against the already-admitted broader queue families
4. one top-level broader `attention_queue` payload handoff through `render_status_payload(...)` plus the unchanged top-level `active_session` read-model handoff

The worker may distinguish only:

- `session_state == "resume_failed"` versus `final_status == "resume_failed"` versus neither admitted field qualifying
- fixed `high` severity for `resume_failed`
- admitted `details.session_id`, `details.task_id`, and `details.resume_failure_reason` only
- inherited queue-level `clear` versus `needs_review`
- inherited severity-first ordering and `highest_severity` calculation

## Exact Preserved Payload Surface

The worker must preserve the inherited queue payload surface only:

- `status`
- `item_count`
- `highest_severity`
- `items`

For the `resume_failed` queue item itself, the worker must preserve only:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details.session_id`
- `details.task_id`
- `details.resume_failure_reason`

For the top-level active-session handoff, the worker must preserve only the existing `active_session` payload already produced by `render_status_payload(...)`.

## Exact Mandatory Proof Cases

1. `session_state`-qualified emission
   - emit one `resume_failed` when `session_state == "resume_failed"`
   - preserve admitted `session_id`, `task_id`, and `resume_failure_reason` detail fields only
   - preserve fixed `high` severity

2. `final_status`-qualified emission
   - emit one `resume_failed` when `final_status == "resume_failed"` even if `session_state` is different
   - preserve the same bounded payload shape

3. non-qualifying omission
   - omit `resume_failed` when neither admitted active-session state field equals `resume_failed`

4. registry-unavailable coexistence
   - preserve `resume_failed` when the admitted active-session state qualifies even if registry health is unavailable
   - preserve separate `registry_error` coexistence only
   - do not widen into contradiction, retry, or repair semantics

5. registry-drift coexistence
   - preserve `resume_failed` when the admitted active-session state qualifies and the active-session registry digest differs from the current registry digest
   - preserve separate `registry_drift` coexistence only
   - do not widen the resume-failure payload

6. mixed resume-failed plus other broader queue families
   - preserve all admitted families in one queue
   - preserve final deterministic ordering by `attention_item_sort_key(...)`
   - preserve queue-level `highest_severity` from the first sorted item

7. top-level render-status handoff
   - preserve the bounded `attention_queue` payload at top-level `render_status_payload(...)`
   - preserve the unchanged top-level `active_session` payload
   - do not widen those handoffs into retry authority, resume authority, merge authority, or doctrine semantics

8. pass-290 overflow noninteraction
   - preserve `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP` behavior for provenance items only
   - do not let `resume_failed` emit, suppress, or reinterpret `provenance_alert_overflow`

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

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue resume_failed prompt-pack and handoff contract pass 367`

## Marker Decision

- `none`

## Rule

Admit the narrowest live resume-failure slice first: active-session qualifier, bounded queue emission, inherited deterministic merge, and top-level handoff, before reopening retry execution, resume execution, merge execution, registry repair, or broader failure doctrine.

## Pattern

resume failed contract freeze -> owner admission -> support hold at none yet -> first implementation admission -> prompt-pack -> readiness closeout -> bounded proof landing

## Failure Mode

`Resume Failed Slice Inflation`

If the first slice widens beyond bounded active-session qualification, queue emission, inherited ordering, and top-level handoff, the family turns into premature retry execution, resume execution, merge execution, repair, or broader session-failure work.
