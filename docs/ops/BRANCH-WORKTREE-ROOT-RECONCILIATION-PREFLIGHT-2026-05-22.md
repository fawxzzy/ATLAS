# Branch & Worktree Root Reconciliation Preflight

Date: 2026-05-22
Mode: Read-only and docs-only
Status: Preflight complete; direct root reconciliation is not yet approved

## Purpose

This preflight determines whether the ATLAS root is safe to reconcile with `origin/main` after the replay preservation packages were recorded.

It does not switch branches, pull `main`, regenerate `stack.lock.yaml`, or modify stash state.

## Safe-To-Reconcile Verdict

Verdict: `not safe yet`

Interpretation:

- transport-level Git risk is lower than before
- governance and preservation blockers still remain
- do not run `git pull --ff-only origin main` yet

Why the verdict is not yet safe:

1. The root working tree is still dirty with docs-only changes that are not yet preserved on `main`.
2. Replay-touched root doctrine surfaces are packaged, but not yet preserved on `main` as part of the docs-only normalization chain.
3. Root stash state remains preserved and intentionally untouched.

## Live Root Git Posture

- current branch: `main`
- current `HEAD`: `8b37bf0`
- upstream `origin/main`: `babb379`
- ahead/behind versus `origin/main`: `0 ahead`, `4 behind`
- root stashes: `4`

Current stash entries:

- `stash@{0}`: `codex-post-merge-pr45-closeout-isolation`
- `stash@{1}`: `codex-temp-root-lock-refresh`
- `stash@{2}`: `r21-pre-clean-regeneration`
- `stash@{3}`: `post-r20-normalization-bad-rerun`

## Replay Accounting Check

`replay/steps-cardio-prod-catchup` is now accounted for at the package level:

| Replay class | Count | Current handling |
| --- | ---: | --- |
| `archive_snapshot` | `4533` | Root preservation evidence; now covered by the archive retention receipt |
| `recovery_docs` | `98` | Root recovery dossier; preserved in package receipt |
| `recovery_captures` | `127` | Root recovery proof set; preserved in package receipt |
| `stack_docs` | `11` | Manual-review root doctrine subset; not yet adopted into normalized root |
| `stack_registry_contract` | `4` | Deferred stack contract subset; includes `stack.lock.yaml` and remains intentionally deferred |
| `repo_touches` | `13` | Separated into the Fitness owner-repo spillover package |

Package receipts now on record:

- `docs/recovery/ARCHIVE_RETENTION_RECEIPT_2026-05-22.md`
- `docs/recovery/REPLAY_STEPS_CARDIO_PRESERVATION_PACKAGE_2026-05-22.md`
- `docs/recovery/FITNESS_PROGRESSION_PLAYBOOK_SPILLOVER_PACKAGE_2026-05-22.md`

## Pull / Switch Collision Check

Results from the current root preflight:

- the three locally modified tracked docs are not touched by the four upstream `origin/main` commits
- the current untracked docs and recovery package notes do not exist on `origin/main`
- the current Git-visible `archive/**` entries do not collide with paths on `origin/main`

Interpretation:

- no direct path-overwrite collision was detected in the current preflight set
- the remaining blockers are preservation and normalization blockers, not immediate path collisions

## Blocking Items

| Item | Current state | Why it blocks direct reconcile | Recommended action |
| --- | --- | --- | --- |
| `README-STACK.md` | tracked modified | Docs-only local change is not yet preserved on `main` | Commit as docs-only normalization when ready |
| `docs/PLAYBOOK_NOTES.md` | tracked modified | Docs-only local change is not yet preserved on `main` | Commit as docs-only normalization when ready |
| `docs/ops/ATLAS-CODEX-CONTEXT-RUNBOOK.md` | tracked modified | Docs-only local change is not yet preserved on `main` | Commit as docs-only normalization when ready |
| `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md` | untracked | Active planning doc is not yet preserved on `main` | Commit as docs-only normalization when ready |
| `docs/ops/BRANCH-WORKTREE-NORMALIZATION-INVENTORY-2026-05-22.md` | untracked | Active preservation baseline is not yet preserved on `main` | Commit as docs-only normalization when ready |
| `docs/ops/BRANCH-WORKTREE-NORMALIZATION-ROUTING-2026-05-22.md` | untracked | Active routing plan is not yet preserved on `main` | Commit as docs-only normalization when ready |
| `docs/ops/STACK-LANE-0-BASELINE-INVENTORY-2026-05-22.md` | untracked | Lane 0 planning surface is not yet preserved on `main` | Commit as docs-only normalization when ready |
| `docs/ops/STACK-LANE-0-TRUTH-MAP-2026-05-22.md` | untracked | Lane 0 planning surface is not yet preserved on `main` | Commit as docs-only normalization when ready |
| `docs/recovery/REPLAY_STEPS_CARDIO_PRESERVATION_PACKAGE_2026-05-22.md` | untracked | Root preservation receipt is not yet preserved on `main` | Commit as docs-only normalization when ready |
| `docs/recovery/FITNESS_PROGRESSION_PLAYBOOK_SPILLOVER_PACKAGE_2026-05-22.md` | untracked | Fitness spillover receipt is not yet preserved on `main` | Commit as docs-only normalization when ready |
| `archive/**` | untracked preserved residue | Recovery archive payload is intentional, retained by receipt, and still should not be mixed into root normalization | Preserve in place; do not stage or delete during docs-only normalization |
| replay-touched root doctrine subset | packaged manual-review set | Root doctrine has been preserved, but not yet reviewed for normalized adoption | Manual review later; do not adopt from replay residue by default |
| root stashes | `4` preserved stashes | They are not a pull collision, but they remain active preservation artifacts that cannot be ignored | Preserve only; do not pop or drop |

