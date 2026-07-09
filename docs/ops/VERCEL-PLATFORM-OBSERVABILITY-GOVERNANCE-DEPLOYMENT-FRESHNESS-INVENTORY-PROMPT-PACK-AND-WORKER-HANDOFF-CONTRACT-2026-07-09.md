# Vercel Platform Observability Governance deployment freshness inventory prompt-pack and worker handoff contract

- Date: `2026-07-09`
- Lane: `Vercel Platform Observability Governance`
- Mode: `ATLAS-root docs-only prompt-pack contract`
- Control-plane checkpoint: `049e65d923af3c0ad71389db11ea6a3eb547df0d`
- Marker movement: none

## Worker Objective

Implement one bounded helper/test pair so `ops/atlas/vercel_deployment_freshness_inventory.py` can classify production deployment freshness for the governed Vercel project set from already admitted project-inventory evidence without touching live Vercel state.

## Exact Files

The worker may touch only:

- `ops/atlas/vercel_deployment_freshness_inventory.py`
- `tests/test_atlas_vercel_deployment_freshness_inventory.py`

## Exact Input Contract

The helper must consume only explicit root-relative `tmp/**.json` inputs from the already admitted project-inventory evidence family:

- `atlas.vercel.observability.project_inventory_export.v1`
- `atlas.vercel_observability_project_inventory.v1`

The helper must reject:

- absolute paths
- parent traversal
- protected paths
- non-`.json` paths
- unsupported schemas
- runtime-log or runtime-error wrapper schemas
- live Vercel query inputs

## Exact CLI Contract

Required flags:

- `--input` repeatable, one or more root-relative `tmp/**.json` paths
- `--json` optional JSON-only stdout mode
- `--output` optional root-relative `tmp/**.json` output path
- `--strict` optional nonzero exit for advisory-gap and blocker statuses

The helper may derive the evaluation date internally; it must not require live platform time or remote calls.

## Exact Helper Contract

The worker must implement a helper that:

1. reads only the admitted Vercel doctrine receipts plus stack inventory truth
2. validates root-relative `tmp/**.json` input paths
3. accepts only the admitted project-inventory export or helper-report schemas
4. extracts governed project deployment freshness fields only
5. rejects duplicate project captures in one run
6. rejects unknown projects, malformed timestamps, or missing production deployment timestamps
7. derives `deployment_age_days`
8. maps each project into the frozen freshness bucket enum
9. emits deterministic advisory JSON only
10. writes optional output only to root-relative `tmp/**.json`

## Exact Output Contract

The helper output must emit schema version:

```text
atlas.vercel_deployment_freshness_inventory.v1
```

Allowed statuses:

- `ok`
- `advisory_gap`
- `blocker`
- `internal_error`

Required top-level fields:

- `schema_version`
- `status`
- `safe_to_use`
- `basis_receipts`
- `input_count`
- `captured_project_count`
- `project_count`
- `as_of_date`
- `freshness_counts`
- `projects`
- `missing_projects`
- `warnings`
- `blockers`
- `next_recommended_packet`

Required per-project summary fields:

- `project_name`
- `project_id`
- `repo_logical_id`
- `latest_production_deployment_id`
- `latest_production_deployment_created_at`
- `latest_production_commit_sha`
- `deployment_age_days`
- `freshness_bucket`

## Exact Freshness Buckets

The helper may emit only:

- `same_day`
- `age_1_to_7_days`
- `age_8_to_30_days`
- `age_over_30_days`
- `missing_production_timestamp`

## Exact Allowed Inputs

The helper may read only:

- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-CAPABILITY-AUDIT-2026-07-09.md`
- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-READ-ONLY-PROJECT-INVENTORY-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-READ-ONLY-PROJECT-INVENTORY-FIRST-OPERATOR-EXPORT-CAPTURE-EXECUTION-2026-07-09.md`
- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-PROJECT-INVENTORY-COVERAGE-RECONCILIATION-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-DEPLOYMENT-FRESHNESS-INVENTORY-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-DEPLOYMENT-FRESHNESS-INVENTORY-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/registry/STACK-REPO-INVENTORY.json`
- explicitly named project-inventory evidence files under `tmp/atlas/vercel-observability/`

## Exact Proof Commands

The worker must run:

1. `python -m unittest tests.test_atlas_vercel_deployment_freshness_inventory -v`
2. one root-safe helper proof command against admitted `tmp/atlas/vercel-observability/*.json`
3. `python ops/validation/validate_stack.py`
4. `git status --short`
5. `git diff --name-only`

## Exact Required Proof Matrix

The worker proof must cover at least:

1. valid helper-report input is accepted
2. valid export-wrapper input is accepted
3. freshness buckets classify same-day and stale deployments correctly
4. duplicate project capture blocks
5. unknown projects block
6. malformed deployment timestamps block
7. protected input paths block
8. absolute output paths block
9. safe `tmp/**.json` output is accepted
10. deterministic top-level JSON ordering is preserved
11. `--strict` returns nonzero on advisory-gap

## Exact Forbidden Authority

The worker must not:

- call Vercel
- query deployments live
- read `.env*`
- read token or secret material
- touch owner repos
- widen into runtime-log or runtime-error helper scope
- move markers
- emit final receipts
- add helper files outside the admitted two-file surface

## Next

Open only this next packet:

```text
Vercel Platform Observability Governance deployment freshness inventory implementation-readiness closeout and worker routing
```
