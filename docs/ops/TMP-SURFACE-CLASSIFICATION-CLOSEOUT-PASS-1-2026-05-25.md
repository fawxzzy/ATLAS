# Tmp Surface Classification And Closeout Pass 1

- Date: `2026-05-25`
- Lane: `Tmp Surface Classification And Closeout Pass 1`
- Mode: `classification and closeout planning only`

## Scope

Classify `tmp/` after canonical repo restoration and current stack reconciliation.

This pass does not:

- delete `tmp/` broadly
- delete retained references or historical evidence
- mutate repos
- mutate Supabase, Vercel, Discord, or runtime behavior
- touch `archive/`

## Objective

Confirm that `tmp/` is no longer production-critical source truth, classify the current `tmp/` surface families, and identify later safe-delete candidates without broad mutation.

## Executive Verdict

`tmp/` is noisy, but it is no longer the canonical source of truth for the stack.

What `tmp/` still contains:

- active Git worktrees across multiple repo families
- retained historical evidence and recovery checkpoints
- generated preview/capture/debug residue
- loose top-level files that should later be moved, receipted, or deleted in bounded cleanup passes

What `tmp/` is not doing in this pass:

- driving production repo truth
- driving stack registry truth
- serving as required source truth for deploy, Discord runtime, or Supabase mutation

## Current Shape

- top-level directories: `300`
- top-level files: `916`

## Tmp Surface Table

