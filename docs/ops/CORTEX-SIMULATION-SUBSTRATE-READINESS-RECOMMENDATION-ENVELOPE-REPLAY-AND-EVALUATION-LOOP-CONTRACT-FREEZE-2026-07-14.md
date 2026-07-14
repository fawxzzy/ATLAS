# Cortex Simulation Substrate Readiness Recommendation-Envelope Replay And Evaluation Loop Contract Freeze

- Date: `2026-07-14`
- Opening checkpoint: `main@ce8c6c48`
- Marker posture: `80%`, unchanged by this contract

## Decision

Admit one deterministic root-only evaluator that replays digest-bound simulator manifests through the recommendation bridge and classifies each resulting envelope as:

- `match`: current envelope identity equals the expected identity;
- `changed`: valid current envelope identity differs from the expected identity;
- `invalid`: the source manifest, source digest, simulator, doctrine adoption, or recommendation bridge fails closed.

The loop evaluates evidence. It does not execute recommendations, promote doctrine, update Cortex state, or mutate operational truth.

## Evaluation Manifest

One committed manifest below `data/cortex/simulation-evaluations/` declares one or more cases. Each case includes:

- stable case ID;
- root-relative simulator manifest below `data/cortex/simulation-replays/`;
- expected SHA-256 digest of those manifest bytes;
- expected recommendation envelope ID when a valid envelope is expected;
- expected classification.

The first canary must exercise `match`, `changed`, and `invalid` in one bounded run.

## Output

The output records ordered case results, classification counts, mismatches, threshold eligibility, termination, and a complete authority-false block. It may be printed or written only to an explicit `tmp/atlas/*.json` path.

## Implementation Admission

Admitted paths:

- `schemas/atlas.cortex.simulation.recommendation-evaluation-manifest.v1.json`
- `schemas/atlas.cortex.simulation.recommendation-evaluation.v1.json`
- `ops/cortex/simulation_recommendation_evaluator.py`
- `tests/test_cortex_simulation_recommendation_evaluator.py`
- `data/cortex/simulation-evaluations/first-recommendation-loop/manifest.json`
- `docs/registry/CORTEX-SIMULATION-RECOMMENDATION-EVALUATION.v1.json`
- later proof-backed reconciliation and continuity projections

Required proof:

1. the committed loop classifies one match, one changed result, and one invalid source;
2. case order and output identity are deterministic;
3. digest mismatch, unsafe paths, duplicate IDs, unknown fields, invalid expected classifications, and output-path violations fail closed or classify invalid as specified;
4. changed output never becomes a mutation instruction;
5. every execution, dispatch, promotion, owner-write, external-write, approval, final-receipt, and marker authority remains false;
6. existing recommendation, simulator, replay, selector, continuity, and stack validation remain green.

## Marker Gate

This contract moves no marker. `90%` becomes eligible only after the loop is implemented and the committed three-class canary passes.

## Exact Next Packet

```text
Cortex Simulation Substrate Readiness recommendation-envelope replay and evaluation loop first implementation and 90 percent reconciliation
```

## Governance

**RULE - Changed is not failed and not approved.** A changed envelope requires review; it neither proves a defect nor authorizes adoption.

**PATTERN - Three-class deterministic evaluation.** Prove unchanged, changed, and invalid behavior in one bounded replay loop.

**FAILURE MODE - Evaluation-driven mutation.** A replay difference directly triggers execution or doctrine promotion without a separately authorized job.
