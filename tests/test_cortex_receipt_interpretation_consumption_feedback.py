from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.receipt_interpretation_consumption_feedback import (
    build_receipt_interpretation_consumption_feedback_payload,
    default_receipt_interpretation_consumption_feedback_latest_json_path,
    default_receipt_interpretation_consumption_feedback_latest_markdown_path,
    main,
    persist_receipt_interpretation_consumption_feedback_artifact,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class CortexReceiptInterpretationConsumptionFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.receipt_interpretation_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "receipt-interpretation" / "latest.json").read_text(encoding="utf-8")
        )
        cls.stack_consumption_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "receipt-interpretation-stack-consumption" / "latest.json").read_text(
                encoding="utf-8"
            )
        )
        cls.stack_handoff_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "stack-advisory-handoff" / "latest.json").read_text(encoding="utf-8")
        )
        cls.stack_pilot_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "stack-consumption-pilot" / "latest.json").read_text(encoding="utf-8")
        )
        cls.worker_prompt_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "worker-prompts" / "latest.json").read_text(encoding="utf-8")
        )
        cls.ledger_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "ledger" / "latest.json").read_text(encoding="utf-8")
        )
        cls.validation_payload = json.loads(
            (cls.root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json").read_text(
                encoding="utf-8"
            )
        )
        cls.state_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json").read_text(encoding="utf-8")
        )
        cls.rule_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json").read_text(encoding="utf-8")
        )
        cls.schema_payload = json.loads(
            (
                cls.root / "schemas" / "atlas.cortex.receipt-interpretation-consumption-feedback.v1.json"
            ).read_text(encoding="utf-8")
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

    def _base_receipt_interpretation_payload(self) -> dict:
        payload = deepcopy(self.receipt_interpretation_payload)
        payload["interpretation_result"] = {
            "status": "ready",
            "ready_for_stack_consumer": True,
            "blocked_reason": None,
            "failed_checks": [],
        }
        payload["interpreted_proof_summary"] = {
            "status": "proof_ready",
            "what_proved": [
                "Receipt interpretation proof posture is proof_ready.",
                "Stack advisory handoff is ready.",
            ],
            "what_remains_blocked": [
                "No final Lifeline receipt artifact observed; Cortex interpretation remains advisory."
            ],
        }
        payload["source_refs"] = [
            "runtime/cortex/worker-prompts/latest.json",
            "runtime/cortex/stack-advisory-handoff/latest.json",
            "runtime/cortex/stack-consumption-pilot/latest.json",
            "runtime/cortex/ledger/latest.json",
        ]
        return payload

    def _base_stack_consumption_payload(self) -> dict:
        payload = deepcopy(self.stack_consumption_payload)
        payload["consumption_result"] = {
            "status": "ready",
            "ready_for_stack_consumer": True,
            "blocked_reason": None,
            "failed_checks": [],
        }
        payload["consumption_summary"] = {
            "what_changed": [
                "Receipt interpretation is now consumable through explicit artifact refs.",
            ],
            "what_proved": [
                "Receipt interpretation proof posture is consumable by _stack without authority widening.",
            ],
            "what_remains_blocked": [
                "Final receipt authority remains outside Cortex."
            ],
        }
        payload["authority"] = {
            "stack_consumption_authorized": True,
            "automatic_dispatch_enabled": False,
            "final_receipt_authorized": False,
            "approval_authorized": False,
            "execution_authorized": False,
            "dispatch_authorized": False,
            "owner_truth_mutation_authorized": False,
            "lifeline_truth_mutation_authorized": False,
            "transcript_scraping_allowed": False,
        }
        payload["source_refs"] = [
            "runtime/cortex/receipt-interpretation/latest.json",
            "runtime/cortex/stack-advisory-handoff/latest.json",
            "runtime/cortex/stack-consumption-pilot/latest.json",
            "runtime/cortex/worker-prompts/latest.json",
            "runtime/cortex/ledger/latest.json",
        ]
        return payload

    def _base_stack_handoff_payload(self) -> dict:
        payload = deepcopy(self.stack_handoff_payload)
        payload["handoff_result"] = {
            "status": "ready",
            "ready_for_stack_consumer": True,
            "blocked_reason": None,
            "failed_checks": [],
        }
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-receipt-interpretation-consumption-feedback-wave11",
            "owner_layer": "cortex",
            "rationale": "Cortex needs one read-only feedback contract over receipt-interpretation stack consumption.",
        }
        return payload

    def _base_stack_pilot_payload(self) -> dict:
        payload = deepcopy(self.stack_pilot_payload)
        payload["pilot_result"] = {
            "status": "ready",
            "ready_for_stack_consumer": True,
            "blocked_reason": None,
            "failed_checks": [],
        }
        return payload

    def _base_worker_prompt_payload(self) -> dict:
        payload = deepcopy(self.worker_prompt_payload)
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-receipt-interpretation-consumption-feedback-wave11",
            "owner_layer": "cortex",
            "rationale": "Cortex needs one read-only feedback contract over receipt-interpretation stack consumption.",
        }
        payload["boundary_reminders"] = [
            "Cortex observes, interprets, and proves.",
            "Cortex does not become owner truth for product, governance, or receipts.",
        ]
        return payload

    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(
            root / "runtime" / "cortex" / "receipt-interpretation" / "latest.json",
            self._base_receipt_interpretation_payload(),
        )
        _write_json(
            root / "runtime" / "cortex" / "receipt-interpretation-stack-consumption" / "latest.json",
            self._base_stack_consumption_payload(),
        )
        _write_json(
            root / "runtime" / "cortex" / "stack-advisory-handoff" / "latest.json",
            self._base_stack_handoff_payload(),
        )
        _write_json(
            root / "runtime" / "cortex" / "stack-consumption-pilot" / "latest.json",
            self._base_stack_pilot_payload(),
        )
        _write_json(
            root / "runtime" / "cortex" / "worker-prompts" / "latest.json",
            self._base_worker_prompt_payload(),
        )
        _write_json(root / "runtime" / "cortex" / "ledger" / "latest.json", self.ledger_payload)
        _write_json(
            root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json",
            self._base_validation_payload(),
        )
        _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", self.state_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", self.rule_payload)
        return root

    def test_ready_feedback_from_clean_consumption_inputs(self) -> None:
        root = self._temp_root()

        payload = build_receipt_interpretation_consumption_feedback_payload(root=root)

        self.assertEqual(
            "atlas.cortex.receipt-interpretation-consumption-feedback.v1",
            payload["contract_version"],
        )
        self.assertEqual("read_only_feedback", payload["authority_level"])
        self.assertEqual("ready", payload["feedback_result"]["status"])
        self.assertTrue(payload["feedback_result"]["ready_for_feedback_consumer"])
        self.assertEqual(
            "promote-cortex-receipt-interpretation-consumption-feedback-wave11",
            payload["next_recommended_lane"]["lane_id"],
        )
        self.assertIn(
            "Receipt interpretation proof posture is consumable by _stack without authority widening.",
            payload["feedback_summary"]["what_proved"],
        )
        json.dumps(payload, sort_keys=True)

    def test_consumption_authority_widening_blocks_feedback(self) -> None:
        root = self._temp_root()
        consumption_path = root / "runtime" / "cortex" / "receipt-interpretation-stack-consumption" / "latest.json"
        payload = json.loads(consumption_path.read_text(encoding="utf-8"))
        payload["authority"]["execution_authorized"] = True
        _write_json(consumption_path, payload)

        feedback = build_receipt_interpretation_consumption_feedback_payload(root=root)

        self.assertEqual("blocked", feedback["feedback_result"]["status"])
        self.assertIn(
            "receipt-interpretation-stack-consumption-authority-guard-clean",
            feedback["feedback_result"]["failed_checks"],
        )

    def test_validation_critical_or_error_blocks_feedback(self) -> None:
        root = self._temp_root()
        validation_path = root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json"
        payload = json.loads(validation_path.read_text(encoding="utf-8"))
        payload["summary"]["error"] = 1
        payload["findings"] = [
            {
                "severity": "error",
                "category": "demo-validation-error",
                "message": "Demonstration blocker."
            }
        ]
        _write_json(validation_path, payload)

        feedback = build_receipt_interpretation_consumption_feedback_payload(root=root)

        self.assertEqual("blocked", feedback["feedback_result"]["status"])
        self.assertIn("validation-critical-error-absent", feedback["feedback_result"]["failed_checks"])

    def test_transcript_ref_blocks_feedback(self) -> None:
        root = self._temp_root()
        interpretation_path = root / "runtime" / "cortex" / "receipt-interpretation" / "latest.json"
        payload = json.loads(interpretation_path.read_text(encoding="utf-8"))
        payload["source_refs"].append("runtime/atlas/conversations/demo-transcript.json")
        _write_json(interpretation_path, payload)

        feedback = build_receipt_interpretation_consumption_feedback_payload(root=root)

        self.assertEqual("blocked", feedback["feedback_result"]["status"])
        self.assertIn("transcript-scraping-absent", feedback["feedback_result"]["failed_checks"])

    def test_markdown_summary_includes_feedback_boundaries(self) -> None:
        root = self._temp_root()

        artifact = persist_receipt_interpretation_consumption_feedback_artifact(root=root)
        payload = json.loads(
            default_receipt_interpretation_consumption_feedback_latest_json_path(root).read_text(encoding="utf-8")
        )
        summary = default_receipt_interpretation_consumption_feedback_latest_markdown_path(root).read_text(
            encoding="utf-8"
        )

        self.assertEqual(json.dumps(payload), json.dumps(artifact.payload))
        self.assertIn("# Cortex Receipt Interpretation Consumption Feedback", summary)
        self.assertIn("read_only_feedback", summary)
        self.assertIn("What Proved", summary)
        self.assertIn("Feedback Checks", summary)
        self.assertIn("feedback does not dispatch or execute _stack work".lower(), summary.lower())

    def test_missing_stack_consumption_artifact_fails_clearly(self) -> None:
        root = self._temp_root()
        (
            root / "runtime" / "cortex" / "receipt-interpretation-stack-consumption" / "latest.json"
        ).unlink()

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--root", str(root), "--quiet"])

        self.assertEqual(2, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("Cortex receipt-interpretation stack-consumption artifact not found", stderr.getvalue())

    def test_schema_declares_emitted_top_level_payload_shape(self) -> None:
        root = self._temp_root()

        payload = build_receipt_interpretation_consumption_feedback_payload(root=root)
        schema = self.schema_payload

        self.assertFalse(schema["additionalProperties"])
        self.assertTrue(set(payload.keys()).issubset(set(schema["properties"].keys())))
        for required_key in schema["required"]:
            self.assertIn(required_key, payload)


if __name__ == "__main__":
    unittest.main()
