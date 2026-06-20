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

    def test_resolved_raw_imports_are_superseded_and_residue_remains_pending_review(self) -> None:
        manifest = build_continuity_source_manifest(root=self.root)
        items = {
            item["source_id"]: item
            for item in manifest["sources"]
            if isinstance(item, dict) and isinstance(item.get("source_id"), str)
        }

        self.assertEqual(items["imports_verta_core_glob"]["status"], "indexed")
        self.assertEqual(items["imports_verta_core_glob"]["content_class"], "raw_evidence")
        self.assertFalse(items["imports_verta_core_glob"]["promotion_candidate"])
        self.assertFalse(items["root_continuity_backlog"]["promotion_candidate"])
        self.assertFalse(items["playbook_next_four_weeks"]["promotion_candidate"])
        self.assertFalse(items["imports_verta_core_sanitized_evaluation"]["promotion_candidate"])
        self.assertEqual(items["imports_verta_architecture_decision"]["status"], "superseded")
        self.assertEqual(
            items["imports_verta_architecture_decision"]["superseded_by"],
            ["promotion_verta_historical_playbook_principles"],
        )
        self.assertEqual(items["imports_verta_core_next_moves"]["status"], "superseded")
        self.assertEqual(
            items["imports_verta_core_next_moves"]["superseded_by"],
            ["promotion_verta_historical_benchmark_priority"],
        )
        self.assertEqual(items["imports_verta_atlas_absorption_gate"]["status"], "superseded")
        self.assertEqual(
            items["imports_verta_atlas_absorption_gate"]["superseded_by"],
            ["promotion_verta_historical_export_gate"],
        )
        self.assertEqual(items["downloads_continuity_packet"]["status"], "superseded")
        self.assertEqual(
            items["downloads_continuity_packet"]["superseded_by"],
            ["promotion_historical_harvest_note"],
        )
        self.assertEqual(items["downloads_continuity_prompt"]["status"], "superseded")
        self.assertEqual(
            items["downloads_continuity_prompt"]["superseded_by"],
            ["promotion_historical_harvest_note"],
        )
        self.assertEqual(items["downloads_fitness_adoption_packet"]["status"], "superseded")
        self.assertEqual(
            items["downloads_fitness_adoption_packet"]["superseded_by"],
            ["owner_fitness_playbook_truth_surfaces"],
        )
        self.assertEqual(items["downloads_fitness_adoption_prompt"]["status"], "superseded")
        self.assertEqual(
            items["downloads_fitness_adoption_prompt"]["superseded_by"],
            ["owner_fitness_playbook_truth_surfaces"],
        )
        self.assertEqual(items["imports_atlas_universal_interoperable_pdf"]["status"], "superseded")
        self.assertEqual(
            items["imports_atlas_universal_interoperable_pdf"]["superseded_by"],
            ["promotion_atlas_interoperable_stack"],
        )
        self.assertEqual(items["imports_verta_claude_operating_system"]["status"], "superseded")
        self.assertEqual(
            items["imports_verta_claude_operating_system"]["superseded_by"],
            ["promotion_verta_historical_continuity_memory"],
        )
        self.assertEqual(items["imports_verta_claude_operating_system"]["source_type"], "imported_doc")
        self.assertEqual(items["downloads_continuity_packet"]["content_class"], "residue")

    def test_reviewed_verta_promotion_notes_are_registered(self) -> None:
        manifest = build_continuity_source_manifest(root=self.root)
        items = {
            item["source_id"]: item
            for item in manifest["sources"]
            if isinstance(item, dict) and isinstance(item.get("source_id"), str)
        }

        for source_id in (
            "promotion_verta_historical_roadmap_intent",
            "promotion_verta_historical_playbook_principles",
            "promotion_verta_historical_convergence_intent",
            "promotion_verta_historical_scope_boundaries",
            "promotion_verta_historical_continuity_memory",
            "promotion_verta_historical_export_gate",
            "promotion_verta_historical_benchmark_priority",
            "promotion_verta_historical_evidence_enrichment_loop",
        ):
            with self.subTest(source_id=source_id):
                self.assertEqual(items[source_id]["status"], "promoted")
                self.assertEqual(items[source_id]["source_type"], "reviewed_promotion_note")
                self.assertEqual(items[source_id]["trust_posture"], "trusted")


if __name__ == "__main__":
    unittest.main()
