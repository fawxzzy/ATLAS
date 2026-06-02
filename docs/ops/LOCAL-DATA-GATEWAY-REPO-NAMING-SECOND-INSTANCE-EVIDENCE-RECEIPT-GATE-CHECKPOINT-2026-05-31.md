# Local Data Gateway Repo Naming Second-Instance Evidence Receipt-Gate Checkpoint - 2026-05-31

- Date: `2026-05-31`
- Owner: ATLAS root
- Mode: `docs-only second-instance evidence receipt-gate checkpoint`
- Scope: `repo naming second-instance evidence bundle completeness only`
- Source surfaces:
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-SECOND-INSTANCE-EVIDENCE-WATCHPOINT-CHECKPOINT-2026-05-31.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-SECOND-INSTANCE-ADMISSION-TRIGGER-REVIEW-2026-05-31.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-PARKED-FAMILY-RE-ENTRY-THRESHOLD-CHECKPOINT-2026-05-31.md`
  - `runtime/receipts/validation/stack-validation.latest.md`

## Objective

Freeze the smallest honest receipt-gate checkpoint for when a second repo-naming evidence bundle should count as durably complete enough to reopen the family for a real second-instance admission decision.

This checkpoint does not:

- widen repo naming into `adoptable now`
- admit second-instance evidence already present
- reopen owner-repo rename execution
- refresh shared restart spines
- touch `_stack`

## Root State

- branch: `main`
- working tree: dirty from surrounding wave work outside this packet
- validation baseline before drafting: `critical=0 error=3 warning=489 info=0`

## Durable Starting Truth

Already frozen before this checkpoint:

- the second-instance admission trigger is already defined
- the evidence watchpoints are already defined
- repo naming still has only one proven bounded instance

The remaining question is what exact receipt set must exist together, how lineage must be visible across that set, and what partial bundles remain insufficient even when some receipts are individually strong.

## Gate-Complete Receipt Bundle

The exact receipt set that must exist together before the second-instance evidence bundle counts as durably gate-complete is:

1. one durable rename-manifest packet or equivalent contract-complete candidate packet for one distinct second repo-naming candidate
2. one bounded execution receipt for that same candidate with honest outcome:
   - `blocked-before-rename`
   - or `executed-and-reconciled`
3. one proof or reconciliation receipt tied to that same candidate
4. one explicit no-send attestation preserving all remote-facing fields as `false`
5. one green validation closeout reference for the relevant control-plane checkpoint

All five must be present together.

No subset counts as gate-complete.

## Required Lineage Binding

The following exact lineage binding must be visible across the gate-complete bundle:

- all receipts must point to the same exact second candidate identity
- the candidate packet must be the anchor receipt for the bundle
- the execution receipt must visibly cite the same candidate packet lineage
- the proof or reconciliation receipt must visibly cite the same candidate packet and execution lineage
- the no-send attestation must visibly apply to that same candidate bundle rather than to repo naming in the abstract
- the validation reference must be attributable to the same bounded closeout point for that candidate

Lineage must be explicit enough that the bundle can be read as one bounded candidate submission rather than as several similar receipts nearby in time.

## Insufficient Partial Bundles

The following partial bundles remain insufficient even if individually strong:

- candidate packet plus execution receipt, but no proof or reconciliation receipt
- candidate packet plus proof receipt, but no bounded execution receipt
- execution receipt plus proof receipt, but no durable candidate packet anchor
- a full-looking bundle where no-send preservation is only implied
- a bundle with all major receipt classes present, but lineage binding across them is ambiguous or split
- a bundle with all major receipt classes present, but the candidate appears to require new mandatory family-shape fields

These may justify attention or assembly work.

They do not justify reopening the family for second-instance admission.

## Receipt-Gate Result

The exact receipt gate is now frozen as:

- one visibly complete and lineage-bound five-part bundle for one distinct second repo-naming candidate:
  - candidate packet
  - bounded execution receipt
  - proof or reconciliation receipt
  - explicit no-send attestation
  - green validation closeout reference

That is the smallest honest gate-complete bundle.

## Derivative Or Mirror Restatement Only

Derivative or mirror surfaces may:

- restate the five-part gate-complete bundle
- restate the required lineage binding
- restate the insufficient partial bundles

Derivative or mirror surfaces may not:

- narrate scattered strong receipts as if the gate were complete
- weaken lineage requirements into similarity by timing or topic alone
- treat a nearly complete bundle as if family reopening is already justified

## Recommendation Status

Recommendation type:

- `durable`

Why:

- the receipt gate is anchored in the already-frozen trigger and watchpoint boundaries
- no speculative implementation assumption is needed to define bundle completeness honestly

## Marker Decision

Decision:

- hold `Local Data Gateway` at `66%`

Why:

- this pass freezes the receipt gate only
- it does not widen the proven `adoptable now` set
- it does not clear a blocker in executed or proven reuse state
- it does not create a new proof-backed reuse class

## Validation

- `python .\ops\validation\validate_stack.py`
- result after drafting: `critical=0 error=3 warning=489 info=0`

The live `error=3` state remains the already-classified in-flight `stack.lock.yaml` dirty-state drift and is not introduced by this receipt.

## Exact Next Packet

- `Local Data Gateway repo naming second-instance evidence bundle closeout boundary checkpoint`

Why:

- the receipt gate is now frozen
- the next honest control-plane move is to define the exact closeout boundary for when a future gate-complete bundle is sufficient to reopen the family, versus when it still only counts as prepared evidence
- that remains docs-only and root-bounded while staying below actual second-instance admission

## Rule

Strong receipts count only when they form one complete, lineage-bound candidate bundle.

## Pattern

freeze admission trigger -> freeze watchpoints -> freeze receipt gate -> define the closeout boundary for future gate-complete evidence

## Failure Mode

The lane mistakes several individually strong receipts for a valid second-instance bundle even though they are not visibly bound to one exact candidate or one bounded closeout point.
