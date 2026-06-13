# AI Long-Run Batch Orchestration Queue-Or-Registry Runtime-State Exact Child-Path Selection First-Implementation Admission Pass 68 - 2026-06-12

- Date: `2026-06-12`
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
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-EXACT-CHILD-PATH-SELECTION-CONTRACT-FREEZE-PASS-65-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-EXACT-CHILD-PATH-SELECTION-OWNER-SURFACE-ADMISSION-PASS-66-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-EXACT-CHILD-PATH-SELECTION-SUPPORTING-LANE-ADMISSION-PASS-67-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-PATH-OR-ARTIFACT-SHAPE-SELECTION-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-12.md`
  - `ops/atlas/runtime_state_child_path_or_artifact_shape_selection.py`
  - `stack.yaml`
  - `AGENTS.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@4fd69bc3`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned `runtime-state exact child-path selection` seam, plus one proof matrix for validating that slice without crossing the no-write, no-artifact-shape-choice, no-runtime-state-discovery, or no-execution-home boundary.

This pass does not:

- implement helper code
- create live queue or registry state
- choose one final queue-home or registry-home destination class
- choose one exact filename, schema, or snapshot shape
- admit runtime-state discovery, validator execution, status transitions, supervisor behavior, dispatch, or `_stack` execution-home semantics
- mutate runtime state, owner repos, Fitness, `archive/`, deploy/publication surfaces, `.env`, or secrets

## Inherited State

Pass 65 froze:

- the exact retained-state child-path contract beneath the already admitted `queue-home` and `registry-home` destination classes
- the rule that exact filename, schema, snapshot shape, and final artifact-shape choice stay separate later questions after exact child-path truth is chosen
- the rule that retained-state exact-child-path meaning remains below runtime-state discovery and execution semantics

Pass 66 froze:

- `ATLAS root control-plane surfaces` as the owner-facing home for that retained-state exact-child-path seam
- continued deferral of `_stack`, Playbook, owner-repo, and execution-home ownership for discovery or mutation semantics

Pass 67 froze:

- no separate supporting lane honestly reopens yet
- the family remains root-local retained-state exact-child-path control-plane truth at this stage

The current stack state and implementation proof already expose:

- one real retained-state descendant classifier that can distinguish unresolved destination roots from deeper admitted descendant candidates beneath `queue-home` and `registry-home`
- explicit separation between retained mutable state under `runtime/state/**` and append-only observation history under `runtime/receipts/**`
- explicit deferral of exact filename, schema, snapshot shape, runtime-state discovery, and final artifact-shape choice

This pass consumes those boundaries and freezes the narrowest first code slice plus the exact proof behavior expected from that slice.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. `one explicit exact-live-path proposal input loader`
   - accept exactly one explicit local candidate path or one inline JSON object carrying one candidate path string
   - read only one explicitly provided local input path or one inline JSON payload
   - do not discover candidate paths from directories, runtime state, receipts, or queue artifacts

2. `one root-relative path normalization layer`
   - normalize the candidate path relative to the ATLAS root
   - preserve the candidate only as one proposed exact retained-state live path beneath one already admitted destination class when present
   - reject paths that cannot be resolved as one root-relative candidate under the ATLAS workspace
   - do not rewrite the candidate into one exact filename, schema, or snapshot shape by convenience

3. `one destination-class-aware exact-child-path classifier`
   - classify the normalized candidate against the already admitted destination roots only:
     - `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/`
     - `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/registry-home/`
   - emit `queue-home-destination-root-still-unresolved` when the candidate is exactly the admitted `queue-home` destination root
   - emit `registry-home-destination-root-still-unresolved` when the candidate is exactly the admitted `registry-home` destination root
   - emit `admitted-queue-home-exact-child-path-candidate` when the candidate is deeper beneath the admitted `queue-home` destination root
   - emit `admitted-registry-home-exact-child-path-candidate` when the candidate is deeper beneath the admitted `registry-home` destination root
   - fail closed as `neutral-family-root-without-destination-class` when the candidate stops at the neutral family root without narrowing into an admitted destination class
   - fail closed as `non-admitted-neutral-family-descendant` when the candidate stays inside the neutral family root but under another non-admitted destination-class descendant
   - fail closed as `outside-admitted-neutral-family-root` when the candidate is outside the admitted neutral family root
   - stop below any claim that one admitted exact child-path candidate now chooses one filename, schema, snapshot shape, runtime-state discovery rule, or live runtime-state artifact shape

4. `one bounded exact-child-path decision renderer`
   - emit only:
     - the normalized candidate path in root-relative form
     - one decision value
     - one top-level home-class value
     - one child-home value
     - one neutral retained-state family-root value
     - one destination-class value
     - one destination-root-path value
     - one exact-child-path-candidate value:
       - `none` when the candidate is still only a destination root or fails closed
       - the preserved deeper root-relative path when the candidate is deeper beneath one admitted destination root
     - one note that exact filename, schema, snapshot shape, runtime-state discovery, and final artifact-shape choice remain deferred
   - preserve the distinction between admitted exact child-path candidate truth and deferred artifact-shape truth

5. `one no-write, no-discovery, and no-artifact-shape guard`
   - create no directories, files, queue records, or registry records
   - choose no exact filename, schema, or snapshot shape
   - perform no runtime-state discovery, validator execution, status transition, or execution-home routing
   - preserve the distinction between admitted exact-child-path candidate truth and unchosen final artifact shape

6. `one fail-closed unsupported-input handler`
   - reject multi-candidate payloads
   - reject queue, registry, dispatch, resume, or execution hints
   - reject mixed input modes and discovered-path flows
   - stop before any runtime mutation, persistence behavior, or directory crawling

This first slice may:

- classify exactly one explicit candidate path against the frozen retained-state exact-child-path contract
- report whether that candidate is still only an unresolved `queue-home` or `registry-home` destination root, a deeper admitted exact-child-path candidate beneath one of those roots, a neutral-family root with no destination class, a non-admitted neutral-family descendant, or outside the admitted neutral family root
- preserve one deeper exact child-path candidate without treating it as filename/schema/snapshot-shape truth
- use only explicit local input

This first slice may not:

- create, mutate, or persist a queue or registry
- choose one final queue-home or registry-home destination class
- choose one exact filename, schema, or snapshot shape
- infer runtime-state discovery defaults from adjacent retained-state surfaces
- read live runtime state to discover queue or registry state
- dispatch work
- change entry status as a side effect
- widen into artifact-shape selection, runtime-state discovery, supervisor, execution-home, or summary behavior

## Exact Deferred Later Slices

Deferred to later slices are:

- exact-child-path worker prompt-pack and handoff packaging
- richer fixture tooling beyond the minimum first-slice harness
- exact filename, schema, or snapshot shape choice beneath one admitted exact child path
- final artifact-shape selection
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
- final queue-home or registry-home destination-class invention
- exact filename, schema, or snapshot-shape invention
- runtime-state discovery
- validator execution
- status mutation or lifecycle advancement
- supervisor, dispatch, or resume behavior
- protected-surface bypass
- owner-boundary rewriting by convenience

## Exact Proof Matrix

### Queue-home destination-root candidate

Expected behavior:

- emit `queue-home-destination-root-still-unresolved`
- preserve the candidate in root-relative form
- report `queue-home` as the admitted destination class
- emit the admitted `queue-home` destination root as `destination_root_path`
- emit `none` as the exact-child-path candidate
- keep the result below any claim that artifact shape is now chosen

### Queue-home exact-child-path candidate

Expected behavior:

- emit `admitted-queue-home-exact-child-path-candidate`
- preserve the deeper root-relative candidate path
- report `queue-home` as the admitted destination class
- emit the admitted `queue-home` destination root as `destination_root_path`
- emit the deeper root-relative path as the exact-child-path candidate
- keep the result below any claim that filename, schema, or snapshot shape is now chosen

### Registry-home destination-root candidate

Expected behavior:

- emit `registry-home-destination-root-still-unresolved`
- preserve the candidate in root-relative form
- report `registry-home` as the admitted destination class
- emit the admitted `registry-home` destination root as `destination_root_path`
- emit `none` as the exact-child-path candidate
- keep the result below any claim that artifact shape is now chosen

### Registry-home exact-child-path candidate

Expected behavior:

- emit `admitted-registry-home-exact-child-path-candidate`
- preserve the deeper root-relative candidate path
- report `registry-home` as the admitted destination class
- emit the admitted `registry-home` destination root as `destination_root_path`
- emit the deeper root-relative path as the exact-child-path candidate
- keep the result below any claim that filename, schema, or snapshot shape is now chosen

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
- stop before replaying the earlier descendant-candidate classifier as if it were this seam

### Multi-candidate or discovered input mode

Expected behavior:

- fail closed on input
- reject more than one candidate path or any discovered-path flow

### Queue or execution hint payload

Expected behavior:

- fail closed on input
- reject queue, registry, dispatch, resume, or execution-home hints

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry runtime-state exact child-path selection prompt-pack and handoff contract pass 69`

Why:

- the first slice and proof matrix are now explicit
- the next remaining docs-only ambiguity is how that exact slice is handed to a future implementation worker without widening into filename/schema/snapshot-shape choice, artifact-shape choice, runtime-state discovery, live writes, or execution semantics

## Marker Decision

- `none`

Why:

- this pass freezes retained-state exact-child-path classification and proof shape only
- it does not land code, execution proof, or widened operator adoption

## Rule

Freeze Exact Live-Path Candidate Truth Before Artifact Shape Or Discovery

No exact filename/schema/snapshot shape or runtime-state discovery seam is honest until the admitted destination classes first gain one explicit first-slice classifier that keeps unresolved destination roots, exact live-path candidates, and final artifact-shape choice separate.

## Pattern

exact child-path contract freeze -> root owner admission -> support check -> first exact-live-path implementation admission -> prompt-pack and handoff contract

## Failure Mode

`Exact-Live-Path-Means-Artifact Drift`

This family becomes fake progress when one admitted exact live-path candidate starts acting like permission for filename/schema invention, snapshot-shape choice, runtime-state discovery, or live queue or registry mutation instead of forcing those to stay separate later bounded questions.

## What This Pass Proves

This pass proves:

- `runtime-state exact child-path selection` now has one exact first-slice classifier and proof matrix
- the admitted `queue-home` and `registry-home` destination roots can stay unresolved while deeper exact-live-path candidates are preserved without implying artifact-shape truth
- the next honest question is worker handoff packaging rather than more first-slice explanation

This pass does not prove:

- that any helper code has landed
- that any exact filename, schema, or snapshot shape is now chosen
- that any runtime-state discovery or execution semantics are now admitted
