# Repo Gitdir Hygiene

This runbook covers local git metadata hygiene for relocated or renamed ATLAS child repos.

## Scope

Tracked source does not include `.git/` internals. Gitdir pointers, linked-worktree admin entries, and local repo config are machine-local state.

Tracked:

- `ops/stack/audit_gitdir_hygiene.py`
- this runbook
- optional non-blocking validator warnings

Local-only:

- `.git/`
- `.git/worktrees/*`
- local git config
- linked worktree checkout paths

## Failure Mode

Relocating ATLAS from one root to another can leave linked-worktree metadata pointing at stale machine-local checkout paths from the previous location. That can break:

- `git status`
- `git worktree list`
- lockfile generation
- worker tooling that shells out to git

## Audit

Run:

```powershell
python ops/stack/audit_gitdir_hygiene.py
```

The audit checks the current `_stack` and Lifeline repos by default and reports:

- prunable linked-worktree entries
- stale `worktrees/*/gitdir` pointers
- stale absolute `worktree = ...` config values when present
- stale nested `.codex/worktrees/*/.git` pointers left behind by relocated local worktree checkouts
- basic git command health for `status`, `rev-parse --show-toplevel`, and `rev-parse --git-dir`

## Repair

Use the safe prune path first:

```powershell
python ops/stack/audit_gitdir_hygiene.py --apply
```

That runs `git worktree prune --expire now` only for repos with stale linked-worktree metadata, renames any stale nested `.codex/worktrees/*/.git` files to `.git.stale`, and then re-audits the result.

## Verification

After repair, confirm for each affected repo:

```powershell
git -C repos/_stack status --short
git -C repos/_stack rev-parse --show-toplevel
git -C repos/_stack rev-parse --git-dir
git -C repos/_stack worktree list

git -C repos/lifeline status --short
git -C repos/lifeline rev-parse --show-toplevel
git -C repos/lifeline rev-parse --git-dir
git -C repos/lifeline worktree list
```

## Move / Rename Rule

When the stack root moves:

1. move the working tree
2. audit gitdir hygiene
3. prune stale linked worktrees
4. rerun stack validation and lockfile generation

Do not commit `.git/` repairs or `.git.stale` files. They are local machine maintenance, not versioned source.
