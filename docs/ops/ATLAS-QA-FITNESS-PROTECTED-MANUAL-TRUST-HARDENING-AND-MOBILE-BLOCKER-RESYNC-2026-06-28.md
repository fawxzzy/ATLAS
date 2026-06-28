# ATLAS QA Fitness Protected Manual Trust Hardening And Mobile Blocker Resync - 2026-06-28

- Date: `2026-06-28`
- Lane: `ATLAS QA release-governance hardening plus blocker resync`
- Owner: `ATLAS/root`
- Source surfaces:
  - `ops/atlas/qa/_common.py`
  - `tests/test_atlas_qa_pipeline.py`
  - `docs/ops/ATLAS-QA-PROMOTION-RUNBOOK.md`
  - `runtime/atlas/qa/release-readiness.latest.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T000707356239Z/promotion.record.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T000707356239Z/manual_attestation.result.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T000707356239Z/manual-attestations/android.chrome.real.manual.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T000707356239Z/manual-attestations/iphone.webkit.real.manual.json`

## Objective

Keep the remaining Fitness release blocker honest while hardening the trusted-origin contract so local execution cannot forge `protected_manual` or other non-local receipt origins.

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

Verification executed:

```powershell
python -m unittest tests.test_atlas_qa_pipeline
python ops/validation/validate_stack.py
python ops/atlas/qa/provider_readiness.py --provider ops/atlas/qa/providers/browserstack.playwright.v1.json --adapter fitness.web --scenario fitness.progression-pr-smoke
```

## Verified State

Root QA and stack validation are clean:

- `python -m unittest tests.test_atlas_qa_pipeline` -> `OK`
- `python ops/validation/validate_stack.py` -> `critical=0 error=0 warning=0 info=0`

The current Fitness release gate is still honestly narrowed to the mobile lanes on run:

- `fitness-progression-pr-smoke-20260628T000707356239Z`

Current governed state:

- `promotion_status`: `manual_review`
- `manual_required_lanes`:
  - `android.chrome.real`
  - `iphone.webkit.real`
- desktop real manual proof remains valid

The two remaining manual attestation files are still invalid for one exact reason:

- `manual_attestation.result.json` reports `missing_attestation_screenshot`
- missing files:
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T000707356239Z/captures/android.chrome.real/manual.png`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T000707356239Z/captures/iphone.webkit.real/manual.png`

Provider readiness is also still blocked in the current local environment:

- `BROWSERSTACK_USERNAME`: `missing`
- `BROWSERSTACK_ACCESS_KEY`: `missing`
- `live_smoke_eligible`: `false`

## Exact Remaining Honest Move

Only one of these paths can close the final Fitness release gate:

1. Capture real Android and iPhone screenshots into the frozen run paths, update attestation metadata and checksums, then rerun:
   - `python ops/atlas/qa/manual_attestation.py validate --root . --run fitness-progression-pr-smoke-20260628T000707356239Z`
   - `python ops/atlas/qa/promote_run.py --root . --run fitness-progression-pr-smoke-20260628T000707356239Z --scenario-file ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json --stack-validation-file runtime/receipts/validation/stack-validation.latest.json`
   - `python ops/atlas/qa/evidence_index.py --root .`
   - `python ops/atlas/qa/release_readiness.py --root .`
2. Dispatch the protected GitHub workflow with BrowserStack secrets available upstream so trusted provider-backed evidence can be generated from a protected lane.

## Guard

This receipt does not claim Fitness release readiness landed.

- `fitness` remains `manual_review`
- the remaining blocker is real mobile proof or protected provider execution only
- the trust-origin hardening prevents root from faking that blocker away locally
