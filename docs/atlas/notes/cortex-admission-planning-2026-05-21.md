# Cortex Admission Planning - 2026-05-21

## Purpose

This note opens the next Cortex lane as planning/admission documentation only.

It does not promote Cortex into an active owner repo.
It does not move runtime ownership away from ATLAS root.
It does not widen execution authority.

## Current Posture

Cortex is currently a root-owned read-only subsystem under:

- `runtime/cortex/**`
- `ops/cortex/**`

Adjacent repo posture remains unchanged:

- `repos/cortex` is adjacent historical context only
- it is not active runtime truth
- it is not a release-eligible owner surface
- it is not the current place for execution, receipts, or stack boundary truth

Current authority boundary:

- ATLAS root owns stack truth and path policy
- Lifeline owns operator execution and final release receipt truth
- Playbook owns governance/runtime verification patterns
- Foundation owns control-plane registry posture
- Cortex may read, summarize, classify, index, and prepare advisory artifacts only

## What Counts As Allowed Planning Work

This tranche may:

- document the live Cortex runtime surface
- classify which Cortex surfaces are root-only vs potentially extractable later
- define explicit admission gates for any future repo promotion or extraction
- identify reusable contracts, schemas, or examples worth isolating later
- describe the evidence needed before Cortex could become more than a root-owned read-only subsystem

This tranche should prefer documentation and contract inventory over implementation.

## Candidate Future Extraction Surfaces

These are the most plausible future extraction candidates if Cortex ever moves beyond planning:

1. Contract and schema surfaces
   - worker-context artifact contract
   - supervisor merge-request artifact contract
   - query bundle contract
   - kernel seed and proof summary example contracts

2. Read-only documentation and runbook surfaces
   - worker-context runbook
   - supervisor runbook
   - receipt compatibility notes
   - surface-reconciliation and MVP inventory notes

3. Pure read-model helpers
   - query and catalog interpretation rules
   - status/view-model logic that does not mutate owner truth

These are not currently approved for extraction. They are only the most likely later candidates.

## Blocked Surfaces

The following remain blocked from admission or extraction in this tranche:

- `runtime/cortex/**` as active runtime ownership
- any write path that mutates Lifeline receipts or final proof state
- any write path that mutates Foundation registry truth
- any execution or approval authority
- any dispatch authority into `_stack`, Lifeline, Playbook, or app repos
- any promotion of `repos/cortex` into active owner status

## Admission Gates

Any future Cortex admission or promotion lane should fail closed unless all of the following are true:

1. Owner truth is explicit
   - the candidate surface has one named owner
   - ATLAS root no longer needs to act as implicit backup owner for that surface

2. Runtime authority is unchanged or intentionally redefined
   - read-only surfaces remain read-only unless a later lane explicitly approves broader authority
   - no hidden receipt writer, executor, or dispatcher emerges through helper code

3. Path truth is updated atomically
   - manifest, lock, inventory, and owner-usage surfaces all agree
   - no half-root-owned / half-child-owned posture survives

4. Validation is real
   - the admitted surface has a documented verify entrypoint
   - proof for the new posture is machine-runnable, not only descriptive

5. Adjacent history is not promoted by accident
   - `repos/cortex` remains adjacent until an explicit later admission decision says otherwise
   - historical context does not become active owner truth by mere presence

6. Receipt truth remains bounded
   - Lifeline stays final receipt owner unless a separate lane changes that explicitly
   - Cortex compatibility or interpretation artifacts do not become final operational proof

## Recommended Planning Outputs For The Next Cortex Tranche

The next useful Cortex docs-only tranche should produce:

- one explicit extraction candidate inventory
- one admission checklist keyed to stack root truth surfaces
- one clear split between root-only runtime, extractable contracts, and blocked authority surfaces

That would be enough to prepare a later decision without starting implementation prematurely.

## Non-Goals

This planning lane does not:

- migrate runtime ownership
- expand execution authority
- modify Lifeline, Foundation, Playbook, or app repos
- change stack manifest or lock posture
- create a new Cortex service
- promote `repos/cortex`

## Rule

Cortex planning may define future admission boundaries, but it must not quietly cross them.

## Pattern

Inventory first, gate second, promote later.

## Failure Mode

Treating advisory Cortex documentation as implicit approval for runtime extraction would recreate the same owner-truth ambiguity the stack just finished removing elsewhere.
