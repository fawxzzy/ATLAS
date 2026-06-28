# ATLAS QA Fitness Desktop Manual Attestation Closeout And Mobile Gate Resync - 2026-06-28

- Date: `2026-06-28`
- Lane: `ATLAS QA Fitness desktop manual attestation closeout`
- Owner: `ATLAS/root`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/manual-attestations/desktop.chromium.real.manual.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/captures/desktop.chromium.real/manual.png`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/manual_attestation.result.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/promotion.record.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/report.summary.json`
  - `runtime/atlas/releases/fitness/fitness-progression-pr-smoke-20260628T014030459839Z/release-snapshot.md`
  - `runtime/atlas/qa/release-readiness.latest.json`
  - `ops/atlas/qa/report_run.py`
  - `tests/test_atlas_qa_pipeline.py`

## Objective

Convert as much of the remaining current-SHA Fitness physical/manual gate as this workstation can honestly satisfy, then resync the current read-model surfaces to the narrowed blocker set.

## Executed Work

Desktop Chromium manual proof landed on the current governed run.

- Connected to a live local Chrome session against:
  - `http://127.0.0.1:3002/dev/mobile-regression?scenario=today-progression-status`
- Captured a real desktop browser screenshot to:
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/captures/desktop.chromium.real/manual.png`
- Recorded concrete attestation metadata on:
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/manual-attestations/desktop.chromium.real.manual.json`
- Filled:
  - browser version `149.0.7827.197`
  - OS version `Windows 10 Pro build 26200`
  - capture timestamp `2026-06-28T02:08:30Z`
  - screenshot checksum `sha256:d70563446a0b57d0601500f656fac0207329fbab138e158c94113f5772b83262`

The attestation chain was then rerun:

```powershell
python ops/atlas/qa/manual_attestation.py validate --root . --file runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/manual-attestations/desktop.chromium.real.manual.json
python ops/atlas/qa/manual_attestation.py validate --root . --run fitness-progression-pr-smoke-20260628T014030459839Z
python ops/atlas/qa/promote_run.py --root . --run fitness-progression-pr-smoke-20260628T014030459839Z --scenario-file ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json --stack-validation-file runtime/receipts/validation/stack-validation.latest.json
python ops/atlas/qa/report_run.py --root . --run fitness-progression-pr-smoke-20260628T014030459839Z
python ops/atlas/qa/evidence_index.py --root .
python ops/atlas/qa/release_readiness.py --root .
python ops/atlas/qa/release_snapshot.py --root . --repo fitness --run fitness-progression-pr-smoke-20260628T014030459839Z
```

One supporting projection bug was fixed in the same pass:

- `ops/atlas/qa/report_run.py` now projects valid manual attestations into the per-lens report as `manual_attested` with the manual screenshot path instead of echoing the stale pre-attestation matrix status.
- `python -m unittest tests.test_atlas_qa_pipeline` now includes regression coverage for that report projection.

## Verified State

The desktop attestation file is individually valid:

- `status`: `clean`
- `lens_id`: `desktop.chromium.real`

The run-level attestation report remains invalid overall, but only because the remaining mobile screenshots do not exist yet:

- `status`: `invalid`
- valid attested lane: `desktop.chromium.real`
- remaining invalid lanes:
  - `android.chrome.real`
  - `iphone.webkit.real`

Promotion and reporting now reflect the narrower blocker truth on committed SHA `9403472d200e7d620fc1ba8e00d6d9509f00510f`:

- `promotion_status`: `manual_review`
- `manual_required_lanes`:
  - `android.chrome.real`
  - `iphone.webkit.real`
- report status for `desktop.chromium.real`: `manual_attested`

The regenerated Fitness release snapshot now shows:

- evidence present:
  - `android.chrome.emulated`
  - `desktop.chromium.emulated`
  - `desktop.chromium.real.manual`
  - `iphone.webkit.emulated`
- evidence missing:
  - `android.chrome.real.manual`
  - `iphone.webkit.real.manual`

## Exact Remaining Honest Move

The current Fitness release gate is no longer a three-lane blocker.

Only these remaining bounded paths are still open on the current run:

1. Capture Android and iPhone real/manual screenshots plus metadata, then rerun validation and promotion.
2. Dispatch a protected/provider-backed upstream lane that satisfies those two remaining mobile requirements.

## Guard

This receipt does **not** claim Fitness release readiness landed.

- `fitness` remains `manual_review`
- only `desktop.chromium.real` is now satisfied by current-run manual attestation
- `android.chrome.real` and `iphone.webkit.real` remain the exact open release blockers
