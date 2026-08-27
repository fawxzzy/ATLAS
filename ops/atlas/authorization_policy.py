from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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
    return registry


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
        }
    )
    return updated


def evaluate_authorization(
    request: dict[str, Any],
    registry: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    request_id = _require_token(request, "request_id")
    action_class = _require_token(request, "action_class")
    scope_key = _require_token(request, "scope_key")
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
    if operator_rule is not None:
        raw_exceptions = operator_rule.get("risk_flag_exceptions", [])
        if not isinstance(raw_exceptions, list) or any(not isinstance(name, str) for name in raw_exceptions):
            raise AuthorizationPolicyError("operator rule risk_flag_exceptions must be a list of strings")
        risk_flag_exceptions = set(raw_exceptions)
    blocking_risks = [name for name in risky if name not in risk_flag_exceptions]
    required_gates = list(policy["common_required_gates"])
    required_gates.extend(policy["allowlisted_action_classes"].get(action_class, []))
    if operator_rule is not None:
        required_gates.extend(operator_rule.get("required_gates", []))
    required_gates = list(dict.fromkeys(required_gates))
    missing_gates = sorted(name for name in required_gates if gates.get(name) is not True)

    if blocking_risks:
        reasons.extend(f"never_learn_risk:{name}" for name in blocking_risks)
    elif action_class not in policy["allowlisted_action_classes"]:
        reasons.append("action_class_not_allowlisted")
    elif missing_gates:
        decision = "HOLD"
        reasons.extend(f"gate_not_true:{name}" for name in missing_gates)
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
        "required_post_action_proof": (
            operator_rule.get("required_post_action_proof", []) if operator_rule is not None else []
        ),
        "owner_first": True,
        "executes_action": False,
    }
    result["evaluation_digest"] = _digest(result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate and learn bounded Atlas authorizations.")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    subparsers = parser.add_subparsers(dest="command", required=True)
    record = subparsers.add_parser("record")
    record.add_argument("--decision", type=Path, required=True)
    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--request", type=Path, required=True)
    args = parser.parse_args(argv)

    policy = load_policy(args.policy)
    registry = load_registry(args.registry)
    if args.command == "record":
        updated = record_operator_decision(registry, _load_json(args.decision), policy)
        _atomic_write_json(args.registry, updated)
        print(json.dumps(updated, indent=2, sort_keys=True))
        return 0
    result = evaluate_authorization(_load_json(args.request), registry, policy)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
