# Vercel Platform Observability Governance deployment freshness inventory first-implementation admission

- Date: `2026-07-09`
- Lane: `Vercel Platform Observability Governance`
- Mode: `ATLAS-root implementation admission`
- Control-plane checkpoint: `c919234cafb5538bbe0b25e0608e3e4dc448d439`
- Marker movement: none

## Decision

Admit one future root-owned helper/test pair for bounded deployment freshness inventory classification across the governed Vercel project set:

- `ops/atlas/vercel_deployment_freshness_inventory.py`
- `tests/test_atlas_vercel_deployment_freshness_inventory.py`

The next exact packet is:

```text
Vercel Platform Observability Governance deployment freshness inventory prompt-pack and worker handoff contract
```

This packet does not implement the helper yet, does not call Vercel, does not read env values or token values, does not mutate deployments, and does not move any marker.

## Why Admission Is Now Honest

Admission is now justified because the immediately prior contract freeze already fixed the smallest useful scope:

- deployment freshness must remain read-only
- evidence must stay rooted in already admitted project-inventory wrappers and helper output
- freshness posture must use exact production deployment timestamps, ids, and commit SHAs
- freshness output must not widen into runtime payloads, env values, or mutation authority

That makes the helper shape narrow enough to admit without guessing new platform authority.

## Admitted Inputs

The future helper may consume only already admitted evidence from the project-inventory family:

- `atlas.vercel.observability.project_inventory_export.v1`
- `atlas.vercel_observability_project_inventory.v1`

The helper must stay root-relative and local-only for inputs:

- `tmp/**.json`

Forbidden inputs remain:

- `.env*`
- secrets or token-bearing files
- `.vercel/**`
- owner repos
- direct Vercel live API calls
- runtime log or runtime-error payload wrappers

## Admitted Output Shape

The future helper may emit deterministic advisory JSON only.

Required top-level posture fields:

- schema version
- status
- safe-to-use flag
- input count
- captured project count
- per-project freshness summaries
- warnings
- blockers
- next recommended packet

Required per-project summary fields:

- `project_name`
- `repo_logical_id`
- `latest_production_deployment_id`
- `latest_production_deployment_created_at`
- `latest_production_commit_sha`
- `deployment_age_days`
- `freshness_bucket`

Admitted freshness buckets remain the frozen contract enum:

- `same_day`
- `age_1_to_7_days`
- `age_8_to_30_days`
- `age_over_30_days`
- `missing_production_timestamp`

## Admitted CLI Envelope

The future helper may expose only a bounded root-safe CLI surface such as:

```text
python ops/atlas/vercel_deployment_freshness_inventory.py
  --input <root-relative tmp path> [repeatable]
  [--json]
  [--output <root-relative tmp report path>]
  [--strict]
```

This admission does not freeze the exact argparse spelling beyond that narrow envelope, but it does freeze these boundaries:

- input must remain explicit, root-relative, and local
- optional output must remain root-relative `tmp/**.json`
- `--strict` may elevate blockers to nonzero exit
- no hidden project selection, no ambient secret intake, and no live Vercel fetch path are admitted

## Required Rejections

The future helper must reject:

- absolute paths
- parent traversal
- protected surfaces outside `tmp/**`
- unsupported schemas
- missing deployment timestamp when the wrapper/report does not admit it
- malformed timestamps
- duplicate project rows when one run would double-count the same governed project
- unknown governed projects

It must preserve authority denial for:

- deploy
- redeploy
- promote
- rollback
- env access
- token access
- secret access
- owner-repo mutation
- marker movement

## Why This Is Still Separate From Runtime/Error Governance

The current runtime-error helper family and this deployment-freshness family must stay separate because they answer different questions:

- deployment freshness asks when production last changed
- runtime-error inventory asks what grouped failures are visible

Joining them too early would collapse clean read-only boundaries and make the next helper harder to validate.

## Proof Required Later

The later worker implementation must prove:

- deterministic JSON ordering
- safe parsing of admitted project-inventory evidence only
- correct bucket assignment for same-day, recent, and stale deployments
- rejection of unsupported schemas and forbidden paths
- optional safe tmp-output writes only
- no authority widening into deploy or secret surfaces

## Marker Decision

No marker moves.

`Vercel Platform Observability Governance` remains `0%`.

Reason:

- admission alone is doctrine and scope control
- implementation proof is still required before any broader marker decision is honest

## Next

Open only this next packet:

```text
Vercel Platform Observability Governance deployment freshness inventory prompt-pack and worker handoff contract
```

That packet should freeze the exact worker prompt, schema details, and proof plan for the admitted helper/test pair without widening beyond the already admitted project-inventory evidence path.