| Surface family | Classification | Owner | Current role | Reason retained / deferred | Safe-delete later? |
| --- | --- | --- | --- | --- | --- |
| `tmp/atlas-adopt-fawx-den-os-techstack`, `tmp/atlas-foundation-lock-refresh`, `tmp/atlas-playbook-lock-refresh`, `tmp/feedback-task-packet-filter-fix`, `tmp/pr45-clean`, `tmp/r21-seed-wave11`, `tmp/rollback-check-*` | active worktree / retained safety checkpoint / stale-but-not-safe | ATLAS root | retained root worktree and rollback family | still attached to live branches, detached checkpoints, or manual-review residue | later only, after dedicated worktree disposal decision |
| `tmp/fawxzzy-lifeline-rollback-rehearsal-evidence`, `tmp/lifeline-*`, `tmp/r18-main-merge-20260511/repos/fawxzzy-lifeline*` | active worktree / retained reference / stale worktree registration | Lifeline | operator evidence, closeout checkpoints, rollback rehearsal, retained scout lanes | repo family still carries active worktree bindings plus prunable/broken historical registrations | later only, after Lifeline worktree disposal decision |
| `tmp/fawxzzy-playbook-*`, `tmp/playbook-*`, `tmp/r18-main-merge-20260511/repos/fawxzzy-playbook` | active worktree / manual review / stale worktree registration | Playbook | active Playbook side lanes, sustain lanes, research lanes, lint-debt lane, detached closeout lane | still attached to branches or retained for repo-local review; external prunable registrations remain visible | later only, after dedicated Playbook cleanup lane |
| `tmp/fitness-prod-rollout-20260525`, `tmp/fitness-prod-rollout-3f48f9c2`, `tmp/fitness-prod-rollout-623089bb`, `tmp/fitness-prod-rollout-b2e60634` | active worktree / historical rollout evidence | Fitness | detached rollout checkpoints and production-rollout evidence | still live Git worktrees for rollout history; one is named in current closeout receipts | yes, after rollout evidence retention decision |
| `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` | retained reference | Fitness | restoration-era fallback/reference checkout | explicitly demoted by prior tmp dependency receipts; no longer required for canonical verify/preflight path | yes, after duplicate-surface decommission final decision |
| `tmp/fitness-main-post-merge` | historical evidence | Fitness | detached post-merge comparison snapshot | restoration archaeology surface, not active truth | yes, after duplicate-surface decommission final decision |
| broad Fitness historical lane family: `tmp/fitness-*`, `tmp/fawxzzy-fitness-*`, `tmp/history-ui-archaeology`, `tmp/fitness-discord-main-rollout`, `tmp/fitness-discord-update-bot-clean`, `tmp/fitness-feedback-*`, `tmp/fitness-migration-*`, `tmp/fitness-qa-*`, `tmp/fitness-recovery-*` excluding the explicit retained-reference surfaces above | historical evidence / manual review / generated residue | Fitness | recovery, rollout, QA, Discord board, migration, and archaeology lanes | many are clearly historical, but they are mixed with retained evidence and should not be deleted blindly | yes, by bounded family slices after receipt review |
| `tmp/fawxzzy-stream-2b`, `tmp/fawxzzy-stream-2c`, `tmp/r18-main-merge-20260511/repos/fawxzzy-stream` | active worktree / stale worktree registration | Stream | retained stream-family worktrees | still attached to stream repo worktree family | later only, after stream family cleanup decision |
| `tmp/deploy/fawxzzy-trove-prod`, `tmp/release-isolation/fawxzzy-trove-pwa-release`, `tmp/r18-main-merge-20260511/repos/fawxzzy-trove*`, `tmp/trove-*` | active worktree / retained release evidence / generated residue | Trove | deploy/release isolation, preview cleanup, proof captures | worktree bindings still exist for part of the family; some top-level trove files are artifact residue | later only, after Trove release-cutover review |
| `tmp/mazer-*`, `tmp/r18-main-merge-20260511/repos/fawxzzy-mazer`, `tmp/worktrees/fawxzzy-mazer-head-20260416-150909` | active worktree / manual review | Mazer | retained Mazer side lanes and worktree family | active worktree bindings still exist | later only, after Mazer family cleanup decision |
| preview/capture/debug family: `tmp/edge-*`, `tmp/hosted-preview-*`, `tmp/login-review*`, `tmp/install-review*`, `tmp/entry-review*`, `tmp/manual-fitness-review`, `tmp/vercel-*`, `tmp/qa-storage-state-localhost.json`, `tmp/ui-observe-*`, `tmp/atlas-cleanup-resync-status-2026-05-25.txt` | generated residue / historical evidence / manual review | mixed root + repo-family support | browser profiles, preview proof, deploy logs, operator notes, Vercel/debug outputs | not active truth, but some remain useful as short-lived evidence until later review packets land | yes, many after receipts are finalized |
| fitness visual proof family: `tmp/exercise-*`, `tmp/stretch-*`, `tmp/session-*`, `tmp/today-*`, `tmp/bench-*`, `tmp/triceps-*`, `tmp/rest-card-*`, `tmp/smoke-*`, `tmp/bodyweight-goal.html`, `tmp/strength-goal*.html`, `tmp/walking_lunge-verify.html`, `tmp/seated_cable_row-verify.html` | generated residue / historical evidence | Fitness QA / local proof | screenshot, capture, and HTML proof artifacts | no active runtime dependency; evidence only | yes, after QA proof retention decision |
| shared artifact family: `tmp/artifacts`, `tmp/captures`, `tmp/deploy`, `tmp/logs`, `tmp/cleanup-manifests`, `tmp/disposable-local-captures`, `tmp/branding-*`, `tmp/discord-emoji-assets`, `tmp/cortex-*`, `tmp/codex-modal-visuals`, `tmp/cb002b_pydeps`, `tmp/voice-*` | historical evidence / generated residue / manual review | mixed | cross-lane artifact and debugging storage | some are clearly scratch, some are retained support artifacts; no broad delete in this pass | partial later, after family-level review |
| loose top-level files under `tmp/` (`916` files) | generated residue / historical evidence / manual review | mixed | raw captures, logs, SQL probes, HTML snapshots, screenshots, cookies, patch files, proof manifests | highly mixed top-level residue; must be grouped before deletion | yes, but only by typed family buckets |
| `tmp/atlas-qa-release-refresh-pr` | stale filesystem residue | ATLAS root | leftover directory after earlier worktree removal | already documented as non-active worktree residue after Windows deletion failure | yes, strong candidate for later manual-safe deletion |

## Active Worktree Summary

Top-level `tmp/` surfaces confirmed as active worktrees in this pass include:

- root family:
  - `atlas-adopt-fawx-den-os-techstack`
  - `atlas-foundation-lock-refresh`
  - `atlas-playbook-lock-refresh`
  - `feedback-task-packet-filter-fix`
  - `pr45-clean`
  - `r21-seed-wave11`
  - `rollback-check-1716271`
  - `rollback-check-420c5c3`
- Lifeline family:
  - `fawxzzy-lifeline-rollback-rehearsal-evidence`
  - `lifeline-closeout-checkpoint`
  - `lifeline-main-closeout*`
  - `lifeline-pr24-refresh`
  - `lifeline-release-cli-guardrails-worktree`
  - `lifeline-release-replay-verification-clean`
  - `lifeline-wave2-scout`
  - `lifeline-wave3-scout`
- Playbook family:
  - `fawxzzy-playbook-finding-identity`
  - `fawxzzy-playbook-sarif-output`
  - `fawxzzy-playbook-verify-baseline`
  - `playbook-fawx-den-os-doctrine`
  - `playbook-lint-debt-closeout`
  - `playbook-main-closeout`
  - `playbook-pr9-worktree`
  - `playbook-research-phase-grid-evidence`
  - `playbook-research-phase-grid-math`
  - `playbook-sustain-pr19-refresh`
