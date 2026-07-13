# Atlas Contracts v2 Artifact Validator Foundation - 2026-07-13

## Implementation receipt

Atlas Contracts now owns one reusable deterministic JSON Schema validation engine at `packages/atlas-contracts/scripts/lib/validate-json-schema.mjs`. The bundled fixture suite and `validate-artifact.mjs` both consume that engine and the same registered sixteen-schema plan (five v1 families plus eleven v2 foundations).

The artifact CLI accepts a registered identifier or exact package-owned schema file plus a caller-owned artifact JSON path. It emits stable JSON result fields (`ok`, `code`, `schema`, `artifact`, `errors`) when invoked with `--json`, returns documented deterministic exit codes, rejects traversal, and returns `UNSUPPORTED_CONTRACT_VERSION` for an unknown major.

## Boundary and state

- Atlas root owns schema semantics and validator behavior.
- Owner repositories invoke the Atlas-owned validator; they do not copy a validator engine or load arbitrary schema paths.
- No owner repository, board, marker, or producer/consumer integration changed in this task.
- The contracts mesh remains `0/11` until governed producer and consumer proof lands.

## Verification

- `node packages/atlas-contracts/scripts/validate-contracts.mjs`
- `npm --prefix packages/atlas-contracts run test:artifact-validator`
- `npm --prefix packages/atlas-contracts run validate`

## Next serialized task

Restart `_stack` producer adoption using the Atlas-owned artifact validator.
