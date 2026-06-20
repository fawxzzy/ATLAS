# AI Long-Run Batch Orchestration Single Supervised Pilot Winner Selection Prompt-Pack And Handoff Contract Pass 484 - 2026-06-20

- Date: `2026-06-20`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded prompt-pack and handoff contract`
- Scope: `freeze the exact worker objective, proof obligations, allowed-touch boundary, and stop conditions for the already-admitted fail-closed pilot winner-selection slice`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-WINNER-SELECTION-CONTRACT-FREEZE-PASS-480-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-WINNER-SELECTION-OWNER-SURFACE-ADMISSION-PASS-481-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-WINNER-SELECTION-SUPPORTING-LANE-ADMISSION-PASS-482-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-WINNER-SELECTION-FIRST-IMPLEMENTATION-ADMISSION-PASS-483-2026-06-20.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-SINGLE-SUPERVISED-PILOT-WINNER-CONVERSION-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-20.md`
  - `ops/atlas/pilot_winner_conversion.py`
  - `tests/test_atlas_pilot_winner_conversion.py`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-owned `single supervised pilot winner selection` family.

This pass does not:

- implement code
- choose one live owner-side pilot repo, worktree, branch, or execution home by adjacency
- reopen winner conversion, selector redesign, or queue-or-registry doctrine
- infer `_stack` execution-home ownership, owner-readiness tie-breaking, or owner-repo implementation posture
- reopen deploy/publication, archive/delete, `.env`, or secret work
- widen into manifest, restart-surface, runtime-state, or broader orchestration redesign

## Root Health Baseline

- pass 480 already froze the exact winner-selection contract
- pass 481 already admitted ATLAS root as the owner-facing home for that selection seam
- pass 482 already proved separate support still honestly holds at `none yet`
- pass 483 already froze the exact first implementation slice and exact proof matrix around the admitted conversion-status, pilot-winner, selected-pilot, and rejection surfaces
- root validation is currently clean at `critical=0 error=0 warning=10 info=0`

## Inherited Contract Spine

The future worker must inherit exactly:

- pass 480 exact winner-selection contract
- pass 481 root control-plane owner admission
- pass 482 supporting-lane hold at `none yet`
- pass 483 exact first implementation slice and exact proof matrix

No worker may reinterpret those seams as suggestions.
They are contract inputs.

## Exact Worker Objective

The next worker is allowed to pursue one exact implementation objective only:

- implement one root-local fail-closed pilot-winner selection helper in `ops/atlas/pilot_winner_selection.py` plus one direct proof file in `tests/test_atlas_pilot_winner_selection.py` so the helper preserves only `conversion_status`, `pilot_winner`, `conversion_reasons`, `selection_status`, `selected_pilot`, and `selection_reasons`, converts only an explicit `winner_selected` conversion result with one explicit `pilot_winner` card and empty conversion reasons into the exact explicit selected-pilot card already present in the bundle, emits only `pilot_selected` or `no_selection`, reports only the admitted `selection_reasons`, fails closed on hidden or widened selection inputs, and proves behavior against the frozen pass-483 matrix

The worker is not allowed to pursue:

- live repo discovery
- branch or worktree enumeration from live repos
- owner-readiness tie-breaking or `_stack` execution-home inference
- owner-repo edits
- broader selector, manifest, restart-surface, runtime-inventory, or queue-or-registry redesign

## Exact Preserved Selection Surface

The worker must preserve exactly these surfaces:

- `conversion_status`
- `pilot_winner`
- `conversion_reasons`
- `selection_status`
- `selected_pilot`
- `selection_reasons`

The worker may render these surfaces only.
The worker may not widen them into live repo inventory, branch inventory, worktree inventory, owner-readiness doctrine, owner-repo mutation authority, worker launch or routing authority, execution-home choice, deploy/publication semantics, or protected-surface exceptions.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

1. explicit `winner_selected` result with empty conversion reasons
   - preserve `selection_status` as `pilot_selected`
   - preserve `selected_pilot` as the explicit `pilot_winner` card
   - preserve `selection_reasons` as `[]`

2. `no_winner` conversion status
   - preserve `selection_status` as `no_selection`
   - preserve `selected_pilot` as `null`
   - preserve `conversion_status_not_winner_selected`

3. non-empty conversion reasons despite `winner_selected`
   - preserve `selection_status` as `no_selection`
   - preserve `selected_pilot` as `null`
   - preserve `conversion_reasons_present`

