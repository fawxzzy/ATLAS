# AI Long-Run Batch Orchestration Queue-Or-Registry Batch-Entry Validator Prompt-Pack And Handoff Contract Pass 6 - 2026-06-09

- Date: `2026-06-09`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded handoff-contract design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONTRACT-FREEZE-PASS-1-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-OWNER-SURFACE-ADMISSION-PASS-2-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SUPPORTING-LANE-ADMISSION-PASS-3-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-FIRST-IMPLEMENTATION-SLICE-SELECTION-PASS-4-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BATCH-ENTRY-VALIDATOR-FIRST-SLICE-ADMISSION-PASS-5-2026-06-09.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-owned `batch-entry validator`.

This pass does not:

- implement code
- choose queue or registry storage placement
- create live queue or registry entries
- admit `_stack` execution semantics
- admit supervisor, dispatch, or resume behavior
- mutate runtime state, owner repos, Fitness, `archive/`, deploy/publication surfaces, `.env`, or secrets
- claim that implementation, execution-home proof, or operator adoption has already landed

## Inherited Contract Spine

The future worker must inherit exactly:

- pass 1 batch-entry field contract, bounded status vocabulary, protected-surface exclusion expectations, and storage-agnostic meaning
- pass 2 owner-facing home in `ATLAS root control-plane surfaces` plus deferral of `_stack`, Playbook, owner-repo, and `runtime/` ownership
- pass 3 no-separate-support-lane decision at the current threshold
- pass 4 first-slice selection of `batch-entry validator`
- pass 5 exact first implementation slice and exact proof matrix

No worker may reinterpret those seams as suggestions.
They are contract inputs.

## Exact Worker Objective

The next worker is allowed to pursue one exact implementation objective:

- locally implement the already-admitted root-local `batch-entry validator` first slice as a bounded validator surface that loads exactly one explicit candidate-entry payload, enforces the required fields, enforces bounded status and optional-field discipline, checks single-owner and single-target boundaries, checks protected-surface exclusions and cited-receipt presence, renders the frozen fail-closed result vocabulary, and proves behavior against the frozen proof matrix

The worker is not allowed to pursue:

- any broader queue or registry implementation plan
- any new evidence class
- any new result vocabulary or storage semantics
- any runtime-state discovery behavior
- any entry creation, mutation, dispatch, or supervisor behavior

## Exact Preserved Payload Surface

The worker must preserve exactly this bounded payload surface:

- one required result classifier field:
  - `result`
- allowed `result` values only:
  - `valid`
  - `invalid-missing-field`
  - `invalid-status`
  - `invalid-optional-field`
  - `invalid-owner-boundary`
  - `invalid-target-boundary`
  - `invalid-protected-surface-exclusion`
  - `invalid-input`
- one required entry-identity echo when present in the input:
  - `entry_id`
- one optional admitted boundary-context echo set:
  - `owner_repo`
  - `target_branch_or_worktree`
  - `status`
- one optional failure-detail set, only when triggered:
  - `missing_fields`
  - `invalid_fields`
  - `boundary_failure`
  - `protected_surface_failure`
  - `input_failure_reason`
  - `cited_receipt_fields`

The worker may render this payload surface only.
The worker may not widen it into queue metadata, supervisor hints, path planning, or execution-state narration.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

1. valid single candidate entry
   - bounded `valid` payload only
   - no failure-only fields emitted

2. missing required field
   - fail closed to `invalid-missing-field`
   - exact missing field set present

3. invalid status value
   - fail closed to `invalid-status`
   - offending value reported through the admitted invalid-field surface

4. optional-field misuse
   - fail closed to `invalid-optional-field`
   - reject optional fields outside their triggering condition

5. multi-owner or hidden cross-repo scope
   - fail closed to `invalid-owner-boundary`
   - no partial success payload emitted

6. multi-target branch or worktree implication
   - fail closed to `invalid-target-boundary`
   - no partial success payload emitted

7. protected-surface exclusion failure
   - fail closed to `invalid-protected-surface-exclusion`
   - reject omission or implication of protected-surface writes

