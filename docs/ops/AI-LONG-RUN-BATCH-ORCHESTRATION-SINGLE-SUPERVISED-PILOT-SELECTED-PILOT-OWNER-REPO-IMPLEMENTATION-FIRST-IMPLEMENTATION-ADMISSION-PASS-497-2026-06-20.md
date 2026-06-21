# AI Long-Run Batch Orchestration Single Supervised Pilot Selected-Pilot Owner-Repo Implementation First-Implementation Admission Pass 497 - 2026-06-20

- Date: `2026-06-20`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Scope: `freeze the smallest fail-closed implementation slice for the root-owned selected-pilot owner-repo implementation family without choosing any concrete owner-side mutation packet, branch, worktree, or execution home by adjacency`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-SELECTED-PILOT-OWNER-REPO-IMPLEMENTATION-CONTRACT-FREEZE-PASS-494-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-SELECTED-PILOT-OWNER-REPO-IMPLEMENTATION-OWNER-SURFACE-ADMISSION-PASS-495-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-SELECTED-PILOT-OWNER-REPO-IMPLEMENTATION-SUPPORTING-LANE-ADMISSION-PASS-496-2026-06-20.md`
  - `docs/memory/initiatives/continuity-manifest-ai-long-run-batch-orchestration.json`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned `single supervised pilot selected-pilot owner-repo implementation` family plus one proof matrix for validating that slice without crossing the no-owner-repo-mutation-by-adjacency, no-live-repo-discovery, no-branch-or-worktree-enumeration, no-_stack execution-home inference, no Playbook doctrine export, no deploy/publication, no `.env` or secret, and no protected-surface mutation boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one root-local owner-repo implementation bundle that preserves only one already-produced implementation-routing result through:
   - `selection_status`
   - `selection_reasons`
   - `routing_status`
   - `implementation_route`
   - `routing_reasons`
2. one fail-closed implementation classifier that evaluates only the already admitted implementation dimensions:
   - whether `routing_status` is exactly `implementation_route_admissible`
   - whether `routing_reasons` is exactly `[]`
   - whether `implementation_route` still maps to one explicit candidate card already preserved by the admitted implementation-routing family
   - whether that preserved implementation-route card still carries one explicit `owner_repo_count`, `target_kind`, `target_ref`, `objective_summary`, `allowed_write_scope`, `checkpoint_surface`, `verification_gate`, `closeout_artifact`, `park_or_escalation_rule`, and `protected_surface_exclusions` surface without hidden repo discovery, branch/worktree enumeration, owner-repo mutation authority, `_stack` execution-home inference, or Playbook doctrine export inference
3. one bounded implementation-status layer that may emit only:
   - `owner_repo_implementation_admissible`
   - `no_owner_repo_implementation`
4. one bounded owner-repo implementation layer that may emit only one explicit `implementation_route` candidate card already present in the bundle or `null`
5. one preserved separation layer where the implementation slice may classify whether one explicit implementation-route card is admissible for one later downstream owner-side implementation packet but may not choose a branch, worktree, execution home, `_stack` command/runtime home, worker packet, or deploy/publication path
6. one preserved ownership boundary where the implementation slice may not treat Playbook doctrine reuse, owner-repo readiness, deploy/publication, archive/delete, `.env`, secret work, or protected-surface exceptions as implementation-enabling evidence

## Exact Preserved Implementation Surface

The worker must preserve only:

- `selection_status`
- `selection_reasons`
- `routing_status`
- `implementation_route`
- `routing_reasons`
- `implementation_status`
- `owner_repo_implementation`
- `implementation_reasons`

Top-level implementation rules remain:

- `routing_status` may include only:
  - `implementation_route_admissible`
  - `no_route`
- `implementation_route` may be inspected only through:
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
- `implementation_status` may include only:
  - `owner_repo_implementation_admissible`
  - `no_owner_repo_implementation`
- `owner_repo_implementation` may be either:
  - the exact explicit `implementation_route` card
  - `null`
- `owner_repo_implementation` may be non-null only when:
  - `routing_status` is `implementation_route_admissible`
  - `routing_reasons` is `[]`
  - `implementation_route` is one explicit candidate card already present in the bundle
  - that card does not require hidden repo discovery, hidden branch/worktree enumeration, owner-repo mutation authority, `_stack` execution-home inference, Playbook doctrine export inference, deploy/publication, archive/delete, `.env`, or secret work as an implementation-enabling factor
- `implementation_reasons` may include only:
  - `routing_status_not_implementation_route_admissible`
  - `routing_reasons_present`
  - `implementation_route_missing`
  - `implementation_route_not_explicit`
  - `protected_surface_violation`
  - `repo_discovery_invented`
  - `branch_worktree_enumeration_invented`
  - `execution_home_inference_invented`
  - `owner_repo_mutation_invented`
  - `playbook_doctrine_export_invented`
- no live repo discovery, branch discovery, worktree discovery, owner-repo inventory expansion, execution-home choice, `_stack` helper-home choice, Playbook doctrine export, or concrete owner-side implementation selection may leak into this first slice

## Exact Mandatory Proof Cases

1. explicit `implementation_route_admissible` result with empty routing reasons
   - emit `implementation_status` as `owner_repo_implementation_admissible`
   - preserve `owner_repo_implementation` as the explicit `implementation_route` card
   - preserve `implementation_reasons` as `[]`

2. `no_route` routing status
   - emit `implementation_status` as `no_owner_repo_implementation`
   - preserve `owner_repo_implementation` as `null`
   - preserve `routing_status_not_implementation_route_admissible`

3. non-empty routing reasons despite `implementation_route_admissible`
   - emit `implementation_status` as `no_owner_repo_implementation`
   - preserve `owner_repo_implementation` as `null`
   - preserve `routing_reasons_present`

4. missing or non-explicit `implementation_route`
   - emit `implementation_status` as `no_owner_repo_implementation`
   - preserve `owner_repo_implementation` as `null`
   - preserve either `implementation_route_missing` or `implementation_route_not_explicit`

5. preserved `implementation_route` violates the admitted protected-surface boundary
   - emit `implementation_status` as `no_owner_repo_implementation`
   - preserve `owner_repo_implementation` as `null`
   - preserve `protected_surface_violation`

6. implementation argument invents live repo discovery or branch/worktree enumeration
   - emit `implementation_status` as `no_owner_repo_implementation`
   - preserve `repo_discovery_invented` or `branch_worktree_enumeration_invented`

7. implementation argument invents owner-repo mutation authority or `_stack` execution-home inference
   - emit `implementation_status` as `no_owner_repo_implementation`
   - preserve `owner_repo_mutation_invented` or `execution_home_inference_invented`

8. implementation argument invents Playbook doctrine export
   - emit `implementation_status` as `no_owner_repo_implementation`
   - preserve `playbook_doctrine_export_invented`

## Exact Next Package

- `AI Long-Run Batch Orchestration single supervised pilot selected-pilot owner-repo implementation prompt-pack and handoff contract pass 498`

## Marker Decision

- `none`

Why:

- this pass freezes the smallest exact implementation slice and proof matrix only
- no code landing, proof execution, concrete owner-side implementation routing, or broader operator adoption occurs here

## Rule

Freeze the smallest fail-closed selected-pilot owner-repo implementation slice before admitting prompt-pack routing, worker touch surfaces, owner-repo mutation, `_stack` execution-home doctrine, or Playbook doctrine export.

## Failure Mode

`Selected-Pilot Owner-Repo Implementation By Adjacency Drift`

This family becomes dishonest when the first implementation slice treats one explicit `implementation_route` card as enough to choose an owner-side mutation packet, enumerate branches/worktrees, infer `_stack` execution-home doctrine, export doctrine to Playbook, or launch concrete implementation work before those later boundaries are separately admitted.
