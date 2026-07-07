# AI Long-Run Batch Orchestration Held-Lane Unlock Matrix Prompt-Pack And Worker Handoff Contract

Date: 2026-07-07

## Result

The held-lane unlock matrix worker handoff contract is frozen.

This remains a docs-only packet. It does not implement the worker.

## Worker Objective

Implement a read-only ATLAS-root helper that turns the marker-aware planner's held-candidate output into a deterministic unlock matrix.

Future implementation file:

- `ops/atlas/held_lane_unlock_matrix.py`

Future test file:

- `tests/test_atlas_held_lane_unlock_matrix.py`

Primary command:

```powershell
python ops\atlas\held_lane_unlock_matrix.py --json
```

Optional safe output command:

```powershell
python ops\atlas\held_lane_unlock_matrix.py --json --output tmp/atlas/held-lane-unlock-matrix.latest.json
```

## Required Behavior

The worker must:

- load marker-aware planner output or source-equivalent candidate data
- preserve deterministic candidate ordering
- classify each candidate into frozen blocker classes
- emit candidate-level required proofs, required receipts, operator actions, and owner-lane boundaries
- preserve Playbook rule references as evidence only
- preserve Cortex references as advisory only
- report `recommended_next_selection` as advisory only
- fail closed for malformed inputs
- reject forbidden source refs
- reject protected output paths
- write only to explicit `tmp/**.json` output paths when `--output` is supplied

## Required Output Fields

The output must include:

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

## Proof Obligations

The test suite must cover:

- deterministic output ordering
- status classification
- all frozen blocker classes
- manifest-held candidate classification
- proof-gated candidate classification
- external-proof-required candidate classification
- owner-lane-required candidate classification
- operator-selection-required candidate classification
- already-completed and stale-packet classification
- missing contract, missing implementation, and missing readiness classification
- authority-risk and protected-surface-risk classification
- no-action-hold classification
- owner-lane boundaries for Fitness, Mazer, and Playbook owner work
- Playbook refs as evidence only
- Cortex refs as advisory only
- forbidden source-ref rejection
- protected output-path rejection
- explicit `tmp/**.json` output-path allowance
- no marker, final receipt, workflow dispatch, deploy, approval, owner-truth, or owner-repo mutation authority

## Allowed Touch Surface For Implementation

Only these implementation surfaces are admitted by the eventual worker packet:

- `ops/atlas/held_lane_unlock_matrix.py`
- `tests/test_atlas_held_lane_unlock_matrix.py`

Worker reconciliation may also add one bounded reconciliation receipt and exact Book/manifest mirrors after proof passes.

## Forbidden Surfaces

The worker and implementation packet must not touch:

- `repos/**`
- Fitness owner repo files
- Mazer owner repo files
- Playbook owner repo files
- `secrets/**`
- `.env*`
- `.vercel/**`
- `.playwright-mcp/**`
- `archive/**`
- `.github/workflows/**`
- deploy or platform surfaces
- broad untracked backlog

## Stop Conditions

Stop without committing if:

- root validation has `critical` or `error`
- the marker-aware planner output cannot be generated
- owner-repo mutation is required
- Fitness or Mazer mutation is required
- Playbook owner-repo mutation is required
- workflow edit or dispatch is required
- secret/deploy/platform/protected-surface work is required
- marker movement would be claimed without implementation-backed proof
- unrelated residue would need to be staged

## Marker Decision

No marker moves.

`AI Long-Run Batch Orchestration` remains at `67%`.

## Exact Next Packet

`AI Long-Run Batch Orchestration held-lane unlock matrix implementation-readiness closeout and worker routing`

That packet should confirm no docs-only prerequisite remains before the bounded implementation worker.

