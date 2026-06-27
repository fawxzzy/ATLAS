# Sandbox Simulation Readiness Local-Only First Validator-Behavior First-Implementation Admission - 2026-06-27

- Date: `2026-06-27`
- Lane: `Sandbox Simulation Readiness`
- Mode: `root-owned docs-only validator-behavior first-implementation admission`

## Objective

Freeze one compact authoritative first implementation slice for the root-local Sandbox validator-behavior family plus one proof matrix for validating that slice without admitting validator execution, report mutation, verdict-bearing status assignment, runner behavior, `_stack` routing, owner-repo work, or any deploy, secret, or live-data widening.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one root-local read-only helper in `ops/atlas/sandbox_validator_behavior.py`
2. one direct proof file in `tests/test_atlas_sandbox_validator_behavior.py`
3. one explicit-input load path that accepts only the already admitted:
   - validator descriptor
   - validator report stub
   - validator candidate-output stub
   - expected-output oracle stub
4. one bounded coherence check that may validate only:
   - `validator_id`
   - `scenario_id`
   - `run_id`
   - `validator_ref`
   - `oracle_ref`
   - `report.result.status`
5. one bounded comparison layer that may compare only:
   - `candidate_output.payload.mode`
   - `candidate_output.payload.status`
   - `candidate_output.payload.observations`
   against:
   - `expected_output.payload.mode`
   - `expected_output.payload.status`
   - `expected_output.payload.observations`
6. one bounded pre-verdict outcome layer that may emit only:
   - `equal_on_boundary`
   - `unequal_on_boundary`
   - `not_admissible`
7. one bounded reason layer that may report only:
   - `report_status_not_not_run`
   - `identity_mismatch`
   - `oracle_ref_mismatch`
   - `missing_boundary_field`
   - `unexpected_path_discovery`
   - `attempted_verdict_assignment`
   - `attempted_report_mutation`

## Exact Preserved Behavior Surface

The worker must preserve only:

- `validator_ref`
- `report_ref`
- `candidate_output_ref`
- `oracle_ref`
- `report_status`
- `compared_fields`
- `comparison_outcome`
- `comparison_reasons`

Top-level rules remain:

- the helper may read only explicit paths provided to it
- the helper may not discover alternate runs, scenarios, validators, or artifacts
- the helper may not write back into `report.json` or `candidate-output.json`
- the helper may not emit `match`, `mismatch`, or `blocked`
- `comparison_outcome` remains pre-verdict only and may not be treated as executed validator truth

## Exact Mandatory Proof Cases

1. the current admitted validator descriptor, report stub, candidate-output stub, and oracle stub align on identity and equality over the frozen boundary
   - emit `comparison_outcome` as `equal_on_boundary`
   - preserve `comparison_reasons` as `[]`

2. one synthetic unequal payload over `mode`, `status`, or `observations` while all admitted identity surfaces still align
   - emit `comparison_outcome` as `unequal_on_boundary`
   - preserve `comparison_reasons` as `[]`

3. one synthetic report status other than `not_run`
   - emit `comparison_outcome` as `not_admissible`
   - preserve `comparison_reasons` as `["report_status_not_not_run"]`

4. one synthetic identity mismatch across `validator_id`, `scenario_id`, or `run_id`
   - emit `comparison_outcome` as `not_admissible`
   - preserve `comparison_reasons` as `["identity_mismatch"]`

5. one synthetic missing required boundary field under `payload.mode`, `payload.status`, or `payload.observations`
   - emit `comparison_outcome` as `not_admissible`
   - preserve `comparison_reasons` as `["missing_boundary_field"]`

6. one synthetic oracle-ref mismatch between the candidate-output stub and the explicit oracle path
   - emit `comparison_outcome` as `not_admissible`
   - preserve `comparison_reasons` as `["oracle_ref_mismatch"]`

7. preserved no-verdict and no-mutation boundary
   - the helper may not emit `match`, `mismatch`, or `blocked`
   - the helper may not mutate the report or candidate-output files

## Exact Next Package

- `Sandbox Simulation Readiness local-only first validator-behavior prompt-pack and handoff contract`

## Marker Decision

- `none`

Why:

- this pass freezes the smallest exact implementation slice and proof matrix only
- no code landing, proof execution, validator execution, or broader adoption occurs here

## Rule

Freeze the smallest fail-closed Sandbox validator-behavior helper slice before admitting prompt-pack routing, live behavior execution, verdict activation, or wider routing.

## Failure Mode

`Sandbox Validator Verdict Drift`

This family becomes dishonest when the first implementation slice treats equality or inequality on the frozen boundary as a live `match`, `mismatch`, or `blocked` verdict, mutates the report surfaces, or discovers alternate artifacts beyond the explicit admitted files.
