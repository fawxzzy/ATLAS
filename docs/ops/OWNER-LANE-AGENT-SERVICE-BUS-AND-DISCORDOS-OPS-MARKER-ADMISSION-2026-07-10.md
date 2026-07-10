# Owner-Lane Agent Service Bus And DiscordOS Ops Marker Admission

- Date: `2026-07-10`
- Lane: `ATLAS-root owner-lane orchestration governance`
- Mode: `ATLAS-root docs-only supporting-marker admission`
- Scope: `admit the owner-lane agent service bus and DiscordOS Ops readiness marker at 0 percent, freeze the durable request/receipt operating model, and preserve the current Cortex Dual-Mode selected packet without implementing the bus or mutating any owner repo`
- Control-plane checkpoint: `main@6ab14089`
- Marker movement:
  - admit `Owner-Lane Agent Service Bus & DiscordOS Ops Readiness: 0%`
  - no other marker moves
  - preserve the current `Cortex Dual-Mode Replacement Readiness` selected packet unchanged

## Why This Marker Exists

The stack now has a clear architectural boundary for owner-lane Discord board work:

- Mazer, Fitness, ATLAS root, and later owner-lane clients should submit structured requests
- one logical `discordos_ops` service should own DiscordOS-side mutation authority
- the service should return correlated receipts with live-sync and readback truth

That architecture was already reasoned through, but it was still chat-local and therefore non-durable. This marker exists to promote that architecture into the ATLAS marker board as a tracked future lane without claiming any implementation progress yet.

## Why Direct Owner-Chat Writes To DiscordOS Are Forbidden

Direct owner-chat writes are forbidden because they collapse routing, authority, and proof:

- the source chat can blur Mazer or Fitness repo work with DiscordOS repo mutation
- natural-language requests do not provide durable request ids, idempotency keys, or resource locks
- source-chat prose is not live Discord proof
- thread-specific references couple the client to one mutable runtime thread instead of one logical service boundary

Root doctrine stays cleaner when owner-lane chats request Discord operations but do not perform them directly.

## Why DiscordOS Ops Is The Single Writer

`discordos_ops` is the single writer because the Discord board state is one shared mutation surface.

One writer gives the stack:

- serial board mutation
- one place to enforce schema validation
- one place to enforce idempotency and resource leases
- one place to require live sync and mandatory readback
- one permission profile with bounded filesystem and network scope

That keeps board truth coherent even when Mazer and Fitness both need updates.

## Why Clients Use Logical Service Name, Not Thread ID

Clients should target:

```text
target_service = discordos_ops
```

They should not target a raw chat or thread id.

The service registry should own the real runtime thread mapping so the DiscordOS worker can be restarted or replaced without changing every owner-lane prompt or packet.

## Request Protocol

Admitted request contract:

```json
{
  "schema_version": "atlas.agent-bus.request.v1",
  "request_id": "mazer-20260710-0001",
  "idempotency_key": "mazer:card:update:invisibility-cloak:v3",
  "source_lane": "mazer",
  "source_client": "mazer-main-codex",
  "source_thread_id": null,
  "reply_mode": "queue",
  "target_service": "discordos_ops",
  "action": "board.card.update",
  "resource_key": "discord-board:mazer:invisibility-cloak-item",
  "priority": 50,
  "expected_version": 3,
  "payload": {},
  "proof_requirements": {
    "live_sync": true,
    "readback": true,
    "commit_if_repo_changed": true
  }
}
```

Required fields are:

- request identity: `request_id`, `idempotency_key`
- caller identity: `source_lane`, `source_client`, optional `source_thread_id`
- routing: `reply_mode`, `target_service`
- mutation intent: `action`, `resource_key`, `priority`, optional `expected_version`
- exact work payload
- proof requirements

## Receipt Protocol

Admitted receipt contract:

```json
{
  "schema_version": "atlas.agent-bus.receipt.v1",
  "request_id": "mazer-20260710-0001",
  "status": "succeeded",
  "service": "discordos_ops",
  "started_at": "2026-07-10T12:00:00Z",
  "completed_at": "2026-07-10T12:01:12Z",
  "action": "board.card.update",
  "resource_key": "discord-board:mazer:invisibility-cloak-item",
  "files_changed": [],
  "commit_sha": null,
  "live_sync_status": "passed",
  "readback_status": "passed",
  "card_ids": [
    "mazer-invisibility-cloak-item"
  ],
  "board_version": 4,
  "evidence_refs": [],
  "warnings": [],
  "blockers": [],
  "return_summary": "Card updated and verified by live Discord readback."
}
```

This receipt is the only admitted completion evidence for a queued board mutation. Request submission alone is never sufficient proof.

## Queue States

The queue state model is:

