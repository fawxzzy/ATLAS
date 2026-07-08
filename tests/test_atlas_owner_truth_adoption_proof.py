from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import owner_truth_adoption_proof as proof


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _inventory_payload(*, advisory: list[str] | None = None, root_blocking: list[str] | None = None) -> dict[str, object]:
    advisory = advisory or []
    root_blocking = root_blocking or []
    repos = [
        {
            "logical_id": repo_id,
            "dirty": True,
            "root_blocking": False,
            "dirty_blocks_root": False,
            "status": "unmanaged",
        }
        for repo_id in advisory
    ]
    repos.extend(
        {
            "logical_id": repo_id,
            "dirty": True,
            "root_blocking": True,
            "dirty_blocks_root": True,
            "status": "active",
        }
        for repo_id in root_blocking
    )
    return {
        "schema_version": "atlas.stack.repo-inventory.v1",
        "repo_count": len(repos),
        "dirty_repo_count": len(root_blocking),
        "visible_dirty_repo_count": len(advisory) + len(root_blocking),
        "advisory_dirty_repo_count": len(advisory),
        "repos": repos,
    }


def _minimal_root(
    root: Path,
    *,
    advisory: list[str] | None = None,
    root_blocking: list[str] | None = None,
    validation: str = "critical=0 error=0 warning=0 info=0",
    book_counts: tuple[int, int, int] | None = None,
) -> None:
    payload = _inventory_payload(advisory=advisory, root_blocking=root_blocking)
    _write(root / "docs" / "registry" / "STACK-REPO-INVENTORY.json", json.dumps(payload, indent=2))
    counts = book_counts or (
        int(payload["dirty_repo_count"]),
        int(payload["visible_dirty_repo_count"]),
        int(payload["advisory_dirty_repo_count"]),
    )
    _write(
        root / "docs" / "audits" / "STACK-REPO-INVENTORY.md",
        "\n".join(
            [
                "# Stack Repo Inventory",
                "",
                f"- Root-blocking dirty repo count: `{payload['dirty_repo_count']}`",
                f"- Visible dirty repo count: `{payload['visible_dirty_repo_count']}`",
                f"- Advisory dirty repo count: `{payload['advisory_dirty_repo_count']}`",
                "",
            ]
        ),
    )
    book_text = "\n".join(
        [
            "Inventory truth is mirrored.",
            f"root validation currently reads `{validation}`",
            f"dirty_repo_count: {counts[0]}",
            f"visible_dirty_repo_count: {counts[1]}",
            f"advisory_dirty_repo_count: {counts[2]}",
            "No immediate Inventory & Truth Map follow-on packet",
            "INVENTORY-AND-TRUTH-MAP-OWNER-TRUTH-ADOPTION-PROOF-CONTRACT-FREEZE-2026-07-08.md",
            "",
        ]
    )
    for ref in proof.ATLAS_BOOK_REFS:
        _write(root / ref, book_text)
    _write(
        root / "AGENTS.md",
        "\n".join(
            [
                "ATLAS-root sessions are root-governance sessions by default.",
                "Fitness, Mazer, and other owner repos are excluded fallback lanes unless explicitly selected.",
                "Do not switch into Fitness, Mazer, Stripe/Vercel launch work, game work, or owner-repo cleanup as a fallback.",
                "",
            ]
        ),
    )
    _write(root / "stack.yaml", "name: atlas\n")
    for ref in proof.REQUIRED_RECEIPTS:
        _write(root / ref, f"# {Path(ref).stem}\n")


