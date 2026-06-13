from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.runtime_state_execution_ready_transition_semantics import (
    RuntimeStateExecutionReadyTransitionSemanticsError,
    classify_runtime_state_execution_ready_transition_semantics,
)

FIXTURE_ROOT = (
    ROOT
    / "data"
    / "fixtures"
    / "ai-long-run-batch-orchestration"
    / "runtime-state-execution-ready-transition-semantics"
)


def _load_fixture(name: str) -> object:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class RuntimeStateExecutionReadyTransitionSemanticsTests(unittest.TestCase):
    def test_queue_home_destination_root_candidate_stays_unresolved(self) -> None:
        result = classify_runtime_state_execution_ready_transition_semantics(
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
                "discovery_mode_class": "none",
                "execution_transition_class": "none",
                "artifact_status_note": "live runtime-state read execution, queue mutation, registry mutation, execution-ready entry movement, and final execution-home routing remain deferred",
            },
        )

    def test_queue_home_direct_file_candidate_is_blocked(self) -> None:
        payload = classify_runtime_state_execution_ready_transition_semantics(
            _load_fixture("queue-home-direct-file-transition-candidate.json"),
            root=ROOT,
        ).to_payload()
        self.assertEqual(payload["decision"], "admitted-queue-home-live-direct-json-read-blocked-before-execution")
        self.assertEqual(payload["discovery_mode_class"], "direct-json-file-read-candidate")
        self.assertEqual(payload["execution_transition_class"], "blocked-pending-live-direct-json-read")

    def test_queue_home_directory_candidate_is_blocked(self) -> None:
        payload = classify_runtime_state_execution_ready_transition_semantics(
            _load_fixture("queue-home-directory-transition-candidate.json"),
            root=ROOT,
        ).to_payload()
        self.assertEqual(payload["decision"], "admitted-queue-home-live-directory-read-blocked-before-execution")
        self.assertEqual(payload["discovery_mode_class"], "directory-scoped-read-candidate")
        self.assertEqual(payload["execution_transition_class"], "blocked-pending-live-directory-read")

    def test_registry_home_destination_root_candidate_stays_unresolved(self) -> None:
        result = classify_runtime_state_execution_ready_transition_semantics(
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
                "discovery_mode_class": "none",
                "execution_transition_class": "none",
                "artifact_status_note": "live runtime-state read execution, queue mutation, registry mutation, execution-ready entry movement, and final execution-home routing remain deferred",
            },
        )

    def test_registry_home_direct_file_candidate_is_blocked(self) -> None:
        payload = classify_runtime_state_execution_ready_transition_semantics(
            _load_fixture("registry-home-direct-file-transition-candidate.json"),
            root=ROOT,
        ).to_payload()
        self.assertEqual(payload["decision"], "admitted-registry-home-live-direct-json-read-blocked-before-execution")
        self.assertEqual(payload["execution_transition_class"], "blocked-pending-live-direct-json-read")

    def test_registry_home_directory_candidate_is_blocked(self) -> None:
        payload = classify_runtime_state_execution_ready_transition_semantics(
            _load_fixture("registry-home-directory-transition-candidate.json"),
            root=ROOT,
        ).to_payload()
        self.assertEqual(payload["decision"], "admitted-registry-home-live-directory-read-blocked-before-execution")
        self.assertEqual(payload["execution_transition_class"], "blocked-pending-live-directory-read")

    def test_unsupported_candidate_fails_closed(self) -> None:
        payload = classify_runtime_state_execution_ready_transition_semantics(
            _load_fixture("unsupported-transition-candidate.json"),
            root=ROOT,
        ).to_payload()
        self.assertEqual(payload["decision"], "non-admitted-discovery-mode-execution-transition")
        self.assertEqual(payload["execution_transition_class"], "none")

    def test_neutral_family_root_candidate_fails_closed_without_destination(self) -> None:
        payload = classify_runtime_state_execution_ready_transition_semantics(
            _load_fixture("neutral-family-root-candidate.json"),
            root=ROOT,
        ).to_payload()
        self.assertEqual(payload["decision"], "neutral-family-root-without-destination-class")
        self.assertEqual(payload["execution_transition_class"], "none")

    def test_other_neutral_family_descendant_is_non_admitted(self) -> None:
        payload = classify_runtime_state_execution_ready_transition_semantics(
            _load_fixture("other-neutral-family-descendant-candidate.json"),
            root=ROOT,
        ).to_payload()
        self.assertEqual(payload["decision"], "non-admitted-neutral-family-descendant")
        self.assertEqual(payload["destination_class"], "staging-bucket")
        self.assertEqual(payload["execution_transition_class"], "none")

    def test_outside_neutral_family_root_candidate_is_rejected(self) -> None:
        payload = classify_runtime_state_execution_ready_transition_semantics(
            _load_fixture("outside-neutral-family-root-candidate.json"),
            root=ROOT,
        ).to_payload()
        self.assertEqual(payload["decision"], "outside-admitted-neutral-family-root")
        self.assertEqual(payload["normalized_candidate_path"], "runtime/state/atlas/session-cache")
        self.assertEqual(payload["execution_transition_class"], "none")

    def test_multi_candidate_or_discovered_input_is_rejected(self) -> None:
        for fixture_name in ("multi-candidate-payload.json", "discovered-input-mode.json"):
            with self.subTest(fixture_name=fixture_name):
                with self.assertRaises(RuntimeStateExecutionReadyTransitionSemanticsError) as context:
                    classify_runtime_state_execution_ready_transition_semantics(
                        _load_fixture(fixture_name),
                        root=ROOT,
                    )
                self.assertIn("unsupported input field", str(context.exception))

    def test_queue_registry_or_execution_hint_payload_is_rejected(self) -> None:
        for fixture_name in ("queue-or-execution-hint-payload.json", "registry-hint-payload.json"):
            with self.subTest(fixture_name=fixture_name):
                with self.assertRaises(RuntimeStateExecutionReadyTransitionSemanticsError) as context:
                    classify_runtime_state_execution_ready_transition_semantics(
                        _load_fixture(fixture_name),
                        root=ROOT,
                    )
                self.assertIn("unsupported input field", str(context.exception))


if __name__ == "__main__":
    unittest.main()
