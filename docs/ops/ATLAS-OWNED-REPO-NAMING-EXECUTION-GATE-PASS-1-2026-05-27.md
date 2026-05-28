# Atlas-Owned Repo Naming Execution Gate Pass 1 - 2026-05-27

- Date: `2026-05-27`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only execution-gate freeze`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 50%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-CANONICALIZATION-2026-05-27.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `stack.yaml`
  - `stack.lock.yaml`
- Missing prerequisite surface:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-INVENTORY-DEPENDENCY-MAP-2026-05-27.md` (`not yet durable`)
- Control-plane checkpoint: `main@ae56e63`

## Objective

Freeze the hard prerequisites for any future repo-naming execution lane so this stays policy-first and migration-safe.

This pass does not:

- rename any repo directory
- rename any remote
- assume GitHub rename execution
- change `fawxzzy-fitness`
- mutate owner-repo content
- convert gate language into rename approval

## Root State

- branch: `main`
- HEAD: `ae56e63`
- status: clean except intentional untracked `archive/`
- validation: green before gate drafting at `critical=0 error=0 warning=310`

## Current Gate Reality

Execution remains blocked.

Why:

- the naming policy is durable
- the in-scope internal repo set is durable
- the `fawxzzy-fitness` exception is durable
- but the named inventory and dependency map is not yet a durable surface

That means this pass can freeze execution prerequisites and explicitly block rename execution until the missing dependency map exists.

## Hard Execution Gates

Any future actual rename lane must remain blocked until all of the following are durable.

### 1. Stack Registry Readiness

Required before rename execution:

- `stack.yaml` repo paths must have a reviewed rename plan
- `stack.lock.yaml` component and excluded-surface paths must have a reviewed rename plan
- `docs/registry/STACK-REPO-INVENTORY.json` and `docs/audits/STACK-REPO-INVENTORY.md` must be included in the dependency map and update plan
- any generated registry surfaces must have a known regeneration command or owner

Blocked today:

- the durable dependency map naming those exact surfaces is not yet landed

### 2. Receipt And Reference Rewrite Scope

Required before rename execution:

- the dependency map must classify which receipt families need live-path rewrite
- historical provenance receipts must be separated from current-truth surfaces
- execution planning must preserve historical references where they are meant to describe old state rather than current state

Blocked today:

- no durable dependency map yet separates current-truth rewrite scope from historical provenance preservation scope

### 3. Restart-Surface Update Scope

Required before rename execution:

- restart and handoff surfaces must be mapped before any rename:
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/02-lanes-and-markers.md` when naming posture changes
- continuity manifests must be checked for affected repo-path references

Blocked today:

- restart-surface impact is acknowledged, but not yet durably mapped

### 4. Local Directory Rename Safety

Required before rename execution:

- each candidate repo must be verified as locally rename-safe in its current checkout state
- worktree bindings, tooling assumptions, and repo-local path-sensitive scripts must be inventoried first
- execution planning must distinguish:
  - repos that can be renamed by local directory move only
  - repos that would break current tooling or active worktree assumptions

Blocked today:

- no durable candidate-by-candidate local rename-safety map exists

### 5. Remote-Name Assumption Prohibition

Required before rename execution:

- execution planning must assume local directory rename only unless a separate remote rename lane is explicitly opened
- no local rename receipt may imply GitHub repo rename, remote URL rewrite, or ownership transfer

Always blocked unless separately opened:

- remote rename assumptions
- GitHub-side rename assumptions
- silent remote URL churn

### 6. Rollback Expectation

Required before rename execution:

- every future rename package must define exact rollback posture
- rollback must restore:
  - prior directory name
  - registry projection
  - restart-surface references
  - any manifest or receipt-index surfaces touched by the rename package
- rollback must be defined before execution, not reconstructed after breakage

Blocked today:

- no durable rollback sequence exists yet

## Candidate Classification Rules

This pass freezes how future candidates must be classified.

### Safe-First Rename Candidate

A future candidate counts as `safe-first` only if all of the following are true:

- it is in the internal ATLAS-owned target set
- it is not the explicit `fawxzzy-fitness` exception
- its dependency-map footprint is small and durable
- local rename safety is proven
- rollback is explicit
- no remote rename assumption is required

Current honest posture:

- no repo is admitted as a safe-first execution candidate yet because the dependency map is still missing

### Blocked Candidate

A future candidate is `blocked` if any of the following remain true:

- dependency-map coverage is missing
- registry rewrite scope is unclear
- restart-surface impact is unclear
- local rename safety is unclear
- rollback is undefined
- the candidate would force implied remote rename behavior

Current blocked class:

- `repos/fawxzzy-foundation`
- `repos/fawxzzy-lifeline`
- `repos/fawxzzy-playbook`
- `repos/fawxzzy-mazer`
- `repos/fawxzzy-stream`
- `repos/fawxzzy-trove`

These are blocked for execution-gate purposes, not because rename is forbidden forever, but because the mapping and rollback surfaces are not durable yet.

### Preserved Exception

A `preserved exception` is a name intentionally held outside the internal canonicalization target sequence.

Current preserved exception:

- `repos/fawxzzy-fitness`

Why:

- the exception is already durable in the naming policy
- this gate pass does not reopen or weaken that exception

## Hard Rule

Policy and durable mapping must exist before rename execution.

More specifically:

- marker admission is not execution approval
- naming policy is not execution approval
- execution-gate language is not execution approval
- the missing dependency map keeps execution blocked even after this pass

## Honest Effect On Marker Posture

This pass does not justify a marker move.

Why:

- it strengthens execution discipline
- it does not land the dependency map
- it does not land rollback sequencing
- it does not admit any safe-first execution candidate yet

## Exact Next Package

`Atlas-owned repo naming canonicalization inventory and dependency map`

Why:

- this pass made the missing dependency map the first explicit hard gate
- the next honest move is to land that map rather than imply any rename readiness

## Rule

Rename execution must stay blocked until dependency mapping and rollback posture are durable.

## Pattern

policy admission -> dependency map -> execution gate -> rollback sequence -> bounded rename execution

## Failure Mode

Execution-gate language quietly becomes execution approval.
