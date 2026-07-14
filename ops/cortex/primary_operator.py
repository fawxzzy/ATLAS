from __future__ import annotations

"""Deterministic dry-run acceptance for Cortex execution plans.

The primary operator is an admission boundary, not an execution backend. It
reads explicit local JSON, decides whether a plan is admissible, and can write
one correlated dry-run receipt under ``tmp/atlas``. It never invokes _stack or
performs a platform, Git, network, or owner-repository mutation.
"""

import argparse
import hashlib
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any

PLAN_SCHEMA = "atlas.cortex.execution_plan.v1"
ACCEPTANCE_SCHEMA = "atlas.cortex.primary_operator_acceptance.v1"
RECEIPT_SCHEMA = "atlas.cortex.primary_operator_receipt.v1"
CONTRACT_VERSION = "atlas.cortex.primary_operator_acceptance_receipt_contract.v1"
NO_RUNTIME_DISPATCH = "no_runtime_dispatch"

FORBIDDEN_AUTHORITY = {
    "deploy",
    "production_deploy",
    "push",
    "merge",
    "pull_request",
    "discord_write",
    "board_write",
    "database_mutation",
    "external_mutation",
}
PROTECTED_PARTS = {"repos", "runtime", "secrets", ".codex", ".vercel", "archive", "archives"}
FORBIDDEN_PATH_TERMS = ("credential", "secret", "token", "browser-profile", "private-reasoning")


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


def _path_error(argument: str, *, output: bool = False) -> str | None:
    normalized = argument.replace("\\", "/")
    candidate = Path(argument)
    parts = [part.lower() for part in normalized.split("/") if part not in ("", ".")]
    if candidate.is_absolute() or (len(argument) > 1 and argument[1] == ":"):
        return "absolute_output_path" if output else "absolute_input_path"
    if ".." in parts:
        return "parent_traversal"
    if any(part in PROTECTED_PARTS or part.startswith(".env") for part in parts):
        return "protected_path"
    if any(term in normalized.lower() for term in FORBIDDEN_PATH_TERMS):
        return "forbidden_source_class"
    return None


