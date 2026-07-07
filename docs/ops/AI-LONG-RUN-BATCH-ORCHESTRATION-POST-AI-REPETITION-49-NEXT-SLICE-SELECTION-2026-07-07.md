# AI Long-Run Batch Orchestration Post AI Repetition 49 Next-Slice Selection

Date: 2026-07-07
Status: selected
Scope: ATLAS root docs and governance only

## Inputs Checked

- Root branch: `main`
- Root head at selection start: `ec0e100a`
- Root parity at selection start: `origin/main...HEAD = 0 0`
- Stack validation: `critical=0 error=0 warning=19 info=0`
- Continuity manifest health: `20 / 20`
- Open marker restart readiness: `7 / 7`
- Continuity coverage: `pending_review_count=0`
- Selector posture: active held lane remains `Sandbox Simulation Readiness`; operator action remains `no_immediate_root_packet`
- AI Repetition current marker: `49%`
- AI Long-Run current marker: `66%`

## Fresh Context

AI Repetition-to-Automation Pipeline reached `49%` through the reusable workflow proof-contract cluster:

- `d00bd06b` routed the reusable workflow proof contract worker.
- `6e51e41c` implemented the reusable workflow proof contract classifier.
- `ec0e100a` reconciled that classifier proof contract.
- `ops/atlas/reusable_workflow_proof_contract_candidate.py` now emits live candidate evidence.
- Direct proof reported `status=ok`, `candidate_count=3`, and `safe_to_continue=true`.

That does not justify another AI Repetition packet by adjacency because the AI Repetition manifest is already held after the helper cluster. The useful question moves back to orchestration: choosing the next bounded root-owned packet without reopening owner repos, secrets, deploys, protected surfaces, or marker movement by wording.

## Candidate Lanes Considered

1. `AI Long-Run Batch Orchestration marker-aware next-packet planner contract freeze`
2. `AI Long-Run Batch Orchestration held-lane blocker classifier contract freeze`
3. `AI Long-Run Batch Orchestration cross-marker execution queue contract freeze`
4. `Cortex Readiness second advisory substrate selector`
5. `Playbook Everywhere + Cortex Interface second consumer selector`
6. Hold flat with no new packet

## Selection

Selected packet:

```text
AI Long-Run Batch Orchestration marker-aware next-packet planner contract freeze
```

Reason:

- It is the smallest root-owned continuation after AI Repetition reached `49%`.
- It converts the current repeated manual lane-selection work into a bounded planner contract without implementing worker code yet.
- It can consume existing read models instead of inventing new truth: marker selector JSON, continuity manifests, continuity health, restart coverage, closeout, projection freshness, Playbook adoption matrix, reusable workflow proof candidates, and Cortex authority-safe handoff surfaces.
- It keeps Fitness and Mazer out of this ATLAS lane by making owner-lane separation an explicit planning input.
- It respects the marker ratchet threshold: planning can select a packet, but cannot move a marker without execution, proof-backed adoption, manifest-backed restart widening, or real blocker clearance.

## Rejected Candidates

- Held-lane blocker classifier: useful later, but narrower than the planner. It classifies one blocker class before the planner defines how blocker state competes against other next-packet factors.
- Cross-marker execution queue: too much authority for this slice. Queue semantics imply scheduling and execution posture, while this pass only needs selection criteria.
- Cortex second advisory substrate selector: valid but not the best immediate continuation from the AI Repetition reusable workflow proof cluster.
- Playbook/Cortex second consumer selector: valid but depends on a clearer planner boundary so it does not become another manual routing narration.
- Hold flat: rejected because AI Repetition produced new proof-backed helper evidence that creates a legitimate orchestration-contract follow-on.

## Contract Inputs To Freeze Next

The selected contract-freeze packet should define a future planner that can read, score, and report from these inputs only:

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
- Atlas Book restart and receipt mirrors

The selected contract must not implement the future worker yet. The implementation candidate remains future work:

- `ops/atlas/marker_aware_next_packet_planner.py`
- `tests/test_atlas_marker_aware_next_packet_planner.py`

## External Workflow Design Constraints

The next contract should follow reusable workflow discipline from GitHub Actions documentation:

- Keep a reusable workflow contract explicit before treating it as an execution substrate.
- Separate caller-facing inputs, secrets, outputs, and permission assumptions.
- Avoid relying on implied runtime inheritance when a contract can name the required boundary.
- Preserve proof artifacts and current-head evidence separately from green status claims.

Reference:

- `https://docs.github.com/en/actions/how-tos/sharing-automations/reusing-workflows`

## Boundaries

This selection does not authorize:

- Fitness or Mazer mutation.
- Any owner-repo mutation.
- Supabase mutation.
- Vercel mutation.
- Deploy or publication.
- Secret or `.env*` handling changes.
- GitHub workflow edits or dispatch.
- Protected-surface edits under `archive/`, `.playwright-mcp/`, `.vercel/`, or `secrets/`.
- Marker movement.

## Marker Decision

No marker moves from this selector packet.

- `AI Long-Run Batch Orchestration` remains `66%`.
- `AI Repetition-to-Automation Pipeline` remains `49%`.

The selected next packet is a docs-only contract freeze. Marker movement would require a later receipt-backed ratchet condition.

## Next Packet

```text
AI Long-Run Batch Orchestration marker-aware next-packet planner contract freeze
```
