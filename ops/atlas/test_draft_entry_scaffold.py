from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.draft_entry_scaffold import DraftEntryScaffoldError, build_draft_entry_scaffold

FIXTURE_ROOT = ROOT / "data" / "fixtures" / "ai-long-run-batch-orchestration" / "draft-entry-scaffold"


def _load_fixture(name: str) -> object:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class DraftEntryScaffoldTests(unittest.TestCase):
    def test_partial_candidate_renders_missing_markers(self) -> None:
        result = build_draft_entry_scaffold(_load_fixture("partial-single-candidate.json"))
        payload = result.to_payload()
        self.assertEqual(payload["candidate_entry"]["status"], "proposed")
        self.assertEqual(payload["candidate_entry"]["entry_id"], "draft-entry-scaffold-001")
        self.assertEqual(payload["candidate_entry"]["owner_repo"], "MISSING_OWNER_REPO")
        self.assertEqual(
            payload["missing_required_fields"],
            [
                "owner_repo",
                "target_branch_or_worktree",
                "allowed_write_scope",
                "checkpoint_surface",
                "verification_gate",
                "closeout_artifact",
                "park_or_escalation_rule",
                "protected_surface_exclusions",
                "created_from_receipt",
                "last_reconciled_receipt",
            ],
        )

    def test_full_explicit_candidate_has_no_missing_required_fields(self) -> None:
        result = build_draft_entry_scaffold(_load_fixture("full-explicit-candidate.json"))
        payload = result.to_payload()
        self.assertEqual(payload["missing_required_fields"], [])
        self.assertEqual(payload["candidate_entry"]["status"], "proposed")
        self.assertEqual(payload["candidate_entry"]["owner_repo"], "atlas-root")

    def test_non_proposed_status_is_rejected(self) -> None:
        with self.assertRaises(DraftEntryScaffoldError) as context:
            build_draft_entry_scaffold(_load_fixture("invalid-status.json"))
        self.assertIn("status must be omitted or explicitly set to proposed", str(context.exception))

    def test_optional_fields_are_rejected(self) -> None:
        with self.assertRaises(DraftEntryScaffoldError) as context:
            build_draft_entry_scaffold(_load_fixture("optional-field-misuse.json"))
        self.assertIn("is not admitted for a proposed scaffold", str(context.exception))

    def test_unsupported_input_field_is_rejected(self) -> None:
        with self.assertRaises(DraftEntryScaffoldError) as context:
            build_draft_entry_scaffold(_load_fixture("unsupported-input-mode.json"))
        self.assertIn("unsupported input field", str(context.exception))

    def test_multi_entry_payload_is_rejected(self) -> None:
        with self.assertRaises(DraftEntryScaffoldError) as context:
            build_draft_entry_scaffold(_load_fixture("multi-entry-payload.json"))
        self.assertIn("multi-entry payloads are unsupported", str(context.exception))


if __name__ == "__main__":
    unittest.main()
