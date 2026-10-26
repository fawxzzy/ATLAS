"""Regression cases for false whole-Goal blocks and all-stop decisions."""

import copy
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

from ops.atlas.assess_owner_goal_continuity import SCHEMA, assess_audit, goal_policy


REF = "runtime/atlas/continuity/proof.json#sha256=" + "a" * 64


def attach_prior(case: dict, prior: dict, root: Path, name: str = "prior.json") -> None:
    relative = Path("runtime/atlas/continuity") / name
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(prior, sort_keys=True, separators=(",", ":")) + "\n").encode()
    path.write_bytes(raw)
    case["prior_fingerprint"] = prior["fingerprint"]
    case["prior_assessment"] = prior
    case["prior_assessment_ref"] = relative.as_posix() + "#sha256=" + hashlib.sha256(raw).hexdigest()


def audit() -> dict:
    return {
        "schema": SCHEMA,
        "require_independent_candidate_search": True,
        "coverage": {
            "scope": "complete_critical_path",
            "role_ids": ["platform.supabase-migration"],
            "evidence_ref": REF,
        },
        "program_ref": REF,
        "ready_packet_targets": [],
        "owners": [
            {
                "role_id": "platform.supabase-migration",
                "thread_id": "platform-thread",
                "goal_state": "ACTIVE",
                "goal_scope_ref": REF,
                "accepted_obligation_ids": ["DOD-06", "DOD-09"],
                "task_state": "idle",
                "equivalent_delivery_active": False,
                "owner_binding_state": "VERIFIED",
                "monitoring_route_state": "VERIFIED",
                "same_hold_turns": 3,
                "obligations": [
                    {
                        "id": "DOD-06",
                        "admission": "HELD",
                        "independent_checked": True,
                        "evidence_ref": REF,
                        "hold": {
                            "code": "GENUINE_SESSION_ABSENT",
                            "evidence_ref": REF,
                            "unblock_condition": "Current Fitness actor and app session",
                        },
                        "independent_candidate_search": {
                            "evidence_ref": REF,
                            "disposition": "NO_ADMITTED_CANDIDATE",
                            "candidate_count": 0,
                        },
                    },
                    {
                        "id": "DOD-09",
                        "admission": "HELD",
                        "independent_checked": True,
                        "evidence_ref": REF,
                        "hold": {
                            "code": "PUBLISHER_ROUTE_ABSENT",
                            "evidence_ref": REF,
                            "unblock_condition": "Current publisher writer route",
                        },
                        "independent_candidate_search": {
                            "evidence_ref": REF,
                            "disposition": "NO_ADMITTED_CANDIDATE",
                            "candidate_count": 0,
                        },
                    },
                ],
            }
        ],
    }


