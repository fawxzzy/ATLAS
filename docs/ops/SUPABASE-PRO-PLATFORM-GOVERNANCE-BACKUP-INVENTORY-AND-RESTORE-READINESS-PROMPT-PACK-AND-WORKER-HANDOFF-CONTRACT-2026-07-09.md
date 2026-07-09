# Supabase Pro Platform Governance backup inventory and restore-readiness prompt-pack and worker handoff contract

- Date: `2026-07-09`
- Lane: `Supabase Pro Platform Governance`
- Mode: `ATLAS-root docs-only prompt-pack freeze`
- Marker movement: none

## Result

The backup inventory and restore-readiness worker handoff contract is frozen.

This remains a docs-only packet. It does not implement the helper, call Supabase, list backups, restore projects, enable PITR, or move any marker.

## Worker Objective

Implement one bounded, read-only ATLAS-root helper that classifies the known Supabase project set into the frozen backup and restore posture classes using committed root-owned governance inputs only.

The worker must create:

- `ops/atlas/supabase_backup_restore_posture.py`
- `tests/test_atlas_supabase_backup_restore_posture.py`

Primary command:

```powershell
python ops\atlas\supabase_backup_restore_posture.py --json
```

Optional safe output command:

```powershell
python ops\atlas\supabase_backup_restore_posture.py --json --output tmp/atlas/supabase-backup-restore-posture.latest.json
```

## Required Behavior

The helper must:

- emit deterministic JSON
- read only committed ATLAS-root governance inputs
- classify `FawxzzyFitness`, `DiscordOS`, and `Mazer` as the only confirmed project-bound surfaces
- classify `Nat1-Games` as dependency-only with `no_project_identity`
- preserve `daily_backup_covered` plus `daily_backup_unverified` coexistence where the platform entitlement is expected but project-specific backup inventory proof is still missing
- preserve `restore_process_unverified` until a later packet proves more
- preserve `pitr_candidate` only for `FawxzzyFitness` and `DiscordOS`
- preserve `pitr_not_approved`, `manual_dump_plan_needed`, `storage_restore_gap`, `custom_role_password_gap`, and `operator_decision_required` where the contract freeze requires them
- fail closed on missing or contradictory root inputs
- emit no secret values
- write only to explicit root-relative `tmp/**.json` output paths when `--output` is supplied

## Required Output Schema

The helper must emit:

```json
{
  "schema_version": "atlas.supabase_backup_restore_posture.v1",
  "status": "ok",
  "safe_to_use": true,
  "basis_receipts": [],
  "project_count": 0,
  "projects": [],
  "dependency_only_surfaces": [],
  "missing_evidence": [],
  "operator_decisions_required": [],
  "blockers": [],
  "warnings": []
}
```

Allowed `status` values:

- `ok`
- `blocker`
- `internal_error`

## Project Record Shape

Each confirmed project record must include:

- `project_name`
- `project_ref`
- `posture_classes`
- `pitr_candidate`
- `restore_readiness`
- `backup_inventory_status`
- `storage_restore_gap`
- `custom_role_password_gap`
- `notes`

## Dependency-Only Record Shape

Each dependency-only surface record must include:

- `surface_name`
- `posture_classes`
- `notes`

## Admitted Inputs

The worker may read only:

- `docs/ops/SUPABASE-PRO-PLATFORM-CAPABILITY-ADOPTION-AUDIT-2026-07-09.md`
- `docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-AND-RESTORE-POSTURE-CONTRACT-FREEZE-2026-07-09.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/registry/STACK-REPO-INVENTORY.json`

The first implementation must not read:

- owner-repo working trees
- Supabase APIs or mutable connector surfaces
- secrets, `.env*`, `.vercel/**`, `.playwright-mcp/**`, `archive/**`
- hidden transcripts or session state
- uncommitted diffs
- deploy or workflow surfaces

## Proof Obligations

The test suite must cover:

- deterministic top-level output ordering
- deterministic confirmed-project ordering
- correct posture classification for `FawxzzyFitness`, `DiscordOS`, and `Mazer`
- `Nat1-Games` dependency-only handling with `no_project_identity`
- preservation of `daily_backup_covered` plus `daily_backup_unverified`
- preservation of `pitr_candidate` only for `FawxzzyFitness` and `DiscordOS`
- preservation of `storage_restore_gap` and `custom_role_password_gap`
- fail-closed behavior for missing required receipts
- fail-closed behavior for malformed stack inventory inputs
- safe `tmp/**.json` output path handling if output writing is implemented
- rejection of protected output paths
- no marker movement or platform mutation authority appears in output

## Allowed Touch Surface For Implementation

Only these implementation surfaces are admitted by the eventual worker packet:

- `ops/atlas/supabase_backup_restore_posture.py`
- `tests/test_atlas_supabase_backup_restore_posture.py`

Worker reconciliation may also add one bounded reconciliation receipt and exact Book/restart/receipt-index mirrors after proof passes.

## Forbidden Surfaces

The worker and implementation packet must not touch:

- `repos/**`
- Fitness owner repo files
- Mazer owner repo files
- any owner repo files
- `secrets/**`
- `.env*`
- `.vercel/**`
- `.playwright-mcp/**`
- `archive/**`
- `.github/workflows/**`
- live Supabase platform state
- broad untracked backlog

## Forbidden Authority

The worker must not:

- mutate Supabase settings
- restore projects
- enable PITR
- create branches
- stage, commit, or push
- mutate owner repos
- touch Fitness or Mazer owner-lane work
- touch secrets
- deploy
- dispatch workflows
- emit final receipts
- move markers
- infer restore readiness from plan entitlement alone

## Stop Conditions

The worker must stop or emit `blocker` / `internal_error` without fabricating posture if:

- root validation has `critical` or `error`
- required root-owned receipts or inventory inputs are missing or malformed
- the worker would need live secret-bearing API access
- the worker would need owner-repo mutation, deploy, workflow, or protected-surface authority
- the worker would need to invent project identity or backup metadata that is not present in admitted root inputs

## Marker Decision

No marker moves from this prompt-pack.

No Supabase marker is opened.

## Exact Next Packet

```text
Supabase Pro Platform Governance backup inventory and restore-readiness implementation-readiness closeout and worker routing
```

That packet should confirm no docs-only prerequisite remains before the bounded helper implementation worker.
