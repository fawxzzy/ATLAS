# `@atlas/contracts`

`@atlas/contracts` is the Wave 1 import surface for ATLAS platform contracts.

It freezes the minimum cross-repo contract set before any shared auth package work:

- env contracts
- app registration contracts
- health contracts
- event envelopes
- receipts

## Purpose

ATLAS root owns versioned platform contracts. Owner repos own implementation.

This package gives app repos a stable, machine-validated surface to conform to without moving app logic, auth flows, or deployment behavior into the ATLAS root.

The first Contracts v2 implementation cluster also provides schema, export, and fixture foundations for:

- `atlas.component-manifest.v2`
- `atlas.job-envelope.v2`
- `atlas.execution-receipt.v2`
- `atlas.context-packet.v2`
- `atlas.evidence-bundle.v2`
- `atlas.approval-record.v2`
- `atlas.worker-lease.v2`
- `atlas.card-record.v2`
- `atlas.board-event.v2`
- `atlas.marker-evidence.v2`
- `atlas.knowledge-candidate.v2`

These v2 families remain implementation foundations rather than completed mesh units until governed producer and consumer adoption proof exists.

The package also carries the canonical GitHub projection seam contracts:

- `atlas.github.event-receipt.v1`
- `atlas.github.event-admission.v1`
- `atlas.github.projection-intent.v1`

These GitHub contracts are backend-neutral interoperability seams for `_stack -> Atlas -> DiscordOS`. They are not counted inside the eleven-family Atlas Contracts v2 mesh denominator.

The package also owns `atlas.project-board.owner-export.v1`, the deterministic
owner-repository-to-Atlas board admission envelope. Each export embeds exact
`atlas.card-record.v2` records, source provenance, planning content, stable
idempotency keys, and duplicate/supersession relationships. Semantic validation
adds cross-record checks that JSON Schema alone cannot express: unique identity,
project/board/source correlation, portable relative paths, relationship rules,
and the requirement that a `ready` card has an objective, acceptance criteria,
and no blockers. This seam is outside the eleven-family v2 mesh denominator.

## Package Surface

Schemas:

- `atlas.env.v1`
- `atlas.app-registration.v1`
- `atlas.health.v1`
- `atlas.event.v1`
- `atlas.receipt.v1`
- `atlas.github.event-receipt.v1`
- `atlas.github.event-admission.v1`
- `atlas.github.projection-intent.v1`
- `atlas.project-board.owner-export.v1`
- `atlas.component-manifest.v2`
- `atlas.job-envelope.v2`
- `atlas.execution-receipt.v2`
- `atlas.context-packet.v2`
- `atlas.evidence-bundle.v2`
- `atlas.approval-record.v2`
- `atlas.worker-lease.v2`
- `atlas.card-record.v2`
- `atlas.board-event.v2`
- `atlas.marker-evidence.v2`
- `atlas.knowledge-candidate.v2`

Exports:

- `src/constants.ts` for version ids, enums, and schema path maps
- package export paths for each schema JSON file

## GitHub Projection Seam

These three contracts freeze the backend-neutral boundary between normalized GitHub observations and any later Discord-facing application:

```text
_stack normalized GitHub facts
-> atlas.github.event-receipt.v1
-> Atlas admission and deduplication
-> atlas.github.event-admission.v1
-> zero or more atlas.github.projection-intent.v1 records
-> DiscordOS single writer
```

Boundary rules:

- `_stack` is the immutable GitHub fact producer and does not call Discord.
- Atlas owns admission, deduplication, durable correlation, backend-neutral ledger meaning, and intent production.
- DiscordOS owns final wording, route-specific presentation, idempotent application, and readback.
- `external_mutation` remains denied in all three contracts until a separately authorized consumer action exists.
- Event receipts preserve deterministic `ghr_` event identities and `ghk_` idempotency keys from `_stack`.
- Atlas admission adds deterministic `gha_` and `ghak_` identities without rewriting owner-repository truth.
- Projection intents add deterministic `ghp_` and `ghpk_` identities for formatting-free downstream application.

Planned migrations:

