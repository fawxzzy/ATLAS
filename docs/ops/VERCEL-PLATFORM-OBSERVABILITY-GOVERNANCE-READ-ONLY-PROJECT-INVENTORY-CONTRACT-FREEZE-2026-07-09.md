# Vercel Platform Observability Governance Read-Only Project Inventory Contract Freeze

Date: 2026-07-09
Mode: root governance, read-only contract freeze
Status: completed

## Goal

Freeze the exact allowed read-only inventory contract for future Vercel observability packets so ATLAS can gather stable deployment and project truth without widening into env values, secret handling, or mutation-capable platform operations.

This packet does not:

- query Vercel again
- read env values
- read or print token values
- deploy, redeploy, promote, or roll back
- mutate Vercel settings
- mutate owner repos
- move markers

## Governing receipt

This contract freeze inherits from:

- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-CAPABILITY-AUDIT-2026-07-09.md`

That audit already proved:

- connector-visible Vercel read access
- ATLAS-visible authenticated access
- partial but real deployment/build/runtime observability
- mutation risk on the same auth path

This packet converts those findings into a strict inventory boundary.

## Contract purpose

Future Vercel observability work must separate two concerns:

1. inventory truth
2. operational capability

Inventory truth is allowed.
Operational mutation is not.

This packet freezes what future root-side helpers and receipts may read, record, and publish when the task is limited to project inventory and observability posture.

## Allowed inventory scopes

### 1. Team inventory

Allowed fields:

- team name
- team slug
- team id

Not allowed:

- membership details beyond what is already necessary for team identity
- billing state
- payment methods
- role/permission mutation

### 2. Project inventory

Allowed fields:

- project name
- project id
- ATLAS repo mapping
- framework
- node version
- root directory if exposed by a read-only surface
- canonical Vercel domains
- production branch if exposed by a read-only surface
- whether the project is in scope for ATLAS governance

Not allowed:

- env values
- secret values
- project-setting mutation
- domain mutation
- branch mutation

### 3. Deployment inventory

Allowed fields:

- deployment id
- deployment URL or hostname
- created timestamp
- ready/state value
- target (`production` or `preview`)
- commit SHA
- branch/ref
- creator identity if already visible in the read-only deployment surface
- inspector URL
- rollback-candidate status

Not allowed:

- triggering new deployments
- redeploy actions
- promote/rollback actions
- deleting deployments

### 4. Log and error inventory

Allowed fields:

- whether build logs are queryable
- whether runtime logs are queryable
- grouped runtime log counts
- grouped runtime error counts
- route names
- error labels
- error occurrence counts
- first-seen / last-seen timestamps
- affected deployment ids
- high-level sample error summaries when they contain no secrets

Not allowed:

- raw secret-bearing payload dumps
- full request bodies
- credential-bearing headers
- auth tokens
- env-derived secret values

### 5. Observability product posture inventory

Allowed fields:

- whether a surface is proven visible
- whether a surface is unproven
- whether a surface is forbidden in the current lane
- whether the capability is connector-visible, CLI-visible, or unknown

Example surfaces:

- build logs
- runtime logs
- runtime errors
- Web Analytics visibility
- Speed Insights visibility
- drains visibility
- alerts visibility
- env-name-only visibility

Not allowed:

- enabling any observability product
- changing any retention setting
- creating drains
- editing alerting

## Env-name-only boundary

Future inventory packets may record env names only if all of the following are true:

1. the packet explicitly names env-name-only intake as its scope
2. no values are printed, persisted, or paraphrased
3. the receipt stores names, targets, and type posture only
4. no secret-bearing diff, export, or API response is committed

Until that specific packet lands, env inventory remains outside the allowed read model.

## Forbidden surfaces

The following are forbidden in all inventory-only Vercel observability packets:

- env values
- token values
- secrets
- deployment creation
- redeploy
- rollback
- promotion
- alias mutation
- domain mutation
- project-setting mutation
- billing mutation
- team membership mutation
- webhooks mutation
- drains mutation

## Token visibility classes

Future receipts in this family may classify token posture only with bounded vocabulary:

- `vercel_observability_discordos_only`
- `vercel_observability_atlas_visible`
- `vercel_observability_connector_visible`
- `vercel_observability_partial`
- `vercel_observability_full_read_only`
- `vercel_observability_mutation_risk`
- `vercel_observability_unknown`

Rules:

- classify capability posture, not token contents
- never print token values
- never infer full-read-only unless env, deployment, and observability boundaries are all proven safely

## Team and project mapping model

Canonical mapping model for this family:

1. identify the Vercel team
2. identify visible projects under that team
3. map each visible project to an ATLAS repo when one exists
4. label each project as:
   - in-scope governed repo
   - inventory-only governed repo
   - adjacent owner-lane surface
   - unknown mapping

For the current family, the audited mapping starts from:

- `fawxzzy-discordos` -> `repos/DiscordOS`
- `fawxzzy-fitness` -> `repos/fawxzzy-fitness`
- `fawxzzy-mazer` -> `repos/mazer`
- `fawxzzy-trove` -> `repos/trove`
- `fawxzzy-foundation` -> `repos/foundation`

This mapping is read-model truth, not owner-lane admission.

## Fitness webhook observation boundary

The Fitness runtime error cluster recorded in the audit remains admissible only as an observability observation:

- route: `/api/billing/webhook/stripe`
- grouped occurrences and time window
- affected deployment reference

It does not automatically open a Fitness fix packet.

If future work needs to debug or fix that error:

- route it as explicit owner-lane work
- do not smuggle it through root observability governance

## Receipt publication rules

A future project-inventory receipt in this family may publish:

- inventory tables
- posture classes
- repo mappings
- deployment freshness summaries
- read-only log-surface availability
- grouped runtime error observations

It may not publish:

- env values
- secret values
- raw credentials
- owner-side implementation recommendations presented as completed root truth

## Future helper contract

If implementation is admitted later, the expected helper surface is:

- `ops/atlas/vercel_observability_project_inventory.py`

Expected test surface:

- `tests/test_atlas_vercel_observability_project_inventory.py`

Required helper behavior:

- consume only read-only Vercel surfaces
- emit structured inventory output
- keep env values out of output
- label unknown surfaces explicitly
- preserve team/project/repo mapping separation
- preserve token-visibility classification without secret disclosure

## Non-goals

- no live helper implementation in this packet
- no new validator in this packet
- no marker ratchet
- no owner-lane routing beyond observation boundaries

## Exact next packet

`Vercel Platform Observability Governance read-only project inventory first-implementation admission`

Why this is next:

- the inventory contract is now frozen
- the next smallest honest move is to admit one bounded helper and one focused test
- broader log/error/env-name automation should wait until this inventory helper contract is proven first

## Completion

Completion: `100%` for the contract freeze packet itself.

No Vercel mutation was performed.
No owner repo was mutated.
No env values or token values were read or committed.
