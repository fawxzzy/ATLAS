# Duplicate Surface PR1 Stack Lock Refresh Commit Review

Date: 2026-05-23
Lane: Duplicate Surface Decommission
Mode: Read-only commit classification
Status: Initial classification complete
Target: `<ATLAS_WORKTREES>/pr1-stack-lock-refresh`

## Purpose

This review classifies the three unique commits on `codex/pr1-stack-lock-refresh` so the worktree can later be retained, replayed, archived, or deleted with an explicit rationale.

## Branch state

- Worktree: `<ATLAS_WORKTREES>/pr1-stack-lock-refresh`
- Branch: `codex/pr1-stack-lock-refresh`
- HEAD: `50b8b459c29309d50863261b9787ca0ccb59b28f`
- Remote: `https://github.com/fawxzzy/ATLAS.git`
- Remote branch state: `origin/codex/pr1-stack-lock-refresh` is gone
- Dirty state: clean
- Divergence vs current `main`: `3` commits ahead, `196` behind
- Merge base with `main`: `719c45d813f1c32fe8c493a1a65fa39abd1d9d3d`

## Unique commit inventory

### `50b8b45` - `Refresh stack lock from clean worktree`

- Changed files:
  - `stack.lock.yaml`
- Diff summary:
  - lockfile payload refresh only
- Overlap with current `main`:
  - high subject overlap; current `main` has many later stack-lock refresh commits
  - no code-path change, only serialized lock output
- Current assessment:
  - this commit is not absorbed literally, but its main purpose has been superseded by later lock refreshes on canonical `main`
- Classification:
  - `obsolete`
- Reason:
  - the lock snapshot is tied to an older stack state and does not carry unique tooling logic by itself

### `bd3791f` - `Fix stack lock path normalization`

- Changed files:
  - `ops/_atlas.py`
  - `ops/atlas/observations.py`
  - `ops/stack/generate_lockfile.py`
  - `ops/validation/validate_stack.py`
- Diff summary:
  - adds broader path relativization behavior in `ops/_atlas.py`
  - shortens stable observation path segments
  - changes lock generator path serialization to preserve configured paths rather than resolved relative paths
  - changes validator display-path behavior and observation source-ref normalization
- Overlap with current `main`:
  - these file areas are still live on `main`
  - the exact logic is not present on current `main`
  - current `main` validates green without this patch, so the change is not proven required for present stack health
- Current assessment:
  - substantive tooling change, not just stale output
  - not absorbed literally
  - intent may still matter for long-term stack path policy, but it has not been proven necessary enough to replay automatically
- Classification:
  - `manual review`
- Reason:
  - the patch touches active path and validation semantics and should be explicitly accepted, rejected, or partially replayed rather than silently discarded

### `fda89ab` - `Normalize stack lock to durable refs`

- Changed files:
  - `ops/stack/generate_lockfile.py`
  - `ops/validation/validate_stack.py`
  - `stack.lock.yaml`
- Diff summary:
  - adds durable-branch and canonical-ref resolution in lock generation
  - changes validation to resolve pinned refs against their referenced commit instead of current HEAD
  - refreshes `stack.lock.yaml` to older durable ref choices
- Overlap with current `main`:
  - current `main` does not contain this exact durable-ref implementation
  - current `main` already has a green lock/validation posture after later reconciliation and refresh work
  - the code change is not absorbed literally, even though its operational goal overlaps later canonical-root cleanup
- Current assessment:
  - substantive stack-tooling change
  - operational intent overlaps later governance improvements, but the implementation itself has not been merged or explicitly superseded in code
- Classification:
  - `manual review`
- Reason:
  - this is the commit most likely to deserve a conscious accept/reject decision because it changes lock semantics, not just lock contents

## Aggregate classification

| Commit | Classification | Rationale |
| --- | --- | --- |
| `50b8b45` | obsolete | lock snapshot only; superseded by later lock refreshes |
| `bd3791f` | manual review | substantive path/validation semantics not present on current `main` |
| `fda89ab` | manual review | substantive durable-ref semantics not present on current `main` |

## Recommended disposition

- Worktree disposition now: `retain worktree pending commit-level decision`
- Branch disposition now: `do not delete yet`

## Why deletion is not safe yet

1. Two of the three unique commits contain live tooling changes, not just old serialized outputs.
2. Those tooling changes are not present on current `main` in the same form.
3. Current stack health is green without them, which means they might be obsolete in effect, but that has not been proven strongly enough to discard them without review.

## Recommended next package

Run a focused `PR1 Stack Lock Refresh Commit Disposition Pass` that decides, commit by commit, whether:

- `bd3791f` should be replayed in full or part
- `fda89ab` should be replayed in full or part
- both should be archived as historical evidence and explicitly discarded

Only after that decision should `<ATLAS_WORKTREES>/pr1-stack-lock-refresh` become a delete-later candidate.
