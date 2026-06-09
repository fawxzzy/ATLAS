# AI Long-Run Batch Orchestration Queue-Or-Registry First-Implementation-Slice Selection Pass 4 - 2026-06-09

- Date: `2026-06-09`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-slice selection`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONTRACT-FREEZE-PASS-1-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-OWNER-SURFACE-ADMISSION-PASS-2-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SUPPORTING-LANE-ADMISSION-PASS-3-2026-06-09.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Select the first real implementation slice for the root-owned `queue-or-registry batch entry contract` and record why the other plausible options remain deferred.

This pass does not:

- implement helper code
- choose queue or registry storage placement
- admit `_stack` execution semantics
- mutate runtime state
- generate live queue entries
- widen into supervisor behavior, owner-repo mutation, Fitness work, archive/delete work, deploy/publication work, `.env`, or secret work

## Root Health Baseline

- the contract is already frozen
- the owner-facing home is already admitted as `ATLAS root control-plane surfaces`
- no separate support lane honestly reopened
- the next honest question is the smallest root-local implementation slice that proves the contract is useful without creating de facto queue state
- root validation remains clean at `critical=0 error=0 warning=50 info=0`
- local `HEAD` remains in parity with `origin/main`

## Candidate Comparison

The smallest plausible first-slice choices are:

1. `batch-entry validator`
2. `draft entry scaffold renderer`
3. `entry status summary renderer`
4. `storage-path manifest planner`

## Selection

Select exactly one first implementation slice:

- `batch-entry validator`

## Why `batch-entry validator` Wins

This is the smallest reusable helper slice because it proves the contract can be enforced before any storage, queue mutation, or supervisor behavior is admitted.

What it proves cleanly:

- required batch-entry fields can be checked consistently
- status vocabulary can fail closed
- single-owner and single-target boundaries can be enforced
- protected-surface exclusions can be enforced
- cited receipt fields can be required without inventing queue state
- later scaffold, storage, and execution layers can all depend on one shared contract gate

Why this is smaller than a draft scaffold:

- validator logic is reusable across every later storage or rendering mode
- it avoids producing de facto queue entries before storage-home truth exists
- it avoids mixing field enforcement with entry generation
- it avoids quietly committing to one artifact shape or path

## Deferred Alternatives

### `draft entry scaffold renderer`

Deferred because:

- too close to generating de facto queue or registry entries
- risks smuggling storage shape and artifact expectations in under draft-only language
- too easy to infer owner or worktree defaults that are not yet proven

Reopen condition:

- only after validator behavior proves contract-fail and protected-surface behavior on real candidate entries

### `entry status summary renderer`

Deferred because:

- depends on an admitted entry set already existing
- too close to becoming a registry reader before storage-home truth is frozen
- summarizes state rather than proving the contract gate itself

Reopen condition:

- only after validator plus one admitted draft-entry surface exist

### `storage-path manifest planner`

Deferred because:

- too close to deciding queue or registry placement by implication
- risks choosing `runtime/` or another state surface before that boundary is explicitly admitted
- blends contract enforcement with later storage semantics

Reopen condition:

- only after validator coverage exists and storage-home truth is explicitly reopened

## Smallest Safe Boundary

The first implementation slice should therefore do only this:

- accept one candidate batch-entry description
- enforce required contract fields
- enforce allowed status values
- enforce single owner-repo and target-branch-or-worktree boundaries
- enforce protected-surface exclusion reporting
- return pass/fail plus missing or invalid field results

It must not:

- create or mutate a live queue or registry
- choose `runtime/` or any other storage home
- infer owner repo, branch, checkpoint, or verification fields silently
- dispatch work
- mark entries `running-supervised` or `complete`
- perform hidden multi-entry batching

## Marker Decision

- `none`

Why:

- this is a sharper implementation choice, not implementation proof
- no validator code exists yet
- no operator adoption widened yet

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry batch-entry validator first-slice admission pass 5`

Why:

- the validator is now the smallest reusable first slice
- every later scaffold, storage, and execution layer depends on it
- it avoids turning the first helper into a half-queue under draft or planning language

## Rule

First implementation selection must prefer the smallest reusable contract gate over any slice that already smells like state storage or execution.

## Pattern

contract freeze -> root owner admission -> support check -> first-slice selection -> validator admission -> later scaffold or storage layers

## Failure Mode

Choosing a first implementation that is already half-validator, half-queue.
