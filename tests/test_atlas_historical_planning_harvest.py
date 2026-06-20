from __future__ import annotations

import json
from pathlib import Path
import unittest

from ops._atlas import atlas_root
from ops.atlas.continuity import build_continuity_source_manifest, validate_continuity_source_manifest


class AtlasHistoricalPlanningHarvestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = atlas_root()

    def test_manifest_file_is_loaded_and_uses_live_owner_paths(self) -> None:
        manifest_path = self.root / "data" / "imports" / "knowledge" / "continuity" / "harvest-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(validate_continuity_source_manifest(manifest), [])

        built_manifest = build_continuity_source_manifest(root=self.root)
        self.assertEqual(built_manifest["manifest_id"], manifest["manifest_id"])

        items = {
            item["source_id"]: item
            for item in built_manifest["sources"]
            if isinstance(item, dict) and isinstance(item.get("source_id"), str)
        }

        self.assertEqual(
            items["playbook_roadmap_json"]["source_path"],
            "repos/fawxzzy-playbook/docs/roadmap/ROADMAP.json",
        )
        self.assertEqual(
            items["playbook_product_roadmap"]["source_path"],
            "repos/fawxzzy-playbook/docs/PLAYBOOK_PRODUCT_ROADMAP.md",
        )
        self.assertEqual(items["imports_verta_core_glob"]["status"], "indexed")
        self.assertFalse(items["imports_verta_core_glob"]["promotion_candidate"])
        self.assertFalse(items["root_continuity_backlog"]["promotion_candidate"])
        self.assertFalse(items["playbook_next_four_weeks"]["promotion_candidate"])
        self.assertFalse(items["imports_verta_core_sanitized_evaluation"]["promotion_candidate"])
        self.assertEqual(items["imports_verta_architecture_summary"]["status"], "superseded")
        self.assertEqual(
            items["imports_verta_architecture_summary"]["superseded_by"],
            ["promotion_verta_historical_scope_boundaries"],
        )
        self.assertEqual(items["imports_verta_core_run_next"]["status"], "superseded")
        self.assertEqual(
            items["imports_verta_core_run_next"]["superseded_by"],
            ["promotion_verta_historical_evidence_enrichment_loop"],
        )
        self.assertEqual(
            items["downloads_continuity_packet"]["source_path"],
            "Downloads/ATLAS-HISTORICAL-PLANNING-HARVEST-PACKET.md",
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

    def test_handoff_and_promotion_capture_provenance_and_trust_posture(self) -> None:
        handoff_path = (
            self.root
            / "runtime"
            / "receipts"
            / "handoffs"
            / "playbook-convergence-historical-planning-harvest-20260417t161500z.handoff.json"
        )
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))

        self.assertEqual(handoff["contract_version"], "atlas.continuity.handoff.v1")
        self.assertEqual(handoff["transcript_role"], "trace_only")
        self.assertIn("initiative-playbook-convergence-and-continuity", handoff["initiative_refs"])
        self.assertIn("knowledge", handoff["promotion_targets"])

        durable_facts = {
            item["id"]: item
            for item in handoff["durable_facts"]
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        self.assertIn("playbook-roadmap-truth-lives-under-docs-roadmap", durable_facts)
        self.assertIn("verta-imports-stay-trust-bounded", durable_facts)

        promotion_path = (
            self.root
            / "docs"
            / "knowledge"
            / "promotions"
            / "atlas--historical-planning-harvest-20260417.md"
        )
        promotion_text = promotion_path.read_text(encoding="utf-8")

        self.assertIn("repos/fawxzzy-playbook/docs/PLAYBOOK_PRODUCT_ROADMAP.md", promotion_text)
        self.assertIn("repos/fawxzzy-playbook/docs/roadmap/ROADMAP.json", promotion_text)
        self.assertIn("verta-core-sanitized", promotion_text)
        self.assertIn("Downloads/ATLAS-HISTORICAL-PLANNING-HARVEST-PACKET.md", promotion_text)


if __name__ == "__main__":
    unittest.main()
