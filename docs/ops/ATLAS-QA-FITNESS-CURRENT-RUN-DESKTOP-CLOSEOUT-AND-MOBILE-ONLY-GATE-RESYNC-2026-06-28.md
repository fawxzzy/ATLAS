# ATLAS QA Fitness Current Run Desktop Closeout And Mobile-Only Gate Re-Sync - 2026-06-28

- Date: `2026-06-28`
- Lane: `ATLAS QA Fitness current-run desktop manual attestation closeout`
- Owner: `ATLAS/root`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T072049067050Z/manual-attestations/desktop.chromium.real.manual.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T072049067050Z/manual_attestation.result.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T072049067050Z/promotion.record.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T072049067050Z/report.summary.json`
  - `runtime/atlas/releases/fitness/fitness-progression-pr-smoke-20260628T072049067050Z/release-snapshot.md`
  - `runtime/atlas/qa/release-readiness.latest.json`
  - `docs/ops/ATLAS-ROOT-MAIN-AND-FITNESS-POST-VERIFY-ZERO-DIRTY-INVENTORY-RESYNC-2026-06-28.md`

## Objective

Recreate the current-run Fitness desktop real-browser proof on the latest protected refresh so the live release gate narrows from a three-lane physical/manual blocker to the remaining mobile-only blocker set.

## Executed Work

The current protected Fitness run was first prepared for honest manual closeout:

- run: `fitness-progression-pr-smoke-20260628T072049067050Z`
- command:
  - `python ops/atlas/qa/manual_attestation.py scaffold --root . --run fitness-progression-pr-smoke-20260628T072049067050Z --operator "zredfield\\zjhre" --operator-identity "local:codex-desktop:zredfield\\zjhre"`

Desktop proof then landed on that same run:

- route:
  - `http://127.0.0.1:3002/dev/mobile-regression?scenario=today-progression-status`
- required seam remained visible in a live local Chrome session:
  - `Back Squat`
  - `Promote`
  - `225 lbs`
  - `230 lbs`
- screenshot:
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T072049067050Z/captures/desktop.chromium.real/manual.png`
- attestation:
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T072049067050Z/manual-attestations/desktop.chromium.real.manual.json`
- recorded metadata:
  - browser version `149.0.7827.197`
  - OS version `Windows 10 Pro build 26200`
  - capture timestamp `2026-06-28T07:37:10Z`
  - screenshot checksum `sha256:a33140d80266f8e10aaa424fafaa5fd1b9cfcceba7d384d9f20b04423b274dab`

The exact run was then rebuilt from that new desktop proof:

```powershell
python ops/atlas/qa/manual_attestation.py validate --root . --file runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T072049067050Z/manual-attestations/desktop.chromium.real.manual.json
python ops/atlas/qa/manual_attestation.py validate --root . --run fitness-progression-pr-smoke-20260628T072049067050Z
python ops/atlas/qa/promote_run.py --root . --run fitness-progression-pr-smoke-20260628T072049067050Z --scenario-file ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json --stack-validation-file runtime/receipts/validation/stack-validation.latest.json
python ops/atlas/qa/report_run.py --root . --run fitness-progression-pr-smoke-20260628T072049067050Z
python ops/atlas/qa/evidence_index.py --root .
python ops/atlas/qa/release_readiness.py --root .
python ops/atlas/qa/release_snapshot.py --root . --repo fitness --run fitness-progression-pr-smoke-20260628T072049067050Z
```

## Verified State

The desktop attestation file is individually valid:

- `status`: `clean`
- `lens_id`: `desktop.chromium.real`

The run-level attestation report remains invalid overall, but only because the mobile screenshots still do not exist:

- `status`: `invalid`
- valid attested lane:
  - `desktop.chromium.real`
- remaining invalid lanes:
  - `android.chrome.real`
  - `iphone.webkit.real`

The current protected run now narrows the live blocker truth correctly:

- `promotion_status`: `manual_review`
- `manual_required_lanes`:
  - `android.chrome.real`
  - `iphone.webkit.real`
- `real_device_proof`: `manual_required`

The current release snapshot now shows:

- evidence present:
  - `android.chrome.emulated`
  - `desktop.chromium.emulated`
  - `desktop.chromium.real.manual`
  - `iphone.webkit.emulated`
- evidence missing:
  - `android.chrome.real.manual`
  - `iphone.webkit.real.manual`

The top-level release-readiness mirror remains honest and current:

- repo: `fitness`
- `readiness_source_run_id`: `fitness-progression-pr-smoke-20260628T072049067050Z`
- `promotion_status`: `manual_review`
- `release_gate_status`: `manual_review`
- remaining blocker:
  - `Release gate still requires manual or provider-backed physical proof.`

## Exact Remaining Honest Move

Only the two mobile physical/manual lanes remain open on the current protected run:

1. Capture a real Android screenshot and complete:
   - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T072049067050Z/captures/android.chrome.real/manual.png`
   - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T072049067050Z/manual-attestations/android.chrome.real.manual.json`
2. Capture a real iPhone screenshot and complete:
   - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T072049067050Z/captures/iphone.webkit.real/manual.png`
   - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T072049067050Z/manual-attestations/iphone.webkit.real.manual.json`
3. Or run one protected BrowserStack-backed pass once real credentials exist again.

## Guard

This receipt does **not** claim Fitness release readiness landed.

- `fitness` remains `manual_review`
- only `desktop.chromium.real` is now satisfied on the current protected run
- `android.chrome.real` and `iphone.webkit.real` remain the exact open release blockers
- local BrowserStack credentials are still absent on this machine
