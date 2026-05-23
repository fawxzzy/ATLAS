# Worktree Disposal / Retention Inventory

Date: 2026-05-22
Mode: Inventory only
Status: Active worktrees classified for later retention or removal; no worktrees removed

## Purpose

This report classifies every active ATLAS-root worktree after Branch Disposal Pass 1.

The immediate problem is no longer unknown branch contents. The remaining branch-deletion blockers are active worktree bindings, detached checkpoint worktrees, and a smaller set of dirty or broken worktree states that still need manual review.

## Current Root Posture

- root branch: `main`
- root `HEAD`: `fda9e97`
- root branch state: `main...origin/main`
- root working tree: only untracked `archive/`
- validation posture at inventory time: `critical=0 error=0 warning=113`

## Category Summary

| Category | Count | Meaning |
| --- | ---: | --- |
| `keep active` | `1` | the current root worktree remains the live stack surface |
| `safety checkpoint` | `2` | detached rollback checkouts preserved for later explicit review |
| `stale but not safe` | `4` | clean worktrees that still point at unique commits not on `main` |
| `safe to remove later` | `12` | clean worktrees with no unique commits beyond `main`, or detached clean snapshots already reachable from `main` |
| `manual review` | `4` | dirty, missing, or otherwise broken worktrees that need review before removal |

## Active Worktree Table

