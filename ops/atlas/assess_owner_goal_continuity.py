"""Read-only gate for whole-Goal blocks and an all-owner stop.

The caller supplies independently verified native Goal, task, scope, and
obligation evidence. This module never changes a Goal or dispatches work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA = "atlas.owner-goal-continuity-audit.v1"
ADMISSIONS = {"ADMITTED", "HELD", "COMPLETE", "UNKNOWN"}
GOAL_STATES = {"ACTIVE", "BLOCKED", "COMPLETE", "UNKNOWN"}
TASK_STATES = {"active", "idle", "unknown"}
POLICY_PATH = Path(__file__).resolve().parents[2] / "docs/registry/ATLAS-AUTONOMOUS-ENGINEERING-GOVERNANCE.v1.json"


def goal_policy() -> dict[str, Any]:
    """Read the canonical minimum; missing or malformed policy fails closed."""
    source = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    policy = source.get("goal_continuity")
    if (source.get("schema") != "atlas.autonomous-engineering-governance.v1"
            or not isinstance(policy, dict)
            or policy.get("policy_id") != "ATLAS-GOAL-CONTINUITY-V1"
            or not isinstance(policy.get("whole_goal_block"), dict)
            or policy["whole_goal_block"].get("require_independent_candidate_search") is not True
            or type(policy["whole_goal_block"].get("minimum_same_hold_turns")) is not int
            or policy["whole_goal_block"]["minimum_same_hold_turns"] < 3):
        raise ValueError("canonical Goal-continuity policy is missing or weaker than the accepted minimum")
    return policy


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value != "UNKNOWN"


def _fingerprint(
    owners: list[dict[str, Any]], coverage_scope: str, program_ref: str,
    ready_target_gaps: list[str], ready_target_rechecks: list[str],
    program_decision: str, program_coverage_valid: bool,
    require_independent_candidate_search: bool,
) -> str:
    owner_material = [
        {
            "role_id": owner["role_id"],
            "goal_state": owner["goal_state"],
            "decision": owner["decision"],
            "route_issues": sorted(owner["route_issues"]),
            "missing": sorted(owner["missing"]),
            "admitted_ids": sorted(owner["admitted_ids"]),
            "holds": sorted(owner["holds"], key=lambda hold: hold["id"]),
        }
        for owner in sorted(owners, key=lambda item: item["role_id"])
    ]
    material = {
        "owners": owner_material,
        "coverage_scope": coverage_scope,
        "program_ref": program_ref,
        "ready_target_gaps": sorted(ready_target_gaps),
        "ready_target_rechecks": sorted(ready_target_rechecks),
        "program_decision": program_decision,
        "program_ready_coverage_verified": program_coverage_valid,
        "independent_candidate_search_required": require_independent_candidate_search,
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def assess_owner(owner: dict[str, Any], *, require_independent_candidate_search: bool | None = None) -> dict[str, Any]:
    """Classify one exact accepted Goal scope without granting execution."""
    policy = goal_policy()
    require_independent_candidate_search = (
        policy["whole_goal_block"]["require_independent_candidate_search"]
        or require_independent_candidate_search is True
    )
    role = owner.get("role_id")
    result: dict[str, Any] = {
        "role_id": role if _text(role) else "UNKNOWN",
        "thread_id": owner.get("thread_id", "UNKNOWN"),
        "goal_state": owner.get("goal_state", "UNKNOWN"),
        "decision": "AUDIT_INCOMPLETE",
        "admitted_ids": [],
        "holds": [],
        "missing": [],
        "route_issues": [],
        "native_goal_resume_required": False,
        "resume_action": "NONE",
        "owner_wake_allowed": False,
        "authorizes_execution": False,
    }
    missing = result["missing"]
    if not _text(role) or not _text(owner.get("thread_id")):
        missing.append("owner_identity")
    if owner.get("goal_state") not in GOAL_STATES:
        missing.append("native_goal_state")
    if owner.get("task_state") not in TASK_STATES or owner.get("task_state") == "unknown":
        missing.append("native_task_state")
    if not isinstance(owner.get("equivalent_delivery_active"), bool):
        missing.append("equivalent_delivery_state")
    if not _text(owner.get("goal_scope_ref")):
        missing.append("accepted_goal_scope_ref")
    expected = owner.get("accepted_obligation_ids")
    obligations = owner.get("obligations")
    if not isinstance(expected, list) or not expected or any(not _text(x) for x in expected) or len(set(expected)) != len(expected):
        missing.append("accepted_obligation_ids")
        expected = []
    if not isinstance(obligations, list):
        missing.append("remaining_obligations")
        obligations = []
    actual = [item.get("id") for item in obligations if isinstance(item, dict)]
    if (len(actual) != len(obligations) or any(not _text(x) for x in actual)
            or len(set(actual)) != len(actual) or set(actual) != set(expected)):
        missing.append("full_scope_obligation_match")
    if missing:
        return result
    if owner["goal_state"] == "UNKNOWN":
        missing.append("native_goal_readback")
        return result
    if owner.get("owner_binding_state") != "VERIFIED":
        result["route_issues"].append("current_owner_binding")
    if owner.get("monitoring_route_state") != "VERIFIED":
        result["route_issues"].append("current_monitoring_route")

    complete = []
    unknown = []
    for item in obligations:
        identity = item["id"]
        admission = item.get("admission")
        if admission not in ADMISSIONS or item.get("independent_checked") is not True or not _text(item.get("evidence_ref")):
            unknown.append(identity)
            continue
        if admission == "ADMITTED":
            if not _text(item.get("admission_ref")) or not _text(item.get("authority_ref")):
                unknown.append(identity)
            else:
                result["admitted_ids"].append(identity)
        elif admission == "HELD":
            hold = item.get("hold")
            if not isinstance(hold, dict) or any(not _text(hold.get(key)) for key in ("code", "evidence_ref", "unblock_condition")):
                unknown.append(identity)
            elif require_independent_candidate_search and (
                not isinstance(item.get("independent_candidate_search"), dict)
                or not _text(item["independent_candidate_search"].get("evidence_ref"))
                or item["independent_candidate_search"].get("disposition") != "NO_ADMITTED_CANDIDATE"
                or type(item["independent_candidate_search"].get("candidate_count")) is not int
                or item["independent_candidate_search"]["candidate_count"] != 0
            ):
                unknown.append(identity)
            else:
                result["holds"].append({
                    "id": identity,
                    "code": hold["code"],
                    "evidence_ref": hold["evidence_ref"],
                    "unblock_condition": hold["unblock_condition"],
                    **({"candidate_search_ref": item["independent_candidate_search"]["evidence_ref"]}
                       if require_independent_candidate_search else {}),
                })
        elif admission == "COMPLETE":
            if not _text(item.get("acceptance_ref")):
                unknown.append(identity)
            else:
                complete.append(identity)
        else:
            unknown.append(identity)

    if unknown:
        missing.extend(f"obligation_evidence:{identity}" for identity in unknown)
        return result
    if owner["goal_state"] == "COMPLETE" and len(complete) != len(expected):
        result["decision"] = "INCONSISTENT_GOAL_COMPLETION"
        return result
    if len(complete) == len(expected):
        result["decision"] = "COMPLETION_REVIEW_REQUIRED"
        return result
    if result["admitted_ids"]:
        result["native_goal_resume_required"] = owner["goal_state"] == "BLOCKED"
        if result["native_goal_resume_required"]:
            result["resume_action"] = "MANUAL_RESUME_REQUIRED"
        if owner["task_state"] == "active" or owner.get("equivalent_delivery_active") is True:
            result["decision"] = "IN_PROGRESS_NO_DUPLICATE_WAKE"
        elif owner["task_state"] == "idle" and owner.get("equivalent_delivery_active") is False:
            if result["route_issues"]:
                result["decision"] = "ADMITTED_WORK_ROUTE_REPAIR_REQUIRED"
            else:
                result["decision"] = "BLOCKED_GOAL_HAS_ADMITTED_WORK" if owner["goal_state"] == "BLOCKED" else "WAKE_ELIGIBLE_OWNER"
                # A message can start a task turn but cannot resume its native
                # blocked Goal. Leave that action to the supported Resume control.
                result["owner_wake_allowed"] = owner["goal_state"] != "BLOCKED"
        else:
            missing.append("delivery_deduplication")
        return result
    if owner["task_state"] == "active" or owner.get("equivalent_delivery_active") is True:
        result["decision"] = "IN_PROGRESS_NO_DUPLICATE_WAKE"
        return result
    if len(result["holds"]) + len(complete) != len(expected):
        missing.append("unclassified_remaining_obligation")
        return result
    if result["route_issues"]:
        result["decision"] = "ROUTE_OR_MONITORING_GAP"
        return result
    hold_turns = owner.get("same_hold_turns")
    if not isinstance(hold_turns, int) or isinstance(hold_turns, bool) or hold_turns < 0:
        missing.append("same_hold_turn_count")
        return result
    if hold_turns < policy["whole_goal_block"]["minimum_same_hold_turns"]:
        result["decision"] = "HELD_NOT_YET_WHOLE_GOAL_BLOCKABLE"
        return result
    result["decision"] = "WHOLE_GOAL_BLOCK_PROVEN"
    return result


def assess_audit(audit: dict[str, Any]) -> dict[str, Any]:
    policy = goal_policy()
    if audit.get("schema") != SCHEMA or not isinstance(audit.get("owners"), list) or not audit["owners"]:
        raise ValueError("expected a nonempty atlas.owner-goal-continuity-audit.v1 owners list")
    if any(not isinstance(owner, dict) for owner in audit["owners"]):
        raise ValueError("owner audits must be objects")
    require_independent_candidate_search = (
        policy["whole_goal_block"]["require_independent_candidate_search"]
        or audit.get("require_independent_candidate_search") is True
    )
    owners = [
        assess_owner(owner, require_independent_candidate_search=require_independent_candidate_search)
        for owner in audit["owners"]
    ]
    roles = [owner["role_id"] for owner in owners]
    if len(set(roles)) != len(roles):
        raise ValueError("duplicate owner role")
    coverage = audit.get("coverage")
    coverage_valid = (
        isinstance(coverage, dict)
        and coverage.get("scope") in {"owner_subset", "complete_critical_path"}
        and _text(coverage.get("evidence_ref"))
        and isinstance(coverage.get("role_ids"), list)
        and all(_text(role) for role in coverage["role_ids"])
        and len(set(coverage["role_ids"])) == len(coverage["role_ids"])
        and set(coverage["role_ids"]) == set(roles)
    )
    ready_target_gaps: list[str] = []
    ready_target_rechecks: list[str] = []
    program_coverage_valid = True
    if coverage_valid and coverage["scope"] == "complete_critical_path":
        targets = audit.get("ready_packet_targets")
        program_coverage_valid = _text(audit.get("program_ref")) and isinstance(targets, list)
        if program_coverage_valid:
            for packet in targets:
                if (not isinstance(packet, dict) or any(not _text(packet.get(key)) for key in
                    ("packet_id", "target_role_id", "target_thread_id", "evidence_ref"))
                    or packet.get("target_native_state") not in {"active", "archived", "unknown"}
                    or packet.get("binding_state") not in {"VERIFIED", "STALE", "UNKNOWN"}):
                    program_coverage_valid = False
                    break
                if packet["target_native_state"] != "active" or packet["binding_state"] != "VERIFIED":
                    ready_target_gaps.append(packet["packet_id"])
                else:
                    ready_target_rechecks.append(packet["packet_id"])
        if not program_coverage_valid:
            ready_target_gaps.clear()
            ready_target_rechecks.clear()
    decisions = {owner["decision"] for owner in owners}
    if decisions & {"WAKE_ELIGIBLE_OWNER", "BLOCKED_GOAL_HAS_ADMITTED_WORK"}:
        program_decision = "ADMITTED_WORK_REQUIRES_OWNER_ACTION"
    elif "ADMITTED_WORK_ROUTE_REPAIR_REQUIRED" in decisions:
        program_decision = "ADMITTED_WORK_WITH_ROUTE_GAP"
    elif "IN_PROGRESS_NO_DUPLICATE_WAKE" in decisions:
        program_decision = "OWNER_WORK_IN_PROGRESS"
    elif "ROUTE_OR_MONITORING_GAP" in decisions:
        program_decision = "ROUTE_REPAIR_REQUIRED"
    elif ready_target_gaps:
        program_decision = "ROUTE_REPAIR_REQUIRED"
    elif ready_target_rechecks:
        program_decision = "READY_PACKET_ADMISSION_RECHECK"
    elif decisions & {"AUDIT_INCOMPLETE", "INCONSISTENT_GOAL_COMPLETION", "HELD_NOT_YET_WHOLE_GOAL_BLOCKABLE"}:
        program_decision = "ALL_STOP_UNPROVEN"
    elif decisions == {"WHOLE_GOAL_BLOCK_PROVEN"}:
        if not coverage_valid:
            program_decision = "OWNER_COVERAGE_UNVERIFIED"
        elif not program_coverage_valid:
            program_decision = "READY_PACKET_COVERAGE_UNVERIFIED"
        elif coverage["scope"] == "complete_critical_path":
            program_decision = "GENUINE_ALL_STOP"
        else:
            program_decision = "ALL_INCLUDED_OWNERS_BLOCKED"
    else:
        program_decision = "COMPLETION_REVIEW_REQUIRED"
    fingerprint = _fingerprint(
        owners, coverage.get("scope") if coverage_valid else "UNKNOWN",
        audit.get("program_ref") if program_coverage_valid and _text(audit.get("program_ref")) else "UNKNOWN",
        ready_target_gaps, ready_target_rechecks, program_decision,
        program_coverage_valid, require_independent_candidate_search,
    )
    return {
        "schema": "atlas.owner-goal-continuity-assessment.v1",
        "policy_id": policy["policy_id"],
        "decision": program_decision,
        "fingerprint": fingerprint,
        "changed_since_prior": fingerprint != audit.get("prior_fingerprint"),
        "coverage_scope": coverage.get("scope") if coverage_valid else "UNKNOWN",
        "program_ready_coverage_verified": program_coverage_valid,
        "independent_candidate_search_required": require_independent_candidate_search,
        "ready_target_gaps": ready_target_gaps,
        "ready_target_rechecks": ready_target_rechecks,
        "owners": owners,
        "authorizes_execution": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", type=Path, help="verified owner audit JSON")
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    print(json.dumps(assess_audit(audit), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
