from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import supabase_backup_metadata_intake as intake


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _required_receipts(root: Path) -> None:
    audit = "\n".join(
        [
            "# Supabase Audit",
            "FawxzzyFitness lpswxoyfniocuhljgzbc",
            "DiscordOS nwexsktuuenfdegzrbut",
            "Mazer geknvnrmktchljnyddwp",
            "Nat1-Games dependency-only",
            "",
        ]
    )
    intake_contract = "\n".join(
        [
            "/v1/projects/{ref}/database/backups",
            intake.EXPORT_SCHEMA_VERSION,
            "tmp/atlas/supabase-backup-metadata",
        ]
    )
    for ref, text in (
        (intake.AUDIT_RECEIPT, audit),
        (intake.POSTURE_CONTRACT, "# posture contract\n"),
        (intake.INTAKE_CONTRACT, intake_contract),
        (intake.CURRENT_STATE, "# current state\n"),
        (intake.RECEIPT_INDEX, "# receipt index\n"),
        (intake.RESTART_GUIDE, "# restart guide\n"),
    ):
        _write(root / ref, text)
    inventory = {
        "schema_version": "atlas.stack.repo-inventory.v1",
        "repos": [{"logical_id": repo_id} for repo_id in intake.REQUIRED_INVENTORY_IDS],
    }
    _write(root / intake.STACK_REPO_INVENTORY, json.dumps(inventory, indent=2))


def _capture_wrapper(project_ref: str) -> dict[str, object]:
    return {
        "schema_version": intake.EXPORT_SCHEMA_VERSION,
        "captured_at": "2026-07-09T15:00:00Z",
        "project_ref": project_ref,
        "source": intake.EXPORT_SOURCE,
        "payload": {
            "region": "us-east-1",
            "walg_enabled": True,
            "pitr_enabled": False,
            "backups": [
                {"id": 4, "is_physical_backup": True, "status": "COMPLETED", "inserted_at": "2026-07-09T04:00:00Z"},
                {"id": 3, "is_physical_backup": True, "status": "COMPLETED", "inserted_at": "2026-07-08T04:00:00Z"},
            ],
            "physical_backup_data": {
                "earliest_physical_backup_date_unix": 1751937600,
                "latest_physical_backup_date_unix": 1752024000,
            },
        },
    }


