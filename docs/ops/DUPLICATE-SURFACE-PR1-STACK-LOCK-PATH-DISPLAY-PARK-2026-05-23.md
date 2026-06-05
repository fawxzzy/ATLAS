# Duplicate Surface PR1 Stack Lock Path Display Park

Date: 2026-05-23
Lane: Duplicate Surface Decommission
Mode: Rewrite evaluation
Status: Parked
Source idea: `bd3791f` from `codex/pr1-stack-lock-refresh`

## Purpose

This note records the decision not to extract a fresh ATLAS-root rewrite from the path-display portion of `bd3791f` at this time.

## What was evaluated

The potentially useful idea in `bd3791f` was narrower than the full branch patch:

- improve how sibling ATLAS-adjacent paths like `<ATLAS_WORKTREES>/...` or `<ATLAS_STANDALONE>/...` display in diagnostics
- avoid replaying the broader observation, lock-generation, and validation semantics bundled into the original commit

## Current-main check

- `main` validates green without the branch patch
- current lockfile doctrine still intentionally describes generation from the current managed git working set
- `ops/_atlas.py` still uses a simple `atlas_relative()` model that returns root-relative paths when possible and absolute paths otherwise
- current validation output confirms the dominant issue is existing absolute-path debt already present in committed docs and receipts, not a newly blocking runtime path-resolution failure

## Why this is parked

1. The current pain is debt cleanup, not a proven missing runtime feature.
   The stack validation warning budget shows a large inherited `path-discipline-leaks` class already living in committed docs.

2. Replaying the branch idea would risk over-solving the wrong problem.
   The original commit mixed path-display changes with broader semantics changes, and a fresh rewrite would still need a clear failing case to justify touching shared root helpers.

3. The value is real but not urgent.
   Shorter sibling-surface display refs may still be worth a later targeted UX cleanup, but that belongs in a dedicated path-discipline or diagnostics lane, not as a follow-on from a stale external worktree.

## Decision

- Classification: `parked`
- Rewrite status: `do not implement now`
- Source branch impact: `bd3791f` remains historical evidence only unless a future dedicated path-discipline lane reopens the idea from current main

## Reopen conditions

Revisit this only if one of the following becomes true:

- a current `main` operator workflow is materially degraded by absolute sibling-surface paths in diagnostics
- a dedicated path-discipline cleanup lane decides to normalize committed absolute-path debt and wants a narrowly tested helper improvement
- a future root tooling patch can demonstrate a small, isolated benefit without changing lock truth doctrine or observation semantics

## Effect on `pr1-stack-lock-refresh`

Because the only potentially useful idea is now explicitly parked, `codex/pr1-stack-lock-refresh` no longer represents an implementation lane. It can move toward retained historical evidence and later disposal once this park decision is preserved.
