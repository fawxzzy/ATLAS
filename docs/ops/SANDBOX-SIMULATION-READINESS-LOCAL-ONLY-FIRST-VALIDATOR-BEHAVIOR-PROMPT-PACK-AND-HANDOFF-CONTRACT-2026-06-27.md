# Sandbox Simulation Readiness Local-Only First Validator-Behavior Prompt-Pack And Handoff Contract - 2026-06-27

- Date: `2026-06-27`
- Lane: `Sandbox Simulation Readiness`
- Mode: `root-owned docs-only validator-behavior prompt-pack and handoff contract`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-local Sandbox validator-behavior family.

This pass does not:

- implement code
- execute validator behavior
- assign verdict-bearing statuses
- mutate report, candidate-output, or oracle files
- reopen `_stack` routing, owner-repo work, deploy/publication, `.env`, secret, or protected-surface work
- widen into broader selector, manifest, or runtime redesign

## Root Health Baseline

- the validator-behavior boundary, owner-facing home, and support posture are already durable
- the first implementation slice is already frozen around one root-local read-only helper and one direct proof file
- the remaining gap is worker handoff precision, not root-side design ambiguity
- current restart projection already expects this exact prompt-pack contract as the next root-ready packet

## Inherited Contract Spine

The future worker must inherit exactly:

- validator-behavior boundary contract freeze
- validator-behavior owner-surface admission
- validator-behavior supporting-lane hold at `none yet`
- validator-behavior first-implementation admission

No worker may reinterpret those seams as suggestions.
They are contract inputs.

## Exact Worker Objective

The next worker is allowed to pursue one exact implementation objective only:

- implement one root-local read-only helper in `ops/atlas/sandbox_validator_behavior.py` plus one direct proof file in `tests/test_atlas_sandbox_validator_behavior.py` so the helper loads only one explicit validator descriptor, one explicit validator report stub, one explicit candidate-output stub, and one explicit expected-output oracle stub; validates only the admitted identity and reference fields; compares only the frozen boundary fields; emits only `equal_on_boundary`, `unequal_on_boundary`, or `not_admissible`; reports only the admitted `comparison_reasons`; fails closed on widened or hidden inputs; preserves the no-verdict and no-mutation boundary; and proves behavior against the frozen first-implementation matrix

The worker is not allowed to pursue:

- report mutation
- candidate-output mutation
- real validator execution
- `match`, `mismatch`, or `blocked` assignment
- `_stack` helper-runtime or worker-routing logic
- owner-repo edits
- broader runtime, selector, manifest, or restart-surface redesign

## Exact Preserved Behavior Surface

The worker must preserve exactly these surfaces:

- `validator_ref`
- `report_ref`
- `candidate_output_ref`
- `oracle_ref`
- `report_status`
- `compared_fields`
- `comparison_outcome`
- `comparison_reasons`

The worker may render these surfaces only.
The worker may not widen them into report mutation authority, verdict authority, execution authority, runner authority, or broader routing semantics.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

1. the current admitted descriptor, report stub, candidate-output stub, and oracle stub align on identity and equality over the frozen boundary
   - preserve `comparison_outcome` as `equal_on_boundary`
   - preserve `comparison_reasons` as `[]`

2. one synthetic unequal payload over `mode`, `status`, or `observations` while identity still aligns
   - preserve `comparison_outcome` as `unequal_on_boundary`
   - preserve `comparison_reasons` as `[]`

3. one synthetic report status other than `not_run`
   - preserve `comparison_outcome` as `not_admissible`
   - preserve `comparison_reasons` as `["report_status_not_not_run"]`

4. one synthetic identity mismatch across `validator_id`, `scenario_id`, or `run_id`
   - preserve `comparison_outcome` as `not_admissible`
   - preserve `comparison_reasons` as `["identity_mismatch"]`

5. one synthetic missing required boundary field
   - preserve `comparison_outcome` as `not_admissible`
   - preserve `comparison_reasons` as `["missing_boundary_field"]`

6. one synthetic oracle-ref mismatch
   - preserve `comparison_outcome` as `not_admissible`
   - preserve `comparison_reasons` as `["oracle_ref_mismatch"]`

7. preserved no-verdict and no-mutation boundary
   - the helper may not emit `match`, `mismatch`, or `blocked`
   - the helper may not mutate report or candidate-output files

## Exact No-Mutation / No-Verdict / No-Discovery Boundary

The worker must carry this wording forward verbatim:

`No-mutation, no-verdict, and no-discovery guard: this packet may implement one explicit root-local read-only validator-behavior helper plus direct proof for the already admitted identity checks, boundary comparisons, outcomes, and reasons, but it may not mutate report, candidate-output, oracle, runtime, manifest, selector, receipt, or owner-repo state; it may not emit match, mismatch, or blocked; it may not discover alternate runs, scenarios, validators, or artifacts; and it may not widen into _stack, deploy, publication, .env, secret, archive, screenshot, capture, or protected-surface work.`

## Exact No Hidden Transcript-State Inference Boundary

The worker must carry this rule forward:

- use only the cited durable surfaces in this receipt chain plus the admitted helper and test files
- do not infer validator truth, owner readiness, routing meaning, or protected-surface exceptions from uncited transcript memory or broad root residue

## Exact Allowed Future Implementation Surfaces

The worker may touch only:

- `ops/atlas/sandbox_validator_behavior.py`
- `tests/test_atlas_sandbox_validator_behavior.py`

## Exact Forbidden Future Implementation Surfaces

The worker must not touch:

- `ops/atlas/marker_knockout_selector.py`
- `docs/atlas-book/*`
- `docs/memory/initiatives/*`
- owner repos under `repos/*`
- `_stack` helper-runtime or command-design surfaces
- `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, `.playwright-mcp/`, or broad untracked root backlog

## Exact Stop Conditions

The worker must stop and return immediately if the slice requires:

- report or candidate-output mutation
- emitted `match`, `mismatch`, or `blocked`
- alternate artifact discovery beyond the explicit admitted files
- `_stack` routing or execution-home inference
- owner-repo edits
- deploy/publication, `.env`, secret, archive/delete, or protected-surface touch
- selector redesign, manifest edits, or broader runtime-inventory work to make the helper work

If one of those triggers appears, the work is no longer valid first-slice implementation work.

## Exact Handoff Prompt-Pack Spine

Any future worker prompt-pack must include:

1. the exact implementation objective
2. the inherited Sandbox receipt chain as frozen inputs
3. the exact preserved behavior surface
4. the exact proof matrix
5. the exact no-mutation, no-verdict, and no-discovery guard verbatim
6. the exact no-hidden-transcript-state boundary
7. the exact allowed-touch and forbidden-touch surfaces
8. the exact stop-and-return conditions

Mirror surfaces may restate this spine.
They may not redefine it.

## Exact Next Package

- `Sandbox Simulation Readiness local-only first validator-behavior implementation-readiness closeout and worker-routing`

## Marker Decision

- `none`

Why:

- this pass narrows the worker handoff contract only
- no new executed state, broader proof-backed adoption, or blocker clearance landed

## Rule

Freeze the worker handoff contract before authorizing any first-slice implementation work for the root-local Sandbox validator-behavior family.

## Failure Mode

`Sandbox Validator Handoff Drift`

This family becomes dishonest when the worker handoff contract stays implicit and the first behavior slice expands through prompt wording into verdict assignment, report mutation, alternate artifact discovery, or protected-surface exceptions that the durable chain has not admitted.
