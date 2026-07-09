# Vercel Platform Observability Governance deployment freshness inventory first-implementation worker-cluster reconciliation

- Date: `2026-07-09`
- Lane: `Vercel Platform Observability Governance`
- Mode: `ATLAS-root implementation-backed worker-cluster reconciliation`
- Marker movement: none

## Scope

This receipt reconciles the admitted ATLAS-root worker slice for:

- `ops/atlas/vercel_deployment_freshness_inventory.py`
- `tests/test_atlas_vercel_deployment_freshness_inventory.py`

The worker remains read-only and root-bounded.

## Implemented Helper

`ops/atlas/vercel_deployment_freshness_inventory.py` now:

1. validates explicit root-relative `tmp/**.json` input and output paths
2. admits only the project-inventory export and helper-report schemas
3. enforces governed-project mapping across the five known Vercel projects
4. derives `deployment_age_days` from the latest production deployment timestamp
5. classifies each governed project into the frozen freshness bucket enum
6. reports missing-project coverage as `advisory_gap`
7. rejects duplicate project captures, malformed timestamps, protected paths, and unsupported schemas
8. writes optional output only to root-relative `tmp/**.json`
9. supports `--strict` for nonzero advisory/blocker exit handling

## CLI Contract Reconciled

The landed CLI is:

```text
python ops/atlas/vercel_deployment_freshness_inventory.py
  --input <root-relative tmp path> [repeatable]
  [--json]
  [--output <root-relative tmp report path>]
  [--strict]
```

## JSON Contract Reconciled

The landed output schema is:

```text
atlas.vercel_deployment_freshness_inventory.v1
```

Allowed statuses:

- `ok`
- `advisory_gap`
- `blocker`
- `internal_error`

## Proof

Focused worker tests:

```powershell
python -m unittest tests.test_atlas_vercel_deployment_freshness_inventory -v
```

Result:

- focused helper tests passed

Root-safe smoke:

```powershell
python ops/atlas/vercel_deployment_freshness_inventory.py --json --input tmp/atlas/vercel-observability/fawxzzy-full-coverage-2026-07-09T18-38-23Z.report.json --output tmp/atlas/vercel-observability/deployment-freshness-smoke-report.json
```

Result:

- `status=ok`
- `safe_to_use=true`
- `captured_project_count=5`
- `project_count=5`
- `freshness_counts.same_day=3`
- `freshness_counts.age_over_30_days=2`

Root validation:

```powershell
python ops/validation/validate_stack.py
```

Result:

- `critical=0 error=0 warning=0 info=0`

## Authority Preservation

Preserved throughout this packet:

- no live Vercel query
- no deploy/redeploy/promote/rollback authority
- no env or token handling
- no owner-repo mutation
- no committed `tmp/**` artifacts
- no marker movement

## Marker Decision

No marker move is claimed here.

`Vercel Platform Observability Governance` remains `0%`.

Reason:

- the helper implementation is real and proof-backed
- but this packet intentionally does not widen into broader marker-surface reconciliation

## Exact Next Packet

If root reopens this family explicitly, the next safe root-only packet should be:

```text
Vercel Platform Observability Governance deployment freshness inventory prompt-pack and worker reconciliation marker-surface ratchet decision
```

That packet should decide whether the helper-backed freshness slice materially broadens the lane beyond `0%`, or whether it remains a supporting proof family under the held-root routing posture.
