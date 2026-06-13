# AI Long-Run Batch Orchestration Queue-Or-Registry Runtime-State Exact Child-Path Selection Prompt-Pack And Handoff Contract Pass 69 - 2026-06-12

- Date: `2026-06-12`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded handoff-contract design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONTRACT-FREEZE-PASS-1-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-EXACT-CHILD-PATH-SELECTION-CONTRACT-FREEZE-PASS-65-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-EXACT-CHILD-PATH-SELECTION-OWNER-SURFACE-ADMISSION-PASS-66-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-EXACT-CHILD-PATH-SELECTION-SUPPORTING-LANE-ADMISSION-PASS-67-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-EXACT-CHILD-PATH-SELECTION-FIRST-IMPLEMENTATION-ADMISSION-PASS-68-2026-06-12.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@f0203fce`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-owned `runtime-state exact child-path selection` seam.

This pass does not implement code, choose one final queue-home or registry-home destination class, choose one exact filename/schema/snapshot shape, admit runtime-state discovery, or widen into execution semantics.

## Inherited Contract Spine

The future worker must inherit exactly:

- pass 65 exact retained-state child-path contract
- pass 66 owner-surface admission in `ATLAS root control-plane surfaces`
- pass 67 no-separate-support-lane decision
- pass 68 exact first-slice classifier and proof matrix

These are contract inputs, not suggestions.

## Exact Worker Objective

The worker is allowed to pursue one exact implementation objective only:

- implement one root-local helper that loads exactly one explicit candidate path, normalizes it relative to the ATLAS root, classifies it only against the already admitted `queue-home` and `registry-home` destination roots, emits only the frozen exact-child-path decision payload surface, preserves the deferred-artifact note, and proves behavior against the frozen matrix

The worker is not allowed to pursue:

- final queue-home or registry-home selection
- exact filename, schema, or snapshot-shape selection
- runtime-state discovery
- live queue or registry mutation
- validator execution
- supervisor, dispatch, resume, status-transition, or `_stack` execution-home behavior

## Exact Preserved Payload Surface

The worker must preserve exactly this payload surface:

- `normalized_candidate_path`
- `decision`
- `top_level_home_class`
- `child_home_class`
- `layout_family_root`
- `destination_class`
- `destination_root_path`
- `exact_child_path_candidate`
- `artifact_status_note`

Allowed `decision` values only:

- `queue-home-destination-root-still-unresolved`
- `admitted-queue-home-exact-child-path-candidate`
- `registry-home-destination-root-still-unresolved`
- `admitted-registry-home-exact-child-path-candidate`
- `neutral-family-root-without-destination-class`
- `non-admitted-neutral-family-descendant`
- `outside-admitted-neutral-family-root`

Allowed value rules:

- `top_level_home_class` may render only from the first normalized path segment
- `child_home_class` may render only as `runtime/state/` or `none`
- `layout_family_root` may render only as `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/` or `none`
- `destination_class` may render only as `queue-home`, `registry-home`, one non-admitted descendant label beneath the neutral family root, or `none`
- `destination_root_path` may render only as the admitted `queue-home` or `registry-home` root path, or `none`
- `exact_child_path_candidate` may render only as:
  - `none` when the candidate is still only a destination root or fails closed
  - the preserved deeper normalized root-relative path when the candidate is deeper beneath one admitted destination root
- `artifact_status_note` must stay one note that exact filename, schema, snapshot shape, runtime-state discovery, and final artifact-shape choice remain deferred

The worker may not widen this payload into filename plans, schema hints, snapshot hints, runtime-state discovery hints, queue metadata, registry metadata, or lifecycle narration.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

1. explicit queue-home destination-root candidate
   - emit `queue-home-destination-root-still-unresolved`
   - preserve the normalized root-relative path
   - report `queue-home` as the admitted destination class
   - emit the admitted `queue-home` destination root
   - emit `none` as the exact-child-path candidate

2. explicit queue-home exact-child-path candidate
   - emit `admitted-queue-home-exact-child-path-candidate`
   - preserve the deeper normalized root-relative path
   - report `queue-home` as the admitted destination class
   - emit the admitted `queue-home` destination root
   - emit the deeper normalized path as the exact-child-path candidate

3. explicit registry-home destination-root candidate
   - emit `registry-home-destination-root-still-unresolved`
   - preserve the normalized root-relative path
   - report `registry-home` as the admitted destination class
   - emit the admitted `registry-home` destination root
   - emit `none` as the exact-child-path candidate

4. explicit registry-home exact-child-path candidate
   - emit `admitted-registry-home-exact-child-path-candidate`
   - preserve the deeper normalized root-relative path
   - report `registry-home` as the admitted destination class
   - emit the admitted `registry-home` destination root
   - emit the deeper normalized path as the exact-child-path candidate

5. explicit neutral family-root candidate
   - emit `neutral-family-root-without-destination-class`
   - preserve the normalized root-relative path
   - stop below destination-class truth

6. explicit other neutral-family descendant candidate
   - emit `non-admitted-neutral-family-descendant`
   - preserve the normalized root-relative path
   - report that the path stays inside the neutral family root but outside the admitted destination classes

7. explicit outside-neutral-family-root candidate
   - emit `outside-admitted-neutral-family-root`
   - stop below the admitted neutral family root

8. multi-candidate or discovered input mode
   - fail closed on input
   - no decision payload emitted

9. queue, registry, dispatch, resume, or execution hint payload
   - fail closed on input
   - no decision payload emitted

## Exact No-Execution Guard

The worker must carry this wording forward verbatim:

`No-execution guard: this packet may admit future implementation of one explicit retained-state exact-child-path proposal input load, one root-relative path normalization layer, one bounded destination-class-aware exact-child-path classifier, one bounded exact-child-path decision renderer, one deferred-artifact note renderer, and one fail-closed unsupported-input handler for the queue-or-registry runtime-state exact child-path selection slice, but it may not create or mutate queue or registry state, choose one final queue-home or registry-home destination class, choose one exact filename, schema, or snapshot shape, infer final live-artifact defaults, read runtime state to discover existing queue or registry state, execute validation, dispatch work, widen into supervisor behavior, or imply runtime-state discovery, execution-home, status-transition, or operator-adoption proof.`

## Exact Allowed Future Implementation Surfaces

The worker may touch only:

- one future root-local exact-child-path classifier helper surface
- one future explicit local-input loader for exactly one candidate path
- one future root-relative normalization layer
- one future bounded destination-class-aware exact-child-path classifier
- one future bounded decision-rendering layer
- one future deferred-artifact note layer
- one future fixture or static-input proof harness for the admitted matrix
- local non-secret fixtures needed to prove the admitted matrix

## Exact Forbidden Future Implementation Surfaces

The worker must not touch:

- queue or registry creation, mutation, or final artifact-planning surfaces
- final queue-home or registry-home choice surfaces
- exact filename, schema, or snapshot-shape selection surfaces
- runtime-state discovery or directory-crawling surfaces
- validator execution or validator-home integration surfaces
- `_stack` execution-home or Playbook doctrine surfaces
- owner-repo mutation surfaces
- Fitness, `archive/`, deploy/publication, `.env`, or secret surfaces
- supervisor, dispatch, resume, or status-transition surfaces

## Exact Stop Conditions

The worker must stop and return immediately if the slice requires:

- queue or registry mutation
- directory creation or file creation under live runtime state
- final queue-home or registry-home choice
- exact filename, schema, or snapshot-shape invention
- runtime-state discovery or directory crawling
- inferred defaults or candidate-path rewriting beyond root-relative normalization
- payload-surface changes
- validator execution
- supervisor, dispatch, resume, or status-transition behavior
- protected-surface bypass or secret-bearing fixtures
- widening beyond one explicit candidate path

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry runtime-state exact child-path selection implementation-readiness closeout and worker-routing pass 70`

Why:

- the handoff contract is now frozen
- the remaining docs-only question is whether any control-plane prerequisite still blocks routing this exact slice into one bounded implementation worker

## Marker Decision

- `none`

Why:

- this pass narrows worker handoff only
- no code, execution proof, or operator adoption landed

## Rule

Freeze the exact live-path worker packet before authorizing first-slice implementation.

## Pattern

exact child-path contract freeze -> owner admission -> support check -> first implementation admission -> prompt-pack and handoff contract -> implementation-readiness closeout -> implementation

## Failure Mode

`Exact-Child-Path Prompt Scope Bleed`

If the worker handoff is left implicit, the admitted exact-child-path slice widens through prompt wording into filename/schema invention, snapshot-shape choice, runtime-state discovery, live queue mutation, live registry mutation, or execution semantics that the frozen chain does not admit.
