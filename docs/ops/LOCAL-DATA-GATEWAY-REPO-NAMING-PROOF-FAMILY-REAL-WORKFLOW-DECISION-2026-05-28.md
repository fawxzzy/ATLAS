# Local Data Gateway Repo Naming Proof-Family Real-Workflow Decision - 2026-05-28

- Date: `2026-05-28`
- Owner: ATLAS root
- Mode: `docs-only proof-family decision`
- Scope: `repo naming real-workflow proof-family posture inside Local Data Gateway`
- Source surfaces:
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-RENAME-MANIFEST-PROOF-ADMISSION-DECISION-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-BOUNDED-PROOF-SHAPE-REVIEW-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-WORKFLOW-ADOPTION-EXPANSION-PASS-2-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-MARKER-RATCHET-CHECKPOINT-10-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-STREAM-BLOCKER-DISPOSITION-RATCHET-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-STREAM-BLOCKER-CLASS-RECHECK-2026-05-28.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/atlas-book/14-lane-split-execution.md`
- Control-plane checkpoint: `main@8d876fe`

## Objective

Decide whether the already-durable repo naming `proof-admitted later` class is now strong enough to admit a bounded real-workflow proof family inside the Local Data Gateway lane without promoting repo naming workflows to `adoptable now`.

This pass does not:

- modify `_stack`
- imply send-capable behavior
- authorize repo rename execution
- authorize remote or GitHub-side rename assumptions
- graduate repo naming into `adoptable now`
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `8d876fe`
- status: clean except intentional untracked `archive/`
- validation: green before drafting at `critical=0 error=0 warning=311`

## Current Repo-Naming Posture Recomputed

Before this decision, the repo-naming family already stood at:

- `proof-admitted later`
- `contract-complete but execution-blocked`
- bounded proof shape frozen for:
  - `blocked-before-rename`
  - `executed-and-reconciled`

The exact open question is narrower now:

- does the family still only have a clean contract and proof shape
or
- does it now also have enough real workflow evidence to enter a sharper proof-family class

## Current Real Workflow Evidence

The `stream` packet now provides one exact real local workflow family path with durable evidence:

- one approved safe-first candidate
- one frozen rewrite and rollback plan
- repeated blocked-before-rename execution receipts
- repeated blocked proof / reconciliation receipts
- one blocked-state interpretation ratchet
- one blocker-resolution chain that consumed `2b`
- one blocker-class recheck proving `2c` is now the sole remaining blocker

That means the family no longer has only hypothetical proof shape.

It now has one real bounded workflow path that has already produced honest local receipts under live blocker conditions.

## Decision Standard

For a family to enter a `real-workflow proof-admitted later` class, all of the following must already be true:

1. the family already satisfies the lower `proof-admitted later` standard
2. the bounded proof shape is already frozen
3. at least one exact bounded workflow path has produced durable live receipts under real local conditions
4. that live workflow path can end in honest blocked truth without breaking the proof contract
5. the family still remains below generic execution packaging, send behavior, and `adoptable now`

If any of those fail, the family stays only:

- `proof-admitted later`

## Decision

Yes.

Atlas-owned repo naming now enters the narrower middle class:

- `real-workflow proof-admitted later`

Equivalent bounded reading:

- `contract-complete`
- `proof-shape-complete`
- `one real workflow family path proven`
- `still execution-blocked`

## Why This Admission Is Honest

This class is now honest because the family has moved beyond contract-only readiness.

The `stream` packet has already shown that the current family can produce:

- a bounded candidate identity
- bounded rewrite-surface truth
- bounded rollback truth
- blocked-before-rename execution truth
- blocked proof / reconciliation truth
- blocked-state interpretation truth

under a real local workflow chain rather than only a hypothetical packet model.

The key point is that the workflow did not need to pretend the rename succeeded.

Blocked truth remained a valid proof outcome, and the durable receipt chain preserved useful local evidence anyway.

That is enough to admit one bounded real-workflow proof family.

## Why This Still Does Not Reach `adoptable now`

Repo naming still remains below `adoptable now` because:

- the admitted real workflow path is still tied to one bounded candidate family
- the current useful outcome is still tightly coupled to rename-lane execution state
- the current family still depends on rename-specific rewrite and reconciliation semantics
- the only live candidate family path is still blocked by owner-side `2c`
- no proof yet shows that the current generic no-send chain carries this family as reusable operational workflow without rename-specific gateway creep

So the honest maturity is now:

- above plain `proof-admitted later`
- below `adoptable now`

## Exact Newly Admitted Class

The newly admitted class is:

- local-only repo-naming real-workflow proof families

This class may include:

- rename-manifest packets with real blocker or execution state
- blocked-before-rename real workflow proof
- executed-and-reconciled real workflow proof
- no-send attestations that remain fully local

This class may not imply:

- rename execution approval
- generic workflow admission across all naming candidates
- `_stack` helper implementation
- remote rename assumptions
- GitHub-side rename assumptions
- send-capable wrapper behavior

## Relation To The Current `stream` Packet

The current `stream` packet is now strong enough to count as one bounded real-workflow proof family path.

It is not yet strong enough to count as family-wide operational admission.

Current exact read:

- `2b` is cleared
- `2c` remains the sole active blocker
- the family therefore still has live operator relevance
- but the family still does not justify another root-side rename retry

That posture strengthens this decision:

- one real workflow path exists
- the path is still bounded
- the path still ends in honest blocked truth
- the family still stays below adoption

## What This Pass Proves

This pass proves:

- repo naming now has more than contract-only proof posture
- one bounded real workflow family path is now durably proven
- blocked execution can still count as valid real-workflow proof when the proof class explicitly admits blocked truth

## What This Pass Does Not Prove

This pass does not prove:

- repo naming is now `adoptable now`
- `_stack` should implement repo-naming helper logic
- one bounded family path is enough for marker movement
- the family is reusable across multiple rename candidates yet
- any rename should execute now

## Workflow Posture After This Decision

Updated Local Data Gateway posture for repo naming:

- `real-workflow proof-admitted later`
- still `contract-complete but execution-blocked`
- still below `adoptable now`

That is the smallest honest refinement beyond the bounded proof-shape review.

## Exact Next Package

`Local Data Gateway repo naming proof-family reuse threshold review`

Why:

- the family now has one bounded real workflow proof path
- the next honest question is not contract shape
- the next honest question is what additional reuse evidence would be required before this family could ever move beyond narrow proof-family admission

## Rule

Proof-family decisions must narrow maturity honestly without silently graduating execution-blocked workflows into adopt-now.

## Pattern

contract checkpoint -> proof-admission decision -> bounded proof-shape review -> one real blocked workflow chain -> real-workflow proof-family admission -> reuse threshold review before any adoption claim

## Failure Mode

A contract-complete workflow gets over-read as operationally adopted just because one bounded real blocked-workflow family now exists.
