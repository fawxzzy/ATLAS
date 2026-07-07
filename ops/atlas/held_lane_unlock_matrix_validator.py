from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops._atlas import normalize_slashes
from ops.atlas import held_lane_unlock_matrix as matrix
from ops.atlas import marker_aware_next_packet_planner as planner

SCHEMA_VERSION = "atlas.held_lane_unlock_matrix_validator.v1"
STATUS_VALID = "valid"
STATUS_BLOCKED = "blocked"
STATUS_INTERNAL_ERROR = "internal_error"

EXPECTED_MATRIX_SCHEMA = matrix.SCHEMA_VERSION
ACCEPTED_MATRIX_STATUSES = {matrix.STATUS_OK, matrix.STATUS_ADVISORY_MATRIX}
REQUIRED_TOP_LEVEL_FIELDS = [
    "schema_version",
    "status",
    "candidate_count",
    "held_count",
    "unlockable_count",
    "blocker_classes",
    "candidates",
    "required_proofs",
    "required_receipts",
    "operator_actions",
    "owner_lane_boundaries",
    "playbook_rule_refs",
    "authority_risks",
    "recommended_next_selection",
    "safe_to_continue",
    "blockers",
    "branch",
    "head",
]
REQUIRED_CANDIDATE_FIELDS = [
    "marker",
    "percent",
    "source_ref",
    "planner_classification",
    "packet",
    "safe_to_select",
    "unlockable",
    "blocker_classes",
    "required_proofs",
    "required_receipts",
    "operator_actions",
]
REQUIRED_OWNER_BOUNDARIES = [
    "Fitness app work is an owner lane and is not mutated by this helper.",
    "Mazer game work is an owner lane and is not mutated by this helper.",
]


