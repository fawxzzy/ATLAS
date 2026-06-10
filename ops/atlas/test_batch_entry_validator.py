from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.batch_entry_validator import validate_batch_entry_payload

FIXTURE_ROOT = ROOT / "data" / "fixtures" / "ai-long-run-batch-orchestration" / "batch-entry-validator"


def _load_fixture(name: str) -> object:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class BatchEntryValidatorTests(unittest.TestCase):
    def test_valid_single_candidate(self) -> None:
        result = validate_batch_entry_payload(_load_fixture("valid-single-candidate.json"), root=ROOT)
        payload = result.to_payload()
        self.assertEqual(payload["result"], "valid")
        self.assertEqual(payload["entry_id"], "batch-entry-validator-001")
        self.assertNotIn("missing_fields", payload)
        self.assertNotIn("invalid_fields", payload)
        self.assertNotIn("protected_surface_failure", payload)

    def test_valid_blocked_candidate_with_triggered_optional_fields(self) -> None:
        result = validate_batch_entry_payload(_load_fixture("valid-blocked-candidate.json"), root=ROOT)
        payload = result.to_payload()
        self.assertEqual(payload["result"], "valid")
        self.assertEqual(payload["status"], "blocked")
        self.assertNotIn("invalid_fields", payload)

    def test_missing_required_field(self) -> None:
        result = validate_batch_entry_payload(_load_fixture("missing-required-field.json"), root=ROOT)
        payload = result.to_payload()
        self.assertEqual(payload["result"], "invalid-missing-field")
        self.assertIn("verification_gate", payload["missing_fields"])

    def test_missing_cited_receipt_fields_are_reported(self) -> None:
        result = validate_batch_entry_payload(_load_fixture("missing-cited-receipt-fields.json"), root=ROOT)
        payload = result.to_payload()
        self.assertEqual(payload["result"], "invalid-missing-field")
        self.assertEqual(
            sorted(payload["cited_receipt_fields"]),
            ["created_from_receipt", "last_reconciled_receipt"],
        )

    def test_invalid_status(self) -> None:
        result = validate_batch_entry_payload(_load_fixture("invalid-status.json"), root=ROOT)
        payload = result.to_payload()
        self.assertEqual(payload["result"], "invalid-status")
        self.assertEqual(payload["invalid_fields"]["status"], "queued")

    def test_optional_field_misuse(self) -> None:
        result = validate_batch_entry_payload(_load_fixture("optional-field-misuse.json"), root=ROOT)
        payload = result.to_payload()
        self.assertEqual(payload["result"], "invalid-optional-field")
        self.assertIn("blocking_class", payload["invalid_fields"])

    def test_multi_owner_scope(self) -> None:
        result = validate_batch_entry_payload(_load_fixture("multi-owner-scope.json"), root=ROOT)
        payload = result.to_payload()
        self.assertEqual(payload["result"], "invalid-owner-boundary")

    def test_multi_target_scope(self) -> None:
        result = validate_batch_entry_payload(_load_fixture("multi-target-scope.json"), root=ROOT)
        payload = result.to_payload()
        self.assertEqual(payload["result"], "invalid-target-boundary")

    def test_protected_surface_failure(self) -> None:
        result = validate_batch_entry_payload(_load_fixture("protected-surface-failure.json"), root=ROOT)
        payload = result.to_payload()
        self.assertEqual(payload["result"], "invalid-protected-surface-exclusion")
        self.assertTrue(payload["protected_surface_failure"])

    def test_unsupported_input_mode(self) -> None:
        result = validate_batch_entry_payload(_load_fixture("unsupported-input-mode.json"), root=ROOT)
        payload = result.to_payload()
        self.assertEqual(payload["result"], "invalid-input")
        self.assertIn("unsupported input field", payload["input_failure_reason"])

    def test_multi_entry_payload_is_rejected(self) -> None:
        result = validate_batch_entry_payload(_load_fixture("multi-entry-payload.json"), root=ROOT)
        payload = result.to_payload()
        self.assertEqual(payload["result"], "invalid-input")
        self.assertIn("multi-entry payloads", payload["input_failure_reason"])


if __name__ == "__main__":
    unittest.main()
