# Stack Lock _stack Launcher Sync Decision

Date: 2026-05-23
Lane: `_stack` lock governance repair
Mode: Narrow lock repair
Status: Accepted for lock truth

## Decision

Accept `_stack` commit `6c47304` (`assets: sync release launcher icon`) as current stack truth and refresh the `_stack` pin in `stack.lock.yaml`.

## Why

- The commit is not random local dirt.
- It is the result of the narrow `_stack` launcher icon sync already recorded in `docs/ops/BRAND-STACK-LAUNCHER-SYNC-2026-05-23.md`.
- The commit scope is a single launcher asset:
  - `repos/_stack/ops/assets/release-launcher.ico`
- `_stack` operator-surface verification passed after the sync.
- Root validation only turned red because `stack.lock.yaml` still pinned the older `_stack` commit.

## Regeneration constraint

Full `python .\ops\stack\generate_lockfile.py` regeneration is currently blocked in this root because `stack.yaml` still includes:

- `foundation`

but the declared path is absent:

- `repos/fawxzzy-foundation`

That means this pass cannot honestly rebuild the full canonical lock payload from the current managed working set.

## Accepted repair shape

- Update only the `_stack` component pin inside `stack.lock.yaml`
- Recompute the lockfile digest from the normalized payload
- Validate with:
  - `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`

## What this decision does not do

- does not accept Trove or Fitness brand sync
- does not commit `branding/**`
- does not restore `repos/fawxzzy-foundation`
- does not claim the full stack lock is globally regenerable from the current root

## Follow-up

Before the next full lock refresh, restore or explicitly reclassify the missing `foundation` repo path in stack governance so `generate_lockfile.py` can rebuild the complete managed set again.
