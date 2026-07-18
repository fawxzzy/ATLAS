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
- internal durable schema `atlas.operator-notification.ledger.v2`
- canonicalization contract `atlas.operator-notification.canonical-json.v1`

The module prepares deterministic events, atomically claims receive-side delivery, records
duplicates, returns correlated acknowledgements, and reports whether a sender may retry.
It has no transport client and cannot emit an operator-facing message by itself.

Runtime adoption must configure the SQLite file below an explicit `runtime/` root and run
one explicit, exclusive provisioning operation before first use. Normal receiver startup
opens only an existing file with SQLite `mode=rw`; it never creates a missing ledger. A
missing adopted ledger requires restore or operator action, not fresh provisioning. No
runtime database is committed. Tests own temporary runtime directories.

First-time provisioning constructs the complete `ledger.v2` database at an exclusively
created, same-directory private path. It initializes and validates schema and metadata,
checkpoints WAL state, requires no SQLite sidecars, and synchronizes the database before an
atomic no-replace publication to the configured path. The configured path is therefore
absent or complete; it is never used as initialization scratch. Concurrent provisioners
may each prepare a private database, but exactly one may publish. Losers fail closed and
remove only their own identity-checked artifacts without changing the winner.

Handled pre-publication failures remove only the exact private database and its exact
`-wal`, `-shm`, or `-journal` sidecars after parent, name, regular-file, symlink, and file
identity checks. An abrupt process exit may leave a uniquely named private artifact of the
form `.<ledger>.provision-<random>.tmp`. Such residue is never authoritative, never adopted
as the configured ledger, and never blocks a later exclusive provision. Its deletion is a
separate bounded cleanup operation requiring exact path and identity proof; broad cleanup
by prefix is forbidden.

On POSIX filesystems, provisioning synchronizes the parent directory immediately after
publishing the canonical hard link and again after removing the private name. A successful
return therefore covers both directory-entry transitions, not only SQLite file contents.

## Stable Identity

`canonical_payload_digest` is SHA-256 over canonical JSON for `payload.facts` only.
Canonical JSON uses UTF-8, Unicode NFC, sorted object keys, compact separators, integers,
booleans, strings, arrays, objects, and null. Floating-point values are rejected; callers
must use integer or string fixed-point facts.

`event_id` is:

```text
onv1_ + sha256(
  source_thread_id + U+001F + event_class + U+001F + notification_kind
  + U+001F + canonical_payload_digest
  [+ U+001F + supersedes_event_id for a changed deliverable]
)
```

`notification_kind` is identity-bearing because it changes delivery semantics. A heartbeat
and operator update with otherwise identical facts therefore cannot collide. In contrast,
`payload.transport` and `created_at` are declared transport-volatile fields. They are
excluded from logical identity, so an unchanged same-kind retry preserves `event_id`
across hosts and restarts. Their combined envelope digest is retained only to distinguish
exact from semantic duplicate receipts.

Every event carries `created_at`. A changed deliverable binds its causal predecessor into
identity. This makes `ready -> blocked -> ready` three distinct occurrences while a retry
of any occurrence with the same facts and predecessor remains stable. Unless the event is
explicitly typed `periodic_digest`, the receiver requires the changed event to name the
latest stream event in `supersedes_event_id` and provide sorted, unique JSON Pointer paths
in `delta.changed_fact_paths`. The successor's canonical fact digest must differ from its
predecessor, so causal identity cannot turn unchanged facts plus a false delta into a new
delivery. The privacy-preserving ledger retains fact digests rather than payload bodies;
it therefore enforces real digest change plus non-empty, valid delta syntax without
claiming to recompute path-level differences from discarded facts. Existing event-v1
changed-deliverable envelopes created
without the causal identity component remain valid for replay and duplicate recognition;
new preparation always uses causal identity. `ledger.v2` is unchanged. Initial stream
events may establish a first snapshot. Heartbeats and continuations are control records
and never authorize an operator-facing message. Control records cannot carry
`supersedes_event_id` or `delta`;
only a validated deliverable event may mark a predecessor superseded, and only within its
source-thread/event-class stream. Timestamps use canonical RFC 3339 UTC with an uppercase
`T` and `Z`, optional one-to-six digit fractional seconds, and no offset form. JSON Pointer
paths exclude the empty root pointer and admit `~` only as the RFC 6901 escapes `~0` or
`~1`.

