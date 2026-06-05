# Local Data Gateway Repo Naming Second-Instance Admission Trigger Review - 2026-05-31

- Date: `2026-05-31`
- Owner: ATLAS root
- Mode: `docs-only second-instance admission trigger review`
- Scope: `Atlas-owned repo naming proof-family reuse threshold trigger conditions`
- Source surfaces:
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-PARKED-FAMILY-RE-ENTRY-THRESHOLD-CHECKPOINT-2026-05-31.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-PARKED-ADOPTABLE-LATER-FAMILY-RE-ENTRY-SELECTION-CHECKPOINT-2026-05-31.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-BROADER-ADOPTION-MAP-REFRESH-CHECKPOINT-2026-05-31.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-PROOF-FAMILY-REUSE-THRESHOLD-REVIEW-2026-05-28.md`
  - `runtime/receipts/validation/stack-validation.latest.md`

## Objective

Freeze the smallest honest admission-trigger review for when a second bounded repo-naming candidate should count as a valid reuse-threshold trigger without silently widening the family contract.

This checkpoint does not:

- widen repo naming into `adoptable now`
- admit family reuse already proven
- reopen owner-repo rename execution
- refresh shared restart spines
- touch `_stack`

## Root State

- branch: `main`
- working tree: dirty from surrounding wave work outside this packet
- validation baseline before drafting: `critical=0 error=3 warning=489 info=0`

## Durable Starting Truth

Already frozen before this checkpoint:

- repo naming remains the parked-family re-entry winner
- repo naming remains `adoptable later`
- the family already has one proven bounded instance
- the family still needs one second bounded candidate instance to test same-shape reuse

The remaining question is what exact evidence should count toward admitting that second instance and what should instead route to explicit family-shape expansion.

## Admitted Second-Instance Trigger Evidence

The following exact evidence classes should count toward admitting a second bounded repo-naming instance as a valid reuse-threshold trigger:

1. one durable rename-manifest packet or equivalent contract-complete candidate packet for a distinct repo-naming candidate
2. one exact execution receipt for that same candidate with an honest bounded outcome class:
   - `blocked-before-rename`
   - or `executed-and-reconciled`
3. one exact proof or reconciliation receipt tied to the same candidate
4. one no-send attestation that still preserves all remote-facing fields as explicitly `false`
5. one validation closeout reference that stays green at the relevant control-plane checkpoint
6. one candidate packet whose minimum manifest fields and proof-output contract stay within the already-frozen repo-naming family shape

If all of the above are present for one distinct second candidate, the family may honestly treat that candidate as a valid second-instance trigger for reuse-threshold review.

## Insufficient Trigger Evidence

The following evidence classes are insufficient:

- one second candidate named in prose without a durable candidate packet
- one second candidate with only planning or doctrine language and no execution receipt
- one second candidate with only an execution receipt but no proof or reconciliation receipt tied to the same candidate
- one second candidate that preserves the no-send boundary unclearly or implicitly rather than explicitly
- one second candidate whose contract shape becomes legible only after adding new mandatory family fields
- one second candidate that relies on hidden gateway-specific rename logic to make the packet understandable

Any of those may justify later exploration.

None of them justify second-instance admission.

## Same-Family Shape Versus Allowable Differences

The exact shape similarities that must remain stable are:

- the same minimum manifest field class
- the same proof-output contract class
- the same no-send boundary
- the same family-level interpretation that candidate-specific truth still lives in per-candidate receipts

The following differences are allowable without forcing expansion:

- different exact candidate identity
- different exact rewrite-surface inventory
- different exact rollback order
- different exact blocker class
- different exact stale-reference reconciliation scope
- different bounded outcome between `blocked-before-rename` and `executed-and-reconciled`

Those are candidate-specific differences, not automatic family-shape differences.

## Expansion-Forcing Conditions

The following conditions force explicit contract expansion instead of second-instance admission:

- the second candidate needs new mandatory manifest fields not present in the current family shape
- the second candidate needs new mandatory proof-output fields to remain legible
- the second candidate requires hidden gateway-specific rename logic not already represented in the frozen family shape
- the second candidate weakens or blurs the no-send boundary
- the second candidate changes the family from bounded local repo-naming proof into a different control-plane class

If any of those appear, the correct route is:

- explicit expansion review

not:

- second-instance admission

## Admission-Trigger Result

The exact second-instance admission trigger is now frozen as:

- one distinct second bounded repo-naming candidate with full candidate packet, full bounded execution receipt, full proof or reconciliation linkage, explicit no-send preservation, green validation reference, and no mandatory family-shape expansion

That is the smallest honest trigger surface.

## Derivative Or Mirror Restatement Only

Derivative or mirror surfaces may:

- restate the admitted second-instance trigger evidence classes
- restate the insufficient evidence classes
- restate the allowable candidate-specific differences
- restate the expansion-forcing conditions

Derivative or mirror surfaces may not:

- narrate trigger recognition as if second-instance evidence already exists
- treat allowed candidate-specific differences as proof of family expansion
- weaken expansion-forcing conditions into informal tolerance

## Recommendation Status

Recommendation type:

- `durable`

Why:

- the trigger review is anchored in the parked-family threshold checkpoint and the earlier repo-naming reuse-threshold review
- no speculative implementation assumption is needed to define the evidence boundary honestly

## Marker Decision

Decision:

- hold `Local Data Gateway` at `66%`

Why:

- this pass freezes the admission trigger only
- it does not widen the proven `adoptable now` set
- it does not clear a blocker in executed or proven reuse state
- it does not create a new proof-backed reuse class

## Validation

- `python .\ops\validation\validate_stack.py`
- result after drafting: `critical=0 error=3 warning=489 info=0`

The live `error=3` state remains the already-classified in-flight `stack.lock.yaml` dirty-state drift and is not introduced by this receipt.

## Exact Next Packet

- `Local Data Gateway repo naming second-instance evidence watchpoint checkpoint`

Why:

- the trigger conditions are now frozen
- the next honest control-plane move is to define the exact watchpoint for recognizing when real future evidence satisfies those trigger conditions
- that remains docs-only and root-bounded while staying below actual reuse admission

## Rule

Second-instance admission must preserve the bounded family shape; anything that changes the shape routes to explicit expansion review.

## Pattern

freeze re-entry threshold -> freeze second-instance trigger evidence -> separate allowed candidate variation from true family-shape expansion -> define evidence watchpoint next

## Failure Mode

The lane mistakes a merely similar second candidate for a valid reuse trigger even though it adds hidden logic, new mandatory fields, or a blurred no-send boundary.
