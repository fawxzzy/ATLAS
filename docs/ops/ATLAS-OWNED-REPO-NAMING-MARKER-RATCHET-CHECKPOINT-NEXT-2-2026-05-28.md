# Atlas-Owned Repo Naming Marker Ratchet Checkpoint Next 2 - 2026-05-28

- Date: `2026-05-28`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only marker ratchet`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-MARKER-RATCHET-CHECKPOINT-NEXT-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-TROVE-SAFE-THIRD-EXECUTION-APPROVAL-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-TROVE-LOCAL-RENAME-EXECUTION-PASS-1-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-TROVE-RENAME-PROOF-RECONCILIATION-PASS-1-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-BOUNDED-REWRITE-ROLLBACK-PLAN-2026-05-28.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
- Control-plane checkpoint: `main@9bb230c`

## Objective

Recompute whether `Atlas-owned Repo Naming Canonicalization` can move above `75%` after a third exact local rename has executed and been durably proven.

This pass does not:

- rename any repo directory
- rename any remote
- execute any registry path rewrite
- reopen the `fawxzzy-fitness` exception
- mutate owner-repo content
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `9bb230c`
- status: existing ATLAS docs-only changes in `AGENTS.md`, atlas-book surfaces, prior naming receipts, refreshed `stack.lock.yaml`, refreshed inventory surfaces, and intentional untracked `archive/`
- validation: green before ratchet drafting at `critical=0 error=0 warning=366`

## What Is Now Durable

The lane now has durable ATLAS-owned surfaces for:

- naming policy and scoring rubric
- explicit internal target set
- explicit `fawxzzy-fitness` preserved exception
- execution-gate doctrine
- candidate-by-candidate dependency map
- safe-first, safe-second, and safe-third selection work
- exact bounded rewrite order
- exact bounded rollback order
- three exact local rename execution receipts
- three exact positive proof and reconciliation receipts

## What Newly Landed Since Checkpoint Next

Checkpoint Next moved the lane to `75%` because two distinct bounded candidates had executed and reconciled cleanly.

That missing third-packet maturity class has now landed.

The current durable proof chain now says:

- `repos/fawxzzy-stream` no longer represents the active local path and `repos/stream` is canonical
- `repos/fawxzzy-foundation` no longer represents the active local path and `repos/foundation` is canonical
- `repos/fawxzzy-trove` no longer represents the active local path and `repos/trove` is canonical
- `stack.yaml` and `stack.lock.yaml` are reconciled for all three executed packets
- `docs/registry/STACK-REPO-INVENTORY.json` and `docs/audits/STACK-REPO-INVENTORY.md` are reconciled for all three executed packets
- no remote-name assumption was introduced in any packet

That means:

- three exact local rename executions are durable
- three exact rename proofs of success are durable
- three exact reconciliations to new canonical local paths are durable

## Marker Decision

Yes, the marker can move.

Move:

- `Atlas-owned Repo Naming Canonicalization`: `75% -> 76%`

## Why The Marker Moves

Checkpoint Next explicitly held the lane at `75%` because only two bounded candidates had executed and reconciled.

What changed since then is operator reality, not cleaner doctrine:

- the third distinct bounded candidate actually executed
- the canonical local path actually changed for `trove`
- current-truth control-plane surfaces actually reconciled to the new `trove` path
- the proof chain now includes three exact executed-and-reconciled packets rather than two

That is enough to cross the next evidence threshold by the smallest honest amount.

## Why The Marker Only Moves By One Point

This is the smallest honest move above `75%`.

Why it stops at `76%`:

- the lane now proves the bounded local-only rename shape across three distinct candidates
- but later-candidate reuse is still not broad enough to justify a larger move
- `mazer`, `lifeline`, and `playbook` remain blocked by exact owner-side lane classes
- remote-name and GitHub-side rename assumptions remain explicitly blocked

So the lane is stronger than checkpoint Next, but still not broad enough for a larger ratchet.

## Maturity That Now Exists

What is now durably true:

- the lane has three exact executed-and-reconciled local packets
- the local-only rename shape is now proven across multiple application and package surfaces
- the control-plane rewrite and reconciliation packet is reusable in practice beyond the first two exemplars
- remote-name and GitHub-side rename drift are still tightly excluded

## What Still Blocks Later Candidates

Still blocked after this pass:

- `mazer` because the active owner-side multi-worktree lane still blocks bounded rename execution
- `lifeline` because the active owner-side release lane closeout still blocks bounded rename execution
- `playbook` because the active owner-side release-governance multi-worktree lane still blocks bounded rename execution
- `fawxzzy-fitness` preserved exception

Still prohibited:

- remote rename assumptions
- GitHub-side rename assumptions
- multi-repo rename widening

## Exact Next Package

No additional root naming packet is currently open.

Next honest move:

- owner-side blocker conversion in `mazer`, `lifeline`, or `playbook`
- then one exact family or candidate blocker-class recheck only after owner-side reality changes

## Rule

Naming marker movement must reflect actual executed and reconciled canonicalization, not just readiness.

## Failure Mode

The marker rises because a third candidate was approved, even though executed canonicalization did not land cleanly.
