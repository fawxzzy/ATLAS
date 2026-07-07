# AI Long-Run Batch Orchestration Marker-Aware Next-Packet Planner Contract Freeze

Date: 2026-07-07
Status: contract_frozen
Scope: ATLAS root docs and governance only

## Objective

Freeze the contract for a future marker-aware next-packet planner before implementation.

The future planner will rank the next bounded ATLAS packet from durable marker, manifest, receipt, read-model, Playbook, Cortex, and helper evidence. It will not execute the selected packet, move markers, mutate owner repos, edit workflows, dispatch CI, touch secrets, deploy, or override validation.

## Admitted Inputs

The future planner may consume only root-owned, read-only inputs:

- `ops/atlas/marker_knockout_selector.py --format json`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/memory/initiatives/continuity-manifest-*.json`
- `ops/atlas/continuity_manifest_health.py`
- `ops/atlas/continuity_open_marker_restart_index.py`
- `ops/atlas/continuity_coverage.py`
- `ops/atlas/ai_work_session_closeout.py --json --scope root`
- `ops/atlas/projection_freshness.py --json --scope root`
- `ops/atlas/playbook_adoption_matrix.py --json --scope root`
- `ops/atlas/reusable_workflow_proof_contract_candidate.py --json --scope root`
- `ops/cortex/authority_safe_interface_handoff.py --json --scope root`
- `ops/cortex/authority_safe_handoff_consumption.py --json`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- Current root branch/head/parity from Git, read-only

## Scoring Model

The future planner must score candidate packets using additive positive factors:

- Root-bounded packet with no owner-repo mutation.
- Explicit receipt or manifest basis.
- Existing helper or read-model input can answer the question.
- Held-lane churn is avoided.
- Marker ratchet condition is named and not faked.
- Playbook adoption or proof posture is consumed rather than restated.
- Cortex advisory state is consumed without granting authority.
- Fitness, Mazer, and other owner lanes stay separated unless explicitly selected by a separate owner packet.
- The candidate improves future execution quality instead of only refreshing wording.
- The candidate can be verified by deterministic local commands.

The future planner must apply penalties for:

- Owner-repo mutation by adjacency.
- Secret, `.env*`, deploy, publication, Vercel, Supabase, or protected-surface touch.
- GitHub workflow edit or dispatch.
- Marker movement based only on narration.
- Green CI status without artifact/proof specificity.
- Stale held-lane repetition.
- Unverified external state.
- Broad queue or scheduling authority before a smaller contract exists.

## Held-Lane Blocker Model

The future planner must distinguish:

- `held`: a lane has no immediate same-lane packet from its manifest.
- `blocked`: a lane has a specific missing proof, access, owner-side action, or external state.
- `execution_ready`: a lane has a named bounded packet and no blocker.
- `selector_ready`: a lane can run one docs-only selector or contract packet but cannot claim execution.

Held lanes should not be rerun unless new evidence materially changes the selector input.

## Owner-Lane Separation Model

The future planner must treat owner apps and games as separate lanes from ATLAS root governance.

For this contract, Fitness and Mazer are explicit non-targets. Their status may be read only if an ATLAS read model already reports it, but the future planner must not route ATLAS progress through owner-repo mutation, owner marker ratchets, or owner-specific proof cleanup unless a separate owner-lane packet is selected.

## Proof-Risk Model

The future planner must report proof risk separately from packet value:

- `low`: deterministic local docs/read-model proof is sufficient.
- `medium`: helper implementation or unit tests are required.
- `high`: external provider, CI artifact, owner-repo validation, or manual proof is required.
- `blocked`: required proof is absent and cannot be inferred responsibly.

The planner may select a high-value packet with proof risk, but it must not claim readiness until the proof exists.

## External Workflow Constraints

Reusable workflow and CI-related candidates must preserve caller/callee boundary clarity:

- Inputs, secrets, outputs, and permissions must be explicit before execution claims.
- Current-head artifact proof must be separated from green status.
- Reusable workflow references must not imply authority to edit or dispatch workflows.

Reference:

- `https://docs.github.com/en/actions/how-tos/sharing-automations/reusing-workflows`

## Future Output Schema

The future implementation must emit JSON with these fields:

```json
{
  "schema_version": "atlas.marker_aware_next_packet_planner.v1",
  "status": "ok",
  "branch": "main",
  "head": "<sha>",
  "active_lane": "<marker or lane>",
  "operator_action": "<selector action>",
  "candidate_packets": [],
  "selected_packet": null,
  "rejected_candidates": [],
  "scoring_factors": [],
  "blockers": [],
  "warnings": [],
  "proof_requirements": [],
  "authority_denials": [],
  "safe_to_continue": true,
  "next_packet": null,
  "source_refs": []
}
```

Failure envelopes must be deterministic and fail closed when required inputs are missing or malformed.

## Forbidden Authority

The future planner must not:

- Mutate owner repos.
- Invent owner truth.
- Edit or dispatch GitHub workflows.
- Touch secrets or `.env*` files.
- Touch deploy, publication, Vercel, Supabase, `.vercel/`, `.playwright-mcp/`, `archive/`, or `secrets/` surfaces.
- Emit final receipt truth for work it did not execute.
- Move markers.
- Override stack validation or continuity health.
- Turn Cortex advisory outputs into authority.

## Future Implementation Boundary

The future implementation may be admitted only by the next packet:

```text
AI Long-Run Batch Orchestration marker-aware next-packet planner first-implementation admission
```

Candidate future files:

- `ops/atlas/marker_aware_next_packet_planner.py`
- `tests/test_atlas_marker_aware_next_packet_planner.py`

This contract freeze does not create those files.

## Marker Decision

No marker moves from this contract freeze.

- `AI Long-Run Batch Orchestration` remains `66%`.
- `AI Repetition-to-Automation Pipeline` remains `49%`.

## Next Packet

```text
AI Long-Run Batch Orchestration marker-aware next-packet planner first-implementation admission
```
