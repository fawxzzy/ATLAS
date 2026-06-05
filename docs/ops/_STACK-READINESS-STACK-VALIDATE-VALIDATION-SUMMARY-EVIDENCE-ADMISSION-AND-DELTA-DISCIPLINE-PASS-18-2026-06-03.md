# _Stack Readiness Stack Validate Validation-Summary Evidence-Admission And Delta-Discipline Pass 18 - 2026-06-03

- Date: `2026-06-03`
- Lane: `_stack Readiness stack validate validation-summary evidence-admission and delta-discipline pass 18`
- Mode: `docs-only root-bounded evidence-admission and delta-discipline design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/ops/_STACK-READINESS-STACK-VALIDATE-VALIDATION-SUMMARY-COMMAND-DESIGN-PASS-17-2026-06-03.md`
  - `docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-VALIDATION-SUMMARY-AND-DELTA-REPORTING-CONTRACT-FREEZE-PASS-3-2026-06-03.md`
  - `docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-VALIDATION-SUMMARY-OWNER-SURFACE-ADMISSION-PASS-4-2026-06-03.md`
  - `docs/ops/_STACK-READINESS-STACK-VERCEL-HEALTH-EVIDENCE-ADMISSION-AND-FRESHNESS-PASS-10-2026-05-29.md`
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

Freeze one compact authoritative evidence-admission and delta-discipline spine for `_stack` `stack validate` validation-summary work.

This pass does not:

- implement or run a `_stack` command
- mutate `repos/_stack`
- reopen the pass-4 owner-surface admission
- widen into marker-checkpoint or receipt-draft automation
- claim that baseline history is already durably available for every future delta request

## Inherited Command-Design Result

Pass 17 already froze:

- the exact command purpose
- the exact in-scope current validation surfaces
- the exact bounded inputs and outputs
- the exact non-health failure exits
- the exact no-mutation guard
- the exact count-only delta ceiling

This pass consumes that command seam and freezes:

- which current snapshot surfaces are authoritative
- which baseline receipt shapes are admitted for `--delta-from`
- how missing or contradictory baseline truth must fail closed

## Exact Current Snapshot Evidence

The future command must derive the current summary only from the paired latest validation artifacts:

- `runtime/receipts/validation/stack-validation.latest.md`
- `runtime/receipts/validation/stack-validation.latest.json`

The authoritative current snapshot is the exact shared count tuple:

- `critical=<n> error=<n> warning=<n> info=<n>`

Current book mirrors, lane receipts, and restart surfaces may cite that tuple after the command runs, but they may not replace the paired artifacts as the current source of truth.

## Exact Admitted Baseline Classes For `--delta-from`

### 1. `durable validation-summary family receipt`

Admitted when the cited receipt:

- is a durable receipt path
- belongs to the same bounded validation-summary closeout or comparison story
- contains one exact historical validator count tuple in the same four-count shape
- cites or clearly owns that baseline tuple rather than narrating only qualitative drift

Use:

- primary baseline for delta wording
- durable comparison surface for closeout narration

### 2. `durable validator-snapshot receipt mirror`

Admitted only when the cited receipt path directly preserves one historical validator snapshot with:

- one exact four-count tuple
- one explicit reference to the validator snapshot surface it came from
- no conflicting alternate tuple inside the same receipt path

Use:

- bounded fallback baseline when the baseline is preserved as a validator-snapshot receipt rather than a broader closeout receipt

## Exact Forbidden Baseline Classes

Forbidden for `--delta-from`:

- chat recap
- uncited narrative summaries
- marker prose without an exact four-count tuple
- debt-class-only summaries without the exact four-count tuple
- receipts from a different closeout story
- current restart mirrors standing in for historical baseline
- arbitrary owner-repo notes or unpublished drafts

## Exact Baseline Sufficiency Rule

One baseline is sufficient only when all of these are true:

