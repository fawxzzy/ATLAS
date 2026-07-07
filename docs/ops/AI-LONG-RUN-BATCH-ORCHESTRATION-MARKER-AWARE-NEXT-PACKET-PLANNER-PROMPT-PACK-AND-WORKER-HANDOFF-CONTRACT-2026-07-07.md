# AI Long-Run Batch Orchestration Marker-Aware Next-Packet Planner Prompt-Pack And Worker Handoff Contract

Date: 2026-07-07
Status: prompt_pack_frozen
Scope: ATLAS root docs and governance only

## Worker Objective

Implement one bounded, read-only marker-aware next-packet planner.

The worker must create:

- `ops/atlas/marker_aware_next_packet_planner.py`
- `tests/test_atlas_marker_aware_next_packet_planner.py`

The helper must read current marker state, continuity manifests, recent receipt/read-model outputs, Playbook doctrine refs, Cortex advisory handoff state, and proof-risk signals to recommend the next bounded packet without inventing work, reopening held lanes by wording, touching owner repos, or claiming marker movement.

## Required Behavior

The helper must:

- Emit deterministic JSON.
- Read only ATLAS-root governed inputs.
- Classify every candidate packet into an explicit status class.
- Preserve Fitness and Mazer as separate owner lanes.
- Preserve Cortex outputs as advisory-only.
- Preserve Playbook refs as scoring evidence, not execution authority.
- Treat green CI as insufficient unless artifact-backed or receipt-backed proof exists.
- Reject protected, secret, deploy, owner-repo, hidden transcript, absolute-path, and parent-traversal inputs.
- Fail closed on missing or malformed required inputs.

## Required Candidate Classes

The helper must classify candidates as:

- `immediately_executable_packet`
- `held_lane`
- `proof_gated_lane`
- `owner_lane_blocked_lane`
- `external_proof_blocked_lane`
- `stale_packet`
- `implementation_ready_packet`
- `docs_only_packet`
- `unsafe_authority_risk_packet`
- `no_action_hold`

## Required Output Schema

The helper must emit:

```json
{
  "schema_version": "atlas.marker_aware_next_packet_planner.v1",
  "status": "ok",
  "selected_marker": null,
  "selected_packet": null,
  "candidate_count": 0,
  "candidate_scores": [],
  "held_lanes": [],
  "proof_gated_lanes": [],
  "owner_lane_boundaries": [],
  "playbook_rule_refs": [],
  "pattern_refs": [],
  "failure_mode_refs": [],
  "authority_risks": [],
  "rejected_candidates": [],
  "proof_requirements": [],
  "safe_to_continue": true
}
```

Allowed `status` values:

- `ok`
- `advisory_recommendation`
- `blocked`
- `internal_error`

## Admitted Inputs

The worker may read or call:

- `ops/atlas/marker_knockout_selector.py --format json`
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
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/memory/initiatives/continuity-manifest-*.json`
- `docs/PLAYBOOK_NOTES.md`
- `docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md`
- `docs/standards/WORKER-ORCHESTRATION.md`
- `docs/ops/PLAYBOOK-ADOPTION-MATRIX.md`

## Explicit Design Constraints

The helper may encode these design constraints:

- Reusable workflow candidates should be modeled like `workflow_call` contracts with explicit inputs, secrets, permissions, outputs, and proof obligations.
- Manual/protected proof candidates should be modeled like explicit dispatch/input contracts.
- CI proof must be artifact-backed or receipt-backed.
- Automation must use least privilege and deny secret, deploy, auto-approval, final-receipt, and owner-mutation authority.
- External reusable workflow/action references should prefer stable pinned refs, with full-length commit SHA preferred where applicable.

Primary GitHub references checked on 2026-07-07:

- `https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows`
- `https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax`
- `https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts`
- `https://docs.github.com/en/actions/reference/security/secure-use`

## Forbidden Surfaces

The worker must not read from or write to:

- `repos/**`
- `secrets/**`
- `.env*`
- `.vercel/**`
- `.playwright-mcp/**`
- `archive/**`
- `.github/workflows/**`
- Deployment outputs
- Hidden transcript/session state
- Absolute paths
- Parent-traversal paths

## Forbidden Authority

The worker must not:

- Mutate files except an explicitly passed safe `tmp/**` JSON output path if that output option is implemented.
- Stage, commit, or push.
- Mutate owner repos.
- Touch Fitness or Mazer.
- Touch secrets.
- Deploy.
- Dispatch workflows.
- Approve or merge PRs.
- Emit final receipts.
- Move markers.
- Treat Cortex advisory output as authority.
- Infer proof from green CI alone.

## Required Tests

The worker test file must cover:

- Deterministic JSON field ordering.
- Live root input path returns `ok` or `advisory_recommendation`.
- Held-lane classification.
- Proof-gated-lane classification.
- Owner-lane blocked classification.
- External-proof blocked classification.
- Implementation-ready packet classification.
- Docs-only packet classification.
- Unsafe authority-risk rejection.
- Playbook refs are surfaced.
- Cortex advisory inputs remain advisory and authority-denying.
- Workflow-style candidate remains contract-only and cannot edit `.github/workflows/**`.
- Owner, secret, deploy, protected, hidden transcript, absolute-path, and parent-traversal inputs are rejected.
- Explicit safe `tmp/**` JSON output path handling if output writing is implemented.
- No marker movement or final-receipt authority appears in output.

## Stop Conditions

The worker must stop or emit `blocked` / `internal_error` without fabricating a recommendation if:

- Stack validation has `critical` or `error`.
- Required marker or manifest inputs are missing.
- Input sources include protected, owner, secret, deploy, workflow, hidden, absolute, or parent-traversal paths.
- The candidate requires owner mutation, workflow dispatch, deploy, secret handling, or platform mutation.
- Proof is missing for a proof-gated candidate.

## Next Packet

```text
AI Long-Run Batch Orchestration marker-aware next-packet planner implementation-readiness closeout and worker routing
```

## Marker Decision

No marker moves from this prompt-pack.

- `AI Long-Run Batch Orchestration` remains `66%`.
- `AI Repetition-to-Automation Pipeline` remains `49%`.
