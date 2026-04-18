from __future__ import annotations

import unittest

from ops._atlas import atlas_root
from ops.atlas.awareness import atlas_status, fetch_status_slice, search


class AtlasContinuitySearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = atlas_root()

    def test_status_exposes_continuity_slices(self) -> None:
        status = atlas_status(root=self.root)
        slices = status["slices"]

        for slice_name in (
            "continuity_source_inventory",
            "continuity_promotion_queue",
            "continuity_source_groups",
            "continuity_search_status",
            "continuity_historical_query_coverage",
            "continuity_coverage",
        ):
            with self.subTest(slice_name=slice_name):
                self.assertIn(slice_name, slices)

        self.assertGreater(status["slices"]["continuity_coverage"]["pending_review_count"], 0)

    def test_search_and_fetch_resolve_continuity_slices(self) -> None:
        results = search("continuity promotion queue", root=self.root, limit=20)
        result_ids = {
            item["id"]
            for item in results["results"]
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        self.assertIn("slice:continuity_promotion_queue", result_ids)

        payload = fetch_status_slice("continuity_promotion_queue", root=self.root)
        self.assertEqual(payload["metadata"]["slice_name"], "continuity_promotion_queue")
        self.assertIn("promotion_targets", payload["text"])


if __name__ == "__main__":
    unittest.main()
