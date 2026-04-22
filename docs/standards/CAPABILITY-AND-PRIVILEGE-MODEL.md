# Capability And Privilege Model

ATLAS workers do not hold ambient admin rights. Privilege is requested per action, approved per action, executed by the host, and proven by a receipt.

This document is a root boundary summary only. Lifeline owns the canonical execution lineage and receipt semantics:

- `repos/fawxzzy-lifeline/docs/contracts/privileged-execution-contract.md`
- `repos/fawxzzy-lifeline/docs/privileged-execution.md`

## Contract Roles

- `atlas.capability.profile.v1` describes what a worker may request.
- `atlas.privileged-action.request.v1` records the worker proposal.
- `atlas.approval.receipt.v1` records the approval, rejection, or expiry state for that proposal.
- `atlas.privileged-action.receipt.v1` records what actually ran under the approved scope.

Ownership rule:

- Lifeline owns the execution-side field contract and lineage for these artifacts.
- ATLAS root uses the vocabulary to route work and interpret boundaries.
- Playbook may govern approval policy, but it does not replace Lifeline receipt ownership.
- `_stack` may provide worker context and `source_refs`, but it does not redefine Lifeline execution receipts.

## Proposal To Receipt Flow

1. a worker proposes an action
2. system or human approval grants a scoped capability, or rejects it
3. the host executes only within the approved scope
4. execution emits a receipt that names the request, approval, worker, assignment, and stack lock digest

Worker-originated requests may also carry `source_refs` so the privileged path stays anchored to governed assignment, context, merge, or session artifacts instead of hidden transcript history.

Use the Lifeline contract doc for exact lineage keys, status values, normalized path rules, and blocked/failure receipt requirements.

## Capability Profile

A capability profile must declare:

- filesystem read, write, and create scopes
- network scopes
- process execution permissions
- package manager permissions
- elevation requirement
- resource budgets
- allowed data classes

Profiles are descriptive. They are not permission by themselves.

## Approval Rules

- approvals are per action
- approvals are time bounded
- approvals are scoped to the request they approve
- approval receipts must reference the request digest
- rejected and expired approvals remain auditable

## Receipt Rule

No privileged action is considered valid without a receipt. If execution happened, there must be a `atlas.privileged-action.receipt.v1` record that ties the run back to the original request and approval.

## Audit Retention

- keep request, approval, and execution receipts together as the auditable trail
- keep the stack lock digest in every object so the working set is pinned to a reproducible state
- do not rely on worker transcript history for privilege provenance
- do not infer approval from successful execution alone

## Hard Constraints

- privilege is never ambient worker state
- admin/elevation is not a worker mode
- read-only is the default when a worker has no approved scope
- exact action, target paths, and target resources must be explicit before approval
