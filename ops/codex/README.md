# Codex On Windows Wrapper

This directory provides the explicit wrapper strategy for running Codex from ATLAS on Windows without native Codex hooks.

## Current Tool

- `run_scoped_task.ps1`
- `commit_stack_repos.ps1`
- `commit_dirty_repos.ps1` (legacy alias)

The wrapper is intentionally simple:

1. emit `session_start`
2. emit `task_start`
3. emit `pre_command`
4. run the explicit Codex command
5. emit `post_command`
6. optionally run validation and emit `validation_complete`
7. optionally emit `export_complete`
8. emit `session_stop`

## What This Solves Today

- explicit receipts under `runtime/receipts/events/`
- repeatable stack-owned lifecycle logging
- no hidden background process
- no dependency on native hooks
- no dependency on one AI vendor

## Important Limit

The wrapper can only observe commands that it launches itself. It cannot see internal tool calls made inside Codex unless a future native hook surface exists.

That is acceptable for the current phase because the contract is receipts-first and inspectable.

## Example Usage

Run a scoped Codex task from the ATLAS root:

```powershell
powershell -ExecutionPolicy Bypass -File ops/codex/run_scoped_task.ps1 `
  -TaskName atlas-event-contract `
  -TaskSummary "Build the vendor-neutral ATLAS event system." `
  -Workspace . `
  -ScopePaths docs/architecture,ops/events,ops/validation,docs/playbooks,data/imports/playbooks `
  -RepoIds stack `
  -MutationMode stack_only `
  -CodexCommand codex,'--cwd','.' `
  -ValidationCommand python,'ops/validation/validate_event_contracts.py'
```

Use the event invoker directly from PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File ops/events/invoke_event.ps1 `
  -PayloadFile tmp/scratch/example-event.json `
  -EventType session_start `
  -SkipHandler
```

Use the event invoker directly from Python:

```powershell
python ops/events/invoke_event.py --payload-file tmp/scratch/example-event.json --skip-handler
```

## Recommended Workflow

1. keep the wrapper scope explicit
2. keep scope paths ATLAS-relative
3. run validators explicitly
4. inspect receipts after each run
5. add future adapters by mapping them into the same event contract

## Multi-Repo Commit Helper

Use `commit_stack_repos.ps1` from the ATLAS root when you need to commit dirty registered repos without opening each repo separately.

It reads `stack.yaml`, checks each eligible repo independently, and commits each dirty child repo with its own git history. The ATLAS root control repo is separate and stays opt-in unless you pass `-IncludeRoot` or target `stack`.

Dry-run example:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\commit_stack_repos.ps1 -DryRun
```

Target only named repos and include the root control repo:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\commit_stack_repos.ps1 `
  -IncludeRoot `
  -RepoIds mazer,fitness `
  -CommitMessage "chore: sync local updates" `
  -CommitMessagePrefix "[atlas] " `
  -CommitMessageSuffix " root-orchestrated"
```

The older `commit_dirty_repos.ps1` surface remains available for compatibility, but the stack-aware helper is the preferred command.
