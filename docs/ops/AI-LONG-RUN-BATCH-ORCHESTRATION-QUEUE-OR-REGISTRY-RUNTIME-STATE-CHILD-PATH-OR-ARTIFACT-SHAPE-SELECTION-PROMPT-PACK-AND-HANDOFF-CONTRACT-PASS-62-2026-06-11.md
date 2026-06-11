# AI Long-Run Batch Orchestration Queue-Or-Registry Runtime-State Child-Path Or Artifact-Shape Selection Prompt-Pack And Handoff Contract Pass 62 - 2026-06-11

- Date: `2026-06-11`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded handoff-contract design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONTRACT-FREEZE-PASS-1-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-PATH-OR-ARTIFACT-SHAPE-SELECTION-CONTRACT-FREEZE-PASS-58-2026-06-11.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-PATH-OR-ARTIFACT-SHAPE-SELECTION-OWNER-SURFACE-ADMISSION-PASS-59-2026-06-11.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-PATH-OR-ARTIFACT-SHAPE-SELECTION-SUPPORTING-LANE-ADMISSION-PASS-60-2026-06-11.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-PATH-OR-ARTIFACT-SHAPE-SELECTION-FIRST-IMPLEMENTATION-ADMISSION-PASS-61-2026-06-11.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-owned `runtime-state child-path or artifact-shape selection`.

This pass does not:

- implement code
- create live queue or registry state
- choose one final queue-home or registry-home path
- choose one exact child path, filename, schema, or snapshot shape
- admit `_stack` execution semantics
- admit runtime-state discovery, validator execution, status transitions, supervisor behavior, dispatch, or resume behavior
- mutate runtime state, owner repos, Fitness, `archive/`, deploy/publication surfaces, `.env`, or secrets
- claim that implementation, execution proof, or operator adoption has already landed

## Inherited Contract Spine

The future worker must inherit exactly:

- pass 58 retained-state descendant contract, admitted `queue-home` and `registry-home` destination classes, deferred exact child path, deferred filename/schema/snapshot shape, deferred runtime-state discovery, and continued no-execution boundary
- pass 59 owner-facing home in `ATLAS root control-plane surfaces` plus continued deferral of `_stack`, Playbook, owner-repo, and execution-home ownership
- pass 60 no-separate-support-lane decision at the current threshold
- pass 61 exact destination-class-aware descendant-classifier first slice and exact proof matrix

No worker may reinterpret those seams as suggestions.
They are contract inputs.

## Exact Worker Objective

The next worker is allowed to pursue one exact implementation objective:

- locally implement the already-admitted root-local `runtime-state child-path or artifact-shape selection` first slice as a bounded retained-state descendant classifier that loads exactly one explicit candidate path, normalizes that path relative to the ATLAS root, classifies only the admitted `queue-home` and `registry-home` destination roots plus deeper descendants beneath those roots, emits only the admitted decision payload for unresolved destination roots, deeper descendant candidates, neutral-family-root-without-destination-class, non-admitted neutral-family descendants, or outside-family candidates, preserves the exact deferred-artifact note, and proves behavior against the frozen proof matrix

The worker is not allowed to pursue:

- any broader queue or registry implementation plan
- final queue-home or registry-home choice
- exact child path, filename, schema, or snapshot-shape choice
- runtime-state discovery
- queue or registry mutation
- validator execution or validator-home export
- any status transition, dispatch, resume, or supervisor behavior

## Exact Preserved Payload Surface

The worker must preserve exactly this bounded payload surface:

- one required normalized candidate-path field:
  - `normalized_candidate_path`
- one required decision field:
  - `decision`
- allowed `decision` values only:
  - `admitted-queue-home-destination-root-unresolved`
  - `admitted-queue-home-descendant-candidate`
  - `admitted-registry-home-destination-root-unresolved`
  - `admitted-registry-home-descendant-candidate`
  - `neutral-family-root-without-destination-class`
  - `non-admitted-neutral-family-descendant`
  - `outside-admitted-neutral-family-root`
