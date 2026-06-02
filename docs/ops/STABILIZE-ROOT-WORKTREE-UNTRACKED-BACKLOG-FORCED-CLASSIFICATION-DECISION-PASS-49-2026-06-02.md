# Stabilize Root Worktree Untracked-Backlog Forced Classification Decision Pass 49 - 2026-06-02

- Date: `2026-06-02`
- Lane: `stabilize-root-worktree`
- Mode: `blocker-facing untracked-backlog forced classification`
- Source surfaces:
  - `git status --short`
  - direct inventory of untracked `docs/ops/*`
  - direct inventory of retained `archive/*`

## Objective

Choose exactly one of the two remaining untracked backlog classes as the immediate blocker-facing carry and freeze the other as later adjacent hold, without reopening tracked-surface stabilization, QA workflow routing, or Cortex authority work.

## Untracked Pair

- `docs/ops/*` durable control-plane backlog
- `archive/*` retained evidence backlog

## Decision

- immediate blocker-facing carry: untracked `docs/ops/*` durable control-plane backlog
- later adjacent hold: retained `archive/*` evidence backlog

## Why This One First

1. untracked `docs/ops/*` is durable control-plane truth that should ultimately be preserved or explicitly classified, not left indefinitely outside versioned history
2. the current untracked `docs/ops/*` set is finite and bounded enough to classify as one root control-plane backlog class right now
3. `archive/*` is explicitly retained evidence, not live control-plane routing, and its much larger volume argues for hold posture unless a retention-policy or preservation question is explicitly opened
4. pushing `archive/*` ahead of the `docs/ops/*` backlog would invert the root-state priority by preferring cold retained evidence over live durable control-plane material

## Exact Non-Claim Boundary

- this pass does not preserve or stage the untracked `docs/ops/*` backlog
- this pass does not preserve or stage retained `archive/*`
- this pass does not reopen tracked-surface stabilization, QA workflow routing, or Cortex authority work
- this pass does not grant any marker movement

## Exact Next Move

- open one bounded blocker-facing classification or preservation slice for the untracked `docs/ops/*` durable control-plane backlog only
- keep `archive/*` explicitly held as later retained-evidence carry until a retention or preservation question is opened for that class

## Marker Decision

- `none`
