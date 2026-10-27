"""Regression cases for false whole-Goal blocks and all-stop decisions."""

import copy
import hashlib
import json
import re
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ops.atlas.assess_owner_goal_continuity import SCHEMA, assess_audit, goal_policy
from ops.atlas import assess_owner_goal_continuity as assessor
from ops.atlas import codex_native_goal_readback as native_readback


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

    def test_incomplete_other_obligation_preserves_blocked_goals_admitted_work(self) -> None:
        case = audit()
        owner = case["owners"][0]
        owner["goal_state"] = "BLOCKED"
        owner["obligations"][0].update(
            {"admission": "ADMITTED", "admission_ref": REF, "authority_ref": REF})
        owner["obligations"][0].pop("hold")
        owner["obligations"][1]["admission"] = "UNKNOWN"
        owner["obligations"][1].pop("hold")
        result = assess_audit(case)
        assessed = result["owners"][0]
        self.assertEqual(result["decision"], "ADMITTED_WORK_REQUIRES_OWNER_ACTION")
        self.assertEqual(assessed["decision"], "BLOCKED_GOAL_HAS_ADMITTED_WORK")
        self.assertEqual(assessed["admitted_ids"], ["DOD-06"])
        self.assertIn("obligation_evidence:DOD-09", assessed["missing"])
        self.assertEqual(assessed["resume_action"], "MANUAL_RESUME_REQUIRED")
        self.assertFalse(assessed["owner_wake_allowed"])
        self.assertFalse(result["authorizes_execution"])

    def test_invalid_prior_proof_changes_fingerprint_then_stabilizes(self) -> None:
        case = audit()
        case["owners"][0]["goal_state"] = "BLOCKED"
        prior = assess_audit(case)
        case["prior_fingerprint"] = prior["fingerprint"]
        invalid = assess_audit(case)
        self.assertEqual(invalid["decision"], "ALL_STOP_UNPROVEN")
        self.assertIn("prior_blocked_hold_comparison", invalid["owners"][0]["missing"])
        self.assertNotEqual(invalid["fingerprint"], prior["fingerprint"])
        self.assertTrue(invalid["changed_since_prior"])
        case["prior_fingerprint"] = invalid["fingerprint"]
        repeated = assess_audit(case)
        self.assertEqual(repeated["fingerprint"], invalid["fingerprint"])
        self.assertFalse(repeated["changed_since_prior"])

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


CALLER = "01a16bc3-fe20-7fa0-b09d-2397622478e8"
TURN = "01a17b50-408f-7870-869f-06294b2db68d"
OTHER = "01a16bbf-57f9-7f12-9c70-94c41430b9b3"
ORIGIN_ITEM = "exec-11111111-1111-4111-8111-111111111111"


