# GitHub Cleanup Retention Classification

Captured: `2026-07-13T16:25:01Z`

## Decision

All accepted remote-branch and local-worktree candidates have explicit retention classes. No cleanup mutation is authorized.

## Summary

- Local worktree candidates: `62`
- Explicit local retention classes: `62`
- Unknown local retention classes: `0`
- Remote branch candidates: `80`
- Removal-safe candidates: `0`
- Deletion, pruning, archive, and worktree removal authority: `false`

## Local Worktrees

| Repository | Registered path or locator | Branch | Dirty | Merged | Retention class |
|---|---|---|---:|---|---|
| ATLAS | `external-worktree:b0r2` | `codex/atlas-vnext-wave1b0-r2-canonical-writer-proof-recovery` | 0 | true | `merged_clean_candidate_hold` |
| ATLAS | `external-worktree:pr108-ci-repro` | `detached` | 0 | true | `detached_reproduction_hold` |
| ATLAS | `tmp/atlas-browserstack-fix` | `codex/atlas-browserstack-provider-capture` | 0 | false | `open_pull_request_hold` |
| DiscordOS | `d` | `codex/mazer-ai-corpus-board` | 0 | false | `unmerged_branch_hold` |
| DiscordOS | `d2` | `codex/mazer-ai-metric-board` | 0 | false | `unmerged_branch_hold` |
| DiscordOS | `d3` | `codex/mazer-board-epic-reconciliation` | 0 | false | `unmerged_branch_hold` |
| DiscordOS | `d4` | `codex/mazer-ui-evidence-board-update` | 0 | false | `unmerged_branch_hold` |
| DiscordOS | `d5` | `codex/mazer-player-input-evidence` | 0 | true | `merged_clean_candidate_hold` |
| DiscordOS | `d6` | `codex/mazer-play-loop-evidence` | 0 | true | `merged_clean_candidate_hold` |
| DiscordOS | `d7` | `codex/mazer-world-turn-evidence` | 0 | true | `merged_clean_candidate_hold` |
| DiscordOS | `runtime/w/d/d2r2` | `codex/d2r2` | 0 | true | `merged_clean_candidate_hold` |
| DiscordOS | `runtime/w/d/d2r2-2` | `codex/d2r2-2` | 0 | true | `merged_clean_candidate_hold` |
| DiscordOS | `runtime/w/d/d2r5` | `codex/d2r5` | 0 | true | `merged_clean_candidate_hold` |
| DiscordOS | `runtime/w/d/d2r6` | `codex/d2r6` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-codex-cli-capability-convergence` | `codex/atlas-operational-prep-codex-cli-capability-convergence` | 6 | true | `dirty_uncommitted_work_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-codex-cli-capability-convergence-r2` | `codex/atlas-operational-prep-codex-cli-capability-convergence-r2` | 9 | true | `dirty_uncommitted_work_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-codex-cli-capability-convergence-r3` | `codex/atlas-operational-prep-codex-cli-capability-convergence-r3` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-codex-cli-capability-convergence-r4` | `codex/atlas-operational-prep-codex-cli-capability-convergence-r4` | 9 | true | `dirty_uncommitted_work_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-codex-cli-capability-convergence-r5` | `codex/atlas-operational-prep-codex-cli-capability-convergence-r5` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-d0-r1-discordos-owner-adapter` | `codex/atlas-operational-prep-d0-r1-discordos-owner-adapter` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-d0-s0-worktree-safe-brand-verifier` | `codex/atlas-operational-prep-d0-s0-worktree-safe-brand-verifier` | 5 | true | `dirty_uncommitted_work_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-d0-s1-r1-scoped-brand-proof-recovery` | `codex/atlas-operational-prep-d0-s1-r1-scoped-brand-proof-recovery` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-d0-s1-scoped-brand-verification-recovery` | `codex/atlas-operational-prep-d0-s1-scoped-brand-verification-recovery` | 5 | true | `dirty_uncommitted_work_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-d2-r0-stack-discordos-runtime-receipt-repair` | `codex/atlas-operational-prep-d2-r0-stack-discordos-runtime-receipt-repair` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-d2-r2-stack-worktree-path-budget` | `codex/atlas-operational-prep-d2-r2-stack-worktree-path-budget` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-d2-r3-stack-permission-precedence-repair` | `codex/atlas-operational-prep-d2-r3-stack-permission-precedence-repair` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-d2-r4-stack-verified-no-change-contract` | `codex/atlas-operational-prep-d2-r4-stack-verified-no-change-contract` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-packet-c0-r1-owner-path-verifier-recovery` | `codex/atlas-operational-prep-packet-c0-r1-owner-path-verifier-recovery` | 9 | true | `dirty_uncommitted_work_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-packet-c0-r2-diff-addressable-proof-recovery` | `codex/atlas-operational-prep-packet-c0-r2-diff-addressable-proof-recovery` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-packet-c0-stack-owner-path-truth` | `codex/atlas-operational-prep-packet-c0-stack-owner-path-truth` | 8 | true | `dirty_uncommitted_work_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-packet-c1-r1-stack-playbook-adoption-recovery` | `codex/atlas-operational-prep-packet-c1-r1-stack-playbook-adoption-recovery` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-packet-c1-s0-stack-playbook-evidence-admission` | `codex/atlas-operational-prep-packet-c1-s0-stack-playbook-evidence-admission` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-packet-c1-stack-playbook-adoption` | `codex/atlas-operational-prep-packet-c1-stack-playbook-adoption` | 6 | true | `dirty_uncommitted_work_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-packet-d0-discordos-owner-adapter` | `codex/atlas-operational-prep-packet-d0-discordos-owner-adapter` | 7 | true | `dirty_uncommitted_work_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1a-r1-stack-runtime-salvage` | `codex/atlas-vnext-wave1a-r1-stack-runtime-salvage` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1a-stack-runtime-bootstrap` | `codex/atlas-vnext-wave1a-stack-runtime-bootstrap` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1a-stack-runtime-bootstrap-2` | `codex/atlas-vnext-wave1a-stack-runtime-bootstrap-2` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1a-stack-runtime-bootstrap-3` | `codex/atlas-vnext-wave1a-stack-runtime-bootstrap-3` | 21 | true | `dirty_uncommitted_work_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b0-canonical-workspace-writer` | `codex/atlas-vnext-wave1b0-canonical-workspace-writer` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b0-canonical-workspace-writer-2` | `codex/atlas-vnext-wave1b0-canonical-workspace-writer-2` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b0-canonical-workspace-writer-3` | `codex/atlas-vnext-wave1b0-canonical-workspace-writer-3` | 14 | true | `dirty_uncommitted_work_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b0-r2-canonical-writer-proof-recovery` | `codex/atlas-vnext-wave1b0-r2-canonical-writer-proof-recovery` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b0-r3-canonical-writer-recovery` | `codex/atlas-vnext-wave1b0-r3-canonical-writer-recovery` | 14 | true | `dirty_uncommitted_work_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b0-r4-canonical-writer-recovery` | `codex/atlas-vnext-wave1b0-r4-canonical-writer-recovery` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b1-r2-canonical-directory-digest-fix` | `codex/atlas-vnext-wave1b1-r2-canonical-directory-digest-fix` | 3 | true | `dirty_uncommitted_work_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b1-r3-canonical-directory-digest-recovery` | `codex/atlas-vnext-wave1b1-r3-canonical-directory-digest-recovery` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b1-r4-canonical-executable-resolution-fix` | `codex/atlas-vnext-wave1b1-r4-canonical-executable-resolution-fix` | 3 | true | `dirty_uncommitted_work_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b1-r5-canonical-executable-resolution-recovery` | `codex/atlas-vnext-wave1b1-r5-canonical-executable-resolution-recovery` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b1-r6-registered-owner-worktree-preservation` | `codex/atlas-vnext-wave1b1-r6-registered-owner-worktree-preservation` | 3 | true | `dirty_uncommitted_work_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b1-r7-registered-owner-worktree-proof-recovery` | `codex/atlas-vnext-wave1b1-r7-registered-owner-worktree-proof-recovery` | 3 | true | `dirty_uncommitted_work_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b1-r8-registered-owner-worktree-network-recovery` | `codex/atlas-vnext-wave1b1-r8-registered-owner-worktree-network-recovery` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b1-r9-registered-owner-worktree-supported-model-recovery` | `codex/atlas-vnext-wave1b1-r9-registered-owner-worktree-supported-model-recovery` | 0 | true | `merged_clean_candidate_hold` |
| _stack | `tmp/_stack-mazer-operator-fix` | `codex/mazer-operator-path-fix-clean` | 0 | false | `unmerged_branch_hold` |
| fawxzzy-fitness | `tmp/fawxzzy-fitness-discord-hotfix` | `codex/discord-message-command-recovery` | 1 | true | `dirty_uncommitted_work_hold` |
| mazer | `input4` | `codex/player-input-movement-correctness` | 0 | false | `unmerged_branch_hold` |
| mazer | `m2` | `codex/ai-metric-contract-parity` | 0 | false | `unmerged_branch_hold` |
| mazer | `playloop` | `codex/play-mode-perpetual-loop` | 0 | true | `merged_clean_candidate_hold` |
| mazer | `tmp/worktrees/mazer-ai-run-corpus-quality-calibration` | `codex/ai-run-corpus-quality-calibration` | 0 | false | `unmerged_branch_hold` |
| mazer | `tmp/worktrees/mazer-viewport-layout-contract` | `codex/viewport-layout-contract` | 0 | false | `unmerged_branch_hold` |
| mazer | `turnlive` | `codex/world-turn-live-integration` | 0 | true | `merged_clean_candidate_hold` |
| mazer | `turnsim` | `codex/turn-synchronous-world-simulation` | 0 | true | `merged_clean_candidate_hold` |
| mazer | `ui3` | `codex/cross-platform-ui-followup` | 0 | false | `unmerged_branch_hold` |

## Remote Branches

All `80` accepted merged-remote candidates are classified as `merged_remote_branch_candidate_hold`. They remain removal-unsafe until a separate, explicitly authorized deletion receipt is produced.

## Governance

- Classification is not cleanup authority.
- Clean is not removal-safe.
- Dirty, unmerged, detached, open-PR, missing, and unavailable candidates remain preserved.
- Every eventual removal requires a correlated pre/post receipt and explicit authority.
