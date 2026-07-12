from __future__ import annotations

import json
from collections import Counter
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

    def _live_report_and_rows(self) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
        report = build_playbook_adoption_report(root=self.root)
        rows = {row["repo_id"]: row for row in report["repos"] if isinstance(row, dict) and isinstance(row.get("repo_id"), str)}
        return report, rows

    def test_live_contract_source_loads_from_owner_repo(self) -> None:
        report, _ = self._live_report_and_rows()
        contract_source = report["contract_source"]

        self.assertEqual(contract_source["repo_id"], "playbook")
        self.assertEqual(contract_source["source_status"], "present")
        self.assertIn(contract_source["repo_identity"], {"remote", "local_only", "unknown"})
        self.assertTrue(contract_source["contract_version"])
        self.assertEqual(validate_playbook_adoption_report(report), [])

    def test_live_rows_follow_current_inventory_identity(self) -> None:
        report, rows = self._live_report_and_rows()
        inventory = json.loads((self.root / "docs/registry/STACK-REPO-INVENTORY.json").read_text(encoding="utf-8"))
        expected = {
            entry["logical_id"]: "remote" if str(entry.get("remote_url") or "").strip() else "local_only" if entry.get("exists") else "unknown"
            for entry in inventory["repos"]
            if isinstance(entry, dict) and isinstance(entry.get("logical_id"), str)
        }

        self.assertIn("stack", rows)
        self.assertNotIn("atlas", rows)
        for repo_id, identity in expected.items():
            with self.subTest(repo_id=repo_id):
                self.assertEqual(identity, rows[repo_id]["repo_identity"])
        self.assertEqual(validate_playbook_adoption_report(report), [])

    def test_fitness_remains_non_green_when_trusted_state_blocks_it(self) -> None:
        _, rows = self._live_report_and_rows()
        fitness = rows["fitness"]

        self.assertNotEqual(fitness["verification_status"], "verified")
        self.assertTrue(fitness["blocking_gaps"])
        self.assertNotEqual(fitness["adoption_status"], "verified")
        self.assertTrue(any(ref.endswith("fitness.playbook.adoption.evidence.v1.json") for ref in fitness["evidence_refs"]))

    def test_live_summary_reconciles_exactly_to_emitted_rows(self) -> None:
        report, rows = self._live_report_and_rows()
        summary = report["summary"]
        emitted = list(rows.values())
        identity_counts = Counter(row["repo_identity"] for row in emitted)
        verification_counts = Counter(row["verification_status"] for row in emitted)

        self.assertEqual(len(emitted), summary["repo_count"])
        self.assertEqual(identity_counts["remote"], summary["remote_count"])
        self.assertEqual(identity_counts["local_only"], summary["local_only_count"])
        self.assertEqual(verification_counts["verified"], summary["verified_count"])
        self.assertEqual(verification_counts["missing"], summary["verification_missing_count"])
        self.assertEqual(verification_counts["partial"], summary["verification_partial_count"])
        self.assertEqual(verification_counts["blocked"], summary["verification_blocked_count"])
        self.assertEqual(sum(row["adoption_status"] == "adopted" and row["verification_status"] != "verified" for row in emitted), summary["adopted_count"])

    def test_missing_export_is_reported_non_green(self) -> None:
        with TemporaryDirectory() as tempdir:
            base = Path(tempdir)
            result = inspect_playbook_contract_source(export_path=base / "missing.json", schema_path=base / "schema.json", doc_path=base / "contract.md", repo_id="playbook", repo_path="repos/fawxzzy-playbook", repo_identity="remote")

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
            result = inspect_playbook_contract_source(export_path=export_path, schema_path=schema_path, doc_path=doc_path, repo_id="playbook", repo_path="repos/fawxzzy-playbook", repo_identity="remote")

        self.assertEqual(result["source_status"], "malformed")
        self.assertEqual(result["validation_state"], "schema_invalid")


if __name__ == "__main__":
    unittest.main()
