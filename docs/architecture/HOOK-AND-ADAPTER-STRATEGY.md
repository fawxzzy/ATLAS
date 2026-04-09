# Hook And Adapter Strategy

This document describes how ATLAS uses wrappers now and how future adapters plug into the same event contract later.

## Current Rule

ATLAS does not assume native Codex hooks on Windows today.

The approved near-term strategy is:

1. explicit wrapper scripts launch visible work
2. wrapper-visible lifecycle events are emitted through `ops/events/invoke_event.py`
3. receipts are written to `runtime/receipts/events/`
4. humans inspect receipts and reports

No daemon, background watcher, or fake autonomous orchestrator is introduced.

## Adapter Layers

### Layer 1: Wrapper execution now

Active now.

Primary tool:

- `ops/codex/run_scoped_task.ps1`

Responsibilities:

- create `session_start` and `task_start`
- emit `pre_command` before the wrapped Codex command
- emit `post_command` after the wrapped Codex command finishes
- optionally emit `validation_complete`
- optionally emit `export_complete`
- always emit `session_stop`

Limit:

- this wrapper only sees commands that it launches itself
- it does not observe internal Codex tool calls

### Layer 2: Native Codex hooks later

Planned later.

Native hooks should become a thin adapter that maps hook callback data into the same ATLAS event envelope. Native hooks must not invent a separate receipt format.

Expected mapping:

| Native signal | ATLAS event |
| --- | --- |
| session created | `session_start` |
| task accepted | `task_start` |
| tool command about to run | `pre_command` |
| tool command completed | `post_command` |
| validator step completed | `validation_complete` |
| export step completed | `export_complete` |
| session ended | `session_stop` |

Adapter rule:

- native hook code translates data into ATLAS JSON
- native hook code calls the same ATLAS invoker or an API-compatible future service
- ATLAS remains the contract owner

### Layer 3: Git hooks

Allowed later when explicit.

Use cases:

- pre-commit validation receipts
- pre-push validation receipts
- post-merge stack refresh receipts

Git hooks should emit:

- `pre_command` and `post_command` for the Git-managed command they wrap
- `validation_complete` when hook validation runs

Git hooks must stay opt-in and repo-scoped. They must not mutate unrelated repos from the root.

### Layer 4: CI pipelines

Allowed later.

Use cases:

- run stack validators in CI
- validate playbook catalog normalization
- publish export receipts

CI should emit the same event contract with `producer.kind = "ci"`.

### Layer 5: Future CORTEX service

Advisory later, not active now.

Future CORTEX responsibilities:

- read retained receipts
- correlate them across sessions
- rank next tasks
- emit proposed handoff manifests

Future CORTEX should not replace the contract. It should consume and eventually relay the same ATLAS event model.

## Handler Strategy

ATLAS event handlers are vendor-neutral scripts that live under `ops/events/handlers/`.

Current handler model:

- event ingestion validates the payload first
- the invoker looks for `ops/events/handlers/<event_type>.py`
- if that does not exist, it looks for `ops/events/handlers/<event_type>.ps1`
- if no handler exists, the event is still accepted and a receipt is written with `handler.status = "skipped"`

This keeps the contract usable before any specialized handlers exist.

## Why Receipts First

Receipts are the safe compatibility layer because they are:

- explicit
- inspectable
- replayable
- portable across wrapper types
- usable by future CORTEX without hidden state

## Adapter Contract Rules

Every current and future adapter must follow these rules:

1. Do not write stack truth into tool-specific hidden config.
2. Do not require a background process to make the event system work.
3. Do not assume a single AI vendor.
4. Do not unpack third-party playbooks into `repos/cortex`.
5. Do not bypass ATLAS receipts with proprietary side channels.

## Today On Windows

Use `ops/codex/run_scoped_task.ps1` when a human wants explicit, inspectable Codex task execution from the stack root.

Use `ops/events/invoke_event.ps1` or `python ops/events/invoke_event.py` when another stack script needs to emit lifecycle receipts without depending on Codex at all.
