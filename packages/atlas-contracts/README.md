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

These v2 families remain implementation foundations rather than completed mesh units until governed producer and consumer adoption proof exists.

## Package Surface

Schemas:

- `atlas.env.v1`
- `atlas.app-registration.v1`
- `atlas.health.v1`
- `atlas.event.v1`
- `atlas.receipt.v1`
- `atlas.component-manifest.v2`
- `atlas.job-envelope.v2`
- `atlas.execution-receipt.v2`

Exports:

- `src/constants.ts` for version ids, enums, and schema path maps
- package export paths for each schema JSON file

## Compatibility

This package does not delete or replace the existing schema lanes under:

- `schemas/`
- `ops/events/schemas/`

Instead, it defines the first importable v1 platform surface and keeps compatibility notes in `docs/architecture/atlas-platform-v1.md`.

## Validation

Run:

```powershell
node packages/atlas-contracts/scripts/validate-contracts.mjs
```

The validator checks all bundled valid fixtures and bundled invalid fixtures against the v1 schemas.
