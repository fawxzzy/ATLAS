"""Small durable ATLAS runtime core.

This is deliberately adapter-neutral.  It owns durable task truth, scoped
leases, idempotent receipts, and atomic successor scheduling; a worker adapter
is responsible for doing the actual work.
"""

from __future__ import annotations

import hashlib
import json
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

    def get(self, task_id: str) -> Task | None:
        row = self.db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if not row:
            return None
        return Task(row["task_id"], row["lane"], row["state"], row["priority"], row["scope"],
                    tuple(json.loads(row["depends_on"])), tuple(json.loads(row["successor_ids"])))
