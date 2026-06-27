# ATLAS QA Topology Repair And Read-Model Re-Sync - 2026-06-27

- Date: `2026-06-27`
- Lane: `ATLAS QA topology / read-model repair`
- Owner: `ATLAS/root`
- Mode: `root repair plus read-model reconciliation`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/ops/ATLAS-QA-PROMOTION-RUNBOOK.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
  - `ops/atlas/qa/evidence_index.py`
  - `ops/atlas/qa/adoption_drift.py`
  - `ops/atlas/qa/release_readiness.py`
  - `ops/atlas/qa/release_rehearsal.py`
  - `ops/atlas/qa/waiver_monitor.py`
  - `tests/test_atlas_qa_pipeline.py`
  - `runtime/atlas/qa/evidence-index.latest.json`
  - `runtime/atlas/qa/adoption-drift.latest.json`
  - `runtime/atlas/qa/release-readiness.latest.json`
  - `runtime/atlas/qa/release-rehearsal.latest.json`
  - `runtime/atlas/qa/waiver-monitor.latest.json`
  - `runtime/atlas/qa/runs/foundation-contract-smoke-20260627T035250436338Z/evaluated.result.json`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@6d47295a`

## Objective

Repair the ATLAS protected-QA topology so the root read-model reflects the real adopted repo set again, refresh the runtime artifacts from that repaired topology, and reconcile the Book and restart surfaces back to the live blocker truth.

## Implementation

The repaired root QA topology now:

- merges root-owned QA contracts under `ops/atlas/qa/**` with repo-local contracts under `repos/*/qa/**`
- resolves repo-owned `docs/qa.md` through the repo registry path instead of hardcoded repo-name assumptions
- fail-soft loads QA manifest references so missing or invalid refs surface as validation findings instead of crashing the read-model refresh

The refreshed runtime read-model now reflects the real adopted QA set again:

- `fitness`
- `foundation`
- `lifeline`
- `playbook`
- `stream`
- `trove`

Repo-local QA docs and manifest-path hygiene were repaired enough for the read-model to stop misclassifying adoption topology and missing-doc drift for the adopted set.

## Current Root Truth

As of the refreshed `2026-06-27T04:03Z` runtime artifacts:

- `evidence-index.latest.json` now reports the adopted repo set as `fitness`, `foundation`, `lifeline`, `playbook`, `stream`, and `trove`
- `adoption-drift.latest.json` is `clean` for `foundation`
- `adoption-drift.latest.json` is `drift` for `fitness`, `lifeline`, `playbook`, `stream`, and `trove`, but that drift is now stale-receipt drift rather than topology, path, or missing-doc drift
- `waiver-monitor.latest.json` reports one waiver on file and zero active waivers; the remaining waiver is expired

Current release-readiness truth after the refresh:

- `foundation` now has one fresh current-SHA run at `foundation-contract-smoke-20260627T035250436338Z`
- that `foundation` run is `receipt_fresh: true` and `sha_match: true`
- `foundation` still fails the release gate because its latest promotion status is `blocked`
- `fitness` still fails the release gate because both governed Fitness Hobby checkpoints are stale and its latest meaningful receipt is also stale and for the wrong SHA
- `lifeline`, `playbook`, `stream`, and `trove` still fail the release gate on stale and wrong-SHA receipt provenance

## Root Validation Boundary

The root workspace is not at a clean validation checkpoint right now.

`runtime/receipts/validation/stack-validation.latest.json` currently reports:

- `critical=0 error=4 warning=0 info=0`
- `stack-lock-drift`
- `stack-lock-render-drift`
- `stack-lock-worktree-drift` for `stack.lock.yaml#foundation`
- `stack-lock-worktree-drift` for `stack.lock.yaml#lifeline`

That validation drift is the expected consequence of the intentional owner-repo QA manifest/path and `docs/qa.md` edits now present in `repos/foundation`, `repos/lifeline`, `repos/stream`, and `repos/trove`; it is not a new validator correctness problem.

## Exact Remaining Blocker Classes

The repaired topology moves the system off bad read-model truth. The remaining blocker classes are now simpler and real:

1. stale release receipts for `fitness`, `lifeline`, `playbook`, `stream`, and `trove`
2. stale Fitness Hobby governance checkpoints inside release-readiness
3. `foundation` fresh run blocked at promotion status rather than freshness or SHA mismatch
4. root `stack.lock.yaml` drift caused by intentional owner-repo QA manifest/path and `docs/qa.md` edits that have not yet been reconciled into the lockfile or otherwise cleared

## Validation

- `python -m unittest tests.test_atlas_qa_pipeline.AtlasQaPipelineTests.test_evidence_index_merges_root_owned_and_repo_local_contracts tests.test_atlas_qa_pipeline.AtlasQaPipelineTests.test_adoption_drift_uses_repo_registry_for_root_owned_docs_path tests.test_atlas_qa_pipeline.AtlasQaPipelineTests.test_adoption_drift_labels_prototype_only_root_config tests.test_atlas_qa_pipeline.AtlasQaPipelineTests.test_release_readiness_applies_repo_tier_policy`
- direct root read-model refresh via:
  - `build_evidence_index(root=Path("."))`
  - `build_waiver_monitor(root=Path("."))`
  - `build_adoption_drift(root=Path("."))`
  - `build_release_readiness(root=Path("."))`
  - `build_release_rehearsal(root=Path("."))`

Result:

- targeted QA pipeline tests passed
- the refreshed runtime artifacts emitted successfully
- the Book current/restart surfaces can now point at repaired root QA truth instead of stale release-green narration

## Exact Next Honest Move

- owner-side evidence refresh for `fitness`, `lifeline`, `playbook`, `stream`, and `trove`
- owner-side promotion-status conversion or policy reconciliation for the fresh `foundation` run
- root `stack.lock.yaml` re-sync only after those owner-side dirty-state decisions are intentionally resolved
