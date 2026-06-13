# Near-100 Marker Closeout Selector After Naming And Discord Closeouts - 2026-06-12

- Date: `2026-06-12`
- Owner: `ATLAS root`
- Mode: `docs-only root selector receipt`
- Scope: `classify the next near-100 non-Fitness candidate after the naming and DiscordOS workflow closeouts without touching archive, Fitness, secrets, deploy surfaces, or closed markers`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-GITHUB-REMOTE-CANONICALIZATION-CLOSEOUT-2026-06-12.md`
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-FINAL-LIVE-CUTOVER-CLOSEOUT-2026-06-12.md`
  - `docs/ops/NEAR-100-MARKER-CLOSEOUT-SELECTOR-AND-ROOT-CLEANUP-PRESERVATION-PASS-1-2026-06-09.md`
  - `docs/ops/DUPLICATE-SURFACE-DECOMMISSION-DECISION-PASS-1-2026-05-23.md`
  - `docs/ops/TMP-DEPENDENCY-DEMOTION-RECEIPT-2026-05-23.md`
  - `docs/ops/BRAND-ASSET-CANONICALIZATION-DECISION-PASS-1-2026-05-23.md`
  - `branding/manifest.json`
  - `stack.lock.yaml`

## Objective

1. Recheck the ordered near-100 candidate set after the accepted `100%` closeouts for naming and DiscordOS workflow cutover.
2. Hold any candidate that still depends on archive/delete, protected Fitness mutation, or broader owner-lane proof.
3. Name the next admissible bounded lane if one now exists.

## Verified Root Truth

- `origin/main` and local `HEAD` both resolve to `a9555ea316c25bae8199f40b79af78406e748c04` (`Close DiscordOS feedback workflow cutover`).
- `git rev-list --left-right --count origin/main...HEAD` returned `0 0`.
- `python ops/validation/validate_stack.py --ratchet` returned `critical=0 error=0 warning=56 info=0`.
- Protected surfaces remained untouched:
  - `repos/fawxzzy-fitness`
  - `archive/`
  - `.vercel`
  - `.env`
  - `secrets/`
  - deployment surfaces

## Candidate Classification

### 1. `Duplicate Surface Decommission`

- Current marker percentage: `98%`
- Exact remaining blocker class:
  - unique-state verification still has not been converted into a closeout-ready retain/archive/delete decision for the highest-risk duplicate surfaces
  - the lane still routes through later archive-or-delete authority rather than a non-destructive root-only ratchet
- Is the blocker still real: `yes`
- Can closure happen without archive/delete: `no`
- Can closure happen without owner-repo mutation: `no honest full closeout`; the remaining verification can stay read-only, but the marker does not close until disposition authority is exercised or explicitly re-routed
- Can closure happen without Fitness: `no honest full closeout`; the highest-risk duplicate remains the Fitness-adjacent `fitness-release-main` surface from the lane's own decision pass
- Can closure happen without deploy/secrets: `yes`
- Exact proof needed for movement:
  - unique-state verification for `fitness-release-main`
  - unique-commit and residue verification for the ATLAS duplicate worktree family
  - explicit retain/archive/delete outcomes for the retained Trove and Lifeline evidence lanes
  - one bounded disposition receipt proving the duplicate family is no longer held open by unresolved state
- Whether one bounded closeout is admissible now: `no`
- Hold and exact unlock condition:
  - hold until the lane has both unique-state proof and explicit archive/delete authority, or a narrower non-destructive disposition contract that removes archive/delete as the final blocker

### 2. `Tmp Dependency Elimination`

- Current marker percentage: `90%`
- Exact remaining blocker class:
  - `tmp` is demoted out of the proven active verify/preflight path, but retained `tmp` surfaces still exist on disk and still need final retention-versus-removal governance
  - the lane still lacks proof that no remaining governed manual deploy or QA path re-enters a `tmp` checkout
- Is the blocker still real: `yes`
- Can closure happen without archive/delete: `no`
- Can closure happen without owner-repo mutation: `no honest full closeout`; the remaining no-reentry proof still depends on owner-side workflow truth, not just root narration
- Can closure happen without Fitness: `no`
- Can closure happen without deploy/secrets: `yes`, if the remaining proof stays verification-only
- Exact proof needed for movement:
  - durable proof that no governed manual deploy, QA, or recovery lane still depends on any `tmp` checkout
  - explicit retention/removal timing for `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` and `tmp/fitness-main-post-merge`
  - manual-safe cleanup or separately governed retention of `tmp/atlas-qa-release-refresh-pr`
  - broader duplicate-surface review showing no hidden `tmp` re-entry class remains
- Whether one bounded closeout is admissible now: `no`
- Hold and exact unlock condition:
  - hold until the remaining Fitness-derived `tmp` surfaces have disposition truth and the no-reentry proof exists for the last governed manual paths

### 3. `Brand Asset Canonicalization`

- Current marker percentage: `90%`
- Exact remaining blocker class:
  - the root brand manifest still points Trove consumers at stale pre-canonicalization paths under `repos/fawxzzy-trove/...`
  - the canonical Trove targets under `repos/trove/...` exist, but their current brand files still drift from canonical generated assets
- Is the blocker still real: `yes`
- Can closure happen without archive/delete: `yes`
- Can closure happen without owner-repo mutation: `no`
- Can closure happen without Fitness: `yes`
- Can closure happen without deploy/secrets: `yes`
- Exact proof needed for movement:
  - update the Trove consumer targets in `branding/manifest.json` to the canonical `repos/trove/...` paths
  - sync the canonical Trove brand/icon/favicon targets to the generated ATLAS brand outputs
  - verify the synced Trove targets match canonical asset hashes
  - package the change as one bounded root-plus-Trove brand sync without widening into Fitness or deploy work
- Additional current truth from this selector:
  - `repos/_stack/ops/assets/release-launcher.ico` already matches `branding/generated/ico/atlas-sigil-core-launcher.ico`
  - the checked Fitness canonical targets already match the current brand outputs, so Fitness is no longer the blocker class for this lane
  - the remaining drift is concentrated in Trove
- Whether one bounded closeout is admissible now: `yes`, but only as a dedicated follow-on lane rather than inside this selector receipt
- Hold or unlock condition:
  - unlock immediately for one bounded root-plus-Trove sync packet

## Selector Verdict

- `Duplicate Surface Decommission` remains `held`.
- `Tmp Dependency Elimination` remains `held`.
- `Brand Asset Canonicalization` is now the first admissible next lane.
- This selector earns `no marker movement` by itself because it is a classification receipt, not the follow-on Trove sync packet.

## Exact Next Admissible Move

Run one bounded `Brand Asset Canonicalization` follow-on packet that:

1. fixes Trove consumer path truth in `branding/manifest.json`
2. syncs the canonical Trove brand/icon/favicon targets under `repos/trove/...`
3. verifies hash parity against the ATLAS-generated assets
4. records the proof in one closeout receipt without touching Fitness, archive, secrets, or deploy surfaces
