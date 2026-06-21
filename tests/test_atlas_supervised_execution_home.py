from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ops.atlas.supervised_execution_home import (
    ACTUAL_MUTATION_RESULT_REF,
    BLOCKED_QUESTIONS,
    COMMAND,
    OWNER_SURFACE,
    REPAIR_ROUTING_NOTE,
    RESULT_CLASS_CANDIDATE_MISSING,
    RESULT_CLASS_CANDIDATE_NON_ADMISSIBLE,
    RESULT_CLASS_CONTRACT_TRUTH_UNAVAILABLE,
    RESULT_CLASS_CONTRACT_VISIBLE,
    SUCCESS_ROUTING_NOTE,
    SUPPORT_POSTURE,
    evaluate_supervised_execution_home,
)


def _base_actual_owner_side_mutation(target_ref: str = "repos/example/.worktrees/pilot-a") -> dict[str, object]:
    return {
        "owner_repo_count": 1,
        "target_kind": "worktree",
        "target_ref": target_ref,
        "objective_summary": "Land one bounded root-local supervised execution-home helper.",
        "allowed_write_scope": "ops/atlas/supervised_execution_home.py",
        "checkpoint_surface": "docs/ops/checkpoint.md",
        "verification_gate": "python -m unittest tests.test_atlas_supervised_execution_home -v",
        "closeout_artifact": "docs/ops/reconciliation.md",
        "park_or_escalation_rule": "stop and escalate if command-home choice or owner-repo edits are required",
        "protected_surface_exclusions": [
            "deploy",
            "publication",
            "archive_delete",
            "env_mutation",
            "secret_mutation",
        ],
    }


def _base_bundle(target_ref: str = "repos/example/.worktrees/pilot-a") -> dict[str, object]:
    return {
        "selection_status": "pilot_selected",
        "selection_reasons": [],
        "routing_status": "implementation_route_admissible",
        "routing_reasons": [],
        "implementation_status": "owner_repo_implementation_admissible",
        "implementation_reasons": [],
        "mutation_status": "owner_repo_mutation_admissible",
        "mutation_reasons": [],
        "actual_mutation_status": "actual_owner_side_mutation_admissible",
        "actual_owner_side_mutation": _base_actual_owner_side_mutation(target_ref),
        "actual_mutation_reasons": [],
    }


def _write_contract_receipts(root: Path) -> None:
    docs_ops = root / "docs" / "ops"
    docs_ops.mkdir(parents=True, exist_ok=True)
    (docs_ops / "_STACK-READINESS-SUPERVISED-EXECUTION-HOME-COMMAND-DESIGN-PASS-518-2026-06-21.md").write_text(
        "\n".join(
            [
                "# pass 518",
                "`stack supervised-execution-home`",
                "`contract-visible`",
                "`candidate-missing`",
                "`candidate-non-admissible`",
                "`contract-truth-unavailable`",
            ]
        ),
        encoding="utf-8",
    )
    (docs_ops / "_STACK-READINESS-SUPERVISED-EXECUTION-HOME-EVIDENCE-ADMISSION-AND-CONTRADICTION-DISCIPLINE-PASS-519-2026-06-21.md").write_text(
        "\n".join(
            [
                "# pass 519",
                "forbidden-evidence contradiction",
                "actual owner-side mutation authority",
                "command-home",
                "runtime-home",
            ]
        ),
        encoding="utf-8",
    )
    (docs_ops / "_STACK-READINESS-SUPERVISED-EXECUTION-HOME-REPORT-CONTRACT-AND-NO-MUTATION-GUARD-PASS-520-2026-06-21.md").write_text(
        "\n".join(
            [
                "# pass 520",
                SUCCESS_ROUTING_NOTE,
                REPAIR_ROUTING_NOTE,
                "`contract-visible`",
                "`candidate-missing`",
                "`candidate-non-admissible`",
                "`contract-truth-unavailable`",
            ]
        ),
        encoding="utf-8",
    )
    (docs_ops / "_STACK-READINESS-SUPERVISED-EXECUTION-HOME-IMPLEMENTATION-ADMISSION-AND-NO-MUTATION-GUARD-PASS-521-2026-06-21.md").write_text(
        "\n".join(
            [
                "# pass 521",
                "`command`",
                "`normalized_candidate_path`",
                "`owner_surface`",
                "`support_posture`",
                "`blocked_questions`",
                "`routing_note`",
                "`payload`",
            ]
        ),
        encoding="utf-8",
    )


