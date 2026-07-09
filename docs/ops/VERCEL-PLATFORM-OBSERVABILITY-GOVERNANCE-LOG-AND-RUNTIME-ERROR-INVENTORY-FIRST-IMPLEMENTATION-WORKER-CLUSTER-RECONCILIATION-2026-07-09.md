# Vercel Platform Observability Governance log and runtime-error inventory first-implementation worker-cluster reconciliation

- Date: `2026-07-09`
- Lane: `Vercel Platform Observability Governance`
- Mode: `ATLAS-root implementation-backed worker-cluster reconciliation`
- Marker movement: none

## Scope

This receipt reconciles the admitted ATLAS-root worker slice for:

- `ops/atlas/vercel_log_runtime_error_inventory.py`
- `tests/test_atlas_vercel_log_runtime_error_inventory.py`

The worker remains read-only and root-bounded.

## Worker Commit

The worker landed on:

- `main@de799ab0b6c09f9929163d0c4c36cff11a0d1412`

This commit added the admitted helper/test pair only.

## Implemented Helper

`ops/atlas/vercel_log_runtime_error_inventory.py` now:

1. validates root-relative `tmp/**` wrapper intake for `.json`, `.jsonl`, and `.ndjson`
2. accepts only admitted source classes:
   - `request_log`
   - `runtime_log`
   - `runtime_error_group`
   - `build_log_summary`
3. enforces governed-project identity against the fixed Vercel project set
4. normalizes route input to route or path patterns
5. aggregates deterministic project and cluster summaries
6. rejects forbidden sensitive keys and sensitive value patterns
7. writes optional output only to root-relative `tmp/**.json`
8. supports `--strict` for nonzero advisory/blocker exit handling

## CLI Contract Reconciled

The landed CLI is:

```text
python ops/atlas/vercel_log_runtime_error_inventory.py
  --input <root-relative tmp wrapper path> [repeatable]
  [--json]
  [--output <root-relative tmp report path>]
  [--strict]
```

## JSON Contract Reconciled

The landed output schema is:

```text
atlas.vercel_log_runtime_error_inventory.v1
```

Top-level fields:

- `schema_version`
- `status`
- `safe_to_use`
- `captured_project_count`
- `project_count`
- `runtime_error_cluster_count`
- `log_record_count`
- `redaction_status`
- `projects`
- `clusters`
- `warnings`
- `blockers`
- `forbidden_fields_detected`
- `next_recommended_packet`

Allowed statuses:

- `ok`
- `advisory_gap`
- `blocker`
- `internal_error`

## Accepted Source Classes

The helper now admits only:

- `request_log`
- `runtime_log`
- `runtime_error_group`
- `build_log_summary`

## Rejected Sensitive Classes

The helper rejects or blocks:

- env values
- token values
- secret values
- cookie or authorization header material
- raw request bodies
- payment or customer payload material
- unsupported source classes
- unknown governed projects
- protected or out-of-bound input/output paths

## Proof

Focused worker tests:

```powershell
python -m unittest tests.test_atlas_vercel_log_runtime_error_inventory -v
```

Result:

- `11` tests passed

Regression guard for the existing Vercel project-inventory helper:

```powershell
python -m unittest tests.test_atlas_vercel_observability_project_inventory -v
```

Result:

- `9` tests passed

Root validation:

```powershell
python ops/validation/validate_stack.py
```

Result:

- `critical=0 error=0 warning=0 info=0`

Continuity health:

```powershell
python ops/atlas/continuity_manifest_health.py
python ops/atlas/continuity_open_marker_restart_index.py
python ops/atlas/continuity_coverage.py
```

Result:

- manifest health `status=ok`
- restart index `status=ok`
- coverage `status=structured`

Synthetic root-safe smoke:

```powershell
python ops/atlas/vercel_log_runtime_error_inventory.py --json --input tmp/atlas/vercel-observability/worker-smoke-fitness.json --input tmp/atlas/vercel-observability/worker-smoke-discordos.ndjson --output tmp/atlas/vercel-observability/worker-smoke-report.json
```

Result:

- `status=advisory_gap`
- `safe_to_use=true`
- `captured_project_count=2`
- `project_count=5`
- `runtime_error_cluster_count=1`
- `log_record_count=171`
- Fitness cluster preserved as observability evidence only:
  - `cluster_label=billing-webhook-stripe`
  - `route_pattern=/api/billing/webhook/stripe`
  - `deployment_id=dpl_HUsDUbhofhJFEKxLCazcDfQk8pTM`

The smoke report remained local under `tmp/atlas/vercel-observability/` and was not staged.

## Sensitive-Rejection Proof

The focused test suite proves:

1. env-style assignment strings are rejected
2. token-style strings are rejected
3. cookie or authorization-header keys are rejected
4. request-body keys are rejected
5. unknown projects are rejected
6. unsupported source classes are rejected
7. input paths outside `tmp/**` are rejected
8. absolute output paths are rejected
9. safe `tmp/**.json` output is accepted
10. deterministic top-level JSON ordering is preserved
11. `--strict` returns nonzero on blockers

## Authority Preservation

Preserved throughout this packet:

- no live log pull
- no Vercel mutation
- no owner-repo mutation
- no secrets read
- no `.env*` read
- no committed `tmp/**` artifacts

## Marker Decision

No marker move is claimed here.

`Vercel Platform Observability Governance` remains `0%`.

Reason:

- the worker implementation is real and proof-backed
- the helper/test pair is now durably landed
- but this packet intentionally did not widen into broader marker/current-state/restart/manifest mirror edits
- the existing ATLAS root read model still reports held active-lane routing above this supporting lane

## Exact Next Packet

No immediate same-lane ratchet is claimed from this receipt alone.

If root reopens this family explicitly, the next safe root-only packet should be:

```text
Vercel Platform Observability Governance log and runtime-error inventory marker-surface ratchet decision
```

That packet would decide whether broader ATLAS mirror surfaces can be updated cleanly for a future `0% -> 10%` move, or whether the lane should remain held at `0%` until a broader capture-backed widening is selected.