| Path | Branch | HEAD | Dirty state | Location class | Merged / preserved posture | Branch deletion blocker | Classification | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `C:/ATLAS` | `main` | `fda9e97` | dirty: untracked `archive/` | root | live root truth | n/a | `keep active` | not a disposal target in this lane |
| `C:/ATLAS/tmp/archive-registry-pr45-clean` | detached | `3cdafe9` | clean | tmp worktree | detached commit already reachable from `main` | no | `safe to remove later` | clean verification snapshot |
| `C:/ATLAS/tmp/atlas-adopt-fawx-den-os-techstack` | `codex/adopt-fawx-den-os-techstack` | `89cc250` | clean | tmp worktree | ahead of `main` by `1` unique commit | yes | `stale but not safe` | unique branch tip still outside `main` |
| `C:/ATLAS/tmp/atlas-discord-workflow-memory` | `codex/discord-update-workflow-memory` | `a385024` | clean | tmp worktree | already merged into `main` | yes | `safe to remove later` | branch survived Pass 1 only because of this worktree |
| `C:/ATLAS/tmp/atlas-foundation-lock-refresh` | `codex/foundation-pnpm-protected-refresh` | `3b9362d` | dirty: untracked artifact zip and extracted folder | tmp worktree | already merged into `main` | yes | `manual review` | generated artifact residue must be reviewed before removal |
| `C:/ATLAS/tmp/atlas-moderation-receipt-clean` | `codex/discord-moderation-receipt-clean` | `debc3f4` | clean | tmp worktree | already merged into `main` | yes | `safe to remove later` | clean merged branch worktree |
| `C:/ATLAS/tmp/atlas-playbook-lock-refresh` | `codex/sparse-protected-stack-validation` | `82fb59f` | dirty: untracked artifact zip and extracted folder | tmp worktree | already merged into `main` | yes | `manual review` | duplicate verification artifacts remain |
| `C:/ATLAS/tmp/atlas-pnpm-protected-refresh` | `codex/pnpm-protected-refresh` | `10d6b77` | clean | tmp worktree | already merged into `main` | yes | `safe to remove later` | clean merged branch worktree |
| `C:/ATLAS/tmp/atlas-qa-release-refresh-pr` | `codex/atlas-qa-release-refresh-pr` | `7d11cbe` | clean | tmp worktree | already merged into `main` | yes | `safe to remove later` | clean PR review worktree |
| `C:/ATLAS/tmp/atlas-sparse-verify` | detached | `82fb59f` | clean | tmp worktree | detached commit already reachable from `main` | no | `safe to remove later` | redundant clean verification checkout of the same commit family as `atlas-playbook-lock-refresh` |
| `C:/ATLAS/tmp/atlas-stack-checkpoint` | `codex/stack-progression-checkpoint` | `ce532ed` | clean | tmp worktree | already merged into `main` | yes | `safe to remove later` | clean merged checkpoint worktree |
| `C:/ATLAS/tmp/cortex-admission-planning` | `codex/cortex-admission-planning` | `63e1fb4` | clean | tmp worktree | already merged into `main` | yes | `safe to remove later` | clean merged branch worktree |
| `C:/ATLAS/tmp/cortex-surface-reconciliation` | `codex/cortex-surface-reconciliation` | `2183929` | missing / prunable registration | tmp worktree | already merged into `main` | yes | `manual review` | `git worktree list` reports `prunable gitdir file points to non-existent location` |
| `C:/ATLAS/tmp/feedback-task-packet-filter-fix` | `codex/fix-feedback-task-packet-status-filter` | `6e6b7c7` | clean | tmp worktree | ahead of `main` by `1` unique commit | yes | `stale but not safe` | local-only unique branch tip remains |
| `C:/ATLAS/tmp/pr45-clean` | detached | `3cdafe9` | dirty: modified doc and `stack.lock.yaml` | tmp worktree | detached snapshot not safe while dirty | no | `manual review` | shares commit with `archive-registry-pr45-clean` but has local modifications |
| `C:/ATLAS/tmp/r18-main-merge-20260511` | `codex/r21-main-land` | `9e73779` | clean | tmp worktree | already merged into `main` | yes | `safe to remove later` | historical merge worktree retained only by branch binding |
| `C:/ATLAS/tmp/r21-main-clean` | `codex/r21-main-clean` | `b73dc3c` | clean | tmp worktree | already merged into `main` | yes | `safe to remove later` | clean merged cleanup worktree |
| `C:/ATLAS/tmp/r21-seed-wave11` | `codex/cortex-receipt-interpretation-consumption-feedback-wave11-seed` | `9366416` | clean | tmp worktree | ahead of `main` by `1` unique commit | yes | `stale but not safe` | unique seed branch tip remains |
| `C:/ATLAS/tmp/rollback-check-1716271` | detached | `1716271` | clean | tmp worktree | detached rollback snapshot not reachable from `main` | no | `safety checkpoint` | explicit rollback evidence should not be removed without review |
| `C:/ATLAS/tmp/rollback-check-420c5c3` | detached | `420c5c3` | clean | tmp worktree | detached rollback snapshot not reachable from `main` | no | `safety checkpoint` | recovery-era rollback evidence |
| `C:/ATLAS/tmp/spotify-club-phase-3-queue-approval` | `codex/spotify-club-phase-3-queue-approval` | `620bfa2` | clean | tmp worktree | already merged into `main` | yes | `safe to remove later` | clean merged workflow worktree |
| `C:/ATLAS-worktrees/fitness-dal-slice-2` | `codex/fitness-dal-slice-2` | `bb16755` | clean | external ATLAS worktree | already merged into `main` | yes | `safe to remove later` | external worktree path but no unique commits remain |
| `C:/ATLAS-worktrees/pr1-stack-lock-refresh` | `codex/pr1-stack-lock-refresh` | `50b8b45` | clean | external ATLAS worktree | ahead of `main` by `3` unique commits | yes | `stale but not safe` | preserved PR review branch still outside `main` |

## Safe-To-Remove Later Candidates

These are clean worktrees with no unique branch content beyond `main`, or detached clean snapshots already reachable from `main`. No removal was performed in this inventory pass.

