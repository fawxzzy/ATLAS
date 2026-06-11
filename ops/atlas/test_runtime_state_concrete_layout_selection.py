from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.runtime_state_concrete_layout_selection import (
    RuntimeStateConcreteLayoutSelectionError,
    classify_runtime_state_concrete_layout_selection,
)

FIXTURE_ROOT = (
    ROOT
    / "data"
    / "fixtures"
    / "ai-long-run-batch-orchestration"
    / "runtime-state-concrete-layout-selection"
)


def _load_fixture(name: str) -> object:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class RuntimeStateConcreteLayoutSelectionTests(unittest.TestCase):
    def test_neutral_layout_family_root_candidate_is_admitted(self) -> None:
        result = classify_runtime_state_concrete_layout_selection(
            _load_fixture("neutral-layout-family-root-candidate.json"),
            root=ROOT,
        )
        self.assertEqual(
            result.to_payload(),
            {
                "normalized_candidate_path": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/",
                "decision": "admitted-neutral-layout-family-root",
                "top_level_home_class": "runtime/",
                "child_home_class": "runtime/state/",
                "layout_family_root": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/",
                "layout_status_note": "exact filename, schema, snapshot shape, runtime-state discovery, and final queue-home or registry-home choice remain deferred",
            },
        )

    def test_neutral_layout_family_descendant_candidate_is_admitted(self) -> None:
        result = classify_runtime_state_concrete_layout_selection(
            _load_fixture("neutral-layout-family-descendant-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "admitted-neutral-layout-family-descendant")
        self.assertEqual(
            payload["normalized_candidate_path"],
            "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/draft-entries/proposed-entry.json",
        )
        self.assertEqual(payload["top_level_home_class"], "runtime/")
        self.assertEqual(payload["child_home_class"], "runtime/state/")
        self.assertEqual(
            payload["layout_family_root"],
            "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/",
        )

    def test_retained_state_sibling_candidate_is_non_admitted(self) -> None:
        result = classify_runtime_state_concrete_layout_selection(
            _load_fixture("retained-state-sibling-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "non-admitted-retained-state-sibling")
        self.assertEqual(payload["normalized_candidate_path"], "runtime/state/atlas/session-cache")
        self.assertEqual(payload["child_home_class"], "runtime/state/")
        self.assertEqual(payload["layout_family_root"], "runtime/state/atlas/")

    def test_other_lane_descendant_candidate_is_non_admitted(self) -> None:
        result = classify_runtime_state_concrete_layout_selection(
            _load_fixture("other-lane-descendant-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "non-admitted-retained-state-sibling")
        self.assertEqual(
            payload["normalized_candidate_path"],
            "runtime/state/ai-long-run-batch-orchestration/manual-review/pending.json",
        )
        self.assertEqual(payload["child_home_class"], "runtime/state/")
        self.assertEqual(payload["layout_family_root"], "runtime/state/ai-long-run-batch-orchestration/")

    def test_outside_child_home_candidate_is_rejected(self) -> None:
        result = classify_runtime_state_concrete_layout_selection(
            _load_fixture("outside-child-home-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "outside-admitted-state-child-home")
        self.assertEqual(
            payload["normalized_candidate_path"],
            "runtime/receipts/ai-long-run-batch-orchestration/pass-49.md",
        )
        self.assertEqual(payload["top_level_home_class"], "runtime/")
        self.assertEqual(payload["child_home_class"], "none")
        self.assertEqual(payload["layout_family_root"], "none")

    def test_multi_candidate_or_discovered_input_is_rejected(self) -> None:
        for fixture_name in ("multi-candidate-payload.json", "discovered-input-mode.json"):
            with self.subTest(fixture_name=fixture_name):
                with self.assertRaises(RuntimeStateConcreteLayoutSelectionError) as context:
                    classify_runtime_state_concrete_layout_selection(_load_fixture(fixture_name), root=ROOT)
                self.assertIn("unsupported input field", str(context.exception))

    def test_queue_or_execution_hint_payload_is_rejected(self) -> None:
        with self.assertRaises(RuntimeStateConcreteLayoutSelectionError) as context:
            classify_runtime_state_concrete_layout_selection(
                _load_fixture("queue-or-execution-hint-payload.json"),
                root=ROOT,
            )
        self.assertIn("unsupported input field", str(context.exception))


if __name__ == "__main__":
    unittest.main()
