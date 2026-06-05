# AI Repetition-to-Automation Pipeline Guarded Codex Continuation Gate Non-Packaged Runtime Surface Proof Pass 19 - 2026-06-04

- Date: `2026-06-04`
- Lane: `AI Repetition-to-Automation Pipeline`
- Mode: `docs-plus-runtime-surface-proof root-bounded automation candidate`
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
  - `docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-GUARDED-CODEX-CONTINUATION-GATE-WINDOWS-CODEX-RUNTIME-AVAILABILITY-BOUNDARY-PASS-18-2026-06-04.md`
  - `ops/codex/README.md`
  - `ops/codex/atlas_continue_gate.py`
  - `runtime/receipts/codex-continuation/2026-06-04/20260604T224216Z-result-20260604T180000Z-sample.decision.json`
  - `runtime/receipts/codex-continuation/2026-06-04/20260604T235233Z-result-20260604T180000Z-sample.decision.json`
- Control-plane checkpoint: `main`

## Objective

Preserve the historical packaged WindowsApps blocker while proving the active Codex runtime surface has materially changed to a non-packaged launchable CLI.

This pass does not:

- admit live unattended continuation
- reopen the historical packaged blocker ladder as if nothing changed
- run an unbounded `codex exec resume --last` loop
- claim that one clean `codex --version` check is the same as governed live resume proof
- widen into doctrine, deploy, publication, destructive cleanup, or held-lane reopening

## Root Health Baseline

- latest durable validation posture before this pass was `critical=0 error=3 warning=498 info=0`
- the `3` errors remain classified as expected in-flight `_stack` `stack.lock.yaml` dirty-state drift
- Pass 17 already froze the exact live command family as the real `codex exec resume --last`
- Pass 18 already froze the historical packaged WindowsApps blocker as `windowsapps_packaged_codex_start_access_denied`
- the two-strike blocker stop for that packaged blocker class remains valid; this pass reopens only because the executable/runtime surface materially changed

## Runtime Surface Proof Decision

### Historical blocker that remains durable

- the packaged WindowsApps Codex surface remains historically recorded as:
  - `windowsapps_packaged_codex_start_access_denied`
- that classification still means:
  - the earlier real resume command shape was correct
  - the packaged executable path resolved
  - the packaged host-runtime start seam blocked on this machine

### What materially changed now

- `npm install -g @openai/codex` created a non-packaged CLI surface in the user-scoped npm bin:
  - `%APPDATA%\npm\codex*` on this host
- `Get-Command codex -All` now resolves the npm-backed surfaces before WindowsApps
- `where.exe codex` now lists the npm-backed surfaces before WindowsApps
- `codex --version` now starts cleanly as:
  - `codex-cli 0.137.0`
- the guarded continuation gate now has one bounded runtime-surface probe seam that can classify the active surface without attempting live continuation

### Exact active runtime-surface classification admitted now

- the active runtime surface is now frozen as:
  - `non_packaged_npm_codex_launchable`
- the exact resolved executable family in the probe receipt is:
  - the user-scoped npm `codex.CMD` shim
- lower-priority WindowsApps entries still remain visible in command resolution order
- that means:
  - the historical packaged blocker stays preserved
  - the active shell/runtime surface is now a different executable family
  - the new surface launches cleanly for version proof
  - live continuation is still a separate later question

## Implementation Landed

### `ops/codex/atlas_continue_gate.py`

- added one bounded runtime-surface probe path:
  - `--probe-runtime-surface`
- added one explicit runtime-executable selector:
  - `--runtime-executable`
- added command-order capture through `where.exe`
- added npm-global-prefix resolution through the resolved npm executable path
- added runtime-surface classification for changed executable order:
  - `non_packaged_npm_codex_launchable`
  - `non_packaged_codex_launchable`
  - retained historical blocked start classifications including `windowsapps_packaged_codex_start_access_denied`
- updated decision receipts and preview output to surface:
  - runtime-surface classification
  - resolved executable
  - version status/output
  - lower-priority WindowsApps presence

### `ops/codex/README.md`

- documented bounded runtime-surface proof capture as a current admitted mode

## Verification

