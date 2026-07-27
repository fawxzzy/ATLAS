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
    successor_ids: tuple[str, ...]


@dataclass(frozen=True)
class WorkerLease:
    task_id: str
    worker_id: str
    run_id: str
    scope: str
    expires_at: float
    heartbeat_at: float


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
        successor_ids: Iterable[str] = (),
        event_id: str | None = None,
        payload: Mapping[str, object] | None = None,
    ) -> bool:
        """Insert a task and event idempotently. Returns whether task was new."""
        now = time.time()
        successors = tuple(successor_ids)
        event_id = event_id or f"task:{task_id}"
        event_payload = dict(payload or {})
        event_payload.update({"task_id": task_id, "lane": lane, "scope": scope})
        digest = self.digest(event_payload)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            existing = self.db.execute(
                "SELECT task_id FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            self.db.execute(
                "INSERT OR IGNORE INTO events(event_id,payload_digest,task_id,kind,payload,created_at)"
                " VALUES(?,?,?,?,?,?)",
                (event_id, digest, task_id, "ENQUEUE", json.dumps(event_payload, sort_keys=True), now),
            )
            if existing:
                self.db.execute("COMMIT")
                return False
            if scope == "":
                raise ValueError("scope must be non-empty")
            self.db.execute(
                "INSERT INTO tasks(task_id,lane,state,priority,scope,successor_ids,created_at,updated_at)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (task_id, lane, "QUEUED", priority, scope, json.dumps(successors), now, now),
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
                "SELECT * FROM tasks WHERE state='QUEUED' ORDER BY priority DESC, created_at LIMIT 1"
            ).fetchone()
            if not row:
                self.db.execute("COMMIT")
                return None
            conflict = self.db.execute(
                "SELECT 1 FROM leases WHERE scope=? AND expires_at>?", (row["scope"], now)
            ).fetchone()
            if conflict:
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
        cur = self.db.execute(
            "UPDATE leases SET heartbeat_at=?, expires_at=? WHERE task_id=? AND worker_id=? AND run_id=?",
            (now, expires, task_id, worker_id, run_id),
        )
        if cur.rowcount != 1:
            raise KeyError("lease not found or worker/run identity mismatched")
        row = self.db.execute("SELECT scope FROM leases WHERE task_id=?", (task_id,)).fetchone()
        return WorkerLease(task_id, worker_id, run_id, row["scope"], expires, now)

    def complete(self, *, task_id: str, worker_id: str, run_id: str,
                 state: str = "SUCCEEDED", receipt: Mapping[str, object] | None = None) -> tuple[str, ...]:
        """Atomically settle a lease, record its receipt, and enqueue successors."""
        if state not in STATES or state in {"QUEUED", "CLAIMED", "RUNNING"}:
            raise ValueError("completion requires a terminal or waiting state")
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT t.*, l.worker_id, l.run_id FROM tasks t JOIN leases l ON l.task_id=t.task_id"
                " WHERE t.task_id=?", (task_id,)
            ).fetchone()
            if not row or row["worker_id"] != worker_id or row["run_id"] != run_id:
                raise KeyError("lease not found or worker/run identity mismatched")
            receipt = dict(receipt or {})
            receipt.update({"task_id": task_id, "state": state})
            event_id = str(receipt.get("event_id") or f"receipt:{task_id}:{run_id}")
            digest = self.digest(receipt)
            self.db.execute(
                "INSERT OR IGNORE INTO events(event_id,payload_digest,task_id,kind,payload,created_at)"
                " VALUES(?,?,?,?,?,?)",
                (event_id, digest, task_id, "RECEIPT", json.dumps(receipt, sort_keys=True), now),
            )
            successors = tuple(json.loads(row["successor_ids"]))
            self.db.execute("UPDATE tasks SET state=?, updated_at=? WHERE task_id=?", (state, now, task_id))
            self.db.execute("DELETE FROM leases WHERE task_id=?", (task_id,))
            for successor in successors:
                self.db.execute("UPDATE tasks SET state='QUEUED', updated_at=? WHERE task_id=?", (now, successor))
            self.db.execute("COMMIT")
            return successors
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def reconcile(self, *, now: float | None = None, heartbeat_timeout: float = 120) -> list[str]:
        """Convert orphaned/stale RUNNING tasks to truthful PAUSED_RUNTIME."""
        now = time.time() if now is None else now
        rows = self.db.execute(
            "SELECT t.task_id, l.heartbeat_at, l.expires_at FROM tasks t LEFT JOIN leases l ON l.task_id=t.task_id"
            " WHERE t.state='RUNNING'"
        ).fetchall()
        paused: list[str] = []
        self.db.execute("BEGIN IMMEDIATE")
        try:
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

    def get(self, task_id: str) -> Task | None:
        row = self.db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if not row:
            return None
        return Task(row["task_id"], row["lane"], row["state"], row["priority"], row["scope"], tuple(json.loads(row["successor_ids"])))
