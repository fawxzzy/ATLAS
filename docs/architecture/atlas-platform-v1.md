# ATLAS Platform v1

## Purpose

ATLAS platform v1 freezes the first importable contract surface for app repos and platform repos.

The purpose is narrow:

- define stable machine-validated contracts at the ATLAS root
- let owner repos adopt those contracts without moving implementation truth into root
- give later packages, including auth, a stable boundary to target

The v1 import surface is `packages/atlas-contracts/`.

## Why Contracts Precede Auth

`atlas-contracts` must land before `atlas-auth`.

Reason:

- auth depends on environment shape
- auth depends on app registration and owner-repo routing
- auth emits health, events, and receipts
- auth migration work in `fitness` will otherwise encode unstable repo-local assumptions into a shared package

Rule:

- contracts freeze before auth packages

Pattern:

- ATLAS root owns versioned platform contracts
- owner repos own implementation

Failure mode:

- building `atlas-auth` first bakes Fitness-specific session and env assumptions into the shared package and forces rework when event, health, receipt, and registration semantics are later normalized

## Platform Surface

Wave 1 includes five contract families:

- `atlas.env.v1`
- `atlas.app-registration.v1`
- `atlas.health.v1`
- `atlas.event.v1`
- `atlas.receipt.v1`

Those contracts define the minimum platform boundary needed for app admission and later package work.

## Relationship To Existing Schemas And Event Docs

Wave 1 does not delete, move, or replace the existing schema lanes under:

- `schemas/`
- `ops/events/schemas/`

Compatibility posture:

- existing root schemas remain valid as their current source-of-truth surfaces
- existing lifecycle event payload schemas remain the executable contract for the current event lane
- `packages/atlas-contracts` becomes the importable platform surface that app repos can adopt directly

The event contract remains anchored by `docs/architecture/ATLAS-EVENT-CONTRACT.md`. `atlas.event.v1` aligns with that document by preserving the shared lifecycle envelope fields while widening the platform boundary to admit repo-owned application events.

## Root And App Boundary

ATLAS root owns:

- versioned schemas
- shared workflow contracts
- admission doctrine
- compatibility notes

Owner repos own:

- auth implementation
- data access implementation
- deployment configuration
- app-specific event payloads
- app-specific receipts and health production

Root sessions should define the contracts. Owner-repo sessions should implement the behavior.

## Versioning Rules

Versioning is explicit and boring.

- each schema has a contract id such as `atlas.health.v1`
- breaking changes require a new contract version
- additive notes and non-breaking docs updates do not create a new version
- owner repos should pin to explicit contract versions
- do not silently mutate v1 semantics after adoption begins

## Adoption Sequence

Adopt in this order:

1. ATLAS root freezes `atlas-contracts`, reusable workflow, and admission rules.
2. `fitness` adopts the contracts, then performs auth and DAL migration work.
3. `trove` adopts the contracts, then replaces hardcoded catalog assumptions with generated inputs.
4. `mazer` adopts the contracts, then aligns observability envelopes and receipts.
5. `cortex` stays admission-only until explicit promotion evidence exists.

## Out Of Scope

Wave 1 explicitly does not include:

- `atlas-auth`
- shared DAL implementation
- shared UI packages
- app repo implementation edits
- repo moves or renames
- migration of existing root schema lanes
- Cortex runtime promotion

## Package Contents

The v1 package is intentionally small:

- schema JSON files
- typed constants
- example valid and invalid fixtures
- a validation script that exercises each schema

That keeps the contract surface importable, reviewable, and independent from any single app framework or vendor SDK.