- one required top-level home-class field:
  - `top_level_home_class`
- one required child-home field:
  - `child_home_class`
- one required neutral retained-state family-root field:
  - `layout_family_root`
- one required retained-state destination-class field:
  - `destination_class`
- one required admitted destination-root field:
  - `destination_root_path`
- one required descendant-tail field:
  - `descendant_tail`
- one required deferred-artifact note field:
  - `artifact_status_note`

The worker may render `top_level_home_class` only from the first path segment derived from the normalized candidate path.

The worker may render `child_home_class` only as:

- `runtime/state/`
- `none`

The worker may render `layout_family_root` only as:

- `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/`
- `none`

The worker may render `destination_class` only as:

- `queue-home`
- `registry-home`
- one non-admitted descendant label beneath the neutral family root
- `none`

The worker may render `destination_root_path` only as:

- `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/`
- `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/registry-home/`
- `none`

The worker may render `descendant_tail` only as:

- `none` when the candidate is exactly one admitted destination root
- one preserved deeper suffix beneath one admitted destination root
- `none` when the candidate fails closed outside an admitted descendant candidate

The worker must preserve `artifact_status_note` only as one note that exact child path, filename, schema, snapshot shape, runtime-state discovery, and final live artifact choice remain deferred.

The worker may render this payload surface only.
The worker may not widen it into live queue-home choice, registry-home choice, directory plans, file plans, queue metadata, registry metadata, discovery hints, execution hints, or lifecycle narration.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

1. explicit queue-home destination-root candidate
   - emit `admitted-queue-home-destination-root-unresolved`
   - preserve the normalized root-relative path
   - report `queue-home` as the admitted destination class
   - report the admitted `queue-home` destination root
   - emit `none` as the descendant tail
   - keep final child-path and artifact-shape truth deferred

2. explicit queue-home descendant candidate
   - emit `admitted-queue-home-descendant-candidate`
   - preserve the deeper normalized root-relative path
   - report `queue-home` as the admitted destination class
   - report the admitted `queue-home` destination root
   - preserve the deeper suffix as the descendant tail
   - keep final child path, filename, schema, and snapshot shape deferred

3. explicit registry-home destination-root candidate
   - emit `admitted-registry-home-destination-root-unresolved`
   - preserve the normalized root-relative path
   - report `registry-home` as the admitted destination class
   - report the admitted `registry-home` destination root
   - emit `none` as the descendant tail
   - keep final child-path and artifact-shape truth deferred

4. explicit registry-home descendant candidate
   - emit `admitted-registry-home-descendant-candidate`
   - preserve the deeper normalized root-relative path
   - report `registry-home` as the admitted destination class
   - report the admitted `registry-home` destination root
   - preserve the deeper suffix as the descendant tail
   - keep final child path, filename, schema, and snapshot shape deferred

5. explicit neutral family-root candidate
   - emit `neutral-family-root-without-destination-class`
   - preserve the normalized root-relative path
   - report that the candidate stops at the neutral family root without narrowing into one admitted destination class

6. explicit other neutral-family descendant candidate
   - emit `non-admitted-neutral-family-descendant`
   - preserve the normalized root-relative path
   - report that the candidate stays inside the neutral family root but outside the admitted `queue-home` and `registry-home` destination classes

7. explicit outside-neutral-family-root candidate
   - emit `outside-admitted-neutral-family-root`
   - report the top-level home class outside the admitted neutral family root

8. multi-candidate or discovered input mode
   - fail closed on input
   - no decision payload emitted

9. queue, registry, dispatch, resume, or execution hint payload
   - fail closed on input
   - no decision payload emitted

These proof cases inherit the pass-61 matrix exactly.

## Exact No-Execution Guard

The worker must carry this wording forward verbatim:

