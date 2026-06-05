# Stabilize Root Worktree Cortex Shadow-Support Disposition Decision Pass 36 - 2026-06-02

- Date: `2026-06-02`
- Lane: `stabilize-root-worktree`
- Mode: `blocker-facing cortex shadow-support disposition decision`
- Source surfaces:
  - `docs/ops/STABILIZE-ROOT-WORKTREE-CORTEX-SHADOW-SUPPORT-STAGING-PROOF-PASS-35-2026-06-02.md`
  - `git diff --cached --name-only`

## Objective

Decide the safe immediate disposition of the exact staged Cortex shadow-support tranche.

## Decision

- keep the exact staged Cortex shadow-support tranche held in the index
- do not widen the staged set to the later memory-path carry, the residual QA workflow carry, unrelated `docs/ops/*` backlog, or retained `archive/*`

## Exact Non-Claim Boundary

- this pass does not clear the broader dirty-root blocker
- this pass does not claim the remaining tracked or untracked support carries are preserved
- this pass does not grant any marker movement

## Exact Next Move

- decide commit-intent for the exact staged Cortex shadow-support tranche only

## Marker Decision

- `none`
