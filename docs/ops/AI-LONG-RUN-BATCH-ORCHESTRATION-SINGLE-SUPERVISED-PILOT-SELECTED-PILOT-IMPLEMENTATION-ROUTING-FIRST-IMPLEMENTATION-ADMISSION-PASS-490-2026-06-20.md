# AI Long-Run Batch Orchestration Single Supervised Pilot Selected-Pilot Implementation-Routing First-Implementation Admission Pass 490 - 2026-06-20

- Date: `2026-06-20`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Scope: `freeze the smallest fail-closed implementation slice for the root-owned selected-pilot implementation-routing family without choosing any concrete owner-side implementation packet, repo, worktree, branch, or execution home by adjacency`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-SELECTED-PILOT-IMPLEMENTATION-ROUTING-CONTRACT-FREEZE-PASS-487-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-SELECTED-PILOT-IMPLEMENTATION-ROUTING-OWNER-SURFACE-ADMISSION-PASS-488-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-SELECTED-PILOT-IMPLEMENTATION-ROUTING-SUPPORTING-LANE-ADMISSION-PASS-489-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-WINNER-SELECTION-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-20.md`
  - `ops/atlas/pilot_winner_selection.py`
  - `tests/test_atlas_pilot_winner_selection.py`
  - `docs/memory/initiatives/continuity-manifest-ai-long-run-batch-orchestration.json`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned `single supervised pilot selected-pilot implementation-routing` family plus one proof matrix for validating that slice without crossing the no-owner-repo-mutation-by-adjacency, no-live-repo-discovery, no-branch-or-worktree-enumeration, no-_stack execution-home inference, no Playbook doctrine export, no deploy/publication, no `.env` or secret, and no protected-surface mutation boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one root-local implementation-routing bundle that preserves only one already-produced winner-selection result through:
   - `selection_status`
   - `selected_pilot`
   - `selection_reasons`
2. one fail-closed routing classifier that evaluates only the already admitted routing dimensions:
   - whether `selection_status` is exactly `pilot_selected`
   - whether `selection_reasons` is exactly `[]`
   - whether `selected_pilot` still maps to one explicit candidate card already preserved by the admitted winner-selection family
   - whether that preserved selected-pilot card still carries one explicit `owner_repo_count`, `target_kind`, `target_ref`, `objective_summary`, `allowed_write_scope`, `checkpoint_surface`, `verification_gate`, `closeout_artifact`, `park_or_escalation_rule`, and `protected_surface_exclusions` surface without hidden repo discovery, branch/worktree enumeration, owner-repo mutation authority, `_stack` execution-home inference, or Playbook doctrine export inference
3. one bounded routing-status layer that may emit only:
   - `implementation_route_admissible`
   - `no_route`
4. one bounded implementation-route layer that may emit only one explicit `selected_pilot` candidate card already present in the bundle or `null`
5. one preserved separation layer where the routing slice may classify whether one explicit selected pilot is routeable to one later downstream implementation packet but may not choose an owner repo, worktree, branch, execution home, `_stack` command/runtime home, worker packet, or deploy/publication path
6. one preserved ownership boundary where the routing slice may not treat Playbook doctrine reuse, owner-repo readiness, deploy/publication, archive/delete, `.env`, secret work, or protected-surface exceptions as route-enabling evidence

## Exact Preserved Routing Surface

The worker must preserve only:

- `selection_status`
- `selected_pilot`
- `selection_reasons`
- `routing_status`
- `implementation_route`
- `routing_reasons`

Top-level routing rules remain:

- `selection_status` may include only:
  - `pilot_selected`
  - `no_selection`
- `selected_pilot` may be inspected only through:
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
- `routing_status` may include only:
  - `implementation_route_admissible`
  - `no_route`
- `implementation_route` may be either:
  - the exact explicit `selected_pilot` card
  - `null`
- `implementation_route` may be non-null only when:
  - `selection_status` is `pilot_selected`
  - `selection_reasons` is `[]`
  - `selected_pilot` is one explicit candidate card already present in the bundle
  - that card does not require hidden repo discovery, hidden branch/worktree enumeration, owner-repo mutation authority, `_stack` execution-home inference, Playbook doctrine export inference, deploy/publication, archive/delete, `.env`, or secret work as a route-enabling factor
- `routing_reasons` may include only:
  - `selection_status_not_pilot_selected`
  - `selection_reasons_present`
  - `selected_pilot_missing`
  - `selected_pilot_not_explicit`
  - `protected_surface_violation`
  - `repo_discovery_invented`
  - `branch_worktree_enumeration_invented`
  - `execution_home_inference_invented`
  - `owner_repo_mutation_invented`
  - `playbook_doctrine_export_invented`
- no live repo discovery, branch discovery, worktree discovery, owner-repo inventory expansion, execution-home choice, `_stack` helper-home choice, Playbook doctrine export, or concrete owner-side implementation selection may leak into this first slice

## Exact Mandatory Proof Cases

1. explicit `pilot_selected` with empty selection reasons
   - emit `routing_status` as `implementation_route_admissible`
   - preserve `implementation_route` as the explicit `selected_pilot` card
   - preserve `routing_reasons` as `[]`

2. `no_selection` selection status
   - emit `routing_status` as `no_route`
   - preserve `implementation_route` as `null`
   - preserve `selection_status_not_pilot_selected`

3. non-empty selection reasons despite `pilot_selected`
   - emit `routing_status` as `no_route`
   - preserve `implementation_route` as `null`
   - preserve `selection_reasons_present`

4. missing or non-explicit `selected_pilot`
   - emit `routing_status` as `no_route`
   - preserve `implementation_route` as `null`
   - preserve either `selected_pilot_missing` or `selected_pilot_not_explicit`

5. preserved `selected_pilot` violates the admitted protected-surface boundary
   - emit `routing_status` as `no_route`
   - preserve `implementation_route` as `null`
   - preserve `protected_surface_violation`

6. routing argument invents live repo discovery or branch/worktree enumeration
   - emit `routing_status` as `no_route`
   - preserve `repo_discovery_invented` or `branch_worktree_enumeration_invented`

7. routing argument invents owner-repo mutation authority or `_stack` execution-home inference
   - emit `routing_status` as `no_route`
   - preserve `owner_repo_mutation_invented` or `execution_home_inference_invented`

8. routing argument invents Playbook doctrine export
   - emit `routing_status` as `no_route`
   - preserve `playbook_doctrine_export_invented`

## Exact Next Package

- `AI Long-Run Batch Orchestration single supervised pilot selected-pilot implementation-routing prompt-pack and handoff contract pass 491`

## Marker Decision

- `none`

Why:

- this pass freezes the smallest exact implementation slice and proof matrix only
- no code landing, proof execution, concrete owner-side implementation routing, or broader operator adoption occurs here

## Rule

Freeze the smallest fail-closed selected-pilot implementation-routing slice before admitting prompt-pack routing, worker touch surfaces, owner-repo mutation, `_stack` execution-home doctrine, or Playbook doctrine export.

## Failure Mode

`Selected-Pilot Implementation Routing By Adjacency Drift`

This family becomes dishonest when the first implementation slice treats one explicit `selected_pilot` card as enough to choose an owner repo, enumerate branches/worktrees, infer `_stack` execution-home doctrine, export doctrine to Playbook, or launch concrete implementation work before those later boundaries are separately admitted.
