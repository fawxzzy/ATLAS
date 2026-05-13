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
    result_path = run_root / "evaluated.result.json"
    if not result_path.exists():
        result_path = run_root / "matrix.result.json"
    result_payload = load_json_object(result_path)
    unresolved = list(result_payload.get("summary", {}).get("manual_required_lanes", []))
    if not unresolved:
        unresolved = [
            str(item.get("lens_id"))
            for item in result_payload.get("matrix", [])
            if isinstance(item, dict) and item.get("status") == "manual_required"
        ]
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
    raise SystemExit("Unsupported command.")


if __name__ == "__main__":
    raise SystemExit(main())
