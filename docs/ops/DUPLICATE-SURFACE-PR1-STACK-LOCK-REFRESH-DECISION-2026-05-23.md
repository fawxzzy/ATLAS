# Duplicate Surface PR1 Stack Lock Refresh Decision

Date: 2026-05-23
Lane: Duplicate Surface Decommission
Mode: Manual-review decision pass
Status: Initial decision complete
Target worktree: `C:/ATLAS-worktrees/pr1-stack-lock-refresh`
Target commits:

- `bd3791f`
- `fda89ab`

## Purpose

This pass decides whether the two remaining manual-review commits on `codex/pr1-stack-lock-refresh` should be accepted, rejected, replayed, or preserved as historical evidence.

## Current doctrine baseline

Two current facts matter more than the original branch intent:

1. Root validation is green on canonical `main`.
2. `ops/stack/generate_lockfile.py` currently describes the lockfile as generated from the "current managed git working set."

That means any replay must add clear value without weakening current lockfile truth or broadening path semantics in ways that are no longer justified.

## Commit: `bd3791f` - `Fix stack lock path normalization`

### Files changed

- `ops/_atlas.py`
- `ops/atlas/observations.py`
- `ops/stack/generate_lockfile.py`
- `ops/validation/validate_stack.py`

### Intent

- broaden `atlas_relative()` fallback behavior so sibling paths outside the ATLAS root can still render as shorter logical paths
- shorten stable observation path segments
- preserve configured repo and excluded-surface paths in lock generation instead of always re-deriving display paths from resolved filesystem locations
- normalize validator display paths and observation source refs

### Current-main absorption check

- Not absorbed literally.
- The exact code is not present on current `main`.
- Current validation and lockflow are already green without it.

### Value assessment

- The path-display part has some plausible value, especially for sibling surfaces like `ATLAS-worktrees/...` or `ATLAS-standalone/...`.
- The rest of the patch is broader than that:
  - it changes observation slug sizing
  - it changes source-ref normalization behavior
  - it changes lock and validation path rendering behavior across multiple code paths
- Those broader changes are not proven necessary by the current green state.

### Risk assessment

- Medium.
- The patch mixes several semantics changes into one branch-local fix.
- Replaying it whole would create churn in active path and observation logic without a current failing case that requires it.

### Decision

- Classification: `split/rewrite needed`
- Recommended disposition: do not replay the original commit as-is

### Why

The useful part is narrower than the branch patch. If later review decides shorter non-absolute display refs for sibling ATLAS-adjacent surfaces are worthwhile, that should be implemented as a small canonical-root patch with explicit tests or receipts, not by replaying this mixed semantics commit wholesale.

## Commit: `fda89ab` - `Normalize stack lock to durable refs`

### Files changed

- `ops/stack/generate_lockfile.py`
- `ops/validation/validate_stack.py`
- `stack.lock.yaml`

### Intent

- resolve canonical lock refs from durable branches instead of the current checkout
- validate pinned refs against resolved branch or tag commits rather than current `HEAD`
- refresh `stack.lock.yaml` to those durable refs

### Current-main absorption check

- Not absorbed literally.
- Current `main` does not contain this durable-ref implementation.
- Current `main` already has a green lockfile and validation posture after later reconciliation and refresh work.

### Value assessment

- The original intent was understandable during earlier branch-chaos cleanup: reduce drift from temporary checkouts.
- That need is much smaller now because:
  - canonical repo paths are restored
  - root reconciliation is complete
  - `_stack` proof now runs from canonical paths

### Conflict with current doctrine

- Strong.
- Current lockfile doctrine is tied to the current managed working set, not an inferred durable branch.
- Replaying this commit would change what the lockfile claims to pin.
- That risks hiding active checkout reality behind durable-branch resolution, which is the opposite of what current cleanup governance has been proving.

### Risk assessment

- High.
- This is not just output churn; it changes stack lock semantics.

### Decision

- Classification: `reject/obsolete`
- Recommended disposition: preserve as historical evidence only, do not replay

### Why

The branch solved an old problem with a semantics change that no longer matches the current restored-canonical-repo model. The present stack is healthier because the canonical source surfaces were restored, not because lock truth was abstracted away from the current working set.

## Aggregate decision

| Commit | Decision | Recommended action |
| --- | --- | --- |
| `bd3791f` | split/rewrite needed | Do not replay as-is. Keep only as idea or evidence unless a later small path-display patch is explicitly justified. |
| `fda89ab` | reject/obsolete | Do not replay. Preserve as historical evidence only. |

## Worktree disposition after this pass

- Worktree: `retain temporarily as historical evidence until receipt is committed`
- Branch: `later delete candidate after receipt lands and no follow-up rewrite is requested`

## Recommended next package

1. Commit this decision receipt by itself.
2. Unless a later targeted path-display patch is explicitly requested, mark `codex/pr1-stack-lock-refresh` as:
   - historical evidence for `bd3791f`
   - rejected obsolete semantics for `fda89ab`
3. Then the worktree and branch can move into a later disposal pass rather than an implementation lane.
