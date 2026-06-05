# Duplicate Surface Decommission High-Risk Review

Date: 2026-05-23
Lane: Duplicate Surface Decommission
Mode: Read-only review
Status: Pass 1 complete
Depends on:

- `docs/ops/DUPLICATE-SURFACE-DECOMMISSION-INVENTORY-2026-05-23.md`
- `docs/ops/DUPLICATE-SURFACE-DECOMMISSION-DECISION-PASS-1-2026-05-23.md`

## Purpose

This pass inspects the two highest-risk external duplicate surfaces to determine whether they carry unique source truth, preserved evidence value, stale generated residue, or later-delete potential.

## Review target: `<ATLAS_STANDALONE>/fitness-release-main`

### Live state

- Exists: yes
- Git root: yes
- Remote URL: none configured in `.git/config`
- Branch / HEAD: `main` / `c55728235648a4a45bfe49a48ed1bd7a7086391e`
- Dirty state: dirty (`src/generated/appBuildManifest.json`)
- Ahead/behind: not meaningful against canonical Fitness because this snapshot has no remote and no shared commit lineage with the restored canonical repo
- Approximate footprint: `40,738` files, about `1.10 GB`

### Top-level layout

Present:

- `.next`
- `.playbook`
- `.vercel`
- `docs`
- `node_modules`
- `public`
- `scripts`
- `src`
- `supabase`
- `tests`
- `truth-pack`
- temp dev logs

Compared with canonical `repos/fawxzzy-fitness`, this surface overlaps the app/product layout heavily but lacks several canonical repo governance surfaces such as `.github`, `.husky`, `.codex`, `.githooks`, `assets`, `exports`, and the broader policy files currently present in the canonical repo.

### Unique-state assessment

- Commit graph size: `1` reachable commit
- Commit message: `Release workspace snapshot`
- The single-commit isolated history plus missing remote suggests this is a standalone snapshot, not an active branch in the canonical Fitness lineage
- Dirty state is limited to generated artifact output in `src/generated/appBuildManifest.json`
- Presence of `.next`, `node_modules`, `.vercel`, and temp logs indicates substantial generated/runtime residue rather than a clean governed source checkout

### Overlap with canonical repo

- Purpose overlap: high
- Source overlap: high by structure and product domain
- Canonical-source value: no longer primary; canonical source now lives at `repos/fawxzzy-fitness`
- Duplicate-source risk: high if this surface remains unexplained because it looks like a live alternate Fitness root

### Recommended disposition

- Current classification: manual review
- Recommended next disposition: archive deeper or delete later after a narrow evidence check

### Required verification before later removal

1. Confirm whether the single snapshot commit contains any release-evidence value not already preserved by canonical Fitness, retained `tmp` evidence, or ATLAS recovery docs.
2. Confirm whether `src/generated/appBuildManifest.json` and the generated/runtime surfaces are fully disposable.
3. If no unique retained-evidence value exists, mark the surface as stale duplicate and later-delete candidate.

## Review target: `<ATLAS_WORKTREES>/pr1-stack-lock-refresh`

### Live state

- Exists: yes
- Git root: yes
- Remote URL: `https://github.com/fawxzzy/ATLAS.git`
- Branch / HEAD: `codex/pr1-stack-lock-refresh` / `50b8b459c29309d50863261b9787ca0ccb59b28f`
- Dirty state: clean
- Ahead/behind vs current `main`: `3` commits ahead, `196` commits behind
- Remote branch state: `origin/codex/pr1-stack-lock-refresh` is gone
- Approximate footprint: `363` files, about `3.9 MB`

### Top-level layout

This is a full ATLAS root duplicate shape, including:

- `apps`
- `branding`
- `data`
- `docs`
- `ops`
- `packages`
- `repos`
- `runtime`
- `schemas`
- `secrets`
- `tests`
- `tmp`
- `stack.lock.yaml`
- `stack.yaml`

### Unique-state assessment

- Commit graph size: `101` reachable commits
- Unique branch lead over `main`: `3` commits
- Unique commit chain still outside `main`:
  - `50b8b45` `Refresh stack lock from clean worktree`
  - `bd3791f` `Fix stack lock path normalization`
  - `fda89ab` `Normalize stack lock to durable refs`
- Because the branch is clean and remote-gone, the main risk is not generated residue; it is unmerged or unclassified stack-lock/documentation lineage living in an external worktree container

### Overlap with canonical ATLAS root

- Purpose overlap: full
- Source overlap: full stack root duplicate
- Canonical-source value: not canonical; `.` on `main` is canonical
- Duplicate-source risk: high because it is a near-complete ATLAS root outside the canonical workspace, with unique commits still not proven absorbed

### Recommended disposition

- Current classification: manual review with later-delete potential
- Recommended next disposition: route unique commits into explicit governance first, then delete later if absorbed or intentionally discarded

### Required verification before later removal

1. Compare the three unique commits against current `main` to determine whether they were superseded by later stack lock normalization work.
2. If their intent is already absorbed, record that absorption explicitly and mark the worktree/branch safe delete later.
3. If their intent is not absorbed, either replay the needed changes into canonical `main` or preserve them as explicit historical evidence before removal.

## Review conclusions

1. `fitness-release-main` is not a live branching problem; it is a standalone snapshot/evidence problem.
   Its risk comes from looking like an alternate Fitness root while carrying generated and runtime residue.

2. `pr1-stack-lock-refresh` is the more concrete duplicate-source blocker.
   It carries three unique ATLAS commits outside canonical `main`, so it cannot be deleted on naming alone.

3. Neither target should be removed yet.
   Both need one more focused verification step, but for different reasons:
   `fitness-release-main` needs retained-evidence validation, while `pr1-stack-lock-refresh` needs unique-commit absorption validation.

## Recommended next package

Run a `Duplicate Surface Verification Pass 2` with two separate sub-checks:

- `fitness-release-main`: determine whether the isolated snapshot has any retained evidence value beyond canonical Fitness plus existing `tmp` evidence
- `pr1-stack-lock-refresh`: determine whether the three unique commits are already superseded or must be preserved/replayed before later deletion
