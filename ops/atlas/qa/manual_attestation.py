from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.qa._common import (
    default_run_root,
    load_json_object,
    resolve_ref,
    utc_now,
    validate_manual_attestation,
)
from ops.cortex._artifacts import sha256_bytes, write_json


def _parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _validate_png(path: Path) -> str | None:
    try:
        with Image.open(path) as image:
            image.verify()
        return None
    except Exception as exc:
        return str(exc)


def _load_result_payload(*, run_root: Path) -> dict[str, Any]:
    result_path = run_root / "evaluated.result.json"
    if not result_path.exists():
        result_path = run_root / "matrix.result.json"
    return load_json_object(result_path)


def _manual_required_lanes_from_result(result_payload: dict[str, Any]) -> list[str]:
    unresolved = list(result_payload.get("summary", {}).get("manual_required_lanes", []))
    if unresolved:
        return [str(item) for item in unresolved if isinstance(item, str) and item.strip()]
    return [
        str(item.get("lens_id"))
        for item in result_payload.get("matrix", [])
        if isinstance(item, dict) and item.get("status") == "manual_required" and isinstance(item.get("lens_id"), str)
    ]


def _partition_manual_required_lanes(
    manual_required_lanes: list[str],
    attestation_status_by_lens: dict[str, str],
) -> tuple[list[str], list[str]]:
    validated_lanes: list[str] = []
    open_lanes: list[str] = []
    for lens_id in manual_required_lanes:
        if attestation_status_by_lens.get(lens_id) == "valid":
            validated_lanes.append(lens_id)
            continue
        open_lanes.append(lens_id)
    return validated_lanes, open_lanes


