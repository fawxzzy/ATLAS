from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.runtime_state_artifact_shape_selection import (
    RuntimeStateArtifactShapeSelectionError,
    classify_runtime_state_artifact_shape_selection,
)

FIXTURE_ROOT = (
    ROOT
    / "data"
    / "fixtures"
    / "ai-long-run-batch-orchestration"
    / "runtime-state-artifact-shape-selection"
)


def _load_fixture(name: str) -> object:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class RuntimeStateArtifactShapeSelectionTests(unittest.TestCase):
    def test_queue_home_destination_root_candidate_stays_unresolved(self) -> None:
        result = classify_runtime_state_artifact_shape_selection(
            _load_fixture("queue-home-destination-root-candidate.json"),
            root=ROOT,
        )
        self.assertEqual(
            result.to_payload(),
            {
                "normalized_candidate_path": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/",
                "decision": "queue-home-destination-root-still-unresolved",
                "top_level_home_class": "runtime/",
                "child_home_class": "runtime/state/",
                "layout_family_root": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/",
                "destination_class": "queue-home",
                "destination_root_path": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/",
                "exact_child_path_candidate": "none",
                "artifact_shape_class": "none",
                "artifact_status_note": "exact filename, schema, snapshot shape, runtime-state discovery, and final artifact-shape choice remain deferred",
            },
        )

    def test_queue_home_json_file_candidate_is_admitted(self) -> None:
        payload = classify_runtime_state_artifact_shape_selection(
            _load_fixture("queue-home-json-file-artifact-shape-candidate.json"),
            root=ROOT,
        ).to_payload()
        self.assertEqual(payload["decision"], "admitted-queue-home-json-file-artifact-shape-candidate")
        self.assertEqual(payload["artifact_shape_class"], "json-file-candidate")
        self.assertEqual(
            payload["exact_child_path_candidate"],
            "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/live/draft-queue.json",
        )

    def test_queue_home_directory_candidate_is_admitted(self) -> None:
        payload = classify_runtime_state_artifact_shape_selection(
            _load_fixture("queue-home-directory-artifact-shape-candidate.json"),
            root=ROOT,
        ).to_payload()
        self.assertEqual(payload["decision"], "admitted-queue-home-directory-artifact-shape-candidate")
        self.assertEqual(payload["artifact_shape_class"], "directory-candidate")
        self.assertEqual(
            payload["exact_child_path_candidate"],
            "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/live/",
        )

    def test_registry_home_destination_root_candidate_stays_unresolved(self) -> None:
        result = classify_runtime_state_artifact_shape_selection(
            _load_fixture("registry-home-destination-root-candidate.json"),
            root=ROOT,
        )
        self.assertEqual(
            result.to_payload(),
            {
                "normalized_candidate_path": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/registry-home/",
                "decision": "registry-home-destination-root-still-unresolved",
                "top_level_home_class": "runtime/",
                "child_home_class": "runtime/state/",
                "layout_family_root": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/",
                "destination_class": "registry-home",
                "destination_root_path": "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/registry-home/",
                "exact_child_path_candidate": "none",
                "artifact_shape_class": "none",
                "artifact_status_note": "exact filename, schema, snapshot shape, runtime-state discovery, and final artifact-shape choice remain deferred",
            },
        )

    def test_registry_home_json_file_candidate_is_admitted(self) -> None:
        payload = classify_runtime_state_artifact_shape_selection(
            _load_fixture("registry-home-json-file-artifact-shape-candidate.json"),
            root=ROOT,
        ).to_payload()
        self.assertEqual(payload["decision"], "admitted-registry-home-json-file-artifact-shape-candidate")
        self.assertEqual(payload["artifact_shape_class"], "json-file-candidate")
        self.assertEqual(
            payload["exact_child_path_candidate"],
            "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/registry-home/draft/registry.json",
        )

    def test_registry_home_directory_candidate_is_admitted(self) -> None:
        payload = classify_runtime_state_artifact_shape_selection(
            _load_fixture("registry-home-directory-artifact-shape-candidate.json"),
            root=ROOT,
        ).to_payload()
        self.assertEqual(payload["decision"], "admitted-registry-home-directory-artifact-shape-candidate")
        self.assertEqual(payload["artifact_shape_class"], "directory-candidate")
        self.assertEqual(
            payload["exact_child_path_candidate"],
            "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/registry-home/draft/",
        )

    def test_unsupported_non_json_file_shape_fails_closed(self) -> None:
        payload = classify_runtime_state_artifact_shape_selection(
            _load_fixture("unsupported-exact-child-path-artifact-shape-candidate.json"),
            root=ROOT,
        ).to_payload()
        self.assertEqual(payload["decision"], "non-admitted-exact-child-path-artifact-shape")
        self.assertEqual(payload["artifact_shape_class"], "none")
        self.assertEqual(
            payload["exact_child_path_candidate"],
            "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/live/draft-queue.txt",
        )

    def test_neutral_family_root_candidate_fails_closed_without_destination(self) -> None:
        payload = classify_runtime_state_artifact_shape_selection(
            _load_fixture("neutral-family-root-candidate.json"),
            root=ROOT,
        ).to_payload()
        self.assertEqual(payload["decision"], "neutral-family-root-without-destination-class")
        self.assertEqual(payload["artifact_shape_class"], "none")

    def test_other_neutral_family_descendant_is_non_admitted(self) -> None:
        payload = classify_runtime_state_artifact_shape_selection(
            _load_fixture("other-neutral-family-descendant-candidate.json"),
            root=ROOT,
        ).to_payload()
        self.assertEqual(payload["decision"], "non-admitted-neutral-family-descendant")
        self.assertEqual(payload["destination_class"], "staging-bucket")
        self.assertEqual(payload["artifact_shape_class"], "none")

    def test_outside_neutral_family_root_candidate_is_rejected(self) -> None:
        payload = classify_runtime_state_artifact_shape_selection(
            _load_fixture("outside-neutral-family-root-candidate.json"),
            root=ROOT,
        ).to_payload()
        self.assertEqual(payload["decision"], "outside-admitted-neutral-family-root")
        self.assertEqual(payload["normalized_candidate_path"], "runtime/state/atlas/session-cache")
        self.assertEqual(payload["artifact_shape_class"], "none")

    def test_multi_candidate_or_discovered_input_is_rejected(self) -> None:
        for fixture_name in ("multi-candidate-payload.json", "discovered-input-mode.json"):
            with self.subTest(fixture_name=fixture_name):
                with self.assertRaises(RuntimeStateArtifactShapeSelectionError) as context:
                    classify_runtime_state_artifact_shape_selection(
                        _load_fixture(fixture_name),
                        root=ROOT,
                    )
                self.assertIn("unsupported input field", str(context.exception))

    def test_queue_registry_or_execution_hint_payload_is_rejected(self) -> None:
        for fixture_name in ("queue-or-execution-hint-payload.json", "registry-hint-payload.json"):
            with self.subTest(fixture_name=fixture_name):
                with self.assertRaises(RuntimeStateArtifactShapeSelectionError) as context:
                    classify_runtime_state_artifact_shape_selection(
                        _load_fixture(fixture_name),
                        root=ROOT,
                    )
                self.assertIn("unsupported input field", str(context.exception))


if __name__ == "__main__":
    unittest.main()
