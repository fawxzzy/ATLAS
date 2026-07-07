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

from ops._atlas import atlas_root, normalize_slashes
from ops.atlas import reusable_workflow_proof_contract_candidate as candidates

SCHEMA_VERSION = "atlas.proof_contract_candidate_contract.v1"
STATUS_OK = "ok"
STATUS_ADVISORY_GAP = "advisory_gap"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"

SUPPORTED_CANDIDATES = {
    "reusable-workflow-proof-contract",
    "manual-protected-proof-contract",
    "artifact-backed-proof-contract",
}


def _finding(code: str, message: str, *, severity: str = "warning", **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("severity", severity), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _candidate_groups(candidate_report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        *(candidate_report.get("workflow_contract_candidates") or []),
        *(candidate_report.get("manual_dispatch_candidates") or []),
        *(candidate_report.get("artifact_proof_candidates") or []),
    ]


def _candidate_by_id(candidate_report: dict[str, Any], candidate_id: str) -> dict[str, Any] | None:
    for candidate in _candidate_groups(candidate_report):
        if candidate.get("candidate_id") == candidate_id:
            return candidate
    return None


def _base_authority_denials() -> list[str]:
    return [
        "no_workflow_edit",
        "no_workflow_dispatch",
        "no_owner_repo_mutation",
        "no_owner_truth_claim",
        "no_secret_value_access",
        "no_deploy_or_platform_mutation",
        "no_final_receipt_authority",
        "no_marker_movement_authority",
        "no_release_readiness_claim",
        "no_validation_verdict_authority",
    ]


def _contract_for(candidate: dict[str, Any]) -> OrderedDict[str, Any]:
    candidate_id = str(candidate.get("candidate_id") or "")
    if candidate_id == "reusable-workflow-proof-contract":
        trigger_style = "workflow_call_style_contract"
        typed_inputs = [
            "source_ref",
            "caller_ref",
            "target_head_sha",
            "proof_artifact_ref",
            "receipt_ref",
        ]
        permissions = ["contents:read"]
        proof_refs = ["proof_artifact_ref", "receipt_ref"]
        stop_conditions = [
            "workflow_file_edit_required",
            "workflow_dispatch_required",
            "owner_repo_mutation_required",
            "secret_value_required",
            "proof_artifact_missing",
        ]
    elif candidate_id == "manual-protected-proof-contract":
        trigger_style = "workflow_dispatch_style_manual_proof_contract"
        typed_inputs = [
            "target_repo",
            "target_head_sha",
            "manual_attestation_ref",
            "provider_run_id",
            "proof_artifact_ref",
            "receipt_ref",
        ]
        permissions = ["contents:read", "actions:read"]
        proof_refs = ["manual_attestation_ref", "provider_run_id", "proof_artifact_ref", "receipt_ref"]
        stop_conditions = [
            "manual_attestation_missing",
            "provider_run_missing",
            "proof_artifact_missing",
            "secret_value_required",
            "owner_repo_mutation_required",
        ]
    else:
        trigger_style = "artifact_or_receipt_backed_proof_contract"
        typed_inputs = [
            "artifact_ref",
            "artifact_digest",
            "receipt_ref",
            "source_ref",
            "target_head_sha",
        ]
        permissions = ["contents:read", "actions:read"]
        proof_refs = ["artifact_ref", "artifact_digest", "receipt_ref"]
        stop_conditions = [
            "artifact_missing",
            "artifact_digest_missing",
            "receipt_missing",
            "green_ci_without_artifact_or_receipt",
            "owner_repo_mutation_required",
        ]

    return OrderedDict(
        [
            ("candidate_id", candidate_id),
            ("classification", candidate.get("classification")),
            ("proof_kind", candidate.get("proof_kind")),
            ("trigger_style", trigger_style),
            ("typed_inputs", typed_inputs),
            ("secret_names_only", ["BROWSERSTACK_USERNAME", "BROWSERSTACK_ACCESS_KEY"] if candidate_id == "manual-protected-proof-contract" else []),
            ("permissions", permissions),
            ("proof_artifacts_or_receipts", proof_refs),
            ("stop_conditions", stop_conditions),
            ("authority_denials", _base_authority_denials()),
            ("source_refs", candidate.get("source_refs") or []),
            ("authority", "advisory_contract_only"),
        ]
    )


def build_report(*, root: Path, candidate_id: str, source_refs: list[str] | None = None) -> OrderedDict[str, Any]:
    normalized_candidate_id = candidate_id.strip()
    blockers: list[OrderedDict[str, Any]] = []
    warnings: list[OrderedDict[str, Any]] = []
    if normalized_candidate_id not in SUPPORTED_CANDIDATES:
        blockers.append(
            _finding(
                "unsupported_candidate_id",
                "Candidate id is not supported by the advisory proof-contract renderer.",
                severity="blocker",
                candidate_id=normalized_candidate_id,
                supported_candidates=sorted(SUPPORTED_CANDIDATES),
            )
        )

    candidate_report = candidates.build_report(root=root, scope="root", source_refs=list(source_refs or []))
    if candidate_report.get("blockers"):
        blockers.extend(candidate_report["blockers"])

    selected = _candidate_by_id(candidate_report, normalized_candidate_id)
    contract = _contract_for(selected) if selected and not blockers else None
    if selected is None and not blockers:
        warnings.append(
            _finding(
                "candidate_not_found",
                "Requested candidate was not present in reusable proof-contract candidate evidence.",
                candidate_id=normalized_candidate_id,
            )
        )

    status = STATUS_BLOCKER if blockers else (STATUS_OK if contract is not None else STATUS_ADVISORY_GAP)
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("candidate_id", normalized_candidate_id),
            ("candidate_report_schema", candidate_report.get("schema_version")),
            ("candidate_report_status", candidate_report.get("status")),
            ("contract", contract),
            ("playbook_rule_refs", candidate_report.get("playbook_rule_refs") or []),
            ("pattern_refs", candidate_report.get("pattern_refs") or []),
            ("failure_mode_refs", candidate_report.get("failure_mode_refs") or []),
            ("authority_risks", candidate_report.get("authority_risks") or []),
            ("safe_to_continue", not blockers),
            ("root", normalize_slashes(str(root))),
            ("branch", candidate_report.get("branch")),
            ("head", candidate_report.get("head")),
            ("source_refs", candidate_report.get("source_refs") or []),
            ("blockers", blockers),
            ("warnings", warnings),
        ]
    )


