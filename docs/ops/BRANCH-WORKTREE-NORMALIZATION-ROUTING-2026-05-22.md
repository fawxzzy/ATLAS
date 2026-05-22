# Branch & Worktree Normalization Routing

Date: 2026-05-22
Mode: Routing plan only
Status: Preserved replay branch classified into actionable routing packages

## Purpose

This report converts the `replay/steps-cardio-prod-catchup` classification into a routing plan.

It does not move files, merge branches, regenerate `stack.lock.yaml`, or normalize the ATLAS root.

## Guardrails

Do not:

- regenerate `stack.lock.yaml`
- delete replay or recovery branches
- move raw archive payloads
- move Fitness owner-repo files from the replay branch
- start Fitness product implementation work
- run broad cleanup
- treat the replay branch as a merge candidate

## Source Inputs

- `docs/ops/BRANCH-WORKTREE-NORMALIZATION-INVENTORY-2026-05-22.md`
- `tmp/scratch/replay-steps-cardio-classification-2026-05-22.json`

The replay classification JSON is a local scout artifact only. Durable routing truth is captured in this plan and the linked package receipts.

## Package Decision Summary

Two top-level routing packages now exist:

1. Root-owned preservation package
2. Fitness owner-repo spillover package

Current package receipt:

- `docs/recovery/ARCHIVE_RETENTION_RECEIPT_2026-05-22.md`
- `docs/recovery/REPLAY_STEPS_CARDIO_PRESERVATION_PACKAGE_2026-05-22.md`
- `docs/recovery/FITNESS_PROGRESSION_PLAYBOOK_SPILLOVER_PACKAGE_2026-05-22.md`
- `docs/ops/BRANCH-WORKTREE-ROOT-RECONCILIATION-PREFLIGHT-2026-05-22.md`

The root-owned preservation package is still split internally because it contains two different lifecycles:

- preserved recovery evidence that should stay grouped as recovery/archive material
- root doctrine and stack contract surfaces that need review against normalized root state before any adoption

## Routing Table

