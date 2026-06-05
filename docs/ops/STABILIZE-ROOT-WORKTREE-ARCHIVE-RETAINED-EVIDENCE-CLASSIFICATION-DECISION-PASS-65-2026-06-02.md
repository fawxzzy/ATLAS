# Stabilize Root Worktree Archive Retained-Evidence Classification Decision Pass 65 - 2026-06-02

- Date: `2026-06-02`
- Lane: `stabilize-root-worktree`
- Mode: `blocker-facing archive retained-evidence classification`
- Source surfaces:
  - `git status --short`
  - `git ls-files --others --exclude-standard archive`
  - direct inventory of `archive/fitness-source-reset`
  - `docs/ops/STABILIZE-ROOT-WORKTREE-INVENTORY-AND-OWNERSHIP-SPLIT-PASS-2-2026-06-01.md`
  - `docs/ops/STABILIZE-ROOT-WORKTREE-PRESERVE-DISPOSITION-DECISION-PASS-3-2026-06-01.md`

## Objective

Classify the last live dirty-root carry in `archive/*` without pretending it is ready for blanket preservation, cleanup, deletion, or staging.

## Current Archive Truth

- the only remaining dirty-root carry is `archive/*`
- the entire live archive carry currently sits under one top-level family:
  - `archive/fitness-source-reset`
- that family currently includes at least:
  - timestamped snapshot roots
  - generated `.next` outputs
  - `node_modules`
  - `.playbook` runtime state
  - archived `.env.local`
  - retained static asset files

## Decision

- immediate blocker-facing carry: `archive/fitness-source-reset` retained-evidence family
- posture: retained evidence, high-risk mixed-content hold
- do not preserve this family wholesale
- do not stage this family wholesale
- do not delete or clean this family wholesale

## Why This Classification Is Honest

1. this family is no longer adjacent control-plane truth like the cleared `docs/ops/*` backlog; it is retained evidence with mixed safety classes
2. the presence of generated build outputs, runtime residue, and archived `.env.local` means blanket preservation would over-claim safety
3. the same mixed-content posture also blocks blanket cleanup or deletion without a stronger retention-class decision
4. the remaining blocker is no longer "what do we preserve next" but "what retention class and sensitivity split does this evidence family require"

## Exact Non-Claim Boundary

- this pass does not preserve any `archive/*` subset
- this pass does not stage any `archive/*` subset
- this pass does not approve deletion, movement, or quarantine mutation
- this pass does not reopen any `docs/ops/*`, Cortex, bridge, or owner-repo lane
- this pass does not grant any marker movement

## Exact Next Move

- open one bounded archive manifest-only inventory or sensitivity-split packet for `archive/fitness-source-reset` only
- classify at least:
  - snapshot roots
  - generated build outputs
  - runtime residue
  - secret-like or config-like files
- keep the archive family untouched until that split exists durably

## Rule

Retained Evidence Is Not Preservation-Ready.

## Pattern

Mixed-Content Archive Hold.

## Failure Mode

Archive Bulk-Preserve Theater.

## Marker Decision

- `none`
