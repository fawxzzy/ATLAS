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
from ops.atlas.supervised_execution_home_actual_concrete_runtime_home_choice import (
    ACTUAL_CONCRETE_RUNTIME_HOME_CHOICE_STATUS_ADMISSIBLE,
    CONTRACT_RECEIPT_REFS,
    NO_ACTUAL_CONCRETE_RUNTIME_HOME_CHOICE,
    QUESTION_PROMPT,
    evaluate_supervised_execution_home_actual_concrete_runtime_home_choice,
)
from ops.atlas.supervised_execution_home_command_home import (
    COMMAND_HOME_SELECTION_STATUS_ADMISSIBLE,
    CONTRACT_RECEIPT_REFS as COMMAND_HOME_CONTRACT_RECEIPT_REFS,
    QUESTION_PROMPT as COMMAND_HOME_QUESTION_PROMPT,
)
from ops.atlas.supervised_execution_home_concrete_command_file import (
    evaluate_supervised_execution_home_concrete_command_file,
)
from ops.atlas.supervised_execution_home_concrete_command_home import (
    CONCRETE_COMMAND_HOME_STATUS_ADMISSIBLE,
    CONTRACT_RECEIPT_REFS as CONCRETE_COMMAND_HOME_CONTRACT_RECEIPT_REFS,
    QUESTION_PROMPT as CONCRETE_COMMAND_HOME_QUESTION_PROMPT,
)
from ops.atlas.supervised_execution_home_concrete_runtime_home_choice import (
    CONCRETE_RUNTIME_HOME_CHOICE_STATUS_ADMISSIBLE,
    CONTRACT_RECEIPT_REFS as CONCRETE_RUNTIME_HOME_CHOICE_CONTRACT_RECEIPT_REFS,
    QUESTION_PROMPT as CONCRETE_RUNTIME_HOME_CHOICE_QUESTION_PROMPT,
    evaluate_supervised_execution_home_concrete_runtime_home_choice,
)
from ops.atlas.supervised_execution_home_concrete_stack_command_home import (
    CONCRETE_STACK_COMMAND_HOME_SELECTION_STATUS_ADMISSIBLE,
    CONTRACT_RECEIPT_REFS as CONCRETE_STACK_COMMAND_HOME_CONTRACT_RECEIPT_REFS,
    QUESTION_PROMPT as CONCRETE_STACK_COMMAND_HOME_QUESTION_PROMPT,
)
from ops.atlas.supervised_execution_home_concrete_stack_command_implementation_surface import (
    evaluate_supervised_execution_home_concrete_stack_command_implementation_surface,
)
from ops.atlas.supervised_execution_home_runtime_home_choice import (
    CONTRACT_RECEIPT_REFS as RUNTIME_HOME_CHOICE_CONTRACT_RECEIPT_REFS,
    QUESTION_PROMPT as RUNTIME_HOME_CHOICE_QUESTION_PROMPT,
    RUNTIME_HOME_CHOICE_STATUS_ADMISSIBLE,
    evaluate_supervised_execution_home_runtime_home_choice,
)
from ops.atlas.supervised_execution_home_runtime_home_selection import (
    evaluate_supervised_execution_home_runtime_home_selection,
)


def _upstream_bundle() -> dict[str, object]:
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
        "concrete_command_home_status": CONCRETE_COMMAND_HOME_STATUS_ADMISSIBLE,
        "concrete_command_home_question": {
            "question": CONCRETE_COMMAND_HOME_QUESTION_PROMPT,
            "candidate_ref": candidate_ref,
            "authoritative_receipt_refs": list(CONCRETE_COMMAND_HOME_CONTRACT_RECEIPT_REFS),
        },
        "concrete_command_home_reasons": [],
        "concrete_stack_command_home_selection_status": (
            CONCRETE_STACK_COMMAND_HOME_SELECTION_STATUS_ADMISSIBLE
        ),
        "concrete_stack_command_home_selection_question": {
            "question": CONCRETE_STACK_COMMAND_HOME_QUESTION_PROMPT,
            "candidate_ref": candidate_ref,
            "authoritative_receipt_refs": list(CONCRETE_STACK_COMMAND_HOME_CONTRACT_RECEIPT_REFS),
        },
        "concrete_stack_command_home_selection_reasons": [],
    }


def _base_result() -> dict[str, object]:
    concrete_command_file_result = evaluate_supervised_execution_home_concrete_command_file(
        _upstream_bundle()
    )
    runtime_home_selection_input = (
        evaluate_supervised_execution_home_concrete_stack_command_implementation_surface(
            concrete_command_file_result
        )
    )
    runtime_home_choice_input = evaluate_supervised_execution_home_runtime_home_selection(
        runtime_home_selection_input
    )
    concrete_runtime_home_choice_input = (
        evaluate_supervised_execution_home_runtime_home_choice(runtime_home_choice_input)
    )
    return evaluate_supervised_execution_home_concrete_runtime_home_choice(
        concrete_runtime_home_choice_input
    )


