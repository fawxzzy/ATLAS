# AI Long-Run Batch Orchestration Queue-Or-Registry Runtime-State Child-Path Or Artifact-Shape Selection First-Implementation Admission Pass 61 - 2026-06-11

- Date: `2026-06-11`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/architecture/STATE-AND-MEMORY-BOUNDARIES.md`
  - `docs/architecture/AWARENESS-FIRST-WORLD-MODEL.md`
  - `docs/architecture/ORCHESTRATION-BOUNDARIES.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONTRACT-FREEZE-PASS-1-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-PATH-OR-ARTIFACT-SHAPE-SELECTION-CONTRACT-FREEZE-PASS-58-2026-06-11.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-PATH-OR-ARTIFACT-SHAPE-SELECTION-OWNER-SURFACE-ADMISSION-PASS-59-2026-06-11.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-PATH-OR-ARTIFACT-SHAPE-SELECTION-SUPPORTING-LANE-ADMISSION-PASS-60-2026-06-11.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-QUEUE-HOME-OR-REGISTRY-HOME-SELECTION-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-11.md`
  - `ops/atlas/runtime_state_queue_home_or_registry_home_selection.py`
  - `stack.yaml`
  - `AGENTS.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned `runtime-state child-path or artifact-shape selection` seam, plus one proof matrix for validating that slice without crossing the no-write, no-runtime-state-discovery, no-final-child-path-choice, no-filename/schema/snapshot-shape-choice, or no-execution-home boundary.

This pass does not:

- implement helper code
- create live queue or registry state
- choose one final queue-home or registry-home path
- choose one exact child path, filename, schema, or snapshot shape
- admit runtime-state discovery, validator execution, status transitions, supervisor behavior, dispatch, or `_stack` execution-home semantics
- mutate runtime state, owner repos, Fitness, `archive/`, deploy/publication surfaces, `.env`, or secrets

## Inherited State

Pass 58 froze:

- the exact retained-state descendant contract beneath the already admitted `queue-home` and `registry-home` destination classes
- the rule that exact child path, filename, schema, snapshot shape, and final live artifact choice stay one jointly deferred descendant question
- the rule that retained-state descendant meaning remains below runtime-state discovery and execution semantics

Pass 59 froze:

- `ATLAS root control-plane surfaces` as the owner-facing home for that retained-state descendant seam
- continued deferral of `_stack`, Playbook, owner-repo, and execution-home ownership for discovery or mutation semantics

Pass 60 froze:

- no separate supporting lane honestly reopens yet
- the family remains root-local retained-state descendant control-plane truth at this stage

The current stack state and implementation proof already expose:

- one real retained-state destination classifier that admits the neutral family root plus admitted `queue-home` and `registry-home` destination classes
- explicit separation between retained mutable state under `runtime/state/**` and append-only observation history under `runtime/receipts/**`
- explicit deferral of exact child path, filename, schema, snapshot shape, runtime-state discovery, and final live artifact choice

This pass consumes those boundaries and freezes the narrowest first code slice plus the exact proof behavior expected from that slice.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. `one explicit retained-state descendant proposal input loader`
   - accept exactly one explicit local candidate path or one inline JSON object carrying one candidate path string
   - read only one explicitly provided local input path or one inline JSON payload
   - do not discover candidate paths from directories, runtime state, receipts, or queue artifacts

2. `one root-relative path normalization layer`
   - normalize the candidate path relative to the ATLAS root
   - preserve the candidate only as one proposed retained-state descendant beneath the already admitted neutral family root and beneath one already admitted destination class when present
   - reject paths that cannot be resolved as one root-relative candidate under the ATLAS workspace
   - do not rewrite the candidate into one exact final child path, filename, schema, or snapshot shape by convenience

