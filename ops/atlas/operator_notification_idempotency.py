#!/usr/bin/env python3
"""Deterministic sender/receiver idempotency for Atlas operator notifications.

This module has no transport client and never emits an operator-facing message.
Callers prepare an event, atomically claim it in a runtime-owned receive ledger,
fence the claim with ``begin_delivery`` immediately before transport, and then
acknowledge the correlated claim token and generation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import secrets
import sqlite3
import stat
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


EVENT_CONTRACT_VERSION = "atlas.operator-notification.event.v1"
ACK_CONTRACT_VERSION = "atlas.operator-notification.ack.v1"
LEDGER_SCHEMA_VERSION = "atlas.operator-notification.ledger.v2"
CANONICALIZATION_VERSION = "atlas.operator-notification.canonical-json.v1"
TRANSPORT_VOLATILE_PATHS = ("$.payload.transport", "$.created_at")
NOTIFICATION_KINDS = frozenset(
    {"operator_update", "periodic_digest", "heartbeat", "continuation"}
)
CONTROL_KINDS = frozenset({"heartbeat", "continuation"})
PROVISION_SIDECAR_SUFFIXES = ("-wal", "-shm", "-journal")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]*$")
EVENT_ID_RE = re.compile(r"^onv1_[0-9a-f]{64}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
CLAIM_TOKEN_RE = re.compile(r"^oncl1_[0-9a-f]{64}$")
RFC3339_UTC_RE = re.compile(
    r"^[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r"(?:\.[0-9]{1,6})?Z$"
)
LEDGER_EVENT_COLUMNS = frozenset(
    {
        "sequence",
        "event_id",
        "source_thread_id",
        "event_class",
        "notification_kind",
        "event_contract_version",
        "canonicalization_version",
        "canonical_payload_digest",
        "first_envelope_digest",
        "last_envelope_digest",
        "created_at",
        "first_seen",
        "last_seen",
        "duplicate_count",
        "disposition",
        "supersedes_event_id",
        "superseded_by_event_id",
        "delta_json",
        "claim_generation",
        "claim_acquired_at",
        "claim_token",
        "claim_expires_at",
        "claimant_digest",
        "delivery_state",
        "delivery_started_at",
        "ack_state",
        "ack_id",
        "acknowledged_at",
    }
)


class NotificationContractError(ValueError):
    """The event or state transition violates the notification contract."""


class LedgerCorruptionError(RuntimeError):
    """The durable ledger failed integrity validation."""


class UnknownLedgerSchemaError(RuntimeError):
    """The durable ledger uses an unknown or incomplete schema."""


class LedgerUnavailableError(RuntimeError):
    """The ledger or a required runtime capability is temporarily unavailable."""


class LedgerProvisioningError(RuntimeError):
    """Explicit first-time provisioning was not safely admitted."""


class ClaimTokenError(NotificationContractError):
    """A delivery transition did not correlate to the active claim fence."""


class DeliveryStateError(NotificationContractError):
    """A delivery transition is stale, unsafe, or out of order."""


def _system_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not RFC3339_UTC_RE.fullmatch(value):
        raise NotificationContractError(
            f"{field} must be a canonical RFC 3339 UTC timestamp"
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise NotificationContractError(
            f"{field} must be a canonical RFC 3339 UTC timestamp"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise NotificationContractError(f"{field} must be UTC")
    return parsed


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _normalize_json(value: Any, path: str = "$") -> Any:
    if value is None or isinstance(value, bool) or isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise NotificationContractError(f"{path} contains a non-finite number")
        raise NotificationContractError(
            f"{path} contains a floating-point value; use integer or string fixed-point facts"
        )
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_normalize_json(item, f"{path}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise NotificationContractError(f"{path} contains a non-string object key")
            normalized_key = unicodedata.normalize("NFC", key)
            if normalized_key in normalized:
                raise NotificationContractError(
                    f"{path} contains duplicate keys after Unicode normalization"
                )
            normalized[normalized_key] = _normalize_json(
                item, f"{path}.{normalized_key}"
            )
        return normalized
    raise NotificationContractError(
        f"{path} contains unsupported JSON value {type(value).__name__}"
    )


def canonical_json_bytes(value: Any) -> bytes:
    normalized = _normalize_json(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _prefixed_id(prefix: str, value: bytes) -> str:
    return prefix + hashlib.sha256(value).hexdigest()


def _validate_identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise NotificationContractError(
            f"{field} must match {ID_RE.pattern}"
        )
    return value


def _validate_delta(delta: Any) -> dict[str, Any] | None:
    if delta is None:
        return None
    if not isinstance(delta, dict) or set(delta) != {"changed_fact_paths"}:
        raise NotificationContractError(
            "delta must contain only changed_fact_paths"
        )
    paths = delta["changed_fact_paths"]
    if (
        not isinstance(paths, list)
        or not paths
        or any(not _is_non_root_json_pointer(path) for path in paths)
    ):
        raise NotificationContractError(
            "delta.changed_fact_paths must be a non-empty JSON Pointer array"
        )
    if paths != sorted(set(paths)):
        raise NotificationContractError(
            "delta.changed_fact_paths must be sorted and unique"
        )
    return {"changed_fact_paths": paths}


def _is_non_root_json_pointer(value: Any) -> bool:
    """Admit RFC 6901 pointers while keeping the existing no-root policy."""

    if not isinstance(value, str) or not value.startswith("/"):
        return False
    index = 0
    while index < len(value):
        if value[index] != "~":
            index += 1
            continue
        if index + 1 >= len(value) or value[index + 1] not in "01":
            return False
        index += 2
    return True


def _notification_event_id(
    *,
    source_thread_id: str,
    event_class: str,
    notification_kind: str,
    canonical_payload_digest: str,
    supersedes_event_id: str | None,
    include_causal_predecessor: bool = True,
) -> str:
    identity_parts = [
        source_thread_id,
        event_class,
        notification_kind,
        canonical_payload_digest,
    ]
    if (
        include_causal_predecessor
        and notification_kind not in CONTROL_KINDS
        and supersedes_event_id is not None
    ):
        identity_parts.append(supersedes_event_id)
    return _prefixed_id("onv1_", "\x1f".join(identity_parts).encode("utf-8"))


def build_event(
    *,
    source_thread_id: str,
    event_class: str,
    payload: Mapping[str, Any],
    created_at: str,
    notification_kind: str = "operator_update",
    supersedes_event_id: str | None = None,
    delta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a deterministic, cross-host notification event envelope."""

    source_thread_id = _validate_identifier(source_thread_id, "source_thread_id")
    event_class = _validate_identifier(event_class, "event_class")
    if notification_kind not in NOTIFICATION_KINDS:
        raise NotificationContractError(
            f"notification_kind must be one of {sorted(NOTIFICATION_KINDS)}"
        )
    _utc(created_at, "created_at")
    if not isinstance(payload, Mapping) or "facts" not in payload:
        raise NotificationContractError("payload.facts is required")
    if set(payload) - {"facts", "transport"}:
        raise NotificationContractError("payload permits only facts and transport")
    facts = payload["facts"]
    transport = payload.get("transport", {})
    if not isinstance(facts, dict) or not facts:
        raise NotificationContractError("payload.facts must be a non-empty object")
    if not isinstance(transport, dict):
        raise NotificationContractError("payload.transport must be an object")
    normalized_payload = _normalize_json({"facts": facts, "transport": transport})
    canonical_payload_digest = _sha256(canonical_json_bytes(normalized_payload["facts"]))
    transport_envelope_digest = _sha256(
        canonical_json_bytes(
            {"created_at": created_at, "payload": normalized_payload}
        )
    )
    if supersedes_event_id is not None and not EVENT_ID_RE.fullmatch(
        supersedes_event_id
    ):
        raise NotificationContractError("supersedes_event_id is invalid")
    normalized_delta = _validate_delta(delta)
    if notification_kind == "periodic_digest" and (
        supersedes_event_id is not None or normalized_delta is not None
    ):
        raise NotificationContractError(
            "periodic_digest events must remain unlinked"
        )
    if normalized_delta is not None and supersedes_event_id is None:
        raise NotificationContractError("delta requires supersedes_event_id")
    if notification_kind in CONTROL_KINDS and (
        supersedes_event_id is not None or normalized_delta is not None
    ):
        raise NotificationContractError(
            "heartbeat and continuation events cannot supersede notifications"
        )
    event_id = _notification_event_id(
        source_thread_id=source_thread_id,
        event_class=event_class,
        notification_kind=notification_kind,
        canonical_payload_digest=canonical_payload_digest,
        supersedes_event_id=supersedes_event_id,
    )
    authority = {
        "notification_only": True,
        "repository_execution_authorized": False,
        "board_mutation_authorized": False,
    }
    return {
        "contract_version": EVENT_CONTRACT_VERSION,
        "event_id": event_id,
        "source_thread_id": source_thread_id,
        "event_class": event_class,
        "notification_kind": notification_kind,
        "canonicalization": {
            "contract_version": CANONICALIZATION_VERSION,
            "digest_algorithm": "sha256",
            "included_paths": ["$.payload.facts"],
            "excluded_paths": list(TRANSPORT_VOLATILE_PATHS),
        },
        "canonical_payload_digest": canonical_payload_digest,
        "transport_envelope_digest": transport_envelope_digest,
        "created_at": created_at,
        "supersedes_event_id": supersedes_event_id,
        "delta": normalized_delta,
        "payload": normalized_payload,
        "authority": authority,
    }


