# Branch Disposal Inventory

Date: 2026-05-22
Mode: Inventory only
Status: Branches classified for later review; no deletions performed

## Purpose

This report classifies every current local ATLAS-root branch into disposal categories without deleting anything.

It follows the current branch cleanup rule:

1. do not delete a branch until its contents are classified
2. useful work is committed, packaged, or routed
3. a safety branch or remote reference preserves it
4. root is reconciled with `origin/main`
5. the branch is explicitly listed as safe to delete

## Current Root Posture

- `main` has been pushed to `origin/main`
- current `HEAD`: `6973fea`
- validation posture: `critical=0 error=0 warning=100`
- root working tree: only untracked `archive/`

## Category Summary

| Category | Count | Meaning |
| --- | ---: | --- |
| `keep` | `1` | active branch that remains the current root truth |
| `safety checkpoint` | `2` | explicit rollback or preservation branches created during root reconciliation |
| `already preserved` | `14` | replay or recovery branches intentionally retained until a later disposal pass |
| `stale but not safe to delete` | `15` | branches with unique commits not on `main` or other unresolved preservation value |
| `safe delete candidate` | `40` | branches already merged into `main` with no unique commits ahead of `main`; review still required before deletion |

## Keep

| Branch | Reason |
| --- | --- |
| `main` | current reconciled and validated root branch |

## Safety Checkpoints

| Branch | SHA | Reason |
| --- | --- | --- |
| `codex/branch-worktree-normalization-docs` | `409781c` | preserves the docs-only normalization package checkpoint before the later safety-check and rebase work |
| `codex/root-reconciliation-pre-rebase` | `a6e68dc` | preserves the exact pre-rebase root tip before rebasing `main` onto `origin/main` |

## Already Preserved

These branches remain intentionally visible because they are part of the replay or recovery evidence chain and are not ready for disposal review yet.

| Branch | SHA | Ahead of `main` | Reason |
| --- | --- | ---: | --- |
| `hotfix/may19-dropdown-runtime-stability` | `420c5c3` | `2` | recovery-era preservation branch |
| `recovery/may19-functional-baseline` | `420c5c3` | `2` | recovery baseline branch |
| `replay/current-thread-product-rq-009` | `05d4198` | `4` | replay restoration branch |
| `replay/current-thread-product-wave-01` | `069fe80` | `3` | replay restoration branch |
| `replay/discord-connector-prod-catchup` | `ed716f2` | `13` | replay preservation branch |
| `replay/edit-day-dropdown-reorder-parity` | `883eb35` | `12` | replay preservation branch |
| `replay/older-thread-wave-01` | `420c5c3` | `2` | replay or recovery preservation branch |
| `replay/pw-011-progression-layer-spec` | `de5570b` | `5` | replay restoration branch |
| `replay/pw-012-target-mutation-foundation` | `6c1eb7d` | `6` | replay restoration branch |
| `replay/pw-013-qualification-window-foundation` | `7708ea1` | `7` | replay restoration branch |
| `replay/pw-014-target-mutation-editor-ui` | `45138be` | `8` | replay restoration branch |
| `replay/pw-015-manual-review-checklist-layout` | `2764de2` | `9` | replay restoration branch |
| `replay/rq-012-edit-day-shared-scaffold` | `99fd40a` | `11` | replay preservation branch |
| `replay/steps-cardio-prod-catchup` | `80ca253` | `71` | explicitly preserved replay branch with package receipts already recorded |

## Stale But Not Safe To Delete

These branches still have unique commits not on `main`, but they do not yet have a current disposal approval.

