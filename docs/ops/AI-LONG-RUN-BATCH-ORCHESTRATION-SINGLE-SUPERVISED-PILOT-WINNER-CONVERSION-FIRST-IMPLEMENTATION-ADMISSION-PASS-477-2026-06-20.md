# AI Long-Run Batch Orchestration Single Supervised Pilot Winner Conversion First-Implementation Admission Pass 477 - 2026-06-20

- Date: `2026-06-20`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Scope: `freeze the smallest fail-closed implementation slice for the root-owned pilot winner-conversion family without choosing any live pilot winner, repo, worktree, branch, or execution home by adjacency`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-WINNER-CONVERSION-CONTRACT-FREEZE-PASS-474-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-WINNER-CONVERSION-OWNER-SURFACE-ADMISSION-PASS-475-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-WINNER-CONVERSION-SUPPORTING-LANE-ADMISSION-PASS-476-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-CANDIDATE-COMPARISON-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-20.md`
  - `ops/atlas/pilot_candidate_comparison.py`
  - `tests/test_atlas_pilot_candidate_comparison.py`
  - `docs/memory/initiatives/continuity-manifest-ai-long-run-batch-orchestration.json`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned `single supervised pilot winner conversion` family plus one proof matrix for validating that slice without crossing the no-live-pilot-selection-by-adjacency, no-owner-repo-inventory widening, no-_stack execution-home widening, no deploy/publication, no `.env` or secret, and no protected-surface mutation boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one root-local winner-conversion bundle that preserves only two explicit candidate cards already compared under the admitted comparison family plus one already-produced comparison result
2. one fail-closed conversion classifier that evaluates only the already admitted conversion dimensions:
   - whether `comparison_outcome` is exactly `candidate_a_preferred` or `candidate_b_preferred`
   - whether `comparison_reasons` is exactly `[]`
   - whether the preferred label still maps back to one explicit candidate card already present in the conversion bundle
   - whether that preferred candidate card still preserves one explicit `target_kind`, `target_ref`, and protected-surface boundary without hidden repo, branch, or worktree discovery
3. one bounded conversion-status layer that may emit only:
   - `winner_selected`
   - `no_winner`
4. one bounded winner-output layer that may emit only one explicit preferred candidate card already present in the conversion bundle or `null`
5. one preserved separation layer where the conversion slice may convert one explicit preferred comparison label into one contract-local real pilot winner but may not infer owner-repo readiness, `_stack` helper-home ownership, branch/worktree discovery, or live execution-home choice
6. one preserved ownership boundary where the conversion slice may not treat deploy/publication, archive/delete, `.env`, secret work, or hidden owner-side proof posture as winner tie-breakers

## Exact Preserved Conversion Surface

The worker must preserve only:

- `candidate_a`
- `candidate_b`
- `comparison_outcome`
- `comparison_reasons`
- `conversion_status`
- `pilot_winner`
- `conversion_reasons`

Top-level conversion rules remain:

- `candidate_a` and `candidate_b` must each already carry one explicit candidate-card shape that satisfies the admitted criteria and comparison contract surfaces
- `comparison_outcome` may include only:
  - `candidate_a_preferred`
  - `candidate_b_preferred`
  - `tie`
  - `not_comparable`
- `conversion_status` may include only:
  - `winner_selected`
  - `no_winner`
- `pilot_winner` may be either:
  - the exact explicit `candidate_a` card
  - the exact explicit `candidate_b` card
  - `null`
- `pilot_winner` may be non-null only when:
  - `comparison_outcome` is `candidate_a_preferred` or `candidate_b_preferred`
  - `comparison_reasons` is `[]`
  - the preferred label maps directly back to one explicit candidate card already present in the bundle
  - that card does not require hidden repo discovery, hidden branch/worktree discovery, `_stack` ownership, owner-repo readiness, deploy/publication, archive/delete, `.env`, or secret work as a tie-breaker
- `conversion_reasons` may include only:
  - `comparison_outcome_not_preferred`
  - `comparison_reasons_present`
  - `preferred_candidate_missing`
  - `preferred_candidate_not_explicit`
  - `protected_surface_violation`
  - `repo_discovery_invented`
  - `owner_readiness_tiebreak_invented`
  - `execution_home_tiebreak_invented`
- no live repo discovery, branch discovery, worktree discovery, owner-repo inventory expansion, execution-home choice, `_stack` helper-home choice, or owner-side implementation selection may leak into this first slice

## Exact Mandatory Proof Cases

1. explicit `candidate_a_preferred` result with empty comparison reasons
   - emit `conversion_status` as `winner_selected`
   - preserve `pilot_winner` as the explicit `candidate_a` card
   - preserve `conversion_reasons` as `[]`

2. explicit `candidate_b_preferred` result with empty comparison reasons
   - emit `conversion_status` as `winner_selected`
   - preserve `pilot_winner` as the explicit `candidate_b` card
   - preserve `conversion_reasons` as `[]`

3. `tie` comparison result
   - emit `conversion_status` as `no_winner`
   - preserve `pilot_winner` as `null`
   - preserve `comparison_outcome_not_preferred`

4. `not_comparable` comparison result
   - emit `conversion_status` as `no_winner`
   - preserve `pilot_winner` as `null`
   - preserve `comparison_outcome_not_preferred`

5. non-empty comparison reasons despite one preferred label
   - emit `conversion_status` as `no_winner`
   - preserve `pilot_winner` as `null`
   - preserve `comparison_reasons_present`

6. preferred label cannot be mapped back to one explicit candidate card
   - emit `conversion_status` as `no_winner`
   - preserve either `preferred_candidate_missing` or `preferred_candidate_not_explicit`

7. winner argument invents repo discovery, owner-readiness tie-breaking, or execution-home tie-breaking
   - emit `conversion_status` as `no_winner`
   - preserve the exact corresponding conversion reason

## Exact Next Package

- `AI Long-Run Batch Orchestration single supervised pilot winner conversion prompt-pack and handoff contract pass 478`

## Marker Decision

- `none`

Why:

- this pass freezes the smallest exact implementation slice and proof matrix only
- no code landing, proof execution, live pilot winner selection, or broader operator adoption occurs here

## Rule

Freeze the smallest fail-closed pilot winner-conversion slice before admitting prompt-pack routing, live lane winner selection, owner-side implementation widening, or `_stack` execution-home semantics.

## Failure Mode

`Pilot Winner By Conversion Drift`

This family becomes dishonest when the first implementation slice invents repo discovery, owner-readiness tie-breaking, or execution-home doctrine instead of converting only one explicit preferred comparison label into one explicit contract-local winner under the frozen fail-closed rules.
