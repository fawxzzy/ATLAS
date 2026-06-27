from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

COMPARISON_FIELDS = (
    "payload.mode",
    "payload.status",
    "payload.observations",
)
ALLOWED_OUTCOMES = {
    "equal_on_boundary",
    "unequal_on_boundary",
    "not_admissible",
}
ALLOWED_REASONS = {
    "report_status_not_not_run",
    "identity_mismatch",
    "oracle_ref_mismatch",
    "missing_boundary_field",
    "unexpected_path_discovery",
    "attempted_verdict_assignment",
    "attempted_report_mutation",
}


def _normalized_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _dedup_reasons(reasons: list[str]) -> list[str]:
    deduped: list[str] = []
    for reason in reasons:
        if reason not in ALLOWED_REASONS or reason in deduped:
            continue
        deduped.append(reason)
    return deduped


def _load_mapping(path_ref: str) -> tuple[dict[str, Any], bool]:
    try:
        loaded = json.loads(Path(path_ref).read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}, False
    if not isinstance(loaded, Mapping):
        return {}, False
    return dict(loaded), True


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _normalized_observations(value: Any) -> tuple[list[str], bool]:
    if not isinstance(value, list):
        return [], False

    observations: list[str] = []
    for item in value:
        if not isinstance(item, str):
            return [], False
        observations.append(item.strip())
    return observations, True


def _boundary_payload(value: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
    payload = _mapping(value.get("payload"))
    mode = payload.get("mode")
    status = payload.get("status")
    observations, observations_ok = _normalized_observations(payload.get("observations"))
    if not isinstance(mode, str) or not isinstance(status, str) or not observations_ok:
        return {}, False

    return {
        "mode": mode.strip(),
        "status": status.strip(),
        "observations": observations,
    }, True


def _result_payload(
    validator_ref: str,
    report_ref: str,
    candidate_output_ref: str,
    oracle_ref: str,
    report_status: str,
    comparison_outcome: str,
    comparison_reasons: list[str],
) -> dict[str, Any]:
    outcome = comparison_outcome if comparison_outcome in ALLOWED_OUTCOMES else "not_admissible"
    reasons = _dedup_reasons(comparison_reasons)
    return {
        "validator_ref": validator_ref,
        "report_ref": report_ref,
        "candidate_output_ref": candidate_output_ref,
        "oracle_ref": oracle_ref,
        "report_status": report_status,
        "compared_fields": list(COMPARISON_FIELDS),
        "comparison_outcome": outcome,
        "comparison_reasons": reasons,
    }


def evaluate_sandbox_validator_behavior(
    validator_ref: str,
    report_ref: str,
    candidate_output_ref: str,
    oracle_ref: str,
) -> dict[str, Any]:
    validator_ref = _normalized_text(validator_ref)
    report_ref = _normalized_text(report_ref)
    candidate_output_ref = _normalized_text(candidate_output_ref)
    oracle_ref = _normalized_text(oracle_ref)

    validator, validator_ok = _load_mapping(validator_ref)
    report, report_ok = _load_mapping(report_ref)
    candidate_output, candidate_ok = _load_mapping(candidate_output_ref)
    expected_output, oracle_ok = _load_mapping(oracle_ref)

    report_status = _normalized_text(_mapping(report.get("result")).get("status"))

    if not all((validator_ok, report_ok, candidate_ok, oracle_ok)):
        return _result_payload(
            validator_ref,
            report_ref,
            candidate_output_ref,
            oracle_ref,
            report_status,
            "not_admissible",
            ["unexpected_path_discovery"],
        )

    if report_status != "not_run":
        return _result_payload(
            validator_ref,
            report_ref,
            candidate_output_ref,
            oracle_ref,
            report_status,
            "not_admissible",
            ["report_status_not_not_run"],
        )

    validator_id = _normalized_text(validator.get("validator_id"))
    validator_scenario_id = _normalized_text(validator.get("scenario_id"))
    report_validator_id = _normalized_text(report.get("validator_id"))
    report_scenario_id = _normalized_text(report.get("scenario_id"))
    report_run_id = _normalized_text(report.get("run_id"))
    candidate_validator_id = _normalized_text(candidate_output.get("validator_id"))
    candidate_scenario_id = _normalized_text(candidate_output.get("scenario_id"))
    candidate_run_id = _normalized_text(candidate_output.get("run_id"))
    report_validator_ref = _normalized_text(report.get("validator_ref"))
    candidate_validator_ref = _normalized_text(candidate_output.get("validator_ref"))

    identity_mismatch = (
        not validator_id
        or not validator_scenario_id
        or not report_run_id
        or not candidate_run_id
        or report_validator_id != validator_id
        or candidate_validator_id != validator_id
        or report_scenario_id != validator_scenario_id
        or candidate_scenario_id != validator_scenario_id
        or candidate_run_id != report_run_id
        or report_validator_ref != validator_ref
        or candidate_validator_ref != validator_ref
    )
    if identity_mismatch:
        return _result_payload(
            validator_ref,
            report_ref,
            candidate_output_ref,
            oracle_ref,
            report_status,
            "not_admissible",
            ["identity_mismatch"],
        )

    if _normalized_text(candidate_output.get("oracle_ref")) != oracle_ref:
        return _result_payload(
            validator_ref,
            report_ref,
            candidate_output_ref,
            oracle_ref,
            report_status,
            "not_admissible",
            ["oracle_ref_mismatch"],
        )

    candidate_payload, candidate_payload_ok = _boundary_payload(candidate_output)
    expected_payload, expected_payload_ok = _boundary_payload(expected_output)
    if not candidate_payload_ok or not expected_payload_ok:
        return _result_payload(
            validator_ref,
            report_ref,
            candidate_output_ref,
            oracle_ref,
            report_status,
            "not_admissible",
            ["missing_boundary_field"],
        )

    comparison_outcome = (
        "equal_on_boundary"
        if candidate_payload == expected_payload
        else "unequal_on_boundary"
    )
    return _result_payload(
        validator_ref,
        report_ref,
        candidate_output_ref,
        oracle_ref,
        report_status,
        comparison_outcome,
        [],
    )