8. unsupported input mode
   - fail closed to `invalid-input`
   - reject multi-entry payloads, unsupported storage hints, and unsupported mode flags

9. optional-field discipline
   - success payloads do not carry failure-only fields
   - failure payloads do not claim `valid`
   - unsupported queue, registry, storage, or dispatch fields are not silently accepted

These proof cases inherit the pass-5 matrix exactly.

## Exact No-Execution Guard

The worker must carry this wording forward verbatim:

`No-execution guard: this packet may admit future implementation of one explicit candidate-entry load, required-field enforcement, bounded status and optional-field discipline, single-owner and single-target boundary checks, protected-surface exclusion checks, cited-receipt presence checks, and bounded validation-result rendering for the queue-or-registry batch-entry validator, but it may not create or mutate queue or registry state, infer defaults, read runtime state to discover entries, dispatch work, widen into supervisor behavior, or imply execution-home, supervised-pilot, or operator-adoption proof.`

## Exact Allowed Future Implementation Surfaces

The worker may touch only:

- one future root-local batch-entry validator entry surface
- one future explicit local-input loader for exactly one candidate entry
- one future contract-validation layer for required fields, statuses, optional fields, owner boundaries, target boundaries, and protected-surface exclusions
- one future cited-receipt-presence checker
- one future bounded result-rendering layer
- one future fixture or static-input proof harness for the admitted matrix
- local non-secret fixtures needed to prove the admitted matrix

The worker may touch only implementation-local surfaces for the admitted first slice.
The worker may not widen into runtime storage, shared execution homes, or unrelated root systems.

## Exact Forbidden Future Implementation Surfaces

The worker must not touch:

- queue or registry creation, mutation, or storage-path planning surfaces
- `runtime/` state discovery surfaces
- `_stack` execution-home or Playbook doctrine surfaces
- owner-repo mutation surfaces
- Fitness, `archive/`, deploy/publication, `.env`, secret, or secret-adjacent surfaces
- supervisor, dispatch, resume, or status-transition surfaces
- multi-entry scaffold, generation, or summary-rendering surfaces

## Exact Stop Conditions

The worker must stop and return immediately if the slice requires:

- queue or registry mutation
- directory crawling or runtime-state discovery
- storage-path invention
- inferred defaults for owner repo, branch, worktree, checkpoint, verification, or closeout fields
- any change to the admitted result vocabulary or payload surface
- supervisor, dispatch, resume, or status-transition behavior
- protected-surface bypass or secret-bearing fixtures
- widening beyond one explicit candidate entry

If one of those triggers appears, the work is no longer valid first-slice implementation work.

## Exact Handoff Prompt-Pack Spine

Any future worker prompt-pack must include:

1. the exact implementation objective
2. the inherited passes 1 through 5 as frozen inputs
3. the exact preserved payload surface
4. the exact proof matrix
5. the exact no-execution guard verbatim
6. the exact allowed-touch and forbidden-touch surfaces
7. the exact stop-and-return conditions

Mirror surfaces may restate this spine.
They may not redefine it.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry batch-entry validator implementation-readiness closeout and worker-routing pass 7`

Why:

- the contract spine, first-slice boundary, proof matrix, and worker handoff are now frozen
- the next remaining root-only ambiguity is whether this docs chain is materially complete enough to leave root docs-only and route bounded implementation work without reopening storage or supervisor design

## Marker Decision

- `none`

Why:

- this pass narrows the worker handoff contract only
- no code, execution proof, or operator adoption landed

## Rule

Freeze the worker handoff contract before authorizing first-slice validator implementation work.

## Pattern

contract freeze -> owner admission -> support check -> first-slice selection -> first-slice admission and proof matrix -> prompt-pack and handoff contract -> implementation-readiness closeout -> implementation

## Failure Mode

Scope bleed through validator handoff.

If the worker handoff contract is left implicit, the admitted validator slice expands through prompt wording into queue behavior, storage planning, supervisor semantics, or broader authority claims than the frozen design chain actually allows.
