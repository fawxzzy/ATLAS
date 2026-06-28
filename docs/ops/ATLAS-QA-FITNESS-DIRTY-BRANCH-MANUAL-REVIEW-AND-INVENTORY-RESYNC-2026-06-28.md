# ATLAS QA Fitness Dirty Branch Manual Review And Inventory Re-Sync

## Scope

- refresh the root read model from the current dirty Fitness owner-side branch state
- republish the protected-QA and release-readiness handoff after the emulated visual blockers cleared again
- resync published inventory truth so root docs no longer describe the earlier blocked `main` snapshot as current

## Why

The earlier `ATLAS-QA-FITNESS-CURRENT-MAIN-BLOCKED-VISUAL-GATE-AND-INVENTORY-RESYNC-2026-06-28.md` receipt honestly described one live checkpoint, but it no longer matches the current owner-side Fitness worktree.

Current repo and QA truth now show:

- `repos/fawxzzy-fitness` is on branch `codex/fitness-main-progression-summary-reapply`
- the checkout is dirty
- the current commit remains `f0b1a0e1b737d4a8ad81d5aa30ba795212e0fd62`
- the latest protected-QA run is back to `manual_review`
- all emulated lenses are passing again
- the only remaining gate is the three real-device or manual lanes

## Executed proof

### Owner-side branch and dirty-state check

- `git -C repos/fawxzzy-fitness status --short --branch`

Result:

- current branch: `codex/fitness-main-progression-summary-reapply`
- dirty files remain present across the current progression-summary and spacing/layout batch

### Inventory refresh

- `python ops/stack/export_repo_inventory.py`

Result:

- `docs/registry/STACK-REPO-INVENTORY.json` and `docs/audits/STACK-REPO-INVENTORY.md` now publish:
  - `dirty_repo_count: 2`
  - stack root dirty
  - `fitness` dirty on `codex/fitness-main-progression-summary-reapply`
  - `fitness` current commit `f0b1a0e1b737d4a8ad81d5aa30ba795212e0fd62`

### Fitness verification and protected refresh

- `npm run test:mobile-regression-fixtures`
- `npm run verify`
- `python ops/atlas/qa/protected_release_refresh.py --root . --repo fitness --mode promotion`

Result:

- verification commands passed
- protected refresh latest republished successfully
- latest Fitness run is `fitness-progression-pr-smoke-20260628T062756838693Z`
- promotion status is now `manual_review`

## Current truth

### Published inventory latest

`docs/registry/STACK-REPO-INVENTORY.json` now reports:

- `dirty_repo_count: 2`
- `fitness` current ref: `codex/fitness-main-progression-summary-reapply`
- `fitness` current commit: `f0b1a0e1b737d4a8ad81d5aa30ba795212e0fd62`
- `fitness` dirty: `true`

### Protected refresh latest

`runtime/atlas/qa/protected-release-refresh.latest.json` now reports:

- `fitness`: `manual_review`
  - run: `fitness-progression-pr-smoke-20260628T062756838693Z`

### Release readiness latest

`runtime/atlas/qa/release-readiness.latest.json` now reports:

- `release_ready_count: 4`
- `manual_review_count: 1`
- `blocked_count: 0`
- `not_applicable_count: 1`
- `fitness` target SHA: `f0b1a0e1b737d4a8ad81d5aa30ba795212e0fd62`
- `fitness` release gate status: `manual_review`

### Current Fitness gate

`runtime/atlas/qa/runs/fitness-progression-pr-smoke-20260628T062756838693Z/promotion.record.json` and `report.summary.json` now agree on:

- `visual_status: passed`
- `desktop.chromium.emulated`: `pass`
  - changed pixels: `34374`
  - allowed max pixel delta: `70000`
- `android.chrome.emulated`: `pass`
  - changed pixels: `43323`
  - allowed max pixel delta: `350000`
- `iphone.webkit.emulated`: `pass`
  - changed pixels: `48639`
  - allowed max pixel delta: `225000`
- remaining manual or physical lanes:
  - `desktop.chromium.real`
  - `android.chrome.real`
  - `iphone.webkit.real`

### Local provider truth

- BrowserStack provider routing remains aligned for the real-device lanes
- this machine still has no `BROWSERSTACK_USERNAME`
- this machine still has no `BROWSERSTACK_ACCESS_KEY`

## Consequences

- the earlier blocked-current-`main` checkpoint is now historical, not current
- root inventory truth must now show both the stack root and `fitness` dirty
- the current Fitness release lane is no longer blocked on emulated visual diffs
- the remaining release-critical gate is manual or physical proof only
- the current owner-side visual/layout work is still not durably committed, so the present `manual_review` state is a dirty-branch checkpoint rather than a clean commit-backed release closeout

## Next honest moves

1. Preserve the current owner-side Fitness visual state on purpose:
   - commit the dirty branch state
   - or intentionally discard or replace it before any further release proof is treated as durable
2. Clear the remaining real-device/manual gate with one of:
   - fresh manual attestation for `desktop.chromium.real`, `android.chrome.real`, and `iphone.webkit.real`
   - or a protected provider-backed run after BrowserStack credentials exist again
3. After the owner-side visual state is durably preserved, rerun protected refresh so the release lane no longer depends on dirty-worktree truth.
