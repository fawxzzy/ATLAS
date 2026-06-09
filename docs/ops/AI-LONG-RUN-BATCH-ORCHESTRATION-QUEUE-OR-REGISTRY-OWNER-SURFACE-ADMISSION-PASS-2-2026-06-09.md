# AI Long-Run Batch Orchestration Queue-Or-Registry Owner-Surface Admission Pass 2 - 2026-06-09

- Date: `2026-06-09`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded owner-surface admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONTRACT-FREEZE-PASS-1-2026-06-09.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Admit the exact owner-facing surface for the contract-frozen `queue-or-registry batch entry contract`, keep execution semantics and queue placement deferred, and stop below supporting-lane admission, implementation, or supervised pilot design.

This pass does not:

- admit a live queue, registry, or runtime state store
- admit `_stack` execution semantics, worker flow, or supervisor behavior
- admit Playbook doctrine ownership
- admit owner-repo mutation, Fitness work, archive/delete work, deploy/publication work, `.env`, or secret work
- claim that owner-surface admission alone earns marker movement

## Root Health Baseline

- the long-run lane remains doctrine and contract first, not an implementation sprint
- pass 1 already froze one exact storage-agnostic batch-entry contract
- the unresolved question from pass 1 is which surface honestly owns that contract before any support or implementation talk
- root validation remains clean at `critical=0 error=0 warning=50 info=0`
- local `HEAD` remains in parity with `origin/main`

## Owner-Surface Candidates Considered

### ATLAS root control-plane surfaces

What they already own:

- stack doctrine
- lane definitions
- path and boundary rules
- cross-repo planning
- pilot selection criteria
- restart projection and receipt consequence

Why they win:

- the batch-entry contract is still pre-execution lane-definition truth
- the contract names owner repo, worktree, write scope, checkpoint, verification, closeout, and park boundaries before any supervisor behavior is admitted
- that matches ATLAS root ownership of doctrine, boundary rules, and cross-repo planning
- admitting root here keeps the family bounded to contract truth instead of prematurely collapsing it into execution or runtime storage semantics

### `_stack`

Why it does not win yet:

- `_stack` owns execution-oriented orchestration contracts, worker flow, resume and merge behavior, and supervised dispatch semantics
- this family has not yet admitted queue placement, execution transitions, or supervisor behavior
- moving the contract into `_stack` now would blur pre-execution lane-definition truth with later execution semantics

### Playbook

Why it does not win:

- Playbook owns reusable workflow doctrine, verification expectations, and closeout discipline
- this family is still deciding where the cross-repo batch-entry contract lives before any reusable doctrine export is in scope
- Playbook may later consume the pattern, but it does not own this control-plane contract home

### owner repos

Why they do not win:

- the contract is cross-repo by design
- each entry may point at one owner repo, but the field rules, admissibility, and protected-surface boundaries are stack-level truth
- putting the contract into one owner repo would collapse lane planning into repo-local ownership incorrectly

### `runtime/`

Why it does not win:

- `runtime/` is a state-placement surface, not the owner of cross-repo contract meaning
- choosing a storage path now would decide queue or registry placement by implication
- storage remains deferred until a later support or implementation pass makes that choice explicit

## Admission Decision

### Contract truth owner remains at root

- `ATLAS root control-plane surfaces`

What that means:

- ATLAS root owns the canonical field rules
- ATLAS root owns the meaning of `proposed` and `admitted` entry posture
- ATLAS root owns restart-safe projection of the contract and next-packet consequence
- ATLAS root does not thereby become a background runner or runtime queue host

### Execution ownership remains deferred

- `_stack` remains the later candidate owner for:
  - execution-ready transitions
  - supervised run semantics
  - worker flow
  - resume or merge behavior

### Doctrine ownership remains deferred

- Playbook remains a later candidate consumer for reusable doctrine extraction

### Repo ownership remains unchanged

- owner repos still own:
  - repo-local mutation truth
  - repo-local verification truth
  - repo-local implementation truth

## Supporting Dependency Decision

- `none yet`

Why:

- owner-surface admission is now exact
- the next honest question is whether any separate supporting lane actually reopens from that decision
- support should be admitted explicitly rather than assumed from eventual future execution

## Still Not Admitted In This Pass

- live queue or registry storage
- queue entry mutation tooling
- `_stack` helper-home or command-design work
- supervised pilot implementation
- unattended execution
- marker movement

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry supporting-lane admission pass 3`

Why:

- the contract and owner-facing home are now explicit
- the next honest question is whether one exact separate support seam reopens now or whether the family remains root-local at this stage
- implementation would be premature before that support question is frozen

## Marker Decision

- `none`

Why:

- this pass admits the owner-facing surface only
- it does not widen supervised adoption, clear an execution blocker, or land a repeatable pilot

## Rule

`Pre-Execution Batch Truth Stays At Root`

Until long-run batching crosses from lane-definition truth into execution semantics, the batch-entry contract belongs to ATLAS root control-plane surfaces rather than `_stack`, Playbook, or any single owner repo.

## Pattern

contract freeze -> root control-plane owner admission -> explicit support decision -> only then discuss storage path, execution semantics, or pilot implementation

## Failure Mode

`Contract-Home Collapse`

This family becomes dishonest when pre-execution lane-definition truth is pushed into `_stack`, Playbook, runtime storage, or an owner repo before support and execution semantics are explicitly admitted.

## What This Pass Proves

This pass proves:

- the `queue-or-registry batch entry contract` now has one exact owner-facing home
- that home is `ATLAS root control-plane surfaces`
- `_stack`, Playbook, owner repos, and `runtime/` are all still outside ownership for this stage

This pass does not prove:

- that any supporting lane is admitted
- that queue placement is admitted
- that execution semantics or supervised pilot work are admitted
