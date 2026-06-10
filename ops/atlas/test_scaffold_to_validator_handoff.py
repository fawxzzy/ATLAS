from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.scaffold_to_validator_handoff import (
    ScaffoldToValidatorHandoffError,
    build_scaffold_to_validator_handoff,
)

FIXTURE_ROOT = ROOT / "data" / "fixtures" / "ai-long-run-batch-orchestration" / "scaffold-to-validator-handoff"


def _load_fixture(name: str) -> object:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class ScaffoldToValidatorHandoffTests(unittest.TestCase):
    def test_scaffold_with_missing_required_fields_routes_not_ready(self) -> None:
        result = build_scaffold_to_validator_handoff(_load_fixture("not-validator-ready.json"))
        payload = result.to_payload()
        self.assertEqual(payload["route"], "not-validator-ready")
        self.assertEqual(payload["scaffold_payload"]["candidate_entry"]["status"], "proposed")
        self.assertEqual(
            payload["scaffold_payload"]["missing_required_fields"],
            ["owner_repo", "target_branch_or_worktree", "verification_gate"],
        )
        self.assertNotIn("candidate_entry", payload)

    def test_full_scaffold_routes_validator_input_ready(self) -> None:
        result = build_scaffold_to_validator_handoff(_load_fixture("validator-input-ready.json"))
        payload = result.to_payload()
        self.assertEqual(payload["route"], "validator-input-ready")
        self.assertEqual(payload["candidate_entry"]["status"], "proposed")
        self.assertEqual(payload["candidate_entry"]["entry_id"], "scaffold-to-validator-handoff-002")
        self.assertNotIn("scaffold_payload", payload)

    def test_empty_missing_list_with_not_ready_note_is_rejected(self) -> None:
        with self.assertRaises(ScaffoldToValidatorHandoffError) as context:
            build_scaffold_to_validator_handoff(_load_fixture("empty-missing-not-ready-contradiction.json"))
        self.assertIn("empty missing_required_fields contradict", str(context.exception))

    def test_non_empty_missing_list_with_ready_note_is_rejected(self) -> None:
        with self.assertRaises(ScaffoldToValidatorHandoffError) as context:
            build_scaffold_to_validator_handoff(_load_fixture("non-empty-missing-ready-contradiction.json"))
        self.assertIn("missing_required_fields contradict", str(context.exception))

    def test_non_proposed_candidate_status_is_rejected(self) -> None:
        with self.assertRaises(ScaffoldToValidatorHandoffError) as context:
            build_scaffold_to_validator_handoff(_load_fixture("invalid-status.json"))
        self.assertIn("candidate_entry.status must be exactly proposed", str(context.exception))

    def test_unsupported_top_level_field_is_rejected(self) -> None:
        with self.assertRaises(ScaffoldToValidatorHandoffError) as context:
            build_scaffold_to_validator_handoff(_load_fixture("unsupported-input-mode.json"))
        self.assertIn("unsupported input field", str(context.exception))

    def test_multi_entry_payload_is_rejected(self) -> None:
        with self.assertRaises(ScaffoldToValidatorHandoffError) as context:
            build_scaffold_to_validator_handoff(_load_fixture("multi-entry-payload.json"))
        self.assertIn("multi-entry payloads are unsupported", str(context.exception))


if __name__ == "__main__":
    unittest.main()
