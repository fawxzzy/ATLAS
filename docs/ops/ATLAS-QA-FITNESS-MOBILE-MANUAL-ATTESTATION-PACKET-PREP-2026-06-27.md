# ATLAS QA Fitness Mobile Manual Attestation Packet Prep - 2026-06-27

- Date: `2026-06-27`
- Lane: `ATLAS QA Fitness release-gate packet prep`
- Owner: `ATLAS/root`
- Mode: `root execution prep plus restart-proof`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `ops/atlas/qa/manual_attestation.py`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260627T065101512537Z/evaluated.result.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260627T065101512537Z/manual_attestation.result.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260627T065101512537Z/manual-attestation.scaffold.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260627T065101512537Z/manual-attestations/desktop.chromium.real.manual.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260627T065101512537Z/manual-attestations/android.chrome.real.manual.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260627T065101512537Z/manual-attestations/iphone.webkit.real.manual.json`

## Objective

Convert the remaining Fitness release gate from a generic mobile-proof blocker into one exact bounded packet with concrete attestation files and screenshot targets for the two still-open real-device lanes.

## Execution

The current governed Fitness run already had one valid manual attestation:

- run: `fitness-progression-pr-smoke-20260627T065101512537Z`
- valid attested lane: `desktop.chromium.real`
- validation receipt: `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260627T065101512537Z/manual_attestation.result.json`

The remaining unresolved lanes were confirmed from `evaluated.result.json`:

- `android.chrome.real`
- `iphone.webkit.real`

The exact packet-prep command was executed:

```powershell
python ops/atlas/qa/manual_attestation.py scaffold --root . --run fitness-progression-pr-smoke-20260627T065101512537Z --operator zredfield\\zjhre --operator-identity local:codex-desktop:zredfield\\zjhre
```

That created:

- `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260627T065101512537Z/manual-attestation.scaffold.json`
- `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260627T065101512537Z/manual-attestations/android.chrome.real.manual.json`
- `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260627T065101512537Z/manual-attestations/iphone.webkit.real.manual.json`

Expected screenshot targets are now frozen explicitly:

- `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260627T065101512537Z/captures/android.chrome.real/manual.png`
- `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260627T065101512537Z/captures/iphone.webkit.real/manual.png`

## Read-Model Result

The blocker did not clear, but it is now narrower and restart-safe:

- `fitness` remains `manual_review`
- desktop real-browser manual attestation remains valid
- only the Android and iPhone real-device lanes still require real screenshots plus completed attestation metadata
- the exact attestation JSON files already exist and no longer need to be rediscovered or hand-created

## Important Guard

This packet does **not** claim mobile proof landed.

- placeholder signatures, versions, and screenshot checksums remain unresolved in the two newly scaffolded files
- no validation rerun was performed for those placeholders
- no promotion rerun was performed from scaffold-only data

## Exact Next Honest Move

1. Capture real screenshots to:
   - `captures/android.chrome.real/manual.png`
   - `captures/iphone.webkit.real/manual.png`
2. Replace placeholder metadata and checksums in:
   - `manual-attestations/android.chrome.real.manual.json`
   - `manual-attestations/iphone.webkit.real.manual.json`
3. Validate manual attestations:
   - `python ops/atlas/qa/manual_attestation.py validate --root . --run fitness-progression-pr-smoke-20260627T065101512537Z`
4. Re-run promotion/readiness after the attestation files are valid.
