# Sandbox Simulation Readiness Local-Only Artifact-Home And Scenario-Manifest Contract Freeze - 2026-06-27

- Date: `2026-06-27`
- Scope: `freeze the exact local-only sandbox runtime artifact home and scenario-manifest contract without admitting fixture execution, validator behavior, runner behavior, or any owner-repo, deploy, secret, or live-data widening`
- Lane: `Sandbox Simulation Readiness`
- Mode: `root-owned docs-only sandbox contract freeze`

## Objective

Clear the next exact Sandbox blocker by freezing one path-disciplined committed scenario-manifest home plus one path-disciplined generated runtime artifact home, then refresh the continuity and restart surfaces so the lane can reopen from durable contract truth instead of starter-only wording.

## Executed

1. Froze the committed scenario-manifest home at `data/atlas/sandbox/scenarios/<scenario_id>.json`.
2. Froze the generated local runtime artifact home at `runtime/atlas/sandbox/runs/<scenario_id>/<run_id>/`.
3. Froze the minimum scenario-manifest contract around stable identity, source references, future fixture references, artifact-home targeting, and explicit no-mutation guards.
4. Refreshed the maintained Sandbox continuity surfaces so the decisive receipt, marker posture, and exact next package all point at this contract-frozen state.

## Contract Freeze

### Placement

- committed scenario manifests belong only under `data/atlas/sandbox/scenarios/`
- generated sandbox run state belongs only under `runtime/atlas/sandbox/runs/`
- receipts about Sandbox lane movement stay under `docs/ops/`
- no machine-specific absolute paths become part of the contract
- no `tmp/`, owner-repo, deploy, secret, or live-system surface is admitted

### Scenario Manifest Contract

Every future Sandbox scenario manifest must be one root-relative JSON document at:

- `data/atlas/sandbox/scenarios/<scenario_id>.json`

Minimum frozen fields:

- `contract_version`
  - exact value: `atlas.sandbox.scenario.v1`
- `scenario_id`
  - stable root-owned identifier
  - doubles as the filename stem and the run-path segment; no separate slug mapping is admitted yet
- `title`
- `status`
  - exact admitted values: `draft` or `admitted`
- `purpose`
- `source_refs`
  - ATLAS-root-relative refs only
  - may cite only already-admitted `docs/**`, `data/**`, or `runtime/**` surfaces
- `fixture_refs`
  - may be empty now
  - if populated later, they may point only at a separately admitted future `data/atlas/sandbox/fixtures/**` contract
- `artifact_home`
  - must include `run_root`
  - `run_root` must stay under `runtime/atlas/sandbox/runs/<scenario_id>/<run_id>/`
- `guards`
  - exact current posture must remain:
    - `owner_repo_mutation: false`
    - `deploy_mutation: false`
    - `secret_use: false`
    - `live_data_mutation: false`
    - `_stack_execution: false`
- `non_goals`
  - must explicitly preserve the blocked mutation and execution classes for the scenario

### Run Artifact Home

This packet admits only one generated runtime descendant family:

- `runtime/atlas/sandbox/runs/<scenario_id>/<run_id>/`

That home is for future local-only run outputs only. This packet does not admit:

- a validator
- a runner
- a supervisor
- a fixture pack
- a writeback path
- a publish path
- any owner-repo mutation

## Ratchet Decision

`Sandbox Simulation Readiness` moves from `5%` to `8%`.

Why:

- the lane already had one honest starter packet
- the exact local-only artifact-home and scenario-manifest blocker is now cleared
- the lane now has one path-disciplined committed contract plus one path-disciplined generated runtime home instead of a future-home placeholder only

It stays low because:

- no scenario fixture pack exists yet
- no validator exists
- no runner exists
- no `_stack` command or owner-repo widening exists
- no proof-backed adoption exists

## Non-Claim

This does not prove:

- scenario fixture design
- validator behavior
- runner behavior
- `_stack` ownership
- owner-repo execution
- safe unattended simulation

## Exact Next Package

- `Sandbox Simulation Readiness local-only scenario-fixture pack contract freeze`

Why:

- the descriptor location and generated runtime home are now fixed
- the next honest question is the minimum durable fixture boundary for one future sandbox scenario
- validator, runner, `_stack`, and owner-repo execution claims remain premature until that fixture boundary exists
