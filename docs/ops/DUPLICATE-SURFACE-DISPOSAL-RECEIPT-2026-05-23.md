# Duplicate Surface Disposal Receipt

Date: 2026-05-23
Lane: Duplicate Surface Decommission
Mode: Conservative disposal
Status: Pass 1 complete

## Scope

Targets for this pass:

- `C:/ATLAS-worktrees/pr1-stack-lock-refresh`
- `C:/ATLAS-standalone/fitness-release-main`

Out of scope for this pass:

- `branding/**`
- `archive/`
- `tmp/**`
- raw Verta surfaces
- `repos/fawxzzy-fitness`
- `stack.lock.yaml`

## Removed surfaces

### `C:/ATLAS-worktrees/pr1-stack-lock-refresh`

- Status before removal:
  - active worktree: yes
  - branch: `codex/pr1-stack-lock-refresh`
  - HEAD: `50b8b45`
  - dirty state: clean
- Disposal result:
  - worktree directory removed
  - worktree registration pruned
  - local branch deleted

## Retained surfaces

### `C:/ATLAS-standalone/fitness-release-main`

- Retained in this pass: yes
- Reason:
  - still classified as standalone snapshot or evidence surface
  - still dirty (`src/generated/appBuildManifest.json`)
  - no safe deletion path is documented yet
- Future decision required:
  - determine whether its single snapshot commit carries retained evidence value beyond canonical Fitness plus existing retained `tmp` evidence

## Branch disposition

- Deleted local branch:
  - `codex/pr1-stack-lock-refresh`

## Commit classification basis for `pr1-stack-lock-refresh`

The branch was removed only after its unique commits were classified and preserved by receipts:

- `50b8b45` -> obsolete
- `fda89ab` -> reject or obsolete
- `bd3791f` -> useful idea parked, not replayed

Relevant receipts:

- `docs/ops/DUPLICATE-SURFACE-PR1-STACK-LOCK-REFRESH-COMMIT-REVIEW-2026-05-23.md`
- `docs/ops/DUPLICATE-SURFACE-PR1-STACK-LOCK-REFRESH-DECISION-2026-05-23.md`
- `docs/ops/DUPLICATE-SURFACE-PR1-STACK-LOCK-PATH-DISPLAY-PARK-2026-05-23.md`

## Commands run

Attempted normal removal:

- `git worktree remove C:\\ATLAS-worktrees\\pr1-stack-lock-refresh`
- `git branch -d codex/pr1-stack-lock-refresh`

Observed constraint:

- normal worktree removal failed with Windows path-length error
- normal branch deletion failed while the worktree was still attached

Resolved path:

- `Remove-Item -LiteralPath '\\\\?\\C:\\ATLAS-worktrees\\pr1-stack-lock-refresh' -Recurse -Force`
- `git worktree prune`
- `git branch -d codex/pr1-stack-lock-refresh`
- `git branch -D codex/pr1-stack-lock-refresh`

## Unexpected side effect and correction

During external worktree directory removal, tracked `packages/atlas-contracts/**` files disappeared from the root working tree because the removed worktree directory had been holding the only filesystem copy for that tracked package.

Correction applied immediately:

- `git restore --source=HEAD --worktree -- packages/atlas-contracts`

Post-correction result:

- root tracked package restored
- no remaining tracked deletions from the disposal step
- root residue returned to unrelated `branding/**` plus intentional `archive/`

## Why no source truth was lost

1. The canonical ATLAS root remains `C:/ATLAS` on `main`.
2. The removed `pr1` worktree was not treated as source truth; its commit intent was classified and preserved in receipts first.
3. The only potentially useful idea from `bd3791f` was explicitly parked instead of silently discarded.
4. `fitness-release-main` was retained rather than deleted because its evidence status is not fully closed yet.
5. The accidental tracked package deletion side effect was reversed immediately from `HEAD`.

## Validation

- Root validation after disposal and correction:
  - `python .\\ops\\validation\\validate_stack.py --allow-missing-locked-repos`
- Result:
  - `critical=0 error=0 warning=236`

## Pass conclusion

Duplicate Surface Disposal Pass 1 removed one fully classified duplicate worktree surface and retained the still-uncertain standalone Fitness snapshot. No canonical repo, active source truth, or required retained evidence was intentionally deleted in this pass.
