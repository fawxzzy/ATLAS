from __future__ import annotations

import io
import json
import tempfile
import unittest
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from ops.atlas import root_plus_owner_adoption_evidence as evidence


def _branch_state(
    *,
    parity_status: str = "clean",
    staged: list[str] | None = None,
    unstaged: list[str] | None = None,
    untracked: list[str] | None = None,
) -> OrderedDict[str, object]:
    return OrderedDict(
        [
            ("branch", "main"),
            ("head", "abc123"),
            ("parity", OrderedDict([("status", parity_status), ("behind", 0), ("ahead", 0)])),
            ("staged", staged or []),
            ("unstaged", unstaged or []),
            ("untracked", untracked or []),
        ]
    )


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_root(root: Path) -> None:
    for ref in evidence.CONTRACT_RECEIPTS:
        _write(root / ref, f"# {Path(ref).stem}\n")


def _owner_receipt(root: Path, name: str, owner: str, *, root_mutated: str = "false") -> None:
    _write(
        root / "docs" / "ops" / f"{name}.md",
        "\n".join(
            [
                "# Owner Evidence",
                "- Owner-lane adoption proof: true",
                f"- Owner repo: {owner}",
                "- AI work-session loop used: true",
                "- Separate owner-lane authorization: true",
                f"- Root mutated owner repo: {root_mutated}",
                "- Platform mutation from root: false",
                "- Protected-surface mutation: false",
                "- Secrets touched: false",
                "",
            ]
        ),
    )


def _owner_repo_receipt(repo_root: Path, name: str, owner: str) -> Path:
    path = repo_root / "docs" / "ops" / f"{name}.md"
    _write(
        path,
        "\n".join(
            [
                "# Owner Evidence",
                "- Owner-lane adoption proof: true",
                f"- Owner repo: {owner}",
                "- AI work-session loop used: true",
                "- Separate owner-lane authorization: true",
                "- Root mutated owner repo: false",
                "- Platform mutation from root: false",
                "- Protected-surface mutation: false",
                "- Secrets touched: false",
                "",
            ]
        ),
    )
    return path


