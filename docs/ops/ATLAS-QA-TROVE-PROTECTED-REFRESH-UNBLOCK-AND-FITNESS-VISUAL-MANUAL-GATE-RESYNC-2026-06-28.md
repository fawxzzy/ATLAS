# ATLAS QA Trove Protected Refresh Unblock And Fitness Visual Manual Gate Re-Sync

## Scope

- refresh protected-QA truth after the last raw-`next` `trove` blocker is cleared
- republish the current full protected release refresh state
- replace stale Fitness execution-failure wording with the current visual/manual blocker class

## Why

The published handoff surfaces still pointed at a stale blocker class for the protected release refresh family. Current execution now proves:

- `trove` no longer fails on raw `next`
- the full release set refresh completes again
- the only release-ready blocker left in the current protected-QA set is `fitness`

## What changed

1. Cleared the `trove` owner-side blocker by making repo-local web commands install-honest and by separating live-server QA smoke from repo-local verify:
   - `repos/trove/package.json`
   - `repos/trove/scripts/ensure-repo-deps.mjs`
   - `repos/trove/scripts/next-cli.mjs`
   - `repos/trove/scripts/eslint-cli.mjs`
   - `repos/trove/scripts/assert-home-smoke.mjs`
   - `repos/trove/scripts/qa-home-smoke.mjs`
   - `repos/trove/scripts/smoke-lifeline.mjs`
   - `repos/trove/scripts/start-static.mjs`
2. Updated the root adapter so the browser-capture lane uses the live-server smoke command instead of re-running full verify:
   - `ops/atlas/qa/adapters/trove.web.json`
3. Preserved the `trove` unblock on branch `codex/path-discipline-warning-slice-trove` as commit `437c7604adee02e0403d77f75162a6c5f232221f` with message `Bootstrap trove verify and visual smoke entrypoints`, then pushed it to origin.
4. Re-ran the protected release refresh family, refreshed `stack.lock.yaml` plus the published inventory, and re-read the release-readiness surfaces against the preserved `trove` pin.

## Executed proof

### Trove repo-local verification

- `npm run verify` in `repos/trove`
- result: passed

### Trove protected refresh recheck

- `python ops/atlas/qa/protected_release_refresh.py --mode evidence --repo trove --output-file runtime/atlas/qa/protected-release-refresh.trove.json`
- result: completed successfully

### Full protected refresh recheck

- `python ops/atlas/qa/protected_release_refresh.py --mode evidence`
- result: completed successfully at `2026-06-28T04:46:47.444656Z`

### Stack truth re-sync

- `python ops/stack/generate_lockfile.py`
- `python ops/stack/export_repo_inventory.py`
- `python ops/validation/validate_stack.py`
- result: `stack.lock.yaml` now pins `trove` at `437c7604adee02e0403d77f75162a6c5f232221f`, the published inventory now reports `dirty_repo_count: 2`, and root validation now reads `critical=0 error=0 warning=6 info=0`

## Current truth

### Protected refresh latest

`runtime/atlas/qa/protected-release-refresh.latest.json` now reports:

- `fitness`: `blocked`
  - run: `fitness-progression-pr-smoke-20260628T044154077263Z`
- `foundation`: `promoted_emulated`
- `lifeline`: `promoted_emulated`
- `playbook`: `promoted_emulated`
- `trove`: `promoted_emulated`
  - run: `trove-home-smoke-20260628T044553514326Z`

### Release readiness latest

`runtime/atlas/qa/release-readiness.latest.json` now reports:

- `release_ready_count: 4`
- `blocked_count: 1`
- `not_applicable_count: 1`
- only `fitness` remains blocked

### Fitness blocker class

The current Fitness blocker is no longer prepare/preflight failure. The current governed run is blocked by:

- one failed visual diff on `iphone.webkit.emulated`
  - changed pixels: `444912`
  - allowed max pixel delta: `225000`
- the still-open release-critical physical/manual requirement for:
  - `desktop.chromium.real`
  - `android.chrome.real`
  - `iphone.webkit.real`

Additional local blocker truth:

- the BrowserStack provider manifests still support those real-device lanes
- this machine currently has no `BROWSERSTACK_USERNAME` or `BROWSERSTACK_ACCESS_KEY` env vars
- therefore provider-backed closeout is not executable from this machine right now

### Published inventory and validation posture

- `stack.lock.yaml` now pins `repos/trove` at `437c7604adee02e0403d77f75162a6c5f232221f`
- `docs/registry/STACK-REPO-INVENTORY.json` and `docs/audits/STACK-REPO-INVENTORY.md` now report `dirty_repo_count: 2`
- the only dirty repos are ATLAS root and `repos/fawxzzy-fitness`
- current root validation is `critical=0 error=0 warning=6 info=0`, and every warning is repo-owned mutable-state residue rather than a contract or topology error

### Fitness worktree note

`repos/fawxzzy-fitness` remains dirty on `main`, and the current iPhone visual delta aligns with owner-side goal-summary and compact-layout changes already present in:

- `src/app/dev/mobile-regression/DevMobileRegressionRoute.tsx`
- `src/components/workout/ExerciseCardStandardTitle.tsx`

This means the remaining emulated blocker is now an owner-side visual/baseline decision, not a root harness failure.

## Consequences

- `trove` is back inside the release-ready set
- the protected refresh family is no longer blocked by stale command routing
- the canonical lock and inventory surfaces now carry the preserved `trove` commit instead of a dirty worktree assumption
- the current root blocker language must move from stale `next` / `TS2448` / `TS2454` failure wording to the current Fitness visual/manual gate

## Next honest moves

1. Preserve or intentionally ratchet the current Fitness iPhone visual state from the owner repo side.
2. Collect fresh desktop, Android, and iPhone real-device proof or valid manual attestation for the current Fitness run, or re-enable BrowserStack credentials before attempting provider-backed closeout again.
3. Keep root read-model surfaces aligned to this narrower blocker class until owner-side Fitness proof materially changes again.
