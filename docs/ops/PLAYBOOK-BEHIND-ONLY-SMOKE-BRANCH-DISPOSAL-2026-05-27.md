# Playbook Behind-Only Smoke Branch Disposal - 2026-05-27

- Date: `2026-05-27`
- Lane: `Playbook behind-only smoke branch disposal execution pass`
- Mode: `branch-only disposal`
- Source decision: `docs/ops/PLAYBOOK-BEHIND-ONLY-SMOKE-BRANCH-DISPOSAL-DECISION-2026-05-27.md`
- Control-plane checkpoint: `main@1c4605b`

## Objective

Delete only the exact Playbook behind-only smoke branch refs already cleared in the branch-only decision receipt.

This pass does not:

- remove worktrees
- drop stashes
- delete files or directories
- mutate Lifeline
- mutate Playbook manual-review or safety-checkpoint surfaces
- mutate Supabase, Vercel, Discord, runtime, schema, or data surfaces
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `1c4605b193a947d6725d2619fce8f4840cd8a07c`
- status before mutation: clean except intentional untracked `archive/`

## Inputs

- `docs/ops/PLAYBOOK-BEHIND-ONLY-SMOKE-BRANCH-DISPOSAL-DECISION-2026-05-27.md`
- `docs/ops/PLAYBOOK-LIFELINE-EXTERNAL-WORKTREE-SMOKE-CLOSEOUT-RECHECK-2026-05-27.md`
- `docs/ops/FULL-STACK-RESYNC-CLOSEOUT-CONSOLIDATION-2026-05-27.md`

## Pre-Delete Verification

Reconfirmed before deletion:

- `python .\ops\validation\validate_stack.py` was green at `critical=0 error=0 warning=307`
- root status was clean except intentional untracked `archive/`
- the approved branch set still matched the decision receipt exactly
- no live Playbook worktree was attached to any branch in the approved set
- every approved branch was still `origin/main [behind 74]`
- every approved branch was an ancestor of `origin/main`
- none of the approved branches was framed as:
  - a safety checkpoint
  - an evidence-bearing branch
  - an ahead-of-main proof branch
  - an active retained dependency in current restart surfaces

## Deleted Branch Refs

Deleted exactly these branch refs:

- `codex/codex-inbox-proof-docs-touch`
- `codex/codex-inbox-smoke-four`
- `codex/codex-inbox-smoke-one`
- `codex/codex-inbox-smoke-one-2`
- `codex/codex-inbox-smoke-three`
- `codex/codex-inbox-smoke-two`
- `codex/codex-inbox-smoke-two-2`
- `codex/mock-stdin-smoke-eight`
- `codex/mock-stdin-smoke-seven`
- `codex/mock-watcher-smoke-four`
- `codex/mock-watcher-smoke-one`
- `codex/mock-watcher-smoke-three`
- `codex/mock-watcher-smoke-two`
- `codex/tmp-check`

Deletion method:

- non-force `git branch -d`

Result:

- all 14 deleted cleanly without needing force

## Post-Delete State

### Playbook branch state

The behind-only smoke branch class is now gone.

Remaining Playbook branches still include:

- active owner-lane branches
- retained branch worktrees
- manual-review branches
- non-smoke doctrine / pattern / reliability branches outside this execution class

### Playbook worktree state

Post-delete `git -C repos/fawxzzy-playbook worktree list --porcelain` was unchanged:

- active repo root remained `repos/fawxzzy-playbook`
- retained `tmp/*` Playbook worktrees remained intact
- no git worktree registration changed

### Playbook stash state

Unchanged and intentionally retained:

- `stash@{0}` `On main: codex-temp-playbook-agents-noise`
- `stash@{1}` `On main: codex-temp-local-hygiene-playbook-docs`
- `stash@{2}` `On main: qa residue before syncing main after PR 8`

## Validation

Executed after deletion:

- Playbook branch listing
- Playbook worktree listing
- Playbook stash listing
- root cleanliness check via `git status --short --branch`
- `python .\ops\validation\validate_stack.py`

Result:

- deleted branch class no longer appears
- worktree registrations unchanged
- stash set unchanged
- root status returned to clean except intentional untracked `archive/`
- `critical=0 error=0 warning=307`

## What Still Blocks `100%`

`Branch & Worktree Normalization` should still remain `99%`.

Remaining blockers:

- Playbook stashes
- Playbook manual-review worktrees
- Playbook detached checkpoint `playbook-main-closeout`
- Lifeline evidence-bearing worktrees
- Lifeline safety checkpoints
- Lifeline manual-review worktrees

## Marker Reassessment

Keep markers unchanged in this pass.

Recommended unchanged markers:

- `Branch & Worktree Normalization`: `99%`
- `Full Stack Re-sync, Clean & Closeout`: `85%`
- `Inventory & Truth Map`: `74%`

Reason:

- one more retained class is now consumed
- but the remaining retained-surface gate is still real enough that `100%` would overstate closeout

## Next Package Recommendation

`Playbook / Lifeline Retained Surface Final Gate Recheck`

Purpose:

- recompute the remaining retained-surface gate after both the filesystem-only Playbook class and the behind-only Playbook smoke branch class are consumed
- decide whether any further safe subset exists
- determine whether `Branch & Worktree Normalization Final Closeout` can open or still remains blocked by stash/manual-review/evidence classes

## Outcome

The Playbook behind-only smoke branch class is now fully consumed.

Current truth:

- Playbook external smoke residue is no longer blocking on directories or behind-only smoke branches
- the remaining pressure is now stashes, manual-review surfaces, checkpoints, and Lifeline evidence/safety surfaces
- the next correct move is a retained-surface final gate recheck, not another disposal-by-momentum pass
