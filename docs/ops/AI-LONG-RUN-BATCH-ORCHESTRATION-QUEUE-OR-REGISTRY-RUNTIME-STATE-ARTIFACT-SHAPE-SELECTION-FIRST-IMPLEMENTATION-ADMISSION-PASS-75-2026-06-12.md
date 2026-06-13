# AI Long-Run Batch Orchestration Queue-Or-Registry Runtime-State Artifact-Shape Selection First-Implementation Admission Pass 75 - 2026-06-12

- Date: `2026-06-12`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-ARTIFACT-SHAPE-SELECTION-CONTRACT-FREEZE-PASS-72-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-ARTIFACT-SHAPE-SELECTION-OWNER-SURFACE-ADMISSION-PASS-73-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-ARTIFACT-SHAPE-SELECTION-SUPPORTING-LANE-ADMISSION-PASS-74-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-EXACT-CHILD-PATH-SELECTION-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-12.md`
  - `ops/atlas/runtime_state_exact_child_path_selection.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@790e64fd`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned `runtime-state artifact-shape selection` seam plus one proof matrix for validating that slice without crossing the no-write, no-discovery, no-final-filename, no-final-schema, and no-execution boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one explicit exact-child-path proposal input loader
2. one root-relative path normalization layer
3. one destination-class-aware and exact-child-path-aware artifact-shape classifier
4. one bounded decision renderer
5. one no-write, no-discovery, and no-final-artifact guard
6. one fail-closed unsupported-input handler

The first-slice classifier may distinguish only:

- unresolved destination roots beneath admitted destination classes
- preserved deeper directory candidates beneath admitted destination classes
- preserved deeper `.json` file candidates beneath admitted destination classes
- unsupported deeper non-`.json` file shapes beneath admitted destination classes
- neutral-family-root and other existing fail-closed boundaries

## Exact Preserved Payload Surface

The worker must preserve only:

- `normalized_candidate_path`
- `decision`
- `top_level_home_class`
- `child_home_class`
- `layout_family_root`
- `destination_class`
- `destination_root_path`
- `exact_child_path_candidate`
- `artifact_shape_class`
- `artifact_status_note`

Allowed `artifact_shape_class` values only:

- `json-file-candidate`
- `directory-candidate`
- `none`

## Exact Mandatory Proof Cases

1. explicit queue-home destination-root candidate
   - emit `queue-home-destination-root-still-unresolved`
   - preserve no exact child-path candidate
   - preserve `artifact_shape_class` as `none`

2. explicit queue-home `.json` file candidate
   - emit `admitted-queue-home-json-file-artifact-shape-candidate`
   - preserve the deeper exact child-path candidate
   - preserve `artifact_shape_class` as `json-file-candidate`

3. explicit queue-home directory candidate
   - emit `admitted-queue-home-directory-artifact-shape-candidate`
   - preserve the deeper exact child-path candidate
   - preserve `artifact_shape_class` as `directory-candidate`

4. explicit registry-home destination-root candidate
   - emit `registry-home-destination-root-still-unresolved`
   - preserve no exact child-path candidate
   - preserve `artifact_shape_class` as `none`

5. explicit registry-home `.json` file candidate
   - emit `admitted-registry-home-json-file-artifact-shape-candidate`
   - preserve the deeper exact child-path candidate
   - preserve `artifact_shape_class` as `json-file-candidate`

6. explicit registry-home directory candidate
   - emit `admitted-registry-home-directory-artifact-shape-candidate`
   - preserve the deeper exact child-path candidate
   - preserve `artifact_shape_class` as `directory-candidate`

7. explicit unsupported deeper non-`.json` file candidate
   - emit `non-admitted-exact-child-path-artifact-shape`
   - preserve the deeper exact child-path candidate
   - preserve `artifact_shape_class` as `none`

8. explicit neutral family-root candidate
   - emit `neutral-family-root-without-destination-class`

9. explicit other neutral-family descendant candidate
   - emit `non-admitted-neutral-family-descendant`

10. explicit outside-neutral-family-root candidate
    - emit `outside-admitted-neutral-family-root`

11. multi-candidate or discovered input mode
    - fail closed on input
    - no decision payload emitted

12. queue, registry, dispatch, resume, or execution hint payload
    - fail closed on input
    - no decision payload emitted

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry runtime-state artifact-shape selection prompt-pack and handoff contract pass 76`

## Marker Decision

- `none`

## Rule

Freeze coarse artifact-shape candidates before final filename/schema/snapshot-shape or discovery truth.
