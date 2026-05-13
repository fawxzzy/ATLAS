from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.qa._common import (
    baseline_manifest_path,
    default_run_root,
    load_json_object,
    load_schema,
    validate_artifact_manifest,
    validate_capture_receipt,
    validate_schema_metadata,
    validate_visual_baseline_payload,
)
from ops.atlas.qa.manual_attestation import validate_attestation_file
from ops.cortex._artifacts import sha256_bytes, write_json

RUNNER_VERSION = "atlas.qa.validate-artifacts.v1"


def _artifact_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _artifact_report_path(run_root: Path) -> Path:
    return run_root / "artifact.validation.json"


def _validate_image(path: Path) -> str | None:
    try:
        with Image.open(path) as image:
            image.verify()
        return None
    except Exception as exc:
        return str(exc)


def validate_artifact_manifest_file(
    *,
    root: Path,
    artifact_path: Path,
    promotion_strict: bool = False,
) -> dict[str, Any]:
    payload = load_json_object(artifact_path.resolve())
    manifest_errors = validate_artifact_manifest(payload)
    findings: list[dict[str, Any]] = []
    capture_schema_errors = validate_schema_metadata(load_schema("atlas.qa.capture_receipt.v1", root=root), "atlas.qa.capture_receipt.v1")
    baseline_schema_errors = validate_schema_metadata(load_schema("atlas.qa.visual_baseline.v1", root=root), "atlas.qa.visual_baseline.v1")
    for message in [*capture_schema_errors, *baseline_schema_errors]:
        findings.append({"severity": "error", "code": "invalid_root_schema", "message": message})
    if manifest_errors:
        findings.extend({"severity": "error", "code": "invalid_manifest", "message": message} for message in manifest_errors)

    if payload.get("evidence_grade") == "dry_run":
        findings.append(
            {
                "severity": "error" if promotion_strict else "warning",
                "code": "dry_run_evidence",
                "message": "Dry-run evidence may validate pipeline wiring, but may never satisfy promotion.",
            }
        )

    attestation_by_lens: dict[str, dict[str, Any]] = {}
    for attestation in payload.get("attestations", []):
        if not isinstance(attestation, dict):
            findings.append(
                {
                    "severity": "error",
                    "code": "invalid_attestation_summary",
                    "message": "attestations entries must be objects.",
                }
            )
            continue
        attestation_ref = attestation.get("attestation_ref")
        if not isinstance(attestation_ref, str) or not attestation_ref.strip():
            findings.append(
                {
                    "severity": "error",
                    "code": "missing_attestation_ref",
                    "message": "Attestation summary is missing attestation_ref.",
                }
            )
            continue
        summary, attestation_findings = validate_attestation_file(root=root, attestation_path=(root / attestation_ref).resolve())
        lens_id = summary.get("lens_id")
        if isinstance(lens_id, str) and lens_id:
            attestation_by_lens[lens_id] = summary
        findings.extend(attestation_findings)
        if summary.get("run_id") != payload.get("run_id"):
            findings.append(
                {
                    "severity": "error",
                    "code": "attestation_wrong_run_id",
                    "message": "Manual attestation run_id does not match the active run.",
                }
            )
        if summary.get("scenario_id") != payload.get("scenario_id"):
            findings.append(
                {
                    "severity": "error",
                    "code": "attestation_wrong_scenario_id",
                    "message": "Manual attestation scenario_id does not match the artifact manifest.",
                }
            )
        if summary.get("adapter_id") != payload.get("adapter_id"):
            findings.append(
                {
                    "severity": "error",
                    "code": "attestation_wrong_adapter_id",
                    "message": "Manual attestation adapter_id does not match the artifact manifest.",
                }
            )

    for artifact in payload.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        artifact_id = str(artifact.get("artifact_id") or "")
        artifact_kind = str(artifact.get("artifact_kind") or "")
        status = str(artifact.get("status") or "")
        if status == "manual_attested":
            lens_id = str(artifact.get("lens_id") or "")
            if lens_id not in attestation_by_lens:
                findings.append(
                    {
                        "severity": "error",
                        "code": "missing_manual_attestation",
                        "message": f"Artifact '{artifact_id}' is manual_attested but no valid attestation exists for the lens.",
                    }
                )
            continue
        if status != "present":
            continue
        path_ref = artifact.get("path_ref")
        if not isinstance(path_ref, str) or not path_ref.strip():
            findings.append(
                {
                    "severity": "error",
                    "code": "missing_path_ref",
                    "message": f"Artifact '{artifact_id}' is present but missing path_ref.",
                }
            )
            continue
        resolved_path = (root / path_ref).resolve()
        if not resolved_path.exists():
            findings.append(
                {
                    "severity": "error",
                    "code": "missing_artifact_file",
                    "message": f"Artifact '{artifact_id}' path does not exist.",
                }
            )
            continue
        size = resolved_path.stat().st_size
        if size <= 0:
            findings.append(
                {
                    "severity": "error",
                    "code": "zero_byte_artifact",
                    "message": f"Artifact '{artifact_id}' is zero bytes.",
                }
            )
            continue
        digest = sha256_bytes(_artifact_bytes(resolved_path))
        declared_digest = artifact.get("checksum_sha256")
        if not isinstance(declared_digest, str) or declared_digest != digest:
            findings.append(
                {
                    "severity": "error",
                    "code": "checksum_mismatch",
                    "message": f"Artifact '{artifact_id}' checksum does not match the file bytes.",
                }
            )
        if artifact_kind == "screenshot":
            image_error = _validate_image(resolved_path)
            if image_error:
                findings.append(
                    {
                        "severity": "error",
                        "code": "invalid_image_file",
                        "message": f"Artifact '{artifact_id}' is not a decodable image: {image_error}",
                    }
                )
            evidence = artifact.get("evidence")
            if not isinstance(evidence, dict):
                findings.append(
                    {
                        "severity": "error",
                        "code": "missing_evidence_metadata",
                        "message": f"Artifact '{artifact_id}' is missing required screenshot evidence metadata.",
                    }
                )
                continue
            required_fields = (
                "run_id",
                "scenario_id",
                "adapter_id",
                "repo_id",
                "git_sha",
                "lens_id",
                "viewport",
                "browser_engine",
                "captured_at",
                "source_url",
                "artifact_sha256",
            )
            for field in required_fields:
                value = evidence.get(field)
                if value is None or (isinstance(value, str) and not value):
                    findings.append(
                        {
                            "severity": "error",
                            "code": "missing_evidence_field",
                            "message": f"Artifact '{artifact_id}' evidence is missing '{field}'.",
                        }
                    )
            capture_method = evidence.get("capture_method")
            if capture_method not in {"browser_emulation", "provider_automation", "manual_attestation"}:
                findings.append(
                    {
                        "severity": "error",
                        "code": "invalid_capture_method",
                        "message": f"Artifact '{artifact_id}' evidence capture_method is not supported.",
                    }
                )
            if evidence.get("run_id") != payload.get("run_id"):
                findings.append(
                    {
                        "severity": "error",
                        "code": "wrong_run_id",
                        "message": f"Artifact '{artifact_id}' evidence run_id does not match the active run.",
                    }
                )
            if evidence.get("scenario_id") != payload.get("scenario_id"):
                findings.append(
                    {
                        "severity": "error",
                        "code": "wrong_scenario_id",
                        "message": f"Artifact '{artifact_id}' evidence scenario_id does not match the manifest.",
                    }
                )
            if evidence.get("adapter_id") != payload.get("adapter_id"):
                findings.append(
                    {
                        "severity": "error",
                        "code": "wrong_adapter_id",
                        "message": f"Artifact '{artifact_id}' evidence adapter_id does not match the manifest.",
                    }
                )
            if evidence.get("repo_id") != payload.get("repo_id"):
                findings.append(
                    {
                        "severity": "error",
                        "code": "wrong_repo_id",
                        "message": f"Artifact '{artifact_id}' evidence repo_id does not match the manifest.",
                    }
                )
            if evidence.get("git_sha") != payload.get("git_sha"):
                findings.append(
                    {
                        "severity": "error",
                        "code": "wrong_git_sha",
                        "message": f"Artifact '{artifact_id}' evidence git_sha does not match the manifest.",
                    }
                )
            if evidence.get("lens_id") != artifact.get("lens_id"):
                findings.append(
                    {
                        "severity": "error",
                        "code": "wrong_lens_id",
                        "message": f"Artifact '{artifact_id}' evidence lens_id does not match the artifact.",
                    }
                )
            if evidence.get("artifact_sha256") != digest:
                findings.append(
                    {
                        "severity": "error",
                        "code": "missing_artifact_hash",
                        "message": f"Artifact '{artifact_id}' evidence artifact_sha256 does not match the file bytes.",
                            }
                        )
            metadata_ref = evidence.get("metadata_ref")
            if capture_method in {"browser_emulation", "provider_automation"}:
                if not isinstance(metadata_ref, str) or not metadata_ref.strip():
                    findings.append(
                        {
                            "severity": "error",
                            "code": "missing_capture_receipt",
                            "message": f"Artifact '{artifact_id}' evidence is missing metadata_ref for automated capture.",
                        }
                    )
                else:
                    metadata_path = (root / metadata_ref).resolve()
                    if not metadata_path.exists():
                        findings.append(
                            {
                                "severity": "error",
                                "code": "missing_capture_receipt",
                                "message": f"Artifact '{artifact_id}' capture receipt does not exist.",
                            }
                        )
                    else:
                        receipt_payload = load_json_object(metadata_path)
                        receipt_errors = validate_capture_receipt(receipt_payload)
                        findings.extend(
                            {
                                "severity": "error",
                                "code": "invalid_capture_receipt",
                                "message": f"Artifact '{artifact_id}' capture receipt error: {message}",
                            }
                            for message in receipt_errors
                        )
            if capture_method == "provider_automation":
                for field in ("provider_id", "provider_run_id", "device_model", "os_name", "os_version", "browser_name"):
                    value = evidence.get(field)
                    if value is None or (isinstance(value, str) and not value):
                        findings.append(
                            {
                                "severity": "error",
                                "code": "missing_provider_field",
                                "message": f"Artifact '{artifact_id}' evidence is missing provider field '{field}'.",
                            }
                        )
            if capture_method == "manual_attestation":
                for field in ("operator", "attestation_ref", "device_model", "os_name", "os_version", "browser_name"):
                    value = evidence.get(field)
                    if value is None or (isinstance(value, str) and not value):
                        findings.append(
                            {
                                "severity": "error",
                                "code": "missing_manual_attestation_field",
                                "message": f"Artifact '{artifact_id}' evidence is missing manual attestation field '{field}'.",
                            }
                        )
        if artifact_kind == "screenshot" and status == "present":
            lens_id = str(artifact.get("lens_id") or "")
            baseline_image = None
            for path in (root / "data" / "atlas" / "qa" / "baselines").rglob(f"{lens_id}.png"):
                baseline_image = path
                break
            if baseline_image is not None:
                manifest_path = baseline_manifest_path(baseline_image)
                if manifest_path.exists():
                    baseline_payload = load_json_object(manifest_path)
                    baseline_errors = validate_visual_baseline_payload(baseline_payload)
                    findings.extend(
                        {
                            "severity": "error",
                            "code": "invalid_visual_baseline",
                            "message": f"Baseline manifest for lens '{lens_id}' is invalid: {message}",
                        }
                        for message in baseline_errors
                    )

    status = "clean" if not any(item["severity"] == "error" for item in findings) else "invalid"
    report = {
        "runner_version": RUNNER_VERSION,
        "generated_at": payload.get("generated_at"),
        "run_id": payload.get("run_id"),
        "artifact_manifest_ref": atlas_relative(artifact_path.resolve(), root=root),
        "promotion_strict": promotion_strict,
        "status": status,
        "finding_count": len(findings),
        "findings": findings,
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ATLAS QA artifact authenticity.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--artifact-file", type=Path)
    parser.add_argument("--run")
    parser.add_argument("--promotion", action="store_true")
    args = parser.parse_args(argv)

    base_root = args.root.resolve()
    if isinstance(args.artifact_file, Path):
        artifact_path = args.artifact_file.resolve()
        run_root = artifact_path.parent
    elif args.run:
        run_root = (default_run_root(root=base_root) / args.run).resolve()
        artifact_path = run_root / "artifacts.manifest.json"
    else:
        raise SystemExit("Provide --artifact-file or --run.")
    report = validate_artifact_manifest_file(
        root=base_root,
        artifact_path=artifact_path,
        promotion_strict=bool(args.promotion),
    )
    write_json(_artifact_report_path(run_root), report)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "clean" else 1


if __name__ == "__main__":
    raise SystemExit(main())