## Untracked And Ignored Residue Snapshot

Current Git-visible untracked entries:

- `14` entries total
- `7` under `archive/**`
- `7` docs-only planning or recovery files

Current ignored residue footprint:

- `1534` ignored entries detected in the root view
- largest top-level ignored families include `tmp`, `data`, `runtime`, `repos`, `archive`, `ops`, and `packages`

Interpretation:

- ignored residue is large but expected in the ATLAS root posture
- ignored residue does not by itself block reconciliation
- the visible `archive/**` payload remains intentionally retained preserved residue and should stay out of the docs-only normalization commit

## Stash Preservation Status

Status: `preserved / untouched`

Assessment:

- the four ATLAS-root stashes remain valid preservation artifacts
- no stash needs to be popped, dropped, or merged for the preflight
- stash state is not the immediate reason reconciliation is blocked

## What Must Happen Before Reconcile Approval

1. Preserve the current docs-only normalization state on `main` with one intentional docs commit or equivalent preservation step.
2. Keep the archive retention receipt, replay package receipts, and replay branch as evidence rather than merge targets.
3. Keep the Fitness spillover package separate from root normalization.
4. Leave `stack.lock.yaml` deferred until after the root is actually reconciled with `origin/main`.

## Conditional Command Sequence Once Safe

Do not run this sequence yet. This is the exact next sequence once the blockers above are cleared.

```powershell
git add README-STACK.md `
  docs/PLAYBOOK_NOTES.md `
  docs/ops/ATLAS-CODEX-CONTEXT-RUNBOOK.md `
  docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md `
  docs/ops/BRANCH-WORKTREE-NORMALIZATION-INVENTORY-2026-05-22.md `
  docs/ops/BRANCH-WORKTREE-NORMALIZATION-ROUTING-2026-05-22.md `
  docs/ops/BRANCH-WORKTREE-ROOT-RECONCILIATION-PREFLIGHT-2026-05-22.md `
  docs/ops/STACK-LANE-0-BASELINE-INVENTORY-2026-05-22.md `
  docs/ops/STACK-LANE-0-TRUTH-MAP-2026-05-22.md `
  docs/recovery/ARCHIVE_RETENTION_RECEIPT_2026-05-22.md `
  docs/recovery/REPLAY_STEPS_CARDIO_PRESERVATION_PACKAGE_2026-05-22.md `
  docs/recovery/FITNESS_PROGRESSION_PLAYBOOK_SPILLOVER_PACKAGE_2026-05-22.md
git commit -m "docs: record branch worktree normalization package"
git pull --ff-only origin main
python ops/validation/validate_stack.py --allow-missing-locked-repos
```

Lock repair remains outside this sequence:

- only after the root is reconciled should `stack.lock.yaml` be regenerated

## Outcome

The root is closer to safe reconciliation than before:

- replay residue is fully split into root preservation versus Fitness owner-repo spillover
- no direct untracked-path collision with `origin/main` was detected
- no upstream overlap was detected in the three locally modified tracked docs

But the root is not yet approved for reconcile because:

- docs-only normalization state is still uncommitted
- replay-touched doctrine remains preserved rather than normalized
- archive retention is now documented, but remains intentionally untracked preserved residue

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
- Branch & Worktree Normalization: `50%`
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
