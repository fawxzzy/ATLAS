# Sandbox Simulation Readiness Local-Only First Validator-Boundary Contract Freeze - 2026-06-27

- Date: `2026-06-27`
- Scope: `freeze one future local-only validator descriptor home plus one read-only validator boundary over the admitted Sandbox example root without admitting validator execution, runner behavior, or any owner-repo, deploy, secret, or live-data widening`
- Lane: `Sandbox Simulation Readiness`
- Mode: `root-owned docs-only validator-boundary contract freeze`

## Objective

Clear the next exact Sandbox blocker by freezing where one future local-only validator descriptor may live, exactly which admitted Sandbox surfaces it may read, and which runtime validation artifact home it may target before any validator implementation or execution claim becomes honest.

## Executed

1. Froze one future committed validator descriptor home at `data/atlas/sandbox/validators/<scenario_id>/validator.json`.
2. Froze the rule that a future local-only validator may read only the paired scenario manifest, the paired fixture-pack manifest, and the leaf fixtures explicitly listed by that pack.
3. Froze one future generated validation artifact home at `runtime/atlas/sandbox/runs/<scenario_id>/<run_id>/validation/`.
4. Refreshed the maintained Sandbox continuity and restart surfaces so the exact next packet becomes one first validator-descriptor stub admission under the frozen boundary.

## Contract Freeze

### Placement

- committed Sandbox validator descriptors belong only under `data/atlas/sandbox/validators/`
- one future validator root per scenario is admitted at `data/atlas/sandbox/validators/<scenario_id>/`
- one future validator descriptor per scenario is admitted at `data/atlas/sandbox/validators/<scenario_id>/validator.json`
- generated validation artifacts belong only under `runtime/atlas/sandbox/runs/<scenario_id>/<run_id>/validation/`
- no validator descriptor or validation artifact path may escape into `tmp/`, owner repos, deploy surfaces, secrets, or live-system state

### Validator Descriptor Contract

Every future Sandbox validator descriptor must be one root-relative JSON document at:

- `data/atlas/sandbox/validators/<scenario_id>/validator.json`

Minimum frozen fields:

- `contract_version`
  - exact value: `atlas.sandbox.validator.v1`
- `validator_id`
  - stable root-owned identifier
- `scenario_id`
  - must match the parent directory name and the paired scenario-manifest identifier
- `status`
  - exact admitted values: `draft` or `admitted`
- `purpose`
- `reads`
  - must include:
    - `scenario_ref`
    - `fixture_pack_ref`
    - `allowed_kinds`
- `artifact_home`
  - must include `validation_root`
  - `validation_root` must stay under `runtime/atlas/sandbox/runs/<scenario_id>/<run_id>/validation/`
- `guards`
  - exact current posture must remain:
    - `owner_repo_mutation: false`
    - `deploy_mutation: false`
    - `secret_use: false`
    - `live_data_mutation: false`
    - `_stack_execution: false`
- `non_goals`
  - must explicitly preserve the blocked execution and mutation classes for the validator

### Read Boundary

A future local-only validator may read only:

1. `data/atlas/sandbox/scenarios/<scenario_id>.json`
2. `data/atlas/sandbox/fixtures/<scenario_id>/fixture-pack.json`
3. the exact leaf fixture payloads listed in `items[*].path` inside that paired pack

A future local-only validator may not:

- crawl sibling scenario roots
- discover arbitrary descendants under `data/atlas/sandbox/fixtures/**`
- consume generated runtime state outside its own future `validation_root`
- read owner-repo files, secrets, network resources, or live-system state
- mutate any committed or runtime surface as part of this contract alone

### Runtime Validation Artifact Home

This packet admits only one future generated validation-artifact descendant family:

- `runtime/atlas/sandbox/runs/<scenario_id>/<run_id>/validation/`

That home is reserved for future local-only validation outputs only. This packet does not admit:

- validator execution
- a validation report schema
- a runner
- a supervisor
- a writeback path
- a publish path
- any owner-repo mutation

## Ratchet Decision

`Sandbox Simulation Readiness` moves from `24%` to `27%`.

Why:

- the lane already had one concrete local-only note/input/expected-output example root
- the next exact ambiguity was the first validator boundary over that admitted root
- one future validator home, read boundary, and runtime validation home are now frozen without widening into execution

It stays low because:

- no validator descriptor exists yet
- no validation report contract exists yet
- no validator implementation exists
- no runner exists
- no `_stack` or owner-repo widening exists
- no proof-backed adoption exists

## Non-Claim

This does not prove:

- validator descriptor data
- validation report data
- validator behavior
- runner behavior
- `_stack` ownership
- owner-repo execution
- safe unattended simulation

## Exact Next Package

- `Sandbox Simulation Readiness local-only first validator-descriptor stub admission`

Why:

- one future validator home and read boundary are now fixed
- the next honest move is one committed non-executing validator descriptor stub under that frozen contract
- validation report shape, validator behavior, runner behavior, and wider execution claims remain premature
