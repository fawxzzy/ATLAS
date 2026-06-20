# AI Long-Run Batch Orchestration Single Supervised Pilot Winner Selection First-Implementation Admission Pass 483 - 2026-06-20

- Date: `2026-06-20`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Scope: `freeze the smallest fail-closed implementation slice for the root-owned pilot winner-selection family without choosing any live owner-side implementation, repo, worktree, branch, or execution home by adjacency`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-WINNER-SELECTION-CONTRACT-FREEZE-PASS-480-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-WINNER-SELECTION-OWNER-SURFACE-ADMISSION-PASS-481-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-WINNER-SELECTION-SUPPORTING-LANE-ADMISSION-PASS-482-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-WINNER-CONVERSION-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-20.md`
  - `ops/atlas/pilot_winner_conversion.py`
  - `tests/test_atlas_pilot_winner_conversion.py`
  - `docs/memory/initiatives/continuity-manifest-ai-long-run-batch-orchestration.json`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned `single supervised pilot winner selection` family plus one proof matrix for validating that slice without crossing the no-owner-repo-mutation-by-adjacency, no-live-repo-discovery, no-_stack execution-home widening, no deploy/publication, no `.env` or secret, and no protected-surface mutation boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one root-local winner-selection bundle that preserves only one already-produced winner-conversion result through:
   - `conversion_status`
   - `pilot_winner`
   - `conversion_reasons`
2. one fail-closed selection classifier that evaluates only the already admitted selection dimensions:
   - whether `conversion_status` is exactly `winner_selected`
   - whether `conversion_reasons` is exactly `[]`
   - whether `pilot_winner` still maps to one explicit candidate card already preserved by the admitted conversion family
   - whether that preserved winner card still carries one explicit `target_kind`, `target_ref`, and protected-surface boundary without hidden repo, branch, or worktree discovery
3. one bounded selection-status layer that may emit only:
   - `pilot_selected`
   - `no_selection`
4. one bounded selected-pilot layer that may emit only one explicit `pilot_winner` candidate card already present in the bundle or `null`
5. one preserved separation layer where the selection slice may convert one explicit contract-local `pilot_winner` card into one contract-local lane-level selected pilot but may not infer owner-repo mutation authority, worker launch or routing authority, `_stack` helper-home ownership, branch/worktree discovery, or live execution-home choice
6. one preserved ownership boundary where the selection slice may not treat owner-readiness tie-breaking, deploy/publication, archive/delete, `.env`, secret work, or hidden owner-side proof posture as deciding factors

## Exact Preserved Selection Surface

The worker must preserve only:

- `conversion_status`
- `pilot_winner`
- `conversion_reasons`
- `selection_status`
- `selected_pilot`
- `selection_reasons`

Top-level selection rules remain:

- `conversion_status` may include only:
  - `winner_selected`
  - `no_winner`
- `selection_status` may include only:
  - `pilot_selected`
  - `no_selection`
- `selected_pilot` may be either:
  - the exact explicit `pilot_winner` card
  - `null`
- `selected_pilot` may be non-null only when:
  - `conversion_status` is `winner_selected`
  - `conversion_reasons` is `[]`
  - `pilot_winner` is one explicit candidate card already present in the bundle
  - that card does not require hidden repo discovery, hidden branch/worktree discovery, owner-readiness tie-breaking, owner-repo mutation authority, worker-launch authority, or `_stack` execution-home choice as a deciding factor
- `selection_reasons` may include only:
  - `conversion_status_not_winner_selected`
  - `conversion_reasons_present`
  - `pilot_winner_missing`
  - `pilot_winner_not_explicit`
  - `protected_surface_violation`
  - `repo_discovery_invented`
  - `owner_readiness_tiebreak_invented`
  - `execution_home_tiebreak_invented`
  - `owner_repo_mutation_invented`
- no live repo discovery, branch discovery, worktree discovery, owner-repo inventory expansion, execution-home choice, `_stack` helper-home choice, or owner-side implementation selection may leak into this first slice

## Exact Mandatory Proof Cases

1. explicit `winner_selected` with empty conversion reasons
   - emit `selection_status` as `pilot_selected`
   - preserve `selected_pilot` as the explicit `pilot_winner` card
   - preserve `selection_reasons` as `[]`

2. `no_winner` conversion status
   - emit `selection_status` as `no_selection`
   - preserve `selected_pilot` as `null`
   - preserve `conversion_status_not_winner_selected`

3. non-empty conversion reasons despite `winner_selected`
   - emit `selection_status` as `no_selection`
   - preserve `selected_pilot` as `null`
   - preserve `conversion_reasons_present`

4. missing or non-explicit `pilot_winner`
   - emit `selection_status` as `no_selection`
   - preserve either `pilot_winner_missing` or `pilot_winner_not_explicit`

5. selected-winner argument invents repo discovery, owner-readiness tie-breaking, execution-home tie-breaking, or owner-repo mutation/worker-launch authority
   - emit `selection_status` as `no_selection`
   - preserve the exact corresponding selection reason

6. preserved `pilot_winner` violates the admitted protected-surface boundary
   - emit `selection_status` as `no_selection`
   - preserve `protected_surface_violation`

## Exact Next Package

- `AI Long-Run Batch Orchestration single supervised pilot winner selection prompt-pack and handoff contract pass 484`

## Marker Decision

- `none`

Why:

- this pass freezes the smallest exact implementation slice and proof matrix only
- no code landing, proof execution, live owner-side pilot routing, or broader operator adoption occurs here

## Rule

Freeze the smallest fail-closed pilot winner-selection slice before admitting prompt-pack routing, owner-repo implementation widening, or `_stack` execution-home semantics.

## Failure Mode

`Pilot Winner Selection By Adjacency Drift`

This family becomes dishonest when the first implementation slice invents owner-repo mutation authority, worker launch or routing authority, repo discovery, or execution-home doctrine instead of selecting only one already-preserved explicit `pilot_winner` card under the frozen fail-closed rules.
