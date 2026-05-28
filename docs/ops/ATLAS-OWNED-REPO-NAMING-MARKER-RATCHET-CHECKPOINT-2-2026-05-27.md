# Atlas-Owned Repo Naming Canonicalization Marker Ratchet Checkpoint 2 - 2026-05-27

- Date: `2026-05-27`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only marker ratchet`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-CANONICALIZATION-2026-05-27.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-EXECUTION-GATE-PASS-1-2026-05-27.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-INVENTORY-DEPENDENCY-MAP-2026-05-27.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-SAFE-FIRST-CANDIDATE-DECISION-2026-05-27.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
- Control-plane checkpoint: `main@c466e0e`

## Objective

Recompute whether `Atlas-owned Repo Naming Canonicalization` can move above `50%` after marker admission, execution-gate pass 1, dependency mapping, and the safe-first candidate decision are all now durable.

This pass does not:

- rename any repo directory
- rename any remote
- rewrite live registry paths by execution
- reopen the `fawxzzy-fitness` exception
- mutate owner-repo content
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `c466e0e`
- status: clean except intentional untracked `archive/`
- validation: green before ratchet drafting at `critical=0 error=0 warning=310`

## What Is Now Durable

The lane now has durable ATLAS-owned surfaces for:

- marker definition and scoring rubric
- explicit internal target set
- explicit `fawxzzy-fitness` preserved exception
- execution-gate doctrine
- candidate-by-candidate dependency map
- explicit safe-first decision that still keeps execution blocked

That is materially stronger than the original `50%` posture, which only admitted policy, scope, and exception handling.

## Marker Decision

Yes, the marker can move.

Move:

- `Atlas-owned Repo Naming Canonicalization`: `50% -> 60%`

## Why `60%` Is The Smallest Honest Move

The lane has moved beyond pure policy.

It now has:

- durable execution-safety gates
- durable dependency clarity across registry, truth-map, and restart surfaces
- durable per-candidate classification
- durable proof that no candidate is execution-ready yet

That is real governance maturity and real execution-safety clarity.

It is not yet `75%` territory because the lane still lacks:

- one exact bounded rename execution package
- one exact rewrite order
- one exact rollback order
- one exact current-state-safe candidate admitted for live execution

So the lane is more mature, but still clearly below rename execution readiness.

## Naming Maturity That Now Exists

What is durably true now:

- the policy target is explicit:
  - internal ATLAS-owned stack repos should shed unnecessary legacy `fawxzzy-` prefixes
- the exception is explicit:
  - `repos/fawxzzy-fitness` stays as-is
- the active dependency footprint is mapped:
  - `stack.yaml`
  - `stack.lock.yaml`
  - repo inventory surfaces
  - restart and system-map surfaces
- candidate classes are separated honestly:
  - `rename-safe candidate later`
  - `blocked by dependency mapping gap`
  - `preserved exception`
- execution remains blocked until a future package proves more than “looks simple”

That is a real ratchet in control-plane clarity.

## What Still Blocks Actual Rename Execution

Execution is still blocked because the lane does not yet have:

- one exact candidate admitted as `safe-first now`
- one exact rewrite sequence
- one exact rollback sequence
- one exact execution-time safety check against current repo branch and dirty posture
- any approval to treat local rename as implied remote rename

Those blockers are still real and should remain visible in the marker reasoning.

## What Still Blocks `75%+` Territory

The lane is still below `75%` because it does not yet have the things the rubric reserves for execution-safe planning:

- one durable rename-safe execution plan
- one bounded candidate package
- one exact no-regression rewrite order across registry and restart surfaces
- one exact rollback posture that can be run intentionally rather than reconstructed after damage

It also still lacks:

- execution-time confirmation that even the lighter later candidates are actually safe in their current repo state when the rename moment arrives

## Why This Is Not Marker Theater

This move is not based on cleaner doctrine alone.

It is based on the fact that the lane now has four distinct durable governance assets that did not exist at the first `50%` admission:

1. execution-gate doctrine
2. dependency-map truth
3. per-candidate classification
4. explicit no-candidate-safe-first decision

That is more than policy volume.

It still stops far short of execution.

## Marker Surface Recommendation

Update the marker surfaces to reflect:

- the lane is no longer only policy-and-inventory complete
- it now has durable execution-safety clarity
- but it still has no admitted rename execution package

## Exact Next Package

`Atlas-owned Repo Naming bounded rewrite-order and rollback planning pass 1`

Why:

- the next missing class is not more naming policy
- the next honest move is one bounded execution-planning surface that freezes:
  - rewrite order
  - rollback order
  - candidate-local preflight checks
- only after that could the lane honestly approach `75%` territory

## Rule

Naming marker movement must reflect durable execution safety and dependency clarity, not just policy volume.

## Pattern

marker admission -> execution gate -> dependency map -> safe-first decision -> marker ratchet -> bounded rewrite and rollback planning -> only then rename execution

## Failure Mode

The marker rises because naming doctrine is cleaner, even though actual rename execution is still blocked.
