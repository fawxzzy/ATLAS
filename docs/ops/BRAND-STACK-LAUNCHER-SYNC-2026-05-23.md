# Brand _stack Launcher Sync — 2026-05-23

## Scope

- Narrow brand consumer sync for `_stack` only.
- No Trove assets changed.
- No Fitness assets changed.
- No `tmp/` consumer targets used.
- No generated brand outputs were regenerated in this pass.

## Source Of Truth

- Manifest: `branding/manifest.json`
- Consumer id: `stack-launcher-icon`
- Source asset: `branding/generated/ico/atlas-sigil-core-launcher.ico`
- Target asset: `repos/_stack/ops/assets/release-launcher.ico`

## Preconditions

- `docs/ops/BRAND-ASSET-CANONICALIZATION-DECISION-PASS-1-2026-05-23.md` classified `_stack` as the only consumer eligible for an immediate narrow sync package.
- `_stack` working tree contained only the stale launcher icon delta before sync.
- Broad `atlas:brand:sync` / `atlas:brand:verify` was intentionally not used because it would evaluate Trove and Fitness consumers outside this package boundary.

## Commands Run

```powershell
Get-FileHash C:\ATLAS\branding\generated\ico\atlas-sigil-core-launcher.ico -Algorithm SHA256
Get-FileHash C:\ATLAS\repos\_stack\ops\assets\release-launcher.ico -Algorithm SHA256
Copy-Item -LiteralPath C:\ATLAS\branding\generated\ico\atlas-sigil-core-launcher.ico -Destination C:\ATLAS\repos\_stack\ops\assets\release-launcher.ico -Force
powershell -ExecutionPolicy Bypass -File C:\ATLAS\repos\_stack\ops\codex\Test-StackOperatorSurface.ps1
python .\ops\validation\validate_stack.py --allow-missing-locked-repos
```

## Hash Proof

- Source SHA256 before sync: `49EF6E187208C643A1345EE71C658F2EC99AFF68BB906DFB09C0BA859A50485B`
- Target SHA256 before sync: `37A6C3919592EE2D8B5FB87BFA755AC77D6E5566500961A0A03D15EFBECE30D7`
- Target SHA256 after sync: `49EF6E187208C643A1345EE71C658F2EC99AFF68BB906DFB09C0BA859A50485B`

## Verification

- `_stack` operator surface test: passed
- Root stack validation: passed

## Outcome

- `repos/_stack/ops/assets/release-launcher.ico` now matches the canonical launcher icon output declared in `branding/manifest.json`.
- No other `_stack` assets were modified.
- No downstream Trove or Fitness brand targets were touched.
- Remaining `branding/**` residue remains isolated for later brand packages.

## Validation

- `critical=0`
- `error=0`
- `warning=222`
- Report: `runtime/receipts/validation/stack-validation.latest.md`
