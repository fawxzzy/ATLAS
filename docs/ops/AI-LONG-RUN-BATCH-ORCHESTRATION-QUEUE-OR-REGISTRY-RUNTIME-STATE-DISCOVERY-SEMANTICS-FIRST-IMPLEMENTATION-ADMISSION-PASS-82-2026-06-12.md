# AI Long-Run Batch Orchestration Queue-Or-Registry Runtime-State Discovery Semantics First-Implementation Admission Pass 82 - 2026-06-12

- Date: `2026-06-12`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-DISCOVERY-SEMANTICS-CONTRACT-FREEZE-PASS-79-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-DISCOVERY-SEMANTICS-OWNER-SURFACE-ADMISSION-PASS-80-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-DISCOVERY-SEMANTICS-SUPPORTING-LANE-ADMISSION-PASS-81-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-ARTIFACT-SHAPE-SELECTION-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-12.md`
  - `ops/atlas/runtime_state_artifact_shape_selection.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@1197cede`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned `runtime-state discovery semantics` seam plus one proof matrix for validating that slice without crossing the no-read-execution, no-write, no-final-filename, no-final-schema, and no-execution boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one explicit retained-state candidate input loader
2. one root-relative path normalization layer
3. one destination-class-aware, exact-child-path-aware, and artifact-shape-aware discovery-mode classifier
4. one bounded decision renderer
5. one no-read-execution, no-write, and no-lifecycle guard
6. one fail-closed unsupported-input handler

The first-slice classifier may distinguish only:

- unresolved destination roots beneath admitted destination classes
- preserved deeper `.json` file candidates beneath admitted destination classes that imply one bounded `direct-json-file-read-candidate`
- preserved deeper directory candidates beneath admitted destination classes that imply one bounded `directory-scoped-read-candidate`
- unsupported deeper candidates that fail closed below live read execution
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
- `discovery_mode_class`
- `artifact_status_note`

Allowed `discovery_mode_class` values only:

- `direct-json-file-read-candidate`
- `directory-scoped-read-candidate`
- `none`

## Exact Mandatory Proof Cases

1. explicit queue-home destination-root candidate
   - emit `queue-home-destination-root-still-unresolved`
   - preserve `discovery_mode_class` as `none`

2. explicit queue-home `.json` file candidate
   - emit `admitted-queue-home-direct-json-file-read-candidate`
   - preserve `artifact_shape_class` as `json-file-candidate`
   - preserve `discovery_mode_class` as `direct-json-file-read-candidate`

3. explicit queue-home directory candidate
   - emit `admitted-queue-home-directory-scoped-read-candidate`
   - preserve `artifact_shape_class` as `directory-candidate`
   - preserve `discovery_mode_class` as `directory-scoped-read-candidate`

4. explicit registry-home destination-root candidate
   - emit `registry-home-destination-root-still-unresolved`

5. explicit registry-home `.json` file candidate
   - emit `admitted-registry-home-direct-json-file-read-candidate`

6. explicit registry-home directory candidate
   - emit `admitted-registry-home-directory-scoped-read-candidate`

7. explicit unsupported deeper candidate
   - emit `non-admitted-exact-child-path-discovery-mode`
   - preserve `discovery_mode_class` as `none`

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

- `AI Long-Run Batch Orchestration queue-or-registry runtime-state discovery semantics prompt-pack and handoff contract pass 83`

## Marker Decision

- `none`
