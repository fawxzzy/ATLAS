# Atlas-Owned Repo Naming Safe-First Candidate Decision - 2026-05-27

- Date: `2026-05-27`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only execution-readiness decision`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 50%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-CANONICALIZATION-2026-05-27.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-EXECUTION-GATE-PASS-1-2026-05-27.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-INVENTORY-DEPENDENCY-MAP-2026-05-27.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `stack.yaml`
  - `stack.lock.yaml`
- Control-plane checkpoint: `main@ca425ca`

## Objective

Decide whether the newly mapped naming dependencies admit any exact safe-first local rename candidate while keeping execution blocked unless the evidence truly supports it.

This pass does not:

- rename any repo directory
- rename any remote
- assume GitHub-side rename execution
- reopen the `fawxzzy-fitness` exception
- mutate owner-repo content

## Root State

- branch: `main`
- HEAD: `ca425ca`
- status: clean except intentional untracked `archive/`
- validation: green before decision drafting at `critical=0 error=0 warning=310`

## What Is Now Durable

The lane now has all of the following as durable ATLAS surfaces:

- marker definition and exception posture
- execution-gate doctrine
- candidate-by-candidate dependency map

That is enough to decide whether any exact candidate is admitted as `safe-first` now.

## Decision

No exact safe-first rename candidate is admitted yet.

Execution remains fully blocked.

## Why Execution Still Stays Blocked

The dependency map improved classification, but it did not satisfy the full safe-first bar frozen in the execution gate.

A candidate counts as truly safe-first only when all of the following are proven together:

- dependency-map footprint is durable and small
- current-truth registry rewrite scope is explicit
- restart-surface rewrite scope is explicit
- local rename safety is proven in current repo state
- rollback is explicit
- no remote rename assumption is required

What the lane has now:

- small-vs-large candidate differences are durably mapped
- some candidates look tractable later
- the `fawxzzy-fitness` exception remains explicit

What the lane still lacks:

- exact bounded rewrite sequence
- exact rollback sequence
- exact candidate package with preflight checks
- explicit confirmation that current repo-local branch and dirty posture are safe for execution at rename time

That keeps the lane below execution readiness.

## Candidate-Class Decision

### No Candidate Is Safe-First Now

Current honest result:

- none

Reason:

- the map admits some `rename-safe candidate later` classes
- it does not yet convert any one candidate into a fully execution-ready package

## What Looks Tractable Later But Is Not Admitted Now

These currently look like the smallest later candidates once a real execution package exists:

- `repos/fawxzzy-foundation -> repos/foundation`
- `repos/fawxzzy-stream -> repos/stream`
- `repos/fawxzzy-mazer -> repos/mazer`
- `repos/fawxzzy-trove -> repos/trove`

Why they are not admitted now:

- no exact rollback sequence is durable yet
- no exact registry and restart rewrite order is frozen yet
- `mazer` and `trove` still carry non-`main` branch posture in `stack.lock.yaml`
- all candidates still require controlled updates to:
  - `stack.yaml`
  - `stack.lock.yaml`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`

So these are still `rename-safe candidate later`, not `safe-first now`.

## What Remains Blocked

Blocked candidates remain:

- `repos/fawxzzy-lifeline -> repos/lifeline`
- `repos/fawxzzy-playbook -> repos/playbook`

Why:

- both have dirty live repo state in current lock/inventory posture
- both have active non-`main` branch posture
- they still inherit the same registry/restart rewrite and rollback gaps as the lighter candidates

These are not forbidden forever.

They are just farther from safe-first than the lighter candidates.

## Preserved Exception

Preserved exception remains:

- `repos/fawxzzy-fitness`

Why:

- explicit exception is already durable
- current stack, runtime, and external pilot identity still rely on that name
- this pass does not weaken or reopen that exception

## Exact Remaining Execution Blockers

The blockers preventing any exact safe-first admission are:

1. no exact rename package sequence is durable yet
2. no exact rollback package is durable yet
3. restart-surface update order is still mapped only at family level, not package level
4. registry rewrite scope is known, but not yet frozen into one bounded apply order
5. current candidate-local branch and dirty posture still need execution-time recheck

## What This Pass Does Not Approve

This pass does not approve:

- any local repo rename
- any remote rename
- any GitHub-side rename
- any “easy one first” execution by implication

Execution stays blocked until a future lane freezes an exact bounded rename package with:

- one candidate
- one rewrite order
- one rollback order
- one current-state safety check

## Marker Interpretation

This pass improves execution honesty.

It does not justify a marker move by itself.

Why:

- it prevents a false-positive safe-first claim
- it does not open execution
- it does not land rollback or bounded sequencing

## Exact Next Package

`Atlas-owned Repo Naming Canonicalization marker ratchet checkpoint 2`

Why:

- the lane now has policy, execution gates, dependency mapping, and a durable no-candidate-safe-first decision
- the next honest move is to recompute whether that governance maturity justifies a small marker move without implying live rename approval

## Rule

Safe-first candidate work must prove exact rename safety before it ever becomes execution-ready.

## Failure Mode

A decision pass quietly becomes rename approval because one candidate “looks simple.”
