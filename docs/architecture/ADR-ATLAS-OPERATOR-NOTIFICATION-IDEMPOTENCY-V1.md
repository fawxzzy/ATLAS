# ADR: Atlas Operator Notification Idempotency v1

Date: 2026-07-17
Status: Accepted for repository integration; runtime adoption is held
Packet: `ATLAS-MSG-IDEMPOTENCY-001`

## Context

Atlas operator notifications can cross task and host boundaries. A delivery retry may
therefore arrive after a receiver restart or through a different transport envelope.
Transport-level message IDs, timestamps, host names, and retry counters do not identify
the logical notification. Replaying those retries into FAWXZZY MESSAGES creates duplicate
operator-visible updates and can be amplified further when duplicate acknowledgements are
themselves surfaced as messages.

The repository did not contain an attributable operator-notification sender, receiver,
outbox, or service-bus implementation. Existing native-first doctrine keeps Codex as the
execution surface and permits a thin Atlas-owned durability layer for stable meaning. A
new daemon, scheduler, transport client, or second execution authority would violate that
boundary.

## Decision

Add a transport-neutral Python standard-library module and two Draft 2020-12 contracts:

- `atlas.operator-notification.event.v1`
- `atlas.operator-notification.ack.v1`
- internal durable schema `atlas.operator-notification.ledger.v1`
- canonicalization contract `atlas.operator-notification.canonical-json.v1`

The module prepares deterministic events, atomically claims receive-side delivery, records
duplicates, returns correlated acknowledgements, and reports whether a sender may retry.
It has no transport client and cannot emit an operator-facing message by itself.

Runtime adoption must configure the SQLite file below an explicit `runtime/` root. No
runtime database is committed. Tests own temporary runtime directories.

## Stable Identity

`canonical_payload_digest` is SHA-256 over canonical JSON for `payload.facts` only.
Canonical JSON uses UTF-8, Unicode NFC, sorted object keys, compact separators, integers,
booleans, strings, arrays, objects, and null. Floating-point values are rejected; callers
must use integer or string fixed-point facts.

`event_id` is:

```text
onv1_ + sha256(source_thread_id + U+001F + event_class + U+001F + canonical_payload_digest)
```

`payload.transport` and `created_at` are declared transport-volatile fields. They are
excluded from logical identity, so an unchanged retry preserves `event_id` across hosts
and restarts. Their combined envelope digest is retained only to distinguish exact from
semantic duplicate receipts.

Every event carries `created_at`. A changed fact set creates a new `event_id`. Unless the
event is explicitly typed `periodic_digest`, the receiver requires the changed event to
name the latest stream event in `supersedes_event_id` and provide sorted, unique JSON
Pointer paths in `delta.changed_fact_paths`. Initial stream events may establish a first
snapshot. Heartbeats and continuations are control records and never authorize an
operator-facing message.

## Atomic Receive Contract

The receive ledger uses Python `sqlite3`, WAL journaling, `synchronous=FULL`, foreign keys,
a five-second busy timeout, and `BEGIN IMMEDIATE` for one-writer claim and acknowledgement
transactions.

For a new notification event, one transaction:

1. validates and deterministically reconstructs the event;
2. checks the current stream and supersession relationship;
3. inserts the immutable identity and version metadata;
4. creates a deterministic claim token and expiry for an operator update or periodic digest;
5. returns `should_emit=true` to exactly one claimant.

For an existing `event_id`, one transaction increments `duplicate_count`, advances
`last_seen`, records exact or semantic duplicate disposition, and returns
`should_emit=false`. A claim may be reissued only after an unacknowledged lease expires.
That retry uses a new deterministic claim generation and token. Once a correlated
acknowledgement is accepted, every later retry returns the stable acknowledgement and the
sender must stop. Superseded events remain suppressed even if an earlier claim lease later
expires. Replayed acknowledgements always set both `retry_authorized=false` and
`operator_message_authorized=false`.

## Stored Data and Privacy

The SQLite ledger stores event identity, source thread, event class, contract versions,
canonical and envelope digests, first/last seen timestamps, duplicate count, disposition,
supersession/delta metadata, claim state, delivery state, and acknowledgement state. It
does not store notification bodies, transport metadata, claimant host names, secrets, or
PII. Claimant identifiers are retained only as SHA-256 digests.

Ledger paths are fail-closed unless they remain below the configured runtime root, use the
`.sqlite3` suffix, and avoid `.git` and `secrets`. CLI JSON inputs under `secrets` or `.env*`
paths are rejected.

## Retention, Backup, and Recovery

Version 1 performs no automatic deletion or compaction. Duplicate evidence is represented
by the durable first/last seen values, duplicate count, and current disposition. A future
compaction feature must first write a versioned audit export plus digest and explicit
compaction receipt; silent row deletion is forbidden.

Before operational adoption, the owner must define the backup destination and retention
window, prove SQLite online backup and restore on the actual runtime filesystem, and prove
that restored duplicate and acknowledgement state suppresses replay. An unknown ledger
schema, missing required tables, SQLite open failure, or failed `quick_check` is a terminal
fail-closed condition; the receiver must not emit while state is unknown.

## Authority Boundary

The event and acknowledgement contracts freeze:

- `notification_only=true`
- `repository_execution_authorized=false`
- `board_mutation_authorized=false`

Neither receipt authorizes repository execution, board mutation, Discord mutation, task
mutation, or production action. A caller may deliver only after its own authority check
and only when `should_emit=true`.

## Failure Mode

**Duplicate acknowledgement amplification:** acknowledging a duplicate by creating another
operator-facing notification can turn one retry loop into two mutually amplifying message
streams. Duplicate claims and replayed acknowledgements are control-plane receipts only.
They are recorded durably but must never be routed back through the operator-notification
lane as new messages.

## Adoption Gate

Repository acceptance does not activate the feature. Runtime adoption requires all of:

1. an owner-named native sender and receiver integration point;
2. one configured `runtime/` location with single-writer ownership;
3. actual-filesystem WAL, lock, online-backup, integrity, restore, and replay proof;
4. a transport adapter that treats `should_emit` as a mandatory gate and validates the
   correlated acknowledgement before stopping retries;
5. observability for rejected/corrupt/unknown state that does not disclose payload facts;
6. an explicit rollback procedure and operator acceptance.

Until those gates pass, the implementation is dormant repository capability only.

## Rollback

Before runtime adoption, rollback is deletion or revert of these repository additions.
After adoption, stop the adapter first, preserve and hash the ledger and WAL sidecars, then
revert the adapter. Do not replace the receiver with an unguarded direct-send path. A
forward fix or restore of the last verified v1 backup is required before notification
delivery resumes.
