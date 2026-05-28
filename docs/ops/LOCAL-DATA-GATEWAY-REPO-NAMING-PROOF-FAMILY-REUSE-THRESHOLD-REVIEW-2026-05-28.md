# Local Data Gateway Repo Naming Proof-Family Reuse Threshold Review - 2026-05-28

- Date: `2026-05-28`
- Owner: ATLAS root
- Mode: `docs-only proof-family threshold review`
- Scope: `repo naming proof-family reuse threshold inside Local Data Gateway`
- Source surfaces:
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-PROOF-FAMILY-REAL-WORKFLOW-DECISION-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-BOUNDED-PROOF-SHAPE-REVIEW-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-RENAME-MANIFEST-PROOF-ADMISSION-DECISION-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-MARKER-RATCHET-CHECKPOINT-10-2026-05-28.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/atlas-book/14-lane-split-execution.md`
- Control-plane checkpoint: `main@f80ea31`

## Objective

Decide whether the already-durable repo naming `real-workflow proof-admitted later` class is now strong enough to define a reuse threshold inside the Local Data Gateway lane without promoting repo naming workflows to `adoptable now`.

This pass does not:

- modify `_stack`
- imply send-capable behavior
- authorize repo rename execution
- authorize remote or GitHub-side rename assumptions
- graduate repo naming into `adoptable now`
- move the Local Data Gateway marker
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `f80ea31`
- status: clean except intentional untracked `archive/`
- validation: green before drafting at `critical=0 error=0 warning=311`

## Current Repo-Naming Posture Recomputed

The repo-naming family now stands at:

- `proof-admitted later`
- `real-workflow proof-admitted later`
- `contract-complete but execution-blocked`

That means:

- the contract exists
- the bounded proof shape exists
- one exact real workflow path now exists
- reuse across multiple rename workflows is still not yet proven

## Current Evidence Count

Current durable family evidence count:

- exact real workflow instances: `1`
- exact reusable family instances: `0`

The single durable instance is the `stream` packet family path.

That instance is valuable because it proves:

- one real candidate can produce durable local receipts
- blocked-before-rename is a valid proof outcome
- the family can preserve honest local truth without overclaiming execution

That instance is not enough by itself to prove family reuse.

## What Counts As One Proven Instance

One proven instance for this family must include all of the following for one exact rename candidate:

1. one durable rename-manifest packet or equivalent contract-complete candidate packet
2. one exact execution receipt with an honest outcome class:
   - `blocked-before-rename`
   - or `executed-and-reconciled`
3. one exact proof / reconciliation receipt tied to the same candidate
4. one no-send attestation that keeps all remote-facing fields explicitly `false`
5. one green validation reference at the relevant control-plane closeout point

If any one of those is missing, the candidate does not count as one proven instance.

## What Counts As Reusable Proof Shape

Reusable proof shape for this family is not just a strong first example.

It requires at minimum:

1. two distinct bounded rename candidates
2. both candidates using the same minimum manifest fields and proof-output contract without adding new mandatory family fields
3. both candidates producing durable local receipts that remain useful under the same no-send boundary
4. no candidate requiring hidden gateway-specific rename logic to make the packet legible

If the second candidate requires new mandatory contract shape, the family is not yet reusable.

If the second candidate only works by adding candidate-specific hidden logic, the family is not yet reusable.

## What Still Requires Per-Workflow Proof

Even after reuse threshold is frozen, the following still require per-workflow proof:

- exact candidate identity
- exact rewrite-surface inventory
- exact rollback order
- exact blocker class if blocked
- exact stale-reference reconciliation scope
- exact no-op or rewrite outcome
- exact validation result

Those are candidate-specific truths.

They cannot be inherited from a previous candidate just because the family shape is reusable.

## Current Reuse Decision

No.

The family is not yet above the reuse threshold.

Current honest read:

- one proven instance exists
- one real workflow family path exists
- no second distinct candidate instance exists yet
- reusable proof shape is therefore not yet demonstrated in practice

So the family remains:

- `real-workflow proof-admitted later`

It does not yet become:

- reusable proof-family admitted
- operationally reusable
- `adoptable now`

## Why The Threshold Is Not Yet Met

The missing evidence is not more contract writing.

The missing evidence is a second bounded candidate instance.

Specifically still missing:

- one second rename candidate that uses the same proof shape without shape expansion
- proof that the family remains legible under a different candidate packet
- proof that the current no-send chain can carry more than one bounded candidate without rename-specific creep

Until that exists, the family is still a strong single-instance middle class, not a reusable family.

## What Would Meet The Reuse Threshold

The smallest honest threshold-crossing evidence would be:

1. one second bounded repo-naming candidate
2. the same manifest and proof-output contract used without adding new mandatory fields
3. a durable execution receipt for that second candidate
4. a durable proof / reconciliation receipt for that second candidate
5. no-send attestation still fully preserved

The second candidate may still be:

- blocked-before-rename
or
- executed-and-reconciled

The threshold is about reusable family shape, not successful rename outcome alone.

## What Would Justify Graduation Beyond `real-workflow proof-admitted later`

Graduation beyond the current middle class would require more than simple threshold-crossing.

At minimum it would need:

1. the reuse threshold above to be met across at least two distinct candidates
2. at least one candidate showing `executed-and-reconciled` truth, not only blocked truth
3. proof that reuse does not require gateway-specific rename logic
4. evidence that operator value is now broader than one exact candidate family path

Only after that should the lane reconsider whether repo naming can move beyond narrow proof-family maturity.

That still would not automatically mean `adoptable now`.

## Relation To The Current `stream` Packet

The `stream` packet remains the anchor instance.

Current read:

- it is the first proven instance
- it is still blocked by `2c`
- it proves the family can carry real blocked truth
- it does not prove family reuse on its own

So the correct next question is not another root-side rename retry.

The correct next question is whether a second bounded candidate ever lands without changing the proof shape.

## What This Pass Proves

This pass proves:

- the family now has an explicit reuse threshold
- one strong first example is not enough for family reuse
- candidate-specific proof remains required even after reuse threshold is defined

## What This Pass Does Not Prove

This pass does not prove:

- the reuse threshold is already met
- repo naming is now operationally reusable
- repo naming is now `adoptable now`
- `_stack` should implement repo-naming helper logic
- any marker move is justified

## Workflow Posture After This Review

Updated Local Data Gateway posture for repo naming:

- `real-workflow proof-admitted later`
- reuse threshold frozen
- reuse threshold not yet met
- still below `adoptable now`

That is the smallest honest refinement after the real-workflow proof-family decision.

## Exact Next Package

`Local Data Gateway repo naming second-instance admission trigger review`

Why:

- the family no longer needs more contract language
- the next honest root-side question is what exact evidence should trigger recognition of a second valid instance when another bounded candidate appears
- that still stays below implementation and below adoption claims

## Rule

Reuse-threshold review must narrow when a proof family is reusable, not silently graduate it into general workflow adoption.

## Pattern

contract checkpoint -> proof admission -> bounded proof shape -> one real blocked workflow instance -> real-workflow proof-family admission -> reuse threshold frozen -> second candidate required before reuse claim

## Failure Mode

A strong first proof family gets mistaken for broad operational reuse before multiple real workflow instances exist.
