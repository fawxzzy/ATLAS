# Worktree Disposal Receipt

Date: 2026-05-22
Mode: Worktree Disposal Pass 1
Status: Safe worktrees removed only; one broken registration pruned; no force operations

## Purpose

This receipt records the first reviewed worktree disposal pass after the committed worktree retention inventory.

The pass followed `docs/ops/WORKTREE-DISPOSAL-INVENTORY-2026-05-22.md` and removed only worktrees classified there as `safe to remove later`, plus one explicitly identified broken/prunable worktree registration.

## Root Posture At Execution

- current branch: `main`
- current `HEAD`: `744e7bc`
- branch state before pass: `main...origin/main`
- root working tree before pass: only untracked `archive/`
- `stack.lock.yaml`: not modified in this pass

## Commands Run

```powershell
git worktree remove "C:/ATLAS/tmp/archive-registry-pr45-clean"
git worktree remove "C:/ATLAS/tmp/atlas-discord-workflow-memory"
git worktree remove "C:/ATLAS/tmp/atlas-moderation-receipt-clean"
git worktree remove "C:/ATLAS/tmp/atlas-pnpm-protected-refresh"
git worktree remove "C:/ATLAS/tmp/atlas-qa-release-refresh-pr"
git worktree remove "C:/ATLAS/tmp/atlas-sparse-verify"
git worktree remove "C:/ATLAS/tmp/atlas-stack-checkpoint"
git worktree remove "C:/ATLAS/tmp/cortex-admission-planning"
git worktree remove "C:/ATLAS/tmp/r18-main-merge-20260511"
git worktree remove "C:/ATLAS/tmp/r21-main-clean"
git worktree remove "C:/ATLAS/tmp/spotify-club-phase-3-queue-approval"
git worktree remove "C:/ATLAS-worktrees/fitness-dal-slice-2"
git worktree prune --verbose
git branch -d codex/discord-update-workflow-memory
git branch -d codex/discord-moderation-receipt-clean
git branch -d codex/pnpm-protected-refresh
git branch -d codex/atlas-qa-release-refresh-pr
git branch -d codex/stack-progression-checkpoint
git branch -d codex/cortex-admission-planning
git branch -d codex/r21-main-land
git branch -d codex/r21-main-clean
git branch -d codex/spotify-club-phase-3-queue-approval
git branch -d codex/fitness-dal-slice-2
git branch -d codex/cortex-surface-reconciliation
python .\ops\validation\validate_stack.py --allow-missing-locked-repos
```

## Removed Worktrees

Removed cleanly in this pass: `11`

| Worktree path | Branch at removal | Result |
| --- | --- | --- |
| `C:/ATLAS/tmp/archive-registry-pr45-clean` | detached | removed cleanly |
| `C:/ATLAS/tmp/atlas-discord-workflow-memory` | `codex/discord-update-workflow-memory` | removed cleanly |
| `C:/ATLAS/tmp/atlas-moderation-receipt-clean` | `codex/discord-moderation-receipt-clean` | removed cleanly |
| `C:/ATLAS/tmp/atlas-pnpm-protected-refresh` | `codex/pnpm-protected-refresh` | removed cleanly |
| `C:/ATLAS/tmp/atlas-sparse-verify` | detached | removed cleanly |
| `C:/ATLAS/tmp/atlas-stack-checkpoint` | `codex/stack-progression-checkpoint` | removed cleanly |
| `C:/ATLAS/tmp/cortex-admission-planning` | `codex/cortex-admission-planning` | removed cleanly |
| `C:/ATLAS/tmp/r18-main-merge-20260511` | `codex/r21-main-land` | removed cleanly |
| `C:/ATLAS/tmp/r21-main-clean` | `codex/r21-main-clean` | removed cleanly |
| `C:/ATLAS/tmp/spotify-club-phase-3-queue-approval` | `codex/spotify-club-phase-3-queue-approval` | removed cleanly |
| `C:/ATLAS-worktrees/fitness-dal-slice-2` | `codex/fitness-dal-slice-2` | removed cleanly |

## Partial Removal Outcome

One safe-remove worktree left Git cleanly but not the filesystem cleanly.

