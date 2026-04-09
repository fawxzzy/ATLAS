# ATLAS Event Contract

This document defines the vendor-neutral event contract for ATLAS-owned lifecycle receipts.

## Purpose

The contract exists so wrappers, future hooks, CI jobs, Git hooks, and a future CORTEX service can all emit the same inspectable event envelope without depending on one AI vendor or one operating system feature.

Current design rules:

- ATLAS owns the contract and schema files.
- Events are explicit JSON payloads.
- Receipts are written under `runtime/receipts/events/`.
- Adapters may add context, but they may not change the contract shape.
- Hidden background interception is out of scope.

## Lifecycle Events

The current lifecycle set is:

1. `session_start`
2. `task_start`
3. `pre_command`
4. `post_command`
5. `validation_complete`
6. `export_complete`
7. `session_stop`

These are the only event types defined in this version of the contract.

## Event Envelope

Every event payload must conform to the event-specific schema under `ops/events/schemas/`.

Shared envelope fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `contract_version` | string | yes | Current value: `atlas.event.v1` |
| `event_type` | string | yes | One of the seven lifecycle names |
| `event_id` | string | yes | Unique per emitted event |
| `occurred_at` | string | yes | UTC timestamp in ISO 8601 form |
| `producer` | object | yes | Who emitted the event |
| `session` | object | yes | Session scope and workspace context |
| `task` | object | event-specific | Present when the event belongs to one task |
| `payload` | object | yes | Event-specific details |

## Shared Object Rules

### `producer`

Required fields:

- `kind`: one of `wrapper`, `native_hook`, `git_hook`, `ci`, `service`, `manual`, `test`
- `name`: emitter name such as `atlas-codex-wrapper`

Optional fields:

- `version`
- `host`

### `session`

Required fields:

- `session_id`
- `workspace_root`

Optional fields:

- `operator`
- `run_label`

`workspace_root` should be ATLAS-relative when the work happens inside this stack, for example `.` or `repos/fawxzzy-playbook`.

### `task`

Used on task-scoped events. Required fields when present:

- `task_id`
- `task_name`

Optional fields:

- `scope_paths`
- `repo_ids`
- `mutation_mode`

## Event Payloads

### `session_start`

Purpose:

- mark the start of an explicit session or wrapper run
- record the human-visible intent and scope

Required `payload` fields:

- `trigger`
- `intent`
- `workspace_scope`

### `task_start`

Purpose:

- mark the beginning of one scoped task inside the session

Required `payload` fields:

- `task_summary`
- `scoped_paths`
- `mutation_mode`

### `pre_command`

Purpose:

- record a command about to run through an explicit wrapper or adapter

Required `payload` fields:

- `command`
- `cwd`

### `post_command`

Purpose:

- record the result of the explicit wrapped command

Required `payload` fields:

- `command`
- `cwd`
- `status`
- `exit_code`
- `duration_ms`

### `validation_complete`

Purpose:

- record the result of an explicit validation step

Required `payload` fields:

- `validator`
- `status`
- `summary`
- `finding_counts`

### `export_complete`

Purpose:

- record the result of an export, bundle, patch, or snapshot step

Required `payload` fields:

- `export_type`
- `status`
- `artifact_path`
- `summary`

### `session_stop`

Purpose:

- close the session and summarize the run outcome

Required `payload` fields:

- `status`
- `summary`

## Receipt Model

Each invocation writes one receipt JSON file and one rolling `latest.json` file under:

- `runtime/receipts/events/<event_type>/`

Invalid submissions that fail before ATLAS can confirm a supported lifecycle type are not treated as event types.

Those rejected inputs are written under:

- `runtime/receipts/events/_rejected/invalid_input/`

That rejected lane preserves the submitted material for audit purposes, but it is not part of the lifecycle event contract.

Receipt shape:

| Field | Type | Notes |
| --- | --- | --- |
| `receipt_version` | string | Current value: `atlas.event.receipt.v1` |
| `receipt_id` | string | Unique per receipt |
| `recorded_at` | string | UTC timestamp when ATLAS recorded the result |
| `atlas_root` | string | Usually `.` |
| `event` | object | Original submitted event payload |
| `schema` | object | Event type and schema path used for validation |
| `processing` | object | Acceptance state, validation errors, and handler outcome |
| `paths` | object | Relative paths for the timestamped receipt and rolling latest file |

Rejected input receipts in `_rejected/invalid_input/` keep the same processing and paths sections, but they preserve a best-effort `submission` object instead of claiming a supported `event`.

`processing.status` uses:

- `accepted`
- `rejected`
- `handler_failed`

The receipt is the durable handoff surface. Console output is not the contract.

## Command Granularity

Today, on Windows without native Codex hooks, `pre_command` and `post_command` represent only commands that an explicit ATLAS wrapper can see and launch. They do not imply full visibility into internal tool calls made by Codex itself.

Future native hooks may emit the same event types at finer granularity without changing the receipt model.

## Minimal Example

```json
{
  "contract_version": "atlas.event.v1",
  "event_type": "task_start",
  "event_id": "evt-task-start-20260409-001",
  "occurred_at": "2026-04-09T15:00:00Z",
  "producer": {
    "kind": "wrapper",
    "name": "atlas-codex-wrapper",
    "version": "1"
  },
  "session": {
    "session_id": "sess-20260409-001",
    "workspace_root": ".",
    "operator": "human"
  },
  "task": {
    "task_id": "task-20260409-001",
    "task_name": "build-event-contract",
    "scope_paths": [
      "docs/architecture",
      "ops/events"
    ],
    "repo_ids": [
      "stack"
    ],
    "mutation_mode": "stack_only"
  },
  "payload": {
    "task_summary": "Create the vendor-neutral ATLAS event contract and wrapper scaffolding.",
    "scoped_paths": [
      "docs/architecture",
      "ops/events",
      "ops/validation"
    ],
    "mutation_mode": "stack_only",
    "validation_plan": [
      "python ops/validation/validate_event_contracts.py"
    ]
  }
}
```

## Source Of Truth

The schema files under `ops/events/schemas/` are the executable source of truth for payload validation.

This document is the human-readable contract.
