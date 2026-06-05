# Stabilize Root Worktree QA-Workflow Staging Admission Decision Pass 40 - 2026-06-02

- Date: `2026-06-02`
- Lane: `stabilize-root-worktree`
- Mode: `blocker-facing qa-workflow staging admission`
- Source surfaces:
  - `docs/ops/STABILIZE-ROOT-WORKTREE-QA-WORKFLOW-CARRY-DECISION-PASS-39-2026-06-02.md`
  - `git status --short`

## Objective

Decide whether selective staging is now honest for the exact QA-workflow carry tranche only.

## Decision

- selective staging is now honest for the exact QA-workflow carry tranche only
- do not widen staging to `docs/memory/initiatives/initiative-mazer-d2-learning-scorer.json`, unrelated `docs/ops/*` backlog, or retained `archive/*`

## Exact Next Move

- stage the workflow tranche in isolation
- prove the staged set is exact
- verify the stale trigger path is removed while the remaining root QA trigger paths stay intact
- run full stack validation before deciding commit-intent

## Marker Decision

- `none`
