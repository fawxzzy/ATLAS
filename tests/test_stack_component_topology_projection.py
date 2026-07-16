from __future__ import annotations

import subprocess
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from ops.stack.export_repo_inventory import (
    build_repo_inventory,
    render_repo_inventory_markdown,
)
from ops.stack.generate_lockfile import (
    apply_scoped_component_refresh,
    build_lock_payload,
    declared_root_coordinate,
    describe_lock_payload_drift,
    load_lockfile,
    render_lockfile_text,
    resolve_declared_root_path,
)


class StackComponentTopologyProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.root = Path(temp_dir.name)
        self.config = {
            "repo_registry": {
                "discordos": {
                    "path": "repos/DiscordOS",
                    "role": "board-and-discord-writer",
                    "playbook_adoption_status": "not-claimed",
                    "playbook_adoption_profile": "playbook_convergence_contract",
                    "playbook_adoption_version": "1.0.0",
                    "playbook_adoption_owner_head": "0123456789abcdef0123456789abcdef01234567",
                    "playbook_adoption_owner_ref": "main",
                    "status": "incubating",
                },
                "foundation": {
                    "path": "repos/foundation",
                    "role": "shared-contract-foundation",
                    "playbook_adoption_status": "not-claimed",
                    "status": "active",
                },
            },
            "stack_lock": {
                "path": "stack.lock.yaml",
                "include_repo_ids": ["discordos", "foundation"],
            },
        }
        for repo_path in ("repos/DiscordOS", "repos/foundation"):
            self._initialize_repo(self.root / repo_path)

    @staticmethod
    def _initialize_repo(repo_path: Path) -> None:
        repo_path.mkdir(parents=True)
        commands = (
            ("init", "--quiet", "--initial-branch=main"),
            ("config", "user.name", "ATLAS Test"),
            ("config", "user.email", "atlas-test@example.invalid"),
            ("commit", "--quiet", "--allow-empty", "-m", "fixture"),
        )
        for command in commands:
            subprocess.run(
                ["git", "-C", str(repo_path), *command],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

    def test_role_and_adoption_posture_project_deterministically(self) -> None:
        first_lock = build_lock_payload(config=self.config, root=self.root)
        second_lock = build_lock_payload(config=self.config, root=self.root)

        self.assertEqual(first_lock, second_lock)
        self.assertEqual(render_lockfile_text(first_lock), render_lockfile_text(second_lock))
        self.assertFalse(describe_lock_payload_drift(first_lock, second_lock)["has_drift"])

        lock_path = self.root / "stack.lock.yaml"
        lock_path.write_text(render_lockfile_text(first_lock), encoding="utf-8")
        self.assertEqual(first_lock, load_lockfile(lock_path))

        expected = {
            "discordos": "board-and-discord-writer",
            "foundation": "shared-contract-foundation",
        }
        for repo_id, role in expected.items():
            component = first_lock["components"][repo_id]
            self.assertEqual(role, component["role"])
            self.assertEqual("not-claimed", component["playbook_adoption_status"])
            self.assertEqual(self.config["repo_registry"][repo_id]["path"], component["path"])

        changed_lock = deepcopy(first_lock)
        changed_lock["components"]["discordos"]["playbook_adoption_status"] = "adopted"
        drift = describe_lock_payload_drift(first_lock, changed_lock)
        self.assertEqual(
            ["playbook_adoption_status"],
            drift["components"]["discordos"]["fields"],
        )

        first_inventory = build_repo_inventory(
            root=self.root,
            config=self.config,
            lock_payload=first_lock,
        )
        second_inventory = build_repo_inventory(
            root=self.root,
            config=self.config,
            lock_payload=second_lock,
        )
        self.assertEqual(first_inventory, second_inventory)

        inventory_by_id = {item["logical_id"]: item for item in first_inventory["repos"]}
        for repo_id, role in expected.items():
            self.assertEqual(role, inventory_by_id[repo_id]["role"])
            self.assertEqual(self.config["repo_registry"][repo_id]["path"], inventory_by_id[repo_id]["local_path"])
            self.assertEqual(
                "not-claimed",
                inventory_by_id[repo_id]["playbook_adoption_status"],
            )

        self.assertEqual(
            {
                "playbook_adoption_status": "not-claimed",
                "playbook_adoption_profile": "playbook_convergence_contract",
                "playbook_adoption_version": "1.0.0",
                "playbook_adoption_owner_head": "0123456789abcdef0123456789abcdef01234567",
                "playbook_adoption_owner_ref": "main",
            },
            {
                key: inventory_by_id["discordos"][key]
                for key in (
                    "playbook_adoption_status",
                    "playbook_adoption_profile",
                    "playbook_adoption_version",
                    "playbook_adoption_owner_head",
                    "playbook_adoption_owner_ref",
                )
            },
        )
        for key in (
            "playbook_adoption_profile",
            "playbook_adoption_version",
            "playbook_adoption_owner_head",
            "playbook_adoption_owner_ref",
        ):
            self.assertEqual("", inventory_by_id["foundation"][key])

        first_markdown = render_repo_inventory_markdown(first_inventory)
        second_markdown = render_repo_inventory_markdown(second_inventory)
        self.assertEqual(first_markdown, second_markdown)
        self.assertIn("| Role | Playbook adoption status |", first_markdown)
        self.assertIn("board-and-discord-writer | not-claimed", first_markdown)
        self.assertIn("shared-contract-foundation | not-claimed", first_markdown)

    def test_declared_coordinates_reject_parent_and_absolute_escape(self) -> None:
        for raw_path in ("../outside-repo", str(self.root.parent / "outside-repo")):
            with self.subTest(raw_path=raw_path):
                broken = deepcopy(self.config)
                broken["repo_registry"]["foundation"]["path"] = raw_path
                with self.assertRaisesRegex(ValueError, "root-relative|parent traversal"):
                    build_lock_payload(config=broken, root=self.root)

        broken = deepcopy(self.config)
        broken["stack_lock"]["excluded_surfaces"] = {
            "outside_archive": {
                "path": "../outside.zip",
                "trust_class": "untrusted",
                "release_eligible": False,
                "reason": "invalid fixture",
            }
        }
        with self.assertRaisesRegex(ValueError, "parent traversal"):
            build_lock_payload(config=broken, root=self.root)

    def test_lexical_lookalike_remains_a_distinct_in_root_coordinate(self) -> None:
        self.assertEqual(
            "repos/foundation-archive",
            declared_root_coordinate("repos/foundation-archive", root=self.root),
        )
        self.assertNotEqual(
            declared_root_coordinate("repos/foundation", root=self.root),
            declared_root_coordinate("repos/foundation-archive", root=self.root),
        )

    def test_in_root_presentation_allows_junction_backed_resolution(self) -> None:
        external_dir = tempfile.TemporaryDirectory()
        self.addCleanup(external_dir.cleanup)
        external = Path(external_dir.name).resolve()

        with patch("ops.stack.generate_lockfile.resolve_atlas_path", return_value=external):
            coordinate, resolved = resolve_declared_root_path(
                "repos/junction-backed",
                root=self.root,
                label="fixture.path",
            )

        self.assertEqual("repos/junction-backed", coordinate)
        self.assertEqual(external, resolved)

    def test_scoped_refresh_preserves_unselected_component_pins_deterministically(self) -> None:
        baseline = build_lock_payload(config=self.config, root=self.root)
        for repo_path in ("repos/DiscordOS", "repos/foundation"):
            subprocess.run(
                ["git", "-C", str(self.root / repo_path), "commit", "--quiet", "--allow-empty", "-m", "advance"],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        live = build_lock_payload(config=self.config, root=self.root)

        scoped = apply_scoped_component_refresh(
            live,
            baseline_payload=baseline,
            refresh_repo_ids={"foundation"},
            baseline_ref="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )
        repeated = apply_scoped_component_refresh(
            live,
            baseline_payload=scoped,
            refresh_repo_ids={"foundation"},
            baseline_ref="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )

        self.assertEqual(baseline["components"]["discordos"]["commit"], scoped["components"]["discordos"]["commit"])
        self.assertEqual(live["components"]["foundation"]["commit"], scoped["components"]["foundation"]["commit"])
        self.assertEqual(
            {
                "mode": "scoped",
                "baseline_ref": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "repo_ids": {"foundation": True},
            },
            scoped["refresh_scope"],
        )
        self.assertEqual(scoped, repeated)


if __name__ == "__main__":
    unittest.main()
