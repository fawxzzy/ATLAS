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
from ops.atlas.draft_entry_scaffold import FIXED_STATUS, MISSING_FIELDS_NOTE

NOT_READY_ROUTE = "not-validator-ready"
READY_ROUTE = "validator-input-ready"
ADMITTED_ROUTES = (NOT_READY_ROUTE, READY_ROUTE)
SCAFFOLD_TOP_LEVEL_FIELDS = (
    "candidate_entry",
    "missing_required_fields",
    "validator_readiness_note",
)


class EntryStatusSummaryRendererError(RuntimeError):
    pass


@dataclass(frozen=True)
class EntryStatusSummaryRendererResult:
    entries: tuple[dict[str, Any], ...]
    entry_count: int
    status_counts: dict[str, int]
    readiness_counts: dict[str, int]

    def to_payload(self) -> dict[str, Any]:
        return {
            "entries": list(self.entries),
            "entry_count": self.entry_count,
            "status_counts": self.status_counts,
            "readiness_counts": self.readiness_counts,
        }


def _normalize_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def _load_json_payload(*, input_path: Path | None, inline_json: str | None) -> Any:
    if bool(input_path) == bool(inline_json):
        raise EntryStatusSummaryRendererError("Provide exactly one of --input or --json.")
    if input_path is not None:
        try:
            return json.loads(input_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise EntryStatusSummaryRendererError(f"Input file not found: {input_path}") from exc
        except json.JSONDecodeError as exc:
            raise EntryStatusSummaryRendererError(f"Malformed JSON input file: {exc}") from exc
    assert inline_json is not None
    try:
        return json.loads(inline_json)
    except json.JSONDecodeError as exc:
        raise EntryStatusSummaryRendererError(f"Malformed inline JSON payload: {exc}") from exc


def _validate_string_list(value: Any, *, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise EntryStatusSummaryRendererError(f"{field_name} must be a list of strings.")
    validated: list[str] = []
    for item in value:
        normalized = _normalize_text(item)
        if normalized is None:
            raise EntryStatusSummaryRendererError(f"{field_name} must contain only non-empty strings.")
        validated.append(normalized)
    return tuple(validated)


def _extract_entry(candidate_entry: Any) -> tuple[str, str]:
    if not isinstance(candidate_entry, dict):
        raise EntryStatusSummaryRendererError("candidate_entry must be a JSON object.")
    entry_id = _normalize_text(candidate_entry.get("entry_id"))
    if entry_id is None:
        raise EntryStatusSummaryRendererError("candidate_entry.entry_id must be a non-empty string.")
    status = _normalize_text(candidate_entry.get("status"))
    if status != FIXED_STATUS:
        raise EntryStatusSummaryRendererError("candidate_entry.status must be exactly proposed.")
    return entry_id, status


def _build_row_from_not_ready(item: dict[str, Any]) -> dict[str, Any]:
    if tuple(item.keys()) != ("route", "scaffold_payload") and set(item.keys()) != {"route", "scaffold_payload"}:
        unexpected = next(key for key in item.keys() if key not in {"route", "scaffold_payload"})
        raise EntryStatusSummaryRendererError(f"unsupported handoff field: {unexpected}")

    scaffold_payload = item.get("scaffold_payload")
    if not isinstance(scaffold_payload, dict):
        raise EntryStatusSummaryRendererError("scaffold_payload must be a JSON object.")

    extra_fields = [key for key in scaffold_payload if key not in SCAFFOLD_TOP_LEVEL_FIELDS]
    if extra_fields:
        raise EntryStatusSummaryRendererError(f"unsupported scaffold field: {extra_fields[0]}")
    missing_fields = [key for key in SCAFFOLD_TOP_LEVEL_FIELDS if key not in scaffold_payload]
    if missing_fields:
        raise EntryStatusSummaryRendererError(f"missing scaffold field: {missing_fields[0]}")

    entry_id, status = _extract_entry(scaffold_payload.get("candidate_entry"))
    unresolved = _validate_string_list(
        scaffold_payload.get("missing_required_fields"),
        field_name="missing_required_fields",
    )
    readiness_note = _normalize_text(scaffold_payload.get("validator_readiness_note"))
    if readiness_note != MISSING_FIELDS_NOTE:
        raise EntryStatusSummaryRendererError(
            "validator_readiness_note for not-validator-ready items must match the admitted not-ready note."
        )
    return {
        "entry_id": entry_id,
        "status": status,
        "readiness_route": NOT_READY_ROUTE,
        "missing_required_fields_count": len(unresolved),
    }


def _build_row_from_ready(item: dict[str, Any]) -> dict[str, Any]:
    if tuple(item.keys()) != ("route", "candidate_entry") and set(item.keys()) != {"route", "candidate_entry"}:
        unexpected = next(key for key in item.keys() if key not in {"route", "candidate_entry"})
        raise EntryStatusSummaryRendererError(f"unsupported handoff field: {unexpected}")

    entry_id, status = _extract_entry(item.get("candidate_entry"))
    return {
        "entry_id": entry_id,
        "status": status,
        "readiness_route": READY_ROUTE,
        "missing_required_fields_count": 0,
    }


def build_entry_status_summary(payload: Any) -> EntryStatusSummaryRendererResult:
    if isinstance(payload, dict):
        if payload:
            unsupported_field = next(iter(payload))
            raise EntryStatusSummaryRendererError(f"unsupported input field: {unsupported_field}")
        raise EntryStatusSummaryRendererError("entry status summary input must be a non-empty ordered JSON list.")
    if not isinstance(payload, list):
        raise EntryStatusSummaryRendererError("entry status summary input must be an ordered JSON list.")
    if not payload:
        raise EntryStatusSummaryRendererError("entry status summary input must contain at least one handoff item.")

    rows: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {}
    readiness_counts: dict[str, int] = {}

    for item in payload:
        if not isinstance(item, dict):
            raise EntryStatusSummaryRendererError("each handoff item must be a JSON object.")
        route = _normalize_text(item.get("route"))
        if route not in ADMITTED_ROUTES:
            raise EntryStatusSummaryRendererError(f"unsupported route: {item.get('route')}")
        row = _build_row_from_not_ready(item) if route == NOT_READY_ROUTE else _build_row_from_ready(item)
        rows.append(row)
        status = row["status"]
        readiness_route = row["readiness_route"]
        status_counts[status] = status_counts.get(status, 0) + 1
        readiness_counts[readiness_route] = readiness_counts.get(readiness_route, 0) + 1

    return EntryStatusSummaryRendererResult(
        entries=tuple(rows),
        entry_count=len(rows),
        status_counts=status_counts,
        readiness_counts=readiness_counts,
    )


def run_summary(
    *,
    input_path: Path | None = None,
    inline_json: str | None = None,
) -> EntryStatusSummaryRendererResult:
    payload = _load_json_payload(input_path=input_path, inline_json=inline_json)
    return build_entry_status_summary(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render one bounded entry-status summary for an explicit local handoff set."
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", type=Path)
    group.add_argument("--json")
    args = parser.parse_args(argv)

    try:
        result = run_summary(
            input_path=args.input.resolve() if isinstance(args.input, Path) else None,
            inline_json=args.json,
        )
    except EntryStatusSummaryRendererError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result.to_payload(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
