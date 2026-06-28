# Inventory And Truth Map And ATLAS Book Fitness Current-SHA Blocked Readiness And Inventory Re-Sync - 2026-06-28

- Date: `2026-06-28`
- Lane: `Inventory & Truth Map`
- Mode: `root-bounded inventory and projection resync`
- Scope: `refresh published inventory plus Book-side protected-QA handoff truth after live Fitness main advanced to a new dirty SHA and the release-readiness family moved from stale manual-review truth into current blocked truth`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
  - `runtime/atlas/qa/adoption-drift.latest.md`
  - `runtime/atlas/qa/release-readiness.latest.md`
  - `runtime/atlas/qa/release-rehearsal.latest.md`
  - `runtime/atlas/qa/evidence-index.latest.md`
  - `runtime/atlas/qa/protected-release-refresh.latest.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
  - `docs/memory/initiatives/continuity-manifest-inventory-and-truth-map.json`
  - `ops/stack/export_repo_inventory.py`
  - `ops/atlas/qa/adoption_drift.py`
  - `ops/atlas/qa/release_rehearsal.py`
  - `ops/atlas/qa/protected_release_refresh.py`
- Control-plane checkpoint: `codex/stack-lock-refresh-post-playbook-resync@0f991f2e`

## Objective

Refresh the canonical inventory-facing and restart-facing root truth after the live Fitness repo moved beyond the older June 28 `manual_review` checkpoint.

Two distinct drifts were open together:

1. published inventory still showed the root repo dirty at old commit `c1725f87def092c5eb8819611d0e33a600c8b21c`
2. Book-side protected-QA handoff text still described Fitness as `manual_review` on committed SHA `9403472d200e7d620fc1ba8e00d6d9509f00510f`

The live root had already changed:

- ATLAS root itself was clean on `0f991f2e6100a314b354b3d4630cad2ee60cff58`
- `repos/fawxzzy-fitness` had advanced on `main` to `12d726b57edc1c8cb81128eac9e47daabec97cd1`
- Fitness was the one live dirty repo
- the current governed Fitness release run had moved to blocked truth on `fitness-progression-pr-smoke-20260628T033301205065Z`

## Executed

1. Re-exported the published repo inventory surfaces.
2. Rebuilt the live release-readiness and release-rehearsal latest artifacts against the newest evidence index.
3. Rebuilt adoption drift so the repo-family latests point at the same newest Fitness and Playbook runs.
4. Attempted one protected-release-refresh republish and recorded the exact blocker instead of preserving stale manual-review handoff wording.
5. Refreshed the Book and continuity-manifest surfaces to the current blocked-Fitness truth.

## Exact Current Truth

- Published inventory now truthfully reads:
  - root repo `stack` clean on `0f991f2e6100a314b354b3d4630cad2ee60cff58`
  - `dirty_repo_count: 1`
  - the one dirty repo is `fitness`
  - `fitness` current commit is `12d726b57edc1c8cb81128eac9e47daabec97cd1`
- `runtime/atlas/qa/release-readiness.latest.md` now truthfully reads:
  - `release_ready_count: 4`
  - `blocked_count: 1`
  - `not_applicable_count: 1`
  - `fitness` is `blocked`
  - current governed Fitness run is `fitness-progression-pr-smoke-20260628T033301205065Z`
  - current release blocker is `Latest promotion status 'blocked' does not satisfy the release gate.`
- `runtime/atlas/qa/release-rehearsal.latest.md` now agrees with that same blocked Fitness gate on current SHA `12d726b57edc1c8cb81128eac9e47daabec97cd1`.
- `runtime/atlas/qa/adoption-drift.latest.md` remains clean across all six adopted repos, which means the adopted QA topology still resolves coherently even though the current Fitness release lane is blocked.
- Trusted-origin selection remains narrower than raw newest-run time:
  - `foundation` and `lifeline` keep their older `protected_manual` release-ready receipts because stronger trusted origin beats the newer weaker `local_dev` runs
  - `playbook` now selects the new current local-dev docs-governance run `playbook-docs-governance-20260628T033558571839Z`

## Protected Refresh Blocker

`python ops/atlas/qa/protected_release_refresh.py --mode evidence` did not republish `protected-release-refresh.latest.*`.

The refresh reached live owner-side execution and failed inside the current Fitness lane instead of failing on stale root policy:

- adapter execution surfaced `next` command-resolution failure during the owner-side prepare path
- the same run also surfaced current owner-side Fitness typecheck failure in `src/app/dev/mobile-regression/DevMobileRegressionRoute.tsx`
- exact errors included:
  - `TS2448: Block-scoped variable 'REGRESSION_WALKING_LUNGE_TARGET' used before its declaration.`
  - `TS2454: Variable 'REGRESSION_WALKING_LUNGE_TARGET' is used before being assigned.`

That means the stale protected-release-refresh latest is now an honest execution blocker, not a hidden truth gap.

## Marker Decision

- `Inventory & Truth Map`: `86% -> 87%`

Why this is enough:

- one real executed-state change was absorbed into the canonical inventory surfaces
- one real protected-QA handoff drift class was corrected from stale `manual_review` / stale SHA truth to current `blocked` / current SHA truth
- one exact current blocker class is now named precisely instead of being left inside stale root projections

Why the lane still stays below closeout:

- the blocker was clarified, not cleared
- `protected-release-refresh.latest.*` is still not republished to current time because the owner-side Fitness execution lane is blocked
- no broader owner-truth adoption widening occurred
- no broader continuity-read automation arrived beyond the current manifest-health plus coverage plus restart-index surface

## Exact Next Package

- `No immediate Inventory & Truth Map docs-only follow-on packet`

Reopen only when one of these changes:

1. owner-side Fitness execution repair clears the current prepare/preflight blocker class
2. a fresh protected-release-refresh republish lands on current Fitness SHA
3. another distinct inventory-facing or restart-facing truth drift opens

## Verification

Commands run:

- `python ops/stack/export_repo_inventory.py`
- `python ops/atlas/qa/release_rehearsal.py`
- `python ops/atlas/qa/adoption_drift.py`
- `python ops/atlas/qa/protected_release_refresh.py --mode evidence`

Results:

- published inventory now matches the live root-clean / Fitness-dirty state
- release readiness and release rehearsal now agree on one blocked Fitness gate at current SHA `12d726b57edc1c8cb81128eac9e47daabec97cd1`
- adoption drift remains `6 clean / 0 drift`
- protected release refresh fails for a concrete owner-side Fitness execution reason rather than stale root routing truth