| Branch | SHA | Upstream | Ahead of `main` | Reason |
| --- | --- | --- | ---: | --- |
| `codex/adopt-fawx-den-os-techstack` | `89cc250` | `origin/main` | `1` | unique commit still outside `main` |
| `codex/archive-admission-normalization` | `322acfe` | `origin/codex/archive-admission-normalization` | `1` | unique archive-admission branch commit |
| `codex/closeout-trove-lifeline-pilot` | `21c5ece` | `origin/codex/closeout-trove-lifeline-pilot` | `5` | unique historical lane commits |
| `codex/cortex-context-assembler-wave3` | `fc1616d` | `origin/codex/cortex-context-assembler-wave3` | `1` | unique branch tip not on `main` |
| `codex/cortex-receipt-interpretation-consumption-feedback-wave11-seed` | `9366416` | `origin/main` | `1` | unique seed commit not on `main` |
| `codex/cortex-receipt-interpretation-contract-wave9` | `1c08570` | `origin/codex/cortex-receipt-interpretation-contract-wave9` | `10` | large unique Cortex branch |
| `codex/cortex-receipt-interpretation-stack-consumption-wave10` | `5bb1bf8` | none | `11` | unique local-only Cortex branch |
| `codex/discord-moderation-receipt` | `abfa724` | `origin/codex/discord-moderation-receipt` | `14` | unique Discord doctrine branch |
| `codex/fix-feedback-task-packet-status-filter` | `6e6b7c7` | none | `1` | local-only unique commit |
| `codex/lane-ai-cortex-receipt-audit-handoff` | `b5ca8c3` | `origin/codex/lane-ai-cortex-receipt-audit-handoff` | `4` | unique lane handoff branch |
| `codex/post-r20-cortex-artifact-normalization` | `5bb1bf8` | none | `11` | local-only historical Cortex branch |
| `codex/pr1-stack-lock-refresh` | `50b8b45` | `origin/codex/pr1-stack-lock-refresh` | `3` | previously identified as a preservation-review branch |
| `codex/progression-layer-spec-update` | `d87907f` | `origin/codex/progression-layer-spec-update` | `16` | large unique progression/update branch |
| `codex/remove-stale-cortex-contract` | `78390c5` | `origin/codex/remove-stale-cortex-contract` | `2` | unique contract-cleanup branch |
| `codex/remove-stale-cortex-contract-v2` | `7b8a52c` | `origin/codex/remove-stale-cortex-contract-v2` | `2` | unique contract-cleanup follow-up |

## Safe Delete Candidates

These branches are already merged into `main` and have `0` commits ahead of `main`. They are candidates only; no deletion has been performed.