4. missing or non-explicit `pilot_winner`
   - preserve `selection_status` as `no_selection`
   - preserve either `pilot_winner_missing` or `pilot_winner_not_explicit`

5. selected-winner argument invents repo discovery, owner-readiness tie-breaking, execution-home tie-breaking, or owner-repo mutation/worker-launch authority
   - preserve `selection_status` as `no_selection`
   - preserve the exact corresponding selection reason

6. preserved `pilot_winner` violates the admitted protected-surface boundary
   - preserve `selection_status` as `no_selection`
   - preserve `protected_surface_violation`

## Exact No-Mutation / No-Discovery / No-Owner-Routing-By-Adjacency Boundary

The worker must carry this wording forward verbatim:

`No-mutation, no-discovery, and no-owner-routing-by-adjacency guard: this packet may implement one explicit fail-closed winner-selection helper plus direct proof for the already-admitted conversion_status, pilot_winner, conversion_reasons, selection_status, selected_pilot, and selection_reasons surfaces, but it may not discover live repos beyond the explicit preserved winner card, enumerate worktrees or branches, infer owner readiness or execution-home ownership, widen one contract-local selected pilot into owner-repo mutation or _stack execution-home choice, mutate queue, registry, runtime, session, merge, manifest, archive, repair, blocker, or owner-repo state, or widen into deploy, publication, .env, secret, or protected-surface work.`

## Exact No Hidden Transcript-State Inference Boundary

The worker must carry this rule forward:

- use only the cited durable surfaces in this receipt chain plus the admitted conversion helper/test files and the new selection helper/test files
- do not infer winner-selection truth, owner readiness, execution-home meaning, or protected-surface exceptions from uncited transcript memory or broad root residue

## Exact Allowed Future Implementation Surfaces

The worker may touch only:

- `ops/atlas/pilot_winner_selection.py`
- `tests/test_atlas_pilot_winner_selection.py`

## Exact Forbidden Future Implementation Surfaces

The worker must not touch:

- `ops/atlas/marker_knockout_selector.py`
- `ops/atlas/continuity.py`
- `ops/atlas/pilot_selection_criteria.py`
- `ops/atlas/pilot_candidate_comparison.py`
- `ops/atlas/pilot_winner_conversion.py`
- `tests/test_atlas_pilot_selection_criteria.py`
- `tests/test_atlas_pilot_candidate_comparison.py`
- `tests/test_atlas_pilot_winner_conversion.py`
- `docs/atlas-book/*`
- `docs/memory/initiatives/*`
- owner repos under `repos/*`
- `_stack` helper-runtime or command-design surfaces
- `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, `.playwright-mcp/`, or broad untracked root backlog

## Exact Stop Conditions

The worker must stop and return immediately if the slice requires:

- real repo discovery or winner selection beyond the explicit preserved `pilot_winner` card
- worktree or branch enumeration from live repos
- owner-readiness tie-breaking, owner-repo mutation, or execution-home inference
- owner-repo edits
- deploy/publication, `.env`, secret, archive/delete, or protected-surface touch
- new selection-status values, new selection-reason values, or widened conversion/winner fields beyond the admitted set
- selector, manifest, restart-surface, or runtime-state edits to make the helper work

If one of those triggers appears, the work is no longer valid first-slice implementation work.

## Exact Handoff Prompt-Pack Spine

Any future worker prompt-pack must include:

1. the exact implementation objective
2. the inherited passes 480 through 483 as frozen inputs
3. the exact preserved selection surface
4. the exact proof matrix
5. the exact no-mutation, no-discovery, and no-owner-routing-by-adjacency guard verbatim
6. the exact no-hidden-transcript-state boundary
7. the exact allowed-touch and forbidden-touch surfaces
8. the exact stop-and-return conditions

Mirror surfaces may restate this spine.
They may not redefine it.

## Exact Next Package

- `AI Long-Run Batch Orchestration single supervised pilot winner selection implementation-readiness closeout and worker-routing pass 485`

## Marker Decision

- `none`

Why:

- this pass narrows the worker handoff contract only
- no new executed state, broader proof-backed adoption, or blocker clearance landed

## Rule

Freeze the worker handoff contract before authorizing any first-slice implementation work for the root-owned pilot winner-selection family.

## Failure Mode

`Pilot-Winner-Selection Handoff Drift`

This family becomes dishonest when the worker handoff contract stays implicit and the first winner-selection slice expands through prompt wording into owner-repo mutation, live repo discovery, execution-home inference, or protected-surface exceptions that the durable chain has not admitted.
