from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.draft_entry_scaffold import FIXED_STATUS, MISSING_FIELDS_NOTE, VALIDATOR_READY_NOTE

EXACT_TOP_LEVEL_FIELDS = (
    "candidate_entry",
    "missing_required_fields",
    "validator_readiness_note",
)


class ScaffoldToValidatorHandoffError(RuntimeError):
    pass


@dataclass(frozen=True)
class ScaffoldToValidatorHandoffResult:
    route: str
    scaffold_payload: dict[str, Any] | None = None
    candidate_entry: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"route": self.route}
        if self.scaffold_payload is not None:
            payload["scaffold_payload"] = self.scaffold_payload
        if self.candidate_entry is not None:
            payload["candidate_entry"] = self.candidate_entry
        return payload


def _normalize_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def _validate_string_list(value: Any, *, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ScaffoldToValidatorHandoffError(f"{field_name} must be a list of strings.")
    validated: list[str] = []
    for item in value:
        normalized = _normalize_text(item)
        if normalized is None:
            raise ScaffoldToValidatorHandoffError(f"{field_name} must contain only non-empty strings.")
        validated.append(normalized)
    return tuple(validated)


def _load_json_payload(*, input_path: Path | None, inline_json: str | None) -> Any:
    if bool(input_path) == bool(inline_json):
        raise ScaffoldToValidatorHandoffError("Provide exactly one of --input or --json.")
    if input_path is not None:
        try:
            return json.loads(input_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ScaffoldToValidatorHandoffError(f"Input file not found: {input_path}") from exc
        except json.JSONDecodeError as exc:
            raise ScaffoldToValidatorHandoffError(f"Malformed JSON input file: {exc}") from exc
    assert inline_json is not None
    try:
        return json.loads(inline_json)
    except json.JSONDecodeError as exc:
        raise ScaffoldToValidatorHandoffError(f"Malformed inline JSON payload: {exc}") from exc


def build_scaffold_to_validator_handoff(payload: Any) -> ScaffoldToValidatorHandoffResult:
    if isinstance(payload, list):
        raise ScaffoldToValidatorHandoffError("multi-entry payloads are unsupported")
    if not isinstance(payload, dict):
        raise ScaffoldToValidatorHandoffError("scaffold-to-validator handoff input must be a JSON object")

    extra_fields = [key for key in payload if key not in EXACT_TOP_LEVEL_FIELDS]
    if extra_fields:
        raise ScaffoldToValidatorHandoffError(f"unsupported input field: {extra_fields[0]}")

    missing_top_level_fields = [key for key in EXACT_TOP_LEVEL_FIELDS if key not in payload]
    if missing_top_level_fields:
        raise ScaffoldToValidatorHandoffError(f"missing scaffold field: {missing_top_level_fields[0]}")

    candidate_entry = payload.get("candidate_entry")
    if not isinstance(candidate_entry, dict):
        raise ScaffoldToValidatorHandoffError("candidate_entry must be a JSON object")

    status = _normalize_text(candidate_entry.get("status"))
    if status != FIXED_STATUS:
        raise ScaffoldToValidatorHandoffError("candidate_entry.status must be exactly proposed")

    missing_required_fields = _validate_string_list(
        payload.get("missing_required_fields"),
        field_name="missing_required_fields",
    )
    readiness_note = _normalize_text(payload.get("validator_readiness_note"))
    if readiness_note not in {MISSING_FIELDS_NOTE, VALIDATOR_READY_NOTE}:
        raise ScaffoldToValidatorHandoffError("validator_readiness_note must match one admitted scaffold readiness note")

    if missing_required_fields and readiness_note == VALIDATOR_READY_NOTE:
        raise ScaffoldToValidatorHandoffError("missing_required_fields contradict a ready-for-validator-input note")
    if not missing_required_fields and readiness_note == MISSING_FIELDS_NOTE:
        raise ScaffoldToValidatorHandoffError("empty missing_required_fields contradict a not-yet-validator-ready note")

    payload_copy = copy.deepcopy(payload)
    if missing_required_fields or readiness_note == MISSING_FIELDS_NOTE:
        return ScaffoldToValidatorHandoffResult(
            route="not-validator-ready",
            scaffold_payload=payload_copy,
        )

    return ScaffoldToValidatorHandoffResult(
        route="validator-input-ready",
        candidate_entry=copy.deepcopy(candidate_entry),
    )


def run_handoff(
    *,
    input_path: Path | None = None,
    inline_json: str | None = None,
) -> ScaffoldToValidatorHandoffResult:
    payload = _load_json_payload(input_path=input_path, inline_json=inline_json)
    return build_scaffold_to_validator_handoff(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Route one bounded scaffold payload into validator-ready or not-ready handoff output.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", type=Path)
    group.add_argument("--json")
    args = parser.parse_args(argv)

    try:
        result = run_handoff(
            input_path=args.input.resolve() if isinstance(args.input, Path) else None,
            inline_json=args.json,
        )
    except ScaffoldToValidatorHandoffError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result.to_payload(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