`No-execution guard: this packet may admit future implementation of one explicit retained-state descendant proposal input load, one root-relative path normalization layer, one bounded destination-class-aware retained-state descendant classifier, one bounded retained-state descendant decision renderer, one descendant-tail renderer, one deferred-artifact note renderer, and one fail-closed unsupported-input handler for the queue-or-registry runtime-state child-path or artifact-shape selection slice, but it may not create or mutate queue or registry state, choose one final queue-home or registry-home path, choose one exact child path, filename, schema, or snapshot shape, infer final live-artifact defaults, read runtime state to discover existing queue or registry state, execute validation, dispatch work, widen into supervisor behavior, or imply runtime-state discovery, execution-home, status-transition, or operator-adoption proof.`

## Exact Allowed Future Implementation Surfaces

The worker may touch only:

- one future root-local retained-state descendant classifier helper surface
- one future explicit local-input loader for exactly one candidate path
- one future root-relative normalization layer
- one future bounded destination-class-aware retained-state descendant classifier
- one future bounded decision-rendering layer
- one future descendant-tail rendering layer
- one future deferred-artifact note layer
- one future fixture or static-input proof harness for the admitted matrix
- local non-secret fixtures needed to prove the admitted matrix

The worker may touch only implementation-local surfaces for the admitted first slice.
The worker may not widen into runtime discovery, shared execution homes, or unrelated root systems.

## Exact Forbidden Future Implementation Surfaces

The worker must not touch:

- queue or registry creation, mutation, or final artifact-planning surfaces
- final queue-home or registry-home path-selection surfaces
- exact child-path, filename, schema, or snapshot-shape selection surfaces
- `runtime/state/` discovery or live queue-state inspection surfaces
- validator execution or validator-home integration surfaces
- `_stack` execution-home or Playbook doctrine surfaces
- owner-repo mutation surfaces
- Fitness, `archive/`, deploy/publication, `.env`, secret, or secret-adjacent surfaces
- supervisor, dispatch, resume, or status-transition surfaces
- multi-candidate discovery, summary-rendering, execution-ready semantics, or broader orchestration surfaces

## Exact Stop Conditions

The worker must stop and return immediately if the slice requires:

- queue or registry mutation
- directory creation or file creation
- runtime-state discovery or directory crawling
- final queue-home or registry-home path invention
- exact child path, filename, schema, snapshot shape, or persistence-layout invention
- inferred defaults or candidate-path rewriting beyond root-relative normalization
- any change to the admitted decision payload surface
- validator execution or result rendering
- supervisor, dispatch, resume, or status-transition behavior
- protected-surface bypass or secret-bearing fixtures
- widening beyond one explicit candidate path

If one of those triggers appears, the work is no longer valid first-slice implementation work.

## Exact Handoff Prompt-Pack Spine

Any future worker prompt-pack must include:

1. the exact implementation objective
2. the inherited passes 58 through 61 as frozen inputs
3. the exact preserved payload surface
4. the exact proof matrix
5. the exact no-execution guard verbatim
6. the exact allowed-touch and forbidden-touch surfaces
7. the exact stop-and-return conditions

Mirror surfaces may restate this spine.
They may not redefine it.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry runtime-state child-path or artifact-shape selection implementation-readiness closeout and worker-routing pass 63`

Why:

- the contract spine, first-slice boundary, proof matrix, and worker handoff are now frozen
- the next remaining root-only ambiguity is whether this docs chain is materially complete enough to leave root docs-only and route bounded implementation work without reopening final child-path choice, filename/schema/snapshot-shape choice, runtime-state discovery, live writes, or execution semantics

## Marker Decision

- `none`

Why:

- this pass narrows the worker handoff contract only
- no code, execution proof, or operator adoption landed

## Rule

Freeze the worker handoff contract before authorizing first-slice retained-state descendant implementation work.

## Pattern

retained-state descendant contract freeze -> root owner admission -> support check -> first implementation admission -> prompt-pack and handoff contract -> implementation-readiness closeout -> implementation

## Failure Mode

`Retained-Descendant Prompt Scope Bleed`

If the worker handoff contract is left implicit, the admitted retained-state descendant slice expands through prompt wording into final child-path choice, filename/schema choice, runtime-state discovery, live queue mutation, live registry mutation, or broader authority claims than the frozen design chain actually allows.
