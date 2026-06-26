from __future__ import annotations

import copy
import unittest

from ops.atlas.supervised_execution_home_concrete_stack_command_implementation_surface import (
    CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_SELECTION_STATUS_ADMISSIBLE,
    CONTRACT_RECEIPT_REFS as CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_SELECTION_CONTRACT_RECEIPT_REFS,
    QUESTION_PROMPT as CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_SELECTION_QUESTION_PROMPT,
    evaluate_supervised_execution_home_concrete_stack_command_implementation_surface,
)
from ops.atlas.supervised_execution_home_concrete_stack_command_implementation_surface_choice import (
    CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_CHOICE_STATUS_ADMISSIBLE,
    CONTRACT_RECEIPT_REFS,
    NO_CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_CHOICE,
    QUESTION_PROMPT,
    evaluate_supervised_execution_home_concrete_stack_command_implementation_surface_choice,
)
from tests.test_atlas_supervised_execution_home_concrete_stack_command_implementation_surface import (
    _base_result as _implementation_surface_selection_base_result,
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
    "concrete_stack_command_home_choice_status",
    "concrete_stack_command_home_choice_question",
    "concrete_stack_command_home_choice_reasons",
    "concrete_command_file_choice_status",
    "concrete_command_file_choice_question",
    "concrete_command_file_choice_reasons",
    "actual_concrete_command_file_choice_status",
    "actual_concrete_command_file_choice_question",
    "actual_concrete_command_file_choice_reasons",
    "actual_concrete_command_file_downstream_runtime_home_value_placement_status",
    "actual_concrete_command_file_downstream_runtime_home_value_placement_question",
    "actual_concrete_command_file_downstream_runtime_home_value_placement_reasons",
    "concrete_stack_command_implementation_surface_selection_status",
    "concrete_stack_command_implementation_surface_selection_question",
    "concrete_stack_command_implementation_surface_selection_reasons",
    "concrete_stack_command_implementation_surface_choice_status",
    "concrete_stack_command_implementation_surface_choice_question",
    "concrete_stack_command_implementation_surface_choice_reasons",
}


def _base_result() -> dict[str, object]:
    return evaluate_supervised_execution_home_concrete_stack_command_implementation_surface(
        _implementation_surface_selection_base_result()
    )


