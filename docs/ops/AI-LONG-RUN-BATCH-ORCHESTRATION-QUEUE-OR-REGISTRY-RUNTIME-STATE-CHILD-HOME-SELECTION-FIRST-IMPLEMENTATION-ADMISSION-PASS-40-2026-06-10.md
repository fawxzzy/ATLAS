# AI Long-Run Batch Orchestration Queue-Or-Registry Runtime-State Child-Home Selection First-Implementation Admission Pass 40 - 2026-06-10

- Date: `2026-06-10`
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
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-HOME-SELECTION-CONTRACT-FREEZE-PASS-37-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-HOME-SELECTION-OWNER-SURFACE-ADMISSION-PASS-38-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-HOME-SELECTION-SUPPORTING-LANE-ADMISSION-PASS-39-2026-06-10.md`
  - `stack.yaml`
  - `AGENTS.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned `runtime-state child-home selection` seam, plus one proof matrix for validating that slice without crossing the no-write, no-concrete-runtime-layout, no-validator-execution, or no-execution-home boundary.

This pass does not:

- implement helper code
- create live queue or registry state
- choose one exact runtime subtree, filename, schema, snapshot shape, or persistence layout
- admit `_stack` execution semantics
- admit validator execution, status transitions, or supervisor behavior
- mutate runtime state, owner repos, Fitness, `archive/`, deploy/publication surfaces, `.env`, or secrets

## Inherited State

Pass 37 froze:

- `runtime-state child-home selection` as one exact bounded family
- `runtime/state/` as the admitted child-home class for mutable pre-execution queue-or-registry truth
- `runtime/receipts/` as explicitly excluded from acting as the live mutable queue-or-registry state home
- continued deferral of exact runtime subtree, filename, schema, snapshot shape, and persistence layout

Pass 38 froze:

- `ATLAS root control-plane surfaces` as the owner-facing home for that child-home seam
- continued deferral of `_stack`, Playbook, owner-repo, and `runtime/` ownership for implementation or execution semantics

Pass 39 froze:

- no separate supporting lane honestly reopens yet
- the family remains root-local retained-state control-plane truth at this stage

The current stack state and memory doctrine already exposes:

- retained mutable state under `runtime/**`
- queue-like read models under `runtime/state/**` when needed
- append-only observation history under `runtime/receipts/**`
- explicit separation from repo roots, fixtures, packages, tmp, and secrets

This pass consumes those boundaries and freezes the narrowest first code slice plus the exact proof behavior expected from that slice.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. `one explicit child-home proposal input loader`
   - accept exactly one explicit local candidate path or one inline JSON object carrying one candidate path string
   - read only one explicitly provided local input path or one inline JSON payload
   - do not discover candidate paths from directories, runtime state, receipts, or queue artifacts

2. `one root-relative path normalization layer`
   - normalize the candidate path relative to the ATLAS root
   - preserve the candidate only as one proposed child-home path inside the already admitted `runtime/` family
   - reject paths that cannot be resolved as one root-relative candidate under the ATLAS workspace
   - do not rewrite the candidate into a final queue-home or registry-home choice by convenience

3. `one bounded runtime child-home classifier`
   - classify the normalized candidate by its first two path segments only
   - admit only candidates that fall under `runtime/state/`
   - explicitly exclude candidates that fall under `runtime/receipts/`
   - fail closed on candidates that fall under other `runtime/*` child homes such as:
     - `runtime/atlas/`
     - `runtime/codex/`
     - `runtime/cortex/`
     - `runtime/devservers/`
     - `runtime/lifeline/`
     - `runtime/playbook/`
   - fail closed on candidates outside the already admitted `runtime/` family
   - stop below any claim that an admitted `runtime/state/` descendant is now the chosen concrete queue-home or registry-home layout

4. `one bounded child-home decision renderer`
   - emit only:
     - the normalized candidate path in root-relative form
     - one decision value:
       - `admitted-state-child-home-candidate`
       - `excluded-receipt-history-child-home`
       - `non-admitted-runtime-child-home`
       - `outside-runtime-home-family`
     - one top-level home-class value
     - one child-home value
     - one note that exact subtree, filename, schema, snapshot shape, and persistence layout remain deferred
   - preserve the distinction between admitted child-home class and deferred concrete runtime layout

5. `one no-write and no-layout guard`
   - create no directories, files, or queue records
   - choose no exact runtime subtree, filename, schema, snapshot shape, or persistence layout
   - perform no validator execution, status transition, or execution-home routing
   - preserve the distinction between admitted child-home class and unchosen concrete layout

