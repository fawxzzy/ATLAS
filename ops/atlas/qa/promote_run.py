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
from ops.atlas.qa._common import (
    ARTIFACT_CONTRACT_VERSION,
    PROMOTION_CONTRACT_VERSION,
    RESULT_CONTRACT_VERSION,
    build_receipt_origin,
    default_run_waiver_dir,
    default_run_root,
    derive_evidence_profile,
    load_json_object,
    load_schema,
    payload_with_digest,
    resolve_ref,
    utc_now,
    validate_artifact_manifest,
    validate_promotion_payload,
    validate_waiver_payload,
    validate_result_payload,
    validate_schema_metadata,
    write_manifest,
)

RUNNER_VERSION = "atlas.qa.promote-run.v3"


def _highest_tier(value: list[str]) -> str | None:
    order = ["dry_run", "emulated_browser", "manual_attestation", "physical_device"]
    for item in reversed(order):
        if item in value:
            return item
    return None


def _parse_utc(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _load_manual_attestation_statuses(*, run_root: Path) -> dict[str, str]:
    result_path = run_root / "manual_attestation.result.json"
    if not result_path.exists():
        return {}
    payload = load_json_object(result_path)
    statuses: dict[str, str] = {}
    for item in payload.get("attestations", []):
        if not isinstance(item, dict):
            continue
        lens_id = str(item.get("lens_id") or "")
        status = str(item.get("status") or "")
        if lens_id:
            statuses[lens_id] = status
    return statuses


def _load_valid_waivers(
    *,
    root: Path,
    run_root: Path,
    repo_id: str,
    scenario_id: str,
    run_id: str,
    candidate_lanes: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    waiver_dir = default_run_waiver_dir(root=root, run_id=run_id)
    if not waiver_dir.exists():
        return [], []
    valid: list[dict[str, Any]] = []
    findings: list[str] = []
    lane_set = {item for item in candidate_lanes if isinstance(item, str) and item}
    for path in sorted(waiver_dir.glob("*.json")):
        payload = load_json_object(path)
        errors = validate_waiver_payload(payload)
        if errors:
            findings.extend(f"Waiver '{atlas_relative(path, root=root)}' is invalid: {detail}" for detail in errors)
            continue
        if str(payload.get("repo_id") or "") != repo_id:
            findings.append(f"Waiver '{atlas_relative(path, root=root)}' repo_id does not match the active repo.")
            continue
        if str(payload.get("scenario_id") or "") != scenario_id:
            findings.append(f"Waiver '{atlas_relative(path, root=root)}' scenario_id does not match the active scenario.")
            continue
        if str(payload.get("run_id") or "") != run_id:
            findings.append(f"Waiver '{atlas_relative(path, root=root)}' run_id does not match the active run.")
            continue
        waived_lane = str(payload.get("waived_lane") or "")
        canonical_lane = waived_lane.removesuffix(".manual")
        if waived_lane not in lane_set and canonical_lane not in lane_set:
            findings.append(f"Waiver '{atlas_relative(path, root=root)}' waived_lane does not match an unresolved manual lane.")
            continue
        expires_at = _parse_utc(str(payload.get("expires_at") or ""))
        if expires_at is None or expires_at <= datetime.now(timezone.utc):
            findings.append(f"Waiver '{atlas_relative(path, root=root)}' is expired or has an invalid expires_at.")
            continue
        payload["_waiver_ref"] = atlas_relative(path, root=root)
        payload["_waived_lane_canonical"] = canonical_lane
        valid.append(payload)
    return valid, findings


def promote_run(
    *,
    root: Path | None = None,
    result_path: Path | None = None,
    artifact_path: Path | None = None,
    run_id: str | None = None,
    scenario_path: Path | None = None,
    stack_validation_path: Path | None = None,
    output_file: Path | None = None,
) -> dict[str, object]:
    base_root = (root or atlas_root()).resolve()
    if result_path is None:
        if not run_id:
            raise ValueError("Provide result_path or run_id.")
        result_path = (default_run_root(root=base_root) / run_id / "evaluated.result.json").resolve()
    if artifact_path is None:
        artifact_path = result_path.with_name("artifacts.manifest.json")
    promotion_schema = load_schema("atlas.qa.promotion.v1", root=base_root)
    schema_errors = validate_schema_metadata(promotion_schema, "atlas.qa.promotion.v1")
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
    run_root = result_path.resolve().parent

    scenario_target = scenario_path.resolve() if isinstance(scenario_path, Path) else resolve_ref(str(result_payload["scenario_ref"]), root=base_root)
    scenario_payload = load_json_object(scenario_target)
    adapter_payload: dict[str, object] = {}
    adapter_ref = result_payload.get("adapter_ref")
    if isinstance(adapter_ref, str) and adapter_ref.strip():
        adapter_target = resolve_ref(adapter_ref, root=base_root)
        if adapter_target.exists():
            adapter_payload = load_json_object(adapter_target)
    governance = {
        "status": "not_run",
        "critical_count": 0,
        "error_count": 0,
    }
    if isinstance(stack_validation_path, Path):
        stack_validation_payload = load_json_object(stack_validation_path.resolve())
        summary = stack_validation_payload.get("summary", {}) if isinstance(stack_validation_payload.get("summary"), dict) else {}
        critical_count = int(summary.get("critical", 0) or 0)
        error_count = int(summary.get("error", 0) or 0)
        governance = {
            "status": "blocking" if critical_count or error_count else "clean",
            "critical_count": critical_count,
            "error_count": error_count,
            "report_ref": atlas_relative(stack_validation_path.resolve(), root=base_root),
        }

    executable_truth = "unknown"
    if result_payload["summary"]["executable_status"] == "clean":
        executable_truth = "clean"
    elif result_payload["summary"]["executable_status"] == "failed":
        executable_truth = "failed"

    artifact_coverage = "unknown"
    if result_payload["summary"]["artifact_status"] == "complete":
        artifact_coverage = "complete"
    elif result_payload["summary"]["artifact_status"] == "incomplete":
        artifact_coverage = "incomplete"

    certification_status = str(result_payload["summary"]["certification_status"])
    if certification_status == "missing":
        real_device_proof = "missing"
    elif certification_status == "planned":
        real_device_proof = "unknown"
    else:
        real_device_proof = "not_required"
    visual_status = str(result_payload.get("summary", {}).get("visual_status") or "not_configured")
    test_evidence_status = str(result_payload.get("summary", {}).get("test_evidence_status") or "not_configured")

    blocking_reasons: list[str] = []
    manual_gaps: list[str] = []
    if executable_truth == "failed":
        blocking_reasons.append("Executable truth failed.")
    if artifact_coverage == "incomplete":
        blocking_reasons.append("Required artifacts are incomplete.")
    if visual_status == "failed":
        blocking_reasons.append("Visual diff assertions failed.")
    elif visual_status == "baseline_required":
        manual_gaps.append("One or more visual assertions still require a promoted baseline.")
    if test_evidence_status == "failed":
        blocking_reasons.append("Required repo-native test evidence failed.")
    elif test_evidence_status == "missing":
        blocking_reasons.append("Required repo-native test evidence is missing.")
    elif test_evidence_status == "planned":
        manual_gaps.append("Repo-native test evidence has not been executed yet.")
    if governance["status"] == "blocking":
        blocking_reasons.append("Root governance validation is blocking promotion.")

    satisfied_evidence_tiers = list(result_payload.get("summary", {}).get("satisfied_evidence_tiers", []))
    missing_evidence_tiers = list(result_payload.get("summary", {}).get("missing_evidence_tiers", []))
    raw_manual_required_lanes = list(result_payload.get("summary", {}).get("manual_required_lanes", []))
    manual_attestation_statuses = _load_manual_attestation_statuses(run_root=run_root)
    manually_attested_lanes = sorted(
        lens_id for lens_id, status in manual_attestation_statuses.items() if status == "valid"
    )
    manual_required_lanes = [
        lens_id for lens_id in raw_manual_required_lanes if lens_id not in set(manually_attested_lanes)
    ]
    active_waivers, waiver_findings = _load_valid_waivers(
        root=base_root,
        run_root=run_root,
        repo_id=str(result_payload["repo_id"]),
        scenario_id=str(scenario_payload["scenario_id"]),
        run_id=str(result_payload["run_id"]),
        candidate_lanes=manual_required_lanes,
    )
    waived_lanes = sorted({str(item.get("waived_lane") or "") for item in active_waivers if str(item.get("waived_lane") or "")})
    waived_lane_canonical = {
        str(item.get("_waived_lane_canonical") or "")
        for item in active_waivers
        if str(item.get("_waived_lane_canonical") or "")
    }
    manual_required_lanes = [lens_id for lens_id in manual_required_lanes if lens_id not in waived_lane_canonical]
    waiver_refs = [str(item.get("_waiver_ref") or "") for item in active_waivers if str(item.get("_waiver_ref") or "")]
    waiver_reasons = [str(item.get("reason") or "") for item in active_waivers if str(item.get("reason") or "")]
    blocking_reasons.extend(waiver_findings)
    highest_satisfied_tier = result_payload.get("summary", {}).get("highest_satisfied_tier")
    if not isinstance(highest_satisfied_tier, str) or not highest_satisfied_tier:
        highest_satisfied_tier = _highest_tier(satisfied_evidence_tiers)
    require_real_device_on = str(scenario_payload.get("promotion", {}).get("require_real_device_on", "never"))
    real_device_required = require_real_device_on != "never"
    if real_device_required:
        if manual_required_lanes:
            real_device_proof = "manual_required"
            manual_gaps.append("Real-device certification still requires manual completion.")
        elif waived_lanes:
            real_device_proof = "waived"
        elif manually_attested_lanes:
            real_device_proof = "manual_attested"
        elif certification_status == "manual_attested":
            real_device_proof = "manual_attested"
        elif certification_status == "satisfied":
            real_device_proof = "satisfied"
        elif certification_status == "missing":
            real_device_proof = "missing"
        elif certification_status == "planned":
            real_device_proof = "unknown"
        else:
            real_device_proof = "not_required"
    elif certification_status == "satisfied":
        real_device_proof = "satisfied"
    if real_device_proof == "missing":
        blocking_reasons.append("Required real-device certification is missing.")

    decision = "promote"
    if blocking_reasons:
        decision = "hold"
    elif manual_gaps or result_payload["mode"] == "dry_run":
        decision = "manual_review"
    if result_payload["mode"] == "dry_run":
        manual_gaps.append("Dry-run receipt only; executable and artifact truth were not executed.")

    operator_summary = []
    if result_payload["mode"] == "dry_run":
        operator_summary.append("Dry-run only: scenario planning succeeded, but executable truth and certification still need a real run.")
    elif decision == "promote":
        operator_summary.append("Promotion ready: executable truth, artifact coverage, and certification are satisfied.")
    elif decision == "manual_review":
        operator_summary.append("Manual review required before promotion.")
    else:
        operator_summary.append("Promotion blocked by executable or evidence failures.")

    if result_payload["mode"] == "dry_run":
        promotion_status = "dry_run"
    elif decision == "promote":
        if waived_lanes:
            promotion_status = "waived_promoted"
        elif real_device_required and real_device_proof == "satisfied":
            promotion_status = "promoted_physical"
        elif real_device_required and real_device_proof == "manual_attested":
            promotion_status = "promoted_physical_manual"
        else:
            promotion_status = "promoted_emulated"
    elif decision == "manual_review":
        promotion_status = "manual_review"
    else:
        promotion_status = "blocked"
    evidence_profile = derive_evidence_profile(
        scenario_payload=scenario_payload,
        adapter_payload=adapter_payload,
        matrix=result_payload.get("matrix", []),
    )

    if active_waivers and promotion_status == "waived_promoted":
        operator_summary.append("Scoped waiver applied: one or more required real-device lanes remain waived, not satisfied.")

    body = {
        "contract_version": PROMOTION_CONTRACT_VERSION,
        "generated_at": utc_now(),
        "evaluator_version": RUNNER_VERSION,
        "run_id": str(result_payload["run_id"]),
        "scenario_id": str(scenario_payload["scenario_id"]),
        "repo_id": str(result_payload["repo_id"]),
        "criticality": str(scenario_payload["criticality"]),
        "promotion_status": promotion_status,
        "evidence_profile": evidence_profile,
        "highest_satisfied_tier": highest_satisfied_tier,
        "satisfied_evidence_tiers": satisfied_evidence_tiers,
        "missing_evidence_tiers": missing_evidence_tiers,
        "manual_required_lanes": manual_required_lanes,
        "waived_lanes": waived_lanes,
        "waiver_refs": waiver_refs,
        "waiver_reasons": waiver_reasons,
        "decision": decision,
        "summary": {
            "executable_truth": executable_truth,
            "artifact_coverage": artifact_coverage,
            "real_device_proof": real_device_proof,
            "visual_status": visual_status,
            "test_evidence_status": test_evidence_status,
            "evidence_profile": evidence_profile,
            "governance_status": str(governance["status"]),
            "flake_status": "none",
        },
        "blocking_reasons": blocking_reasons,
        "manual_gaps": manual_gaps,
        "governance": governance,
        "source_refs": {
            "scenario_ref": atlas_relative(scenario_target, root=base_root),
            "result_ref": atlas_relative(result_path.resolve(), root=base_root),
            "artifact_refs": [atlas_relative(artifact_path.resolve(), root=base_root)],
        },
        "operator_summary": operator_summary,
        "receipt_origin": build_receipt_origin(
            root=base_root,
            runner_version=RUNNER_VERSION,
            repo_id=str(result_payload["repo_id"]),
            git_sha=str(result_payload["git_sha"]),
            command="python ops/atlas/qa/promote_run.py",
        ),
    }
    promotion = payload_with_digest(body, "promotion_id")
    payload_errors = validate_promotion_payload(promotion)
    if payload_errors:
        raise ValueError("; ".join(payload_errors))

    target = output_file.resolve() if isinstance(output_file, Path) else result_path.with_name("promotion.record.json")
    write_manifest(target, promotion)
    return promotion | {"output_ref": atlas_relative(target, root=base_root)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit an ATLAS QA promotion record.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--result-file", type=Path)
    parser.add_argument("--artifact-file", type=Path)
    parser.add_argument("--run")
    parser.add_argument("--scenario-file", type=Path)
    parser.add_argument("--stack-validation-file", type=Path)
    parser.add_argument("--output-file", type=Path)
    args = parser.parse_args(argv)

    result = promote_run(
        root=args.root.resolve(),
        result_path=args.result_file.resolve() if isinstance(args.result_file, Path) else None,
        artifact_path=args.artifact_file.resolve() if isinstance(args.artifact_file, Path) else None,
        run_id=args.run,
        scenario_path=args.scenario_file.resolve() if isinstance(args.scenario_file, Path) else None,
        stack_validation_path=args.stack_validation_file.resolve() if isinstance(args.stack_validation_file, Path) else None,
        output_file=args.output_file.resolve() if isinstance(args.output_file, Path) else None,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["promotion_status"] in {"promoted_emulated", "promoted_physical", "promoted_physical_manual", "manual_review", "dry_run", "waived_promoted"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
