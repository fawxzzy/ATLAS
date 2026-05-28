# Atlas-Owned Repo Naming Stream Local Rename Execution Pass 1 - 2026-05-28

- Date: `2026-05-28`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `bounded local execution`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 70%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-SAFE-FIRST-EXECUTION-APPROVAL-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-BOUNDED-REWRITE-ROLLBACK-PLAN-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-MARKER-RATCHET-CHECKPOINT-3-2026-05-28.md`
  - `stack.yaml`
  - `stack.lock.yaml`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
  - `docs/ops/ATLAS-NEXT-BUILD-QUEUE.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/05-receipt-index.md`

## Objective

Perform the exact approved safe-first local rename only:

- `repos/fawxzzy-stream -> repos/stream`

This pass does not:

- rename any remote
- assume any GitHub-side rename
- widen into another repo
- touch `fawxzzy-fitness`
- touch `foundation`, `trove`, `mazer`, `lifeline`, or `playbook`

## Root State

- branch: `main`
- HEAD: `529a1bb`
- status: clean except intentional untracked `archive/`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=310`

## Candidate Recheck

The exact approved candidate is still:

- `repos/fawxzzy-stream -> repos/stream`

Current source and target posture:

- source path exists: `yes`
- target path exists: `no`

## Candidate-Local Preflight Result

The candidate does **not** pass execution-time preflight.

Why:

- the repo itself is clean
- the repo itself is on `main`
- no remote is configured
- but active linked worktrees still depend on the current repo path

That means the frozen rule from the bounded rewrite-and-rollback plan applies:

- if a candidate-local preflight requirement fails, execution stays blocked

## Exact Blocking Evidence

Current `stream` worktree posture:

- main worktree:
  - `repos/fawxzzy-stream`
  - branch: `main`
- active linked worktree:
  - `tmp/fawxzzy-stream-2b`
  - branch: `codex/fstrm-2b-twitch-auth`
- active linked worktree:
  - `tmp/fawxzzy-stream-2c`
  - branch: `codex/fstrm-2c-eventsub-runtime`
- retained/prunable linked surface:
  - `tmp/r18-main-merge-20260511/repos/fawxzzy-stream`
  - detached
  - `prunable gitdir file points to non-existent location`

These surfaces still depend on the current main repo path and gitdir structure.

Executing the local rename anyway would risk silently breaking linked-worktree metadata and violating the safe-first contract.

## Why Execution Was Stopped

The bounded rewrite-and-rollback plan froze this execution-time rule:

1. source path exists
2. target path does not exist
3. current repo branch posture is admitted
4. dirty state is admitted
5. no active worktree or adjacent retained surface still depends on the old local path
6. no current-truth control-plane surface outside the planned rewrite set still requires the old path
7. remote rename remains explicitly out of scope

The failure is at step `5`.

So execution stopped before the local directory rename step.

## What Was Not Changed

No rename executed.

These remained intentionally unchanged:

- `repos/fawxzzy-stream`
- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `docs/ops/ATLAS-NEXT-BUILD-QUEUE.md`
- `docs/atlas-book/11-system-map-graph.md`

Those surfaces are still correct because the canonical local path is still:

- `repos/fawxzzy-stream`

## Rollback Evidence

No rollback was needed.

Why:

- the execution packet failed closed before step `2` of the frozen rewrite order
- no filesystem rename occurred
- no control-plane rewrite occurred

Rollback state therefore remains:

- not entered

## Exact Current-Truth Surfaces Still Pointing At The Old Path

These current-truth surfaces still point at `repos/fawxzzy-stream`, and they remain correct in this blocked execution result:

- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `docs/ops/ATLAS-NEXT-BUILD-QUEUE.md`

Verified no-op current-truth checks:

- `docs/atlas-book/11-system-map-graph.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`

## Exact Result

Execution result:

- `blocked before rename`

Why this is the correct result:

- the safe-first packet is only honest if it remains one-candidate-only **and** preflight-complete
- forcing the rename through active linked worktrees would widen the risk surface beyond the approved packet

## What Still Remains Blocked

Still blocked after this pass:

- the `stream` rename itself until worktree dependency clearance lands
- any multi-repo rename
- any remote rename
- any GitHub-side rename
- `foundation`, `trove`, `mazer`, `lifeline`, and `playbook`
- the `fawxzzy-fitness` exception

## Exact Next Package

`Atlas-owned Repo Naming stream worktree dependency clearance pass 1`

Why:

- the blocker is no longer naming doctrine
- the blocker is exact linked-worktree dependency on the current repo path
- clearing or governing those worktree dependencies must happen before a safe rename can execute

## Rule

Safe-first naming execution must stay one-candidate-only and follow the frozen rewrite order exactly.

## Failure Mode

A "simple" rename silently widens into linked-worktree breakage, adjacent repo rename pressure, or remote-name changes.