6. `one fail-closed unsupported-input handler`
   - reject multi-candidate payloads
   - reject queue, registry, dispatch, resume, or execution hints
   - reject mixed input modes and discovered-path flows
   - stop before any runtime mutation or persistence behavior

This first slice may:

- classify exactly one explicit candidate path against the frozen child-home contract
- report whether that candidate is an admitted `runtime/state/` child-home candidate, an excluded `runtime/receipts/` child-home candidate, another non-admitted runtime child-home, or outside the runtime family
- preserve the distinction between admitted child-home class and deferred concrete layout
- use only explicit local input

This first slice may not:

- create, mutate, or persist a queue or registry
- choose one final queue-home or registry-home path
- infer layout defaults from existing runtime roots or adjacent lane surfaces
- read live runtime state to discover queue state
- dispatch work
- change entry status as a side effect
- widen into supervisor, execution-home, or summary behavior

## Exact Deferred Later Slices

Deferred to later slices are:

- child-home worker prompt-pack and handoff packaging
- richer fixture tooling beyond the minimum first-slice harness
- exact runtime subtree, filename, schema, or snapshot shape choice
- concrete queue-home or registry-home layout choice
- live queue or registry writes
- execution-ready transition semantics
- any `_stack` execution-home follow-on

Deferred does not mean admitted now.
Those slices require later bounded packets.

## Exact Forbidden First-Slice Elements

Forbidden from the first slice are:

- queue or registry mutation
- directory creation or file creation
- exact runtime layout invention
- snapshot-shape or schema invention
- validator execution
- status mutation or lifecycle advancement
- supervisor, dispatch, or resume behavior
- protected-surface bypass
- owner-boundary rewriting by convenience

## Exact Proof Matrix

### `runtime/state/` root candidate

Expected behavior:

- emit `admitted-state-child-home-candidate`
- preserve the candidate in root-relative form
- report `runtime/` as the top-level home class
- report `runtime/state/` as the admitted child-home class
- note that exact layout remains deferred

### `runtime/state/` descendant candidate

Expected behavior:

- emit `admitted-state-child-home-candidate`
- preserve the deeper root-relative candidate path
- keep the result below any claim that the concrete layout is now chosen

### `runtime/receipts/` root candidate

Expected behavior:

- emit `excluded-receipt-history-child-home`
- preserve the candidate in root-relative form
- report `runtime/receipts/` as explicitly excluded from acting as the live mutable queue-or-registry state home

### `runtime/receipts/` descendant candidate

Expected behavior:

- emit `excluded-receipt-history-child-home`
- preserve the deeper root-relative candidate path
- keep the result below any claim that receipt descendants may serve as live mutable queue state

### other `runtime/*` child-home candidate

Expected behavior:

- fail closed as `non-admitted-runtime-child-home`
- preserve the candidate in root-relative form
- report that the path is inside `runtime/` but outside the admitted `runtime/state/` child-home class and outside the explicitly excluded `runtime/receipts/` branch

### non-runtime top-level candidate

Expected behavior:

- fail closed as `outside-runtime-home-family`
- report the top-level home class as outside the current child-home family
- stop before replaying the earlier top-level storage-home classifier as if it were this seam

### multi-candidate or discovered input mode

Expected behavior:

- fail closed on input
- reject more than one candidate path or any discovered-path flow

### queue or execution hint payload

Expected behavior:

- fail closed on input
- reject queue, registry, dispatch, resume, or execution-home hints

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry runtime-state child-home selection prompt-pack and handoff contract pass 41`

Why:

- the first slice and proof matrix are now explicit
- the next remaining docs-only ambiguity is how that exact slice is handed to a future implementation worker without widening into concrete layout choice, live writes, or execution semantics

## Marker Decision

- `none`

Why:

- this pass narrows the first implementation slice only
- no code, execution proof, or operator adoption landed

## Rule

`Admit Child-Home Class; Defer Concrete Runtime Layout`

The first child-home implementation slice is honest only when it can classify one explicit candidate path against the frozen `runtime/state/` versus `runtime/receipts/` boundary while still refusing to bless concrete queue layout, persistence shape, or live state mutation.

## Pattern

child-home contract freeze -> root owner admission -> support check -> first implementation admission -> worker handoff -> implementation

## Failure Mode

`Child-Home Slice Drift`

If the first child-home implementation slice is left implicit, later prompt wording widens the seam into concrete runtime-layout choice, live queue writes, or execution semantics that the frozen chain does not yet allow.