| Path | Why safe later | Unique commits | Contents clean | Branch preserved elsewhere | Exact later removal command |
| --- | --- | ---: | --- | --- | --- |
| `C:/ATLAS/tmp/archive-registry-pr45-clean` | detached snapshot already reachable from `main` | `0` | yes | n/a | `git worktree remove \"C:/ATLAS/tmp/archive-registry-pr45-clean\"` |
| `C:/ATLAS/tmp/atlas-discord-workflow-memory` | merged branch retained only because of worktree binding | `0` | yes | yes, on `main` | `git worktree remove \"C:/ATLAS/tmp/atlas-discord-workflow-memory\"; git branch -d codex/discord-update-workflow-memory` |
| `C:/ATLAS/tmp/atlas-moderation-receipt-clean` | merged branch retained only because of worktree binding | `0` | yes | yes, on `main` | `git worktree remove \"C:/ATLAS/tmp/atlas-moderation-receipt-clean\"; git branch -d codex/discord-moderation-receipt-clean` |
| `C:/ATLAS/tmp/atlas-pnpm-protected-refresh` | merged branch retained only because of worktree binding | `0` | yes | yes, on `main` | `git worktree remove \"C:/ATLAS/tmp/atlas-pnpm-protected-refresh\"; git branch -d codex/pnpm-protected-refresh` |
| `C:/ATLAS/tmp/atlas-qa-release-refresh-pr` | merged branch retained only because of worktree binding | `0` | yes | yes, on `main` | `git worktree remove \"C:/ATLAS/tmp/atlas-qa-release-refresh-pr\"; git branch -d codex/atlas-qa-release-refresh-pr` |
| `C:/ATLAS/tmp/atlas-sparse-verify` | detached clean verification checkout already reachable from `main` | `0` | yes | n/a | `git worktree remove \"C:/ATLAS/tmp/atlas-sparse-verify\"` |
| `C:/ATLAS/tmp/atlas-stack-checkpoint` | merged branch retained only because of worktree binding | `0` | yes | yes, on `main` | `git worktree remove \"C:/ATLAS/tmp/atlas-stack-checkpoint\"; git branch -d codex/stack-progression-checkpoint` |
| `C:/ATLAS/tmp/cortex-admission-planning` | merged branch retained only because of worktree binding | `0` | yes | yes, on `main` | `git worktree remove \"C:/ATLAS/tmp/cortex-admission-planning\"; git branch -d codex/cortex-admission-planning` |
| `C:/ATLAS/tmp/r18-main-merge-20260511` | merged branch retained only because of worktree binding | `0` | yes | yes, on `main` | `git worktree remove \"C:/ATLAS/tmp/r18-main-merge-20260511\"; git branch -d codex/r21-main-land` |
| `C:/ATLAS/tmp/r21-main-clean` | merged branch retained only because of worktree binding | `0` | yes | yes, on `main` | `git worktree remove \"C:/ATLAS/tmp/r21-main-clean\"; git branch -d codex/r21-main-clean` |
| `C:/ATLAS/tmp/spotify-club-phase-3-queue-approval` | merged branch retained only because of worktree binding | `0` | yes | yes, on `main` | `git worktree remove \"C:/ATLAS/tmp/spotify-club-phase-3-queue-approval\"; git branch -d codex/spotify-club-phase-3-queue-approval` |
| `C:/ATLAS-worktrees/fitness-dal-slice-2` | merged branch retained only because of worktree binding | `0` | yes | yes, on `main` | `git worktree remove \"C:/ATLAS-worktrees/fitness-dal-slice-2\"; git branch -d codex/fitness-dal-slice-2` |

## Manual Review Worktrees

These worktrees should not be removed until their local state is resolved or explicitly preserved elsewhere.

| Path | Review blocker | Later likely action |
| --- | --- | --- |
| `C:/ATLAS/tmp/atlas-foundation-lock-refresh` | untracked artifact zip and extracted directory | review whether artifacts are disposable build residue, then remove worktree and branch if confirmed clean |
| `C:/ATLAS/tmp/atlas-playbook-lock-refresh` | untracked artifact zip and extracted directory | review whether artifacts are disposable build residue, then remove worktree and branch if confirmed clean |
| `C:/ATLAS/tmp/cortex-surface-reconciliation` | missing worktree path with prunable registration | inspect `git worktree list` anomaly, then prune or remove deliberately |
| `C:/ATLAS/tmp/pr45-clean` | modified `docs/ops/ATLAS-ARCHIVE-NORMALIZATION-CHECKPOINT.md` and modified `stack.lock.yaml` | preserve or discard local modifications explicitly before any removal |