class AtlasOwnerTruthAdoptionProofTests(unittest.TestCase):
    def test_advisory_owner_dirt_is_adopted_as_non_blocking_truth(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root, advisory=["fitness", "mazer"])
            report = proof.build_report(root=root)

        self.assertEqual(proof.STATUS_OK, report["status"])
        self.assertTrue(report["safe_to_use"])
        self.assertEqual(proof.ADOPTION_ADOPTED, report["adoption_result"])
        self.assertEqual(["fitness", "mazer"], report["advisory_owner_repos"])
        self.assertEqual([], report["root_blocking_owner_repos"])
        self.assertEqual(proof.MARKER_CANDIDATE, report["marker_implication"])

    def test_root_blocking_owner_dirt_blocks_adoption(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root, root_blocking=["playbook"])
            report = proof.build_report(root=root)

        self.assertEqual(proof.STATUS_BLOCKER, report["status"])
        self.assertFalse(report["safe_to_use"])
        self.assertEqual(proof.ADOPTION_BLOCKED, report["adoption_result"])
        self.assertEqual(["playbook"], report["root_blocking_owner_repos"])

    def test_stale_book_mirror_is_insufficient_evidence_not_blocking_owner_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root, advisory=["fitness"], book_counts=(0, 0, 0))
            report = proof.build_report(root=root)

        self.assertEqual(proof.STATUS_ADVISORY, report["status"])
        self.assertTrue(report["safe_to_use"])
        self.assertEqual(proof.ADOPTION_INSUFFICIENT, report["adoption_result"])
        self.assertIn("book_mirror_drift", {item["code"] for item in report["warnings"]})

    def test_validation_error_blocks_adoption(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root, advisory=["fitness"], validation="critical=0 error=1 warning=0 info=0")
            report = proof.build_report(root=root)

        self.assertEqual(proof.STATUS_BLOCKER, report["status"])
        self.assertIn("root_validation_not_clean", {item["code"] for item in report["blockers"]})

    def test_owner_status_inline_summary_must_match_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root, advisory=["fitness"])
            report = proof.build_report(root=root, owner_status_values=["mazer:dirty:advisory"])

        self.assertEqual(proof.STATUS_ADVISORY, report["status"])
        self.assertIn("owner_status_not_adopted", {item["code"] for item in report["warnings"]})

    def test_owner_status_root_blocking_summary_missing_from_inventory_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root, advisory=["fitness"])
            report = proof.build_report(root=root, owner_status_values=["playbook:dirty:root_blocking"])

        self.assertEqual(proof.STATUS_BLOCKER, report["status"])
        self.assertIn("owner_status_root_blocking_not_adopted", {item["code"] for item in report["blockers"]})

    def test_scope_lock_missing_is_contract_violation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root, advisory=["fitness"])
            _write(root / "AGENTS.md", "root governance only\n")
            report = proof.build_report(root=root)

        self.assertEqual(proof.STATUS_BLOCKER, report["status"])
        self.assertEqual(proof.ADOPTION_CONTRACT_VIOLATION, report["adoption_result"])
        self.assertIn("scope_lock_drift", {item["code"] for item in report["blockers"]})

    def test_authority_denials_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root, advisory=["fitness"])
            report = proof.build_report(root=root)

        self.assertTrue(report["authority_denials"]["owner_repo_mutation"])
        self.assertTrue(report["authority_denials"]["secret_access"])
        self.assertTrue(report["authority_denials"]["marker_movement_without_reconciliation_receipt"])

    def test_protected_output_path_rejected(self) -> None:
        resolved, error = proof.validate_output_path(root=Path("C:/ATLAS"), output_path="repos/out.json")
        self.assertIsNone(resolved)
        self.assertEqual("protected_output_path", error["code"])

    def test_absolute_output_path_rejected(self) -> None:
        resolved, error = proof.validate_output_path(root=Path("C:/ATLAS"), output_path="C:/tmp/out.json")
        self.assertIsNone(resolved)
        self.assertEqual("absolute_output_path", error["code"])

    def test_invalid_owner_status_input_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root, advisory=["fitness"])
            report = proof.build_report(root=root, owner_status_values=["repos/fitness:dirty:advisory"])

        self.assertEqual(proof.STATUS_BLOCKER, report["status"])
        self.assertIn("invalid_owner_status_repo", {item["code"] for item in report["blockers"]})

    def test_deterministic_json_field_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root, advisory=["fitness"])
            report = proof.build_report(root=root)

        self.assertEqual(
            [
                "schema_version",
                "status",
                "safe_to_use",
                "root_validation_summary",
                "inventory_dirty_repo_count",
                "inventory_visible_dirty_repo_count",
                "inventory_advisory_dirty_repo_count",
                "advisory_owner_repos",
                "root_blocking_owner_repos",
                "owner_status_inputs",
                "book_mirror_status",
                "scope_lock_status",
                "receipt_status",
                "adoption_result",
                "marker_implication",
                "blockers",
                "warnings",
                "authority_denials",
            ],
            list(report.keys()),
        )

    def test_main_writes_output_only_for_root_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root, advisory=["fitness"])
            output_path = root / "tmp" / "owner-truth.json"
            with mock.patch.object(proof, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = proof.main(["--json", "--output", "tmp/owner-truth.json"])

            self.assertEqual(0, code)
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(proof.SCHEMA_VERSION, payload["schema_version"])


if __name__ == "__main__":
    unittest.main()
