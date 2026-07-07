from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import receipt_automation_candidate_extractor as extractor


def _write(path: Path, text: str = "# Receipt\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ReceiptAutomationCandidateExtractorTests(unittest.TestCase):
    def test_repeated_committed_receipts_admit_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "docs" / "ops" / "AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-PROJECTION-FRESHNESS-CHECKER-FIRST-IMPLEMENTATION-ADMISSION-2026-07-02.md")
            _write(root / "docs" / "ops" / "CORTEX-READINESS-AUTHORITY-SAFE-HANDOFF-CONSUMPTION-PROOF-FIRST-IMPLEMENTATION-ADMISSION-2026-07-06.md")

            report = extractor.build_report(root=root)

        self.assertEqual(extractor.STATUS_OK, report["status"])
        self.assertGreaterEqual(report["candidate_count"], 1)
        ids = {candidate["id"] for candidate in report["candidates"]}
        self.assertIn("first-implementation", ids)
        self.assertNotIn("marker", report)
        self.assertNotIn("marker_movement", report)

    def test_single_receipt_pattern_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "docs" / "ops" / "AI-REPETITION-TO-AUTOMATION-PIPELINE-UNIQUE-PROMPT-PACK-2026-07-07.md")

            report = extractor.build_report(root=root)

        self.assertEqual(extractor.STATUS_ADVISORY_GAP, report["status"])
        self.assertEqual(0, report["candidate_count"])
        self.assertEqual("fewer_than_two_committed_receipts", report["rejected_candidates"][0]["rejection_reason"])

    def test_source_ref_rejects_owner_repo_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "repos" / "fitness" / "docs" / "ops" / "receipt.md")

            report = extractor.build_report(root=root, source_refs=["repos/fitness/docs/ops/receipt.md"])

        self.assertEqual(extractor.STATUS_BLOCKER, report["status"])
        self.assertIn("protected_source_ref", {item["code"] for item in report["blockers"]})

    def test_source_ref_rejects_hidden_transcript_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / ".codex" / "transcripts" / "session.json")

            report = extractor.build_report(root=root, source_refs=[".codex/transcripts/session.json"])

        self.assertEqual(extractor.STATUS_BLOCKER, report["status"])
        self.assertIn("hidden_context_source_ref", {item["code"] for item in report["blockers"]})

    def test_source_ref_rejects_secret_deploy_archive_and_vercel_paths(self) -> None:
        blocked_refs = [
            "secrets/token.txt",
            "deploy/output.json",
            "archive/old.md",
            ".vercel/project.json",
            ".playwright-mcp/state.json",
            ".env",
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for ref in blocked_refs:
                _write(root / ref)

            for ref in blocked_refs:
                report = extractor.build_report(root=root, source_refs=[ref])
                self.assertEqual(extractor.STATUS_BLOCKER, report["status"], ref)

    def test_absolute_and_parent_traversal_source_refs_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            absolute_report = extractor.build_report(root=root, source_refs=[str(root / "docs" / "ops" / "x.md")])
            parent_report = extractor.build_report(root=root, source_refs=["../docs/ops/x.md"])

        self.assertEqual(extractor.STATUS_BLOCKER, absolute_report["status"])
        self.assertEqual(extractor.STATUS_BLOCKER, parent_report["status"])

    def test_deterministic_json_field_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = extractor.build_report(root=root)

        self.assertEqual(
            [
                "schema_version",
                "status",
                "root",
                "branch",
                "head",
                "source_refs",
                "candidate_count",
                "candidates",
                "rejected_candidates",
                "warnings",
                "blockers",
                "safe_to_use",
            ],
            list(report.keys()),
        )

    def test_main_writes_output_only_for_explicit_tmp_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_path = root / "tmp" / "candidates.json"
            with mock.patch.object(extractor, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = extractor.main(["--json", "--output", "tmp/candidates.json"])

            self.assertEqual(0, code)
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(extractor.SCHEMA_VERSION, payload["schema_version"])

    def test_main_rejects_protected_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(extractor, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = extractor.main(["--json", "--output", "docs/ops/out.json"])

        self.assertEqual(2, code)

    def test_strict_returns_nonzero_for_advisory_gap(self) -> None:
        self.assertEqual(1, extractor.report_exit_code(status=extractor.STATUS_ADVISORY_GAP, strict=True))


if __name__ == "__main__":
    unittest.main()
