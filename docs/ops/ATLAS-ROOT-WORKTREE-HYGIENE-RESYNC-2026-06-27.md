# ATLAS Root Worktree Hygiene Re-sync

Date: 2026-06-27
Mode: Root-bounded hygiene and validation receipt
Status: landed

## Purpose

Record the root-owned cleanup that converts the live untracked-root backlog from ambient drift into explicit local-only classes that match the ATLAS path contract.

## What Changed

1. Stack validation was re-run from the ATLAS root and returned:
   - `critical=0`
   - `error=0`
   - `warning=0`
   - `info=0`
2. Loose Fitness proof captures were removed from the repository root and relocated to:
   - `tmp/captures/fitness-ui-proof-2026-06-27/`
3. Root `.gitignore` was updated so two local-only residue classes stop appearing as false-positive root backlog:
   - `.playwright-mcp/**`
   - `archive/**`

## Why These Classes Are Ignored

### `.playwright-mcp/**`

This directory is tool-generated browser automation residue:

- console logs
- page dumps
- ephemeral local diagnostics

It is local runtime residue, not stack source truth. Ignoring it aligns the worktree with the existing rule that disposable captures and logs belong outside committed source surfaces.

### `archive/**`

`archive/fitness-source-reset` is already documented as retained evidence rather than live repo truth in:

- `docs/recovery/ARCHIVE_RETENTION_RECEIPT_2026-05-22.md`
- `docs/ops/DUPLICATE-SURFACE-RETENTION-GOVERNANCE-2026-05-23.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`

This pass does not move, rewrite, compress, or delete that retained evidence. It only stops the local archive mass from presenting as normal root source drift.

## Path-Policy Reconciliation

This pass keeps the ATLAS root closer to the declared contract:

- disposable screenshots and proof captures live under `tmp/`
- tool-generated local residue is not treated as repo truth
- retained archive evidence stays preserved without being mistaken for active source

## Verification

Commands run:

- `python ops/validation/validate_stack.py`
- `git status --short`

Observed outcome:

- stack validation stayed fully green
- the repository root no longer carries loose screenshot and snapshot files
- remaining local-only residue is classified through `.gitignore` instead of polluting active root status

## Non-Goals

This pass did not:

- delete or mutate retained archive evidence
- change `stack.yaml` topology
- reopen the already-closed Full Stack Re-sync, Clean & Closeout lane
- change any owner-repo source truth
