from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.ui_observe.drift import validate_drift_report_payload
from ops.atlas.ui_observe.fitness import load_json_object
from ops.atlas.ui_visual_proof.fitness import validate_visual_proof_report_payload
from ops.cortex._artifacts import stable_json_digest, write_json

UI_PROOF_SUMMARY_CONTRACT_VERSION = "atlas.ui.proof-summary.v1"
UI_PROOF_SUMMARY_SCHEMA_ID = "atlas://schemas/atlas.ui.proof-summary.v1.json"
UI_PROOF_SUMMARY_RUNNER_VERSION = "atlas.ui.proof-summary.fitness.v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stamp_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def default_schema_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "schemas" / "atlas.ui.proof-summary.v1.json"


def default_drift_report_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "atlas" / "ui-observe" / "drift" / "fitness" / "latest.json"


def default_visual_report_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "atlas" / "ui-visual-proof" / "fitness" / "latest.json"


def default_report_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "atlas" / "ui-proof" / "fitness"


def validate_schema_definition(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("Schema $schema must target draft 2020-12.")
    if schema.get("$id") != UI_PROOF_SUMMARY_SCHEMA_ID:
        errors.append(f"Schema $id must be '{UI_PROOF_SUMMARY_SCHEMA_ID}'.")
    if schema.get("title") != "ATLAS UI proof summary v1":
        errors.append("Schema title must be 'ATLAS UI proof summary v1'.")
    return errors


def validate_ui_proof_summary_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("contract_version") != UI_PROOF_SUMMARY_CONTRACT_VERSION:
        errors.append(f"contract_version must be '{UI_PROOF_SUMMARY_CONTRACT_VERSION}'.")
    report_id = payload.get("report_id")
    if not isinstance(report_id, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", report_id):
        errors.append("report_id must be a sha256 digest string.")
    if not isinstance(payload.get("generated_at"), str) or not str(payload.get("generated_at")).strip():
        errors.append("generated_at must be a non-empty string.")
    if not isinstance(payload.get("owner_repo_id"), str) or not str(payload.get("owner_repo_id")).strip():
        errors.append("owner_repo_id must be a non-empty string.")
    if not isinstance(payload.get("completion_ready"), bool):
        errors.append("completion_ready must be a boolean.")
    if not isinstance(payload.get("failed_capture_ids"), list):
        errors.append("failed_capture_ids must be an array.")
    if not isinstance(payload.get("blocking_reasons"), list):
        errors.append("blocking_reasons must be an array.")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary must be an object.")
    else:
        if summary.get("status") not in {"completion_ready", "proof_blocked"}:
            errors.append("summary.status must be 'completion_ready' or 'proof_blocked'.")
        if summary.get("semantic_status") not in {"clean", "drift_detected", "missing_report", "invalid_report"}:
            errors.append("summary.semantic_status is invalid.")
        if summary.get("visual_status") not in {"clean", "proof_failed", "missing_report", "invalid_report"}:
            errors.append("summary.visual_status is invalid.")
        for field in ("gated_capture_count", "failed_capture_count"):
            value = summary.get(field)
            if not isinstance(value, int) or value < 0:
                errors.append(f"summary.{field} must be a non-negative integer.")

    for field in ("semantic_proof", "visual_proof"):
        value = payload.get(field)
        if not isinstance(value, dict):
            errors.append(f"{field} must be an object.")
            continue
        if not isinstance(value.get("status"), str) or not str(value.get("status")).strip():
            errors.append(f"{field}.status must be a non-empty string.")
        if not isinstance(value.get("report_ref"), str) or not str(value.get("report_ref")).strip():
            errors.append(f"{field}.report_ref must be a non-empty string.")
        if not isinstance(value.get("errors"), list):
            errors.append(f"{field}.errors must be an array.")
        if not isinstance(value.get("failed_capture_ids"), list):
            errors.append(f"{field}.failed_capture_ids must be an array.")

    if not isinstance(payload.get("operator_summary"), list):
        errors.append("operator_summary must be an array.")
    return errors


def _result_status(summary: Any, fallback: str) -> str:
    if isinstance(summary, dict):
        status = summary.get("status")
        if isinstance(status, str) and status.strip():
            return status
    return fallback


def _read_report(
    path: Path,
    *,
    root: Path,
    validator: Any,
    missing_status: str,
    invalid_status: str,
) -> dict[str, Any]:
    relative_ref = atlas_relative(path, root=root)
    if not path.exists():
        return {
            "status": missing_status,
            "report_ref": relative_ref,
            "report_id": None,
            "payload": None,
            "errors": [f"Report is missing: {relative_ref}"],
        }
    try:
        payload = load_json_object(path)
    except Exception as exc:
        return {
            "status": invalid_status,
            "report_ref": relative_ref,
            "report_id": None,
            "payload": None,
            "errors": [f"Failed to read report: {exc}"],
        }
    errors = validator(payload)
    if errors:
        return {
            "status": invalid_status,
            "report_ref": relative_ref,
            "report_id": payload.get("report_id") if isinstance(payload.get("report_id"), str) else None,
            "payload": payload,
            "errors": errors,
        }
    return {
        "status": _result_status(payload.get("summary"), invalid_status),
        "report_ref": relative_ref,
        "report_id": payload.get("report_id"),
        "payload": payload,
        "errors": [],
    }


def _semantic_failed_capture_ids(payload: dict[str, Any] | None) -> list[str]:
    if not isinstance(payload, dict):
        return []
    findings = payload.get("findings")
    if not isinstance(findings, list):
        return []
    capture_ids = {
        str(item.get("capture_id"))
        for item in findings
        if isinstance(item, dict) and isinstance(item.get("capture_id"), str) and str(item.get("capture_id")).strip()
    }
    return sorted(capture_ids)


def _visual_failed_capture_ids(payload: dict[str, Any] | None) -> list[str]:
    if not isinstance(payload, dict):
        return []
    results = payload.get("results")
    if not isinstance(results, list):
        return []
    capture_ids = {
        str(item.get("capture_id"))
        for item in results
        if isinstance(item, dict)
        and isinstance(item.get("capture_id"), str)
        and str(item.get("capture_id")).strip()
        and item.get("status") != "pass"
    }
    return sorted(capture_ids)


def _operator_summary(summary: dict[str, Any], blocking_reasons: list[str]) -> list[str]:
    if summary["status"] == "completion_ready":
        return [f"Semantic drift clean and visual proof clean across {summary['gated_capture_count']} gated captures."]
    return [
        (
            "Completion blocked: "
            f"semantic={summary['semantic_status']}, visual={summary['visual_status']}, "
            f"failed_captures={summary['failed_capture_count']}."
        ),
        *blocking_reasons[:4],
    ]


def _markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# ATLAS UI Proof Summary",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Owner repo: `{report['owner_repo_id']}`",
        f"- Completion ready: `{str(report['completion_ready']).lower()}`",
        f"- Summary status: `{report['summary']['status']}`",
        f"- Semantic status: `{report['summary']['semantic_status']}`",
        f"- Visual status: `{report['summary']['visual_status']}`",
        f"- Gated captures: {report['summary']['gated_capture_count']}",
        f"- Failed captures: {report['summary']['failed_capture_count']}",
        "",
        "## Operator Summary",
        "",
    ]
    for line in report["operator_summary"]:
        lines.append(f"- {line}")
    if report["blocking_reasons"]:
        lines.extend(["", "## Blocking Reasons", ""])
        for line in report["blocking_reasons"]:
            lines.append(f"- {line}")
    return "\n".join(lines) + "\n"


def derive_ui_proof_summary(
    *,
    root: Path | None = None,
    schema_path: Path | None = None,
    drift_report_path: Path | None = None,
    visual_report_path: Path | None = None,
    report_root: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    schema_target = (schema_path or default_schema_path(base_root)).resolve()
    drift_target = (drift_report_path or default_drift_report_path(base_root)).resolve()
    visual_target = (visual_report_path or default_visual_report_path(base_root)).resolve()
    report_target = (report_root or default_report_root(base_root)).resolve()

    schema = load_json_object(schema_target)
    schema_errors = validate_schema_definition(schema)
    if schema_errors:
        raise ValueError("; ".join(schema_errors))

    semantic_proof = _read_report(
        drift_target,
        root=base_root,
        validator=validate_drift_report_payload,
        missing_status="missing_report",
        invalid_status="invalid_report",
    )
    visual_proof = _read_report(
        visual_target,
        root=base_root,
        validator=validate_visual_proof_report_payload,
        missing_status="missing_report",
        invalid_status="invalid_report",
    )

    semantic_payload = semantic_proof["payload"] if isinstance(semantic_proof.get("payload"), dict) else None
    visual_payload = visual_proof["payload"] if isinstance(visual_proof.get("payload"), dict) else None
    semantic_failed_capture_ids = _semantic_failed_capture_ids(semantic_payload)
    visual_failed_capture_ids = _visual_failed_capture_ids(visual_payload)
    gated_capture_count = (
        int(visual_payload["summary"]["capture_count"])
        if isinstance(visual_payload, dict)
        and isinstance(visual_payload.get("summary"), dict)
        and isinstance(visual_payload["summary"].get("capture_count"), int)
        else 0
    )

    blocking_reasons: list[str] = []
    if semantic_proof["status"] != "clean":
        blocking_reasons.append(f"Semantic drift status is {semantic_proof['status']}.")
    if visual_proof["status"] != "clean":
        blocking_reasons.append(f"Visual proof status is {visual_proof['status']}.")
    if visual_proof["status"] == "clean" and gated_capture_count == 0:
        blocking_reasons.append("Visual proof report declares zero gated captures.")
    blocking_reasons.extend(str(item) for item in semantic_proof["errors"])
    blocking_reasons.extend(str(item) for item in visual_proof["errors"])

    failed_capture_ids = sorted(set(semantic_failed_capture_ids) | set(visual_failed_capture_ids))
    completion_ready = semantic_proof["status"] == "clean" and visual_proof["status"] == "clean" and gated_capture_count > 0
    summary = {
        "status": "completion_ready" if completion_ready else "proof_blocked",
        "semantic_status": str(semantic_proof["status"]),
        "visual_status": str(visual_proof["status"]),
        "gated_capture_count": gated_capture_count,
        "failed_capture_count": len(failed_capture_ids),
    }
    report_body = {
        "contract_version": UI_PROOF_SUMMARY_CONTRACT_VERSION,
        "generated_at": utc_now(),
        "runner_version": UI_PROOF_SUMMARY_RUNNER_VERSION,
        "owner_repo_id": "fitness",
        "completion_ready": completion_ready,
        "failed_capture_ids": failed_capture_ids,
        "blocking_reasons": blocking_reasons,
        "summary": summary,
        "semantic_proof": {
            "status": semantic_proof["status"],
            "report_ref": semantic_proof["report_ref"],
            "report_id": semantic_proof["report_id"],
            "finding_count": (
                int(semantic_payload["summary"]["finding_count"])
                if isinstance(semantic_payload, dict)
                and isinstance(semantic_payload.get("summary"), dict)
                and isinstance(semantic_payload["summary"].get("finding_count"), int)
                else 0
            ),
            "failed_capture_ids": semantic_failed_capture_ids,
            "errors": list(semantic_proof["errors"]),
        },
        "visual_proof": {
            "status": visual_proof["status"],
            "report_ref": visual_proof["report_ref"],
            "report_id": visual_proof["report_id"],
            "gated_capture_count": gated_capture_count,
            "failed_capture_ids": visual_failed_capture_ids,
            "errors": list(visual_proof["errors"]),
        },
        "operator_summary": _operator_summary(summary, blocking_reasons),
    }
    report = {**report_body, "report_id": stable_json_digest(report_body)}

    payload_errors = validate_ui_proof_summary_payload(report)
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
        latest_md.parent.mkdir(parents=True, exist_ok=True)
        latest_md.write_text(_markdown_report(report), encoding="utf-8")
        stamped_md.write_text(_markdown_report(report), encoding="utf-8")
        outputs = {
            "latest_json_ref": atlas_relative(latest_json, root=base_root),
            "latest_md_ref": atlas_relative(latest_md, root=base_root),
            "report_json_ref": atlas_relative(stamped_json, root=base_root),
            "report_md_ref": atlas_relative(stamped_md, root=base_root),
        }

    return {
        **report,
        "schema_ref": atlas_relative(schema_target, root=base_root),
        "outputs": outputs,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Derive a combined ATLAS UI proof summary from semantic and visual proof lanes.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--schema-file", type=Path)
    parser.add_argument("--drift-report", type=Path)
    parser.add_argument("--visual-report", type=Path)
    parser.add_argument("--report-root", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    result = derive_ui_proof_summary(
        root=args.root.resolve(),
        schema_path=args.schema_file.resolve() if isinstance(args.schema_file, Path) else None,
        drift_report_path=args.drift_report.resolve() if isinstance(args.drift_report, Path) else None,
        visual_report_path=args.visual_report.resolve() if isinstance(args.visual_report, Path) else None,
        report_root=args.report_root.resolve() if isinstance(args.report_root, Path) else None,
        dry_run=bool(args.dry_run),
    )
    print(json.dumps(result, indent=2))
    return 0 if result["completion_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
