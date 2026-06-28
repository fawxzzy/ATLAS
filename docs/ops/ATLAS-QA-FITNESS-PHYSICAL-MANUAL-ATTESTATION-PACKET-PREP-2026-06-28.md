# ATLAS QA Fitness Physical Manual Attestation Packet Prep - 2026-06-28

- Date: `2026-06-28`
- Lane: `ATLAS QA Fitness release-gate packet prep`
- Owner: `ATLAS/root`
- Mode: `root execution prep plus restart-proof`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `ops/atlas/qa/manual_attestation.py`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/evaluated.result.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/manual-attestation.scaffold.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/manual-attestations/desktop.chromium.real.manual.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/manual-attestations/android.chrome.real.manual.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/manual-attestations/iphone.webkit.real.manual.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/promotion.record.json`

## Objective

Convert the remaining Fitness release gate on committed SHA `9403472d200e7d620fc1ba8e00d6d9509f00510f` into one exact bounded packet with concrete attestation files and screenshot targets for every still-open physical/manual lane.

## Execution

The current governed Fitness run is:

- run: `fitness-progression-pr-smoke-20260628T014030459839Z`
- target SHA: `9403472d200e7d620fc1ba8e00d6d9509f00510f`
- promotion status: `manual_review`

The remaining unresolved lanes were confirmed from `evaluated.result.json` and `promotion.record.json`:

- `desktop.chromium.real`
- `android.chrome.real`
- `iphone.webkit.real`

The exact packet-prep command was executed:

```powershell
python ops/atlas/qa/manual_attestation.py scaffold --root . --run fitness-progression-pr-smoke-20260628T014030459839Z --operator zredfield\\zjhre --operator-identity local:codex-desktop:zredfield\\zjhre
```

That created:

- `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/manual-attestation.scaffold.json`
- `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/manual-attestations/desktop.chromium.real.manual.json`
- `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/manual-attestations/android.chrome.real.manual.json`
- `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/manual-attestations/iphone.webkit.real.manual.json`

Expected screenshot targets are now frozen explicitly:

- `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/captures/desktop.chromium.real/manual.png`
- `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/captures/android.chrome.real/manual.png`
- `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T014030459839Z/captures/iphone.webkit.real/manual.png`

The scaffold-only packet was then validated to freeze the exact blocker class on the current run:

```powershell
python ops/atlas/qa/manual_attestation.py validate --root . --run fitness-progression-pr-smoke-20260628T014030459839Z
```

Validation result:

- `status`: `invalid`
- `finding_count`: `3`
- `code`: `missing_attestation_screenshot`

## Read-Model Result

The blocker did not clear, but it is now restart-safe on the current committed SHA:

- `fitness` remains `manual_review`
- emulated evidence remains green on the current run
- all remaining release blockers are now bound to three exact manual-attestation files and three exact screenshot targets
- the current invalidation reason is frozen exactly: the three expected screenshot files do not exist yet

## Important Guard

This packet does **not** claim physical proof landed.

- placeholder signatures, versions, and screenshot checksums remain unresolved in the three scaffolded files
- validation was rerun only to prove the exact missing-screenshot blocker on the current run
- no promotion rerun was performed from scaffold-only data

## Exact Next Honest Move

1. Capture real screenshots to:
   - `captures/desktop.chromium.real/manual.png`
   - `captures/android.chrome.real/manual.png`
   - `captures/iphone.webkit.real/manual.png`
2. Replace placeholder metadata and checksums in:
   - `manual-attestations/desktop.chromium.real.manual.json`
   - `manual-attestations/android.chrome.real.manual.json`
   - `manual-attestations/iphone.webkit.real.manual.json`
3. Validate manual attestations:
   - `python ops/atlas/qa/manual_attestation.py validate --root . --run fitness-progression-pr-smoke-20260628T014030459839Z`
4. Re-run promotion and readiness after the attestation files are valid:
   - `python ops/atlas/qa/promote_run.py --root . --run fitness-progression-pr-smoke-20260628T014030459839Z --scenario-file ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json --stack-validation-file runtime/receipts/validation/stack-validation.latest.json`
   - `python ops/atlas/qa/evidence_index.py --root .`
   - `python ops/atlas/qa/release_readiness.py --root .`
