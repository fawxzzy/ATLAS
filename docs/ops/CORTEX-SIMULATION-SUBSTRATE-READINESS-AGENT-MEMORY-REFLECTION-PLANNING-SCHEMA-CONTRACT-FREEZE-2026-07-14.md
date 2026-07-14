# Cortex Simulation Substrate Readiness Agent Memory Reflection Planning Schema Contract Freeze

- Date: `2026-07-14`
- Lane: `Cortex Simulation Substrate Readiness`
- Mode: `ATLAS-root schema contract freeze`
- Scope: `freeze the first versioned agent memory, retrieval, reflection, and planning state contract without implementing simulation execution`
- Opening checkpoint: `main@8c4902aa325066f0c1b510d01379065afc6a6818`
- Marker movement: `20% -> 30%`

## Decision

Move `Cortex Simulation Substrate Readiness` from `20%` to `30%`.

The first agent cognitive-state contract is now frozen in:

- `schemas/atlas.cortex.simulation.agent-state.v1.json`
- `docs/registry/CORTEX-SIMULATION-AGENT-STATE-SCHEMA.v1.json`
- `tests/test_cortex_simulation_agent_state_schema.py`

The JSON Schema defines the serializable state shape. The registry defines lifecycle and policy semantics that cannot be enforced completely by structural validation alone.

## Memory Contract

Every memory requires:

- stable digest identity
- observation time
- summary-only content
- source references and source digest
- explicit importance and confidence
- retention class
- rights class
- privacy class
- injection state
- supersession history

Unknown rights, prohibited sensitive data, and rejected injection inputs must be excluded and blocked. Raw hidden transcript content is not admitted.

## Retrieval Contract

Retrieval requires:

- explicit candidate and selected memory identities
- explicit recency, importance, and relevance weights
- explicit minimum confidence
- deterministic score-descending then memory-ID-ascending tie breaking
- a reason for every excluded candidate

The registry additionally requires selected memories to be a subset of candidates. A future helper must enforce cross-field rules that JSON Schema cannot express alone.

## Reflection Contract

Reflection may trigger only from:

- event count
- importance threshold
- operator request
- replay checkpoint

Every reflection must cite source memories and durable sources, carry confidence, remain labeled `derived_not_observed=true`, and remain `advisory_only`. A reflection cannot overwrite an observation.

## Planning Contract

Plans use the states:

- candidate
- active
- completed
- blocked
- abandoned

The registry freezes allowed transitions. Every step requires evidence and an advisory authority check. Every plan permanently carries `execution_authorized=false`.

Termination reasons are explicit:

- success
- blocked
- timeout
- operator stop
- safety stop

## Provenance, Retention, Rights, And Privacy

The schema and registry require:

- root-relative durable source references
- source digests for memories
- explicit retention instead of indefinite implicit persistence
- explicit rights classification
- explicit privacy classification
- hidden transcripts denied
- secrets denied
- raw live user data denied by default
- owner-repository private drift excluded from canonical simulation truth

## Authority Boundary

The top-level authority object enforces:

- `advisory_only=true`
- `execution_authorized=false`
- `owner_repo_mutation_authorized=false`
- `platform_mutation_authorized=false`
- `discord_write_authorized=false`
- `marker_movement_authorized=false`

The registry additionally denies board writes and final-receipt authority.

## Proof

Focused schema tests prove:

1. the schema declares the Draft 2020-12 contract and stable Atlas identifier
2. a complete advisory fixture validates through the focused dependency-free contract checker
3. top-level execution authority is rejected
4. plan execution authority is rejected
5. raw or unknown memory fields are rejected
6. reflections cannot masquerade as direct observations

## Why 40 Percent Is Not Yet Claimed

The 40% threshold requires a first read-only scenario simulation helper.

This packet defines state only. It does not:

- instantiate an agent
- retrieve memories at runtime
- generate reflections
- transition plans
- execute scenarios
- call models or external APIs
- read owner repositories or live data

## Exact Next Packet

```text
Cortex Simulation Substrate Readiness first read-only scenario helper contract freeze
```

## Reusable Governance

**RULE - Derived state must identify itself.** Reflections and plans may not masquerade as observations or receipts.

**PATTERN - Structural schema plus lifecycle registry.** JSON Schema validates shape while a companion registry freezes cross-field transitions, provenance, retention, and authority semantics.

**FAILURE MODE - Plausible-state authority creep.** A simulated plan appears actionable because execution denial is implicit instead of machine-enforced.

## Completion

The agent memory/reflection/planning schema threshold is frozen at `30%`.

No simulator, model call, owner-repository mutation, platform mutation, deployment, Discord write, board write, secret access, or live-data mutation occurred.