def validate_attestation_file(*, root: Path, attestation_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = load_json_object(attestation_path.resolve())
    findings: list[dict[str, Any]] = []
    for error in validate_manual_attestation(payload):
        findings.append({"severity": "error", "code": "invalid_attestation", "message": error})
    expires_at = payload.get("expires_at")
    if isinstance(expires_at, str):
        parsed = _parse_timestamp(expires_at)
        if parsed is None:
            findings.append({"severity": "error", "code": "invalid_attestation_expiry", "message": "expires_at must be a valid date-time."})
        elif parsed < datetime.now(timezone.utc):
            findings.append({"severity": "error", "code": "stale_attestation", "message": "Manual attestation has expired."})
    for index, item in enumerate(payload.get("screenshot_artifacts", [])):
        if not isinstance(item, dict):
            continue
        path_ref = item.get("path_ref")
        if not isinstance(path_ref, str) or not path_ref.strip():
            continue
        path = resolve_ref(path_ref, root=root)
        if not path.exists():
            findings.append({"severity": "error", "code": "missing_attestation_screenshot", "message": f"screenshot_artifacts[{index}] file does not exist."})
            continue
        decode_error = _validate_png(path)
        if decode_error:
            findings.append({"severity": "error", "code": "invalid_attestation_screenshot", "message": f"screenshot_artifacts[{index}] is not a decodable image: {decode_error}"})
        digest = sha256_bytes(path.read_bytes())
        if item.get("checksum_sha256") != digest:
            findings.append({"severity": "error", "code": "attestation_hash_mismatch", "message": f"screenshot_artifacts[{index}] checksum does not match the file bytes."})
    summary = {
        "attestation_id": payload.get("attestation_id"),
        "attestation_ref": atlas_relative(attestation_path.resolve(), root=root),
        "run_id": payload.get("run_id"),
        "scenario_id": payload.get("scenario_id"),
        "adapter_id": payload.get("adapter_id"),
        "lens_id": payload.get("lens_id"),
        "operator": payload.get("operator"),
        "capture_method": "manual_attestation",
        "status": "valid" if not any(item["severity"] == "error" for item in findings) else "invalid",
    }
    return summary, findings


def scaffold_manual_attestations(
    *,
    root: Path,
    run_id: str,
    operator: str = "REPLACE_ME_OPERATOR",
    operator_identity: str = "REPLACE_ME_IDENTITY",
    force: bool = False,
) -> dict[str, Any]:
    run_root = (default_run_root(root=root) / run_id).resolve()
    result_payload = _load_result_payload(run_root=run_root)
    unresolved = _manual_required_lanes_from_result(result_payload)
    matrix_by_lens = {
        str(item.get("lens_id")): item
        for item in result_payload.get("matrix", [])
        if isinstance(item, dict) and isinstance(item.get("lens_id"), str)
    }
    created: list[str] = []
    files: list[dict[str, Any]] = []
    attestation_dir = run_root / "manual-attestations"
    attestation_dir.mkdir(parents=True, exist_ok=True)
    expires_at = "2099-01-01T00:00:00Z"
    for lens_id in unresolved:
        if not isinstance(lens_id, str) or not lens_id.strip():
            continue
        matrix_entry = matrix_by_lens.get(lens_id, {})
        browser_engine = str(matrix_entry.get("browser_engine") or "")
        device_model = "REPLACE_ME_DEVICE_MODEL"
        os_name = "REPLACE_ME_OS"
        if "iphone" in lens_id:
            device_model = "iPhone"
            os_name = "iOS"
        elif "android" in lens_id:
            device_model = "Android Device"
            os_name = "Android"
        elif "desktop" in lens_id:
            device_model = "Desktop Browser"
            os_name = "Windows"
        screenshot_path = run_root / "captures" / lens_id / "manual.png"
        attestation_path = attestation_dir / f"{lens_id}.manual.json"
        payload = {
            "contract_version": "atlas.qa.manual_attestation.v1",
            "attestation_id": f"{run_id}:{lens_id}:manual",
            "operator": operator,
            "operator_identity": operator_identity,
            "attestation_signature": "REPLACE_ME_SIGNATURE",
            "scenario_id": str(result_payload["scenario_ref"]).rsplit("/", 1)[-1].replace(".json", "") if "scenario_ref" in result_payload else "REPLACE_ME_SCENARIO",
            "adapter_id": str(result_payload.get("adapter_id") or "REPLACE_ME_ADAPTER"),
            "run_id": run_id,
            "lens_id": lens_id,
            "device_model": device_model,
            "os_name": os_name,
            "os_version": "REPLACE_ME_OS_VERSION",
            "browser_name": browser_engine or "REPLACE_ME_BROWSER",
            "browser_version": "REPLACE_ME_BROWSER_VERSION",
            "capture_timestamp": utc_now(),
            "expires_at": expires_at,
            "screenshot_artifacts": [
                {
                    "path_ref": atlas_relative(screenshot_path, root=root),
                    "checksum_sha256": "sha256:" + ("0" * 64),
                }
            ],
            "supporting_artifacts": [],
            "notes": [
                "Replace placeholder metadata and checksum after capturing the manual screenshot.",
            ],
        }
        if attestation_path.exists() and not force:
            files.append({"lens_id": lens_id, "attestation_ref": atlas_relative(attestation_path, root=root), "status": "existing"})
            continue
        write_json(attestation_path, payload)
        created.append(lens_id)
        files.append(
            {
                "lens_id": lens_id,
                "attestation_ref": atlas_relative(attestation_path, root=root),
                "expected_screenshot_ref": atlas_relative(screenshot_path, root=root),
                "status": "created",
            }
        )
    report = {
        "runner_version": "atlas.qa.manual-attestation.scaffold.v1",
        "generated_at": utc_now(),
        "run_id": run_id,
        "created_count": len(created),
        "manual_required_lanes": unresolved,
        "files": files,
    }
    write_json(run_root / "manual-attestation.scaffold.json", report)
    return report


def validate_attestations_for_run(*, root: Path, run_id: str) -> dict[str, Any]:
    run_root = (default_run_root(root=root) / run_id).resolve()
    attestation_dir = run_root / "manual-attestations"
    files = sorted(attestation_dir.glob("*.json")) if attestation_dir.exists() else []
    results: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for path in files:
        summary, file_findings = validate_attestation_file(root=root, attestation_path=path)
        results.append(summary)
        findings.extend(file_findings)
    report = {
        "runner_version": "atlas.qa.manual-attestation.validate.v1",
        "generated_at": utc_now(),
        "run_id": run_id,
        "status": "clean" if not any(item["severity"] == "error" for item in findings) else "invalid",
        "attestation_count": len(results),
        "attestations": results,
        "finding_count": len(findings),
        "findings": findings,
    }
    write_json(run_root / "manual_attestation.result.json", report)
    return report


def build_manual_attestation_packet_prep(
    *,
    root: Path,
    run_id: str,
    output_path: Path | None = None,
) -> dict[str, Any]:
    run_root = (default_run_root(root=root) / run_id).resolve()
    result_payload = _load_result_payload(run_root=run_root)
    scenario_ref = str(result_payload.get("scenario_ref") or "")
    scenario_id = scenario_ref.rsplit("/", 1)[-1].replace(".json", "") if scenario_ref else "unknown"
    promotion_path = run_root / "promotion.record.json"
    promotion = load_json_object(promotion_path) if promotion_path.exists() else {}
    scaffold_path = run_root / "manual-attestation.scaffold.json"
    scaffold_report = load_json_object(scaffold_path) if scaffold_path.exists() else scaffold_manual_attestations(root=root, run_id=run_id)
    validation_path = run_root / "manual_attestation.result.json"
    validation_report = load_json_object(validation_path) if validation_path.exists() else validate_attestations_for_run(root=root, run_id=run_id)
    manual_required_lanes = [
        str(item)
        for item in promotion.get("manual_required_lanes", _manual_required_lanes_from_result(result_payload))
        if isinstance(item, str) and item.strip()
    ]
    attestation_status_by_lens = {
        str(item.get("lens_id")): str(item.get("status"))
        for item in validation_report.get("attestations", [])
        if isinstance(item, dict) and isinstance(item.get("lens_id"), str)
    }
    validated_manual_attestation_lanes, open_manual_required_lanes = _partition_manual_required_lanes(
        manual_required_lanes,
        attestation_status_by_lens,
    )
    file_entries: list[dict[str, Any]] = []
    for item in scaffold_report.get("files", []):
        if not isinstance(item, dict):
            continue
        lens_id = item.get("lens_id")
        if not isinstance(lens_id, str) or not lens_id.strip():
            continue
        attestation_ref = str(item.get("attestation_ref") or f"runtime/atlas/qa/runs/{run_id}/manual-attestations/{lens_id}.manual.json")
        expected_screenshot_ref = str(item.get("expected_screenshot_ref") or f"runtime/atlas/qa/runs/{run_id}/captures/{lens_id}/manual.png")
        screenshot_exists = resolve_ref(expected_screenshot_ref, root=root).exists()
        file_entries.append(
            {
                "lens_id": lens_id,
                "attestation_ref": attestation_ref,
                "expected_screenshot_ref": expected_screenshot_ref,
                "attestation_status": attestation_status_by_lens.get(lens_id, "unknown"),
                "screenshot_exists": screenshot_exists,
            }
        )
    findings = [item for item in validation_report.get("findings", []) if isinstance(item, dict)]
    output = (run_root / "manual-attestation.packet-prep.md") if output_path is None else output_path.resolve()
    lines = [
        "# ATLAS QA Manual Attestation Packet Prep",
        "",
        f"- Generated: `{utc_now()}`",
        f"- Run: `{run_id}`",
        f"- Scenario: `{scenario_id}`",
        f"- Promotion status: `{promotion.get('promotion_status', 'unknown')}`",
        f"- Validation status: `{validation_report.get('status', 'unknown')}`",
        f"- Manual-required lanes: `{', '.join(manual_required_lanes) or 'none'}`",
        f"- Still-open manual lanes: `{', '.join(open_manual_required_lanes) or 'none'}`",
        f"- Validated manual lanes: `{', '.join(validated_manual_attestation_lanes) or 'none'}`",
        "",
        "## Current Packet",
        "",
    ]
    for item in file_entries:
        lines.append(
            f"- `{item['lens_id']}`: attestation `{item['attestation_ref']}`, screenshot `{item['expected_screenshot_ref']}`, validation `{item['attestation_status']}`, screenshot file `{'present' if item['screenshot_exists'] else 'missing'}`"
        )
    if not file_entries:
        lines.append("- No scaffolded attestation files were found for this run.")
    lines.extend(
        [
            "",
            "## Findings",
            "",
        ]
    )
    if findings:
        for item in findings:
            lines.append(f"- `{item.get('code', 'unknown')}`: {item.get('message', '')}")
    else:
        lines.append("- No validation findings.")
    lines.extend(
        [
            "",
            "## Next Honest Move",
            "",
            "1. Capture real screenshots for each still-open lane whose screenshot file is still missing.",
            "2. Replace placeholder metadata, signature, and checksum fields inside the matching still-open manual-attestation JSON files.",
            f"3. Re-run validation: `python ops/atlas/qa/manual_attestation.py validate --run {run_id}`",
            f"4. Re-run promotion after the attestation files are valid: `python ops/atlas/qa/promote_run.py --root . --run {run_id} --scenario-file ops/atlas/qa/scenarios/{scenario_id}.json --stack-validation-file runtime/receipts/validation/stack-validation.latest.json`",
            "",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    report = {
        "runner_version": "atlas.qa.manual-attestation.packet-prep.v1",
        "generated_at": utc_now(),
        "run_id": run_id,
        "scenario_id": scenario_id,
        "promotion_status": str(promotion.get("promotion_status") or "unknown"),
        "validation_status": str(validation_report.get("status") or "unknown"),
        "manual_required_lanes": manual_required_lanes,
        "open_manual_required_lanes": open_manual_required_lanes,
        "validated_manual_attestation_lanes": validated_manual_attestation_lanes,
        "output_ref": atlas_relative(output, root=root),
        "finding_count": len(findings),
    }
    write_json(run_root / "manual-attestation.packet-prep.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create or validate manual ATLAS QA device attestations.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scaffold_parser = subparsers.add_parser("scaffold", help="Create manual attestation templates for unresolved manual lanes.")
    scaffold_parser.add_argument("--root", type=Path, default=atlas_root())
    scaffold_parser.add_argument("--run", required=True)
    scaffold_parser.add_argument("--operator", default="REPLACE_ME_OPERATOR")
    scaffold_parser.add_argument("--operator-identity", default="REPLACE_ME_IDENTITY")
    scaffold_parser.add_argument("--force", action="store_true")

    validate_parser = subparsers.add_parser("validate", help="Validate manual attestation files for a run or a single file.")
    validate_parser.add_argument("--root", type=Path, default=atlas_root())
    validate_parser.add_argument("--run")
    validate_parser.add_argument("--file", type=Path)

    packet_parser = subparsers.add_parser("packet-prep", help="Render an operator packet for the current manual-attestation state.")
    packet_parser.add_argument("--root", type=Path, default=atlas_root())
    packet_parser.add_argument("--run", required=True)
    packet_parser.add_argument("--output", type=Path)

    args = parser.parse_args(argv)
    if args.command == "scaffold":
        report = scaffold_manual_attestations(
            root=args.root.resolve(),
            run_id=args.run,
            operator=args.operator,
            operator_identity=args.operator_identity,
            force=bool(args.force),
        )
        print(json.dumps(report, indent=2))
        return 0
    if args.command == "validate":
        root = args.root.resolve()
        if isinstance(args.file, Path):
            summary, findings = validate_attestation_file(root=root, attestation_path=args.file.resolve())
            report = {
                "runner_version": "atlas.qa.manual-attestation.validate.v1",
                "generated_at": utc_now(),
                "status": "clean" if not any(item["severity"] == "error" for item in findings) else "invalid",
                "attestation": summary,
                "finding_count": len(findings),
                "findings": findings,
            }
            print(json.dumps(report, indent=2))
            return 0 if report["status"] == "clean" else 1
        if not args.run:
            raise SystemExit("Provide --run or --file for validate.")
        report = validate_attestations_for_run(root=root, run_id=args.run)
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "clean" else 1
    if args.command == "packet-prep":
        report = build_manual_attestation_packet_prep(
            root=args.root.resolve(),
            run_id=args.run,
            output_path=args.output,
        )
        print(json.dumps(report, indent=2))
        return 0
    raise SystemExit("Unsupported command.")


if __name__ == "__main__":
    raise SystemExit(main())
