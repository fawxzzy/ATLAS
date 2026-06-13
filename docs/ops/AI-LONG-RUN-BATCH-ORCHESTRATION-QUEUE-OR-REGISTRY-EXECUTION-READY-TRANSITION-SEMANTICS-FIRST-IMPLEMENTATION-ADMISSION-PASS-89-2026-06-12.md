# AI Long-Run Batch Orchestration Queue-Or-Registry Execution-Ready Transition Semantics First-Implementation Admission Pass 89 - 2026-06-12

- Date: `2026-06-12`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-EXECUTION-READY-TRANSITION-SEMANTICS-CONTRACT-FREEZE-PASS-86-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-EXECUTION-READY-TRANSITION-SEMANTICS-OWNER-SURFACE-ADMISSION-PASS-87-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-EXECUTION-READY-TRANSITION-SEMANTICS-SUPPORTING-LANE-ADMISSION-PASS-88-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-DISCOVERY-SEMANTICS-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-12.md`
  - `ops/atlas/runtime_state_discovery_semantics.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@556af697`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned `execution-ready transition semantics` seam plus one proof matrix for validating that slice without crossing the no-live-read, no-write, no-execution-ready, and no-execution-home boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one explicit retained-state candidate input loader
2. one root-relative path normalization layer
3. one destination-class-aware, exact-child-path-aware, artifact-shape-aware, and discovery-mode-aware execution-gate classifier
4. one bounded decision renderer
5. one no-live-read, no-write, and no-execution-ready guard
6. one fail-closed unsupported-input handler

The first-slice classifier may distinguish only:

- unresolved destination roots beneath admitted destination classes
- bounded direct-file-read candidates that remain blocked on one future live direct-file read before any execution-ready claim
- bounded directory-scoped-read candidates that remain blocked on one future live directory-scoped read before any execution-ready claim
- unsupported deeper candidates that fail closed below execution-ready posture
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
- `execution_transition_class`
- `artifact_status_note`

Allowed `execution_transition_class` values only:

- `blocked-pending-live-direct-json-read`
- `blocked-pending-live-directory-read`
- `none`

## Exact Mandatory Proof Cases

1. explicit queue-home destination-root candidate
   - emit `queue-home-destination-root-still-unresolved`
   - preserve `execution_transition_class` as `none`

2. explicit queue-home direct-file discovery candidate
   - emit `admitted-queue-home-live-direct-json-read-blocked-before-execution`
   - preserve `execution_transition_class` as `blocked-pending-live-direct-json-read`

3. explicit queue-home directory-scoped discovery candidate
   - emit `admitted-queue-home-live-directory-read-blocked-before-execution`
   - preserve `execution_transition_class` as `blocked-pending-live-directory-read`

4. explicit registry-home destination-root candidate
   - emit `registry-home-destination-root-still-unresolved`

5. explicit registry-home direct-file discovery candidate
   - emit `admitted-registry-home-live-direct-json-read-blocked-before-execution`

6. explicit registry-home directory-scoped discovery candidate
   - emit `admitted-registry-home-live-directory-read-blocked-before-execution`

7. explicit unsupported deeper candidate
   - emit `non-admitted-discovery-mode-execution-transition`
   - preserve `execution_transition_class` as `none`

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

- `AI Long-Run Batch Orchestration queue-or-registry execution-ready transition semantics prompt-pack and handoff contract pass 90`

## Marker Decision

- `none`
