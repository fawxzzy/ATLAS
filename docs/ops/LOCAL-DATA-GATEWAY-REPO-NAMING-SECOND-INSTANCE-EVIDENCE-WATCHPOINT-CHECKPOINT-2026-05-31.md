# Local Data Gateway Repo Naming Second-Instance Evidence Watchpoint Checkpoint - 2026-05-31

- Date: `2026-05-31`
- Owner: ATLAS root
- Mode: `docs-only second-instance evidence watchpoint checkpoint`
- Scope: `repo naming second-instance evidence recognition only`
- Source surfaces:
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-SECOND-INSTANCE-ADMISSION-TRIGGER-REVIEW-2026-05-31.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-PARKED-FAMILY-RE-ENTRY-THRESHOLD-CHECKPOINT-2026-05-31.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-PARKED-ADOPTABLE-LATER-FAMILY-RE-ENTRY-SELECTION-CHECKPOINT-2026-05-31.md`
  - `runtime/receipts/validation/stack-validation.latest.md`

## Objective

Freeze the smallest honest watchpoint checkpoint for what evidence should be monitored to recognize a valid second bounded repo-naming instance without prematurely admitting family reuse.

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

- repo naming remains the parked-family re-entry winner
- repo naming remains `adoptable later`
- the second-instance admission trigger is already frozen
- the family still has only one proven bounded instance

The remaining question is what concrete evidence should be watched for, what only counts as a near miss, and what exact event should trigger reopening the family for a real second-instance admission decision.

## Valid Second-Instance Watchpoints

The exact concrete watchpoints to monitor are:

1. one distinct second repo-naming candidate appears with a durable rename-manifest packet or equivalent contract-complete candidate packet
2. that same candidate receives one bounded execution receipt with honest outcome:
   - `blocked-before-rename`
   - or `executed-and-reconciled`
3. that same candidate receives one proof or reconciliation receipt tied to the same candidate lineage
4. that same candidate preserves one explicit no-send attestation with all remote-facing fields still `false`
5. that same candidate closes with one green validation reference at the relevant control-plane point
6. the candidate remains inside the already-frozen family shape:
   - same minimum manifest field class
   - same proof-output contract class
   - same no-send boundary

These are watchpoints because they are concrete, evidence-shaped, and directly tied to the already-frozen admission trigger.

## Near-Miss Watchpoints

The following evidence should be watched but not admitted yet:

- a second candidate named in planning, doctrine, or issue prose without a durable candidate packet
- a second candidate with candidate packet plus execution receipt but no proof or reconciliation linkage
- a second candidate whose no-send preservation is implied rather than explicit
- a second candidate that is mostly shape-compatible but still appears to need one new mandatory field
- a second candidate whose evidence bundle is partial, stale, or split across receipts without clear lineage binding

These signals matter because they may indicate a real second instance is forming.

They do not yet satisfy admission conditions.

## Explicit Re-Open Trigger

The exact event that should trigger reopening the family for a real second-instance admission decision is:

- one distinct second bounded repo-naming candidate accumulates the full watchpoint bundle:
  - durable candidate packet
  - bounded execution receipt
  - proof or reconciliation linkage
  - explicit no-send preservation
  - green validation reference
  - no mandatory family-shape expansion

Only that event reopens the family for a real second-instance admission decision.

Near misses do not reopen the family by themselves.

They justify monitoring only.

## Derivative Or Mirror Restatement Only

Derivative or mirror surfaces may:

- restate the valid watchpoints
- restate the near-miss watchpoints
- restate the exact reopen trigger

Derivative or mirror surfaces may not:

- narrate near-miss evidence as if second-instance admission is underway
- weaken the reopen trigger into a vague similarity standard
- treat watchpoint monitoring as proof-backed family reuse

## Recommendation Status

Recommendation type:

- `durable`

Why:

- the watchpoint checkpoint is anchored in the earlier second-instance admission trigger review and parked-family threshold posture
- no speculative implementation assumption is needed to define what should be monitored

## Marker Decision

Decision:

- hold `Local Data Gateway` at `66%`

Why:

- this pass freezes evidence watchpoints only
- it does not widen the proven `adoptable now` set
- it does not clear a blocker in executed or proven reuse state
- it does not create a new proof-backed reuse class

## Validation

- `python .\ops\validation\validate_stack.py`
- result after drafting: `critical=0 error=3 warning=489 info=0`

The live `error=3` state remains the already-classified in-flight `stack.lock.yaml` dirty-state drift and is not introduced by this receipt.

## Exact Next Packet

- `Local Data Gateway repo naming second-instance evidence receipt-gate checkpoint`

Why:

- the watchpoints are now frozen
- the next honest control-plane move is to define the exact receipt gate a future evidence bundle must pass through to count as a valid second-instance submission
- that remains docs-only and root-bounded while staying below actual reuse admission

## Rule

Watchpoints monitor concrete evidence signals; only the full trigger bundle reopens the family for admission review.

## Pattern

freeze threshold -> freeze admission trigger -> freeze evidence watchpoints -> define the receipt gate future evidence must satisfy

## Failure Mode

The lane mistakes partial or near-miss evidence for a true second-instance trigger and reopens repo naming before the full bounded evidence bundle actually exists.
