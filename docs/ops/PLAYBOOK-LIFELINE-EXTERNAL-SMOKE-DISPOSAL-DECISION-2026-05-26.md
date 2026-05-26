# Playbook / Lifeline External Smoke Disposal Decision - 2026-05-26

- Date: `2026-05-26`
- Lane: `Playbook / Lifeline external smoke disposal decision`
- Mode: `docs-only inventory and classification`
- Control-plane checkpoint: `main@35ab062`

## Scope

Classify the remaining Playbook and Lifeline external-smoke and retained-surface pressure after:

- `docs/ops/FULL-STACK-RESYNC-CLOSEOUT-CONSOLIDATION-2026-05-26.md`
- `docs/ops/PLAYBOOK-LIFELINE-RETAINED-WORKTREE-RESIDUE-PLAN-2026-05-25.md`
- `docs/ops/PLAYBOOK-LIFELINE-RETAINED-RESIDUE-DISPOSAL-2026-05-25.md`

This pass does not:

- delete worktrees
- prune branches
- drop stashes
- mutate external services
- mutate Playbook or Lifeline repo content
- reopen Fitness Supabase hygiene

## Owner / Marker Confirmation

Confirmed from the current ATLAS Book and latest closeout receipt:

- `Fitness Supabase Profile/Data Hygiene` stays closed at `100%`
- `Inventory & Truth Map` stays `74%`
- `Full Stack Re-sync, Clean & Closeout` stays `85%`
- `Discord OS Infrastructure Separation` stays `95%`
- Discord and Music Sesh profile/data concerns stay owned by `Discord OS Infrastructure Separation`, not Fitness hygiene

No marker change is justified by this pass. This is a bounded classification packet only.

## Inputs

- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- current `git worktree list --porcelain` for:
  - `repos/fawxzzy-lifeline`
  - `repos/fawxzzy-playbook`
- current `git branch -vv` and `git stash list` for:
  - `repos/fawxzzy-lifeline`
  - `repos/fawxzzy-playbook`

## Current Evidence

- ATLAS root is on `main`
- ATLAS root `HEAD` is `35ab0629ed52a8104cef4e17f225070dff177edb`
- ATLAS root status is still bounded to intentional untracked `archive/`
- Lifeline has no live external smoke worktree family in the current worktree list
- Playbook still has:
  - retained ATLAS-root worktrees
  - one stranded external smoke checkout under user-home Codex worktree storage: `.codex/worktrees/fawxzzy-playbook/smoke-home`
  - eighteen external `.codex/worktrees/**` registrations in the Playbook repo metadata
- the historical user-home Playbook dev checkout root is no longer present
- the historical user-home Playbook `.codex/worktrees` parent is no longer present
- `.codex/worktrees/fawxzzy-playbook/smoke-home/.git` points to missing git admin under the historical user-home Playbook checkout's `.git/worktrees/smoke-home`

## Lifeline Surface Decision Table

