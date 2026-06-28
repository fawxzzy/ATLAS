# ATLAS QA Fitness Current Main Blocked Visual Gate And Inventory Re-Sync

## Scope

- reconcile the earlier branch-only Fitness `manual_review` ratchet against the current live `main` checkout
- refresh the published inventory from current repo topology
- republish protected-QA latest artifacts from current `fitness` `main`
- replace stale "manual review" handoff wording with the current blocked visual/manual gate

## Why

The earlier June 28 branch run at `3fe4ab2da88481ec3413535d9d93fb0ee9e2295d` was real, but it stopped being the live Fitness checkout truth after the repo moved again.

Current repo topology now proves:

- `origin/codex/fitness-progression-target-summary-ratchet` still preserves `3fe4ab2d` (`Normalize fitness progression target summaries`)
- the local `codex/fitness-progression-target-summary-ratchet` branch adds `1a835823` on top of that branch line
- `main` and `origin/main` now both point at `f0b1a0e1b737d4a8ad81d5aa30ba795212e0fd62` (`Retire legacy Discord polling endpoint`)

That means the earlier branch-only manual-review checkpoint and baseline ratchet cannot be treated as the current root handoff truth for Fitness release readiness.

## Executed proof

### Repo-topology reconciliation

- `git -C repos/fawxzzy-fitness branch -vv`
- `git -C repos/fawxzzy-fitness log --graph --oneline --decorate --all -8`
- `git -C repos/fawxzzy-fitness reflog -15`

Result:

- the earlier preserved progression-summary commit remains real and preserved on the remote branch
- current live checkout truth is now clean `main` at `f0b1a0e1b737d4a8ad81d5aa30ba795212e0fd62`

### Published inventory refresh

- `python ops/stack/export_repo_inventory.py`

Result:

- `docs/registry/STACK-REPO-INVENTORY.json` and `docs/audits/STACK-REPO-INVENTORY.md` now publish the current topology
- `fitness` is now clean on `main` at `f0b1a0e1b737d4a8ad81d5aa30ba795212e0fd62`
- `dirty_repo_count` is now `1`
- the one published dirty managed repo is the stack root itself, because the published inventory outputs are tracked root files

### Current protected release refresh

- `python ops/atlas/qa/protected_release_refresh.py --root . --repo fitness --mode promotion`

Result:

- protected refresh latest republished successfully
- current Fitness run is `fitness-progression-pr-smoke-20260628T051422666458Z`
- current promotion status is `blocked`

## Current truth

### Published inventory latest

`docs/registry/STACK-REPO-INVENTORY.json` now reports:

- `fitness` current ref: `main`
- `fitness` current commit: `f0b1a0e1b737d4a8ad81d5aa30ba795212e0fd62`
- `fitness` dirty: `false`
- `dirty_repo_count: 1`

### Protected refresh latest

`runtime/atlas/qa/protected-release-refresh.latest.json` now reports:

- `fitness`: `blocked`
  - run: `fitness-progression-pr-smoke-20260628T051422666458Z`

### Release readiness latest

`runtime/atlas/qa/release-readiness.latest.json` now reports:

- `release_ready_count: 4`
- `manual_review_count: 0`
- `blocked_count: 1`
- `not_applicable_count: 1`
- `fitness` target SHA: `f0b1a0e1b737d4a8ad81d5aa30ba795212e0fd62`
- `fitness` release gate status: `blocked`

### Current Fitness blocker class

The current Fitness blocker is no longer the earlier branch-only narrowed iPhone gate. On current `main`, the blocked promotion now comes from:

- `android.chrome.emulated`
  - changed pixels: `500097`
  - allowed max pixel delta: `350000`
- `iphone.webkit.emulated`
  - changed pixels: `680850`
  - allowed max pixel delta: `225000`
- still-open release-critical manual lanes:
  - `desktop.chromium.real`
  - `android.chrome.real`
  - `iphone.webkit.real`

Additional local provider truth:

- BrowserStack provider routing remains valid for those real-device lanes
- this machine still has no `BROWSERSTACK_USERNAME`
- this machine still has no `BROWSERSTACK_ACCESS_KEY`

## Consequences

- the earlier June 28 branch-only `manual_review` window is now historical, not current
- the protected-QA root truth is back to `blocked` on current Fitness `main`
- the preserved progression-summary ratchet at `3fe4ab2d` remains available as an owner-side branch decision, but it is not the current release-readiness basis
- current Atlas read-model surfaces must point to `f0b1a0e1b737d4a8ad81d5aa30ba795212e0fd62` plus the reopened Android and iPhone emulated blocker class

## Next honest moves

1. Decide the owner-side Fitness visual state on purpose:
   - cherry-pick or otherwise adopt `3fe4ab2d` onto `main`, then rerun protected refresh
   - or keep current `main` visual state and intentionally re-ratchet baselines against it
2. After the owner-side visual state is settled, rerun the protected refresh and release-readiness latest artifacts.
3. Clear the remaining real-device/manual gate with fresh manual attestation or restored BrowserStack credentials.
