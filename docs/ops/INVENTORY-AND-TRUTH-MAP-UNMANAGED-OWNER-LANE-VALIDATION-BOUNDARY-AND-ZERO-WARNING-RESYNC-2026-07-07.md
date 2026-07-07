# Inventory & Truth Map unmanaged owner-lane validation boundary and zero-warning resync

- Date: `2026-07-07`
- Lane: `Inventory & Truth Map`
- Mode: `docs-only root truth refresh after root-owned validator boundary implementation`
- Control-plane checkpoint: `58f0072a`
- Marker posture: `Inventory & Truth Map: 99%`

## Decision

ATLAS root now keeps unmanaged owner repos visible in inventory metadata while excluding their internals from root validation scans and cleanup hooks.

This makes the owner-lane separation operational instead of narrative-only:

- `fitness` and `mazer` stay visible as `status: unmanaged` inventory entries.
- unmanaged owner dirtiness remains advisory and non-root-blocking.
- root validation does not run generated-state cleanup, mutable-state checks, root artifact checks, repo-local env checks, or text scans inside unmanaged owner repos.
- ATLAS root validation can return all-zero without mutating Fitness or Mazer.

## Proof

- `6d68414e` landed the root validator boundary:
  - `ops/validation/validate_stack.py`
  - `tests/validation/test_validate_stack_mutable_state_rules.py`
- `58f0072a` refreshed inventory after the validator boundary.
- `python -m unittest tests/validation/test_validate_stack_mutable_state_rules.py`
  - result: `10/10`
- `python ops/validation/validate_stack.py`
  - result: `critical=0 error=0 warning=0 info=0`
- `docs/registry/STACK-REPO-INVENTORY.json`
  - `dirty_repo_count: 0`
  - `visible_dirty_repo_count: 1`
  - `advisory_dirty_repo_count: 1`

## Boundary

This is not a Fitness release-readiness proof.
This is not a Mazer game-lane cleanup.
This is not a protected BrowserStack promotion.
This is not marker movement.

The change clears root validation noise and prevents unmanaged owner repos from halting ATLAS-root validation. It does not clear the remaining marker-level condition for `Inventory & Truth Map` because higher marker movement still requires broader continuity automation, a distinct blocker-clearance class, or an explicitly selected new inventory/truth-map packet.

## Marker Decision

`Inventory & Truth Map` remains `99%`.

Reason: root validation is now cleaner and owner-lane separation is stronger, but the manifest already treats the current lane as held after continuity-coverage rollup widening. This pass refreshes restart truth and clears validation noise; it does not create a new broader continuity automation surface or close a protected proof family.

## Next

- Keep Fitness and Mazer owner work separated from ATLAS-root marker work.
- Use ATLAS root for governance, inventory, validation, receipts, and marker truth.
- Reopen `Inventory & Truth Map` only with distinct restart-truth drift, broader continuity automation, or a separately selected bounded packet.
