# Workstation Resource Hygiene Baseline And Codex QALLL Closeout Contract Pass 1 - 2026-06-11

- Date: `2026-06-11`
- Owner: `ATLAS root`
- Mode: `docs-first support lane with one read-only helper`
- Scope: `classify local CPU/GPU and process-residue pressure as a bounded supporting safety lane, land one read-only Windows snapshot helper, and freeze the Codex/QALLL process-closeout contract without mutating owner repos or protected surfaces`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/NEAR-100-MARKER-CLOSEOUT-SELECTOR-AND-ROOT-CLEANUP-PRESERVATION-PASS-1-2026-06-09.md`
  - `runtime/receipts/validation/stack-validation.latest.json`

## Objective

1. Admit `Workstation Resource Hygiene` as a real supporting marker rather than an informal chat-only concern.
2. Freeze the one-hot-chat operating rule and the required process-closeout report for Codex/QALLL lanes that run local services or automation.
3. Add one read-only local helper that can summarize likely workflow processes without killing anything or writing committed logs.

## Current Root Checks

### Repo and parity

- `git fetch origin main` completed cleanly.
- `git rev-list --left-right --count origin/main...HEAD` returned `0 0`.
- `git log -1 --oneline --decorate` matched `03348891 (HEAD -> main, origin/main) Close AI batch child path readiness`.

### Local residue left untouched

- unrelated root-level screenshots and capture artifacts remain untracked
- `.playwright-mcp/` remains untracked
- `archive/` remains untracked and protected

### Protected surfaces preserved

- `repos/fawxzzy-fitness`
- `archive/`
- `.vercel`
- `.env`
- `secrets/`
- deployment surfaces

## Problem Classification

The main failure mode is not simply "two chats exist."

The higher-risk class is lingering local process residue after a chat is archived or restarted:

- dev servers
- test watchers
- Playwright or browser automation sessions
- screenshot-heavy preview tabs
- validators
- local helper loops

That residue can degrade Codex responsiveness, browser inspection reliability, local validation speed, and closeout discipline across otherwise separate lanes.

## Operating Rule

Starting from this pass:

- only one Codex chat may be `hot` at a time
- `hot` means commands, browser automation, tests, dev servers, screenshots, or validation are actively running
- another Codex chat may remain open only if it is idle

This is a supporting safety rule. It does not compete with the current main product lane, and it does not move the immediate ATLAS control-plane packet away from `AI Long-Run Batch Orchestration`.

## Codex QALLL Closeout Contract

Any Codex chat that runs dev servers, Playwright, browser automation, screenshots, tests, validators, or other long-running local helpers must close with:

- `Processes started:`
- `Processes still running:`
- `Dev server status:`
- `Browser/Playwright status:`
- `Watch/test status:`
- `Stop commands run:`
- `Anything left intentionally running:`
- `Should the next chat inherit or restart local services:`

The contract is a reporting requirement, not an automatic-kill policy.

## Read-Only Helper

New helper:

- `ops/atlas/workstation_resource_snapshot.ps1`

Helper guarantees:

- Windows-focused
- read-only
- no process termination
- no secret inspection
- no committed machine-private logs by default
- optional process-path output only when `-IncludePath` is explicitly requested

Default helper coverage:

- top CPU processes
- top memory processes
- common workflow processes by name:
  - `node`
  - `python`
  - `pwsh`
  - `powershell`
  - `Code`
  - `codex`
  - `chrome`
  - `msedge`
  - `chromium`
  - `playwright`
  - `npm`
  - `vite`
  - `next`

## Marker Decision

- `Workstation Resource Hygiene` is now admitted at `10%`
- `AI Long-Run Batch Orchestration` stays at `25%` in the active marker table
- `_stack Readiness` stays at `100%`
- `AI Repetition-to-Automation Pipeline` stays at `32%`

Why `10%` is honest:

- one durable root receipt now defines the lane
- one read-only helper now exists
- one durable closeout contract now exists in restart surfaces
- validation stayed green

Why the lane stays low:

- no repeated relief cycle is proven yet
- no cross-lane adoption proof exists yet beyond the contract landing
- no CPU/GPU reduction proof is claimed from this first baseline alone

## Exact Next Admissible Move

- resume `AI Long-Run Batch Orchestration queue-or-registry runtime-state child-path or artifact-shape selection first-implementation worker packet 1` only under the one-hot-chat rule
- or run a separate near-100 selector pass if the operator chooses closeout-first instead of current-lane continuation

## Verification

Commands:

- `git status -sb`
- `git fetch origin main`
- `git rev-list --left-right --count origin/main...HEAD`
- `git log -1 --oneline --decorate`
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\atlas\workstation_resource_snapshot.ps1 -WorkflowOnly`
- `python .\ops\validation\validate_stack.py --ratchet`

Result:

- helper executed as a safe read-only dry run
- stack validation remained `critical=0 error=0 warning=52 info=0`
