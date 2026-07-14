# Cortex Simulation Substrate Readiness Simulation-Output Playbook And Cortex Recommendation Consumption Contract Freeze

- Date: `2026-07-14`
- Opening checkpoint: `main@340ff8f6`
- Marker posture: `70%`, unchanged by this contract

## Decision

Admit one root-owned bridge that consumes a proved `atlas.cortex.simulation.workflow-resilience.v1` result and emits one deterministic authority-false recommendation envelope with two projections:

1. Playbook-facing doctrine candidates that remain candidate-only and source-linked;
2. Cortex-facing next-proof recommendations that remain advisory and non-executing.

The bridge does not modify the Playbook owner repository, doctrine registry, Cortex state, a marker, or any external system.

## Playbook Projection

The projection uses `docs/registry/ATLAS-PLAYBOOK-DOCTRINE-ADOPTION.json` as the root's accepted source-linked Playbook adoption record. It emits candidate records classified as `rule_candidate`, `pattern_candidate`, or `failure_mode_candidate` with:

- stable candidate ID;
- exact simulation and doctrine source refs;
- recommendation text;
- `promotion_state=candidate_only`;
- `doctrine_is_not_implementation_proof=true`;
- no automatic promotion or owner-repo write authority.

## Cortex Projection

The projection emits ordered next-proof recommendations with:

- stable recommendation ID;
- simulation correlation;
- observed state and reason;
- required evidence;
- advisory priority;
- `execution_authorized=false`;
- no dispatch, final-receipt, approval, or marker authority.

## Implementation Admission

Admitted paths:

- `schemas/atlas.cortex.simulation.recommendation-envelope.v1.json`
- `ops/cortex/simulation_recommendation_bridge.py`
- `tests/test_cortex_simulation_recommendation_bridge.py`
- `docs/registry/CORTEX-SIMULATION-RECOMMENDATION-CONSUMPTION.v1.json`
- later proof-backed reconciliation and continuity projections

Required proof:

1. identical simulator and doctrine inputs produce identical envelopes;
2. every simulator recommendation produces one Cortex recommendation;
3. at least one Playbook-facing Rule, Pattern, and Failure Mode candidate is emitted for the blocked canary;
4. all candidates remain candidate-only and source-linked;
5. unsafe paths, doctrine contract drift, simulator blockers, and output-path violations fail closed;
6. every execution, dispatch, promotion, owner-write, external-write, approval, final-receipt, and marker authority remains false;
7. existing simulator, replay, selector, continuity, and stack validation remain green.

## Marker Gate

This contract moves no marker. `80%` becomes eligible only when both projections are implemented, tested, and proved against the committed Atlas workflow-resilience canary.

## Exact Next Packet

```text
Cortex Simulation Substrate Readiness simulation-output recommendation bridge first implementation and 80 percent reconciliation
```

## Governance

**RULE - Recommendation consumption does not grant recommendation authority.** A consumer may render and correlate advisory output without executing or promoting it.

**PATTERN - Dual projection from one source envelope.** Preserve one simulation identity while projecting doctrine candidates and next-proof recommendations for distinct consumers.

**FAILURE MODE - Candidate auto-promotion.** Simulation-derived doctrine is written into canonical Playbook truth without owner review and evidence-backed promotion.