def _finding(code: str, message: str, *, severity: str = "blocker", **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("severity", severity), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _normalized_relative(value: str) -> str:
    return normalize_slashes(value).strip("/")


def validate_input_path(*, root: Path, input_path: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    candidate = Path(input_path)
    if candidate.is_absolute():
        return None, _finding("absolute_input_path", "Input path must be root-relative.", path=normalize_slashes(str(candidate)))
    relative_path = _normalized_relative(str(candidate))
    if ".." in Path(relative_path).parts:
        return None, _finding("parent_traversal_input_path", "Input path must not use parent traversal.", path=relative_path)
    if not relative_path.startswith("tmp/") or not relative_path.endswith(".json"):
        return None, _finding("protected_input_path", "Input reads are admitted only from root-relative tmp/**.json.", path=relative_path)
    resolved = (root / relative_path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_input_path", "Input path must stay inside the ATLAS root.", path=relative_path)
    if not resolved.exists():
        return None, _finding("missing_input_path", "Input file does not exist.", path=relative_path)
    return resolved, None


def _load_input_report(*, root: Path, input_path: str) -> tuple[dict[str, Any] | None, list[OrderedDict[str, Any]], str | None]:
    resolved, error = validate_input_path(root=root, input_path=input_path)
    if error is not None:
        return None, [error], None
    assert resolved is not None
    try:
        loaded = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [_finding("invalid_json_input", "Input file is not valid JSON.", path=_normalized_relative(input_path), error=str(exc))], _normalized_relative(input_path)
    if not isinstance(loaded, dict):
        return None, [_finding("invalid_json_shape", "Input JSON must be an object.", path=_normalized_relative(input_path))], _normalized_relative(input_path)
    return loaded, [], _normalized_relative(input_path)


def _field_results(report: dict[str, Any]) -> list[OrderedDict[str, Any]]:
    results: list[OrderedDict[str, Any]] = []
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        present = field in report
        value = report.get(field)
        valid = present
        if field in {"candidate_count", "held_count", "unlockable_count"}:
            valid = present and isinstance(value, int) and value >= 0
        elif field in {"candidates", "blocker_classes", "required_proofs", "required_receipts", "operator_actions", "owner_lane_boundaries", "playbook_rule_refs", "authority_risks", "blockers"}:
            valid = present and isinstance(value, list)
        elif field == "safe_to_continue":
            valid = present and isinstance(value, bool)
        elif field in {"schema_version", "status"}:
            valid = present and isinstance(value, str) and bool(value)
        results.append(OrderedDict([("field", field), ("present", present), ("valid", valid)]))
    return results


def _candidate_results(candidates: Any) -> list[OrderedDict[str, Any]]:
    if not isinstance(candidates, list):
        return [OrderedDict([("index", None), ("valid", False), ("reason", "not_a_list")])]
    results: list[OrderedDict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        missing: list[str] = []
        invalid: list[str] = []
        if not isinstance(candidate, dict):
            results.append(OrderedDict([("index", index), ("valid", False), ("missing_fields", REQUIRED_CANDIDATE_FIELDS), ("invalid_fields", ["candidate"])]))
            continue
        for field in REQUIRED_CANDIDATE_FIELDS:
            if field not in candidate:
                missing.append(field)
                continue
            value = candidate[field]
            if field == "percent" and not isinstance(value, int):
                invalid.append(field)
            elif field in {"safe_to_select", "unlockable"} and not isinstance(value, bool):
                invalid.append(field)
            elif field in {"blocker_classes", "required_proofs", "required_receipts", "operator_actions"} and not isinstance(value, list):
                invalid.append(field)
            elif field in {"marker", "source_ref", "planner_classification", "packet"} and not isinstance(value, str):
                invalid.append(field)
        results.append(OrderedDict([("index", index), ("marker", candidate.get("marker")), ("valid", not missing and not invalid), ("missing_fields", missing), ("invalid_fields", invalid)]))
    return results


def _count_results(report: dict[str, Any]) -> list[OrderedDict[str, Any]]:
    candidates = report.get("candidates") if isinstance(report.get("candidates"), list) else []
    held_count = sum(1 for candidate in candidates if isinstance(candidate, dict) and "held_by_manifest" in candidate.get("blocker_classes", []))
    unlockable_count = sum(1 for candidate in candidates if isinstance(candidate, dict) and candidate.get("unlockable") is True)
    return [
        OrderedDict([("field", "candidate_count"), ("expected", len(candidates)), ("actual", report.get("candidate_count")), ("valid", report.get("candidate_count") == len(candidates))]),
        OrderedDict([("field", "held_count"), ("expected", held_count), ("actual", report.get("held_count")), ("valid", report.get("held_count") == held_count)]),
        OrderedDict([("field", "unlockable_count"), ("expected", unlockable_count), ("actual", report.get("unlockable_count")), ("valid", report.get("unlockable_count") == unlockable_count)]),
    ]


def _selection_result(report: dict[str, Any]) -> OrderedDict[str, Any]:
    unlockable_count = report.get("unlockable_count")
    selected = report.get("recommended_next_selection")
    valid = (unlockable_count == 0 and selected is None) or (isinstance(unlockable_count, int) and unlockable_count > 0 and isinstance(selected, str) and bool(selected))
    return OrderedDict([("unlockable_count", unlockable_count), ("recommended_next_selection", selected), ("valid", valid)])


def _boundary_results(report: dict[str, Any]) -> list[OrderedDict[str, Any]]:
    boundaries = report.get("owner_lane_boundaries") if isinstance(report.get("owner_lane_boundaries"), list) else []
    return [
        OrderedDict(
            [
                ("boundary", boundary),
                ("present", boundary in boundaries),
                ("valid", boundary in boundaries),
            ]
        )
        for boundary in REQUIRED_OWNER_BOUNDARIES
    ]


def validate_report(*, root: Path, report: dict[str, Any], input_ref: str | None = None) -> OrderedDict[str, Any]:
    blockers: list[OrderedDict[str, Any]] = []
    warnings: list[OrderedDict[str, Any]] = []

    if report.get("schema_version") != EXPECTED_MATRIX_SCHEMA:
        blockers.append(_finding("unexpected_matrix_schema", "Payload must come from the held-lane unlock matrix helper.", expected=EXPECTED_MATRIX_SCHEMA, actual=report.get("schema_version")))
    if report.get("status") not in ACCEPTED_MATRIX_STATUSES:
        blockers.append(_finding("matrix_status_not_accepted", "Matrix status must be ok or advisory_matrix.", actual=report.get("status")))
    if report.get("safe_to_continue") is not True:
        blockers.append(_finding("matrix_not_safe_to_continue", "Matrix must be safe_to_continue=true before reuse.", actual=report.get("safe_to_continue")))
    if report.get("blockers"):
        blockers.append(_finding("matrix_has_blockers", "Matrix payload contains blockers.", blocker_count=len(report.get("blockers") or [])))

    field_results = _field_results(report)
    candidate_results = _candidate_results(report.get("candidates"))
    count_results = _count_results(report)
    selection_result = _selection_result(report)
    boundary_results = _boundary_results(report)

    for result in field_results:
        if not result["valid"]:
            blockers.append(_finding("invalid_matrix_field", "Required matrix field is missing or invalid.", field=result["field"]))
    for result in candidate_results:
        if not result["valid"]:
            blockers.append(_finding("invalid_candidate_shape", "Matrix candidate is missing required fields or has invalid field types.", index=result["index"], marker=result.get("marker")))
    for result in count_results:
        if not result["valid"]:
            blockers.append(_finding("invalid_matrix_count", "Matrix count does not match candidate payload.", field=result["field"], expected=result["expected"], actual=result["actual"]))
    if not selection_result["valid"]:
        blockers.append(_finding("invalid_selection_state", "Recommended selection must match unlockable candidate count.", unlockable_count=selection_result["unlockable_count"]))
    for result in boundary_results:
        if not result["valid"]:
            blockers.append(_finding("missing_owner_lane_boundary", "Required owner-lane boundary is missing.", boundary=result["boundary"]))

    status = STATUS_BLOCKED if blockers else STATUS_VALID
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("matrix_schema", report.get("schema_version")),
            ("matrix_status", report.get("status")),
            ("candidate_count", report.get("candidate_count")),
            ("held_count", report.get("held_count")),
            ("unlockable_count", report.get("unlockable_count")),
            ("recommended_next_selection", report.get("recommended_next_selection")),
            ("field_results", field_results),
            ("candidate_results", candidate_results),
            ("count_results", count_results),
            ("selection_result", selection_result),
            ("owner_lane_boundary_results", boundary_results),
            ("safe_to_use", status == STATUS_VALID),
            ("root", normalize_slashes(str(root))),
            ("branch", report.get("branch")),
            ("head", report.get("head")),
            ("input_ref", input_ref),
            ("blockers", blockers),
            ("warnings", warnings),
        ]
    )


def build_report(*, root: Path, source_refs: list[str] | None = None, input_path: str | None = None) -> OrderedDict[str, Any]:
    if input_path:
        payload, blockers, input_ref = _load_input_report(root=root, input_path=input_path)
        if blockers:
            return OrderedDict(
                [
                    ("schema_version", SCHEMA_VERSION),
                    ("status", STATUS_BLOCKED),
                    ("matrix_schema", None),
                    ("matrix_status", None),
                    ("candidate_count", None),
                    ("held_count", None),
                    ("unlockable_count", None),
                    ("recommended_next_selection", None),
                    ("field_results", []),
                    ("candidate_results", []),
                    ("count_results", []),
                    ("selection_result", OrderedDict([("valid", False)])),
                    ("owner_lane_boundary_results", []),
                    ("safe_to_use", False),
                    ("root", normalize_slashes(str(root))),
                    ("branch", None),
                    ("head", None),
                    ("input_ref", input_ref),
                    ("blockers", blockers),
                    ("warnings", []),
                ]
            )
        assert payload is not None
        return validate_report(root=root, report=payload, input_ref=input_ref)
    live_matrix = matrix.build_report(root=root, source_refs=list(source_refs or []))
    return validate_report(root=root, report=live_matrix, input_ref=None)


def report_exit_code(*, status: str, strict: bool) -> int:
    if status == STATUS_VALID:
        return 0
    if status == STATUS_BLOCKED:
        return 1 if strict else 2
    return 3


def render_summary(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Status: {report.get('status')}",
            f"Matrix status: {report.get('matrix_status') or 'none'}",
            f"Candidates: {report.get('candidate_count')}",
            f"Held: {report.get('held_count')}",
            f"Unlockable: {report.get('unlockable_count')}",
            f"Safe to use: {str(report.get('safe_to_use')).lower()}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate advisory held-lane unlock matrix payloads.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--source", action="append", default=[], help="Optional root-relative admitted source ref for the underlying matrix. May be repeated.")
    parser.add_argument("--input", help="Optional root-relative tmp/**.json matrix report to validate.")
    parser.add_argument("--output", help="Optional root-relative tmp/**.json validation report output path.")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root, source_refs=list(args.source or []), input_path=args.input)
        if args.output:
            resolved_output, output_error = planner.validate_output_path(root=root, output_path=args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKED
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
                report["safe_to_use"] = False
            elif resolved_output is not None:
                resolved_output.parent.mkdir(parents=True, exist_ok=True)
                resolved_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        sys.stdout.write(render_stdout(report, json_only=args.json))
        return report_exit_code(status=str(report.get("status") or STATUS_INTERNAL_ERROR), strict=args.strict)
    except Exception as exc:
        report = OrderedDict(
            [
                ("schema_version", SCHEMA_VERSION),
                ("status", STATUS_INTERNAL_ERROR),
                ("matrix_schema", None),
                ("matrix_status", None),
                ("candidate_count", None),
                ("held_count", None),
                ("unlockable_count", None),
                ("recommended_next_selection", None),
                ("field_results", []),
                ("candidate_results", []),
                ("count_results", []),
                ("selection_result", OrderedDict([("valid", False)])),
                ("owner_lane_boundary_results", []),
                ("safe_to_use", False),
                ("root", normalize_slashes(str(root))),
                ("branch", None),
                ("head", None),
                ("input_ref", getattr(args, "input", None)),
                ("blockers", [_finding("internal_error", "Held-lane unlock matrix validation failed.", exception=str(exc))]),
                ("warnings", []),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
