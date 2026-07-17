# ADR: ATLAS board authority v3

- Decision ID: `ATLAS-BOARD-000`
- Program ID: `program-atlas-board-authority-v3`
- Lane and marker ID: `lane-atlas-board-authority-v3`
- Status: contract freeze in review; runtime activation not started
- Measurement: `UNMEASURED`; zero Full-System audit points
- Base: `4617c67b367b04dbc287ab2b20b23469e3ec37b7`

## Decision

The Atlas-local `CardRecord` / `CardEvent` ledger is the authoritative planning and engineering-closure store. DiscordOS is an asynchronous, idempotent projection adapter with exact touched-card readback. Atlas Control is a generated read model and UI, never a second authority.

Engineering closes when one local SQLite transaction accepts a succeeded `ExecutionReceipt`, appends and materializes the card mutation, durably enqueues its projection, and persists a `BoardCommitReceipt`. Discord projection lag or failure remains visible but never reopens or blocks that accepted engineering closure.

This is an additive v3 family. It does not modify, reinterpret, migrate, supersede, or award new adoption credit to any v2 contract, fixture, adoption receipt, native correlation implementation, native correlation test, or historical marker.

## Scope and explicit non-goals

ATLAS-BOARD-000 freezes schemas, semantics, storage and authority ADRs, compatibility rules, failure behavior, proof gates, ownership, and packet registration only. It does not create a SQLite database, write a board, capture or import the live v2 authority snapshot, start a process, add a runtime activation step, implement a dispatcher, build a UI, create a projection index, supervise a resource, or perform cutover.

The selected placement is:

| Surface | Owner | Placement | Authority |
| --- | --- | --- | --- |
| Card ledger, materialization, outbox, local receipts, backups and JSONL export | ATLAS root | `runtime/atlas/board` | Authoritative |
| Atlas Control generated board read model | ATLAS root | `runtime/atlas/control` | Non-authoritative projection |
| Private read-only operator UI | Playbook Observer | loopback only | Consumer of Atlas Control |
| Discord board projection and exact touched-card readback | DiscordOS | DiscordOS owner runtime | Asynchronous adapter only |

There is no new general-purpose Atlas server. Foundation does not gain a dashboard or board authority.

## Contract surfaces

| Contract | Purpose |
| --- | --- |
| `atlas.card-record.v3` | Authoritative materialized card state, current epoch/work identity, blockers, owned resources, receipts, next action, archive posture, and visible projection state. |
| `atlas.card-event.v3` | Immutable, sequenced, idempotent event carrying the expected version, succeeded execution receipt, deterministic materialization operations, and preallocated local receipt/outbox identities. |
| `atlas.board-commit-receipt.v1` | Accepted local transaction proof that closes engineering independently of projection delivery. |
| `atlas.projection-delivery.v1` | Durable DiscordOS outbox item with retry state and exact touched-card readback accounting. |
| `atlas.projection-ack.v1` | Applied, stale, failed, or `UNKNOWN` projection acknowledgement; it has no local-acceptance effect. |
| `atlas.board-authority-migration.v1` | Immutable v2 baseline, one-time import, first-v3-acceptance boundary, cutover gates, and irreversible rollback-mode transition. |
| `atlas.control-board-read-model.v1` | Deterministic generated read model with explicit availability and queued/applied/stale/failed/`UNKNOWN` counts. |
| `atlas.rollover-manifest.v1` | Predecessor/successor continuity and bounded-epoch archive gate while preserving stable standing anchors. |

All schemas declare JSON Schema Draft 2020-12 and have schema-valid plus semantic-invalid focused fixtures. Semantic validation is part of the registered artifact validator.

## Local closure transaction

One writer holding the active board-writer lease performs this exact order inside one SQLite transaction:

1. validate a succeeded `ExecutionReceipt`;
2. resolve the unique idempotency key;
3. compare-and-swap the expected `CardRecord` version;
4. append one immutable `CardEvent`;
5. materialize the next `CardRecord`;
6. enqueue one durable `ProjectionDelivery`;
7. persist one accepted `BoardCommitReceipt`;
8. commit the transaction.

An existing idempotency key returns the original accepted result and creates no second event, version, outbox row, or receipt. An expected-version mismatch rejects before append and creates no materialization, delivery, or accepted receipt. Any failure before commit rolls back all transaction-owned effects.

