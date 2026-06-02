# Stabilize Root Worktree Active-Tranche Boundary Pass 6 - 2026-06-01

- Date: `2026-06-01`
- Lane: `stabilize-root-worktree`
- Mode: `docs-only active-tranche boundary freeze`
- Source surfaces:
  - `docs/ops/STABILIZE-ROOT-WORKTREE-TRACKED-SURFACE-TRANCHE-SPLIT-AND-HOLD-PASS-4-2026-06-01.md`
  - `docs/ops/STABILIZE-ROOT-WORKTREE-STABILIZATION-ROUTING-DECISION-PASS-5-2026-06-01.md`
  - `docs/PLAYBOOK_NOTES.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `git diff --name-only`

## Objective

Freeze the minimum future stageable subset inside the intentional held root stabilization tranche so future sessions do not widen the first candidate commit boundary by implication.

## Root Health Baseline

- validation remains `critical=0 error=0 warning=493 info=0`
- the intentional held root stabilization tranche still contains:
  - active current-tranche tracked work: `18`
  - coupled root truth mirrors/policy surfaces: `7`
- mixed tracked governance/memory/QA support backlog remains a separate later hold
- no current packet proves commitability for the whole held tranche

## Minimum Future Stageable Subset

### 1. Minimum subset now frozen

Paths:

- `docs/PLAYBOOK_NOTES.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/ops/STABILIZE-ROOT-WORKTREE-BLOCKER-CLASSIFICATION-AND-HOLD-PASS-1-2026-06-01.md`
- `docs/ops/STABILIZE-ROOT-WORKTREE-INVENTORY-AND-OWNERSHIP-SPLIT-PASS-2-2026-06-01.md`
- `docs/ops/STABILIZE-ROOT-WORKTREE-PRESERVE-DISPOSITION-DECISION-PASS-3-2026-06-01.md`
- `docs/ops/STABILIZE-ROOT-WORKTREE-TRACKED-SURFACE-TRANCHE-SPLIT-AND-HOLD-PASS-4-2026-06-01.md`
- `docs/ops/STABILIZE-ROOT-WORKTREE-STABILIZATION-ROUTING-DECISION-PASS-5-2026-06-01.md`
- `docs/ops/STABILIZE-ROOT-WORKTREE-ACTIVE-TRANCHE-BOUNDARY-PASS-6-2026-06-01.md`

Decision:

- `freeze as minimum future stageable subset candidate`

Why:

1. these are the files directly carrying the current root-worktree blocker doctrine, restart truth, and receipt chain
2. they are the smallest coherent set that can preserve the current stabilization story without forcing unrelated active-tranche files to travel
3. the latest root-worktree chain already refreshes these surfaces together, so this boundary is evidenced instead of speculative

### 2. Explicitly outside the minimum subset for now

Paths remain outside by default:

- coupled root truth mirrors/policy surfaces:
  - `AGENTS.md`
  - `README-STACK.md`
  - `docs/audits/STACK-REPO-INVENTORY.md`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/registry/STACK-SYNERGY-REGISTRY.json`
  - `stack.lock.yaml`
  - `stack.yaml`
- active-tranche book/cortex/test files not needed to preserve the root-worktree hold chain:
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
- mixed tracked governance/memory/QA support backlog

Why they stay outside:

1. no current root-worktree packet proves they must travel in the first minimum subset
2. some are broader truth mirrors or earlier Cortex/read-model changes whose next honest treatment is separate
3. keeping them outside prevents the first future stageable boundary from inflating into a broad synthetic tranche

## What This Pass Proves

- the first future stageable boundary is now narrower than the whole intentional held tranche
- the root-worktree doctrine and restart spine now have one explicit minimum subset candidate
- future sessions should not widen that first subset by silently pulling in truth mirrors, older Cortex files, or mixed support backlog

## What This Does Not Prove

This pass does not prove:

- that the minimum subset is ready to stage or commit now
- that the excluded truth mirrors should not travel later
- that the excluded Cortex/read-model files are stale or disposable
- that the deferred Cortex lane may resume now

## Exact Next Slice Inside This Lane

Still inside `stabilize-root-worktree`, the next honest slice is:

- one bounded truth-mirror carry decision that states whether any coupled root truth mirrors must join the first future stageable subset, or whether they remain a later adjacent hold

Why this is next:

1. the minimum root-worktree subset is now explicit
2. the largest remaining ambiguity inside the held tranche is truth-mirror carry, not support-backlog classification
3. no broader stabilization claim is honest until that mirror relationship is explicit

## Marker Decision

- `none`

Why:

- this pass freezes a minimum future subset boundary only
- no blocker was cleared
- no execution, adoption, or restart breadth widened
