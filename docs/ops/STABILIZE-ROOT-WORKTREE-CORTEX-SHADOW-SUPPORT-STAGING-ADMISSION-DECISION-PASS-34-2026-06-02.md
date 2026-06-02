# Stabilize Root Worktree Cortex Shadow-Support Staging Admission Decision Pass 34 - 2026-06-02

- Date: `2026-06-02`
- Lane: `stabilize-root-worktree`
- Mode: `blocker-facing cortex shadow-support staging admission`
- Source surfaces:
  - `docs/ops/STABILIZE-ROOT-WORKTREE-CORTEX-SHADOW-SUPPORT-TRANCHE-DECISION-PASS-33-2026-06-02.md`
  - `git status --short`

## Objective

Decide whether selective staging is now honest for the exact Cortex shadow-support tranche only.

## Decision

- selective staging is now honest for the exact Cortex shadow-support tranche only
- do not widen staging to the later memory-path carry, the residual QA workflow carry, unrelated `docs/ops/*` backlog, or retained `archive/*`

## Exact Staging Boundary

- stage only the exact tranche named in pass 33
- keep `docs/memory/initiatives/initiative-mazer-d2-learning-scorer.json`, `.github/workflows/atlas-qa-llel.yml`, unrelated untracked receipts, and `archive/*` out of the index

## Exact Next Move

- stage the tranche in isolation
- prove the staged set is exact
- run the targeted shadow tests and full stack validation before deciding commit-intent

## Marker Decision

- `none`
