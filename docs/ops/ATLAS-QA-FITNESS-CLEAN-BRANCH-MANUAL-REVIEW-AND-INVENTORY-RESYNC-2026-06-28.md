# ATLAS QA Fitness Clean Branch Manual Review And Inventory Re-Sync

## Scope

- refresh the root read model from the committed clean Fitness branch head
- republish current inventory truth after the owner-side source batch was preserved and temp residue was cleared
- confirm that protected QA still lands at `manual_review` on the new committed Fitness head

## Why

`ATLAS-QA-FITNESS-DIRTY-BRANCH-MANUAL-REVIEW-AND-INVENTORY-RESYNC-2026-06-28.md` captured the first honest post-blocker manual-review state, but that checkpoint still depended on an uncommitted source batch and a dirty repo.

Current owner-side truth is now stronger:

- branch `codex/fitness-main-progression-summary-reapply` preserves the source batch as commit `6ab5bbd49821952b7d2810550a141de74619142d`
- `repos/fawxzzy-fitness` is now clean
- protected QA still lands at `manual_review`
- only the stack root remains dirty because the root docs and receipts are being refreshed

## Executed proof

### Owner-side preservation and cleanup

- `git -C repos/fawxzzy-fitness commit -m "Tighten mobile routine card spacing"`
- restore `supabase/.temp/cli-latest` to the committed no-newline value so the repo returns clean
- `git -C repos/fawxzzy-fitness status --short --branch`

Result:

- current branch remains `codex/fitness-main-progression-summary-reapply`
- current commit is `6ab5bbd49821952b7d2810550a141de74619142d`
- the Fitness repo is now clean

### Verification and protected refresh

- `npm run test:mobile-regression-fixtures`
- `npm run verify`
- `python ops/atlas/qa/protected_release_refresh.py --root . --repo fitness --mode promotion`

Result:

- verification commands passed
- protected refresh latest republished successfully
- latest Fitness run is `fitness-progression-pr-smoke-20260628T064605661368Z`
- promotion status remains `manual_review`

### Inventory refresh

- `python ops/stack/export_repo_inventory.py`

Result:

- `docs/registry/STACK-REPO-INVENTORY.json` and `docs/audits/STACK-REPO-INVENTORY.md` now publish:
  - `dirty_repo_count: 1`
  - stack root dirty
  - `fitness` clean on `codex/fitness-main-progression-summary-reapply`
  - `fitness` current commit `6ab5bbd49821952b7d2810550a141de74619142d`

## Current truth

### Published inventory latest

`docs/registry/STACK-REPO-INVENTORY.json` now reports:

- `dirty_repo_count: 1`
- `fitness` current ref: `codex/fitness-main-progression-summary-reapply`
- `fitness` current commit: `6ab5bbd49821952b7d2810550a141de74619142d`
- `fitness` dirty: `false`

### Protected refresh latest

`runtime/atlas/qa/protected-release-refresh.latest.json` now reports:

- `fitness`: `manual_review`
  - run: `fitness-progression-pr-smoke-20260628T064605661368Z`

### Release readiness latest

`runtime/atlas/qa/release-readiness.latest.json` now reports:

- `release_ready_count: 4`
- `manual_review_count: 1`
- `blocked_count: 0`
- `not_applicable_count: 1`
- `fitness` target SHA: `6ab5bbd49821952b7d2810550a141de74619142d`
- `fitness` release gate status: `manual_review`

### Current Fitness gate

The current release gate is unchanged in kind but stronger in durability:

- all emulated lenses are already passing
- the owner-side source batch is now preserved at committed clean head `6ab5bbd49821952b7d2810550a141de74619142d`
- remaining manual or physical lanes:
  - `desktop.chromium.real`
  - `android.chrome.real`
  - `iphone.webkit.real`

### Local provider truth

- BrowserStack provider routing remains aligned for the real-device lanes
- this machine still has no `BROWSERSTACK_USERNAME`
- this machine still has no `BROWSERSTACK_ACCESS_KEY`

## Consequences

- the current Fitness `manual_review` checkpoint is now durable at a clean committed branch head instead of a dirty worktree
- published inventory truth returns to `dirty_repo_count: 1`
- the only remaining Fitness release blocker is the real-device or manual proof trio
- Atlas root should now point at the clean branch commit `6ab5bbd49821952b7d2810550a141de74619142d`, not at the earlier dirty-branch or current-`main` checkpoints

## Next honest moves

1. Complete the three remaining real-device/manual lanes:
   - `desktop.chromium.real`
   - `android.chrome.real`
   - `iphone.webkit.real`
2. Use one of:
   - fresh manual attestation
   - or a protected provider-backed run after BrowserStack credentials exist again
3. After that proof lands, rerun protected refresh and release readiness so the Fitness lane can move beyond `manual_review`.
