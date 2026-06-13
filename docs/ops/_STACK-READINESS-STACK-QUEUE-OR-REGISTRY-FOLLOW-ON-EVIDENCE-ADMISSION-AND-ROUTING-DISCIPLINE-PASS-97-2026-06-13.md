# _Stack Readiness Stack Queue-Or-Registry Follow-On Evidence-Admission And Routing-Discipline Pass 97 - 2026-06-13

- Date: `2026-06-13`
- Lane: `_stack Readiness stack queue-or-registry follow-on evidence-admission and routing-discipline pass 97`
- Mode: `docs-only root-bounded evidence-admission and routing-discipline design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/ops/_STACK-READINESS-STACK-QUEUE-OR-REGISTRY-FOLLOW-ON-COMMAND-DESIGN-PASS-96-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-_STACK-EXECUTION-HOME-FOLLOW-ON-CONTRACT-FREEZE-PASS-93-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-_STACK-EXECUTION-HOME-FOLLOW-ON-OWNER-SURFACE-ADMISSION-PASS-94-2026-06-12.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-_STACK-EXECUTION-HOME-FOLLOW-ON-SUPPORTING-LANE-ADMISSION-PASS-95-2026-06-12.md`
  - `ops/atlas/runtime_state_execution_ready_transition_semantics.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@3a794f63`

## Objective

Freeze one compact authoritative evidence-admission and routing-discipline spine for `_stack` `stack queue-or-registry follow-on` work.

This pass does not:

- implement or run a `_stack` command
- mutate `repos/_stack`
- reopen execution-home admission
- widen into live runtime-state reads, queue drops, or worker launch
- claim that retained-state follow-on packaging is already landed

## Inherited Command-Design Result

Pass 96 already froze:

- the exact command purpose
- the exact bounded inputs and outputs
- the exact failure exits
- the exact no-mutation guard
- the exact routing-only ceiling

This pass consumes that command seam and freezes:

- which classifier surface is authoritative
- which classifier result classes are admitted for follow-on packaging
- how malformed or out-of-family classifier truth must fail closed

## Exact Authoritative Evidence

The future command must derive follow-on packaging only from one authoritative ATLAS classifier:

- `ops/atlas/runtime_state_execution_ready_transition_semantics.py`

The command may provide one explicit `candidate_path` input to that classifier.

The command may not replace classifier truth with:

- direct reads of live runtime-state json files
- direct reads of live runtime-state directories
- receipt prose
- restart prose
- queue folder inference
- worker or dispatch state

## Exact Admitted Classifier Result Classes

### 1. `destination-root unresolved`

Admitted only when the classifier resolves:

- `queue-home-destination-root-still-unresolved`
- `registry-home-destination-root-still-unresolved`

Use:

- package one bounded unresolved follow-on posture only
- route to exact-child-path resolution before any deeper shared follow-on claim

### 2. `blocked pending live direct-json read`

Admitted only when the classifier resolves one direct-file blocked-before-execution decision:

- `admitted-queue-home-live-direct-json-read-blocked-before-execution`
- `admitted-registry-home-live-direct-json-read-blocked-before-execution`

Use:

- package one bounded blocked follow-on posture only
- route to one bounded future live direct-json-read admission seam only

### 3. `blocked pending live directory read`

Admitted only when the classifier resolves one directory blocked-before-execution decision:

- `admitted-queue-home-live-directory-read-blocked-before-execution`
- `admitted-registry-home-live-directory-read-blocked-before-execution`

Use:

- package one bounded blocked follow-on posture only
- route to one bounded future live directory-read admission seam only

### 4. `non-admitted transition`

Admitted only when the classifier resolves one fail-closed non-follow-on class such as:

- `non-admitted-discovery-mode-execution-transition`
- `neutral-family-root-without-destination-class`
- `non-admitted-neutral-family-descendant`
- `outside-admitted-neutral-family-root`

Use:

- package one bounded stop-and-return posture only
- do not promote the candidate into a shared follow-on route

## Exact Forbidden Evidence Classes

Forbidden for follow-on packaging:

- live runtime-state artifact contents
- directory listings under retained-state homes
- queue markdown drops
- owner-repo runtime notes
- uncited recap prose
- multiple competing classifier runs in one command result
- restart mirrors standing in for classifier output

## Exact Sufficiency Rule

One classifier result is sufficient only when all of these are true:

- exactly one explicit `candidate_path` is provided
- the authoritative classifier runs successfully
- the classifier emits one exact bounded result payload
- the result belongs to one admitted class above

If any one of those is false, follow-on packaging is unavailable.

## Exact Routing Discipline Rule

Routing wording may report only:

- destination-root unresolved
- blocked pending live direct-json read
- blocked pending live directory read
- non-admitted transition

The command may not:

- infer live-read success
- infer queue-drop readiness
- infer worker-launch readiness
- infer execution-ready movement
- restate broader orchestration strategy as if it were classifier truth

## Exact Contradiction / Failure Handling

### `classifier execution failure`

If the authoritative classifier does not run cleanly:

- fail with `classifier-failed`
- emit no follow-on packaging result

### `classifier output malformed`

If classifier output is missing required fields or does not resolve to one admitted class:

- fail with `classifier-failed`
- emit no follow-on packaging result

### `input unavailable`

If the supplied `candidate_path` is missing, absolute, or escapes the workspace:

- fail with `invalid-input`
- emit no classifier claim

## Exact Output Strength Rules

### `follow-on success`

Emit one bounded follow-on package only when:

- the classifier runs successfully
- the classifier output is structurally valid
- the output resolves to one admitted class

### `fail closed`

Do not emit narrative smoothing such as:

- `probably ready for queue drop`
- `safe to dispatch`
- `close enough to execute`

unless a later admitted seam proves that claim directly.

## Exact Next Package

- `_stack Readiness stack queue-or-registry follow-on report-contract and contradiction-routing pass 98`

Why:

- command purpose, evidence authority, admitted classifier classes, and fail-closed routing discipline are now frozen
- the next remaining docs-only ambiguity is the exact success and failure report contract for this helper

## Marker Decision

- `none`

## Rule

One follow-on package needs one authoritative classifier result.
