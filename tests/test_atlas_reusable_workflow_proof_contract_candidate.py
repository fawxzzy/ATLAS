from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import reusable_workflow_proof_contract_candidate as candidate


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_contract_sources(root: Path) -> None:
    _write(
        root / "docs" / "ops" / "contract.md",
        "Reusable workflow proof-contract with workflow_call typed inputs, workflow_dispatch manual proof inputs, artifact-backed proof, receipt-backed proof, least privilege.",
    )
    _write(root / "docs" / "PLAYBOOK_NOTES.md", "Rule: do not promote repeated workflow until trigger inputs proof artifact and fallback path are explicit.")
    _write(root / "docs" / "architecture" / "ATLAS-CORTEX-PLAYBOOK-CODEX.md", "Cortex consumes explicit artifact refs without dispatch or execution authority.")
    _write(root / "docs" / "standards" / "WORKER-ORCHESTRATION.md", "Workers resume from handoff artifacts.")


class ReusableWorkflowProofContractCandidateTests(unittest.TestCase):
    def test_explicit_source_classifies_all_candidate_families(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_contract_sources(root)
            report = candidate.build_report(root=root, source_refs=["docs/ops/contract.md", "docs/PLAYBOOK_NOTES.md", "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md", "docs/standards/WORKER-ORCHESTRATION.md"])

        self.assertEqual(candidate.STATUS_OK, report["status"])
        self.assertEqual(3, report["candidate_count"])
        self.assertEqual("reusable_workflow_style_candidate", report["workflow_contract_candidates"][0]["classification"])
        self.assertEqual("workflow_dispatch_style_manual_proof_candidate", report["manual_dispatch_candidates"][0]["classification"])
        self.assertEqual("artifact_backed_proof_candidate", report["artifact_proof_candidates"][0]["classification"])
        self.assertTrue(report["safe_to_continue"])
        self.assertNotIn("marker", report)
        self.assertNotIn("marker_movement", report)

    def test_rejects_owner_hidden_secret_deploy_and_workflow_sources(self) -> None:
        blocked_refs = [
            "repos/fitness/docs/ops/receipt.md",
            ".codex/transcripts/session.json",
            "secrets/token.txt",
            ".env",
            "deploy/output.json",
            ".github/workflows/proof.yml",
            "archive/old.md",
            ".vercel/project.json",
            ".playwright-mcp/state.json",
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for ref in blocked_refs:
                _write(root / ref, "{}")
            for ref in blocked_refs:
                report = candidate.build_report(root=root, source_refs=[ref])
                self.assertEqual(candidate.STATUS_BLOCKER, report["status"], ref)
                self.assertFalse(report["safe_to_continue"], ref)

    def test_rejects_absolute_and_parent_traversal_source_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            absolute = candidate.build_report(root=root, source_refs=[str(root / "docs" / "ops" / "receipt.md")])
            parent = candidate.build_report(root=root, source_refs=["../docs/ops/receipt.md"])

        self.assertEqual(candidate.STATUS_BLOCKER, absolute["status"])
        self.assertEqual(candidate.STATUS_BLOCKER, parent["status"])

    def test_main_writes_output_only_for_explicit_tmp_json_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_contract_sources(root)
            output_path = root / "tmp" / "reusable.json"
            with mock.patch.object(candidate, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = candidate.main(["--json", "--source", "docs/ops/contract.md", "--source", "docs/PLAYBOOK_NOTES.md", "--source", "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md", "--source", "docs/standards/WORKER-ORCHESTRATION.md", "--output", "tmp/reusable.json"])

            self.assertEqual(0, code)
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(candidate.SCHEMA_VERSION, payload["schema_version"])

    def test_main_rejects_protected_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_contract_sources(root)
            with mock.patch.object(candidate, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = candidate.main(["--json", "--source", "docs/ops/contract.md", "--output", "docs/ops/out.json"])

        self.assertEqual(2, code)

    def test_deterministic_top_level_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = candidate.build_report(root=root, source_refs=[])

        self.assertEqual(
            [
                "schema_version",
                "status",
                "candidate_count",
                "workflow_contract_candidates",
                "manual_dispatch_candidates",
                "artifact_proof_candidates",
                "playbook_rule_refs",
                "pattern_refs",
                "failure_mode_refs",
                "doctrine_gaps",
                "authority_risks",
                "rejected_candidates",
                "proof_requirements",
                "safe_to_continue",
                "scope",
                "root",
                "branch",
                "head",
                "source_refs",
                "blockers",
                "warnings",
            ],
            list(report.keys()),
        )

    def test_strict_returns_nonzero_for_advisory_statuses(self) -> None:
        self.assertEqual(1, candidate.report_exit_code(status=candidate.STATUS_ADVISORY_CANDIDATE, strict=True))
        self.assertEqual(1, candidate.report_exit_code(status=candidate.STATUS_DOCTRINE_GAP, strict=True))


if __name__ == "__main__":
    unittest.main()
