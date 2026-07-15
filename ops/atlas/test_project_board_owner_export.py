from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.project_board_owner_export import (
    ATLAS_GOVERNANCE_BACKLOG_OWNERS,
    ATLAS_OUTPUT_NAME,
    CORTEX_OUTPUT_NAME,
    MARKER_BOOK_REF,
    REGISTRY_REF,
    ProjectBoardOwnerExportError,
    build_project_board_owner_exports,
    write_project_board_owner_exports,
)


class ProjectBoardOwnerExportTests(unittest.TestCase):
    def test_current_registry_produces_the_frozen_atlas_and_cortex_shapes(self) -> None:
        exports = build_project_board_owner_exports()
        atlas = exports["atlas"]
        cortex = exports["cortex"]

        self.assertEqual(len(atlas["cards"]), 31)
        self.assertEqual(atlas["extensions"]["selection"]["marker_parent_count"], 6)
        self.assertEqual(atlas["extensions"]["selection"]["direct_lane_count"], 10)
        self.assertEqual(atlas["extensions"]["selection"]["governance_backlog_count"], 15)
        self.assertEqual(
            atlas["extensions"]["selection"]["backlog_owner_allowlist"],
            sorted(ATLAS_GOVERNANCE_BACKLOG_OWNERS),
        )
        self.assertEqual(len(cortex["cards"]), 2)
        atlas_card_ids = {card["record"]["card_id"] for card in atlas["cards"]}
        cortex_card_ids = {card["record"]["card_id"] for card in cortex["cards"]}
        self.assertFalse(atlas_card_ids & cortex_card_ids)
        self.assertEqual(
            {card["record"]["card_id"] for card in cortex["cards"]},
            {"lane-cortex-context-synthesis", "lane-cortex-boundary-decision"},
        )
        self.assertTrue(all(card["record"]["priority"] is None for card in [*atlas["cards"], *cortex["cards"]]))
        self.assertTrue(all(card["record"]["updated_at"].endswith("Z") for card in atlas["cards"]))

    def test_marker_parents_are_not_executable_and_children_keep_parent_identity(self) -> None:
        atlas = build_project_board_owner_exports()["atlas"]
        cards_by_id = {card["record"]["card_id"]: card for card in atlas["cards"]}
        marker_ids = {card["record"]["card_id"] for card in atlas["cards"] if card["record_kind"] == "marker"}
        self.assertEqual(len(marker_ids), 6)
        for card in atlas["cards"]:
            if card["record"]["card_id"] in marker_ids:
                self.assertIn(card["record"]["lifecycle"], {"planning", "completed"})
            parent_id = card["relationships"]["parent_card_id"]
            if parent_id is not None:
                self.assertIn(parent_id, cards_by_id)
                self.assertIn(cards_by_id[parent_id]["record"]["lifecycle"], {"planning", "completed"})

    def test_atlas_backlog_excludes_owner_repo_implementation_records(self) -> None:
        registry = json.loads((ROOT / REGISTRY_REF).read_text(encoding="utf-8"))
        atlas = build_project_board_owner_exports()["atlas"]
        selected_ids = {card["record"]["card_id"] for card in atlas["cards"]}
        backlog_by_id = {record["id"]: record for record in registry["backlog_candidates"]}
        selected_backlog = [backlog_by_id[record_id] for record_id in selected_ids if record_id in backlog_by_id]
        self.assertEqual(len(selected_backlog), 15)
        self.assertTrue(all(record["owner"] in ATLAS_GOVERNANCE_BACKLOG_OWNERS for record in selected_backlog))
        self.assertNotIn("lane-cortex-context-synthesis", selected_ids)
        self.assertNotIn("lane-cortex-boundary-decision", selected_ids)
        self.assertNotIn("lane-fitness-dependency-security", selected_ids)
        self.assertNotIn("lane-discordos-command-surface-convergence", selected_ids)
        self.assertNotIn("lane-stack-github-event-contracts", selected_ids)

    def test_line_endings_do_not_change_source_revision(self) -> None:
        baseline = build_project_board_owner_exports()["atlas"]["source_revision"]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            registry_path = root / "registry.json"
            marker_path = root / "markers.md"
            registry_path.write_text(
                (ROOT / REGISTRY_REF).read_text(encoding="utf-8").replace("\n", "\r\n"),
                encoding="utf-8",
                newline="",
            )
            marker_path.write_text(
                (ROOT / MARKER_BOOK_REF).read_text(encoding="utf-8").replace("\n", "\r\n"),
                encoding="utf-8",
                newline="",
            )
            candidate = build_project_board_owner_exports(
                registry_path=registry_path,
                marker_book_path=marker_path,
            )["atlas"]["source_revision"]
        self.assertEqual(candidate, baseline)

    def test_registry_book_status_conflict_fails_closed(self) -> None:
        registry = json.loads((ROOT / REGISTRY_REF).read_text(encoding="utf-8"))
        stale = copy.deepcopy(registry)
        github = next(record for record in stale["lanes"] if record["id"] == "lane-github-control-plane-integration")
        github["status"] = "candidate"
        github["percentage"] = None
        github.pop("completed_units", None)
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "registry.json"
            registry_path.write_text(json.dumps(stale), encoding="utf-8")
            with self.assertRaises(ProjectBoardOwnerExportError):
                build_project_board_owner_exports(registry_path=registry_path)

    def test_write_and_check_are_deterministic(self) -> None:
        exports = build_project_board_owner_exports()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            write_project_board_owner_exports(exports, output_root=output_root, check=False)
            write_project_board_owner_exports(exports, output_root=output_root, check=True)
            self.assertTrue((output_root / ATLAS_OUTPUT_NAME).exists())
            self.assertTrue((output_root / CORTEX_OUTPUT_NAME).exists())
            (output_root / ATLAS_OUTPUT_NAME).write_text("{}\n", encoding="utf-8")
            with self.assertRaises(ProjectBoardOwnerExportError):
                write_project_board_owner_exports(exports, output_root=output_root, check=True)


if __name__ == "__main__":
    unittest.main()
