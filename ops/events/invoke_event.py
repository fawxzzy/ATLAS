from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "atlas.event.v1"
RECEIPT_VERSION = "atlas.event.receipt.v1"
EVENT_TYPES = [
    "session_start",
    "task_start",
    "pre_command",
    "post_command",
    "validation_complete",
    "export_complete",
    "session_stop",
]
REJECTED_LANE = "_rejected"


def atlas_root() -> Path:
    return Path(__file__).resolve().parents[2]


def normalize_path(path: Path) -> str:
    root = atlas_root()
    resolved = path.resolve()
    if resolved.is_relative_to(root):
        relative = resolved.relative_to(root)
        return "." if not relative.parts else relative.as_posix()
    return resolved.as_posix()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stamp_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def make_identifier(prefix: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}"


def schema_root() -> Path:
    return atlas_root() / "ops" / "events" / "schemas"


def default_receipt_root() -> Path:
    return atlas_root() / "runtime" / "receipts" / "events"


def rejected_receipt_root(receipt_root: Path) -> Path:
    return receipt_root / REJECTED_LANE


def load_json_input(args: argparse.Namespace) -> dict[str, Any]:
    text: str
    if args.payload_file:
        text = Path(args.payload_file).read_text(encoding="utf-8-sig")
    elif args.payload_json:
        text = args.payload_json
    elif args.stdin:
        text = sys.stdin.read()
    else:
        raise ValueError("One of --payload-file, --payload-json, or --stdin is required.")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Payload is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Payload root must be a JSON object.")
    if args.event_type and "event_type" not in payload:
        payload["event_type"] = args.event_type
    if args.event_type and payload.get("event_type") != args.event_type:
        raise ValueError("Explicit --event-type does not match payload event_type.")
    return payload


def load_schema(event_type: str) -> dict[str, Any]:
    schema_path = schema_root() / f"{event_type}.schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Missing schema for event type '{event_type}'.")
    return json.loads(schema_path.read_text(encoding="utf-8-sig"))


def is_type(expected: str, value: Any) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValueError(f"Unsupported schema type: {expected}")