class SupervisedExecutionHomeTests(unittest.TestCase):
    def _evaluate(self, bundle: dict[str, object], root: Path) -> dict[str, object]:
        payload = evaluate_supervised_execution_home(bundle, root=root)
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
            },
            set(payload.keys()),
        )
        self.assertEqual(COMMAND, payload["command"])
        self.assertEqual(OWNER_SURFACE, payload["owner_surface"])
        self.assertEqual(SUPPORT_POSTURE, payload["support_posture"])
        self.assertEqual(BLOCKED_QUESTIONS, payload["blocked_questions"])
        self.assertEqual(
            [
                ACTUAL_MUTATION_RESULT_REF,
                "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-COMMAND-DESIGN-PASS-518-2026-06-21.md",
                "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-EVIDENCE-ADMISSION-AND-CONTRADICTION-DISCIPLINE-PASS-519-2026-06-21.md",
                "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-REPORT-CONTRACT-AND-NO-MUTATION-GUARD-PASS-520-2026-06-21.md",
                "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-IMPLEMENTATION-ADMISSION-AND-NO-MUTATION-GUARD-PASS-521-2026-06-21.md",
            ],
            payload["admitted_evidence_refs"],
        )
        return payload

    def test_explicit_admissible_actual_mutation_result_is_contract_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write_contract_receipts(root)
            bundle = _base_bundle(".\\repos\\example\\.worktrees\\pilot-a")

            payload = self._evaluate(bundle, root)

            self.assertEqual("repos/example/.worktrees/pilot-a", payload["normalized_candidate_path"])
            self.assertEqual(RESULT_CLASS_CONTRACT_VISIBLE, payload["result_class"])
            self.assertEqual(SUCCESS_ROUTING_NOTE, payload["routing_note"])
            self.assertEqual(
                {
                    "candidate_ref",
                    "owner_surface_statement",
                    "support_posture_statement",
                    "admitted_evidence_summary",
                    "blocked_question_summary",
                    "authoritative_receipt_refs",
                },
                set(payload["payload"].keys()),
            )
            self.assertEqual("repos/example/.worktrees/pilot-a", payload["payload"]["candidate_ref"])

    def test_missing_explicit_candidate_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write_contract_receipts(root)
            bundle = _base_bundle()
            bundle["actual_owner_side_mutation"] = None

            payload = self._evaluate(bundle, root)

            self.assertEqual("", payload["normalized_candidate_path"])
            self.assertEqual(RESULT_CLASS_CANDIDATE_MISSING, payload["result_class"])
            self.assertEqual(REPAIR_ROUTING_NOTE, payload["routing_note"])
            self.assertEqual("missing-explicit-candidate", payload["payload"]["contradiction_class"])
            self.assertEqual(["actual_owner_side_mutation_missing"], payload["payload"]["reasons"])

    def test_non_admissible_actual_mutation_result_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write_contract_receipts(root)
            bundle = _base_bundle()
            bundle["actual_mutation_status"] = "no_actual_owner_side_mutation"
            bundle["actual_mutation_reasons"] = ["mutation_reasons_present"]

            payload = self._evaluate(bundle, root)

            self.assertEqual(RESULT_CLASS_CANDIDATE_NON_ADMISSIBLE, payload["result_class"])
            self.assertEqual(REPAIR_ROUTING_NOTE, payload["routing_note"])
            self.assertEqual(
                "authoritative-candidate-contradiction",
                payload["payload"]["contradiction_class"],
            )
            self.assertEqual(["mutation_reasons_present"], payload["payload"]["reasons"])

    def test_missing_or_contradictory_contract_truth_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write_contract_receipts(root)
            pass_520 = (
                root
                / "docs"
                / "ops"
                / "_STACK-READINESS-SUPERVISED-EXECUTION-HOME-REPORT-CONTRACT-AND-NO-MUTATION-GUARD-PASS-520-2026-06-21.md"
            )
            pass_520.write_text("# broken pass 520", encoding="utf-8")

            payload = self._evaluate(_base_bundle(), root)

            self.assertEqual(RESULT_CLASS_CONTRACT_TRUTH_UNAVAILABLE, payload["result_class"])
            self.assertEqual(REPAIR_ROUTING_NOTE, payload["routing_note"])
            self.assertEqual(
                "authoritative-contract-contradiction",
                payload["payload"]["contradiction_class"],
            )
            self.assertEqual(
                [
                    "contradictory:docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-REPORT-CONTRACT-AND-NO-MUTATION-GUARD-PASS-520-2026-06-21.md"
                ],
                payload["payload"]["reasons"],
            )

    def test_invented_runtime_home_or_doctrine_export_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write_contract_receipts(root)

            runtime_bundle = _base_bundle()
            runtime_bundle["runtime_home"] = "_stack"
            runtime_payload = self._evaluate(runtime_bundle, root)

            self.assertEqual(RESULT_CLASS_CONTRACT_TRUTH_UNAVAILABLE, runtime_payload["result_class"])
            self.assertEqual(
                "forbidden-evidence-contradiction",
                runtime_payload["payload"]["contradiction_class"],
            )
            self.assertEqual(
                ["runtime_home_inference_invented"],
                runtime_payload["payload"]["reasons"],
            )

            doctrine_bundle = _base_bundle()
            doctrine_bundle["playbook_doctrine_export"] = True
            doctrine_payload = self._evaluate(doctrine_bundle, root)

            self.assertEqual(RESULT_CLASS_CONTRACT_TRUTH_UNAVAILABLE, doctrine_payload["result_class"])
            self.assertEqual(
                ["playbook_doctrine_export_invented"],
                doctrine_payload["payload"]["reasons"],
            )


if __name__ == "__main__":
    unittest.main()
