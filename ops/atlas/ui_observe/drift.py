from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.ui_observe.fitness import (
    EXPECTED_TRAIT_KEYS,
    UI_OBSERVATION_CONTRACT_VERSION,
    default_output_root as default_observation_output_root,
    load_json_object,
    observe_fitness_ui,
    validate_observation_payload,
)
from ops.cortex._artifacts import stable_json_digest, write_json

UI_DRIFT_REPORT_CONTRACT_VERSION = "atlas.ui.drift.report.v1"
UI_DRIFT_REPORT_SCHEMA_ID = "atlas://schemas/atlas.ui.drift.report.v1.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stamp_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def default_drift_schema_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "schemas" / "atlas.ui.drift.report.v1.json"


def default_drift_output_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "atlas" / "ui-observe" / "drift" / "fitness"


def validate_drift_schema_definition(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("Schema $schema must target draft 2020-12.")
    if schema.get("$id") != UI_DRIFT_REPORT_SCHEMA_ID:
        errors.append(f"Schema $id must be '{UI_DRIFT_REPORT_SCHEMA_ID}'.")
    if schema.get("title") != "ATLAS UI drift report v1":
        errors.append("Schema title must be 'ATLAS UI drift report v1'.")
    return errors


def validate_drift_report_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("contract_version") != UI_DRIFT_REPORT_CONTRACT_VERSION:
        errors.append(f"contract_version must be '{UI_DRIFT_REPORT_CONTRACT_VERSION}'.")
    report_id = payload.get("report_id")
    if not isinstance(report_id, str) or not report_id.startswith("sha256:"):
        errors.append("report_id must be a sha256 digest string.")
    if not isinstance(payload.get("generated_at"), str) or not str(payload.get("generated_at")).strip():
        errors.append("generated_at must be a non-empty string.")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary must be an object.")
    findings = payload.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be an array.")
    operator_summary = payload.get("operator_summary")
    if not isinstance(operator_summary, list):
        errors.append("operator_summary must be an array.")
    return errors


def load_latest_observations(output_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not output_root.exists():
        return [], []
    observations: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    for path in sorted(output_root.rglob("latest.json")):
        payload = load_json_object(path)
        if payload.get("contract_version") != UI_OBSERVATION_CONTRACT_VERSION:
            invalid.append(
                {
                    "path": atlas_relative(path),
                    "errors": [f"contract_version must be '{UI_OBSERVATION_CONTRACT_VERSION}'."],
                    "payload": payload,
                }
            )
            continue
        errors = validate_observation_payload(payload)
        if errors:
            invalid.append(
                {
                    "path": atlas_relative(path),
                    "errors": errors,
                    "payload": payload,
                }
            )
            continue
        observations.append(payload)
    observations.sort(key=lambda item: str(item.get("comparison_key", "")))
    return observations, invalid


def _list_delta(expected: list[Any], observed: list[Any]) -> dict[str, list[Any]]:
    expected_unique = list(dict.fromkeys(expected))
    observed_unique = list(dict.fromkeys(observed))
    return {
        "missing": [item for item in expected_unique if item not in observed_unique],
        "unexpected": [item for item in observed_unique if item not in expected_unique],
    }


def _dict_delta(expected: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    changed_keys = sorted(key for key in sorted(set(expected) | set(observed)) if expected.get(key) != observed.get(key))
    return {
        "changed_keys": changed_keys,
        "expected_subset": {key: expected.get(key) for key in changed_keys},
        "observed_subset": {key: observed.get(key) for key in changed_keys},
    }


def _trait_delta(expected: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    delta: dict[str, Any] = {}
    if "token_refs" in expected or "token_refs" in observed:
        token_delta = _list_delta(
            list(expected.get("token_refs", [])) if isinstance(expected.get("token_refs"), list) else [],
            list(observed.get("token_refs", [])) if isinstance(observed.get("token_refs"), list) else [],
        )
        if token_delta["missing"] or token_delta["unexpected"]:
            delta["token_refs"] = token_delta
    if expected.get("primitive_id") != observed.get("primitive_id"):
        delta["primitive_id"] = {"expected": expected.get("primitive_id"), "observed": observed.get("primitive_id")}
    if expected.get("variant_id") != observed.get("variant_id"):
        delta["variant_id"] = {"expected": expected.get("variant_id"), "observed": observed.get("variant_id")}
    expected_snapshot = expected.get("trait_snapshot") if isinstance(expected.get("trait_snapshot"), dict) else {}
    observed_snapshot = observed.get("trait_snapshot") if isinstance(observed.get("trait_snapshot"), dict) else {}
    if expected_snapshot != observed_snapshot:
        delta["trait_snapshot"] = _dict_delta(expected_snapshot, observed_snapshot)
    expected_sources = expected.get("source_primitives")
    observed_sources = observed.get("source_primitives")
    if isinstance(expected_sources, list) or isinstance(observed_sources, list):
        normalized_expected_sources = [json.dumps(item, sort_keys=True) for item in expected_sources or []]
        normalized_observed_sources = [json.dumps(item, sort_keys=True) for item in observed_sources or []]
        source_delta = _list_delta(normalized_expected_sources, normalized_observed_sources)
        if source_delta["missing"] or source_delta["unexpected"]:
            delta["source_primitives"] = source_delta
    return delta


def _finding(
    *,
    kind: str,
    severity: str,
    comparison_key: str,
    capture_id: str,
    message: str,
    dimension: str | None = None,
    expected: Any = None,
    observed: Any = None,
    delta: Any = None,
) -> dict[str, Any]:
    payload = {
        "kind": kind,
        "severity": severity,
        "comparison_key": comparison_key,
        "capture_id": capture_id,
        "dimension": dimension,
        "message": message,
        "expected": expected,
        "observed": observed,
        "delta": delta,
    }
    return {
        "finding_id": stable_json_digest(payload),
        **payload,
    }


def _index_by_comparison_key(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("comparison_key")): item
        for item in items
        if isinstance(item.get("comparison_key"), str) and str(item.get("comparison_key")).strip()
    }


def _operator_summary(summary: dict[str, Any], findings: list[dict[str, Any]]) -> list[str]:
    if not findings:
        return [f"No UI drift detected across {summary['expected_capture_count']} captures."]
    lines = [
        (
            f"UI drift detected: findings={summary['finding_count']}, "
            f"mismatches={summary['mismatch_count']}, missing={summary['missing_count']}, "
            f"unexpected={summary['unexpected_count']}."
        )
    ]
    for finding in findings[:5]:
        dimension = f" ({finding['dimension']})" if isinstance(finding.get("dimension"), str) else ""
        lines.append(f"{finding['capture_id']}{dimension}: {finding['message']}")
    return lines


def _write_markdown_report(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# ATLAS UI Drift Validation",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Owner repo: `{report['owner_repo_id']}`",
        f"- Capture map: `{report['capture_map_ref']}`",
        f"- Status: `{report['summary']['status']}`",
        f"- Findings: {report['summary']['finding_count']}",
        "",
        "## Operator Summary",
        "",
    ]
    for line in report["operator_summary"]:
        lines.append(f"- {line}")
    if report["findings"]:
        lines.extend(["", "## Findings", ""])
        for finding in report["findings"]:
            dimension = f" `{finding['dimension']}`" if isinstance(finding.get("dimension"), str) else ""
            lines.append(f"- `{finding['capture_id']}`{dimension}: {finding['message']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_fitness_ui_drift(
    *,
    root: Path | None = None,
    observation_root: Path | None = None,
    report_root: Path | None = None,
    schema_path: Path | None = None,
    observation_schema_path: Path | None = None,
    capture_map_schema_path: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    schema_target = (schema_path or default_drift_schema_path(base_root)).resolve()
    observation_target = (observation_root or default_observation_output_root(base_root)).resolve()
    report_target = (report_root or default_drift_output_root(base_root)).resolve()

    schema = load_json_object(schema_target)
    schema_errors = validate_drift_schema_definition(schema)
    if schema_errors:
        raise ValueError("; ".join(schema_errors))

    expected_payload = observe_fitness_ui(
        root=base_root,
        schema_path=observation_schema_path,
        capture_map_schema_path=capture_map_schema_path,
        dry_run=True,
    )
    observed, invalid_observed = load_latest_observations(observation_target)
    expected = list(expected_payload["observations"])
    expected_index = _index_by_comparison_key(expected)
    observed_index = _index_by_comparison_key(observed)
    findings: list[dict[str, Any]] = []

    for item in invalid_observed:
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        capture = payload.get("capture") if isinstance(payload.get("capture"), dict) else {}
        findings.append(
            _finding(
                kind="invalid_observation",
                severity="warning",
                comparison_key=str(payload.get("comparison_key") or item["path"]),
                capture_id=str(capture.get("capture_id") or Path(str(item["path"])).parent.name),
                message="Runtime observation artifact is stale or malformed for the current contract.",
                observed={"path": item["path"]},
                delta={"errors": item["errors"]},
            )
        )

    for comparison_key in sorted(expected_index):
        expected_item = expected_index[comparison_key]
        observed_item = observed_index.get(comparison_key)
        capture_id = str(expected_item["capture"]["capture_id"])
        if observed_item is None:
            findings.append(
                _finding(
                    kind="missing_observation",
                    severity="warning",
                    comparison_key=comparison_key,
                    capture_id=capture_id,
                    message="Expected observation is missing from the runtime observation store.",
                    expected={"comparison_key": comparison_key},
                )
            )
            continue
        for dimension in EXPECTED_TRAIT_KEYS:
            expected_trait = expected_item["traits"][dimension]
            observed_trait = observed_item["traits"][dimension]
            if expected_trait == observed_trait:
                continue
            findings.append(
                _finding(
                    kind="trait_drift",
                    severity="warning",
                    comparison_key=comparison_key,
                    capture_id=capture_id,
                    dimension=dimension,
                    message=f"Observed {dimension} differs from the owner-backed expected contract.",
                    expected=expected_trait,
                    observed=observed_trait,
                    delta=_trait_delta(expected_trait, observed_trait),
                )
            )

    for comparison_key in sorted(set(observed_index) - set(expected_index)):
        observed_item = observed_index[comparison_key]
        findings.append(
            _finding(
                kind="unexpected_observation",
                severity="info",
                comparison_key=comparison_key,
                capture_id=str(observed_item["capture"]["capture_id"]),
                message="Observed runtime artifact does not belong to the active capture-set contract.",
                observed={"comparison_key": comparison_key},
            )
        )

    summary = {
        "status": "clean" if not findings else "drift_detected",
        "expected_capture_count": len(expected_index),
        "observed_capture_count": len(observed_index),
        "finding_count": len(findings),
        "mismatch_count": sum(1 for item in findings if item["kind"] == "trait_drift"),
        "missing_count": sum(1 for item in findings if item["kind"] == "missing_observation"),
        "unexpected_count": sum(1 for item in findings if item["kind"] == "unexpected_observation"),
    }
    report_body = {
        "contract_version": UI_DRIFT_REPORT_CONTRACT_VERSION,
        "generated_at": utc_now(),
        "owner_repo_id": str(expected_payload["observations"][0]["owner_repo_id"]) if expected_payload["observations"] else "fitness",
        "owner_contract_refs": expected_payload["observations"][0]["owner_contract_refs"] if expected_payload["observations"] else {},
        "capture_map_ref": str(expected_payload.get("capture_map_ref", "")),
        "summary": summary,
        "findings": findings,
        "operator_summary": _operator_summary(summary, findings),
    }
    report = {
        **report_body,
        "report_id": stable_json_digest(report_body),
    }
    payload_errors = validate_drift_report_payload(report)
    if payload_errors:
        raise ValueError("; ".join(payload_errors))

    outputs: dict[str, str] = {}
    if not dry_run:
        stamped_name = f"{stamp_now()}-{report['report_id'].replace('sha256:', '')[:16]}"
        latest_json = report_target / "latest.json"
        latest_md = report_target / "latest.md"
        stamped_json = report_target / f"{stamped_name}.json"
        stamped_md = report_target / f"{stamped_name}.md"
        write_json(latest_json, report)
        write_json(stamped_json, report)
        _write_markdown_report(report, latest_md)
        _write_markdown_report(report, stamped_md)
        outputs = {
            "latest_json_ref": atlas_relative(latest_json, root=base_root),
            "latest_md_ref": atlas_relative(latest_md, root=base_root),
            "report_json_ref": atlas_relative(stamped_json, root=base_root),
            "report_md_ref": atlas_relative(stamped_md, root=base_root),
        }

    return {
        **report,
        "schema_ref": atlas_relative(schema_target, root=base_root),
        "observation_root": atlas_relative(observation_target, root=base_root),
        "report_root": atlas_relative(report_target, root=base_root),
        "outputs": outputs,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate runtime Fitness UI observations against owner contracts.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--observation-root", type=Path)
    parser.add_argument("--report-root", type=Path)
    parser.add_argument("--schema-file", type=Path)
    parser.add_argument("--observation-schema-file", type=Path)
    parser.add_argument("--capture-map-schema-file", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    result = validate_fitness_ui_drift(
        root=args.root.resolve(),
        observation_root=args.observation_root.resolve() if isinstance(args.observation_root, Path) else None,
        report_root=args.report_root.resolve() if isinstance(args.report_root, Path) else None,
        schema_path=args.schema_file.resolve() if isinstance(args.schema_file, Path) else None,
        observation_schema_path=(
            args.observation_schema_file.resolve() if isinstance(args.observation_schema_file, Path) else None
        ),
        capture_map_schema_path=(
            args.capture_map_schema_file.resolve() if isinstance(args.capture_map_schema_file, Path) else None
        ),
        dry_run=bool(args.dry_run),
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