def validate_instance(instance: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected constant value {schema['const']!r}.")
        return errors
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']!r}.")
        return errors

    schema_type = schema.get("type")
    if schema_type is not None:
        expected_types = schema_type if isinstance(schema_type, list) else [schema_type]
        if not any(is_type(expected, instance) for expected in expected_types):
            errors.append(f"{path}: expected type {expected_types!r}.")
            return errors

    if isinstance(instance, str):
        min_length = schema.get("minLength")
        if min_length is not None and len(instance) < min_length:
            errors.append(f"{path}: string length must be at least {min_length}.")
        pattern = schema.get("pattern")
        if pattern is not None and re.fullmatch(pattern, instance) is None:
            errors.append(f"{path}: string does not match required pattern.")
        if schema.get("format") == "date-time":
            try:
                datetime.fromisoformat(instance.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{path}: value is not a valid ISO 8601 date-time.")

    if isinstance(instance, list):
        min_items = schema.get("minItems")
        if min_items is not None and len(instance) < min_items:
            errors.append(f"{path}: array must contain at least {min_items} item(s).")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(instance):
                errors.extend(validate_instance(item, item_schema, f"{path}[{index}]"))

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        minimum = schema.get("minimum")
        if minimum is not None and instance < minimum:
            errors.append(f"{path}: value must be at least {minimum}.")

    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{path}: missing required property '{key}'.")
        for key, value in instance.items():
            if key in properties:
                errors.extend(validate_instance(value, properties[key], f"{path}.{key}"))
                continue
            additional = schema.get("additionalProperties", True)
            if additional is False:
                errors.append(f"{path}: unexpected property '{key}'.")
            elif isinstance(additional, dict):
                errors.extend(validate_instance(value, additional, f"{path}.{key}"))

    return errors


def discover_handler(event_type: str) -> Path | None:
    handlers_dir = atlas_root() / "ops" / "events" / "handlers"
    for suffix in [".py", ".ps1"]:
        candidate = handlers_dir / f"{event_type}{suffix}"
        if candidate.exists():
            return candidate
    return None


def run_handler(handler_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    temp_dir = atlas_root() / "tmp" / "scratch" / "events"
    temp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, dir=temp_dir, encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        temp_path = Path(handle.name)
    try:
        if handler_path.suffix == ".py":
            command = [
                sys.executable,
                str(handler_path),
                "--payload-file",
                str(temp_path),
                "--atlas-root",
                str(atlas_root()),
            ]
        else:
            command = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(handler_path),
                "-PayloadFile",
                str(temp_path),
                "-AtlasRoot",
                str(atlas_root()),
            ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        parsed_result: dict[str, Any] = {}
        if result.stdout.strip():
            try:
                loaded = json.loads(result.stdout)
                parsed_result = loaded if isinstance(loaded, dict) else {"raw_stdout": result.stdout.strip()}
            except json.JSONDecodeError:
                parsed_result = {"raw_stdout": result.stdout.strip()}
        return {
            "status": "completed" if result.returncode == 0 else "failed",
            "command": command,
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "result": parsed_result,
        }
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def write_receipt(receipt_root: Path, lane_parts: list[str], event_id: str, receipt: dict[str, Any]) -> dict[str, str]:
    event_dir = receipt_root.joinpath(*lane_parts)
    event_dir.mkdir(parents=True, exist_ok=True)
    receipt_name = f"{stamp_now()}-{event_id}.json"
    receipt_path = event_dir / receipt_name
    latest_path = event_dir / "latest.json"
    receipt["paths"] = {
        "receipt_path": normalize_path(receipt_path),
        "latest_path": normalize_path(latest_path),
    }
    encoded = json.dumps(receipt, indent=2) + "\n"
    receipt_path.write_text(encoded, encoding="utf-8")
    latest_path.write_text(encoded, encoding="utf-8")
    return receipt["paths"]


def build_receipt(payload: dict[str, Any], schema_path: Path, validation_errors: list[str], handler_result: dict[str, Any]) -> dict[str, Any]:
    accepted = not validation_errors
    status = "accepted"
    if validation_errors:
        status = "rejected"
    elif handler_result.get("status") == "failed":
        status = "handler_failed"
    return {
        "receipt_version": RECEIPT_VERSION,
        "receipt_id": make_identifier("receipt"),
        "recorded_at": utc_now(),
        "atlas_root": ".",
        "event": payload,
        "schema": {
            "event_type": payload["event_type"],
            "schema_path": normalize_path(schema_path),
        },
        "processing": {
            "accepted": accepted,
            "status": status,
            "errors": validation_errors,
            "handler": handler_result,
        },
    }


def build_rejected_input_receipt(
    submission: dict[str, Any],
    validation_errors: list[str],
    handler_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "receipt_version": RECEIPT_VERSION,
        "receipt_id": make_identifier("receipt"),
        "recorded_at": utc_now(),
        "atlas_root": ".",
        "submission": submission,
        "processing": {
            "accepted": False,
            "status": "rejected",
            "errors": validation_errors,
            "handler": handler_result,
        },
        "classification": {
            "lane": f"runtime/receipts/events/{REJECTED_LANE}/invalid_input",
            "reason": "input_rejected_before_supported_event_validation",
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and record an ATLAS lifecycle event.")
    parser.add_argument("--event-type", choices=EVENT_TYPES)
    parser.add_argument("--payload-file")
    parser.add_argument("--payload-json")
    parser.add_argument("--stdin", action="store_true", help="Read JSON payload from stdin.")
    parser.add_argument("--receipt-dir")
    parser.add_argument("--skip-handler", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    receipt_root = Path(args.receipt_dir).resolve() if args.receipt_dir else default_receipt_root()
    submission: dict[str, Any] | None = None

    try:
        payload = load_json_input(args)
        submission = json.loads(json.dumps(payload))
        event_type = payload.get("event_type")
        if event_type not in EVENT_TYPES:
            raise ValueError(f"Unsupported event_type: {event_type!r}.")
        schema_path = schema_root() / f"{event_type}.schema.json"
        schema = load_schema(event_type)
        validation_errors = validate_instance(payload, schema)
    except Exception as exc:
        if submission is None:
            payload_source = "stdin" if args.stdin else "payload_json" if args.payload_json else "payload_file"
            submission = {
                "submitted_event_type": args.event_type,
                "payload_source": payload_source,
                "payload_file": normalize_path(Path(args.payload_file).resolve()) if args.payload_file else "",
                "summary": "Input rejected before a supported event payload could be loaded.",
            }
        receipt_id = submission.get("event_id") if isinstance(submission.get("event_id"), str) else make_identifier("invalid")
        validation_errors = [str(exc)]
        handler_result = {
            "status": "skipped",
            "reason": "validation_failed_before_handler",
        }
        receipt = build_rejected_input_receipt(submission, validation_errors, handler_result)
        paths = write_receipt(rejected_receipt_root(receipt_root), ["invalid_input"], receipt_id, receipt)
        print(f"Event input rejected: {paths['receipt_path']}")
        return 1

    handler_result = {
        "status": "skipped",
        "reason": "no_handler_configured",
    }
    if not validation_errors and not args.skip_handler:
        handler_path = discover_handler(event_type)
        if handler_path is not None:
            handler_result = run_handler(handler_path, payload)

    receipt = build_receipt(payload, schema_path, validation_errors, handler_result)
    paths = write_receipt(receipt_root, [event_type], payload["event_id"], receipt)
    if validation_errors:
        print(f"Event rejected: {paths['receipt_path']}")
        for item in validation_errors:
            print(f"- {item}")
        return 1
    if handler_result.get("status") == "failed":
        print(f"Event accepted with handler failure: {paths['receipt_path']}")
        return 2
    print(f"Event accepted: {paths['receipt_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
