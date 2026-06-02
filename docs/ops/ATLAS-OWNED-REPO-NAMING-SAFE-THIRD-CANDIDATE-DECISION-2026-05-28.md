# Atlas-Owned Repo Naming Safe-Third Candidate Decision - 2026-05-28

- Date: `2026-05-28`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only candidate decision`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 75%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-BLOCKED-STATE-FAMILY-RECHECK-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-BOUNDED-REWRITE-ROLLBACK-PLAN-2026-05-28.md`
  - `docs/atlas-book/05-receipt-index.md`
- Control-plane checkpoint: `main@9bb230c`

## Objective

Freeze one exact safe-third rename candidate from the remaining family, or freeze an explicit none-ready result.

This pass does not:

- rename any repo directory
- rename any remote
- assume any GitHub-side rename
- reopen the `fawxzzy-fitness` exception
- mutate owner-repo content
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `9bb230c`
- status before drafting: existing ATLAS docs-only changes in `AGENTS.md`, atlas-book surfaces, naming receipts, `PROCESS-AMPLIFICATION-PASS-2-2026-05-28.md`, and intentional untracked `archive/`
- validation before drafting: `critical=0 error=0 warning=311`

## Safe-Third Verification

The blocked-state family recheck already froze the remaining family as:

- `trove`: blocked by branch / non-`main` posture and retained-surface / manual-review pressure
- `mazer`: blocked by branch / non-`main` posture, retained-surface / manual-review pressure, and active initiative entanglement
- `lifeline`: blocked by dirty owner-lane state and non-`main` branch posture
- `playbook`: blocked by dirty owner-lane state and non-`main` branch posture
- `fawxzzy-fitness`: preserved / not admissible

That means no remaining repo currently satisfies the bounded rename preflight class already proven by `stream` and `foundation`.

## Decision

Exact safe-third candidate:

- `none ready`

Why this is the honest decision:

- no remaining repo is both `main`-aligned and free of active local-state or retained-surface pressure
- no remaining repo changed class since the family-wide blocked-state recheck
- reopening per-repo exploration would recreate the exact loop this family decision was meant to stop

## What This Decision Freezes

This pass freezes:

- no exact safe-third candidate is execution-ready yet
- no new root-side naming approval or execution packet should open for the remaining family until owner-side blocker class changes

## What This Decision Does Not Freeze

This pass does not:

- pick a provisional or "maybe" candidate
- widen into `trove`, `mazer`, `lifeline`, or `playbook` separately
- approve any rename execution
- approve any remote rename
- approve any GitHub-side rename

## Marker Read

No numeric marker move is justified from this pass alone.

Hold:

- `Atlas-owned Repo Naming Canonicalization`: `75% -> 75%`

Why:

- this decision clarifies candidate readiness and closes loop pressure
- but no new executed-and-reconciled packet landed and no blocker class cleared

## Exact Next Package

No new root naming package is open.

Next honest move:

- owner-side blocker conversion in one of `trove`, `mazer`, `lifeline`, or `playbook`
- then one exact family or candidate blocker-class recheck only after owner-side reality changes

## Rule

Candidate decision must pick one exact repo or none, not reopen exploration.

## Failure Mode

A decision pass names several "maybe" candidates and recreates the loop.
