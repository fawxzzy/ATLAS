from __future__ import annotations

import copy
import unittest

from ops.atlas.supervised_execution_home_stack_command_implementation import (
    CONTRACT_RECEIPT_REFS as STACK_COMMAND_IMPLEMENTATION_CONTRACT_RECEIPT_REFS,
    QUESTION_PROMPT as STACK_COMMAND_IMPLEMENTATION_QUESTION_PROMPT,
    STACK_COMMAND_IMPLEMENTATION_STATUS_ADMISSIBLE,
    evaluate_supervised_execution_home_stack_command_implementation,
)
from ops.atlas.supervised_execution_home_stack_command_implementation_worker_authority import (
    CONTRACT_RECEIPT_REFS,
    NO_STACK_COMMAND_IMPLEMENTATION_WORKER_AUTHORITY,
    QUESTION_PROMPT,
    STACK_COMMAND_IMPLEMENTATION_WORKER_AUTHORITY_STATUS_ADMISSIBLE,
    evaluate_supervised_execution_home_stack_command_implementation_worker_authority,
)
from tests.test_atlas_supervised_execution_home_stack_command_implementation import (
    EXPECTED_KEYS as STACK_COMMAND_IMPLEMENTATION_EXPECTED_KEYS,
    _base_result as _stack_command_implementation_base_result,
)

EXPECTED_KEYS = STACK_COMMAND_IMPLEMENTATION_EXPECTED_KEYS | {
    "stack_command_implementation_worker_authority_status",
    "stack_command_implementation_worker_authority_question",
    "stack_command_implementation_worker_authority_reasons",
}


def _base_result() -> dict[str, object]:
    return evaluate_supervised_execution_home_stack_command_implementation(
        _stack_command_implementation_base_result()
    )


