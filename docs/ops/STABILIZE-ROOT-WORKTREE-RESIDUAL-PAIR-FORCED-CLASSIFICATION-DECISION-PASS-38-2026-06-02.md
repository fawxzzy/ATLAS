# Stabilize Root Worktree Residual-Pair Forced Classification Decision Pass 38 - 2026-06-02

- Date: `2026-06-02`
- Lane: `stabilize-root-worktree`
- Mode: `blocker-facing residual-pair forced classification`
- Source surfaces:
  - `git diff -- .github/workflows/atlas-qa-llel.yml`
  - `git diff -- docs/memory/initiatives/initiative-mazer-d2-learning-scorer.json`
  - direct read of `.github/workflows/atlas-qa-llel.yml`
  - direct read of `docs/memory/initiatives/initiative-mazer-d2-learning-scorer.json`
  - `stack.yaml`
  - `README-STACK.md`

## Objective

Choose exactly one of the two remaining tracked carries as the immediate blocker-facing carry and freeze the other as later adjacent hold, without reopening Cortex authority work and without widening into the broad untracked backlog.

## Residual Pair

- `.github/workflows/atlas-qa-llel.yml`
- `docs/memory/initiatives/initiative-mazer-d2-learning-scorer.json`

## Decision

- immediate blocker-facing carry: `.github/workflows/atlas-qa-llel.yml`
- later adjacent hold: `docs/memory/initiatives/initiative-mazer-d2-learning-scorer.json`

## Why This One First

1. `.github/workflows/atlas-qa-llel.yml` is a live governed verification surface, not a passive memory record
2. the diff removes `docs/codex/ATLAS-QA-LLEL-PROMPT-PACK.md` from the trigger set, and that file is no longer present on disk, so the workflow currently carries stale path truth inside the verification router itself
3. fixing or preserving that workflow decision is more directly tied to current proof routing and operator workflow truth than the Mazer initiative file, which is non-executing memory-path canonicalization
4. `initiative-mazer-d2-learning-scorer.json` still matters, but its diff is route hygiene for durable memory ownership after the already-landed `repos/fawxzzy-mazer -> repos/mazer` rename, not the sharper verification blocker

## Exact Non-Claim Boundary

- this pass does not preserve or stage either file
- this pass does not widen into the untracked `docs/ops/*` backlog or retained `archive/*` evidence
- this pass does not reopen Cortex authority, contract export, or orchestration work
- this pass does not grant any marker movement

## Exact Next Move

- open one bounded blocker-facing slice for `.github/workflows/atlas-qa-llel.yml` only
- keep `docs/memory/initiatives/initiative-mazer-d2-learning-scorer.json` explicitly held as later adjacent carry until the QA workflow slice is resolved

## Marker Decision

- `none`
