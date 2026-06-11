# AI Long-Run Batch Orchestration Queue-Or-Registry Runtime-State Queue-Home Or Registry-Home Selection First-Implementation Admission Pass 54 - 2026-06-11

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
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-QUEUE-HOME-OR-REGISTRY-HOME-SELECTION-CONTRACT-FREEZE-PASS-51-2026-06-11.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-QUEUE-HOME-OR-REGISTRY-HOME-SELECTION-OWNER-SURFACE-ADMISSION-PASS-52-2026-06-11.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-QUEUE-HOME-OR-REGISTRY-HOME-SELECTION-SUPPORTING-LANE-ADMISSION-PASS-53-2026-06-11.md`
  - `stack.yaml`
  - `AGENTS.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned `runtime-state queue-home or registry-home selection` seam, plus one proof matrix for validating that slice without crossing the no-write, no-runtime-state-discovery, no-exact-child-path, no-filename/schema/snapshot-shape, or no-execution-home boundary.

This pass does not:

- implement helper code
- create live queue or registry state
- choose one final queue-home or registry-home path
- choose one exact child path, filename, schema, or snapshot shape
- admit `_stack` execution semantics
- admit runtime-state discovery, validator execution, status transitions, supervisor behavior, or dispatch
- mutate runtime state, owner repos, Fitness, `archive/`, deploy/publication surfaces, `.env`, or secrets

## Inherited State

Pass 51 froze:

- the exact retained-state destination contract
- `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/` as the admitted neutral family root
- `queue-home` and `registry-home` as the only admissible destination classes for later narrowing beneath that neutral family root
- continued deferral of exact child path, filename, schema, snapshot shape, runtime-state discovery, and final live path choice

Pass 52 froze:

- `ATLAS root control-plane surfaces` as the owner-facing home for that retained-state destination seam
- continued deferral of `_stack`, Playbook, owner-repo, and retained-state implementation ownership for execution or discovery semantics

Pass 53 froze:

- no separate supporting lane honestly reopens yet
- the family remains root-local retained-state destination control-plane truth at this stage

The current stack state and memory doctrine already exposes:

- retained mutable state under `runtime/**`
- queue-like retained state under `runtime/state/**` when needed
- append-only observation history under `runtime/receipts/**`
- explicit separation from repo roots, fixtures, packages, tmp, and secrets

This pass consumes those boundaries and freezes the narrowest first code slice plus the exact proof behavior expected from that slice.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. `one explicit retained-state destination proposal input loader`
   - accept exactly one explicit local candidate path or one inline JSON object carrying one candidate path string
   - read only one explicitly provided local input path or one inline JSON payload
   - do not discover candidate paths from directories, runtime state, receipts, or queue artifacts

2. `one root-relative path normalization layer`
   - normalize the candidate path relative to the ATLAS root
   - preserve the candidate only as one proposed retained-state destination path beneath the already admitted neutral family root
   - reject paths that cannot be resolved as one root-relative candidate under the ATLAS workspace
   - do not rewrite the candidate into one exact child path, filename, schema, or snapshot shape by convenience

3. `one bounded retained-state destination classifier`
   - classify the normalized candidate by its first five path segments only
   - admit only candidates that are either:
     - the neutral family root:
       - `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/`
     - beneath the admitted `queue-home` destination class:
       - `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/`
     - beneath the admitted `registry-home` destination class:
       - `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/registry-home/`
   - treat the neutral family root as admitted-but-unresolved retained-state destination truth only
   - treat `queue-home` and `registry-home` descendants as admitted destination-class truth only
   - fail closed on candidates that stay inside the neutral family root but fall under other non-admitted destination-class descendants
   - fail closed on candidates outside the admitted neutral family root
   - stop below any claim that an admitted destination-class descendant is now the chosen exact child path, filename, schema, snapshot shape, or live runtime-state artifact

4. `one bounded retained-state destination decision renderer`
   - emit only:
     - the normalized candidate path in root-relative form
     - one decision value:
       - `admitted-neutral-family-root`
       - `admitted-queue-home-destination-class`
       - `admitted-registry-home-destination-class`
       - `non-admitted-neutral-family-descendant`
       - `outside-admitted-neutral-family-root`
     - one top-level home-class value
     - one child-home value
     - one retained-state layout-family value
     - one retained-state destination-class value
     - one note that exact child path, filename, schema, snapshot shape, runtime-state discovery, and final live artifact choice remain deferred
   - preserve the distinction between admitted destination-class truth and deferred final artifact shape

5. `one no-write, no-discovery, and no-final-artifact guard`
   - create no directories, files, queue records, or registry records
   - choose no exact child path, filename, schema, or snapshot shape
   - perform no runtime-state discovery, validator execution, status transition, or execution-home routing
   - preserve the distinction between admitted destination-class truth and unchosen final live artifact shape

