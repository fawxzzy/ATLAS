# Automation Levels

ATLAS now uses one machine-readable automation policy across chat, voice, CLI, Awareness API, MCP, Cortex, and Lifeline.

The policy is carried on governed artifacts as `automation_level`, and governed tool registry entries declare `max_automation_level`.

## Levels

### `observe`

Read-only status and inventory access.

Allowed examples:

- render status
- list attention
- list inventory
- health checks

### `context`

Read-only context gathering that may fetch richer session, artifact, or knowledge detail.

Allowed examples:

- session fetch
- governed artifact fetch
- knowledge query
- search over promoted state

### `request_action`

A client is asking root-owned governed machinery to perform an action, but no execution approval has been consumed yet.

Allowed examples:

- privileged-action request artifacts
- root-owned resume request and dispatch artifacts
- local voice or CLI issuing a governed action request

### `approved_action`

Execution may proceed because the governed approval boundary has been crossed.

Allowed examples:

- approval receipts
- Lifeline execution receipts
- bounded write classes that explicitly require approval
- `workspace_file_apply` inside a declared session-owned workspace root

## Enforcement

Defaults:

- every client defaults to `observe`
- clients may only request a higher level when the target surface allows it

Registry rule:

- every governed tool entry declares `max_automation_level`
- artifacts for that tool must not exceed the registered maximum

Artifact rule:

- session manifests carry `automation_level` and `max_automation_level`
- privileged-action requests must use `request_action`
- approval receipts must use `approved_action`
- privileged-action receipts must use `approved_action`
- resume request and resume dispatch artifacts use `request_action`

## Client Matrix

| Surface | Max level | Notes |
| --- | --- | --- |
| Awareness API status, inventory, attention | `observe` | Read-only and fail closed on higher requested levels |
| Awareness API search, fetch, knowledge, session fetch | `context` | Read-only and fail closed on action attempts |
| MCP read bridge | per tool registry entry | Uses the same awareness policy and rejects action-level requests |
| Voice | `request_action` | Must route through governed session/request artifacts |
| CLI | `request_action` | Must route through governed session/request artifacts |
| Cortex session orchestration | up to session `max_automation_level` | Root-owned coordinator, not an executor |
| Lifeline | `approved_action` | Executes only with matching approval and governed identity |

## Resume Lifecycle

The root-owned resume path is now:

1. `resume_ready`
2. `resume_requested`
3. `resume_dispatched`
4. `completed` or `resume_failed`

Required refs for resume:

- session manifest
- merge completion ref
- resume-context ref
- merge request ref
- paused worker handoff refs
- current `stack_lock_digest`
- current `tool_id` and `registry_digest`

Root resume fails closed when any of those are stale, missing, or inconsistent.

## Audit Expectations

Awareness API and MCP request logs must record:

- requested automation level
- max automation level
- route or tool name

Governed observations and receipts should also carry automation level so later analysis can distinguish:

- asked
- approved
- executed

## First Write Class

The first truthful machine write class is deliberately narrow:

- one bounded file write/apply
- inside `runtime/atlas/session-workspaces/<session_id>/`
- approval-gated at `approved_action`
- rollback-aware through prior hash or backup ref when available

Still out of scope:

- package installs
- service installs
- OS-wide mutation
- arbitrary shell writes
- admin-wide mutation