| Worktree path | Branch | Outcome | Later action |
| --- | --- | --- | --- |
| `C:/ATLAS/tmp/atlas-qa-release-refresh-pr` | `codex/atlas-qa-release-refresh-pr` | `git worktree remove` cleared the active Git worktree binding, but Windows returned `Permission denied` while deleting the directory contents | treat the remaining directory as later filesystem residue review; it is no longer an active Git worktree |

Live confirmation after the pass:

- `git worktree list` no longer includes `C:/ATLAS/tmp/atlas-qa-release-refresh-pr`
- `codex/atlas-qa-release-refresh-pr` was deletable afterward and is now gone
- the directory `C:/ATLAS/tmp/atlas-qa-release-refresh-pr` still exists on disk and remains out of scope for this pass

## Pruned Registration

`git worktree prune --verbose` removed the broken registration for:

- `worktrees/cortex-surface-reconciliation`

That pruned registration corresponded to the previously missing worktree path `C:/ATLAS/tmp/cortex-surface-reconciliation`.

## Deleted Branches

Deleted branches in this pass: `11`

| Branch | Reason |
| --- | --- |
| `codex/discord-update-workflow-memory` | worktree removed cleanly and branch was already merged into `main` |
| `codex/discord-moderation-receipt-clean` | worktree removed cleanly and branch was already merged into `main` |
| `codex/pnpm-protected-refresh` | worktree removed cleanly and branch was already merged into `main` |
| `codex/atlas-qa-release-refresh-pr` | active worktree binding cleared; branch was already merged into `main` |
| `codex/stack-progression-checkpoint` | worktree removed cleanly and branch was already merged into `main` |
| `codex/cortex-admission-planning` | worktree removed cleanly and branch was already merged into `main` |
| `codex/r21-main-land` | worktree removed cleanly and branch was already merged into `main` |
| `codex/r21-main-clean` | worktree removed cleanly and branch was already merged into `main` |
| `codex/spotify-club-phase-3-queue-approval` | worktree removed cleanly and branch was already merged into `main` |
| `codex/fitness-dal-slice-2` | worktree removed cleanly and branch was already merged into `main` |
| `codex/cortex-surface-reconciliation` | broken worktree registration was pruned and branch was already merged into `main` |

## Retained Worktrees

These worktrees remain intentionally after Pass 1.

| Worktree path | Classification | Reason retained |
| --- | --- | --- |
| `C:/ATLAS` | `keep active` | live root worktree |
| `C:/ATLAS/tmp/atlas-adopt-fawx-den-os-techstack` | `stale but not safe` | branch is still ahead of `main` by `1` |
| `C:/ATLAS/tmp/atlas-foundation-lock-refresh` | `manual review` | dirty artifact zip and extracted directory remain |
| `C:/ATLAS/tmp/atlas-playbook-lock-refresh` | `manual review` | dirty artifact zip and extracted directory remain |
| `C:/ATLAS/tmp/feedback-task-packet-filter-fix` | `stale but not safe` | local-only unique commit remains |
| `C:/ATLAS/tmp/pr45-clean` | `manual review` | modified doc and modified `stack.lock.yaml` remain in the worktree |
| `C:/ATLAS/tmp/r21-seed-wave11` | `stale but not safe` | branch is still ahead of `main` by `1` |
| `C:/ATLAS/tmp/rollback-check-1716271` | `safety checkpoint` | detached rollback snapshot intentionally retained |
| `C:/ATLAS/tmp/rollback-check-420c5c3` | `safety checkpoint` | detached recovery-era rollback snapshot intentionally retained |
| `C:/ATLAS-worktrees/pr1-stack-lock-refresh` | `stale but not safe` | branch is still ahead of `main` by `3` |

## Non-Goals

- no force removal was used
- no dirty worktree was removed
- no safety checkpoint was removed
- no stale-but-not-safe worktree was removed
- no stash entries were changed
- `archive/` was not modified, cleaned, or staged
- `stack.lock.yaml` was not regenerated or edited

## Validation Result

- command: `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`
- result: `critical=0 error=0 warning=180 info=0`
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
- Branch & Worktree Normalization: `92%`
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
