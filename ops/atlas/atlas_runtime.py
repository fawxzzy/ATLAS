"""Small durable ATLAS runtime core.

This is deliberately adapter-neutral.  It owns durable task truth, scoped
leases, idempotent receipts, and atomic successor scheduling; a worker adapter
is responsible for doing the actual work.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


STATES = {
    "QUEUED", "CLAIMED", "RUNNING", "WAITING_EXTERNAL", "WAITING_MANUAL",
    "PAUSED_USAGE", "PAUSED_RUNTIME", "BLOCKED_DEPENDENCY", "SUCCEEDED",
    "FAILED", "CANCELLED", "SUPERSEDED", "UNKNOWN",
}

CONTINUATION_PACKET_STATES = {
    "BLOCKED_AUTHORIZATION", "BLOCKED_COST", "BLOCKED_DEPENDENCY",
    "DEAD_LETTER", "DISPATCH_PENDING", "ACTIVE", "READY",
    "RESUMABLE_QUEUED", "SETTLED", "WAITING_CONFLICT",
}
CONTINUATION_OUTBOX_STATES = {
    "PENDING", "LEASED", "DISPATCHED", "CONFIRMED", "DEAD_LETTER",
}
CONTINUATION_DESIRED_STATES = {
    "ACTIVE_COMPUTE", "DISPATCH_PENDING", "QUEUED", "TERMINAL",
    "WAITING_AUTHORIZATION", "WAITING_COST", "WAITING_EXTERNAL",
}
CONTINUATION_OBSERVED_STATES = {
    "ACTIVE_COMPUTE", "EXPECTED_IDLE", "TERMINAL", "UNEXPECTED_IDLE",
    "UNKNOWN",
}
RESUMABLE_TRIGGER_FAILURES = {"CAPACITY_EXHAUSTED", "TOKEN_EXHAUSTED"}
_CONTEXT_FORBIDDEN_KEYS = {
    "api_key", "credential", "password", "prompt", "raw", "secret", "token",
    "transcript", "user_content", "output",
}
_DRIVE_RELATIVE_PATH = re.compile(r"^[A-Za-z]:[^\\/].*")
_PROTOTYPE_POLLUTION_KEYS = {"__proto__", "constructor", "prototype"}


@dataclass(frozen=True)
class Task:
    task_id: str
    lane: str
    state: str
    priority: int
    scope: str
    depends_on: tuple[str, ...]
    successor_ids: tuple[str, ...]


@dataclass(frozen=True)
class WorkerLease:
    task_id: str
    worker_id: str
    run_id: str
    scope: str
    expires_at: float
    heartbeat_at: float


@dataclass(frozen=True)
class RecoveryDisposition:
    """A truthful handoff for work that needs a runtime/operator action."""

    task_id: str
    state: str
    disposition: str


@dataclass(frozen=True)
class WatchdogReservation:
    """One durable watchdog run reservation."""

    name: str
    reservation_id: str
    reserved_at: float
    expires_at: float


@dataclass(frozen=True)
class ContinuationOutboxItem:
    trigger_key: str
    owner_id: str
    binding_epoch: int
    packet_id: str
    thread_id: str
    context_pack_id: str
    payload_digest: str
    attempt_count: int
    leased_until: float


@dataclass(frozen=True)
class ContinuationCommit:
    packet_id: str
    successor_packet_id: str | None
    trigger_key: str | None
    owner_revision: int
    replayed: bool


class AtlasRuntime:
    """SQLite/WAL-backed queue and truth store for one ATLAS runtime."""

    def __init__(self, database: str | Path):
        self.database = str(database)
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=5000")
        self._init_schema()

    def close(self) -> None:
        self.db.close()

    def _init_schema(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
              task_id TEXT PRIMARY KEY,
              lane TEXT NOT NULL,
              state TEXT NOT NULL CHECK(state IN (
                'QUEUED','CLAIMED','RUNNING','WAITING_EXTERNAL','WAITING_MANUAL',
                'PAUSED_USAGE','PAUSED_RUNTIME','BLOCKED_DEPENDENCY','SUCCEEDED',
                'FAILED','CANCELLED','SUPERSEDED','UNKNOWN')),
              priority INTEGER NOT NULL DEFAULT 0,
              scope TEXT NOT NULL,
              depends_on TEXT NOT NULL DEFAULT '[]',
              successor_ids TEXT NOT NULL DEFAULT '[]',
              created_at REAL NOT NULL,
              updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS leases (
              task_id TEXT PRIMARY KEY REFERENCES tasks(task_id) ON DELETE CASCADE,
              worker_id TEXT NOT NULL,
              run_id TEXT NOT NULL,
              scope TEXT NOT NULL,
              acquired_at REAL NOT NULL,
              heartbeat_at REAL NOT NULL,
              expires_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
              event_id TEXT PRIMARY KEY,
              payload_digest TEXT NOT NULL,
              task_id TEXT,
              kind TEXT NOT NULL,
              payload TEXT NOT NULL,
              created_at REAL NOT NULL,
              UNIQUE(event_id, payload_digest)
            );
            CREATE INDEX IF NOT EXISTS tasks_runnable ON tasks(state, priority DESC);
            CREATE INDEX IF NOT EXISTS leases_expiry ON leases(expires_at);
            CREATE TABLE IF NOT EXISTS watchdog_state (
              name TEXT PRIMARY KEY,
              last_checked_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS watchdog_runs (
              reservation_id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              state TEXT NOT NULL CHECK(state IN (
                'IN_PROGRESS','SUCCEEDED','ABANDONED')),
              reserved_at REAL NOT NULL,
              expires_at REAL,
              terminal_at REAL,
              CHECK(state!='IN_PROGRESS' OR expires_at IS NOT NULL)
            );
            CREATE UNIQUE INDEX IF NOT EXISTS watchdog_one_in_progress
              ON watchdog_runs(name) WHERE state='IN_PROGRESS';
            CREATE INDEX IF NOT EXISTS watchdog_runs_name_state
              ON watchdog_runs(name, state, reserved_at);
            CREATE TABLE IF NOT EXISTS watchdog_receipt_sets (
              reservation_id TEXT PRIMARY KEY
                REFERENCES watchdog_runs(reservation_id) ON DELETE CASCADE,
              receipt_count INTEGER NOT NULL CHECK(receipt_count >= 0),
              receipt_set_digest TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS continuation_owners (
              owner_id TEXT PRIMARY KEY,
              thread_id TEXT NOT NULL UNIQUE,
              binding_epoch INTEGER NOT NULL CHECK(binding_epoch >= 1),
              desired_state TEXT NOT NULL CHECK(desired_state IN (
                'ACTIVE_COMPUTE','DISPATCH_PENDING','QUEUED','TERMINAL',
                'WAITING_AUTHORIZATION','WAITING_COST','WAITING_EXTERNAL')),
              observed_state TEXT NOT NULL CHECK(observed_state IN (
                'ACTIVE_COMPUTE','EXPECTED_IDLE','TERMINAL','UNEXPECTED_IDLE','UNKNOWN')),
              revision INTEGER NOT NULL CHECK(revision >= 0),
              active_turn_id TEXT,
              evidence_at REAL,
              created_at REAL NOT NULL,
              updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS continuation_context_packs (
              context_pack_id TEXT PRIMARY KEY,
              payload TEXT NOT NULL,
              payload_digest TEXT NOT NULL UNIQUE,
              created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS continuation_packets (
              packet_id TEXT PRIMARY KEY,
              owner_id TEXT NOT NULL REFERENCES continuation_owners(owner_id),
              state TEXT NOT NULL CHECK(state IN (
                'BLOCKED_AUTHORIZATION','BLOCKED_COST','BLOCKED_DEPENDENCY',
                'DEAD_LETTER','DISPATCH_PENDING','ACTIVE','READY',
                'RESUMABLE_QUEUED','SETTLED','WAITING_CONFLICT')),
              priority INTEGER NOT NULL,
              conflict_key TEXT NOT NULL,
              after_packet_id TEXT,
              context_pack_id TEXT NOT NULL REFERENCES continuation_context_packs(context_pack_id),
              authorization_kind TEXT NOT NULL,
              cost_kind TEXT NOT NULL,
              logical_identity TEXT NOT NULL UNIQUE,
              content_digest TEXT NOT NULL,
              terminal_digest TEXT,
              created_at REAL NOT NULL,
              updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS continuation_claims (
              conflict_key TEXT PRIMARY KEY,
              packet_id TEXT NOT NULL UNIQUE REFERENCES continuation_packets(packet_id),
              owner_id TEXT NOT NULL REFERENCES continuation_owners(owner_id),
              binding_epoch INTEGER NOT NULL,
              claimed_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS continuation_outbox (
              trigger_key TEXT PRIMARY KEY,
              owner_id TEXT NOT NULL REFERENCES continuation_owners(owner_id),
              binding_epoch INTEGER NOT NULL,
              packet_id TEXT NOT NULL REFERENCES continuation_packets(packet_id),
              context_pack_id TEXT NOT NULL REFERENCES continuation_context_packs(context_pack_id),
              payload_digest TEXT NOT NULL,
              state TEXT NOT NULL CHECK(state IN (
                'PENDING','LEASED','DISPATCHED','CONFIRMED','DEAD_LETTER')),
              attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count >= 0),
              lease_owner TEXT,
              leased_until REAL,
              dispatched_at REAL,
              confirmation_deadline REAL,
              delivery_method TEXT,
              thread_id TEXT,
              turn_id TEXT,
              error_class TEXT,
              created_at REAL NOT NULL,
              updated_at REAL NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS continuation_one_open_trigger
              ON continuation_outbox(packet_id)
              WHERE state IN ('PENDING','LEASED','DISPATCHED');
            CREATE INDEX IF NOT EXISTS continuation_outbox_ready
              ON continuation_outbox(state, created_at);
            CREATE TABLE IF NOT EXISTS continuation_metrics (
              metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
              owner_id TEXT,
              packet_id TEXT,
              name TEXT NOT NULL,
              value REAL NOT NULL,
              created_at REAL NOT NULL
            );
            """
        )
        columns = {row["name"] for row in self.db.execute("PRAGMA table_info(tasks)")}
        if "depends_on" not in columns:
            self.db.execute("ALTER TABLE tasks ADD COLUMN depends_on TEXT NOT NULL DEFAULT '[]'")
        outbox_columns = {
            row["name"] for row in self.db.execute("PRAGMA table_info(continuation_outbox)")
        }
        if "delivery_method" not in outbox_columns:
            self.db.execute("ALTER TABLE continuation_outbox ADD COLUMN delivery_method TEXT")
        watchdog_columns = {
            row["name"] for row in self.db.execute("PRAGMA table_info(watchdog_runs)")
        }
        if "expires_at" not in watchdog_columns:
            # A pre-migration in-progress run has no trustworthy issued expiry.
            # Leave it fail-closed until its owner explicitly abandons it.
            self.db.execute("ALTER TABLE watchdog_runs ADD COLUMN expires_at REAL")
        self.db.executescript(
            """
            CREATE TRIGGER IF NOT EXISTS watchdog_in_progress_requires_expiry_insert
              BEFORE INSERT ON watchdog_runs
              WHEN NEW.state='IN_PROGRESS' AND NEW.expires_at IS NULL
            BEGIN
              SELECT RAISE(ABORT, 'in-progress watchdog run requires expires_at');
            END;
            CREATE TRIGGER IF NOT EXISTS watchdog_in_progress_requires_expiry_update
              BEFORE UPDATE ON watchdog_runs
              WHEN NEW.state='IN_PROGRESS' AND NEW.expires_at IS NULL
            BEGIN
              SELECT RAISE(ABORT, 'in-progress watchdog run requires expires_at');
            END;
            """
        )

    def _record_event(self, *, event_id: str, digest: str, task_id: str, kind: str,
                      payload: Mapping[str, object], now: float) -> None:
        existing = self.db.execute(
            "SELECT payload_digest FROM events WHERE event_id=?", (event_id,)
        ).fetchone()
        if existing:
            if existing["payload_digest"] != digest:
                raise ValueError("event_id is already bound to a different payload digest")
            return
        self.db.execute(
            "INSERT INTO events(event_id,payload_digest,task_id,kind,payload,created_at) VALUES(?,?,?,?,?,?)",
            (event_id, digest, task_id, kind, json.dumps(payload, sort_keys=True), now),
        )

    @staticmethod
    def digest(payload: Mapping[str, object]) -> str:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return "sha256:" + hashlib.sha256(body).hexdigest()

    def enqueue(
        self,
        task_id: str,
        *,
        lane: str,
        scope: str,
        priority: int = 0,
        depends_on: Iterable[str] = (),
        successor_ids: Iterable[str] = (),
        event_id: str | None = None,
        payload: Mapping[str, object] | None = None,
    ) -> bool:
        """Insert a task and event idempotently. Returns whether task was new."""
        now = time.time()
        successors = tuple(successor_ids)
        dependencies = tuple(depends_on)
        event_id = event_id or f"task:{task_id}"
        event_payload = dict(payload or {})
        # This is the canonical enqueue identity. Do not allow an idempotency
        # key to conceal priority, dependency, or successor-topology drift.
        event_payload.update({
            "task_id": task_id,
            "lane": lane,
            "scope": scope,
            "priority": priority,
            "depends_on": dependencies,
            "successor_ids": successors,
        })
        digest = self.digest(event_payload)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            existing = self.db.execute(
                "SELECT task_id FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            self._record_event(event_id=event_id, digest=digest, task_id=task_id,
                               kind="ENQUEUE", payload=event_payload, now=now)
            if existing:
                self.db.execute("COMMIT")
                return False
            if scope == "":
                raise ValueError("scope must be non-empty")
            dependency_rows = [self.db.execute("SELECT state FROM tasks WHERE task_id=?", (item,)).fetchone()
                               for item in dependencies]
            state = "QUEUED" if not dependencies or all(row and row["state"] == "SUCCEEDED" for row in dependency_rows) else "BLOCKED_DEPENDENCY"
            self.db.execute(
                "INSERT INTO tasks(task_id,lane,state,priority,scope,depends_on,successor_ids,created_at,updated_at)"
                " VALUES(?,?,?,?,?,?,?,?,?)",
                (task_id, lane, state, priority, scope, json.dumps(dependencies), json.dumps(successors), now, now),
            )
            self.db.execute("COMMIT")
            return True
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def claim(self, *, worker_id: str, run_id: str, lease_seconds: float = 300) -> WorkerLease | None:
        """Claim the highest-priority runnable task with a scoped single-writer lock."""
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT t.* FROM tasks t WHERE t.state='QUEUED' AND NOT EXISTS "
                "(SELECT 1 FROM leases l WHERE l.scope=t.scope AND l.expires_at>?) "
                "ORDER BY t.priority DESC, t.created_at LIMIT 1", (now,)
            ).fetchone()
            if not row:
                self.db.execute("COMMIT")
                return None
            expires = now + lease_seconds
            self.db.execute(
                "UPDATE tasks SET state='RUNNING', updated_at=? WHERE task_id=?",
                (now, row["task_id"]),
            )
            self.db.execute(
                "INSERT INTO leases(task_id,worker_id,run_id,scope,acquired_at,heartbeat_at,expires_at)"
                " VALUES(?,?,?,?,?,?,?)",
                (row["task_id"], worker_id, run_id, row["scope"], now, now, expires),
            )
            self.db.execute("COMMIT")
            return WorkerLease(row["task_id"], worker_id, run_id, row["scope"], expires, now)
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def heartbeat(self, *, task_id: str, worker_id: str, run_id: str, lease_seconds: float = 300) -> WorkerLease:
        now = time.time()
        expires = now + lease_seconds
        self.db.execute("BEGIN IMMEDIATE")
        try:
            cur = self.db.execute(
                "UPDATE leases SET heartbeat_at=?, expires_at=? WHERE task_id=? AND worker_id=? AND run_id=? AND expires_at>?",
                (now, expires, task_id, worker_id, run_id, now),
            )
            if cur.rowcount != 1:
                raise KeyError("lease not found, expired, or worker/run identity mismatched")
            row = self.db.execute("SELECT scope FROM leases WHERE task_id=?", (task_id,)).fetchone()
            self.db.execute("COMMIT")
            return WorkerLease(task_id, worker_id, run_id, row["scope"], expires, now)
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def complete(self, *, task_id: str, worker_id: str, run_id: str,
                 state: str = "SUCCEEDED", receipt: Mapping[str, object] | None = None) -> tuple[str, ...]:
        """Atomically settle a lease, record its receipt, and enqueue successors."""
        if state not in STATES or state in {"QUEUED", "CLAIMED", "RUNNING"}:
            raise ValueError("completion requires a terminal or waiting state")
        now = time.time()
        receipt = dict(receipt or {})
        receipt.update({"task_id": task_id, "state": state})
        event_id = str(receipt.get("event_id") or f"receipt:{task_id}:{run_id}")
        digest = self.digest(receipt)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT t.*, l.worker_id, l.run_id FROM tasks t JOIN leases l ON l.task_id=t.task_id"
                " WHERE t.task_id=? AND l.expires_at>?", (task_id, now)
            ).fetchone()
            if not row:
                task = self.db.execute(
                    "SELECT state, successor_ids FROM tasks WHERE task_id=?", (task_id,)
                ).fetchone()
                event = self.db.execute(
                    "SELECT payload_digest FROM events WHERE event_id=?", (event_id,)
                ).fetchone()
                if task and event and event["payload_digest"] == digest and task["state"] == state:
                    self.db.execute("COMMIT")
                    return tuple(json.loads(task["successor_ids"])) if state == "SUCCEEDED" else ()
                if event and event["payload_digest"] != digest:
                    raise ValueError("event_id is already bound to a different payload digest")
                raise KeyError("lease not found, expired, or receipt does not match settled task")
            if row["worker_id"] != worker_id or row["run_id"] != run_id:
                raise KeyError("lease not found or worker/run identity mismatched")
            self._record_event(event_id=event_id, digest=digest, task_id=task_id,
                               kind="RECEIPT", payload=receipt, now=now)
            successors = tuple(json.loads(row["successor_ids"]))
            self.db.execute("UPDATE tasks SET state=?, updated_at=? WHERE task_id=?", (state, now, task_id))
            self.db.execute("DELETE FROM leases WHERE task_id=?", (task_id,))
            if state == "SUCCEEDED":
                for successor in successors:
                    successor_row = self.db.execute(
                        "SELECT depends_on FROM tasks WHERE task_id=?", (successor,)
                    ).fetchone()
                    if not successor_row:
                        raise KeyError(f"successor task is absent: {successor}")
                    dependencies = tuple(json.loads(successor_row["depends_on"]))
                    if task_id not in dependencies:
                        raise ValueError(f"successor {successor} does not declare dependency on {task_id}")
                    dependency_status = self.db.execute(
                        "SELECT COUNT(*) AS total, "
                        "SUM(CASE WHEN state='SUCCEEDED' THEN 1 ELSE 0 END) AS succeeded "
                        "FROM tasks WHERE task_id IN ({})".format(
                            ",".join("?" for _ in dependencies)
                        ), dependencies
                    ).fetchone()
                    # An absent dependency is unresolved, not implicitly
                    # successful. It may be registered later, but it cannot
                    # release this successor until it has itself succeeded.
                    if (dependency_status["total"] == len(dependencies)
                            and dependency_status["succeeded"] == len(dependencies)):
                        self.db.execute(
                            "UPDATE tasks SET state='QUEUED', updated_at=? WHERE task_id=? AND state='BLOCKED_DEPENDENCY'",
                            (now, successor),
                        )
            self.db.execute("COMMIT")
            return successors
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def reconcile(self, *, now: float | None = None, heartbeat_timeout: float = 120) -> list[str]:
        """Convert orphaned/stale RUNNING tasks to truthful PAUSED_RUNTIME.

        This transaction is independent of watchdog finalization by design. Its
        conditional RUNNING-to-PAUSED_RUNTIME transition and lease deletion are
        idempotent, so overlapping reconcilers cannot repeat or undo durable
        work.
        """
        now = time.time() if now is None else now
        paused: list[str] = []
        self.db.execute("BEGIN IMMEDIATE")
        try:
            rows = self.db.execute(
                "SELECT t.task_id, l.heartbeat_at, l.expires_at FROM tasks t LEFT JOIN leases l ON l.task_id=t.task_id"
                " WHERE t.state='RUNNING'"
            ).fetchall()
            for row in rows:
                if row["heartbeat_at"] is None or row["expires_at"] <= now or now - row["heartbeat_at"] > heartbeat_timeout:
                    self.db.execute("UPDATE tasks SET state='PAUSED_RUNTIME', updated_at=? WHERE task_id=?", (now, row["task_id"]))
                    self.db.execute("DELETE FROM leases WHERE task_id=?", (row["task_id"],))
                    paused.append(row["task_id"])
            self.db.execute("COMMIT")
            return paused
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def recovery_dispositions(self) -> tuple[RecoveryDisposition, ...]:
        """Expose restartable truth without silently dispatching it."""
        rows = self.db.execute(
            "SELECT task_id, state FROM tasks WHERE state IN ('QUEUED', 'PAUSED_RUNTIME') "
            "ORDER BY priority DESC, created_at"
        ).fetchall()
        return tuple(
            RecoveryDisposition(
                task_id=row["task_id"],
                state=row["state"],
                disposition=("READY_NOT_DISPATCHED" if row["state"] == "QUEUED" else "PAUSED_RUNTIME_REQUIRES_RESUME"),
            )
            for row in rows
        )

    def reserve_watchdog_tick(
        self,
        *,
        name: str,
        now: float,
        fallback_seconds: float,
        event_observed: bool,
        reservation_seconds: float | None = None,
    ) -> WatchdogReservation | None:
        """Atomically reserve one event-driven or fallback watchdog run.

        Only a terminally successful run starts the fallback cooldown. A
        failed run can be abandoned immediately, while an unclosed run becomes
        recoverable after ``reservation_seconds``.
        """
        if not name.strip():
            raise ValueError("watchdog name must be non-empty")
        if not math.isfinite(now):
            raise ValueError("now must be finite")
        if not math.isfinite(fallback_seconds) or fallback_seconds <= 0:
            raise ValueError("fallback_seconds must be positive")
        if reservation_seconds is None:
            reservation_seconds = min(60, fallback_seconds / 10)
        if not math.isfinite(reservation_seconds) or reservation_seconds <= 0:
            raise ValueError("reservation_seconds must be positive")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute(
                "UPDATE watchdog_runs SET state='ABANDONED', terminal_at=? "
                "WHERE name=? AND state='IN_PROGRESS' "
                "AND expires_at IS NOT NULL AND expires_at<=?",
                (now, name, now),
            )
            active = self.db.execute(
                "SELECT reservation_id FROM watchdog_runs "
                "WHERE name=? AND state='IN_PROGRESS'",
                (name,),
            ).fetchone()
            if active:
                self.db.execute("COMMIT")
                return None
            row = self.db.execute(
                "SELECT last_checked_at FROM watchdog_state WHERE name=?", (name,)
            ).fetchone()
            due = event_observed or row is None or now - row["last_checked_at"] >= fallback_seconds
            if not due:
                self.db.execute("COMMIT")
                return None
            reservation_id = uuid.uuid4().hex
            self.db.execute(
                "INSERT INTO watchdog_runs("
                "reservation_id,name,state,reserved_at,expires_at,terminal_at"
                ") VALUES(?,?,'IN_PROGRESS',?,?,NULL)",
                (reservation_id, name, now, now + reservation_seconds),
            )
            self.db.execute("COMMIT")
            return WatchdogReservation(
                name=name,
                reservation_id=reservation_id,
                reserved_at=now,
                expires_at=now + reservation_seconds,
            )
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def complete_watchdog_tick(
        self,
        *,
        reservation: WatchdogReservation,
        now: float,
    ) -> None:
        """Finalize a receipt-free watchdog run and begin its fallback cooldown."""
        self.finalize_watchdog_tick(reservation=reservation, receipts=(), now=now)

    def finalize_watchdog_tick(
        self,
        *,
        reservation: WatchdogReservation,
        receipts: Iterable[tuple[str, Mapping[str, object]]],
        now: float,
    ) -> tuple[bool, ...]:
        """Atomically persist a complete receipt set and settle its reservation.

        The hard deadline is checked while holding the same SQLite write
        transaction that records every receipt, marks the run successful, and
        advances the fallback cooldown. An exact replay of an already committed
        reservation is a read-only no-op; a partial or different replay fails
        closed.
        """
        if not math.isfinite(now):
            raise ValueError("now must be finite")

        prepared: list[tuple[str, str, str, Mapping[str, object]]] = []
        seen_event_ids: set[str] = set()
        for task_id, payload in receipts:
            if not isinstance(task_id, str) or not task_id.strip():
                raise ValueError("watchdog receipt task_id must be non-empty")
            event_payload = dict(payload)
            event_payload["task_id"] = task_id
            digest = self.digest(event_payload)
            event_id = "watchdog:" + digest.removeprefix("sha256:")
            if event_id in seen_event_ids:
                raise ValueError("watchdog receipt batch contains duplicate identity")
            seen_event_ids.add(event_id)
            prepared.append((event_id, digest, task_id, event_payload))

        receipt_set_body = json.dumps(
            sorted((event_id, digest) for event_id, digest, _, _ in prepared),
            separators=(",", ":"),
        ).encode()
        receipt_set_digest = "sha256:" + hashlib.sha256(receipt_set_body).hexdigest()

        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT state,terminal_at FROM watchdog_runs "
                "WHERE reservation_id=? AND name=? AND reserved_at=? AND expires_at=?",
                (
                    reservation.reservation_id,
                    reservation.name,
                    reservation.reserved_at,
                    reservation.expires_at,
                ),
            ).fetchone()
            if row and row["state"] == "SUCCEEDED":
                receipt_set = self.db.execute(
                    "SELECT receipt_count,receipt_set_digest "
                    "FROM watchdog_receipt_sets WHERE reservation_id=?",
                    (reservation.reservation_id,),
                ).fetchone()
                if (
                    receipt_set is None
                    or receipt_set["receipt_count"] != len(prepared)
                    or receipt_set["receipt_set_digest"] != receipt_set_digest
                ):
                    raise KeyError(
                        "watchdog reservation is already settled with a different receipt set"
                    )
                for event_id, digest, _, _ in prepared:
                    event = self.db.execute(
                        "SELECT payload_digest FROM events WHERE event_id=?",
                        (event_id,),
                    ).fetchone()
                    if event is None or event["payload_digest"] != digest:
                        raise KeyError(
                            "watchdog reservation receipt set is incomplete or mismatched"
                        )
                cooldown = self.db.execute(
                    "SELECT last_checked_at FROM watchdog_state WHERE name=?",
                    (reservation.name,),
                ).fetchone()
                if (
                    cooldown is None
                    or cooldown["last_checked_at"] < row["terminal_at"]
                ):
                    raise KeyError("watchdog reservation cooldown does not match completion")
                self.db.execute("COMMIT")
                return tuple(False for _ in prepared)

            if (
                row is None
                or row["state"] != "IN_PROGRESS"
                or not (reservation.reserved_at <= now < reservation.expires_at)
            ):
                raise KeyError(
                    "watchdog reservation is absent, expired, mismatched, "
                    "or no longer in progress"
                )

            inserted: list[bool] = []
            self.db.execute(
                "INSERT INTO watchdog_receipt_sets("
                "reservation_id,receipt_count,receipt_set_digest"
                ") VALUES(?,?,?)",
                (reservation.reservation_id, len(prepared), receipt_set_digest),
            )
            for event_id, digest, task_id, event_payload in prepared:
                existing = self.db.execute(
                    "SELECT payload_digest FROM events WHERE event_id=?", (event_id,)
                ).fetchone()
                self._record_event(
                    event_id=event_id,
                    digest=digest,
                    task_id=task_id,
                    kind="WATCHDOG",
                    payload=event_payload,
                    now=now,
                )
                inserted.append(existing is None)

            cur = self.db.execute(
                "UPDATE watchdog_runs SET state='SUCCEEDED', terminal_at=? "
                "WHERE reservation_id=? AND name=? AND state='IN_PROGRESS' "
                "AND reserved_at=? AND expires_at=? "
                "AND reserved_at<=? AND expires_at>?",
                (
                    now,
                    reservation.reservation_id,
                    reservation.name,
                    reservation.reserved_at,
                    reservation.expires_at,
                    now,
                    now,
                ),
            )
            if cur.rowcount != 1:
                raise KeyError(
                    "watchdog reservation is absent, expired, mismatched, "
                    "or no longer in progress"
                )
            self.db.execute(
                "INSERT INTO watchdog_state(name,last_checked_at) VALUES(?,?) "
                "ON CONFLICT(name) DO UPDATE SET last_checked_at=excluded.last_checked_at",
                (reservation.name, now),
            )
            self.db.execute("COMMIT")
            return tuple(inserted)
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def abandon_watchdog_tick(
        self,
        *,
        reservation: WatchdogReservation,
        now: float,
    ) -> bool:
        """Make a failed watchdog run immediately recoverable."""
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT state FROM watchdog_runs "
                "WHERE reservation_id=? AND name=?",
                (reservation.reservation_id, reservation.name),
            ).fetchone()
            if not row:
                raise KeyError("watchdog reservation is absent")
            if row["state"] == "ABANDONED":
                self.db.execute("COMMIT")
                return False
            if row["state"] != "IN_PROGRESS":
                raise KeyError("watchdog reservation is no longer in progress")
            self.db.execute(
                "UPDATE watchdog_runs SET state='ABANDONED', terminal_at=? "
                "WHERE reservation_id=?",
                (now, reservation.reservation_id),
            )
            self.db.execute("COMMIT")
            return True
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def watchdog_tasks(self, *, now: float) -> tuple[tuple[Task, bool], ...]:
        """Return durable liveness candidates and whether each has a valid lease."""
        rows = self.db.execute(
            "SELECT t.*, EXISTS("
            "SELECT 1 FROM leases l WHERE l.expires_at>? "
            "AND (l.task_id=t.task_id OR l.scope=t.scope)"
            ") AS has_valid_lease "
            "FROM tasks t "
            "WHERE t.state IN ('QUEUED','BLOCKED_DEPENDENCY','WAITING_MANUAL',"
            "'WAITING_EXTERNAL','PAUSED_USAGE','PAUSED_RUNTIME','UNKNOWN') "
            "ORDER BY t.priority DESC, t.created_at",
            (now,),
        ).fetchall()
        return tuple(
            (
                Task(
                    row["task_id"], row["lane"], row["state"], row["priority"], row["scope"],
                    tuple(json.loads(row["depends_on"])), tuple(json.loads(row["successor_ids"])),
                ),
                bool(row["has_valid_lease"]),
            )
            for row in rows
        )

    @staticmethod
    def _canonical_json(value: object) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def _assert_context_safe(cls, value: object, *, path: str = "$") -> None:
        """Reject context that could become a transcript or credential store."""
        if isinstance(value, Mapping):
            for key, child in value.items():
                if not isinstance(key, str):
                    raise ValueError(f"{path}: context keys must be strings")
                normalized = key.casefold().replace("-", "_")
                if normalized in _PROTOTYPE_POLLUTION_KEYS:
                    raise ValueError(f"{path}.{key}: prototype-polluting context field")
                if normalized in _CONTEXT_FORBIDDEN_KEYS or any(
                    forbidden in normalized
                    for forbidden in ("secret", "credential", "password", "raw_", "_raw", "output")
                ):
                    raise ValueError(f"{path}.{key}: forbidden context field")
                cls._assert_context_safe(child, path=f"{path}.{key}")
        elif isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                cls._assert_context_safe(child, path=f"{path}[{index}]")
        elif not isinstance(value, (str, int, float, bool, type(None))):
            raise ValueError(f"{path}: context value is not JSON-safe")
        elif isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"{path}: non-finite number is not allowed")
        elif isinstance(value, str) and _DRIVE_RELATIVE_PATH.fullmatch(value):
            raise ValueError(f"{path}: drive-relative path is semantically invalid")

    def create_context_pack(self, payload: Mapping[str, object]) -> str:
        """Persist one small content-addressed continuation context pack."""
        body = dict(payload)
        self._assert_context_safe(body)
        encoded = self._canonical_json(body).encode("utf-8")
        if len(encoded) > 32_768:
            raise ValueError("context pack exceeds 32768 bytes")
        digest = "sha256:" + hashlib.sha256(encoded).hexdigest()
        context_pack_id = "ctx_" + digest.removeprefix("sha256:")
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT payload_digest,payload FROM continuation_context_packs WHERE context_pack_id=?",
                (context_pack_id,),
            ).fetchone()
            if row:
                if row["payload_digest"] != digest or row["payload"] != encoded.decode("utf-8"):
                    raise ValueError("context pack identity collision")
            else:
                self.db.execute(
                    "INSERT INTO continuation_context_packs(context_pack_id,payload,payload_digest,created_at) "
                    "VALUES(?,?,?,?)",
                    (context_pack_id, encoded.decode("utf-8"), digest, now),
                )
            self.db.execute("COMMIT")
            return context_pack_id
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def register_continuation_owner(
        self,
        *,
        owner_id: str,
        thread_id: str,
        binding_epoch: int = 1,
    ) -> bool:
        """Register an ATLAS-owned persistent thread without creating a task."""
        if not owner_id.strip() or not thread_id.strip() or binding_epoch < 1:
            raise ValueError("owner, thread, and positive binding epoch are required")
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT thread_id,binding_epoch FROM continuation_owners WHERE owner_id=?",
                (owner_id,),
            ).fetchone()
            if row:
                if row["thread_id"] != thread_id or row["binding_epoch"] != binding_epoch:
                    raise ValueError("owner binding drift requires an explicit epoch transition")
                self.db.execute("COMMIT")
                return False
            self.db.execute(
                "INSERT INTO continuation_owners(owner_id,thread_id,binding_epoch,desired_state,"
                "observed_state,revision,created_at,updated_at) "
                "VALUES(?,?,?,'QUEUED','EXPECTED_IDLE',0,?,?)",
                (owner_id, thread_id, binding_epoch, now, now),
            )
            self.db.execute("COMMIT")
            return True
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def register_continuation_packet(
        self,
        *,
        packet_id: str,
        owner_id: str,
        conflict_key: str,
        context_pack_id: str,
        after_packet_id: str | None = None,
        priority: int = 0,
        authorization_kind: str = "AUTO_AUTHORIZED_LOCAL_ONLY",
        cost_kind: str = "LOCAL_ZERO",
        logical_identity: str | None = None,
        state: str = "READY",
    ) -> bool:
        """Register a content-bound packet; changed replay fails without caller help."""
        if state not in CONTINUATION_PACKET_STATES:
            raise ValueError("invalid continuation packet state")
        if not packet_id.strip() or not owner_id.strip() or not conflict_key.strip():
            raise ValueError("packet, owner, and conflict key are required")
        identity = logical_identity or packet_id
        definition = {
            "packet_id": packet_id,
            "owner_id": owner_id,
            "conflict_key": conflict_key,
            "context_pack_id": context_pack_id,
            "after_packet_id": after_packet_id,
            "priority": priority,
            "authorization_kind": authorization_kind,
            "cost_kind": cost_kind,
            "logical_identity": identity,
        }
        digest = self.digest(definition)
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            owner = self.db.execute(
                "SELECT owner_id FROM continuation_owners WHERE owner_id=?", (owner_id,)
            ).fetchone()
            pack = self.db.execute(
                "SELECT context_pack_id FROM continuation_context_packs WHERE context_pack_id=?",
                (context_pack_id,),
            ).fetchone()
            if not owner or not pack:
                raise KeyError("owner or context pack is absent")
            existing = self.db.execute(
                "SELECT packet_id,content_digest FROM continuation_packets "
                "WHERE packet_id=? OR logical_identity=?",
                (packet_id, identity),
            ).fetchone()
            if existing:
                if existing["packet_id"] != packet_id or existing["content_digest"] != digest:
                    raise ValueError("logical continuation identity is already bound to different content")
                self.db.execute("COMMIT")
                return False
            self.db.execute(
                "INSERT INTO continuation_packets(packet_id,owner_id,state,priority,conflict_key,"
                "after_packet_id,context_pack_id,authorization_kind,cost_kind,logical_identity,"
                "content_digest,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (packet_id, owner_id, state, priority, conflict_key, after_packet_id,
                 context_pack_id, authorization_kind, cost_kind, identity, digest, now, now),
            )
            self.db.execute("COMMIT")
            return True
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def activate_continuation_packet(self, *, packet_id: str) -> bool:
        """Claim one initial packet for an already-owned thread."""
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            packet = self.db.execute(
                "SELECT p.*,o.binding_epoch FROM continuation_packets p "
                "JOIN continuation_owners o ON o.owner_id=p.owner_id WHERE p.packet_id=?",
                (packet_id,),
            ).fetchone()
            if not packet:
                raise KeyError("continuation packet is absent")
            if packet["state"] == "ACTIVE":
                self.db.execute("COMMIT")
                return False
            if packet["state"] != "READY":
                raise ValueError("only READY continuation packets may be activated")
            self.db.execute(
                "INSERT INTO continuation_claims(conflict_key,packet_id,owner_id,binding_epoch,claimed_at) "
                "VALUES(?,?,?,?,?)",
                (packet["conflict_key"], packet_id, packet["owner_id"], packet["binding_epoch"], now),
            )
            self.db.execute(
                "UPDATE continuation_packets SET state='ACTIVE',updated_at=? WHERE packet_id=?",
                (now, packet_id),
            )
            self.db.execute(
                "UPDATE continuation_owners SET desired_state='ACTIVE_COMPUTE',"
                "observed_state='ACTIVE_COMPUTE',revision=revision+1,updated_at=? WHERE owner_id=?",
                (now, packet["owner_id"]),
            )
            self.db.execute("COMMIT")
            return True
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    @staticmethod
    def _trigger_key(*, owner_id: str, binding_epoch: int, packet_id: str,
                     context_pack_id: str, owner_revision: int) -> str:
        body = json.dumps(
            [owner_id, binding_epoch, packet_id, context_pack_id, owner_revision],
            separators=(",", ":"),
        ).encode("utf-8")
        return "trg_" + hashlib.sha256(body).hexdigest()

    def _promote_waiting_conflicts(
        self, *, now: float, conflict_keys: Iterable[str] | None = None
    ) -> tuple[dict[str, str], ...]:
        """Promote one deterministic eligible waiter per free conflict key.

        The caller owns an IMMEDIATE transaction. Claim, packet, outbox, owner,
        and metric changes therefore commit or roll back as one effect.
        """
        keys = tuple(sorted(set(conflict_keys or ())))
        key_filter = ""
        parameters: list[object] = []
        if keys:
            key_filter = " AND p.conflict_key IN ({})".format(
                ",".join("?" for _ in keys)
            )
            parameters.extend(keys)
        waiters = self.db.execute(
            "SELECT p.*,o.binding_epoch,o.revision AS owner_revision "
            "FROM continuation_packets p "
            "JOIN continuation_owners o ON o.owner_id=p.owner_id "
            "LEFT JOIN continuation_packets predecessor ON predecessor.packet_id=p.after_packet_id "
            "WHERE p.state='WAITING_CONFLICT' "
            "AND o.desired_state='QUEUED' "
            "AND (p.after_packet_id IS NULL OR predecessor.state='SETTLED')"
            + key_filter
            + " ORDER BY p.conflict_key,p.priority DESC,p.created_at,p.packet_id",
            tuple(parameters),
        ).fetchall()
        promoted_keys: set[str] = set()
        actions: list[dict[str, str]] = []
        for packet in waiters:
            conflict_key = packet["conflict_key"]
            if conflict_key in promoted_keys:
                continue
            if packet["authorization_kind"] not in {
                "AUTO_AUTHORIZED_LOCAL_ONLY", "EXPLICIT_AUTHORIZED_LOCAL_ONLY"
            } or packet["cost_kind"] not in {"LOCAL_ZERO", "NO_COST"}:
                continue
            if self.db.execute(
                "SELECT 1 FROM continuation_claims WHERE conflict_key=?", (conflict_key,)
            ).fetchone():
                continue
            if self.db.execute(
                "SELECT 1 FROM continuation_claims WHERE owner_id=?", (packet["owner_id"],)
            ).fetchone():
                continue
            if self.db.execute(
                "SELECT 1 FROM continuation_outbox WHERE owner_id=? "
                "AND state IN ('PENDING','LEASED','DISPATCHED')",
                (packet["owner_id"],),
            ).fetchone():
                continue
            next_revision = packet["owner_revision"] + 1
            trigger_key = self._trigger_key(
                owner_id=packet["owner_id"],
                binding_epoch=packet["binding_epoch"],
                packet_id=packet["packet_id"],
                context_pack_id=packet["context_pack_id"],
                owner_revision=next_revision,
            )
            payload = {
                "owner_id": packet["owner_id"],
                "binding_epoch": packet["binding_epoch"],
                "packet_id": packet["packet_id"],
                "context_pack_id": packet["context_pack_id"],
                "trigger_key": trigger_key,
            }
            self.db.execute(
                "INSERT INTO continuation_claims(conflict_key,packet_id,owner_id,binding_epoch,claimed_at) "
                "VALUES(?,?,?,?,?)",
                (conflict_key, packet["packet_id"], packet["owner_id"],
                 packet["binding_epoch"], now),
            )
            self.db.execute(
                "UPDATE continuation_packets SET state='DISPATCH_PENDING',updated_at=? "
                "WHERE packet_id=? AND state='WAITING_CONFLICT'",
                (now, packet["packet_id"]),
            )
            self.db.execute(
                "INSERT INTO continuation_outbox(trigger_key,owner_id,binding_epoch,packet_id,"
                "context_pack_id,payload_digest,state,created_at,updated_at) "
                "VALUES(?,?,?,?,?,?,'PENDING',?,?)",
                (trigger_key, packet["owner_id"], packet["binding_epoch"],
                 packet["packet_id"], packet["context_pack_id"], self.digest(payload), now, now),
            )
            self.db.execute(
                "UPDATE continuation_owners SET desired_state='DISPATCH_PENDING',"
                "observed_state='EXPECTED_IDLE',active_turn_id=NULL,revision=?,evidence_at=?,"
                "updated_at=? WHERE owner_id=?",
                (next_revision, now, now, packet["owner_id"]),
            )
            self.db.execute(
                "INSERT INTO continuation_metrics(owner_id,packet_id,name,value,created_at) "
                "VALUES(?,?,'conflict_waiter_promoted',1,?)",
                (packet["owner_id"], packet["packet_id"], now),
            )
            promoted_keys.add(conflict_key)
            actions.append({
                "packet_id": packet["packet_id"],
                "trigger_key": trigger_key,
                "action": "PROMOTED_CONFLICT_WAITER",
            })
        return tuple(actions)

    def _existing_continuation_commit(
        self, *, event_id: str, digest: str, packet_id: str
    ) -> ContinuationCommit | None:
        event = self.db.execute(
            "SELECT payload_digest,payload FROM events WHERE event_id=?", (event_id,)
        ).fetchone()
        if not event:
            return None
        if event["payload_digest"] != digest:
            raise ValueError("terminal event identity is already bound to different content")
        packet = self.db.execute(
            "SELECT state,owner_id FROM continuation_packets WHERE packet_id=?", (packet_id,)
        ).fetchone()
        if not packet or packet["state"] != "SETTLED":
            raise ValueError("terminal event exists without its settled packet postimage")
        outbox = self.db.execute(
            "SELECT x.trigger_key,x.packet_id FROM continuation_outbox x "
            "JOIN continuation_packets p ON p.packet_id=x.packet_id "
            "WHERE p.after_packet_id=? ORDER BY x.created_at DESC LIMIT 1",
            (packet_id,),
        ).fetchone()
        blocked_successors = self.db.execute(
            "SELECT packet_id FROM continuation_packets WHERE after_packet_id=? "
            "AND state IN ('BLOCKED_AUTHORIZATION','BLOCKED_COST','WAITING_CONFLICT') "
            "ORDER BY packet_id",
            (packet_id,),
        ).fetchall()
        if not outbox and len(blocked_successors) > 1:
            raise ValueError("settled replay has ambiguous blocked successor identity")
        successor_packet_id = (
            outbox["packet_id"] if outbox
            else blocked_successors[0]["packet_id"] if blocked_successors
            else None
        )
        owner = self.db.execute(
            "SELECT revision FROM continuation_owners WHERE owner_id=?", (packet["owner_id"],)
        ).fetchone()
        return ContinuationCommit(
            packet_id=packet_id,
            successor_packet_id=successor_packet_id,
            trigger_key=(outbox["trigger_key"] if outbox else None),
            owner_revision=owner["revision"],
            replayed=True,
        )

    def commit_continuation(
        self,
        *,
        packet_id: str,
        terminal_receipt: Mapping[str, object],
        expected_owner_revision: int,
        fail_after: str | None = None,
    ) -> ContinuationCommit:
        """Atomically settle, reserve a successor, and create its dispatch outbox row."""
        receipt = dict(terminal_receipt)
        event_id = str(receipt.get("event_id") or "")
        if not event_id.strip():
            raise ValueError("terminal receipt requires event_id")
        receipt["packet_id"] = packet_id
        digest = self.digest(receipt)
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            replay = self._existing_continuation_commit(
                event_id=event_id, digest=digest, packet_id=packet_id
            )
            if replay:
                self.db.execute("COMMIT")
                return replay
            packet = self.db.execute(
                "SELECT p.*,o.binding_epoch,o.revision AS owner_revision "
                "FROM continuation_packets p JOIN continuation_owners o ON o.owner_id=p.owner_id "
                "WHERE p.packet_id=?",
                (packet_id,),
            ).fetchone()
            if not packet or packet["state"] != "ACTIVE":
                raise KeyError("active continuation packet is absent")
            if packet["owner_revision"] != expected_owner_revision:
                raise ValueError("owner revision drift")
            claim = self.db.execute(
                "SELECT packet_id FROM continuation_claims WHERE packet_id=?", (packet_id,)
            ).fetchone()
            if not claim:
                raise KeyError("active packet has no conflict claim")
            self._record_event(
                event_id=event_id, digest=digest, task_id=packet_id,
                kind="CONTINUATION_TERMINAL", payload=receipt, now=now,
            )
            self.db.execute(
                "UPDATE continuation_packets SET state='SETTLED',terminal_digest=?,updated_at=? "
                "WHERE packet_id=?",
                (digest, now, packet_id),
            )
            self.db.execute("DELETE FROM continuation_claims WHERE packet_id=?", (packet_id,))
            if fail_after == "settlement":
                raise RuntimeError("fault injection after settlement")

            successor = self.db.execute(
                "SELECT * FROM continuation_packets WHERE owner_id=? AND after_packet_id=? "
                "AND state IN ('READY','BLOCKED_DEPENDENCY') "
                "ORDER BY priority DESC,packet_id LIMIT 1",
                (packet["owner_id"], packet_id),
            ).fetchone()
            trigger_key: str | None = None
            next_revision = packet["owner_revision"] + 1
            desired = "TERMINAL"
            observed = "TERMINAL"
            successor_id: str | None = None
            if successor:
                successor_id = successor["packet_id"]
                if successor["authorization_kind"] not in {
                    "AUTO_AUTHORIZED_LOCAL_ONLY", "EXPLICIT_AUTHORIZED_LOCAL_ONLY"
                }:
                    self.db.execute(
                        "UPDATE continuation_packets SET state='BLOCKED_AUTHORIZATION',updated_at=? "
                        "WHERE packet_id=?", (now, successor_id),
                    )
                    desired, observed = "WAITING_AUTHORIZATION", "EXPECTED_IDLE"
                elif successor["cost_kind"] not in {"LOCAL_ZERO", "NO_COST"}:
                    self.db.execute(
                        "UPDATE continuation_packets SET state='BLOCKED_COST',updated_at=? "
                        "WHERE packet_id=?", (now, successor_id),
                    )
                    desired, observed = "WAITING_COST", "EXPECTED_IDLE"
                elif self.db.execute(
                    "SELECT 1 FROM continuation_claims WHERE conflict_key=?",
                    (successor["conflict_key"],),
                ).fetchone():
                    self.db.execute(
                        "UPDATE continuation_packets SET state='WAITING_CONFLICT',updated_at=? "
                        "WHERE packet_id=?", (now, successor_id),
                    )
                    desired, observed = "QUEUED", "EXPECTED_IDLE"
                else:
                    self.db.execute(
                        "INSERT INTO continuation_claims(conflict_key,packet_id,owner_id,binding_epoch,claimed_at) "
                        "VALUES(?,?,?,?,?)",
                        (successor["conflict_key"], successor_id, packet["owner_id"],
                         packet["binding_epoch"], now),
                    )
                    trigger_key = self._trigger_key(
                        owner_id=packet["owner_id"], binding_epoch=packet["binding_epoch"],
                        packet_id=successor_id, context_pack_id=successor["context_pack_id"],
                        owner_revision=next_revision,
                    )
                    payload = {
                        "owner_id": packet["owner_id"], "binding_epoch": packet["binding_epoch"],
                        "packet_id": successor_id, "context_pack_id": successor["context_pack_id"],
                        "trigger_key": trigger_key,
                    }
                    payload_digest = self.digest(payload)
                    self.db.execute(
                        "UPDATE continuation_packets SET state='DISPATCH_PENDING',updated_at=? "
                        "WHERE packet_id=?", (now, successor_id),
                    )
                    self.db.execute(
                        "INSERT INTO continuation_outbox(trigger_key,owner_id,binding_epoch,packet_id,"
                        "context_pack_id,payload_digest,state,created_at,updated_at) "
                        "VALUES(?,?,?,?,?,?,'PENDING',?,?)",
                        (trigger_key, packet["owner_id"], packet["binding_epoch"], successor_id,
                         successor["context_pack_id"], payload_digest, now, now),
                    )
                    desired, observed = "DISPATCH_PENDING", "EXPECTED_IDLE"
                    if fail_after == "outbox":
                        raise RuntimeError("fault injection after outbox")
            self.db.execute(
                "UPDATE continuation_owners SET desired_state=?,observed_state=?,revision=?,"
                "active_turn_id=NULL,evidence_at=?,updated_at=? WHERE owner_id=?",
                (desired, observed, next_revision, now, now, packet["owner_id"]),
            )
            self.db.execute(
                "INSERT INTO continuation_metrics(owner_id,packet_id,name,value,created_at) "
                "VALUES(?,?,'terminal_commit',1,?)",
                (packet["owner_id"], packet_id, now),
            )
            self._promote_waiting_conflicts(
                now=now, conflict_keys=(packet["conflict_key"],)
            )
            self.db.execute("COMMIT")
            return ContinuationCommit(packet_id, successor_id, trigger_key, next_revision, False)
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def lease_continuation_trigger(
        self, *, worker_id: str, lease_seconds: float = 60
    ) -> ContinuationOutboxItem | None:
        if not worker_id.strip() or not math.isfinite(lease_seconds) or lease_seconds <= 0:
            raise ValueError("worker and positive finite lease are required")
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute(
                "UPDATE continuation_outbox SET state='PENDING',lease_owner=NULL,leased_until=NULL,"
                "updated_at=? WHERE state='LEASED' AND leased_until<=?",
                (now, now),
            )
            row = self.db.execute(
                "SELECT x.*,o.thread_id AS owner_thread_id FROM continuation_outbox x "
                "JOIN continuation_owners o ON o.owner_id=x.owner_id "
                "WHERE x.state='PENDING' ORDER BY x.created_at,x.trigger_key LIMIT 1"
            ).fetchone()
            if not row:
                self.db.execute("COMMIT")
                return None
            until = now + lease_seconds
            self.db.execute(
                "UPDATE continuation_outbox SET state='LEASED',lease_owner=?,leased_until=?,"
                "attempt_count=attempt_count+1,updated_at=? WHERE trigger_key=? AND state='PENDING'",
                (worker_id, until, now, row["trigger_key"]),
            )
            self.db.execute("COMMIT")
            return ContinuationOutboxItem(
                row["trigger_key"], row["owner_id"], row["binding_epoch"], row["packet_id"],
                row["owner_thread_id"], row["context_pack_id"], row["payload_digest"],
                row["attempt_count"] + 1, until,
            )
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def mark_continuation_trigger_dispatched(
        self, *, trigger_key: str, worker_id: str, confirmation_seconds: float = 30
    ) -> bool:
        """Persist the sent-unconfirmed boundary before invoking the adapter."""
        if not math.isfinite(confirmation_seconds) or confirmation_seconds <= 0:
            raise ValueError("confirmation window must be positive")
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT state,lease_owner,leased_until FROM continuation_outbox WHERE trigger_key=?",
                (trigger_key,),
            ).fetchone()
            if not row:
                raise KeyError("trigger is absent")
            if row["state"] == "DISPATCHED":
                self.db.execute("COMMIT")
                return False
            if row["state"] != "LEASED" or row["lease_owner"] != worker_id or row["leased_until"] <= now:
                raise KeyError("trigger lease is absent, expired, or mismatched")
            self.db.execute(
                "UPDATE continuation_outbox SET state='DISPATCHED',dispatched_at=?,"
                "confirmation_deadline=?,lease_owner=NULL,leased_until=NULL,updated_at=? "
                "WHERE trigger_key=?",
                (now, now + confirmation_seconds, now, trigger_key),
            )
            self.db.execute(
                "UPDATE continuation_outbox SET delivery_method='EXISTING_THREAD_ADAPTER' "
                "WHERE trigger_key=?", (trigger_key,),
            )
            self.db.execute("COMMIT")
            return True
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def mark_continuation_trigger_uncertain(self, *, trigger_key: str) -> bool:
        """Record invocation uncertainty without making the trigger retryable."""
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT state,error_class FROM continuation_outbox WHERE trigger_key=?",
                (trigger_key,),
            ).fetchone()
            if not row:
                raise KeyError("trigger is absent")
            if row["state"] != "DISPATCHED":
                raise ValueError("only sent-unconfirmed triggers may become uncertain")
            if row["error_class"] == "EXTERNAL_EFFECT_UNCONFIRMED":
                self.db.execute("COMMIT")
                return False
            self.db.execute(
                "UPDATE continuation_outbox SET error_class='EXTERNAL_EFFECT_UNCONFIRMED',"
                "updated_at=? WHERE trigger_key=?", (now, trigger_key),
            )
            self.db.execute("COMMIT")
            return True
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def confirm_continuation_trigger(
        self, *, trigger_key: str, thread_id: str, turn_id: str
    ) -> bool:
        """Validate correlation before the irreversible state transition."""
        if not thread_id.strip() or not turn_id.strip():
            raise ValueError("thread_id and turn_id are required")
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT x.*,o.thread_id AS expected_thread FROM continuation_outbox x "
                "JOIN continuation_owners o ON o.owner_id=x.owner_id WHERE x.trigger_key=?",
                (trigger_key,),
            ).fetchone()
            if not row:
                raise KeyError("trigger is absent")
            if thread_id != row["expected_thread"]:
                raise ValueError("turn readback thread identity mismatch")
            if row["state"] == "CONFIRMED":
                if row["thread_id"] != thread_id or row["turn_id"] != turn_id:
                    raise ValueError("confirmed trigger cannot be rebound")
                self.db.execute("COMMIT")
                return False
            if row["state"] != "DISPATCHED":
                raise ValueError("only DISPATCHED triggers may be confirmed")
            duplicate = self.db.execute(
                "SELECT trigger_key FROM continuation_outbox WHERE thread_id=? AND turn_id=? "
                "AND trigger_key<>?",
                (thread_id, turn_id, trigger_key),
            ).fetchone()
            if duplicate:
                raise ValueError("turn is already correlated to another trigger")
            self.db.execute(
                "UPDATE continuation_outbox SET state='CONFIRMED',thread_id=?,turn_id=?,updated_at=? "
                "WHERE trigger_key=?",
                (thread_id, turn_id, now, trigger_key),
            )
            self.db.execute(
                "UPDATE continuation_packets SET state='ACTIVE',updated_at=? WHERE packet_id=?",
                (now, row["packet_id"]),
            )
            self.db.execute(
                "UPDATE continuation_owners SET desired_state='ACTIVE_COMPUTE',"
                "observed_state='ACTIVE_COMPUTE',active_turn_id=?,evidence_at=?,updated_at=? "
                "WHERE owner_id=?",
                (turn_id, now, now, row["owner_id"]),
            )
            self.db.execute("COMMIT")
            return True
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def fail_continuation_trigger(
        self, *, trigger_key: str, worker_id: str, error_class: str
    ) -> str:
        """Capacity/token failures remain queued; deterministic ambiguity dead-letters."""
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT * FROM continuation_outbox WHERE trigger_key=?", (trigger_key,)
            ).fetchone()
            if not row:
                raise KeyError("trigger is absent")
            if row["state"] in {"CONFIRMED", "DEAD_LETTER"}:
                if row["error_class"] == error_class or row["state"] == "CONFIRMED":
                    self.db.execute("COMMIT")
                    return row["state"]
                raise ValueError("terminal trigger state cannot regress")
            if row["state"] == "LEASED" and row["lease_owner"] != worker_id:
                raise KeyError("trigger lease worker mismatch")
            resumable = error_class in RESUMABLE_TRIGGER_FAILURES
            state = "PENDING" if resumable else "DEAD_LETTER"
            packet_state = "RESUMABLE_QUEUED" if resumable else "DEAD_LETTER"
            desired = "QUEUED" if resumable else "WAITING_EXTERNAL"
            self.db.execute(
                "UPDATE continuation_outbox SET state=?,error_class=?,lease_owner=NULL,leased_until=NULL,"
                "updated_at=? WHERE trigger_key=?",
                (state, error_class, now, trigger_key),
            )
            self.db.execute(
                "UPDATE continuation_packets SET state=?,updated_at=? WHERE packet_id=?",
                (packet_state, now, row["packet_id"]),
            )
            self.db.execute(
                "UPDATE continuation_owners SET desired_state=?,observed_state='EXPECTED_IDLE',"
                "updated_at=? WHERE owner_id=?", (desired, now, row["owner_id"]),
            )
            self.db.execute("COMMIT")
            return state
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def reconcile_continuation_startup(
        self,
        *,
        observed_turns: Mapping[str, Mapping[str, str]] | None = None,
        now: float | None = None,
    ) -> tuple[dict[str, str], ...]:
        """One event-driven startup pass; it never starts a timer or polling loop."""
        liveness_collected = observed_turns is not None
        observed_turns = observed_turns or {}
        now = time.time() if now is None else now
        actions: list[dict[str, str]] = []
        self.db.execute("BEGIN IMMEDIATE")
        try:
            expired = self.db.execute(
                "SELECT trigger_key,packet_id FROM continuation_outbox "
                "WHERE state='LEASED' AND leased_until<=?", (now,)
            ).fetchall()
            for row in expired:
                self.db.execute(
                    "UPDATE continuation_outbox SET state='PENDING',lease_owner=NULL,leased_until=NULL,"
                    "error_class='LEASE_EXPIRED',updated_at=? WHERE trigger_key=?",
                    (now, row["trigger_key"]),
                )
                actions.append({"trigger_key": row["trigger_key"], "action": "REQUEUED_UNSENT"})

            dispatched = self.db.execute(
                "SELECT x.*,o.thread_id AS expected_thread FROM continuation_outbox x "
                "JOIN continuation_owners o ON o.owner_id=x.owner_id WHERE x.state='DISPATCHED'"
            ).fetchall()
            for row in dispatched:
                observed = observed_turns.get(row["trigger_key"])
                if observed:
                    thread_id = str(observed.get("thread_id") or "")
                    turn_id = str(observed.get("turn_id") or "")
                    if thread_id != row["expected_thread"] or not turn_id:
                        raise ValueError("startup readback identity is missing or mismatched")
                    self.db.execute(
                        "UPDATE continuation_outbox SET state='CONFIRMED',thread_id=?,turn_id=?,updated_at=? "
                        "WHERE trigger_key=?", (thread_id, turn_id, now, row["trigger_key"]),
                    )
                    self.db.execute(
                        "UPDATE continuation_packets SET state='ACTIVE',updated_at=? WHERE packet_id=?",
                        (now, row["packet_id"]),
                    )
                    self.db.execute(
                        "UPDATE continuation_owners SET desired_state='ACTIVE_COMPUTE',"
                        "observed_state='ACTIVE_COMPUTE',active_turn_id=?,evidence_at=?,updated_at=? "
                        "WHERE owner_id=?", (turn_id, now, now, row["owner_id"]),
                    )
                    actions.append({"trigger_key": row["trigger_key"], "action": "CONFIRMED_READBACK"})
                elif row["confirmation_deadline"] is not None and row["confirmation_deadline"] <= now:
                    self.db.execute(
                        "UPDATE continuation_outbox SET state='DEAD_LETTER',"
                        "error_class='SENT_UNCONFIRMED_AMBIGUITY',updated_at=? WHERE trigger_key=?",
                        (now, row["trigger_key"]),
                    )
                    self.db.execute(
                        "UPDATE continuation_packets SET state='DEAD_LETTER',updated_at=? WHERE packet_id=?",
                        (now, row["packet_id"]),
                    )
                    self.db.execute(
                        "UPDATE continuation_owners SET desired_state='WAITING_EXTERNAL',"
                        "observed_state='UNKNOWN',updated_at=? WHERE owner_id=?",
                        (now, row["owner_id"]),
                    )
                    actions.append({"trigger_key": row["trigger_key"], "action": "DEAD_LETTER_AMBIGUOUS"})

            actions.extend(self._promote_waiting_conflicts(now=now))

            active_owners = (
                self.db.execute(
                    "SELECT * FROM continuation_owners WHERE desired_state='ACTIVE_COMPUTE'"
                ).fetchall()
                if liveness_collected else ()
            )
            observed_thread_ids = {
                str(item.get("thread_id")) for item in observed_turns.values() if item.get("thread_id")
            }
            for owner in active_owners:
                if owner["thread_id"] not in observed_thread_ids:
                    active_packet = self.db.execute(
                        "SELECT p.*,x.context_pack_id AS confirmed_context_pack_id "
                        "FROM continuation_packets p LEFT JOIN continuation_outbox x "
                        "ON x.packet_id=p.packet_id AND x.state='CONFIRMED' "
                        "WHERE p.owner_id=? AND p.state='ACTIVE' ORDER BY p.updated_at DESC LIMIT 1",
                        (owner["owner_id"],),
                    ).fetchone()
                    next_revision = owner["revision"] + 1
                    self.db.execute(
                        "UPDATE continuation_owners SET observed_state='UNEXPECTED_IDLE',"
                        "desired_state='DISPATCH_PENDING',active_turn_id=NULL,revision=?,updated_at=? "
                        "WHERE owner_id=?",
                        (next_revision, now, owner["owner_id"]),
                    )
                    if active_packet:
                        context_pack_id = (
                            active_packet["confirmed_context_pack_id"]
                            or active_packet["context_pack_id"]
                        )
                        trigger_key = self._trigger_key(
                            owner_id=owner["owner_id"],
                            binding_epoch=owner["binding_epoch"],
                            packet_id=active_packet["packet_id"],
                            context_pack_id=context_pack_id,
                            owner_revision=next_revision,
                        )
                        payload = {
                            "owner_id": owner["owner_id"],
                            "binding_epoch": owner["binding_epoch"],
                            "packet_id": active_packet["packet_id"],
                            "context_pack_id": context_pack_id,
                            "trigger_key": trigger_key,
                        }
                        self.db.execute(
                            "UPDATE continuation_packets SET state='DISPATCH_PENDING',updated_at=? "
                            "WHERE packet_id=?", (now, active_packet["packet_id"]),
                        )
                        self.db.execute(
                            "INSERT INTO continuation_outbox(trigger_key,owner_id,binding_epoch,packet_id,"
                            "context_pack_id,payload_digest,state,error_class,created_at,updated_at) "
                            "VALUES(?,?,?,?,?,?,'PENDING','UNEXPECTED_IDLE_RECOVERY',?,?)",
                            (trigger_key, owner["owner_id"], owner["binding_epoch"],
                             active_packet["packet_id"], context_pack_id,
                             self.digest(payload), now, now),
                        )
                        actions.append({"owner_id": owner["owner_id"], "action": "REDISPATCH_UNEXPECTED_IDLE"})
                    else:
                        self.db.execute(
                            "UPDATE continuation_owners SET desired_state='WAITING_EXTERNAL',"
                            "observed_state='UNKNOWN',updated_at=? WHERE owner_id=?",
                            (now, owner["owner_id"]),
                        )
                        actions.append({"owner_id": owner["owner_id"], "action": "UNEXPECTED_IDLE_NO_PACKET"})
            self.db.execute("COMMIT")
            return tuple(actions)
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def continuation_context(self, context_pack_id: str) -> dict[str, object]:
        row = self.db.execute(
            "SELECT payload FROM continuation_context_packs WHERE context_pack_id=?",
            (context_pack_id,),
        ).fetchone()
        if not row:
            raise KeyError("context pack is absent")
        return json.loads(row["payload"])

    def continuation_status(self) -> dict[str, object]:
        def counts(table: str, column: str) -> dict[str, int]:
            rows = self.db.execute(
                f"SELECT {column} AS value,COUNT(*) AS n FROM {table} GROUP BY {column} ORDER BY {column}"
            ).fetchall()
            return {row["value"]: row["n"] for row in rows}

        owners = [dict(row) for row in self.db.execute(
            "SELECT owner_id,thread_id,binding_epoch,desired_state,observed_state,revision,"
            "active_turn_id FROM continuation_owners ORDER BY owner_id"
        )]
        return {
            "schema": "atlas.durable-continuation-kernel.status.v1",
            "owners": owners,
            "packets_by_state": counts("continuation_packets", "state"),
            "outbox_by_state": counts("continuation_outbox", "state"),
            "active_claims": self.db.execute("SELECT COUNT(*) FROM continuation_claims").fetchone()[0],
        }

    def export_continuation_projection(self) -> bytes:
        """Return a deterministic byte-for-byte projection of durable kernel state."""
        tables = (
            "continuation_owners", "continuation_context_packs", "continuation_packets",
            "continuation_claims", "continuation_outbox", "continuation_metrics",
        )
        projection: dict[str, list[dict[str, Any]]] = {}
        for table in tables:
            columns = [row["name"] for row in self.db.execute(f"PRAGMA table_info({table})")]
            order = ",".join(columns)
            projection[table] = [
                dict(row) for row in self.db.execute(f"SELECT * FROM {table} ORDER BY {order}")
            ]
        return (self._canonical_json({
            "schema": "atlas.durable-continuation-kernel.projection.v1",
            "tables": projection,
        }) + "\n").encode("utf-8")

    def inspect_json_scheduler(self, path: str | Path) -> dict[str, object]:
        """Read-only current-scheduler evidence importer; it never mutates SQLite."""
        source = Path(path)
        raw = source.read_bytes()
        try:
            document = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("scheduler evidence is not valid JSON") from None

        def validate(value: object, at: str = "$") -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if not isinstance(key, str) or key.casefold() in _PROTOTYPE_POLLUTION_KEYS:
                        raise ValueError(f"{at}: unsafe scheduler key")
                    validate(child, f"{at}.{key}")
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    validate(child, f"{at}[{index}]")
            elif isinstance(value, str) and _DRIVE_RELATIVE_PATH.fullmatch(value):
                raise ValueError(f"{at}: drive-relative path is semantically invalid")

        validate(document)
        if not isinstance(document, dict):
            raise ValueError("scheduler evidence root must be an object")
        revision = document.get("revision")
        return {
            "schema": "atlas.scheduler.read-only-import.v1",
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "revision": revision,
            "top_level_keys": sorted(document),
            "mutated": False,
        }

    def record_continuation_process_event(
        self, *, event_id: str, owner_id: str, packet_id: str,
        process_state: str, process_id: int | None = None,
    ) -> bool:
        if process_state not in {"STARTING", "STARTED", "EXITED", "FAILED"}:
            raise ValueError("unsupported child-process lifecycle state")
        payload = {
            "owner_id": owner_id,
            "packet_id": packet_id,
            "process_state": process_state,
            "process_id_present": process_id is not None,
        }
        digest = self.digest(payload)
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            existing = self.db.execute(
                "SELECT payload_digest FROM events WHERE event_id=?", (event_id,)
            ).fetchone()
            self._record_event(
                event_id=event_id, digest=digest, task_id=packet_id,
                kind="CONTINUATION_PROCESS", payload=payload, now=now,
            )
            self.db.execute("COMMIT")
            return existing is None
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def stop_hook_decision(
        self, *, owner_id: str, thread_id: str | None = None,
        confirmation_seconds: float = 30,
    ) -> dict[str, str]:
        """Atomically consume one trigger for the Stop transport.

        Moving PENDING to the sent-unconfirmed DISPATCHED state before returning
        decision=block makes the Stop hook and external dispatcher mutually
        exclusive. Startup/readback reconciliation owns later confirmation.
        """
        if not owner_id.strip() or not math.isfinite(confirmation_seconds) or confirmation_seconds <= 0:
            raise ValueError("owner and positive confirmation window are required")
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            owner = self.db.execute(
                "SELECT thread_id FROM continuation_owners WHERE owner_id=?", (owner_id,),
            ).fetchone()
            if not owner or (thread_id is not None and thread_id != owner["thread_id"]):
                self.db.execute("COMMIT")
                return {}
            row = self.db.execute(
                "SELECT trigger_key,packet_id,context_pack_id FROM continuation_outbox "
                "WHERE owner_id=? AND state='PENDING' ORDER BY created_at LIMIT 1",
                (owner_id,),
            ).fetchone()
            if not row:
                self.db.execute("COMMIT")
                return {}
            reason = (
                f"Continue ATLAS packet {row['packet_id']} using context pack "
                f"{row['context_pack_id']} and trigger {row['trigger_key']}."
            )
            if len(reason) > 512:
                raise ValueError("Stop-hook continuation reason exceeds bounded envelope")
            changed = self.db.execute(
                "UPDATE continuation_outbox SET state='DISPATCHED',attempt_count=attempt_count+1,"
                "dispatched_at=?,confirmation_deadline=?,delivery_method='STOP_HOOK',"
                "thread_id=?,updated_at=? WHERE trigger_key=? AND state='PENDING'",
                (now, now + confirmation_seconds, owner["thread_id"], now, row["trigger_key"]),
            ).rowcount
            if changed != 1:
                raise RuntimeError("Stop-hook trigger claim was lost")
            self.db.execute("COMMIT")
            return {"decision": "block", "reason": reason}
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def get(self, task_id: str) -> Task | None:
        row = self.db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if not row:
            return None
        return Task(row["task_id"], row["lane"], row["state"], row["priority"], row["scope"],
                    tuple(json.loads(row["depends_on"])), tuple(json.loads(row["successor_ids"])))
