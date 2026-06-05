# Stabilize Root Worktree Restart-Referenced DocsOps Tranche Decision Pass 50 - 2026-06-02

- Date: `2026-06-02`
- Lane: `stabilize-root-worktree`
- Mode: `blocker-facing restart-referenced docsops tranche decision`
- Source surfaces:
  - direct inventory of untracked `docs/ops/*`
  - direct comparison against `docs/atlas-book/01-current-state.md`
  - direct comparison against `docs/atlas-book/05-receipt-index.md`
  - direct comparison against `docs/atlas-book/12-restart-and-handoff-guide.md`

## Objective

Define the next exact preservation boundary inside the immediate untracked `docs/ops/*` durable control-plane backlog by separating restart-referenced receipts from colder untracked control-plane backlog.

## Decision

- the next exact candidate is one `restart-referenced docsops tranche`
- this tranche contains only untracked `docs/ops/*` receipts already cited by the active restart spine
- do not widen this tranche to colder untracked `docs/ops/*` receipts that are not cited by the restart spine
- do not widen this tranche to retained `archive/*`

## Exact Restart-Referenced DocsOps Tranche

- the untracked `docs/ops/*` receipts already cited by one or more of:
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
- the pass-50-through-pass-54 receipt chain
- the minimum restart/index updates needed to preserve the tranche boundary

## Exact Later Carry Outside This Tranche

- untracked `docs/ops/*` receipts not cited by the active restart spine remain later adjacent hold
- retained `archive/*` evidence remains later adjacent hold

## Why This Is Honest

1. restart-referenced untracked receipts are already being used as durable navigation truth, so they have stronger blocker weight than colder backlog files
2. preserving the cited set first reduces contradiction between restart surfaces and versioned control-plane state
3. colder untracked `docs/ops/*` receipts can remain explicitly held without pretending they are needed for current restart truth

## Exact Next Move

- admit and stage the restart-referenced docsops tranche in isolation
- verify the staged set matches the cited restart-referenced receipt set
- run full stack validation before deciding commit-intent

## Marker Decision

- `none`
