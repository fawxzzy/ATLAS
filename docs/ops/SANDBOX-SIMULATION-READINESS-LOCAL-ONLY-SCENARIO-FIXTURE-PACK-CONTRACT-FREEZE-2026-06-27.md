# Sandbox Simulation Readiness Local-Only Scenario-Fixture Pack Contract Freeze - 2026-06-27

- Date: `2026-06-27`
- Scope: `freeze the exact committed Sandbox fixture-pack home and manifest-reference discipline without admitting example fixture payloads, validator behavior, runner behavior, or any owner-repo, deploy, secret, or live-data widening`
- Lane: `Sandbox Simulation Readiness`
- Mode: `root-owned docs-only fixture-pack contract freeze`

## Objective

Clear the next exact Sandbox blocker by freezing one path-disciplined committed fixture-pack home, one minimum fixture-pack manifest shape, and one scenario-manifest reference rule so future Sandbox inputs can become durable without widening into execution behavior.

## Executed

1. Froze the committed Sandbox fixture-pack home at `data/atlas/sandbox/fixtures/<scenario_id>/`.
2. Froze the pack-manifest home at `data/atlas/sandbox/fixtures/<scenario_id>/fixture-pack.json`.
3. Froze the rule that scenario manifests may cite only the pack manifest, not leaf fixture payloads directly.
4. Refreshed the maintained Sandbox continuity and restart surfaces so the exact next packet moves from fixture-boundary doctrine to one example scenario-plus-pack stub follow-on.

## Contract Freeze

### Placement

- Sandbox-specific committed fixtures belong only under `data/atlas/sandbox/fixtures/`
- the generic cross-lane fixture library under `data/fixtures/**` remains historical shared fixture truth and is not the home for Sandbox lane-specific committed fixture packs
- one future fixture pack root per scenario is admitted at `data/atlas/sandbox/fixtures/<scenario_id>/`
- one future pack manifest per scenario is admitted at `data/atlas/sandbox/fixtures/<scenario_id>/fixture-pack.json`
- future leaf fixture payloads, if later admitted, must stay under the same scenario root and may not escape into sibling scenario roots, `tmp/`, owner repos, or runtime state

### Fixture-Pack Manifest Contract

Every future Sandbox fixture pack must be one root-relative JSON document at:

- `data/atlas/sandbox/fixtures/<scenario_id>/fixture-pack.json`

Minimum frozen fields:

- `contract_version`
  - exact value: `atlas.sandbox.fixture-pack.v1`
- `scenario_id`
  - must match the parent directory name and the paired scenario-manifest identifier
- `fixture_pack_id`
  - stable pack identifier for the scenario root
- `title`
- `status`
  - exact admitted values: `draft` or `admitted`
- `purpose`
- `items`
  - array of fixture descriptors only
  - may be empty at this stage
- `guards`
  - exact current posture must remain:
    - `owner_repo_mutation: false`
    - `deploy_mutation: false`
    - `secret_use: false`
    - `live_data_mutation: false`
    - `_stack_execution: false`
- `non_goals`
  - must explicitly preserve the blocked execution and mutation classes for the pack

### Fixture Item Descriptor Contract

When items exist later, each descriptor must declare:

- `fixture_id`
- `kind`
  - exact admitted values: `input`, `expected_output`, `reference`, or `note`
- `path`
  - ATLAS-root-relative
  - must stay under `data/atlas/sandbox/fixtures/<scenario_id>/`
- `format`
  - exact admitted values: `json`, `md`, or `txt`

This packet does not admit:

- binary fixture payloads
- image fixture payloads
- external URLs as fixture content
- fixture references outside the scenario root

### Scenario-Manifest Reference Discipline

The paired scenario manifest may reference only:

- `data/atlas/sandbox/fixtures/<scenario_id>/fixture-pack.json`

It may not reference:

- individual leaf fixture payloads directly
- generic shared fixtures under `data/fixtures/**`
- runtime-generated descendants under `runtime/atlas/sandbox/**`

That keeps the future read path deterministic:

1. scenario manifest
2. fixture-pack manifest
3. committed leaf fixtures inside the same scenario root

## Ratchet Decision

`Sandbox Simulation Readiness` moves from `8%` to `11%`.

Why:

- the lane already had the starter contract
- the scenario-manifest home and generated runtime home were already fixed
- the remaining exact committed-fixture-boundary ambiguity is now cleared too

It stays low because:

- no example scenario exists yet
- no example fixture pack exists yet
- no validator exists
- no runner exists
- no `_stack` or owner-repo widening exists
- no proof-backed adoption exists

## Non-Claim

This does not prove:

- example Sandbox scenario data
- example fixture-pack contents
- validator behavior
- runner behavior
- `_stack` ownership
- owner-repo execution

## Exact Next Package

- `Sandbox Simulation Readiness local-only example scenario and fixture-pack stub admission`

Why:

- the committed scenario, fixture-pack, and runtime homes are now fixed
- the next honest move is one concrete example pair under the frozen boundaries
- validator, runner, and broader execution claims remain premature until one example pair exists first
