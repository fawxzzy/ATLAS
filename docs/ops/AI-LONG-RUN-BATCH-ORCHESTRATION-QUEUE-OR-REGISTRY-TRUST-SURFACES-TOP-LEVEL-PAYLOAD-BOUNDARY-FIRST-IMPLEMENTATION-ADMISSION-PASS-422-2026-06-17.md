# AI Long-Run Batch Orchestration Queue-Or-Registry Trust-Surfaces Top-Level Payload Boundary First-Implementation Admission Pass 422 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-TRUST-SURFACES-TOP-LEVEL-PAYLOAD-BOUNDARY-CONTRACT-FREEZE-PASS-419-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-TRUST-SURFACES-TOP-LEVEL-PAYLOAD-BOUNDARY-OWNER-SURFACE-ADMISSION-PASS-420-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-TRUST-SURFACES-TOP-LEVEL-PAYLOAD-BOUNDARY-SUPPORTING-LANE-ADMISSION-PASS-421-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-QUARANTINED-TRUST-SURFACE-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-16.md`
  - `docs/ops/ATLAS-STATUS-RUNBOOK.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@6f9e86a3`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned top-level `trust_surfaces` payload boundary plus one proof matrix for validating that slice without crossing the no-summary-widening, no-queue-change, no-archive-hydration, no-trust-promotion, no-remediation-routing, and no-runtime-mutation boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one explicit descriptor scan for `artifact_type = "knowledge_catalog"` only
2. one `trust_class != "trusted"` qualification gate
3. one bounded item projector preserving the admitted top-level trust-surface fields only
4. one deterministic `trust_class` then `archive_id` sort layer
5. one unchanged top-level `render_status_payload(...)` handoff through `trust_surfaces`
6. one preserved separation layer where the raw top-level payload remains distinct from the fuller top-level `trust_posture` summary and the narrower queue-side `quarantined_trust_surface` family

The first-slice top-level projector may distinguish only:

- qualifying non-`trusted` `knowledge_catalog` descriptors that survive into the top-level payload
- non-qualifying descriptors that fail closed to omission

## Exact Preserved Payload Surface

The worker must preserve only:

- `archive_id`
- `knowledge_ref`
- `trust_class`
- `indexing_profile`
- `promotion_status`
- `source_ref`

Top-level payload rules remain:

- only `knowledge_catalog` descriptors participate
- only descriptors whose `trust_class` is not `trusted` survive
- `knowledge_ref` may resolve only as `knowledge:{archive_id}` when `archive_id` exists, otherwise `None`
- top-level items preserve the admitted field set only
- top-level items sort by `trust_class`, then `archive_id`
- the payload remains separate from the richer top-level `trust_posture` summary and the smaller queue-side `quarantined_trust_surface` subset

## Exact Mandatory Proof Cases

1. no qualifying trust-surface descriptors
   - preserve top-level `trust_surfaces` as `[]`

2. non-knowledge or `trusted` descriptors
   - omit descriptors whose `artifact_type` is not `knowledge_catalog`
   - omit descriptors whose `trust_class` is `trusted`

3. one qualifying restricted trust surface
   - preserve one top-level item with the exact admitted field set
   - preserve `trust_class` as `restricted`
   - preserve `knowledge_ref` as `knowledge:{archive_id}`

4. one qualifying untrusted trust surface
   - preserve one top-level item with the exact admitted field set
   - preserve `trust_class` as `untrusted`
   - preserve item metadata without adding derived `read_mode`, counts, or summary status

5. multiple qualifying trust surfaces
   - preserve deterministic ordering by `trust_class`, then `archive_id`

6. top-level versus summary and queue separation
   - preserve the raw top-level `trust_surfaces` payload unchanged while `trust_posture` may stay richer and `attention_queue` may still emit only the narrower `quarantined_trust_surface` subset

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry trust_surfaces top-level payload boundary prompt-pack and handoff contract pass 423`

## Marker Decision

- `none`

Why:

- this pass freezes the smallest exact implementation slice and proof matrix only
- no code landing, proof execution, or broader operator adoption occurs here

## Rule

Freeze the smallest top-level trust-surfaces payload slice and proof matrix before admitting implementation or widening into summary semantics, queue semantics, archive hydration, trust promotion, remediation, or doctrine semantics.
