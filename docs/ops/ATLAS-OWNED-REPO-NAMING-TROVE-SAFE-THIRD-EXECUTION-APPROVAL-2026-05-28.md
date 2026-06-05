# Atlas-Owned Repo Naming Trove Safe-Third Execution Approval - 2026-05-28

- Date: `2026-05-28`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only bounded execution approval`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 75%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-REMAINING-FAMILY-DELTA-RECHECK-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-BOUNDED-REWRITE-ROLLBACK-PLAN-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-MARKER-RATCHET-CHECKPOINT-NEXT-2026-05-28.md`
  - `stack.yaml`
  - `stack.lock.yaml`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
- Control-plane checkpoint: `main@9bb230c`

## Objective

Freeze one exact safe-third execution approval packet only:

- `repos/fawxzzy-trove -> repos/trove`

This pass does not:

- rename any local repo directory
- rename any remote
- assume any GitHub-side rename
- reopen the `fawxzzy-fitness` exception
- mutate owner-repo content
- widen approval to any other repo
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `9bb230c`
- status before drafting: existing ATLAS docs-only changes in `AGENTS.md`, atlas-book surfaces, prior naming receipts, refreshed `stack.lock.yaml`, refreshed inventory surfaces, and intentional untracked `archive/`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=366`

## Safe-Third Candidate Recheck

The already-selected safe-third candidate still holds on current facts.

Current durable posture for `trove`:

- stack registry path still reads `repos/fawxzzy-trove`
- source path exists
- target path `repos/trove` does not exist in current stack truth
- `stack.lock.yaml` now pins `trove` on `main`
- dirty state remains `false`
- the repo has no registered extra worktrees
- published inventory still shows no related initiative refs
- remote `origin` exists, but remote-name and GitHub-side rename assumptions remain out of scope

That means the remaining-family delta result is still valid:

- `trove` remains the exact safe-third candidate

## Approval Decision

Approved safe-third candidate:

- `repos/fawxzzy-trove -> repos/trove`

This approval is narrow.

It approves only:

- one local-only rename candidate
- one exact rewrite-surface family
- one exact rollback order
- one exact execution boundary

It does not reopen general rename exploration.

## Exact Local Rename Order Approved

Any future `trove` execution packet must use this exact order:

1. verify `trove` candidate-local preflight again at execution time
2. rename `repos/fawxzzy-trove` to `repos/trove`
3. update `stack.yaml`
4. update `stack.lock.yaml`
5. update `docs/registry/STACK-REPO-INVENTORY.json`
6. update `docs/audits/STACK-REPO-INVENTORY.md`
7. update `docs/atlas-book/11-system-map-graph.md`
8. update `docs/atlas-book/12-restart-and-handoff-guide.md` only if live ladder truth changes
9. add the candidate-specific execution receipt and update `docs/atlas-book/05-receipt-index.md`
10. run `python .\ops\validation\validate_stack.py`

Rule:

- if execution-time state requires extra current-truth surfaces beyond this packet, the execution must stop and reopen bounded planning rather than improvise

## Exact Rewrite Surfaces Approved

Approved rewrite surfaces for the future `trove` execution packet:

- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `docs/atlas-book/11-system-map-graph.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md` only if next-ladder truth changes
- candidate execution receipt
- `docs/atlas-book/05-receipt-index.md`

Why `11-system-map-graph.md` is in scope:

- it still presents `repos/fawxzzy-trove` as the canonical local repo surface

Why `12-restart-and-handoff-guide.md` is conditional:

- it currently points at the `trove` approval packet as the next root naming package
- after execution it should only change if the live ladder advances beyond approval

## Exact Rollback Order Approved

Any future `trove` rollback packet must use this exact reverse order:

1. revert the execution receipt and `docs/atlas-book/05-receipt-index.md`
2. revert `docs/atlas-book/12-restart-and-handoff-guide.md` if it changed
3. revert `docs/atlas-book/11-system-map-graph.md`
4. revert `docs/audits/STACK-REPO-INVENTORY.md`
5. revert `docs/registry/STACK-REPO-INVENTORY.json`
6. revert `stack.lock.yaml`
7. revert `stack.yaml`
8. rename `repos/trove` back to `repos/fawxzzy-trove`
9. run `python .\ops\validation\validate_stack.py`

Rule:

- rollback restores local directory naming and ATLAS control-plane truth only
- rollback never implies remote URL or GitHub-side rename reversal because those stay out of scope from the start

## Exact Still-Blocked Scope

Still blocked after this approval:

- any rename candidate other than `trove`
- any remote rename
- any GitHub-side rename
- any `fawxzzy-fitness` rename
- `mazer`
- `lifeline`
- `playbook`
- any multi-repo rename packet
- any historical-receipt mass rewrite

## Approval Boundary

This pass approves bounded execution-readiness for one exact candidate only.

It does not approve:

- sequence skipping
- extra surface rewrites discovered ad hoc during execution
- using the `trove` packet as precedent for other repos
- execution without fresh preflight recheck

If execution-time state differs from the approved assumptions, the packet must stop rather than widen.

## Marker Read

No numeric marker move is justified from this pass alone.

Hold:

- `Atlas-owned Repo Naming Canonicalization`: `75% -> 75%`

Why:

- a third exact candidate is now approval-frozen
- but the third executed and reconciled packet has still not landed

## Exact Next Package

`Atlas-owned Repo Naming trove local rename execution pass 1`

Why:

- one exact safe-third candidate is now approved
- one exact rewrite order is now approved
- one exact rollback order is now approved
- the next honest move is a single bounded local execution packet for `trove`

## Rule

Safe-third approval must freeze one exact candidate, not reopen general rename exploration.

## Failure Mode

Approval wording becomes broad enough that later execution silently widens to other repos.
