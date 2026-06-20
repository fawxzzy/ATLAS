# AI Long-Run Batch Orchestration Single Supervised Pilot Selection Criteria First-Implementation Admission Pass 465 - 2026-06-19

- Date: `2026-06-19`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Scope: `freeze the smallest fail-closed implementation slice for the root-owned pilot-selection criteria family without choosing any real pilot candidate, repo, worktree, branch, or execution home`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-SELECTION-CRITERIA-CONTRACT-FREEZE-PASS-462-2026-06-18.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-SELECTION-CRITERIA-OWNER-SURFACE-ADMISSION-PASS-463-2026-06-19.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-SELECTION-CRITERIA-SUPPORTING-LANE-ADMISSION-PASS-464-2026-06-19.md`
  - `docs/memory/initiatives/continuity-manifest-ai-long-run-batch-orchestration.json`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned `single supervised pilot selection criteria` family plus one proof matrix for validating that slice without crossing the no-real-candidate-selection, no-owner-repo-inventory widening, no-_stack execution-home widening, no deploy/publication, no `.env` or secret, and no protected-surface mutation boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one root-local pilot-admission card that preserves only the already admitted gate classes:
   - `owner_repo_count`
   - `target_kind`
   - `target_ref`
   - `objective_summary`
   - `allowed_write_scope`
   - `checkpoint_surface`
   - `verification_gate`
   - `closeout_artifact`
   - `park_or_escalation_rule`
   - `protected_surface_exclusions`
2. one fail-closed admissibility classifier that derives status from those explicit card fields only
3. one bounded rejection-reason layer that may report only the first admitted gate-failure families
4. one preserved separation layer where the criteria slice may validate one explicit candidate-card shape later but may not discover, rank, compare, or select any real repo candidate by adjacency
5. one preserved ownership boundary where the criteria slice may not infer `_stack` execution-home ownership, owner-repo readiness, or deploy/publication admissibility

The first-slice classifier may distinguish only:

- `admissible`
- `not_admissible`

## Exact Preserved Criteria Surface

The worker must preserve only:

- `owner_repo_count`
- `target_kind`
- `target_ref`
- `objective_summary`
- `allowed_write_scope`
- `checkpoint_surface`
- `verification_gate`
- `closeout_artifact`
- `park_or_escalation_rule`
- `protected_surface_exclusions`
- `status`
- `rejection_reasons`

Top-level criteria rules remain:

- `owner_repo_count` must be exactly `1`
- `target_kind` may be only `worktree` or `branch`
- `target_ref` must be explicit and non-empty
- `objective_summary` must stay bounded enough for one reviewable closeout
- `allowed_write_scope` must be explicit and must not widen into hidden surfaces
- `checkpoint_surface`, `verification_gate`, `closeout_artifact`, and `park_or_escalation_rule` must all be explicit
- `protected_surface_exclusions` must stay explicit and must fail closed when the candidate requires deploy, publication, archive/delete, `.env`, secret mutation, or other preserved protected-surface widening
- `rejection_reasons` may include only:
  - `owner_repo_count_not_one`
  - `target_not_explicit`
  - `objective_not_bounded`
  - `allowed_write_scope_missing`
  - `checkpoint_surface_missing`
  - `verification_gate_missing`
  - `closeout_artifact_missing`
  - `park_rule_missing`
  - `protected_surface_exclusions_missing`
  - `protected_surface_violation`
- no real repo discovery, repo ranking, worktree discovery, branch discovery, execution-home choice, or candidate comparison may leak into this first slice

## Exact Mandatory Proof Cases

1. complete bounded single-owner card
   - emit `status` as `admissible`
   - preserve `rejection_reasons` as `[]`

2. multiple-owner or zero-owner shape
   - emit `status` as `not_admissible`
   - preserve `owner_repo_count_not_one`

3. missing target kind or target ref
   - emit `status` as `not_admissible`
   - preserve `target_not_explicit`

4. missing bounded-control fields
   - emit `status` as `not_admissible`
   - preserve the exact missing-field reason for any omitted:
     - `allowed_write_scope`
     - `checkpoint_surface`
     - `verification_gate`
     - `closeout_artifact`
     - `park_or_escalation_rule`

5. missing or violated protected-surface boundary
   - emit `status` as `not_admissible`
   - preserve either `protected_surface_exclusions_missing` or `protected_surface_violation`

6. preserved no-comparison boundary
   - the slice may validate one explicit card shape only
   - it may not rank, discover, compare, or choose real repo candidates by adjacency

## Exact Next Package

- `AI Long-Run Batch Orchestration single supervised pilot selection criteria prompt-pack and handoff contract pass 466`

## Marker Decision

- `none`

Why:

- this pass freezes the smallest exact implementation slice and proof matrix only
- no code landing, proof execution, candidate selection, or broader operator adoption occurs here

## Rule

Freeze the smallest fail-closed pilot-criteria validator slice before admitting candidate comparison, repo discovery, execution-home choice, or owner-side implementation widening.

## Failure Mode

`Pilot By Criteria Drift`

This family becomes dishonest when the first implementation slice infers real repo candidates, execution homes, or protected-surface exceptions before the criteria card itself is validated as a bounded fail-closed shape.
