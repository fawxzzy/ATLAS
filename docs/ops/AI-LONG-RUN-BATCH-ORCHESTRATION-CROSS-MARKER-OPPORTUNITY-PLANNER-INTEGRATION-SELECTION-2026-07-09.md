# AI Long-Run Batch Orchestration cross-marker opportunity planner-integration selection

- Date: `2026-07-09`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `ATLAS-root docs-only selector packet`
- Control-plane checkpoint: `dd8603f3105792e80385c7b602fc5e66fc9efe82`
- Marker movement: none; `AI Long-Run Batch Orchestration` remains `70%`

## Decision

Select `cross-marker opportunity planner-integration contract freeze` as the next exact AI Long-Run packet.

The next exact packet is:

```text
AI Long-Run Batch Orchestration cross-marker opportunity planner-integration contract freeze
```

## Why This Packet Exists

The bounded cross-marker helper is now real proof, but the marker-aware planner still does not consume that signal:

- `python ops/atlas/cross_marker_ratchet_opportunity.py --json` reports `status=ok`, `candidate_count=12`, `opportunity_count=1`, and `safe_to_use=true`
- `python ops/atlas/marker_aware_next_packet_planner.py --json` still reports `status=advisory_recommendation` with no selected packet
- `python ops/atlas/codex_hour_block_queue_prompt.py --json` still reports `suppression_decision=suppress_continuation` because planner `safe_candidate_count=0`

That means the landed helper is useful evidence, but not yet routable orchestration truth. The missing behavior is a bounded contract for how the planner should consume cross-marker opportunities as advisory scoring input without inventing work or widening authority.

## What The Landed Helper Proves

The current implementation-backed proof is:

- `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-CROSS-MARKER-RATCHET-OPPORTUNITY-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-07-08.md`

It proves:

- one committed implementation-backed receipt can be reused as cross-marker evidence
- docs-only receipts are blocked as ratchet proof
- owner-lane, protected-surface, workflow, deploy, secret, and hidden-context sources fail closed
- the output is advisory only and denies marker-write and final-receipt authority

It does not prove:

- that the planner can consume the signal yet
- that the queue can route a safe packet from that signal yet
- that a marker should move again
- that any owner-lane or protected proof should reopen

## Candidate Lanes Considered

| Candidate lane | Decision | Reason |
| --- | --- | --- |
| `AI Long-Run Batch Orchestration cross-marker opportunity planner-integration contract freeze` | selected | Smallest root-bounded slice that turns the landed helper into usable planner-routing doctrine without implementing anything yet. |
| `AI Long-Run Batch Orchestration cross-marker opportunity queue-integration contract freeze` | rejected for this packet | Queue behavior is downstream of planner selection. The planner must define when the signal is actionable before queue wording or routing should depend on it. |
| `AI Long-Run Batch Orchestration proof-reuse adoption class selector` | rejected for this packet | Broader than necessary. The missing gap is not another generic selector; it is explicit planner-consumption rules for an already-landed helper. |
| `AI Long-Run Batch Orchestration supervised-execution widening selector` | rejected for this packet | Unrelated to the current bottleneck. No supervised execution blocker was cleared by the helper landing. |
| `Hold / no immediate ATLAS-root packet` | rejected for this packet | Repo evidence now shows one fresh, bounded, root-only doctrine gap: how planner routing should treat cross-marker opportunities. That is enough to justify a docs-only packet without moving any marker. |

## Why Planner Integration Wins

- It reuses the landed helper instead of creating another standalone surface.
- It stays root-bounded and docs-only.
- It directly addresses the observed gap between `opportunity_count=1` and `safe_candidate_count=0`.
- It can preserve the current hold posture when the helper signal is real but still non-executable.
- It avoids forcing queue, owner-lane, deploy, workflow, or protected-surface widening.

## Required Guardrails

The future planner integration must preserve:

- Playbook rule refs
- pattern refs
- failure-mode refs
- doctrine status
- marker-ratchet requirements
- proof availability
- authority-risk modeling
- adjacent-marker relationships
- reusable automation value
- Cortex substrate value
- owner-lane separation

The contract must also preserve:

- no owner-repo mutation
- no Fitness fallback
- no Mazer fallback
- no workflow edit or dispatch
- no secrets, deploy, Vercel, Supabase, or protected-surface access
- no marker movement without receipt-backed proof
- no final-receipt authority

## Marker Decision

No marker moves from this selector.

- `AI Long-Run Batch Orchestration` remains `70%`
- `Cortex Readiness` remains `46%`
- `Playbook Everywhere + Cortex Interface` remains `45%`

Selector receipts choose the next bounded packet. They do not prove executed state change.

## Next

Open only this next packet:

```text
AI Long-Run Batch Orchestration cross-marker opportunity planner-integration contract freeze
```

That contract freeze must define:

- admitted helper inputs
- advisory scoring behavior
- false-positive prevention
- proof-reuse rules
- selected-packet output behavior
- no-action hold behavior
- future implementation and test surfaces
- authority denials

