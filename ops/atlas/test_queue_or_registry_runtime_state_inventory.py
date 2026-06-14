from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.queue_or_registry_runtime_state_inventory import (
    QueueOrRegistryRuntimeStateInventoryError,
    build_queue_or_registry_runtime_state_inventory,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class QueueOrRegistryRuntimeStateInventoryTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "stack.yaml").write_text("repo_registry: {}\n", encoding="utf-8")
        return root

    def test_absent_family_root_reports_unpopulated(self) -> None:
        root = self._temp_root()
        payload = build_queue_or_registry_runtime_state_inventory(root=root).to_payload()

        self.assertFalse(payload["family_root_exists"])
        self.assertEqual(payload["inventory_status"], "unpopulated-family-root")
        self.assertEqual(payload["family_entry_count"], 0)
        self.assertEqual(payload["json_candidate_refs"], [])

    def test_populated_queue_and_registry_homes_are_inventory_visible(self) -> None:
        root = self._temp_root()
        family_root = root / "runtime" / "state" / "ai-long-run-batch-orchestration" / "queue-or-registry"
        _write_json(family_root / "queue-home" / "pending.json", {"status": "pending"})
        _write_json(family_root / "registry-home" / "completed.json", {"status": "completed"})
        (family_root / "registry-home" / "archive").mkdir(parents=True, exist_ok=True)

        payload = build_queue_or_registry_runtime_state_inventory(root=root).to_payload()

        self.assertTrue(payload["family_root_exists"])
        self.assertTrue(payload["queue_home_exists"])
        self.assertTrue(payload["registry_home_exists"])
        self.assertEqual(payload["inventory_status"], "queue-and-registry-populated")
        self.assertEqual(payload["json_candidate_count"], 2)
        self.assertGreaterEqual(payload["directory_candidate_count"], 3)
        self.assertIn(
            "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/pending.json",
            payload["json_candidate_refs"],
        )
        self.assertIn(
            "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/registry-home",
            payload["directory_candidate_refs"],
        )

    def test_family_root_must_be_directory(self) -> None:
        root = self._temp_root()
        family_root = root / "runtime" / "state" / "ai-long-run-batch-orchestration" / "queue-or-registry"
        family_root.parent.mkdir(parents=True, exist_ok=True)
        family_root.write_text("not a directory", encoding="utf-8")

        with self.assertRaises(QueueOrRegistryRuntimeStateInventoryError) as context:
            build_queue_or_registry_runtime_state_inventory(root=root)
        self.assertIn("is not a directory", str(context.exception))


if __name__ == "__main__":
    unittest.main()
