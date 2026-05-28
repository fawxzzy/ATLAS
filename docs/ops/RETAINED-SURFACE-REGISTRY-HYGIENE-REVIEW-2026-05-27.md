# Retained Surface Registry Hygiene Review - 2026-05-27

- Date: `2026-05-27`
- Mode: `docs-only retained-surface registry hygiene review`
- Scope: `control-plane reconciliation only`
- Source surfaces:
  - `docs/ops/RETAINED-SURFACE-MANUAL-DISPOSAL-PASS-2026-05-27.md`
  - `docs/registry/ATLAS-ARCHIVE-REGISTRY.json`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `stack.lock.yaml`
- Control-plane checkpoint: `main@25a4216`

## Objective

Reconcile canonical control-plane surfaces after the destructive retained-surface disposal pass so deleted retained artifacts no longer appear as present in live registry or truth-map surfaces.

This pass does not:

- delete any additional path
- touch `archive/`
- touch `repos/fawxzzy-fitness`
- reopen worktree, branch, stash, runtime, schema, or deploy cleanup
- rewrite historical provenance receipts that intentionally preserve prior state

## Root State

- branch: `main`
- HEAD: `25a4216`
- status: clean except intentional untracked `archive/`
- validation: green before hygiene review at `critical=0 error=0 warning=310`

## Exact Removed Set Reconfirmed

From the durable disposal receipt, the exact removed paths are:

- `../ATLAS-worktrees`
- `repos/fawxzzy-lifeline-operator-evidence`
- `repos/fawxzzy-playbook-codex`
- `repos/fawxzzy-trove-release-cutover`
- `repos/Verta-Core`
- `repos/Verta-Core.zip`
- `repos/playbook-old.zip`

## Canonical Surface Audit

This pass checked the canonical retained-surface, registry, truth-map, and restart surfaces named in scope for stale present-state implications.

### `docs/registry/ATLAS-ARCHIVE-REGISTRY.json`

Result:

- no stale present-state remained

Why:

- `verta_core_archive` was already corrected by the disposal pass to `present: false`
- no newly deleted retained surface still appeared there as a live current surface

### `stack.lock.yaml`

Result:

- no stale present-state remained

Why:

- the deleted retained surfaces already showed `present: false`
- this pass did not need to re-open lock projection correction

### `docs/registry/STACK-REPO-INVENTORY.json`

Result:

- stale present-state was still present and required correction

Why:

- the deleted retained surfaces still appeared as `present: true` in the live machine-readable repo inventory
- that directly conflicted with the durable disposal receipt and with `stack.lock.yaml`

Action:

- regenerated the canonical repo inventory JSON using `python .\ops\stack\export_repo_inventory.py`
- the deleted retained surfaces now correctly read `present: false`

### `docs/audits/STACK-REPO-INVENTORY.md`

Result:

- paired human-readable inventory also required correction

Why:

- it is the published rendered companion to `docs/registry/STACK-REPO-INVENTORY.json`
- leaving it stale would preserve a contradictory control-plane truth surface

Action:

- refreshed automatically from the same exporter run so the rendered inventory matches the machine-readable registry

### `docs/atlas-book/01-current-state.md`

Result:

- no correction needed

Why:

- the chapter does not still name the deleted retained artifacts as currently present
- its retained-surface posture remains accurate at the governance level

### `docs/atlas-book/12-restart-and-handoff-guide.md`

Result:

- no correction needed

Why:

- restart guidance does not still instruct operators to rely on the deleted retained artifacts
- no next-ladder or restart rule changed in this pass

### `docs/atlas-book/11-system-map-graph.md`

Result:

- no correction needed

Why:

- the current system map does not still present the deleted retained artifacts as active surfaces

## Extra Nearby Candidates Reconfirmed

These remain intentionally not auto-deleted:

| Path | Current classification | Why it remains untouched |
| --- | --- | --- |
| `repos/Hard Pill To Swallow.zip` | `manual-review candidate` | obvious same-class zip artifact, but not in the approved delete set |
| `repos/Realm Blade.zip` | `manual-review candidate` | obvious same-class zip artifact, but not in the approved delete set |

This hygiene review does not reclassify them into safe-delete or blocked beyond what the disposal receipt already froze.

## Exact Files Corrected In This Pass

- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`

No change was required in:

- `docs/registry/ATLAS-ARCHIVE-REGISTRY.json`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/atlas-book/11-system-map-graph.md`

## Validation

- `python .\ops\validation\validate_stack.py`
- result after hygiene review drafting: `critical=0 error=0 warning=310`

## Exact Next Package

`Atlas-owned repo naming canonicalization inventory and dependency map`

Why:

- retained-surface disposal is now durably reconciled at the registry layer
- the next bounded control-plane gap is repo naming dependency mapping, not more retained-surface churn

## Rule

Registry hygiene must reconcile durable state after deletion without widening into another disposal pass.

## Failure Mode

A hygiene review silently expands into a second destructive cleanup pass.