`periodic_digest` is an explicitly unlinked deliverable. It rejects both
`supersedes_event_id` and `delta`, never writes predecessor or successor materialization,
and is excluded when resolving the latest causal predecessor for ordinary deliverables.
This preserves an existing `A -> B` lineage before and after a digest snapshot.

CLI input failures are contract rejections. Missing or unreadable files, malformed JSON,
non-object input, and invalid top-level builder fields return a compact
`NotificationContractError` record with exit code 2. Rejections never include the input
path, raw payload, or a traceback.

## Atomic Receive Contract

The receive ledger uses Python `sqlite3`, WAL journaling, `synchronous=FULL`, foreign keys,
a five-second busy timeout, and `BEGIN IMMEDIATE` for one-writer claim, pre-send fence, and
acknowledgement transactions.

For a new notification event, one transaction:

1. validates and deterministically reconstructs the event;
2. checks the current stream and supersession relationship;
3. inserts the immutable identity and version metadata;
4. creates an opaque claim token plus generation, persists that generation's acquisition
   timestamp, and computes a microsecond-precise expiry from the ledger's UTC runtime clock
   inside the claim transaction for an operator update or periodic digest;
5. returns `should_begin_delivery=true` to exactly one claimant while keeping
   `should_emit=false` and `operator_message_authorized=false`.

Immediately before transport, the claimant must atomically call `begin_delivery` with the
event ID, claim token, and claim generation. The transition succeeds only while that exact
claim is active and unexpired, changes the durable state to non-stealable
`delivery_in_progress`, and returns the only receipt with `should_emit=true` and
`operator_message_authorized=true`. The transport must use the stable `event_id` as its
idempotency key and must prove duplicate acceptance is suppressed. SQLite fencing alone is
not network exactly-once delivery. `started_at` must be at or after the active generation's
persisted acquisition timestamp and before its expiry; the original event `first_seen`
timestamp cannot authorize a later generation. The ledger records `started_at` from its
UTC runtime clock inside the fence transaction; callers cannot supply or backdate it.

The same transaction validates the stored payload digest and produces one canonical
`transport_identity_json` string containing only contract version, `event_id`, and
`payload_digest`. Both identifiers must already be exact strings matching `onv1_` plus 64
lowercase hexadecimal characters and `sha256:` plus 64 lowercase hexadecimal characters.
Adapters must forward this serialized string unchanged or parse it with a strict JSON
decoder; object coercion, string interpolation of mappings, bare digests, and reconstruction
from transport-local metadata are prohibited. Cross-host retries therefore serialize to
identical bytes, while invalid identity types fail before the delivery transaction commits.

Every newly issued claim generation receives an independently generated 256-bit capability
from the operating system cryptographic random source. The token is persisted before the
claim commits and is never derived from public event identity or generation metadata.
Deterministic tests may inject a private byte-source fixture; runtime callers must not
replace the secure default. Existing active `ledger.v2` tokens remain valid across restart,
while every later replacement generation receives a new unpredictable capability. Secure
token-source failure is temporary unavailability and rolls the claim transaction back; it
does not imply ledger corruption or authorize restore.

