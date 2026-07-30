from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = ROOT / "runtime" / "atlas" / "thread-context"
SCHEMA = "atlas.thread-context-checkpoint.v1"
STATES = {"ACTIVE", "WAITING", "BLOCKED", "TERMINAL", "IDLE"}
SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]+$")
SAFE_PATH_COMPONENT = re.compile(r"^[A-Za-z0-9._-]+$")
WINDOWS_RESERVED_PATH_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}
PAYLOAD_DIGEST = re.compile(r"^sha256:([0-9a-f]{64})$")
CHECKPOINT_KEYS = {"schema", "checkpoint_id", "payload_digest", "payload"}
PAYLOAD_KEYS = {
    "thread_id",
    "logical_role_id",
    "visible_title",
    "state",
    "recorded_at",
    "summary",
    "done",
    "now",
    "next",
    "decisions",
    "blockers",
    "receipts",
    "source_refs",
    "content_class",
    "sensitive_material_policy",
}
PAYLOAD_TEXT_FIELDS = {
    "thread_id",
    "logical_role_id",
    "visible_title",
    "state",
    "recorded_at",
    "summary",
    "content_class",
    "sensitive_material_policy",
}
PAYLOAD_LIST_FIELDS = {
    "done",
    "now",
    "next",
    "decisions",
    "blockers",
    "receipts",
    "source_refs",
}
SENSITIVE_TEXT_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\b(?:sk[-_]|sbp_)[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bsb_(?:secret|publishable)_[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{8,}=*\b", re.IGNORECASE),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(
        r"\b(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis|amqps?|https?)"
        r"://[^/\s:@]+:[^@\s/]+@",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:cookie|set-cookie|authorization)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(
        r"\b(?:password|passwd|pwd|secret|token|api[_-]?key|client[_-]?secret|"
        r"access[_-]?key|private[_-]?key|session[_-]?key)\s*[:=]\s*['\"]?[^\s,'\";]{6,}",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b[A-Z][A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|PRIVATE_KEY|"
        r"COOKIE|CREDENTIAL)[A-Z0-9_]*\s*=\s*\S+"
    ),
    re.compile(r"\b(?:sessionid|connect\.sid|__Host-|__Secure-)[A-Za-z0-9_.-]*\s*=\s*\S+", re.IGNORECASE),
)


class ThreadContextError(ValueError):
    pass


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(payload: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical_bytes(payload)).hexdigest()}"


