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

Root-owned Atlas and Cortex exports may additionally carry the optional
`atlas.runtime-owner-export.readback.v1` projection. When present, semantic
validation binds it to the runtime-registry source revision and checks frozen
activation identity/order, selector derivation, marker counts, status
boundaries, and `discord_mutation_authorized=false`. Owner exports that do not
cite the runtime registry remain valid without this optional projection.

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
node packages/atlas-contracts/scripts/validate-artifact.mjs --schema atlas.projection-ack.v1 --artifact packages/atlas-contracts/fixtures/valid/projection-ack.v1.json --projection-delivery packages/atlas-contracts/fixtures/valid/projection-delivery.v1.json --json
```

`--json` emits one deterministic JSON result with `ok`, `code`, `schema`, `artifact`, and `errors`. ProjectionAck admission additionally requires `--projection-delivery`; the CLI validates the referenced delivery and rejects any identity or payload-digest mismatch. The supported exit codes are `0` (`VALID`), `1` (`INVALID_ARTIFACT`), `2` (unsupported, unknown, or invalid schema reference), `3` (`MALFORMED_JSON`), and `4` (`MISSING_INPUT`). Unsupported major versions use the stable `UNSUPPORTED_CONTRACT_VERSION` code. Schema resolution accepts only an identifier in the registered plan or an exact package-owned `schemas/<file>.schema.json` path; traversal segments and arbitrary filesystem schemas are rejected.

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

Atlas root owns schema semantics and validation behavior. Owner repositories produce or consume governed artifacts through this package and do not maintain validator copies. Clusters 1 through 6 prove `11/11` adoption for ComponentManifest, JobEnvelope, ContextPacket, ApprovalRecord, WorkerLease, EvidenceBundle, ExecutionReceipt, CardRecord, BoardEvent, MarkerEvidence, and KnowledgeCandidate through governed producer and independent consumer evidence. KnowledgeCandidate is admitted only to Playbook's review-candidate queue with exact identity and classified provenance, deterministic correlated receipts, byte-identical replay, deterministic two-candidate append behavior, and zero automatic doctrine promotion. See [the Cluster 1 adoption receipt](../../docs/ops/ATLAS-CONTRACTS-V2-CLUSTER-1-ADOPTION-2026-07-13.md), [the Cluster 2 adoption receipt](../../docs/ops/ATLAS-CONTRACTS-V2-CLUSTER-2-ADOPTION-2026-07-13.md), [the Cluster 3 WorkerLease adoption receipt](../../docs/ops/ATLAS-CONTRACTS-V2-CLUSTER-3-WORKERLEASE-ADOPTION-2026-07-15.md), [the Cluster 4 CardRecord and BoardEvent adoption receipt](../../docs/ops/ATLAS-CONTRACTS-V2-CLUSTER-4-CARDRECORD-BOARDEVENT-ADOPTION-2026-07-15.md), [the Cluster 5 MarkerEvidence adoption receipt](../../docs/ops/ATLAS-CONTRACTS-V2-CLUSTER-5-MARKEREVIDENCE-ADOPTION-2026-07-15.md), and [the Cluster 6 KnowledgeCandidate adoption receipt](../../docs/ops/ATLAS-CONTRACTS-V2-CLUSTER-6-KNOWLEDGECANDIDATE-ADOPTION-2026-07-15.md).

## Board authority v3 contract freeze

ATLAS-BOARD-000 adds an independent, additive board-authority family without changing or superseding any v2 file or adoption claim. The eight registered surfaces are `atlas.card-record.v3`, `atlas.card-event.v3`, `atlas.board-commit-receipt.v1`, `atlas.projection-delivery.v1`, `atlas.projection-ack.v1`, `atlas.board-authority-migration.v1`, `atlas.control-board-read-model.v1`, and `atlas.rollover-manifest.v1`.

These schemas freeze Atlas-local ledger authority, local atomic acceptance, asynchronous DiscordOS projection, generated Atlas Control read models, explicit UNKNOWN handling, one-time v2 baseline import, post-acceptance v3-only restore/replay rollback, and bounded epoch rollover. Schema registration is not runtime adoption: no database, outbox dispatcher, projection adapter, UI, supervisor, migration, or cutover is implemented by this package change. The architecture and activation gates are frozen in `docs/architecture/ADR-ATLAS-BOARD-AUTHORITY-V3.md`.
