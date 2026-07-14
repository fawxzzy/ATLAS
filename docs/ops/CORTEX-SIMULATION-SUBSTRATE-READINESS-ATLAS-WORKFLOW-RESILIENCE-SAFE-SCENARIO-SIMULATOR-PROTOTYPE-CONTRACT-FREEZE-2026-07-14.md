# Cortex Simulation Substrate Readiness Atlas Workflow-Resilience Safe Scenario Simulator Prototype Contract Freeze

- Date: `2026-07-14`
- Opening checkpoint: `main@0454a42a`
- Marker posture: `60%`, unchanged by this contract
- Adapter: `atlas-workflow-resilience`

## Decision

Freeze and admit one root-owned simulator prototype over the existing digest-bound Atlas receipt replay. The prototype converts committed execution and validation outcomes into a bounded advisory recovery rehearsal. It does not execute the rehearsal.

## Inputs

The simulator accepts one committed manifest below `data/cortex/simulation-replays/`. That manifest names an existing `atlas.cortex.simulation.receipt-replay-manifest.v1` input and declares:

- the Atlas workflow-resilience adapter;
- a fixed maximum step count from `1` through `8`;
- allowed scenario classes: `observed`, `proof_recovery`, and `blocked_hold`;
- an explicit digest for the replay manifest bytes.

No hidden transcript, secret, raw live user data, arbitrary owner file, browser state, model output, network response, or runtime command output is admitted.

## Output

The deterministic `atlas.cortex.simulation.workflow-resilience.v1` output contains:

- source and replay correlation;
- an observed workflow state derived from replay failure-mode counts;
- a bounded sequence of hypothetical recovery steps;
- preconditions and proof required for each step;
- termination state and reason;
- recommendations that remain advisory;
- a complete authority-false block.

The result may be printed or written only below `tmp/atlas/` when an explicit output path is supplied.

## State Model

| Receipt evidence | Observed state | Rehearsal posture |
| --- | --- | --- |
| blocked receipt or blocked verification | `blocked` | preserve hold, identify owner, require new proof |
| failed receipt or failed verification | `failed` | isolate failure, require corrected execution and proof |
| advisory-only receipt | `watch` | request stronger evidence before action |
| success-only replay | `healthy` | recommend no mutation and continued observation |

The simulator cannot claim that a hypothetical recovery happened. A recovery branch ends as `rehearsed`, never `executed` or `completed`.

## Termination

Every successful simulation terminates when the fixed scenario template is exhausted or `max_steps` is reached. Cycles, recursive planning, unbounded retries, and model-generated continuation are prohibited.

## Implementation Admission

Admitted paths:

- `schemas/atlas.cortex.simulation.workflow-resilience-manifest.v1.json`
- `schemas/atlas.cortex.simulation.workflow-resilience.v1.json`
- `ops/cortex/workflow_resilience_simulator.py`
- `tests/test_cortex_workflow_resilience_simulator.py`
- `data/cortex/simulation-replays/first-mixed-replay/workflow-resilience-manifest.json`
- `docs/registry/CORTEX-SIMULATION-ATLAS-WORKFLOW-RESILIENCE-PROTOTYPE.v1.json`
- the later proof-backed reconciliation, Atlas Book projection, and continuity-manifest updates

Required proof:

1. identical input produces byte-equivalent structured output;
2. the committed mixed replay produces a blocked recovery rehearsal and terminates;
3. success-only, failure, advisory, and blocked states are classified deterministically;
4. digest mismatch, unsafe paths, unknown fields, invalid steps, and unadmitted scenario classes fail closed;
5. no output is written unless an explicit `tmp/atlas/` path is supplied;
6. every authority field remains false;
7. existing Cortex replay, scenario-helper, schema, selector, and continuity tests remain green.

## Marker Gate

This contract moves no marker. `70%` becomes eligible only after implementation, focused proof, regression proof, a committed canary manifest, continuity reconciliation, and a clean stack validation.

## Exact Next Packet

```text
Cortex Simulation Substrate Readiness Atlas workflow-resilience safe scenario simulator prototype first implementation and 70 percent reconciliation
```

## Governance

**RULE - A simulation is not an execution receipt.** Hypothetical recovery output cannot prove that any state changed.

**PATTERN - Receipt-bound bounded rehearsal.** Replay verified receipts, derive a fixed scenario, terminate deterministically, and return only advisory proof requirements.

**FAILURE MODE - Simulated recovery promoted as completion.** A rehearsal result is used to move a card, marker, deployment, or owner state without real execution and readback.
