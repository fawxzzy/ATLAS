# Inventory And Truth Map And ATLAS Book Mazer README Path And Dirty-Head Re-Sync

## Scope

- preserve the owner-side `mazer` README path-discipline normalization as durable repo truth
- refresh ATLAS lock, inventory, Book mirrors, and continuity manifests after `mazer` moved from the earlier clean pushed head to a newer pushed head with active owner-side residue
- keep the Fitness protected-QA blocker posture exact while restoring honest dirty-working-set truth

## Why

The earlier `INVENTORY-AND-TRUTH-MAP-AND-ATLAS-BOOK-MAZER-LEGACY-PARITY-CLEAN-HEAD-RESYNC-2026-06-28.md` receipt stopped being current once one bounded owner-side repo fix landed in `mazer` and concurrent owner work remained uncommitted.

Current owner truth now shows:

- `repos/mazer` pushed `Normalize Mazer README paths` as commit `34b806a2a8325eae965524c1b1ff92c9d4db8e20`
- branch `codex/legacy-web-port-truth` is pushed through that head
- the repo is still dirty because active owner-side residue remains in:
  - `src/scenes/MenuScene.ts`
  - `src/legacy-runtime/legacyMenuLayout.ts`
  - `tests/reset/legacy-menu-layout.test.ts`

The protected-QA blocker truth did not change:

- `fitness` still remains `manual_review`
- the remaining live blocker is still `android.chrome.real` plus `iphone.webkit.real` plus missing ATLAS GitHub Actions secrets `BROWSERSTACK_USERNAME` and `BROWSERSTACK_ACCESS_KEY`

## Executed Proof

### Owner-side Mazer preservation

- `git -C repos/mazer diff -- README.md`
- `npm run verify`
- `git -C repos/mazer add README.md`
- `git -C repos/mazer commit -m "Normalize Mazer README paths"`
- `git -C repos/mazer push origin codex/legacy-web-port-truth`
- `git -C repos/mazer status -sb`

Result:

- repo-local verify passed after the README normalization:
  - `vitest run tests/reset --maxWorkers 1`
  - `node ./scripts/build/run-build.mjs`
- pushed `mazer` head is now `34b806a2a8325eae965524c1b1ff92c9d4db8e20`
- `mazer` is not clean anymore because concurrent owner-side residue remains in `MenuScene.ts` plus two untracked legacy menu-layout files

### Root hygiene refresh

- `python ops/cortex/index_working_memory.py`
- `python ops/stack/generate_lockfile.py`
- `python ops/stack/export_repo_inventory.py`
- `python ops/validation/validate_stack.py`
- `python ops/atlas/continuity_manifest_health.py`

Result:

- working-memory catalog drift is cleared
- `stack.lock.yaml` now pins `mazer` at `34b806a2a8325eae965524c1b1ff92c9d4db8e20` with `dirty: true`
- published inventory now reports `dirty_repo_count: 3`
- root validation is back to `critical=0 error=0 warning=0 info=0`
- initiative manifest health remains `19 ok / 0 warning / 0 error`

## Current Truth

- the clean published ATLAS root checkpoint still consumed by this refresh is `9db850c108008bc0ebac5a790b197df77d922b99`
- the live dirty managed repo set is now exactly:
  - `stack`
  - `fitness`
  - `mazer`
- `fitness` is still dirty on `codex/fitness-main-progression-summary-reapply` at `09dfac80ad0fd51794425e3111d98b2660522060`
- `mazer` is now dirty on pushed `codex/legacy-web-port-truth` at `34b806a2a8325eae965524c1b1ff92c9d4db8e20`
- published inventory now reports `dirty_repo_count: 3`
- the protected-QA posture is unchanged:
  - `fitness` still remains `manual_review`
  - current governed run still remains `fitness-progression-pr-smoke-20260628T072049067050Z`
  - `desktop.chromium.real.manual` remains valid
  - remaining manual or physical lanes still are only `android.chrome.real` and `iphone.webkit.real`
  - the remaining hosted blocker still is only missing ATLAS GitHub Actions secrets `BROWSERSTACK_USERNAME` and `BROWSERSTACK_ACCESS_KEY`

## Consequences

- `Inventory & Truth Map` stays at `95%`
- `Truth Map & ATLAS Book` stays at `99%`

Why:

- the README path-discipline blocker inside `mazer` was cleared and preserved on a pushed head
- concurrent owner-side work immediately reopened `dirty-mazer` live inventory truth, so there is no additional marker ratchet
- the protected Fitness blocker family did not change
- broader continuity automation did not widen beyond the current clean validation plus manifest-health surfaces