| Branch | SHA | Upstream | Behind `main` | Candidate reason |
| --- | --- | --- | ---: | --- |
| `chore/unify-ambient-background-and-icon-color` | `cab8836` | none | `155` | fully merged and no unique commits remain |
| `codex/archive-normalization-closeout` | `676751a` | `origin/codex/archive-normalization-closeout` | `16` | fully merged and no unique commits remain |
| `codex/atlas-platform-v1-contracts` | `7e1f989` | `origin/codex/atlas-platform-v1-contracts` | `103` | fully merged and no unique commits remain |
| `codex/atlas-qa-release-refresh-pr` | `7d11cbe` | `origin/codex/atlas-qa-release-refresh-pr` | `63` | fully merged and no unique commits remain |
| `codex/cortex-admission-planning` | `63e1fb4` | `origin/main` | `4` | fully merged and no unique commits remain |
| `codex/cortex-current-state` | `1dc9b66` | `origin/codex/cortex-current-state` | `148` | fully merged and no unique commits remain |
| `codex/cortex-rail-seed-progression` | `ca4ba0e` | `origin/codex/cortex-rail-seed-progression` | `141` | fully merged and no unique commits remain |
| `codex/cortex-rail-seed-progression-r17` | `2779dea` | `origin/codex/cortex-rail-seed-progression-r17` | `103` | fully merged and no unique commits remain |
| `codex/cortex-rail-state-reader-wave2` | `308cf69` | `origin/codex/cortex-rail-state-reader-wave2` | `144` | fully merged and no unique commits remain |
| `codex/cortex-receipt-interpretation-stack-consumption-contract` | `992fc4a` | none | `81` | fully merged and no unique commits remain |
| `codex/cortex-receipt-interpretation-stack-consumption-wave10-clean` | `fa404f2` | `origin/codex/cortex-receipt-interpretation-stack-consumption-wave10-clean` | `84` | fully merged and no unique commits remain |
| `codex/cortex-stack-consumer-default-routing-wave8` | `e503596` | `origin/codex/cortex-stack-consumer-default-routing-wave8` | `105` | fully merged and no unique commits remain |
| `codex/cortex-surface-reconciliation` | `2183929` | `origin/main` | `137` | fully merged and no unique commits remain |
| `codex/discord-moderation-receipt-clean` | `debc3f4` | `origin/codex/discord-moderation-receipt-clean` | `42` | fully merged and no unique commits remain |
| `codex/discord-update-workflow-memory` | `a385024` | `origin/codex/discord-update-workflow-memory` | `39` | fully merged and no unique commits remain |
| `codex/final-verta-closeout-self-lock` | `15d4c2a` | `origin/codex/final-verta-closeout-self-lock` | `20` | fully merged and no unique commits remain |
| `codex/fitness-dal-slice-2` | `bb16755` | `origin/main` | `78` | fully merged and no unique commits remain |
| `codex/foundation-atlas-admission-alignment` | `051cfe6` | `origin/codex/foundation-atlas-admission-alignment` | `9` | fully merged and no unique commits remain |
| `codex/foundation-pnpm-protected-refresh` | `3b9362d` | `origin/codex/foundation-pnpm-protected-refresh` | `48` | fully merged and no unique commits remain |
| `codex/foundation-release-lock-refresh` | `5b26857` | `origin/codex/foundation-release-lock-refresh` | `50` | fully merged and no unique commits remain |
| `codex/lifeline-protected-refresh-main` | `8e38c3c` | none | `44` | fully merged and no unique commits remain |
| `codex/playbook-release-lock-refresh` | `7e808b4` | `origin/codex/playbook-release-lock-refresh` | `59` | fully merged and no unique commits remain |
| `codex/pnpm-protected-refresh` | `10d6b77` | `origin/codex/pnpm-protected-refresh` | `61` | fully merged and no unique commits remain |
| `codex/post-r20-cortex-artifact-normalization-land` | `e0c32de` | `origin/codex/post-r20-cortex-artifact-normalization` | `76` | fully merged and no unique commits remain |
| `codex/r18-main-land` | `79e9611` | `origin/main` | `88` | fully merged and no unique commits remain |
| `codex/r19-main-land` | `be4fdd7` | `origin/main` | `82` | fully merged and no unique commits remain |
| `codex/r20-main-land` | `70d48f8` | `origin/main` | `74` | fully merged and no unique commits remain |
| `codex/r21-main-clean` | `b73dc3c` | none | `72` | fully merged and no unique commits remain |
| `codex/r21-main-land` | `9e73779` | `origin/main` | `70` | fully merged and no unique commits remain |
| `codex/sparse-protected-stack-validation` | `82fb59f` | `origin/codex/sparse-protected-stack-validation` | `55` | fully merged and no unique commits remain |
| `codex/spotify-club-phase-3-queue-approval` | `620bfa2` | `origin/main` | `32` | fully merged and no unique commits remain |
| `codex/stack-progression-checkpoint` | `ce532ed` | `origin/main` | `6` | fully merged and no unique commits remain |
| `codex/validate-archive-registry-surfaces` | `92d6f65` | `origin/codex/validate-archive-registry-surfaces` | `12` | fully merged and no unique commits remain |
| `codex/verta-absorption-closeout-checkpoint` | `54e927a` | `origin/codex/verta-absorption-closeout-checkpoint` | `25` | fully merged and no unique commits remain |
| `codex/verta-closeout-final-self-lock` | `34626bb` | `origin/codex/verta-closeout-final-self-lock` | `22` | fully merged and no unique commits remain |
| `codex/verta-derivative-absorption-phase-gates` | `49511e5` | `origin/main` | `35` | fully merged and no unique commits remain |
| `codex/verta-gate-final-lock-refresh` | `477edaa` | `origin/codex/verta-gate-final-lock-refresh` | `27` | fully merged and no unique commits remain |
| `codex/verta-gate-stack-lock-refresh` | `017d918` | `origin/codex/verta-gate-stack-lock-refresh` | `29` | fully merged and no unique commits remain |
| `codex/verta-lookup-stack-lock-refresh` | `7db98d0` | `origin/codex/verta-lookup-stack-lock-refresh` | `31` | fully merged and no unique commits remain |
| `codex/verta-post-merge-stack-lock-refresh` | `b052ec0` | `origin/codex/verta-post-merge-stack-lock-refresh` | `33` | fully merged and no unique commits remain |

## Review Rules For The Later Disposal Pass

Before any actual deletion:

1. keep `main`
2. keep both safety checkpoint branches until the disposal list is explicitly approved
3. keep all replay and recovery branches until the preservation lane explicitly closes
4. review every `stale but not safe to delete` branch for unique content, remote preservation, or packaging needs
5. only then review the `safe delete candidate` list for actual removal

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
- Branch & Worktree Normalization: `70%`
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
