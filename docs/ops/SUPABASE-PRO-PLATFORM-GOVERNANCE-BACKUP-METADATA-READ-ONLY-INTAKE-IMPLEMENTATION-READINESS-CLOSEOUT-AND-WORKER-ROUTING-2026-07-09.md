# Supabase Pro Platform Governance backup metadata read-only intake implementation-readiness closeout and worker routing

- Date: `2026-07-09`
- Lane: `Supabase Pro Platform Governance`
- Mode: `ATLAS-root docs-only implementation-readiness closeout`
- Marker movement: none

## Objective

Close the remaining root-only design question for the backup metadata intake helper and route one bounded implementation worker.

## Source Chain

The readiness decision rests on this durable chain:

- `docs/ops/SUPABASE-PRO-PLATFORM-CAPABILITY-ADOPTION-AUDIT-2026-07-09.md`
- `docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-AND-RESTORE-POSTURE-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-METADATA-READ-ONLY-INTAKE-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-METADATA-READ-ONLY-INTAKE-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md`
- `docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-METADATA-READ-ONLY-INTAKE-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-09.md`

## Readiness Decision

The backup metadata intake helper is `implementation_ready`.

Why:

- the official source boundary is frozen to the documented backups endpoint
- the runtime safety boundary is frozen to operator-exported `tmp/**.json` wrappers
- the exact helper/test files are frozen
- the wrapper schema, CLI contract, output schema, proof commands, and authority denials are explicit
- no remaining root-only ambiguity blocks one bounded worker

## Exact Worker Objective

Implement one bounded, read-only helper that consumes only admitted root receipts plus explicit `tmp/**.json` backup wrapper files, validates the frozen wrapper contract, summarizes only documented backup metadata fields for confirmed projects, and proves the behavior through focused tests.

## Exact Allowed Touch Surfaces

The worker may touch only:

- `ops/atlas/supabase_backup_metadata_intake.py`
- `tests/test_atlas_supabase_backup_metadata_intake.py`

Runtime proof may create temporary files only under:

- `tmp/atlas/supabase-backup-metadata/`

## Exact Forbidden Authority

The worker must not:

- call live Supabase endpoints
- read or write secrets
- mutate owner repos
- stage, commit, or push
- edit workflow or deploy surfaces
- move markers
- emit final receipts

## Exact Post-Worker Package

If the worker lands cleanly, the exact next package is:

```text
Supabase Pro Platform Governance backup metadata read-only intake first-implementation worker-cluster reconciliation
```

That reconciliation may add one bounded receipt plus ATLAS Book mirrors only after focused proof, stack validation, and one synthetic root-safe helper run succeed.

## Marker Decision

No marker moves.

No Supabase marker is opened.
