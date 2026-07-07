# AI Repetition-to-Automation Pipeline Reusable Workflow Proof-Contract Candidate Prompt-Pack And Worker Handoff Contract

Date: 2026-07-07

## Worker Objective

Implement one root-only, read-only reusable workflow proof-contract candidate helper and its focused tests:

- `ops/atlas/reusable_workflow_proof_contract_candidate.py`
- `tests/test_atlas_reusable_workflow_proof_contract_candidate.py`

The worker must classify durable ATLAS receipt and doctrine evidence into explicit proof-contract candidates. It must not implement GitHub workflows, dispatch workflows, mutate owner repos, touch secrets, or claim marker movement.

## Required CLI

Minimum command:

```powershell
python ops\atlas\reusable_workflow_proof_contract_candidate.py --json
```

Optional bounded output command:

```powershell
python ops\atlas\reusable_workflow_proof_contract_candidate.py --json --output tmp/reusable-workflow-proof-contract-candidates.json
```

The only admitted write output is an explicit `tmp/**.json` path.

## Required JSON Fields

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

## Proof Obligations

The worker must prove:

- deterministic JSON ordering
- owner-repo, protected-surface, secret, deploy/platform, and hidden-transcript source refs are rejected or flagged unsafe
- only explicit `tmp/**.json` output is writable
- workflow-style, manual-proof, artifact-proof, rejected, doctrine-gap, and authority-risk classifications are covered
- Playbook rule refs, repeated pattern refs, failure-mode refs, authority risks, and proof requirements are emitted
- no marker authority is emitted
- no workflow edit, workflow dispatch, owner mutation, deploy mutation, secret read, PR approval, merge, final receipt, or release-readiness claim is possible

## Allowed Files For Future Worker

- `ops/atlas/reusable_workflow_proof_contract_candidate.py`
- `tests/test_atlas_reusable_workflow_proof_contract_candidate.py`
- bounded docs receipt/mirror updates only after implementation proof passes and a later reconciliation packet admits them

## Forbidden Files And Actions

- owner repos
- Fitness
- Mazer
- Foundation owner repo mutation
- Playbook owner repo mutation
- `.github/workflows/**`
- workflow dispatch or rerun
- `_stack` dispatch
- Supabase
- Vercel
- deploy/platform mutation
- BrowserStack mutation
- secrets
- `.env*`
- protected surfaces
- broad untracked backlog
- marker movement
- final receipt authority
- release-readiness claims

## Stop Conditions

Stop without committing if:

- stack validation reports any `critical` or `error`
- the helper needs owner repo, platform, deploy, secret, or protected-surface access
- `.github/workflows/**` changes are needed
- workflow dispatch is needed
- implementation proof fails
- marker movement would be claimed without implementation-backed ratchet evidence
- output path safety cannot be made fail-closed
- source-admission boundaries cannot reject hidden transcript/session inputs

## Marker Decision

`AI Repetition-to-Automation Pipeline` remains at `48%`.

Reason: this freezes worker scope and proof obligations only. Marker movement requires the future helper, tests, live proof, and reconciliation.

## Exact Next Packet

`AI Repetition-to-Automation Pipeline reusable workflow proof-contract candidate implementation-readiness closeout and worker routing`
