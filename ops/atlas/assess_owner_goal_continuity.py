"""Read-only gate for whole-Goal blocks and an all-owner stop.

The caller supplies independently verified native Goal, task, scope, and
obligation evidence. A repeated blocked-Goal audit also supplies the prior
assessment and its source reference, so a changed hold condition can be
distinguished from an unrelated fingerprint change. This module never changes
a Goal or dispatches work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import UUID


SCHEMA = "atlas.owner-goal-continuity-audit.v1"
ADMISSIONS = {"ADMITTED", "HELD", "COMPLETE", "UNKNOWN"}
GOAL_STATES = {"ACTIVE", "BLOCKED", "COMPLETE", "UNKNOWN"}
TASK_STATES = {"active", "idle", "unknown"}
POLICY_PATH = Path(__file__).resolve().parents[2] / "docs/registry/ATLAS-AUTONOMOUS-ENGINEERING-GOVERNANCE.v1.json"
PROGRAM_PATH = Path(__file__).resolve().parents[2] / "tmp/atlas/autonomous-work-program.json"


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


def _verified_prior_assessment(audit: dict[str, Any], root: Path) -> dict[str, Any] | None:
    """Bind a caller-supplied prior snapshot to local content-addressed evidence."""
    ref = audit.get("prior_assessment_ref")
    if not isinstance(ref, str):
        return None
    match = re.fullmatch(
        r"((?:runtime/atlas/continuity|tmp/atlas)/[A-Za-z0-9._/-]+\.json)#sha256=([0-9a-f]{64})",
        ref,
    )
    if not match or ".." in Path(match[1]).parts:
        return None
    try:
        path = (root / match[1]).resolve(strict=True)
        if not path.is_relative_to(root.resolve(strict=True)) or not path.is_file():
            return None
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != match[2]:
            return None
        prior = json.loads(raw)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    return prior if isinstance(prior, dict) and prior == audit.get("prior_assessment") else None


def _fingerprint(
    owners: list[dict[str, Any]], coverage_scope: str, program_ref: str,
    ready_target_gaps: list[str], ready_target_rechecks: list[str],
    program_decision: str, program_coverage_valid: bool,
    require_independent_candidate_search: bool,
) -> str:
    owner_material = [
        {
            "role_id": owner["role_id"],
            "thread_id": owner["thread_id"],
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


def assess_owner(owner: dict[str, Any], *, require_independent_candidate_search: bool | None = None,
                 _current_audit_thread: str | None = None) -> dict[str, Any]:
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
        # Incomplete evidence cannot prove a whole-Goal stop. It also cannot
        # hide independently admitted work or a blocked Goal's Resume action.
        if not result["admitted_ids"]:
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
            result["resume_control"] = "Resume goal"
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
    if ((owner["task_state"] == "active" and owner["thread_id"] != _current_audit_thread)
            or owner.get("equivalent_delivery_active") is True):
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


def assess_audit(audit: dict[str, Any], *, evidence_root: Path | None = None) -> dict[str, Any]:
    """External-watch assessment; serialized self-audit claims never change activity."""
    return _assess_audit(audit, evidence_root=evidence_root)


def _assess_audit(audit: dict[str, Any], *, evidence_root: Path | None = None,
                  current_audit_thread: str | None = None) -> dict[str, Any]:
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
        assess_owner(owner, require_independent_candidate_search=require_independent_candidate_search,
                     _current_audit_thread=current_audit_thread)
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
    baseline_fingerprint = _fingerprint(
        owners, coverage.get("scope") if coverage_valid else "UNKNOWN",
        audit.get("program_ref") if program_coverage_valid and _text(audit.get("program_ref")) else "UNKNOWN",
        ready_target_gaps, ready_target_rechecks, program_decision,
        program_coverage_valid, require_independent_candidate_search,
    )
    prior_fingerprint = audit.get("prior_fingerprint")
    prior_evidence_invalid = False
    if _text(prior_fingerprint):
        blocked = [owner for owner in owners if owner["goal_state"] == "BLOCKED"
                   and not owner["admitted_ids"] and owner["holds"]]
        if blocked:
            prior = _verified_prior_assessment(
                audit, evidence_root or Path(__file__).resolve().parents[2]
            )
            prior_owners = prior.get("owners") if isinstance(prior, dict) else None
            prior_valid = (
                prior.get("schema") == "atlas.owner-goal-continuity-assessment.v1"
                and prior.get("fingerprint") == prior_fingerprint
                and isinstance(prior_owners, list)
                and all(isinstance(item, dict) and _text(item.get("role_id"))
                        and isinstance(item.get("holds"), list) for item in prior_owners)
                and len({item["role_id"] for item in prior_owners}) == len(prior_owners)
                and {item["role_id"] for item in prior_owners} == set(roles)
                and all(
                    all(isinstance(hold, dict) and _text(hold.get("id"))
                        and _text(hold.get("unblock_condition")) for hold in item["holds"])
                    and len({hold["id"] for hold in item["holds"]}) == len(item["holds"])
                    for item in prior_owners
                )
            ) if isinstance(prior, dict) else False
            if prior_valid:
                prior_by_role = {item["role_id"]: item for item in prior_owners}
                for owner in blocked:
                    previous = prior_by_role[owner["role_id"]]["holds"]
                    old_conditions = {item["id"]: item["unblock_condition"] for item in previous}
                    new_conditions = {item["id"]: item["unblock_condition"] for item in owner["holds"]}
                    if old_conditions != new_conditions:
                        owner["native_goal_resume_required"] = True
                        owner["resume_action"] = "MANUAL_RESUME_REQUIRED"
                        owner["resume_control"] = "Resume goal"
                        owner["owner_wake_allowed"] = False
                        owner["decision"] = "BLOCKED_GOAL_UNBLOCK_CONDITION_CHANGED"
                        if program_decision in {"GENUINE_ALL_STOP", "ALL_INCLUDED_OWNERS_BLOCKED", "ALL_STOP_UNPROVEN"}:
                            program_decision = "BLOCKED_GOAL_MANUAL_RESUME_REQUIRED"
            if not prior_valid:
                prior_evidence_invalid = True
                for owner in blocked:
                    owner["missing"].append("prior_blocked_hold_comparison")
                    owner["decision"] = "HOLD_DELTA_EVIDENCE_REQUIRED"
                if program_decision in {"GENUINE_ALL_STOP", "ALL_INCLUDED_OWNERS_BLOCKED"}:
                    program_decision = "ALL_STOP_UNPROVEN"
    # A changed hold condition is already in the baseline material. Its
    # one-time Resume notification must not churn a genuinely repeated input.
    # Invalid prior evidence, however, changes the actual decision and must
    # change the fingerprint even when the hold condition itself is unchanged.
    fingerprint = (
        _fingerprint(
            owners, coverage.get("scope") if coverage_valid else "UNKNOWN",
            audit.get("program_ref") if program_coverage_valid and _text(audit.get("program_ref")) else "UNKNOWN",
            ready_target_gaps, ready_target_rechecks, program_decision,
            program_coverage_valid, require_independent_candidate_search,
        ) if prior_evidence_invalid else baseline_fingerprint
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
        "manual_resume_required_owners": [
            {"role_id": owner["role_id"], "thread_id": owner["thread_id"],
             "control": "Resume goal"}
            for owner in owners if owner["resume_action"] == "MANUAL_RESUME_REQUIRED"
        ],
        "authorizes_execution": False,
    }


def _uuid(value: Any, label: str) -> str:
    try:
        if not isinstance(value, str) or str(UUID(value)) != value:
            raise ValueError()
    except (ValueError, AttributeError):
        raise ValueError(f"SELF_AUDIT_INVALID_{label}") from None
    return value


def _read_current_native_turn(caller: str, turn_id: str) -> dict[str, Any]:
    if __package__ in (None, ""):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from ops.atlas.codex_native_goal_readback import read_current_native_turn

    return read_current_native_turn(caller, turn_id)


def _verify_native_turn(caller: str, turn_id: str) -> None:
    if (os.environ.get("CODEX_THREAD_ID") != caller
            or os.environ.get("CODEX_TURN_ID") not in (None, "", turn_id)):
        raise ValueError("SELF_AUDIT_EXECUTOR_IDENTITY_DRIFT")
    payload = _read_current_native_turn(caller, turn_id)
    thread = payload.get("thread", {})
    turns = payload.get("turns")
    if (not isinstance(thread, dict) or thread.get("id") != caller
            or thread.get("kind") != "codex" or thread.get("hostId") != "local"
            or thread.get("archived") is True
            or not isinstance(thread.get("status"), dict) or thread["status"].get("type") != "active"
            or not isinstance(turns, list) or len(turns) != 1 or not isinstance(turns[0], dict)
            or turns[0].get("id") != turn_id or turns[0].get("status") != "inProgress"):
        raise ValueError("SELF_AUDIT_CURRENT_NATIVE_TURN_UNVERIFIED")


def _verify_program(audit: dict[str, Any], caller: str, role: str) -> str:
    if __package__ in (None, ""):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from ops.atlas.autonomous_lane_scheduler import READY_STATES

    ref = audit.get("program_ref")
    match = re.fullmatch(r"tmp/atlas/autonomous-work-program\.json(?:#revision=(\d+))?#sha256=([0-9a-f]{64})",
                         ref if isinstance(ref, str) else "")
    raw = PROGRAM_PATH.read_bytes()
    if not match or hashlib.sha256(raw).hexdigest() != match[2]:
        raise ValueError("SELF_AUDIT_CURRENT_PROGRAM_DRIFT")
    program = json.loads(raw)
    if (type(program.get("revision")) is not int
            or (match[1] is not None and int(match[1]) != program["revision"])
            or any(not isinstance(program.get(k), list) for k in
                   ("standing_packets", "active_leases", "delivery_intents"))):
        raise ValueError("SELF_AUDIT_CURRENT_PROGRAM_UNVERIFIED")

    def relevant(record: dict[str, Any]) -> bool:
        targets = [record]
        for key in ("execution_target", "owner_return"):
            target = record.get(key)
            if target is not None:
                if not isinstance(target, dict):
                    raise ValueError("SELF_AUDIT_WORK_OWNER_UNKNOWN")
                targets.append(target)
        roles = [t.get(k) for t in targets for k in ("logical_role_id", "role_id", "target_role_id") if _text(t.get(k))]
        threads = [t.get(k) for t in targets for k in ("runtime_thread_id", "thread_id", "target_thread_id") if _text(t.get(k))]
        if not roles and not threads:
            raise ValueError("SELF_AUDIT_WORK_OWNER_UNKNOWN")
        return role in roles or caller in threads

    packets = {}
    for packet in program["standing_packets"]:
        if (not isinstance(packet, dict) or not _text(packet.get("packet_id"))
                or packet["packet_id"] in packets):
            raise ValueError("SELF_AUDIT_PACKET_CORRELATION_UNKNOWN")
        packets[packet["packet_id"]] = packet
        state = str(packet.get("state") or "").upper()
        if state in READY_STATES and relevant(packet):
            raise ValueError("SELF_AUDIT_OWNER_READY_WORK")
        if state == "ACTIVE" and relevant(packet):
            raise ValueError("SELF_AUDIT_EQUIVALENT_DELIVERY_ACTIVE")
    for key in ("active_leases", "delivery_intents"):
        for record in program[key]:
            if not isinstance(record, dict) or record.get("packet_id") not in packets:
                raise ValueError("SELF_AUDIT_PACKET_CORRELATION_UNKNOWN")
            packet = packets[record["packet_id"]]
            # The packet supplies ownership when the active record only names
            # its packet. Explicit record targets also count, including drift.
            has_target = any(_text(record.get(k)) for k in
                             ("logical_role_id", "role_id", "target_role_id", "runtime_thread_id", "thread_id", "target_thread_id"))
            has_target = (has_target or record.get("execution_target") is not None
                          or record.get("owner_return") is not None)
            if relevant(packet) or (has_target and relevant(record)):
                raise ValueError("SELF_AUDIT_EQUIVALENT_DELIVERY_ACTIVE")
    return match[2]


def assess_current_owner_audit(audit: dict[str, Any], *, current_owner_turn: str) -> dict[str, Any]:
    """Exclude only the verified caller's read-only assessing turn, never work.

    This explicit entry point is for a current owner, not an external watch.
    Native and program state are checked on both sides of classification. No
    serialized capability or audit JSON flag can select this path implicitly.
    """
    caller = _uuid(os.environ.get("CODEX_THREAD_ID"), "CALLER")
    turn_id = _uuid(current_owner_turn, "TURN")
    if os.environ.get("CODEX_TURN_ID") not in (None, "", turn_id):
        raise ValueError("SELF_AUDIT_EXECUTOR_TURN_MISMATCH")
    owners = audit.get("owners")
    coverage = audit.get("coverage", {})
    if (not isinstance(owners, list) or len(owners) != 1 or not isinstance(owners[0], dict)
            or owners[0].get("thread_id") != caller or owners[0].get("task_state") != "active"
            or not _text(owners[0].get("role_id")) or not isinstance(coverage, dict)
            or coverage.get("scope") != "owner_subset"
            or coverage.get("role_ids") != [owners[0]["role_id"]]):
        raise ValueError("SELF_AUDIT_EXACT_OWNER_SUBSET_REQUIRED")
    # Snapshot the caller's evidence so it cannot be changed during verification.
    snapshot = json.loads(json.dumps(audit))
    program_sha = _verify_program(snapshot, caller, owners[0]["role_id"])
    _verify_native_turn(caller, turn_id)
    result = _assess_audit(snapshot, current_audit_thread=caller)
    _verify_native_turn(caller, turn_id)
    if _verify_program(snapshot, caller, owners[0]["role_id"]) != program_sha or audit != snapshot:
        raise ValueError("SELF_AUDIT_EVIDENCE_DRIFT")
    result["current_owner_self_audit"] = {
        "thread_id": caller, "turn_id": turn_id, "program_sha256": program_sha,
        "excluded_activity": "CURRENT_READ_ONLY_ASSESSING_TURN_ONLY",
        "native_and_program_rechecked": True,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", type=Path, help="verified owner audit JSON")
    parser.add_argument("--current-owner-turn", help="explicit self-audit: exact current native turn UUID")
    args = parser.parse_args()
    try:
        audit = json.loads(args.audit.read_text(encoding="utf-8"))
        result = (assess_current_owner_audit(audit, current_owner_turn=args.current_owner_turn)
                  if args.current_owner_turn is not None else assess_audit(audit))
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({"decision": "AUDIT_VALIDATION_HOLD", "reason": str(error), "authorizes_execution": False}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
