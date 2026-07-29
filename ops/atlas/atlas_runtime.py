"""Small durable ATLAS runtime core.

This is deliberately adapter-neutral.  It owns durable task truth, scoped
leases, idempotent receipts, and atomic successor scheduling; a worker adapter
is responsible for doing the actual work.
"""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


STATES = {
    "QUEUED", "CLAIMED", "RUNNING", "WAITING_EXTERNAL", "WAITING_MANUAL",
    "PAUSED_USAGE", "PAUSED_RUNTIME", "BLOCKED_DEPENDENCY", "SUCCEEDED",
    "FAILED", "CANCELLED", "SUPERSEDED", "UNKNOWN",
}


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


class AtlasRuntime:
    """SQLite/WAL-backed queue and truth store for one ATLAS runtime."""

    def __init__(self, database: str | Path):
        self.database = str(database)
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
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
              terminal_at REAL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS watchdog_one_in_progress
              ON watchdog_runs(name) WHERE state='IN_PROGRESS';
            CREATE INDEX IF NOT EXISTS watchdog_runs_name_state
              ON watchdog_runs(name, state, reserved_at);
            """
        )
        columns = {row["name"] for row in self.db.execute("PRAGMA table_info(tasks)")}
        if "depends_on" not in columns:
            self.db.execute("ALTER TABLE tasks ADD COLUMN depends_on TEXT NOT NULL DEFAULT '[]'")

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
        """Convert orphaned/stale RUNNING tasks to truthful PAUSED_RUNTIME."""
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
                "WHERE name=? AND state='IN_PROGRESS' AND reserved_at<=?",
                (now, name, now - reservation_seconds),
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
                "reservation_id,name,state,reserved_at,terminal_at"
                ") VALUES(?,?,'IN_PROGRESS',?,NULL)",
                (reservation_id, name, now),
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
        """Mark a watchdog run successful and begin its fallback cooldown."""
        self.db.execute("BEGIN IMMEDIATE")
        try:
            cur = self.db.execute(
                "UPDATE watchdog_runs SET state='SUCCEEDED', terminal_at=? "
                "WHERE reservation_id=? AND name=? AND state='IN_PROGRESS'",
                (now, reservation.reservation_id, reservation.name),
            )
            if cur.rowcount != 1:
                raise KeyError("watchdog reservation is absent or no longer in progress")
            self.db.execute(
                "INSERT INTO watchdog_state(name,last_checked_at) VALUES(?,?) "
                "ON CONFLICT(name) DO UPDATE SET last_checked_at=excluded.last_checked_at",
                (reservation.name, now),
            )
            self.db.execute("COMMIT")
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

    def record_watchdog_receipt(self, *, task_id: str, payload: Mapping[str, object], now: float) -> bool:
        """Persist one canonical wake-or-hold receipt; repeated identity is a no-op."""
        event_payload = dict(payload)
        event_payload["task_id"] = task_id
        digest = self.digest(event_payload)
        event_id = "watchdog:" + digest.removeprefix("sha256:")
        self.db.execute("BEGIN IMMEDIATE")
        try:
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
            self.db.execute("COMMIT")
            return existing is None
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def get(self, task_id: str) -> Task | None:
        row = self.db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if not row:
            return None
        return Task(row["task_id"], row["lane"], row["state"], row["priority"], row["scope"],
                    tuple(json.loads(row["depends_on"])), tuple(json.loads(row["successor_ids"])))