3. `one destination-class-aware retained-state descendant classifier`
   - classify the normalized candidate against the already admitted destination roots only:
     - `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/`
     - `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/registry-home/`
   - emit `admitted-queue-home-destination-root-unresolved` when the candidate is exactly the admitted `queue-home` destination root
   - emit `admitted-queue-home-descendant-candidate` when the candidate is deeper beneath the admitted `queue-home` destination root
   - emit `admitted-registry-home-destination-root-unresolved` when the candidate is exactly the admitted `registry-home` destination root
   - emit `admitted-registry-home-descendant-candidate` when the candidate is deeper beneath the admitted `registry-home` destination root
   - fail closed as `neutral-family-root-without-destination-class` when the candidate stops at the neutral family root without narrowing into an admitted destination class
   - fail closed as `non-admitted-neutral-family-descendant` when the candidate stays inside the neutral family root but under another non-admitted destination-class descendant
   - fail closed as `outside-admitted-neutral-family-root` when the candidate is outside the admitted neutral family root
   - stop below any claim that a deeper admitted descendant is now the chosen final child path, filename, schema, snapshot shape, or live runtime-state artifact

4. `one bounded retained-state descendant decision renderer`
   - emit only:
     - the normalized candidate path in root-relative form
     - one decision value
     - one top-level home-class value
     - one child-home value
     - one neutral retained-state family-root value
     - one destination-class value
     - one destination-root-path value
     - one descendant-tail value:
       - `none` when the candidate is exactly the destination root
       - the preserved deeper suffix beneath the admitted destination root when the candidate is deeper
     - one note that exact child path, filename, schema, snapshot shape, runtime-state discovery, and final live artifact choice remain deferred
   - preserve the distinction between admitted descendant-candidate truth and deferred final artifact truth

5. `one no-write, no-discovery, and no-final-artifact guard`
   - create no directories, files, queue records, or registry records
   - choose no exact child path, filename, schema, or snapshot shape
   - perform no runtime-state discovery, validator execution, status transition, or execution-home routing
   - preserve the distinction between admitted descendant-candidate truth and unchosen final live artifact shape

6. `one fail-closed unsupported-input handler`
   - reject multi-candidate payloads
   - reject queue, registry, dispatch, resume, or execution hints
   - reject mixed input modes and discovered-path flows
   - stop before any runtime mutation, persistence behavior, or directory crawling

This first slice may:

- classify exactly one explicit candidate path against the frozen retained-state descendant contract
- report whether that candidate is still the unresolved `queue-home` or `registry-home` destination root, a deeper admitted descendant candidate beneath one of those roots, a neutral-family root with no destination class, a non-admitted neutral-family descendant, or outside the admitted neutral family root
- preserve one deeper descendant tail without treating it as final child-path or artifact-shape truth
- use only explicit local input

This first slice may not:

- create, mutate, or persist a queue or registry
- choose one final queue-home or registry-home path
- choose one exact child path, filename, schema, or snapshot shape
- infer runtime-state discovery defaults from adjacent retained-state surfaces
- read live runtime state to discover queue or registry state
- dispatch work
- change entry status as a side effect
- widen into runtime-state discovery, supervisor, execution-home, or summary behavior

## Exact Deferred Later Slices

Deferred to later slices are:

- retained-state descendant worker prompt-pack and handoff packaging
- richer fixture tooling beyond the minimum first-slice harness
- exact child path, filename, schema, or snapshot shape choice beneath either admitted destination class
- live queue or registry writes
- runtime-state discovery semantics
- execution-ready transition semantics
- any `_stack` execution-home follow-on

Deferred does not mean admitted now.
Those slices require later bounded packets.

## Exact Forbidden First-Slice Elements

Forbidden from the first slice are:

- queue or registry mutation
- directory creation or file creation
- final queue-home or registry-home path invention
- exact child path, filename, schema, or snapshot-shape invention
- runtime-state discovery
- validator execution
- status mutation or lifecycle advancement
- supervisor, dispatch, or resume behavior
- protected-surface bypass
- owner-boundary rewriting by convenience

## Exact Proof Matrix

### Queue-home destination-root candidate

Expected behavior:

- emit `admitted-queue-home-destination-root-unresolved`
- preserve the candidate in root-relative form
- report `queue-home` as the admitted destination class
- emit the admitted `queue-home` destination root as `destination_root_path`
- emit `none` as the descendant tail
- keep the result below any claim that final child path or artifact shape is now chosen