6. `one fail-closed unsupported-input handler`
   - reject multi-candidate payloads
   - reject queue, registry, dispatch, resume, or execution hints
   - reject mixed input modes and discovered-path flows
   - stop before any runtime mutation, persistence behavior, or directory crawling

This first slice may:

- classify exactly one explicit candidate path against the frozen retained-state destination contract
- report whether that candidate is the admitted neutral family root, an admitted `queue-home` destination-class candidate, an admitted `registry-home` destination-class candidate, a non-admitted neutral-family descendant, or outside the admitted neutral family root
- preserve the distinction between admitted destination-class truth and deferred exact child path or artifact shape
- use only explicit local input

This first slice may not:

- create, mutate, or persist a queue or registry
- choose one final queue-home or registry-home path
- choose one exact child path, filename, schema, or snapshot shape
- infer runtime-state discovery defaults from adjacent retained-state surfaces
- read live runtime state to discover queue state
- dispatch work
- change entry status as a side effect
- widen into runtime-state discovery, supervisor, execution-home, or summary behavior

## Exact Deferred Later Slices

Deferred to later slices are:

- retained-state destination worker prompt-pack and handoff packaging
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

### Neutral family-root candidate

Expected behavior:

- emit `admitted-neutral-family-root`
- preserve the candidate in root-relative form
- report `runtime/` as the top-level home class
- report `runtime/state/` as the admitted child-home class
- report the admitted neutral retained-state family root
- note that destination-class narrowing remains unresolved

### Queue-home destination-root candidate

Expected behavior:

- emit `admitted-queue-home-destination-class`
- preserve the candidate in root-relative form
- report `queue-home` as the admitted destination class
- keep the result below any claim that exact child path or artifact shape is now chosen

### Queue-home descendant candidate

Expected behavior:

- emit `admitted-queue-home-destination-class`
- preserve the deeper root-relative candidate path
- keep the result below any claim that the deeper child path, filename, schema, or snapshot shape is now chosen

### Registry-home destination-root candidate

Expected behavior:

- emit `admitted-registry-home-destination-class`
- preserve the candidate in root-relative form
- report `registry-home` as the admitted destination class
- keep the result below any claim that exact child path or artifact shape is now chosen

### Registry-home descendant candidate

Expected behavior:

- emit `admitted-registry-home-destination-class`
- preserve the deeper root-relative candidate path
- keep the result below any claim that the deeper child path, filename, schema, or snapshot shape is now chosen

### Other neutral-family descendant candidate

Expected behavior:

- fail closed as `non-admitted-neutral-family-descendant`
- preserve the candidate in root-relative form
- report that the path stays inside the neutral family root but outside the admitted `queue-home` and `registry-home` destination classes

### Outside neutral-family root candidate

Expected behavior:

- fail closed as `outside-admitted-neutral-family-root`
- report that the candidate is outside the admitted neutral retained-state family root
- stop before replaying the earlier child-home or layout-family classifier as if it were this seam

### Multi-candidate or discovered input mode

Expected behavior:

- fail closed on input
- reject more than one candidate path or any discovered-path flow

### Queue or execution hint payload

Expected behavior:

- fail closed on input
- reject queue, registry, dispatch, resume, or execution-home hints

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry runtime-state queue-home or registry-home selection prompt-pack and handoff contract pass 55`

Why:

- the first slice and proof matrix are now explicit
- the next remaining docs-only ambiguity is how that exact slice is handed to a future implementation worker without widening into exact child path choice, filename/schema/snapshot-shape choice, runtime-state discovery, live writes, or execution semantics

## Marker Decision

- `none`

Why:

- this pass freezes retained-state destination classification and proof shape only
- it does not land code, execution proof, or widened operator adoption

## Rule

Freeze Destination-Class Truth Before Child-Path Or Artifact-Shape Truth

No exact child path, filename/schema/snapshot shape, or runtime-state discovery seam is honest until the admitted neutral retained-state family first gains one explicit first-slice classifier that keeps destination-class truth separate from deeper artifact choice and execution semantics.

## Pattern

retained-state destination contract freeze -> root owner admission -> support check -> first destination-class implementation admission -> prompt-pack and handoff contract

## Failure Mode

`Destination-Class-Means-Artifact Drift`

This family becomes fake progress when one admitted `queue-home` or `registry-home` destination-class result starts acting like permission for deeper child-path invention, filename/schema choice, runtime-state discovery, or live queue or registry mutation instead of forcing those to stay separate later bounded questions.

## What This Pass Proves

This pass proves:

- `runtime-state queue-home or registry-home selection` now has one exact first-slice classifier and proof matrix
- the admitted neutral family root can remain unresolved while `queue-home` and `registry-home` destination-class candidates are admitted without implying exact child-path or artifact-shape truth
- the next honest question is worker handoff packaging rather than more first-slice explanation

This pass does not prove:

- that any helper code has landed
- that any final queue-home or registry-home path is now chosen
- that any exact child path, filename, schema, or snapshot shape is now chosen
- that any runtime-state discovery or execution semantics are now admitted
