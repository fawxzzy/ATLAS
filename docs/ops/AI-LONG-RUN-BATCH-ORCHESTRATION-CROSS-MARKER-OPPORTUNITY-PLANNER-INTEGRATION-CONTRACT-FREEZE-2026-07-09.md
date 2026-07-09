# AI Long-Run Batch Orchestration cross-marker opportunity planner-integration contract freeze

- Date: `2026-07-09`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `ATLAS-root docs-only contract freeze`
- Control-plane checkpoint: `dd8603f3105792e80385c7b602fc5e66fc9efe82`
- Marker movement: none; `AI Long-Run Batch Orchestration` remains `70%`

## Decision

Freeze the planner-integration contract for cross-marker opportunities.

The next exact packet is:

```text
AI Long-Run Batch Orchestration cross-marker opportunity planner-integration first-implementation admission
```

This receipt does not implement the integration, mutate manifests programmatically, change queue behavior directly, dispatch work, or move any marker.

## Objective

The future integration must let `ops/atlas/marker_aware_next_packet_planner.py` consume `ops/atlas/cross_marker_ratchet_opportunity.py` output as an advisory signal when ranking or surfacing bounded root packets.

The integration is advisory only. It may improve candidate visibility and safe packet selection. It must not create execution authority, marker-write authority, or final-receipt authority.

## Why Helper Output Alone Is Not Enough

The landed helper proves one safe cross-marker opportunity, but the planner still returns no selected packet and the hour-block queue still suppresses generic continuation.

That means the missing contract is not "find more opportunities." It is "define when an opportunity is strong enough to affect planner output, and when it must remain advisory while the root stays held."

## Admitted Inputs

Future implementation may consume only root-owned, reproducible inputs:

- `docs/memory/initiatives/continuity-manifest-*.json`
- `docs/ops/*.md` receipts already admitted by the existing planner and opportunity helper
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `ops/atlas/cross_marker_ratchet_opportunity.py` live report or `build_report(...)` output
- existing marker-aware planner candidate set
- stack validation output only as advisory context

Future implementation must stay inside the existing planner's admitted root-owned source model.

## Excluded Inputs

Future implementation must reject or ignore:

- owner-repo source truth used directly as planner authority
- hidden transcripts or chat memory
- uncommitted diffs
- `.env*`, `secrets/**`, deploy/platform state, workflow state, `.vercel/**`, `.playwright-mcp/**`, `archive/**`
- green CI without receipt-backed ratchet reasons
- any packet suggestion that requires owner fallback, protected proof, deploy, workflow dispatch, or secret handling

## Cross-Marker Proof Reuse Model

Planner integration may treat a cross-marker opportunity as real only when all of these are true:

1. `cross_marker_ratchet_opportunity.py` reports `safe_to_use=true`.
2. The opportunity class is implementation-backed, not docs-only.
3. Separate marker receipts already cite distinct ratchet reasons for the shared proof cluster.
4. The candidate marker remains root-owned or root-advisory rather than owner-lane-owned.
5. The suggested follow-up stays inside ATLAS root authority.

If any of those are false, the signal is non-actionable and must not influence packet selection.

## Advisory Scoring Model

The future planner may add a cross-marker signal only after base candidate classification is complete.

Required behavior:

- base planner safety rules still win first
- unsafe, owner-lane, deploy, workflow, protected-surface, and secret-adjacent candidates remain rejected
- held candidates remain held unless the cross-marker signal points to a separately admitted non-held packet
- docs-only packets may be selected only when they already exist as explicit next-package truth

Allowed scoring effect:

- add one bounded advisory score bonus when a candidate marker has both:
  - a safe cross-marker opportunity
  - an explicit non-held next packet already named in continuity truth

Disallowed scoring effect:

- invent a packet from helper wording alone
- convert `No immediate ... same-lane packet` into an executable packet
- outrank an existing safer exact packet by cross-marker novelty alone

## Selected-Packet Output Behavior

If the signal is actionable, the future planner may:

- keep the existing candidate classification
- attach cross-marker evidence fields to the selected candidate
- choose the candidate only when its next packet is already explicit and safe

Expected added evidence fields:

- `cross_marker_signal_applied`
- `cross_marker_source_receipt`
- `cross_marker_source_marker`
- `cross_marker_candidate_marker`
- `cross_marker_required_follow_up_packet`
- `cross_marker_reason`

The planner must still emit one deterministic selected packet or `null`.

## No-Action Hold Behavior

If the helper reports an opportunity but the follow-up remains `No immediate ... same-lane packet`, the planner must:

- keep `selected_packet=null`
- keep the lane held
- expose the opportunity as advisory context only
- preserve the current suppression-safe behavior for generic ATLAS-root continuation

The current live Cortex-to-Playbook/Cortex opportunity is the motivating example for this hold-preserving branch.

## False-Positive Prevention

The future integration must fail closed when:

- the opportunity source is docs-only
- the opportunity helper reports blocked candidates only
- the candidate marker has no explicit next packet
- the candidate marker's next packet is itself a hold packet
- conflicting marker posture exists across book, manifest, or governing receipts
- one proof cluster is double-counted inside one marker lane
- the signal would route owner-lane, deploy, workflow, or protected proof work by fallback

## Future Implementation Surfaces

The next admitted implementation surface may include only:

- `ops/atlas/marker_aware_next_packet_planner.py`
- `tests/test_atlas_marker_aware_next_packet_planner.py`

This packet does not admit queue helper edits, selector edits, or any new helper file.

## Future Proof Matrix

The future first implementation must prove:

- a safe cross-marker signal can be attached to planner output deterministically
- a candidate with explicit non-held next-package truth can receive bounded advisory score uplift
- the current Cortex-to-Playbook/Cortex opportunity remains advisory-only because the candidate lane still has no immediate same-lane packet
- docs-only receipts do not become cross-marker planner signals
- owner-lane, protected-surface, secret, deploy, and workflow signals remain rejected
- selected packet output remains deterministic
- planner still fails closed when no safe packet exists

## Authority Denials

The future integration must continue to deny:

- marker write authority
- final receipt authority
- owner-repo mutation
- Fitness or Mazer fallback routing
- workflow edit or dispatch authority
- secret or deploy authority
- protected-surface writes
- queue execution authority
- release-readiness authority

## Marker Decision

No marker moves in this contract freeze.

`AI Long-Run Batch Orchestration` remains `70%` because this packet freezes doctrine only.

## Next

Open only this next packet:

```text
AI Long-Run Batch Orchestration cross-marker opportunity planner-integration first-implementation admission
```

Expected admission contents:

- admit `ops/atlas/marker_aware_next_packet_planner.py`
- admit `tests/test_atlas_marker_aware_next_packet_planner.py`
- freeze the smallest implementation slice for advisory cross-marker signal consumption
- preserve hold behavior when the signal is real but still non-executable

