# AI Long-Run Batch Orchestration Queue-Or-Registry Runtime-State Concrete-Layout Selection Prompt-Pack And Handoff Contract Pass 48 - 2026-06-11

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
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CONCRETE-LAYOUT-SELECTION-CONTRACT-FREEZE-PASS-44-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CONCRETE-LAYOUT-SELECTION-OWNER-SURFACE-ADMISSION-PASS-45-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CONCRETE-LAYOUT-SELECTION-SUPPORTING-LANE-ADMISSION-PASS-46-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CONCRETE-LAYOUT-SELECTION-FIRST-IMPLEMENTATION-ADMISSION-PASS-47-2026-06-11.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-owned `runtime-state concrete-layout selection`.

This pass does not:

- implement code
- create live queue or registry state
- choose one final queue-home or registry-home path
- choose one exact filename, schema, or snapshot shape
- admit `_stack` execution semantics
- admit runtime-state discovery, validator execution, status transitions, supervisor behavior, dispatch, or resume behavior
- mutate runtime state, owner repos, Fitness, `archive/`, deploy/publication surfaces, `.env`, or secrets
- claim that implementation, execution proof, or operator adoption has already landed

## Inherited Contract Spine

The future worker must inherit exactly:

- pass 44 retained-state descendant-layout contract, admitted `runtime/state/` child-home class, deferred exact descendant contents, deferred exact filename/schema/snapshot shape, deferred final queue-home or registry-home choice, deferred runtime-state discovery, and continued no-execution boundary
- pass 45 owner-facing home in `ATLAS root control-plane surfaces` plus continued deferral of `_stack`, Playbook, owner-repo, and `runtime/state/` implementation ownership
- pass 46 no-separate-support-lane decision at the current threshold
- pass 47 exact retained-state layout-family classifier first slice and exact proof matrix

No worker may reinterpret those seams as suggestions.
They are contract inputs.

## Exact Worker Objective

The next worker is allowed to pursue one exact implementation objective:

- locally implement the already-admitted root-local `runtime-state concrete-layout selection` first slice as a bounded retained-state layout-family classifier that loads exactly one explicit candidate path, normalizes that path relative to the ATLAS root, classifies only the admitted neutral `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/` family root and descendants beneath that root, emits only the admitted decision payload for that neutral family root, descendants beneath that root, retained-state siblings, or outside-child-home candidates, preserves the exact deferred-layout note, and proves behavior against the frozen proof matrix

The worker is not allowed to pursue:

- any broader queue or registry implementation plan
- final queue-home or registry-home choice
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
  - `admitted-neutral-layout-family-root`
  - `admitted-neutral-layout-family-descendant`
  - `non-admitted-retained-state-sibling`
  - `outside-admitted-state-child-home`
- one required top-level home-class field:
  - `top_level_home_class`
- one required child-home field:
  - `child_home_class`
- one required retained-state layout-family field:
  - `layout_family_root`
- one required deferred-layout note field:
  - `layout_status_note`

The worker may render `top_level_home_class` only from the first path segment derived from the normalized candidate path.

The worker may render `child_home_class` only as:

- `runtime/state/`
- `none`

The worker may render `layout_family_root` only as:

- `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/`
- one non-admitted retained-state sibling root beneath `runtime/state/`
- `none` when the candidate is outside the admitted child-home family

The worker must preserve `layout_status_note` only as one note that exact filename, schema, snapshot shape, runtime-state discovery, and final queue-home or registry-home choice remain deferred.

The worker may render this payload surface only.
The worker may not widen it into live queue-home choice, registry-home choice, directory plans, file plans, queue metadata, discovery hints, execution hints, or lifecycle narration.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

1. explicit neutral family-root candidate
   - emit `admitted-neutral-layout-family-root`
   - preserve the normalized root-relative path
   - report `runtime/` as the top-level home class
   - report `runtime/state/` as the admitted child-home class
   - report the neutral family root exactly

