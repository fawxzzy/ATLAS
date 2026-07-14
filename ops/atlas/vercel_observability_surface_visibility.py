from __future__ import annotations

import argparse
import json
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

SCHEMA_VERSION = "atlas.vercel_observability_surface_visibility.v1"
WRAPPER_SCHEMA_VERSION = "atlas.vercel.observability.surface_visibility_wrapper.v1"
WRAPPER_SOURCE = "vercel.read_only.observability.surface_visibility.v1"
STATUS_OK = "ok"
STATUS_ADVISORY_GAP = "advisory_gap"
STATUS_BLOCKER = "blocker"

SURFACES = ("web_analytics", "speed_insights", "traces", "alerts", "drains", "observability_plus")
VISIBILITY_STATES = {"visible", "unproven", "unavailable", "forbidden", "unknown"}
EVIDENCE_CLASSES = {"connector_readback", "cli_readback", "dashboard_readback", "documented_unproven", "access_denied", "not_queried"}
WRAPPER_KEYS = {"schema_version", "source", "captured_at_utc", "project_id", "project_name", "surfaces"}
SURFACE_KEYS = {"state", "evidence_class", "mutation_capable"}
FORBIDDEN_FRAGMENTS = ("enable", "create", "update", "delete", "destination", "retention", "value", "token", "secret", "entitlement")
NEXT_RECOMMENDED_PACKET = "Vercel Platform Observability Governance analytics and drain live read-only capability audit"


