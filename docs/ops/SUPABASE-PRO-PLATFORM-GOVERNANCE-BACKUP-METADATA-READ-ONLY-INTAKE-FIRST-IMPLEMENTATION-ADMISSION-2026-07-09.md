# Supabase Pro Platform Governance backup metadata read-only intake first-implementation admission

- Date: `2026-07-09`
- Lane: `Supabase Pro Platform Governance`
- Mode: `ATLAS-root docs-only first-implementation admission`
- Control-plane checkpoint: `072cd5a10467533369219b58031bee7d9d9f45fd`
- Marker movement: none

## Decision

Admit one future read-only helper/test pair for Supabase backup metadata wrapper validation and summary emission.

The next exact packet is:

```text
Supabase Pro Platform Governance backup metadata read-only intake prompt-pack and worker handoff contract
```

This admission does not call Supabase, store tokens, capture live backup metadata, or move any marker.

## Admitted Future Surfaces

Only these future files are admitted:

- `ops/atlas/supabase_backup_metadata_intake.py`
- `tests/test_atlas_supabase_backup_metadata_intake.py`

No other file is admitted by this packet.

## Objective

Freeze the smallest honest implementation slice that can validate one or more root-safe exported backup metadata wrappers and summarize only the documented read-only fields for the confirmed project set.

The first implementation is advisory only.

## Admitted Scope

The future helper may do only this:

1. read root-owned Supabase governance receipts and stack inventory truth
2. read operator-exported `tmp/**.json` capture wrappers
3. validate wrapper shape and project identity
4. summarize documented backup metadata fields deterministically
5. report which confirmed projects are still missing capture evidence

The future helper may not:

- contact Supabase directly
- manage tokens
- read `secrets/**`
- read `.env*`
- inspect owner repos
- download backups
- restore backups
- infer a project identity that is not already governed at ATLAS root

## Required Inputs

The future helper may consume only:

- `docs/ops/SUPABASE-PRO-PLATFORM-CAPABILITY-ADOPTION-AUDIT-2026-07-09.md`
- `docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-AND-RESTORE-POSTURE-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-METADATA-READ-ONLY-INTAKE-CONTRACT-FREEZE-2026-07-09.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/registry/STACK-REPO-INVENTORY.json`
- operator-exported wrapper files under `tmp/atlas/supabase-backup-metadata/*.json`

## Required Output Shape

Minimum output fields:

- `schema_version`
- `status`
- `safe_to_use`
- `basis_receipts`
- `input_count`
- `captured_project_count`
- `projects`
- `missing_projects`
- `blockers`
- `warnings`

Each captured project output must be able to carry:

- `project_name`
- `project_ref`
- `source`
- `captured_at`
- `region`
- `walg_enabled`
- `pitr_enabled`
- `backup_count`
- `latest_backup_id`
- `latest_backup_status`
- `latest_backup_inserted_at`
- `latest_backup_is_physical`
- `earliest_physical_backup_date_unix`
- `latest_physical_backup_date_unix`

## Required Safety Behavior

The future helper must:

- accept only root-relative `tmp/**.json` capture paths
- reject absolute paths and parent traversal
- fail closed on malformed wrapper JSON
- fail closed on unknown project refs
- fail closed on duplicate project refs in a single run
- keep uncaptured confirmed projects explicit
- avoid restore-readiness claims

## Proof Matrix For The Future Worker

The future implementation must prove at least:

1. deterministic summary output for one valid confirmed-project capture
2. safe partial coverage when fewer than all confirmed projects are captured
3. duplicate project-ref rejection
4. unknown project-ref rejection
5. protected-input-path rejection
6. `tmp/**.json` output-only write behavior
7. failure-closed behavior for missing root inputs or malformed wrapper JSON

## Not Yet Admitted

This packet does not yet admit:

- exact CLI flags
- wrapper schema constants
- proof command strings
- runtime proof fixture paths
- live capture execution

Those belong to the next prompt-pack packet.

## Marker Decision

No marker moves.

No Supabase marker is opened.

## Next

Open only this next packet:

```text
Supabase Pro Platform Governance backup metadata read-only intake prompt-pack and worker handoff contract
```
