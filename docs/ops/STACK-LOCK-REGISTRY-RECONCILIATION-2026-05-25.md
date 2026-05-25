# Stack Lock And Registry Reconciliation

- Date: `2026-05-25`
- Lane: `Stack Lock And Registry Reconciliation Pass`
- Mode: `stack truth repair only`

## Scope

Resolve the stack truth blockers recorded in:

- `docs/ops/FULL-STACK-RESYNC-CLEAN-CLOSEOUT-RESUME-2026-05-25.md`
- `docs/ops/FULL-STACK-RESYNC-CLEAN-CLOSEOUT-BASELINE-PASS-2-2026-05-25.md`

This pass repaired stack/registry surfaces only. It did not touch `archive/`, `tmp/`, Supabase, Vercel, Discord runtime behavior, or app runtime code.

## Root State

- Root branch before pass: `main`
- Root HEAD before pass: `624107e339f3fde3c889a2cbb8c31b3f0bc21587`
- `origin/main` before pass: `624107e339f3fde3c889a2cbb8c31b3f0bc21587`
- Root working tree before pass: tracked stack truth surfaces only; retained untracked `archive/` residue remained untouched
- Root HEAD after pass, before receipt commit: `624107e339f3fde3c889a2cbb8c31b3f0bc21587`

## Problem

The current stack truth had two stack-owned blockers:

1. `stack.lock.yaml` pinned stale root `stack` truth.
2. `repos/fawxzzy-foundation` was declared active in `stack.yaml` but missing locally.

That meant validation only stayed green with `--allow-missing-locked-repos`, masking the missing-checkout class instead of resolving it.

## Foundation Restoration Result

Canonical Foundation identity was clear from existing stack metadata and the remote:

- Expected local path: `repos/fawxzzy-foundation`
- Remote: `https://github.com/fawxzzy/fawxzzy-foundation.git`
- Remote `main` / `HEAD`: `a016da2f08f167747f7ae7c804c0d6840cb9514d`

Restoration action:

```powershell
git clone https://github.com/fawxzzy/fawxzzy-foundation.git repos/fawxzzy-foundation
```

Verification:

- Restored branch: `main`
- Restored HEAD: `a016da2f08f167747f7ae7c804c0d6840cb9514d`
- Restored remote: `https://github.com/fawxzzy/fawxzzy-foundation.git`
- Restored status: clean

## Stack Truth Repair

### Manifest correction

`foundation` was active in `stack.yaml` but was not included in `stack_lock.include_repo_ids`.

Repair:

- added `foundation` to `stack.yaml` `stack_lock.include_repo_ids`

### Lock regeneration command

```powershell
python .\ops\stack\generate_lockfile.py
```

Result:

- regenerated `stack.lock.yaml`
- updated root `stack` lock entry to current root commit state
- added current `foundation` lock entry
- lock digest: `sha256:7a8f547d946a8df80ad13aab69489c6785d27c2bc7491e99cbf22083debe8054`

### Registry regeneration command

```powershell
python .\ops\stack\export_repo_inventory.py
```

Result:

- regenerated `docs/registry/STACK-REPO-INVENTORY.json`
- regenerated `docs/audits/STACK-REPO-INVENTORY.md`
- current repo count: `12`
- current dirty repo count: `5`
- inventory digest: `sha256:4be914534d7010751dc72768c46601037bdff0fd8d14d17c099f851f3575d1df`

### Stack-owned package surface repair

Normal validation after Foundation restoration exposed missing required package directories from `subpaths.packages.*`.

Repairs:

- created durable directories:
  - `packages/bundles/`
  - `packages/patches/`
  - `packages/prebuilt/`
  - `packages/releases/`
  - `packages/snapshots/`
- added `.gitkeep` markers in each directory
- updated root `.gitignore` to allow those governed package paths to be versioned instead of ignored

## Files Changed

- `.gitignore`
- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `packages/bundles/.gitkeep`
- `packages/patches/.gitkeep`
- `packages/prebuilt/.gitkeep`
- `packages/releases/.gitkeep`
- `packages/snapshots/.gitkeep`

## Validation

### Before Foundation restoration

Normal validation was blocked by:

- missing `repos/fawxzzy-foundation`
- stale lock/registry truth

### After Foundation restoration and lock regeneration

```powershell
python .\ops\validation\validate_stack.py
```

Result:

- `critical=0`
- `error=1`
- `warning=307`

Remaining normal-validation blocker:

- `repos/fawxzzy-lifeline`: expected `.codex/config.toml` is missing for an active repo

### Allow-missing validation

```powershell
python .\ops\validation\validate_stack.py --allow-missing-locked-repos
```

Result:

- `critical=0`
- `error=0`
- `warning=307`

## Allow-Missing Status

`--allow-missing-locked-repos` is no longer needed for the missing-active-repo class.

Foundation is restored and stack lock truth now includes it correctly.

Normal validation still fails, but for a different reason:

- preexisting Lifeline repo-local `.codex/config.toml` absence

That blocker belongs to the next repo/worktree normalization package, not this stack truth repair pass.

## Remaining Blockers

1. `repos/fawxzzy-lifeline` is missing `.codex/config.toml` for an active repo.
2. Historical warning residue remains across active repos, worktree metadata, mutable generated state, and path-discipline debt.
3. `archive/` remains intentionally retained and untouched.

## Next Package

`Branch And Worktree Normalization Closeout Pass 2`

Why:

- it owns the remaining Lifeline `.codex/config.toml` blocker
- it is the next clean step in the full-stack closeout ladder
- stack lock and registry truth are now repaired enough to hand off safely

## Outcome

- Foundation active/missing mismatch: resolved
- root stack lock truth: refreshed
- stack registry/inventory truth: refreshed
- governed package directory contract: restored
- fake green lock posture: removed
- remaining blocker: narrowed to repo-local Lifeline residue
