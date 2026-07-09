# Vercel Platform Observability Governance deployment freshness inventory contract freeze

- Date: `2026-07-09`
- Lane: `Vercel Platform Observability Governance`
- Mode: `ATLAS-root docs-only contract freeze`
- Control-plane checkpoint: `ed653c6e9e91c42141970f4b5166f19db702c352`
- Marker movement: none

## Decision

Freeze one bounded read-only deployment freshness inventory contract for the five governed Vercel projects already captured through the landed project-inventory wrapper/report path.

The next exact packet is:

```text
Vercel Platform Observability Governance deployment freshness inventory first-implementation admission
```

This packet does not call Vercel, pull new wrappers, mutate deployments, promote or roll back releases, read env values, handle tokens, or move any marker.

## Why This Contract Exists

The current Vercel observability chain already proves two durable facts:

- the governed five-project inventory is fully captured through root-safe wrappers and a landed helper
- each captured project already exposes exact production deployment metadata fields that are useful for restart truth and platform posture

What is still missing is one explicit contract that says how ATLAS root should treat those deployment fields as a separate read-only governance slice instead of letting them stay incidental to project inventory.

## Governing Inputs

This contract inherits from:

- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-CAPABILITY-AUDIT-2026-07-09.md`
- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-READ-ONLY-PROJECT-INVENTORY-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-READ-ONLY-PROJECT-INVENTORY-FIRST-OPERATOR-EXPORT-CAPTURE-EXECUTION-2026-07-09.md`
- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-PROJECT-INVENTORY-COVERAGE-RECONCILIATION-CONTRACT-FREEZE-2026-07-09.md`

The current real full-coverage evidence is the local report:

- `tmp/atlas/vercel-observability/fawxzzy-full-coverage-2026-07-09T18-38-23Z.report.json`

That report is local-only evidence and remains out of git.

## Admitted Source Boundary

Deployment freshness inventory may consume only the already admitted project-inventory evidence family:

- wrapper schema: `atlas.vercel.observability.project_inventory_export.v1`
- helper output schema: `atlas.vercel_observability_project_inventory.v1`

This contract does not admit a separate live deployment query path yet. It remains grounded in the landed project-inventory helper and safe operator-export wrappers already captured under `tmp/atlas/vercel-observability/`.

## Admitted Fields

For each governed project, the deployment freshness slice may consume only these production-deployment fields:

- `project_name`
- `repo_logical_id`
- `latest_production_deployment_id`
- `latest_production_deployment_created_at`
- `latest_production_commit_sha`

Optional supporting identity fields may remain visible for context only:

- `project_id`
- `framework`
- `node_version`
- `domains`

The freshness slice must not widen into:

- env names or env values
- secrets or token-bearing headers
- runtime log bodies
- runtime error record bodies
- build log text beyond presence or queryability posture
- deployment mutation actions

## Freshness Model

The frozen read-only model is:

1. preserve the exact latest production deployment timestamp in UTC
2. preserve the exact latest production deployment id
3. preserve the exact latest production commit SHA
4. derive deployment age only from the captured UTC timestamp and the packet evaluation date
5. classify each project into one bounded freshness bucket

Admitted freshness buckets:

- `same_day`
- `age_1_to_7_days`
- `age_8_to_30_days`
- `age_over_30_days`
- `missing_production_timestamp`

This model is read-only posture only. A stale bucket is not deployment authority.

## Current July 9, 2026 Snapshot

Using the full five-project report captured on July 9, 2026, the current governed production-deployment snapshot is:

| Project | Latest production deployment id | Latest production deployment created at (UTC) | Latest production commit SHA | Freshness bucket on July 9, 2026 |
| --- | --- | --- | --- | --- |
| `fawxzzy-discordos` | `dpl_F4GWszrJ3kKtLLpjWEn1NhxmNCfX` | `2026-07-09T16:33:54.692000Z` | `f93988dfb7553e460275e50571d4d3eda8ad1099` | `same_day` |
| `fawxzzy-fitness` | `dpl_2yKa5EXY3dhgePyBJq4AnEPzBhBV` | `2026-07-09T17:27:03.241000Z` | `e1ab7fbea979456380230c5459fdef6ae4c927e9` | `same_day` |
| `fawxzzy-mazer` | `dpl_J4KJ9u2eZzHK6m5qSxq19qCPYTfT` | `2026-07-09T12:54:32.293000Z` | `845446266347be19524fbe36f39e688db804e9e8` | `same_day` |
| `fawxzzy-trove` | `dpl_Esx36xmewDbqKGMSuN3YMrFC6YSG` | `2026-05-23T03:31:42.635000Z` | `e0566a6b8d65d5892f0cc9defda36481eccbaa29` | `age_over_30_days` |
| `fawxzzy-foundation` | `dpl_HeA4TWgXwr9CwJgGkBBpYD1R8eiB` | `2026-04-12T23:42:19.230000Z` | `2187fb27b744325e690113277d537951a8b11846` | `age_over_30_days` |

Observed implications from this snapshot:

- three governed projects had same-day production deployments on July 9, 2026
- two governed projects had materially older production deployments, dated May 23, 2026 and April 12, 2026
- the contract can therefore support useful comparative posture without widening into deployment mutation

## What This Contract Proves

This contract proves that ATLAS root can govern one bounded deployment freshness read model from already admitted evidence.

It does not prove:

- whether any project should be redeployed
- whether any project is healthy at runtime
- whether build logs are clean
- whether runtime-error posture is acceptable
- whether a stale deployment is wrong or merely inactive

Those remain separate packets.

## Forbidden Conclusions

This packet must not be used to claim:

- redeploy authority
- rollback authority
- production-traffic authority
- incident authority
- owner-repo implementation authority
- marker movement by freshness alone

It is a read-only inventory contract, not an operations runbook.

## Future Helper Boundary

If a helper is admitted later, it may:

- consume only admitted project-inventory wrapper/report inputs
- emit deterministic per-project freshness summaries
- compute `deployment_age_days` and the frozen bucket enum
- write optional output only to root-relative `tmp/**.json`

If a helper is admitted later, it must not:

- call Vercel directly
- mutate Vercel projects or deployments
- read `.env*`
- print or persist token values
- widen into runtime log or runtime-error payloads

## Marker Decision

No marker moves.

`Vercel Platform Observability Governance` remains `0%`.

Reason:

- this packet freezes one next observability subfamily cleanly
- but it does not add a new helper, new proof harness, or broader marker-surface reconciliation

## Next

Open only this next packet:

```text
Vercel Platform Observability Governance deployment freshness inventory first-implementation admission
```

That packet may admit:

- `ops/atlas/vercel_deployment_freshness_inventory.py`
- `tests/test_atlas_vercel_deployment_freshness_inventory.py`

It should stay rooted in the already admitted project-inventory wrappers and helper output rather than inventing a new live Vercel query surface.
