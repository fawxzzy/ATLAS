# ATLAS QA Fitness Protected Manual Trust Hardening And Mobile Blocker Resync - 2026-06-28

- Date: `2026-06-28`
- Lane: `ATLAS QA release-governance hardening plus blocker resync`
- Owner: `ATLAS/root`
- Source surfaces:
  - `ops/atlas/qa/_common.py`
  - `tests/test_atlas_qa_pipeline.py`
  - `repos/fawxzzy-fitness/src/app/globals.css`
  - `repos/fawxzzy-fitness/src/lib/discord/discordos-interactions-proxy.test.ts`
  - `repos/fawxzzy-fitness/src/lib/discord/discordos-message-command-poll-proxy.test.ts`
  - `runtime/atlas/qa/release-readiness.latest.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/evaluated.result.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/promotion.record.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/test-evidence.json`

## Objective

Keep the remaining Fitness release blocker honest while hardening the trusted-origin contract so local execution cannot forge `protected_manual` or other non-local receipt origins, then resync the governed Fitness lane onto the current committed SHA.

## Executed Work

The receipt-origin resolver was tightened in `ops/atlas/qa/_common.py`.

- local execution now resolves to `local_dev`
- local env overrides can no longer relabel receipts as `protected_manual`, `ci_pr`, `ci_release`, or `provider`
- GitHub Actions still resolves:
  - `pull_request` -> `ci_pr`
  - `workflow_dispatch` -> `protected_manual`
  - other GitHub Actions execution -> `ci_release`

Regression coverage was added in `tests/test_atlas_qa_pipeline.py` for:

- rejecting trusted-origin overrides outside GitHub Actions
- preserving `workflow_dispatch` -> `protected_manual` inside GitHub Actions

Owner-side blocker conversion then completed in `repos/fawxzzy-fitness`.

- Discord proxy tests were repaired so current-head `npm run typecheck` passes again.
- The mobile regression route now disables the animated `exercise-card-progress-glint` and applies glass-off variables at the regression root, removing the unstable highlight band that was drifting between emulated captures.
- The updated Fitness repo was verified locally and committed as `9403472d200e7d620fc1ba8e00d6d9509f00510f` with message `Stabilize progression regression captures`.
- Fresh baselines were blessed from the stabilized capture set and the governed evidence gate was rerun on the committed SHA.

Verification executed:

```powershell
python -m unittest tests.test_atlas_qa_pipeline
python ops/validation/validate_stack.py
npm run verify
python ops/atlas/qa/ci_gate.py --mode evidence --scenario fitness.progression-pr-smoke --adapter fitness.web
python ops/atlas/qa/evidence_index.py
python ops/atlas/qa/release_readiness.py
python ops/atlas/qa/release_rehearsal.py
python ops/atlas/qa/adoption_drift.py
```

## Verified State

Root QA and stack validation are clean:

- `python -m unittest tests.test_atlas_qa_pipeline` -> `OK`
- `python ops/validation/validate_stack.py` -> `critical=0 error=0 warning=0 info=0`

Fitness owner verification is clean on committed SHA `9403472d200e7d620fc1ba8e00d6d9509f00510f`:

- `npm run verify` -> `Verification passed`

The current governed Fitness run is now aligned to the latest committed repo head:

- `run_id`: `fitness-progression-pr-smoke-20260628T014030459839Z`
- `target_sha`: `9403472d200e7d620fc1ba8e00d6d9509f00510f`
- `receipt_sha`: `9403472d200e7d620fc1ba8e00d6d9509f00510f`
- `sha_match`: `true`

Current governed state:

- `promotion_status`: `manual_review`
- `visual_status`: `passed`
- `test_evidence_status`: `clean`
- `manual_required_lanes`:
  - `desktop.chromium.real`
  - `android.chrome.real`
  - `iphone.webkit.real`
- `trusted_origin_status`: `warn`
- `origin_enforcement_stage`: `warn`

What closed in this resync:

- the stale wrong-SHA blocker is gone
- the emulated visual blocker is gone
- the remaining blocker is no longer a layout or typecheck problem; it is physical/manual release proof only on the current SHA

Release readiness now resolves to one exact blocker:

- `Release gate still requires manual or provider-backed physical proof.`

## Exact Remaining Honest Move

Only one of these paths can close the final Fitness release gate for committed SHA `9403472d200e7d620fc1ba8e00d6d9509f00510f`:

1. Capture fresh real-device screenshots and attestation metadata for the current run, then rerun:
   - `python ops/atlas/qa/manual_attestation.py validate --root . --run fitness-progression-pr-smoke-20260628T014030459839Z`
   - `python ops/atlas/qa/promote_run.py --root . --run fitness-progression-pr-smoke-20260628T014030459839Z --scenario-file ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json --stack-validation-file runtime/receipts/validation/stack-validation.latest.json`
   - `python ops/atlas/qa/evidence_index.py --root .`
   - `python ops/atlas/qa/release_readiness.py --root .`
2. Dispatch the protected GitHub workflow with provider credentials available upstream so trusted provider-backed physical evidence can be generated from a protected lane.

## Guard

This receipt does not claim Fitness release readiness landed.

- `fitness` remains `manual_review`
- the remaining blocker is real-device proof or protected provider execution only
- the trust-origin hardening prevents root from faking that blocker away locally
