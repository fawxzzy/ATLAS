# AI Long-Run Batch Orchestration Queue-Or-Registry Runtime-State Concrete-Layout Selection First-Implementation Admission Pass 47 - 2026-06-11

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
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CONCRETE-LAYOUT-SELECTION-CONTRACT-FREEZE-PASS-44-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CONCRETE-LAYOUT-SELECTION-OWNER-SURFACE-ADMISSION-PASS-45-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CONCRETE-LAYOUT-SELECTION-SUPPORTING-LANE-ADMISSION-PASS-46-2026-06-10.md`
  - `stack.yaml`
  - `AGENTS.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned `runtime-state concrete-layout selection` seam, plus one proof matrix for validating that slice without crossing the no-write, no-runtime-state-discovery, no-final-queue-home-or-registry-home, or no-execution-home boundary.

This pass does not:

- implement helper code
- create live queue or registry state
- choose one final queue-home or registry-home path
- choose one exact filename, schema, or snapshot shape
- admit `_stack` execution semantics
- admit runtime-state discovery, validator execution, status transitions, or supervisor behavior
- mutate runtime state, owner repos, Fitness, `archive/`, deploy/publication surfaces, `.env`, or secrets

## Inherited State

Pass 44 froze:

- the exact retained-state descendant-layout contract
- `runtime/state/` as the admitted child-home class for mutable pre-execution queue-or-registry truth
- continued deferral of exact descendant contents, filename, schema, snapshot shape, final queue-home or registry-home choice, and runtime-state discovery

Pass 45 froze:

- `ATLAS root control-plane surfaces` as the owner-facing home for that retained-state layout seam
- continued deferral of `_stack`, Playbook, owner-repo, and `runtime/state/` ownership for implementation or execution semantics

Pass 46 froze:

- no separate supporting lane honestly reopens yet
- the family remains root-local retained-state control-plane truth at this stage

The current stack state and memory doctrine already exposes:

- retained mutable state under `runtime/**`
- queue-like retained state under `runtime/state/**` when needed
- append-only observation history under `runtime/receipts/**`
- active retained-state examples under sibling surfaces such as `runtime/state/atlas/**`
- explicit separation from repo roots, fixtures, packages, tmp, and secrets

This pass consumes those boundaries and freezes the narrowest first code slice plus the exact proof behavior expected from that slice.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. `one explicit retained-state layout proposal input loader`
   - accept exactly one explicit local candidate path or one inline JSON object carrying one candidate path string
   - read only one explicitly provided local input path or one inline JSON payload
   - do not discover candidate paths from directories, runtime state, receipts, or queue artifacts

2. `one root-relative path normalization layer`
   - normalize the candidate path relative to the ATLAS root
   - preserve the candidate only as one proposed retained-state layout path beneath the already admitted `runtime/state/` family
   - reject paths that cannot be resolved as one root-relative candidate under the ATLAS workspace
   - do not rewrite the candidate into a final queue-home or registry-home choice by convenience

3. `one bounded retained-state layout-family classifier`
   - classify the normalized candidate by its first four path segments only
   - admit only candidates that fall under the neutral family root:
     - `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/`
   - treat that neutral family root as the admitted retained-state layout seam only
   - fail closed on candidates that stay inside `runtime/state/` but fall under other retained-state siblings such as:
     - `runtime/state/atlas/`
     - `runtime/state/cortex/`
     - `runtime/state/discord/`
     - `runtime/state/playbook/`
   - fail closed on candidates that fall under other `runtime/state/ai-long-run-batch-orchestration/*` descendants outside the admitted neutral layout-family root
   - fail closed on candidates outside the already admitted `runtime/state/` child-home family
   - stop below any claim that an admitted descendant is now the chosen final queue-home or registry-home path, filename, schema, or snapshot shape

4. `one bounded retained-state layout decision renderer`
   - emit only:
     - the normalized candidate path in root-relative form
     - one decision value:
       - `admitted-neutral-layout-family-root`
       - `admitted-neutral-layout-family-descendant`
       - `non-admitted-retained-state-sibling`
       - `outside-admitted-state-child-home`
     - one top-level home-class value
     - one child-home value
     - one retained-state layout-family value
     - one note that exact filename, schema, snapshot shape, runtime-state discovery, and final queue-home or registry-home choice remain deferred
   - preserve the distinction between admitted neutral layout-family root and deferred final live-state shape

