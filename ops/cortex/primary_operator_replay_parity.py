from __future__ import annotations

"""Offline replay parity for the Cortex primary-operator boundary."""

import argparse
import hashlib
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any

from ops.cortex.primary_operator import build_decision, validate_input_path, validate_output_path

REPORT_SCHEMA = "atlas.cortex.primary_operator_replay_parity_report.v1"
ADAPTER_SCHEMA = "atlas.cortex.primary_operator_adapter_projection.v1"
CONTRACT_VERSION = "atlas.cortex.primary_operator_replay_parity_contract.v1"
STATE_RANK = {"accepted": 0, "blocked": 1, "rejected": 2}
FORBIDDEN_ADAPTER_ACTIONS = {
    "deploy", "production_deploy", "push", "merge", "pull_request",
    "discord_write", "board_write", "database_mutation", "external_mutation",
}


def atlas_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return OrderedDict((str(key), _canonical(value[key])) for key in sorted(value, key=str))
    if isinstance(value, list):
        values = [_canonical(item) for item in value]
        return sorted(values, key=lambda item: json.dumps(item, ensure_ascii=False, separators=(",", ":")))
    return value


def _digest(value: Any) -> str:
    encoded = json.dumps(_canonical(value), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _finding(code: str, detail: str, **extra: Any) -> OrderedDict[str, Any]:
    return OrderedDict((("code", code), ("detail", detail), *sorted(extra.items())))


def _reason_codes(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    result: set[str] = set()
    for item in value:
        if isinstance(item, dict) and isinstance(item.get("code"), str):
            result.add(item["code"])
        elif isinstance(item, str):
            result.add(item)
    return result


def _read_json(root: Path, argument: str) -> tuple[dict[str, Any] | None, OrderedDict[str, Any] | None, str | None]:
    path, error = validate_input_path(root, argument)
    if error:
        return None, error, None
    assert path is not None
    try:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, _finding("invalid_json", "Input must be valid UTF-8 JSON.", path=argument, exception=str(exc)), None
    if not isinstance(value, dict):
        return None, _finding("invalid_json_shape", "Input JSON must be an object.", path=argument), None
    return value, None, hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _adapter_actions(adapter: dict[str, Any]) -> set[str]:
    raw = adapter.get("external_action_authority", [])
    if isinstance(raw, list):
        return {str(item).strip().lower() for item in raw}
    if isinstance(raw, dict):
        return {str(key).strip().lower() for key, enabled in raw.items() if enabled is True}
    return set()


def build_report(
    *,
    plan: dict[str, Any],
    authority: dict[str, Any],
    leases: dict[str, Any],
    truth: dict[str, Any],
    adapter: dict[str, Any] | None = None,
    source_digests: list[OrderedDict[str, str]] | None = None,
) -> OrderedDict[str, Any]:
    acceptance, receipt = build_decision(plan=plan, authority=authority, leases=leases, truth=truth)
    mode = "optional_adapter_projection" if adapter is not None else "internal_no_adapter"
    comparisons: list[OrderedDict[str, Any]] = []
    regressions: list[OrderedDict[str, Any]] = []
    mismatches: list[OrderedDict[str, Any]] = []
    result_class = "equivalent"

    if acceptance["state"] != "accepted":
        result_class = "blocked"

    if adapter is not None:
        if adapter.get("schema_version") != ADAPTER_SCHEMA:
            mismatches.append(_finding("invalid_adapter_schema", "Adapter projection schema is not admitted."))
        adapter_state = adapter.get("acceptance_state")
        internal_state = acceptance["state"]
        comparisons.append(OrderedDict((("dimension", "acceptance_state"), ("internal", internal_state), ("adapter", adapter_state))))
        if adapter_state not in STATE_RANK:
            mismatches.append(_finding("invalid_adapter_state", "Adapter acceptance state is unavailable."))
        elif STATE_RANK[str(internal_state)] > STATE_RANK[str(adapter_state)]:
            result_class = "cortex_stricter"
        elif STATE_RANK[str(adapter_state)] > STATE_RANK[str(internal_state)]:
            result_class = "adapter_stricter"

        internal_reasons = _reason_codes(acceptance["reasons"])
        adapter_reasons = _reason_codes(adapter.get("reason_codes", []))
        comparisons.append(OrderedDict((("dimension", "reason_codes"), ("internal", sorted(internal_reasons)), ("adapter", sorted(adapter_reasons)))))
        if internal_reasons > adapter_reasons:
            result_class = "cortex_stricter"
        elif adapter_reasons > internal_reasons and result_class == "equivalent":
            result_class = "adapter_stricter"
        elif internal_reasons != adapter_reasons and not (internal_reasons > adapter_reasons or adapter_reasons > internal_reasons):
            mismatches.append(_finding("reason_code_mismatch", "Internal and adapter reason codes are incompatible."))

        if adapter.get("plan_id") != acceptance["plan_id"]:
            mismatches.append(_finding("plan_identity_mismatch", "Adapter projection does not preserve the plan identity."))
        correlation = adapter.get("receipt_correlation")
        if not isinstance(correlation, dict) or correlation.get("plan_id") != acceptance["plan_id"] or correlation.get("acceptance_id") != acceptance["acceptance_id"]:
            mismatches.append(_finding("receipt_correlation_mismatch", "Adapter projection does not preserve acceptance and plan correlation."))

        actions = sorted(action for action in _adapter_actions(adapter) if action in FORBIDDEN_ADAPTER_ACTIONS or action.endswith("_mutation"))
        if actions:
            regressions.append(_finding("adapter_authority_widening", "Adapter projection grants prohibited external authority.", actions=actions))
        if adapter.get("runtime_dispatch") is not False:
            regressions.append(_finding("adapter_dispatch_claim", "Adapter projection must explicitly deny runtime dispatch."))
        if adapter.get("mutation_performed") is not False:
            regressions.append(_finding("adapter_mutation_claim", "Adapter projection must explicitly deny mutation."))
        if adapter.get("operator_plane") != "_stack":
            regressions.append(_finding("operator_plane_replacement", "Adapter projection must preserve _stack as the operator plane."))
        if adapter.get("external_adapters_required") is not False:
            regressions.append(_finding("adapter_dependency_claim", "External adapters must remain optional."))

        if regressions:
            result_class = "authority_regression"
        elif mismatches:
            result_class = "mismatch"

    safe = result_class in {"equivalent", "adapter_stricter"} and acceptance["state"] == "accepted"
    seed = OrderedDict(
        (("contract_version", CONTRACT_VERSION), ("acceptance", acceptance), ("receipt", receipt),
         ("adapter", adapter), ("source_digests", source_digests or []))
    )
    return OrderedDict(
        (("schema_version", REPORT_SCHEMA), ("report_id", "parity-" + _digest(seed)[:20]),
         ("replay_mode", mode), ("plan_id", acceptance["plan_id"]),
         ("source_digests", sorted(source_digests or [], key=lambda item: item["path"])),
         ("internal_baseline", OrderedDict((("acceptance", acceptance), ("receipt", receipt)))),
         ("adapter_projection", _canonical(adapter) if adapter is not None else None),
         ("comparisons", comparisons), ("authority_regressions", regressions),
         ("mismatches", mismatches), ("result_class", result_class),
         ("external_adapters_required", False), ("operator_plane", "_stack"),
         ("runtime_dispatch", False), ("mutation_performed", False),
         ("safe_to_use", safe),
         ("next_action", "replay_parity_complete" if safe else "resolve_replay_parity_findings")))


def exit_code(report: dict[str, Any]) -> int:
    return 0 if report.get("safe_to_use") is True else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare primary-operator decisions with an optional adapter projection.")
    parser.add_argument("--execution-plan", required=True)
    parser.add_argument("--authority-envelope", required=True)
    parser.add_argument("--lease-receipts", required=True)
    parser.add_argument("--truth-digests", required=True)
    parser.add_argument("--adapter-projection")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    root = atlas_root()
    requested = [
        ("plan", args.execution_plan), ("authority", args.authority_envelope),
        ("leases", args.lease_receipts), ("truth", args.truth_digests),
    ]
    if args.adapter_projection:
        requested.append(("adapter", args.adapter_projection))
    values: dict[str, dict[str, Any]] = {}
    errors: list[OrderedDict[str, Any]] = []
    digests: list[OrderedDict[str, str]] = []
    for name, path in requested:
        value, error, digest = _read_json(root, path)
        if error:
            errors.append(error)
        elif value is not None and digest is not None:
            values[name] = value
            digests.append(OrderedDict((("path", path.replace("\\", "/")), ("sha256", digest))))
    if errors:
        report = OrderedDict(
            (("schema_version", REPORT_SCHEMA), ("report_id", "parity-" + _digest(errors)[:20]),
             ("replay_mode", "blocked"), ("plan_id", None), ("source_digests", digests),
             ("internal_baseline", None), ("adapter_projection", None), ("comparisons", []),
             ("authority_regressions", []), ("mismatches", errors), ("result_class", "blocked"),
             ("external_adapters_required", False), ("operator_plane", "_stack"),
             ("runtime_dispatch", False), ("mutation_performed", False), ("safe_to_use", False),
             ("next_action", "resolve_replay_parity_findings")))
    else:
        report = build_report(
            plan=values["plan"], authority=values["authority"], leases=values["leases"],
            truth=values["truth"], adapter=values.get("adapter"), source_digests=digests,
        )
    if args.output:
        output, error = validate_output_path(root, args.output)
        if error:
            report["mismatches"] = sorted(list(report["mismatches"]) + [error], key=lambda item: (item["code"], item["detail"]))
            report["result_class"] = "blocked"
            report["safe_to_use"] = False
            report["next_action"] = "resolve_replay_parity_findings"
        else:
            assert output is not None
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
