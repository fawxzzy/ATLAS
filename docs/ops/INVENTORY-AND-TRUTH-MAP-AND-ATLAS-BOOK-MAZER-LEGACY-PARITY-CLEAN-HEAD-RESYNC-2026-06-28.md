# Inventory And Truth Map And ATLAS Book Mazer Legacy Parity Clean-Head Re-Sync

## Scope

- absorb the newly preserved `mazer` owner-side legacy-front-door lane into canonical ATLAS root truth
- refresh `stack.lock.yaml`, published inventory, Book mirrors, and continuity manifests after `mazer` moved from dirty local drift to a clean pushed head
- keep the Fitness protected-QA blocker posture exact while clearing the now-stale dirty-`mazer` projection

## Why

The earlier `INVENTORY-AND-TRUTH-MAP-AND-ATLAS-BOOK-LIVE-DIRTY-WORKING-SET-STACK-LOCK-RESYNC-2026-06-28.md` receipt was honest for the earlier moment, but it stopped being current once the `mazer` legacy port lane was preserved.

Current owner truth now shows:

- `repos/mazer` is clean on `codex/legacy-web-port-truth`
- current `mazer` head is `e651784860af229a0bb6a2195df55cb0fe940778`
- that head is pushed to `origin/codex/legacy-web-port-truth`
- the published inventory should therefore no longer carry `mazer` as a dirty managed repo

The protected-QA blocker truth did not change:

- `fitness` still remains `manual_review`
- the remaining live blocker is still `android.chrome.real` plus `iphone.webkit.real` plus missing ATLAS GitHub Actions secrets `BROWSERSTACK_USERNAME` and `BROWSERSTACK_ACCESS_KEY`

## Executed Proof

### Owner-side Mazer preservation

- `git -C repos/mazer status --short --branch`
- `git -C repos/mazer rev-parse HEAD`
- `git -C repos/mazer show --stat --oneline --no-patch HEAD`
- `git -C repos/mazer push -u origin codex/legacy-web-port-truth`

Result:

- `mazer` is clean on `codex/legacy-web-port-truth`
- current `mazer` head is `e651784860af229a0bb6a2195df55cb0fe940778`
- subject: `Port Mazer front door toward legacy parity`
- owner-side durable receipt now exists at `repos/mazer/docs/ops/MAZER-LEGACY-MAIN-MENU-PARITY-PACKET-2026-06-28.md`

### Stack truth refresh

- `python ops/stack/generate_lockfile.py`
- `python ops/stack/export_repo_inventory.py`

Result:

- `stack.lock.yaml` now pins `mazer` clean on `codex/legacy-web-port-truth` at `e651784860af229a0bb6a2195df55cb0fe940778`
- `docs/registry/STACK-REPO-INVENTORY.json` and `docs/audits/STACK-REPO-INVENTORY.md` now publish:
  - `dirty_repo_count: 2`
  - `fitness` dirty at `09dfac80ad0fd51794425e3111d98b2660522060`
  - `mazer` clean at `e651784860af229a0bb6a2195df55cb0fe940778`
  - `stack` dirty because this writeback mutates stack-owned truth surfaces again

### Root posture verification

- `python ops/validation/validate_stack.py`
- `python ops/atlas/continuity_manifest_health.py`
- `python ops/atlas/continuity_open_marker_restart_index.py`

Result:

- root validation remains `critical=0 error=0 warning=0 info=0`
- initiative manifest health remains `19 ok / 0 warning / 0 error`
- eligible open-marker restart readiness remains `7 / 7`

## Current Truth

- the clean published ATLAS root checkpoint still consumed by this refresh is `9db850c108008bc0ebac5a790b197df77d922b99`
- the live dirty managed repo set is now exactly:
  - `stack`
  - `fitness`
- `fitness` is still dirty on `codex/fitness-main-progression-summary-reapply` at `09dfac80ad0fd51794425e3111d98b2660522060`
- `mazer` is now clean on `codex/legacy-web-port-truth` at `e651784860af229a0bb6a2195df55cb0fe940778`
- published inventory now reports `dirty_repo_count: 2`
- the protected-QA posture is unchanged:
  - `fitness` still remains `manual_review`
  - current governed run still remains `fitness-progression-pr-smoke-20260628T072049067050Z`
  - `desktop.chromium.real.manual` remains valid
  - remaining manual or physical lanes still are only `android.chrome.real` and `iphone.webkit.real`
  - the remaining hosted blocker still is only missing ATLAS GitHub Actions secrets `BROWSERSTACK_USERNAME` and `BROWSERSTACK_ACCESS_KEY`

## Consequences

- `Inventory & Truth Map` moves to `95%`
- `Truth Map & ATLAS Book` stays at `99%`

Why:

- one real owner-side blocker was cleared because the live inventory no longer has to carry dirty `mazer`
- the Book-side projection changed materially enough to require a new current receipt
- the protected Fitness blocker family did not change
- broader continuity automation still did not widen beyond the current health, coverage, and restart-index surfaces
