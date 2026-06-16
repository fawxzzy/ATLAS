# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Quarantined-Trust-Surface First-Implementation Admission Pass 317 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-QUARANTINED-TRUST-SURFACE-CONTRACT-FREEZE-PASS-314-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-QUARANTINED-TRUST-SURFACE-OWNER-SURFACE-ADMISSION-PASS-315-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-QUARANTINED-TRUST-SURFACE-SUPPORTING-LANE-ADMISSION-PASS-316-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@c2b7be30`

## Objective

Freeze the smallest exact first implementation slice for the root-local `quarantined_trust_surface` queue seam without widening beyond the already-live `render_status` helper boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one descriptor-derived `quarantined_trust_surface` emission branch inside `attention_queue(...)`
2. one inherited final merge and deterministic `attention_item_sort_key(...)` ordering layer against the already-admitted broader queue families
3. one top-level broader `attention_queue` payload handoff through `render_status_payload(...)` with no new summary or projection surface beyond the existing queue contract

The worker may distinguish only:

- `knowledge_catalog` descriptor posture that reaches `trust_surfaces(...)` and remains `trust_class == "untrusted"`
- non-qualifying descriptor posture that must fail closed to no emitted quarantine queue item
- queue-level `clear` versus `needs_review`
- inherited severity-first ordering and `highest_severity` calculation

## Exact Preserved Payload Surface

The worker must preserve the inherited queue payload surface only:

- `status`
- `item_count`
- `highest_severity`
- `items`

For the `quarantined_trust_surface` item itself, the worker must preserve only:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details.archive_id`
- `details.indexing_profile`
- `details.promotion_status`

## Exact Mandatory Proof Cases

1. one untrusted `knowledge_catalog` descriptor and no higher-severity queue items
   - emit queue `status` as `needs_review`
   - emit one `quarantined_trust_surface`
   - preserve `highest_severity` as `medium`
   - preserve `archive_id`, `indexing_profile`, and `promotion_status`

2. one non-qualifying descriptor
   - omit `quarantined_trust_surface`
   - fail closed to no new queue item from that descriptor

3. one descriptor that reaches trust posture but is not `untrusted`
   - omit `quarantined_trust_surface`
   - preserve the separation between broader trust posture and the narrower quarantine queue family

4. mixed untrusted trust surface plus higher-severity provenance-derived queue item
   - preserve both families in one queue
   - preserve final deterministic ordering by `attention_item_sort_key(...)`
   - preserve queue-level `highest_severity` from the first sorted item

5. mixed untrusted trust surface plus other non-quarantine broader queue families
   - preserve all admitted families in one queue
   - preserve final deterministic ordering
   - do not create any new summary or projection surface beyond the existing queue contract

6. pass-290 overflow noninteraction
   - preserve `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP` behavior for provenance items only
   - do not let `quarantined_trust_surface` emit, suppress, or reinterpret `provenance_alert_overflow`

## Exact Allowed Touch Surfaces

The future worker may touch only:

- `ops/cortex/render_status.py`
- `tests/test_cortex_render_status_provenance.py`

## Exact Forbidden Touch Surfaces

The future worker must not touch:

- `_stack` surfaces
- `ops/atlas/*`
- owner repos
- queue, registry, runtime, manifest, session, merge, deploy, trust-promotion, or archive-mutation surfaces
- protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, `.playwright-mcp/`

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue quarantined_trust_surface prompt-pack and handoff contract pass 318`

## Marker Decision

- `none`

## Rule

Admit the narrowest live descriptor-derived quarantine slice first: queue emission plus inherited deterministic merge, before reopening trust-remediation, archive, or broader runtime semantics.

## Pattern

quarantined trust surface contract freeze -> owner admission -> support hold at none yet -> first implementation admission -> prompt-pack -> readiness closeout -> bounded proof landing

## Failure Mode

`Quarantined Trust Surface Slice Inflation`

If the first slice widens beyond `render_status.py` queue emission plus inherited ordering, the family turns into premature trust-remediation, archive-routing, or queue-mutation work.
