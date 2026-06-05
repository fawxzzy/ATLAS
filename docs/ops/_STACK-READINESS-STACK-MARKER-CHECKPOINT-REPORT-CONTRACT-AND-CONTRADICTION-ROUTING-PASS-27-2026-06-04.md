# _Stack Readiness Stack Marker Checkpoint Report-Contract And Contradiction-Routing Pass 27 - 2026-06-04

- Date: `2026-06-04`
- Lane: `_stack Readiness stack marker checkpoint report-contract and contradiction-routing pass 27`
- Mode: `docs-only root-bounded report-contract design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/ops/_STACK-READINESS-STACK-MARKER-CHECKPOINT-COMMAND-DESIGN-PASS-25-2026-06-04.md`
  - `docs/ops/_STACK-READINESS-STACK-MARKER-CHECKPOINT-EVIDENCE-ADMISSION-AND-RESTART-SURFACE-DISCIPLINE-PASS-26-2026-06-04.md`
  - `docs/ops/_STACK-READINESS-STACK-VALIDATE-VALIDATION-SUMMARY-REPORT-CONTRACT-AND-CONTRADICTION-ROUTING-PASS-19-2026-06-03.md`
  - `docs/PLAYBOOK_NOTES.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative report contract for `_stack` `stack marker checkpoint` and one explicit contradiction-routing rule.

This pass does not:

- implement the command
- mutate `repos/_stack`
- reopen pass-25 command design or pass-26 evidence discipline
- widen into validation-summary, doctrine-draft, or ratchet automation
- claim that marker-checkpoint execution is implementation-ready

## Inherited Result

Pass 25 already froze:

- the exact command purpose
- exact bounded inputs and outputs
- exact non-health failure exits
- the exact no-ratchet guard
- the exact next-package rule

Pass 26 already froze:

- authoritative current marker truth from `docs/atlas-book/02-lanes-and-markers.md`
- derivative restart mirrors from `01-current-state.md`, `11-system-map-graph.md`, and `12-restart-and-handoff-guide.md`
- one optional same-story cited receipt context
- fail-closed handling for restart-surface and cited-receipt contradiction

This pass consumes those seams and freezes how the report must present that already-governed posture.

## Exact Required Success Report Fields

Every successful marker-checkpoint report must emit:

1. `command`
   - fixed identifier: `stack marker checkpoint`

2. `scope`
   - exactly one of:
     - `front-page`
     - `lane`

3. `checkpoint`
   - the exact current front-page marker table, or
   - one lane-bounded checkpoint excerpt

4. `authoritative_ref`
   - fixed path:
     - `docs/atlas-book/02-lanes-and-markers.md`

5. `context_status`
   - exactly one of:
     - `not-requested`
     - `agreed`
     - `unavailable`

6. `report_mode`
   - exactly one of:
     - `checkpoint-only`
     - `checkpoint-plus-context`

7. `supporting_refs`
   - flat list of the ATLAS restart surfaces actually used

8. `routing_note`
   - one exact next routing posture only

## Exact Optional Success Report Fields

These fields may appear only when their condition is true:

1. `lane`
   - only when `scope=lane`

2. `supporting_posture`
   - only when the requested lane posture is supportable from the authoritative marker read and agreeing restart mirrors

3. `next_package`
   - only when `context_status=agreed`
   - only when the agreeing restart mirrors already freeze one exact next package

4. `receipt_context`
   - only when `--receipt-context <relative-path>` was supplied
   - must echo the bounded relative path only

5. `context_unavailable_reason`
   - only when `context_status=unavailable`
   - must be one exact bounded reason rather than narrative smoothing

## Exact Failure Report Fields

When the command fails before a full restart-context report exists, it must emit:

1. `command`
   - fixed identifier: `stack marker checkpoint`

2. `failure_code`
   - one of:
     - `invalid-input`
     - `source-missing`
     - `source-contradiction`
     - `lane-unavailable`
     - `checkpoint-context-unavailable`

3. `failure_scope`
   - exactly one of:
     - `input`
     - `authoritative-marker`
     - `requested-lane`
     - `restart-context`

4. `message`
   - one bounded sentence only

5. `routing_note`
   - one exact next routing posture only

## Exact Conditional Partial Payload

### `checkpoint-context-unavailable`

May include:

- `checkpoint`
- `authoritative_ref`
- `supporting_refs`

only when:

- `docs/atlas-book/02-lanes-and-markers.md` is present
- the requested checkpoint is non-contradictory there
- the failure is limited to restart-context or cited-receipt disagreement or absence

May also include one bounded `contradiction_note` containing:

- `contradiction_scope`
  - `restart-surfaces`
  - `receipt-context`

- `conflicting_refs`
  - flat list only

- `summary_consequence`
  - `checkpoint-only`
  - `no-next-package`

No other failure code may emit a partial checkpoint payload.

## Exact Text Report Contract

### `checkpoint-only`

Text output must contain, in this order:

1. one exact checkpoint block
2. one refs line
   - naming `docs/atlas-book/02-lanes-and-markers.md`
   - plus any derivative restart mirrors actually used
3. one routing line

### `checkpoint-plus-context`

Text output must contain, in this order:

1. one exact checkpoint block
2. one exact context line or block
   - limited to current supporting or held posture
   - and one exact next package only when already frozen in agreeing restart mirrors
3. one refs line
4. one routing line

### `failure`

Text failure output must contain only:

1. `failure_code=<code>`
2. one bounded message line
3. one routing line

and may include the admitted partial checkpoint payload only for `checkpoint-context-unavailable`.

## Exact JSON Report Contract

### `success`

JSON success output must contain:

- `command`
- `scope`
- `checkpoint`
- `authoritative_ref`
- `context_status`
- `report_mode`
- `supporting_refs`
- `routing_note`

and only the conditionally admitted optional fields.

### `failure`

JSON failure output must contain:

- `command`
- `failure_code`
- `failure_scope`
- `message`
- `routing_note`

and only the conditionally admitted partial-checkpoint payload.

## Exact Forbidden Report Fields

The report may not emit:

- marker-ratchet claims
- deploy readiness claims
- owner-repo health claims
- publication claims
- speculative next-package wording
- multiple competing routing recommendations
- contradiction narration without cited refs
- prose that smooths unavailable context into implied certainty

## Exact Routing Note By Outcome

### `checkpoint-only`

Routing note must say only:

- `package checkpoint only and continue`

### `checkpoint-plus-context`

Routing note must say only:

- `package checkpoint plus exact restart context and continue`

### `invalid-input`

Routing note must say only:

- `fix invocation and rerun before packaging`

### `source-missing`

Routing note must say only:

- `restore required marker or restart surfaces before packaging`

### `source-contradiction`

Routing note must say only:

- `repair authoritative marker truth before packaging`

### `lane-unavailable`

Routing note must say only:

- `fix lane selection or reroute before packaging`

### `checkpoint-context-unavailable`

Routing note must say only:

- `package checkpoint only and route to one bounded restart-surface or cited-receipt reconciliation packet`

## Exact Contradiction Rule

### Authoritative marker contradiction

Counts as authoritative contradiction when:

- `docs/atlas-book/02-lanes-and-markers.md` conflicts with itself for the requested current checkpoint
- or the requested lane checkpoint cannot be read there as one exact current truth

Output:

- `failure_code=source-contradiction`
- no checkpoint payload

Routing:

- repair authoritative marker truth before packaging

### Restart-surface contradiction

Counts as restart-context contradiction when:

- `01-current-state.md`, `11-system-map-graph.md`, and `12-restart-and-handoff-guide.md` disagree on the same lane's current supporting or held posture
- or they disagree on one exact next package for the same bounded story

Output:

- `failure_code=checkpoint-context-unavailable`
- partial checkpoint payload is allowed only when authoritative marker truth is still clean

Routing:

- route to one bounded root-only restart-surface reconciliation packet

### Receipt-context contradiction

Counts as cited-receipt contradiction when:

- the cited receipt conflicts with the current agreeing restart spine
- the cited receipt belongs to an older superseded package order
- or the cited receipt itself contains multiple competing next-package statements for the same bounded story

Output:

- `failure_code=checkpoint-context-unavailable`
- partial checkpoint payload is allowed only when authoritative marker truth is still clean

Routing:

- route to one bounded root-only cited-receipt reconciliation packet

## Exact Root-Side Follow-On Packet Rule For Contradictions

When the contradiction is limited to derivative restart surfaces or one same-story cited receipt:

- root may open one bounded root-only reconciliation packet
- root must not pretend the context is still agreed

When the contradiction touches authoritative marker truth:

- root must repair `docs/atlas-book/02-lanes-and-markers.md` first
- root must not open implementation-admission or execution packets from that broken checkpoint

## Exact Out-Of-Scope Boundary

Still out of scope:

- implementation admission
- live command execution
- repo mutation
- marker ratchet automation
- proof-matrix admission
- broader marker-family expansion

## Exact Next Package

`_stack Readiness stack marker checkpoint implementation-admission and no-execution guard pass 28`

Why:

- command purpose, evidence admission, restart discipline, report shape, partial-checkpoint failure boundary, and contradiction routing are now frozen
- the next remaining docs-only ambiguity is the exact admitted implementation boundary without allowing live execution or ratchet-surface bleed

## Recommendation Type

`durable with bounded inference`

Durable because:

- this pass closes the last report-shape ambiguity left open by passes 25 and 26
- the partial-checkpoint exception stays bounded to already-frozen authoritative-versus-derivative rules

Bounded inference because:

- the exact pass-28 label is compressed from the remaining implementation-admission ambiguity by analogy to the earlier `_stack` command families

## Ratchet Decision

Ratchet:

- `_stack Readiness: 81% -> 82%`

Why:

- this pass freezes one new operator-facing report surface for the second admitted family
- the lane now has command-design, evidence-admission, and receipt-ready report-contract seams for `stack marker checkpoint`
- the move stays to the smallest honest increment because no implementation slice, no governed operator execution, and no repeatable proof loop landed for that family

## Validation Note

The inherited validation baseline for this lane was:

- `critical=0 error=3 warning=494 info=0`

Live validation at the end of this pass remained:

- `critical=0 error=3 warning=494 info=0`

## Rule

`Checkpoint-Only Fallback Must Stay Explicit`

If restart context disagrees but authoritative marker truth still holds, package the checkpoint only and route one bounded reconciliation packet instead of smoothing the contradiction into next-package prose.

## Pattern

`Authoritative Checkpoint, Fail-Closed Context`

authoritative marker checkpoint -> optional agreeing restart context -> optional same-story cited receipt -> checkpoint-only fallback on context failure -> no ratchet or implementation claim

## Failure Mode

`Pretty Checkpoint Overclaim`

If the report contract lets restart-context failure collapse into polished prose instead of an explicit checkpoint-only fallback, the helper sounds more certain than the governed marker and restart surfaces actually are.
