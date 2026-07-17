# ATLAS-MSG-IDEMPOTENCY-001 Implementation Receipt

Date: 2026-07-17
Status: implementation complete; runtime adoption held
Authority: bounded Atlas root repository packet

## Problem

Unchanged cross-task or cross-host delivery retries can replay into FAWXZZY MESSAGES because
transport identity is not durable logical identity and acknowledgement replay can create a
second notification stream.

## Repository Result

- Frozen deterministic event and acknowledgement contracts.
- Added a transport-free event builder and SQLite receive ledger using WAL, FULL
  synchronous durability, one-writer claim transactions, token-plus-generation pre-send
  fencing, stable acknowledgement identities, and fail-closed schema/integrity checks.
- Normal startup opens only a previously provisioned ledger and cannot recreate a missing
  authority file; first-time provisioning is a separate exclusive operation.
- `notification_kind` is part of deterministic event identity, preserving same-kind
  cross-host retries while separating control and operator delivery semantics.
- Durable `ledger.v2` stores each active generation's acquisition timestamp, captures
  delivery start from its runtime clock, and rejects starts outside the current lease.
- Claim acquisition and expiry use that ledger clock inside the claim transaction;
  caller-supplied `seen_at` is retained only as first/last-seen receipt metadata.
- Claim receipts never authorize transport. Only an atomic, unexpired `begin_delivery`
  transition enters non-stealable `delivery_in_progress` and authorizes one transport call.
- A transport crash after fencing remains explicit `UNKNOWN` and reconciliation-required;
  automatic lease takeover is forbidden without downstream `event_id` dedupe evidence.
- Exact and semantic duplicates are recorded without operator-message authorization.
- Changed facts require supersession and machine-readable delta paths; only typed periodic
  digests may replay an unlinked full snapshot.
- Heartbeats and continuations are durably suppressed and cannot carry supersession
  metadata or mark any deliverable event superseded.
- Payload bodies and transport metadata are not retained in the ledger.
- Duplicate acknowledgements are stable control receipts with no message or retry authority.
- Lease expiries retain microsecond precision; timestamps are canonical RFC 3339 UTC; and
  changed-fact paths enforce RFC 6901 escape grammar with the existing no-root policy.

## Fixed Verification Units

- Draft 2020-12 compilation and semantic validation for both schemas.
- Exact duplicate suppression.
- Semantic duplicate suppression after volatile-field normalization.
- Changed-delta and supersession enforcement.
- Cross-host stable identity.
- Notification-kind identity separation.
- Missing-ledger startup rejection and exclusive first-time provisioning.
- Pre-send token/generation fencing and stale claimant rejection.
- Current-generation acquisition-time fencing across restart.
- Correlated token/generation acknowledgement stopping retry.
- Heartbeat and continuation non-replay.
- Control-kind supersession rejection across same and unrelated streams.
- Ledger-clock claim acquisition under past/future caller-clock skew and restart.
- Restart recovery.
- Corrupt and unknown schema fail-closed behavior.
- Concurrent duplicate claim with exactly one pre-send delivery candidate.
- Expired pre-send claim recovery without lease shortening.
- Durable crash-to-`UNKNOWN` recovery and non-stealable delivery state.
- Canonical timestamp and JSON Pointer grammar rejection.
- Periodic-digest full-snapshot exception.
- Payload non-retention.

Completion values are not inferred from these units. Runtime effectiveness remains
`UNKNOWN` until an owner-named adapter passes the adoption gates in the ADR.

## Local Verification Snapshot

- Notification contract/ledger suite: 30 passed in each of two final runs on Python 3.12
  and in each of two final runs on Python 3.13.
- Native task and board correlation suite: 22 passed in each of two runs.
- Root QA pipeline suite: 78 passed in each of two runs.
- Root stack validation: exit 0 in each of two runs with identical semantic results. The
  sparse clone reports 0 critical, 1 error, and 10 warnings; the error is the existing
  `repos/repo-backups` archive-present-state mismatch, outside this packet.
- Broad root Python discovery: reproducibly did not pass in this sparse clone. Both runs
  executed 1,481 tests and returned 150 failures, 102 errors, and 1 skip across unrelated
  owner-inventory, live-governance, and simulation-state surfaces. No broad-suite pass is
  claimed.
- Exact allowlist, Draft 2020-12 schemas, JSON/YAML parsing, Python syntax, UTF-8/LF,
  whitespace, credential, and machine-path checks passed.

## Protected Boundaries

This packet does not send any message, activate any runtime, create a non-test SQLite file,
start a daemon/service/scheduler, mutate a board or Discord, edit an owner repository, or
touch Supabase, Vercel, production, secrets, or the canonical Atlas checkout.

The contracts explicitly deny repository-execution and board-mutation authority. The new
CI lane validates repository code only.

## Adoption and Rollback

Adoption is held until the native sender/receiver owner, runtime path, filesystem WAL and
backup/restore proof, pre-send fence, mandatory downstream `event_id` dedupe, privacy-safe
observability, reconciliation procedure, and rollback owner are named and verified. Before
adoption, rollback is a repository revert. After adoption, stop the adapter, preserve and
hash the ledger plus WAL sidecars, then restore or forward-fix v1 before resuming; never
fall back to an unguarded direct-send path.

## Failure Mode

`Duplicate acknowledgement amplification`: emitting acknowledgements of duplicates as new
operator notifications can amplify the original incident. Duplicate and replayed ack
receipts must remain control-plane-only.
