# Full Stack Re-sync, Clean & Closeout — Current Baseline Pass 2

Date: 2026-05-25
Owner: Codex
Mode: Inventory and reconciliation only
Scope: ATLAS root baseline recompute after DiscordOS scaffold work, Fitness Discord hardening, and current live rollout repair lanes

## Goal

Recompute the current clean baseline from the present durable state and identify the shortest safe path toward stack closeout without mixing mutation classes.

## 1. Current Root Cleanliness

Root repo:

- branch: `main`
- HEAD: `7e41142c60ad8b3b90616c16213787b3a6214056`
- dirty state: clean except retained untracked `archive/`

Current root residue:

- `archive/`
  - still intentionally untracked
  - still retained
  - no action taken in this pass

Assessment:

- root cleanliness is strong
- root closeout pressure is no longer broad repo chaos
- root pressure is now governance, lock alignment, and retained-surface classification

## 2. Current Managed Repo Lock Alignment

### Confirmed lock-tracked alignment

These lock-tracked repos matched current local heads in this pass:

- `_stack`
- `discordos`
- `lifeline`
- `mazer`
- `nat1-games`
- `playbook`
- `playbook-demo`
- `stream`
- `trove`

### Confirmed lock mismatch

`stack.lock.yaml` is stale for the root `stack` entry:

- lock commit: `e8086879d2b58e8c54b1c379fb9b2df626104ade`
- actual root commit: `7e41142c60ad8b3b90616c16213787b3a6214056`

Assessment:

- the stack lock is no longer globally broken
- the immediate lock hygiene problem is now narrow and explicit
- next lock package should refresh the root `stack` pin and re-audit the tracked set

## 3. Current Untracked / Dirty Surfaces

### Root

- `archive/` untracked by intent

### Fitness

`repos/fawxzzy-fitness` is still carrying unrelated tracked residue after successful Discord work:

- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/favicon-16x16.png`
- `public/favicon-32x32.png`
- `public/favicon.ico`
- `public/sw.js`
- `scripts/mobile_regression/__pycache__/__init__.cpython-313.pyc`
- `scripts/mobile_regression/__pycache__/board_builder.cpython-313.pyc`
- `src/generated/appBuildManifest.json`
- `src/lib/stretch-library-details.ts`
- `src/lib/stretch-library-summaries.ts`

Assessment:

- Fitness is functionally healthy
- residue is still present and should be classified or cleaned in a bounded package
- this is a closeout pressure point, not an immediate runtime blocker

### Lifeline

`repos/fawxzzy-lifeline` remains meaningfully dirty:

- deleted `.codex/**` local state
- modified `README.md`
- untracked `docs/history/`

Assessment:

- this is still one of the strongest branch/worktree normalization blockers

### Playbook

`repos/fawxzzy-playbook` remains one of the largest dirty worktree surfaces:

- `docs/CHANGELOG.md` staged/modified
- broad runtime command file modifications under `packages/cli-wrapper/runtime/**`

Assessment:

- this remains a major normalization blocker
- should be handled as a dedicated repo lane, not mixed into stack-wide mutation work

### Nat1 Games

- untracked `AGENTS.md`

Assessment:

- small but real registry/worktree residue

## 4. Current Missing / Extra Repo Surfaces

### Missing declared repo

`stack.yaml` still declares:

- `foundation` -> `repos/fawxzzy-foundation`

But local state in this pass:

- `repos/fawxzzy-foundation` is missing

At the same time, Vercel still shows:

- `fawxzzy-foundation`

Assessment:

- local registry truth and actual local surface are out of sync
- this is a real closeout item
- it needs a registry decision, not an implicit assumption

### Extra / adjacent / retained repo surfaces still present

Visible non-canonical repo surfaces still in `repos/`:

- `fawxzzy-lifeline-operator-evidence`
- `fawxzzy-playbook-codex`
- `fawxzzy-trove-release-cutover`
- `repo-backups`
- `Verta-Core`
- `ZachariahRedfield`
- zip archives including `Verta-Core.zip`, `Realm Blade.zip`, `Hard Pill To Swallow.zip`, `playbook-old.zip`

Assessment:

- these remain governed retained or excluded surfaces
- they are not immediate blockers, but they continue to count against closeout completeness until formally converged or receipted as permanent exclusions

## 5. Remaining Duplicate Surfaces

### Vercel duplicate/helper surfaces still active

Current Vercel projects still visible:

- canonical:
  - `fawxzzy-fitness`
  - `fawxzzy-trove`
  - `fawxzzy-mazer`
  - `fawxzzy-foundation`
- helper / duplicate-pressure:
  - `fitness-prod-rollout-20260525`
  - `fitness-deploy-green-panels`

Both helper projects still have live production deployments:

- `fitness-prod-rollout-20260525`
  - latest production ready
  - age in this pass: `8h`
- `fitness-deploy-green-panels`
  - latest production ready
  - age in this pass: `22h`

Assessment:

- stale Spotify-era projects are already gone
- remaining Vercel pressure is now focused and small
- this lane can move again once dependency review decides whether those two helper projects should be retained briefly or deleted

## 6. Remaining Tmp Surfaces

Recent `tmp/` pressure is now concentrated in rollout and verification residue:

- `fitness-prod-rollout-3f48f9c2`
- `fitness-prod-rollout-623089bb`
- `fitness-prod-rollout-b2e60634`
- `fitness-prod-rollout-20260525`
- `fitness-prod-discord.env`
- `atlas-cleanup-resync-status-2026-05-25.txt`
- multiple Vercel deployment log/jsonl artifacts
- Discord board recovery JSON exports

Assessment:

- `tmp/` is still noisy
- this is not acting as production truth in this pass
- it is a strong candidate for a bounded tmp closeout/classification package

## 7. Remaining Archive Retention Posture

`archive/` remains:

- retained
- intentionally untracked
- untouched in this pass

Assessment:

- archive retention is still acceptable as a held surface
- there is no evidence in this pass that archive needs immediate mutation
- closeout should treat it as a retained classified surface unless a later retention decision changes

## 8. Current Vercel Pressure

Current Vercel pressure state:

- Fitness production is active and recently updated
- helper/duplicate production projects still exist:
  - `fitness-prod-rollout-20260525`
  - `fitness-deploy-green-panels`
- `fawxzzy-foundation` still exists on Vercel even though the declared local repo is missing

Assessment:

- Vercel pressure is lower than earlier convergence phases
- but not fully closed
- remaining pressure is now:
  - helper project retention/deletion
  - foundation project/local-registry truth mismatch

## 9. Lanes That Can Move Toward 100 Without Broad Runtime Mutation

Strongest near-complete closeout candidates:

- `Branch & Worktree Normalization`
  - can move with focused dirty-worktree closure in `lifeline`, `playbook`, and small residue repos
- `Duplicate Surface Decommission`
  - can move with final Vercel helper-surface dependency review and decision
- `Tmp Dependency Elimination`
  - can move with one bounded tmp classification/removal package
- `Full Stack Re-sync, Clean & Closeout`
  - can move materially now that the baseline is explicit again
- `Inventory & Truth Map`
  - can move with this receipt plus stack-lock and registry reconciliation

## 10. Lanes Still Requiring Mutation / Deploy / Runtime Gating

Still gated or higher-risk:

- `Fitness Supabase Profile/Data Hygiene`
  - still requires exact row-level scope and rollback/export path
- `Preview Cache & Surface Consistency`
  - still needs deploy-backed remote verification
- further `DiscordOS` runtime work
  - should stay tiny/scaffold/shadow only until a named runtime lane is opened
- helper-project Vercel deletion
  - requires final dependency/deletion decision

## 11. Exact Next 5 Packages Toward 100%

1. `Stack Lock And Registry Reconciliation Pass`

- refresh root `stack` pin in `stack.lock.yaml`
- decide whether `foundation` remains active in `stack.yaml` or needs registry correction
- verify `discordos` and current tracked set remain aligned

2. `Branch And Worktree Normalization Closeout Pass 2`

- classify/close dirty surfaces in:
  - `repos/fawxzzy-lifeline`
  - `repos/fawxzzy-playbook`
  - `repos/Nat1-Games/nat1-games`

3. `Tmp Surface Classification And Closeout Pass 1`

- classify retained versus disposable entries under `tmp/`
- remove or receipt obsolete rollout/log artifacts
- keep only intentionally retained execution evidence

4. `Vercel Helper Surface Final Review`

- review `fitness-prod-rollout-20260525`
- review `fitness-deploy-green-panels`
- decide retain briefly / delete / reclassify

5. `Fitness Residue Classification Pass`

- classify generated/derived residue still dirty in `repos/fawxzzy-fitness`
- separate intentional generated assets from accidental leftover state
- restore a cleaner repo baseline before the next runtime-heavy lane

## Marker Recommendation

Recommended movement after this pass:

- `Full Stack Re-sync, Clean & Closeout`: `22% -> 35%`
- `Inventory & Truth Map`: `35% -> 40%`
- `Knowledge Capture & Transfer`: `72% -> 75%`

## Summary

The stack is no longer blocked by broad uncertainty. The remaining closeout pressure is concentrated into:

- one root lock mismatch
- one missing declared repo surface (`foundation`)
- a few dirty repo worktrees (`lifeline`, `playbook`, `fitness`)
- noisy but non-canonical `tmp/`
- two remaining helper Vercel projects

That means the next path to 100 is not another broad convergence pass. It is a short ladder of narrow cleanup packages with explicit ownership and no mixed mutation classes.