EXPECTED_KEYS = {
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
    "concrete_stack_command_home_selection_status",
    "concrete_stack_command_home_selection_question",
    "concrete_stack_command_home_selection_reasons",
    "concrete_command_file_selection_status",
    "concrete_command_file_selection_question",
    "concrete_command_file_selection_reasons",
    "concrete_stack_command_implementation_surface_selection_status",
    "concrete_stack_command_implementation_surface_selection_question",
    "concrete_stack_command_implementation_surface_selection_reasons",
    "runtime_home_selection_status",
    "runtime_home_selection_question",
    "runtime_home_selection_reasons",
    "runtime_home_choice_status",
    "runtime_home_choice_question",
    "runtime_home_choice_reasons",
    "concrete_runtime_home_choice_status",
    "concrete_runtime_home_choice_question",
    "concrete_runtime_home_choice_reasons",
    "actual_concrete_runtime_home_choice_status",
    "actual_concrete_runtime_home_choice_question",
    "actual_concrete_runtime_home_choice_reasons",
}


class SupervisedExecutionHomeActualConcreteRuntimeHomeChoiceTests(unittest.TestCase):
    def _evaluate(self, bundle: dict[str, object]) -> dict[str, object]:
        payload = evaluate_supervised_execution_home_actual_concrete_runtime_home_choice(
            bundle
        )
        self.assertEqual(EXPECTED_KEYS, set(payload.keys()))
        return payload

    def test_admissible_result_reopens_one_contract_local_question(self) -> None:
        payload = self._evaluate(_base_result())

        self.assertEqual(
            CONCRETE_RUNTIME_HOME_CHOICE_STATUS_ADMISSIBLE,
            payload["concrete_runtime_home_choice_status"],
        )
        self.assertEqual([], payload["concrete_runtime_home_choice_reasons"])
        self.assertEqual(
            ACTUAL_CONCRETE_RUNTIME_HOME_CHOICE_STATUS_ADMISSIBLE,
            payload["actual_concrete_runtime_home_choice_status"],
        )
        self.assertEqual([], payload["actual_concrete_runtime_home_choice_reasons"])
        self.assertEqual(
            {"question", "candidate_ref", "authoritative_receipt_refs"},
            set(payload["actual_concrete_runtime_home_choice_question"].keys()),
        )
        self.assertEqual(
            QUESTION_PROMPT,
            payload["actual_concrete_runtime_home_choice_question"]["question"],
        )
        self.assertEqual(
            "repos/example/.worktrees/pilot-a",
            payload["actual_concrete_runtime_home_choice_question"]["candidate_ref"],
        )
        self.assertEqual(
            list(CONTRACT_RECEIPT_REFS),
            payload["actual_concrete_runtime_home_choice_question"][
                "authoritative_receipt_refs"
            ],
        )
        self.assertEqual(
            {
                "question": CONCRETE_RUNTIME_HOME_CHOICE_QUESTION_PROMPT,
                "candidate_ref": "repos/example/.worktrees/pilot-a",
                "authoritative_receipt_refs": list(
                    CONCRETE_RUNTIME_HOME_CHOICE_CONTRACT_RECEIPT_REFS
                ),
            },
            payload["concrete_runtime_home_choice_question"],
        )
        self.assertEqual(
            RUNTIME_HOME_CHOICE_STATUS_ADMISSIBLE,
            payload["runtime_home_choice_status"],
        )
        self.assertEqual(
            {
                "question": RUNTIME_HOME_CHOICE_QUESTION_PROMPT,
                "candidate_ref": "repos/example/.worktrees/pilot-a",
                "authoritative_receipt_refs": list(
                    RUNTIME_HOME_CHOICE_CONTRACT_RECEIPT_REFS
                ),
            },
            payload["runtime_home_choice_question"],
        )

    def test_non_admissible_upstream_status_fails_closed(self) -> None:
        bundle = _base_result()
        bundle["concrete_runtime_home_choice_status"] = "no_concrete_runtime_home_choice"
        bundle["concrete_runtime_home_choice_question"] = None
        bundle["concrete_runtime_home_choice_reasons"] = [
            "concrete_runtime_home_choice_question_not_explicit"
        ]

        payload = self._evaluate(bundle)

        self.assertEqual(
            NO_ACTUAL_CONCRETE_RUNTIME_HOME_CHOICE,
            payload["actual_concrete_runtime_home_choice_status"],
        )
        self.assertIsNone(payload["actual_concrete_runtime_home_choice_question"])
        self.assertEqual(
            ["concrete_runtime_home_choice_status_not_admissible"],
            payload["actual_concrete_runtime_home_choice_reasons"],
        )

    def test_non_explicit_question_card_or_upstream_reasons_fail_closed(self) -> None:
        cases = (
            (
                "question_card_missing_field",
                {
                    "concrete_runtime_home_choice_question": {
                        "question": CONCRETE_RUNTIME_HOME_CHOICE_QUESTION_PROMPT,
                        "candidate_ref": "repos/example/.worktrees/pilot-a",
                    }
                },
                ["concrete_runtime_home_choice_question_not_explicit"],
            ),
            (
                "question_card_wrong_receipts",
                {
                    "concrete_runtime_home_choice_question": {
                        "question": CONCRETE_RUNTIME_HOME_CHOICE_QUESTION_PROMPT,
                        "candidate_ref": "repos/example/.worktrees/pilot-a",
                        "authoritative_receipt_refs": list(
                            CONCRETE_RUNTIME_HOME_CHOICE_CONTRACT_RECEIPT_REFS[:-1]
                        ),
                    }
                },
                ["concrete_runtime_home_choice_question_not_explicit"],
            ),
            (
                "upstream_reasons_present",
                {
                    "concrete_runtime_home_choice_reasons": [
                        "forbidden_evidence_class_used"
                    ]
                },
                ["concrete_runtime_home_choice_reasons_present"],
            ),
        )
        for _, updates, expected_reasons in cases:
            with self.subTest(expected_reasons=expected_reasons):
                bundle = _base_result()
                bundle.update(updates)

                payload = self._evaluate(bundle)

                self.assertEqual(
                    NO_ACTUAL_CONCRETE_RUNTIME_HOME_CHOICE,
                    payload["actual_concrete_runtime_home_choice_status"],
                )
                self.assertIsNone(payload["actual_concrete_runtime_home_choice_question"])
                self.assertEqual(
                    expected_reasons,
                    payload["actual_concrete_runtime_home_choice_reasons"],
                )

    def test_forbidden_evidence_or_hidden_dependency_fails_closed(self) -> None:
        cases = (
            (
                "payload_not_explicit",
                lambda bundle: bundle["payload"].pop("blocked_question_summary"),
                ["forbidden_evidence_class_used"],
            ),
            (
                "result_class_drift",
                lambda bundle: bundle.update({"result_class": "candidate-missing"}),
                ["forbidden_evidence_class_used"],
            ),
            (
                "hidden_dependency",
                lambda bundle: bundle.update({"worktree_inventory": ["pilot-a"]}),
                ["live_repo_discovery_or_hidden_transcript_dependency"],
            ),
        )
        for _, mutate, expected_reasons in cases:
            with self.subTest(expected_reasons=expected_reasons):
                bundle = _base_result()
                bundle["payload"] = copy.deepcopy(bundle["payload"])
                mutate(bundle)

                payload = self._evaluate(bundle)

                self.assertEqual(
                    NO_ACTUAL_CONCRETE_RUNTIME_HOME_CHOICE,
                    payload["actual_concrete_runtime_home_choice_status"],
                )
                self.assertIsNone(payload["actual_concrete_runtime_home_choice_question"])
                self.assertEqual(
                    expected_reasons,
                    payload["actual_concrete_runtime_home_choice_reasons"],
                )

    def test_attempted_choice_runtime_authority_or_exception_fail_closed(self) -> None:
        cases = (
            (
                "concrete_stack_command_home",
                "_stack",
                ["concrete_stack_command_home_choice_attempted"],
            ),
            (
                "command_file",
                "repos/_stack/cmd.py",
                ["concrete_command_file_choice_attempted"],
            ),
            (
                "stack_command_implementation_surface",
                "repos/_stack/ops/codex/stack-supervised.py",
                ["stack_command_implementation_surface_choice_attempted"],
            ),
            (
                "actual_concrete_runtime_home_value",
                "_stack",
                ["actual_concrete_runtime_home_value_attempted"],
            ),
            (
                "stack_command_implementation",
                "implemented",
                ["stack_command_implementation_attempted"],
            ),
            ("worker_authority", "launch", ["worker_authority_attempted"]),
            (
                "owner_repo_edit_authority",
                True,
                ["owner_repo_or_actual_mutation_authority_attempted"],
            ),
            (
                "actual_owner_side_mutation_authority",
                True,
                ["owner_repo_or_actual_mutation_authority_attempted"],
            ),
            (
                "playbook_doctrine_export",
                True,
                ["playbook_doctrine_export_attempted"],
            ),
            (
                "protected_surface_exception",
                True,
                ["protected_surface_exception_attempted"],
            ),
        )
        for field, value, expected_reasons in cases:
            with self.subTest(field=field):
                bundle = _base_result()
                bundle[field] = value

                payload = self._evaluate(bundle)

                self.assertEqual(
                    NO_ACTUAL_CONCRETE_RUNTIME_HOME_CHOICE,
                    payload["actual_concrete_runtime_home_choice_status"],
                )
                self.assertIsNone(payload["actual_concrete_runtime_home_choice_question"])
                self.assertEqual(
                    expected_reasons,
                    payload["actual_concrete_runtime_home_choice_reasons"],
                )


if __name__ == "__main__":
    unittest.main()
