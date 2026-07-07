from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import proof_contract_candidate_contract as contract


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_sources(root: Path) -> None:
    _write(
        root / "docs" / "ops" / "contract.md",
        "Reusable workflow proof-contract with workflow_call typed inputs, workflow_dispatch manual proof inputs, artifact-backed proof, receipt-backed proof, least privilege.",
    )
    _write(root / "docs" / "PLAYBOOK_NOTES.md", "Rule: proof artifact and fallback path are explicit.")
    _write(root / "docs" / "architecture" / "ATLAS-CORTEX-PLAYBOOK-CODEX.md", "Cortex consumes explicit artifact refs without dispatch authority.")
    _write(root / "docs" / "standards" / "WORKER-ORCHESTRATION.md", "Workers resume from handoff artifacts.")


class ProofContractCandidateContractTests(unittest.TestCase):
    def test_artifact_candidate_renders_advisory_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_sources(root)
            report = contract.build_report(
                root=root,
                candidate_id="artifact-backed-proof-contract",
                source_refs=[
                    "docs/ops/contract.md",
                    "docs/PLAYBOOK_NOTES.md",
                    "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md",
                    "docs/standards/WORKER-ORCHESTRATION.md",
                ],
            )

        self.assertEqual(contract.STATUS_OK, report["status"])
        rendered = report["contract"]
        self.assertEqual("artifact_or_receipt_backed_proof_contract", rendered["trigger_style"])
        self.assertIn("artifact_digest", rendered["typed_inputs"])
        self.assertIn("green_ci_without_artifact_or_receipt", rendered["stop_conditions"])
        self.assertIn("no_workflow_dispatch", rendered["authority_denials"])
        self.assertNotIn("marker", report)
        self.assertNotIn("marker_movement", report)

    def test_manual_candidate_uses_secret_names_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_sources(root)
            report = contract.build_report(
                root=root,
                candidate_id="manual-protected-proof-contract",
                source_refs=[
                    "docs/ops/contract.md",
                    "docs/PLAYBOOK_NOTES.md",
                    "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md",
                    "docs/standards/WORKER-ORCHESTRATION.md",
                ],
            )

        rendered = report["contract"]
        self.assertEqual(contract.STATUS_OK, report["status"])
        self.assertEqual(["BROWSERSTACK_USERNAME", "BROWSERSTACK_ACCESS_KEY"], rendered["secret_names_only"])
        self.assertIn("no_secret_value_access", rendered["authority_denials"])

    def test_unsupported_candidate_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = contract.build_report(root=Path(temp_dir), candidate_id="unknown")

        self.assertEqual(contract.STATUS_BLOCKER, report["status"])
        self.assertFalse(report["safe_to_continue"])

    def test_missing_candidate_is_advisory_gap_not_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "docs" / "ops" / "contract.md", "no matching candidate evidence")
            report = contract.build_report(root=root, candidate_id="artifact-backed-proof-contract", source_refs=["docs/ops/contract.md"])

        self.assertEqual(contract.STATUS_ADVISORY_GAP, report["status"])
        self.assertIsNone(report["contract"])
        self.assertTrue(report["safe_to_continue"])

    def test_main_writes_only_tmp_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_sources(root)
            output_path = root / "tmp" / "proof-contract.json"
            with mock.patch.object(contract, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = contract.main(["--json", "--candidate-id", "artifact-backed-proof-contract", "--source", "docs/ops/contract.md", "--source", "docs/PLAYBOOK_NOTES.md", "--source", "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md", "--source", "docs/standards/WORKER-ORCHESTRATION.md", "--output", "tmp/proof-contract.json"])

            self.assertEqual(0, code)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(contract.SCHEMA_VERSION, payload["schema_version"])

    def test_main_rejects_non_tmp_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_sources(root)
            with mock.patch.object(contract, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = contract.main(["--json", "--candidate-id", "artifact-backed-proof-contract", "--source", "docs/ops/contract.md", "--output", "docs/ops/proof-contract.json"])

        self.assertEqual(2, code)

    def test_deterministic_top_level_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = contract.build_report(root=Path(temp_dir), candidate_id="artifact-backed-proof-contract")

        self.assertEqual(
            [
                "schema_version",
                "status",
                "candidate_id",
                "candidate_report_schema",
                "candidate_report_status",
                "contract",
                "playbook_rule_refs",
                "pattern_refs",
                "failure_mode_refs",
                "authority_risks",
                "safe_to_continue",
                "root",
                "branch",
                "head",
                "source_refs",
                "blockers",
                "warnings",
            ],
            list(report.keys()),
        )


if __name__ == "__main__":
    unittest.main()
