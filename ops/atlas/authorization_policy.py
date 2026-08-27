from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = ROOT / "docs" / "registry" / "ATLAS-AUTHORIZATION-POLICY.v1.json"
DEFAULT_REGISTRY = ROOT / "runtime" / "atlas" / "authorization" / "learned-registry.json"
SCHEMA = "atlas.learned-authorization-registry.v1"
SAFE_TOKEN = re.compile(r"^[A-Za-z0-9._:/@+-]+$")


class AuthorizationPolicyError(ValueError):
    pass


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(payload: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical_bytes(payload)).hexdigest()}"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AuthorizationPolicyError(f"Unable to read JSON {path}: {error}") from error
    if not isinstance(payload, dict):
        raise AuthorizationPolicyError(f"Expected JSON object at {path}")
    return payload


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def load_policy(path: Path | None = None) -> dict[str, Any]:
    policy = _load_json(path or DEFAULT_POLICY)
    if policy.get("schema") != "atlas.authorization-policy.v1":
        raise AuthorizationPolicyError("Unsupported authorization policy schema")
    threshold = policy.get("learning", {}).get("minimum_matching_approvals")
    if not isinstance(threshold, int) or threshold < 2:
        raise AuthorizationPolicyError("minimum_matching_approvals must be an integer >= 2")
    return policy


def empty_registry() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "registry_version": 1,
        "applied_event_ids": [],
        "applied_event_digests": {},
        "entries": [],
        "operator_authorization_consumptions": {},
    }


def load_registry(path: Path | None = None) -> dict[str, Any]:
    registry_path = path or DEFAULT_REGISTRY
    if not registry_path.exists():
        return empty_registry()
    registry = _load_json(registry_path)
    if registry.get("schema") != SCHEMA:
        raise AuthorizationPolicyError("Unsupported learned authorization registry schema")
    if not isinstance(registry.get("entries"), list) or not isinstance(registry.get("applied_event_ids"), list):
        raise AuthorizationPolicyError("Malformed learned authorization registry")
    applied_event_digests = registry.get("applied_event_digests")
    if applied_event_digests is None:
        registry["applied_event_digests"] = {}
    elif (
        not isinstance(applied_event_digests, dict)
        or any(
            not isinstance(event_id, str)
            or not isinstance(digest, str)
            or not digest.startswith("sha256:")
            for event_id, digest in applied_event_digests.items()
        )
        or any(event_id not in registry["applied_event_ids"] for event_id in applied_event_digests)
    ):
        raise AuthorizationPolicyError("Malformed learned authorization registry")
    consumptions = registry.get("operator_authorization_consumptions")
    if consumptions is None:
        registry["operator_authorization_consumptions"] = {}
    elif not isinstance(consumptions, dict) or any(
        not isinstance(key, str) or not isinstance(value, dict)
        for key, value in consumptions.items()
    ):
        raise AuthorizationPolicyError("Malformed operator authorization consumptions")
    return registry


