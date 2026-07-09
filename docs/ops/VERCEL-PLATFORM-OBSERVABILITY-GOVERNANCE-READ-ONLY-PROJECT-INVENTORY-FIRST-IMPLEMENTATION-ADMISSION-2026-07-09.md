# Vercel Platform Observability Governance read-only project inventory first-implementation admission

- Date: `2026-07-09`
- Lane: `Vercel Platform Observability Governance`
- Mode: `ATLAS-root docs-only first-implementation admission`
- Control-plane checkpoint: `f210d703f5df370a48d7ee68276661a163752f31`
- Marker movement: none

## Decision

Admit one future read-only helper/test pair for Vercel project-inventory wrapper validation and deterministic summary emission.

The next exact packet is:

```text
Vercel Platform Observability Governance read-only project inventory prompt-pack and worker handoff contract
```

This admission does not query Vercel, store tokens, inspect env values, or move any marker.

## Admitted Future Surfaces

Only these future files are admitted:

- `ops/atlas/vercel_observability_project_inventory.py`
- `tests/test_atlas_vercel_observability_project_inventory.py`

No other file is admitted by this packet.

## Objective

Freeze the smallest honest implementation slice that can validate one or more root-safe Vercel observability project wrappers and summarize only the admitted read-only inventory fields for the currently governed project set.

The first implementation is advisory only.

## Admitted Scope

The future helper may do only this:

1. read root-owned Vercel governance receipts and stack inventory truth
2. read operator-exported `tmp/**.json` project inventory wrappers
3. validate team identity, project identity, and admitted field shape
4. summarize deterministic deployment, domain, and observability posture fields
5. report which governed projects still lack admitted capture evidence

The future helper may not:

- contact Vercel directly
- manage tokens
- read `secrets/**`
- read `.env*`
- inspect owner repos
- deploy, redeploy, promote, or roll back
- infer a project identity that is not already governed at ATLAS root

## Required Inputs

The future helper may consume only:

- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-CAPABILITY-AUDIT-2026-07-09.md`
- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-READ-ONLY-PROJECT-INVENTORY-CONTRACT-FREEZE-2026-07-09.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/registry/STACK-REPO-INVENTORY.json`
- operator-exported wrapper files under `tmp/atlas/vercel-observability/*.json`

## Admitted Wrapper Shape

Each admitted wrapper must be able to carry only bounded read-only fields:

- `schema_version`
- `captured_at`
- `source`
- `team`
- `project`
- `deployments`
- `log_surfaces`
- `runtime_error_observations`
- `observability_surfaces`
- `posture_classes`

Required `team` fields:

- `id`
- `name`
- optional `slug`

Required `project` fields:

- `id`
- `name`
- `framework`
- `node_version`
- `domains`
- `repo_logical_id`
- `inventory_scope`

Allowed `deployments` fields:

- `id`
- `url`
- `created_at`
- `state`
- `target`
- `commit_sha`
- `branch`
- `creator`
- `inspector_url`
- `rollback_candidate`

Allowed `log_surfaces` fields:

- `build_logs_queryable`
- `runtime_logs_queryable`
- `runtime_errors_queryable`

Allowed `runtime_error_observations` fields:

- `error_group`
- `count`
- `route`
- `first_seen`
- `last_seen`
- `last_deployment_id`

Allowed `observability_surfaces` fields:

- `web_analytics`
- `speed_insights`
- `drains`
- `alerts`
- `env_name_only`

## Required Output Shape

Minimum output fields:

- `schema_version`
- `status`
- `safe_to_use`
- `basis_receipts`
- `input_count`
- `team`
- `posture_classes`
- `captured_project_count`
- `projects`
- `missing_projects`
- `blockers`
- `warnings`

Each captured project output must be able to carry:

- `project_name`
- `project_id`
- `repo_logical_id`
- `inventory_scope`
- `framework`
- `node_version`
- `domain_count`
- `domains`
- `latest_production_deployment_id`
- `latest_production_deployment_created_at`
- `latest_production_commit_sha`
- `build_logs_queryable`
- `runtime_logs_queryable`
- `runtime_errors_queryable`
- `runtime_error_group_count`
- `runtime_error_observations`

## Required Safety Behavior

The future helper must:

- accept only root-relative `tmp/**.json` capture paths
- reject absolute paths and parent traversal
- fail closed on malformed wrapper JSON
- fail closed on unknown project ids, names, or repo logical ids
- fail closed on duplicate project refs in a single run
- fail closed on inconsistent team identity across inputs
- reject forbidden sensitive wrapper keys such as env-value, token-value, or secret-value payloads
- keep uncaptured governed projects explicit
- avoid deploy or observability entitlement claims beyond the admitted wrapper content

## Proof Matrix For The Future Worker

The future implementation must prove at least:

1. deterministic summary output for one valid governed-project capture
2. safe partial coverage when fewer than all governed projects are captured
3. duplicate project capture rejection
4. inconsistent team identity rejection
5. invalid posture-class rejection
6. protected-input-path rejection
7. `tmp/**.json` output-only write behavior
8. failure-closed behavior for malformed wrapper JSON or forbidden sensitive keys

## Not Yet Admitted

This packet does not yet admit:

- exact CLI flags
- exact schema constants
- proof command strings
- runtime proof fixture paths
- live capture execution

Those belong to the next prompt-pack packet.

## Marker Decision

No marker moves.

No Vercel marker is opened.

## Next

Open only this next packet:

```text
Vercel Platform Observability Governance read-only project inventory prompt-pack and worker handoff contract
```