Event sequence is monotonic and immutable. Card version equals `expected_version + 1`. Replay orders events by event sequence, applies the frozen deterministic operations, verifies each resulting record digest, and fails closed on gaps, duplicates, version drift, or digest drift. JSONL export uses canonical UTF-8/LF serialization and is the canonical portable audit/export form; it is not transaction authority.

## Storage ADR

The selected local transaction engine is Python standard-library `sqlite3` with:

- `journal_mode=WAL`;
- `synchronous=FULL`;
- exactly one application writer enforced by the board-writer lease;
- atomic event append, record materialization, outbox enqueue, and commit-receipt persistence;
- online backup; and
- integrity-check plus deterministic replay restore gates before a restored database may become authoritative.

The database, WAL, shared-memory file, online backups, exports, and restore staging belong under `runtime/atlas/board`. Generated Atlas Control state belongs under `runtime/atlas/control`. These runtime paths remain excluded from default source snapshots.

ATLAS-BOARD-000 does not claim that WAL locking, durability, filesystem semantics, online backup, integrity check, or restore behavior works on the target path. Exact target-path filesystem/WAL proof is an ATLAS-BOARD-001 activation gate.

Alternatives rejected:

- JSONL-only transaction authority loses atomic multi-surface commit and safe concurrent read behavior.
- DiscordOS authority makes engineering closure depend on an external projection plane.
- A second Atlas service or Foundation dashboard duplicates existing component roles.
- Multiple SQLite writers weaken deterministic lease and failure semantics without current need.

## Projection and readback semantics

`ProjectionDelivery` is committed atomically with local acceptance, then processed asynchronously. `ProjectionAck` is separate from `BoardCommitReceipt` and never changes whether engineering is closed.

Visible projection states are exactly `queued`, `applied`, `stale`, `failed`, and `UNKNOWN`. Unavailable evidence is always `UNKNOWN`; it is never converted to zero requests, healthy state, applied state, or empty-board truth.

Every delivery and acknowledgement binds card, event, sequence, version, idempotency key, attempt count, and payload digest. Critical-path readback fetches the exact touched card only and records request count plus response digest. Full-board scans are scheduled integrity work outside engineering closure. A partial projection failure retries only the failed delivery; it never replays the accepted local transaction or unrelated cards.

## Failure matrix

| Failure | Local result | Projection result | Required evidence |
| --- | --- | --- | --- |
| Execution receipt invalid or not succeeded | Reject before transaction mutation | No delivery | Validation error |
| Duplicate idempotency key | Return original accepted result | No duplicate delivery | Original receipt identity/digest |
| Expected-version mismatch | Reject before append | No delivery | Expected and observed versions |
| Failure before SQLite commit | Roll back event, materialization, outbox, and receipt | No delivery | Failure-injection proof |
| Crash after commit and before dispatch | Engineering remains closed | `queued` until retry | Durable outbox recovery proof |
| DiscordOS unavailable | Engineering remains closed | `UNKNOWN` | Availability error; null request/readback proof |
| Exact touched-card readback differs | Engineering remains closed | `stale` | Request count and response digest |
| Projection attempt fails | Engineering remains closed | `failed`, retryable when classified | Attempt/error/next-attempt evidence |
| Full scan unavailable | No effect | Touched-card state unchanged | Scheduled integrity work remains separate |
| Restore integrity or replay fails | Restored DB cannot become authority | No dispatch from candidate restore | Integrity/replay rejection receipt |
| Writer lease conflict | Second writer rejected | No delivery | Lease-holder and contender evidence |

## Compatibility, import, cutover and rollback

The protected v2/historical/native-correlation path set is frozen at base `4617c67b367b04dbc287ab2b20b23469e3ec37b7`:

- file count: `63`;
- path-set digest: `sha256:b7e427c102012241b71a296dba55c95ef64aa10f42cd9fdb75d75091bc9c77fe`;
- Git tree-input digest: `sha256:736271a2e95b5151b57bc6a34db732c49deee8e24ee3dedb4494575044528609`.

The selection rule and exact digests are frozen in `docs/registry/ATLAS-BOARD-AUTHORITY-MIGRATION.v1.json`. The live v2 authority snapshot remains `UNKNOWN` in this packet. ATLAS-BOARD-001 must capture an exact content-addressed source snapshot, verify it, and import it once under the registered import id and idempotency key. Baseline import emits deterministic v3 events and must prove byte-identical replay.