## Stale But Not Safe Worktrees

These worktrees are clean, but they still point at unique commits not on `main`, so they remain preservation or review surfaces rather than disposal candidates.

| Path | Branch or snapshot | Unique posture | Reason to retain |
| --- | --- | --- | --- |
| `C:/ATLAS/tmp/atlas-adopt-fawx-den-os-techstack` | `codex/adopt-fawx-den-os-techstack` | ahead of `main` by `1` | unique branch tip still outside `main` |
| `C:/ATLAS/tmp/feedback-task-packet-filter-fix` | `codex/fix-feedback-task-packet-status-filter` | ahead of `main` by `1` | local-only branch with unique commit |
| `C:/ATLAS/tmp/r21-seed-wave11` | `codex/cortex-receipt-interpretation-consumption-feedback-wave11-seed` | ahead of `main` by `1` | unique seed branch tip remains |
| `C:/ATLAS-worktrees/pr1-stack-lock-refresh` | `codex/pr1-stack-lock-refresh` | ahead of `main` by `3` | preserved PR review branch still outside `main` |

## Safety Checkpoint Worktrees

These detached rollback worktrees are not branch blockers, but they are explicit checkpoint surfaces and should remain until a later rollback-evidence review says otherwise.

| Path | HEAD | Reason |
| --- | --- | --- |
| `C:/ATLAS/tmp/rollback-check-1716271` | `1716271` | detached rollback snapshot not reachable from `main` |
| `C:/ATLAS/tmp/rollback-check-420c5c3` | `420c5c3` | detached recovery-era rollback snapshot not reachable from `main` |

## Recommended Later Order

1. Remove the clean `safe to remove later` worktrees under `C:/ATLAS/tmp`.
2. Remove the clean external ATLAS worktree `C:/ATLAS-worktrees/fitness-dal-slice-2`.
3. Delete the now-unbound merged branches from the same safe-remove set.
4. Review the dirty or broken worktrees before any prune or branch disposal.
5. Leave the unique-commit and rollback-check worktrees untouched until their preservation lanes close.

## Non-Goals

- no worktrees were removed
- no branches were deleted in this inventory pass
- no force operations were used
- no stashes were changed
- `archive/` was not modified, cleaned, or staged
- `stack.lock.yaml` was not regenerated or edited

## Validation Result

- command: `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`
- result: `critical=0 error=0 warning=160 info=0`
- latest report: `runtime/receipts/validation/stack-validation.latest.md`

## Marker Table

- Verta Absorption: `99%`
- Archive Normalization: `100%`
- ATLAS Core Phase: `92%`
- `_stack` Readiness: `40%`
- Foundation Alignment: `100%`
- Lifeline Readiness: `97%`
- Playbook Maturity: `92%`
- Cortex Readiness: `35%`
- Fitness Source-of-Truth Reset: `100%`
- Fitness QA/LLEL Workflow: `96%`
- Fitness Branch Cleanup / Main-Only Governance: `96%`
- Fitness Recovery Preservation: `80%`
- Branch & Worktree Normalization: `85%`
- Unified Workflow Convergence: `0%`
- Inventory & Truth Map: `15%`
- Full Stack Re-sync, Clean & Closeout: `22% paused`
- Vision & Future Alignment: `0%`
- Dependency Untangling: `0%`
- Playbook Everywhere + Cortex Interface: `0%`
- Knowledge Capture & Transfer: `10%`
- Feedback Loop Readiness: `0%`
- Sandbox Simulation Readiness: `0%`
- AI Long-Run Batch Orchestration: `20%`
- Truth Map & ATLAS Book: `0%`
- Discord OS Extraction Review: `0%`
- Discord Workflow & Documentation Publishing: `0%`
- Post-Convergence Lane Split Readiness: `0%`
