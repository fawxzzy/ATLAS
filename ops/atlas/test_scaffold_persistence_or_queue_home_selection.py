from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.scaffold_persistence_or_queue_home_selection import (
    ScaffoldPersistenceOrQueueHomeSelectionError,
    classify_scaffold_persistence_or_queue_home_selection,
)

FIXTURE_ROOT = (
    ROOT
    / "data"
    / "fixtures"
    / "ai-long-run-batch-orchestration"
    / "scaffold-persistence-or-queue-home-selection"
)


def _load_fixture(name: str) -> object:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class ScaffoldPersistenceOrQueueHomeSelectionTests(unittest.TestCase):
    def test_runtime_root_candidate_is_admitted(self) -> None:
        result = classify_scaffold_persistence_or_queue_home_selection(_load_fixture("runtime-root-candidate.json"), root=ROOT)
        payload = result.to_payload()
        self.assertEqual(
            payload,
            {
                "normalized_candidate_path": "runtime/",
                "decision": "admitted-runtime-home-candidate",
                "home_class": "runtime/",
                "layout_status_note": "exact runtime subpath, filename, schema, and persistence layout remain deferred",
            },
        )

    def test_runtime_descendant_candidate_is_admitted(self) -> None:
        result = classify_scaffold_persistence_or_queue_home_selection(
            _load_fixture("runtime-descendant-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "admitted-runtime-home-candidate")
        self.assertEqual(
            payload["normalized_candidate_path"],
            "runtime/ai-long-run-batch-orchestration/storage-home-candidate",
        )
        self.assertEqual(payload["home_class"], "runtime/")

    def test_repo_root_candidate_is_forbidden(self) -> None:
        result = classify_scaffold_persistence_or_queue_home_selection(_load_fixture("repo-root-candidate.json"), root=ROOT)
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "forbidden-home-class")
        self.assertEqual(payload["home_class"], "repos/")

    def test_fixture_or_import_candidate_is_forbidden(self) -> None:
        result = classify_scaffold_persistence_or_queue_home_selection(
            _load_fixture("fixture-or-import-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "forbidden-home-class")
        self.assertEqual(payload["home_class"], "data/")

    def test_scratch_or_package_candidate_is_forbidden(self) -> None:
        result = classify_scaffold_persistence_or_queue_home_selection(
            _load_fixture("scratch-or-package-candidate.json"),
            root=ROOT,
        )
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "forbidden-home-class")
        self.assertEqual(payload["home_class"], "tmp/")

    def test_secret_candidate_is_forbidden(self) -> None:
        result = classify_scaffold_persistence_or_queue_home_selection(_load_fixture("secret-candidate.json"), root=ROOT)
        payload = result.to_payload()
        self.assertEqual(payload["decision"], "forbidden-home-class")
        self.assertEqual(payload["home_class"], "secrets/")

    def test_multi_candidate_payload_is_rejected(self) -> None:
        with self.assertRaises(ScaffoldPersistenceOrQueueHomeSelectionError) as context:
            classify_scaffold_persistence_or_queue_home_selection(_load_fixture("multi-candidate-payload.json"), root=ROOT)
        self.assertIn("unsupported input field", str(context.exception))

    def test_queue_or_execution_hint_payload_is_rejected(self) -> None:
        with self.assertRaises(ScaffoldPersistenceOrQueueHomeSelectionError) as context:
            classify_scaffold_persistence_or_queue_home_selection(
                _load_fixture("queue-or-execution-hint-payload.json"),
                root=ROOT,
            )
        self.assertIn("unsupported input field", str(context.exception))


if __name__ == "__main__":
    unittest.main()
