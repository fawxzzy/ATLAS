# Stabilize Root Worktree Non-LDG DocsOps Tail Staging Admission Decision Pass 61 - 2026-06-02

- Date: `2026-06-02`
- Lane: `stabilize-root-worktree`
- Mode: `blocker-facing non-ldg docsops tail staging admission`
- Source surfaces:
  - `docs/ops/STABILIZE-ROOT-WORKTREE-NON-LDG-DOCSOPS-TAIL-TRANCHE-DECISION-PASS-60-2026-06-02.md`
  - `git status --short`

## Objective

Decide whether selective staging is now honest for the exact non-LDG `docs/ops/*` tail tranche only.

## Decision

- selective staging is now honest for the exact non-LDG `docs/ops/*` tail tranche only
- do not widen staging to retained `archive/*`

## Exact Next Move

- stage the non-LDG `docs/ops/*` tail tranche in isolation
- prove the staged set matches the exact two-file remainder
- run full stack validation before deciding commit-intent

## Marker Decision

- `none`
