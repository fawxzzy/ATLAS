# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Unknown-Tool-Surface First-Implementation Admission Pass 387 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-UNKNOWN-TOOL-SURFACE-CONTRACT-FREEZE-PASS-384-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-UNKNOWN-TOOL-SURFACE-OWNER-SURFACE-ADMISSION-PASS-385-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-UNKNOWN-TOOL-SURFACE-SUPPORTING-LANE-ADMISSION-PASS-386-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@06608625`

## Objective

Freeze the smallest exact first implementation slice for the root-local `unknown_tool_surface` queue seam without widening beyond the already-live active-session governed-surface plus registry-state contradiction boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one root-local governed-surface plus registry-state qualification layer inside `attention_queue(...)` using admitted `active_session.governed_surfaces`, per-scope `tool_id`, `registry_state.ok`, and `registry_state.tool_ids` only
2. one root-local `unknown_tool_surface` emission branch inside the governed-surface contradiction helper used by `attention_queue(...)`
3. one inherited final merge and deterministic `attention_item_sort_key(...)` ordering layer against the already-admitted broader queue families
4. one top-level broader `attention_queue` payload handoff through `render_status_payload(...)` plus the unchanged top-level `active_session` read-model handoff

The worker may distinguish only:

- truthy healthy registry versus falsey unhealthy registry
- admitted governed-surface scopes `context`, `supervision`, and `execution`
- dict-valued governed-surface scope payloads versus non-dict omission
- trimmed non-empty `tool_id` versus missing or empty `tool_id`
- tool ids absent from `registry_state.tool_ids` versus present tool ids
- fixed `high` severity for `unknown_tool_surface`
- admitted `details.scope`, `details.tool_id`, and `details.extension_id` only
- inherited queue-level `clear` versus `needs_review`
- inherited severity-first ordering and `highest_severity` calculation

## Exact Preserved Payload Surface

The worker must preserve the inherited queue payload surface only:

- `status`
- `item_count`
- `highest_severity`
- `items`

For the `unknown_tool_surface` queue item itself, the worker must preserve only:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details.scope`
- `details.tool_id`
- `details.extension_id`

For the top-level active-session handoff, the worker must preserve only the existing `active_session` payload already produced by `render_status_payload(...)`.

## Exact Mandatory Proof Cases

1. healthy-registry unknown-tool emission
   - emit one `unknown_tool_surface` when `registry_state.ok` is truthy, one admitted governed-surface scope is dict-valued, its trimmed `tool_id` is non-empty, and that id is absent from `registry_state.tool_ids`
   - preserve admitted `scope`, `tool_id`, and `extension_id` detail fields only
   - preserve fixed `high` severity

2. known-tool omission
   - omit `unknown_tool_surface` when the trimmed tool id is already present in `registry_state.tool_ids`

3. missing-or-empty-tool omission
   - omit `unknown_tool_surface` when the admitted scope has no `tool_id` or only an empty or whitespace tool id
   - omit `unknown_tool_surface` when the admitted scope is not a dict

4. unhealthy-registry omission and fail-closed split
   - omit `unknown_tool_surface` when `registry_state.ok` is falsey
   - preserve separate `registry_error` coexistence only
   - preserve omission of registry-health-dependent contradiction families

5. coexistence with sibling `unknown_extension_surface` without widening
   - preserve separate coexistence when the same admitted scope also has one unknown `extension_id`
   - do not widen the unknown-tool payload into sibling-extension ownership or doctrine

6. coexistence with admitted active-session state families
   - preserve separate coexistence with `session_needs_resume`
   - preserve separate coexistence with `resume_failed`
   - preserve separate coexistence with `session_failed`
   - do not widen governed-surface contradiction payload into resume, retry, repair, or failure semantics

7. mixed-family deterministic ordering
   - preserve all admitted families in one queue
   - preserve final deterministic ordering by `attention_item_sort_key(...)`
   - preserve queue-level `highest_severity` from the first sorted item

8. top-level render-status handoff
   - preserve the bounded `attention_queue` payload at top-level `render_status_payload(...)`
   - preserve the unchanged top-level `active_session` payload
   - do not widen those handoffs into repair authority, retry authority, resume authority, merge authority, or doctrine semantics

9. pass-290 overflow noninteraction
   - preserve `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP` behavior for provenance items only
   - do not let `unknown_tool_surface` emit, suppress, or reinterpret `provenance_alert_overflow`

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

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue unknown_tool_surface prompt-pack and handoff contract pass 388`

## Marker Decision

- `none`

## Rule

Admit the narrowest live governed-surface unknown-tool slice first: healthy-registry qualification, bounded queue emission, inherited deterministic merge, and top-level handoff, before reopening registry repair, registry mutation, retry execution, resume execution, merge execution, sibling-contradiction doctrine, or owner-repo authority.

## Pattern

unknown tool surface contract freeze -> owner admission -> support hold at none yet -> first implementation admission -> prompt-pack -> readiness closeout -> bounded proof landing

## Failure Mode

`Unknown Tool Surface Slice Inflation`

If the first slice widens beyond healthy-registry qualification, bounded queue emission, inherited ordering, and top-level handoff, the family turns into premature registry repair, registry mutation, retry execution, resume execution, merge execution, sibling-contradiction doctrine, or broader active-session runtime work.