| Surface | Current state | Classification | Why |
| --- | --- | --- | --- |
| `repos/fawxzzy-lifeline` | active repo root on `codex/lifeline-release-replay-verification`; dirty by known repo-local residue | retain temporarily | active owner-repo lane, not a disposal target in ATLAS root |
| `repos/fawxzzy-lifeline-operator-evidence` | retained evidence worktree; upstream present | retain temporarily | explicit evidence surface still referenced by prior receipts |
| `tmp/fawxzzy-lifeline-rollback-rehearsal-evidence` | retained rollback evidence worktree; upstream present | retain temporarily | rollback proof surface should not be deleted without a later evidence-retention decision |
| `tmp/lifeline-closeout-checkpoint` | retained closeout checkpoint; upstream present | retain temporarily | local-only safety checkpoint still intentionally retained |
| `tmp/lifeline-main-closeout` | merged checkpoint branch with no current upstream tracking line | manual review | stale merge checkpoint, but still a named checkpoint rather than a proven delete-now surface |
| `tmp/lifeline-main-closeout-2` | merged checkpoint branch with no current upstream tracking line | manual review | same reasoning as `lifeline-main-closeout` |
| `tmp/lifeline-main-closeout-24` | retained `main` checkpoint; in sync with `origin/main` at captured state | retain temporarily | local-only safety checkpoint, not current external smoke pressure |
| `tmp/lifeline-main-closeout-3` | merged checkpoint branch with no current upstream tracking line | manual review | same reasoning as `lifeline-main-closeout` |
| `tmp/lifeline-pr24-refresh` | retained branch worktree; upstream present | retain temporarily | still a bounded retained branch surface, not proven disposable here |
| `tmp/lifeline-release-cli-guardrails-worktree` | retained branch worktree; upstream present | retain temporarily | current branch lineage is intact and not external smoke |
| `tmp/lifeline-release-replay-verification-clean` | retained safety branch worktree; upstream present | retain temporarily | safety evidence surface should stay until a later repo-local closeout says otherwise |
| `tmp/lifeline-wave2-scout` | retained safety branch worktree; upstream present | retain temporarily | same reasoning as `lifeline-release-replay-verification-clean` |
| `tmp/lifeline-wave3-scout` | retained safety branch worktree; upstream present | retain temporarily | same reasoning as `lifeline-release-replay-verification-clean` |
| `tmp/r18-main-merge-20260511/repos/fawxzzy-lifeline` | no longer present in current worktree list | already gone | removed by the 2026-05-25 retained-residue disposal pass |
| `tmp/r18-main-merge-20260511/repos/fawxzzy-lifeline-operator-evidence` | no longer present in current worktree list | already gone | removed by the 2026-05-25 retained-residue disposal pass |

## Playbook Surface Decision Table

| Surface | Current state | Classification | Why |
| --- | --- | --- | --- |
| `repos/fawxzzy-playbook` | active repo root on `codex/playbook-sustain-docs-audit`; dirty by known repo-local runtime/docs residue | retain temporarily | active owner-repo lane, not an ATLAS-root deletion target |
| `tmp/fawxzzy-playbook-finding-identity` | retained branch worktree; upstream present | retain temporarily | still a named branch lane with intact lineage |
| `tmp/fawxzzy-playbook-sarif-output` | retained branch worktree; upstream present | retain temporarily | still a named branch lane with intact lineage |
| `tmp/fawxzzy-playbook-verify-baseline` | retained branch worktree; upstream present | retain temporarily | still a named branch lane with intact lineage |
| `tmp/playbook-fawx-den-os-doctrine` | ahead `1`, behind `17` from `origin/main` | manual review | divergent manual-review branch with possible remaining doctrine value |
| `tmp/playbook-lint-debt-closeout` | retained branch worktree; upstream present | retain temporarily | still a named branch lane with intact lineage |
| `tmp/playbook-main-closeout` | detached local-only checkpoint | manual review | stale-but-not-proven-disposable checkpoint |
| `tmp/playbook-pr9-worktree` | retained branch worktree; upstream present | retain temporarily | still a named branch lane with intact lineage |
| `tmp/playbook-research-phase-grid-evidence` | retained branch worktree; upstream present | retain temporarily | still a named branch lane with intact lineage |
| `tmp/playbook-research-phase-grid-math` | retained branch worktree; upstream present | retain temporarily | still a named branch lane with intact lineage |
| `tmp/playbook-sustain-pr19-refresh` | branch tracks `origin/codex/playbook-sustain-docs-audit` rather than a same-name upstream | manual review | stale lineage mismatch remains unresolved |
| user-home external Playbook smoke checkout `.codex/worktrees/fawxzzy-playbook/smoke-home` | stranded full checkout still on disk; `.git` points to missing git admin; branch is `codex/home-smoke` behind `74` from `origin/main` | manual review | the checkout is broken and stale, but it is still a live directory that could contain local-only residue; do not delete without one last local content review |
| external broken `.codex/worktrees/**` registrations on merged/behind-only smoke branches: `codex/codex-inbox-proof-docs-touch`, `codex/codex-inbox-smoke-four`, `codex/codex-inbox-smoke-one`, `codex/codex-inbox-smoke-one-2`, `codex/codex-inbox-smoke-three`, `codex/codex-inbox-smoke-two`, `codex/codex-inbox-smoke-two-2`, `codex/mock-stdin-smoke-eight`, `codex/mock-stdin-smoke-seven`, `codex/mock-watcher-smoke-four`, `codex/mock-watcher-smoke-one`, `codex/mock-watcher-smoke-three`, `codex/mock-watcher-smoke-two`, `codex/tmp-check` | all paths are prunable; source repo path is gone; each branch is behind `74` from `origin/main` with no ahead signal | delete now | these are broken metadata registrations only and no longer point at a live checkout family with unique branch work |
| external broken `.codex/worktrees/**` registrations on ahead-by-`1` proof/test branches: `codex/codex-inbox-proof-docs-touch-2`, `codex/mock-stdin-smoke-nine`, `codex/mock-watcher-smoke-five`, `codex/mock-watcher-smoke-six` | all paths are prunable, but each branch is ahead `1`, behind `74` from `origin/main` | export/archive first | these still represent unique local proof/test commits and should be preserved before any metadata/branch disposal |
| Playbook stashes `stash@{0}` through `stash@{2}` | intact local safety surfaces | manual review | still explicitly reserved for a dedicated repo-local stash disposition lane |
| `tmp/r18-main-merge-20260511/repos/fawxzzy-playbook` | no longer present in current worktree list | already gone | removed by the 2026-05-25 retained-residue disposal pass |

