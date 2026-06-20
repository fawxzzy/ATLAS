from __future__ import annotations

import json
import unittest

from ops._atlas import atlas_root
from ops.atlas.continuity import (
    build_continuity_source_manifest,
    validate_continuity_handoff,
)


class AtlasContinuityHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = atlas_root()

    def test_current_zero_queue_handoff_validates_and_stays_trace_only(self) -> None:
        handoff_path = (
            self.root
            / "runtime"
            / "receipts"
            / "handoffs"
            / "playbook-convergence-zero-queue-validation-20260619t160235z.handoff.json"
        )
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))

        self.assertEqual(validate_continuity_handoff(handoff), [])
        self.assertEqual(handoff["contract_version"], "atlas.continuity.handoff.v1")
        self.assertEqual(handoff["transcript_role"], "trace_only")
        self.assertIn("fitness", handoff["repo_refs"])
        self.assertIn("initiative-playbook-convergence-and-continuity", handoff["initiative_refs"])
        self.assertIn("initiative", handoff["promotion_targets"])
        self.assertIn("receipt", handoff["promotion_targets"])

    def test_manifest_registers_the_current_zero_queue_handoff(self) -> None:
        manifest = build_continuity_source_manifest(root=self.root)
        items = {
            item["source_id"]: item
            for item in manifest["sources"]
            if isinstance(item, dict) and isinstance(item.get("source_id"), str)
        }

        self.assertIn("handoff_zero_queue_validation", items)
        self.assertEqual(
            items["handoff_zero_queue_validation"]["source_path"],
            "runtime/receipts/handoffs/playbook-convergence-zero-queue-validation-20260619t160235z.handoff.json",
        )
        self.assertEqual(items["handoff_zero_queue_validation"]["source_type"], "handoff")
        self.assertEqual(items["handoff_zero_queue_validation"]["status"], "indexed")
        self.assertFalse(items["handoff_zero_queue_validation"]["promotion_candidate"])


if __name__ == "__main__":
    unittest.main()
