# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Open-Merge-Request First-Implementation Admission Pass 338 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-OPEN-MERGE-REQUEST-CONTRACT-FREEZE-PASS-335-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-OPEN-MERGE-REQUEST-OWNER-SURFACE-ADMISSION-PASS-336-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-OPEN-MERGE-REQUEST-SUPPORTING-LANE-ADMISSION-PASS-337-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@9c87bb1c`

## Objective

Freeze the smallest exact first implementation slice for the root-local `open_merge_request` queue seam without widening beyond the already-live merge-request helper boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one root-local merge-request lineage grouping and canonical-selection layer inside `classify_merge_requests(...)`
2. one root-local active-read-model derivation layer inside `open_merge_requests(...)`
3. one root-local `open_merge_request` emission branch inside `attention_queue(...)`
4. one inherited final merge and deterministic `attention_item_sort_key(...)` ordering layer against the already-admitted broader queue families
5. one root-local registry-health interaction layer that preserves `open_merge_request` emission even when registry health is unavailable while keeping registry-health-dependent contradiction follow-ons fail-closed
6. one top-level broader `attention_queue` payload handoff through `render_status_payload(...)` plus the unchanged top-level `open_merge_requests` read-model payload handoff

The worker may distinguish only:

- canonical versus superseded merge-request descriptors within one lineage
- completed versus still-open merge-request lineages
- session-linked canonical preference only as part of canonical selection
- fixed `high` severity for `open_merge_request`
- healthy versus unhealthy registry state only for contradiction-follow-on omission, not for open-merge visibility itself
- inherited queue-level `clear` versus `needs_review`
- inherited severity-first ordering and `highest_severity` calculation

## Exact Preserved Payload Surface

The worker must preserve the inherited queue payload surface only:

- `status`
- `item_count`
- `highest_severity`
- `items`

For the `open_merge_request` queue item itself, the worker must preserve only:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details.merge_request_id`
- `details.conflicting_workers`

For the top-level open-merge read-model handoff, the worker must preserve only the existing `open_merge_requests` payload already produced by `open_merge_requests(...)`.

## Exact Mandatory Proof Cases

1. canonical active merge-request selection
   - preserve one canonical merge request per lineage
   - omit superseded descriptors from the active read model
   - preserve an active merge request when the lineage is not completed

2. completed-lineage omission
   - omit a merge-request lineage from `open_merge_requests_payload` when a `supervisor_merge_completion` descriptor closes that lineage

3. open merge-request emission
   - emit one `open_merge_request`
   - preserve fixed `high` severity
   - preserve only the admitted detail fields

4. unhealthy registry plus open merge request
   - preserve `open_merge_request`
   - omit `unknown_tool_surface`
   - omit `unknown_extension_surface`
   - preserve the fail-closed split between open-merge visibility and registry-health-dependent contradiction emission

5. mixed open-merge-request plus other broader queue families
   - preserve all admitted families in one queue
   - preserve final deterministic ordering by `attention_item_sort_key(...)`
   - preserve queue-level `highest_severity` from the first sorted item

6. top-level render-status handoff
   - preserve the bounded `attention_queue` payload at top-level `render_status_payload(...)`
   - preserve the unchanged top-level `open_merge_requests` payload
   - do not widen those handoffs into merge execution, repair, worker mutation, or doctrine semantics

7. pass-290 overflow noninteraction
   - preserve `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP` behavior for provenance items only
   - do not let `open_merge_request` emit, suppress, or reinterpret `provenance_alert_overflow`

## Exact Allowed Touch Surfaces

The future worker may touch only:

- `ops/cortex/render_status.py`
- `tests/test_cortex_render_status_provenance.py`

## Exact Forbidden Touch Surfaces

The future worker must not touch:

- `_stack` surfaces
- `ops/atlas/*`
- owner repos
- queue, registry, runtime, manifest, session, merge-execution, deploy, repair, or contradiction-mutation surfaces
- protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, `.playwright-mcp/`

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue open_merge_request prompt-pack and handoff contract pass 339`

## Marker Decision

- `none`

## Rule

Admit the narrowest live open-merge slice first: lineage canonicalization, active read-model derivation, queue emission, inherited deterministic merge, fail-closed contradiction omission, and top-level handoff, before reopening merge execution, repair, or doctrine semantics.

## Pattern

open merge request contract freeze -> owner admission -> support hold at none yet -> first implementation admission -> prompt-pack -> readiness closeout -> bounded proof landing

## Failure Mode

`Open Merge Request Slice Inflation`

If the first slice widens beyond lineage canonicalization, active-read-model derivation, queue emission, contradiction omission, inherited ordering, and top-level handoff, the family turns into premature merge-execution, repair, or queue-mutation work.
