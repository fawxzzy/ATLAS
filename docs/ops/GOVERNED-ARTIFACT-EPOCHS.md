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

Legacy visibility is carried by descriptor-backed backfill records, not by mutating the original artifacts.

### `governed_v1`

Use this class for:

- artifacts created at or after the cutover
- older artifacts that already carry the governed_v1 identity and closure contract

Governed_v1 artifacts fail closed when required governed fields are missing or inconsistent.

Post-cutover execution-receipt repair also stays inside `governed_v1`. Truthful repair emits a new superseding receipt; it does not downgrade the failure into `legacy_pre_registry`.

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
- missing descriptor-backed legacy backfill visibility for `legacy_pre_registry` history is blocking
- missing truthful repair metadata on a superseding governed_v1 execution receipt is blocking

## Non-Blocking Rules

- a `legacy_pre_registry` artifact may be incomplete
- a `legacy_pre_registry` artifact may not be invisible
- legacy compatibility classification does not rewrite the original source artifact
- legacy backfill may record `unknown_legacy` or `conflict_legacy` when governed identity cannot be proven
- original governed_v1 receipts may remain visible after supersession, but they are no longer the preferred current-state artifact

## Supersession Rule

Receipt supersession is allowed only for post-cutover governed execution receipts and only when truthful reconstruction is possible.

The superseding receipt becomes the preferred current-state artifact when it includes:

- `supersedes_receipt_ref`
- `repair_basis_refs`
- `reconciled_at`
- `reconciled_by_tool_version`
- a valid current `registry_digest`

The original receipt remains immutable evidence.

## Residue Rule

Historical artifact retention is broader than epoch compatibility.

An artifact may be:

- `legacy_pre_registry` because it predates the governed cutover
- retained residue because it is still visible history but not canonical current state

Retention never permits silent invisibility, silent mutation, or multiple competing current artifacts.

## Backfill Rule

Historical compatibility is published through dedicated backfill records under `runtime/state/atlas/legacy-backfill/`.

Those records:

- keep source evidence immutable
- record provenance and inference basis
- register descriptor surfaces into the root world model
- allow awareness and status to query historical sessions without pretending they were minted as `governed_v1`

## Provenance Rule

Epoch classification is derived from explicit timestamps and artifact shape, then published as compatibility state.

ATLAS does not mutate old receipts just to make them look governed_v1.