class CurrentOwnerAuditTests(unittest.TestCase):
    @contextmanager
    def verified(self):
        case = audit()
        case["coverage"]["scope"] = "owner_subset"
        case["owners"][0].update(thread_id=CALLER, task_state="active")
        program = {"revision": 9, "standing_packets": [], "active_leases": [], "delivery_intents": []}
        native = {"thread": {"id": CALLER, "kind": "codex", "hostId": "local", "status": {"type": "active"}},
                  "turns": [{"id": TURN, "status": "inProgress"}]}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "program.json"
            def write():
                raw = json.dumps(program).encode()
                path.write_bytes(raw)
                case["program_ref"] = "tmp/atlas/autonomous-work-program.json#revision=9#sha256=" + hashlib.sha256(raw).hexdigest()
            write()
            with patch.object(assessor, "PROGRAM_PATH", path), patch.dict("os.environ", {"CODEX_THREAD_ID": CALLER}, clear=True), \
                    patch.object(assessor, "_read_current_native_turn", return_value=native) as read:
                self.native = native
                yield case, program, native, read, write, path

    def run_self(self, case, turn=TURN):
        marker = assessor._origin_marker(case, CALLER, turn, case["program_ref"].split("#sha256=")[1])
        item = {
            "id": ORIGIN_ITEM, "type": "commandExecution", "status": "completed", "exitCode": 0,
            "cwd": str(assessor.POLICY_PATH.parents[2]),
            "command": '"C:\\native\\pwsh.exe" -Command "Write-Output \'' + marker + '\'"',
        }
        if self.native.get("turns"):
            self.native["turns"][0]["items"] = [item]
        return assessor.assess_current_owner_audit(case, current_owner_turn=turn,
                                                   owner_origin_item=ORIGIN_ITEM)

    def test_current_owner_can_assess_all_held_scope_without_claiming_program_stop(self):
        with self.verified() as (case, _, _, read, _, _):
            result = self.run_self(case)
            self.assertEqual(result["decision"], "ALL_INCLUDED_OWNERS_BLOCKED")
            self.assertEqual(result["owners"][0]["decision"], "WHOLE_GOAL_BLOCK_PROVEN")
            self.assertFalse(result["authorizes_execution"])
            self.assertFalse(result["owners"][0]["owner_wake_allowed"])
            self.assertEqual(read.call_count, 2)
            self.assertEqual(result["current_owner_self_audit"]["turn_id"], TURN)
            self.assertEqual(result["current_owner_self_audit"]["owner_origin_item_id"], ORIGIN_ITEM)

    def test_mutable_environment_and_active_turn_without_host_origin_fail_closed(self):
        with self.verified() as (case, _, native, read, _, _):
            self.run_self(case)
            native["turns"][0]["items"] = []
            with self.assertRaisesRegex(ValueError, "OWNER_ORIGIN_UNVERIFIED"):
                assessor.assess_current_owner_audit(case, current_owner_turn=TURN,
                                                   owner_origin_item=ORIGIN_ITEM)
            self.assertEqual(read.call_count, 3)

    def test_owner_origin_binds_exact_audit_program_turn_and_native_item(self):
        with self.verified() as (case, _, native, _, _, _):
            self.run_self(case)
            item = native["turns"][0]["items"][0]
            for mutate in (
                lambda: item.update(type="mcpToolCall"),
                lambda: item.update(status="inProgress"),
                lambda: item.update(exitCode=1),
                lambda: item.update(command=item["command"] + "; Write-Output forged"),
                lambda: item.update(command=item["command"].replace("ATLAS_GOAL_SELF_AUDIT_ORIGIN:", "FORGED:")),
            ):
                with self.subTest(mutate=mutate):
                    original = copy.deepcopy(item)
                    mutate()
                    with self.assertRaisesRegex(ValueError, "OWNER_ORIGIN_UNVERIFIED"):
                        assessor.assess_current_owner_audit(case, current_owner_turn=TURN,
                                                           owner_origin_item=ORIGIN_ITEM)
                    item.clear(); item.update(original)
            changed = copy.deepcopy(case)
            changed["owners"][0]["same_hold_turns"] += 1
            with self.assertRaisesRegex(ValueError, "OWNER_ORIGIN_UNVERIFIED"):
                assessor.assess_current_owner_audit(changed, current_owner_turn=TURN,
                                                   owner_origin_item=ORIGIN_ITEM)
            with self.assertRaisesRegex(ValueError, "OWNER_ORIGIN_UNVERIFIED"):
                assessor.assess_current_owner_audit(case, current_owner_turn=TURN,
                                                   owner_origin_item="exec-22222222-2222-4222-8222-222222222222")

    def test_origin_is_bound_to_native_owner_turn_not_process_working_directory(self):
        with self.verified() as (case, _, native, _, _, _):
            self.run_self(case)
            native["turns"][0]["items"][0]["cwd"] = "C:\\"
            result = assessor.assess_current_owner_audit(case, current_owner_turn=TURN,
                                                          owner_origin_item=ORIGIN_ITEM)
            self.assertEqual(result["owners"][0]["decision"], "WHOLE_GOAL_BLOCK_PROVEN")

    def test_self_audit_preserves_published_changed_blocked_hold_gate(self):
        with self.verified() as (case, *_):
            case["owners"][0]["goal_state"] = "BLOCKED"
            prior = self.run_self(case)
            case["prior_fingerprint"] = prior["fingerprint"]
            case["owners"][0]["obligations"][0]["hold"]["unblock_condition"] = "Changed condition"
            with patch.object(assessor, "_verified_prior_assessment", return_value=prior):
                changed = self.run_self(case)
            self.assertEqual(changed["decision"], "BLOCKED_GOAL_MANUAL_RESUME_REQUIRED")
            self.assertEqual(changed["owners"][0]["decision"], "BLOCKED_GOAL_UNBLOCK_CONDITION_CHANGED")
            self.assertEqual(changed["owners"][0]["resume_action"], "MANUAL_RESUME_REQUIRED")
            self.assertFalse(changed["authorizes_execution"])
            without_prior_proof = self.run_self(case)
            self.assertEqual(without_prior_proof["decision"], "ALL_STOP_UNPROVEN")
            self.assertIn("prior_blocked_hold_comparison", without_prior_proof["owners"][0]["missing"])

    def test_default_external_watch_ignores_serialized_self_audit_claim(self):
        with self.verified() as (case, *_):
            case["current_owner_self_audit"] = {"thread_id": CALLER, "turn_id": TURN, "verified": True}
            self.assertEqual(assess_audit(case)["decision"], "OWNER_WORK_IN_PROGRESS")

    def test_self_audit_preserves_all_existing_scope_and_hold_gates(self):
        mutations = [
            lambda c: c["owners"][0].update(goal_state="UNKNOWN"),
            lambda c: c["owners"][0].update(same_hold_turns=2),
            lambda c: c["owners"][0]["obligations"].pop(),
            lambda c: c["owners"][0]["obligations"][0].pop("independent_candidate_search"),
            lambda c: c["owners"][0]["obligations"][0]["independent_candidate_search"].update(candidate_count=1),
            lambda c: c["owners"][0].update(monitoring_route_state="UNKNOWN"),
            lambda c: c["owners"][0].update(equivalent_delivery_active=True),
            lambda c: c["owners"][0]["obligations"][0].update(admission="ADMITTED", admission_ref=REF, authority_ref=REF),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate), self.verified() as (case, *_):
                mutate(case)
                result = self.run_self(case)
                self.assertNotEqual(result["owners"][0]["decision"], "WHOLE_GOAL_BLOCK_PROVEN")
                self.assertFalse(result["authorizes_execution"])

    def test_requires_actual_caller_and_exact_single_owner_subset(self):
        with self.verified() as (case, *_):
            for value in ("", "forged", OTHER):
                with self.subTest(caller=value), patch.dict("os.environ", {"CODEX_THREAD_ID": value}, clear=True):
                    with self.assertRaisesRegex(ValueError, "SELF_AUDIT_"):
                        self.run_self(case)
            for mutate in (lambda c: c["coverage"].update(scope="complete_critical_path"),
                           lambda c: c["owners"].append(copy.deepcopy(c["owners"][0])),
                           lambda c: c["owners"][0].update(task_state="idle")):
                wrong = copy.deepcopy(case); mutate(wrong)
                with self.assertRaisesRegex(ValueError, "EXACT_OWNER_SUBSET_REQUIRED"):
                    self.run_self(wrong)
            with patch.dict("os.environ", {"CODEX_TURN_ID": OTHER}):
                with self.assertRaisesRegex(ValueError, "EXECUTOR_TURN_MISMATCH"):
                    self.run_self(case)

    def test_native_foreign_stale_idle_or_unavailable_readback_fails_closed(self):
        mutations = [lambda n: n["thread"].update(id=OTHER), lambda n: n["thread"].update(hostId="remote"),
                     lambda n: n["thread"].update(kind="chatgpt"), lambda n: n["thread"]["status"].update(type="idle"),
                     lambda n: n["turns"][0].update(id=OTHER), lambda n: n["turns"][0].update(status="completed"),
                     lambda n: n.update(turns=[])]
        for mutate in mutations:
            with self.subTest(mutation=mutate), self.verified() as (case, _, native, _, _, _):
                mutate(native)
                with self.assertRaisesRegex(ValueError, "CURRENT_NATIVE_TURN_UNVERIFIED"):
                    self.run_self(case)
        with self.verified() as (case, _, native, read, _, _):
            stale = copy.deepcopy(native); stale["turns"][0]["status"] = "completed"
            read.side_effect = [native, stale]
            with self.assertRaisesRegex(ValueError, "CURRENT_NATIVE_TURN_UNVERIFIED"):
                self.run_self(case)

    def test_requires_exact_current_canonical_program_and_rechecks_drift(self):
        with self.verified() as (case, _, _, _, _, path):
            path.write_text("{}")
            with self.assertRaisesRegex(ValueError, "CURRENT_PROGRAM_DRIFT"):
                self.run_self(case)
        with self.verified() as (case, _, native, read, _, path):
            def drift(*args):
                path.write_text("{}")
                return native
            read.side_effect = drift
            with self.assertRaisesRegex(ValueError, "CURRENT_PROGRAM_DRIFT"):
                self.run_self(case)

    def test_current_owner_ready_packet_lease_and_intent_cannot_be_excluded(self):
        for lane in ("ready", "active_leases", "delivery_intents"):
            with self.subTest(lane=lane), self.verified() as (case, program, _, _, write, _):
                program["standing_packets"].append({"packet_id": "P1", "logical_role_id": case["owners"][0]["role_id"],
                                                    "runtime_thread_id": OTHER, "state": "READY" if lane == "ready" else "BLOCKED"})
                if lane != "ready":
                    program[lane].append({"packet_id": "P1"})
                write()
                with self.assertRaisesRegex(ValueError, "SELF_AUDIT_(OWNER_READY_WORK|EQUIVALENT_DELIVERY_ACTIVE)"):
                    self.run_self(case)

    def test_every_scheduler_ready_state_blocks_self_audit(self):
        from ops.atlas.autonomous_lane_scheduler import READY_STATES

        self.assertEqual(READY_STATES, {"READY", "ADMITTED", "QUEUED"})
        for state in READY_STATES:
            with self.subTest(state=state), self.verified() as (case, program, _, _, write, _):
                program["standing_packets"].append({
                    "packet_id": "P-ready", "logical_role_id": case["owners"][0]["role_id"],
                    "runtime_thread_id": OTHER, "state": state})
                write()
                with self.assertRaisesRegex(ValueError, "SELF_AUDIT_OWNER_READY_WORK"):
                    self.run_self(case)

    def test_owner_return_correlates_delegated_packet_and_active_delivery(self):
        target = {"thread_id": OTHER, "logical_role_id": "owner.other"}
        owner_return = {"thread_id": CALLER, "logical_role_id": "owner.workflow-operations"}
        for lane in ("packet", "active_leases", "delivery_intents"):
            with self.subTest(lane=lane), self.verified() as (case, program, _, _, write, _):
                packet = {"packet_id": "P-delegated", "state": "BLOCKED",
                          "execution_target": target}
                if lane == "packet":
                    packet.update(state="ADMITTED", owner_return=owner_return)
                program["standing_packets"].append(packet)
                if lane != "packet":
                    program[lane].append({"packet_id": "P-delegated",
                                          "execution_target": target,
                                          "owner_return": owner_return})
                write()
                with self.assertRaisesRegex(
                        ValueError, "SELF_AUDIT_(OWNER_READY_WORK|EQUIVALENT_DELIVERY_ACTIVE)"):
                    self.run_self(case)

    def test_malformed_owner_return_fails_closed(self):
        with self.verified() as (case, program, _, _, write, _):
            program["standing_packets"].append({
                "packet_id": "P-unknown", "state": "QUEUED",
                "execution_target": {"thread_id": OTHER}, "owner_return": "unknown"})
            write()
            with self.assertRaisesRegex(ValueError, "SELF_AUDIT_WORK_OWNER_UNKNOWN"):
                self.run_self(case)

    def test_active_delegated_packet_without_lease_cannot_prove_hold(self):
        with self.verified() as (case, program, _, _, write, _):
            program["standing_packets"].append({
                "packet_id": "P-active", "state": "ACTIVE",
                "execution_target": {"thread_id": OTHER, "logical_role_id": "owner.other"},
                "owner_return": {"thread_id": CALLER,
                                 "logical_role_id": "owner.workflow-operations"}})
            write()
            with self.assertRaisesRegex(ValueError, "SELF_AUDIT_EQUIVALENT_DELIVERY_ACTIVE"):
                self.run_self(case)

    def test_separate_owner_work_does_not_suppress_current_owner_hold(self):
        with self.verified() as (case, program, _, _, write, _):
            program["standing_packets"].append({"packet_id": "P2", "logical_role_id": "owner.other", "runtime_thread_id": OTHER, "state": "READY"})
            program["active_leases"].append({"packet_id": "P2"})
            program["delivery_intents"].append({"packet_id": "P2"})
            write()
            self.assertEqual(self.run_self(case)["decision"], "ALL_INCLUDED_OWNERS_BLOCKED")
            program["standing_packets"][0]["execution_target"] = {"thread_id": CALLER}
            write()
            with self.assertRaisesRegex(ValueError, "OWNER_READY_WORK"):
                self.run_self(case)

    def test_unknown_active_owner_or_packet_correlation_cannot_prove_hold(self):
        for mutation in (lambda p: p["standing_packets"].append({"packet_id": "P", "state": "READY"}),
                         lambda p: p["active_leases"].append({"packet_id": "missing"}),
                         lambda p: p["delivery_intents"].append({"packet_id": "missing"})):
            with self.verified() as (case, program, _, _, write, _):
                mutation(program); write()
                with self.assertRaisesRegex(ValueError, "SELF_AUDIT_(WORK_OWNER_UNKNOWN|PACKET_CORRELATION_UNKNOWN)"):
                    self.run_self(case)

    def test_changed_input_during_verification_is_rejected(self):
        with self.verified() as (case, _, native, read, _, _):
            def mutate(*args):
                case["owners"][0]["same_hold_turns"] = 99
                return native
            read.side_effect = mutate
            with self.assertRaisesRegex(ValueError, "EVIDENCE_DRIFT"):
                self.run_self(case)

    def test_executor_drift_is_rejected(self):
        import os
        with self.verified() as (case, _, native, read, _, _):
            def mutate(*args):
                os.environ["CODEX_THREAD_ID"] = OTHER
                return native
            read.side_effect = mutate
            with self.assertRaisesRegex(ValueError, "EXECUTOR_IDENTITY_DRIFT"):
                self.run_self(case)

    def test_cli_invalid_self_mode_reports_hold_and_nonzero_exit(self):
        import io
        from contextlib import redirect_stdout
        with self.verified() as (case, *_), tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "audit.json"; path.write_text(json.dumps(case))
            with patch("sys.argv", ["assessor", str(path), "--current-owner-turn", "forged"]), redirect_stdout(io.StringIO()) as output:
                self.assertEqual(assessor.main(), 2)
            result = json.loads(output.getvalue())
            self.assertEqual(result["decision"], "AUDIT_VALIDATION_HOLD")
            self.assertFalse(result["authorizes_execution"])

    def test_semantic_fingerprint_excludes_current_native_turn_metadata(self):
        with self.verified() as (case, _, native, _, _, _):
            first = self.run_self(case)
            native["turns"][0]["id"] = OTHER
            second = self.run_self(case, turn=OTHER)
            self.assertEqual(first["fingerprint"], second["fingerprint"])


