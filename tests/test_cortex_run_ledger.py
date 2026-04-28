from __future__ import annotations

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.kernel import CortexProofSummary, VerificationResult
from ops.cortex.loop import CORTEX_RUN_RESULT_CONTRACT_VERSION, load_and_run_cortex_loop
from ops.cortex.run_ledger import load_cortex_run_ledger, summarize_run_ledger
from ops.cortex.verification_ingest import (
    KNOWN_STACK_VALIDATION_BASELINE,
    VerificationDebtCounts,
    VerificationOutcome,
    ingest_verification_outcome,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _failing_proof_summary() -> CortexProofSummary:
    return CortexProofSummary(
        proof_id="cortex-run-ledger-regression",
        command="python -m unittest tests.test_cortex_run_ledger",
        verification=VerificationResult(
            status="failed",
            passed=(),
            failed=("tests.test_cortex_run_ledger.CortexRunLedgerTests.test_blocked_run_is_summarized_with_blocked_reason",),
            known_debt=(),
            notes=(),
        ),
        touched_files=("ops/cortex/run_ledger.py", "tests/test_cortex_run_ledger.py"),
        owner_layer="cortex",
        next_required_layer="cortex",
        receipt_ready=False,
        evidence=("tests/test_cortex_run_ledger.py",),
    )


class CortexRunLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.base_payload = load_and_run_cortex_loop(root=cls.root).to_payload()
        cls.blocked_payload = load_and_run_cortex_loop(root=cls.root, proof_summary=_failing_proof_summary()).to_payload()

    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return Path(temp_dir.name)

    def test_empty_ledger_returns_no_entries_and_summary_fails_clearly(self) -> None:
        root = self._temp_root()

        ledger = load_cortex_run_ledger(root=root)

        self.assertEqual((), ledger.entries)
        with self.assertRaisesRegex(FileNotFoundError, "No Cortex run artifacts found under"):
            summarize_run_ledger(root=root)

    def test_latest_run_is_selected_deterministically(self) -> None:
        root = self._temp_root()
        older_path = root / "runtime" / "cortex" / "runs" / "2026-04-27T20-00-00Z.json"
        newer_path = root / "runtime" / "cortex" / "runs" / "2026-04-27T20-15-00Z.json"
        _write_json(older_path, self.base_payload)
        _write_json(newer_path, self.blocked_payload)
        os.utime(older_path, ns=(1_000_000_000, 1_000_000_000))
        os.utime(newer_path, ns=(2_000_000_000, 2_000_000_000))

        summary = summarize_run_ledger(root=root)

        self.assertEqual("2026-04-27T20-15-00Z", summary.latest_run_id)
        self.assertEqual("runtime/cortex/runs/2026-04-27T20-15-00Z.json", summary.latest_run_path)
        self.assertEqual("failed", summary.proof_status)

    def test_receipt_ready_run_is_summarized_correctly(self) -> None:
        root = self._temp_root()
        artifact_path = root / "runtime" / "cortex" / "runs" / "cortex-run-result.latest.json"
        _write_json(artifact_path, self.base_payload)

        summary = summarize_run_ledger(root=root)

        self.assertEqual("cortex-run-result.latest", summary.latest_run_id)
        self.assertEqual("runtime/cortex/runs/cortex-run-result.latest.json", summary.latest_run_path)
        self.assertEqual(
            self.base_payload["selected_next_action"]["action_id"],
            summary.selected_next_action,
        )
        self.assertEqual(
            self.base_payload["selected_next_action"]["owner_layer"],
            summary.owner_layer,
        )
        self.assertEqual(self.base_payload["next_required_layer"], summary.next_required_layer)
        self.assertTrue(summary.receipt_ready)
        self.assertEqual("passed", summary.proof_status)
        self.assertIsNone(summary.blocked_reason)

    def test_blocked_run_is_summarized_with_blocked_reason(self) -> None:
        root = self._temp_root()
        artifact_path = root / "runtime" / "cortex" / "runs" / "blocked-run.json"
        _write_json(artifact_path, self.blocked_payload)

        summary = summarize_run_ledger(root=root)

        self.assertFalse(summary.receipt_ready)
        self.assertEqual("failed", summary.proof_status)
        self.assertIn("test_blocked_run_is_summarized_with_blocked_reason", summary.blocked_reason or "")

    def test_known_ambient_stack_debt_is_preserved(self) -> None:
        root = self._temp_root()
        artifact_path = root / "runtime" / "cortex" / "runs" / "ambient-only.json"
        _write_json(artifact_path, self.base_payload)

        summary = summarize_run_ledger(root=root)

        self.assertEqual(tuple(self.base_payload["known_ambient_debt"]), summary.known_ambient_debt)
        self.assertEqual((), summary.current_validation_debt)

    def test_changed_validation_debt_is_surfaced_separately_from_ambient_debt(self) -> None:
        root = self._temp_root()
        artifact_path = root / "runtime" / "cortex" / "runs" / "verification-overlay.json"
        _write_json(artifact_path, self.base_payload)
        verification_ingest = ingest_verification_outcome(
            VerificationOutcome(
                command="python .\\ops\\validation\\validate_stack.py",
                exit_code=2,
                owner_layer="stack",
                observed_debt=VerificationDebtCounts(critical=346, error=14, warning=181),
                expected_ambient_debt=KNOWN_STACK_VALIDATION_BASELINE,
                next_required_layer="cortex",
                proof_id="stack-validation-changed-debt",
            )
        )

        summary = summarize_run_ledger(root=root, verification_ingest=verification_ingest)

        self.assertEqual(tuple(self.base_payload["known_ambient_debt"]), summary.known_ambient_debt)
        self.assertEqual(verification_ingest.current_validation_debt, summary.current_validation_debt)
        self.assertEqual("completed_with_changed_debt", summary.proof_status)
        self.assertFalse(summary.receipt_ready)

    def test_applied_rule_trace_is_carried_into_summary(self) -> None:
        root = self._temp_root()
        artifact_path = root / "runtime" / "cortex" / "runs" / "rule-trace.json"
        _write_json(artifact_path, self.base_payload)

        summary = summarize_run_ledger(root=root)
        expected = self.base_payload["applied_rule_trace"]

        self.assertEqual(tuple(expected["decision_rule_ids"]), summary.applied_rules.decision_rule_ids)
        self.assertEqual(tuple(expected["plan_rule_ids"]), summary.applied_rules.plan_rule_ids)
        self.assertEqual(tuple(expected["rule_ids"]), summary.applied_rules.rule_ids)
        self.assertEqual(tuple(expected["pattern_ids"]), summary.applied_rules.pattern_ids)
        self.assertEqual(tuple(expected["failure_mode_ids"]), summary.applied_rules.failure_mode_ids)
        self.assertEqual(tuple(expected["why_selected"]), summary.applied_rules.why_selected)

    def test_malformed_run_artifact_fails_clearly(self) -> None:
        root = self._temp_root()
        artifact_path = root / "runtime" / "cortex" / "runs" / "broken.json"
        payload = copy.deepcopy(self.base_payload)
        payload["contract_version"] = CORTEX_RUN_RESULT_CONTRACT_VERSION
        del payload["selected_next_action"]
        _write_json(artifact_path, payload)

        with self.assertRaisesRegex(ValueError, "Expected object for selected_next_action"):
            summarize_run_ledger(root=root)

    def test_ledger_output_is_json_serializable(self) -> None:
        root = self._temp_root()
        artifact_path = root / "runtime" / "cortex" / "runs" / "serializable.json"
        _write_json(artifact_path, self.base_payload)

        summary = summarize_run_ledger(root=root)

        json.dumps(summary.to_payload(), sort_keys=True)

    def test_ledger_does_not_require_lifeline_or_connector_scope(self) -> None:
        root = self._temp_root()
        artifact_path = root / "runtime" / "cortex" / "runs" / "standalone.json"
        payload = copy.deepcopy(self.base_payload)
        payload["selected_next_action"]["owner_layer"] = "cortex"
        payload["applied_rule_trace"]["selected_owner_layer"] = "cortex"
        _write_json(artifact_path, payload)

        summary = summarize_run_ledger(root=root)

        self.assertEqual("runtime/cortex/runs/standalone.json", summary.latest_run_path)
        self.assertEqual("cortex", summary.owner_layer)
        self.assertTrue(summary.receipt_ready)


if __name__ == "__main__":
    unittest.main()
