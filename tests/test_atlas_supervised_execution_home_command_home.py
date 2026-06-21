from __future__ import annotations

import copy
import unittest

from ops.atlas.supervised_execution_home import (
    ACTUAL_MUTATION_RESULT_REF,
    BLOCKED_QUESTIONS,
    COMMAND,
    OWNER_SURFACE,
    RESULT_CLASS_CONTRACT_VISIBLE,
    SUCCESS_ROUTING_NOTE,
    SUPPORT_POSTURE,
)
from ops.atlas.supervised_execution_home_command_home import (
    COMMAND_HOME_SELECTION_STATUS_ADMISSIBLE,
    CONTRACT_RECEIPT_REFS,
    NO_COMMAND_HOME_SELECTION,
    QUESTION_PROMPT,
    evaluate_supervised_execution_home_command_home,
)


def _base_result() -> dict[str, object]:
    candidate_ref = "repos/example/.worktrees/pilot-a"
    return {
        "command": COMMAND,
        "normalized_candidate_path": candidate_ref,
        "result_class": RESULT_CLASS_CONTRACT_VISIBLE,
        "owner_surface": OWNER_SURFACE,
        "support_posture": SUPPORT_POSTURE,
        "admitted_evidence_refs": [
            ACTUAL_MUTATION_RESULT_REF,
            "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-COMMAND-DESIGN-PASS-518-2026-06-21.md",
            "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-EVIDENCE-ADMISSION-AND-CONTRADICTION-DISCIPLINE-PASS-519-2026-06-21.md",
            "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-REPORT-CONTRACT-AND-NO-MUTATION-GUARD-PASS-520-2026-06-21.md",
            "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-IMPLEMENTATION-ADMISSION-AND-NO-MUTATION-GUARD-PASS-521-2026-06-21.md",
        ],
        "blocked_questions": list(BLOCKED_QUESTIONS),
        "routing_note": SUCCESS_ROUTING_NOTE,
        "payload": {
            "candidate_ref": candidate_ref,
            "owner_surface_statement": OWNER_SURFACE,
            "support_posture_statement": SUPPORT_POSTURE,
            "admitted_evidence_summary": (
                "explicit actual_owner_side_mutation result plus authoritative pass-518-through-pass-521 "
                "supervised execution-home contract receipts"
            ),
            "blocked_question_summary": (
                "command-home, runtime-home, worker-authority, owner-repo-edit, and doctrine-export "
                "decisions remain deferred beyond this posture-only report"
            ),
            "authoritative_receipt_refs": [
                "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-COMMAND-DESIGN-PASS-518-2026-06-21.md",
                "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-EVIDENCE-ADMISSION-AND-CONTRADICTION-DISCIPLINE-PASS-519-2026-06-21.md",
                "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-REPORT-CONTRACT-AND-NO-MUTATION-GUARD-PASS-520-2026-06-21.md",
                "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-IMPLEMENTATION-ADMISSION-AND-NO-MUTATION-GUARD-PASS-521-2026-06-21.md",
            ],
        },
    }


