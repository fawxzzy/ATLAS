from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ALIAS_SCHEMA = "atlas.scoped-approval-alias.v1"
AUTHORIZATION_SCHEMA = "atlas.scoped-approval-authorization.v1"
CONSUMPTION_SCHEMA = "atlas.scoped-approval-consumption.v1"
TASK_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f-]{27,}$", re.IGNORECASE)
SAFE_TOKEN = re.compile(r"^[A-Za-z0-9._:/@+-]+$")
PACKET_LABEL = re.compile(r"(?:^|-)R(\d{3})(?:-|$)")


class ScopedApprovalError(ValueError):
    pass


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(payload: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical_bytes(payload)).hexdigest()}"


def _file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise ScopedApprovalError(f"Unable to read {path}: {error}") from error


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ScopedApprovalError(f"Unable to read JSON {path}: {error}") from error
    if not isinstance(payload, dict):
        raise ScopedApprovalError(f"Expected JSON object at {path}")
    return payload


def _write_once_or_idempotent(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            # A same-directory hard-link publish is atomic and never replaces an
            # existing canonical receipt. The complete temporary inode is
            # visible only after it wins this destination-name race.
            os.link(temporary, path)
            return
        except FileExistsError:
            if _load_json(path) == payload:
                return
            raise ScopedApprovalError(f"Output identity collision at {path}")
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ScopedApprovalError("Timestamp must be a non-empty ISO-8601 string")
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ScopedApprovalError(f"Invalid ISO-8601 timestamp: {value}") from error
    if parsed.tzinfo is None:
        raise ScopedApprovalError("Timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonicalize_decision_request(
    *, template_path: Path, created_at: str, expires_at: str
) -> dict[str, Any]:
    payload = _load_json(template_path)
    if payload.get("schema") != "atlas.operator-decision-request.v1":
        raise ScopedApprovalError("Unsupported decision request schema")
    if payload.get("execution_authority") is not False:
        raise ScopedApprovalError("Decision request must still be execution-disabled")
    created = _utc(created_at)
    expires = _utc(expires_at)
    if expires <= created:
        raise ScopedApprovalError("expires_at must be after created_at")
    payload["created_at"] = _iso(created)
    payload["expires_at"] = _iso(expires)
    return payload


def _require_token(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or not SAFE_TOKEN.fullmatch(value.strip()):
        raise ScopedApprovalError(f"{field} must be a stable token")
    return value.strip()


def _decision_ref(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return str(resolved)


def canonical_alias_path(decision_request_path: Path) -> Path:
    stem = decision_request_path.stem
    for suffix in ("-operator-decision-request", "-decision-request"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    return decision_request_path.with_name(f"{stem}-scoped-approval-alias.json")


def canonical_authorization_path(alias_path: Path) -> Path:
    return alias_path.with_name(f"{alias_path.stem}-authorization.json")


def canonical_consumption_path(alias_path: Path) -> Path:
    return alias_path.with_name(f"{alias_path.stem}-consumption.json")


def _approval_code(packet: str, intent_digest: str) -> str:
    match = PACKET_LABEL.search(packet)
    label = f"R{match.group(1)}" if match else "ACT"
    digest_bytes = bytes.fromhex(intent_digest.removeprefix("sha256:"))[:10]
    encoded = base64.b32encode(digest_bytes).decode("ascii").rstrip("=")
    grouped = "-".join(encoded[index : index + 4] for index in range(0, len(encoded), 4))
    return f"{label}-{grouped}"


def issue_alias(
    *,
    decision_request_path: Path,
    originating_task_id: str,
    effect_class: str,
    target: str,
    max_effect_count: int,
    expires_at: str,
    issued_at: str | None = None,
) -> dict[str, Any]:
    decision = _load_json(decision_request_path)
    phrase = decision.get("exact_authorization_phrase")
    if not isinstance(phrase, str) or not phrase.strip():
        raise ScopedApprovalError("Decision request must contain exact_authorization_phrase")
    if decision.get("execution_authority") is not False:
        raise ScopedApprovalError("Decision request must still be execution-disabled")
    packet = _require_token(str(decision.get("packet", "")), "packet")
    semantic_objective = _require_token(str(decision.get("semantic_objective", "")), "semantic_objective")
    task_id = originating_task_id.strip()
    if not TASK_ID.fullmatch(task_id):
        raise ScopedApprovalError("originating_task_id must be a stable task UUID")
    effect = _require_token(effect_class, "effect_class")
    exact_target = _require_token(target, "target")
    if not isinstance(max_effect_count, int) or not 1 <= max_effect_count <= 100:
        raise ScopedApprovalError("max_effect_count must be an integer from 1 to 100")

    issued = _utc(issued_at) if issued_at else datetime.now(timezone.utc)
    expires = _utc(expires_at)
    if expires <= issued:
        raise ScopedApprovalError("expires_at must be after issued_at")
    decision_expires_raw = decision.get("expires_at")
    if not isinstance(decision_expires_raw, str):
        raise ScopedApprovalError("Decision request must contain expires_at")
    decision_expires = _iso(_utc(decision_expires_raw))
    if decision_expires_raw != decision_expires:
        raise ScopedApprovalError("Decision request expires_at must use canonical six-digit UTC form")
    if decision_expires != _iso(expires):
        raise ScopedApprovalError("Decision request and alias expiry must match")

    decision_sha = _file_sha256(decision_request_path)
    phrase_sha = hashlib.sha256(phrase.encode("utf-8")).hexdigest()
    intent = {
        "decision_request_sha256": decision_sha,
        "exact_authorization_phrase_sha256": phrase_sha,
        "semantic_objective": semantic_objective,
        "packet": packet,
        "originating_task_id": task_id,
        "effect_class": effect,
        "target": exact_target,
        "max_effect_count": max_effect_count,
        "expires_at": _iso(expires),
        "single_use": True,
    }
    intent_digest = _digest(intent)
    code = _approval_code(packet, intent_digest)
    return {
        "schema": ALIAS_SCHEMA,
        "status": "OPEN",
        "issued_at": _iso(issued),
        "expires_at": _iso(expires),
        "originating_task_id": task_id,
        "packet": packet,
        "semantic_objective": semantic_objective,
        "decision_request": {
            "path": _decision_ref(decision_request_path),
            "sha256": decision_sha,
            "exact_authorization_phrase_sha256": phrase_sha,
        },
        "allowed_effect": {
            "effect_class": effect,
            "target": exact_target,
            "max_effect_count": max_effect_count,
        },
        "intent_digest": intent_digest,
        "approval_code": code,
        "expected_operator_response": f"APPROVE {code}",
        "single_use": True,
        "execution_authority": False,
    }


def _resolve_decision_path(alias_path: Path, value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    return candidate.resolve()


def authorize_alias(
    *,
    alias_path: Path,
    operator_response: str,
    originating_task_id: str,
    authorized_at: str | None = None,
) -> dict[str, Any]:
    alias = _load_json(alias_path)
    if alias.get("schema") != ALIAS_SCHEMA or alias.get("status") != "OPEN":
        raise ScopedApprovalError("Alias is not an open scoped approval")
    if alias.get("single_use") is not True or alias.get("execution_authority") is not False:
        raise ScopedApprovalError("Alias authority state is malformed")
    if alias.get("originating_task_id") != originating_task_id:
        raise ScopedApprovalError("Approval was issued in a different task")
    if canonical_consumption_path(alias_path).exists():
        raise ScopedApprovalError("Approval code was already consumed")

    now = _utc(authorized_at) if authorized_at else datetime.now(timezone.utc)
    if now > _utc(str(alias.get("expires_at", ""))):
        raise ScopedApprovalError("Approval code is expired")
    expected = " ".join(str(alias.get("expected_operator_response", "")).split()).upper()
    received = " ".join(operator_response.split()).upper()
    if not expected or received != expected:
        raise ScopedApprovalError("Operator response does not match the scoped approval code")

    decision_ref = alias.get("decision_request")
    if not isinstance(decision_ref, dict):
        raise ScopedApprovalError("Alias decision_request is malformed")
    decision_path = _resolve_decision_path(alias_path, str(decision_ref.get("path", "")))
    if alias_path.resolve() != canonical_alias_path(decision_path).resolve():
        raise ScopedApprovalError("Alias path is not canonical for the decision request")
    if _file_sha256(decision_path) != decision_ref.get("sha256"):
        raise ScopedApprovalError("Decision request hash drift")
    decision = _load_json(decision_path)
    phrase = decision.get("exact_authorization_phrase")
    if not isinstance(phrase, str) or hashlib.sha256(phrase.encode("utf-8")).hexdigest() != decision_ref.get(
        "exact_authorization_phrase_sha256"
    ):
        raise ScopedApprovalError("Exact authority phrase hash drift")
    if decision.get("packet") != alias.get("packet") or decision.get("execution_authority") is not False:
        raise ScopedApprovalError("Decision request identity or authority state drift")

    alias_sha = _file_sha256(alias_path)
    existing_path = canonical_authorization_path(alias_path)
    if existing_path.exists():
        existing = _load_json(existing_path)
        if (
            existing.get("schema") != AUTHORIZATION_SCHEMA
            or existing.get("status") != "AUTHORIZED_SINGLE_USE"
            or existing.get("originating_task_id") != originating_task_id
            or existing.get("intent_digest") != alias.get("intent_digest")
            or existing.get("alias", {}).get("sha256") != alias_sha
        ):
            raise ScopedApprovalError("Canonical authorization identity collision")
        return existing

    payload = {
        "schema": AUTHORIZATION_SCHEMA,
        "status": "AUTHORIZED_SINGLE_USE",
        "authorized_at": _iso(now),
        "originating_task_id": originating_task_id,
        "packet": alias["packet"],
        "alias": {"path": _decision_ref(alias_path), "sha256": alias_sha},
        "approval_code": alias["approval_code"],
        "intent_digest": alias["intent_digest"],
        "decision_request": decision_ref,
        "allowed_effect": alias["allowed_effect"],
        "single_use": True,
        "execution_authority": True,
        "full_phrase_replay_required": False,
    }
    payload["authorization_digest"] = _digest(payload)
    return payload


def consume_alias(
    *,
    alias_path: Path,
    authorization_path: Path,
    execution_correlation_id: str,
    consumed_at: str | None = None,
) -> dict[str, Any]:
    alias = _load_json(alias_path)
    authorization = _load_json(authorization_path)
    if alias.get("schema") != ALIAS_SCHEMA or authorization.get("schema") != AUTHORIZATION_SCHEMA:
        raise ScopedApprovalError("Unsupported alias or authorization schema")
    if authorization.get("status") != "AUTHORIZED_SINGLE_USE" or authorization.get("single_use") is not True:
        raise ScopedApprovalError("Authorization is not consumable")
    if authorization.get("intent_digest") != alias.get("intent_digest"):
        raise ScopedApprovalError("Authorization intent drift")
    if authorization.get("alias", {}).get("sha256") != _file_sha256(alias_path):
        raise ScopedApprovalError("Alias hash drift")
    correlation_id = _require_token(execution_correlation_id, "execution_correlation_id")
    canonical_authorization = canonical_authorization_path(alias_path)
    if authorization_path.resolve() != canonical_authorization.resolve():
        raise ScopedApprovalError("Authorization path is not the canonical alias authorization")
    authorization_sha = _file_sha256(authorization_path)
    consumption_path = canonical_consumption_path(alias_path)
    if consumption_path.exists():
        existing = _load_json(consumption_path)
        if (
            existing.get("schema") == CONSUMPTION_SCHEMA
            and existing.get("status") == "CONSUMED"
            and existing.get("authorization_sha256") == authorization_sha
            and existing.get("execution_correlation_id") == correlation_id
        ):
            return existing
        raise ScopedApprovalError("Approval code was already consumed by a different execution")
    now = _utc(consumed_at) if consumed_at else datetime.now(timezone.utc)
    payload = {
        "schema": CONSUMPTION_SCHEMA,
        "status": "CONSUMED",
        "consumed_at": _iso(now),
        "packet": alias["packet"],
        "approval_code": alias["approval_code"],
        "intent_digest": alias["intent_digest"],
        "authorization_sha256": authorization_sha,
        "execution_correlation_id": correlation_id,
        "max_effect_count": alias["allowed_effect"]["max_effect_count"],
        "reusable": False,
    }
    payload["consumption_digest"] = _digest(payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Issue and validate short, hash-bound Atlas approval codes.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    write_decision = subparsers.add_parser("write-decision")
    write_decision.add_argument("--template", type=Path, required=True)
    write_decision.add_argument("--created-at", required=True)
    write_decision.add_argument("--expires-at", required=True)
    write_decision.add_argument("--output", type=Path, required=True)

    issue = subparsers.add_parser("issue")
    issue.add_argument("--decision-request", type=Path, required=True)
    issue.add_argument("--originating-task-id", required=True)
    issue.add_argument("--effect-class", required=True)
    issue.add_argument("--target", required=True)
    issue.add_argument("--max-effect-count", type=int, required=True)
    issue.add_argument("--expires-at", required=True)
    issue.add_argument("--issued-at")
    issue.add_argument("--output", type=Path, required=True)

    authorize = subparsers.add_parser("authorize")
    authorize.add_argument("--alias", type=Path, required=True)
    authorize.add_argument("--response", required=True)
    authorize.add_argument("--originating-task-id", required=True)
    authorize.add_argument("--authorized-at")
    authorize.add_argument("--output", type=Path, required=True)

    consume = subparsers.add_parser("consume")
    consume.add_argument("--alias", type=Path, required=True)
    consume.add_argument("--authorization", type=Path, required=True)
    consume.add_argument("--execution-correlation-id", required=True)
    consume.add_argument("--consumed-at")
    consume.add_argument("--output", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "write-decision":
        payload = canonicalize_decision_request(
            template_path=args.template,
            created_at=args.created_at,
            expires_at=args.expires_at,
        )
    elif args.command == "issue":
        expected_output = canonical_alias_path(args.decision_request)
        if args.output.resolve() != expected_output.resolve():
            raise ScopedApprovalError(f"Alias output must be {expected_output}")
        payload = issue_alias(
            decision_request_path=args.decision_request,
            originating_task_id=args.originating_task_id,
            effect_class=args.effect_class,
            target=args.target,
            max_effect_count=args.max_effect_count,
            expires_at=args.expires_at,
            issued_at=args.issued_at,
        )
    elif args.command == "authorize":
        expected_output = canonical_authorization_path(args.alias)
        if args.output.resolve() != expected_output.resolve():
            raise ScopedApprovalError(f"Authorization output must be {expected_output}")
        payload = authorize_alias(
            alias_path=args.alias,
            operator_response=args.response,
            originating_task_id=args.originating_task_id,
            authorized_at=args.authorized_at,
        )
    else:
        expected_output = canonical_consumption_path(args.alias)
        if args.output.resolve() != expected_output.resolve():
            raise ScopedApprovalError(f"Consumption output must be {expected_output}")
        payload = consume_alias(
            alias_path=args.alias,
            authorization_path=args.authorization,
            execution_correlation_id=args.execution_correlation_id,
            consumed_at=args.consumed_at,
        )
    _write_once_or_idempotent(args.output, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
