# Governed Artifact Epochs

This runbook defines how ATLAS keeps historical runtime truth visible without faking modern governed identity.

## Epoch Boundary

The registry-backed governed artifact epoch begins at **2026-04-14T08:06:53Z**.

That timestamp is the compatibility cutover used by root validation, Cortex world-model generation, and Playbook verify rules.

## Epoch Classes

### `legacy_pre_registry`

Use this class when all of the following are true:

- the artifact predates the cutover
- the artifact cannot truthfully satisfy the governed_v1 identity or closure contract
- the artifact remains historical evidence rather than a rewritten modern receipt

Legacy artifacts remain:

- visible in the world model
- queryable in awareness and status
- non-blocking for fields that did not exist yet

Legacy artifacts must still be surfaced as compatibility attention until they are backfilled or archived.

### `governed_v1`

Use this class for:

- artifacts created at or after the cutover
- older artifacts that already carry the governed_v1 identity and closure contract

Governed_v1 artifacts fail closed when required governed fields are missing or inconsistent.

## Required Governed_v1 Identity

Governed_v1 runtime artifacts must carry:

- `tool_id`
- optional `extension_id`
- `registry_digest`

Governed_v1 session manifests must also carry the observation-chain refs and closure evidence needed to make the flow visible end to end.

## Blocking Rules

- missing `tool_id` on governed_v1 is blocking
- missing `registry_digest` on governed_v1 is blocking
- mismatched `registry_digest` on governed_v1 is blocking
- missing required observation-chain evidence on governed_v1 is blocking
- missing closure evidence on governed_v1 is blocking
- missing legacy compatibility visibility is blocking

## Non-Blocking Rules

- a `legacy_pre_registry` artifact may be incomplete
- a `legacy_pre_registry` artifact may not be invisible
- legacy compatibility classification does not rewrite the original source artifact

## Provenance Rule

Epoch classification is derived from explicit timestamps and artifact shape, then published as compatibility state.

ATLAS does not mutate old receipts just to make them look governed_v1.
