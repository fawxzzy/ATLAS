# Archive Retention Receipt

Date: 2026-05-22
Mode: Docs-only retention receipt
Status: `archive/**` is intentionally retained; no archive files moved, deleted, or staged

## Purpose

This receipt records why the current `archive/**` surface remains intentionally present in the ATLAS root during Branch & Worktree Normalization.

It converts `archive/**` from unknown residue into named retained preservation material.

## Scope

Current archive root:

- `archive/`

Current top-level archive family:

- `archive/fitness-source-reset`

Measured archive footprint on 2026-05-22:

- approximate file count: `43900`
- approximate directory count: `5297`
- approximate size: `2.04 GB`

## High-Level Inventory

`archive/fitness-source-reset` currently contains two dated preservation batches:

| Path | Approx. files | Purpose | Owner | Class |
| --- | ---: | --- | --- | --- |
| `archive/fitness-source-reset/20260522-005503` | `21727` | Preserved inherited ATLAS-root Fitness surface captured before source-of-truth normalization | ATLAS root | evidence snapshot plus generated residue |
| `archive/fitness-source-reset/20260522-final-cleanup` | `22173` | Preserved final-cleanup and replay-adjacent checkpoint surfaces captured during Fitness recovery closeout | ATLAS root | evidence snapshot, manual-review material, and generated residue |

Known inner preserved surfaces:

| Path | Approx. files | Purpose | Owner | Class |
| --- | ---: | --- | --- | --- |
| `archive/fitness-source-reset/20260522-005503/fawxzzy-fitness-atlas-inherited` | `21727` | Snapshot of inherited Fitness-at-ATLAS-root state before reset | ATLAS root | evidence snapshot |
| `archive/fitness-source-reset/20260522-final-cleanup/fawxzzy-fitness-real` | `21649` | Snapshot of the real Fitness repo surface preserved during final cleanup | ATLAS root | evidence snapshot and manual-review material |
| `archive/fitness-source-reset/20260522-final-cleanup/fitness-feedback-completion-review-workflow` | `510` | Preserved workflow lane residue tied to feedback/completion review closeout | ATLAS root | manual-review material plus generated residue |
| `archive/fitness-source-reset/20260522-final-cleanup/fitness-pr61-merge` | `14` | Small preserved merge/checkpoint residue | ATLAS root | manual-review material |

Visible retained substructure indicates:

- snapshot surfaces with `src`, `docs`, `scripts`, `supabase`, `tests`, and `truth-pack`
- generated and mutable residue such as `.next`, `node_modules`, `.playbook`, `.vercel`, logs, and local env files
- recovery-oriented snapshot folders such as `recovery-snapshots`

## What `archive/**` Represents

`archive/**` represents:

1. Preserved evidence from the Fitness source-of-truth reset and final cleanup sequence.
2. Snapshot material that allows later review of inherited root state versus real repo state.
3. Recovery-era checkpoint residue that should remain inspectable until final normalization decisions are complete.
4. A preservation surface for generated and mixed residue that should not be mistaken for live source.

## What `archive/**` Does Not Represent

`archive/**` does not represent:

1. Current owner-repo source truth.
2. A merge target for ATLAS root normalization.
3. A clean package ready for promotion back into live stack contracts.
4. A signal that generated residue should be restored into repos.

## Ownership And Truth Boundary

Owner:

- ATLAS root preservation layer

Truth boundary:

- `archive/**` is preserved evidence
- it is not Fitness repo source truth
- it is not `_stack` runtime truth
- it is not stack-registry truth

Why it is not owner-repo source truth:

1. It mixes snapshots, generated outputs, local env residue, logs, and preserved checkpoints.
2. It contains captured historical surfaces from both inherited root state and cleanup-era branches.
3. It exists to preserve context for recovery and normalization review, not to replace repo-local ownership.

## Why It Is Intentionally Retained For Now

`archive/**` is intentionally retained because:

1. The root reconciliation program still depends on recovery traceability.
2. The replay branch and preservation packages reference archive-backed evidence.
3. Final cleanup has not yet classified which retained material can be dropped as generated residue versus parked as historical evidence.
4. Deleting it now would break the preservation-first rule that governed replay branch classification.

## Why It Must Not Be Deleted Before Final Cleanup

Do not delete `archive/**` before final cleanup because:

1. It still contains the preserved trail of the Fitness source-of-truth reset.
2. It still holds the inherited-root snapshot needed to explain why root cleanup was deferred.
3. It still contains mixed evidence and generated residue that has not yet been split into keep-versus-drop decisions.
4. Removing it before final review would reintroduce the exact loss-risk that Branch & Worktree Normalization was created to avoid.

## Future Cleanup Decision Required

A later cleanup lane must decide, for each retained archive class:

- keep as long-term historical evidence
- compress or park as archive-only preservation
- drop as generated residue after preservation review
- extract a smaller manifest or receipt and then remove bulky disposable copies

That decision belongs to:

- later Branch & Worktree Normalization closeout
- or Full Stack Re-sync, Clean & Closeout after root normalization is complete

## Relationship To Root Reconciliation

This receipt clears the “unknown archive residue” blocker, but it does not itself approve root reconciliation.

After this receipt:

- `archive/**` is named retained preservation material rather than unknown residue
- the remaining reconcile blocker is primarily the uncommitted docs-only normalization state
- `stack.lock.yaml` still remains deferred until root is reconciled with `origin/main`

## Lockfile Deferral

`stack.lock.yaml` remains deferred because:

1. Archive retention is now documented, but root normalization has not yet occurred.
2. The root is still behind `origin/main`.
3. Stack contract files must follow normalized root state, not transitional preservation posture.

Do not regenerate `stack.lock.yaml` from this lane.

## Related Records

This receipt works with:

- `docs/ops/BRANCH-WORKTREE-NORMALIZATION-INVENTORY-2026-05-22.md`
- `docs/ops/BRANCH-WORKTREE-NORMALIZATION-ROUTING-2026-05-22.md`
- `docs/ops/BRANCH-WORKTREE-ROOT-RECONCILIATION-PREFLIGHT-2026-05-22.md`
- `docs/recovery/REPLAY_STEPS_CARDIO_PRESERVATION_PACKAGE_2026-05-22.md`
- `docs/recovery/FITNESS_PROGRESSION_PLAYBOOK_SPILLOVER_PACKAGE_2026-05-22.md`

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
