from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes
from ops.atlas.vercel_observability_project_inventory import GOVERNED_PROJECTS

SCHEMA_VERSION = "atlas.vercel_environment_name_inventory.v1"
WRAPPER_SCHEMA_VERSION = "atlas.vercel.observability.environment_name_wrapper.v1"
WRAPPER_SOURCE = "vercel.read_only.environment_name_inventory.v1"

STATUS_OK = "ok"
STATUS_ADVISORY_GAP = "advisory_gap"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"

CONTRACT_RECEIPT = "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-ENVIRONMENT-NAME-ONLY-INVENTORY-CONTRACT-FREEZE-2026-07-14.md"
RATCHET_RECEIPT = "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-IMPLEMENTED-INVENTORY-MARKER-RATCHET-2026-07-14.md"
STACK_REPO_INVENTORY = "docs/registry/STACK-REPO-INVENTORY.json"
NEXT_RECOMMENDED_PACKET = "Vercel Platform Observability Governance environment-name-only inventory implementation reconciliation"

ALLOWED_TARGETS = {"production", "preview", "development"}
ALLOWED_PRESENCE = {"configured", "missing"}
ALLOWED_TYPE_POSTURES = {"encrypted", "sensitive", "plain", "system", "unknown"}
WRAPPER_KEYS = {"schema_version", "source", "captured_at_utc", "project_id", "project_name", "variables"}
VARIABLE_KEYS = {"name", "targets", "presence", "type_posture"}
FORBIDDEN_KEY_FRAGMENTS = ("value", "token", "secret", "authorization", "cookie", "payload", "body")
ENV_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,255}$")


