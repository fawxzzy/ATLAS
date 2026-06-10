from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.entry_status_summary_renderer import (
    EntryStatusSummaryRendererError,
    build_entry_status_summary,
)

FIXTURE_ROOT = ROOT / "data" / "fixtures" / "ai-long-run-batch-orchestration" / "entry-status-summary-renderer"


def _load_fixture(name: str) -> object:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class EntryStatusSummaryRendererTests(unittest.TestCase):
    def test_ordered_mixed_handoff_set_preserves_input_order(self) -> None:
        result = build_entry_status_summary(_load_fixture("ordered-mixed-handoff-set.json"))
        payload = result.to_payload()
        self.assertEqual(payload["entry_count"], 2)
        self.assertEqual(
            payload["entries"],
            [
                {
                    "entry_id": "entry-status-summary-renderer-001",
                    "status": "proposed",
                    "readiness_route": "not-validator-ready",
                    "missing_required_fields_count": 2,
                },
                {
                    "entry_id": "entry-status-summary-renderer-002",
                    "status": "proposed",
                    "readiness_route": "validator-input-ready",
                    "missing_required_fields_count": 0,
                },
            ],
        )
        self.assertEqual(payload["status_counts"], {"proposed": 2})
        self.assertEqual(
            payload["readiness_counts"],
            {"not-validator-ready": 1, "validator-input-ready": 1},
        )

    def test_all_not_ready_handoff_set_counts_missing_fields(self) -> None:
        result = build_entry_status_summary(_load_fixture("all-not-validator-ready.json"))
        payload = result.to_payload()
        self.assertEqual(payload["entry_count"], 2)
        self.assertEqual(
            [row["missing_required_fields_count"] for row in payload["entries"]],
            [3, 1],
        )
        self.assertEqual(payload["readiness_counts"], {"not-validator-ready": 2})

    def test_all_ready_handoff_set_preserves_proposed_status(self) -> None:
        result = build_entry_status_summary(_load_fixture("all-validator-input-ready.json"))
        payload = result.to_payload()
        self.assertEqual(payload["entry_count"], 2)
        self.assertEqual([row["status"] for row in payload["entries"]], ["proposed", "proposed"])
        self.assertEqual([row["missing_required_fields_count"] for row in payload["entries"]], [0, 0])
        self.assertEqual(payload["readiness_counts"], {"validator-input-ready": 2})

    def test_raw_scaffold_payload_is_rejected(self) -> None:
        with self.assertRaises(EntryStatusSummaryRendererError) as context:
            build_entry_status_summary(_load_fixture("unsupported-raw-scaffold-payload.json"))
        self.assertIn("unsupported route", str(context.exception))

    def test_raw_validator_result_payload_is_rejected(self) -> None:
        with self.assertRaises(EntryStatusSummaryRendererError) as context:
            build_entry_status_summary(_load_fixture("unsupported-raw-validator-result-payload.json"))
        self.assertIn("unsupported route", str(context.exception))

    def test_unsupported_input_mode_is_rejected(self) -> None:
        with self.assertRaises(EntryStatusSummaryRendererError) as context:
            build_entry_status_summary(_load_fixture("unsupported-input-mode.json"))
        self.assertIn("unsupported input field", str(context.exception))

    def test_multi_source_input_mode_is_rejected(self) -> None:
        with self.assertRaises(EntryStatusSummaryRendererError) as context:
            build_entry_status_summary(_load_fixture("discovered-multi-source-input-mode.json"))
        self.assertIn("unsupported input field", str(context.exception))

    def test_malformed_route_item_is_rejected(self) -> None:
        with self.assertRaises(EntryStatusSummaryRendererError) as context:
            build_entry_status_summary(_load_fixture("malformed-route-item.json"))
        self.assertIn("unsupported route", str(context.exception))


if __name__ == "__main__":
    unittest.main()