def validate_event(event: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(event, Mapping):
        raise NotificationContractError("event must be an object")
    required = {
        "contract_version",
        "event_id",
        "source_thread_id",
        "event_class",
        "notification_kind",
        "canonicalization",
        "canonical_payload_digest",
        "transport_envelope_digest",
        "created_at",
        "supersedes_event_id",
        "delta",
        "payload",
        "authority",
    }
    if set(event) != required:
        missing = sorted(required - set(event))
        extra = sorted(set(event) - required)
        raise NotificationContractError(
            f"event fields mismatch; missing={missing}, extra={extra}"
        )
    rebuilt = build_event(
        source_thread_id=event["source_thread_id"],
        event_class=event["event_class"],
        notification_kind=event["notification_kind"],
        payload=event["payload"],
        created_at=event["created_at"],
        supersedes_event_id=event["supersedes_event_id"],
        delta=event["delta"],
    )
    event_dict = dict(event)
    if event_dict == rebuilt:
        return rebuilt
    if (
        rebuilt["notification_kind"] not in CONTROL_KINDS
        and rebuilt["supersedes_event_id"] is not None
    ):
        legacy = dict(rebuilt)
        legacy["event_id"] = _notification_event_id(
            source_thread_id=rebuilt["source_thread_id"],
            event_class=rebuilt["event_class"],
            notification_kind=rebuilt["notification_kind"],
            canonical_payload_digest=rebuilt["canonical_payload_digest"],
            supersedes_event_id=rebuilt["supersedes_event_id"],
            include_causal_predecessor=False,
        )
        if event_dict == legacy:
            return legacy
    raise NotificationContractError(
        "event does not match deterministic canonical reconstruction"
    )


def resolve_ledger_path(runtime_root: Path | str, ledger_path: Path | str) -> Path:
    root = Path(runtime_root).resolve()
    path = Path(ledger_path).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise NotificationContractError(
            "ledger path must remain under the configured runtime root"
        ) from exc
    if path.suffix.lower() != ".sqlite3":
        raise NotificationContractError("ledger path must use the .sqlite3 suffix")
    if any(part.lower() in {"secrets", ".git"} for part in path.parts):
        raise NotificationContractError("ledger path enters a protected directory")
    return path


class NotificationLedger:
    """SQLite-backed receive ledger with atomic duplicate claim semantics."""

    def __init__(
        self,
        runtime_root: Path | str,
        ledger_path: Path | str,
        *,
        _clock: Callable[[], datetime] | None = None,
        _token_bytes: Callable[[int], bytes] | None = None,
        _busy_timeout_ms: int = 5000,
    ):
        self.runtime_root = Path(runtime_root).resolve()
        self.path = resolve_ledger_path(self.runtime_root, ledger_path)
        self._clock = _clock or _system_utc_now
        self._token_bytes = _token_bytes or secrets.token_bytes
        self._busy_timeout_ms = _busy_timeout_ms
        if not self.path.is_file():
            raise LedgerUnavailableError(
                "configured notification ledger is missing; restore it or provision explicitly"
            )
        self._open_existing()

    @classmethod
    def provision(
        cls,
        runtime_root: Path | str,
        ledger_path: Path | str,
        *,
        _clock: Callable[[], datetime] | None = None,
        _token_bytes: Callable[[int], bytes] | None = None,
        _busy_timeout_ms: int = 5000,
    ) -> "NotificationLedger":
        """Create one new authority ledger only through an explicit first-use call."""

        instance = cls.__new__(cls)
        instance.runtime_root = Path(runtime_root).resolve()
        instance.path = resolve_ledger_path(instance.runtime_root, ledger_path)
        instance._clock = _clock or _system_utc_now
        instance._token_bytes = _token_bytes or secrets.token_bytes
        instance._busy_timeout_ms = _busy_timeout_ms
        canonical_path = instance.path
        canonical_path.parent.mkdir(parents=True, exist_ok=True)
        if os.path.lexists(canonical_path):
            raise LedgerProvisioningError(
                "configured notification ledger already exists; provisioning will not replace it"
            )
        private_path, private_identity = cls._create_private_provision_path(
            canonical_path
        )
        published = False
        try:
            instance.path = private_path
            instance._provision_new()
            instance._before_provision_publish()
            cls._validate_private_provision_path(
                canonical_path,
                private_path,
                expected_identity=private_identity,
            )
            cls._require_no_provision_sidecars(private_path)
            cls._fsync_file(private_path)
            try:
                os.link(private_path, canonical_path)
            except FileExistsError as exc:
                raise LedgerProvisioningError(
                    "configured notification ledger already exists; provisioning will not replace it"
                ) from exc
            except OSError as exc:
                raise LedgerProvisioningError(
                    "atomic notification ledger publication was not admitted"
                ) from exc
            published = True
            canonical_identity = cls._regular_file_identity(canonical_path)
            if canonical_identity != private_identity:
                raise LedgerProvisioningError(
                    "published notification ledger identity did not match its private source"
                )
            cls._remove_private_provision_artifacts(
                canonical_path,
                private_path,
                expected_identity=private_identity,
                remove_database=True,
            )
            instance.path = canonical_path
            instance._open_existing()
            return instance
        except Exception as exc:
            if not published:
                cls._remove_private_provision_artifacts(
                    canonical_path,
                    private_path,
                    expected_identity=private_identity,
                    remove_database=True,
                )
            if isinstance(
                exc,
                (
                    LedgerProvisioningError,
                    LedgerCorruptionError,
                    UnknownLedgerSchemaError,
                    LedgerUnavailableError,
                ),
            ):
                raise
            raise LedgerProvisioningError(
                "notification ledger provisioning failed before publication"
            ) from exc

    @staticmethod
    def _provision_prefix(canonical_path: Path) -> str:
        return f".{canonical_path.name}.provision-"

    @classmethod
    def _create_private_provision_path(
        cls, canonical_path: Path
    ) -> tuple[Path, tuple[int, int]]:
        prefix = cls._provision_prefix(canonical_path)
        for _ in range(16):
            candidate = canonical_path.with_name(
                f"{prefix}{secrets.token_hex(16)}.tmp"
            )
            try:
                descriptor = os.open(
                    candidate,
                    os.O_CREAT | os.O_EXCL | os.O_RDWR,
                    0o600,
                )
            except FileExistsError:
                continue
            except OSError as exc:
                raise LedgerProvisioningError(
                    "private notification ledger path could not be created"
                ) from exc
            try:
                observed = os.fstat(descriptor)
                if not stat.S_ISREG(observed.st_mode):
                    raise LedgerProvisioningError(
                        "private notification ledger path is not a regular file"
                    )
                identity = (observed.st_dev, observed.st_ino)
            finally:
                os.close(descriptor)
            return candidate, identity
        raise LedgerProvisioningError(
            "a unique private notification ledger path could not be created"
        )

    @classmethod
    def _validate_private_provision_path(
        cls,
        canonical_path: Path,
        private_path: Path,
        *,
        expected_identity: tuple[int, int] | None = None,
    ) -> None:
        prefix = cls._provision_prefix(canonical_path)
        token = private_path.name.removeprefix(prefix).removesuffix(".tmp")
        if (
            private_path.parent.resolve() != canonical_path.parent.resolve()
            or not private_path.name.startswith(prefix)
            or not private_path.name.endswith(".tmp")
            or not re.fullmatch(r"[0-9a-f]{32}", token)
            or private_path.is_symlink()
        ):
            raise LedgerProvisioningError(
                "private notification ledger path failed ownership validation"
            )
        observed_identity = cls._regular_file_identity(private_path)
        if (
            expected_identity is not None
            and observed_identity != expected_identity
        ):
            raise LedgerProvisioningError(
                "private notification ledger identity changed before publication"
            )

    @staticmethod
    def _regular_file_identity(path: Path) -> tuple[int, int]:
        try:
            observed = path.stat(follow_symlinks=False)
        except OSError as exc:
            raise LedgerProvisioningError(
                "notification ledger artifact could not be inspected safely"
            ) from exc
        if not stat.S_ISREG(observed.st_mode):
            raise LedgerProvisioningError(
                "notification ledger artifact is not a regular file"
            )
        return observed.st_dev, observed.st_ino

    @staticmethod
    def _provision_sidecars(private_path: Path) -> tuple[Path, ...]:
        return tuple(
            Path(str(private_path) + suffix)
            for suffix in PROVISION_SIDECAR_SUFFIXES
        )

    @classmethod
    def _require_no_provision_sidecars(cls, private_path: Path) -> None:
        if any(os.path.lexists(path) for path in cls._provision_sidecars(private_path)):
            raise LedgerProvisioningError(
                "private notification ledger retained SQLite sidecars after validation"
            )

    @staticmethod
    def _fsync_file(path: Path) -> None:
        try:
            # Windows requires a writable descriptor for FlushFileBuffers,
            # which is the operation Python's os.fsync delegates to there.
            descriptor = os.open(path, os.O_RDWR)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        except OSError as exc:
            raise LedgerProvisioningError(
                "private notification ledger could not be synchronized"
            ) from exc

    @classmethod
    def _remove_private_provision_artifacts(
        cls,
        canonical_path: Path,
        private_path: Path,
        *,
        expected_identity: tuple[int, int],
        remove_database: bool,
    ) -> None:
        cls._validate_private_provision_path(
            canonical_path,
            private_path,
            expected_identity=expected_identity,
        )
        for sidecar in cls._provision_sidecars(private_path):
            if not os.path.lexists(sidecar):
                continue
            if (
                sidecar.parent.resolve() != canonical_path.parent.resolve()
                or sidecar.is_symlink()
            ):
                raise LedgerProvisioningError(
                    "private SQLite sidecar failed ownership validation"
                )
            cls._regular_file_identity(sidecar)
            sidecar.unlink()
        if remove_database and os.path.lexists(private_path):
            cls._validate_private_provision_path(
                canonical_path,
                private_path,
                expected_identity=expected_identity,
            )
            private_path.unlink()

    def _before_provision_publish(self) -> None:
        """Test seam after private validation and before atomic publication."""

    def _connect(self) -> sqlite3.Connection:
        connection = None
        try:
            connection = sqlite3.connect(
                self.path.as_uri() + "?mode=rw",
                timeout=self._busy_timeout_ms / 1000,
                isolation_level=None,
                uri=True,
            )
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(f"PRAGMA busy_timeout={self._busy_timeout_ms}")
            connection.execute("PRAGMA synchronous=FULL")
            synchronous = connection.execute("PRAGMA synchronous").fetchone()[0]
            if synchronous != 2:
                raise LedgerCorruptionError(
                    "SQLite FULL synchronous mode was not admitted"
                )
            return connection
        except Exception as exc:
            if connection is not None:
                connection.close()
            self._raise_if_contention(exc)
            raise

    @staticmethod
    def _raise_if_contention(exc: BaseException) -> None:
        if not isinstance(exc, sqlite3.OperationalError):
            return
        error_code = getattr(exc, "sqlite_errorcode", None)
        primary_code = error_code & 0xFF if isinstance(error_code, int) else None
        message = str(exc).casefold()
        if primary_code in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED} or any(
            marker in message for marker in ("busy", "locked")
        ):
            raise LedgerUnavailableError(
                "notification ledger is temporarily unavailable due to SQLite lock contention"
            ) from exc

    def _ledger_utc_now(self, operation: str) -> datetime:
        observed = self._clock()
        if (
            not isinstance(observed, datetime)
            or observed.tzinfo is None
            or observed.utcoffset() != timedelta(0)
        ):
            raise LedgerCorruptionError(
                f"{operation} clock must return a timezone-aware UTC datetime"
            )
        return observed

    @staticmethod
    def _admit_wal(connection: sqlite3.Connection) -> str:
        for attempt in range(50):
            try:
                current = connection.execute("PRAGMA journal_mode").fetchone()[0]
                if str(current).lower() == "wal":
                    return "wal"
                admitted = connection.execute("PRAGMA journal_mode=WAL").fetchone()[0]
                return str(admitted).lower()
            except sqlite3.OperationalError as exc:
                retryable = "locked" in str(exc).lower() or "busy" in str(exc).lower()
                if not retryable or attempt == 49:
                    raise
                time.sleep(0.02)
        raise LedgerCorruptionError("SQLite WAL admission did not terminate")

    def _open_existing(self) -> None:
        try:
            connection = self._connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                try:
                    self._verify_existing(connection)
                    connection.execute("COMMIT")
                except Exception:
                    if connection.in_transaction:
                        connection.execute("ROLLBACK")
                    raise
                mode = self._admit_wal(connection)
                if mode != "wal":
                    raise LedgerCorruptionError("SQLite WAL mode was not admitted")
                quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
                if quick_check != "ok":
                    raise LedgerCorruptionError(
                        f"SQLite quick_check failed: {quick_check}"
                    )
            finally:
                connection.close()
        except sqlite3.DatabaseError as exc:
            self._raise_if_contention(exc)
            raise LedgerCorruptionError(
                "notification ledger could not be opened safely"
            ) from exc

    def _provision_new(self) -> None:
        try:
            connection = self._connect()
            try:
                mode = self._admit_wal(connection)
                if mode != "wal":
                    raise LedgerCorruptionError("SQLite WAL mode was not admitted")
                connection.execute("BEGIN IMMEDIATE")
                try:
                    tables = {
                        row[0]
                        for row in connection.execute(
                            "SELECT name FROM sqlite_master "
                            "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                        )
                    }
                    if tables:
                        raise LedgerProvisioningError(
                            "new notification ledger is not empty"
                        )
                    self._create_schema(connection)
                    connection.execute("COMMIT")
                except Exception:
                    if connection.in_transaction:
                        connection.execute("ROLLBACK")
                    raise
                self._verify_existing(connection)
                checkpoint = connection.execute(
                    "PRAGMA wal_checkpoint(TRUNCATE)"
                ).fetchone()
                if checkpoint[0] != 0 or checkpoint[1] != checkpoint[2]:
                    raise LedgerCorruptionError(
                        "private notification ledger WAL checkpoint did not complete"
                    )
                quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
                if quick_check != "ok":
                    raise LedgerCorruptionError(
                        f"SQLite quick_check failed: {quick_check}"
                    )
            finally:
                connection.close()
        except sqlite3.DatabaseError as exc:
            self._raise_if_contention(exc)
            raise LedgerCorruptionError(
                "notification ledger could not be provisioned safely"
            ) from exc

    @staticmethod
    def _create_schema(connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE ledger_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            ) STRICT
            """
        )
        connection.execute(
            """
            CREATE TABLE notification_events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                source_thread_id TEXT NOT NULL,
                event_class TEXT NOT NULL,
                notification_kind TEXT NOT NULL,
                event_contract_version TEXT NOT NULL,
                canonicalization_version TEXT NOT NULL,
                canonical_payload_digest TEXT NOT NULL,
                first_envelope_digest TEXT NOT NULL,
                last_envelope_digest TEXT NOT NULL,
                created_at TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                duplicate_count INTEGER NOT NULL DEFAULT 0,
                disposition TEXT NOT NULL,
                supersedes_event_id TEXT,
                superseded_by_event_id TEXT,
                delta_json TEXT,
                claim_generation INTEGER NOT NULL DEFAULT 0,
                claim_acquired_at TEXT,
                claim_token TEXT,
                claim_expires_at TEXT,
                claimant_digest TEXT,
                delivery_state TEXT NOT NULL,
                delivery_started_at TEXT,
                ack_state TEXT NOT NULL,
                ack_id TEXT,
                acknowledged_at TEXT,
                FOREIGN KEY (supersedes_event_id) REFERENCES notification_events(event_id),
                CHECK (duplicate_count >= 0),
                CHECK (claim_generation >= 0)
            ) STRICT
            """
        )
        connection.execute(
            """
            CREATE INDEX notification_stream_latest
                ON notification_events(source_thread_id, event_class, sequence DESC)
            """
        )
        connection.execute(
            "INSERT INTO ledger_meta(key, value) VALUES (?, ?)",
            ("schema_version", LEDGER_SCHEMA_VERSION),
        )

    @staticmethod
    def _verify_existing(connection: sqlite3.Connection) -> None:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if not {"ledger_meta", "notification_events"}.issubset(tables):
            raise UnknownLedgerSchemaError(
                "existing notification ledger is missing required tables"
            )
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(notification_events)")
        }
        if columns != LEDGER_EVENT_COLUMNS:
            raise UnknownLedgerSchemaError(
                "existing notification ledger has incompatible event columns"
            )
        row = connection.execute(
            "SELECT value FROM ledger_meta WHERE key='schema_version'"
        ).fetchone()
        if row is None or row[0] != LEDGER_SCHEMA_VERSION:
            observed = None if row is None else row[0]
            raise UnknownLedgerSchemaError(
                f"unsupported notification ledger schema: {observed!r}"
            )

    def _claim_token(self, prior_token: str | None = None) -> str:
        for _ in range(8):
            try:
                token_bytes = self._token_bytes(32)
            except Exception as exc:
                raise LedgerUnavailableError(
                    "secure claim token source failed"
                ) from exc
            if not isinstance(token_bytes, bytes) or len(token_bytes) != 32:
                raise LedgerUnavailableError(
                    "secure claim token source must return exactly 32 bytes"
                )
            candidate = "oncl1_" + token_bytes.hex()
            if candidate != prior_token:
                return candidate
        raise LedgerUnavailableError(
            "secure claim token source repeated the active capability"
        )

    @staticmethod
    def _ack_id(event_id: str, claim_token: str, claim_generation: int) -> str:
        return _prefixed_id(
            "ona1_",
            f"{event_id}\x1f{claim_token}\x1f{claim_generation}\x1faccepted".encode(
                "utf-8"
            ),
        )

    @staticmethod
    def _row_ack(row: sqlite3.Row, disposition: str) -> dict[str, Any] | None:
        if row["ack_state"] != "accepted":
            return None
        return {
            "contract_version": ACK_CONTRACT_VERSION,
            "ack_id": row["ack_id"],
            "event_id": row["event_id"],
            "source_thread_id": row["source_thread_id"],
            "event_class": row["event_class"],
            "canonical_payload_digest": row["canonical_payload_digest"],
            "claim_generation": row["claim_generation"],
            "acknowledged_at": row["acknowledged_at"],
            "delivery_state": "accepted",
            "ack_disposition": disposition,
            "retry_authorized": False,
            "operator_message_authorized": False,
            "authority": {
                "notification_only": True,
                "repository_execution_authorized": False,
                "board_mutation_authorized": False,
            },
        }

    @staticmethod
    def _invariant_fields(event: Mapping[str, Any]) -> tuple[Any, ...]:
        delta_json = (
            None
            if event["delta"] is None
            else canonical_json_bytes(event["delta"]).decode("utf-8")
        )
        return (
            event["source_thread_id"],
            event["event_class"],
            event["notification_kind"],
            event["contract_version"],
            event["canonicalization"]["contract_version"],
            event["canonical_payload_digest"],
            event["supersedes_event_id"],
            delta_json,
        )

    @staticmethod
    def _row_invariant_fields(row: sqlite3.Row) -> tuple[Any, ...]:
        return (
            row["source_thread_id"],
            row["event_class"],
            row["notification_kind"],
            row["event_contract_version"],
            row["canonicalization_version"],
            row["canonical_payload_digest"],
            row["supersedes_event_id"],
            row["delta_json"],
        )

    def claim(
        self,
        event: Mapping[str, Any],
        *,
        claimant_id: str,
        seen_at: str,
        lease_seconds: int = 300,
    ) -> dict[str, Any]:
        event = validate_event(event)
        _utc(seen_at, "seen_at")
        if not isinstance(claimant_id, str) or not claimant_id:
            raise NotificationContractError("claimant_id is required")
        if lease_seconds < 1 or lease_seconds > 3600:
            raise NotificationContractError("lease_seconds must be between 1 and 3600")
        claimant_digest = _sha256(claimant_id.encode("utf-8"))
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            claimed = self._ledger_utc_now("claim")
            claimed_at = _timestamp(claimed)
            row = connection.execute(
                "SELECT * FROM notification_events WHERE event_id=?",
                (event["event_id"],),
            ).fetchone()
            if row is not None:
                result = self._claim_existing(
                    connection,
                    row,
                    event,
                    claimant_digest=claimant_digest,
                    claimed=claimed,
                    claimed_at=claimed_at,
                    seen_at=seen_at,
                    lease_seconds=lease_seconds,
                )
                connection.execute("COMMIT")
                return result
            result = self._claim_new(
                connection,
                event,
                claimant_digest=claimant_digest,
                claimed=claimed,
                claimed_at=claimed_at,
                seen_at=seen_at,
                lease_seconds=lease_seconds,
            )
            connection.execute("COMMIT")
            return result
        except Exception as exc:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            self._raise_if_contention(exc)
            raise
        finally:
            connection.close()

    def _claim_existing(
        self,
        connection: sqlite3.Connection,
        row: sqlite3.Row,
        event: Mapping[str, Any],
        *,
        claimant_digest: str,
        claimed: datetime,
        claimed_at: str,
        seen_at: str,
        lease_seconds: int,
    ) -> dict[str, Any]:
        if self._row_invariant_fields(row) != self._invariant_fields(event):
            raise NotificationContractError(
                "event_id collision changed immutable notification metadata"
            )
        duplicate_count = row["duplicate_count"] + 1
        if row["ack_state"] == "accepted":
            disposition = "duplicate_acked"
            connection.execute(
                """UPDATE notification_events
                   SET last_seen=?, last_envelope_digest=?, duplicate_count=?, disposition=?
                   WHERE event_id=?""",
                (
                    seen_at,
                    event["transport_envelope_digest"],
                    duplicate_count,
                    disposition,
                    event["event_id"],
                ),
            )
            updated = connection.execute(
                "SELECT * FROM notification_events WHERE event_id=?",
                (event["event_id"],),
            ).fetchone()
            return self._claim_result(
                updated,
                should_begin_delivery=False,
                disposition=disposition,
                ack_disposition="replayed",
            )
        if row["notification_kind"] in CONTROL_KINDS:
            disposition = (
                "duplicate_exact"
                if row["last_envelope_digest"]
                == event["transport_envelope_digest"]
                else "duplicate_semantic"
            )
            connection.execute(
                """UPDATE notification_events
                   SET last_seen=?, last_envelope_digest=?, duplicate_count=?, disposition=?
                   WHERE event_id=?""",
                (
                    seen_at,
                    event["transport_envelope_digest"],
                    duplicate_count,
                    disposition,
                    event["event_id"],
                ),
            )
            updated = connection.execute(
                "SELECT * FROM notification_events WHERE event_id=?",
                (event["event_id"],),
            ).fetchone()
            return self._claim_result(
                updated, should_begin_delivery=False, disposition=disposition
            )
        if row["superseded_by_event_id"] is not None:
            disposition = "duplicate_superseded"
            connection.execute(
                """UPDATE notification_events
                   SET last_seen=?, last_envelope_digest=?, duplicate_count=?, disposition=?
                   WHERE event_id=?""",
                (
                    seen_at,
                    event["transport_envelope_digest"],
                    duplicate_count,
                    disposition,
                    event["event_id"],
                ),
            )
            updated = connection.execute(
                "SELECT * FROM notification_events WHERE event_id=?",
                (event["event_id"],),
            ).fetchone()
            return self._claim_result(
                updated, should_begin_delivery=False, disposition=disposition
            )
        if row["delivery_state"] == "delivery_in_progress":
            disposition = "duplicate_delivery_unknown"
            connection.execute(
                """UPDATE notification_events
                   SET last_seen=?, last_envelope_digest=?, duplicate_count=?, disposition=?
                   WHERE event_id=?""",
                (
                    seen_at,
                    event["transport_envelope_digest"],
                    duplicate_count,
                    disposition,
                    event["event_id"],
                ),
            )
            updated = connection.execute(
                "SELECT * FROM notification_events WHERE event_id=?",
                (event["event_id"],),
            ).fetchone()
            return self._claim_result(
                updated,
                should_begin_delivery=False,
                disposition=disposition,
            )
        if row["delivery_state"] not in {"claimed", "retry_claimed"}:
            raise DeliveryStateError(
                "existing notification has an unsafe delivery state"
            )
        expires = (
            None
            if row["claim_expires_at"] is None
            else _utc(row["claim_expires_at"], "claim_expires_at")
        )
        if expires is not None and expires <= claimed:
            generation = row["claim_generation"] + 1
            claim_token = self._claim_token(row["claim_token"])
            claim_expires_at = _timestamp(
                claimed + timedelta(seconds=lease_seconds)
            )
            disposition = "retry_claimed"
            connection.execute(
                """UPDATE notification_events
                   SET last_seen=?, last_envelope_digest=?, duplicate_count=?,
                       disposition=?, claim_generation=?, claim_token=?,
                       claim_acquired_at=?, claim_expires_at=?, claimant_digest=?,
                       delivery_state='retry_claimed'
                   WHERE event_id=?""",
                (
                    seen_at,
                    event["transport_envelope_digest"],
                    duplicate_count,
                    disposition,
                    generation,
                    claim_token,
                    claimed_at,
                    claim_expires_at,
                    claimant_digest,
                    event["event_id"],
                ),
            )
            updated = connection.execute(
                "SELECT * FROM notification_events WHERE event_id=?",
                (event["event_id"],),
            ).fetchone()
            return self._claim_result(
                updated, should_begin_delivery=True, disposition=disposition
            )
        disposition = (
            "duplicate_exact"
            if row["last_envelope_digest"] == event["transport_envelope_digest"]
            else "duplicate_semantic"
        )
        connection.execute(
            """UPDATE notification_events
               SET last_seen=?, last_envelope_digest=?, duplicate_count=?, disposition=?
               WHERE event_id=?""",
            (
                seen_at,
                event["transport_envelope_digest"],
                duplicate_count,
                disposition,
                event["event_id"],
            ),
        )
        updated = connection.execute(
            "SELECT * FROM notification_events WHERE event_id=?",
            (event["event_id"],),
        ).fetchone()
        return self._claim_result(
            updated, should_begin_delivery=False, disposition=disposition
        )

    def _claim_new(
        self,
        connection: sqlite3.Connection,
        event: Mapping[str, Any],
        *,
        claimant_digest: str,
        claimed: datetime,
        claimed_at: str,
        seen_at: str,
        lease_seconds: int,
    ) -> dict[str, Any]:
        kind = event["notification_kind"]
        delta_json = (
            None
            if event["delta"] is None
            else canonical_json_bytes(event["delta"]).decode("utf-8")
        )
        claim_generation = 0
        claim_acquired_at = None
        claim_token = None
        claim_expires_at = None
        ack_state = "not_required"
        delivery_state = "suppressed"
        disposition = "suppressed_control"
        should_begin_delivery = False
        if kind not in CONTROL_KINDS:
            if kind == "periodic_digest":
                if (
                    event["supersedes_event_id"] is not None
                    or event["delta"] is not None
                ):
                    raise NotificationContractError(
                        "periodic_digest events must remain unlinked"
                    )
                prior = None
            else:
                prior = connection.execute(
                    """SELECT * FROM notification_events
                       WHERE source_thread_id=? AND event_class=?
                         AND notification_kind NOT IN (
                           'heartbeat', 'continuation', 'periodic_digest'
                         )
                       ORDER BY sequence DESC LIMIT 1""",
                    (event["source_thread_id"], event["event_class"]),
                ).fetchone()
            if kind != "periodic_digest" and prior is None:
                if event["supersedes_event_id"] is not None:
                    raise NotificationContractError(
                        "first stream event cannot supersede an unknown predecessor"
                    )
            elif kind != "periodic_digest":
                if event["supersedes_event_id"] != prior["event_id"]:
                    raise NotificationContractError(
                        "changed payload must supersede the latest stream event"
                    )
                if event["delta"] is None:
                    raise NotificationContractError(
                        "changed payload must include machine-readable delta paths"
                    )
                if (
                    event["canonical_payload_digest"]
                    == prior["canonical_payload_digest"]
                ):
                    raise NotificationContractError(
                        "supersession requires changed canonical facts"
                    )
            if event["supersedes_event_id"] is not None:
                predecessor = connection.execute(
                    "SELECT * FROM notification_events WHERE event_id=?",
                    (event["supersedes_event_id"],),
                ).fetchone()
                if predecessor is None:
                    raise NotificationContractError("superseded event is not in the ledger")
                if (
                    predecessor["source_thread_id"] != event["source_thread_id"]
                    or predecessor["event_class"] != event["event_class"]
                ):
                    raise NotificationContractError(
                        "supersession must remain within one source/event-class stream"
                    )
            claim_generation = 1
            claim_acquired_at = claimed_at
            claim_token = self._claim_token()
            claim_expires_at = _timestamp(
                claimed + timedelta(seconds=lease_seconds)
            )
            ack_state = "pending"
            delivery_state = "claimed"
            disposition = "emit_claimed"
            should_begin_delivery = True
        connection.execute(
            """INSERT INTO notification_events(
                   event_id, source_thread_id, event_class, notification_kind,
                   event_contract_version, canonicalization_version,
                   canonical_payload_digest, first_envelope_digest,
                   last_envelope_digest, created_at, first_seen, last_seen,
                   duplicate_count, disposition, supersedes_event_id,
                   delta_json, claim_generation, claim_acquired_at, claim_token,
                   claim_expires_at, claimant_digest, delivery_state, ack_state
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event["event_id"],
                event["source_thread_id"],
                event["event_class"],
                kind,
                event["contract_version"],
                event["canonicalization"]["contract_version"],
                event["canonical_payload_digest"],
                event["transport_envelope_digest"],
                event["transport_envelope_digest"],
                event["created_at"],
                seen_at,
                seen_at,
                disposition,
                event["supersedes_event_id"],
                delta_json,
                claim_generation,
                claim_acquired_at,
                claim_token,
                claim_expires_at,
                claimant_digest,
                delivery_state,
                ack_state,
            ),
        )
        if (
            kind not in CONTROL_KINDS
            and kind != "periodic_digest"
            and event["supersedes_event_id"] is not None
        ):
            connection.execute(
                """UPDATE notification_events
                   SET superseded_by_event_id=?, disposition='superseded'
                   WHERE event_id=?""",
                (event["event_id"], event["supersedes_event_id"]),
            )
        row = connection.execute(
            "SELECT * FROM notification_events WHERE event_id=?",
            (event["event_id"],),
        ).fetchone()
        return self._claim_result(
            row,
            should_begin_delivery=should_begin_delivery,
            disposition=disposition,
        )

    @staticmethod
    def _claim_result(
        row: sqlite3.Row,
        *,
        should_begin_delivery: bool,
        disposition: str,
        ack_disposition: str = "accepted",
    ) -> dict[str, Any]:
        delivery_unknown = row["delivery_state"] == "delivery_in_progress"
        if row["ack_state"] == "accepted":
            delivery_outcome = "accepted"
        elif delivery_unknown:
            delivery_outcome = "UNKNOWN"
        else:
            delivery_outcome = "not_started"
        return {
            "event_id": row["event_id"],
            "should_emit": False,
            "should_begin_delivery": should_begin_delivery,
            "disposition": disposition,
            "duplicate_count": row["duplicate_count"],
            "claim_token": row["claim_token"] if should_begin_delivery else None,
            "claim_generation": (
                row["claim_generation"] if should_begin_delivery else None
            ),
            "claim_acquired_at": (
                row["claim_acquired_at"] if should_begin_delivery else None
            ),
            "claim_expires_at": (
                row["claim_expires_at"] if should_begin_delivery else None
            ),
            "ack": NotificationLedger._row_ack(row, ack_disposition),
            "delivery_outcome": delivery_outcome,
            "reconciliation_required": delivery_unknown,
            "retry_authorized": False,
            "operator_message_authorized": False,
        }

    def begin_delivery(
        self,
        event_id: str,
        *,
        claim_token: str,
        claim_generation: int,
    ) -> dict[str, Any]:
        """Atomically fence one claim immediately before transport begins."""

        if not EVENT_ID_RE.fullmatch(event_id):
            raise NotificationContractError("event_id is invalid")
        if not CLAIM_TOKEN_RE.fullmatch(claim_token):
            raise ClaimTokenError("claim_token is invalid")
        if (
            not isinstance(claim_generation, int)
            or isinstance(claim_generation, bool)
            or claim_generation < 1
        ):
            raise ClaimTokenError("claim_generation is invalid")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            started = self._ledger_utc_now("delivery")
            started_at = _timestamp(started)
            row = connection.execute(
                "SELECT * FROM notification_events WHERE event_id=?", (event_id,)
            ).fetchone()
            if row is None:
                raise NotificationContractError(
                    "event is not present in the receive ledger"
                )
            if row["notification_kind"] in CONTROL_KINDS:
                raise DeliveryStateError(
                    "heartbeat and continuation events do not authorize delivery"
                )
            if (
                row["claim_token"] != claim_token
                or row["claim_generation"] != claim_generation
            ):
                raise ClaimTokenError(
                    "delivery start does not match the active claim fence"
                )
            if row["ack_state"] == "accepted":
                raise DeliveryStateError("accepted delivery cannot be started again")
            if row["superseded_by_event_id"] is not None:
                raise DeliveryStateError("superseded delivery cannot be started")
            if row["delivery_state"] == "delivery_in_progress":
                raise DeliveryStateError(
                    "delivery outcome is unknown and requires reconciliation"
                )
            if row["delivery_state"] not in {"claimed", "retry_claimed"}:
                raise DeliveryStateError("claim is not eligible to begin delivery")
            expires = _utc(row["claim_expires_at"], "claim_expires_at")
            acquired = _utc(row["claim_acquired_at"], "claim_acquired_at")
            if started < acquired or started >= expires:
                raise DeliveryStateError(
                    "delivery start falls outside the active claim lease"
                )
            changed = connection.execute(
                """UPDATE notification_events
                   SET delivery_state='delivery_in_progress',
                       delivery_started_at=?, disposition='delivery_started'
                   WHERE event_id=? AND claim_token=? AND claim_generation=?
                     AND delivery_state IN ('claimed', 'retry_claimed')
                     AND ack_state='pending'""",
                (started_at, event_id, claim_token, claim_generation),
            )
            if changed.rowcount != 1:
                raise DeliveryStateError("delivery fence transition was not admitted")
            connection.execute("COMMIT")
            return {
                "event_id": event_id,
                "claim_token": claim_token,
                "claim_generation": claim_generation,
                "delivery_state": "delivery_in_progress",
                "delivery_outcome": "UNKNOWN",
                "reconciliation_required": True,
                "delivery_started_at": started_at,
                "transport_idempotency_key": event_id,
                "transport_event_id_dedupe_required": True,
                "should_emit": True,
                "retry_authorized": False,
                "operator_message_authorized": True,
            }
        except Exception as exc:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            self._raise_if_contention(exc)
            raise
        finally:
            connection.close()

    def acknowledge(
        self,
        event_id: str,
        *,
        claim_token: str,
        claim_generation: int,
        acknowledged_at: str,
    ) -> dict[str, Any]:
        if not EVENT_ID_RE.fullmatch(event_id):
            raise NotificationContractError("event_id is invalid")
        if not CLAIM_TOKEN_RE.fullmatch(claim_token):
            raise ClaimTokenError("claim_token is invalid")
        if (
            not isinstance(claim_generation, int)
            or isinstance(claim_generation, bool)
            or claim_generation < 1
        ):
            raise ClaimTokenError("claim_generation is invalid")
        acknowledged = _utc(acknowledged_at, "acknowledged_at")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM notification_events WHERE event_id=?", (event_id,)
            ).fetchone()
            if row is None:
                raise NotificationContractError("event is not present in the receive ledger")
            if row["notification_kind"] in CONTROL_KINDS:
                raise NotificationContractError(
                    "heartbeat and continuation events do not authorize delivery acknowledgement"
                )
            if (
                row["claim_token"] != claim_token
                or row["claim_generation"] != claim_generation
            ):
                raise ClaimTokenError(
                    "acknowledgement does not match the active claim fence"
                )
            if row["ack_state"] == "accepted":
                connection.execute("COMMIT")
                return self._row_ack(row, "replayed")
            if row["delivery_state"] != "delivery_in_progress":
                raise DeliveryStateError(
                    "acknowledgement requires a fenced delivery in progress"
                )
            delivery_started = _utc(
                row["delivery_started_at"], "delivery_started_at"
            )
            if acknowledged < delivery_started:
                raise DeliveryStateError(
                    "acknowledgement predates the fenced delivery start"
                )
            ack_id = self._ack_id(event_id, claim_token, claim_generation)
            connection.execute(
                """UPDATE notification_events
                   SET delivery_state='accepted', ack_state='accepted',
                       ack_id=?, acknowledged_at=?, disposition='delivered'
                   WHERE event_id=?""",
                (ack_id, acknowledged_at, event_id),
            )
            updated = connection.execute(
                "SELECT * FROM notification_events WHERE event_id=?", (event_id,)
            ).fetchone()
            connection.execute("COMMIT")
            return self._row_ack(updated, "accepted")
        except Exception as exc:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            self._raise_if_contention(exc)
            raise
        finally:
            connection.close()

    def should_retry(self, event_id: str, *, at: str) -> bool:
        moment = _utc(at, "at")
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM notification_events WHERE event_id=?", (event_id,)
            ).fetchone()
        except Exception as exc:
            self._raise_if_contention(exc)
            raise
        finally:
            connection.close()
        if row is None:
            return True
        if row["ack_state"] == "accepted" or row["notification_kind"] in CONTROL_KINDS:
            return False
        if row["delivery_state"] == "delivery_in_progress":
            return False
        if row["delivery_state"] not in {"claimed", "retry_claimed"}:
            return False
        if row["claim_expires_at"] is None:
            return False
        return _utc(row["claim_expires_at"], "claim_expires_at") <= moment

    def record(self, event_id: str) -> dict[str, Any] | None:
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM notification_events WHERE event_id=?", (event_id,)
            ).fetchone()
        except Exception as exc:
            self._raise_if_contention(exc)
            raise
        finally:
            connection.close()
        if row is None:
            return None
        if row["ack_state"] == "accepted":
            delivery_outcome = "accepted"
        elif row["delivery_state"] == "delivery_in_progress":
            delivery_outcome = "UNKNOWN"
        else:
            delivery_outcome = "not_started"
        return {
            "ledger_schema_version": LEDGER_SCHEMA_VERSION,
            "event_contract_version": row["event_contract_version"],
            "canonicalization_version": row["canonicalization_version"],
            "event_id": row["event_id"],
            "source_thread_id": row["source_thread_id"],
            "event_class": row["event_class"],
            "notification_kind": row["notification_kind"],
            "canonical_payload_digest": row["canonical_payload_digest"],
            "first_seen": row["first_seen"],
            "last_seen": row["last_seen"],
            "duplicate_count": row["duplicate_count"],
            "disposition": row["disposition"],
            "supersession": {
                "supersedes_event_id": row["supersedes_event_id"],
                "superseded_by_event_id": row["superseded_by_event_id"],
                "delta": None if row["delta_json"] is None else json.loads(row["delta_json"]),
            },
            "delivery_state": row["delivery_state"],
            "claim_generation": row["claim_generation"],
            "claim_acquired_at": row["claim_acquired_at"],
            "claim_expires_at": row["claim_expires_at"],
            "delivery_started_at": row["delivery_started_at"],
            "delivery_outcome": delivery_outcome,
            "reconciliation_required": (
                row["delivery_state"] == "delivery_in_progress"
                and row["ack_state"] != "accepted"
            ),
            "ack_state": row["ack_state"],
            "ack_id": row["ack_id"],
            "acknowledged_at": row["acknowledged_at"],
        }