class SupervisedExecutionHomeCommandHomeTests(unittest.TestCase):
    def _evaluate(self, bundle: dict[str, object]) -> dict[str, object]:
        payload = evaluate_supervised_execution_home_command_home(bundle)
        self.assertEqual(
            {
                "command",
                "normalized_candidate_path",
                "result_class",
                "owner_surface",
                "support_posture",
                "admitted_evidence_refs",
                "blocked_questions",
                "routing_note",
                "payload",
                "command_home_selection_status",
                "command_home_selection_question",
                "command_home_selection_reasons",
            },
            set(payload.keys()),
        )
        return payload

    def test_contract_visible_result_reopens_one_contract_local_question(self) -> None:
        payload = self._evaluate(_base_result())

        self.assertEqual(COMMAND_HOME_SELECTION_STATUS_ADMISSIBLE, payload["command_home_selection_status"])
        self.assertEqual([], payload["command_home_selection_reasons"])
        self.assertEqual(
            {
                "question",
                "candidate_ref",
                "authoritative_receipt_refs",
            },
            set(payload["command_home_selection_question"].keys()),
        )
        self.assertEqual(QUESTION_PROMPT, payload["command_home_selection_question"]["question"])
        self.assertEqual(
            "repos/example/.worktrees/pilot-a",
            payload["command_home_selection_question"]["candidate_ref"],
        )
        self.assertEqual(
            list(CONTRACT_RECEIPT_REFS),
            payload["command_home_selection_question"]["authoritative_receipt_refs"],
        )

    def test_non_contract_visible_result_fails_closed(self) -> None:
        for result_class in ("candidate-missing", "candidate-non-admissible", "contract-truth-unavailable"):
            with self.subTest(result_class=result_class):
                bundle = _base_result()
                bundle["result_class"] = result_class

                payload = self._evaluate(bundle)

                self.assertEqual(NO_COMMAND_HOME_SELECTION, payload["command_home_selection_status"])
                self.assertIsNone(payload["command_home_selection_question"])
                self.assertEqual(
                    ["result_class_not_contract_visible"],
                    payload["command_home_selection_reasons"],
                )

    def test_command_routing_candidate_and_owner_drift_fail_closed(self) -> None:
        cases = (
            ("command", "stack something-else", ["command_not_stack_supervised_execution_home"]),
            ("routing_note", "different routing note", ["routing_note_not_posture_only"]),
            ("normalized_candidate_path", "", ["normalized_candidate_path_missing"]),
            ("owner_surface", "different owner surface", ["owner_surface_not_explicit"]),
            ("support_posture", "needs support", ["support_posture_not_none_yet"]),
        )
        for field, value, expected_reasons in cases:
            with self.subTest(field=field):
                bundle = _base_result()
                bundle[field] = value

                payload = self._evaluate(bundle)

                self.assertEqual(NO_COMMAND_HOME_SELECTION, payload["command_home_selection_status"])
                self.assertIsNone(payload["command_home_selection_question"])
                self.assertEqual(expected_reasons, payload["command_home_selection_reasons"])

    def test_invented_command_home_runtime_or_authority_inputs_fail_closed(self) -> None:
        cases = (
            ("command_home", "_stack", ["command_home_inference_invented"]),
            ("command_file", "repos/_stack/cmd.py", ["command_home_inference_invented"]),
            ("runtime_home", "_stack", ["runtime_home_inference_invented"]),
            ("worker_authority", "launch", ["worker_authority_invented"]),
            ("owner_repo_edit_authority", True, ["owner_repo_edit_authority_invented"]),
            (
                "actual_owner_side_mutation_authority",
                True,
                ["actual_owner_side_mutation_authority_invented"],
            ),
            ("playbook_doctrine_export", True, ["playbook_doctrine_export_invented"]),
        )
        for field, value, expected_reasons in cases:
            with self.subTest(field=field):
                bundle = _base_result()
                bundle[field] = value

                payload = self._evaluate(bundle)

                self.assertEqual(NO_COMMAND_HOME_SELECTION, payload["command_home_selection_status"])
                self.assertIsNone(payload["command_home_selection_question"])
                self.assertEqual(expected_reasons, payload["command_home_selection_reasons"])

    def test_non_explicit_payload_fails_closed(self) -> None:
        bundle = _base_result()
        payload = copy.deepcopy(bundle["payload"])
        del payload["blocked_question_summary"]
        bundle["payload"] = payload

        result = self._evaluate(bundle)

        self.assertEqual(NO_COMMAND_HOME_SELECTION, result["command_home_selection_status"])
        self.assertIsNone(result["command_home_selection_question"])
        self.assertEqual(["payload_not_explicit"], result["command_home_selection_reasons"])


if __name__ == "__main__":
    unittest.main()
