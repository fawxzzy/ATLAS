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
    CONTRACT_RECEIPT_REFS as COMMAND_HOME_CONTRACT_RECEIPT_REFS,
    QUESTION_PROMPT as COMMAND_HOME_QUESTION_PROMPT,
)
from ops.atlas.supervised_execution_home_concrete_command_home import (
    CONCRETE_COMMAND_HOME_STATUS_ADMISSIBLE,
    CONTRACT_RECEIPT_REFS,
    NO_CONCRETE_COMMAND_HOME,
    QUESTION_PROMPT,
    evaluate_supervised_execution_home_concrete_command_home,
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
        "command_home_selection_status": COMMAND_HOME_SELECTION_STATUS_ADMISSIBLE,
        "command_home_selection_question": {
            "question": COMMAND_HOME_QUESTION_PROMPT,
            "candidate_ref": candidate_ref,
            "authoritative_receipt_refs": list(COMMAND_HOME_CONTRACT_RECEIPT_REFS),
        },
        "command_home_selection_reasons": [],
    }


class SupervisedExecutionHomeConcreteCommandHomeTests(unittest.TestCase):
    def _evaluate(self, bundle: dict[str, object]) -> dict[str, object]:
        payload = evaluate_supervised_execution_home_concrete_command_home(bundle)
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
                "concrete_command_home_status",
                "concrete_command_home_question",
                "concrete_command_home_reasons",
            },
            set(payload.keys()),
        )
        return payload

    def test_admissible_result_reopens_one_contract_local_question(self) -> None:
        payload = self._evaluate(_base_result())

        self.assertEqual(CONCRETE_COMMAND_HOME_STATUS_ADMISSIBLE, payload["concrete_command_home_status"])
        self.assertEqual([], payload["concrete_command_home_reasons"])
        self.assertEqual(
            {
                "question",
                "candidate_ref",
                "authoritative_receipt_refs",
            },
            set(payload["concrete_command_home_question"].keys()),
        )
        self.assertEqual(QUESTION_PROMPT, payload["concrete_command_home_question"]["question"])
        self.assertEqual(
            "repos/example/.worktrees/pilot-a",
            payload["concrete_command_home_question"]["candidate_ref"],
        )
        self.assertEqual(
            list(CONTRACT_RECEIPT_REFS),
            payload["concrete_command_home_question"]["authoritative_receipt_refs"],
        )

    def test_non_admissible_upstream_status_fails_closed(self) -> None:
        bundle = _base_result()
        bundle["command_home_selection_status"] = "no_command_home_selection"

        payload = self._evaluate(bundle)

        self.assertEqual(NO_CONCRETE_COMMAND_HOME, payload["concrete_command_home_status"])
        self.assertIsNone(payload["concrete_command_home_question"])
        self.assertEqual(
            ["command_home_selection_status_not_admissible"],
            payload["concrete_command_home_reasons"],
        )

    def test_non_explicit_question_card_or_upstream_reasons_fail_closed(self) -> None:
        cases = (
            (
                "question_card_missing_field",
                {"command_home_selection_question": {"question": "x", "candidate_ref": "repos/example/.worktrees/pilot-a"}},
                ["command_home_selection_question_not_explicit"],
            ),
            (
                "upstream_reasons_present",
                {"command_home_selection_reasons": ["payload_not_explicit"]},
                ["command_home_selection_reasons_present"],
            ),
        )
        for _, updates, expected_reasons in cases:
            with self.subTest(updates=updates):
                bundle = _base_result()
                bundle.update(updates)

                payload = self._evaluate(bundle)

                self.assertEqual(NO_CONCRETE_COMMAND_HOME, payload["concrete_command_home_status"])
                self.assertIsNone(payload["concrete_command_home_question"])
                self.assertEqual(expected_reasons, payload["concrete_command_home_reasons"])

    def test_result_class_and_posture_drift_fail_closed(self) -> None:
        cases = (
            ("result_class", "candidate-missing", ["result_class_not_contract_visible"]),
            ("command", "stack something-else", ["command_not_stack_supervised_execution_home"]),
            ("routing_note", "different routing note", ["routing_note_not_posture_only"]),
            ("normalized_candidate_path", "", ["normalized_candidate_path_missing"]),
            ("owner_surface", "different owner surface", ["owner_surface_not_explicit"]),
            ("support_posture", "needs support", ["support_posture_not_none_yet"]),
        )
        for field, value, expected_reasons in cases:
            with self.subTest(field=field):
                bundle = _base_result()
                if field == "normalized_candidate_path":
                    bundle["command_home_selection_question"] = {
                        "question": COMMAND_HOME_QUESTION_PROMPT,
                        "candidate_ref": "",
                        "authoritative_receipt_refs": list(COMMAND_HOME_CONTRACT_RECEIPT_REFS),
                    }
                bundle[field] = value

                payload = self._evaluate(bundle)

                self.assertEqual(NO_CONCRETE_COMMAND_HOME, payload["concrete_command_home_status"])
                self.assertIsNone(payload["concrete_command_home_question"])
                self.assertEqual(expected_reasons, payload["concrete_command_home_reasons"])

    def test_invented_concrete_command_home_runtime_or_authority_inputs_fail_closed(self) -> None:
        cases = (
            ("concrete_command_home", "_stack", ["concrete_command_home_choice_invented"]),
            ("command_file", "repos/_stack/cmd.py", ["concrete_command_file_inference_invented"]),
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

                self.assertEqual(NO_CONCRETE_COMMAND_HOME, payload["concrete_command_home_status"])
                self.assertIsNone(payload["concrete_command_home_question"])
                self.assertEqual(expected_reasons, payload["concrete_command_home_reasons"])

    def test_non_explicit_payload_fails_closed(self) -> None:
        bundle = _base_result()
        payload = copy.deepcopy(bundle["payload"])
        del payload["blocked_question_summary"]
        bundle["payload"] = payload

        result = self._evaluate(bundle)

        self.assertEqual(NO_CONCRETE_COMMAND_HOME, result["concrete_command_home_status"])
        self.assertIsNone(result["concrete_command_home_question"])
        self.assertEqual(["payload_not_explicit"], result["concrete_command_home_reasons"])


if __name__ == "__main__":
    unittest.main()