def _reject_sensitive_input_path(path: Path) -> None:
    lowered = [part.lower() for part in path.parts]
    if "secrets" in lowered or any(part.startswith(".env") for part in lowered):
        raise NotificationContractError("sensitive input paths are not admitted")


def _load_json(path_value: str) -> dict[str, Any]:
    try:
        path = Path(path_value).resolve()
        _reject_sensitive_input_path(path)
        serialized = path.read_text(encoding="utf-8")
    except NotificationContractError:
        raise
    except (OSError, UnicodeError):
        raise NotificationContractError("input JSON could not be read") from None
    try:
        value = json.loads(serialized)
    except (json.JSONDecodeError, RecursionError):
        raise NotificationContractError("input JSON is malformed") from None
    if not isinstance(value, dict):
        raise NotificationContractError("input JSON must be an object")
    return value


def _build_event_from_input(source: Mapping[str, Any]) -> dict[str, Any]:
    required = {"source_thread_id", "event_class", "payload", "created_at"}
    optional = {"notification_kind", "supersedes_event_id", "delta"}
    missing = sorted(required - set(source))
    extra = sorted(set(source) - required - optional)
    if missing or extra:
        raise NotificationContractError(
            f"input JSON fields mismatch; missing={missing}, extra={extra}"
        )
    try:
        return build_event(**source)
    except TypeError:
        raise NotificationContractError(
            "input JSON contains invalid build-event arguments"
        ) from None