For an existing `event_id`, one transaction increments `duplicate_count`, advances
`last_seen`, records exact or semantic duplicate disposition, and returns
`should_emit=false`. A claim may be reissued only when its lease expires before
`begin_delivery`; that retry uses a new claim generation and token, fencing the expired
claimant. The replacement transaction also records the new generation's acquisition time
from the same ledger clock. Caller-supplied `seen_at` is receipt metadata for
`first_seen`/`last_seen` only; it never establishes acquisition, expiry, or takeover
eligibility and therefore cannot skew a claim fence.
Once delivery begins, no lease takeover is automatic. A crash or timeout leaves the
durable outcome explicitly `UNKNOWN`, sets reconciliation required, and authorizes no retry
unless the downstream transport proves idempotent acceptance by `event_id` through a
separate governed reconciliation. Acknowledgement requires the active event ID, token, and
generation and can follow only `delivery_in_progress`. Once accepted, every later retry
returns the stable acknowledgement and the sender must stop. Superseded events remain
suppressed. Replayed acknowledgements always set both `retry_authorized=false` and
`operator_message_authorized=false`.

SQLite `BUSY` or `LOCKED` after the bounded busy timeout is temporary authority
unavailability, not corruption. Startup and state transitions raise
`LedgerUnavailableError`, authorize no delivery, and leave the ledger untouched for a
later retry. Integrity, schema, and quick-check failures remain separate fail-closed
corruption or compatibility errors.

## Stored Data and Privacy

The SQLite ledger stores event identity, source thread, event class, contract versions,
canonical and envelope digests, first/last seen timestamps, duplicate count, disposition,
supersession/delta metadata, claim generation/acquisition state, delivery state, and
acknowledgement state. It does not store notification bodies, transport metadata, claimant
host names, secrets, or PII. Claimant identifiers are retained only as SHA-256 digests.

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
schema, missing configured file, missing required tables, SQLite open failure, or failed
`quick_check` is a terminal fail-closed condition; the receiver must not emit while state
is unknown. Automatic storage migration is forbidden. The dormant pre-adoption
`ledger.v1` test layout is rejected by `ledger.v2`; only known non-authoritative test data
may be explicitly discarded and reprovisioned. Any adopted ledger requires a separately
verified backup/migration/restore packet.

## Authority Boundary

The event and acknowledgement contracts freeze:

- `notification_only=true`
- `repository_execution_authorized=false`
- `board_mutation_authorized=false`

Neither receipt authorizes repository execution, board mutation, Discord mutation, task
mutation, or production action. A claim receipt never authorizes transport. A caller may
deliver only after its own authority check and a successful, current `begin_delivery`
receipt with `should_emit=true` and `operator_message_authorized=true`.

## Failure Mode

**Canonical-path bootstrap wedge:** reserving the configured ledger path before SQLite
schema initialization lets a handled failure or process exit leave an empty or partial file
that startup rejects and provisioning cannot replace. Build and validate at a private,
same-filesystem path, then atomically publish without replacement. Never treat a private
provision residue as authority.

**Duplicate acknowledgement amplification:** acknowledging a duplicate by creating another
operator-facing notification can turn one retry loop into two mutually amplifying message
streams. Duplicate claims and replayed acknowledgements are control-plane receipts only.
They are recorded durably but must never be routed back through the operator-notification
lane as new messages.

## Adoption Gate

Repository acceptance does not activate the feature. Runtime adoption requires all of:

1. an owner-named native sender and receiver integration point;
2. one configured `runtime/` location with single-writer ownership;
3. explicit first-time provisioning plus actual-filesystem WAL, lock, online-backup,
   integrity, restore, and replay proof;
4. a transport adapter that requires the pre-send fence, uses `event_id` as its mandatory
   downstream idempotency key, and validates token-plus-generation acknowledgement before
   stopping retries;
5. observability for rejected/corrupt/unknown state that does not disclose payload facts;
6. an explicit rollback procedure and operator acceptance.

Until those gates pass, the implementation is dormant repository capability only.

## Rollback

Before runtime adoption, rollback is deletion or revert of these repository additions.
After adoption, stop the adapter first, preserve and hash the ledger and WAL sidecars, then
revert the adapter. Do not replace the receiver with an unguarded direct-send path. A
forward fix or restore of the last verified v1 backup is required before notification
delivery resumes.
