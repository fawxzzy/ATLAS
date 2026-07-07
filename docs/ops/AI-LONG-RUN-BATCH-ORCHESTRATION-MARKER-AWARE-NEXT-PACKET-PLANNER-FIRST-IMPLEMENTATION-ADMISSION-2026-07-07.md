# AI Long-Run Batch Orchestration Marker-Aware Next-Packet Planner First-Implementation Admission

Date: 2026-07-07
Status: first_implementation_admitted
Scope: ATLAS root docs and governance only

## Objective

Admit the smallest safe future implementation slice for a marker-aware next-packet planner.

This packet does not implement the planner. It admits one bounded helper file and one bounded test file for a later prompt-pack/readiness/worker sequence.

## Why This Is The Smallest Honest Slice

The previous contract freeze proved the planner boundary but did not yet authorize a worker. The next useful step is not implementation; it is first-implementation admission: naming the exact future files, output classes, proof matrix, and forbidden authority so the next prompt-pack can route a worker without widening into owner repos, workflow dispatch, secrets, deploys, protected surfaces, or marker claims.

## Why This Is AI Long-Run Work

This is `AI Long-Run Batch Orchestration` work because the target helper is an orchestration selector over marker state, manifests, receipt families, blocked-lane state, proof risk, owner-lane separation, Playbook doctrine, and Cortex advisory inputs. It is not generic AI Work Session work because it does not improve preflight, closeout, projection freshness, or session synchronization directly. It improves the long-run packet-selection machinery that decides what bounded packet should run next.

## Admitted Future Files

Future implementation file:

- `ops/atlas/marker_aware_next_packet_planner.py`

Future test file:

- `tests/test_atlas_marker_aware_next_packet_planner.py`

These names follow the existing ATLAS helper convention: root-owned orchestration helpers live under `ops/atlas/`, and direct unit coverage lives under `tests/test_atlas_*.py`.

## Admitted Helper Inputs

The future helper may read only root-owned or generated read-only surfaces:

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

## Admitted Continuity Manifest Inputs

The future helper may consume these manifests as read-only scoring inputs:

- `docs/memory/initiatives/continuity-manifest-ai-long-run-batch-orchestration.json`
- `docs/memory/initiatives/continuity-manifest-ai-repetition-to-automation-pipeline.json`
- `docs/memory/initiatives/continuity-manifest-ai-work-session-stability-auto-sync-loop.json`
- `docs/memory/initiatives/continuity-manifest-playbook-everywhere-cortex-interface.json`
- `docs/memory/initiatives/continuity-manifest-cortex-readiness.json`
- Other `docs/memory/initiatives/continuity-manifest-*.json` files only for read-only marker/held-lane scoring.

## Admitted Receipt Families

The future helper may cite these receipt families:

- AI Long-Run marker-aware planner selector and contract receipts.
- AI Repetition reusable workflow proof-contract candidate receipts.
- AI Work Session preflight, closeout, projection freshness, Playbook adoption matrix, and root-plus-owner adoption receipts.
- Playbook Everywhere + Cortex Interface authority-safe and adoption-matrix receipts.
- Cortex Readiness authority-safe handoff and consumption receipts.

Receipt citation is evidence only. It does not authorize mutation or marker movement.

## Playbook Doctrine Inputs

Every candidate scored by the future helper must report:

- `playbook_rule_refs`
- `pattern_refs`
- `failure_mode_refs`
- `doctrine_status`
- `marker_ratchet_requirements`
- `owner_lane_boundaries`
- `proof_requirements`
- `blocked_lane_state`
- `authority_risks`
- `reusable_automation_value`
- `cortex_substrate_value`

Primary doctrine surfaces:

- `docs/PLAYBOOK_NOTES.md`
- `docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md`
- `docs/standards/WORKER-ORCHESTRATION.md`
- `docs/ops/PLAYBOOK-ADOPTION-MATRIX.md`

## GitHub Workflow Design Constraints

The future helper may use GitHub Actions concepts only as design constraints, not as execution authority:

- Reusable workflow contracts are comparable to `workflow_call` contracts with explicit inputs, secrets, permissions, and outputs.
- Human/protected proof candidates are comparable to manually triggered workflows with explicit dispatch inputs.
- CI proof must be artifact-backed or receipt-backed, not inferred from a green run alone.
- Automation defaults must remain least-privilege and deny secret, deploy, auto-approval, final-receipt, and owner-mutation authority.
- External reusable workflow/action references should prefer stable pinned refs, with full-length commit SHA preferred where applicable.

Primary references checked on 2026-07-07:

- `https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows`
- `https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax`
- `https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts`
- `https://docs.github.com/en/actions/reference/security/secure-use`

## Required Classification Outputs

The future helper must classify candidate packets as one of:

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

## Future Output Fields

The future helper must emit deterministic JSON with:

- `schema_version`
- `status`
- `selected_marker`
- `selected_packet`
- `candidate_count`
- `candidate_scores`
- `held_lanes`
- `proof_gated_lanes`
- `owner_lane_boundaries`
- `playbook_rule_refs`
- `pattern_refs`
- `failure_mode_refs`
- `authority_risks`
- `rejected_candidates`
- `proof_requirements`
- `safe_to_continue`

Allowed status classes:

- `ok`
- `advisory_recommendation`
- `blocked`
- `internal_error`

## Forbidden Authority

The future helper must not:

- Mutate files.
- Stage, commit, or push.
- Mutate owner repos.
- Touch Fitness or Mazer.
- Touch secrets or `.env*`.
- Deploy or mutate platform state.
- Dispatch workflows.
- Approve or merge PRs.
- Emit final receipts.
- Infer proof from green CI alone.
- Scrape hidden transcript/session state.
- Override marker selector authority.
- Move markers.

## Proof Matrix For Future Worker

The future worker must prove:

- Deterministic JSON field ordering.
- Current marker and manifest input classification.
- Held-lane classification.
- Proof-gated-lane classification.
- Owner-lane blocked classification.
- External-proof blocked classification.
- Implementation-ready packet classification.
- Docs-only packet classification.
- Unsafe authority-risk rejection.
- Playbook rule, pattern, and failure-mode refs are surfaced.
- Cortex advisory inputs remain advisory and authority-denying.
- Workflow-style candidates remain contract-only and do not edit `.github/workflows/**`.
- Owner, secret, deploy, protected, hidden transcript, and absolute-path inputs are rejected.
- Output writing, if admitted later, is limited to explicit safe `tmp/**` JSON paths.
- No marker movement or final-receipt authority is emitted.

## Marker Decision

No marker moves from this first-implementation admission.

- `AI Long-Run Batch Orchestration` remains `66%`.
- `AI Repetition-to-Automation Pipeline` remains `49%`.

## Next Packet

```text
AI Long-Run Batch Orchestration marker-aware next-packet planner prompt-pack and worker handoff contract
```
