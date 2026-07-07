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
from ops.atlas import proof_contract_candidate_contract as contracts
from ops.atlas import reusable_workflow_proof_contract_candidate as candidates

SCHEMA_VERSION = "atlas.proof_contract_payload_validator.v1"
STATUS_VALID = "valid"
STATUS_INVALID = "invalid"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"

EXPECTED_CONTRACT_SCHEMA = contracts.SCHEMA_VERSION
REQUIRED_CONTRACT_FIELDS = [
    "candidate_id",
    "classification",
    "proof_kind",
    "trigger_style",
    "typed_inputs",
    "secret_names_only",
    "permissions",
    "proof_artifacts_or_receipts",
    "stop_conditions",
    "authority_denials",
    "source_refs",
    "authority",
]
REQUIRED_AUTHORITY_DENIALS = [
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
FORBIDDEN_SECRET_VALUE_KEYS = {
    "secret_value",
    "secret_values",
    "access_key",
    "access_key_value",
    "browserstack_access_key",
    "browserstack_access_key_value",
    "browserstack_username_value",
}


def _finding(code: str, message: str, *, severity: str = "warning", **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("severity", severity), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _normalized_relative(value: str) -> str:
    return normalize_slashes(value).strip("/")


def validate_input_path(*, root: Path, input_path: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    candidate = Path(input_path)
    if candidate.is_absolute():
        return None, _finding("absolute_input_path", "Input path must be root-relative.", severity="blocker", path=normalize_slashes(str(candidate)))
    relative_path = _normalized_relative(str(candidate))
    if ".." in Path(relative_path).parts:
        return None, _finding("parent_traversal_input_path", "Input path must not use parent traversal.", severity="blocker", path=relative_path)
    if not relative_path.startswith("tmp/") or not relative_path.endswith(".json"):
        return None, _finding("protected_input_path", "Input reads are admitted only from root-relative tmp/**.json.", severity="blocker", path=relative_path)
    resolved = (root / relative_path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_input_path", "Input path must stay inside the ATLAS root.", severity="blocker", path=relative_path)
    if not resolved.exists():
        return None, _finding("missing_input_path", "Input file does not exist.", severity="blocker", path=relative_path)
    return resolved, None


def _load_input_report(*, root: Path, input_path: str) -> tuple[dict[str, Any] | None, list[OrderedDict[str, Any]], str | None]:
    resolved, error = validate_input_path(root=root, input_path=input_path)
    if error is not None:
        return None, [error], None
    assert resolved is not None
    try:
        return json.loads(resolved.read_text(encoding="utf-8")), [], _normalized_relative(input_path)
    except json.JSONDecodeError as exc:
        return None, [_finding("invalid_json_input", "Input file is not valid JSON.", severity="blocker", path=_normalized_relative(input_path), error=str(exc))], _normalized_relative(input_path)


def _field_results(contract: dict[str, Any] | None) -> list[OrderedDict[str, Any]]:
    if contract is None:
        return [
            OrderedDict(
                [
                    ("field", field),
                    ("present", False),
                    ("valid", False),
                    ("reason", "missing_contract"),
                ]
            )
            for field in REQUIRED_CONTRACT_FIELDS
        ]
    results: list[OrderedDict[str, Any]] = []
    for field in REQUIRED_CONTRACT_FIELDS:
        value = contract.get(field)
        present = field in contract
        valid = present
        if field in {"typed_inputs", "secret_names_only", "permissions", "proof_artifacts_or_receipts", "stop_conditions", "authority_denials", "source_refs"}:
            valid = present and isinstance(value, list) and all(isinstance(item, str) and item for item in value)
        elif field in {"candidate_id", "classification", "proof_kind", "trigger_style", "authority"}:
            valid = present and isinstance(value, str) and bool(value.strip())
        results.append(OrderedDict([("field", field), ("present", present), ("valid", valid)]))
    return results


def _authority_results(contract: dict[str, Any] | None) -> list[OrderedDict[str, Any]]:
    denials = set(contract.get("authority_denials") or []) if isinstance(contract, dict) else set()
    return [
        OrderedDict(
            [
                ("denial", denial),
                ("present", denial in denials),
                ("valid", denial in denials),
            ]
        )
        for denial in REQUIRED_AUTHORITY_DENIALS
    ]


def _walk_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.extend(_walk_keys(child))
    return keys


def _secret_boundary(report: dict[str, Any], contract: dict[str, Any] | None) -> OrderedDict[str, Any]:
    secret_names = contract.get("secret_names_only") if isinstance(contract, dict) else None
    name_list_valid = isinstance(secret_names, list) and all(isinstance(name, str) and name for name in secret_names)
    forbidden_keys = sorted({key for key in _walk_keys(report) if key.lower() in FORBIDDEN_SECRET_VALUE_KEYS})
    return OrderedDict(
        [
            ("secret_names_only_present", isinstance(contract, dict) and "secret_names_only" in contract),
            ("secret_names_only_valid", name_list_valid),
            ("forbidden_secret_value_keys", forbidden_keys),
            ("valid", name_list_valid and not forbidden_keys),
        ]
    )


def _ref_results(refs: Any, *, kind: str) -> list[OrderedDict[str, Any]]:
    if not isinstance(refs, list):
        return [OrderedDict([("kind", kind), ("ref", None), ("valid", False), ("reason", "not_a_list")])]
    if not refs:
        return [OrderedDict([("kind", kind), ("ref", None), ("valid", False), ("reason", "empty")])]
    return [
        OrderedDict(
            [
                ("kind", kind),
                ("ref", ref),
                ("valid", isinstance(ref, str) and bool(ref.strip())),
            ]
        )
        for ref in refs
    ]


def validate_report(*, root: Path, report: dict[str, Any], input_ref: str | None = None) -> OrderedDict[str, Any]:
    blockers: list[OrderedDict[str, Any]] = []
    warnings: list[OrderedDict[str, Any]] = []
    contract = report.get("contract") if isinstance(report.get("contract"), dict) else None

    if report.get("schema_version") != EXPECTED_CONTRACT_SCHEMA:
        blockers.append(
            _finding(
                "unexpected_contract_schema",
                "Payload must come from the proof-contract candidate contract renderer.",
                severity="blocker",
                expected=EXPECTED_CONTRACT_SCHEMA,
                actual=report.get("schema_version"),
            )
        )
    if report.get("status") != contracts.STATUS_OK:
        blockers.append(_finding("contract_status_not_ok", "Rendered contract status must be ok.", severity="blocker", actual=report.get("status")))
    if contract is None:
        blockers.append(_finding("missing_contract", "Rendered payload must include a contract object.", severity="blocker"))

    field_results = _field_results(contract)
    authority_results = _authority_results(contract)
    secret_boundary = _secret_boundary(report, contract)
    proof_reference_results = _ref_results(contract.get("proof_artifacts_or_receipts") if contract else None, kind="proof_artifact_or_receipt")
    source_ref_results = _ref_results(contract.get("source_refs") if contract else None, kind="source_ref")

    for result in field_results:
        if not result["valid"]:
            blockers.append(_finding("invalid_contract_field", "Required contract field is missing or invalid.", severity="blocker", field=result["field"]))
    for result in authority_results:
        if not result["valid"]:
            blockers.append(_finding("missing_authority_denial", "Required authority denial is missing.", severity="blocker", denial=result["denial"]))
    if not secret_boundary["valid"]:
        blockers.append(_finding("invalid_secret_boundary", "Contract must expose secret names only and no secret-value fields.", severity="blocker", forbidden_keys=secret_boundary["forbidden_secret_value_keys"]))
    for result in proof_reference_results + source_ref_results:
        if not result["valid"]:
            blockers.append(_finding("invalid_reference", "Contract reference list is missing or invalid.", severity="blocker", kind=result["kind"], ref=result["ref"]))

    status = STATUS_BLOCKER if any(item.get("severity") == "blocker" for item in blockers) else STATUS_VALID
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("candidate_id", report.get("candidate_id")),
            ("contract_schema", report.get("schema_version")),
            ("contract_status", report.get("status")),
            ("required_field_results", field_results),
            ("authority_denial_results", authority_results),
            ("secret_boundary", secret_boundary),
            ("proof_reference_results", proof_reference_results),
            ("source_ref_results", source_ref_results),
            ("safe_to_use", status == STATUS_VALID),
            ("root", normalize_slashes(str(root))),
            ("branch", report.get("branch")),
            ("head", report.get("head")),
            ("input_ref", input_ref),
            ("source_refs", report.get("source_refs") or []),
            ("blockers", blockers),
            ("warnings", warnings),
        ]
    )


def build_report(*, root: Path, candidate_id: str, source_refs: list[str] | None = None, input_path: str | None = None) -> OrderedDict[str, Any]:
    if input_path:
        payload, blockers, input_ref = _load_input_report(root=root, input_path=input_path)
        if blockers:
            return OrderedDict(
                [
                    ("schema_version", SCHEMA_VERSION),
                    ("status", STATUS_BLOCKER),
                    ("candidate_id", None),
                    ("contract_schema", None),
                    ("contract_status", None),
                    ("required_field_results", []),
                    ("authority_denial_results", []),
                    ("secret_boundary", OrderedDict([("valid", False)])),
                    ("proof_reference_results", []),
                    ("source_ref_results", []),
                    ("safe_to_use", False),
                    ("root", normalize_slashes(str(root))),
                    ("branch", None),
                    ("head", None),
                    ("input_ref", input_ref),
                    ("source_refs", []),
                    ("blockers", blockers),
                    ("warnings", []),
                ]
            )
        assert payload is not None
        return validate_report(root=root, report=payload, input_ref=input_ref)
    rendered = contracts.build_report(root=root, candidate_id=candidate_id, source_refs=list(source_refs or []))
    return validate_report(root=root, report=rendered, input_ref=None)


def report_exit_code(*, status: str, strict: bool) -> int:
    if status == STATUS_VALID:
        return 0
    if status in {STATUS_INVALID, STATUS_BLOCKER}:
        return 1 if strict else 2
    return 3


def render_summary(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Status: {report.get('status')}",
            f"Candidate: {report.get('candidate_id') or 'none'}",
            f"Safe to use: {str(report.get('safe_to_use')).lower()}",
            f"Blockers: {len(report.get('blockers') or [])}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate advisory proof-contract payloads emitted by the proof-contract renderer.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--candidate-id", default="artifact-backed-proof-contract", help="Candidate id to render and validate when --input is omitted.")
    parser.add_argument("--source", action="append", default=[], help="Root-relative admitted source ref. May be repeated.")
    parser.add_argument("--input", help="Optional root-relative tmp/**.json rendered contract report to validate.")
    parser.add_argument("--output", help="Optional root-relative tmp/**.json validation report output path.")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root, candidate_id=args.candidate_id, source_refs=list(args.source or []), input_path=args.input)
        if args.output:
            resolved_output, output_error = candidates.validate_output_path(root=root, output_path=args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKER
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
                report["safe_to_use"] = False
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
                ("contract_schema", None),
                ("contract_status", None),
                ("required_field_results", []),
                ("authority_denial_results", []),
                ("secret_boundary", OrderedDict([("valid", False)])),
                ("proof_reference_results", []),
                ("source_ref_results", []),
                ("safe_to_use", False),
                ("root", normalize_slashes(str(root))),
                ("branch", None),
                ("head", None),
                ("input_ref", getattr(args, "input", None)),
                ("source_refs", []),
                ("blockers", [_finding("internal_error", "Proof-contract payload validation failed.", severity="blocker", exception=str(exc))]),
                ("warnings", []),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
