# Stabilize Root Worktree Archive Sensitivity-First Subset Decision Pass 67 - 2026-06-02

- Date: `2026-06-02`
- Lane: `stabilize-root-worktree`
- Mode: `blocker-facing archive sensitivity-first subset decision`
- Source surfaces:
  - `docs/ops/STABILIZE-ROOT-WORKTREE-ARCHIVE-FITNESS-SOURCE-RESET-MANIFEST-ONLY-INVENTORY-AND-SENSITIVITY-SPLIT-PASS-66-2026-06-02.md`
  - direct inventory of `archive/fitness-source-reset/20260522-final-cleanup`
  - root `AGENTS.md` escalation rules

## Objective

Choose the exact next archive subfamily that should be handled first now that `archive/fitness-source-reset` has a durable manifest-only split.

## Exact Sensitivity-First Subset

Secret-like or config-like files:

- `archive/fitness-source-reset/20260522-final-cleanup/fawxzzy-fitness-real/.env.local`
- `archive/fitness-source-reset/20260522-final-cleanup/fitness-feedback-completion-review-workflow/.env.local`

Tool-state residue:

- `archive/fitness-source-reset/20260522-final-cleanup/fawxzzy-fitness-real/.playbook/last-run.json`
- `archive/fitness-source-reset/20260522-final-cleanup/fitness-feedback-completion-review-workflow/.playbook/last-run.json`
- `archive/fitness-source-reset/20260522-final-cleanup/fitness-pr61-merge/.playbook/last-run.json`

Exact count:

- `.env.local`: `2`
- `.playbook/last-run.json`: `3`

## Decision

- immediate blocker-facing subfamily: the five-file sensitivity-first subset above
- later adjacent hold:
  - broader snapshot-root evidence
  - generated `.next` residue
  - archived `node_modules`
  - broader `.playbook/runtime/*` residue

## Why This One First

1. the archived `.env.local` files create the sharpest secrets-handling and retention ambiguity in the remaining dirty-root carry
2. the adjacent `last-run.json` files are small tool-state residue and are materially easier to reason about than the much larger generated archive subtrees
3. handling sensitivity first reduces the risk of accidental blanket preservation or staging of the broader archive corpus

## Escalation Boundary

The root `AGENTS.md` rules now matter directly:

- ask before changing secrets handling
- ask before changing retention policy for backups and installers

Because this subset includes archived `.env.local`, the next honest move is no longer autonomous Codex mutation.

## Exact Non-Claim Boundary

- this pass does not preserve the five-file subset
- this pass does not stage the five-file subset
- this pass does not delete, move, quarantine, or sanitize the five-file subset
- this pass does not reopen any broader archive subfamily
- this pass does not grant any marker movement

## Exact Next Move

- operator approval or policy decision over the five-file sensitivity-first subset
- decide whether the archived `.env.local` files should remain retained as-is, move to a secrets/quarantine posture, or be explicitly deleted under an approved retention rule
- only after that decision should any Codex mutation lane reopen for this archive family

## Rule

Approval Before Sensitive Archive Mutation.

## Pattern

Sensitive Subset First.

## Failure Mode

Archive Sensitivity Drift Through Bulk Handling.

## Marker Decision

- `none`
