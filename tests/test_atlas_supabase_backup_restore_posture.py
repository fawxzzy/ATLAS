from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import supabase_backup_restore_posture as posture


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_text_fixtures(root: Path) -> None:
    audit_text = "\n".join(
        [
            "# Supabase Audit",
            "FawxzzyFitness lpswxoyfniocuhljgzbc",
            "DiscordOS nwexsktuuenfdegzrbut",
            "Mazer geknvnrmktchljnyddwp",
            "Nat1-Games dependency-only",
            "",
        ]
    )
    contract_text = "\n".join(sorted(posture.REQUIRED_POSTURE_CLASSES))
    for ref, text in (
        (posture.AUDIT_RECEIPT, audit_text),
        (posture.CONTRACT_RECEIPT, contract_text),
        (posture.CURRENT_STATE, "# current state\n"),
        (posture.RECEIPT_INDEX, "# receipt index\n"),
        (posture.RESTART_GUIDE, "# restart guide\n"),
    ):
        _write(root / ref, text)


def _inventory_fixture(root: Path, logical_ids: list[str] | None = None) -> None:
    payload = {
        "schema_version": "atlas.stack.repo-inventory.v1",
        "repos": [{"logical_id": repo_id} for repo_id in (logical_ids or list(posture.REQUIRED_INVENTORY_IDS))],
    }
    _write(root / posture.STACK_REPO_INVENTORY, json.dumps(payload, indent=2))


class SupabaseBackupRestorePostureTests(unittest.TestCase):
    def test_live_root_input_returns_ok_or_blocker(self) -> None:
        report = posture.build_report(root=Path.cwd())

        self.assertEqual(posture.SCHEMA_VERSION, report["schema_version"])
        self.assertIn(report["status"], {posture.STATUS_OK, posture.STATUS_BLOCKER})

    def test_confirmed_project_posture_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_text_fixtures(root)
            _inventory_fixture(root)
            report = posture.build_report(root=root)

        self.assertEqual(posture.STATUS_OK, report["status"])
        self.assertEqual(3, report["project_count"])
        self.assertEqual(["FawxzzyFitness", "DiscordOS", "Mazer"], [item["project_name"] for item in report["projects"]])
        self.assertIn("daily_backup_covered", report["projects"][0]["posture_classes"])
        self.assertIn("daily_backup_unverified", report["projects"][0]["posture_classes"])
        self.assertEqual("restore_process_unverified", report["projects"][0]["restore_readiness"])
        self.assertEqual("daily_backup_unverified", report["projects"][0]["backup_inventory_status"])

    def test_nat1_games_remains_dependency_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_text_fixtures(root)
            _inventory_fixture(root)
            report = posture.build_report(root=root)

        self.assertEqual("Nat1-Games", report["dependency_only_surfaces"][0]["surface_name"])
        self.assertEqual(["no_project_identity"], report["dependency_only_surfaces"][0]["posture_classes"])

    def test_pitr_candidate_only_for_fitness_and_discordos(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_text_fixtures(root)
            _inventory_fixture(root)
            report = posture.build_report(root=root)

        flags = {item["project_name"]: item["pitr_candidate"] for item in report["projects"]}
        self.assertTrue(flags["FawxzzyFitness"])
        self.assertTrue(flags["DiscordOS"])
        self.assertFalse(flags["Mazer"])

    def test_missing_audit_project_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_text_fixtures(root)
            _inventory_fixture(root)
            _write(root / posture.AUDIT_RECEIPT, "FawxzzyFitness lpswxoyfniocuhljgzbc\nDiscordOS nwexsktuuenfdegzrbut\nNat1-Games dependency-only\n")
            report = posture.build_report(root=root)

        self.assertEqual(posture.STATUS_BLOCKER, report["status"])
        self.assertEqual("audit_project_missing", report["blockers"][0]["code"])

    def test_malformed_inventory_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_text_fixtures(root)
            _write(root / posture.STACK_REPO_INVENTORY, "{bad json")
            report = posture.build_report(root=root)

        self.assertEqual(posture.STATUS_BLOCKER, report["status"])
        self.assertEqual("stack_repo_inventory_missing", report["blockers"][0]["code"])

    def test_deterministic_top_level_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_text_fixtures(root)
            _inventory_fixture(root)
            report = posture.build_report(root=root)

        self.assertEqual(
            [
                "schema_version",
                "status",
                "safe_to_use",
                "basis_receipts",
                "project_count",
                "projects",
                "dependency_only_surfaces",
                "missing_evidence",
                "operator_decisions_required",
                "blockers",
                "warnings",
            ],
            list(report.keys()),
        )

    def test_main_writes_output_only_to_tmp_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_text_fixtures(root)
            _inventory_fixture(root)
            output = root / "tmp" / "atlas" / "supabase-backup.json"
            with mock.patch.object(posture, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = posture.main(["--json", "--output", "tmp/atlas/supabase-backup.json"])

            self.assertEqual(0, code)
            self.assertTrue(output.exists())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(posture.SCHEMA_VERSION, payload["schema_version"])

    def test_main_rejects_protected_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_text_fixtures(root)
            _inventory_fixture(root)
            with mock.patch.object(posture, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = posture.main(["--json", "--output", "docs/ops/out.json"])

        self.assertEqual(2, code)


if __name__ == "__main__":
    unittest.main()
