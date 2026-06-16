# Tmp Dependency Elimination Root Worktree Disposal And Fitness Link Blocker Recheck - 2026-06-16

- Date: `2026-06-16`
- Lane: `Tmp Dependency Elimination`
- Owner: `ATLAS/root`
- Mode: `bounded cleanup execution plus blocker recheck`
- Source surfaces:
  - `docs/ops/TMP-DEPENDENCY-DEMOTION-INVENTORY-2026-05-23.md`
  - `docs/ops/WORKTREE-DISPOSAL-INVENTORY-2026-05-22.md`
  - `docs/ops/WORKTREE-DISPOSAL-RECEIPT-2026-05-22.md`
  - `docs/ops/REMAINING-CLOSEOUT-QUEUE-RESELECTION-AFTER-DUPLICATE-SURFACE-CLOSEOUT-2026-06-13.md`
  - `docs/ops/DUPLICATE-SURFACE-DECOMMISSION-FINAL-CLOSEOUT-PASS-3-2026-06-13.md`
  - live `git worktree list --porcelain` checks for the ATLAS root and `tmp/fitness-discord-http-interactions`
  - live filesystem checks under `tmp/`

## Objective

Execute the removable ATLAS-root and named Fitness-adjacent `tmp/` cleanup surfaces, preserve any non-canonical local delta that would otherwise be lost, and recheck whether the lane can honestly close.

## Executed Cleanup

### Removed ATLAS-root tmp worktree bindings

`git -C . worktree list --porcelain` now returns only:

- `worktree .`
- `branch refs/heads/main`

The following ATLAS-root `tmp/` worktrees were detached from the root repo in this pass:

- `tmp/atlas-adopt-fawx-den-os-techstack`
- `tmp/atlas-foundation-lock-refresh`
- `tmp/atlas-playbook-lock-refresh`
- `tmp/feedback-task-packet-filter-fix`
- `tmp/pr45-clean`
- `tmp/r21-seed-wave11`
- `tmp/rollback-check-1716271`
- `tmp/rollback-check-420c5c3`

Notes:

- the unique branch tips for `atlas-adopt-fawx-den-os-techstack`, `feedback-task-packet-filter-fix`, and `r21-seed-wave11` were preserved by their branch refs; this pass removed only the `tmp/` worktree bindings
- the rollback snapshots were already reachable from other refs, so their root-repo worktree wrappers were removable without creating new preservation refs

### Removed named Fitness-adjacent retained residue

This pass also removed:

- `tmp/fitness-main-post-merge`
- `tmp/atlas-qa-release-refresh-pr`

Proof:

- `git -C tmp/fitness-discord-http-interactions worktree list --porcelain` no longer lists `tmp/fitness-main-post-merge`
- `tmp/atlas-qa-release-refresh-pr` is no longer a live root worktree blocker and its stale wrapper directory was cleared in the same cleanup pass

### Preserved detached local delta before removal

The dirty detached review checkout `tmp/pr45-clean` contained non-canonical local modifications.

Before removing that worktree wrapper, this pass preserved its diff at:

- `packages/patches/tmp-dependency-elimination/pr45-clean-2026-06-16.patch`

That keeps the local delta restart-visible without keeping the dead `tmp/` worktree bound or leaving it undocumented.

## What This Pass Did Not Touch

- no canonical Fitness repo files were edited
- no `.env*` surface was edited
- no `secrets/` surface was edited
- no Vercel project linkage was changed
- no deploy mutation or remote runtime mutation was performed

## Current Exact Blocker

The lane does **not** honestly close in this pass.

The remaining blocker is now one exact retained surface:

- `tmp/fawxzzy-fitness-main-prod-source-3d00eac7`

Live recheck:

- `git -C tmp/fawxzzy-fitness-main-prod-source-3d00eac7 status --short --branch` still reports a clean `main...origin/main` checkout
- `tmp/fawxzzy-fitness-main-prod-source-3d00eac7/.vercel/project.json` still exists
- `repos/fawxzzy-fitness/.vercel/project.json` does **not** currently exist
- `repos/fawxzzy-fitness` is also not sitting on a clean canonical parity posture in this pass; it is currently a dirty owner checkout on `codex/per-day-exercise-templates`

Interpretation:

- the dangerous broad `tmp/` dependency class is no longer the real blocker
- the exact remaining blocker is that the retained `tmp/` Fitness checkout still carries the only confirmed local Vercel-aware link state
- root governance says not to change Vercel linkage without explicit approval, so this pass stops before copying, re-linking, or deleting that surface

## Marker Decision

- `Tmp Dependency Elimination`: `90% -> 95%`

Why movement is honest:

- executed state changed materially
- ATLAS-root `tmp/` worktree bindings are gone
- the stale `atlas-qa-release-refresh-pr` residue is gone
- the broken `fitness-main-post-merge` historical worktree wrapper is gone
- the blocker family narrowed from a broad retained-surface and active-worktree hold to one exact Vercel-link-bearing retained checkout

Why `100%` is still not honest:

- one retained `tmp/` Fitness checkout still carries the only confirmed local Vercel project link state
- deleting or migrating that state would cross the explicit Vercel-linkage approval boundary

## Exact Next Move

The next admissible move is no longer another broad `tmp/` inventory pass.

It is one exact approval-gated decision:

1. migrate or recreate the local Fitness Vercel link on `repos/fawxzzy-fitness`, then remove `tmp/fawxzzy-fitness-main-prod-source-3d00eac7`
2. or explicitly preserve that retained `tmp/` checkout as the approved local link-bearing fallback and keep the lane below `100%`

Without that Vercel-linkage decision, root should not claim the lane closed.
