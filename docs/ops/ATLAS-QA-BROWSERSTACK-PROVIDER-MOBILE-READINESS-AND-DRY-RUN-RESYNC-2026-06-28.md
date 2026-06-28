# ATLAS QA BrowserStack Provider Mobile Readiness And Dry-Run Resync - 2026-06-28

- Date: `2026-06-28`
- Lane: `ATLAS QA provider-readiness resync`
- Owner: `ATLAS/root`
- Source surfaces:
  - `ops/atlas/qa/providers/browserstack.playwright.v1.json`
  - `ops/atlas/qa/provider_readiness.py`
  - `ops/atlas/qa/ci_gate.py`
  - `ops/atlas/qa/run_matrix.py`
  - `ops/atlas/qa/capture_browserstack.mjs`
  - `tests/test_atlas_qa_pipeline.py`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T025201155886Z/matrix.result.json`
  - `runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T025201155886Z/evaluated.result.json`
  - `runtime/receipts/validation/stack-validation.latest.json`

## Objective

Bring the BrowserStack provider lane back into honest alignment with the current Fitness real-device contract so the remaining mobile blocker is reduced to actual credential availability or actual manual proof, not stale root-owned tooling truth.

## Executed Work

The BrowserStack provider manifest and control-plane logic were resynced to the current Fitness three-lens real-device contract.

- `ops/atlas/qa/providers/browserstack.playwright.v1.json` now declares support for:
  - `desktop.chromium.real`
  - `android.chrome.real`
  - `iphone.webkit.real`
- `ops/atlas/qa/provider_readiness.py` now reports:
  - `supported_lenses`
  - `unsupported_requested_lenses`
  - `live_smoke_eligible: false` when a scenario asks for physical lenses the provider manifest does not actually support
- `ops/atlas/qa/ci_gate.py` now mutates only the provider-supported real lenses when a provider override is requested, instead of blindly rewriting every real lens

The BrowserStack capture script was also corrected for mobile capability shaping.

- `ops/atlas/qa/capture_browserstack.mjs` now:
  - exports `buildCapabilities(...)` for direct regression testing
  - uses BrowserStack mobile-style capability fields for Android and iOS:
    - `deviceName`
    - `osVersion`
    - `realMobile`
  - omits desktop-only `resolution` on mobile
  - omits the iOS-incompatible console capability flag

One additional planning bug surfaced during provider dry-run validation and was fixed in the same pass.

- `ops/atlas/qa/run_matrix.py` now honors an explicit real-lens `command_ref` even when `certify_command_sequence` is empty
- that fix removes the false `missing_command_ref` findings that were previously emitted for provider-planned real lanes

## Verification

Regression coverage now passes with the provider-readiness and provider-planning additions:

```powershell
python -m unittest tests.test_atlas_qa_pipeline
```

Result on `2026-06-28`:

- `Ran 69 tests`
- `OK`

Provider-readiness proof with placeholder env presence now resolves the full Fitness real-device set cleanly:

```powershell
$env:BROWSERSTACK_USERNAME='user'
$env:BROWSERSTACK_ACCESS_KEY='key'
python ops/atlas/qa/provider_readiness.py --root . --provider ops/atlas/qa/providers/browserstack.playwright.v1.json --adapter fitness.web --scenario fitness.progression-pr-smoke
```

Observed result:

- `requested_physical_lenses`:
  - `desktop.chromium.real`
  - `android.chrome.real`
  - `iphone.webkit.real`
- `supported_lenses`:
  - `desktop.chromium.real`
  - `android.chrome.real`
  - `iphone.webkit.real`
- `unsupported_requested_lenses`: `[]`
- `live_smoke_eligible`: `true`

Provider dry-run planning now routes all three real lenses through the provider path without false command-resolution errors:

```powershell
$env:BROWSERSTACK_USERNAME='user'
$env:BROWSERSTACK_ACCESS_KEY='key'
python ops/atlas/qa/ci_gate.py --root . --mode dry-run --scenario fitness.progression-pr-smoke --adapter fitness.web --provider browserstack.playwright.v1
```

Observed result on run `fitness-progression-pr-smoke-20260628T025201155886Z`:

- `finding_count`: `0`
- `desktop.chromium.real`: `execution_mode=provider_capture`
- `android.chrome.real`: `execution_mode=provider_capture`
- `iphone.webkit.real`: `execution_mode=provider_capture`

Stack validation remained clean after the provider-tooling changes:

```powershell
python ops/validation/validate_stack.py
```

Observed result:

- `critical=0 error=0 warning=0 info=0`

## Guard

This receipt does **not** claim a live BrowserStack proof landed.

- the readiness and dry-run checks above used placeholder local env values only to prove contract routing and command wiring
- no real BrowserStack authentication was attempted in this pass
- no real Android or iPhone provider capture artifact was produced in this pass

## Exact Current Truth

The current Fitness release blocker is now split cleanly into two honest options only:

1. capture fresh current-run mobile manual proof for:
   - `android.chrome.real`
   - `iphone.webkit.real`
2. run the protected BrowserStack provider lane with real credentials present

The remaining local blocker on this workstation is therefore no longer stale provider truth.

It is only:

- missing real BrowserStack credentials for actual provider execution
- or missing manual mobile proof on the current governed Fitness run
