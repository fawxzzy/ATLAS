# AI Repetition-to-Automation Pipeline Guarded Codex Continuation Gate Prompt-Bearing Resume Command Admission Pass 22 - 2026-06-04

- Date: `2026-06-04`
- Lane: `AI Repetition-to-Automation Pipeline`
- Mode: `docs-plus-shape-admission root-bounded automation candidate`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/PLAYBOOK_NOTES.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/08-workflow-recipes.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/atlas-book/10-failure-modes-and-recovery.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-GUARDED-CODEX-CONTINUATION-GATE-RESUME-STDIN-BOUNDARY-AND-NON-INTERACTIVE-CONTRACT-PASS-21-2026-06-04.md`
  - `ops/codex/README.md`
  - `ops/codex/atlas_continue_gate.py`
  - `runtime/receipts/codex-continuation/2026-06-05/20260605T005404Z-result-20260604T180000Z-sample.decision.json`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Admit one exact prompt-bearing resume command shape for future bounded proof without widening into dash-stdin prompt injection or unattended live continuation.

This pass does not:

- run prompt-bearing live continuation
- admit dash-stdin prompt injection
- admit wrapper-fed multiline prompt payloads
- widen beyond the guarded continuation lane

## Root Health Baseline

- latest durable validation receipt remains `critical=0 error=3 warning=498 info=0`
- the `3` errors still classify as expected in-flight `_stack` `stack.lock.yaml` dirty-state drift
- Pass 21 already proved the CLI exposes prompt-bearing resume surfaces
- Pass 21 already proved the current blocker belongs to the currently admitted promptless command shape

## Prompt-Bearing Command Admission Decision

### Exact shape admitted now

- the guarded continuation gate now admits one additional prompt-bearing live command shape:
  - `codex exec resume --last <inline-prompt>`
- exact boundaries:
  - executable must still resolve to the admitted Codex executable family
  - suffix must still be `exec resume --last`
  - one and only one prompt argument may follow `--last`
  - that prompt argument must be non-empty

### Exact shape still deferred

- the following remains unadmitted:
  - `codex exec resume --last -`
- reason:
  - dash-stdin prompt injection introduces a separate prompt-source and wrapper-coupling question
  - that surface is visible in CLI help but is not yet frozen with one exact governed source boundary

### Honest blocker posture now

- `resume_requires_stdin_prompt` still remains historically true for the currently admitted promptless shape:
  - `codex exec resume --last`
- that blocker no longer prevents ATLAS from admitting one narrower prompt-bearing variant
- the next honest question is no longer command admission
- the next honest question is bounded execution proof for the newly admitted inline-prompt shape

## Implementation Landed

### `ops/codex/atlas_continue_gate.py`

- widened admitted command parsing from:
  - promptless `codex exec resume --last`
  - to also include one exact inline-prompt variant
- added exact command-shape classification:
  - `promptless_resume_last`
  - `inline_prompt_resume_last`
- dry-run and blocked execution receipts now expose the admitted command shape
- dash-stdin prompt injection now fails closed with an exact admission-boundary message
- widened self-test coverage for:
  - inline prompt-bearing admission
  - dash-stdin rejection

### `ops/codex/README.md`

- documented the new inline-prompt admission and the continued dash-stdin deferral

## Verification

- `python ops/codex/atlas_continue_gate.py --self-test`
  - `21/21 passed`
- `python ops/codex/atlas_continue_gate.py --write-synthetic-jsonl tmp/scratch/atlas_continue_gate.pass22-inline-prompt.jsonl --execute-command "codex exec resume --last continue" --preview`
  - gate decision: `continue`
  - execution status: `skipped`
  - execution command shape: `inline_prompt_resume_last`
  - dry-run kept execution disabled
- `python ops/codex/atlas_continue_gate.py --write-synthetic-jsonl tmp/scratch/atlas_continue_gate.pass22-dash-stdin.jsonl --execute-command "codex exec resume --last -" --preview`
  - gate decision: `continue`
  - execution status: `blocked`
  - execution classification: `non_resume_command_shape`
  - exact boundary: dash-stdin prompt injection is still not admitted
- `python ops/validation/validate_stack.py`
  - `critical=0 error=3 warning=498 info=0`
  - the `3` errors still match the expected in-flight `_stack` `stack.lock.yaml` dirty-state drift

## Generated Runtime Receipt Paths

- `tmp/scratch/atlas_continue_gate.pass22-inline-prompt.jsonl`
- `tmp/scratch/atlas_continue_gate.pass22-dash-stdin.jsonl`
- `runtime/receipts/codex-continuation/2026-06-05/20260605T005404Z-result-20260604T180000Z-sample.decision.json`
- `runtime/receipts/codex-continuation/2026-06-05/20260605T005404Z-result-20260604T180000Z-sample.decision.md`

## Exact Next Package

- `AI Repetition-to-Automation Pipeline Guarded Codex Continuation Gate Inline-Prompt Resume Execution Proof Pass 23`

Why:

- command admission is now frozen
- dash-stdin remains intentionally deferred
- the next bounded question is whether the exact inline-prompt shape can execute cleanly under the existing wrapper-bound guardrails

## Marker Decision

- `AI Repetition-to-Automation Pipeline: none`

Why:

- this pass admits a narrower command shape only
- no blocker was cleared
- no repeatable governed execution proof widened

## Rule

`Inline Prompt First, Dash-stdin Later`

When the resume family exposes multiple prompt-bearing surfaces, admit the smallest explicit inline prompt shape first and keep stdin-fed prompt injection deferred until its source boundary is frozen separately.

## Pattern

`Help Contract -> Inline Prompt Admission -> Execution Proof`

prove prompt support -> admit one exact inline prompt shape -> defer dash-stdin -> run one bounded execution proof only after that

## Failure Mode

`Prompt-Source Collapsing`

If ATLAS treats inline arguments and dash-stdin as the same admission event, the guarded lane loses control of prompt provenance and silently widens into a more ambiguous execution surface than the receipt claimed.

## What This Pass Proves

This pass proves:

- one exact inline-prompt resume shape is now admitted
- dry-run can recognize and classify that admitted shape
- dash-stdin prompt injection still fails closed
- the next honest packet is inline-prompt execution proof

This pass does not prove:

- that inline-prompt live execution succeeds
- that dash-stdin prompt injection is safe
- that unattended continuation is now allowed
