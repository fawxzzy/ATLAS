# Playbook External Codex Worktree Stranded-Directory Disposal - 2026-05-27

- Date: `2026-05-27`
- Lane: `Playbook external Codex worktree stranded-directory disposal execution pass`
- Mode: `filesystem-only cleanup`
- Source decision: `docs/ops/PLAYBOOK-LIFELINE-EXTERNAL-WORKTREE-SMOKE-DISPOSAL-DECISION-2026-05-27.md`
- Control-plane checkpoint: `main@bb0b1ea`

## Objective

Delete only the approved stranded Playbook `.codex/worktrees/*` directories that were already proven safe as filesystem-only residue.

This pass does not:

- remove git worktree registrations
- delete branches
- drop stashes
- delete Lifeline worktrees or checkpoints
- mutate Supabase, Vercel, Discord, runtime, schema, or data surfaces
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `bb0b1ea7d74d0bb509fd62fb17aaf23b6bf4d1e1`
- status before mutation: clean except intentional untracked `archive/`

## Inputs

- `docs/ops/PLAYBOOK-LIFELINE-EXTERNAL-WORKTREE-SMOKE-DISPOSAL-DECISION-2026-05-27.md`
- `docs/ops/PLAYBOOK-LIFELINE-RETAINED-WORKTREE-RESIDUE-PLAN-2026-05-25.md`
- `docs/ops/PLAYBOOK-LIFELINE-RETAINED-RESIDUE-DISPOSAL-2026-05-25.md`
- `docs/ops/FULL-STACK-RESYNC-CLOSEOUT-CONSOLIDATION-2026-05-27.md`
- current Playbook worktree list
- current Playbook branch list
- current Playbook stash list

## Pre-Delete Verification

Reconfirmed before deletion:

- `python .\ops\validation\validate_stack.py` was green at `critical=0 error=0 warning=307`
- `git -C repos/fawxzzy-playbook worktree list --porcelain` showed only the active repo root and current `tmp/*` retained worktrees
- none of the approved names appeared under `repos/fawxzzy-playbook/.git/worktrees/`
- `repos/fawxzzy-playbook/.codex/worktrees/` still contained exactly 18 top-level directories
- every remaining directory still contained a `.git` file pointing at a missing historical gitdir target
- current receipts and restart surfaces referenced this family only as the approved filesystem-only execution subset, not as retained evidence or safety checkpoints
- matching Playbook behind-only branch refs and Playbook stashes remained explicitly out of scope for deletion

## Deleted Paths

Deleted exactly these directories:

- `repos/fawxzzy-playbook/.codex/worktrees/codex-inbox-proof-docs-touch`
- `repos/fawxzzy-playbook/.codex/worktrees/codex-inbox-proof-docs-touch-2`
- `repos/fawxzzy-playbook/.codex/worktrees/codex-inbox-smoke-four`
- `repos/fawxzzy-playbook/.codex/worktrees/codex-inbox-smoke-one`
- `repos/fawxzzy-playbook/.codex/worktrees/codex-inbox-smoke-one-2`
- `repos/fawxzzy-playbook/.codex/worktrees/codex-inbox-smoke-three`
- `repos/fawxzzy-playbook/.codex/worktrees/codex-inbox-smoke-two`
- `repos/fawxzzy-playbook/.codex/worktrees/codex-inbox-smoke-two-2`
- `repos/fawxzzy-playbook/.codex/worktrees/mock-stdin-smoke-eight`
- `repos/fawxzzy-playbook/.codex/worktrees/mock-stdin-smoke-nine`
- `repos/fawxzzy-playbook/.codex/worktrees/mock-stdin-smoke-seven`
- `repos/fawxzzy-playbook/.codex/worktrees/mock-watcher-smoke-five`
- `repos/fawxzzy-playbook/.codex/worktrees/mock-watcher-smoke-four`
- `repos/fawxzzy-playbook/.codex/worktrees/mock-watcher-smoke-one`
- `repos/fawxzzy-playbook/.codex/worktrees/mock-watcher-smoke-six`
- `repos/fawxzzy-playbook/.codex/worktrees/mock-watcher-smoke-three`
- `repos/fawxzzy-playbook/.codex/worktrees/mock-watcher-smoke-two`
- `repos/fawxzzy-playbook/.codex/worktrees/tmp-check`

Operational note:

- one directory (`codex-inbox-proof-docs-touch-2`) required a second long-path-safe PowerShell removal pass because deep nested `node_modules` paths prevented the first recursive delete from finishing cleanly
- the second pass still stayed inside the same already-approved directory root and did not widen the deletion scope

## Post-Delete State

### Playbook worktree registrations

Post-delete `git -C repos/fawxzzy-playbook worktree list --porcelain` was unchanged:

- active repo root remained `repos/fawxzzy-playbook`
- retained `tmp/*` Playbook worktrees remained intact
- no actual git worktree registration was removed or mutated in this pass

### Stranded directory state

Post-delete `repos/fawxzzy-playbook/.codex/worktrees/` is now empty.

### Branches and stashes

Unchanged and intentionally retained:

- behind-only Playbook branch refs matching the deleted directory family
- Playbook stashes
- all Lifeline retained worktrees and checkpoints

## Validation

Executed after deletion:

- `git -C repos/fawxzzy-playbook worktree list --porcelain`
- root cleanliness check via `git status --short --branch`
- `python .\ops\validation\validate_stack.py`

Result:

- active Playbook worktree registrations unchanged
- root status returned to clean except intentional untracked `archive/`
- `critical=0 error=0 warning=307`

## What Remains Retained

Still retained after this pass:

- Playbook behind-only local smoke branch refs
- Playbook stashes
- Playbook manual-review worktrees and detached checkpoint surfaces
- Lifeline evidence, safety-checkpoint, and manual-review worktrees
- all repo-root active owner-lane surfaces

## Branch And Worktree Normalization Reassessment

`Branch & Worktree Normalization` should remain `99%`, not `100%`.

Reason:

- the filesystem-only stranded directory class is now closed
- but branch/worktree closeout is not fully complete while these classes remain:
  - Playbook behind-only smoke branch refs
  - Playbook stashes
  - Playbook manual-review and detached checkpoint worktrees
  - Lifeline safety/evidence/manual-review worktrees

This pass removes one remaining external-smoke residue class, but it does not fully clear retained branch/worktree pressure stack-wide.

## Marker Recommendation

No marker movement yet.

Recommended unchanged markers:

- `Branch & Worktree Normalization`: `99%`
- `Full Stack Re-sync, Clean & Closeout`: `85%`
- `Inventory & Truth Map`: `74%`
- `Discord OS Infrastructure Separation`: `95%`

## Next Package Recommendation

`Playbook / Lifeline External Worktree / Smoke Surface Closeout Recheck`

Purpose:

- recompute the retained-surface ledger after the Playbook filesystem-only subset is consumed
- decide whether any remaining branch/worktree class is now safe for execution
- determine whether `Branch & Worktree Normalization Final Closeout` can open next or must remain blocked by retained manual-review/safety surfaces

## Outcome

The approved Playbook external `.codex/worktrees/*` stranded-directory subset is now fully consumed.

Current truth:

- Playbook external smoke pressure is reduced from mixed directory plus branch residue to branch-only/stash/manual-review residue
- Lifeline still has no delete-now subset in this lane
- the next correct move is a retained-surface recheck, not an assumption that normalization is automatically at `100%`
