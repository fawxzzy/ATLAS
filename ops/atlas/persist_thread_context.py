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
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\b(?:sk|sbp|ghp)_[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
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
    if any(pattern.search(normalized) for pattern in SECRET_PATTERNS):
        raise ThreadContextError(f"{field} contains secret-like material")
    return normalized


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
        "raw_transcript_included": False,
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
    payload = checkpoint.get("payload")
    if checkpoint.get("schema") != SCHEMA or not isinstance(payload, dict):
        raise ThreadContextError("Malformed thread context checkpoint")
    if checkpoint.get("payload_digest") != _digest(payload):
        raise ThreadContextError("Thread context payload digest mismatch")

    thread_id = _stable_id(str(payload.get("thread_id") or ""), "thread_id")
    thread_dir = root / thread_id
    immutable_path = thread_dir / f"{checkpoint['checkpoint_id']}.json"
    existed_before = immutable_path.exists()
    if existed_before:
        existing = json.loads(immutable_path.read_text(encoding="utf-8"))
        if existing != checkpoint:
            raise ThreadContextError("Checkpoint identity collision")
    else:
        _atomic_write_json(immutable_path, checkpoint)
    _atomic_write_json(thread_dir / "latest.json", checkpoint)

    index_path = root / "index.json"
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
        "latest_ref": str(thread_dir / "latest.json"),
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
