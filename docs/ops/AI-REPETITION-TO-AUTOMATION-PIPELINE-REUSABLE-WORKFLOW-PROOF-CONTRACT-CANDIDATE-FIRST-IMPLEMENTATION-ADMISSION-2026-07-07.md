# AI Repetition-to-Automation Pipeline Reusable Workflow Proof-Contract Candidate First-Implementation Admission

Date: 2026-07-07

## Decision

Admit one future root-only helper for the `reusable-workflow-proof-contract` candidate family:

- future helper: `ops/atlas/reusable_workflow_proof_contract_candidate.py`
- future tests: `tests/test_atlas_reusable_workflow_proof_contract_candidate.py`

This is a docs-only first-implementation admission. It does not implement the helper, create or edit workflows, dispatch workflows, mutate owner repos, touch secrets, or move markers.

## Smallest Honest Slice

The admitted first slice is a read-only classifier that turns explicit durable ATLAS evidence into reusable workflow proof-contract candidates.

The helper may classify durable receipts, Book surfaces, continuity manifests, and Playbook doctrine refs into contract candidates. It must not treat green CI alone as release proof, infer hidden chat state, or claim final receipt authority.

This lane is not GitHub workflow implementation. It models proof-contract candidates that may later inform workflow-like contracts; it does not edit `.github/workflows/**`, define live `workflow_call` or `workflow_dispatch` files, or dispatch workflows.

## Admitted Evidence Families

- post-Foundation selector receipt
- reusable workflow proof-contract candidate contract-freeze receipt
- Foundation owner-lane Playbook proof reconciliation receipt
- existing AI Repetition candidate extractor, review, and packet-ladder receipts
- ATLAS Book marker and restart surfaces
- AI Repetition continuity manifest
- root validation surfaces

## Playbook Doctrine Surfaces

The helper may cite these root-owned doctrine surfaces as read-only design references:

- `docs/PLAYBOOK_NOTES.md`
- `docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md`
- `docs/standards/WORKER-ORCHESTRATION.md`

## Allowed External Design Constraints

The helper may encode design constraints inspired by:

- reusable workflow contracts
- manual dispatch inputs
- artifact-backed proof
- least privilege

Those constraints remain advisory contract-shaping inputs only. They do not authorize platform work.

## Excluded Surfaces

The helper and its tests must not read, write, mutate, or infer authority from:

- owner repos
- Fitness
- Mazer
- Foundation owner repo mutation
- Playbook owner repo mutation
- `.github/workflows/**` writes
- workflow dispatch
- `_stack` dispatch
- Supabase
- Vercel
- deploy/platform state
- BrowserStack mutation
- secrets
- `.env*`
- protected surfaces
- broad untracked backlog

## Future Output Contract

The future helper may emit these fields:

- `schema_version`
- `status`
- `candidate_count`
- `workflow_contract_candidates`
- `manual_dispatch_candidates`
- `artifact_proof_candidates`
- `playbook_rule_refs`
- `pattern_refs`
- `failure_mode_refs`
- `doctrine_gaps`
- `authority_risks`
- `rejected_candidates`
- `proof_requirements`
- `safe_to_continue`

## Future Classification Contract

The helper may classify:

- reusable workflow-style candidate
- workflow_dispatch-style manual proof candidate
- artifact-backed proof candidate
- rejected or unsafe candidate
- doctrine gap
- authority risk
- implementation-ready candidate
- blocked candidate

## Authority Denials

The helper must not:

- write workflows
- dispatch workflows
- mutate owner repos
- touch secrets or deploy state
- approve or merge PRs
- emit final receipts
- infer protected proof from green CI alone
- infer truth from hidden transcripts
- move markers
- claim release readiness

## Proof Matrix For Future Worker

| Proof case | Required future behavior |
| --- | --- |
| explicit reusable workflow-style receipt evidence | emits a reusable workflow-style candidate with proof requirements |
| manual proof gate evidence | emits a manual-dispatch-style candidate with typed input needs |
| artifact-backed proof evidence | emits an artifact-proof candidate with artifact requirements |
| owner repo or protected path evidence | rejects or flags as authority risk |
| secret or `.env*` evidence | rejects and reports unsafe source class |
| green CI without protected proof artifact | rejects as insufficient release proof |
| hidden transcript/session source | rejects as inadmissible |
| no implementation-ready candidate | remains `safe_to_continue=false` or blocked, as appropriate |

## Marker Decision

`AI Repetition-to-Automation Pipeline` remains at `48%`.

Reason: this admits a future helper and test surface, but no implementation, live helper output, implementation-backed proof, broadened adoption, or cleared blocker exists yet.

## Exact Next Packet

`AI Repetition-to-Automation Pipeline reusable workflow proof-contract candidate prompt-pack and worker handoff contract`
