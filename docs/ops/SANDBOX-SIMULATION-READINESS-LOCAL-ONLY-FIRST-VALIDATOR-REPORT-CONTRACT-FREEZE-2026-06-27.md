# Sandbox Simulation Readiness Local-Only First Validator-Report Contract Freeze - 2026-06-27

- Date: `2026-06-27`
- Scope: `freeze the exact local-only validator-report path and minimum report shape around the admitted Sandbox validator descriptor without admitting validator execution, runner behavior, or any owner-repo, deploy, secret, or live-data widening`
- Lane: `Sandbox Simulation Readiness`
- Mode: `root-owned docs-only validator-report contract freeze`

## Objective

Clear the next exact Sandbox blocker by freezing where one future validator report must land and what minimum non-executing fields it must carry before any generated validation artifact or validator behavior claim becomes honest.

## Executed

1. Froze the exact future validator-report path at `runtime/atlas/sandbox/runs/<scenario_id>/<run_id>/validation/report.json`.
2. Froze the minimum future validator-report contract around stable references, run identity, bounded result vocabulary, and observation payloads.
3. Preserved the rule that the validator report remains derivative of the admitted validator descriptor, scenario manifest, fixture-pack manifest, and cited leaf fixtures only.
4. Refreshed the maintained Sandbox continuity and restart surfaces so the exact next packet becomes one first validator-report stub admission under the frozen runtime validation home.

## Contract Freeze

### Placement

- future validator reports belong only at `runtime/atlas/sandbox/runs/<scenario_id>/<run_id>/validation/report.json`
- the report path must remain a descendant of the already frozen `validation_root`
- no validator report may be written under `data/`, `tmp/`, owner repos, deploy surfaces, secrets, or live-system state

### Validator-Report Contract

Every future Sandbox validator report must be one root-relative JSON document at:

- `runtime/atlas/sandbox/runs/<scenario_id>/<run_id>/validation/report.json`

Minimum frozen fields:

- `contract_version`
  - exact value: `atlas.sandbox.validation-report.v1`
- `validator_id`
- `scenario_id`
- `run_id`
- `validator_ref`
  - must point only at `data/atlas/sandbox/validators/<scenario_id>/validator.json`
- `result`
  - must include:
    - `status`
      - exact admitted values: `not_run`, `match`, `mismatch`, or `blocked`
    - `summary`
- `compared_fixture_ids`
  - array of fixture identifiers only
- `observations`
  - array of strings only

### Derivation Boundary

A future validator report may derive its contents only from:

1. the admitted validator descriptor
2. the paired scenario manifest
3. the paired fixture-pack manifest
4. the leaf fixtures explicitly listed by that pack

This packet does not admit:

- validator execution
- automatic run discovery
- mutation side effects
- owner-repo writes
- publish behavior
- `_stack` routing

## Ratchet Decision

`Sandbox Simulation Readiness` moves from `30%` to `33%`.

Why:

- the lane already had one admitted validator descriptor under a frozen local-only boundary
- the next exact ambiguity was the first validator-report path and minimum output shape
- one future validation artifact contract is now frozen without widening into execution

It stays low because:

- no validator-report artifact exists yet
- no validator execution exists
- no runner exists
- no `_stack` or owner-repo widening exists
- no proof-backed adoption exists

## Non-Claim

This does not prove:

- generated validator-report data
- validator behavior
- runner behavior
- `_stack` ownership
- owner-repo execution
- safe unattended simulation

## Exact Next Package

- `Sandbox Simulation Readiness local-only first validator-report stub admission`

Why:

- one future validator-report contract now exists
- the next honest move is one bounded non-executing validator-report stub under the frozen runtime validation home
- validator behavior, runner behavior, and wider execution claims remain premature