class AtlasRootPlusOwnerAdoptionEvidenceTests(unittest.TestCase):
    def test_current_contract_without_owner_evidence_returns_needs_owner_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            with mock.patch.object(evidence, "collect_branch_state", return_value=_branch_state()):
                report = evidence.build_report(root=root)

        self.assertEqual(evidence.STATUS_NEEDS_EVIDENCE, report["status"])
        self.assertEqual(0, report["eligible_owner_count"])
        self.assertFalse(report["threshold_met"])
        self.assertTrue(report["safe_to_continue"])

    def test_two_separately_authorized_owner_receipts_return_ok(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            _owner_receipt(root, "fitness-proof", "fitness")
            _owner_receipt(root, "mazer-proof", "mazer")
            with mock.patch.object(evidence, "collect_branch_state", return_value=_branch_state()):
                report = evidence.build_report(root=root)

        self.assertEqual(evidence.STATUS_OK, report["status"])
        self.assertEqual(2, report["eligible_owner_count"])
        self.assertTrue(report["threshold_met"])

    def test_clean_tracked_owner_repo_receipts_count_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            fitness_root = root / "repos" / "fawxzzy-fitness"
            playbook_root = root / "repos" / "playbook"
            _owner_repo_receipt(fitness_root, "fitness-proof", "fitness")
            _owner_repo_receipt(playbook_root, "playbook-proof", "playbook")
            registry = {
                "fitness": SimpleNamespace(root=fitness_root),
                "playbook": SimpleNamespace(root=playbook_root),
            }

            def fake_git_stdout(_repo_root: Path, *args: str) -> tuple[int, str]:
                if args[:2] == ("ls-files", "--error-unmatch"):
                    return 0, args[-1]
                if args[:2] == ("status", "--porcelain=v1"):
                    return 0, ""
                return 0, ""

            with mock.patch.object(evidence, "collect_branch_state", return_value=_branch_state()), mock.patch.object(
                evidence, "load_repo_registry", return_value=registry
            ), mock.patch.object(evidence, "_git_stdout", side_effect=fake_git_stdout):
                report = evidence.build_report(root=root)

        self.assertEqual(evidence.STATUS_OK, report["status"])
        self.assertEqual(2, report["eligible_owner_count"])
        self.assertEqual({"owner_repo"}, {row["source"] for row in report["owner_evidence"]})

    def test_untracked_owner_repo_receipt_is_not_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            fitness_root = root / "repos" / "fawxzzy-fitness"
            _owner_repo_receipt(fitness_root, "fitness-proof", "fitness")
            registry = {"fitness": SimpleNamespace(root=fitness_root)}

            def fake_git_stdout(_repo_root: Path, *args: str) -> tuple[int, str]:
                if args[:2] == ("ls-files", "--error-unmatch"):
                    return 1, ""
                if args[:2] == ("status", "--porcelain=v1"):
                    return 0, ""
                return 0, ""

            with mock.patch.object(evidence, "collect_branch_state", return_value=_branch_state()), mock.patch.object(
                evidence, "load_repo_registry", return_value=registry
            ), mock.patch.object(evidence, "_git_stdout", side_effect=fake_git_stdout):
                report = evidence.build_report(root=root)

        self.assertEqual(evidence.STATUS_NEEDS_EVIDENCE, report["status"])
        self.assertEqual(0, report["eligible_owner_count"])
        self.assertIn("uncommitted:owner receipt not tracked", report["owner_evidence"][0]["reasons"])

    def test_dirty_owner_repo_receipt_is_not_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            fitness_root = root / "repos" / "fawxzzy-fitness"
            _owner_repo_receipt(fitness_root, "fitness-proof", "fitness")
            registry = {"fitness": SimpleNamespace(root=fitness_root)}

            def fake_git_stdout(_repo_root: Path, *args: str) -> tuple[int, str]:
                if args[:2] == ("ls-files", "--error-unmatch"):
                    return 0, args[-1]
                if args[:2] == ("status", "--porcelain=v1"):
                    return 0, " M docs/ops/fitness-proof.md"
                return 0, ""

            with mock.patch.object(evidence, "collect_branch_state", return_value=_branch_state()), mock.patch.object(
                evidence, "load_repo_registry", return_value=registry
            ), mock.patch.object(evidence, "_git_stdout", side_effect=fake_git_stdout):
                report = evidence.build_report(root=root)

        self.assertEqual(evidence.STATUS_NEEDS_EVIDENCE, report["status"])
        self.assertEqual(0, report["eligible_owner_count"])
        self.assertIn("uncommitted:owner receipt has local changes", report["owner_evidence"][0]["reasons"])

    def test_duplicate_owner_receipts_do_not_increase_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            _owner_receipt(root, "fitness-proof-a", "fitness")
            _owner_receipt(root, "fitness-proof-b", "fitness")
            with mock.patch.object(evidence, "collect_branch_state", return_value=_branch_state()):
                report = evidence.build_report(root=root)

        self.assertEqual(evidence.STATUS_NEEDS_EVIDENCE, report["status"])
        self.assertEqual(1, report["eligible_owner_count"])
        self.assertIn("duplicate_owner_evidence", {item["code"] for item in report["warnings"]})

    def test_root_mutation_makes_owner_receipt_ineligible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            _owner_receipt(root, "bad-proof", "fitness", root_mutated="true")
            with mock.patch.object(evidence, "collect_branch_state", return_value=_branch_state()):
                report = evidence.build_report(root=root)

        self.assertEqual(0, report["eligible_owner_count"])
        self.assertFalse(report["owner_evidence"][0]["eligible"])
        self.assertIn("expected:root mutated owner repo=false", report["owner_evidence"][0]["reasons"])

    def test_placeholder_owner_receipt_is_ineligible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            _owner_receipt(root, "placeholder-proof", "<repo-id>")
            with mock.patch.object(evidence, "collect_branch_state", return_value=_branch_state()):
                report = evidence.build_report(root=root)

        self.assertEqual(0, report["eligible_owner_count"])
        self.assertIn("invalid:owner repo", report["owner_evidence"][0]["reasons"])

    def test_root_plus_owner_root_receipts_are_not_owner_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            _write(
                root
                / "docs"
                / "ops"
                / "AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-ROOT-PLUS-OWNER-ADOPTION-EVIDENCE-INTAKE-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-07-04.md",
                "\n".join(
                    [
                        "# Root Reconciliation",
                        "- Owner-lane adoption proof: true",
                        "- Owner repo: <repo-id>",
                        "- AI work-session loop used: true",
                        "- Separate owner-lane authorization: true",
                        "- Root mutated owner repo: false",
                        "- Platform mutation from root: false",
                        "- Protected-surface mutation: false",
                        "- Secrets touched: false",
                        "",
                    ]
                ),
            )
            with mock.patch.object(evidence, "collect_branch_state", return_value=_branch_state()):
                report = evidence.build_report(root=root)

        self.assertEqual([], report["owner_evidence"])
        self.assertEqual(0, report["eligible_owner_count"])

    def test_owner_repo_receipt_scan_control_receipts_are_not_owner_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            _write(
                root
                / "docs"
                / "ops"
                / "AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-OWNER-REPO-RECEIPT-SCAN-SEPARATION-HARDENING-2026-07-04.md",
                "\n".join(
                    [
                        "# Root Control Receipt",
                        "- Owner-lane adoption proof: true",
                        "- Owner repo: <repo-id>",
                        "- AI work-session loop used: true",
                        "- Separate owner-lane authorization: true",
                        "- Root mutated owner repo: false",
                        "- Platform mutation from root: false",
                        "- Protected-surface mutation: false",
                        "- Secrets touched: false",
                        "",
                    ]
                ),
            )
            with mock.patch.object(evidence, "collect_branch_state", return_value=_branch_state()):
                report = evidence.build_report(root=root)

        self.assertEqual([], report["owner_evidence"])
        self.assertEqual(0, report["eligible_owner_count"])

    def test_missing_contract_receipt_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / evidence.CONTRACT_RECEIPTS[0], "# only one\n")
            with mock.patch.object(evidence, "collect_branch_state", return_value=_branch_state()):
                report = evidence.build_report(root=root)

        self.assertEqual(evidence.STATUS_BLOCKER, report["status"])
        self.assertFalse(report["safe_to_continue"])
        self.assertIn("contract_receipt_missing", {item["code"] for item in report["blockers"]})

    def test_strict_returns_nonzero_for_needs_owner_evidence(self) -> None:
        self.assertEqual(1, evidence.report_exit_code(status=evidence.STATUS_NEEDS_EVIDENCE, strict=True))

    def test_blocker_state_returns_nonzero(self) -> None:
        self.assertEqual(2, evidence.report_exit_code(status=evidence.STATUS_BLOCKER, strict=False))

    def test_protected_output_path_rejected(self) -> None:
        resolved, error = evidence.validate_output_path(root=Path("C:/ATLAS"), output_path="secrets/out.json")
        self.assertIsNone(resolved)
        self.assertEqual("protected_output_path", error["code"])

    def test_absolute_output_path_rejected(self) -> None:
        resolved, error = evidence.validate_output_path(root=Path("C:/ATLAS"), output_path="C:/tmp/out.json")
        self.assertIsNone(resolved)
        self.assertEqual("absolute_output_path", error["code"])

    def test_deterministic_json_field_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            with mock.patch.object(evidence, "collect_branch_state", return_value=_branch_state()):
                report = evidence.build_report(root=root)

        self.assertEqual(
            [
                "schema_version",
                "status",
                "root",
                "branch",
                "head",
                "parity",
                "contract_receipts",
                "owner_evidence",
                "eligible_owner_count",
                "required_owner_count",
                "threshold_met",
                "blockers",
                "warnings",
                "required_followups",
                "safe_to_continue",
            ],
            list(report.keys()),
        )

    def test_main_writes_output_only_for_root_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            output_path = root / "tmp" / "evidence.json"
            with mock.patch.object(evidence, "atlas_root", return_value=root), mock.patch.object(
                evidence, "collect_branch_state", return_value=_branch_state()
            ), mock.patch("sys.stdout", new_callable=io.StringIO):
                code = evidence.main(["--json", "--output", "tmp/evidence.json"])

            self.assertEqual(0, code)
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(evidence.SCHEMA_VERSION, payload["schema_version"])


if __name__ == "__main__":
    unittest.main()
