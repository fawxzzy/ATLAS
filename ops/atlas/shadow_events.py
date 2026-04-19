from __future__ import annotations

import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ops.events.invoke_event import (
    build_receipt,
    default_receipt_root,
    load_schema,
    schema_root,
    validate_instance,
    write_receipt,
)

EVENT_CONTRACT_VERSION = "atlas.event.v1"
SHADOW_PRODUCER_NAME = "atlas-session-runner-shadow"
SHADOW_PRODUCER_VERSION = "1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stamp_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _safe_token(value: str) -> str:
    cleaned = "".join(character if character.isalnum() or character in "._-" else "-" for character in value.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "event"


def build_shadow_event(
    *,
    event_type: str,
    session_id: str,
    workspace_root: str,
    payload: dict[str, Any],
    task: dict[str, Any] | None = None,
    event_token: str | None = None,
    occurred_at: str | None = None,
) -> dict[str, Any]:
    event_id_suffix = _safe_token(event_token or stamp_now())
    event = {
        "contract_version": EVENT_CONTRACT_VERSION,
        "event_type": event_type,
        "event_id": _safe_token(f"{session_id}:{event_type}:{event_id_suffix}"),
        "occurred_at": occurred_at or utc_now(),
        "producer": {
            "kind": "service",
            "name": SHADOW_PRODUCER_NAME,
            "version": SHADOW_PRODUCER_VERSION,
            "host": socket.gethostname(),
        },
        "session": {
            "session_id": session_id,
            "workspace_root": workspace_root,
            "operator": "atlas-root",
            "run_label": "shadow-mode",
        },
        "payload": payload,
    }
    if task is not None:
        event["task"] = task
    return event


def emit_shadow_event(
    *,
    event_type: str,
    session_id: str,
    workspace_root: str,
    payload: dict[str, Any],
    task: dict[str, Any] | None = None,
    event_token: str | None = None,
    occurred_at: str | None = None,
    receipt_root: Path | None = None,
    strict: bool = True,
) -> dict[str, Any]:
    event = build_shadow_event(
        event_type=event_type,
        session_id=session_id,
        workspace_root=workspace_root,
        payload=payload,
        task=task,
        event_token=event_token,
        occurred_at=occurred_at,
    )
    schema_path = schema_root() / f"{event_type}.schema.json"
    schema = load_schema(event_type)
    validation_errors = validate_instance(event, schema)
    if validation_errors and strict:
        raise ValueError("; ".join(validation_errors))
    handler_result = {
        "status": "skipped",
        "reason": "shadow_mode_no_handler",
    }
    receipt = build_receipt(event, schema_path, validation_errors, handler_result)
    paths = write_receipt(
        receipt_root if receipt_root is not None else default_receipt_root(),
        [event_type],
        event["event_id"],
        receipt,
    )
    return {
        "ok": not validation_errors,
        "event": event,
        "paths": paths,
        "errors": validation_errors,
    }
