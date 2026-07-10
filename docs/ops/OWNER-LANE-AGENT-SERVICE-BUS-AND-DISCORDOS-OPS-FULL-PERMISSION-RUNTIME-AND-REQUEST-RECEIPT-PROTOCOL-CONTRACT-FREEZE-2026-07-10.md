# Owner-Lane Agent Service Bus And DiscordOS Ops Full-Permission Runtime And Request-Receipt Protocol Contract Freeze

- Date: `2026-07-10`
- Lane: `ATLAS-root owner-lane orchestration governance`
- Mode: `docs-only root-bounded full-permission runtime and request-receipt protocol contract freeze`
- Scope: `make the standing full-permission operator policy durable for the owner-lane service-bus family, freeze the request/receipt protocol and single-writer coordination contract, move the marker from 0 percent to 10 percent, and preserve owner-repo separation`
- Control-plane checkpoint: `main@c9c812f4`
- Marker movement:
  - move `Owner-Lane Agent Service Bus & DiscordOS Ops Readiness: 0% -> 10%`
  - no other marker moves

## Operator Policy Frozen

The standing operator policy for this lane is now frozen as:

```text
CODEX_PERMISSION_MODE = full
CODEX_APPROVAL_POLICY = never
NETWORK_ACCESS = enabled
WEB_SEARCH = live
PERMISSION_DOWNGRADE = forbidden unless operator explicitly requests it
```

This applies to:

- ATLAS-root Codex threads
- `discordos_ops`
- `mazer_owner_lane`
- `fitness_owner_lane`
- scheduler-generated workers
- service-bus dispatch workers
- future Cortex execution adapters
- subagents spawned by those systems

Managed product or workspace requirements may still constrain permission profiles or approval policies. Those constraints are upstream platform controls, not ATLAS doctrine.

## Codex Runtime Configuration

Modern permission-profile configuration is the canonical default:

```toml
default_permissions = ":danger-full-access"
approval_policy = "never"
web_search = "live"

[notice]
hide_full_access_warning = true
```

Legacy fallback for older Codex clients:

```toml
sandbox_mode = "danger-full-access"
approval_policy = "never"
web_search = "live"

[notice]
hide_full_access_warning = true
```

No-mixing rule:

- do not combine `default_permissions` with `sandbox_mode`
- do not combine permission-profile mode with `[sandbox_workspace_write]`
- do not send app-server `permissions` and legacy `sandbox` together

## App Server Runtime Contract

Modern beta app-server clients may launch a service thread with a named permission profile after opting into `capabilities.experimentalApi`:

```json
{
  "method": "initialize",
  "id": 1,
  "params": {
    "clientInfo": {
      "name": "atlas_dispatcher",
      "title": "ATLAS Dispatcher",
      "version": "0.1.0"
    },
    "capabilities": {
      "experimentalApi": true
    }
  }
}
```

```json
{
  "method": "thread/start",
  "id": 10,
  "params": {
    "model": "gpt-5.4",
    "cwd": "C:\\ATLAS\\repos\\DiscordOS",
    "approvalPolicy": "never",
    "permissions": ":danger-full-access",
    "serviceName": "discordos_ops"
  }
}
```

Legacy app-server fallback:

```json
{
  "method": "thread/start",
  "id": 10,
  "params": {
    "model": "gpt-5.4",
    "cwd": "C:\\ATLAS\\repos\\DiscordOS",
    "approvalPolicy": "never",
    "sandbox": "dangerFullAccess",
    "serviceName": "discordos_ops"
  }
}
```

Per-turn runtime contract:

```json
{
  "method": "turn/start",
  "id": 30,
  "params": {
    "threadId": "DISCORDOS_OPS_THREAD_ID",
    "approvalPolicy": "never",
    "sandboxPolicy": {
      "type": "dangerFullAccess"
    },
    "input": [
      {
        "type": "text",
        "text": "Process the next queued DiscordOS Ops request."
      }
    ]
  }
}
```

Session continuity rules:

- clients should store `thread.id`
- app-server resume should use `thread/resume` against the stored `thread.id`
- `thread.sessionId` is the live session-tree root and must be read from the server response instead of inferred
- resume preserves logical service continuity without exposing thread ids as part of the client request schema

## Service Registry Policy

The runtime service registry contract is:

```json
{
  "schema_version": "atlas.agent-service-registry.v1",
  "defaults": {
    "permission_profile": ":danger-full-access",
    "approval_policy": "never",
    "network_access": "enabled",
    "web_search": "live",
    "allow_permission_downgrade": false
  },
  "services": {
    "discordos_ops": {
      "cwd": "repos/DiscordOS",
      "permission_profile": ":danger-full-access",
      "approval_policy": "never",
      "network_access": "enabled",
      "max_concurrency": 1,
      "status": "ready"
    },
    "mazer_owner_lane": {
      "cwd": "repos/mazer",
      "permission_profile": ":danger-full-access",
      "approval_policy": "never",
      "network_access": "enabled"
    },
    "fitness_owner_lane": {
      "cwd": "repos/fawxzzy-fitness",
      "permission_profile": ":danger-full-access",
      "approval_policy": "never",
      "network_access": "enabled"
    }
  }
}
```

`max_concurrency: 1` for `discordos_ops` is a serialization invariant, not a permission limitation.

## Single-Writer Coordination Contract

Full permissions control capability. The service bus controls ownership and correctness.

Preserved coordination rules:

- `discordos_ops` is the only logical writer for Discord board and card mutations
- Mazer, Fitness, ATLAS root, and later clients submit structured requests
- clients target the logical service name, not a raw thread id
- every mutation requires queue ordering, idempotency, resource-key leasing, sync/readback proof, and a correlated receipt
- no direct owner-chat DiscordOS mutation is admissible evidence

The single-writer rule must never be described as a sandbox restriction. It exists to prevent write races and proof drift across a shared board surface.

## Frozen Request Schema

```json
{
  "schema_version": "atlas.agent-bus.request.v1",
  "request_id": "mazer-20260710-0001",
  "idempotency_key": "mazer:board.card.update:invisibility-cloak:v3",
  "source_lane": "mazer",
  "source_client": "mazer-main-codex",
  "source_thread_id": "thr_mazer_123",
  "target_service": "discordos_ops",
  "action": "board.card.update",
  "resource_key": "discord-board:mazer:invisibility-cloak-item",
  "priority": 50,
  "expected_version": 3,
  "payload": {
    "card_id": "mazer-invisibility-cloak-item",
    "changes": {
      "status": "done"
    }
  },
  "proof_requirements": {
    "live_sync": true,
    "readback": true,
    "commit_if_repo_changed": true
  },
  "callback_mode": "queue_return",
  "created_at": "2026-07-10T15:00:00Z"
}
```

Required fields:

- `schema_version`
- `request_id`
- `idempotency_key`
- `source_lane`
- `source_client`
- `source_thread_id`
- `target_service`
- `action`
- `resource_key`
- `priority`
- `expected_version`
- `payload`
- `proof_requirements`
- `callback_mode`
- `created_at`

Callback modes admitted by this contract:

- `queue_return`
- `managed_thread_callback`

## Frozen Receipt Schema

```json
{
  "schema_version": "atlas.agent-bus.receipt.v1",
  "request_id": "mazer-20260710-0001",
  "service": "discordos_ops",
  "status": "succeeded",
  "started_at": "2026-07-10T15:00:07Z",
  "completed_at": "2026-07-10T15:01:12Z",
  "action": "board.card.update",
  "resource_key": "discord-board:mazer:invisibility-cloak-item",
  "files_changed": [],
  "commit_sha": null,
  "sync_status": "passed",
  "readback_status": "passed",
  "evidence_refs": [
    "runtime/orchestration/receipts/mazer-20260710-0001.json"
  ],
  "warnings": [],
  "blockers": [],
  "return_summary": "Card updated and verified by live sync and readback."
}
```

Required fields:

- `schema_version`
- `request_id`
- `service`
- `status`
- `started_at`
- `completed_at`
- `action`
- `resource_key`
- `files_changed`
- `commit_sha`
- `sync_status`
- `readback_status`
- `evidence_refs`
- `warnings`
- `blockers`
- `return_summary`

Completion rule:

- a queued mutation is complete only when the matching receipt reports successful mutation, sync, and readback

## Queue State Model

Frozen queue states:

- `queued`
- `leased`
- `running`
- `succeeded`
- `failed_retryable`
- `dead_lettered`
- `rejected`

State rules:

- only one active lease may exist for a given `resource_key`
- `queued -> leased -> running -> terminal` is the only happy-path progression
- schema, authority, or stale-version failures must terminate as `rejected` before mutation
- retries may transition only through `failed_retryable`
- exhausted or permanently invalid work must terminate as `dead_lettered`

## Idempotency Model

Frozen idempotency rules:

- deduplicate by stable `idempotency_key`
- bind every request to a `resource_key`
- reject stale `expected_version` writes before live mutation
- suppress duplicates before Discord mutation or repo mutation
- allow safe polling or callback retries without replaying completed work

## Resource Lease Model

Frozen lease rules:

- one active lease per `resource_key`
- bounded lease duration
- explicit lease renewal only while execution is still live
- mandatory lease release on success, rejection, retryable failure, dead-letter, or worker loss recovery
- lease loss must fail closed rather than allow concurrent mutation

## Queue-Return And Managed-Thread Callback Modes

Queue-return is the first implementation mode:

- client submits the request
- client stores `request_id`
- client polls queue status or waits on a receipt lookup
- client continues only after a matching final receipt

Managed-thread callback is admitted but not first:

- source thread id is stored by the bus
- the dispatcher resumes the originating managed thread
- the receipt is injected as a bounded callback turn

Both modes preserve the same request and receipt schema.

## Transport And Adapter Model

Transport posture:

- SQLite first at `runtime/orchestration/agent-bus.sqlite3`
- Supabase later as a transport adapter, not a schema fork

Adapter posture:

- Codex is the current client and worker runtime
- Cortex is the future orchestrator
- the request/receipt protocol and service registry stay stable across both

## Validation And Proof

Proof recorded by this freeze:

- full-permission runtime policy is now durable in root doctrine
- the modern and legacy config models are both defined
- the no-mixing rule is explicit
- app-server thread/start, turn/start, and resume behavior are defined
- service registry defaults are frozen
- request and receipt schemas are frozen
- queue states, idempotency, leases, single-writer routing, callback modes, and transport posture are frozen
- owner repos remain unmutated

## Exact Next Packet

```text
Owner-Lane Agent Service Bus & DiscordOS Ops durable SQLite queue first-implementation admission
```

## Completion

Completion: `100%`

- full-permission policy durable: `yes`
- request/receipt protocol frozen: `yes`
- single-writer coordination frozen: `yes`
- marker movement: `0% -> 10%`
- owner repos mutated: `no`