5. `one no-write, no-discovery, and no-final-layout guard`
   - create no directories, files, or queue records
   - choose no final queue-home or registry-home path
   - choose no filename, schema, or snapshot shape
   - perform no runtime-state discovery, validator execution, status transition, or execution-home routing
   - preserve the distinction between admitted retained-state layout-family root and unchosen final live-state shape

6. `one fail-closed unsupported-input handler`
   - reject multi-candidate payloads
   - reject queue, registry, dispatch, resume, or execution hints
   - reject mixed input modes and discovered-path flows
   - stop before any runtime mutation, persistence behavior, or directory crawling

This first slice may:

- classify exactly one explicit candidate path against the frozen retained-state layout-family contract
- report whether that candidate is the admitted neutral family root, an admitted descendant beneath that neutral family root, a non-admitted retained-state sibling, or outside the admitted `runtime/state/` child-home
- preserve the distinction between admitted layout-family root and deferred final queue-home or registry-home shape
- use only explicit local input

This first slice may not:

- create, mutate, or persist a queue or registry
- choose one final queue-home or registry-home path
- infer filename, schema, or snapshot-shape defaults from adjacent runtime state
- read live runtime state to discover queue state
- dispatch work
- change entry status as a side effect
- widen into runtime-state discovery, supervisor, execution-home, or summary behavior

## Exact Deferred Later Slices

Deferred to later slices are:

- retained-state layout worker prompt-pack and handoff packaging
- richer fixture tooling beyond the minimum first-slice harness
- final queue-home or registry-home path choice
- exact filename, schema, or snapshot shape choice
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
- filename, schema, or snapshot-shape invention
- runtime-state discovery
- validator execution
- status mutation or lifecycle advancement
- supervisor, dispatch, or resume behavior
- protected-surface bypass
- owner-boundary rewriting by convenience

## Exact Proof Matrix

### Neutral family-root candidate

Expected behavior:

- emit `admitted-neutral-layout-family-root`
- preserve the candidate in root-relative form
- report `runtime/` as the top-level home class
- report `runtime/state/` as the admitted child-home class
- report `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/` as the admitted neutral layout-family root
- note that final queue-home or registry-home choice remains deferred

### Neutral family descendant candidate

Expected behavior:

- emit `admitted-neutral-layout-family-descendant`
- preserve the deeper root-relative candidate path
- keep the result below any claim that the final live-state path, filename, schema, or snapshot shape is now chosen

### Retained-state sibling candidate

Expected behavior:

- fail closed as `non-admitted-retained-state-sibling`
- preserve the candidate in root-relative form
- report that the path stays inside `runtime/state/` but outside the admitted neutral layout-family root

### Other lane-descendant candidate

Expected behavior:

- fail closed as `non-admitted-retained-state-sibling`
- preserve the candidate in root-relative form
- report that the path stays under `runtime/state/ai-long-run-batch-orchestration/` but outside the admitted `queue-or-registry/` layout-family root

### Outside child-home candidate

Expected behavior:

- fail closed as `outside-admitted-state-child-home`
- report that the candidate is outside the admitted `runtime/state/` child-home family
- stop before replaying the earlier child-home classifier as if it were this seam

### Multi-candidate or discovered input mode

Expected behavior:

- fail closed on input
- reject more than one candidate path or any discovered-path flow

### Queue or execution hint payload

Expected behavior:

- fail closed on input
- reject queue, registry, dispatch, resume, or execution-home hints

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry runtime-state concrete-layout selection prompt-pack and handoff contract pass 48`

Why:

- the first slice and proof matrix are now explicit
- the next remaining docs-only ambiguity is how that exact slice is handed to a future implementation worker without widening into final queue-home choice, runtime-state discovery, live writes, or execution semantics

## Marker Decision

- `none`

Why:

- this pass narrows the first implementation slice only
- no code, execution proof, or operator adoption landed

## Rule

`Admit Neutral Layout Family; Defer Final Live-State Shape`

The first retained-state layout implementation slice is honest only when it can classify one explicit candidate path against the frozen neutral `runtime/state/ai-long-run-batch-orchestration/queue-or-registry/` family root while still refusing to bless final queue-home choice, runtime-state discovery, filename/schema shape, or live state mutation.

## Pattern

retained-state layout contract freeze -> root owner admission -> support check -> first implementation admission -> worker handoff -> implementation

## Failure Mode

`Retained-Layout Slice Drift`

If the first retained-state layout implementation slice is left implicit, later prompt wording widens the seam into final queue-home choice, runtime-state discovery, or live queue writes that the frozen chain does not yet allow.
