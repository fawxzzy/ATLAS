# Playbook Everywhere + Cortex Interface Foundation Owner-Lane Playbook Adoption Proof Prompt-Pack And Worker Handoff Contract

- CODEX-MSG-ID: `CODEX-2026-07-07-PLAYBOOK-CORTEX-FOUNDATION-OWNER-LANE-ADOPTION-PROOF-PROMPT-PACK-AND-WORKER-HANDOFF`
- Date: `2026-07-07`
- Mode: `docs-only prompt-pack and worker handoff contract`
- Scope: `freeze one bounded worker handoff for Foundation owner-lane Playbook adoption proof`
- Branch basis: `main@d4e23949`
- Admission basis: `docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-FOUNDATION-OWNER-LANE-PLAYBOOK-ADOPTION-PROOF-FIRST-IMPLEMENTATION-ADMISSION-2026-07-07.md`
- Selected owner-lane target: `foundation`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`

## Worker Objective

Run one bounded proof worker that reconciles the admitted Foundation owner-lane Playbook adoption proof slice.

The worker must prove the existing root-owned Playbook adoption matrix can classify Foundation in owner scope while preserving owner-lane separation, no owner mutation, no marker inflation, and advisory-only Cortex authority.

## Required Commands

The worker must run:

```powershell
python ops\atlas\playbook_adoption_matrix.py --json --scope owner --owner foundation
git -C repos\foundation status -sb
git -C repos\foundation log -1 --oneline --decorate
python -m unittest tests.test_atlas_playbook_adoption_matrix -v
python ops\validation\validate_stack.py
python ops\atlas\continuity_manifest_health.py
python ops\atlas\continuity_open_marker_restart_index.py
```

The worker may also run:

```powershell
python ops\atlas\marker_knockout_selector.py --format json
python ops\atlas\ai_work_session_closeout.py --json --scope root
```

## Required Proof Fields

The reconciliation receipt must record:

- owner: `foundation`
- owner status command result
- owner latest commit line
- matrix `status`
- matrix owner row `classification`
- matrix owner row `read_only`
- matrix owner row `root_owned_proof`
- matrix warnings and blockers
- whether Fitness was touched
- whether Mazer was touched
- stack validation summary
- marker decision
- exact next packet

## Expected Current Proof Posture

The current expected proof posture is:

- matrix status: `advisory_gap`
- Foundation classification: `missing_adoption`
- Foundation `root_owned_proof`: `false`
- owner-scope warning: `owner_scope_read_only`
- Foundation status: clean on `main`
- marker movement: none

If the live proof differs, the worker must report the live truth and must not force this expected posture.

## Allowed Files

The worker may create or update only:

- one reconciliation receipt under `docs/ops/**`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/memory/initiatives/continuity-manifest-playbook-everywhere-cortex-interface.json`

## Forbidden Files And Actions

The worker must not:

- write under `repos/**`
- stage or commit owner repos
- switch Foundation branches
- read broad Foundation source files
- touch Fitness
- touch Mazer
- mutate Playbook owner repo
- touch Supabase
- touch Vercel
- deploy
- touch secrets or `.env*`
- write `.vercel/**`
- write `.playwright-mcp/**`
- write `archive/**`
- claim release readiness
- claim Foundation owner truth
- grant Cortex execution, approval, dispatch, owner-truth, final-receipt, deploy, secret, repo-mutation, or platform authority

## Stop Conditions

Stop without committing if:

- stack validation has `critical` or `error`
- Foundation has dirty worktree state
- Foundation is not on the expected clean branch and the branch posture is not already represented by stack inventory
- the matrix command fails unexpectedly
- Fitness or Mazer would need to be touched
- owner repo mutation is required
- marker movement cannot be justified by receipt-backed implementation proof
- protected surfaces would be touched

## Marker Decision

No marker moves from this prompt-pack.

`Playbook Everywhere + Cortex Interface` remains `40%`.

Reason: this packet freezes a worker handoff but does not run or reconcile the proof worker.

## Exact Next Packet

Next exact packet:

`Playbook Everywhere + Cortex Interface foundation owner-lane Playbook adoption proof implementation-readiness closeout and worker routing`

That packet should decide whether any root-only prerequisite remains before one bounded proof worker runs.

