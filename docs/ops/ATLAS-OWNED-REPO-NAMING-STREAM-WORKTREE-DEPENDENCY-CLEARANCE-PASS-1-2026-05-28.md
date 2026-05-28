# Atlas-Owned Repo Naming Stream Worktree Dependency Clearance Pass 1 - 2026-05-28

- Date: `2026-05-28`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `bounded local dependency clearance`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 70%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-STREAM-LOCAL-RENAME-EXECUTION-PASS-1-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-STREAM-RENAME-PROOF-RECONCILIATION-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-SAFE-FIRST-EXECUTION-APPROVAL-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-BOUNDED-REWRITE-ROLLBACK-PLAN-2026-05-28.md`
  - `docs/ops/RETAINED-SURFACE-MANUAL-DISPOSAL-PASS-2026-05-27.md`
  - `docs/ops/RETAINED-SURFACE-REGISTRY-HYGIENE-REVIEW-2026-05-27.md`
  - `docs/atlas-book/05-receipt-index.md`
- Control-plane checkpoint: `main@6d9578e`

## Objective

Classify and clear the exact `stream` worktree blockers named by the blocked execution receipt without widening into rename execution or adjacent retained-surface cleanup.

This pass does not:

- rename `repos/fawxzzy-stream`
- rename any remote
- assume any GitHub-side rename
- touch `fawxzzy-fitness`
- touch `archive/`
- widen into broader retained-surface cleanup

## Root State

- branch: `main`
- HEAD: `6d9578e`
- status: clean except intentional untracked `archive/`
- validation: green before clearance at `critical=0 error=0 warning=310`

## Exact Blocker Set Rechecked

The blocked execution receipt named exactly these three blockers:

1. `tmp/fawxzzy-stream-2b`
2. `tmp/fawxzzy-stream-2c`
3. `tmp/r18-main-merge-20260511/repos/fawxzzy-stream`

All clearance work in this pass stayed inside that exact set.

## Exact Classification

| Blocker | Current state | Classification | Why |
| --- | --- | --- | --- |
| `tmp/fawxzzy-stream-2b` | registered linked worktree, branch `codex/fstrm-2b-twitch-auth`, local modifications and untracked files present | `active dependency block` | still an active linked worktree with live local changes, so deleting it would violate the safe-first boundary |
| `tmp/fawxzzy-stream-2c` | registered linked worktree, branch `codex/fstrm-2c-eventsub-runtime`, local modifications and untracked files present | `active dependency block` | still an active linked worktree with live local changes, so deleting it would violate the safe-first boundary |
| `tmp/r18-main-merge-20260511/repos/fawxzzy-stream` | path already missing on disk; only a prunable `stream` worktree admin entry remained | `safe-delete now` | no live filesystem surface remained, and `git worktree prune --dry-run --verbose` showed only one stale `stream` admin record pointing to a non-existent gitdir |

## Verification Evidence

### `tmp/fawxzzy-stream-2b`

Verified:

- present in `git -C repos/fawxzzy-stream worktree list --porcelain`
- branch: `codex/fstrm-2b-twitch-auth`
- worktree-local status includes:
  - modified tracked files
  - untracked files and directories
- `.git` points at:
  - `repos/fawxzzy-stream/.git/worktrees/fawxzzy-stream-2b`

Result:

- not disposable in this pass

### `tmp/fawxzzy-stream-2c`

Verified:

- present in `git -C repos/fawxzzy-stream worktree list --porcelain`
- branch: `codex/fstrm-2c-eventsub-runtime`
- worktree-local status includes:
  - modified tracked files
  - untracked files and directories
- `.git` points at:
  - `repos/fawxzzy-stream/.git/worktrees/fawxzzy-stream-2c`

Result:

- not disposable in this pass

### `tmp/r18-main-merge-20260511/repos/fawxzzy-stream`

Verified:

- path does not exist on disk
- `git -C repos/fawxzzy-stream worktree list --porcelain` still showed:
  - `worktree tmp/r18-main-merge-20260511/repos/fawxzzy-stream`
  - `detached`
  - `prunable gitdir file points to non-existent location`
- corresponding admin entry existed at:
  - `repos/fawxzzy-stream/.git/worktrees/fawxzzy-stream`
- that admin entry `gitdir` file pointed at the missing path
- `git -C repos/fawxzzy-stream worktree prune --dry-run --verbose` proposed exactly:
  - `Removing worktrees/fawxzzy-stream: gitdir file points to non-existent location`

Result:

- safe exact-subset clearance

## Clearance Action Performed

Performed:

- `git -C repos/fawxzzy-stream worktree prune --verbose`

Observed result:

- `Removing worktrees/fawxzzy-stream: gitdir file points to non-existent location`

Why this stays exact-subset:

- the dry run showed only the single stale `stream` admin record
- no active `2b` or `2c` worktree entry was removed
- no filesystem delete outside the exact blocker set occurred

## Post-Clearance Worktree State

After clearance:

- `repos/fawxzzy-stream` remains the main worktree
- `tmp/fawxzzy-stream-2b` remains registered and active
- `tmp/fawxzzy-stream-2c` remains registered and active
- the stale `r18` `stream` admin entry no longer appears in `git worktree list --porcelain`

So the blocker set is smaller, but the rename is still blocked.

## Exact Removed Or Retained Blockers

Removed in this pass:

- stale linked-worktree admin entry for `tmp/r18-main-merge-20260511/repos/fawxzzy-stream`

Retained in this pass:

- `tmp/fawxzzy-stream-2b`
- `tmp/fawxzzy-stream-2c`

Why they remain:

- both are active linked worktrees with live local changes
- they are not same-class dead retained residue
- clearing them would widen this pass into active worktree disposal

## What Remains Blocked

Still blocked after this pass:

- `repos/fawxzzy-stream -> repos/stream` rename execution
- any multi-repo rename
- any remote rename
- any GitHub-side rename
- any `fawxzzy-fitness` rename

The remaining exact blocker class is now:

- active linked-worktree dependency on `tmp/fawxzzy-stream-2b`
- active linked-worktree dependency on `tmp/fawxzzy-stream-2c`

## Why No Rename Happened

This pass is dependency clearance only.

Rule held:

- dependency clearance must not silently become rename execution

So no rename step, no registry rewrite, and no current-truth path change happened here.

## Validation

- `python .\ops\validation\validate_stack.py`
- result after clearance and receipt drafting: `critical=0 error=0 warning=310`

## Exact Next Package

`Atlas-owned Repo Naming stream local rename execution pass 2 only after exact 2b and 2c dependency clearance or explicit closure`

Why:

- the dead `r18` blocker is gone
- the only blockers left are active linked worktrees with live changes
- another rename attempt before those are cleared would just reproduce the same fail-closed result

## Rule

Dependency clearance must stay exact-subset and must not silently become rename execution.

## Failure Mode

A blocker-clearance pass deletes an active worktree or widens into adjacent retained-surface cleanup.
