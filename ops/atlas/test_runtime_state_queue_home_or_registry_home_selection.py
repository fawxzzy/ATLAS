from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.runtime_state_queue_home_or_registry_home_selection import (
    RuntimeStateQueueHomeOrRegistryHomeSelectionError,
    classify_runtime_state_queue_home_or_registry_home_selection,
)

FIXTURE_ROOT = (
    ROOT
    / "data"
    / "fixtures"
    / "ai-long-run-batch-orchestration"
    / "runtime-state-queue-home-or-registry-home-selection"
)


def _load_fixture(name: str) -> object:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class RuntimeStateQueueHomeOrRegistryHomeSelectionTests(unittest.TestCase):
    def test_neutral_family_root_candidate_is_admitted(self) -> None:
        result = classify_runtime_state_queue_home_or_registry_home_selection(
            _load_fixture("neutral-family-root-candidate.json"),
            root=ROOT,
        )
        self.assertEqual(
            result.to_payload(),
            {
                "normalized_candidate_path": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/",
                "decision": "admitted-neutral-family-root",
                "top_level_home_class": "runtime/",
                "child_home_class": "runtime/state/",
                "layout_family_root": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/",
                "destination_class": "unresolved-neutral-root",
                "artifact_status_note": "exact child path, filename, schema, snapshot shape, runtime-state discovery, and final live artifact choice remain deferred",
            },
        )

    def test_queue_home_root_candidate_is_admitted(self) -> None:
        result = classify_runtime_state_queue_home_or_registry_home_selection(
            _load_fixture("queue-home-destination-root-candidate.json"),
            root=ROOT,
        )
        self.assertEqual(
            result.to_payload(),
            {
                "normalized_candidate_path": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/",
                "decision": "admitted-queue-home-destination-class",
                "top_level_home_class": "runtime/",
                "child_home_class": "runtime/state/",
                "layout_family_root": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/",
                "destination_class": "queue-home",
                "artifact_status_note": "exact child path, filename, schema, snapshot shape, runtime-state discovery, and final live artifact choice remain deferred",
            },
        )

    def test_queue_home_descendant_candidate_is_admitted(self) -> None:
        result = classify_runtime_state_queue_home_or_registry_home_selection(
            _load_fixture("queue-home-descendant-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "admitted-queue-home-destination-class")
        self.assertEqual(
            payload["normalized_candidate_path"],
            "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/live/draft-queue.json",
        )
        self.assertEqual(payload["destination_class"], "queue-home")

    def test_registry_home_root_candidate_is_admitted(self) -> None:
        result = classify_runtime_state_queue_home_or_registry_home_selection(
            _load_fixture("registry-home-destination-root-candidate.json"),
            root=ROOT,
        )
        self.assertEqual(
            result.to_payload(),
            {
                "normalized_candidate_path": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/registry-home/",
                "decision": "admitted-registry-home-destination-class",
                "top_level_home_class": "runtime/",
                "child_home_class": "runtime/state/",
                "layout_family_root": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/",
                "destination_class": "registry-home",
                "artifact_status_note": "exact child path, filename, schema, snapshot shape, runtime-state discovery, and final live artifact choice remain deferred",
            },
        )

    def test_registry_home_descendant_candidate_is_admitted(self) -> None:
        result = classify_runtime_state_queue_home_or_registry_home_selection(
            _load_fixture("registry-home-descendant-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "admitted-registry-home-destination-class")
        self.assertEqual(
            payload["normalized_candidate_path"],
            "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/registry-home/draft/registry.json",
        )
        self.assertEqual(payload["destination_class"], "registry-home")

    def test_other_neutral_family_descendant_is_non_admitted(self) -> None:
        result = classify_runtime_state_queue_home_or_registry_home_selection(
            _load_fixture("other-neutral-family-descendant-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "non-admitted-neutral-family-descendant")
        self.assertEqual(
            payload["normalized_candidate_path"],
            "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/staging-bucket/pending.json",
        )
        self.assertEqual(payload["layout_family_root"], "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/")
        self.assertEqual(payload["destination_class"], "staging-bucket")

    def test_outside_neutral_family_root_candidate_is_rejected(self) -> None:
        result = classify_runtime_state_queue_home_or_registry_home_selection(
            _load_fixture("outside-neutral-family-root-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "outside-admitted-neutral-family-root")
        self.assertEqual(payload["normalized_candidate_path"], "runtime/state/atlas/session-cache")
        self.assertEqual(payload["top_level_home_class"], "runtime/")
        self.assertEqual(payload["child_home_class"], "none")
        self.assertEqual(payload["layout_family_root"], "none")
        self.assertEqual(payload["destination_class"], "none")

    def test_multi_candidate_or_discovered_input_is_rejected(self) -> None:
        for fixture_name in ("multi-candidate-payload.json", "discovered-input-mode.json"):
            with self.subTest(fixture_name=fixture_name):
                with self.assertRaises(RuntimeStateQueueHomeOrRegistryHomeSelectionError) as context:
                    classify_runtime_state_queue_home_or_registry_home_selection(
                        _load_fixture(fixture_name),
                        root=ROOT,
                    )
                self.assertIn("unsupported input field", str(context.exception))

    def test_queue_or_execution_hint_payload_is_rejected(self) -> None:
        with self.assertRaises(RuntimeStateQueueHomeOrRegistryHomeSelectionError) as context:
            classify_runtime_state_queue_home_or_registry_home_selection(
                _load_fixture("queue-or-execution-hint-payload.json"),
                root=ROOT,
            )
        self.assertIn("unsupported input field", str(context.exception))


if __name__ == "__main__":
    unittest.main()
