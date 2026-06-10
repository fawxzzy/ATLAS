from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.batch_entry_validator import OPTIONAL_FIELDS, REQUIRED_FIELDS, UNSUPPORTED_TOP_LEVEL_KEYS

FIXED_STATUS = "proposed"
VALIDATOR_READY_NOTE = "scaffold contains all required fields and is ready for validator input but has not been validated"
MISSING_FIELDS_NOTE = "scaffold contains unresolved required fields and is not yet validator-ready"


class DraftEntryScaffoldError(RuntimeError):
    pass


@dataclass(frozen=True)
class DraftEntryScaffoldResult:
    candidate_entry: dict[str, Any]
    missing_required_fields: tuple[str, ...]
    validator_readiness_note: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "candidate_entry": self.candidate_entry,
            "missing_required_fields": list(self.missing_required_fields),
            "validator_readiness_note": self.validator_readiness_note,
        }


def _normalize_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def _normalize_string_list(value: Any, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        normalized = _normalize_text(value)
        return (normalized,) if normalized else ()
    if not isinstance(value, list):
        raise DraftEntryScaffoldError(f"{field_name} must be a string or list of strings.")
    ordered: list[str] = []
    for item in value:
        normalized = _normalize_text(item)
        if normalized is None:
            raise DraftEntryScaffoldError(f"{field_name} must contain only non-empty strings.")
        ordered.append(normalized)
    return tuple(ordered)


def _load_json_payload(*, input_path: Path | None, inline_json: str | None) -> Any:
    if bool(input_path) == bool(inline_json):
        raise DraftEntryScaffoldError("Provide exactly one of --input or --json.")
    if input_path is not None:
        try:
            return json.loads(input_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise DraftEntryScaffoldError(f"Input file not found: {input_path}") from exc
        except json.JSONDecodeError as exc:
            raise DraftEntryScaffoldError(f"Malformed JSON input file: {exc}") from exc
    assert inline_json is not None
    try:
        return json.loads(inline_json)
    except json.JSONDecodeError as exc:
        raise DraftEntryScaffoldError(f"Malformed inline JSON payload: {exc}") from exc


def _missing_marker(field_name: str) -> str:
    return f"MISSING_{field_name.upper()}"


def _normalize_status(value: Any) -> str | None:
    normalized = _normalize_text(value)
    if normalized is None:
        return None
    return normalized


def build_draft_entry_scaffold(payload: Any) -> DraftEntryScaffoldResult:
    if isinstance(payload, list):
        raise DraftEntryScaffoldError("multi-entry payloads are unsupported")
    if not isinstance(payload, dict):
        raise DraftEntryScaffoldError("draft-entry scaffold input must be a JSON object")

    for key in payload:
        if key in UNSUPPORTED_TOP_LEVEL_KEYS:
            raise DraftEntryScaffoldError(f"unsupported input field: {key}")
        if key in OPTIONAL_FIELDS:
            raise DraftEntryScaffoldError(f"{key} is not admitted for a proposed scaffold")
        if key not in REQUIRED_FIELDS:
            raise DraftEntryScaffoldError(f"unsupported input field: {key}")

    status = _normalize_status(payload.get("status"))
    if status is not None and status != FIXED_STATUS:
        raise DraftEntryScaffoldError("status must be omitted or explicitly set to proposed")

    candidate_entry: dict[str, Any] = {}
    missing_required_fields: list[str] = []

    for field_name in REQUIRED_FIELDS:
        if field_name == "status":
            candidate_entry[field_name] = FIXED_STATUS
            continue

        if field_name in {"allowed_write_scope", "protected_surface_exclusions"}:
            values = _normalize_string_list(payload.get(field_name), field_name=field_name)
            if values:
                candidate_entry[field_name] = list(values)
            else:
                candidate_entry[field_name] = _missing_marker(field_name)
                missing_required_fields.append(field_name)
            continue

        normalized = _normalize_text(payload.get(field_name))
        if normalized is None:
            candidate_entry[field_name] = _missing_marker(field_name)
            missing_required_fields.append(field_name)
        else:
            candidate_entry[field_name] = normalized

    readiness_note = VALIDATOR_READY_NOTE if not missing_required_fields else MISSING_FIELDS_NOTE
    return DraftEntryScaffoldResult(
        candidate_entry=candidate_entry,
        missing_required_fields=tuple(missing_required_fields),
        validator_readiness_note=readiness_note,
    )


def run_scaffold(
    *,
    input_path: Path | None = None,
    inline_json: str | None = None,
) -> DraftEntryScaffoldResult:
    payload = _load_json_payload(input_path=input_path, inline_json=inline_json)
    return build_draft_entry_scaffold(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render one bounded draft-entry scaffold for long-run batch orchestration.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", type=Path)
    group.add_argument("--json")
    args = parser.parse_args(argv)

    try:
        result = run_scaffold(
            input_path=args.input.resolve() if isinstance(args.input, Path) else None,
            inline_json=args.json,
        )
    except DraftEntryScaffoldError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result.to_payload(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