| Path or pattern | Count | Owner | Reason | Target location | Verification needed | Safe action |
| --- | ---: | --- | --- | --- | --- | --- |
| `archive/**` | `4533` | ATLAS root | Preserved recovery snapshot payload; dominant evidence surface from replay branch | Keep under ATLAS root preservation ownership; later package as archive evidence manifest, not live doctrine | Archive manifest, size/content receipt, retention classification | Archive as recovery evidence |
| `docs/recovery/**/*.md` | `98` | ATLAS root | Recovery dossier documenting Fitness source-of-truth reset, governance, branch cleanup, and save points | Keep under ATLAS root as recovery dossier | Recovery index review, cross-link audit, duplicate check against live doctrine | Keep in ATLAS root |
| `docs/recovery/captures/**` | `127` | ATLAS root | Proof captures and verification receipts tied to recovery and certification work | Keep under ATLAS root evidence surfaces | Capture manifest, spot-check that referenced docs still resolve | Keep in ATLAS root |
| `README-STACK.md` | `1` | ATLAS root | Root operating doctrine, not owner-repo product work | Keep in ATLAS root only if replay content is still desired after root reconciliation | Diff review against current `main` and `origin/main` posture | Mark manual review |
| `docs/PLAYBOOK_NOTES.md` | `1` | ATLAS root | Stack-wide doctrine and convergence notes | Keep in ATLAS root only if replay content is still desired after root reconciliation | Diff review against current planning posture | Mark manual review |
| `docs/atlas/notes/cortex-admission-planning-2026-05-21.md` | `1` | ATLAS root | ATLAS planning note, not Fitness runtime ownership | Keep in ATLAS root planning surfaces | Planning-note dedupe review | Keep in ATLAS root |
| `docs/ops/ATLAS-DISCORD-OS.md` | `1` | ATLAS root | Root operator doctrine for Discord OS | Keep in ATLAS root doctrine set | Replay-vs-current diff review | Mark manual review |
| `docs/ops/FITNESS_QA_LLEL_WORKFLOW.md` | `1` | ATLAS root | Root projection doc for Fitness QA/LLEL workflow | Keep in ATLAS root doctrine set | Compare against current Fitness workflow truth | Mark manual review |
| `docs/ops/FITNESS_WORKFLOW.md` | `1` | ATLAS root | Root projection doc for Fitness operating workflow | Keep in ATLAS root doctrine set | Compare against current Fitness workflow truth | Mark manual review |
| `docs/ops/STACK-LANE-0-BASELINE-INVENTORY-2026-05-22.md` | `1` | ATLAS root | Lane 0 inventory planning doc | Keep in ATLAS root planning surfaces | Confirm replay content is superseded by current reduced-marker version | Mark manual review |
| `docs/ops/STACK-LANE-0-TRUTH-MAP-2026-05-22.md` | `1` | ATLAS root | Lane 0 truth-map planning doc | Keep in ATLAS root planning surfaces | Confirm replay content is superseded by current reduced-marker version | Mark manual review |
| `docs/ops/STACK-PROGRESSION-CHECKPOINT-2026-05-20.md` | `1` | ATLAS root | Historical stack checkpoint note | Keep in ATLAS root checkpoint history | Historical doc review only | Keep in ATLAS root |
| `docs/playbooks/PLAYBOOK-CATALOG.md` | `1` | ATLAS root | Catalog/projection surface that may overlap with Playbook repo doctrine | Keep in ATLAS root only if still needed as stack projection | Ownership review against Playbook repo | Mark manual review |
| `docs/playbooks/discord-fitness-verification-ops.md` | `1` | ATLAS root | Stack-level workflow/operator playbook surface | Keep in ATLAS root if still part of cross-repo operator doctrine | Projection-vs-owner review | Mark manual review |
| `docs/audits/STACK-REPO-INVENTORY.md` | `1` | ATLAS root | Stack registry audit surface tied to root reconciliation | Leave in deferred stack-registry set until root normalization | Compare with current repo inventory and normalized root state | Mark manual review |
| `docs/registry/STACK-REPO-INVENTORY.json` | `1` | ATLAS root | Machine-readable registry contract tied to root reconciliation | Leave in deferred stack-registry set until root normalization | Registry regeneration decision after root reconciliation | Mark manual review |
| `stack.yaml` | `1` | ATLAS root | Stack contract surface; should follow normalized root, not replay branch residue | Leave in deferred stack-registry set | Stack contract diff review after root reconciliation | Mark manual review |
| `stack.lock.yaml` | `1` | ATLAS root | Lock contract currently known to be in intentional drift posture | Leave deferred until root reconciles with `origin/main` | Regenerate only after normalized root and preservation routing are complete | Mark manual review |
| `repos/fawxzzy-fitness/src/components/routines/ProgressionPlaybookEditor.tsx` | `1` | Fitness repo | Owner-repo UI slice, not root truth | Route decision into Fitness repo preservation package | Fitness repo diff review, feature-scope confirmation, test intent review | Route to Fitness repo |
| `repos/fawxzzy-fitness/src/lib/progression-playbook-form-state.test.ts` | `1` | Fitness repo | Owner-repo test slice tied to progression-playbook behavior | Route decision into Fitness repo preservation package | Fitness repo test ownership review | Route to Fitness repo |
| `repos/fawxzzy-fitness/src/lib/progression-playbook-form-state.ts` | `1` | Fitness repo | Owner-repo logic slice | Route decision into Fitness repo preservation package | Fitness repo feature ownership review | Route to Fitness repo |
| `repos/fawxzzy-fitness/src/lib/progression-playbook-ui-options.test.ts` | `1` | Fitness repo | Owner-repo test slice | Route decision into Fitness repo preservation package | Fitness repo test ownership review | Route to Fitness repo |
| `repos/fawxzzy-fitness/src/lib/progression-playbook-ui-options.ts` | `1` | Fitness repo | Owner-repo logic slice | Route decision into Fitness repo preservation package | Fitness repo feature ownership review | Route to Fitness repo |
| `repos/fawxzzy-fitness/src/lib/progression-playbooks.test.ts` | `1` | Fitness repo | Owner-repo test slice | Route decision into Fitness repo preservation package | Fitness repo test ownership review | Route to Fitness repo |
| `repos/fawxzzy-fitness/src/lib/progression-playbooks.ts` | `1` | Fitness repo | Owner-repo logic slice | Route decision into Fitness repo preservation package | Fitness repo feature ownership review | Route to Fitness repo |
| `repos/fawxzzy-fitness/src/lib/progression-qualification-window.test.ts` | `1` | Fitness repo | Owner-repo test slice | Route decision into Fitness repo preservation package | Fitness repo test ownership review | Route to Fitness repo |
| `repos/fawxzzy-fitness/src/lib/progression-qualification-window.ts` | `1` | Fitness repo | Owner-repo logic slice | Route decision into Fitness repo preservation package | Fitness repo feature ownership review | Route to Fitness repo |
| `repos/fawxzzy-fitness/src/lib/progression-status-display.test.ts` | `1` | Fitness repo | Owner-repo test slice | Route decision into Fitness repo preservation package | Fitness repo test ownership review | Route to Fitness repo |
| `repos/fawxzzy-fitness/src/lib/progression-status-display.ts` | `1` | Fitness repo | Owner-repo logic slice | Route decision into Fitness repo preservation package | Fitness repo feature ownership review | Route to Fitness repo |
| `repos/fawxzzy-fitness/src/lib/progression-target-mutation.test.ts` | `1` | Fitness repo | Owner-repo test slice | Route decision into Fitness repo preservation package | Fitness repo test ownership review | Route to Fitness repo |
| `repos/fawxzzy-fitness/src/lib/progression-target-mutation.ts` | `1` | Fitness repo | Owner-repo logic slice | Route decision into Fitness repo preservation package | Fitness repo feature ownership review | Route to Fitness repo |