def _finding(code: str, message: str, **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("severity", "blocker"), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _normal(value: str | Path) -> str:
    return normalize_slashes(str(value)).strip("/")


def validate_path(root: Path, relative_path: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    candidate = Path(relative_path)
    normalized = _normal(candidate)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None, _finding("unsafe_path", "Path must be root-relative without parent traversal.", path=normalized)
    if not normalized.startswith("tmp/") or not normalized.endswith(".json"):
        return None, _finding("protected_path", "Paths are admitted only under root-relative tmp/**.json.", path=normalized)
    resolved = (root / normalized).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_path", "Path must stay inside the ATLAS root.", path=normalized)
    return resolved, None


def _forbidden_keys(value: Any, path: str = "root") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if any(fragment in str(key).lower() for fragment in FORBIDDEN_FRAGMENTS):
                hits.append(f"{path}.{key}")
            hits.extend(_forbidden_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(_forbidden_keys(child, f"{path}[{index}]"))
    return hits


def _normalize(payload: dict[str, Any]) -> tuple[OrderedDict[str, Any] | None, list[OrderedDict[str, Any]]]:
    blockers: list[OrderedDict[str, Any]] = []
    unknown = sorted(set(payload) - WRAPPER_KEYS)
    forbidden = _forbidden_keys(payload)
    if forbidden:
        blockers.append(_finding("forbidden_mutation_or_secret_field", "Wrapper contains a mutation-, entitlement-, or secret-bearing field.", paths=forbidden))
    if unknown:
        blockers.append(_finding("unknown_wrapper_field", "Wrapper contains fields outside the frozen visibility contract.", fields=unknown))
    if payload.get("schema_version") != WRAPPER_SCHEMA_VERSION:
        blockers.append(_finding("unsupported_schema", "Wrapper schema is not admitted."))
    if payload.get("source") != WRAPPER_SOURCE:
        blockers.append(_finding("unsupported_source", "Wrapper source is not admitted."))

    captured_at = payload.get("captured_at_utc")
    try:
        if not isinstance(captured_at, str) or not captured_at.endswith("Z"):
            raise ValueError
        datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    except ValueError:
        blockers.append(_finding("invalid_capture_timestamp", "Capture timestamp must be RFC 3339 UTC with a trailing Z."))

    project_id = payload.get("project_id")
    meta = GOVERNED_PROJECTS.get(str(project_id)) if isinstance(project_id, str) else None
    if meta is None:
        blockers.append(_finding("unknown_project_id", "Project is not in the governed Vercel registry.", project_id=project_id))
    elif payload.get("project_name") != meta["project_name"]:
        blockers.append(_finding("project_identity_mismatch", "Project name does not match the governed project id."))

    surfaces = payload.get("surfaces")
    if not isinstance(surfaces, dict):
        blockers.append(_finding("surface_shape", "Surfaces must be an object containing the complete frozen surface set."))
        surfaces = {}
    missing = sorted(set(SURFACES) - set(surfaces))
    extra = sorted(set(surfaces) - set(SURFACES))
    if missing or extra:
        blockers.append(_finding("surface_set_mismatch", "Wrapper must contain exactly the frozen observability surface set.", missing=missing, extra=extra))

    normalized_surfaces: OrderedDict[str, Any] = OrderedDict()
    for surface in SURFACES:
        record = surfaces.get(surface)
        if not isinstance(record, dict):
            continue
        record_unknown = sorted(set(record) - SURFACE_KEYS)
        if record_unknown:
            blockers.append(_finding("unknown_surface_field", "Surface record includes fields outside the frozen contract.", surface=surface, fields=record_unknown))
            continue
        state = record.get("state")
        evidence = record.get("evidence_class")
        mutation_capable = record.get("mutation_capable")
        if state not in VISIBILITY_STATES:
            blockers.append(_finding("invalid_visibility_state", "Surface visibility state is outside the frozen enum.", surface=surface))
            continue
        if evidence not in EVIDENCE_CLASSES:
            blockers.append(_finding("invalid_evidence_class", "Surface evidence class is outside the frozen enum.", surface=surface))
            continue
        if not isinstance(mutation_capable, bool):
            blockers.append(_finding("invalid_mutation_capability", "Mutation capability must be a boolean risk flag, not authority.", surface=surface))
            continue
        if state == "visible" and evidence in {"documented_unproven", "not_queried"}:
            blockers.append(_finding("unsupported_visibility_claim", "Visible requires direct readback evidence.", surface=surface))
            continue
        normalized_surfaces[surface] = OrderedDict([("state", state), ("evidence_class", evidence), ("mutation_capable", mutation_capable)])

    if blockers or meta is None:
        return None, blockers
    return (
        OrderedDict(
            [
                ("project_id", project_id),
                ("project_name", payload.get("project_name")),
                ("repo_logical_id", meta["repo_logical_id"]),
                ("captured_at_utc", captured_at),
                ("surfaces", normalized_surfaces),
            ]
        ),
        [],
    )


def build_report(*, root: Path, inputs: list[str]) -> OrderedDict[str, Any]:
    blockers: list[OrderedDict[str, Any]] = []
    projects: list[OrderedDict[str, Any]] = []
    seen: set[str] = set()
    for relative_path in inputs:
        path, path_error = validate_path(root, relative_path)
        if path_error:
            blockers.append(path_error)
            continue
        assert path is not None
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            blockers.append(_finding("input_malformed", "Visibility wrapper is not valid UTF-8 JSON."))
            continue
        if not isinstance(payload, dict):
            blockers.append(_finding("input_shape", "Visibility wrapper must be a JSON object."))
            continue
        project, project_blockers = _normalize(payload)
        blockers.extend(project_blockers)
        if project is None:
            continue
        project_id = str(project["project_id"])
        if project_id in seen:
            blockers.append(_finding("duplicate_project_capture", "Only one visibility wrapper per project is admitted.", project_id=project_id))
            continue
        seen.add(project_id)
        projects.append(project)

    missing_projects = [meta["project_name"] for project_id, meta in GOVERNED_PROJECTS.items() if project_id not in seen]
    warnings = [] if not missing_projects or blockers else [{"code": "partial_capture_coverage", "severity": "warning", "missing_projects": missing_projects}]
    status = STATUS_BLOCKER if blockers else (STATUS_ADVISORY_GAP if warnings else STATUS_OK)
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("safe_to_use", not blockers),
            ("captured_project_count", len(projects)),
            ("project_count", len(GOVERNED_PROJECTS)),
            ("mutation_performed", False),
            ("entitlement_claimed", False),
            ("projects", sorted(projects, key=lambda item: str(item["project_name"]))),
            ("warnings", warnings),
            ("blockers", blockers),
            ("next_recommended_packet", NEXT_RECOMMENDED_PACKET),
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize Vercel observability visibility evidence without mutation or entitlement claims.")
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = atlas_root().resolve()
    report = build_report(root=root, inputs=list(args.input))
    if args.output:
        output, error = validate_path(root, args.output)
        if error:
            report["status"] = STATUS_BLOCKER
            report["safe_to_use"] = False
            report["blockers"] = list(report["blockers"]) + [error]
        elif output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    if report["status"] == STATUS_OK:
        return 0
    if report["status"] == STATUS_ADVISORY_GAP:
        return 1 if args.strict else 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
