# AI Long-Run Batch Orchestration Queue-Or-Registry Legacy-Compatibility Top-Level Payload Boundary First-Implementation Admission Pass 408 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-LEGACY-COMPATIBILITY-TOP-LEVEL-PAYLOAD-BOUNDARY-CONTRACT-FREEZE-PASS-405-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-LEGACY-COMPATIBILITY-TOP-LEVEL-PAYLOAD-BOUNDARY-OWNER-SURFACE-ADMISSION-PASS-406-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-LEGACY-COMPATIBILITY-TOP-LEVEL-PAYLOAD-BOUNDARY-SUPPORTING-LANE-ADMISSION-PASS-407-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-LEGACY-COMPATIBILITY-PAYLOAD-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-17.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@72ea4145`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned top-level `legacy_compatibility` payload boundary plus one proof matrix for validating that slice without crossing the no-queue-change, no-archive-action, no-repair-action, no-governed-v1-blocker, and no-runtime-mutation boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one explicit descriptor scan for `artifact_type = "legacy_runtime_backfill"` only
2. one truthy trimmed `source_ref` qualification gate
3. one bounded item projector preserving the admitted top-level legacy fields only
4. one deterministic `observed_at` then `session_id` then `source_ref` sort layer
5. one unchanged top-level `render_status_payload(...)` handoff through `legacy_compatibility`
6. one preserved separation layer where the fuller top-level payload may stay richer than the smaller queue-side `legacy_compatibility_signal`

The first-slice top-level projector may distinguish only:

- qualifying legacy backfill records that survive into the top-level payload
- non-qualifying records that fail closed to omission

## Exact Preserved Payload Surface

The worker must preserve only:

- `session_id`
- `source_ref`
- `original_session_ref`
- `epoch`
- `cutover_at`
- `observed_at`
- `recorded_at`
- `missing_governed_requirements`
- `governed_identity`

Top-level payload rules remain:

- only `legacy_runtime_backfill` descriptors participate
- only records with truthy trimmed `source_ref` survive
- top-level items preserve the admitted field set only
- top-level items sort by `observed_at`, then `session_id`, then `source_ref`
- the payload remains separate from the smaller queue-side `legacy_compatibility_signal`

## Exact Mandatory Proof Cases

1. no qualifying legacy backfill descriptors
   - preserve top-level `legacy_compatibility` as `[]`

2. non-legacy descriptor shapes
   - omit descriptors whose `artifact_type` is not `legacy_runtime_backfill`

3. missing or empty `source_ref`
   - omit legacy backfill descriptors when `source_ref` is missing, empty, or whitespace-only

4. one qualifying legacy descriptor
   - preserve one top-level item with the exact admitted field set
   - preserve richer fields that are intentionally outside the queue-side signal:
     - `cutover_at`
     - `observed_at`
     - `recorded_at`
     - `governed_identity`

5. multiple qualifying legacy descriptors
   - preserve deterministic ordering by `observed_at`, then `session_id`, then `source_ref`

6. top-level and queue-side separation
   - preserve the top-level `legacy_compatibility` payload unchanged while `attention_queue` may still emit only the smaller `legacy_compatibility_signal` subset

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry legacy_compatibility top-level payload boundary prompt-pack and handoff contract pass 409`

## Marker Decision

- `none`

Why:

- this pass freezes the smallest exact implementation slice and proof matrix only
- no code landing, proof execution, or broader operator adoption occurs here

## Rule

Freeze the smallest top-level legacy payload slice and proof matrix before admitting implementation or widening into queue, archive, repair, blocker, or redesign semantics.