class NativeReadbackBridgeTests(unittest.TestCase):
    @contextmanager
    def mocked_lifecycle(self):
        process = Mock()
        process.stdin = Mock()
        process.stdout = Mock()
        process.stderr = Mock()
        first, second = Mock(), Mock()
        client = native_readback.CodexNativeReadbackClient()
        with patch.object(client, "_command", return_value=(["node", "server.mjs"], Path("."))), \
                patch.object(native_readback.subprocess, "Popen", return_value=process), \
                patch.object(native_readback, "threading",
                             SimpleNamespace(Thread=Mock(side_effect=[first, second]))), \
                patch.object(client, "_write"):
            yield client, process, first, second

    def test_second_reader_start_failure_cleans_owned_helper(self):
        with self.mocked_lifecycle() as (client, process, first, second):
            second.start.side_effect = RuntimeError("second reader failed")
            with self.assertRaisesRegex(RuntimeError, "second reader failed"):
                client.__enter__()
            self.assertIsNone(client.process)
            process.stdin.close.assert_called_once()
            process.wait.assert_called_once()
            first.join.assert_called_once()
            second.join.assert_not_called()
            process.stdout.close.assert_called_once()
            process.stderr.close.assert_called_once()

    def test_init_failure_and_normal_close_are_bounded_and_idempotent(self):
        with self.mocked_lifecycle() as (client, process, first, second), \
                patch.object(client, "_request", side_effect=native_readback.NativeReadbackError("init")):
            with self.assertRaises(native_readback.NativeReadbackError):
                client.__enter__()
            process.wait.assert_called_once()
            first.join.assert_called_once()
            second.join.assert_called_once()
            process.stdin.close.assert_called_once()
        with self.mocked_lifecycle() as (client, process, first, second), \
                patch.object(client, "_request", return_value={}):
            self.assertIs(client.__enter__(), client)
            client.__exit__(None, None, None)
            client.__exit__(None, None, None)
            process.wait.assert_called_once()
            first.join.assert_called_once()
            second.join.assert_called_once()
            process.stdin.close.assert_called_once()

    def test_close_timeout_terminates_then_joins_and_closes(self):
        with self.mocked_lifecycle() as (client, process, first, second), \
                patch.object(client, "_request", return_value={}):
            process.wait.side_effect = [subprocess.TimeoutExpired("node", 2), 0]
            client.__enter__()
            client.__exit__(None, None, None)
            self.assertEqual(process.wait.call_count, 2)
            process.terminate.assert_called_once()
            first.join.assert_called_once()
            second.join.assert_called_once()
            process.stdout.close.assert_called_once()

    def test_second_close_timeout_kills_only_owned_helper(self):
        with self.mocked_lifecycle() as (client, process, first, second), \
                patch.object(client, "_request", return_value={}):
            process.wait.side_effect = [subprocess.TimeoutExpired("node", 2),
                                        subprocess.TimeoutExpired("node", 2), 0]
            client.__enter__()
            client.__exit__(None, None, None)
            self.assertEqual(process.wait.call_count, 3)
            process.terminate.assert_called_once()
            process.kill.assert_called_once()
            first.join.assert_called_once()
            second.join.assert_called_once()
            process.stderr.close.assert_called_once()

    def test_bridge_uses_named_owner_lookup_hint(self):
        client = native_readback.CodexNativeReadbackClient()
        with patch.dict("os.environ", {"CODEX_THREAD_ID": CALLER, "CODEX_TURN_ID": TURN}, clear=True), \
                patch.object(client, "_request", return_value={"content": [{"type": "text", "text": "{}"}]}) as request:
            client.read_current_thread(CALLER, TURN)
        method, payload = request.call_args.args
        self.assertEqual(method, "tools/call")
        self.assertEqual(payload["name"], "read_thread")
        self.assertEqual(payload["arguments"]["threadId"], CALLER)
        self.assertEqual(payload["_meta"]["openai/threadId"], CALLER)
        self.assertEqual(payload["_meta"]["openai/turnId"], TURN)
        self.assertTrue(payload["_meta"]["openai/toolCallId"].startswith("goal-readback-"))

    def test_bridge_rejects_missing_executor_before_transport(self):
        client = native_readback.CodexNativeReadbackClient()
        with patch.dict("os.environ", {}, clear=True), \
                patch.object(client, "_request") as request:
            with self.assertRaises(native_readback.NativeReadbackError):
                client.read_current_thread(CALLER, TURN)
            request.assert_not_called()
        with patch.dict("os.environ", {}, clear=True), \
                patch.object(native_readback, "CodexNativeReadbackClient") as helper:
            with self.assertRaises(native_readback.NativeReadbackError):
                native_readback.read_current_native_turn(CALLER, TURN)
            helper.assert_not_called()

    def test_readback_decodes_supported_tool_payload(self):
        native = {"thread": {"id": CALLER}, "turns": [{"id": TURN}]}

        class FakeClient:
            def __enter__(self):
                return self

            def read_current_thread(self, caller, turn_id):
                self.caller = caller
                self.turn_id = turn_id
                return native

            def __exit__(self, *args):
                return None

        with patch.dict("os.environ", {"CODEX_THREAD_ID": CALLER}, clear=True), \
                patch.object(native_readback, "CodexNativeReadbackClient", FakeClient):
            self.assertEqual(assessor._read_current_native_turn(CALLER, TURN), native)


if __name__ == "__main__":
    unittest.main()