- `Get-Command codex -All | Format-List Name,CommandType,Source,Version`
  - npm-backed surfaces resolve first:
    - `%APPDATA%\npm\codex.ps1`
    - `%APPDATA%\npm\codex.cmd`
    - `%APPDATA%\npm\codex`
  - WindowsApps surfaces remain present later:
    - `C:/Program Files/WindowsApps/OpenAI.Codex_26.601.2237.0_x64__2p2nqsd0c76g0/app/resources/codex.exe`
    - `C:/Program Files/WindowsApps/OpenAI.Codex_26.601.2237.0_x64__2p2nqsd0c76g0/app/resources/codex`
- `where.exe codex`
  - npm-backed command order now leads:
    - `%APPDATA%\npm\codex`
    - `%APPDATA%\npm\codex.cmd`
  - WindowsApps remains only as lower-priority fallback:
    - `C:/Program Files/WindowsApps/OpenAI.Codex_26.601.2237.0_x64__2p2nqsd0c76g0/app/resources/codex`
    - `C:/Program Files/WindowsApps/OpenAI.Codex_26.601.2237.0_x64__2p2nqsd0c76g0/app/resources/codex.exe`
- `codex --version`
  - `codex-cli 0.137.0`
- `python ops/codex/atlas_continue_gate.py --self-test`
  - `15/15 passed`
  - includes non-packaged npm launchable classification proof
- `python ops/codex/atlas_continue_gate.py --write-synthetic-jsonl tmp/scratch/atlas_continue_gate.pass19-non-packaged-runtime.jsonl --probe-runtime-surface --preview`
  - gate decision: `continue`
  - runtime surface classification: `non_packaged_npm_codex_launchable`
  - resolved executable family: the user-scoped npm `codex.CMD` shim
  - runtime version output: `codex-cli 0.137.0`
  - next move remains bounded to Pass 20

## Generated Runtime Receipt Paths

- `tmp/scratch/atlas_continue_gate.pass19-non-packaged-runtime.jsonl`
- `runtime/receipts/codex-continuation/2026-06-04/20260604T235233Z-result-20260604T180000Z-sample.decision.json`
- `runtime/receipts/codex-continuation/2026-06-04/20260604T235233Z-result-20260604T180000Z-sample.decision.md`

## Exact Next Package

- `AI Repetition-to-Automation Pipeline Guarded Codex Continuation Gate Non-Packaged Bounded Resume Execution Proof Pass 20`

Why:

- the changed runtime surface is now durably proven
- live unattended continuation still remains blocked by policy
- the next honest question is whether one explicitly enabled, wrapper-bound, exact real resume execution can run through the newly active non-packaged surface without widening scope

## Marker Decision

- `none`

Why:

- this pass proves runtime availability on a changed surface, not repeatable governed operator proof
- safe fallback and live bounded resume behavior are still separate later questions

## Rule

`Changed Runtime Surface Requires Runtime-Surface Proof Before Live Resume`

After a guarded continuation ladder is closed for one blocker class, a materially changed executable/runtime surface must first land one narrower runtime-surface proof receipt before any new live resume proof is honest.

## Pattern

`Historical Blocker -> Changed Executable Order -> Runtime-Surface Proof -> Later Live Resume Proof`

preserve historical blocker truth -> prove the new active executable order and clean version start -> keep live continuation blocked by default -> only then consider one bounded live resume proof

## Failure Mode

`Changed-Surface Skip-Ahead Drift`

If a new Codex runtime surface appears and root jumps straight into live continuation without first freezing the changed-surface proof, the lane loses the durable contrast between the historical blocker and the newly admitted active surface.

## What This Pass Proves

This pass proves:

- the historical WindowsApps blocker remains durable and preserved
- the active Codex runtime surface is now non-packaged and npm-backed
- the active surface launches cleanly for bounded version proof
- WindowsApps entries still exist only as lower-priority command candidates
- the guarded continuation gate can classify changed runtime surfaces without widening into live continuation

This pass does not prove:

- that the real `codex exec resume --last` command now runs safely end to end on the new surface
- that unattended continuation is admitted
- that `AI Repetition-to-Automation Pipeline` should move above `30%`