def report_exit_code(*, status: str, strict: bool) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_ADVISORY_GAP:
        return 1 if strict else 0
    if status == STATUS_BLOCKER:
        return 2
    return 3


def render_summary(report: dict[str, Any]) -> str:
    contract = report.get("contract") or {}
    return "\n".join(
        [
            f"Status: {report.get('status')}",
            f"Candidate: {report.get('candidate_id')}",
            f"Trigger style: {contract.get('trigger_style') or 'none'}",
            f"Safe to continue: {str(report.get('safe_to_continue')).lower()}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render advisory proof-contracts from reusable workflow proof-contract candidates.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--candidate-id", default="artifact-backed-proof-contract", help="Candidate id to render.")
    parser.add_argument("--source", action="append", default=[], help="Root-relative admitted source ref. May be repeated.")
    parser.add_argument("--output", help="Optional root-relative tmp/**.json output path.")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root, candidate_id=args.candidate_id, source_refs=list(args.source or []))
        if args.output:
            resolved_output, output_error = candidates.validate_output_path(root=root, output_path=args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKER
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
                report["safe_to_continue"] = False
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
                ("candidate_id", getattr(args, "candidate_id", "")),
                ("candidate_report_schema", candidates.SCHEMA_VERSION),
                ("candidate_report_status", None),
                ("contract", None),
                ("playbook_rule_refs", []),
                ("pattern_refs", []),
                ("failure_mode_refs", []),
                ("authority_risks", []),
                ("safe_to_continue", False),
                ("root", normalize_slashes(str(root))),
                ("branch", None),
                ("head", None),
                ("source_refs", []),
                ("blockers", [_finding("internal_error", "Proof-contract rendering failed.", severity="blocker", exception=str(exc))]),
                ("warnings", []),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
