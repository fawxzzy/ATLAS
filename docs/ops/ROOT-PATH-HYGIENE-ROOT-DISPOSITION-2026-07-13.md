# Root Path Hygiene Root Disposition Receipt — 2026-07-13

## Result

Wave 1 is recorded as an incomplete root-governance disposition: `28` current warnings, `25` historical targets, `16` accepted preserved rows, `9` pending `_stack` owner rows, and `3` excluded newer rows. The lane remains incomplete: `complete=false`.

## Identity and Source Boundaries

- Cortex plan: `plan-07dfe809d062b89cafde`.
- Cortex packet: `root-path-hygiene-cortex-bridge-v1`.
- Current evidence: `runtime/receipts/validation/stack-validation.latest.json`.
- Historical preserve boundary: `docs/ops/ATLAS-CURRENT-STATE-INTELLIGENCE-PACKET-2026-07-10.md` contains the 16 accepted historical warnings and is not changed by this wave.
- Owner-remediation boundary: nine warnings in five `_stack` documentation surfaces remain `pending_owner_remediation` for the owner lane.
- Excluded-newer boundary: one durable import finding and two Playbook-doctrine receipt findings are `newer_finding_outside_historical_denominator`; they remain visible but do not change the 25-row denominator.

## Registry Contract

`docs/registry/ROOT-PATH-HYGIENE-DISPOSITION.v1.json` records stable SHA-256 evidence fingerprints over warning category, root-relative path, line number, message, and the SHA-256 of its line preview. This preserves exact receipt matching while avoiding a new copy of machine-specific absolute-path strings.

The initial validator phase requires all 25 historical warnings and all three excluded newer warnings to remain present. The final phase requires the 16 preserved warnings and three excluded warnings to remain present, all nine owner warning fingerprints absent, and owner commit evidence on all nine accepted owner rows.

## Verification

- `node ops/atlas/test_validate_root_path_hygiene_disposition.mjs`
- `node ops/atlas/validate_root_path_hygiene_disposition.mjs --registry docs/registry/ROOT-PATH-HYGIENE-DISPOSITION.v1.json --receipt runtime/receipts/validation/stack-validation.latest.json --phase initial --json`
- `python ops/validation/validate_stack.py --allow-missing-locked-repos`
- `python ops/atlas/continuity_manifest_health.py`
- `git diff --check`

## Governance Receipt

No Root Path Hygiene, Cortex, or Atlas Full-System marker moved. This Wave 1 root job did not edit, move, stage, delete, or normalize the preserved intelligence packet; modify `_stack` or another owner repository; add a root package manifest or run root `pnpm`; push, deploy, create a pull request, mutate Discord or boards, or mutate external data.

The next authorized state transition is owner-side remediation followed by a fresh final reconciliation. A marker may move only after that proof-backed final state exists.
