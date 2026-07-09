# Supabase Pro Platform Governance backup inventory and restore-readiness first-implementation admission

- Date: `2026-07-09`
- Lane: `Supabase Pro Platform Governance`
- Mode: `ATLAS-root docs-only first-implementation admission`
- Control-plane checkpoint: `d2c3303c2f24b017e6d04af24cda95b9ce2b017c`
- Marker movement: none

## Decision

Admit one future read-only helper/test pair for Supabase backup posture inventory and restore-readiness classification.

The next exact packet is:

```text
Supabase Pro Platform Governance backup inventory and restore-readiness prompt-pack and worker handoff contract
```

This admission does not implement the helper, call Supabase, list backups, restore databases, enable PITR, or move any marker.

## Objective

Freeze the smallest honest first implementation slice that can turn the July 9 audit and contract-freeze truth into deterministic posture output.

The first implementation is advisory only. It must classify current root-known Supabase project posture and report what is still missing before any restore-ready or PITR decision claim.

## Admitted Future Surfaces

Only these future files are admitted:

- `ops/atlas/supabase_backup_restore_posture.py`
- `tests/test_atlas_supabase_backup_restore_posture.py`

No other file is admitted by this packet.

## Admitted Scope

The future helper may do only this:

1. read root-owned Supabase governance inputs
2. classify the known project set into the frozen posture classes
3. emit deterministic read-only output
4. report missing evidence and operator-decision requirements

The future helper may not:

- contact Supabase with mutable authority
- retrieve secrets
- execute dumps
- execute restores
- infer project identity that is not already present in root-owned truth

## Required Root-Owned Inputs

The future helper may consume only root-owned, reproducible sources such as:

- `docs/ops/SUPABASE-PRO-PLATFORM-CAPABILITY-ADOPTION-AUDIT-2026-07-09.md`
- `docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-AND-RESTORE-POSTURE-CONTRACT-FREEZE-2026-07-09.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/registry/STACK-REPO-INVENTORY.json`
- other root-owned Supabase governance receipts already cited by the audit

The first implementation is not admitted to depend on:

- live secret-bearing API calls
- owner-repo truth directly
- hidden transcripts
- uncommitted diffs
- deploy surfaces

## Required Output Shape

The future helper must output deterministic advisory posture only.

Minimum output fields:

- `schema_version`
- `status`
- `safe_to_use`
- `project_count`
- `projects`
- `dependency_only_surfaces`
- `missing_evidence`
- `operator_decisions_required`
- `blockers`
- `warnings`

Each confirmed project output must be able to carry:

- `project_name`
- `project_ref`
- `posture_classes`
- `pitr_candidate`
- `restore_readiness`
- `backup_inventory_status`
- `storage_restore_gap`
- `custom_role_password_gap`
- `notes`

The helper must fail closed rather than invent missing project identity or backup metadata.

## Required Classification Behavior

The future helper must preserve the current contract truths:

- `FawxzzyFitness`, `DiscordOS`, and `Mazer` are the only confirmed project-bound surfaces
- `Nat1-Games` remains `no_project_identity`
- `daily_backup_covered` and `daily_backup_unverified` may coexist when entitlement exists but inventory proof does not
- `restore_process_unverified` remains sticky until a later packet proves more
- `pitr_candidate` is allowed for `FawxzzyFitness` and `DiscordOS` only under current truth
- `pitr_not_approved`, `manual_dump_plan_needed`, `storage_restore_gap`, `custom_role_password_gap`, and `operator_decision_required` must remain explicit where applicable

## Required Safety Behavior

The future helper must:

- stay read-only
- emit no secret values
- avoid project-setting claims that exceed the frozen contract
- keep missing backup inventory explicit
- keep `no_project_identity` explicit
- avoid any restore-ready claim from entitlement alone

## Proof Matrix For The Future Worker

The future implementation must prove at least:

1. deterministic posture output for the three confirmed projects
2. deterministic `no_project_identity` handling for `Nat1-Games`
3. preservation of `daily_backup_covered` plus `daily_backup_unverified` coexistence when inventory proof is absent
4. preservation of `pitr_candidate` only for the admitted projects
5. preservation of `storage_restore_gap` and `custom_role_password_gap`
6. failure-closed behavior for missing or contradictory root inputs
7. no secret, deploy, owner-repo, or mutation authority

## Not Yet Admitted

This packet does not yet admit:

- prompt-pack details for the future worker
- CLI flag details
- JSON fixture paths
- runtime artifact paths
- backup metadata ingestion from live APIs
- any Supabase MCP mutation or read call from the implementation

Those belong to the next prompt-pack packet.

## Authority Denials

This admission preserves denial of:

- Supabase mutation
- restore authority
- PITR authority
- Management API mutation
- branch creation
- secret printing or retrieval
- owner-repo mutation
- Fitness or Mazer fallback routing
- deploy, workflow, or protected-surface authority
- marker-write authority
- final-receipt authority outside ATLAS rules

## Marker Decision

No marker moves.

No Supabase marker is opened.

This is still preparatory platform-governance work.

## Next

Open only this next packet:

```text
Supabase Pro Platform Governance backup inventory and restore-readiness prompt-pack and worker handoff contract
```

That packet must freeze:

- exact helper objective
- exact test objective
- CLI contract
- output contract details beyond the current minimum
- allowed and forbidden file surfaces
- stop conditions
- proof expectations before any implementation lands