def validate_input_path(root: Path, argument: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    error = _path_error(argument)
    normalized = argument.replace("\\", "/")
    if error:
        return None, _finding(error, "Input path is not admitted.", path=argument)
    if not normalized.endswith(".json") or not (normalized.startswith("docs/") or normalized.startswith("tmp/atlas/")):
        return None, _finding("unadmitted_input_path", "Input must be explicit docs or tmp/atlas JSON.", path=argument)
    candidate = root / Path(argument)
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return None, _finding("parent_traversal", "Input escapes the Atlas root.", path=argument)
    if not candidate.is_file():
        return None, _finding("missing_input", "Explicit input does not exist.", path=argument)
    return candidate, None


def validate_output_path(root: Path, argument: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    error = _path_error(argument, output=True)
    normalized = argument.replace("\\", "/")
    if error:
        return None, _finding(error, "Output path is not admitted.", path=argument)
    if not normalized.startswith("tmp/atlas/") or not normalized.endswith(".json"):
        return None, _finding("unadmitted_output_path", "Output must be explicit tmp/atlas JSON.", path=argument)
    candidate = root / Path(argument)
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return None, _finding("parent_traversal", "Output escapes the Atlas root.", path=argument)
    return candidate, None


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


def _actions(authority: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for field in ("allowed_actions", "external_actions", "grants"):
        raw = authority.get(field, [])
        if isinstance(raw, list):
            values.update(str(item).strip().lower() for item in raw)
    for field in ("external_mutation_authority", "production_deploy_authority", "push_authority", "discord_write_authority"):
        if authority.get(field) is True:
            values.add(field.removesuffix("_authority"))
    return values


def _source_digests(plan: dict[str, Any], inputs: list[tuple[str, str | None]]) -> list[OrderedDict[str, str]]:
    values = [OrderedDict((("path", path), ("sha256", digest))) for path, digest in inputs if digest]
    declared = plan.get("source_digests", [])
    if isinstance(declared, list):
        for item in declared:
            if isinstance(item, dict):
                path = item.get("path") or item.get("source")
                digest = item.get("sha256") or item.get("digest")
                if isinstance(path, str) and isinstance(digest, str):
                    values.append(OrderedDict((("path", path.replace("\\", "/")), ("sha256", digest))))
    unique = {(item["path"], item["sha256"]): item for item in values}
    return [unique[key] for key in sorted(unique)]


def _build_receipt(acceptance: OrderedDict[str, Any]) -> OrderedDict[str, Any]:
    receipt_id = "receipt-" + _digest(
        OrderedDict((("contract_version", CONTRACT_VERSION), ("acceptance", acceptance)))
    )[:20]
    state = str(acceptance["state"])
    return OrderedDict(
        (("schema_version", RECEIPT_SCHEMA), ("receipt_id", receipt_id),
         ("acceptance_id", acceptance["acceptance_id"]), ("plan_id", acceptance["plan_id"]),
         ("status", "completed" if state == "accepted" else "failed"),
         ("acceptance_state", state), ("runtime_dispatch", False), ("mutation_performed", False),
         ("execution_backend", None), ("operator_plane", "_stack"),
         ("external_adapters_required", False), ("correlated_result", True),
         ("reasons", acceptance["reasons"])))


def build_decision(
    *,
    plan: dict[str, Any],
    authority: dict[str, Any],
    leases: dict[str, Any],
    truth: dict[str, Any],
    input_digests: list[tuple[str, str | None]] | None = None,
) -> tuple[OrderedDict[str, Any], OrderedDict[str, Any]]:
    rejected: list[OrderedDict[str, Any]] = []
    blocked: list[OrderedDict[str, Any]] = []
    warnings: list[OrderedDict[str, Any]] = []

    if plan.get("schema_version") != PLAN_SCHEMA:
        rejected.append(_finding("invalid_plan_schema", "Only atlas.cortex.execution_plan.v1 is admitted."))
    if not isinstance(plan.get("plan_id"), str) or not plan.get("plan_id"):
        rejected.append(_finding("missing_plan_id", "Plan identity is required."))
    if plan.get("safe_to_admit") is not True:
        rejected.append(_finding("unsafe_plan", "Plan must explicitly be safe_to_admit."))
    if plan.get("plan_status") != "ready_for_admission":
        blocked.append(_finding("plan_not_ready", "Plan status must be ready_for_admission."))
    if plan.get("blocked_reasons"):
        blocked.append(_finding("plan_has_blockers", "Plan carries unresolved blocked reasons."))

    requested = _actions(authority)
    widened = sorted(action for action in requested if action in FORBIDDEN_AUTHORITY or action.endswith("_mutation"))
    if widened:
        rejected.append(_finding("authority_widening_rejected", "Dry-run acceptance cannot grant external authority.", actions=widened))
    if authority.get("runtime_dispatch") is True:
        rejected.append(_finding("runtime_dispatch_rejected", "First implementation cannot dispatch runtime work."))

    if truth.get("fresh") is not True or truth.get("stale") is True:
        blocked.append(_finding("stale_truth", "Current root truth must be explicitly fresh."))
    digests = truth.get("digests")
    if not isinstance(digests, list) or not digests:
        blocked.append(_finding("missing_truth_digests", "At least one current root truth digest is required."))

    conflicts = leases.get("conflicts", [])
    if not isinstance(conflicts, list):
        blocked.append(_finding("invalid_lease_receipts", "Lease conflicts must be an array."))
    elif conflicts:
        blocked.append(_finding("resource_lease_conflict", "A current resource lease conflicts with the plan.", conflicts=_canonical(conflicts)))
    if leases.get("current") is not True:
        blocked.append(_finding("stale_lease_receipts", "Resource lease receipts must be current."))

    adapters = authority.get("external_adapters", [])
    if adapters is None:
        adapters = []
    if not isinstance(adapters, list):
        rejected.append(_finding("invalid_external_adapters", "External adapters must be an array when supplied."))
        adapters = []

    state = "rejected" if rejected else "blocked" if blocked else "accepted"
    reasons = sorted(rejected + blocked, key=lambda item: (item["code"], item["detail"]))
    normalized_inputs = OrderedDict(
        (("contract_version", CONTRACT_VERSION), ("plan", plan), ("authority", authority), ("leases", leases), ("truth", truth))
    )
    acceptance_id = "acceptance-" + _digest(normalized_inputs)[:20]
    acceptance = OrderedDict(
        (("schema_version", ACCEPTANCE_SCHEMA), ("acceptance_id", acceptance_id),
         ("plan_id", plan.get("plan_id")), ("state", state),
         ("source_digests", _source_digests(plan, input_digests or [])),
         ("external_adapters", sorted(str(item) for item in adapters)),
         ("external_adapters_required", False), ("runtime_dispatch", False),
         ("operator_plane", "_stack"), ("reasons", reasons), ("warnings", warnings),
         ("safe_to_dispatch", False), ("next_action", "dry_run_acceptance_complete" if state == "accepted" else "resolve_acceptance_blockers"))
    )
    return acceptance, _build_receipt(acceptance)


def exit_code(state: str) -> int:
    return 0 if state == "accepted" else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a Cortex plan at the dry-run primary-operator boundary.")
    parser.add_argument("--execution-plan", required=True)
    parser.add_argument("--authority-envelope", required=True)
    parser.add_argument("--lease-receipts", required=True)
    parser.add_argument("--truth-digests", required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    root = atlas_root()
    named = [
        ("plan", args.execution_plan), ("authority", args.authority_envelope),
        ("leases", args.lease_receipts), ("truth", args.truth_digests),
    ]
    values: dict[str, dict[str, Any]] = {}
    input_digests: list[tuple[str, str | None]] = []
    errors: list[OrderedDict[str, Any]] = []
    for name, path in named:
        value, error, digest = _read_json(root, path)
        if error:
            errors.append(error)
        elif value is not None:
            values[name] = value
            input_digests.append((path.replace("\\", "/"), digest))
    if errors:
        placeholder = {"schema_version": PLAN_SCHEMA, "plan_id": None, "safe_to_admit": False, "plan_status": "blocked"}
        acceptance, _ = build_decision(plan=placeholder, authority={}, leases={}, truth={}, input_digests=input_digests)
        acceptance["reasons"] = sorted(errors, key=lambda item: (item["code"], item["detail"]))
        acceptance["state"] = "rejected"
        receipt = _build_receipt(acceptance)
    else:
        acceptance, receipt = build_decision(
            plan=values["plan"], authority=values["authority"], leases=values["leases"],
            truth=values["truth"], input_digests=input_digests,
        )
    payload = OrderedDict((("acceptance", acceptance), ("receipt", receipt)))
    if args.output:
        output, error = validate_output_path(root, args.output)
        if error:
            acceptance["state"] = "rejected"
            acceptance["reasons"] = sorted(list(acceptance["reasons"]) + [error], key=lambda item: (item["code"], item["detail"]))
            receipt = _build_receipt(acceptance)
            payload["receipt"] = receipt
        else:
            assert output is not None
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return exit_code(str(acceptance["state"]))


if __name__ == "__main__":
    raise SystemExit(main())
