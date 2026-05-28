# Retained Surface Manual Disposal Pass - 2026-05-27

- Date: `2026-05-27`
- Mode: `destructive local retained-surface disposal`
- Scope: `filesystem/worktree/archive-like residue only`
- Approved delete set:
  - `../ATLAS-worktrees`
  - `repos/fawxzzy-lifeline-operator-evidence`
  - `repos/fawxzzy-playbook-codex`
  - `repos/fawxzzy-trove-release-cutover`
  - `repos/Verta-Core`
  - `repos/Verta-Core.zip`
  - `repos/playbook-old.zip`
- Source surfaces:
  - `docs/ops/FULL-STACK-RESYNC-FINAL-CLOSEOUT-2026-05-27.md`
  - `docs/ops/FULL-STACK-RESYNC-CLOSEOUT-REFRESH-2026-05-27.md`
  - `docs/ops/PLAYBOOK-LIFELINE-RETAINED-SURFACE-FINAL-GATE-RECHECK-2026-05-27.md`
  - `docs/ops/LIFELINE-EVIDENCE-SAFETY-MANUAL-REVIEW-RETAINED-SURFACE-DECISION-2026-05-27.md`
  - `docs/ops/LIFELINE-RETAINED-SURFACE-GOVERNANCE-CHECKPOINT-2026-05-27.md`
  - `docs/ops/PLAYBOOK-STASH-MANUAL-REVIEW-RETAINED-SURFACE-DECISION-2026-05-27.md`
  - `docs/ops/VERTA-TRUST-GATE.md`
  - `docs/ops/VERTA-CORE-DEBT-ROUTING.md`
  - `stack.yaml`
- Control-plane checkpoint: `main@449a820`

## Objective

Delete the exact approved retained surfaces and search only the nearby sibling locations for obviously same-class dead retained artifacts that are safe or classifiable in this pass.

This pass does not:

- touch `repos/fawxzzy-fitness`
- touch `archive/`
- widen into branch pruning, stash disposal, runtime cleanup, schema work, deploy work, or repo-local implementation changes
- reclassify owner truth

## Root State Before Execution

- branch: `main`
- HEAD: `449a820`
- status: clean except intentional untracked `archive/`
- validation: green before disposal at `critical=0 error=0 warning=310`

## Verification Checks Performed

For each approved path, this pass checked:

1. existence on disk
2. whether the path is a current truth owner
3. whether the path is a currently registered git worktree target
4. whether the latest live receipts still described the path as retained evidence, manual-review retain, quarantined surface, or similar safety posture

Important constraint:

- several approved paths were still visible in prior retained-surface or quarantine receipts
- this pass treated the user-approved delete set as the later explicit disposal decision
- no active owner repo was removed
- no active Fitness surface was touched

## Execution Method

### `../ATLAS-worktrees`

- existed as a sibling shell outside the governed root
- was not present in the current ATLAS root `git worktree list`
- contained `remove-stale-cortex-contract-v2`, which no longer presented as a live registered worktree
- removed by plain filesystem deletion

### `repos/fawxzzy-lifeline-operator-evidence`

- existed
- was not a current truth owner
- was a registered Lifeline worktree target at execution start
- removal was performed in two stages:
  - `git -C repos/fawxzzy-lifeline worktree remove --force ../fawxzzy-lifeline-operator-evidence`
  - remove the residual plain directory after the worktree admin entry was detached
- result: deleted

### `repos/fawxzzy-playbook-codex`

- existed
- was not a current truth owner
- behaved as a standalone adjacent checkout, not as a currently registered worktree under `repos/fawxzzy-playbook`
- removed by plain filesystem deletion
- result: deleted

### `repos/fawxzzy-trove-release-cutover`

- existed
- was not a current truth owner
- was a registered Trove worktree target at execution start
- removed via:
  - `git -C repos/fawxzzy-trove worktree remove --force ../fawxzzy-trove-release-cutover`
- result: deleted

### `repos/Verta-Core`

- existed
- was not a current truth owner
- remained a quarantined, untrusted raw adjacent surface
- removed by plain filesystem deletion under the explicit approved delete set
- result: deleted

### `repos/Verta-Core.zip`

- existed
- was not a current truth owner
- remained a quarantined raw archive surface
- removed by plain filesystem deletion under the explicit approved delete set
- result: deleted

### `repos/playbook-old.zip`

- existed
- was not a current truth owner
- was an obvious same-class old zip archive already named in prior cleanup receipts
- removed by plain filesystem deletion
- result: deleted

## Exact Removed Paths

The following approved paths are now absent:

- `../ATLAS-worktrees`
- `repos/fawxzzy-lifeline-operator-evidence`
- `repos/fawxzzy-playbook-codex`
- `repos/fawxzzy-trove-release-cutover`
- `repos/Verta-Core`
- `repos/Verta-Core.zip`
- `repos/playbook-old.zip`

## Additional Same-Class Candidates Found Nearby

These were inspected near the same parent locations and intentionally not auto-deleted:

| Path | Classification | Why it was not auto-deleted |
| --- | --- | --- |
| `repos/Hard Pill To Swallow.zip` | `manual-review candidate` | obvious sibling zip archive, but not in the approved delete set and not proven disposable by this pass |
| `repos/Realm Blade.zip` | `manual-review candidate` | obvious sibling zip archive, but not in the approved delete set and not proven disposable by this pass |

Notes:

- `../ATLAS-worktrees/remove-stale-cortex-contract-v2` was inside the explicitly approved parent path `../ATLAS-worktrees`
- it was removed only because the parent path itself was approved for disposal in full
- no extra sibling repo directories were auto-deleted beyond the exact approved set

## Post-Execution State

- `repos/fawxzzy-fitness` untouched
- `archive/` untouched
- no active owner repo deleted
- no current registered ATLAS root worktree target deleted
- worktree-backed removals were executed through owner git admin where applicable

## Registry And Receipt Posture

This pass does not rewrite historical registry or quarantine references in `stack.yaml` and prior receipts.

That means:

- some historical excluded-surface references still exist as control-plane provenance
- the local retained surfaces named above are now gone from disk
- any later registry hygiene pass can decide whether to prune or preserve those historical references

## Minimal Control-Plane Correction

Deleting the approved surfaces changed live present-state for:

- `stack.lock.yaml` excluded-surface projection
- `docs/registry/ATLAS-ARCHIVE-REGISTRY.json` entry `verta_core_archive`

Those files were refreshed in the minimum way required to restore validation:

- regenerated `stack.lock.yaml` from the current managed working set
- flipped `docs/registry/ATLAS-ARCHIVE-REGISTRY.json#verta_core_archive.present` to `false`
- reclassified that registry entry from `direct_current_surface` to `reference_only_manifest_surface`

## Validation

- `python .\ops\validation\validate_stack.py`
- result after receipt drafting: `critical=0 error=0 warning=310`

## Exact Next Package

`Retained surface registry hygiene review`

Why:

- the approved local disposal is complete
- historical excluded-surface and retained-surface references remain visible by design
- the next honest follow-on is a bounded control-plane review of whether any historical registry, audit, or closeout wording should now be tightened without rewriting provenance

## Rule

Approved retained-surface disposal must stay exact-subset and evidence-checked.

## Failure Mode

Deleting something old-looking that is still an active checkpoint, worktree target, or truth surface.
