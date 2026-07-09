# AI Long-Run Batch Orchestration cross-marker opportunity planner-integration first-implementation admission

- Date: `2026-07-09`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `ATLAS-root docs-only first-implementation admission`
- Control-plane checkpoint: `4b64ba9c3254cea769da92b19ab0c0ae77d96f19`
- Marker movement: none

## Decision

Admit one bounded planner/test update so the marker-aware planner can consume cross-marker opportunity output as advisory candidate context without inventing packets or widening authority.

The next exact packet is:

```text
AI Long-Run Batch Orchestration cross-marker opportunity planner-integration prompt-pack and worker handoff contract
```

This admission does not land the planner integration, mutate manifests programmatically, reopen held markers, or move any marker.

## Admitted Future Surfaces

Only these future files are admitted:

- `ops/atlas/marker_aware_next_packet_planner.py`
- `tests/test_atlas_marker_aware_next_packet_planner.py`

No other file is admitted by this packet.

## Objective

Freeze the smallest honest implementation slice that can:

1. read the existing cross-marker opportunity helper report as advisory input
2. attach deterministic advisory evidence fields to matching planner candidates
3. apply bounded score uplift only when continuity truth already names an explicit non-held safe packet
4. preserve held behavior when the opportunity remains real but non-executable

## Required Candidate Evidence Fields

The future planner implementation may add only bounded candidate-level cross-marker evidence:

- `cross_marker_signal_applied`
- `cross_marker_source_receipt`
- `cross_marker_source_marker`
- `cross_marker_candidate_marker`
- `cross_marker_required_follow_up_packet`
- `cross_marker_reason`
- `cross_marker_score_bonus`

The future planner may also retain base score truth explicitly when helpful for deterministic proof.

## Required Safety Behavior

The future implementation must:

- keep helper consumption advisory-only
- reject invented packets from helper wording alone
- keep held candidates held when the follow-up remains `No immediate ...`
- preserve existing owner-lane, workflow, deploy, secret, protected-surface, and final-receipt denials
- keep Fitness and Mazer outside ATLAS-root fallback routing
- preserve deterministic candidate ordering

## Required Cross-Marker Rules

The future planner may apply a bounded score uplift only when all of these are true:

1. the helper reports `status=ok`
2. the helper reports `safe_to_use=true`
3. the candidate marker matches a planner candidate already loaded from admitted continuity truth
4. the required follow-up packet is explicit and non-held
5. the planner candidate is already a safe selectable class without cross-marker invention

If any of those are false, the signal must stay advisory-only.

## Required Proof Matrix

Future proof must cover at least:

1. a live-style non-actionable opportunity that stays advisory-only because the follow-up remains `No immediate ...`
2. a synthetic actionable opportunity that adds bounded score uplift to an explicit non-held docs-only packet
3. preservation of current planner classification behavior outside the new advisory fields
4. preservation of deterministic JSON ordering
5. preservation of protected input/output rejection and authority denials

## Not Yet Admitted

This packet does not yet admit:

- exact proof command strings
- exact mock or live test fixture wording
- implementation readiness verdict
- worker execution

Those belong to the next prompt-pack packet.

## Marker Decision

No marker moves.

`AI Long-Run Batch Orchestration` remains `70%`.

## Next

Open only this next packet:

```text
AI Long-Run Batch Orchestration cross-marker opportunity planner-integration prompt-pack and worker handoff contract
```
