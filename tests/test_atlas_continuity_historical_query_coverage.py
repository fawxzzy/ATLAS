from __future__ import annotations

import unittest

from ops._atlas import atlas_root
from ops.atlas.awareness import atlas_status, fetch_status_slice
from ops.atlas.continuity import build_historical_query_coverage, evaluate_historical_planning_query


class AtlasContinuityHistoricalQueryCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = atlas_root()

    def test_canonical_questions_have_grounded_results(self) -> None:
        coverage = build_historical_query_coverage(root=self.root)

        self.assertEqual(coverage["status"], "answered")
        self.assertEqual(coverage["item_count"], 6)
        self.assertGreaterEqual(coverage["answered_count"], 4)

        items = {
            item["question_id"]: item
            for item in coverage["items"]
            if isinstance(item, dict) and isinstance(item.get("question_id"), str)
        }

        for question_id in (
            "original_atlas_roadmap_shape",
            "pattern_engine_and_cross_repo_convergence",
            "playbook_specific_vs_atlas_wide",
        ):
            with self.subTest(question_id=question_id):
                self.assertEqual(items[question_id]["status"], "answered")
                self.assertGreater(items[question_id]["hit_count"], 0)
                self.assertIsNone(items[question_id]["gap_reason"])

    def test_reviewed_verta_notes_are_preferred_over_raw_imports(self) -> None:
        coverage = build_historical_query_coverage(root=self.root)
        items = {
            item["question_id"]: item
            for item in coverage["items"]
            if isinstance(item, dict) and isinstance(item.get("question_id"), str)
        }

        expected_top_sources = {
            "original_atlas_roadmap_shape": "promotion_verta_historical_roadmap_intent",
            "playbook_principles_into_atlas": "promotion_verta_historical_playbook_principles",
            "persistent_codex_chatgpt_continuity": "promotion_verta_historical_continuity_memory",
            "pattern_engine_and_cross_repo_convergence": "promotion_verta_historical_convergence_intent",
            "playbook_specific_vs_atlas_wide": "promotion_verta_historical_scope_boundaries",
        }

        for question_id, source_id in expected_top_sources.items():
            with self.subTest(question_id=question_id):
                top_hit = items[question_id]["hits"][0]
                self.assertEqual(top_hit["source_type"], "reviewed_promotion_note")
                self.assertEqual(top_hit["source_id"], source_id)

    def test_coverage_exposes_distinct_source_types(self) -> None:
        coverage = build_historical_query_coverage(root=self.root)
        source_type_counts = coverage["source_type_counts"]

        self.assertIn("reviewed_promotion_note", source_type_counts)
        self.assertIn("promotion_note", source_type_counts)
        self.assertIn("root_doc", source_type_counts)

        continuity_question = next(
            item
            for item in coverage["items"]
            if isinstance(item, dict) and item.get("question_id") == "persistent_codex_chatgpt_continuity"
        )
        hit_types = {
            hit["source_type"]
            for hit in continuity_question["hits"]
            if isinstance(hit, dict) and isinstance(hit.get("source_type"), str)
        }
        self.assertIn("root_doc", hit_types)
        self.assertIn("handoff", hit_types)

    def test_explicit_gap_is_returned_for_non_matching_query(self) -> None:
        result = evaluate_historical_planning_query(
            "crystalline orchard moonbase protocol",
            root=self.root,
        )

        self.assertEqual(result["status"], "missing")
        self.assertEqual(result["hit_count"], 0)
        self.assertEqual(result["hits"], [])
        self.assertEqual(
            result["gap_reason"],
            "No manifest-backed historical planning source matched the question terms.",
        )

    def test_awareness_slice_exposes_historical_query_coverage(self) -> None:
        status = atlas_status(root=self.root)
        self.assertIn("continuity_historical_query_coverage", status["slices"])

        payload = fetch_status_slice("continuity_historical_query_coverage", root=self.root)
        self.assertEqual(payload["metadata"]["slice_name"], "continuity_historical_query_coverage")
        self.assertIn("question_id", payload["text"])
        self.assertIn("source_type", payload["text"])


if __name__ == "__main__":
    unittest.main()
