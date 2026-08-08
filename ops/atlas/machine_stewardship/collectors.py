from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

from .contracts import OBSERVED_STATE_VOLATILE_FIELDS, canonical_json_bytes

DEFAULT_COMMAND_TIMEOUT_SECONDS = 10.0
REDACTED = "[REDACTED]"
_SENSITIVE_ASSIGNMENT = re.compile(
    r"(?i)\b(password|passwd|secret|token|api[_-]?key|cookie|authorization)"
    r"\s*[:=]\s*([^\s,;]+)"
)
_POSIX_HOME_PREFIXES = ("/" + "home/", "/" + "Users/")
_USER_HOME = re.compile(
    r"(?i)(?:[A-Z]:\\Users\\|"
    + "|".join(re.escape(prefix) for prefix in _POSIX_HOME_PREFIXES)
    + r")[^\\/\s]+"
)
_VOLUME_ID = re.compile(r"^[A-Z]:$")

_FIXED_LOCAL_VOLUME_SCRIPT = (
    "$ErrorActionPreference='Stop';"
    "$items=@(Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' |"
    "Select-Object DeviceID,DriveType,FileSystem,Size,FreeSpace,VolumeSerialNumber);"
    "$items | ConvertTo-Json -Compress"
)


@dataclass(frozen=True)
class CommandResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False


@dataclass(frozen=True)
class CollectorError:
    collector: str
    code: str
    message: str
    recoverable: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "collector": self.collector,
            "code": self.code,
            "message": redact_text(self.message),
            "recoverable": self.recoverable,
        }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def redact_text(value: str) -> str:
    """Redact common secret assignments and user-home identities."""

    redacted = _SENSITIVE_ASSIGNMENT.sub(lambda match: f"{match.group(1)}={REDACTED}", value)
    return _USER_HOME.sub(REDACTED, redacted)