## Decision Summary

### Delete-now class

Only one clear delete-now class is currently justified:

- the fourteen external Playbook `.codex/worktrees/**` registrations that are both prunable and behind-only from `origin/main`

This delete-now class is local git/worktree metadata cleanup, not an external-service mutation.

### Export/archive-first class

Preserve first, then consider disposal:

- `codex/codex-inbox-proof-docs-touch-2`
- `codex/mock-stdin-smoke-nine`
- `codex/mock-watcher-smoke-five`
- `codex/mock-watcher-smoke-six`

These branches are the only remaining external-smoke items with explicit ahead-by-`1` unique work.

### Manual-review class

Still requires one more bounded human or repo-local review step:

- Lifeline `main-closeout*` stale merge checkpoints
- Playbook `playbook-fawx-den-os-doctrine`
- Playbook `playbook-main-closeout`
- Playbook `playbook-sustain-pr19-refresh`
- external Playbook `smoke-home`
- Playbook stashes

### Retain-temporarily class

Retain for now:

- active Playbook and Lifeline repo roots
- retained evidence worktrees
- retained safety/replay/checkpoint worktrees with intact upstream lineage

### Already-gone class

Already cleared before this pass:

- Lifeline `r18-main-merge-20260511` broken registrations
- Lifeline operator-evidence `r18-main-merge-20260511` broken registration
- Playbook `r18-main-merge-20260511` broken registration

## What This Pass Does Not Reopen

- Fitness Supabase hygiene
- Discord/Music Sesh ownership routing
- repo-local Playbook or Lifeline feature work
- remote preview / unfurl verification
- any external-service mutation

## Execution Boundaries Opened By This Decision

A later bounded local disposal pass may:

- remove the fourteen delete-now Playbook external broken registrations

That follow-on pass must not:

- delete `smoke-home`
- delete or drop the ahead-by-`1` proof/test branches without preservation
- drop Playbook stashes
- delete Lifeline retained worktrees

## Validation

Executed:

- `python .\\ops\\validation\\validate_stack.py`

Result:

- `critical=0 error=0 warning=306`

## Files Changed

- `docs/ops/PLAYBOOK-LIFELINE-EXTERNAL-SMOKE-DISPOSAL-DECISION-2026-05-26.md`

## Next Package

`Playbook / Lifeline retained-surface disposal execution pass 2`

Scope for that package:

- execute only the delete-now class from this receipt
- keep export-first and manual-review surfaces untouched
