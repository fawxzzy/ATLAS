from __future__ import annotations

import json
import unittest

from ops._atlas import atlas_root
from ops.atlas.awareness import atlas_status, fetch, search
from ops.stack.export_repo_inventory import build_repo_inventory


class StackRepoInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = atlas_root()

    def test_inventory_builder_is_deterministic(self) -> None:
        first = build_repo_inventory(root=self.root)
        second = build_repo_inventory(root=self.root)
        self.assertEqual(first, second)
        self.assertEqual(first["content_digest"], second["content_digest"])

    def test_core_repo_entries_are_present(self) -> None:
        inventory = build_repo_inventory(root=self.root)
        repo_ids = {
            item["logical_id"]
            for item in inventory["repos"]
            if isinstance(item, dict) and isinstance(item.get("logical_id"), str)
        }
        self.assertTrue({"stack", "_stack", "atlas", "playbook", "lifeline", "mazer"}.issubset(repo_ids))

    def test_awareness_search_and_fetch_resolve_repo_by_id_and_path(self) -> None:
        by_id = search("mazer", root=self.root, limit=20)
        repo_hits = [
            item
            for item in by_id["results"]
            if isinstance(item, dict) and item.get("id") == "repo:mazer"
        ]
        self.assertTrue(repo_hits)

        by_path = search("repos/fawxzzy-mazer", root=self.root, limit=20)
        path_hits = [
            item
            for item in by_path["results"]
            if isinstance(item, dict) and item.get("id") == "repo:mazer"
        ]
        self.assertTrue(path_hits)

        repo_payload = fetch("repo:mazer", root=self.root)
        path_payload = fetch("repo_path:repos/fawxzzy-mazer", root=self.root)
        repo_json = json.loads(repo_payload["text"])
        path_json = json.loads(path_payload["text"])

        self.assertEqual(repo_payload["metadata"]["source_kind"], "repo_inventory")
        self.assertEqual(repo_json["logical_id"], "mazer")
        self.assertEqual(repo_json["local_path"], "repos/fawxzzy-mazer")
        self.assertEqual(path_json["logical_id"], "mazer")
        self.assertIn(
            "initiative:initiative-mazer-d2-learning-scorer",
            repo_json["related_initiative_refs"],
        )

    def test_status_exposes_repo_inventory_summary(self) -> None:
        status = atlas_status(root=self.root)
        repo_inventory = status["repo_inventory"]
        self.assertIn("repo_ids", repo_inventory)
        self.assertIn("mazer", repo_inventory["repo_ids"])
        self.assertGreaterEqual(repo_inventory["item_count"], 1)


if __name__ == "__main__":
    unittest.main()
