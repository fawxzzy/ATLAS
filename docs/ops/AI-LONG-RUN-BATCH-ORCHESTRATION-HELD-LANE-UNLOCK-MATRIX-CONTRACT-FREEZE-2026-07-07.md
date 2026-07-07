# AI Long-Run Batch Orchestration Held-Lane Unlock Matrix Contract Freeze

Date: 2026-07-07

## Result

The held-lane unlock matrix contract is frozen.

This packet follows the marker-aware planner candidate review, which found:

- planner status: `advisory_recommendation`
- planner candidate count: `20`
- selected packet: none
- held candidates: `20`
- immediately executable candidates: `0`
- marker movement: none

The review did not mean "do nothing forever." It meant the next useful orchestration surface is a deterministic unlock matrix that records why each candidate is held and what exact proof, receipt, operator selection, or owner-lane packet would make it executable.

## Contract Scope

Future helper:

- `ops/atlas/held_lane_unlock_matrix.py`

Future proof:

- `tests/test_atlas_held_lane_unlock_matrix.py`

The future helper may read marker-aware planner output, continuity manifests, ATLAS Book mirrors, Playbook doctrine refs, and validation/read-model receipts. It must remain read-only by default and advisory only.

## Blocker Classes

The unlock matrix must classify held candidates using these blocker classes:

- `held_by_manifest`: the candidate's current manifest explicitly says no immediate same-lane packet is open.
- `proof_gated`: the candidate needs proof-backed evidence before selection.
- `external_proof_required`: the candidate depends on proof outside ATLAS-root execution.
- `owner_lane_required`: the candidate requires a separate owner-repo packet before root can claim progress.
- `operator_selection_required`: multiple safe scopes exist, but none is selected by durable operator intent.
- `already_completed`: the candidate belongs to a closed or fully satisfied marker family.
- `stale_packet`: the candidate references an already consumed, superseded, or contradicted packet.
- `implementation_missing`: a contract exists, but the implementation slice has not landed.
- `contract_missing`: the candidate lacks a frozen contract for safe execution.
- `readiness_missing`: implementation is not yet routed by a readiness closeout.
- `authority_risk`: the candidate would require forbidden authority such as final receipt, marker write, approval, owner truth, or workflow dispatch authority.
- `protected_surface_risk`: the candidate would touch protected surfaces such as `secrets/**`, `.env*`, `.vercel/**`, `.playwright-mcp/**`, `archive/**`, deploy surfaces, or workflow files.
- `no_action_hold`: no useful safe action is available until state changes.

## Required Evidence To Clear Blockers

Each blocker class must have an explicit clearing condition:

- `held_by_manifest` clears only when a later manifest-backed receipt changes the next-package ladder or a separately selected scope overrides the hold.
- `proof_gated` clears only with artifact-backed or receipt-backed proof.
- `external_proof_required` clears only when the external proof is supplied and validated by an admitted root or owner-side proof path.
- `owner_lane_required` clears only after a separate owner-repo packet lands or preserves the needed owner truth.
- `operator_selection_required` clears only with a durable operator-selected packet.
- `already_completed` clears only by opening a new named scope, not by replaying the closed marker.
- `stale_packet` clears only by replacing the stale packet with a current receipt-backed packet.
- `implementation_missing` clears only by a first-implementation worker-cluster reconciliation.
- `contract_missing` clears only by a contract-freeze receipt.
- `readiness_missing` clears only by an implementation-readiness closeout and worker-routing receipt.
- `authority_risk` clears only by narrowing the scope until forbidden authority is no longer required.
- `protected_surface_risk` clears only by narrowing the scope or adding explicit approval and proof gates.
- `no_action_hold` clears only when new state, proof, or operator scope exists.

## Future Output Contract

The future helper must emit deterministic JSON with these fields:

- `schema_version`
- `status`
- `candidate_count`
- `held_count`
- `unlockable_count`
- `blocker_classes`
- `candidates`
- `required_proofs`
- `required_receipts`
- `operator_actions`
- `owner_lane_boundaries`
- `playbook_rule_refs`
- `authority_risks`
- `recommended_next_selection`
- `safe_to_continue`

Allowed status values:

- `ok`
- `advisory_matrix`
- `blocked`
- `internal_error`

`recommended_next_selection` must remain advisory. It cannot move markers, create final receipts, dispatch workflows, approve PRs, mutate repos, or override the marker selector.

## Forbidden Authority

The future helper must not:

- mutate files by default
- stage, commit, or push
- mutate owner repos
- touch secrets
- deploy
- dispatch workflows
- approve PRs
- emit final receipts
- infer proof from green CI alone
- scrape hidden transcript state
- override marker selector authority
- move markers

Fitness app work and Mazer game work remain separate owner lanes. Playbook owner-repo work also requires a separate owner-side packet.

## Workflow And Proof Doctrine

Workflow-style automation candidates should map to explicit reusable workflow-style contracts comparable to `workflow_call`, but this contract does not admit workflow implementation. Human or protected proof candidates should map to explicit dispatch/input contracts before execution. CI evidence must be artifact-backed or receipt-backed, not inferred from a green run alone.

Least privilege remains mandatory: no secret handling, no deploy authority, no owner mutation, no auto-approval, and no final receipt authority.

## Marker Decision

No marker moves.

`AI Long-Run Batch Orchestration` remains at `67%`.

## Exact Next Packet

`AI Long-Run Batch Orchestration held-lane unlock matrix first-implementation admission`

That next packet may admit `ops/atlas/held_lane_unlock_matrix.py` and `tests/test_atlas_held_lane_unlock_matrix.py` as future implementation surfaces. It must still not implement the worker until a later readiness packet routes it.

## Verification

Preflight evidence:

- branch: `main`
- parity: `origin/main...HEAD = 0 0`
- validation: `critical=0 error=0 warning=19 info=0`
- planner status: `advisory_recommendation`
- planner candidate count: `20`
- planner selected packet: none
- continuity manifest health: `20/20`
- open-marker restart readiness: `7/7`

Guardrails preserved:

- no Fitness mutation
- no Mazer mutation
- no owner-repo mutation
- no Supabase, Vercel, deploy, secret, workflow, `.env*`, `.vercel`, `.playwright-mcp/`, or `archive/` touch
- no marker movement
- no worker implementation
