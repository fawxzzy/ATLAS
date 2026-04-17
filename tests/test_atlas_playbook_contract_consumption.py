from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from ops._atlas import atlas_root
from ops.atlas.playbook_contract import (
    build_playbook_adoption_report,
    inspect_playbook_contract_source,
    validate_playbook_adoption_report,
)


class AtlasPlaybookContractConsumptionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = atlas_root()

    def test_live_contract_source_loads_from_owner_repo(self) -> None:
        report = build_playbook_adoption_report(root=self.root)
        contract_source = report["contract_source"]

        self.assertEqual(contract_source["repo_id"], "playbook")
        self.assertEqual(contract_source["repo_identity"], "remote")
        self.assertEqual(contract_source["source_status"], "present")
        self.assertTrue(contract_source["contract_version"])
        self.assertEqual(validate_playbook_adoption_report(report), [])

    def test_local_only_repos_stay_visible_without_verification(self) -> None:
        report = build_playbook_adoption_report(root=self.root)
        rows = {
            row["repo_id"]: row
            for row in report["repos"]
            if isinstance(row, dict) and isinstance(row.get("repo_id"), str)
        }

        for repo_id in ("_stack", "atlas", "stream"):
            with self.subTest(repo_id=repo_id):
                self.assertEqual(rows[repo_id]["repo_identity"], "local_only")
                self.assertEqual(rows[repo_id]["verification_state"], "none")
                self.assertNotEqual(rows[repo_id]["adoption_status"], "verified")

    def test_repo_local_adoption_slices_project_as_adopted_without_verified_promotion(self) -> None:
        report = build_playbook_adoption_report(root=self.root)
        rows = {
            row["repo_id"]: row
            for row in report["repos"]
            if isinstance(row, dict) and isinstance(row.get("repo_id"), str)
        }

        for repo_id in ("fitness", "mazer"):
            with self.subTest(repo_id=repo_id):
                self.assertEqual(rows[repo_id]["adoption_status"], "adopted")
                self.assertEqual(rows[repo_id]["verification_state"], "targeted")
                self.assertEqual(rows[repo_id]["continuity_status"], "structured")
                self.assertNotEqual(rows[repo_id]["adoption_status"], "verified")
                self.assertTrue(
                    any(
                        ref.endswith(f"{repo_id}.playbook.adoption.evidence.v1.json")
                        for ref in rows[repo_id]["evidence_refs"]
                    )
                )

    def test_missing_export_is_reported_non_green(self) -> None:
        with TemporaryDirectory() as tempdir:
            base = Path(tempdir)
            result = inspect_playbook_contract_source(
                export_path=base / "missing.json",
                schema_path=base / "schema.json",
                doc_path=base / "contract.md",
                repo_id="playbook",
                repo_path="repos/fawxzzy-playbook",
                repo_identity="remote",
            )

        self.assertEqual(result["source_status"], "missing")
        self.assertEqual(result["validation_state"], "schema_invalid")

    def test_malformed_export_is_reported_non_green(self) -> None:
        with TemporaryDirectory() as tempdir:
            base = Path(tempdir)
            export_path = base / "example.json"
            schema_path = base / "schema.json"
            doc_path = base / "contract.md"
            export_path.write_text("{not json", encoding="utf-8")
            schema_path.write_text("{}", encoding="utf-8")
            doc_path.write_text("# Contract\n", encoding="utf-8")

            result = inspect_playbook_contract_source(
                export_path=export_path,
                schema_path=schema_path,
                doc_path=doc_path,
                repo_id="playbook",
                repo_path="repos/fawxzzy-playbook",
                repo_identity="remote",
            )

        self.assertEqual(result["source_status"], "malformed")
        self.assertEqual(result["validation_state"], "schema_invalid")


if __name__ == "__main__":
    unittest.main()
