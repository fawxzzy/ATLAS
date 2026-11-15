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
    RUNTIME_REGISTRY_REF,
    ProjectBoardOwnerExportError,
    build_project_board_owner_exports,
    write_project_board_owner_exports,
)


class ProjectBoardOwnerExportTests(unittest.TestCase):
    def test_current_registry_produces_the_frozen_atlas_and_cortex_shapes(self) -> None:
        exports = build_project_board_owner_exports()
        atlas = exports["atlas"]
        cortex = exports["cortex"]

        self.assertEqual(len(atlas["cards"]), 36)
        self.assertEqual(atlas["extensions"]["selection"]["marker_parent_count"], 6)
        self.assertEqual(atlas["extensions"]["selection"]["direct_lane_count"], 13)
        self.assertEqual(atlas["extensions"]["selection"]["governance_backlog_count"], 17)
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
        self.assertEqual(3, len(atlas["sources"]))
        self.assertEqual(atlas["runtime_readback"], cortex["runtime_readback"])
        self.assertEqual(
            [step["id"] for step in atlas["runtime_readback"]["activation_steps"]],
            atlas["runtime_readback"]["activation_sequence"],
        )
        self.assertTrue(all(step["status"] == "accepted" for step in atlas["runtime_readback"]["activation_steps"]))
        self.assertIsNone(atlas["runtime_readback"]["selector"])
        self.assertFalse(atlas["runtime_readback"]["discord_mutation_authorized"])

    def test_marker_parents_are_not_executable_and_children_keep_parent_identity(self) -> None:
        atlas = build_project_board_owner_exports()["atlas"]
        cards_by_id = {card["record"]["card_id"]: card for card in atlas["cards"]}
        marker_ids = {card["record"]["card_id"] for card in atlas["cards"] if card["record_kind"] == "marker"}
        self.assertEqual(len(marker_ids), 6)
        for card in atlas["cards"]:
            if card["record"]["card_id"] in marker_ids:
                self.assertIn(card["record"]["lifecycle"], {"planning", "completed", "archived"})
            parent_id = card["relationships"]["parent_card_id"]
            if parent_id is not None:
                self.assertIn(parent_id, cards_by_id)
                self.assertIn(cards_by_id[parent_id]["record"]["lifecycle"], {"planning", "completed", "archived"})

    def test_atlas_backlog_excludes_owner_repo_implementation_records(self) -> None:
        registry = json.loads((ROOT / REGISTRY_REF).read_text(encoding="utf-8"))
        atlas = build_project_board_owner_exports()["atlas"]
        selected_ids = {card["record"]["card_id"] for card in atlas["cards"]}
        backlog_by_id = {record["id"]: record for record in registry["backlog_candidates"]}
        selected_backlog = [backlog_by_id[record_id] for record_id in selected_ids if record_id in backlog_by_id]
        self.assertEqual(len(selected_backlog), 17)
        self.assertTrue(all(record["owner"] in ATLAS_GOVERNANCE_BACKLOG_OWNERS for record in selected_backlog))
        self.assertIn("lane-creation-os-product-definition-first-wedge", selected_ids)
        self.assertIn("lane-atlas-bootstrap-manifest-recovery-pointer", selected_ids)
        self.assertNotIn("lane-cortex-context-synthesis", selected_ids)
        self.assertNotIn("lane-cortex-boundary-decision", selected_ids)
        self.assertNotIn("lane-fitness-dependency-security", selected_ids)
        self.assertNotIn("lane-discordos-command-surface-convergence", selected_ids)
        self.assertNotIn("lane-stack-github-event-contracts", selected_ids)
        self.assertNotIn("lane-deterministic-builder-loop", selected_ids)

    def test_line_endings_do_not_change_source_revision(self) -> None:
        baseline = build_project_board_owner_exports()["atlas"]["source_revision"]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            registry_path = root / "registry.json"
            marker_path = root / "markers.md"
            runtime_path = root / "runtime.json"
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
            runtime_path.write_text(
                (ROOT / RUNTIME_REGISTRY_REF).read_text(encoding="utf-8").replace("\n", "\r\n"),
                encoding="utf-8",
                newline="",
            )
            candidate = build_project_board_owner_exports(
                registry_path=registry_path,
                marker_book_path=marker_path,
                runtime_registry_path=runtime_path,
            )["atlas"]["source_revision"]
        self.assertEqual(candidate, baseline)

    def test_runtime_registry_is_hashed_and_semantically_validated(self) -> None:
        runtime = json.loads((ROOT / RUNTIME_REGISTRY_REF).read_text(encoding="utf-8"))
        changed = copy.deepcopy(runtime)
        changed["current_unknowns"].append("Synthetic unresolved observation remains UNKNOWN.")
        invalid = copy.deepcopy(runtime)
        invalid["activation_steps"][6]["status"] = "pending"
        invalid["next_owner_side_activation_packet"] = invalid["activation_steps"][6]["packet"]

        with tempfile.TemporaryDirectory() as temp_dir:
            changed_path = Path(temp_dir) / "changed-runtime.json"
            invalid_path = Path(temp_dir) / "invalid-runtime.json"
            changed_path.write_text(json.dumps(changed), encoding="utf-8")
            invalid_path.write_text(json.dumps(invalid), encoding="utf-8")

            baseline = build_project_board_owner_exports()["atlas"]["source_revision"]
            changed_revision = build_project_board_owner_exports(
                runtime_registry_path=changed_path,
            )["atlas"]["source_revision"]
            self.assertNotEqual(baseline, changed_revision)

            invalid["activation_steps"][7]["status"] = "accepted"
            invalid_path.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaises(ProjectBoardOwnerExportError):
                build_project_board_owner_exports(runtime_registry_path=invalid_path)

    def test_runtime_readback_preserves_identity_and_status_boundaries(self) -> None:
        readback = build_project_board_owner_exports()["atlas"]["runtime_readback"]
        step_ids = [step["id"] for step in readback["activation_steps"]]
        marker_ids = [marker["id"] for marker in readback["marker_lanes"]]

        self.assertEqual(len(step_ids), len(set(step_ids)))
        self.assertEqual(len(marker_ids), len(set(marker_ids)))
        self.assertEqual([], readback["status_boundaries"]["pending"])
        self.assertEqual([], readback["status_boundaries"]["blocked"])
        self.assertEqual([], readback["status_boundaries"]["stale"])
        self.assertTrue(readback["status_boundaries"]["unknown"])

    def test_board_close_archives_every_card(self) -> None:
        atlas = build_project_board_owner_exports()["atlas"]
        self.assertEqual(36, len(atlas["cards"]))
        completed = 0
        archived_only = 0
        for card in atlas["cards"]:
            extensions = card["record"]["extensions"]
            self.assertEqual("archived", card["record"]["lifecycle"], card["record"]["card_id"])
            self.assertTrue(extensions["board_reason"])
            self.assertEqual([], card["content"]["blockers"])
            if extensions["board_disposition"] == "completed-archived":
                completed += 1
                self.assertTrue(extensions["completion_record"]["artifact"])
                self.assertTrue(extensions["completion_record"]["completed_on"])
            else:
                archived_only += 1
                self.assertEqual("archived", extensions["board_disposition"])
                self.assertIsNone(extensions["completion_record"])
                self.assertTrue(
                    extensions["board_reason"].startswith(("archived:", "superseded:", "deferred:", "folded into")),
                    card["record"]["card_id"],
                )
                self.assertNotIn("Completed ", " ".join(card["content"]["discoveries"]))
        self.assertEqual(26, completed)
        self.assertEqual(10, archived_only)

    def test_open_secret_alert_cards_are_archived_as_deferred_not_completed(self) -> None:
        atlas = build_project_board_owner_exports()["atlas"]
        cards = {card["record"]["card_id"]: card for card in atlas["cards"]}
        for cid in ("lane-fitness-critical-secret-containment", "lane-security-containment"):
            extensions = cards[cid]["record"]["extensions"]
            self.assertEqual("archived", extensions["board_disposition"])
            self.assertTrue(extensions["board_reason"].startswith("archived:"))
            self.assertIn("alert #1", extensions["board_reason"])
            self.assertIsNone(extensions["completion_record"])
        advisor = cards["lane-supabase-security-advisor-remediation"]["record"]["extensions"]
        self.assertIn("leaked-password protection is OFF", advisor["completion_record"]["artifact"])

    def test_board_projection_fails_closed_on_incomplete_dispositions(self) -> None:
        registry = json.loads((ROOT / REGISTRY_REF).read_text(encoding="utf-8"))
        broken_cases = {
            "archived-without-reason": ("lane-codex-execution-contracts", {"reason": None}),
            "archived-with-completion": ("lane-codex-execution-contracts", {"completion_record": {"completed_on": "2026-11-14", "artifact": "x"}}),
            "completed-without-artifact": ("lane-dependabot-visibility", {"completion_record": {"completed_on": "2026-11-14"}}),
            "archived-without-decided-on": ("lane-security-containment", {"decided_on": None}),
        }
        for name, (record_id, patch) in broken_cases.items():
            candidate = copy.deepcopy(registry)
            record = next(item for item in [*candidate["lanes"], *candidate["backlog_candidates"]] if item["id"] == record_id)
            for key, value in patch.items():
                if value is None:
                    record["board"].pop(key, None)
                else:
                    record["board"][key] = value
            with tempfile.TemporaryDirectory() as temp_dir:
                registry_path = Path(temp_dir) / "registry.json"
                registry_path.write_text(json.dumps(candidate), encoding="utf-8")
                with self.subTest(name), self.assertRaises(ProjectBoardOwnerExportError):
                    build_project_board_owner_exports(registry_path=registry_path)

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
