from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.runtime_state_child_path_or_artifact_shape_selection import (
    RuntimeStateChildPathOrArtifactShapeSelectionError,
    classify_runtime_state_child_path_or_artifact_shape_selection,
)

FIXTURE_ROOT = (
    ROOT
    / "data"
    / "fixtures"
    / "ai-long-run-batch-orchestration"
    / "runtime-state-child-path-or-artifact-shape-selection"
)


def _load_fixture(name: str) -> object:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class RuntimeStateChildPathOrArtifactShapeSelectionTests(unittest.TestCase):
    def test_queue_home_destination_root_candidate_stays_unresolved(self) -> None:
        result = classify_runtime_state_child_path_or_artifact_shape_selection(
            _load_fixture("queue-home-destination-root-candidate.json"),
            root=ROOT,
        )
        self.assertEqual(
            result.to_payload(),
            {
                "normalized_candidate_path": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/",
                "decision": "admitted-queue-home-destination-root-unresolved",
                "top_level_home_class": "runtime/",
                "child_home_class": "runtime/state/",
                "layout_family_root": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/",
                "destination_class": "queue-home",
                "destination_root_path": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/",
                "descendant_tail": "none",
                "artifact_status_note": "exact child path, filename, schema, snapshot shape, runtime-state discovery, and final live artifact choice remain deferred",
            },
        )

    def test_queue_home_descendant_candidate_is_admitted_but_not_final(self) -> None:
        result = classify_runtime_state_child_path_or_artifact_shape_selection(
            _load_fixture("queue-home-descendant-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "admitted-queue-home-descendant-candidate")
        self.assertEqual(
            payload["normalized_candidate_path"],
            "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/live/draft-queue.json",
        )
        self.assertEqual(payload["destination_class"], "queue-home")
        self.assertEqual(
            payload["destination_root_path"],
            "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/",
        )
        self.assertEqual(payload["descendant_tail"], "live/draft-queue.json")

    def test_registry_home_destination_root_candidate_stays_unresolved(self) -> None:
        result = classify_runtime_state_child_path_or_artifact_shape_selection(
            _load_fixture("registry-home-destination-root-candidate.json"),
            root=ROOT,
        )
        self.assertEqual(
            result.to_payload(),
            {
                "normalized_candidate_path": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/registry-home/",
                "decision": "admitted-registry-home-destination-root-unresolved",
                "top_level_home_class": "runtime/",
                "child_home_class": "runtime/state/",
                "layout_family_root": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/",
                "destination_class": "registry-home",
                "destination_root_path": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/registry-home/",
                "descendant_tail": "none",
                "artifact_status_note": "exact child path, filename, schema, snapshot shape, runtime-state discovery, and final live artifact choice remain deferred",
            },
        )

    def test_registry_home_descendant_candidate_is_admitted_but_not_final(self) -> None:
        result = classify_runtime_state_child_path_or_artifact_shape_selection(
            _load_fixture("registry-home-descendant-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "admitted-registry-home-descendant-candidate")
        self.assertEqual(
            payload["normalized_candidate_path"],
            "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/registry-home/draft/registry.json",
        )
        self.assertEqual(payload["destination_class"], "registry-home")
        self.assertEqual(
            payload["destination_root_path"],
            "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/registry-home/",
        )
        self.assertEqual(payload["descendant_tail"], "draft/registry.json")

    def test_neutral_family_root_candidate_fails_closed_without_destination(self) -> None:
        result = classify_runtime_state_child_path_or_artifact_shape_selection(
            _load_fixture("neutral-family-root-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "neutral-family-root-without-destination-class")
        self.assertEqual(payload["destination_class"], "none")
        self.assertEqual(payload["destination_root_path"], "none")
        self.assertEqual(payload["descendant_tail"], "none")

    def test_other_neutral_family_descendant_is_non_admitted(self) -> None:
        result = classify_runtime_state_child_path_or_artifact_shape_selection(
            _load_fixture("other-neutral-family-descendant-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "non-admitted-neutral-family-descendant")
        self.assertEqual(payload["destination_class"], "staging-bucket")
        self.assertEqual(payload["destination_root_path"], "none")
        self.assertEqual(payload["descendant_tail"], "none")

    def test_outside_neutral_family_root_candidate_is_rejected(self) -> None:
        result = classify_runtime_state_child_path_or_artifact_shape_selection(
            _load_fixture("outside-neutral-family-root-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "outside-admitted-neutral-family-root")
        self.assertEqual(payload["normalized_candidate_path"], "runtime/state/atlas/session-cache")
        self.assertEqual(payload["child_home_class"], "none")
        self.assertEqual(payload["layout_family_root"], "none")
        self.assertEqual(payload["destination_class"], "none")

    def test_multi_candidate_or_discovered_input_is_rejected(self) -> None:
        for fixture_name in ("multi-candidate-payload.json", "discovered-input-mode.json"):
            with self.subTest(fixture_name=fixture_name):
                with self.assertRaises(RuntimeStateChildPathOrArtifactShapeSelectionError) as context:
                    classify_runtime_state_child_path_or_artifact_shape_selection(
                        _load_fixture(fixture_name),
                        root=ROOT,
                    )
                self.assertIn("unsupported input field", str(context.exception))

    def test_queue_registry_or_execution_hint_payload_is_rejected(self) -> None:
        for fixture_name in ("queue-or-execution-hint-payload.json", "registry-hint-payload.json"):
            with self.subTest(fixture_name=fixture_name):
                with self.assertRaises(RuntimeStateChildPathOrArtifactShapeSelectionError) as context:
                    classify_runtime_state_child_path_or_artifact_shape_selection(
                        _load_fixture(fixture_name),
                        root=ROOT,
                    )
                self.assertIn("unsupported input field", str(context.exception))


if __name__ == "__main__":
    unittest.main()