- `queued`: accepted but not yet leased
- `leased`: reserved for one worker
- `running`: worker is actively processing the request
- `succeeded`: mutation, sync, and readback all passed
- `failed_retryable`: request failed but may be retried within bounded policy
- `dead_lettered`: retries exhausted or the request is permanently invalid
- `rejected`: schema, authority, or version checks failed before execution

Board mutation stays single-writer and serial while read-only future queries may widen later.

## Idempotency And Lease Rules

The queue contract freezes these rules:

- deduplicate by stable `idempotency_key`
- bind the request to a `resource_key`
- allow one active lease per target board or card resource
- use bounded lease duration with explicit renewal while work is still live
- reject stale `expected_version` writes
- require duplicate suppression before any live Discord mutation
- require lease release on success, rejection, failure, or dead-letter transition

This keeps repeated submissions from causing duplicate board moves or split-brain receipts.

## Permission-Profile Model

The worker should run under one bounded profile, for example `discordos_ops_writer`.

The profile model is:

- writable: `repos/DiscordOS/**` and `runtime/orchestration/receipts/**`
- read-only: source request payload plus required ATLAS marker and receipt references
- network: only what the Discord sync and readback path needs
- forbidden: ATLAS root mutation beyond queue receipts, Mazer or Fitness writes, Vercel mutation, Supabase mutation, secret output, and arbitrary filesystem access

Source chats do not grant permissions by prose. The worker thread configuration remains the authority boundary.

## Queue Return And Managed-Thread Callback Modes

Two return modes are admitted.

Queue return is the first implementation mode:

- client submits the request
- client stores `request_id`
- client polls `discordos_ops.wait` or status reads
- client continues only after a matching succeeded receipt arrives

Managed-thread callback is later and optional:

- source thread id is stored by the bus
- the dispatcher resumes the originating managed thread
- the receipt is injected as a bounded callback turn

Queue return is the safe first adapter because it does not depend on arbitrary UI thread addressing.

## SQLite-First And Supabase-Later Transport

The first transport should be SQLite under:

```text
runtime/orchestration/agent-bus.sqlite3
```

Why SQLite first:

- local durable queue
- transactions
- WAL support
- easy leases and idempotency
- no cloud dependency for the first Codex adapter

Supabase is a later transport adapter for cross-host execution. The request and receipt schema should stay the same across both transports.

## Current Codex Adapter And Future Cortex Adapter

The current adapter posture is:

- Codex chats act as clients or as the `discordos_ops` worker
- the bus, registry, queue, and receipt model provide the durable seam Codex lacks natively between arbitrary UI chats

The future adapter posture is:

- Cortex becomes the native orchestrator
- Codex chats become optional clients
- the same request and receipt contracts remain transport-safe and service-safe

This marker is therefore durable and product-independent rather than Codex-specific.

## Threshold Model

`Owner-Lane Agent Service Bus & DiscordOS Ops Readiness`

- `0%`: marker admitted
- `10%`: request and receipt protocol plus single-writer contract frozen
- `20%`: SQLite queue, CLI, idempotency, and leases implemented
- `30%`: persistent DiscordOS Ops worker thread plus restricted permission profile
- `40%`: Mazer client works end to end
- `50%`: Fitness client works end to end
- `60%`: concurrent fairness, retry, and dead-letter proof lands
- `70%`: automatic receipt routing to originating managed thread
- `80%`: ATLAS cleanup and resync board flow is integrated end to end
- `90%`: Supabase-backed cross-host transport, observability, and recovery land
- `100%`: Cortex-native service bus is operational and Codex chats are optional adapters

This admission packet does not move the marker beyond `0%`.

## Non-Goals

- no arbitrary UI chat-to-chat claim
- no blanket full permissions
- no owner-repo mutation
- no automatic deploy
- no hidden transcript scraping
- no shared direct DiscordOS writes
- no marker ratchet

## Failure Modes

The frozen failure model includes:

- source chats bypass the bus and mutate DiscordOS directly
- thread-id coupling breaks after worker replacement
- duplicate requests race without idempotency enforcement
- stale `expected_version` writes clobber newer board truth
- lease loss causes concurrent mutation
- live sync succeeds but readback fails
- callback delivery interrupts an unrelated managed-thread task
- the worker profile widens into owner repos, secrets, or platform mutation

Any implementation packet has to prove these classes are bounded or fail closed.

## Exact Next Packet

The next exact packet is:

```text
Owner-Lane Agent Service Bus & DiscordOS Ops request-receipt protocol contract freeze
```

That packet should freeze the final request schema, receipt schema, queue state machine, idempotency rules, lease semantics, and basis surfaces without implementing the bus yet.

## Completion

Completion: `100%` for this marker-admission packet itself.

The marker is admitted at `0%`.
No owner repo was mutated.
No DiscordOS runtime mutation was performed.
The current `Cortex Dual-Mode Replacement Readiness` selected packet remains unchanged.
