# ATLAS Archive Normalization Checkpoint

## Status

This checkpoint records the current non-executable archive normalization state in ATLAS root.

Current merged baseline:

- archive registry added
- archive admission runbook added
- `stack.yaml` and `stack.lock.yaml` normalized for archive governance
- `repos/dev.zip` remains provenance-only and `present: false`
- `repos/CORTEX-AND-PLAYBOOK-20260408.zip` remains provenance-only and `present: false`
- raw `repos/Verta-Core.zip` remains quarantined and non-release
- `repos/repo-backups` is classified as recovery and package-layer archive infrastructure
- canonical destinations are `packages/snapshots`, `packages/bundles`, and `packages/patches`
- no raw archives were opened, moved, trusted, or absorbed
- no executable seam was created
- root ratchet is expected to stay green after lock self-refresh

Current branch-state addition pending merge:

- archive registry enforcement added to ATLAS root validation

## Current Boundary

The current archive normalization surfaces are limited to:

- `docs/registry/ATLAS-ARCHIVE-REGISTRY.json`
- `docs/ops/ATLAS-ARCHIVE-ADMISSION-RUNBOOK.md`
- path-policy and stack-operations references for archive routing
- `stack.yaml` archive declarations
- `stack.lock.yaml` excluded-surface projection for archive lanes

The current non-goals remain:

- no raw archive extraction
- no repo moves
- no owner-repo source edits
- no Playbook, Lifeline, `_stack`, or app-repo executable lane
- no new runtime seam

## Proof Trail

Archive normalization merge and follow-up:

- ATLAS PR `#43`: normalize archive admission surfaces
- ATLAS commit `94c29b1`: refresh stack lock after archive normalization merge

Governed proof surfaces for the merged baseline plus the current branch delta:

- `docs/registry/ATLAS-ARCHIVE-REGISTRY.json`
- `docs/ops/ATLAS-ARCHIVE-ADMISSION-RUNBOOK.md`
- `ops/validation/validate_stack.py`
- `docs/architecture/PATH-POLICY.md`
- `docs/ops/STACK-OPERATIONS.md`
- `runtime/receipts/validation/stack-validation.latest.md`
- `runtime/receipts/validation/stack-validation.latest.json`

## Validation

Validation used for the merged baseline and current branch state:

```powershell
python .\ops\validation\validate_stack.py
python -m unittest tests.validation.test_validate_stack_quarantine_policy tests.validation.test_validate_stack_lock_refresh
```

## Rule

Closeout documentation may summarize archive governance, but it must not create a new owner seam or widen trust for raw archive material.

## Pattern

Archive normalization can advance through manifest, registry, runbook, and lock projection hardening without opening raw archive contents.

Known non-mazer archive governance is complete only when future archive-like surfaces under `repos/` are either registered, declared by stack archive or excluded-surface policy, or routed into canonical `packages/snapshots`, `packages/bundles`, or `packages/patches` destinations.

## Failure Mode

Treating this checkpoint as permission to open, move, or absorb raw archive surfaces would bypass the archive admission rule and collapse provenance-only material into owner truth without a named boundary review.
