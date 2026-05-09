from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.receipt_interpreter import (
    build_receipt_interpretation_payload,
    default_receipt_interpretation_latest_json_path,
    default_receipt_interpretation_latest_markdown_path,
    main,
    persist_receipt_interpretation_artifact,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class CortexReceiptInterpreterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.worker_prompt_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "worker-prompts" / "latest.json").read_text(encoding="utf-8")
        )
        cls.stack_handoff_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "stack-advisory-handoff" / "latest.json").read_text(encoding="utf-8")
        )
        cls.stack_pilot_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "stack-consumption-pilot" / "latest.json").read_text(encoding="utf-8")
        )
        cls.ledger_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "ledger" / "latest.json").read_text(encoding="utf-8")
        )
        cls.validation_payload = json.loads(
            (cls.root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json").read_text(encoding="utf-8")
        )
        cls.state_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json").read_text(encoding="utf-8")
        )
        cls.rule_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json").read_text(encoding="utf-8")
        )
        cls.schema_payload = json.loads(
            (cls.root / "schemas" / "atlas.cortex.receipt-interpretation.v1.json").read_text(encoding="utf-8")
        )

    def _base_validation_payload(self) -> dict:
        payload = deepcopy(self.validation_payload)
        payload["summary"] = {
            "critical": 0,
            "error": 0,
            "warning": 4,
            "info": 1,
            "total": 5,
        }
        payload["findings"] = []
        return payload

    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(root / "runtime" / "cortex" / "worker-prompts" / "latest.json", self.worker_prompt_payload)
        _write_json(root / "runtime" / "cortex" / "stack-advisory-handoff" / "latest.json", self.stack_handoff_payload)
        _write_json(root / "runtime" / "cortex" / "stack-consumption-pilot" / "latest.json", self.stack_pilot_payload)
        _write_json(root / "runtime" / "cortex" / "ledger" / "latest.json", self.ledger_payload)
        _write_json(root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json", self._base_validation_payload())
        _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", self.state_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", self.rule_payload)
        return root

    def test_ready_interpretation_without_final_receipt(self) -> None:
        root = self._temp_root()

        payload = build_receipt_interpretation_payload(root=root)

        self.assertEqual("atlas.cortex.receipt-interpretation.v1", payload["contract_version"])
        self.assertEqual("read_only_interpretation", payload["authority_level"])
        self.assertTrue(payload["authority"]["interpretation_authorized"])
        self.assertFalse(payload["authority"]["final_receipt_authorized"])
        self.assertFalse(payload["authority"]["approval_authorized"])
        self.assertFalse(payload["authority"]["execution_authorized"])
        self.assertFalse(payload["authority"]["dispatch_authorized"])
        self.assertFalse(payload["authority"]["owner_truth_mutation_authorized"])
        self.assertFalse(payload["authority"]["lifeline_truth_mutation_authorized"])
        self.assertFalse(payload["authority"]["transcript_scraping_allowed"])
        self.assertEqual("ready", payload["interpretation_result"]["status"])
        self.assertEqual("proof_ready", payload["interpreted_proof_summary"]["status"])
        self.assertIn("Stack advisory handoff is ready.", payload["interpreted_proof_summary"]["what_proved"])
        self.assertIn("Stack-consumption pilot is ready.", payload["interpreted_proof_summary"]["what_proved"])
        self.assertIn(
            "No final Lifeline receipt artifact observed; Cortex interpretation remains advisory.",
            payload["interpreted_proof_summary"]["what_remains_blocked"],
        )
        self.assertTrue(all(item["status"] == "passed" for item in payload["interpretation_checks"]))
        json.dumps(payload, sort_keys=True)

    def test_validation_critical_or_error_blocks_interpretation(self) -> None:
        root = self._temp_root()
        validation_path = root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json"
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        validation["summary"]["critical"] = 1
        validation["summary"]["error"] = 1
        validation["findings"] = [
            {
                "severity": "error",
                "category": "demo-validation-error",
                "message": "Demonstration blocker.",
            }
        ]
        _write_json(validation_path, validation)

        payload = build_receipt_interpretation_payload(root=root)

        self.assertEqual("blocked", payload["interpretation_result"]["status"])
        self.assertIn("validation-critical-error-absent", payload["interpretation_result"]["failed_checks"])
        self.assertEqual("proof_blocked", payload["interpreted_proof_summary"]["status"])
        self.assertIn("demo-validation-error: Demonstration blocker.", payload["interpreted_proof_summary"]["what_remains_blocked"])

    def test_handoff_authority_widening_blocks(self) -> None:
        root = self._temp_root()
        handoff_path = root / "runtime" / "cortex" / "stack-advisory-handoff" / "latest.json"
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        handoff["routing_contract"]["execution_authorized"] = True
        _write_json(handoff_path, handoff)

        payload = build_receipt_interpretation_payload(root=root)

        self.assertEqual("blocked", payload["interpretation_result"]["status"])
        self.assertIn(
            "stack-advisory-handoff-authority-guard-clean",
            payload["interpretation_result"]["failed_checks"],
        )
        self.assertFalse(payload["authority"]["final_receipt_authorized"])

    def test_pilot_authority_widening_blocks(self) -> None:
        root = self._temp_root()
        pilot_path = root / "runtime" / "cortex" / "stack-consumption-pilot" / "latest.json"
        pilot = json.loads(pilot_path.read_text(encoding="utf-8"))
        pilot["stack_handoff"]["receipt_authorized"] = True
        _write_json(pilot_path, pilot)

        payload = build_receipt_interpretation_payload(root=root)

        self.assertEqual("blocked", payload["interpretation_result"]["status"])
        self.assertIn(
            "stack-consumption-pilot-authority-guard-clean",
            payload["interpretation_result"]["failed_checks"],
        )
        self.assertFalse(payload["authority"]["final_receipt_authorized"])

    def test_lifeline_receipt_candidate_is_observed_not_authorized(self) -> None:
        root = self._temp_root()
        _write_json(
            root / "runtime" / "cortex" / "lifeline-receipt-candidates" / "latest.json",
            {
                "contract_version": "atlas.cortex.lifeline-receipt-candidate.v1",
                "run_id": "cortex-run-promote-cortex-receipt-interpretation-contract-wave9",
                "final_receipt_owner": "lifeline",
                "final_receipt_written": False,
                "candidate_payload_digest": "sha256:demo",
                "source_cortex_artifact_refs": ["runtime/cortex/worker-prompts/latest.json"],
            },
        )

        payload = build_receipt_interpretation_payload(root=root)

        self.assertEqual("receipt_candidate_observed", payload["interpreted_proof_summary"]["status"])
        self.assertTrue(
            any(observation["role"] == "lifeline_receipt_candidate" for observation in payload["receipt_observations"])
        )
        self.assertFalse(payload["authority"]["final_receipt_authorized"])

    def test_candidate_claiming_cortex_final_receipt_authority_blocks(self) -> None:
        root = self._temp_root()
        _write_json(
            root / "runtime" / "cortex" / "lifeline-receipt-candidates" / "latest.json",
            {
                "contract_version": "atlas.cortex.lifeline-receipt-candidate.v1",
                "run_id": "cortex-run-promote-cortex-receipt-interpretation-contract-wave9",
                "final_receipt_owner": "cortex",
                "final_receipt_written": False,
                "candidate_payload_digest": "sha256:demo",
                "source_cortex_artifact_refs": ["runtime/cortex/worker-prompts/latest.json"],
            },
        )

        payload = build_receipt_interpretation_payload(root=root)

        self.assertEqual("blocked", payload["interpretation_result"]["status"])
        self.assertIn("cortex-final-receipt-authority-absent", payload["interpretation_result"]["failed_checks"])
        self.assertFalse(payload["authority"]["final_receipt_authorized"])

    def test_explicit_receipt_with_lifeline_final_owner_and_cortex_prepared_by_is_observed(self) -> None:
        root = self._temp_root()
        receipt_path = root / "tmp" / "lifeline-final-receipt.json"
        _write_json(
            receipt_path,
            {
                "contract_version": "demo.final-receipt.v1",
                "receipt_id": "demo",
                "boundary": {
                    "final_receipt_owner": "lifeline",
                    "prepared_by": "cortex",
                },
            },
        )

        payload = build_receipt_interpretation_payload(root=root, receipt_paths=[receipt_path])

        self.assertEqual("ready", payload["interpretation_result"]["status"])
        self.assertEqual("final_receipt_observed", payload["interpreted_proof_summary"]["status"])
        self.assertFalse(payload["authority"]["final_receipt_authorized"])

    def test_explicit_receipt_with_cortex_final_owner_blocks_even_with_lifeline_mentions(self) -> None:
        root = self._temp_root()
        receipt_path = root / "tmp" / "cortex-final-receipt.json"
        _write_json(
            receipt_path,
            {
                "contract_version": "demo.final-receipt.v1",
                "receipt_id": "demo",
                "boundary": {
                    "final_receipt_owner": "cortex",
                    "prepared_by": "lifeline",
                },
            },
        )

        payload = build_receipt_interpretation_payload(root=root, receipt_paths=[receipt_path])

        self.assertEqual("blocked", payload["interpretation_result"]["status"])
        self.assertIn("cortex-final-receipt-authority-absent", payload["interpretation_result"]["failed_checks"])
        self.assertFalse(payload["authority"]["final_receipt_authorized"])

    def test_markdown_summary_includes_boundary_language(self) -> None:
        root = self._temp_root()

        artifact = persist_receipt_interpretation_artifact(root=root)
        payload = json.loads(default_receipt_interpretation_latest_json_path(root).read_text(encoding="utf-8"))
        summary = default_receipt_interpretation_latest_markdown_path(root).read_text(encoding="utf-8")

        self.assertEqual(json.dumps(payload), json.dumps(artifact.payload))
        self.assertIn("# Cortex Receipt Interpretation", summary)
        self.assertIn("read_only_interpretation", summary)
        self.assertIn("Final receipt authorized: `no`", summary)
        self.assertIn("Lifeline owns final receipt authority", summary)
        self.assertIn("No transcript scraping", summary)

    def test_missing_worker_prompt_fails_clearly(self) -> None:
        root = self._temp_root()
        (root / "runtime" / "cortex" / "worker-prompts" / "latest.json").unlink()

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--root", str(root), "--quiet"])

        self.assertEqual(2, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("Cortex worker-prompt artifact not found", stderr.getvalue())

    def test_schema_declares_emitted_top_level_payload_shape(self) -> None:
        root = self._temp_root()

        payload = build_receipt_interpretation_payload(root=root)
        schema = self.schema_payload

        self.assertFalse(schema["additionalProperties"])
        self.assertTrue(set(payload.keys()).issubset(set(schema["properties"].keys())))
        for required_key in schema["required"]:
            self.assertIn(required_key, payload)


if __name__ == "__main__":
    unittest.main()