1. `_stack` later replaces its repo-local receipt schema authority with `atlas.github.event-receipt.v1`.
2. Atlas later persists `atlas.github.event-admission.v1` and `atlas.github.projection-intent.v1` into its chosen ledger implementation without changing contract meaning.
3. DiscordOS later proves consumer-side application, publication/readback receipts, and single-writer behavior against these contracts.

## Compatibility

This package does not delete or replace the existing schema lanes under:

- `schemas/`
- `ops/events/schemas/`

Instead, it defines the first importable v1 platform surface and keeps compatibility notes in `docs/architecture/atlas-platform-v1.md`.

## Validation

Run:

```powershell
npm --prefix packages/atlas-contracts run validate
```

This runs the bundled valid/invalid fixture suite and the artifact-validator CLI suite. The fixture validator and the artifact CLI both use the exported `@atlas/contracts/validator` engine.

### Artifact CLI

Validate an arbitrary JSON artifact against a registered contract identifier or an exact schema file owned by this package:

```powershell
node packages/atlas-contracts/scripts/validate-artifact.mjs --schema atlas.env.v1 --artifact C:\work\env.json
node packages/atlas-contracts/scripts/validate-artifact.mjs --schema schemas/atlas.component-manifest.v2.schema.json --artifact C:\work\component.json --json
node packages/atlas-contracts/scripts/validate-artifact.mjs --schema atlas.github.event-receipt.v1 --artifact packages/atlas-contracts/fixtures/valid/github.event-receipt.v1.json --json
node packages/atlas-contracts/scripts/validate-artifact.mjs --schema atlas.project-board.owner-export.v1 --artifact packages/atlas-contracts/fixtures/valid/project-board.owner-export.v1.json --json
```

`--json` emits one deterministic JSON result with `ok`, `code`, `schema`, `artifact`, and `errors`. The supported exit codes are `0` (`VALID`), `1` (`INVALID_ARTIFACT`), `2` (unsupported, unknown, or invalid schema reference), `3` (`MALFORMED_JSON`), and `4` (`MISSING_INPUT`). Unsupported major versions use the stable `UNSUPPORTED_CONTRACT_VERSION` code. Schema resolution accepts only an identifier in the registered plan or an exact package-owned `schemas/<file>.schema.json` path; traversal segments and arbitrary filesystem schemas are rejected.

### Programmatic use

```js
import {
  loadJson,
  loadKnownSchema,
  validateJsonSchema,
} from "@atlas/contracts/validator";

const loaded = await loadKnownSchema("atlas.env.v1");
const artifact = await loadJson("C:/work/env.json");
const errors = loaded.ok ? validateJsonSchema(artifact, loaded.schema) : [loaded.error];
```

`loadJson` is for caller-owned JSON artifacts. `loadKnownSchema` is deliberately restricted to the Atlas registered schema plan, so owner repositories must invoke this validator instead of copying its engine or loading their own schema paths. The current supported majors are v1 and v2; additions must be registered here before they become callable.

## Producer/consumer boundary

Atlas root owns schema semantics and validation behavior. Owner repositories produce or consume governed artifacts through this package and do not maintain validator copies. Clusters 1 through 4 prove `9/11` adoption for ComponentManifest, JobEnvelope, ContextPacket, ApprovalRecord, WorkerLease, EvidenceBundle, ExecutionReceipt, CardRecord, and BoardEvent through governed producer and independent consumer evidence. The two remaining families are MarkerEvidence and KnowledgeCandidate. See [the Cluster 1 adoption receipt](../../docs/ops/ATLAS-CONTRACTS-V2-CLUSTER-1-ADOPTION-2026-07-13.md), [the Cluster 2 adoption receipt](../../docs/ops/ATLAS-CONTRACTS-V2-CLUSTER-2-ADOPTION-2026-07-13.md), [the Cluster 3 WorkerLease adoption receipt](../../docs/ops/ATLAS-CONTRACTS-V2-CLUSTER-3-WORKERLEASE-ADOPTION-2026-07-15.md), and [the Cluster 4 CardRecord and BoardEvent adoption receipt](../../docs/ops/ATLAS-CONTRACTS-V2-CLUSTER-4-CARDRECORD-BOARDEVENT-ADOPTION-2026-07-15.md).