### Queue-home descendant candidate

Expected behavior:

- emit `admitted-queue-home-descendant-candidate`
- preserve the deeper root-relative candidate path
- report `queue-home` as the admitted destination class
- emit the admitted `queue-home` destination root as `destination_root_path`
- emit the preserved deeper suffix beneath that destination root as the descendant tail
- keep the result below any claim that the deeper child path, filename, schema, or snapshot shape is now chosen

### Registry-home destination-root candidate

Expected behavior:

- emit `admitted-registry-home-destination-root-unresolved`
- preserve the candidate in root-relative form
- report `registry-home` as the admitted destination class
- emit the admitted `registry-home` destination root as `destination_root_path`
- emit `none` as the descendant tail
- keep the result below any claim that final child path or artifact shape is now chosen

### Registry-home descendant candidate

Expected behavior:

- emit `admitted-registry-home-descendant-candidate`
- preserve the deeper root-relative candidate path
- report `registry-home` as the admitted destination class
- emit the admitted `registry-home` destination root as `destination_root_path`
- emit the preserved deeper suffix beneath that destination root as the descendant tail
- keep the result below any claim that the deeper child path, filename, schema, or snapshot shape is now chosen

### Neutral family-root candidate

Expected behavior:

- fail closed as `neutral-family-root-without-destination-class`
- preserve the candidate in root-relative form
- report that the path stops at the admitted neutral family root without narrowing into one admitted destination class

### Other neutral-family descendant candidate

Expected behavior:

- fail closed as `non-admitted-neutral-family-descendant`
- preserve the candidate in root-relative form
- report that the path stays inside the neutral family root but outside the admitted `queue-home` and `registry-home` destination classes

### Outside neutral-family root candidate

Expected behavior:

- fail closed as `outside-admitted-neutral-family-root`
- report that the candidate is outside the admitted neutral retained-state family root
- stop before replaying the earlier destination-class classifier as if it were this seam

### Multi-candidate or discovered input mode

Expected behavior:

- fail closed on input
- reject more than one candidate path or any discovered-path flow

### Queue or execution hint payload

Expected behavior:

- fail closed on input
- reject queue, registry, dispatch, resume, or execution-home hints

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry runtime-state child-path or artifact-shape selection prompt-pack and handoff contract pass 62`

Why:

- the first slice and proof matrix are now explicit
- the next remaining docs-only ambiguity is how that exact slice is handed to a future implementation worker without widening into exact child-path choice, filename/schema/snapshot-shape choice, runtime-state discovery, live writes, or execution semantics

## Marker Decision

- `none`

Why:

- this pass freezes retained-state descendant classification and proof shape only
- it does not land code, execution proof, or widened operator adoption

## Rule

Freeze Descendant-Candidate Truth Before Final Child-Path Or Artifact Truth

No exact child path, filename/schema/snapshot shape, or runtime-state discovery seam is honest until the admitted destination classes first gain one explicit first-slice classifier that keeps unresolved destination roots, deeper descendant candidates, and final artifact choice separate.

## Pattern

retained-state descendant contract freeze -> root owner admission -> support check -> first descendant-candidate implementation admission -> prompt-pack and handoff contract

## Failure Mode

`Descendant-Candidate-Means-Final-Artifact Drift`

This family becomes fake progress when one admitted deeper descendant candidate starts acting like permission for final child-path invention, filename/schema choice, runtime-state discovery, or live queue or registry mutation instead of forcing those to stay separate later bounded questions.

## What This Pass Proves

This pass proves:

- `runtime-state child-path or artifact-shape selection` now has one exact first-slice classifier and proof matrix
- the admitted `queue-home` and `registry-home` destination roots can stay unresolved while deeper descendant candidates are preserved without implying final child-path or artifact-shape truth
- the next honest question is worker handoff packaging rather than more first-slice explanation

This pass does not prove:

- that any helper code has landed
- that any final queue-home or registry-home path is now chosen
- that any exact child path, filename, schema, or snapshot shape is now chosen
- that any runtime-state discovery or execution semantics are now admitted
