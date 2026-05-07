# Repo Class Admission Rules

## Purpose

These rules define how ATLAS admits and routes repo-owned surfaces without turning the root into an umbrella source repo.

Repo class defines what a repo is. Status defines how far it has progressed.

## Repo Classes

Current Wave 1 classes:

- `stack`
- `application`
- `governance-runtime`
- `local-operator`
- `workflow-operator`
- `demo`
- `incubating`
- `legacy`
- `archive`
- `quarantined`

Operational status lanes commonly used with those classes:

- `active`
- `managed`
- `unmanaged`
- `verified`
- `incubating`
- `demo`
- `legacy`
- `archived`
- `quarantined`

## Minimum Files By Class

### Active and managed repos

Required:

- `AGENTS.md`
- `README.md`
- `.codex/config.toml`
- one documented validation entrypoint
- adopted `atlas-contracts` surfaces when the repo is platform-admitted

Exception:

- ATLAS root uses `README-STACK.md` and does not require `.codex/config.toml`

### Incubating repos

Required:

- `AGENTS.md` or an explicit documented exception
- `README.md`
- one documented validation entrypoint, even if minimal
- an app registration contract before promotion to managed or verified

### Demo repos

Required:

- `README.md`
- one documented validation entrypoint
- explicit scope notes that the repo is not a default platform reference

### Legacy repos

Required:

- `README.md`
- explicit maintenance and support posture
- documented reason for non-adoption or partial adoption of current contracts

### Archived repos

Required:

- archive status marker in registry or repo docs
- no implied active ownership
- no new admission claims without explicit reactivation

### Quarantined repos

Required:

- explicit quarantine status
- no promotion
- no reuse as a contract reference until cleared

## Validation Entrypoints

Each admitted repo must expose at least one documented validation entrypoint.

Preferred naming:

- `verify`
- `verify:strict` when a stricter mode exists

Minimum expectation by class:

- `application`: contract check plus repo verify
- `governance-runtime`: contract check plus runtime verification
- `local-operator`: contract check plus execution and receipt verification
- `workflow-operator`: contract check plus workflow verification
- `demo`: lightweight verify is acceptable
- `incubating`: minimal verify is acceptable until promotion

## Contract Conformance

Wave 1 contract conformance means the owner repo can supply or generate:

- `atlas.app-registration.v1`
- `atlas.env.v1`
- `atlas.health.v1`
- `atlas.event.v1` when it emits platform-visible events
- `atlas.receipt.v1` when it emits platform-visible receipts

Read-only or front-door surfaces may declare narrower use:

- no auth
- no privileged DAL
- no event sink beyond build or publish receipts

Those exceptions must be explicit in repo docs and registration metadata.

## Promotion And Demotion Rules

Promotion into a stronger status requires evidence, not intent.

Promotion from `incubating` to `managed` requires:

- required files present
- documented validation entrypoint
- app registration contract present
- owner-repo routing is explicit

Promotion from `managed` to `verified` requires:

- contract checks passing
- repo-local verify passing
- evidence receipts or verification artifacts recorded in the owner surface

Demotion to `legacy`, `archived`, or `quarantined` should happen when:

- the owner no longer maintains the surface
- contract drift becomes intentional and accepted
- security or trust posture blocks normal promotion

## Cortex Promotion Block

`cortex` remains blocked from promotion in Wave 1.

Rules:

- do not mark Cortex promoted or verified from the root contract PR
- do not move Cortex runtime ownership away from `runtime/cortex/**`
- do not treat `repos/cortex` as active runtime truth

Cortex promotion requires explicit criteria and evidence in a later owner-surface lane.

## Owner-Repo Routing Rules

ATLAS root may define:

- contracts
- workflows
- doctrine
- compatibility notes

ATLAS root may not perform app implementation work that belongs to an owner repo.

Route work by owner:

- root contract and admission work stays in ATLAS root
- app auth, DAL, deploy, and runtime changes stay in the owning repo
- cross-repo work must name the participating repos and keep edits inside those surfaces only

This keeps the federation model intact: one platform contract, many owner repos.
