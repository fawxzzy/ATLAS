# AI Long-Run Batch Orchestration Queue-Or-Registry Runtime-State Child-Home Selection Prompt-Pack And Handoff Contract Pass 41 - 2026-06-10

- Date: `2026-06-10`
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
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-HOME-SELECTION-CONTRACT-FREEZE-PASS-37-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-HOME-SELECTION-OWNER-SURFACE-ADMISSION-PASS-38-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-HOME-SELECTION-SUPPORTING-LANE-ADMISSION-PASS-39-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-HOME-SELECTION-FIRST-IMPLEMENTATION-ADMISSION-PASS-40-2026-06-10.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-owned `runtime-state child-home selection`.

This pass does not:

- implement code
- create live queue or registry state
- choose one final queue-home or registry-home path
- choose one exact runtime subtree, filename, schema, snapshot shape, or persistence layout
- admit `_stack` execution semantics
- admit validator execution, status transitions, supervisor behavior, dispatch, or resume behavior
- mutate runtime state, owner repos, Fitness, `archive/`, deploy/publication surfaces, `.env`, or secrets
- claim that implementation, execution proof, or operator adoption has already landed

## Inherited Contract Spine

The future worker must inherit exactly:

- pass 37 child-home contract, `runtime/state/` admission, `runtime/receipts/` exclusion, deferred concrete layout, and continued no-execution boundary
- pass 38 owner-facing home in `ATLAS root control-plane surfaces` plus continued deferral of `_stack`, Playbook, owner-repo, and `runtime/` implementation ownership
- pass 39 no-separate-support-lane decision at the current threshold
- pass 40 exact first implementation slice and exact proof matrix

No worker may reinterpret those seams as suggestions.
They are contract inputs.

## Exact Worker Objective

The next worker is allowed to pursue one exact implementation objective:

- locally implement the already-admitted root-local `runtime-state child-home selection` first slice as a bounded child-home classifier that loads exactly one explicit candidate path, normalizes that path relative to the ATLAS root, classifies only the admitted child-home branch inside `runtime/`, emits only the admitted decision payload for `runtime/state/`, `runtime/receipts/`, other `runtime/*` child homes, or outside-runtime candidates, preserves the exact deferred-layout note, and proves behavior against the frozen proof matrix

The worker is not allowed to pursue:

- any broader queue or registry implementation plan
- concrete runtime-layout choice
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
  - `admitted-state-child-home-candidate`
  - `excluded-receipt-history-child-home`
  - `non-admitted-runtime-child-home`
  - `outside-runtime-home-family`
- one required top-level home-class field:
  - `top_level_home_class`
- one required child-home field:
  - `child_home_class`
- one required deferred-layout note field:
  - `layout_status_note`

The worker may render `top_level_home_class` only from the first path segment derived from the normalized candidate path.

The worker may render `child_home_class` only as:

- `runtime/state/`
- `runtime/receipts/`
- one non-admitted sibling `runtime/*` child-home class
- `none` when the candidate is outside the runtime family

The worker must preserve `layout_status_note` only as one note that exact runtime subtree, filename, schema, snapshot shape, and persistence layout remain deferred.

The worker may render this payload surface only.
The worker may not widen it into live queue-home choice, registry-home choice, directory plans, file plans, queue metadata, execution hints, or lifecycle narration.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

1. explicit `runtime/state/` root candidate
   - emit `admitted-state-child-home-candidate`
   - preserve `runtime/state/` in normalized root-relative form
   - report `runtime/` as the top-level home class
   - report `runtime/state/` as the admitted child-home class

2. explicit `runtime/state/` descendant candidate
   - emit `admitted-state-child-home-candidate`
   - preserve the deeper normalized root-relative path
   - keep exact layout deferred

3. explicit `runtime/receipts/` root candidate
   - emit `excluded-receipt-history-child-home`
   - preserve `runtime/receipts/` in normalized root-relative form
   - report `runtime/receipts/` as excluded

4. explicit `runtime/receipts/` descendant candidate
   - emit `excluded-receipt-history-child-home`
   - preserve the deeper normalized root-relative path
   - keep receipt history excluded from live mutable queue truth

5. explicit other `runtime/*` child-home candidate
   - emit `non-admitted-runtime-child-home`
   - preserve the normalized root-relative path
   - report the exact sibling runtime child-home as non-admitted

6. explicit non-runtime top-level candidate
   - emit `outside-runtime-home-family`
   - report the top-level home class outside the current child-home family

7. multi-candidate or discovered input mode
   - fail closed on input
   - no decision payload emitted

8. queue, registry, dispatch, resume, or execution hint payload
   - fail closed on input
   - no decision payload emitted

These proof cases inherit the pass-40 matrix exactly.

## Exact No-Execution Guard

The worker must carry this wording forward verbatim:

`No-execution guard: this packet may admit future implementation of one explicit child-home proposal input load, one root-relative path normalization layer, one bounded runtime child-home classifier, one bounded child-home decision renderer, one deferred-layout note renderer, and one fail-closed unsupported-input handler for the queue-or-registry runtime-state child-home selection slice, but it may not create or mutate queue or registry state, choose one final queue-home or registry-home path, choose one exact runtime subtree, filename, schema, snapshot shape, or persistence layout, infer concrete runtime layout defaults, read runtime state to discover existing queue state, execute validation, dispatch work, widen into supervisor behavior, or imply execution-home, status-transition, or operator-adoption proof.`

## Exact Allowed Future Implementation Surfaces

The worker may touch only:

- one future root-local child-home classifier helper surface
- one future explicit local-input loader for exactly one candidate path
- one future root-relative normalization layer
- one future bounded runtime child-home classifier
- one future bounded decision-rendering layer
- one future deferred-layout note layer
- one future fixture or static-input proof harness for the admitted matrix
- local non-secret fixtures needed to prove the admitted matrix

The worker may touch only implementation-local surfaces for the admitted first slice.
The worker may not widen into runtime storage, shared execution homes, or unrelated root systems.

## Exact Forbidden Future Implementation Surfaces

The worker must not touch:

- queue or registry creation, mutation, or storage-layout planning surfaces
- concrete runtime subtree, filename, or schema-selection surfaces
- `runtime/` state discovery or live queue-state inspection surfaces
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
- concrete runtime subtree, filename, schema, snapshot shape, or persistence-layout invention
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
2. the inherited passes 37 through 40 as frozen inputs
3. the exact preserved payload surface
4. the exact proof matrix
5. the exact no-execution guard verbatim
6. the exact allowed-touch and forbidden-touch surfaces
7. the exact stop-and-return conditions

Mirror surfaces may restate this spine.
They may not redefine it.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry runtime-state child-home selection implementation-readiness closeout and worker-routing pass 42`

Why:

- the contract spine, first-slice boundary, proof matrix, and worker handoff are now frozen
- the next remaining root-only ambiguity is whether this docs chain is materially complete enough to leave root docs-only and route bounded implementation work without reopening concrete runtime layout, queue mutation, or execution semantics

## Marker Decision

- `none`

Why:

- this pass narrows the worker handoff contract only
- no code, execution proof, or operator adoption landed

## Rule

Freeze the worker handoff contract before authorizing first-slice child-home classifier implementation work.

## Pattern

child-home contract freeze -> root owner admission -> support check -> first implementation admission -> prompt-pack and handoff contract -> implementation-readiness closeout -> implementation

## Failure Mode

`Child-Home Prompt Scope Bleed`

If the worker handoff contract is left implicit, the admitted child-home slice expands through prompt wording into concrete runtime-layout choice, queue mutation, execution semantics, or broader authority claims than the frozen design chain actually allows.
