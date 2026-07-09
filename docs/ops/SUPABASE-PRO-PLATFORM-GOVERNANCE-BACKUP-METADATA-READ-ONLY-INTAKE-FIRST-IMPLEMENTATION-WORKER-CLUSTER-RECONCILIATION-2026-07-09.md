# Supabase Pro Platform Governance backup metadata read-only intake first-implementation worker-cluster reconciliation

- Date: `2026-07-09`
- Lane: `Supabase Pro Platform Governance`
- Mode: `ATLAS-root implementation-backed worker-cluster reconciliation`
- Marker movement: none

## Scope

This is an ATLAS-root implementation-backed reconciliation for the admitted backup metadata intake helper/test pair:

- `ops/atlas/supabase_backup_metadata_intake.py`
- `tests/test_atlas_supabase_backup_metadata_intake.py`

The worker is advisory only. It has no live Supabase call authority, no token authority, no restore authority, no PITR authority, no owner-repo mutation authority, no deploy authority, no workflow authority, and no marker-write authority.

## Basis

The implementation basis before this worker was:

- `main@072cd5a10467533369219b58031bee7d9d9f45fd`

The control-plane chain before execution was:

- `docs/ops/SUPABASE-PRO-PLATFORM-CAPABILITY-ADOPTION-AUDIT-2026-07-09.md`
- `docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-AND-RESTORE-POSTURE-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-METADATA-READ-ONLY-INTAKE-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-METADATA-READ-ONLY-INTAKE-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md`
- `docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-METADATA-READ-ONLY-INTAKE-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-09.md`
- `docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-METADATA-READ-ONLY-INTAKE-IMPLEMENTATION-READINESS-CLOSEOUT-AND-WORKER-ROUTING-2026-07-09.md`

## Implemented Worker

`ops/atlas/supabase_backup_metadata_intake.py` now validates root-relative operator-exported wrapper JSON under `tmp/**.json` and emits deterministic advisory JSON with:

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

The helper freezes wrapper schema `atlas.supabase.backup-management-export.v1`, admitted source `management_api.v1.projects.database.backups`, and output schema `atlas.supabase_backup_metadata_intake.v1`. It rejects protected input or output paths, duplicate project refs, malformed wrappers, unknown project refs, missing root receipts, and any path outside root-relative `tmp/**.json`.

## Proof

Executed proof:

```powershell
python -m unittest tests.test_atlas_supabase_backup_metadata_intake -v
```

Result:

- `9` tests passed

Stack validation:

```powershell
python ops\validation\validate_stack.py
```

Result:

- `critical=0 error=0 warning=0 info=0`

Synthetic helper proof:

```powershell
python ops\atlas\supabase_backup_metadata_intake.py --json --input tmp/atlas/supabase-backup-metadata/proof-sample.json
```

Result:

- `status=ok`
- `safe_to_use=true`
- `input_count=1`
- `captured_project_count=1`

The synthetic proof capture was intentionally non-production and root-safe. It proved the helper contract without claiming that real project backup metadata has already been captured.

## Residual Gap Preserved

This worker does not clear the cross-project evidence gap that motivated the packet.

What remains true:

- no real production backup metadata export is yet recorded at ATLAS root
- `daily_backup_unverified` remains the governed posture in the earlier backup-restore classifier
- the new helper is only the safe intake and validation surface for future metadata capture

## Marker Decision

No marker moves.

No Supabase marker is opened.

## Next Package

The next exact platform packet is:

```text
Supabase Pro Platform Governance backup metadata first operator-export capture contract freeze
```

Reason:

- the safe root-owned intake helper now exists
- the next smallest useful slice is to freeze how one real operator-exported capture may be produced, stored, summarized, and receipted without widening into token automation or restore execution
