# Stack Lock And Inventory Mazer Title Button Module Parity Re-Sync

## Scope

- absorb the latest accepted `repos/mazer` owner-repo truth after the title-lockup and button-chrome module pass
- refresh the root-governed lock and inventory mirrors only
- preserve the held ATLAS-root posture without inventing a new same-lane Sandbox packet

## Why

`repos/mazer` advanced again on `codex/mazer-pass2-menu-parity`:

- previous pushed head: `df18457f718dc119bf307e893c7642252e74e445`
- new pushed head: `dd97b3cf847278661f337ad4e3c37a33e174986d`

The owner-repo lane now includes:

- modular parity execution rules in `docs/current-truth.md`
- a module-lock sequence in `docs/system-map.md`
- extracted title presentation owner `src/legacy-runtime/legacyMenuTitle.ts`
- extracted front-door button chrome owner `src/legacy-runtime/legacyMenuButtonChrome.ts`
- tighter title placement and presentation
- stronger front-door button readability

That made `stack.lock.yaml` and the published stack inventory stale until root refreshed.

## Executed Proof

### Owner-repo proof

- `npm run test -- tests/reset/legacy-menu-layout.test.ts tests/reset/legacy-menu-title.test.ts tests/reset/legacy-menu-button-chrome.test.ts tests/reset/legacy-reset.test.ts`
- `npm run lint`
- `npm run build`
- `npm run visual:matrix -- --preset core --skip-build true`

Latest owner-repo visual proof:

- `tmp/captures/mazer-layout-matrix/2026-06-29T11-56-46-964Z/full/desktop.png`

### Root proof

- `python ops/stack/export_repo_inventory.py`
- `python ops/stack/generate_lockfile.py`
- `python ops/atlas/marker_knockout_selector.py --format json`
- `python ops/validation/validate_stack.py`

## Current Truth

- `stack.lock.yaml` now pins Mazer commit `dd97b3cf847278661f337ad4e3c37a33e174986d`
- published inventory now records:
  - `mazer.current_commit: dd97b3cf847278661f337ad4e3c37a33e174986d`
  - `mazer.dirty: false`
- this first root writeback still reports `dirty_repo_count: 2` because the stack control repo is in-flight during the writeback packet
- stack validation remains non-blocking at:
  - `critical=0 error=0 warning=3 info=0`
- selector posture remains:
  - `active_lane: Sandbox Simulation Readiness`
  - `selected_percentage: 99`
  - `operator_action: hold_current_lane`

## Marker Decision

- `Sandbox Simulation Readiness` stays held at `99%`
- `Inventory & Truth Map` stays at `99%`

Why:

- this pass only absorbs accepted owner-repo truth into root lock/inventory surfaces
- no new deploy/runtime/owner-mutation evidence changed
- no honest same-lane Sandbox packet reopened

## Next Honest Move

Run one final root refresh after this writeback lands so the published inventory can settle from the temporary in-flight `dirty_repo_count: 2` posture back to the clean post-writeback posture, if no additional truth changed.
