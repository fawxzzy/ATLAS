import json
import unittest

from ops.atlas.atlas_worker_adapter import (
    DryRunCodexAdapter,
    ModelProfile,
    ReceiptValidationError,
    heartbeat_for,
    new_worker_run,
    receipt_for,
    render_receipt_json,
    validate_receipt,
)


class AtlasWorkerAdapterTests(unittest.TestCase):
    def setUp(self):
        self.profile = ModelProfile("gpt-5.6-sol", "xhigh", "gpt-5.6-sol", "xhigh")
        self.run = new_worker_run(
            task_id="platform.rereview",
            profile=self.profile,
            worker_id="worker:platform",
            run_id="run:123",
            process_id=42,
            started_at=100.0,
        )

    def test_run_and_heartbeat_preserve_identity(self):
        heartbeat = heartbeat_for(self.run, observed_at=101.0)
        self.assertEqual(heartbeat.worker_id, "worker:platform")
        self.assertEqual(heartbeat.run_id, "run:123")
        self.assertEqual(heartbeat.process_id, 42)
        self.assertEqual(heartbeat.task_id, "platform.rereview")

    def test_structured_receipt_records_requested_and_effective_profile(self):
        receipt = receipt_for(
            self.run,
            state="SUCCEEDED",
            evidence={"tests": "20/20"},
            emitted_at=102.0,
            event_id="evt:platform",
        )
        self.assertEqual(receipt["worker"]["requested_model"], "gpt-5.6-sol")
        self.assertEqual(receipt["worker"]["effective_reasoning_effort"], "xhigh")
        self.assertEqual(json.loads(render_receipt_json(receipt))["event_id"], "evt:platform")

    def test_receipt_fails_closed_on_identity_mismatch(self):
        receipt = receipt_for(self.run, state="SUCCEEDED", evidence={})
        receipt["worker"]["run_id"] = "run:wrong"
        with self.assertRaisesRegex(ReceiptValidationError, "run_id"):
            validate_receipt(receipt, run=self.run)

    def test_receipt_fails_closed_on_missing_evidence(self):
        receipt = receipt_for(self.run, state="SUCCEEDED", evidence={})
        del receipt["evidence"]
        with self.assertRaisesRegex(ReceiptValidationError, "evidence"):
            validate_receipt(receipt)

    def test_dry_run_renders_but_never_executes(self):
        plan = DryRunCodexAdapter.render_plan(prompt_path="runtime/tasks/p1.md", profile=self.profile)
        self.assertEqual(plan["execution"], "NOT_STARTED")
        self.assertEqual(plan["command"][:3], ["codex", "exec", "--model"])
        self.assertIn("runtime/tasks/p1.md", plan["display"])


if __name__ == "__main__":
    unittest.main()
