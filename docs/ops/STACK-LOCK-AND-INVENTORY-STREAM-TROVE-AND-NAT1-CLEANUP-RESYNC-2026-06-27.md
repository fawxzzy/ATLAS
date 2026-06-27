# Stack Lock And Inventory Stream Trove And Nat1 Cleanup Re-Sync - 2026-06-27

- Date: `2026-06-27`
- Owner: `ATLAS/root`
- Mode: `docs-only root-bounded stack-lock and inventory re-sync`
- Scope: `refresh root stack truth after stream, trove, and nat1-games settle clean and post-verify generated residue is cleared`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `stack.yaml`
  - `stack.lock.yaml`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
  - `repos/stream/**`
  - `repos/trove/**`
  - `repos/Nat1-Games/nat1-games/**`
  - `runtime/receipts/validation/stack-validation.latest.md`
- Control-plane checkpoint: `main`

## Objective

Refresh the root lock and published inventory after `stream`, `trove`, and `nat1-games` land clean local owner-side closeout, then remove the generated-state residue created by repo-local verification so the root validator returns to zero warnings.

## Done

- confirmed `repos/stream` settled clean on `main` at `43769ba86d4c6ebc419ab9e7847c3843460a094f`
- confirmed `repos/trove` settled clean on `codex/path-discipline-warning-slice-trove` at `112715291a1d9f3b21c9a830d1dab68e6751b815`
- confirmed `repos/Nat1-Games/nat1-games` settled clean on `codex/path-discipline-warning-slice-nat1` at `404460d3717fab389407582048a9b9f228f26d39`
- regenerated `stack.lock.yaml` to the current managed working set
- regenerated `docs/registry/STACK-REPO-INVENTORY.json` and `docs/audits/STACK-REPO-INVENTORY.md` from the same live working set
- lowered the published dirty-repo count from `6` to `3`
- cleared verifier residue at `repos/trove/.next`, `repos/trove/node_modules`, `repos/stream/node_modules`, `repos/Nat1-Games/nat1-games/node_modules`, and `repos/Nat1-Games/nat1-games/dist`
- reran `python .\ops\validation\validate_stack.py --ratchet` and restored `critical=0 error=0 warning=0 info=0`

## Current Read

- `stream` is now lock-pinned clean at `43769ba86d4c6ebc419ab9e7847c3843460a094f`
- `trove` is now lock-pinned clean at `112715291a1d9f3b21c9a830d1dab68e6751b815`
- `nat1-games` is now lock-pinned clean at `404460d3717fab389407582048a9b9f228f26d39`
- the published dirty-repo count is now `3`
- `stack.lock.yaml` plus the published inventory surfaces now reflect current `stream`, `trove`, and `nat1-games` truth again
- ATLAS root validation is back at `critical=0 error=0 warning=0 info=0`

## Marker Decision

- `none`

Why:

- this pass refreshes root lock and read-model truth only
- it does not widen a root-owned execution family or reopen the held Sandbox lane

## Exact Next Package

- `No immediate ATLAS-root packet is open`

Why:

- the bounded root truth drift is converted by this re-sync
- the active Sandbox family remains held and no new root packet is created by this refresh alone

## Rule

`Refresh Root Truth After Verified Owner Cleanup`

When owner-side verification temporarily creates generated residue, root should clear that residue before freezing the stack read-model so the published dirty count reflects actual repo state rather than transient verifier output.

## Failure Mode

`Published Clean-State Truth Includes Verification Residue`

If root refreshes the lock and inventory before clearing generated verifier residue, the published stack read-model overstates dirty state and restart surfaces misclassify clean owner repos as still mutable.
