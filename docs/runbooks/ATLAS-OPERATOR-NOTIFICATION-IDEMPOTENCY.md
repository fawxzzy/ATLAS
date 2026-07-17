# Atlas Operator Notification Idempotency Runbook

Status: repository capability only; runtime adoption is not authorized by this runbook.

## Purpose

Use the idempotency module to prepare stable notification events, claim a single
operator-facing delivery, and persist a correlated acknowledgement. The module prints JSON
receipts only. It does not connect to FAWXZZY MESSAGES or any other transport.

## Required Call Order

1. Before first use only, explicitly provision one new ledger. Normal startup must open
   that existing ledger and fail closed if it is missing.
2. Prepare one event from allowlisted facts.
3. Pass the event to the receiver claim transaction.
4. When `should_begin_delivery=true`, call the atomic `begin-delivery` transition with the
   returned claim token and generation immediately before transport.
5. Deliver only when that pre-send receipt sets both `should_emit=true` and
   `operator_message_authorized=true`, the caller already has delivery authority, and the
   transport uses `event_id` as its idempotency key.
6. Record the correlated acknowledgement using the same token and generation.
7. Stop sender retries when the acknowledgement sets `retry_authorized=false`.

Never infer permission from a missing, unreadable, corrupt, or unknown ledger. Those states
are failures, not empty or healthy state.

## Prepare

The input file is a small JSON object matching the keyword arguments of `build_event`:

```json
{
  "source_thread_id": "019f52d9-7667-72a3-a5f7-9c0613aedd8f",
  "event_class": "task.completion",
  "notification_kind": "operator_update",
  "created_at": "2026-07-17T14:00:00Z",
  "payload": {
    "facts": {
      "packet_id": "ATLAS-MSG-IDEMPOTENCY-001",
      "state": "ready"
    },
    "transport": {
      "attempt": 1
    }
  },
  "supersedes_event_id": null,
  "delta": null
}
```

Prepare without sending:

```powershell
python ops/atlas/operator_notification_idempotency.py prepare --input <input-json>
```

Transport attempt numbers, host labels, routing metadata, and `created_at` may change on a
retry without changing `event_id`. `notification_kind` is identity-bearing, so changing a
heartbeat into an operator update creates a different ID while same-kind cross-host retries
remain stable. Changed facts must produce a new event and, after the first event in a
stream, must name the latest predecessor and changed fact paths. Only an explicit
`periodic_digest` may establish another unlinked full snapshot. Heartbeats and
continuations must not carry `supersedes_event_id` or `delta`; control receipts can never
supersede a deliverable event. All timestamps must use canonical RFC 3339 UTC (`T`, `Z`,
and at most six fractional digits). Delta paths exclude the empty root pointer and use only
RFC 6901 `~0` and `~1` escapes.

## Provision Once

Before first receiver use and only when no authority ledger exists:

```powershell
python ops/atlas/operator_notification_idempotency.py provision `
  --runtime-root <atlas-runtime-root> `
  --ledger <atlas-runtime-root>\atlas\notifications\receive.sqlite3
```

Provisioning reserves a new file exclusively and fails if any file already exists. Claim,
delivery, acknowledgement, and status commands open only an existing database and never
create a replacement. If an adopted ledger is missing, stop and restore it; never run
`provision` to bypass missing duplicate or acknowledgement history.

## Claim

Both paths must be explicit. The ledger must remain below the runtime root:

```powershell
python ops/atlas/operator_notification_idempotency.py claim `
  --runtime-root <atlas-runtime-root> `
  --ledger <atlas-runtime-root>\atlas\notifications\receive.sqlite3 `
  --event <event-json> `
  --claimant-id <non-sensitive-instance-id> `
  --seen-at <utc-timestamp>
