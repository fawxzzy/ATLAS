# AI Repetition-to-Automation Pipeline Guarded Codex Continuation Gate Resume-Stdin Boundary And Non-Interactive Contract Pass 21 - 2026-06-04

- Date: `2026-06-04`
- Lane: `AI Repetition-to-Automation Pipeline`
- Mode: `docs-plus-help-contract root-bounded automation candidate`
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
  - `docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-GUARDED-CODEX-CONTINUATION-GATE-NON-PACKAGED-BOUNDED-RESUME-EXECUTION-PROOF-PASS-20-2026-06-04.md`
  - `ops/codex/README.md`
  - `ops/codex/atlas_continue_gate.py`
  - `runtime/receipts/codex-continuation/2026-06-05/20260605T003825Z-result-20260604T180000Z-sample.decision.json`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Freeze the exact meaning of `resume_requires_stdin_prompt` so ATLAS does not confuse a promptless admitted command shape with a missing CLI capability.

This pass does not:

- admit prompt-bearing live continuation
- inject wrapper-fed stdin into live resume by implication
- widen beyond the guarded continuation lane
- claim unattended continuation is now viable

## Root Health Baseline

- latest durable validation receipt remains `critical=0 error=3 warning=498 info=0`
- the `3` errors still classify as expected in-flight `_stack` `stack.lock.yaml` dirty-state drift
- Pass 20 already proved the exact admitted command launches through the active non-packaged npm Codex surface
- Pass 20 already froze the current execution blocker as `resume_requires_stdin_prompt`

## Resume Contract Decision

### What Pass 20 did and did not prove

- Pass 20 proved the active launch surface is no longer the blocker
- Pass 20 did not prove that Codex lacks any non-interactive resume surface
- the stderr only proved that the current admitted command shape:
  - `codex exec resume --last`
  - starts without any prompt payload and therefore falls through to stdin expectation

### What the CLI contract now proves

- `codex exec resume --help` now shows:
  - `Usage: codex exec resume [OPTIONS] [SESSION_ID] [PROMPT]`
  - prompt argument support exists on the resume command family
  - `If \`-\` is used, read from stdin` is explicitly documented for the prompt surface
- the guarded continuation gate now freezes that help-driven contract as:
  - `resume_prompt_arg_and_stdin_dash_supported`

### Honest blocker posture now

- the current admitted live command remains:
  - `codex exec resume --last`
- that admitted shape still omits a prompt argument
- therefore `resume_requires_stdin_prompt` is now frozen as:
  - a command-shape boundary on the currently admitted live command
  - not proof that the CLI lacks prompt-bearing or dash-stdin non-interactive resume surfaces

That means:

- the exact bare resume command should not be retried blindly
- prompt-bearing variants are visible in the CLI contract
- prompt-bearing variants are still unadmitted until ATLAS freezes one safe exact shape, prompt source, and proof boundary

## Implementation Landed

### `ops/codex/atlas_continue_gate.py`

- added one bounded help-driven resume-contract probe:
  - `--probe-resume-contract`
- the probe records:
  - resolved executable
  - launch mode
  - resume usage lines
  - prompt-argument support
  - dash-stdin support
  - the current admitted-command gap
- widened self-test coverage for:
  - resume help parsing
  - prompt-bearing dash-stdin contract classification

### `ops/codex/README.md`

- documented bounded resume-contract proof capture as an admitted gate mode

## Verification

- `python ops/codex/atlas_continue_gate.py --self-test`
  - `19/19 passed`
- `codex exec resume --help`
  - shows `Usage: codex exec resume [OPTIONS] [SESSION_ID] [PROMPT]`
  - shows `If \`-\` is used, read from stdin`
- `python ops/codex/atlas_continue_gate.py --write-synthetic-jsonl tmp/scratch/atlas_continue_gate.pass21-resume-contract.jsonl --probe-resume-contract --preview`
  - gate decision: `continue`
  - resume contract classification: `resume_prompt_arg_and_stdin_dash_supported`
  - current admitted command omits prompt: `true`
  - next move remains bounded to Pass 22
- `python ops/validation/validate_stack.py`
  - `critical=0 error=3 warning=498 info=0`
  - the `3` errors still match the expected in-flight `_stack` `stack.lock.yaml` dirty-state drift

## Generated Runtime Receipt Paths

- `tmp/scratch/atlas_continue_gate.pass21-resume-contract.jsonl`
- `runtime/receipts/codex-continuation/2026-06-05/20260605T003825Z-result-20260604T180000Z-sample.decision.json`
- `runtime/receipts/codex-continuation/2026-06-05/20260605T003825Z-result-20260604T180000Z-sample.decision.md`

## Exact Next Package

- `AI Repetition-to-Automation Pipeline Guarded Codex Continuation Gate Prompt-Bearing Resume Command Admission Pass 22`

Why:

- the CLI contract now proves prompt-bearing resume surfaces exist
- the active blocker is no longer whether those surfaces exist
- the next bounded question is whether one exact prompt-bearing variant can be admitted safely without widening into blind live continuation

## Marker Decision

- `AI Repetition-to-Automation Pipeline: none`

Why:

- this pass freezes a contract seam only
- no blocker was cleared
- no repeatable governed execution proof widened

## Rule

`Help-Surface Proof Does Not Auto-Admit Prompt Injection`

When CLI help proves a prompt-bearing resume surface exists, freeze that contract first and route next into exact command admission instead of injecting prompt text into live continuation by implication.

## Pattern

`stderr Boundary -> Help Contract Probe -> Prompt-Bearing Admission Packet`

freeze the stderr blocker -> prove the help surface -> hold live prompt execution closed -> admit one exact prompt-bearing variant only in the next bounded packet

## Failure Mode

`Prompt-Surface Overreach Drift`

If ATLAS treats help text alone as permission to run prompt-bearing live continuation, the guarded lane silently widens from contract proof into execution without freezing prompt source, safe fallback, or exact command shape.

## What This Pass Proves

This pass proves:

- the resume command family exposes `[PROMPT]`
- the resume command family documents `-` stdin prompt support
- the current blocker `resume_requires_stdin_prompt` belongs to the currently admitted promptless command shape
- the next honest packet is prompt-bearing command admission rather than another bare-command retry

This pass does not prove:

- that any prompt-bearing live resume shape is yet admitted
- that wrapper-fed stdin is already safe
- that unattended continuation is now allowed
