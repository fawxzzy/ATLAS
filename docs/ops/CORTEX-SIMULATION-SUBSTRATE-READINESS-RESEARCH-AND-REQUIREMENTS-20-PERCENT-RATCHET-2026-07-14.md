# Cortex Simulation Substrate Readiness Research And Requirements 20 Percent Ratchet

- Date: `2026-07-14`
- Lane: `Cortex Simulation Substrate Readiness`
- Mode: `ATLAS-root evidence reconciliation and marker ratchet`
- Scope: `reconcile already-landed research and requirements-map proof into current marker, restart, registry, and selector truth`
- Opening checkpoint: `main@2025ae3a7c6ebaa1b641eceaba2a84fc75685802`
- Marker movement: `0% -> 20%`

## Decision

Move `Cortex Simulation Substrate Readiness` from `0%` to `20%`.

The lane already satisfies both deterministic thresholds:

- `10%`: the Fable/Showrunner/generative-agent research contract is frozen.
- `20%`: simulation substrate requirements are mapped to ATLAS, Playbook, and Cortex through a landed deterministic helper and focused proof suite.

This is a reconciliation of executed state, not a claim that a simulator exists.

## Primary Research Basis

The current source posture uses:

1. [Showrunner](https://www.showrunner.xyz/) as Fable's first-party description of persistent simulated worlds, AI characters, user steering, and creator-directed story generation.
2. [Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442) as the primary architectural source for observation, memory, retrieval, reflection, planning, and sandbox interaction.

These sources are architectural signals only. They do not authorize ATLAS to clone Showrunner, reproduce protected media, ingest hidden transcripts, train a model, or execute live actions.

## Durable Existing Evidence

The previously completed packet chain is real and committed:

1. `docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md`
2. `docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md`
3. `docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-10.md`
4. `docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-IMPLEMENTATION-READINESS-CLOSEOUT-AND-WORKER-ROUTING-2026-07-10.md`
5. `ops/cortex/simulation_substrate_requirements.py` from worker commit `99ab4dcb`
6. `tests/test_cortex_simulation_substrate_requirements.py`
7. `docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-07-10.md` from reconciliation commit `9bc5d34f`

The prior receipts intentionally held the marker at `0%` because no separate ratchet packet was authorized. The implementation existed; the marker and selector did not yet project it.

## Fresh Proof

Fresh execution against the current root proved:

- `python -m unittest tests.test_cortex_simulation_substrate_requirements -v` -> `10 / 10` passed
- `python ops/cortex/simulation_substrate_requirements.py --json --strict --output tmp/cortex/simulation-substrate-requirements.current.json` -> `status=ok`
- requirement groups: `11 / 11` mapped
- unmapped groups: `0`
- warnings: `0`
- blockers: `0`
- `safe_to_use=true`
- project adapters remain deferred
- authority denials remain explicit

The deterministic requirements map covers:

- scenario
- agent
- world state
- memory
- reflection
- plan
- action
- observation
- evaluation
- safety boundary
- proof reference

## Authority Boundary

This ratchet grants no authority for:

- simulation or agent execution
- owner-repository mutation
- platform mutation
- deploys
- Discord or board writes
- secret handling
- hidden transcript ingestion
- model training
- media generation
- automatic final receipts
- automatic marker movement

The generated requirements output remains advisory and root-owned.

## Why 30 Percent Is Not Yet Claimed

The 30% threshold requires a separately frozen agent memory/reflection/planning schema.

The existing requirements map names those primitives and first required fields, but it does not yet freeze:

- schema identities and versions
- event and state transition semantics
- provenance and retention rules
- reflection trigger and compression policy
- retrieval scoring and confidence handling
- plan lifecycle and termination semantics
- injection, privacy, and rights constraints at field level

Therefore `20%` is the highest honest current marker.

## Exact Next Packet

```text
Cortex Simulation Substrate Readiness agent memory reflection planning schema contract freeze
```

## Reusable Governance

**RULE - Existing executed state outranks a stale marker.** A marker ratchet must reconcile durable implementation and fresh proof before reopening an already-completed packet.

**PATTERN - Research-to-requirements substrate.** First-party product signals and primary research are converted into an authority-bounded deterministic requirements map before schema or runtime work begins.

**FAILURE MODE - Completed-work selector regression.** A stale packet descriptor can route research or implementation that is already durable while the marker remains artificially low.

## Completion

The research and requirements thresholds are reconciled at `20%`.

No owner repository, platform, deployment, Discord surface, board, secret, or live data was mutated.