def redact_sensitive_values(value: Any) -> Any:
    """Recursively redact sensitive keys and strings without changing input objects."""

    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key in sorted(value):
            key_text = str(key)
            if re.search(
                r"(?i)(password|passwd|secret|token|api[_-]?key|cookie|authorization|environment)",
                key_text,
            ):
                result[key_text] = REDACTED
            else:
                result[key_text] = redact_sensitive_values(value[key])
        return result
    if isinstance(value, list):
        return [redact_sensitive_values(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def run_command(
    args: Sequence[str],
    *,
    timeout_seconds: float = DEFAULT_COMMAND_TIMEOUT_SECONDS,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> CommandResult:
    """Run one bounded command without a shell and normalize its outcome."""

    if isinstance(args, (str, bytes)) or not args or not all(isinstance(arg, str) for arg in args):
        raise TypeError("Collector commands require a non-empty explicit string argument array.")
    if timeout_seconds <= 0:
        raise ValueError("Collector command timeout must be positive.")
    try:
        completed = runner(
            list(args),
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            stdout=redact_text(_coerce_output(exc.stdout)),
            stderr=redact_text(_coerce_output(exc.stderr)),
            exit_code=124,
            timed_out=True,
        )
    return CommandResult(
        stdout=redact_text(completed.stdout or ""),
        stderr=redact_text(completed.stderr or ""),
        exit_code=int(completed.returncode),
    )


def _coerce_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _fingerprint(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def collect_machine_identity(
    *,
    system: Callable[[], str] = platform.system,
    release: Callable[[], str] = platform.release,
    version: Callable[[], str] = platform.version,
    machine: Callable[[], str] = platform.machine,
    node: Callable[[], str] = platform.node,
) -> dict[str, Any]:
    """Collect non-admin identity metadata while retaining no raw host label."""

    raw_node = node().strip()
    return {
        "host_fingerprint": _fingerprint(raw_node or "unknown-host"),
        "host_label": REDACTED,
        "os_family": (system().strip() or "unknown").lower(),
        "os_release": redact_text(release().strip() or "unknown"),
        "os_version": redact_text(version().strip() or "unknown"),
        "architecture": machine().strip().lower() or "unknown",
    }


def _powershell_args() -> list[str]:
    return [
        "powershell.exe",
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        _FIXED_LOCAL_VOLUME_SCRIPT,
    ]


def collect_fixed_local_volumes(
    *,
    os_name: str = os.name,
    command: Callable[[Sequence[str]], CommandResult] = run_command,
) -> tuple[list[dict[str, Any]], str, list[CollectorError]]:
    """Collect metadata for Windows fixed local logical volumes without traversal."""

    if os_name != "nt":
        return (
            [],
            "unsupported",
            [
                CollectorError(
                    collector="fixed_local_volumes",
                    code="UNSUPPORTED_PLATFORM",
                    message="Fixed-local-volume collection is implemented only for Windows in Wave 0A.",
                    recoverable=False,
                )
            ],
        )

    result = command(_powershell_args())
    if result.exit_code != 0:
        detail = result.stderr.strip() or f"collector exited with status {result.exit_code}"
        code = "COMMAND_TIMEOUT" if result.timed_out else "COMMAND_FAILED"
        return (
            [],
            "failed",
            [
                CollectorError(
                    collector="fixed_local_volumes",
                    code=code,
                    message=detail,
                    recoverable=True,
                )
            ],
        )

    try:
        decoded = json.loads(result.stdout or "[]")
    except json.JSONDecodeError as exc:
        return (
            [],
            "failed",
            [
                CollectorError(
                    collector="fixed_local_volumes",
                    code="INVALID_COMMAND_OUTPUT",
                    message=f"collector returned invalid JSON at offset {exc.pos}",
                    recoverable=True,
                )
            ],
        )

    rows = decoded if isinstance(decoded, list) else [decoded]
    volumes: list[dict[str, Any]] = []
    errors: list[CollectorError] = []
    for index, row in enumerate(rows):
        try:
            volumes.append(_normalize_fixed_volume(row))
        except (TypeError, ValueError) as exc:
            errors.append(
                CollectorError(
                    collector="fixed_local_volumes",
                    code="INVALID_VOLUME_METADATA",
                    message=f"volume record {index} rejected: {exc}",
                    recoverable=True,
                )
            )
    volumes.sort(key=lambda item: item["volume_id"])
    status = "collected" if not errors else ("partial" if volumes else "failed")
    return volumes, status, errors


def _normalize_fixed_volume(row: Any) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        raise TypeError("record must be an object")
    volume_id = str(row.get("DeviceID", "")).upper()
    if not _VOLUME_ID.fullmatch(volume_id):
        raise ValueError("volume identifier is not a fixed local drive designator")
    if int(row.get("DriveType", -1)) != 3:
        raise ValueError("drive type is not fixed-local")
    capacity = _nonnegative_integer(row.get("Size"), "Size")
    free = _nonnegative_integer(row.get("FreeSpace"), "FreeSpace")
    if free > capacity:
        raise ValueError("FreeSpace exceeds Size")
    filesystem_raw = row.get("FileSystem")
    filesystem = None if filesystem_raw in (None, "") else str(filesystem_raw)
    if filesystem is not None and not re.fullmatch(r"[A-Za-z0-9._+-]{1,32}", filesystem):
        raise ValueError("filesystem metadata contains unsupported characters")
    serial = str(row.get("VolumeSerialNumber") or "")
    return {
        "volume_id": volume_id,
        "drive_type": "fixed",
        "filesystem": filesystem,
        "capacity_bytes": capacity,
        "free_bytes": free,
        "serial_fingerprint": _fingerprint(serial) if serial else None,
    }


def _nonnegative_integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{label} must be an integer") from exc
    if parsed < 0:
        raise ValueError(f"{label} must be non-negative")
    return parsed


def collect_observed_state(
    *,
    collected_at_utc: str | None = None,
    identity_collector: Callable[[], dict[str, Any]] = collect_machine_identity,
    volume_collector: Callable[
        [], tuple[list[dict[str, Any]], str, list[CollectorError]]
    ] = collect_fixed_local_volumes,
) -> dict[str, Any]:
    """Collect the admitted Wave 0A observation without machine mutation."""

    collected_at = collected_at_utc or utc_now()
    errors: list[CollectorError] = []
    try:
        identity = identity_collector()
        identity_status = "collected"
    except Exception as exc:
        identity = {
            "host_fingerprint": _fingerprint("unavailable-host"),
            "host_label": REDACTED,
            "os_family": "unknown",
            "os_release": "unknown",
            "os_version": "unknown",
            "architecture": "unknown",
        }
        identity_status = "failed"
        errors.append(
            CollectorError(
                collector="machine_identity",
                code="COLLECTION_FAILED",
                message=str(exc),
                recoverable=True,
            )
        )

    try:
        volumes, volume_status, volume_errors = volume_collector()
        errors.extend(volume_errors)
    except Exception as exc:
        volumes = []
        volume_status = "failed"
        errors.append(
            CollectorError(
                collector="fixed_local_volumes",
                code="COLLECTION_FAILED",
                message=str(exc),
                recoverable=True,
            )
        )

    identity = redact_sensitive_values(identity)
    volumes = redact_sensitive_values(volumes)
    observation_seed = {
        "collected_at_utc": collected_at,
        "machine_identity": identity,
        "fixed_local_volumes": volumes,
    }
    observation_id = "mobs_" + hashlib.sha256(canonical_json_bytes(observation_seed)).hexdigest()
    return {
        "contract_version": "atlas.machine-observed-state.v1",
        "observation_id": observation_id,
        "collected_at_utc": collected_at,
        "volatile_fields": list(OBSERVED_STATE_VOLATILE_FIELDS),
        "machine_identity": identity,
        "fixed_local_volumes": volumes,
        "collector_status": {
            "machine_identity": identity_status,
            "fixed_local_volumes": volume_status,
        },
        "collector_errors": [error.as_dict() for error in errors],
        "privacy": {
            "redaction_applied": True,
            "file_contents_read": False,
            "reparse_points_followed": False,
            "cloud_placeholders_hydrated": False,
            "network_shares_traversed": False,
            "environment_values_collected": False,
            "deletion_safety_inferred": False,
        },
    }