Before the first accepted v3 `BoardCommitReceipt`, an explicit rollback may return authority to v2. The first accepted v3 receipt is the irreversible authority boundary. After it, rollback means validated backup restore and event replay within v3 only. Silent authority reversion to v2 is forbidden.

ATLAS-CUTOVER-001 requires verified import, SQLite target-path proof, backup/restore proof, one-writer proof, projection and readback proof, Atlas Control proof, observer privacy/loopback proof, and an explicit cutover receipt. No condition in this ADR performs or pre-approves cutover.

## Rollover and archive policy

Every `RolloverManifest` includes predecessor and successor epoch identity, event sequence, card/job/lease correlation, branch/head/worktree/status, blockers, owned resources, receipt digests, next action, context digest, successor reconstruction proof, and an archive gate.

Stable standing anchors such as ATLAS MAIN remain unarchived. A bounded predecessor epoch becomes archive-eligible only after the successor has reconstructed the same context digest and exact continuity/readback is verified. Archiving a task never archives its standing anchor or deletes ledger history.

## Privacy and retention

- Secrets, access tokens, authentication material, payment data, raw private messages, and unrelated user data are forbidden in card bodies, events, projection payloads, JSONL exports, and read models.
- Projection payloads contain only the minimum card fields required by DiscordOS; local receipts are referenced by identity and digest rather than copied wholesale.
- Atlas Control exposes read-only state on loopback through Playbook Observer. No public, Foundation, or general-purpose server exposure is authorized.
- Events, accepted receipts, migration boundaries, and rollover manifests are durable audit records. Corrections append superseding events; ordinary repair never rewrites history.
- Runtime databases, WAL files, backups, and exports remain local runtime state and are excluded from source packaging. Backup deletion or retention contraction requires a separately authorized retention decision; this packet deletes nothing.
- A legally or operationally required privacy erasure needs a separately approved, receipt-backed redaction/compaction design. It is not implemented here.

## Fixed activation proof gates

These gates are named proof obligations, not a denominator and not percentages:

1. `BOARD-PROOF-SCHEMA-SEMANTICS` - all eight schemas and semantic failure cases.
2. `BOARD-PROOF-IDEMPOTENCY-CAS` - duplicate lookup and stale expected-version rejection.
3. `BOARD-PROOF-ATOMIC-FAILURE` - failure injection at every pre-commit boundary.
4. `BOARD-PROOF-DETERMINISTIC-REPLAY` - byte-stable JSONL and state replay.
5. `BOARD-PROOF-V2-IMPORT-ONCE` - exact content-addressed snapshot and single import.
6. `BOARD-PROOF-SQLITE-TARGET-PATH` - WAL/FULL/locking/filesystem evidence on the actual runtime path.
7. `BOARD-PROOF-BACKUP-RESTORE` - online backup, integrity check, replay, and rejection gates.
8. `BOARD-PROOF-ONE-WRITER-LEASE` - contention, expiry, recovery, and no split brain.
9. `BOARD-PROOF-PROJECTION-RETRY` - partial retry without local replay.
10. `BOARD-PROOF-TOUCHED-CARD-READBACK` - exact card and request-count proof.
11. `BOARD-PROOF-UNKNOWN` - unavailable never becomes zero or healthy.
12. `BOARD-PROOF-CONTROL-READ-MODEL` - deterministic generated projection with no authority drift.
13. `BOARD-PROOF-ROLLOVER` - successor reconstruction before bounded-epoch archive.
14. `BOARD-PROOF-CUTOVER-ROLLBACK` - first-v3 boundary and v3-only post-boundary restore/replay.

## Registered packet waves

All work remains `UNMEASURED`. Fixed packet status is recorded in the canonical Full-System lane registry; packet count does not become a denominator.

- Wave 1, parallel only after ATLAS-BOARD-000 merges, one writer per repository: `ATLAS-BOARD-001`, `STACK-BOARD-001`, `DOS-PROJ-001`, `LIFE-SUP-001`.
- Wave 2: `ATLAS-CONTROL-001`, `CORTEX-BOARD-001`, `STACK-SUP-001` then `STACK-ROLL-001`, `DOS-PROJ-002`, and optional `ATLAS-HIST-001` only after privacy, deduplication, and rollover contracts are accepted.
- Wave 3, serialized: `ATLAS-CUTOVER-001`, `DOS-DEBT-001`, `ATLAS-BOARD-002`.

This is existing preparatory Atlas Control/board-authority governance and is allowed before the held Full-System closing audit. It contributes zero audit points and does not create a ninth runtime activation step.
