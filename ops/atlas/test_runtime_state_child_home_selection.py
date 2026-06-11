from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.runtime_state_child_home_selection import (
    RuntimeStateChildHomeSelectionError,
    classify_runtime_state_child_home_selection,
)

FIXTURE_ROOT = (
    ROOT
    / "data"
    / "fixtures"
    / "ai-long-run-batch-orchestration"
    / "runtime-state-child-home-selection"
)


def _load_fixture(name: str) -> object:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class RuntimeStateChildHomeSelectionTests(unittest.TestCase):
    def test_runtime_state_root_candidate_is_admitted(self) -> None:
        result = classify_runtime_state_child_home_selection(_load_fixture("state-root-candidate.json"), root=ROOT)
        self.assertEqual(
            result.to_payload(),
            {
                "normalized_candidate_path": "runtime/state/",
                "decision": "admitted-state-child-home-candidate",
                "top_level_home_class": "runtime/",
                "child_home_class": "runtime/state/",
                "layout_status_note": "exact runtime subtree, filename, schema, snapshot shape, and persistence layout remain deferred",
            },
        )

    def test_runtime_state_descendant_candidate_is_admitted(self) -> None:
        result = classify_runtime_state_child_home_selection(
            _load_fixture("state-descendant-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "admitted-state-child-home-candidate")
        self.assertEqual(
            payload["normalized_candidate_path"],
            "runtime/state/ai-long-run-batch-orchestration/queue-registry-proposal.json",
        )
        self.assertEqual(payload["top_level_home_class"], "runtime/")
        self.assertEqual(payload["child_home_class"], "runtime/state/")

    def test_runtime_receipts_root_candidate_is_excluded(self) -> None:
        result = classify_runtime_state_child_home_selection(_load_fixture("receipts-root-candidate.json"), root=ROOT)
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "excluded-receipt-history-child-home")
        self.assertEqual(payload["normalized_candidate_path"], "runtime/receipts/")
        self.assertEqual(payload["child_home_class"], "runtime/receipts/")

    def test_runtime_receipts_descendant_candidate_is_excluded(self) -> None:
        result = classify_runtime_state_child_home_selection(
            _load_fixture("receipts-descendant-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "excluded-receipt-history-child-home")
        self.assertEqual(
            payload["normalized_candidate_path"],
            "runtime/receipts/ai-long-run-batch-orchestration/pass-42.md",
        )
        self.assertEqual(payload["child_home_class"], "runtime/receipts/")

    def test_other_runtime_child_home_candidate_is_non_admitted(self) -> None:
        result = classify_runtime_state_child_home_selection(
            _load_fixture("other-runtime-child-home-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "non-admitted-runtime-child-home")
        self.assertEqual(payload["top_level_home_class"], "runtime/")
        self.assertEqual(payload["child_home_class"], "runtime/cortex/")

    def test_non_runtime_top_level_candidate_is_outside_runtime_family(self) -> None:
        result = classify_runtime_state_child_home_selection(
            _load_fixture("non-runtime-top-level-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "outside-runtime-home-family")
        self.assertEqual(payload["top_level_home_class"], "docs/")
        self.assertEqual(payload["child_home_class"], "none")

    def test_multi_candidate_or_discovered_input_is_rejected(self) -> None:
        for fixture_name in ("multi-candidate-payload.json", "discovered-input-mode.json"):
            with self.subTest(fixture_name=fixture_name):
                with self.assertRaises(RuntimeStateChildHomeSelectionError) as context:
                    classify_runtime_state_child_home_selection(_load_fixture(fixture_name), root=ROOT)
                self.assertIn("unsupported input field", str(context.exception))

    def test_queue_or_execution_hint_payload_is_rejected(self) -> None:
        with self.assertRaises(RuntimeStateChildHomeSelectionError) as context:
            classify_runtime_state_child_home_selection(
                _load_fixture("queue-or-execution-hint-payload.json"),
                root=ROOT,
            )
        self.assertIn("unsupported input field", str(context.exception))


if __name__ == "__main__":
    unittest.main()