def _finding(code: str, message: str, **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("severity", "blocker"), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _normal(value: str | Path) -> str:
    return normalize_slashes(str(value)).strip("/")


def validate_runtime_json_path(*, root: Path, relative_path: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    candidate = Path(relative_path)
    normalized = _normal(candidate)
    if candidate.is_absolute():
        return None, _finding("absolute_path", "Path must be root-relative.", path=normalized)
    if ".." in candidate.parts:
        return None, _finding("parent_traversal_path", "Path must not use parent traversal.", path=normalized)
    if not normalized.startswith("tmp/") or not normalized.endswith(".json"):
        return None, _finding("protected_path", "Paths are admitted only under root-relative tmp/**.json.", path=normalized)
    resolved = (root / normalized).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_path", "Path must stay inside the ATLAS root.", path=normalized)
    return resolved, None


def _forbidden_keys(value: Any, *, path: str = "root") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in FORBIDDEN_KEY_FRAGMENTS):
                findings.append(f"{path}.{key}")
            findings.extend(_forbidden_keys(child, path=f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_forbidden_keys(child, path=f"{path}[{index}]"))
    return findings


def _load_wrapper(path: Path) -> tuple[dict[str, Any] | None, OrderedDict[str, Any] | None]:
    if not path.exists() or not path.is_file():
        return None, _finding("input_missing", "Environment-name wrapper is missing.", path=_normal(path))
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, _finding("input_malformed", "Environment-name wrapper is not valid UTF-8 JSON.", path=_normal(path))
    if not isinstance(payload, dict):
        return None, _finding("input_shape", "Environment-name wrapper must be a JSON object.", path=_normal(path))
    forbidden = _forbidden_keys(payload)
    if forbidden:
        return None, _finding("forbidden_value_field", "Wrapper includes a forbidden value- or secret-bearing field.", paths=forbidden)
    unknown = sorted(set(payload) - WRAPPER_KEYS)
    if unknown:
        return None, _finding("unknown_wrapper_field", "Wrapper includes fields outside the frozen name-only contract.", fields=unknown)
    return payload, None


def _project_meta(project_id: str) -> dict[str, str] | None:
    value = GOVERNED_PROJECTS.get(project_id)
    return dict(value) if value is not None else None


def _normalize_wrapper(payload: dict[str, Any]) -> tuple[OrderedDict[str, Any] | None, list[OrderedDict[str, Any]]]:
    blockers: list[OrderedDict[str, Any]] = []
    if payload.get("schema_version") != WRAPPER_SCHEMA_VERSION:
        blockers.append(_finding("unsupported_schema", "Wrapper schema is not admitted.", actual=payload.get("schema_version")))
    if payload.get("source") != WRAPPER_SOURCE:
        blockers.append(_finding("unsupported_source", "Wrapper source is not the frozen read-only name inventory source."))

    captured_at = payload.get("captured_at_utc")
    if not isinstance(captured_at, str):
        blockers.append(_finding("missing_capture_timestamp", "Wrapper requires an RFC 3339 UTC capture timestamp."))
    else:
        try:
            parsed_capture = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
            if not captured_at.endswith("Z") or parsed_capture.utcoffset() is None:
                raise ValueError("timestamp is not UTC")
        except ValueError:
            blockers.append(_finding("invalid_capture_timestamp", "Capture timestamp must be RFC 3339 UTC with a trailing Z."))

    project_id = payload.get("project_id")
    project_name = payload.get("project_name")
    meta = _project_meta(str(project_id)) if isinstance(project_id, str) else None
    if meta is None:
        blockers.append(_finding("unknown_project_id", "Wrapper project is not in the governed Vercel project registry.", project_id=project_id))
    elif project_name != meta["project_name"]:
        blockers.append(_finding("project_identity_mismatch", "Wrapper project name does not match the governed project id."))

    variables = payload.get("variables")
    if not isinstance(variables, list):
        blockers.append(_finding("variables_shape", "Wrapper variables must be a list."))
        variables = []

    normalized_variables: list[OrderedDict[str, Any]] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for index, record in enumerate(variables):
        if not isinstance(record, dict):
            blockers.append(_finding("variable_shape", "Variable record must be an object.", index=index))
            continue
        unknown = sorted(set(record) - VARIABLE_KEYS)
        if unknown:
            blockers.append(_finding("unknown_variable_field", "Variable record includes fields outside the name-only contract.", index=index, fields=unknown))
            continue
        name = record.get("name")
        targets = record.get("targets")
        presence = record.get("presence")
        posture = record.get("type_posture")
        if not isinstance(name, str) or not ENV_NAME_PATTERN.fullmatch(name):
            blockers.append(_finding("invalid_environment_name", "Environment name must be an identifier, never an assignment or value.", index=index))
            continue
        if not isinstance(targets, list) or not targets or not all(isinstance(item, str) and item in ALLOWED_TARGETS for item in targets):
            blockers.append(_finding("invalid_targets", "Targets must be a non-empty subset of production, preview, and development.", index=index))
            continue
        normalized_targets = tuple(sorted(set(targets)))
        if presence not in ALLOWED_PRESENCE:
            blockers.append(_finding("invalid_presence", "Presence must be configured or missing.", index=index))
            continue
        if posture not in ALLOWED_TYPE_POSTURES:
            blockers.append(_finding("invalid_type_posture", "Type posture is outside the frozen metadata-only enum.", index=index))
            continue
        identity = (name, normalized_targets)
        if identity in seen:
            blockers.append(_finding("duplicate_variable_record", "Duplicate environment name and target set detected.", index=index, name=name))
            continue
        seen.add(identity)
        normalized_variables.append(
            OrderedDict(
                [
                    ("name", name),
                    ("targets", list(normalized_targets)),
                    ("presence", presence),
                    ("type_posture", posture),
                ]
            )
        )

    if blockers or meta is None:
        return None, blockers
    return (
        OrderedDict(
            [
                ("project_id", project_id),
                ("project_name", project_name),
                ("repo_logical_id", meta["repo_logical_id"]),
                ("captured_at_utc", captured_at),
                ("variable_count", len(normalized_variables)),
                ("variables", sorted(normalized_variables, key=lambda item: (str(item["name"]), tuple(item["targets"])))),
            ]
        ),
        [],
    )


def build_report(*, root: Path, inputs: list[str]) -> OrderedDict[str, Any]:
    blockers: list[OrderedDict[str, Any]] = []
    projects: list[OrderedDict[str, Any]] = []
    seen_projects: set[str] = set()
    for relative_path in inputs:
        resolved, path_error = validate_runtime_json_path(root=root, relative_path=relative_path)
        if path_error is not None:
            blockers.append(path_error)
            continue
        assert resolved is not None
        payload, load_error = _load_wrapper(resolved)
        if load_error is not None:
            blockers.append(load_error)
            continue
        assert payload is not None
        project, project_blockers = _normalize_wrapper(payload)
        blockers.extend(project_blockers)
        if project is None:
            continue
        project_id = str(project["project_id"])
        if project_id in seen_projects:
            blockers.append(_finding("duplicate_project_capture", "Only one environment-name wrapper per governed project is admitted.", project_id=project_id))
            continue
        seen_projects.add(project_id)
        projects.append(project)

    missing = [
        OrderedDict([("project_id", project_id), ("project_name", meta["project_name"]), ("repo_logical_id", meta["repo_logical_id"])])
        for project_id, meta in GOVERNED_PROJECTS.items()
        if project_id not in seen_projects
    ]
    warnings = []
    if missing and not blockers:
        warnings.append(
            OrderedDict(
                [
                    ("code", "partial_capture_coverage"),
                    ("severity", "warning"),
                    ("message", "One or more governed Vercel projects lack environment-name-only evidence."),
                    ("details", {"missing_project_ids": [item["project_id"] for item in missing]}),
                ]
            )
        )
    status = STATUS_BLOCKER if blockers else (STATUS_ADVISORY_GAP if warnings else STATUS_OK)
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("safe_to_use", not blockers),
            ("basis_receipts", [CONTRACT_RECEIPT, RATCHET_RECEIPT, STACK_REPO_INVENTORY]),
            ("input_count", len(inputs)),
            ("captured_project_count", len(projects)),
            ("project_count", len(GOVERNED_PROJECTS)),
            ("environment_value_accessed", False),
            ("projects", sorted(projects, key=lambda item: str(item["project_name"]))),
            ("missing_projects", missing),
            ("warnings", warnings),
            ("blockers", blockers),
            ("next_recommended_packet", NEXT_RECOMMENDED_PACKET),
        ]
    )


def report_exit_code(*, status: str, strict: bool) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_ADVISORY_GAP:
        return 1 if strict else 0
    return 2 if status == STATUS_BLOCKER else 3


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and normalize read-only Vercel environment-name-only wrappers.")
    parser.add_argument("--input", action="append", default=[], help="Root-relative tmp/**.json environment-name wrapper.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    parser.add_argument("--output", help="Optional root-relative tmp/**.json report path.")
    parser.add_argument("--strict", action="store_true", help="Return nonzero for advisory gaps and blockers.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root, inputs=list(args.input))
        if args.output:
            output, output_error = validate_runtime_json_path(root=root, relative_path=args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKER
                report["safe_to_use"] = False
                report["blockers"] = list(report["blockers"]) + [output_error]
            elif output is not None:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
        return report_exit_code(status=str(report["status"]), strict=bool(args.strict))
    except Exception as exc:
        report = OrderedDict(
            [
                ("schema_version", SCHEMA_VERSION),
                ("status", STATUS_INTERNAL_ERROR),
                ("safe_to_use", False),
                ("environment_value_accessed", False),
                ("blockers", [_finding("internal_error", "Environment-name inventory failed.", exception=str(exc))]),
            ]
        )
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
