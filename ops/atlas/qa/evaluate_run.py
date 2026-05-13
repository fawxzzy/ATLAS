from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.qa._common import (
    ARTIFACT_CONTRACT_VERSION,
    RESULT_CONTRACT_VERSION,
    default_run_root,
    derive_evidence_profile,
    load_json_object,
    load_schema,
    payload_with_digest,
    resolve_ref,
    utc_now,
    validate_artifact_manifest,
    validate_result_payload,
    validate_schema_metadata,
    validate_test_evidence_payload,
    write_manifest,
)
from ops.atlas.qa.validate_artifacts import validate_artifact_manifest_file
from ops.atlas.qa.visual_diff import evaluate_visual_diffs

RUNNER_VERSION = "atlas.qa.evaluate-run.v2"


def _tier_from_artifact(artifact: dict[str, Any]) -> str | None:
    if artifact.get("status") == "manual_attested":
        return "manual_attestation"
    evidence = artifact.get("evidence")
    if not isinstance(evidence, dict):
        return None
    tier = evidence.get("evidence_tier")
    if isinstance(tier, str) and tier:
        return tier
    capture_method = evidence.get("capture_method")
    if capture_method == "provider_automation":
        return "physical_device"
    if capture_method == "manual_attestation":
        return "manual_attestation"
    return "emulated_browser"


