# AI Long-Run Batch Orchestration cross-marker opportunity planner-integration prompt-pack and worker handoff contract

- Date: `2026-07-09`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `ATLAS-root docs-only prompt-pack contract`
- Control-plane checkpoint: `4b64ba9c3254cea769da92b19ab0c0ae77d96f19`
- Marker movement: none

## Worker Objective

Implement one bounded planner/test update so `ops/atlas/marker_aware_next_packet_planner.py` can consume `ops/atlas/cross_marker_ratchet_opportunity.py` output as advisory candidate context, preserve current held behavior, and apply only bounded score uplift when continuity truth already names a safe non-held packet.

## Exact Files

The worker may touch only:

- `ops/atlas/marker_aware_next_packet_planner.py`
- `tests/test_atlas_marker_aware_next_packet_planner.py`

## Exact Integration Contract

The worker must:

1. call the existing cross-marker helper through a root-owned read-only report surface
2. ignore the signal entirely if the helper is not `status=ok` or not `safe_to_use=true`
3. match opportunities to already-loaded planner candidates by marker
4. keep non-actionable opportunities advisory-only
5. apply bounded score uplift only for explicit non-held selectable packets already named by continuity truth

## Exact Non-Actionable Hold Branch

When the matched follow-up packet is:

```text
No immediate ...
```

the worker must:

- keep `cross_marker_signal_applied=false`
- keep `cross_marker_score_bonus=0`
- preserve the candidate classification
- preserve held-root behavior
- expose the advisory signal fields without converting the candidate into a selected packet

## Exact Bounded Uplift Branch

When a matched candidate already has an explicit non-held safe packet, the worker may:

- keep the existing candidate classification
- retain the base score explicitly
- apply only one bounded uplift
- preserve existing score hierarchy so docs-only uplift does not outrank safer implementation-ready or immediate classes by novelty alone

## Exact Proof Commands

The worker must run:

1. `python -m unittest tests.test_atlas_marker_aware_next_packet_planner -v`
2. `python ops/atlas/marker_aware_next_packet_planner.py --json`
3. `python ops/validation/validate_stack.py`
4. `git status --short`
5. `git diff --name-only`

## Exact Forbidden Authority

The worker must not:

- edit or dispatch workflows
- touch owner repos
- touch Fitness or Mazer working trees
- read secrets or `.env*`
- touch deploy or platform surfaces
- move markers
- emit final receipts
- widen into queue-helper or selector-helper edits
- invent a packet from cross-marker helper wording alone

## Exact Stop Conditions

Stop and return without implementation if the worker would require:

- new helper files
- queue-helper edits
- selector edits
- owner-lane mutation
- deploy, workflow, or secret authority
- packet invention from helper wording without explicit continuity truth

## Next

Open only this next packet:

```text
AI Long-Run Batch Orchestration cross-marker opportunity planner-integration implementation-readiness closeout and worker routing
```
