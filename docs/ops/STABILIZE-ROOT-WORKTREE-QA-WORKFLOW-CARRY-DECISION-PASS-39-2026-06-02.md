# Stabilize Root Worktree QA-Workflow Carry Decision Pass 39 - 2026-06-02

- Date: `2026-06-02`
- Lane: `stabilize-root-worktree`
- Mode: `blocker-facing qa-workflow carry decision`
- Source surfaces:
  - `docs/ops/STABILIZE-ROOT-WORKTREE-RESIDUAL-PAIR-FORCED-CLASSIFICATION-DECISION-PASS-38-2026-06-02.md`
  - `git diff -- .github/workflows/atlas-qa-llel.yml`
  - direct read of `.github/workflows/atlas-qa-llel.yml`
  - direct read of `docs/standards/ATLAS-QA-LLEL.md`
  - direct read of `docs/ops/ATLAS-QA-PROMOTION-RUNBOOK.md`

## Objective

Define the exact blocker-facing preservation boundary for the immediate residual carry `.github/workflows/atlas-qa-llel.yml` without widening into the later Mazer initiative carry or the broader untracked backlog.

## Decision

- the next exact candidate is one `qa-workflow carry tranche`
- this tranche is the workflow file plus the minimum root restart and receipt surfaces needed to preserve the blocker-facing decision durably
- do not widen this tranche to `docs/memory/initiatives/initiative-mazer-d2-learning-scorer.json`, unrelated `docs/ops/*` backlog, or retained `archive/*`

## Exact QA-Workflow Carry Tranche

- `.github/workflows/atlas-qa-llel.yml`
- `docs/ops/STABILIZE-ROOT-WORKTREE-QA-WORKFLOW-CARRY-DECISION-PASS-39-2026-06-02.md`
- `docs/ops/STABILIZE-ROOT-WORKTREE-QA-WORKFLOW-STAGING-ADMISSION-DECISION-PASS-40-2026-06-02.md`
- `docs/ops/STABILIZE-ROOT-WORKTREE-QA-WORKFLOW-STAGING-PROOF-PASS-41-2026-06-02.md`
- `docs/ops/STABILIZE-ROOT-WORKTREE-QA-WORKFLOW-DISPOSITION-DECISION-PASS-42-2026-06-02.md`
- `docs/ops/STABILIZE-ROOT-WORKTREE-QA-WORKFLOW-COMMIT-INTENT-DECISION-PASS-43-2026-06-02.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`

## Why This Is Honest

1. the workflow is a live governed verification router, not passive documentation
2. the diff removes a pull-request trigger path for `docs/codex/ATLAS-QA-LLEL-PROMPT-PACK.md`, and that file is no longer present on disk
3. preserving the workflow change now keeps the root QA orchestration boundary aligned with current truth while leaving broader QA standards, runbooks, and backlog untouched

## Exact Later Carry Outside This Tranche

- `docs/memory/initiatives/initiative-mazer-d2-learning-scorer.json` remains later memory-path canonicalization carry
- unrelated untracked `docs/ops/*` backlog remains outside this tranche
- retained `archive/*` evidence remains outside this tranche

## Exact Next Move

- admit and stage the QA-workflow carry tranche in isolation
- verify the root QA pipeline test and full stack validation
- only then decide commit-intent for that exact tranche

## Marker Decision

- `none`
