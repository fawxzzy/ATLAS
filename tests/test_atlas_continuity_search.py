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
            "continuity_initiative_manifest_health",
            "continuity_open_marker_manifest_coverage",
            "continuity_open_marker_restart_index",
            "continuity_maintained_manifest_restart_index",
            "continuity_coverage",
        ):
            with self.subTest(slice_name=slice_name):
                self.assertIn(slice_name, slices)

        self.assertEqual(status["slices"]["continuity_coverage"]["pending_review_count"], 0)

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
        self.assertIn('"item_count": 0', payload["text"])
        self.assertIn('"items": []', payload["text"])
        queue_source_ids = {
            item["source_id"]
            for item in atlas_status(root=self.root)["slices"]["continuity_promotion_queue"]["items"]
            if isinstance(item, dict) and isinstance(item.get("source_id"), str)
        }
        self.assertNotIn("imports_verta_architecture_decision", queue_source_ids)
        self.assertNotIn("imports_verta_core_next_moves", queue_source_ids)
        self.assertNotIn("imports_verta_atlas_absorption_gate", queue_source_ids)
        self.assertNotIn("imports_verta_core_glob", queue_source_ids)
        self.assertNotIn("root_continuity_backlog", queue_source_ids)
        self.assertNotIn("playbook_next_four_weeks", queue_source_ids)
        self.assertNotIn("imports_verta_core_sanitized_evaluation", queue_source_ids)
        self.assertNotIn("downloads_continuity_packet", queue_source_ids)
        self.assertNotIn("downloads_continuity_prompt", queue_source_ids)
        self.assertNotIn("downloads_fitness_adoption_packet", queue_source_ids)
        self.assertNotIn("downloads_fitness_adoption_prompt", queue_source_ids)

        coverage_results = search("open marker manifest coverage", root=self.root, limit=20)
        coverage_ids = {
            item["id"]
            for item in coverage_results["results"]
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        self.assertIn("slice:continuity_open_marker_manifest_coverage", coverage_ids)

        coverage_payload = fetch_status_slice("continuity_open_marker_manifest_coverage", root=self.root)
        self.assertEqual(
            coverage_payload["metadata"]["slice_name"], "continuity_open_marker_manifest_coverage"
        )
        self.assertIn("manifest_backed_count", coverage_payload["text"])

        restart_results = search("open marker restart index", root=self.root, limit=20)
        restart_ids = {
            item["id"]
            for item in restart_results["results"]
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        self.assertIn("slice:continuity_open_marker_restart_index", restart_ids)

        restart_payload = fetch_status_slice("continuity_open_marker_restart_index", root=self.root)
        self.assertEqual(
            restart_payload["metadata"]["slice_name"], "continuity_open_marker_restart_index"
        )
        self.assertIn("restart_ready_count", restart_payload["text"])

        maintained_results = search("maintained manifest restart index", root=self.root, limit=20)
        maintained_ids = {
            item["id"]
            for item in maintained_results["results"]
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        self.assertIn("slice:continuity_maintained_manifest_restart_index", maintained_ids)

        maintained_payload = fetch_status_slice("continuity_maintained_manifest_restart_index", root=self.root)
        self.assertEqual(
            maintained_payload["metadata"]["slice_name"], "continuity_maintained_manifest_restart_index"
        )
        self.assertIn("maintained_manifest_count", maintained_payload["text"])


if __name__ == "__main__":
    unittest.main()