class GoalContinuityTests(unittest.TestCase):
    def test_canonical_policy_project_references_exist(self) -> None:
        root = Path(__file__).resolve().parents[1]
        policy = json.loads(
            (root / "docs/registry/ATLAS-AUTONOMOUS-ENGINEERING-GOVERNANCE.v1.json")
            .read_text(encoding="utf-8")
        )

        def references(value):
            if isinstance(value, dict):
                for nested in value.values():
                    yield from references(nested)
            elif isinstance(value, list):
                for nested in value:
                    yield from references(nested)
            elif isinstance(value, str) and re.fullmatch(r"(?:docs|ops|tests)/[A-Za-z0-9_./-]+", value):
                yield value

        missing = sorted({path for path in references(policy) if not (root / path).is_file()})
        self.assertEqual(missing, [])

    def test_canonical_policy_sets_the_minimum_even_if_audit_requests_looser_check(self) -> None:
        self.assertEqual(goal_policy()["policy_id"], "ATLAS-GOAL-CONTINUITY-V1")
        case = audit()
        case["require_independent_candidate_search"] = False
        case["owners"][0]["obligations"][0].pop("independent_candidate_search")
        result = assess_audit(case)
        self.assertTrue(result["independent_candidate_search_required"])
        self.assertEqual(result["decision"], "ALL_STOP_UNPROVEN")

    def test_exact_all_held_scope_is_genuine_stop_and_deduplicates(self) -> None:
        first = assess_audit(audit())
        self.assertEqual(first["decision"], "GENUINE_ALL_STOP")
        self.assertEqual(first["owners"][0]["decision"], "WHOLE_GOAL_BLOCK_PROVEN")
        repeated = audit()
        repeated["prior_fingerprint"] = first["fingerprint"]
        self.assertFalse(assess_audit(repeated)["changed_since_prior"])
        repeated["owners"][0]["obligations"].reverse()
        self.assertFalse(assess_audit(repeated)["changed_since_prior"])

    def test_one_independent_admitted_lane_prevents_whole_goal_block(self) -> None:
        case = audit()
        owner = case["owners"][0]
        owner["obligations"][0].update({"admission": "ADMITTED", "admission_ref": REF, "authority_ref": REF})
        owner["obligations"][0].pop("hold")
        result = assess_audit(case)
        self.assertEqual(result["decision"], "ADMITTED_WORK_REQUIRES_OWNER_ACTION")
        self.assertEqual(result["owners"][0]["decision"], "WAKE_ELIGIBLE_OWNER")
        self.assertTrue(result["owners"][0]["owner_wake_allowed"])

    def test_blocked_goal_with_admitted_work_requires_resume_and_owner_action(self) -> None:
        case = audit()
        owner = case["owners"][0]
        owner["goal_state"] = "BLOCKED"
        owner["obligations"][0].update({"admission": "ADMITTED", "admission_ref": REF, "authority_ref": REF})
        owner["obligations"][0].pop("hold")
        result = assess_audit(case)
        self.assertEqual(result["owners"][0]["decision"], "BLOCKED_GOAL_HAS_ADMITTED_WORK")
        self.assertFalse(result["owners"][0]["owner_wake_allowed"])
        self.assertTrue(result["owners"][0]["native_goal_resume_required"])
        self.assertEqual(result["owners"][0]["resume_action"], "MANUAL_RESUME_REQUIRED")
        self.assertEqual(result["owners"][0]["resume_control"], "Resume goal")
        self.assertFalse(result["authorizes_execution"])

    def test_blocked_goal_changed_unblock_condition_requires_manual_resume(self) -> None:
        case = audit()
        case["owners"][0]["goal_state"] = "BLOCKED"
        prior = assess_audit(case)
        self.assertEqual(prior["decision"], "GENUINE_ALL_STOP")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            attach_prior(case, prior, root)
            case["owners"][0]["obligations"][0]["hold"]["unblock_condition"] = "Current Fitness actor and app session rechecked"
            result = assess_audit(case, evidence_root=root)
            owner = result["owners"][0]
            self.assertTrue(result["changed_since_prior"])
            self.assertEqual(result["decision"], "BLOCKED_GOAL_MANUAL_RESUME_REQUIRED")
            self.assertEqual(owner["thread_id"], "platform-thread")
            self.assertEqual(owner["decision"], "BLOCKED_GOAL_UNBLOCK_CONDITION_CHANGED")
            self.assertTrue(owner["native_goal_resume_required"])
            self.assertEqual(owner["resume_action"], "MANUAL_RESUME_REQUIRED")
            self.assertEqual(owner["resume_control"], "Resume goal")
            self.assertEqual(result["manual_resume_required_owners"], [
                {"role_id": "platform.supabase-migration", "thread_id": "platform-thread", "control": "Resume goal"}
            ])
            self.assertFalse(owner["owner_wake_allowed"])
            self.assertFalse(result["authorizes_execution"])
            attach_prior(case, result, root, "next.json")
            repeated = assess_audit(case, evidence_root=root)
            self.assertFalse(repeated["changed_since_prior"])
            self.assertEqual(repeated["owners"][0]["resume_action"], "NONE")

    def test_blocked_hold_change_without_prior_comparison_fails_closed(self) -> None:
        case = audit()
        case["owners"][0]["goal_state"] = "BLOCKED"
        prior = assess_audit(case)
        case["prior_fingerprint"] = prior["fingerprint"]
        case["owners"][0]["obligations"][0]["hold"]["unblock_condition"] = "Changed unblock condition"
        result = assess_audit(case)
        self.assertEqual(result["decision"], "ALL_STOP_UNPROVEN")
        self.assertIn("prior_blocked_hold_comparison", result["owners"][0]["missing"])
        self.assertFalse(result["authorizes_execution"])
        case["prior_fingerprint"] = result["fingerprint"]
        self.assertEqual(assess_audit(case)["decision"], "ALL_STOP_UNPROVEN")

    def test_owner_thread_change_changes_fingerprint(self) -> None:
        case = audit()
        prior = assess_audit(case)
        case["prior_fingerprint"] = prior["fingerprint"]
        case["owners"][0]["thread_id"] = "new-owner-thread"
        result = assess_audit(case)
        self.assertTrue(result["changed_since_prior"])
        self.assertNotEqual(result["fingerprint"], prior["fingerprint"])

    def test_tampered_prior_assessment_cannot_hide_blocked_hold_change(self) -> None:
        case = audit()
        case["owners"][0]["goal_state"] = "BLOCKED"
        prior = assess_audit(case)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            attach_prior(case, copy.deepcopy(prior), root)
            case["prior_assessment"]["owners"][0]["holds"][0]["unblock_condition"] = "Forged current condition"
            case["owners"][0]["obligations"][0]["hold"]["unblock_condition"] = "Forged current condition"
            result = assess_audit(case, evidence_root=root)
            self.assertEqual(result["decision"], "ALL_STOP_UNPROVEN")
            self.assertIn("prior_blocked_hold_comparison", result["owners"][0]["missing"])

    def test_changed_blocked_hold_does_not_hide_another_owners_admitted_work(self) -> None:
        case = audit()
        case["owners"][0]["goal_state"] = "BLOCKED"
        second = copy.deepcopy(case["owners"][0])
        second.update({"role_id": "owner.web", "thread_id": "web-thread", "goal_state": "ACTIVE"})
        case["coverage"]["role_ids"].append("owner.web")
        case["owners"].append(second)
        prior = assess_audit(case)
        second["obligations"][0].update({"admission": "ADMITTED", "admission_ref": REF, "authority_ref": REF})
        second["obligations"][0].pop("hold")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            attach_prior(case, prior, root)
            case["owners"][0]["obligations"][0]["hold"]["unblock_condition"] = "Changed condition"
            result = assess_audit(case, evidence_root=root)
            self.assertEqual(result["decision"], "ADMITTED_WORK_REQUIRES_OWNER_ACTION")
            self.assertEqual(result["owners"][1]["decision"], "WAKE_ELIGIBLE_OWNER")
            self.assertEqual(result["owners"][0]["resume_action"], "MANUAL_RESUME_REQUIRED")
            self.assertEqual(result["manual_resume_required_owners"], [
                {"role_id": "platform.supabase-migration", "thread_id": "platform-thread", "control": "Resume goal"}
            ])
            case.pop("prior_assessment_ref")
            missing = assess_audit(case, evidence_root=root)
            self.assertEqual(missing["decision"], "ADMITTED_WORK_REQUIRES_OWNER_ACTION")
            self.assertIn("prior_blocked_hold_comparison", missing["owners"][0]["missing"])

    def test_omitted_scope_lane_and_unproven_hold_cannot_block_goal(self) -> None:
        missing_lane = audit()
        missing_lane["owners"][0]["obligations"].pop()
        self.assertEqual(assess_audit(missing_lane)["decision"], "ALL_STOP_UNPROVEN")
        missing_hold = audit()
        missing_hold["owners"][0]["obligations"][0]["hold"].pop("unblock_condition")
        self.assertEqual(assess_audit(missing_hold)["decision"], "ALL_STOP_UNPROVEN")

    def test_missing_owner_route_is_repair_not_quiet_block(self) -> None:
        case = audit()
        case["owners"][0]["owner_binding_state"] = "MISSING"
        self.assertEqual(assess_audit(case)["decision"], "ROUTE_REPAIR_REQUIRED")
        case["owners"][0]["obligations"][0].update({"admission": "ADMITTED", "admission_ref": REF, "authority_ref": REF})
        case["owners"][0]["obligations"][0].pop("hold")
        admitted = assess_audit(case)
        self.assertEqual(admitted["decision"], "ADMITTED_WORK_WITH_ROUTE_GAP")
        self.assertEqual(admitted["owners"][0]["admitted_ids"], ["DOD-06"])
        self.assertFalse(admitted["owners"][0]["owner_wake_allowed"])
        case["owners"][0]["task_state"] = "active"
        active = assess_audit(case)
        self.assertEqual(active["decision"], "OWNER_WORK_IN_PROGRESS")
        self.assertEqual(active["owners"][0]["route_issues"], ["current_owner_binding"])

    def test_changed_route_fault_changes_incident_fingerprint(self) -> None:
        binding_gap = audit()
        binding_gap["owners"][0]["owner_binding_state"] = "MISSING"
        monitoring_gap = audit()
        monitoring_gap["owners"][0]["monitoring_route_state"] = "UNKNOWN"
        first = assess_audit(binding_gap)
        second = assess_audit(monitoring_gap)
        self.assertEqual(first["decision"], "ROUTE_REPAIR_REQUIRED")
        self.assertEqual(second["decision"], "ROUTE_REPAIR_REQUIRED")
        self.assertNotEqual(first["fingerprint"], second["fingerprint"])

    def test_subset_or_missing_owner_coverage_cannot_claim_program_all_stop(self) -> None:
        subset = audit()
        subset["coverage"]["scope"] = "owner_subset"
        self.assertEqual(assess_audit(subset)["decision"], "ALL_INCLUDED_OWNERS_BLOCKED")
        missing = audit()
        missing["coverage"]["role_ids"].append("owner.web")
        self.assertEqual(assess_audit(missing)["decision"], "OWNER_COVERAGE_UNVERIFIED")

    def test_ready_packet_to_archived_reviewer_is_route_gap(self) -> None:
        case = audit()
        case["ready_packet_targets"] = [{
            "packet_id": "REVIEW-1",
            "target_role_id": "atlas.release-control-plane",
            "target_thread_id": "archived-reviewer",
            "target_native_state": "archived",
            "binding_state": "STALE",
            "evidence_ref": REF,
        }]
        result = assess_audit(case)
        self.assertEqual(result["decision"], "ROUTE_REPAIR_REQUIRED")
        self.assertEqual(result["ready_target_gaps"], ["REVIEW-1"])
        self.assertNotEqual(result["fingerprint"], assess_audit(audit())["fingerprint"])
        case["ready_packet_targets"][0].update({"target_native_state": "active", "binding_state": "VERIFIED"})
        self.assertEqual(assess_audit(case)["decision"], "READY_PACKET_ADMISSION_RECHECK")
        case.pop("ready_packet_targets")
        self.assertEqual(assess_audit(case)["decision"], "READY_PACKET_COVERAGE_UNVERIFIED")

    def test_active_turn_suppresses_duplicate_wake(self) -> None:
        case = audit()
        owner = case["owners"][0]
        owner["task_state"] = "active"
        owner["obligations"][0].update({"admission": "ADMITTED", "admission_ref": REF, "authority_ref": REF})
        owner["obligations"][0].pop("hold")
        self.assertEqual(assess_audit(case)["decision"], "OWNER_WORK_IN_PROGRESS")
        owner["goal_state"] = "BLOCKED"
        blocked = assess_audit(case)["owners"][0]
        self.assertEqual(blocked["decision"], "IN_PROGRESS_NO_DUPLICATE_WAKE")
        self.assertFalse(blocked["owner_wake_allowed"])
        self.assertTrue(blocked["native_goal_resume_required"])

    def test_unknown_obligation_and_incomplete_repeat_evidence_do_not_block(self) -> None:
        case = audit()
        case["owners"][0]["obligations"][0]["admission"] = "UNKNOWN"
        self.assertEqual(assess_audit(case)["decision"], "ALL_STOP_UNPROVEN")
        short = audit()
        short["owners"][0]["same_hold_turns"] = 1
        self.assertEqual(assess_audit(short)["owners"][0]["decision"], "HELD_NOT_YET_WHOLE_GOAL_BLOCKABLE")
        unknown_goal = audit()
        unknown_goal["owners"][0]["goal_state"] = "UNKNOWN"
        self.assertEqual(assess_audit(unknown_goal)["decision"], "ALL_STOP_UNPROVEN")
        bad_count = audit()
        bad_count["owners"][0]["same_hold_turns"] = "three"
        self.assertEqual(assess_audit(bad_count)["decision"], "ALL_STOP_UNPROVEN")

    def test_native_blocked_state_does_not_replace_three_turn_hold_evidence(self) -> None:
        case = audit()
        case["owners"][0]["goal_state"] = "BLOCKED"
        case["owners"][0]["same_hold_turns"] = 1
        self.assertEqual(assess_audit(case)["decision"], "ALL_STOP_UNPROVEN")
        case["owners"][0].pop("same_hold_turns")
        self.assertEqual(assess_audit(case)["decision"], "ALL_STOP_UNPROVEN")
        case["owners"][0]["same_hold_turns"] = 3
        self.assertEqual(assess_audit(case)["decision"], "GENUINE_ALL_STOP")

    def test_strict_candidate_search_rejects_boolean_only_all_held_claim(self) -> None:
        case = audit()
        for obligation in case["owners"][0]["obligations"]:
            obligation.pop("independent_candidate_search")
        self.assertEqual(assess_audit(case)["decision"], "ALL_STOP_UNPROVEN")
        for obligation in case["owners"][0]["obligations"]:
            obligation["independent_candidate_search"] = {
                "evidence_ref": REF,
                "disposition": "NO_ADMITTED_CANDIDATE",
                "candidate_count": 0,
            }
        strict = assess_audit(case)
        self.assertEqual(strict["decision"], "GENUINE_ALL_STOP")
        case["owners"][0]["obligations"][0]["independent_candidate_search"]["evidence_ref"] = REF + "-rechecked"
        self.assertNotEqual(strict["fingerprint"], assess_audit(case)["fingerprint"])
        case["owners"][0]["obligations"][0]["independent_candidate_search"]["candidate_count"] = 1
        self.assertEqual(assess_audit(case)["decision"], "ALL_STOP_UNPROVEN")


if __name__ == "__main__":
    unittest.main()