2. explicit neutral family descendant candidate
   - emit `admitted-neutral-layout-family-descendant`
   - preserve the deeper normalized root-relative path
   - keep final live-state shape deferred

3. explicit retained-state sibling candidate
   - emit `non-admitted-retained-state-sibling`
   - preserve the normalized root-relative path
   - report the exact retained-state sibling root as non-admitted

4. explicit other lane-descendant candidate
   - emit `non-admitted-retained-state-sibling`
   - preserve the normalized root-relative path
   - report that the candidate remains under `runtime/state/ai-long-run-batch-orchestration/` but outside the admitted `queue-or-registry/` neutral family root

5. explicit outside-child-home candidate
   - emit `outside-admitted-state-child-home`
   - report the top-level home class outside the current retained-state child-home family

6. multi-candidate or discovered input mode
   - fail closed on input
   - no decision payload emitted

7. queue, registry, dispatch, resume, or execution hint payload
   - fail closed on input
   - no decision payload emitted

These proof cases inherit the pass-47 matrix exactly.

## Exact No-Execution Guard

The worker must carry this wording forward verbatim:

`No-execution guard: this packet may admit future implementation of one explicit retained-state layout proposal input load, one root-relative path normalization layer, one bounded retained-state layout-family classifier, one bounded retained-state layout decision renderer, one deferred-layout note renderer, and one fail-closed unsupported-input handler for the queue-or-registry runtime-state concrete-layout selection slice, but it may not create or mutate queue or registry state, choose one final queue-home or registry-home path, choose one exact filename, schema, or snapshot shape, infer final live-state layout defaults, read runtime state to discover existing queue state, execute validation, dispatch work, widen into supervisor behavior, or imply runtime-state discovery, execution-home, status-transition, or operator-adoption proof.`

## Exact Allowed Future Implementation Surfaces

The worker may touch only:

- one future root-local retained-state layout-family classifier helper surface
- one future explicit local-input loader for exactly one candidate path
- one future root-relative normalization layer
- one future bounded retained-state layout-family classifier
- one future bounded decision-rendering layer
- one future deferred-layout note layer
- one future fixture or static-input proof harness for the admitted matrix
- local non-secret fixtures needed to prove the admitted matrix

The worker may touch only implementation-local surfaces for the admitted first slice.
The worker may not widen into runtime discovery, shared execution homes, or unrelated root systems.

## Exact Forbidden Future Implementation Surfaces

The worker must not touch:

- queue or registry creation, mutation, or final layout-planning surfaces
- final queue-home or registry-home path-selection surfaces
- filename, schema, or snapshot-shape selection surfaces
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
- filename, schema, snapshot shape, or persistence-layout invention
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
2. the inherited passes 44 through 47 as frozen inputs
3. the exact preserved payload surface
4. the exact proof matrix
5. the exact no-execution guard verbatim
6. the exact allowed-touch and forbidden-touch surfaces
7. the exact stop-and-return conditions

Mirror surfaces may restate this spine.
They may not redefine it.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry runtime-state concrete-layout selection implementation-readiness closeout and worker-routing pass 49`

Why:

- the contract spine, first-slice boundary, proof matrix, and worker handoff are now frozen
- the next remaining root-only ambiguity is whether this docs chain is materially complete enough to leave root docs-only and route bounded implementation work without reopening final queue-home choice, runtime-state discovery, live writes, or execution semantics

## Marker Decision

- `none`

Why:

- this pass narrows the worker handoff contract only
- no code, execution proof, or operator adoption landed

## Rule

Freeze the worker handoff contract before authorizing first-slice retained-state layout-family implementation work.

## Pattern

retained-state layout contract freeze -> root owner admission -> support check -> first implementation admission -> prompt-pack and handoff contract -> implementation-readiness closeout -> implementation

## Failure Mode

`Retained-Layout Prompt Scope Bleed`

If the worker handoff contract is left implicit, the admitted retained-state layout slice expands through prompt wording into final queue-home choice, runtime-state discovery, live queue mutation, or broader authority claims than the frozen design chain actually allows.