def _ledger(args: argparse.Namespace) -> NotificationLedger:
    return NotificationLedger(args.runtime_root, args.ledger)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare and deduplicate Atlas operator notifications without sending them."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--input", required=True)

    provision = subparsers.add_parser("provision")
    provision.add_argument("--runtime-root", required=True)
    provision.add_argument("--ledger", required=True)

    claim = subparsers.add_parser("claim")
    claim.add_argument("--runtime-root", required=True)
    claim.add_argument("--ledger", required=True)
    claim.add_argument("--event", required=True)
    claim.add_argument("--claimant-id", required=True)
    claim.add_argument("--seen-at", required=True)
    claim.add_argument("--lease-seconds", type=int, default=300)

    begin = subparsers.add_parser("begin-delivery")
    begin.add_argument("--runtime-root", required=True)
    begin.add_argument("--ledger", required=True)
    begin.add_argument("--event-id", required=True)
    begin.add_argument("--claim-token", required=True)
    begin.add_argument("--claim-generation", type=int, required=True)

    ack = subparsers.add_parser("ack")
    ack.add_argument("--runtime-root", required=True)
    ack.add_argument("--ledger", required=True)
    ack.add_argument("--event-id", required=True)
    ack.add_argument("--claim-token", required=True)
    ack.add_argument("--claim-generation", type=int, required=True)
    ack.add_argument("--acknowledged-at", required=True)

    status = subparsers.add_parser("status")
    status.add_argument("--runtime-root", required=True)
    status.add_argument("--ledger", required=True)
    status.add_argument("--event-id", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "prepare":
            source = _load_json(args.input)
            result = _build_event_from_input(source)
        elif args.command == "provision":
            NotificationLedger.provision(args.runtime_root, args.ledger)
            result = {
                "status": "provisioned",
                "ledger_schema_version": LEDGER_SCHEMA_VERSION,
            }
        elif args.command == "claim":
            result = _ledger(args).claim(
                _load_json(args.event),
                claimant_id=args.claimant_id,
                seen_at=args.seen_at,
                lease_seconds=args.lease_seconds,
            )
        elif args.command == "begin-delivery":
            result = _ledger(args).begin_delivery(
                args.event_id,
                claim_token=args.claim_token,
                claim_generation=args.claim_generation,
            )
        elif args.command == "ack":
            result = _ledger(args).acknowledge(
                args.event_id,
                claim_token=args.claim_token,
                claim_generation=args.claim_generation,
                acknowledged_at=args.acknowledged_at,
            )
        else:
            result = _ledger(args).record(args.event_id)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (
        NotificationContractError,
        LedgerCorruptionError,
        UnknownLedgerSchemaError,
        LedgerUnavailableError,
        LedgerProvisioningError,
    ) as exc:
        print(
            json.dumps(
                {"status": "rejected", "error": type(exc).__name__, "message": str(exc)},
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
