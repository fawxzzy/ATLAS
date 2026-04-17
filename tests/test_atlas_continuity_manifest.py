from __future__ import annotations

import unittest

from ops._atlas import atlas_root
from ops.atlas.continuity import build_continuity_source_manifest, validate_continuity_source_manifest


class AtlasContinuityManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = atlas_root()

    def test_manifest_validates_and_covers_grounded_lanes(self) -> None:
        manifest = build_continuity_source_manifest(root=self.root)
        self.assertEqual(validate_continuity_source_manifest(manifest), [])

        lanes = {
            item["lane"]
            for item in manifest["sources"]
            if isinstance(item, dict) and isinstance(item.get("lane"), str)
        }
        self.assertTrue({"root_docs_ops", "playbook_roadmap", "imports", "downloads"}.issubset(lanes))

    def test_imports_and_downloads_remain_pending_review(self) -> None:
        manifest = build_continuity_source_manifest(root=self.root)
        items = {
            item["source_id"]: item
            for item in manifest["sources"]
            if isinstance(item, dict) and isinstance(item.get("source_id"), str)
        }

        self.assertEqual(items["imports_verta_core_glob"]["status"], "pending_review")
        self.assertEqual(items["imports_verta_core_glob"]["content_class"], "raw_evidence")
        self.assertEqual(items["downloads_continuity_packet"]["status"], "pending_review")
        self.assertEqual(items["downloads_continuity_packet"]["content_class"], "residue")


if __name__ == "__main__":
    unittest.main()
