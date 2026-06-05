# _Stack Readiness Stack Validate Validation-Summary Report-Contract And Contradiction-Routing Pass 19 - 2026-06-03

- Date: `2026-06-03`
- Lane: `_stack Readiness stack validate validation-summary report-contract and contradiction-routing pass 19`
- Mode: `docs-only root-bounded report-contract design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/ops/_STACK-READINESS-STACK-VALIDATE-VALIDATION-SUMMARY-COMMAND-DESIGN-PASS-17-2026-06-03.md`
  - `docs/ops/_STACK-READINESS-STACK-VALIDATE-VALIDATION-SUMMARY-EVIDENCE-ADMISSION-AND-DELTA-DISCIPLINE-PASS-18-2026-06-03.md`
  - `docs/ops/_STACK-READINESS-STACK-VERCEL-HEALTH-REPORT-CONTRACT-AND-CONTRADICTION-ROUTING-PASS-11-2026-05-29.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
  - `docs/PLAYBOOK_NOTES.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative report contract for `_stack` `stack validate` validation-summary work and one explicit contradiction-routing rule.

This pass does not:

- implement the command
- mutate `repos/_stack`
- reopen command-design or evidence-admission logic already frozen
- widen into marker automation or receipt-drafting helpers
- claim that implementation or governed execution is now admitted

## Inherited Result

Pass 17 already froze:

- exact command purpose
- exact bounded inputs and outputs
- exact non-health failure exits
- exact no-mutation guard

Pass 18 already froze:

- exact current snapshot authority
- exact admitted baseline receipt shapes
- exact count-only delta discipline
- exact contradiction and baseline-unavailable fail-closed rules

This pass consumes those seams and freezes how the report must present that already-governed posture.

## Exact Required Success Report Fields

Every successful validation-summary report must emit:

1. `command`
   - fixed identifier: `stack validate`

2. `snapshot`
   - one exact final count tuple:
     - `critical`
     - `error`
     - `warning`
     - `info`

3. `artifact_refs`
   - flat list containing:
     - `runtime/receipts/validation/stack-validation.latest.md`
     - `runtime/receipts/validation/stack-validation.latest.json`

4. `delta_status`
   - exactly one of:
     - `not-requested`
     - `computed`
     - `unavailable`

5. `summary_mode`
   - exactly one of:
     - `snapshot-only`
     - `snapshot-plus-delta`

6. `routing_note`
   - one exact next routing posture only

## Exact Optional Success Report Fields

These fields may appear only when their condition is true:

1. `baseline_ref`
   - only when `--delta-from` was requested

2. `delta`
   - only when `delta_status=computed`
   - limited to exact count deltas for:
     - `critical`
     - `error`
     - `warning`
     - `info`

3. `receipt_context`
   - only when `--receipt-context <relative-path>` was supplied
   - must echo the bounded relative path only

4. `delta_unavailable_reason`
   - only when `delta_status=unavailable`
   - must be one exact bounded reason rather than a narrative bundle

## Exact Failure Report Fields

When the command fails before a receipt-ready success report exists, it must emit:

1. `command`
   - fixed identifier: `stack validate`

2. `failure_code`
   - one of:
     - `invalid-input`
     - `validator-failed`
     - `artifact-missing`
     - `artifact-contradiction`
     - `delta-baseline-unavailable`

3. `failure_scope`
   - exactly one of:
     - `input`
     - `validator-execution`
     - `current-artifacts`
     - `baseline`

4. `message`
   - one bounded sentence only

5. `routing_note`
   - one exact next routing posture only

## Exact Conditional Failure Payloads

### `artifact-contradiction`

May include one bounded `contradiction_note` containing:

- `contradiction_scope`
  - `current-artifacts`
  - `baseline`

- `conflicting_refs`
  - flat list only

- `summary_consequence`
  - `no-summary`
  - `snapshot-only`

### `delta-baseline-unavailable`

May include:

- `baseline_ref`
- `snapshot`
- `artifact_refs`

only when:

- the paired latest artifacts are present
- the paired latest artifacts agree
- current snapshot truth is still packageable even though delta is not

No other failure code may emit a partial summary snapshot.

## Exact Text Report Contract

### `snapshot-only`

Text output must contain, in this order:

1. one exact tuple line
   - `critical=<n> error=<n> warning=<n> info=<n>`

2. one artifact-ref line
   - naming both latest validation artifacts

3. one routing line
   - current-snapshot packaging only

### `snapshot-plus-delta`

Text output must contain, in this order:

