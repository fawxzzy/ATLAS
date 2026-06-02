# Stabilize Root Worktree Preserve-Disposition Decision Pass 3 - 2026-06-01

- Date: `2026-06-01`
- Lane: `stabilize-root-worktree`
- Mode: `docs-only root preserve/disposition decision`
- Source surfaces:
  - `docs/ops/STABILIZE-ROOT-WORKTREE-BLOCKER-CLASSIFICATION-AND-HOLD-PASS-1-2026-06-01.md`
  - `docs/ops/STABILIZE-ROOT-WORKTREE-INVENTORY-AND-OWNERSHIP-SPLIT-PASS-2-2026-06-01.md`
  - `docs/ops/QUEUED-WORK-REVIEW-PACKET-2026-05-25.md`
  - `docs/ops/STACK-LOCK-REGISTRY-RECONCILIATION-2026-05-25.md`
  - `git status --porcelain=v1 --untracked-files=all`
  - `runtime/receipts/validation/stack-validation.latest.json`

## Objective

Freeze the preserve/disposition posture for the highest-pressure untracked root buckets so later stabilization work does not misclassify durable receipt backlog, continuity-manifest backlog, or retained archive evidence as generic cleanup residue.

## Root Health Baseline

- validation remains `critical=0 error=0 warning=493 info=0`
- untracked `docs/ops/*` receipt backlog: `170`
- untracked `docs/memory/initiatives/*` continuity manifests: `5`
- untracked `archive/*` retained evidence paths: `7`
- the immediate lane remains `stabilize-root-worktree`

## Preserve / Disposition Decisions

### 1. `docs/ops/*` durable receipt backlog

Decision:

- `preserve as durable control-plane backlog`

Why:

1. these paths are stack receipts and control-plane packets, not disposable runtime output
2. the backlog is the dominant untracked class in the current root worktree
3. deleting or collapsing them by implication would destroy restart-relevant evidence

Not classified as:

- scratch output
- generic cleanup residue
- auto-stage-now set

Current consequence:

- keep held as durable backlog until a later bounded staging/commit or archival decision explicitly names the subset

### 2. `docs/memory/initiatives/*` continuity-manifest backlog

Decision:

- `preserve as durable continuity backlog`

Why:

1. continuity manifests are canonical retrieval surfaces under current ATLAS doctrine
2. these files belong to restart truth, not to transient runtime state
3. they should travel with later continuity refresh or staging decisions, not with cleanup residue handling

Not classified as:

- disposable manifests
- archive-only evidence
- delete-ready residue

Current consequence:

- keep held with the durable docs backlog until one later bounded continuity/staging packet explicitly decides how they are preserved or committed

### 3. `archive/*` retained evidence surface

Decision:

- `retain; no delete or move decision earned`

Why:

1. prior durable receipts repeatedly described `archive/` as intentional retained evidence rather than cleanup residue
2. the current surface includes preserved historical and secret-bearing paths
3. AGENTS rules explicitly require retention class confirmation before deletion

Not classified as:

- disposable historical clutter
- auto-cleanup material
- safe-to-move archive subset

Current consequence:

- keep `archive/*` retained and untouched until one later bounded retention-class review explicitly names safe disposal or preservation subsets

## What This Pass Proves

- the largest untracked root buckets now have explicit preserve/retain posture
- no future `stabilize-root-worktree` slice should describe these buckets as generic cleanup residue
- the current dirty-root blocker is now narrower: the unresolved pressure is no longer whether those untracked buckets should be preserved, but how the remaining tracked mixed support surfaces and active tranche should be stabilized honestly

## What This Does Not Prove

This pass does not prove:

- that any preserved bucket is ready to stage together
- that any archive subset is safe to delete
- that the root worktree is now stable enough to resume the deferred Cortex lane
- that any marker move is earned

## Exact Next Slice Inside This Lane

Still inside `stabilize-root-worktree`, the next honest slice is:

- tracked-surface tranche split and hold decision for:
  - root truth mirrors and policy surfaces
  - mixed tracked governance/memory/QA support surfaces
  - active current-tranche ATLAS/Cortex tracked work

Why this is next:

1. the dominant untracked buckets are now durably preserved or retained
2. the remaining ambiguity is concentrated in tracked root surfaces
3. no honest worktree-stabilization claim exists until the tracked surfaces are split into active tranche, later hold, or separate preserve decisions

## Marker Decision

- `none`

Why:

- this pass freezes preserve/disposition posture only
- no blocker was cleared
- no new execution or adoption surface widened