- Fitness family:
  - `fitness-prod-rollout-20260525`
  - `fitness-prod-rollout-3f48f9c2`
  - `fitness-prod-rollout-623089bb`
  - `fitness-prod-rollout-b2e60634`
- Stream family:
  - `fawxzzy-stream-2b`
  - `fawxzzy-stream-2c`
- Trove family:
  - `deploy/fawxzzy-trove-prod`
  - `release-isolation/fawxzzy-trove-pwa-release`
- Mazer family:
  - `mazer-ak-v5`
  - `mazer-before-head`
  - `mazer-o-two-shell`
  - `mazer-p-headless-runner`
  - `mazer-w-three-shell`
  - `mazer-y-script-typing`

These are not safe-delete candidates in this pass.

## Durable References Rechecked

### Stack config and path policy

`stack.yaml` and `README-STACK.md` still reference `tmp/` generically as:

- scratch
- captures
- logs
- previews

They do not declare any specific top-level `tmp` lane as source truth.

### Current receipts and docs still naming specific tmp surfaces

Durable receipts still explicitly name some `tmp` surfaces, including:

- `tmp/fawxzzy-fitness-main-prod-source-3d00eac7`
- `tmp/fitness-main-post-merge`
- `tmp/atlas-qa-release-refresh-pr`
- `tmp/fitness-prod-rollout-20260525`
- retained root worktrees such as `tmp/atlas-adopt-fawx-den-os-techstack`

Interpretation:

- some tmp surfaces are still documentation-visible evidence
- documentation visibility is not the same thing as active production truth
- deletion must respect receipt retention value

### Repo scripts

Observed script-side tmp usage is generic or artifact-oriented, not source-truth-oriented:

- `_stack` runbooks use `tmp/captures/...`
- `_stack` ops helpers create ephemeral tmp artifact roots
- no current stack contract in this pass proves a top-level `tmp/<lane>` checkout is production-critical source truth

## Production Truth Verdict

Confirmed in this pass:

- canonical repos and stack registry surfaces exist outside `tmp/`
- `tmp` is not the active source of truth for stack registry, lock, or canonical repos
- `tmp` is not required by this pass for Discord, Supabase, or deploy mutation

Therefore:

- no `tmp` surface is production-critical source truth in the current stack posture

## Safe-Delete Candidates Later

Strongest later candidates, once their receipts or family cleanup lanes approve them:

- `tmp/atlas-qa-release-refresh-pr`
  - already classified as stale filesystem residue
- detached Fitness rollout worktrees:
  - `tmp/fitness-prod-rollout-3f48f9c2`
  - `tmp/fitness-prod-rollout-623089bb`
  - `tmp/fitness-prod-rollout-b2e60634`
  - potentially `tmp/fitness-prod-rollout-20260525` after final rollout retention review
- broad generated proof/capture residue families:
  - top-level `vercel-*` files
  - top-level `ui-observe-*` files
  - top-level screenshot/json/html proof files from the fitness visual proof family
- `tmp/fawxzzy-fitness-main-prod-source-3d00eac7`
  - only after duplicate-surface decommission makes the final retention decision
- `tmp/fitness-main-post-merge`
  - only after historical evidence retention is cleared

## Blockers

1. `tmp/` still contains many active Git worktrees across root, Lifeline, Playbook, Fitness, Stream, Trove, and Mazer families.
2. Historical evidence and generated residue are mixed together at top level instead of already separated into final retained buckets.
3. Some tmp surfaces are still named in durable receipts, so deletion cannot be inferred from age alone.
4. Root self-lock policy still makes root commit sequencing awkward for docs-only closeout work, so queue discipline matters.

## Files Changed

- `docs/ops/TMP-SURFACE-CLASSIFICATION-CLOSEOUT-PASS-1-2026-05-25.md`

## Next Package

`Vercel Helper Surface Final Review`

Why:

- tmp is now classified enough to stop treating it as unknown pressure
- the next narrow closeout lane is Vercel helper surface retention/deletion review
- later tmp cleanup can proceed with stronger family-level boundaries after Vercel and Fitness residue reviews land

## Closeout Verdict

`tmp` is no longer acting as production truth.

The remaining tmp problem is not source-truth ambiguity. It is:

- active retained worktrees
- retained evidence
- generated preview/capture/debug residue
- delayed deletion candidates that need bounded later packages
