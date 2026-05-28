# Atlas-Owned Repo Naming Safe-First Execution Approval - 2026-05-28

- Date: `2026-05-28`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only bounded execution approval`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 60%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-BOUNDED-REWRITE-ROLLBACK-PLAN-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-SAFE-FIRST-CANDIDATE-DECISION-2026-05-27.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-EXECUTION-GATE-PASS-1-2026-05-27.md`
  - `docs/atlas-book/05-receipt-index.md`
- Control-plane checkpoint: `main@d68f096`

## Objective

Approve one exact safe-first local rename candidate only if the bounded rewrite-order and rollback plan proves it is execution-ready.

This pass does not:

- rename any local repo directory
- rename any remote
- assume any GitHub-side rename
- reopen the `fawxzzy-fitness` exception
- mutate owner-repo content
- widen approval beyond one bounded candidate

## Root State

- branch: `main`
- HEAD: `d68f096`
- status: clean except intentional untracked `archive/`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=310`

## Recomputed Execution-Ready Set

From the durable bounded rewrite and rollback plan:

- `stream`: `execution-packet-ready`
- `foundation`: `not yet`
- `trove`: `blocked`
- `mazer`: `blocked`
- `lifeline`: `blocked`
- `playbook`: `blocked`
- `fawxzzy-fitness`: `preserved exception`

That means exactly one candidate is execution-ready.

## Approval Decision

Approved safe-first candidate:

- `repos/fawxzzy-stream -> repos/stream`

This approval is narrow.

It approves only:

- one local-only rename candidate
- one exact rewrite order
- one exact rollback order
- one exact rewrite-surface family

It does not open the rename lane in general.

## Why `stream` Is Approved

`stream` satisfies the bounded readiness bar already frozen in the prior plan:

- current local path is small in current-truth scope
- repo posture is clean
- repo posture is on `main`
- no configured remote appears in `stack.lock.yaml`
- no current `11-system-map-graph.md` path rewrite is required
- no current `12-restart-and-handoff-guide.md` path rewrite is required
- rollback is explicit and local-only

That makes `stream` the only honest safe-first candidate now.

## Exact Local Rename Order Approved

Any future `stream` execution packet must use this exact order:

1. verify `stream` candidate-local preflight again at execution time
2. rename `repos/fawxzzy-stream` to `repos/stream`
3. update `stack.yaml`
4. update `stack.lock.yaml`
5. update `docs/registry/STACK-REPO-INVENTORY.json`
6. update `docs/audits/STACK-REPO-INVENTORY.md`
7. add the candidate-specific execution receipt and update `docs/atlas-book/05-receipt-index.md`
8. run `python .\ops\validation\validate_stack.py`

Approved no-op checks:

- `docs/atlas-book/11-system-map-graph.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`

Rule:

- if either no-op check turns into a real rewrite need at execution time, the packet must stop and re-open bounded planning rather than improvise

## Exact Rollback Order Approved

Any future `stream` rollback packet must use this exact reverse order:

1. revert execution receipt and `docs/atlas-book/05-receipt-index.md`
2. revert `docs/audits/STACK-REPO-INVENTORY.md`
3. revert `docs/registry/STACK-REPO-INVENTORY.json`
4. revert `stack.lock.yaml`
5. revert `stack.yaml`
6. rename `repos/stream` back to `repos/fawxzzy-stream`
7. run `python .\ops\validation\validate_stack.py`

Rule:

- rollback restores ATLAS control-plane truth and the local directory name only
- rollback never implies remote URL or GitHub-side rename reversal because those are out of scope from the start

## Exact Rewrite Surfaces Approved

Approved rewrite surfaces for the future `stream` execution packet:

- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- candidate execution receipt
- `docs/atlas-book/05-receipt-index.md`

Approved non-rewrite verification surfaces:

- `docs/atlas-book/11-system-map-graph.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`

Historical receipt rule remains unchanged:

- do not mass-rewrite old receipts
- preserve historical path truth outside current-truth surfaces

## Exact Still-Blocked Scope

Still blocked after this approval:

- any rename candidate other than `stream`
- any remote rename assumption
- any GitHub-side rename assumption
- any `fawxzzy-fitness` rename
- `foundation` until the smaller `stream` packet is actually proven
- `trove` while non-`main`
- `mazer` while non-`main`
- `lifeline`
- `playbook`
- any multi-repo rename packet

## Approval Boundary

This pass approves bounded execution-readiness for one candidate only.

It does not approve:

- a general rename lane
- sequence skipping
- extra surface rewrites discovered ad hoc during execution
- execution without fresh preflight recheck

If execution-time state differs from the approved assumptions, the packet must stop rather than widen.

## Exact Next Package

`Atlas-owned Repo Naming stream local rename execution pass 1`

Why:

- one exact candidate is now approved
- one exact rewrite order is now approved
- one exact rollback order is now approved
- the next honest move is a single bounded local execution packet for `stream`, not another general naming pass

## Rule

Approval must freeze one exact bounded candidate, not open the rename lane in general.

## Failure Mode

Approval wording becomes broad enough that later execution widens silently.
