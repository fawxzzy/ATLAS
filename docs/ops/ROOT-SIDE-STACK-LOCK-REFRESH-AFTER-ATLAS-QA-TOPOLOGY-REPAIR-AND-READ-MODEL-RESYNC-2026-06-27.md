# Root-Side Stack Lock Refresh After ATLAS QA Topology Repair And Read-Model Re-Sync - 2026-06-27

- Date: `2026-06-27`
- Lane: `root stack-lock re-sync after QA topology repair`
- Owner: `ATLAS/root`
- Mode: `root lock refresh plus validation proof`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/ops/STACK-LOCKFILE.md`
  - `docs/ops/ATLAS-QA-TOPOLOGY-REPAIR-AND-READ-MODEL-RESYNC-2026-06-27.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `ops/stack/generate_lockfile.py`
  - `ops/validation/validate_stack.py`
  - `stack.lock.yaml`
  - `runtime/receipts/validation/stack-validation.latest.json`
  - `runtime/receipts/validation/stack-validation.latest.md`
- Control-plane checkpoint: `main@6d47295a`

## Objective

Clear the remaining root validation blocker class left after the QA topology repair by refreshing `stack.lock.yaml` to the current intentional child-repo dirty-state truth.

## Why Refresh Was Admissible

The live drift was not a generator bug and not an unexpected pin movement.

Canonical lock diff inspection proved:

- no metadata drift
- no excluded-surface drift
- no repo `ref` or `commit` drift
- only four `dirty`-field flips:
  - `foundation`
  - `lifeline`
  - `stream`
  - `trove`

That exactly matched the intentional child-repo QA manifest/path and `docs/qa.md` edits already introduced during the protected-QA topology repair.

## Execution

Commands run:

- `python .\ops\stack\generate_lockfile.py`
- `python .\ops\validation\validate_stack.py --ratchet`

`stack.lock.yaml` now pins the current working-set truth for the four affected repos as `dirty: true`.

## Validation Result

Current validation output:

- `critical=0 error=0 warning=0 info=0`

The earlier blocker class is closed:

- `stack-lock-drift`
- `stack-lock-render-drift`
- `stack-lock-worktree-drift` for `foundation`
- `stack-lock-worktree-drift` for `lifeline`
- `stack-lock-worktree-drift` for `stream`
- `stack-lock-worktree-drift` for `trove`

## Current Truth After Refresh

The stack is now re-synced at the root validation layer, but not at the protected release-readiness layer.

Protected-QA current truth is unchanged apart from the lock refresh:

- adopted repos remain `fitness`, `foundation`, `lifeline`, `playbook`, `stream`, and `trove`
- `foundation` still has one fresh current-SHA run and is blocked only because its latest promotion status is `blocked`
- `fitness` is still blocked by stale Fitness Hobby governance checkpoints plus stale and wrong-SHA receipt provenance
- `lifeline`, `playbook`, `stream`, and `trove` are still blocked by stale and wrong-SHA receipt provenance

## Exact Next Honest Move

- owner-side fresh receipt regeneration for `fitness`, `lifeline`, `playbook`, `stream`, and `trove`
- owner-side promotion-status conversion or policy reconciliation for the fresh `foundation` run