def _stable_id(value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized or not SAFE_ID.fullmatch(normalized):
        raise ThreadContextError(f"{field} must be a stable identifier")
    return normalized


def _clean_text(value: str, field: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ThreadContextError(f"{field} must not be empty")
    _assert_no_sensitive_material(normalized)
    return normalized


def _assert_no_sensitive_material(value: Any) -> None:
    if isinstance(value, str):
        if any(pattern.search(value) for pattern in SENSITIVE_TEXT_PATTERNS):
            raise ThreadContextError("context contains prohibited sensitive material")
        return
    if isinstance(value, dict):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise ThreadContextError("Malformed thread context checkpoint")
            _assert_no_sensitive_material(key)
            _assert_no_sensitive_material(nested)
        return
    if isinstance(value, (list, tuple)):
        for nested in value:
            _assert_no_sensitive_material(nested)
        return
    if value is None or isinstance(value, (bool, int, float)):
        return
    raise ThreadContextError("Malformed thread context checkpoint")


def _validate_checkpoint_shape(checkpoint: Any) -> dict[str, Any]:
    if not isinstance(checkpoint, dict) or set(checkpoint) != CHECKPOINT_KEYS:
        raise ThreadContextError("Malformed thread context checkpoint")
    payload = checkpoint.get("payload")
    if checkpoint.get("schema") != SCHEMA or not isinstance(payload, dict):
        raise ThreadContextError("Malformed thread context checkpoint")
    if set(payload) != PAYLOAD_KEYS:
        raise ThreadContextError("Malformed thread context checkpoint")
    if any(not isinstance(payload.get(field), str) for field in PAYLOAD_TEXT_FIELDS):
        raise ThreadContextError("Malformed thread context checkpoint")
    for field in PAYLOAD_LIST_FIELDS:
        values = payload.get(field)
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise ThreadContextError("Malformed thread context checkpoint")
    if payload["state"] not in STATES:
        raise ThreadContextError("Malformed thread context checkpoint")
    if payload["content_class"] != "COMPACT_OPERATIONAL_CONTEXT":
        raise ThreadContextError("Malformed thread context checkpoint")
    if payload["sensitive_material_policy"] != "REJECT_BEFORE_PERSISTENCE":
        raise ThreadContextError("Malformed thread context checkpoint")
    if payload["thread_id"] != _stable_id(payload["thread_id"], "thread_id"):
        raise ThreadContextError("Malformed thread context checkpoint")
    if payload["logical_role_id"] != _stable_id(payload["logical_role_id"], "logical_role_id"):
        raise ThreadContextError("Malformed thread context checkpoint")
    for field in {"visible_title", "recorded_at", "summary"}:
        if payload[field] != _clean_text(payload[field], field):
            raise ThreadContextError("Malformed thread context checkpoint")
    for field in PAYLOAD_LIST_FIELDS:
        if payload[field] != _clean_list(payload[field], field):
            raise ThreadContextError("Malformed thread context checkpoint")
    return payload


def _safe_path_component(value: str, field: str) -> str:
    windows_stem = value.split(".", 1)[0].upper()
    if (
        not SAFE_PATH_COMPONENT.fullmatch(value)
        or value in {".", ".."}
        or value.endswith((".", " "))
        or windows_stem in WINDOWS_RESERVED_PATH_NAMES
        or Path(value).name != value
        or Path(value).is_absolute()
    ):
        raise ThreadContextError(f"{field} must be one safe path component")
    return value


def _resolved_beneath(root: Path, candidate: Path) -> Path:
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ThreadContextError("Thread context path escapes output root") from error
    return resolved


def _clean_list(values: list[str] | None, field: str) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        cleaned = _clean_text(value, field)
        if cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def build_checkpoint(
    *,
    thread_id: str,
    role_id: str,
    title: str,
    state: str,
    summary: str,
    recorded_at: str | None = None,
    done: list[str] | None = None,
    now: list[str] | None = None,
    next_items: list[str] | None = None,
    decisions: list[str] | None = None,
    blockers: list[str] | None = None,
    receipts: list[str] | None = None,
    source_refs: list[str] | None = None,
) -> dict[str, Any]:
    normalized_state = state.strip().upper()
    if normalized_state not in STATES:
        raise ThreadContextError(f"state must be one of {sorted(STATES)}")
    timestamp = recorded_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "thread_id": _stable_id(thread_id, "thread_id"),
        "logical_role_id": _stable_id(role_id, "role_id"),
        "visible_title": _clean_text(title, "title"),
        "state": normalized_state,
        "recorded_at": _clean_text(timestamp, "recorded_at"),
        "summary": _clean_text(summary, "summary"),
        "done": _clean_list(done, "done"),
        "now": _clean_list(now, "now"),
        "next": _clean_list(next_items, "next"),
        "decisions": _clean_list(decisions, "decisions"),
        "blockers": _clean_list(blockers, "blockers"),
        "receipts": _clean_list(receipts, "receipts"),
        "source_refs": _clean_list(source_refs, "source_refs"),
        "content_class": "COMPACT_OPERATIONAL_CONTEXT",
        "sensitive_material_policy": "REJECT_BEFORE_PERSISTENCE",
    }
    payload_digest = _digest(payload)
    return {
        "schema": SCHEMA,
        "checkpoint_id": f"threadctx_{payload_digest.removeprefix('sha256:')}",
        "payload_digest": payload_digest,
        "payload": payload,
    }


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _load_index(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema": "atlas.thread-context-index.v1", "threads": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ThreadContextError(f"Unable to read context index: {error}") from error
    if payload.get("schema") != "atlas.thread-context-index.v1" or not isinstance(payload.get("threads"), list):
        raise ThreadContextError("Malformed thread context index")
    return payload


def persist_checkpoint(
    checkpoint: dict[str, Any],
    *,
    output_root: Path | None = None,
) -> dict[str, Any]:
    root = (output_root or DEFAULT_OUTPUT_ROOT).resolve()
    _assert_no_sensitive_material(checkpoint)
    payload = _validate_checkpoint_shape(checkpoint)
    expected_digest = _digest(payload)
    if checkpoint.get("payload_digest") != expected_digest:
        raise ThreadContextError("Thread context payload digest mismatch")
    digest_match = PAYLOAD_DIGEST.fullmatch(expected_digest)
    if digest_match is None:
        raise ThreadContextError("Malformed thread context checkpoint")
    expected_checkpoint_id = f"threadctx_{digest_match.group(1)}"
    if checkpoint.get("checkpoint_id") != expected_checkpoint_id:
        raise ThreadContextError("Thread context checkpoint identity mismatch")
    _safe_path_component(expected_checkpoint_id, "checkpoint_id")

    thread_id = _safe_path_component(payload["thread_id"], "thread_id")
    thread_dir = _resolved_beneath(root, root / thread_id)
    immutable_path = _resolved_beneath(root, thread_dir / f"{expected_checkpoint_id}.json")
    latest_path = _resolved_beneath(root, thread_dir / "latest.json")
    index_path = _resolved_beneath(root, root / "index.json")
    try:
        thread_dir.mkdir(parents=True, exist_ok=True)
        if not thread_dir.is_dir():
            raise OSError("thread context path is not a directory")
        existed_before = immutable_path.exists()
    except OSError as error:
        raise ThreadContextError("Unable to prepare thread context path") from error
    if existed_before:
        existing = json.loads(immutable_path.read_text(encoding="utf-8"))
        if existing != checkpoint:
            raise ThreadContextError("Checkpoint identity collision")
    else:
        _atomic_write_json(immutable_path, checkpoint)
    _atomic_write_json(latest_path, checkpoint)

    index = _load_index(index_path)
    records = {
        str(item.get("thread_id")): item
        for item in index["threads"]
        if isinstance(item, dict) and item.get("thread_id")
    }
    records[thread_id] = {
        "thread_id": thread_id,
        "logical_role_id": payload["logical_role_id"],
        "visible_title": payload["visible_title"],
        "state": payload["state"],
        "recorded_at": payload["recorded_at"],
        "checkpoint_id": checkpoint["checkpoint_id"],
        "payload_digest": checkpoint["payload_digest"],
        "latest_ref": f"runtime/atlas/thread-context/{thread_id}/latest.json",
    }
    index["threads"] = [records[name] for name in sorted(records)]
    index["index_digest"] = _digest({"schema": index["schema"], "threads": index["threads"]})
    _atomic_write_json(index_path, index)
    return {
        "checkpoint_ref": str(immutable_path),
        "latest_ref": str(latest_path),
        "index_ref": str(index_path),
        "checkpoint_id": checkpoint["checkpoint_id"],
        "payload_digest": checkpoint["payload_digest"],
        "deduplicated": existed_before,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Persist a compact source-linked Atlas thread context checkpoint.")
    parser.add_argument("--thread-id", required=True)
    parser.add_argument("--role-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--state", required=True, choices=sorted(STATES))
    parser.add_argument("--summary", required=True)
    parser.add_argument("--recorded-at")
    parser.add_argument("--done", action="append", default=[])
    parser.add_argument("--now", action="append", default=[])
    parser.add_argument("--next", dest="next_items", action="append", default=[])
    parser.add_argument("--decision", action="append", default=[])
    parser.add_argument("--blocker", action="append", default=[])
    parser.add_argument("--receipt", action="append", default=[])
    parser.add_argument("--source-ref", action="append", default=[])
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    checkpoint = build_checkpoint(
        thread_id=args.thread_id,
        role_id=args.role_id,
        title=args.title,
        state=args.state,
        summary=args.summary,
        recorded_at=args.recorded_at,
        done=args.done,
        now=args.now,
        next_items=args.next_items,
        decisions=args.decision,
        blockers=args.blocker,
        receipts=args.receipt,
        source_refs=args.source_ref,
    )
    result = persist_checkpoint(checkpoint, output_root=args.output_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