```

Interpretation:

- `should_begin_delivery=true`: this claimant may attempt the atomic pre-send fence.
- Every claim receipt has `should_emit=false` and authorizes no operator message.
- `duplicate_exact`: unchanged facts and unchanged transport envelope.
- `duplicate_semantic`: unchanged canonical facts after declared volatile fields changed.
- `duplicate_acked`: the receiver already accepted delivery; use the returned stable ack.
- `duplicate_superseded`: a newer changed event replaced this event; never retry it.
- `suppressed_control`: heartbeat or continuation; never emit.
- `retry_claimed`: the prior lease expired before delivery began and this fenced claim owns
  the retry.
- `duplicate_delivery_unknown`: delivery began but no acknowledgement is durable; emit
  nothing, do not take over, and reconcile against transport acceptance by `event_id`.

`seen_at` is receipt metadata only. Claim acquisition, lease expiry, and lease takeover are
computed from the ledger's UTC runtime clock while the claim transaction holds its writer
lock. A caller clock in the past or future must not shorten, extend, or replace a claim.

Do not treat delivery-state changes as new operator notifications. In particular, never
send a duplicate acknowledgement through the same notification lane.

## Begin Delivery

Immediately before the transport call:

```powershell
python ops/atlas/operator_notification_idempotency.py begin-delivery `
  --runtime-root <atlas-runtime-root> `
  --ledger <atlas-runtime-root>\atlas\notifications\receive.sqlite3 `
  --event-id <event-id> `
  --claim-token <claim-token> `
  --claim-generation <claim-generation>
```

This transition is the only source of operator-message authorization. It atomically fences
expired claimants and makes the delivery non-stealable. The transport must deduplicate on
the returned `transport_idempotency_key`, which is the stable `event_id`. SQLite protects
local claim ownership; it does not provide network exactly-once delivery. If the process
crashes or times out after this transition, status is `UNKNOWN` and reconciliation is
required. Never replay automatically from `delivery_in_progress`. `started_at` must be at
or after the active claim generation's persisted acquisition timestamp and before expiry;
the ledger captures it from the UTC runtime clock inside the transaction, so callers cannot
backdate it to the event's original `first_seen`.

## Acknowledge

After the separately authorized transport accepts the one claimed notification:

```powershell
python ops/atlas/operator_notification_idempotency.py ack `
  --runtime-root <atlas-runtime-root> `
  --ledger <atlas-runtime-root>\atlas\notifications\receive.sqlite3 `
  --event-id <event-id> `
  --claim-token <claim-token> `
  --claim-generation <claim-generation> `
  --acknowledged-at <utc-timestamp>
```

The token and generation must match the active claim, and delivery must already be fenced
in progress. A repeated acknowledgement returns the same `ack_id` with
`ack_disposition=replayed`; stale acknowledgements fail closed and never authorize a
message or another retry.

## Inspect

```powershell
python ops/atlas/operator_notification_idempotency.py status `
  --runtime-root <atlas-runtime-root> `
  --ledger <atlas-runtime-root>\atlas\notifications\receive.sqlite3 `
  --event-id <event-id>
```

Status output contains digests and allowlisted metadata, not payload bodies or transport
metadata. Do not copy ledger files while the writer is active; the adoption packet must
prove SQLite online backup and restore on the target filesystem.

## Failure Response

- Contract rejection: quarantine the event metadata and fix the producer; do not send.
- Missing configured ledger: stop the adapter and restore the authority ledger; normal
  startup never creates it, and provisioning is not a recovery operation.
- Unknown schema or missing tables: stop the adapter; do not create a replacement ledger
  over the file or auto-migrate it.
- Failed integrity/open check: stop delivery, preserve the database and sidecars, restore
  the last verified backup, then replay the original deterministic events.
- Busy/lock timeout: report unavailable and retry the claim transaction later; do not bypass
  the ledger.
- `delivery_in_progress` without acknowledgement: report `UNKNOWN`, reconcile using the
  transport's `event_id` acceptance evidence, and do not issue a replacement lease.
- Duplicate acknowledgement loop: break the loop at both adapters and retain the ledger
  evidence. An acknowledgement is a control receipt, never notification content.

Version 1 never deletes or compacts ledger rows automatically. Any later compaction must
retain a versioned digest-backed audit artifact and explicit receipt before deleting rows.
