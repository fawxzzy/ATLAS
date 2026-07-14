# Cortex Simulation Substrate Readiness ATLAS Receipt Workflow And Failure-Mode Replay Contract Freeze

- Date: `2026-07-14`
- Lane: `Cortex Simulation Substrate Readiness`
- Mode: `ATLAS-root receipt-replay contract freeze`
- Scope: `freeze deterministic advisory workflow and failure-mode replay from admitted ATLAS receipt contracts`
- Opening checkpoint: `main@64db605e`
- Marker movement: none

## Decision

The first receipt replay surface must consume existing ATLAS receipt contracts rather than define a competing receipt envelope.

Admitted receipt contracts are:

- `atlas.receipt.v1`
- `atlas.execution-receipt.v2`

Their canonical schemas remain owned by `packages/atlas-contracts/schemas/`.

## Replay Manifest

One explicit replay manifest uses contract version `atlas.cortex.simulation.receipt-replay-manifest.v1` and contains:

- stable scenario and agent IDs
- fixed `generated_at`
- an advisory objective
- one or more receipt inputs
- exact root-relative source references
- exact `sha256:` source-byte digests
- explicit source trust classes

Admitted trust classes are:

- `atlas_runtime_receipt`
- `committed_replay_fixture`
- `contract_fixture`

`contract_fixture` is proof-only. A replay made solely from contract fixtures cannot satisfy the 50% marker threshold.

## Admitted Paths

Replay manifests are admitted only under:

```text
data/cortex/simulation-replays/**.json
```

Receipt inputs are admitted only under:

```text
runtime/receipts/**.json
data/cortex/simulation-replays/**.json
packages/atlas-contracts/fixtures/valid/**.json
```

Absolute paths, traversal, secrets, owner repositories, hidden transcripts, browser state, and arbitrary local files are denied.

## Validation And Provenance

Before replay, the helper must:

1. read each source exactly once
2. verify the declared raw-byte SHA-256 digest
3. parse one JSON object
4. validate the admitted contract version
5. validate required fields, status vocabulary, and execution-receipt verification entries
6. reject duplicate receipt IDs
7. preserve receipt ID, contract version, source ref, source digest, recorded time, status, and summary-only evidence

Unknown contract versions, malformed receipts, digest mismatches, duplicate IDs, missing chronology, and unsupported statuses are blockers.

## Deterministic Chronology

Replay order is:

```text
recorded_at ascending
then receipt_id ascending
then source_ref ascending
```

Manifest order cannot override receipt chronology. Identical admitted source bytes and manifest bytes must produce identical output bytes.

## Failure-Mode Classification

The helper classifies receipt observations without changing their source status:

- `success`: `accepted`, `passed`, or `succeeded`
- `advisory`: `warning`, `skipped`, `awaiting-review`, or `partial`
- `failure`: `rejected`, `failed`, or failed verification
- `blocked`: `blocked`, `cancelled`, or blocked verification

Each transition cites the source receipt. The replay may derive an advisory failure-mode summary, but it may not claim a new execution result, final receipt, approval, or completion.

## Output Contract

The implementation will emit `atlas.cortex.simulation.receipt-replay.v1` with:

- stable replay ID
- ordered receipt observations
- deterministic workflow transitions
- failure-mode counts and cited source receipts
- schema-valid advisory agent state
- warnings and blockers
- an authority object permanently denying execution, dispatch, mutation, deployment, publication, board writes, final receipts, approvals, and marker movement

Optional output is admitted only under `tmp/atlas/**.json`. No default output path is allowed.

## Proof Matrix

Implementation proof must cover:

1. both admitted receipt contracts
2. raw-byte digest verification
3. deterministic chronology and output
4. duplicate receipt-ID rejection
5. malformed and unknown contract rejection
6. status and verification failure classification
7. absolute, traversal, secret, owner, and hidden-context path rejection
8. explicit safe output only
9. no output write when omitted
10. top-level and nested execution denial
11. no model, network, subprocess, owner, platform, Discord, board, deploy, or live-action call
12. a mixed success/failure replay using at least one non-contract-fixture receipt source before the 50% marker moves

## Marker Decision

`Cortex Simulation Substrate Readiness` remains at `40%`.

This packet freezes the honest 50% boundary but does not implement or execute replay.

## Exact Next Packet

```text
Cortex Simulation Substrate Readiness ATLAS receipt workflow and failure-mode replay first-implementation admission
```

## Reusable Governance

**RULE - Replay never rewrites receipt truth.** Derived transitions and failure summaries cite source receipts and remain advisory.

**PATTERN - Digest-bound chronological replay.** Freeze source bytes, validate the existing contract, order deterministically, and derive only authority-false state.

**FAILURE MODE - Fixture-only threshold inflation.** Contract fixtures prove parser behavior but are presented as operational receipt replay.

## Completion

The receipt workflow and failure-mode replay contract is frozen. No receipt was executed, rewritten, published, or used to authorize action.
