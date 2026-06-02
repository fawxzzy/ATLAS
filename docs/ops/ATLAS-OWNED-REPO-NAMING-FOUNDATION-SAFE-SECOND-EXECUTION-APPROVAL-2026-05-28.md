# Atlas-Owned Repo Naming Foundation Safe-Second Execution Approval - 2026-05-28

- Date: `2026-05-28`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only bounded execution approval`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 74%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-SAFE-SECOND-CANDIDATE-MASS-RECHECK-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-BOUNDED-REWRITE-ROLLBACK-PLAN-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-MARKER-RATCHET-CHECKPOINT-6-2026-05-28.md`
  - `stack.yaml`
  - `stack.lock.yaml`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
- Control-plane checkpoint: `main@9bb230c`

## Objective

Freeze one exact safe-second execution approval packet only:

- `repos/fawxzzy-foundation -> repos/foundation`

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
- status before drafting: existing ATLAS docs-only changes in `AGENTS.md`, atlas-book surfaces, `PROCESS-AMPLIFICATION-PASS-2-2026-05-28.md`, and the prior safe-second mass-recheck receipt, plus intentional untracked `archive/`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=311`

## Safe-Second Candidate Recheck

The already-selected safe-second candidate still holds on current facts.

Current durable posture for `foundation`:

- stack registry path still reads `repos/fawxzzy-foundation`
- source path exists
- target path `repos/foundation` does not exist in current stack truth
- `stack.lock.yaml` still pins `foundation` on `main`
- dirty state remains `false`
- the repo still has one registered worktree only
- published inventory still shows no related initiative refs
- remote `origin` exists, but remote-name and GitHub-side rename assumptions remain out of scope

That means the mass-recheck decision is still valid:

- `foundation` remains the exact safe-second candidate

## Approval Decision

Approved safe-second candidate:

- `repos/fawxzzy-foundation -> repos/foundation`

This approval is narrow.

It approves only:

- one local-only rename candidate
- one exact rewrite-surface family
- one exact rollback order
- one exact execution boundary

It does not reopen general rename exploration.

## Exact Local Rename Order Approved

Any future `foundation` execution packet must use this exact order:

1. verify `foundation` candidate-local preflight again at execution time
2. rename `repos/fawxzzy-foundation` to `repos/foundation`
3. update `stack.yaml`
4. update `stack.lock.yaml`
5. update `docs/registry/STACK-REPO-INVENTORY.json`
6. update `docs/audits/STACK-REPO-INVENTORY.md`
7. update `docs/atlas-book/11-system-map-graph.md`
8. update `docs/atlas-book/12-restart-and-handoff-guide.md`
9. add the candidate-specific execution receipt and update `docs/atlas-book/05-receipt-index.md`
10. run `python .\ops\validation\validate_stack.py`

Rule:

- if execution-time state requires extra current-truth surfaces beyond this packet, the execution must stop and reopen bounded planning rather than improvise

## Exact Rewrite Surfaces Approved

Approved rewrite surfaces for the future `foundation` execution packet:

- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `docs/atlas-book/11-system-map-graph.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- candidate execution receipt
- `docs/atlas-book/05-receipt-index.md`

Why `12-restart-and-handoff-guide.md` is now in scope:

- the current live restart ladder now names the `foundation` approval packet directly
- leaving that surface unchanged after execution would strand stale next-step truth

## Exact Rollback Order Approved

Any future `foundation` rollback packet must use this exact reverse order:

1. revert the execution receipt and `docs/atlas-book/05-receipt-index.md`
2. revert `docs/atlas-book/12-restart-and-handoff-guide.md`
3. revert `docs/atlas-book/11-system-map-graph.md`
4. revert `docs/audits/STACK-REPO-INVENTORY.md`
5. revert `docs/registry/STACK-REPO-INVENTORY.json`
6. revert `stack.lock.yaml`
7. revert `stack.yaml`
8. rename `repos/foundation` back to `repos/fawxzzy-foundation`
9. run `python .\ops\validation\validate_stack.py`

Rule:

- rollback restores local directory naming and ATLAS control-plane truth only
- rollback never implies remote URL or GitHub-side rename reversal because those stay out of scope from the start

## Exact Still-Blocked Scope

Still blocked after this approval:

- any rename candidate other than `foundation`
- any remote rename
- any GitHub-side rename
- any `fawxzzy-fitness` rename
- `mazer`
- `trove`
- `lifeline`
- `playbook`
- any multi-repo rename packet
- any historical-receipt mass rewrite

## Approval Boundary

This pass approves bounded execution-readiness for one exact candidate only.

It does not approve:

- sequence skipping
- extra surface rewrites discovered ad hoc during execution
- using the `foundation` packet as precedent for other repos
- execution without fresh preflight recheck

If execution-time state differs from the approved assumptions, the packet must stop rather than widen.

## Marker Read

No numeric marker move is justified from this pass alone.

Hold:

- `Atlas-owned Repo Naming Canonicalization`: `74% -> 74%`

Why:

- a second exact candidate is now approval-frozen
- but the second executed and reconciled packet has still not landed

## Exact Next Package

`Atlas-owned Repo Naming foundation local rename execution pass 1`

Why:

- one exact safe-second candidate is now approved
- one exact rewrite order is now approved
- one exact rollback order is now approved
- the next honest move is a single bounded local execution packet for `foundation`

## Rule

Safe-second approval must freeze one exact candidate, not reopen general rename exploration.

## Pattern

first executed packet lands -> family-wide recheck selects one safe-second candidate -> exact safe-second approval freezes the packet -> one bounded local execution packet opens

## Failure Mode

Approval wording becomes broad enough that later execution silently widens to other repos.
