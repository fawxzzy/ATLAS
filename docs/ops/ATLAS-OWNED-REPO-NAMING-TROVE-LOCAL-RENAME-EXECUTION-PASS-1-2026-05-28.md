# Atlas-Owned Repo Naming Trove Local Rename Execution Pass 1 - 2026-05-28

- Date: `2026-05-28`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `bounded local execution`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 75%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-TROVE-SAFE-THIRD-EXECUTION-APPROVAL-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-BOUNDED-REWRITE-ROLLBACK-PLAN-2026-05-28.md`
  - `stack.yaml`
  - `stack.lock.yaml`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
  - `docs/ops/ATLAS-NEXT-BUILD-QUEUE.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
- Control-plane checkpoint: `main@9bb230c`

## Objective

Perform the exact approved safe-third local rename only:

- `repos/fawxzzy-trove -> repos/trove`

This pass does not:

- rename any remote
- assume any GitHub-side rename
- widen into another repo
- touch `fawxzzy-fitness`
- touch `mazer`, `lifeline`, or `playbook`

## Root State

- branch: `main`
- HEAD: `9bb230c`
- status before execution: existing ATLAS docs-only changes in `AGENTS.md`, atlas-book surfaces, prior naming receipts, refreshed `stack.lock.yaml`, refreshed inventory surfaces, and intentional untracked `archive/`
- validation: green before execution at `critical=0 error=0 warning=366`

## Candidate Recheck

The exact approved candidate was still:

- `repos/fawxzzy-trove -> repos/trove`

Pre-execution candidate posture:

- source path exists: `yes`
- target path exists: `no`
- repo branch: `main`
- repo dirty state: `clean`
- repo remote configured: `yes`
- registered worktree count: `1`

Pre-execution local blocker discovered and resolved:

- a trove-local Next dev server process tree was still rooted in `repos/fawxzzy-trove` on port `3101`
- that process tree held the old directory as its working directory and blocked the rename on Windows
- the trove-specific local dev-server tree was stopped before the rename so the bounded execution packet could proceed

## Frozen Rewrite Order Executed

The pass executed only the approved safe-third rewrite order:

1. renamed local directory `repos/fawxzzy-trove` to `repos/trove`
2. updated `stack.yaml`
3. regenerated `stack.lock.yaml`
4. regenerated `docs/registry/STACK-REPO-INVENTORY.json`
5. regenerated `docs/audits/STACK-REPO-INVENTORY.md`
6. updated `docs/atlas-book/11-system-map-graph.md`
7. verified `docs/ops/ATLAS-NEXT-BUILD-QUEUE.md` remained a no-op for this packet
8. added this execution receipt and updated `docs/atlas-book/05-receipt-index.md`
9. reran stack validation

## Exact Execution Evidence

Post-rename local path posture:

- old path exists: `no`
- new path exists: `yes`
- active repo path: `repos/trove`
- repo branch at new path: `main`
- repo commit at new path: `0f5f9fe55bd21aa7f017173f1950d0bd063470c1`
- repo remote configured: `yes`
- repo remote URL unchanged: `https://github.com/fawxzzy/fawxzzy-trove.git`

## Current-Truth Surface Results

Updated current-truth surfaces now point to `repos/trove`:

- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `docs/atlas-book/11-system-map-graph.md`

Verified no-op check:

- `docs/ops/ATLAS-NEXT-BUILD-QUEUE.md`

## Rollback Posture

Rollback was not entered.

Why:

- the rename executed cleanly after the trove-local dev-server lock cleared
- the stack registry rewrite completed cleanly
- the inventory/current-truth rewrite completed cleanly
- validation remained green

If rollback had been required, the frozen order would still be the exact reverse of the approved rewrite packet.

## Exact Result

Execution result:

- `executed cleanly`

Why this is the correct result:

- the safe-third packet remained one-candidate-only
- the only execution blocker was a local trove process tree holding the old path open
- the local directory rename completed before control-plane rewrites
- the rewritten current-truth surfaces now agree on the new canonical local path
- remote naming and GitHub naming stayed untouched

## What Did Not Change

Still out of scope after this pass:

- any remote rename
- any GitHub-side rename
- any multi-repo rename
- `mazer`, `lifeline`, and `playbook`
- the `fawxzzy-fitness` exception
- historical-receipt mass rewrites

## Validation

- `python .\ops\validation\validate_stack.py`
- result after execution pass 1: `critical=0 error=0 warning=366`

## Exact Next Package

`Atlas-owned Repo Naming trove rename proof and reconciliation pass 1`

Why:

- the bounded rename packet has now executed
- the next honest lane step is to prove the canonical local path truth and reconcile any remaining stale references
- marker movement should wait until proof and reconciliation are durable

## Rule

Safe-third naming execution must stay one-candidate-only and follow the frozen rewrite order exactly.

## Failure Mode

A successful simple rename gets used to justify adjacent repo renames in the same pass.
