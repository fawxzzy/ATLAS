from __future__ import annotations

import json
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops._atlas import atlas_root
from ops.atlas.awareness import atlas_status, fetch, search
from ops.stack import export_repo_inventory as repo_inventory_module
from ops.stack.export_repo_inventory import build_repo_inventory


class StackRepoInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = atlas_root()
        # Inventory projection tests do not bootstrap the unrelated Cortex runtime
        # or require every child repository to be installed in a fresh CI clone.
        for name, value in [("ensure_world_model", None), ("_load_snapshot", {}),
                            ("_load_attention", {}), ("render_status_payload", {})]:
            patcher = patch(f"ops.atlas.awareness.{name}", return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_cli_writes_the_exact_selected_manifest_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "stack.yaml").write_text(json.dumps({"repo_registry": {"stack": {"path": "."}}}))
            selected = root / "selected.yaml"
            selected.write_text(json.dumps({"repo_registry": {
                "stack": {"path": "."}, "selected": {"path": "repos/selected"},
            }}))
            json_output = root / "result.json"
            markdown_output = root / "result.md"
            output = io.StringIO()
            with patch.object(repo_inventory_module, "_initiative_index", return_value=({}, "fixture-digest")), \
                 patch.object(repo_inventory_module, "load_lockfile", return_value={"components": {}, "excluded_surfaces": {}}), \
                 patch.object(repo_inventory_module, "build_repo_inventory", wraps=build_repo_inventory) as build, \
                 redirect_stdout(output):
                result = repo_inventory_module.main([
                    "--stack-file", str(selected), "--json-output", str(json_output),
                    "--markdown-output", str(markdown_output),
                ])
            self.assertEqual(result, 0)
            persisted = json.loads(json_output.read_text())
            receipt = json.loads(output.getvalue())
            self.assertEqual({r["logical_id"] for r in persisted["repos"]}, {"stack", "selected"})
            self.assertEqual(receipt["repo_count"], persisted["repo_count"])
            self.assertEqual(receipt["content_digest"], persisted["content_digest"])
            self.assertEqual(persisted["stack_manifest_ref"], "selected.yaml")
            self.assertEqual(markdown_output.read_text(), repo_inventory_module.render_repo_inventory_markdown(persisted))
            self.assertEqual(build.call_count, 1)

    def test_explicit_empty_config_does_not_fall_back_to_default_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "stack.yaml").write_text(json.dumps({"repo_registry": {"unselected": {"path": "."}}}))
            with patch.object(repo_inventory_module, "_initiative_index", return_value=({}, "fixture-digest")):
                payload = build_repo_inventory(root=root, config={}, lock_payload={})
            self.assertEqual(payload["repos"], [])

    def test_cli_dry_run_does_not_write_and_builds_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected = root / "selected.yaml"
            selected.write_text(json.dumps({"repo_registry": {"stack": {"path": "."}}}))
            json_output, markdown_output = root / "result.json", root / "result.md"
            with patch.object(repo_inventory_module, "_initiative_index", return_value=({}, "fixture-digest")), \
                 patch.object(repo_inventory_module, "load_lockfile", return_value={"components": {}, "excluded_surfaces": {}}), \
                 patch.object(repo_inventory_module, "build_repo_inventory", wraps=build_repo_inventory) as build, \
                 redirect_stdout(io.StringIO()):
                self.assertEqual(repo_inventory_module.main([
                    "--stack-file", str(selected), "--json-output", str(json_output),
                    "--markdown-output", str(markdown_output), "--dry-run",
                ]), 0)
            self.assertFalse(json_output.exists())
            self.assertFalse(markdown_output.exists())
            self.assertEqual(build.call_count, 1)

    def test_excluded_presence_uses_current_paths_and_preserves_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "repos" / "present").mkdir(parents=True)
            (root / "retained.zip").write_text("fixture archive metadata only", encoding="utf-8")
            rows = {
                "absent": {"path": "repos/absent", "present": True, "trust_class": "quarantined", "release_eligible": False},
                "alias": {"path": "repos/absent", "present": True, "trust_class": "quarantined", "release_eligible": False},
                "present": {"path": "repos/present", "present": False, "trust_class": "adjacent", "release_eligible": False},
                "present_archive": {"path": "retained.zip", "present": False, "trust_class": "quarantined", "release_eligible": False},
                "absent_archive": {"path": "missing.zip", "present": True, "trust_class": "quarantined", "release_eligible": False},
            }
            with patch.object(repo_inventory_module, "_initiative_index", return_value=({}, "fixture-digest")):
                inventory = build_repo_inventory(
                    root=root, config={"repo_registry": {"stack": {"path": "."}}},
                    lock_payload={"components": {}, "excluded_surfaces": rows},
                )
            by_id = {row["surface_id"]: row for row in inventory["excluded_surfaces"]}
            self.assertEqual(set(rows), set(by_id))
            self.assertFalse(by_id["absent"]["present"])
            self.assertFalse(by_id["alias"]["present"])
            self.assertTrue(by_id["present"]["present"])
            self.assertTrue(by_id["present_archive"]["present"])
            self.assertFalse(by_id["absent_archive"]["present"])
            self.assertTrue(all(row["release_eligible"] is False for row in by_id.values()))

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
        self.assertTrue({"stack", "_stack", "playbook", "lifeline", "mazer"}.issubset(repo_ids))

    def test_trove_entry_projects_current_identity_without_moving_stable_coordinates(self) -> None:
        inventory = build_repo_inventory(root=self.root)
        trove = next(item for item in inventory["repos"] if item["logical_id"] == "trove")

        self.assertEqual("repos/trove", trove["local_path"])
        self.assertEqual("FawxzzyWeb", trove["operational_identity"]["display_name"])
        self.assertEqual("fawxzzyweb", trove["operational_identity"]["vercel_project"])
        self.assertEqual("https://fawxzzy.com", trove["operational_identity"]["public_origin"])

    def test_awareness_search_and_fetch_resolve_repo_by_id_and_path(self) -> None:
        by_id = search("mazer", root=self.root, limit=20)
        repo_hits = [
            item
            for item in by_id["results"]
            if isinstance(item, dict) and item.get("id") == "repo:mazer"
        ]
        self.assertTrue(repo_hits)

        by_path = search("repos/mazer", root=self.root, limit=20)
        path_hits = [
            item
            for item in by_path["results"]
            if isinstance(item, dict) and item.get("id") == "repo:mazer"
        ]
        self.assertTrue(path_hits)

        repo_payload = fetch("repo:mazer", root=self.root)
        path_payload = fetch("repo_path:repos/mazer", root=self.root)
        repo_json = json.loads(repo_payload["text"])
        path_json = json.loads(path_payload["text"])

        self.assertEqual(repo_payload["metadata"]["source_kind"], "repo_inventory")
        self.assertEqual(repo_json["logical_id"], "mazer")
        self.assertEqual(repo_json["local_path"], "repos/mazer")
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

    def test_stack_inventory_outputs_do_not_self_dirty_root(self) -> None:
        def fake_git_status_lines(repo_path):
            if repo_path.resolve() == self.root.resolve():
                return [
                    " M stack.lock.yaml",
                    " M docs/registry/STACK-REPO-INVENTORY.json",
                    " M docs/audits/STACK-REPO-INVENTORY.md",
                ]
            return []

        with patch("ops.stack.export_repo_inventory.git_status_lines", side_effect=fake_git_status_lines):
            inventory = build_repo_inventory(root=self.root)

        stack_entry = next(item for item in inventory["repos"] if item["logical_id"] == "stack")
        self.assertFalse(stack_entry["dirty"])
        self.assertEqual(inventory["dirty_repo_count"], 0)

    def test_non_inventory_root_changes_still_dirty_stack_entry(self) -> None:
        def fake_git_status_lines(repo_path):
            if repo_path.resolve() == self.root.resolve():
                return [
                    " M docs/registry/STACK-REPO-INVENTORY.json",
                    " M docs/audits/STACK-REPO-INVENTORY.md",
                    " M docs/ops/EXTRA-ROOT-CHANGE.md",
                ]
            return []

        with patch("ops.stack.export_repo_inventory.git_status_lines", side_effect=fake_git_status_lines):
            inventory = build_repo_inventory(root=self.root)

        stack_entry = next(item for item in inventory["repos"] if item["logical_id"] == "stack")
        self.assertTrue(stack_entry["dirty"])
        self.assertEqual(inventory["dirty_repo_count"], 1)

    def test_unmanaged_owner_lane_dirty_repos_are_advisory_not_root_blocking(self) -> None:
        def fake_live_state(repo_path, **kwargs):
            return {
                "exists": True, "is_git_root": True, "remote_url": None,
                "current_commit": "fixture-head", "current_ref_type": "branch",
                "current_ref": "fixture", "branch": "fixture",
                "dirty": repo_path.resolve() in {
                    (self.root / "repos" / "fawxzzy-fitness").resolve(),
                    (self.root / "repos" / "mazer").resolve(),
                },
            }

        with patch("ops.stack.export_repo_inventory._live_repo_state", side_effect=fake_live_state):
            inventory = build_repo_inventory(root=self.root)

        by_id = {item["logical_id"]: item for item in inventory["repos"]}
        for repo_id in ("fitness", "mazer"):
            self.assertTrue(by_id[repo_id]["dirty"])
            self.assertFalse(by_id[repo_id]["root_blocking"])
            self.assertFalse(by_id[repo_id]["dirty_blocks_root"])

        self.assertEqual(0, inventory["dirty_repo_count"])
        self.assertEqual(2, inventory["visible_dirty_repo_count"])
        self.assertEqual(2, inventory["advisory_dirty_repo_count"])


if __name__ == "__main__":
    unittest.main()