class SupervisedExecutionHomeStackCommandImplementationWorkerAuthorityTests(unittest.TestCase):
    def _evaluate(self, bundle: dict[str, object]) -> dict[str, object]:
        payload = evaluate_supervised_execution_home_stack_command_implementation_worker_authority(
            bundle
        )
        self.assertEqual(EXPECTED_KEYS, set(payload.keys()))
        return payload

    def test_admissible_result_reopens_one_contract_local_question(self) -> None:
        payload = self._evaluate(_base_result())

        self.assertEqual(
            STACK_COMMAND_IMPLEMENTATION_STATUS_ADMISSIBLE,
            payload["stack_command_implementation_status"],
        )
        self.assertEqual(
            {
                "question": STACK_COMMAND_IMPLEMENTATION_QUESTION_PROMPT,
                "candidate_ref": "repos/example/.worktrees/pilot-a",
                "authoritative_receipt_refs": list(STACK_COMMAND_IMPLEMENTATION_CONTRACT_RECEIPT_REFS),
            },
            payload["stack_command_implementation_question"],
        )
        self.assertEqual(
            STACK_COMMAND_IMPLEMENTATION_WORKER_AUTHORITY_STATUS_ADMISSIBLE,
            payload["stack_command_implementation_worker_authority_status"],
        )
        self.assertEqual([], payload["stack_command_implementation_worker_authority_reasons"])
        self.assertEqual(
            {"question", "candidate_ref", "authoritative_receipt_refs"},
            set(payload["stack_command_implementation_worker_authority_question"].keys()),
        )
        self.assertEqual(
            QUESTION_PROMPT,
            payload["stack_command_implementation_worker_authority_question"]["question"],
        )
        self.assertEqual(
            "repos/example/.worktrees/pilot-a",
            payload["stack_command_implementation_worker_authority_question"]["candidate_ref"],
        )
        self.assertEqual(
            list(CONTRACT_RECEIPT_REFS),
            payload["stack_command_implementation_worker_authority_question"][
                "authoritative_receipt_refs"
            ],
        )

    def test_non_admissible_upstream_status_fails_closed(self) -> None:
        bundle = _base_result()
        bundle["stack_command_implementation_status"] = "no_stack_command_implementation"
        bundle["stack_command_implementation_question"] = None
        bundle["stack_command_implementation_reasons"] = [
            "actual_concrete_stack_command_implementation_surface_choice_status_not_admissible"
        ]

        payload = self._evaluate(bundle)

        self.assertEqual(
            NO_STACK_COMMAND_IMPLEMENTATION_WORKER_AUTHORITY,
            payload["stack_command_implementation_worker_authority_status"],
        )
        self.assertIsNone(payload["stack_command_implementation_worker_authority_question"])
        self.assertEqual(
            ["stack_command_implementation_status_not_admissible"],
            payload["stack_command_implementation_worker_authority_reasons"],
        )

    def test_non_explicit_question_card_or_upstream_reasons_fail_closed(self) -> None:
        cases = (
            (
                "question_card_missing_field",
                {
                    "stack_command_implementation_question": {
                        "question": STACK_COMMAND_IMPLEMENTATION_QUESTION_PROMPT,
                        "candidate_ref": "repos/example/.worktrees/pilot-a",
                    }
                },
                ["stack_command_implementation_question_not_explicit"],
            ),
            (
                "question_card_wrong_receipts",
                {
                    "stack_command_implementation_question": {
                        "question": STACK_COMMAND_IMPLEMENTATION_QUESTION_PROMPT,
                        "candidate_ref": "repos/example/.worktrees/pilot-a",
                        "authoritative_receipt_refs": list(
                            STACK_COMMAND_IMPLEMENTATION_CONTRACT_RECEIPT_REFS[:-1]
                        ),
                    }
                },
                ["stack_command_implementation_question_not_explicit"],
            ),
            (
                "upstream_reasons_present",
                {"stack_command_implementation_reasons": ["forbidden_evidence_class_used"]},
                ["stack_command_implementation_reasons_present"],
            ),
        )
        for _, updates, expected_reasons in cases:
            with self.subTest(updates=updates):
                bundle = _base_result()
                bundle.update(updates)

                payload = self._evaluate(bundle)

                self.assertEqual(
                    NO_STACK_COMMAND_IMPLEMENTATION_WORKER_AUTHORITY,
                    payload["stack_command_implementation_worker_authority_status"],
                )
                self.assertIsNone(payload["stack_command_implementation_worker_authority_question"])
                self.assertEqual(
                    expected_reasons,
                    payload["stack_command_implementation_worker_authority_reasons"],
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
                    NO_STACK_COMMAND_IMPLEMENTATION_WORKER_AUTHORITY,
                    payload["stack_command_implementation_worker_authority_status"],
                )
                self.assertIsNone(payload["stack_command_implementation_worker_authority_question"])
                self.assertEqual(
                    expected_reasons,
                    payload["stack_command_implementation_worker_authority_reasons"],
                )

    def test_attempted_actual_choice_runtime_authority_or_exception_fail_closed(self) -> None:
        cases = (
            (
                "actual_concrete_command_file",
                "repos/_stack/ops/codex/stack.py",
                ["actual_concrete_command_file_choice_attempted"],
            ),
            (
                "actual_concrete_command_file_downstream_runtime_home_value_placement",
                "runtime/supervised-execution-home.json",
                ["actual_concrete_command_file_downstream_runtime_home_value_placement_attempted"],
            ),
            (
                "actual_concrete_stack_command_implementation_surface_choice",
                "repos/_stack/ops/codex/stack.py",
                ["actual_concrete_stack_command_implementation_surface_choice_attempted"],
            ),
            (
                "stack_command_implementation",
                "implemented",
                ["stack_command_implementation_attempted"],
            ),
            ("worker_authority", "launch", ["worker_authority_attempted"]),
            (
                "implementation_route",
                {"target_ref": "repos/_stack/.worktrees/impl"},
                ["owner_repo_implementation_routing_attempted"],
            ),
            (
                "owner_repo_write_authority",
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
                    NO_STACK_COMMAND_IMPLEMENTATION_WORKER_AUTHORITY,
                    payload["stack_command_implementation_worker_authority_status"],
                )
                self.assertIsNone(payload["stack_command_implementation_worker_authority_question"])
                self.assertEqual(
                    expected_reasons,
                    payload["stack_command_implementation_worker_authority_reasons"],
                )


if __name__ == "__main__":
    unittest.main()