@contextmanager
def _exclusive_registry_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(f".{path.name}.lock")
    with lock_path.open("a+b") as lock_file:
        lock_file.seek(0, os.SEEK_END)
        if lock_file.tell() == 0:
            lock_file.write(b"0")
            lock_file.flush()
        lock_file.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            lock_file.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _require_token(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip() or not SAFE_TOKEN.fullmatch(value.strip()):
        raise AuthorizationPolicyError(f"{field} must be a non-empty stable token")
    return value.strip()


def _constraints_digest(payload: dict[str, Any]) -> str:
    constraints = payload.get("constraints")
    if not isinstance(constraints, dict) or not constraints:
        raise AuthorizationPolicyError("constraints must be a non-empty object")
    return _digest(constraints)


def _entry_key(action_class: str, scope_key: str, constraints_digest: str) -> str:
    return f"{action_class}|{scope_key}|{constraints_digest}"


def _risk_flags(payload: dict[str, Any]) -> dict[str, bool]:
    flags = payload.get("risk_flags", {})
    if not isinstance(flags, dict):
        raise AuthorizationPolicyError("risk_flags must be an object")
    invalid = [name for name, value in flags.items() if not isinstance(name, str) or not isinstance(value, bool)]
    if invalid:
        raise AuthorizationPolicyError("risk_flags values must be booleans")
    return flags


def record_operator_decision(
    registry: dict[str, Any],
    decision: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    updated = deepcopy(registry)
    event_id = _require_token(decision, "event_id")
    decision_digest = _digest(decision)
    applied_event_digests = updated.setdefault("applied_event_digests", {})
    if not isinstance(applied_event_digests, dict):
        raise AuthorizationPolicyError("Malformed learned authorization registry")
    if event_id in updated["applied_event_ids"]:
        recorded_digest = applied_event_digests.get(event_id)
        if recorded_digest == decision_digest:
            return updated
        if recorded_digest is None:
            raise AuthorizationPolicyError(
                "Decision event identity cannot be verified for a legacy applied event"
            )
        raise AuthorizationPolicyError("Decision event ID was reused with different content")

    action_class = _require_token(decision, "action_class")
    scope_key = _require_token(decision, "scope_key")
    outcome = _require_token(decision, "outcome").upper()
    if outcome not in {"APPROVE", "DENY", "MODIFY"}:
        raise AuthorizationPolicyError("outcome must be APPROVE, DENY, or MODIFY")
    constraints_digest = _constraints_digest(decision)
    key = _entry_key(action_class, scope_key, constraints_digest)
    entries = {str(entry.get("entry_key")): entry for entry in updated["entries"] if isinstance(entry, dict)}
    entry = deepcopy(
        entries.get(
            key,
            {
                "entry_key": key,
                "action_class": action_class,
                "scope_key": scope_key,
                "constraints_digest": constraints_digest,
                "matching_approval_count": 0,
                "approval_event_ids": [],
                "state": "CANDIDATE",
            },
        )
    )

    never_learn = set(policy["never_learn_risk_flags"])
    risky = sorted(name for name, value in _risk_flags(decision).items() if value and name in never_learn)
    allowlisted = action_class in policy["allowlisted_action_classes"]
    threshold = int(policy["learning"]["minimum_matching_approvals"])

    if outcome in {"DENY", "MODIFY"}:
        decision_time = decision.get("decided_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        for existing_entry in entries.values():
            if (
                existing_entry.get("action_class") == action_class
                and existing_entry.get("scope_key") == scope_key
                and existing_entry.get("state") in {"ACTIVE", "CANDIDATE"}
            ):
                existing_entry["state"] = "REVOKED"
                existing_entry["matching_approval_count"] = 0
                existing_entry["approval_event_ids"] = []
                existing_entry["last_decision"] = f"SUPERSEDED_BY_{outcome}"
                existing_entry["revoked_by_event_id"] = event_id
                existing_entry["revoked_at"] = decision_time
                existing_entry["updated_at"] = decision_time
        entry["state"] = "REVOKED"
        entry["matching_approval_count"] = 0
        entry["approval_event_ids"] = []
        entry["last_decision"] = outcome
        entry["revoked_by_event_id"] = event_id
        entry["revoked_at"] = decision_time
    elif not allowlisted or risky:
        entry["state"] = "INELIGIBLE"
        entry["last_decision"] = "APPROVE"
        entry["ineligible_reasons"] = [
            *(["action_class_not_allowlisted"] if not allowlisted else []),
            *[f"never_learn_risk:{name}" for name in risky],
        ]
    else:
        entry["approval_event_ids"] = [*entry.get("approval_event_ids", []), event_id]
        entry["matching_approval_count"] = len(entry["approval_event_ids"])
        entry["state"] = "ACTIVE" if entry["matching_approval_count"] >= threshold else "CANDIDATE"
        entry["last_decision"] = "APPROVE"

    entry["last_event_id"] = event_id
    entry["updated_at"] = decision.get("decided_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    entries[key] = entry
    updated["entries"] = [entries[name] for name in sorted(entries)]
    updated["applied_event_ids"] = sorted({*updated["applied_event_ids"], event_id})
    applied_event_digests[event_id] = decision_digest
    updated["applied_event_digests"] = {
        name: applied_event_digests[name] for name in sorted(applied_event_digests)
    }
    updated["registry_digest"] = _digest(
        {
            "schema": updated["schema"],
            "registry_version": updated["registry_version"],
            "applied_event_ids": updated["applied_event_ids"],
            "applied_event_digests": updated["applied_event_digests"],
            "entries": updated["entries"],
            "operator_authorization_consumptions": updated["operator_authorization_consumptions"],
        }
    )
    return updated


def _operator_authorization_key(request: dict[str, Any], operator_rule: dict[str, Any]) -> str:
    return _digest(
        {
            "action_class": request.get("action_class"),
            "authority_profile": request.get("authority_profile"),
            "scope_key": request.get("scope_key"),
            "constraints": request.get("constraints"),
            "operator_rule_id": operator_rule.get("rule_id"),
        }
    )


def _exact_json_value(actual: Any, expected: Any) -> bool:
    return type(actual) is type(expected) and actual == expected


def evaluate_authorization(
    request: dict[str, Any],
    registry: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    request_id = _require_token(request, "request_id")
    action_class = _require_token(request, "action_class")
    scope_key = _require_token(request, "scope_key")
    constraints = request.get("constraints")
    constraints_digest = _constraints_digest(request)
    never_learn = set(policy["never_learn_risk_flags"])
    risky = sorted(name for name, value in _risk_flags(request).items() if value and name in never_learn)
    gates = request.get("gates")
    if not isinstance(gates, dict):
        raise AuthorizationPolicyError("gates must be an object")

    reasons: list[str] = []
    decision = "AUTHORIZATION_REQUIRED"
    authority_profile = request.get("authority_profile")
    operator_rule = next(
        (
            rule
            for rule in policy.get("operator_granted_rules", [])
            if isinstance(rule, dict)
            and rule.get("action_class") == action_class
            and isinstance(authority_profile, str)
            and rule.get("authority_profile") == authority_profile
        ),
        None,
    )
    risk_flag_exceptions: set[str] = set()
    forbidden_risk_flags: set[str] = set()
    required_constraint_values: dict[str, Any] = {}
    allowed_true_risk_flags: set[str] = set()
    closed_constraint_schema = False
    single_use = False
    if operator_rule is not None:
        raw_exceptions = operator_rule.get("risk_flag_exceptions", [])
        if not isinstance(raw_exceptions, list) or any(not isinstance(name, str) for name in raw_exceptions):
            raise AuthorizationPolicyError("operator rule risk_flag_exceptions must be a list of strings")
        risk_flag_exceptions = set(raw_exceptions)
        raw_forbidden = operator_rule.get("forbidden_risk_flags", [])
        if not isinstance(raw_forbidden, list) or any(not isinstance(name, str) for name in raw_forbidden):
            raise AuthorizationPolicyError("operator rule forbidden_risk_flags must be a list of strings")
        forbidden_risk_flags = set(raw_forbidden)
        raw_constraint_values = operator_rule.get("required_constraint_values", {})
        if not isinstance(raw_constraint_values, dict):
            raise AuthorizationPolicyError("operator rule required_constraint_values must be an object")
        required_constraint_values = raw_constraint_values
        raw_allowed_true = operator_rule.get("allowed_true_risk_flags", raw_exceptions)
        if not isinstance(raw_allowed_true, list) or any(not isinstance(name, str) for name in raw_allowed_true):
            raise AuthorizationPolicyError("operator rule allowed_true_risk_flags must be a list of strings")
        allowed_true_risk_flags = set(raw_allowed_true)
        closed_constraint_schema = operator_rule.get("closed_constraint_schema", False)
        if not isinstance(closed_constraint_schema, bool):
            raise AuthorizationPolicyError("operator rule closed_constraint_schema must be boolean")
        single_use = operator_rule.get("single_use", False)
        if not isinstance(single_use, bool):
            raise AuthorizationPolicyError("operator rule single_use must be boolean")
    blocking_risks = [name for name in risky if name not in risk_flag_exceptions]
    all_true_risks = {name for name, value in _risk_flags(request).items() if value}
    unrecognized_true_risks = sorted(all_true_risks - allowed_true_risk_flags) if operator_rule else []
    rule_forbidden_risks = sorted(
        name for name in forbidden_risk_flags if _risk_flags(request).get(name) is True
    )
    constraint_mismatches = sorted(
        name
        for name, expected in required_constraint_values.items()
        if not isinstance(constraints, dict) or not _exact_json_value(constraints.get(name), expected)
    )
    unexpected_constraints = sorted(
        set(constraints or {}) - set(required_constraint_values)
    ) if operator_rule and closed_constraint_schema and isinstance(constraints, dict) else []
    operator_authorization_key = (
        _operator_authorization_key(request, operator_rule) if operator_rule is not None else None
    )
    consumptions = registry.get("operator_authorization_consumptions", {})
    already_consumed = bool(
        operator_authorization_key
        and isinstance(consumptions, dict)
        and operator_authorization_key in consumptions
    )
    required_gates = list(policy["common_required_gates"])
    required_gates.extend(policy["allowlisted_action_classes"].get(action_class, []))
    if operator_rule is not None:
        required_gates.extend(operator_rule.get("required_gates", []))
    required_gates = list(dict.fromkeys(required_gates))
    missing_gates = sorted(name for name in required_gates if gates.get(name) is not True)

    if blocking_risks:
        reasons.extend(f"never_learn_risk:{name}" for name in blocking_risks)
    elif unrecognized_true_risks:
        reasons.extend(f"operator_rule_unrecognized_or_forbidden_risk:{name}" for name in unrecognized_true_risks)
    elif rule_forbidden_risks:
        reasons.extend(f"operator_rule_forbidden_risk:{name}" for name in rule_forbidden_risks)
    elif action_class not in policy["allowlisted_action_classes"]:
        reasons.append("action_class_not_allowlisted")
    elif missing_gates:
        decision = "HOLD"
        reasons.extend(f"gate_not_true:{name}" for name in missing_gates)
    elif constraint_mismatches:
        decision = "HOLD"
        reasons.extend(f"constraint_not_exact:{name}" for name in constraint_mismatches)
    elif unexpected_constraints:
        decision = "HOLD"
        reasons.extend(f"constraint_not_allowed:{name}" for name in unexpected_constraints)
    elif already_consumed:
        decision = "HOLD"
        reasons.append(f"operator_authorization_consumed:{operator_authorization_key}")
    elif operator_rule is not None:
        decision = "AUTO_AUTHORIZED"
        reasons.append(f"operator_granted_rule:{operator_rule['rule_id']}")
    else:
        key = _entry_key(action_class, scope_key, constraints_digest)
        matching = next(
            (
                entry
                for entry in registry.get("entries", [])
                if isinstance(entry, dict)
                and entry.get("entry_key") == key
                and entry.get("state") == policy["learning"]["activation_state"]
            ),
            None,
        )
        if matching is not None:
            decision = "AUTO_AUTHORIZED"
            reasons.append(f"active_learned_authorization:{key}")
        else:
            reasons.append("no_active_matching_learned_authorization")

    result = {
        "schema": "atlas.authorization-evaluation.v1",
        "request_id": request_id,
        "action_class": action_class,
        "scope_key": scope_key,
        "constraints_digest": constraints_digest,
        "decision": decision,
        "reasons": reasons,
        "required_gates": required_gates,
        "missing_gates": missing_gates,
        "authority_profile": authority_profile,
        "operator_rule_id": operator_rule.get("rule_id") if operator_rule is not None else None,
        "operator_rule_exclusions": operator_rule.get("exclusions", []) if operator_rule is not None else [],
        "operator_rule_risk_flag_exceptions": sorted(risk_flag_exceptions),
        "operator_rule_forbidden_risk_flags": sorted(forbidden_risk_flags),
        "operator_rule_required_constraint_values": required_constraint_values,
        "operator_authorization_key": operator_authorization_key,
        "single_use": single_use,
        "consumption_required": bool(operator_rule is not None and single_use),
        "replay_permitted": not single_use,
        "required_post_action_proof": (
            operator_rule.get("required_post_action_proof", []) if operator_rule is not None else []
        ),
        "owner_first": True,
        "executes_action": False,
    }
    result["evaluation_digest"] = _digest(result)
    return result


def consume_operator_authorization(
    request: dict[str, Any],
    registry: dict[str, Any],
    policy: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    evaluation = evaluate_authorization(request, registry, policy)
    if evaluation["decision"] != "AUTO_AUTHORIZED":
        raise AuthorizationPolicyError(
            "operator authorization is not consumable: " + ",".join(evaluation["reasons"])
        )
    if not evaluation["single_use"] or not evaluation["operator_authorization_key"]:
        raise AuthorizationPolicyError("operator authorization is not a single-use profile")

    key = evaluation["operator_authorization_key"]
    updated = deepcopy(registry)
    consumptions = updated.setdefault("operator_authorization_consumptions", {})
    if key in consumptions:
        raise AuthorizationPolicyError("operator authorization was already consumed")
    consumed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    receipt = {
        "schema": "atlas.authorization-decision.v1",
        "decision_phase": "CONSUMED",
        "authorization_key": key,
        "request_id": evaluation["request_id"],
        "operator_rule_id": evaluation["operator_rule_id"],
        "authority_profile": evaluation["authority_profile"],
        "evaluation_digest": evaluation["evaluation_digest"],
        "consumed_at": consumed_at,
        "decision": "AUTO_AUTHORIZED",
        "execution_authority": True,
        "single_use": True,
        "replay_permitted": False,
        "required_post_action_proof": evaluation["required_post_action_proof"],
    }
    receipt["consumption_digest"] = _digest(receipt)
    consumptions[key] = receipt
    updated["operator_authorization_consumptions"] = {
        name: consumptions[name] for name in sorted(consumptions)
    }
    updated["registry_digest"] = _digest(
        {
            "schema": updated["schema"],
            "registry_version": updated["registry_version"],
            "applied_event_ids": updated["applied_event_ids"],
            "applied_event_digests": updated["applied_event_digests"],
            "entries": updated["entries"],
            "operator_authorization_consumptions": updated["operator_authorization_consumptions"],
        }
    )
    return updated, receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate and learn bounded Atlas authorizations.")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    subparsers = parser.add_subparsers(dest="command", required=True)
    record = subparsers.add_parser("record")
    record.add_argument("--decision", type=Path, required=True)
    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--request", type=Path, required=True)
    consume = subparsers.add_parser("consume")
    consume.add_argument("--request", type=Path, required=True)
    args = parser.parse_args(argv)

    policy = load_policy(args.policy)
    if args.command == "record":
        with _exclusive_registry_lock(args.registry):
            current_registry = load_registry(args.registry)
            updated = record_operator_decision(
                current_registry, _load_json(args.decision), policy
            )
            _atomic_write_json(args.registry, updated)
        print(json.dumps(updated, indent=2, sort_keys=True))
        return 0
    if args.command == "consume":
        with _exclusive_registry_lock(args.registry):
            current_registry = load_registry(args.registry)
            updated, receipt = consume_operator_authorization(
                _load_json(args.request), current_registry, policy
            )
            _atomic_write_json(args.registry, updated)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0
    registry = load_registry(args.registry)
    result = evaluate_authorization(_load_json(args.request), registry, policy)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
