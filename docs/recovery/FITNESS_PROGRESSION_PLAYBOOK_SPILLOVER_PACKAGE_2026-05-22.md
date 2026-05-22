# Fitness Progression Playbook Spillover Package

Date: 2026-05-22
Package: Fitness spillover package
Mode: Routing and package planning only
Status: Owner-repo spillover package recorded; not yet applied

## Purpose

This note records the Fitness-owner spillover slice from `replay/steps-cardio-prod-catchup`.

It exists to separate owner-repo product files from ATLAS-root preservation evidence before root reconciliation work resumes.

## Source Branch

- source branch: `replay/steps-cardio-prod-catchup`
- comparison baseline: `origin/main`
- branch posture on 2026-05-22: preserved evidence, not normalized history

## Package Boundary

Included:

- the 13 progression-playbook files under `repos/fawxzzy-fitness/**`

Excluded:

- archive snapshot evidence
- recovery docs
- recovery captures
- replay-touched root doctrine
- stack registry and contract files
- `stack.lock.yaml` regeneration
- any direct file application into the Fitness repo

## Current Surface Check

All 13 spillover paths exist in the replay branch tree.

Current checked-out Fitness repo posture:

- none of the 13 spillover paths currently exist on the checked-out `repos/fawxzzy-fitness` surface
- the Fitness repo does already contain adjacent progression infrastructure under `src/lib/**`, `src/components/**`, `scripts/qa/**`, `tests/**`, and progression-related migrations

Interpretation:

- this is a real owner-repo handoff slice, not a root-side duplicate
- it should be reviewed as an additive or renamed-path feature family against current Fitness progression surfaces

## File Classification Table

| File | Classification | Recommended owner destination | Verification needed before applying |
| --- | --- | --- | --- |
| `repos/fawxzzy-fitness/src/components/routines/ProgressionPlaybookEditor.tsx` | source code | Fitness repo source | Confirm target UI surface still belongs under `src/components/routines/**`; compare against current progression UI components; verify no renamed replacement already exists |
| `repos/fawxzzy-fitness/src/lib/progression-playbook-form-state.ts` | source code | Fitness repo source | Review current progression state architecture; confirm form-state contract still fits current feature model |
| `repos/fawxzzy-fitness/src/lib/progression-playbook-form-state.test.ts` | test | Fitness repo source | Pair with source-file review; confirm test harness and assertions still match current repo conventions |
| `repos/fawxzzy-fitness/src/lib/progression-playbook-ui-options.ts` | source code | Fitness repo source | Compare with current progression option and preset surfaces to avoid duplicate config logic |
| `repos/fawxzzy-fitness/src/lib/progression-playbook-ui-options.test.ts` | test | Fitness repo source | Confirm test expectations still map to live option semantics |
| `repos/fawxzzy-fitness/src/lib/progression-playbooks.ts` | source code | Fitness repo source | Review naming overlap with current progression schema, events, and migrations; confirm storage contract before adoption |
| `repos/fawxzzy-fitness/src/lib/progression-playbooks.test.ts` | test | Fitness repo source | Confirm test coverage aligns with current schema and persistence assumptions |
| `repos/fawxzzy-fitness/src/lib/progression-qualification-window.ts` | source code | Fitness repo source | Compare against current qualification/review logic to avoid duplicated domain rules |
| `repos/fawxzzy-fitness/src/lib/progression-qualification-window.test.ts` | test | Fitness repo source | Confirm expected qualification behavior still matches current product rules |
| `repos/fawxzzy-fitness/src/lib/progression-status-display.ts` | source code | Fitness repo source | Compare with current status and review display helpers to prevent parallel display layers |
| `repos/fawxzzy-fitness/src/lib/progression-status-display.test.ts` | test | Fitness repo source | Verify display expectations still align with current UI and terminology |
| `repos/fawxzzy-fitness/src/lib/progression-target-mutation.ts` | source code | Fitness repo source | Review against current target-update and promotion logic to avoid conflicting mutation paths |
| `repos/fawxzzy-fitness/src/lib/progression-target-mutation.test.ts` | test | Fitness repo source | Confirm mutation invariants still match current progression and database rules |

## Classification Summary

- source code: `7`
- test: `6`
- docs: `0`
- generated artifact: `0`
- recovery or proof artifact: `0`
- unknown: `0`

## Destination Decision

Package-level destination:

- primary owner: Fitness repo
- primary destination class: Fitness repo source
- secondary posture: manual review before any application

Reasons:

1. Every file sits under repo-owned `src/**`.
2. None of the files are root doctrine, recovery dossier material, or archive evidence.
3. The current Fitness repo already has adjacent progression infrastructure, so these files need owner-repo integration review rather than root preservation handling.
4. The paths do not exist on the checked-out repo surface, which increases the need for manual review before apply.

## Verification Needed Before Applying

Before any file move, cherry-pick, or patch into the Fitness repo:

1. Compare these 13 paths against current Fitness progression surfaces to detect renamed or superseding modules.
2. Review whether the feature belongs as:
   - one additive UI/editor slice
   - one additive domain-logic slice
   - one additive test slice
3. Confirm whether current Fitness schema and migrations still support the replay branch assumptions behind `progression-playbooks` and target mutation behavior.
4. Decide whether this package should land as:
   - one Fitness replay branch
   - multiple repo-local commits
   - a parked evidence branch for later extraction
5. Run repo-local verification only after the package is actually applied in the Fitness repo.

## Non-Goals

This package does not:

- apply files into `repos/fawxzzy-fitness`
- regenerate `stack.lock.yaml`
- reconcile the ATLAS root with `origin/main`
- merge or delete `replay/steps-cardio-prod-catchup`
- classify root-owned recovery evidence again

## Relationship To Other Preservation Records

This package depends on:

- `docs/ops/BRANCH-WORKTREE-NORMALIZATION-INVENTORY-2026-05-22.md`
- `docs/ops/BRANCH-WORKTREE-NORMALIZATION-ROUTING-2026-05-22.md`
- `docs/recovery/REPLAY_STEPS_CARDIO_PRESERVATION_PACKAGE_2026-05-22.md`
- `tmp/scratch/replay-steps-cardio-classification-2026-05-22.json`

The replay classification JSON above is a local scout artifact. The durable owner-route and file classification are recorded in this receipt.

This package complements:

- the ATLAS-root preservation package for archive/recovery/doctrine/registry evidence

## Outcome

The replay branch now has both package boundaries documented:

- ATLAS root preservation package
- Fitness owner-repo spillover package

That makes the next root-reconciliation step safer because replay residue is now separated into root-owned evidence versus owner-repo source handoff.

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