1. the exact tuple line
2. the exact artifact-ref line
3. one exact delta line tied to one cited `baseline_ref`
4. one routing line

### `failure`

Text failure output must contain only:

1. `failure_code=<code>`
2. one bounded message line
3. one routing line

and may include the bounded contradiction or baseline-unavailable payload only when admitted above.

## Exact JSON Report Contract

### `success`

JSON success output must contain:

- `command`
- `snapshot`
- `artifact_refs`
- `delta_status`
- `summary_mode`
- `routing_note`

and only the conditionally admitted optional fields.

### `failure`

JSON failure output must contain:

- `command`
- `failure_code`
- `failure_scope`
- `message`
- `routing_note`

and only the conditionally admitted bounded failure payloads.

## Exact Forbidden Report Fields

The report may not emit:

- marker recommendations
- lane-ratchet claims
- debt-class interpretation as if it were count delta
- deploy readiness claims
- owner-repo health claims
- publication claims
- multiple competing routing recommendations
- speculative implementation status

## Exact Routing Note By Outcome

### `snapshot-only`

Routing note must say only:

- `package current snapshot only and continue`

### `snapshot-plus-delta`

Routing note must say only:

- `package current snapshot plus exact count delta and continue`

### `invalid-input`

Routing note must say only:

- `fix invocation and rerun before packaging`

### `validator-failed`

Routing note must say only:

- `route to validator-failure triage before summary claims`

### `artifact-missing`

Routing note must say only:

- `rerun or repair latest artifact production before summary claims`

### `artifact-contradiction`

Routing note must say only:

- `route to one bounded root-only contradiction reconciliation packet`

### `delta-baseline-unavailable`

Routing note must say only:

- `package current snapshot only and open one bounded baseline-citation repair packet only if delta wording is still required`

## Exact Contradiction Rule

### `current-artifacts contradiction`

If the latest md/json artifact pair disagree:

- `failure_code=artifact-contradiction`
- `failure_scope=current-artifacts`
- `summary_consequence=no-summary`

Root routing:

- one bounded root-only validation-artifact reconciliation packet

### `baseline contradiction`

If one cited baseline receipt contains competing or self-contradictory historical tuples:

- `failure_code=artifact-contradiction`
- `failure_scope=baseline`
- `summary_consequence=no-summary` when the contradiction blocks even current packaging through the requested delta path
- `summary_consequence=snapshot-only` only when current paired artifacts agree and root still chooses to package current snapshot without delta

Root routing:

- one bounded root-only baseline reconciliation packet

## Exact Out-Of-Scope Boundary

Still out of scope:

- implementation admission
- live command execution
- mutation or repair work
- `_stack` worker routing for code changes
- broader automation-family promotion

## Exact Next Package

`_stack Readiness stack validate validation-summary implementation-admission and no-execution guard pass 20`

Why:

- command purpose, evidence rules, report shape, and contradiction routing are now frozen
- the next remaining docs-only ambiguity is the exact implementation-admission line without letting report-contract work imply live execution permission

## Recommendation Type

`durable with bounded inference`

Durable because:

- this pass closes one real operator-surface ambiguity by freezing the receipt-ready output contract and contradiction-routing posture for the validation-summary family
- the routing rules are downstream of already-frozen command and evidence boundaries

Bounded inference because:

- pass 20 is compressed from the remaining implementation-admission ambiguity by analogy to the earlier `_stack` `stack vercel-health` sequence

## Ratchet Decision

Ratchet:

- `_stack Readiness: 72% -> 73%`

Why:

- this pass materially reduces one real ambiguity class by freezing one exact report schema, one exact partial-snapshot exception for baseline-unavailable cases, and one exact contradiction-routing rule
- the move stays to the smallest honest increment because no implementation, no governed execution, and no repeatable operator proof loop landed

## Validation Note

Live validation at the end of this pass remained:

- `critical=0 error=0 warning=494 info=0`

## Rule

`Freeze Report Shape Before Command Admission`

Do not admit implementation work for a summary command until the success and failure payloads are specific enough that contradiction handling cannot drift into prose.

## Pattern

`Snapshot Contract Before Implementation`

freeze command purpose -> freeze evidence gate -> freeze report contract -> freeze contradiction routing -> only then discuss implementation admission

## Failure Mode

`Pretty Output Contradiction Drift`

If the command reaches implementation before the report payload and routing notes are explicit, current snapshots, unavailable deltas, and contradictions get smoothed into prose that sounds safer than the governed evidence really is.