## Package Rules

### Root-owned preservation package

Keep under ATLAS root ownership:

- `archive/**`
- `docs/recovery/**`
- `docs/recovery/captures/**`
- historical stack checkpoint notes that function as evidence rather than live implementation

Manual-review root doctrine subset:

- `README-STACK.md`
- `docs/PLAYBOOK_NOTES.md`
- `docs/ops/**` replay-touched workflow docs
- `docs/playbooks/**` replay-touched projection docs
- `docs/atlas/notes/**` replay-touched planning notes

Deferred stack-registry subset:

- `docs/audits/STACK-REPO-INVENTORY.md`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `stack.yaml`
- `stack.lock.yaml`

Interpretation:

- recovery evidence stays root-owned
- root doctrine survives only after replay-vs-current review
- stack-registry surfaces must wait for root normalization and should not be adopted from replay residue

### Fitness owner-repo spillover package

Route to Fitness-owner review:

- the 13 `repos/fawxzzy-fitness` progression-playbook files

Interpretation:

- these are owner-repo product files and cannot be normalized as ATLAS root truth
- they should become a separate Fitness preservation or replay package
- the routing decision is about ownership first, not immediate mergeability

Recommended package framing:

1. progression-playbook UI slice
2. progression-playbook logic slice
3. progression-playbook tests

That split preserves one conceptual feature family without forcing a single root replay branch to act as the delivery vehicle.

Current package receipt:

- `docs/recovery/FITNESS_PROGRESSION_PLAYBOOK_SPILLOVER_PACKAGE_2026-05-22.md`

## Root Reconciliation Prerequisites

The ATLAS root should not reconcile with `origin/main` until all of the following are explicit:

1. The replay branch remains preserved as evidence and is not used as the normalization target.
2. `archive/**` has a preservation manifest and retention posture.
3. `docs/recovery/**` and `docs/recovery/captures/**` are accepted as root-owned recovery dossier material.
4. Replay-touched root doctrine files are reviewed against current `main` so root does not re-import stale replay wording.
5. The 13 Fitness spillover files are routed into a Fitness-owner preservation decision.
6. `stack.yaml`, `stack.lock.yaml`, and stack-registry files remain deferred until root is reconciled with `origin/main`.
7. Only after the root is reconciled should `stack.lock.yaml` be regenerated and validation re-run as lock repair.

Current preflight result:

- `archive/**` is now covered by a retention receipt
- direct reconcile is still not approved because the docs-only normalization state is still uncommitted

## Recommended Safe Actions By Package

| Package | Immediate action | Later action |
| --- | --- | --- |
| Root archive snapshot payload | Preserve and manifest only | Later archive/package and possible generated-residue filtering |
| Root recovery dossier | Preserve and cross-link only | Later fold selected rules into convergence doctrine if still canonical |
| Replay-touched root doctrine | Manual review only | Later adopt, supersede, or archive per-file after root reconciliation |
| Replay-touched stack registry / contracts | Defer | Later regenerate from normalized root state |
| Fitness progression-playbook spillover | Route to Fitness-owner preservation package | Later split into Fitness repo commits or parked owner-repo evidence after repo-local review |

## Next Packaging Prompt

```text
At the ATLAS root, continue Branch & Worktree Normalization in preservation-routing mode.

Goal:
Turn the replay routing plan into preservation manifests and owner-package handoff inputs.

Do:
- create a manifest for archive/** replay payload ownership
- create a recovery dossier index for docs/recovery/** and docs/recovery/captures/**
- create a Fitness spillover handoff note for the 13 progression-playbook files
- keep stack-registry and lock surfaces deferred

Do not:
- regenerate stack.lock.yaml
- merge replay/steps-cardio-prod-catchup
- move Fitness files
- delete branches
- run broad cleanup
```

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