class SupervisedExecutionHomeConcreteStackCommandImplementationSurfaceChoiceTests(
    unittest.TestCase
):
    def _evaluate(self, bundle: dict[str, object]) -> dict[str, object]:
        payload = evaluate_supervised_execution_home_concrete_stack_command_implementation_surface_choice(
            bundle
        )
        self.assertEqual(EXPECTED_KEYS, set(payload.keys()))
        return payload

    def test_admissible_result_reopens_one_contract_local_question(self) -> None:
        payload = self._evaluate(_base_result())

        self.assertEqual(
            CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_SELECTION_STATUS_ADMISSIBLE,
            payload["concrete_stack_command_implementation_surface_selection_status"],
        )
        self.assertEqual(
            {
                "question": CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_SELECTION_QUESTION_PROMPT,
                "candidate_ref": "repos/example/.worktrees/pilot-a",
                "authoritative_receipt_refs": list(
                    CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_SELECTION_CONTRACT_RECEIPT_REFS
                ),
            },
            payload["concrete_stack_command_implementation_surface_selection_question"],
        )
        self.assertEqual(
            CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_CHOICE_STATUS_ADMISSIBLE,
            payload["concrete_stack_command_implementation_surface_choice_status"],
        )
        self.assertEqual(
            [], payload["concrete_stack_command_implementation_surface_choice_reasons"]
        )
        self.assertEqual(
            {"question", "candidate_ref", "authoritative_receipt_refs"},
            set(
                payload[
                    "concrete_stack_command_implementation_surface_choice_question"
                ].keys()
            ),
        )
        self.assertEqual(
            QUESTION_PROMPT,
            payload["concrete_stack_command_implementation_surface_choice_question"][
                "question"
            ],
        )
        self.assertEqual(
            "repos/example/.worktrees/pilot-a",
            payload["concrete_stack_command_implementation_surface_choice_question"][
                "candidate_ref"
            ],
        )
        self.assertEqual(
            list(CONTRACT_RECEIPT_REFS),
            payload["concrete_stack_command_implementation_surface_choice_question"][
                "authoritative_receipt_refs"
            ],
        )

    def test_non_admissible_upstream_status_fails_closed(self) -> None:
        bundle = _base_result()
        bundle["concrete_stack_command_implementation_surface_selection_status"] = (
            "no_concrete_stack_command_implementation_surface_selection"
        )
        bundle["concrete_stack_command_implementation_surface_selection_question"] = None
        bundle["concrete_stack_command_implementation_surface_selection_reasons"] = [
            "actual_concrete_command_file_downstream_runtime_home_value_placement_status_not_admissible"
        ]

        payload = self._evaluate(bundle)

        self.assertEqual(
            NO_CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_CHOICE,
            payload["concrete_stack_command_implementation_surface_choice_status"],
        )
        self.assertIsNone(
            payload["concrete_stack_command_implementation_surface_choice_question"]
        )
        self.assertEqual(
            ["concrete_stack_command_implementation_surface_selection_status_not_admissible"],
            payload["concrete_stack_command_implementation_surface_choice_reasons"],
        )

    def test_non_explicit_question_card_or_upstream_reasons_fail_closed(self) -> None:
        cases = (
            (
                "question_card_missing_field",
                {
                    "concrete_stack_command_implementation_surface_selection_question": {
                        "question": CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_SELECTION_QUESTION_PROMPT,
                        "candidate_ref": "repos/example/.worktrees/pilot-a",
                    }
                },
                [
                    "concrete_stack_command_implementation_surface_selection_question_not_explicit"
                ],
            ),
            (
                "question_card_wrong_receipts",
                {
                    "concrete_stack_command_implementation_surface_selection_question": {
                        "question": CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_SELECTION_QUESTION_PROMPT,
                        "candidate_ref": "repos/example/.worktrees/pilot-a",
                        "authoritative_receipt_refs": list(
                            CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_SELECTION_CONTRACT_RECEIPT_REFS[
                                :-1
                            ]
                        ),
                    }
                },
                [
                    "concrete_stack_command_implementation_surface_selection_question_not_explicit"
                ],
            ),
            (
                "upstream_reasons_present",
                {
                    "concrete_stack_command_implementation_surface_selection_reasons": [
                        "forbidden_evidence_class_used"
                    ]
                },
                [
                    "concrete_stack_command_implementation_surface_selection_reasons_present"
                ],
            ),
        )
        for _, updates, expected_reasons in cases:
            with self.subTest(updates=updates):
                bundle = _base_result()
                bundle.update(updates)

                payload = self._evaluate(bundle)

                self.assertEqual(
                    NO_CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_CHOICE,
                    payload["concrete_stack_command_implementation_surface_choice_status"],
                )
                self.assertIsNone(
                    payload[
                        "concrete_stack_command_implementation_surface_choice_question"
                    ]
                )
                self.assertEqual(
                    expected_reasons,
                    payload["concrete_stack_command_implementation_surface_choice_reasons"],
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
                    NO_CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_CHOICE,
                    payload["concrete_stack_command_implementation_surface_choice_status"],
                )
                self.assertIsNone(
                    payload[
                        "concrete_stack_command_implementation_surface_choice_question"
                    ]
                )
                self.assertEqual(
                    expected_reasons,
                    payload["concrete_stack_command_implementation_surface_choice_reasons"],
                )

    def test_attempted_choice_runtime_authority_or_exception_fail_closed(self) -> None:
        cases = (
            (
                "actual_concrete_command_file",
                "repos/_stack/ops/codex/stack.py",
                ["actual_concrete_command_file_choice_attempted"],
            ),
            (
                "actual_command_file_path",
                "repos/_stack/ops/codex/stack.py",
                ["actual_concrete_command_file_choice_attempted"],
            ),
            (
                "actual_concrete_command_file_downstream_runtime_home_value_placement",
                "runtime/supervised-execution-home.json",
                ["actual_concrete_command_file_downstream_runtime_home_value_placement_attempted"],
            ),
            (
                "concrete_stack_command_implementation_surface_choice",
                "repos/_stack/ops/codex/stack.py",
                ["concrete_stack_command_implementation_surface_choice_attempted"],
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
                    NO_CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_CHOICE,
                    payload["concrete_stack_command_implementation_surface_choice_status"],
                )
                self.assertIsNone(
                    payload[
                        "concrete_stack_command_implementation_surface_choice_question"
                    ]
                )
                self.assertEqual(
                    expected_reasons,
                    payload["concrete_stack_command_implementation_surface_choice_reasons"],
                )


if __name__ == "__main__":
    unittest.main()