- exactly one cited receipt path is provided
- the receipt contains one exact four-count tuple
- the tuple is attributable to one bounded historical validator snapshot
- the baseline belongs to the same bounded validation-summary story the command is summarizing

If any one of those is false, delta wording is unavailable.

## Exact Delta Discipline Rule

If `--delta-from` is admitted, delta wording may report only:

- `critical`
- `error`
- `warning`
- `info`

and only as exact count change from baseline to current snapshot.

The command may not:

- infer root cause for the delta
- restate debt-class interpretation as delta truth
- promote improvement or deterioration language beyond the exact count change
- compare against multiple baselines in one run

## Exact Contradiction Handling

### `current artifact contradiction`

If `stack-validation.latest.md` and `stack-validation.latest.json` disagree on any one of the four counts:

- fail with `artifact-contradiction`
- emit no summary snapshot
- emit no delta wording

### `baseline contradiction`

If the cited baseline receipt contains:

- multiple competing four-count tuples for the same claimed baseline
- a tuple that contradicts its own cited baseline snapshot
- ambiguous baseline ownership inside the requested comparison story

then:

- fail with `artifact-contradiction`
- emit no delta wording

### `baseline unavailable`

If the cited receipt path is missing, off-story, or lacks one exact attributable tuple:

- fail with `delta-baseline-unavailable`
- emit the current snapshot only if the current paired artifacts are non-contradictory

## Exact Output Strength Rules

### `current snapshot only`

Emit the final snapshot plus paired artifact references when:

- current paired artifacts are present
- current paired artifacts agree
- no admitted baseline is requested or available

### `snapshot plus delta`

Emit snapshot plus delta only when:

- current paired artifacts agree
- one admitted baseline receipt is available
- the baseline is exact, attributable, and same-story

### `fail closed`

Do not emit narrative smoothing such as:

- `roughly unchanged`
- `improved posture`
- `slightly worse`

unless the exact count delta has already been computed from admitted baseline truth.

## Exact Validation Note For This Pass

Live validation at the end of this pass was:

- `critical=0 error=0 warning=494 info=0`

This pass treats that live snapshot as:

- the current authoritative tuple for command-design purposes
- not an admitted historical baseline for future delta wording by itself unless later preserved through an admitted receipt path

## Exact Next Package

`_stack Readiness stack validate validation-summary report-contract and contradiction-routing pass 19`

Why:

- command purpose, inputs, outputs, no-mutation guard, current evidence, admitted baseline shapes, contradiction handling, and count-only delta discipline are now frozen
- the next remaining docs-only ambiguity is the exact receipt-ready report contract and contradiction-routing presentation shape

## Recommendation Type

`durable with bounded inference`

Durable because:

- this pass closes the remaining evidence-admission and baseline-discipline ambiguity left open by pass 17
- the admitted baseline rule is now narrow enough to keep `_stack` summary wording fail-closed

Bounded inference because:

- pass 19 is compressed from the remaining report-contract ambiguity by analogy to the earlier `_stack` `stack vercel-health` sequence

## Ratchet Decision

Ratchet:

- `_stack Readiness: 71% -> 72%`

Why:

- this pass materially reduces one real ambiguity class by freezing current-evidence authority, admitted baseline receipt shapes, and fail-closed contradiction behavior for validation-summary work
- the move stays to the smallest honest increment because no implementation, no governed operator execution, and no repeatable proof loop landed

## Rule

`Delta Needs One Exact Baseline`

Count-delta reporting is allowed only when one cited durable baseline carries one exact attributable validator tuple from the same bounded story.

## Pattern

`Receipt-Cited Count Delta`

current paired artifacts -> one cited durable baseline receipt -> exact four-count comparison -> fail closed on contradiction or ambiguity

## Failure Mode

`Narrative Delta Drift`

If validation-summary delta wording is allowed to lean on recap prose, debt-class narration, or multiple ambiguous historical counts, the command sounds precise while the baseline truth is not actually governed.
