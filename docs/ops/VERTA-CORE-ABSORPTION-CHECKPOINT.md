# Verta-Core Absorption Checkpoint

## Status

This checkpoint records the current non-executable Verta-Core absorption state in ATLAS root.

Current merged state:

- doctrine absorbed
- read-only lookup absorbed
- seam-gate validator absorbed
- path-trust hardening absorbed
- raw `Verta-Core` remains quarantined and non-release
- executable scope remains unopened
- ATLAS root remains projection-only for lock and stack state
- root ratchet is expected to stay green before any new lane starts

## Current Boundary

The current absorbed Verta surfaces are limited to:

- Playbook-owned derivative doctrine
- Playbook-owned read-only doctrine lookup
- Playbook-owned seam-gate validator
- Playbook-owned path-trust hardening for candidate record location

The current non-goals remain:

- no raw `repos/Verta-Core/**` promotion
- no raw `repos/Verta-Core.zip` promotion
- no Lifeline execution lane
- no `_stack` execution lane
- no app-repo executable seam
- no adapter, parity, runtime, or cutover work

## Proof Trail

Playbook doctrine and governance surfaces:

- Playbook PR `#14`: admit initial Verta derivative doctrine patterns
- Playbook PR `#15`: close out remaining Playbook-only doctrine candidates
- Playbook PR `#16`: add `pnpm playbook patterns verta --json`
- Playbook PR `#17`: add `pnpm playbook patterns verta gate --file <candidate-record.json> --json`
- Playbook PR `#18`: fail closed on raw/quarantined Verta candidate file paths before existence checks, reads, or JSON parse

ATLAS root projections:

- ATLAS PR `#35`: register derivative absorption phase gates
- ATLAS PR `#36`: refresh stack lock after doctrine closeout merge
- ATLAS PR `#37`: refresh stack lock after Playbook lookup merge
- ATLAS PR `#38`: refresh stack lock after Playbook gate-validator merge
- ATLAS PR `#39`: refresh stack lock after the prior gate projection self-refresh

Supporting proof surfaces:

- `docs/architecture/VERTA-CORE-ABSORPTION-BLUEPRINT.md`
- `docs/ops/VERTA-CORE-DERIVATIVE-ADMISSION-RUNBOOK.md`
- `docs/ops/VERTA-TRUST-GATE.md`
- `runtime/receipts/validation/stack-validation.latest.md`
- `runtime/receipts/validation/stack-validation.latest.json`

## Future Gate

Any future executable candidate must pass:

```powershell
pnpm playbook patterns verta gate --file <candidate-record.json> --json
```

Minimum candidate record:

- `Behavior`
- `Owner repo`
- `Why it should exist`
- `Source/provenance`
- `Seam boundary`
- `Inputs`
- `Outputs`
- `Rollback path`
- `Verification`
- `Why raw Verta stays provenance-only`
- `Verdict`

## Rule

Closeout documentation may summarize absorbed surfaces, but it must not create a new owner seam.

## Pattern

Verta absorption can advance through doctrine, lookup, and validator hardening without granting runtime authority.

## Failure Mode

Treating this checkpoint as implicit permission for Lifeline, `_stack`, app-repo, adapter, parity, or runtime work would reopen executable scope without a named candidate and without a validated owner seam.
