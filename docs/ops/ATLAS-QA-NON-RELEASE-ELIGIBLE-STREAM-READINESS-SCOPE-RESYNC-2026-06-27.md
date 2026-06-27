# ATLAS QA Non-Release-Eligible Stream Readiness Scope Re-Sync - 2026-06-27

- Date: `2026-06-27`
- Lane: `ATLAS QA release-readiness contract correction`
- Owner: `ATLAS/root`
- Mode: `root execution cluster plus proof`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `ops/atlas/qa/release_readiness.py`
  - `ops/atlas/qa/release_rehearsal.py`
  - `tests/test_atlas_qa_pipeline.py`
  - `stack.lock.yaml`
  - `runtime/atlas/qa/release-readiness.latest.json`
  - `runtime/atlas/qa/release-rehearsal.latest.json`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@6d9aae8d`

## Objective

Correct the live read model so repos marked `release_eligible: false` in `stack.lock.yaml` stay visible in QA projections without being misreported as failed release candidates.

## Execution

The root QA read-model code now consumes stack lock release scope directly:

- `ops/atlas/qa/release_readiness.py`
  - now reads `release_eligible` and `remote` from `stack.lock.yaml`
  - marks non-release-eligible repos as `release_gate_status: not_applicable`
  - keeps them out of blocked release counts
  - preserves their receipt freshness and SHA alignment as informational truth
- `ops/atlas/qa/release_rehearsal.py`
  - now maps those repos to `readiness_status: not_applicable`
  - tracks them separately from `pass` and `fail`

Focused regression proof passed:

- `python -m unittest tests.test_atlas_qa_pipeline.AtlasQaPipelineTests.test_release_readiness_marks_non_release_eligible_repo_not_applicable tests.test_atlas_qa_pipeline.AtlasQaPipelineTests.test_release_rehearsal_reflects_ready_blocked_and_not_applicable_repos`

The live artifacts were then regenerated:

- `python ops/atlas/qa/release_readiness.py --root .`
- `python ops/atlas/qa/release_rehearsal.py --root .`

## Read-Model Result

Current release-readiness summary is now:

- `release_ready_count: 4`
- `manual_review_count: 1`
- `blocked_count: 0`
- `not_applicable_count: 1`

Current release-rehearsal summary is now:

- `pass_count: 4`
- `fail_count: 1`
- `not_applicable_count: 1`

The only `not_applicable` repo is `stream`:

- `release_eligible: false`
- `stack_remote: ""`
- `release_scope_status: not_applicable`
- `release_gate_status: not_applicable`
- fresh current-SHA receipt preserved for informational QA truth only

That removes the last false blocker from the release-readiness family without pretending `stream` has become a release-ready target.

## Validation Boundary

Root validation remains stable:

- `critical=0 error=0 warning=1 info=0`

Retained warning:

- `repos/lifeline/.lifeline`

## Exact Next Honest Move

- `fitness` still needs Android and iPhone real-device proof or manual attestation
- `stream` needs no release-readiness unblock work while it remains `release_eligible: false`
- reopen `stream` only if stack governance later chooses to give it a protected remote-backed release path and promote it into release scope
