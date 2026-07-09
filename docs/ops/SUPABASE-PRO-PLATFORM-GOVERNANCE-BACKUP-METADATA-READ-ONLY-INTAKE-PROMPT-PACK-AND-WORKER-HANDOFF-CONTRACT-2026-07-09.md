# Supabase Pro Platform Governance backup metadata read-only intake prompt-pack and worker handoff contract

- Date: `2026-07-09`
- Lane: `Supabase Pro Platform Governance`
- Mode: `ATLAS-root docs-only prompt-pack contract`
- Control-plane checkpoint: `072cd5a10467533369219b58031bee7d9d9f45fd`
- Marker movement: none

## Worker Objective

Implement one bounded helper/test pair that validates root-safe exported backup metadata wrappers and emits deterministic advisory JSON for the confirmed Supabase project set without touching live tokens or live platform state.

## Exact Files

The worker may touch only:

- `ops/atlas/supabase_backup_metadata_intake.py`
- `tests/test_atlas_supabase_backup_metadata_intake.py`

## Exact Wrapper Contract

The helper must validate wrapper schema:

```text
atlas.supabase.backup-management-export.v1
```

Each input wrapper must contain:

- `schema_version`
- `captured_at`
- `project_ref`
- `source`
- `payload`

`source` must equal:

```text
management_api.v1.projects.database.backups
```

## Exact CLI Contract

Required flags:

- `--input` repeatable, one or more root-relative `tmp/**.json` wrapper paths
- `--json` optional JSON-only stdout mode
- `--output` optional root-relative `tmp/**.json` output path

The helper must reject:

- zero `--input` arguments
- absolute input paths
- parent traversal
- protected paths
- non-JSON input paths
- output paths outside `tmp/**.json`

## Exact Output Contract

The helper must emit schema version:

```text
atlas.supabase_backup_metadata_intake.v1
```

Allowed statuses:

- `ok`
- `blocker`
- `internal_error`

Required top-level fields:

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

## Exact Project Summary Contract

Each admitted project summary may use only:

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

If `backups` is empty, the helper may emit `backup_count=0` and `null` latest-backup fields, but must not invent backup rows.

## Exact Allowed Inputs

The helper may read only:

- the July 9 Supabase audit
- the July 9 backup-and-restore posture contract freeze
- the July 9 backup metadata intake contract freeze
- ATLAS Book current state, receipt index, and restart guide
- stack repo inventory JSON
- explicitly named `tmp/**.json` wrapper files

## Exact Forbidden Authority

The worker must not:

- call live Supabase APIs
- read or print tokens
- touch `secrets/**`
- touch `.env*`
- mutate owner repos
- mutate Supabase settings
- download or restore backups
- stage, commit, or push
- move markers
- emit final receipts

## Exact Proof Commands

The worker must run:

1. `python -m unittest tests.test_atlas_supabase_backup_metadata_intake -v`
2. `python ops/validation/validate_stack.py`
3. one root-safe helper proof command against a synthetic wrapper written under `tmp/atlas/supabase-backup-metadata/`
4. `git status --short`
5. `git diff --name-only`

## Exact Stop Conditions

Stop and return without implementation if the worker would require:

- live Supabase token use
- owner-repo mutation
- secret handling
- workflow or deploy mutation
- marker movement
- a broader helper family than the admitted single intake helper

## Next

Open only this next packet:

```text
Supabase Pro Platform Governance backup metadata read-only intake implementation-readiness closeout and worker routing
```