def evaluate_run(
    *,
    root: Path | None = None,
    result_path: Path | None = None,
    artifact_path: Path | None = None,
    run_id: str | None = None,
    output_file: Path | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    if result_path is None:
        if not run_id:
            raise ValueError("Provide result_path or run_id.")
        result_path = (default_run_root(root=base_root) / run_id / "matrix.result.json").resolve()
    if artifact_path is None:
        artifact_path = result_path.with_name("artifacts.manifest.json")
    result_schema = load_schema("atlas.qa.result.v1", root=base_root)
    schema_errors = validate_schema_metadata(result_schema, "atlas.qa.result.v1")
    if schema_errors:
        raise ValueError("; ".join(schema_errors))

    result_payload = load_json_object(result_path.resolve())
    artifact_payload = load_json_object(artifact_path.resolve())
    if result_payload.get("contract_version") != RESULT_CONTRACT_VERSION:
        raise ValueError("result_file must contain atlas.qa.result.v1.")
    if artifact_payload.get("contract_version") != ARTIFACT_CONTRACT_VERSION:
        raise ValueError("artifact_file must contain atlas.qa.artifact.v1.")
    result_errors = validate_result_payload(result_payload)
    artifact_errors = validate_artifact_manifest(artifact_payload)
    if result_errors:
        raise ValueError("; ".join(result_errors))
    if artifact_errors:
        raise ValueError("; ".join(artifact_errors))

    scenario_path = resolve_ref(str(result_payload["scenario_ref"]), root=base_root)
    scenario_payload = load_json_object(scenario_path)
    adapter_payload: dict[str, Any] = {}
    adapter_ref = result_payload.get("adapter_ref")
    if isinstance(adapter_ref, str) and adapter_ref.strip():
        adapter_target = resolve_ref(adapter_ref, root=base_root)
        if adapter_target.exists():
            adapter_payload = load_json_object(adapter_target)
    evidence_profile = derive_evidence_profile(
        scenario_payload=scenario_payload,
        adapter_payload=adapter_payload,
        matrix=result_payload.get("matrix", []),
    )
    test_evidence_path = result_path.with_name("test-evidence.json")
    test_evidence_payload = load_json_object(test_evidence_path) if test_evidence_path.exists() else None
    test_evidence_errors = validate_test_evidence_payload(test_evidence_payload) if isinstance(test_evidence_payload, dict) else []
    findings = list(result_payload.get("findings", []))
    artifact_validation = validate_artifact_manifest_file(
        root=base_root,
        artifact_path=artifact_path.resolve(),
        promotion_strict=False,
    )
    validation_ref = artifact_path.with_name("artifact.validation.json")
    write_manifest(validation_ref, artifact_validation)

    missing_artifacts = [item for item in artifact_payload.get("artifacts", []) if item.get("status") == "missing"]
    manual_artifacts = [item for item in artifact_payload.get("artifacts", []) if item.get("status") == "manual_required"]
    manual_attested_artifacts = [item for item in artifact_payload.get("artifacts", []) if item.get("status") == "manual_attested"]
    failed_lenses = [item for item in result_payload.get("matrix", []) if item.get("status") == "fail"]
    manual_lenses = [item for item in result_payload.get("matrix", []) if item.get("status") == "manual_required"]
    invalid_artifacts = [item for item in artifact_validation.get("findings", []) if item.get("severity") == "error"]
    certify_lenses = set(str(item) for item in scenario_payload.get("proof", {}).get("certify_lenses", []))
    present_artifacts = [item for item in artifact_payload.get("artifacts", []) if item.get("status") == "present"]
    required_test_evidence = scenario_payload.get("test_evidence", []) if isinstance(scenario_payload.get("test_evidence"), list) else []
    test_summary = test_evidence_payload.get("summary", {}) if isinstance(test_evidence_payload, dict) and isinstance(test_evidence_payload.get("summary"), dict) else {}
    if required_test_evidence and test_evidence_payload is None:
        findings.append(
            {
                "severity": "error",
                "code": "missing_test_evidence_receipt",
                "message": "Scenario declares required test evidence but the test-evidence receipt is missing.",
            }
        )
        test_summary = {"status": "missing"}
    if test_evidence_errors:
        findings.extend(
            {
                "severity": "error",
                "code": "invalid_test_evidence",
                "message": message,
            }
            for message in test_evidence_errors
        )
    satisfied_tiers = {
        tier
        for tier in (_tier_from_artifact(item) for item in [*present_artifacts, *manual_attested_artifacts])
        if isinstance(tier, str)
    }
    missing_tiers: list[str] = []
    if evidence_profile == "web_visual" and "emulated_browser" not in satisfied_tiers:
        missing_tiers.append("emulated_browser")
    if (
        evidence_profile == "web_visual"
        and certify_lenses
        and "physical_device" not in satisfied_tiers
        and "manual_attestation" not in satisfied_tiers
    ):
        missing_tiers.append("physical_device")
    unresolved_manual_lenses = [
        str(item.get("lens_id"))
        for item in result_payload.get("matrix", [])
        if item.get("status") == "manual_required"
        and str(item.get("lens_id")) not in {
            str(artifact.get("lens_id"))
            for artifact in [*present_artifacts, *manual_attested_artifacts]
            if _tier_from_artifact(artifact) in {"physical_device", "manual_attestation"}
        }
    ]
    visual_diffs, visual_findings = evaluate_visual_diffs(
        root=base_root,
        run_root=result_path.resolve().parent,
        scenario_payload=scenario_payload,
        artifact_payload=artifact_payload,
        dry_run=bool(result_payload["mode"] == "dry_run"),
    )
    findings.extend(visual_findings)
    visual_status = "not_configured"
    if result_payload["mode"] == "dry_run" and visual_diffs:
        visual_status = "planned"
    elif visual_diffs:
        if any(item.get("status") in {"failed", "invalid_baseline", "invalid_candidate", "size_mismatch", "candidate_missing"} for item in visual_diffs):
            visual_status = "failed"
        elif any(item.get("status") == "baseline_required" for item in visual_diffs):
            visual_status = "baseline_required"
        else:
            visual_status = "passed"

    if missing_artifacts:
        findings.append(
            {
                "severity": "error",
                "code": "missing_required_artifacts",
                "message": f"Missing {len(missing_artifacts)} required artifacts.",
            }
        )
    if manual_artifacts or unresolved_manual_lenses:
        findings.append(
            {
                "severity": "warning",
                "code": "manual_certification_required",
                "message": "One or more real-device or external certification lanes still require manual completion.",
            }
        )
    if manual_attested_artifacts:
        findings.append(
            {
                "severity": "info",
                "code": "manual_attestation_used",
                "message": "Manual attestation was used to satisfy one or more physical-device lanes.",
            }
        )
    if invalid_artifacts:
        findings.append(
            {
                "severity": "error",
                "code": "invalid_artifact_evidence",
                "message": f"Artifact validation reported {len(invalid_artifacts)} evidence errors.",
            }
        )
    if required_test_evidence and test_summary.get("status") in {"failed", "missing"}:
        findings.append(
            {
                "severity": "error",
                "code": "required_test_evidence_failed",
                "message": "Required repo-native test evidence is missing or failing.",
            }
        )

    require_real_device_on = str(scenario_payload.get("promotion", {}).get("require_real_device_on", "never"))
    allow_manual = bool(scenario_payload.get("promotion", {}).get("allow_manual_certification", False))
    upstream_executable_status = str(result_payload.get("summary", {}).get("executable_status") or "")
    executable_status = (
        "failed"
        if upstream_executable_status == "failed"
        or failed_lenses
        or any(item.get("severity") == "error" and item.get("code") in {"command_failed", "preflight_failed", "required_test_evidence_failed"} for item in findings)
        else "clean"
    )
    artifact_status = "complete" if not missing_artifacts and not invalid_artifacts else "incomplete"
    if require_real_device_on == "never":
        certification_status = "satisfied"
    elif unresolved_manual_lenses or manual_artifacts:
        certification_status = "manual_required" if allow_manual else "missing"
    elif any(_tier_from_artifact(item) == "manual_attestation" for item in [*present_artifacts, *manual_attested_artifacts]):
        certification_status = "manual_attested"
    else:
        certification_status = "satisfied"
    overall_status = "ready"
    if executable_status == "failed" or artifact_status == "incomplete" or certification_status == "missing" or visual_status == "failed":
        overall_status = "blocked"
    body = {
        "contract_version": RESULT_CONTRACT_VERSION,
        "generated_at": utc_now(),
        "runner_version": RUNNER_VERSION,
        "stage": "evaluated",
        "run_id": str(result_payload["run_id"]),
        "scenario_ref": str(result_payload["scenario_ref"]),
        "repo_id": str(result_payload["repo_id"]),
        "repo_path": str(result_payload["repo_path"]),
        "git_sha": str(result_payload["git_sha"]),
        "adapter_id": str(result_payload["adapter_id"]),
        "adapter_ref": str(result_payload["adapter_ref"]),
        "lens_manifest_ref": str(result_payload["lens_manifest_ref"]),
        "mode": str(result_payload["mode"]),
        "summary": {
            "overall_status": "dry_run" if result_payload["mode"] == "dry_run" else overall_status,
            "executable_status": "planned" if result_payload["mode"] == "dry_run" else executable_status,
            "artifact_status": "planned" if result_payload["mode"] == "dry_run" else artifact_status,
            "certification_status": "planned" if result_payload["mode"] == "dry_run" else certification_status,
            "lens_count": int(result_payload["summary"]["lens_count"]),
            "failing_lens_count": len(failed_lenses),
            "finding_count": len(findings),
            "highest_satisfied_tier": "dry_run" if result_payload["mode"] == "dry_run" else (
                "physical_device" if "physical_device" in satisfied_tiers else (
                    "manual_attestation" if "manual_attestation" in satisfied_tiers else (
                        "emulated_browser" if "emulated_browser" in satisfied_tiers else "dry_run"
                    )
                )
            ),
            "satisfied_evidence_tiers": [] if result_payload["mode"] == "dry_run" else sorted(satisfied_tiers),
            "missing_evidence_tiers": [] if result_payload["mode"] == "dry_run" else missing_tiers,
            "manual_required_lanes": [] if result_payload["mode"] == "dry_run" else unresolved_manual_lenses,
            "visual_status": visual_status,
            "visual_diff_count": len(visual_diffs),
            "test_evidence_status": test_summary.get("status", "not_configured") if required_test_evidence else "not_configured",
            "required_test_evidence_count": len(required_test_evidence),
            "evidence_profile": evidence_profile,
        },
        "matrix": result_payload["matrix"],
        "findings": findings,
        "artifact_manifest_refs": [
            atlas_relative(artifact_path.resolve(), root=base_root),
            atlas_relative(validation_ref.resolve(), root=base_root),
        ],
        "visual_diffs": visual_diffs,
        "test_evidence_refs": [] if test_evidence_payload is None else [atlas_relative(test_evidence_path.resolve(), root=base_root)],
        "receipt_origin": result_payload.get("receipt_origin"),
    }
    evaluated = payload_with_digest(body, "result_id")
    payload_errors = validate_result_payload(evaluated)
    if payload_errors:
        raise ValueError("; ".join(payload_errors))

    target = output_file.resolve() if isinstance(output_file, Path) else result_path.with_name("evaluated.result.json")
    write_manifest(target, evaluated)
    return evaluated | {"output_ref": atlas_relative(target, root=base_root)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate an ATLAS QA run result against its artifact manifest.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--result-file", type=Path)
    parser.add_argument("--artifact-file", type=Path)
    parser.add_argument("--run")
    parser.add_argument("--output-file", type=Path)
    args = parser.parse_args(argv)

    result = evaluate_run(
        root=args.root.resolve(),
        result_path=args.result_file.resolve() if isinstance(args.result_file, Path) else None,
        artifact_path=args.artifact_file.resolve() if isinstance(args.artifact_file, Path) else None,
        run_id=args.run,
        output_file=args.output_file.resolve() if isinstance(args.output_file, Path) else None,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["summary"]["overall_status"] in {"dry_run", "ready"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