class SupabaseBackupMetadataIntakeTests(unittest.TestCase):
    def test_valid_single_capture_returns_ok(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            capture_path = root / "tmp" / "atlas" / "supabase-backup-metadata" / "lpswxoyfniocuhljgzbc.json"
            _write(capture_path, json.dumps(_capture_wrapper("lpswxoyfniocuhljgzbc"), indent=2))

            report = intake.build_report(root=root, inputs=["tmp/atlas/supabase-backup-metadata/lpswxoyfniocuhljgzbc.json"])

        self.assertEqual(intake.STATUS_OK, report["status"])
        self.assertEqual(1, report["captured_project_count"])
        self.assertEqual("FawxzzyFitness", report["projects"][0]["project_name"])
        self.assertEqual(2, len(report["missing_projects"]))
        self.assertEqual(4, report["projects"][0]["latest_backup_id"])

    def test_unknown_project_ref_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            capture_path = root / "tmp" / "atlas" / "supabase-backup-metadata" / "unknown.json"
            _write(capture_path, json.dumps(_capture_wrapper("unknownref"), indent=2))

            report = intake.build_report(root=root, inputs=["tmp/atlas/supabase-backup-metadata/unknown.json"])

        self.assertEqual(intake.STATUS_BLOCKER, report["status"])
        self.assertEqual("unknown_project_ref", report["blockers"][0]["code"])

    def test_duplicate_project_capture_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            first = root / "tmp" / "atlas" / "supabase-backup-metadata" / "one.json"
            second = root / "tmp" / "atlas" / "supabase-backup-metadata" / "two.json"
            _write(first, json.dumps(_capture_wrapper("lpswxoyfniocuhljgzbc"), indent=2))
            _write(second, json.dumps(_capture_wrapper("lpswxoyfniocuhljgzbc"), indent=2))

            report = intake.build_report(
                root=root,
                inputs=[
                    "tmp/atlas/supabase-backup-metadata/one.json",
                    "tmp/atlas/supabase-backup-metadata/two.json",
                ],
            )

        self.assertEqual(intake.STATUS_BLOCKER, report["status"])
        self.assertEqual("duplicate_project_capture", report["blockers"][-1]["code"])

    def test_zero_inputs_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            report = intake.build_report(root=root, inputs=[])

        self.assertEqual(intake.STATUS_BLOCKER, report["status"])
        self.assertEqual("input_required", report["blockers"][-1]["code"])

    def test_main_writes_output_only_to_tmp_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            capture_path = root / "tmp" / "atlas" / "supabase-backup-metadata" / "discordos.json"
            output_path = root / "tmp" / "atlas" / "supabase-backup-metadata" / "out.json"
            _write(capture_path, json.dumps(_capture_wrapper("nwexsktuuenfdegzrbut"), indent=2))

            with mock.patch.object(intake, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = intake.main(
                        [
                            "--json",
                            "--input",
                            "tmp/atlas/supabase-backup-metadata/discordos.json",
                            "--output",
                            "tmp/atlas/supabase-backup-metadata/out.json",
                        ]
                    )

            self.assertEqual(0, code)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(intake.SCHEMA_VERSION, payload["schema_version"])

    def test_main_rejects_protected_input_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            protected_path = root / "docs" / "ops" / "bad.json"
            _write(protected_path, json.dumps(_capture_wrapper("geknvnrmktchljnyddwp"), indent=2))

            with mock.patch.object(intake, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = intake.main(["--json", "--input", "docs/ops/bad.json"])

        self.assertEqual(2, code)

    def test_empty_backup_list_warns_but_stays_ok(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            payload = _capture_wrapper("geknvnrmktchljnyddwp")
            assert isinstance(payload["payload"], dict)
            payload["payload"]["backups"] = []
            capture_path = root / "tmp" / "atlas" / "supabase-backup-metadata" / "mazer.json"
            _write(capture_path, json.dumps(payload, indent=2))

            report = intake.build_report(root=root, inputs=["tmp/atlas/supabase-backup-metadata/mazer.json"])

        self.assertEqual(intake.STATUS_OK, report["status"])
        self.assertEqual(0, report["projects"][0]["backup_count"])
        self.assertEqual("no_backup_rows", report["warnings"][0]["code"])

    def test_top_level_order_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            capture_path = root / "tmp" / "atlas" / "supabase-backup-metadata" / "fitness.json"
            _write(capture_path, json.dumps(_capture_wrapper("lpswxoyfniocuhljgzbc"), indent=2))

            report = intake.build_report(root=root, inputs=["tmp/atlas/supabase-backup-metadata/fitness.json"])

        self.assertEqual(
            [
                "schema_version",
                "status",
                "safe_to_use",
                "basis_receipts",
                "input_count",
                "captured_project_count",
                "projects",
                "missing_projects",
                "blockers",
                "warnings",
            ],
            list(report.keys()),
        )

    def test_utf8_bom_capture_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            capture_path = root / "tmp" / "atlas" / "supabase-backup-metadata" / "fitness-bom.json"
            capture_path.parent.mkdir(parents=True, exist_ok=True)
            capture_path.write_bytes(json.dumps(_capture_wrapper("lpswxoyfniocuhljgzbc"), indent=2).encode("utf-8-sig"))

            report = intake.build_report(root=root, inputs=["tmp/atlas/supabase-backup-metadata/fitness-bom.json"])

        self.assertEqual(intake.STATUS_OK, report["status"])
        self.assertEqual(1, report["captured_project_count"])


if __name__ == "__main__":
    unittest.main()
