# Privileged Action Runbook

This runbook covers the normal lifecycle for a privileged action in ATLAS.

This runbook does not replace Lifeline operator truth. Use these Lifeline docs as canonical references for execution-backed actions:

- `repos/fawxzzy-lifeline/docs/contracts/privileged-execution-contract.md`
- `repos/fawxzzy-lifeline/docs/ops/lifeline-operator-surface.md`
- `repos/fawxzzy-lifeline/docs/runbooks/hermetic-validation-operator-flow.md`

## Lifecycle

1. worker proposes action with a request document
2. approver reviews the request and issues an approval receipt or rejection receipt
3. host executes only when the approval is current and within scope
4. host emits a privileged-action receipt

ATLAS root uses this flow as the operator boundary. Lifeline owns the exact execution, approval-status, blocked-receipt, and remediation semantics.

## Scope Rules

- approval scope must match the requested action
- filesystem access must be explicit and path-scoped
- network access must be explicit and domain-scoped
- process execution permissions must be explicit
- package manager access must be explicit
- elevation must be time bounded and per action

## Expiry Rules

- expired approvals are not executable
- a stale approval receipt is a hard stop, even if the request is otherwise valid
- when the approval expires, the worker must re-request permission

## Audit Rules

- keep the request, approval receipt, and execution receipt together
- retain the stack lock digest, worker id, and assignment id in every object
- record the exact action, target paths, and any changed files or resources in the execution receipt
- if execution is blocked, still emit an execution receipt or blocked receipt equivalent in the host workflow

For proof-backed completion, do not invent a second root receipt doctrine. Follow Lifeline's proof-pass receipt contract and treat root read models as references to that owner-repo truth.

## Operational Defaults

- start as read-only
- escalate only the smallest scope necessary for the action
- prefer system approval for routine scoping and human approval for risky elevation
- never reuse a broad approval for a different action
