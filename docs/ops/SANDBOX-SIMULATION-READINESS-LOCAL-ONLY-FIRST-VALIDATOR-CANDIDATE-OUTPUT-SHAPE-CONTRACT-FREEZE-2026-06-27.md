# Sandbox Simulation Readiness Local-Only First Validator-Candidate-Output Shape Contract Freeze - 2026-06-27

- Date: `2026-06-27`
- Scope: `freeze the exact local-only validator-candidate-output path and minimum projection shape that a future Sandbox validator may compare against the admitted oracle boundary without admitting validator execution, runner behavior, or any owner-repo, deploy, secret, or live-data widening`
- Lane: `Sandbox Simulation Readiness`
- Mode: `root-owned docs-only validator-candidate-output-shape contract freeze`

## Objective

Clear the next exact Sandbox blocker by freezing where one future local-only validator candidate-output artifact must live and what minimum projected shape it may carry before any candidate-output stub or validator behavior claim becomes honest.

## Executed

1. Froze the exact future validator-candidate-output path at `runtime/atlas/sandbox/runs/<scenario_id>/<run_id>/validation/candidate-output.json`.
2. Froze the minimum future candidate-output contract around stable references, run identity, bounded source identity, and one projection subtree aligned to the already admitted comparison boundary.
3. Preserved the rule that candidate-output remains derivative only of the admitted validator descriptor, input fixture context, and frozen expected-output comparison family, without admitting validator behavior.
4. Refreshed the maintained Sandbox continuity and restart surfaces so the exact next packet becomes one first validator-candidate-output stub admission under the frozen validation home.

## Candidate-Output Contract Freeze

### Placement

- future validator candidate-output artifacts belong only at `runtime/atlas/sandbox/runs/<scenario_id>/<run_id>/validation/candidate-output.json`
- the candidate-output path must remain a descendant of the already frozen `validation_root`
- no candidate-output artifact may be written under `data/`, `tmp/`, owner repos, deploy surfaces, secrets, or live-system state

### Validator-Candidate-Output Contract

Every future Sandbox validator candidate-output artifact must be one root-relative JSON document at:

- `runtime/atlas/sandbox/runs/<scenario_id>/<run_id>/validation/candidate-output.json`

Minimum frozen fields:

- `contract_version`
  - exact value: `atlas.sandbox.validator-candidate-output.v1`
- `validator_id`
- `scenario_id`
- `run_id`
- `validator_ref`
  - must point only at `data/atlas/sandbox/validators/<scenario_id>/validator.json`
- `source_input_fixture_id`
  - must name one admitted input fixture identifier only
- `oracle_ref`
  - must point only at `data/atlas/sandbox/fixtures/<scenario_id>/expected-output/<fixture>.json`
- `payload`
  - must include only:
    - `mode`
    - `status`
    - `observations`

### Projection Boundary

- `payload.mode` must remain a string-only candidate value for the already frozen `expected_output.payload.mode` boundary
- `payload.status` must remain a string-only candidate value for the already frozen `expected_output.payload.status` boundary
- `payload.observations` must remain an ordered string-list candidate value for the already frozen `expected_output.payload.observations` boundary
- no extra sibling fields under `payload` are admitted by this packet
- no comparison verdict, no status assignment, and no execution claim is admitted by candidate-output shape alone

### Derivation Guardrails

A future candidate-output artifact may derive its bounded shape only from:

1. the admitted validator descriptor
2. the admitted input fixture as contextual source material
3. the admitted expected-output fixture as oracle-boundary reference
4. the already frozen validator-comparison-boundary contract

This packet does not admit:

- validator execution
- candidate-output generation behavior
- automatic run discovery
- mutation side effects
- owner-repo writes
- publish behavior
- `_stack` routing

## Ratchet Decision

`Sandbox Simulation Readiness` moves from `42%` to `45%`.

Why:

- the lane already had one frozen validator-comparison boundary over the admitted oracle fields
- the next exact ambiguity was where a future local-only projected candidate-output artifact belongs and what minimum shape it may carry
- one future candidate-output contract is now frozen without widening into execution

It stays low because:

- no validator-candidate-output artifact exists yet
- no validator execution exists
- no runner exists
- no `_stack` or owner-repo widening exists
- no proof-backed adoption exists

## Non-Claim

This does not prove:

- generated candidate-output data
- validator behavior
- comparison correctness
- runner behavior
- `_stack` ownership
- owner-repo execution
- safe unattended simulation

## Exact Next Package

- `Sandbox Simulation Readiness local-only first validator-candidate-output stub admission`

Why:

- one future candidate-output contract now exists under the frozen validation home
- the next honest move is one bounded non-executing candidate-output stub aligned to the admitted comparison boundary
- validator behavior, runner behavior, and wider execution claims remain premature
