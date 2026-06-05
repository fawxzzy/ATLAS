# Stabilize Root Worktree Residual Active-Tranche Staging Admission Decision Pass 15 - 2026-06-02

- Date: `2026-06-02`
- Lane: `stabilize-root-worktree`
- Mode: `blocker-facing residual active-tranche staging admission`
- Source surfaces:
  - `docs/ops/STABILIZE-ROOT-WORKTREE-POST-FIRST-COMMIT-RESIDUAL-ACTIVE-TRANCHE-DECISION-PASS-14-2026-06-02.md`
  - `git status --short`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`

## Objective

Decide whether the post-first-commit residual active tranche can now honestly be admitted for selective staging as one exact next candidate subset, without pulling in truth mirrors, mixed tracked support backlog, or broader untracked backlog.

## Residual Active Tranche

- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/03-operating-model.md`
- `docs/atlas-book/08-workflow-recipes.md`
- `docs/atlas-book/10-failure-modes-and-recovery.md`
- `docs/atlas-book/11-system-map-graph.md`
- `docs/atlas-book/13-vision-and-endgames.md`
- `ops/cortex/context_assembler.py`
- `ops/cortex/current_state.py`
- `ops/cortex/operator_surface.py`
- `ops/cortex/rail_state_reader.py`
- `tests/test_cortex_context_assembler.py`
- `tests/test_cortex_current_state.py`
- `tests/test_cortex_operator_surface.py`
- `tests/test_cortex_rail_state_reader.py`

## Decision

- admit the residual active tranche for selective staging
- do not widen that admission to the truth-mirror set
- do not widen that admission to the mixed tracked support backlog
- do not widen that admission to any untracked backlog

## Why This Is Honest

1. the first blocker-preservation tranche is already committed as `1b25ba3`
2. the residual active tranche remains the smallest exact tracked class still directly tied to live Cortex/read-model and restart-surface work
3. the truth-mirror and mixed support classes are still separately held and materially different
4. selective staging is now a narrower and more honest next step than leaving the residual active tranche as an undifferentiated remainder

## Exact Non-Claim Boundary

- this pass does not prove the tranche is commit-ready
- this pass does not prove the tranche should be committed now
- this pass does not clear the broader dirty-root blocker
- this pass does not reopen the materially closed root-docs ladder

## Exact Next Move

- stage the residual active tranche in isolation and prove no adjacent class enters the index

## Marker Decision

- `none`
