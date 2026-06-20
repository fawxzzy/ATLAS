# AI Long-Run Batch Orchestration Single Supervised Pilot Candidate Comparison First-Implementation Admission Pass 471 - 2026-06-20

- Date: `2026-06-20`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Scope: `freeze the smallest fail-closed implementation slice for the root-owned pilot-candidate comparison family without choosing any real pilot winner, repo, worktree, branch, or execution home`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-CANDIDATE-COMPARISON-CONTRACT-FREEZE-PASS-468-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-CANDIDATE-COMPARISON-OWNER-SURFACE-ADMISSION-PASS-469-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-CANDIDATE-COMPARISON-SUPPORTING-LANE-ADMISSION-PASS-470-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-SELECTION-CRITERIA-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-19.md`
  - `docs/memory/initiatives/continuity-manifest-ai-long-run-batch-orchestration.json`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned `single supervised pilot candidate comparison` family plus one proof matrix for validating that slice without crossing the no-real-winner-selection, no-repo-discovery, no-owner-repo-inventory widening, no-_stack execution-home widening, no deploy/publication, no `.env` or secret, and no protected-surface mutation boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one root-local comparison bundle that preserves only explicit candidate cards already normalized under the admitted criteria family
2. one fail-closed comparison classifier that evaluates only the already admitted comparison dimensions:
   - criteria admissibility for each candidate card
   - blast-radius discipline of the declared write scope
   - proof readiness of the declared checkpoint and verification surfaces
   - reviewability of the declared closeout artifact
   - park-or-escalation clarity when the slice stalls
3. one bounded outcome layer that may emit only:
   - `candidate_a_preferred`
   - `candidate_b_preferred`
   - `tie`
   - `not_comparable`
4. one bounded rejection-reason layer that may report only the first admitted comparison failure families
5. one preserved separation layer where the comparison slice may compare only explicit labeled candidates and may not turn a labeled preferred result into one real pilot winner, repo selection, or execution-home decision
6. one preserved ownership boundary where the comparison slice may not infer `_stack` execution-home ownership, owner-repo readiness, or deploy/publication admissibility as tie-breakers

## Exact Preserved Comparison Surface

The worker must preserve only:

- `candidate_a`
- `candidate_b`
- `criteria_status`
- `allowed_write_scope`
- `checkpoint_surface`
- `verification_gate`
- `closeout_artifact`
- `park_or_escalation_rule`
- `protected_surface_exclusions`
- `comparison_outcome`
- `comparison_reasons`

Top-level comparison rules remain:

- `candidate_a` and `candidate_b` must each already carry one explicit candidate card shape that satisfies the admitted comparison contract surface
- each candidate must already be admissible under the admitted criteria family before the comparison slice may emit one preferred result
- `comparison_outcome` may include only:
  - `candidate_a_preferred`
  - `candidate_b_preferred`
  - `tie`
  - `not_comparable`
- `comparison_reasons` may include only:
  - `candidate_a_not_criteria_admissible`
  - `candidate_b_not_criteria_admissible`
  - `candidate_fields_hidden`
  - `protected_surface_violation`
  - `repo_discovery_invented`
  - `execution_home_tiebreak_invented`
  - `insufficient_comparison_signal`
- no repo discovery, branch discovery, worktree discovery, owner-repo inventory expansion, execution-home choice, `_stack` helper-home choice, or real pilot winner selection may leak into this first slice
- a preferred labeled result is comparison-local only and may not be treated as a live lane winner until a later explicit packet admits that conversion

## Exact Mandatory Proof Cases

1. two explicit admissible candidates where candidate A has narrower write scope and equally clear proof surfaces
   - emit `comparison_outcome` as `candidate_a_preferred`
   - preserve `comparison_reasons` as `[]`

2. two explicit admissible candidates where candidate B has cleaner checkpoint or verification readiness
   - emit `comparison_outcome` as `candidate_b_preferred`
   - preserve `comparison_reasons` as `[]`

3. two explicit admissible candidates with materially equal admitted dimensions
   - emit `comparison_outcome` as `tie`
   - preserve `comparison_reasons` as `[]`

4. one candidate fails the admitted criteria family
   - emit `comparison_outcome` as `not_comparable`
   - preserve the exact candidate-specific criteria rejection reason

5. one candidate hides required comparison fields or depends on undeclared protected surfaces
   - emit `comparison_outcome` as `not_comparable`
   - preserve `candidate_fields_hidden` or `protected_surface_violation`

6. comparison logic attempts repo discovery or execution-home tie-breaking
   - emit `comparison_outcome` as `not_comparable`
   - preserve `repo_discovery_invented` or `execution_home_tiebreak_invented`

7. preserved no-winner-conversion boundary
   - the slice may compare only explicit labeled candidates
   - it may not convert one labeled preferred result into a real pilot winner, repo choice, or execution-home decision

## Exact Next Package

- `AI Long-Run Batch Orchestration single supervised pilot candidate comparison prompt-pack and handoff contract pass 472`

## Marker Decision

- `none`

Why:

- this pass freezes the smallest exact implementation slice and proof matrix only
- no code landing, proof execution, real candidate winner selection, or broader operator adoption occurs here

## Rule

Freeze the smallest fail-closed pilot-comparison validator slice before admitting prompt-pack routing, live comparison execution, real pilot winner conversion, or owner-side implementation widening.

## Failure Mode

`Pilot Winner By Comparison Drift`

This family becomes dishonest when the first implementation slice treats a labeled comparison result as a real pilot winner, invents repo discovery, or imports `_stack` execution semantics before those later boundaries are separately admitted.
