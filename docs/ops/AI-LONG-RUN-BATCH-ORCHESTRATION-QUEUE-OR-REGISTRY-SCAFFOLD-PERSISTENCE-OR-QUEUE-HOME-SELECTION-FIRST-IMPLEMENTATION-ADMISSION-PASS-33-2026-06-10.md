# AI Long-Run Batch Orchestration Queue-Or-Registry Scaffold Persistence Or Queue-Home Selection First-Implementation Admission Pass 33 - 2026-06-10

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
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONTRACT-FREEZE-PASS-1-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-CONTRACT-FREEZE-PASS-30-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-OWNER-SURFACE-ADMISSION-PASS-31-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-SUPPORTING-LANE-ADMISSION-PASS-32-2026-06-10.md`
  - `stack.yaml`
  - `AGENTS.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned `scaffold persistence or queue-home selection` seam, plus one proof matrix for validating that slice without crossing the no-write, no-concrete-layout, no-validator-execution, or no-execution-home boundary.

This pass does not:

- implement helper code
- create live queue or registry state
- choose one exact runtime subpath, filename, registry schema, or persistence layout
- admit `_stack` execution semantics
- admit validator execution, status transitions, or supervisor behavior
- mutate runtime state, owner repos, Fitness, `archive/`, deploy/publication surfaces, `.env`, or secrets

## Inherited State

Pass 30 froze:

- the exact storage-home contract
- `runtime/` as the admitted top-level state class
- `repos/`, `docs/`, `ops/`, `data/`, `packages/`, `tmp/`, and `secrets/` as forbidden top-level home classes
- continued deferral of exact runtime subpath, filename, schema, and persistence layout

Pass 31 froze:

- `ATLAS root control-plane surfaces` as the owner-facing home for that storage-home seam
- continued deferral of `_stack`, Playbook, owner-repo, and `runtime/` ownership

Pass 32 froze:

- no separate support lane honestly reopens yet
- the family remains root-local path-class truth at this stage

The current stack path policy already exposes:

- root-owned runtime-state meaning in `AGENTS.md`
- named runtime roots in `stack.yaml`
- explicit separation from fixtures, packages, tmp, and secrets

This pass consumes those boundaries and freezes the narrowest first code slice plus the exact proof behavior expected from that slice.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. `one explicit storage-home proposal input loader`
   - accept exactly one explicit local candidate path or one inline JSON object carrying one candidate path string
   - read only one explicitly provided local input path or one inline JSON payload
   - do not discover candidate paths from directories, registries, runtime state, or receipt chains

2. `one root-relative path normalization layer`
   - normalize the candidate path relative to the ATLAS root
   - preserve the candidate only as one proposed storage-home path
   - reject paths that cannot be resolved as one root-relative candidate under the ATLAS workspace
   - do not rewrite the candidate into a final queue-home or registry-home choice by convenience

3. `one top-level home-class classifier`
   - classify the normalized candidate by its first top-level home class only
   - admit only candidates that fall under `runtime/`
   - reject candidates whose first top-level home class is:
     - `repos/`
     - `docs/`
     - `ops/`
     - `data/`
     - `packages/`
     - `tmp/`
     - `secrets/`
   - fail closed on candidates outside the root-owned path-class contract

4. `one bounded storage-home decision renderer`
   - emit only:
     - the normalized candidate path in root-relative form
     - one decision value:
       - `admitted-runtime-home-candidate`
       - `forbidden-home-class`
     - one home-class value
     - one note that exact subpath, filename, schema, and persistence layout remain deferred
   - stop below any claim that the candidate is now the chosen live queue-home or registry-home

5. `one no-write and no-layout guard`
   - create no directories, files, or queue records
   - choose no filename, registry schema, or persistence layout
   - perform no validator execution, status transition, or execution-home routing
   - preserve the distinction between admitted state class and unchosen concrete layout

6. `one fail-closed unsupported-input handler`
   - reject multi-candidate payloads
   - reject queue, registry, dispatch, resume, or execution hints
   - reject mixed input modes and discovered-path flows
   - stop before any runtime mutation or persistence behavior

This first slice may:

- classify exactly one explicit candidate path against the frozen path-class contract
- report whether that candidate is an admitted runtime-home candidate or a forbidden home-class candidate
- preserve the distinction between state-class admission and deferred concrete layout
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

- storage-home worker prompt-pack and handoff packaging
- richer fixture tooling beyond the minimum first-slice harness
- concrete runtime subpath or filename choice
- registry schema or persistence-layout choice
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
- registry schema invention
- validator execution
- status mutation or lifecycle advancement
- supervisor, dispatch, or resume behavior
- protected-surface bypass
- owner-boundary rewriting by convenience

## Exact Proof Matrix

### Runtime-root candidate

Expected behavior:

- emit `admitted-runtime-home-candidate`
- preserve the candidate in root-relative form
- report `runtime/` as the admitted home class
- note that exact layout remains deferred

### Runtime descendant candidate

Expected behavior:

- emit `admitted-runtime-home-candidate`
- preserve the deeper root-relative candidate path
- keep the result below any claim that the concrete layout is now chosen

### Repo-root candidate

Expected behavior:

- fail closed as `forbidden-home-class`
- report `repos/` as forbidden for durable pre-execution queue-or-registry state

### Fixture or import candidate

Expected behavior:

- fail closed as `forbidden-home-class`
- report `data/` as forbidden for live queue-or-registry truth

### Scratch or package candidate

Expected behavior:

- fail closed as `forbidden-home-class`
- report `tmp/` or `packages/` as forbidden for durable queue-or-registry state

### Secret candidate

Expected behavior:

- fail closed as `forbidden-home-class`
- report `secrets/` as forbidden for ordinary queue-or-registry storage

### Multi-candidate or discovered input mode

Expected behavior:

- fail closed on input
- reject more than one candidate path or any discovered-path flow

### Queue or execution hint payload

Expected behavior:

- fail closed on input
- reject queue, registry, dispatch, resume, or execution-home hints

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry scaffold persistence or queue-home selection prompt-pack and handoff contract pass 34`

Why:

- the first slice and proof matrix are now explicit
- the next remaining docs-only ambiguity is how that exact slice is handed to a future implementation worker without widening into concrete layout choice, live writes, or execution semantics

## Marker Decision

- `none`

Why:

- this pass narrows the first implementation slice only
- no code, execution proof, or operator adoption landed

## Rule

`Admit Runtime Class; Defer Runtime Layout`

The first storage-home implementation slice is honest only when it can classify one explicit candidate path against the frozen top-level path rules while still refusing to bless concrete queue layout, persistence shape, or live state mutation.

## Pattern

storage-home contract freeze -> root owner admission -> support check -> first implementation admission -> worker handoff -> implementation

## Failure Mode

`Storage-Home Slice Drift`

If the first storage-home implementation slice is left implicit, later prompt wording widens the seam into concrete runtime-layout choice, live queue writes, or execution semantics that the frozen chain does not yet allow.
