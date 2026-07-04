from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import ai_work_session_closeout as closeout


def _branch_state(
    *,
    staged: list[str] | None = None,
    unstaged: list[str] | None = None,
    untracked: list[str] | None = None,
) -> dict[str, object]:
    return {
        "branch": "main",
        "head": "abc123",
        "remote_tracking": "origin/main",
        "parity": {"status": "clean", "behind": 0, "ahead": 0},
        "staged": staged or [],
        "unstaged": unstaged or [],
        "untracked": untracked or [],
    }


def _validation(*, error: int = 0) -> dict[str, object]:
    return {
        "available": True,
        "critical": 0,
        "error": error,
        "warning": 3,
        "info": 0,
        "report_ref": "runtime/receipts/validation/stack-validation.latest.json",
    }


def _markers() -> dict[str, object]:
    return {
        "changed": [],
        "current_board": [
            {
                "marker": "AI Work Session Stability & Auto-Sync Loop",
                "percentage": 25,
                "category": "admissible after current lane",
            }
        ],
        "active_lane": "Sandbox Simulation Readiness",
        "operator_action": "hold_current_lane",
        "current_packet": "Sandbox held packet",
        "next_packet": "AI Work Session Stability & Auto-Sync Loop read-only closeout aggregator first-implementation worker packet 1",
        "current_basis_ref": "docs/ops/sandbox.md",
        "next_basis_ref": "docs/ops/closeout-readiness.md",
    }


def _inventory(
    *,
    root_blocking: list[str] | None = None,
    advisory: list[str] | None = None,
) -> dict[str, object]:
    return {
        "source_ref": "docs/registry/STACK-REPO-INVENTORY.json",
        "repo_count": 12,
        "dirty_repo_count": len(root_blocking or []),
        "visible_dirty_repo_count": len(root_blocking or []) + len(advisory or []),
        "advisory_dirty_repo_count": len(advisory or []),
        "root_blocking_dirty_repos": root_blocking or [],
        "advisory_dirty_repos": advisory or [],
    }


def _patch_collectors(
    *,
    branch_state: dict[str, object] | None = None,
    validation: dict[str, object] | None = None,
    inventory: dict[str, object] | None = None,
):
    return mock.patch.multiple(
        closeout,
        collect_branch_state=mock.Mock(return_value=branch_state or _branch_state()),
        collect_validation=mock.Mock(return_value=validation or _validation()),
        collect_markers=mock.Mock(return_value=_markers()),
        collect_inventory=mock.Mock(return_value=inventory or _inventory()),
        collect_owner_scope=mock.Mock(return_value={"mode": "none", "repos": []}),
    )


class AtlasAiWorkSessionCloseoutTests(unittest.TestCase):
    def test_root_closeout_clean_returns_ok(self) -> None:
        with _patch_collectors():
            report = closeout.build_report(
                root=Path("C:/ATLAS"),
                scope="root",
                session_label="clean",
                touched_repos=[],
                commands_run=["python ops/validation/validate_stack.py"],
            )
        self.assertEqual(closeout.STATUS_OK, report["status"])
        self.assertTrue(report["safe_to_close"])
        self.assertEqual([], report["markers"]["changed"])

    def test_closeout_with_advisory_warnings(self) -> None:
        with _patch_collectors(branch_state=_branch_state(unstaged=["docs/example.md"])):
            report = closeout.build_report(
                root=Path("C:/ATLAS"),
                scope="root",
                session_label="advisory",
                touched_repos=[],
                commands_run=[],
            )
        self.assertEqual(closeout.STATUS_ADVISORY, report["status"])
        self.assertFalse(report["safe_to_close"])
        self.assertEqual("local_residue_present", report["warnings"][0]["code"])

    def test_closeout_with_blockers(self) -> None:
        with _patch_collectors(validation=_validation(error=1)):
            report = closeout.build_report(
                root=Path("C:/ATLAS"),
                scope="root",
                session_label="blocked",
                touched_repos=[],
                commands_run=[],
            )
        self.assertEqual(closeout.STATUS_BLOCKER, report["status"])
        self.assertFalse(report["safe_to_close"])
        self.assertIn("validation_blocking", {item["code"] for item in report["blockers"]})

    def test_owner_touched_classification(self) -> None:
        with _patch_collectors(), mock.patch.object(
            closeout,
            "collect_owner_scope",
            return_value={"mode": "read_only", "repos": [{"name": "fitness", "known": True}]},
        ):
            report = closeout.build_report(
                root=Path("C:/ATLAS"),
                scope="owner",
                session_label="owner",
                touched_repos=["fitness"],
                commands_run=[],
            )
        self.assertEqual("read_only", report["owner_repo_scope"]["mode"])

    def test_platform_touched_classification(self) -> None:
        with _patch_collectors():
            report = closeout.build_report(
                root=Path("C:/ATLAS"),
                scope="platform",
                session_label="platform",
                touched_repos=[],
                commands_run=[],
            )
        self.assertEqual("read_only", report["platform_scope"])

    def test_protected_output_path_rejection(self) -> None:
        resolved, error = closeout.validate_output_path(root=Path("C:/ATLAS"), output_path="runtime/out.json")
        self.assertIsNone(resolved)
        self.assertEqual("protected_output_path", error["code"])

    def test_strict_mode_nonzero_on_blockers(self) -> None:
        self.assertEqual(2, closeout.report_exit_code(status=closeout.STATUS_BLOCKER, strict=True))

    def test_deterministic_json_order(self) -> None:
        with _patch_collectors():
            report = closeout.build_report(
                root=Path("C:/ATLAS"),
                scope="root",
                session_label="order",
                touched_repos=[],
                commands_run=[],
            )
        keys = list(report.keys())
        self.assertEqual(
            [
                "schema_version",
                "status",
                "session_label",
                "scope",
                "root",
                "branch",
                "head",
                "parity",
                "repos_touched",
                "commands_run",
                "validation",
                "markers",
                "proof",
                "protected_surfaces",
                "local_residue",
                "blockers",
                "warnings",
                "next_actions",
                "safe_to_close",
                "inventory",
                "owner_repo_scope",
                "platform_scope",
            ],
            keys,
        )

    def test_missing_input_classification(self) -> None:
        with _patch_collectors(branch_state={**_branch_state(), "branch": None}):
            report = closeout.build_report(
                root=Path("C:/ATLAS"),
                scope="root",
                session_label="missing",
                touched_repos=[],
                commands_run=[],
            )
        self.assertEqual(closeout.STATUS_BLOCKER, report["status"])
        self.assertIn("branch_truth_unavailable", {item["code"] for item in report["blockers"]})

    def test_safe_to_close_true_and_false_cases(self) -> None:
        with _patch_collectors():
            clean = closeout.build_report(
                root=Path("C:/ATLAS"),
                scope="root",
                session_label="clean",
                touched_repos=[],
                commands_run=[],
            )
        with _patch_collectors(branch_state=_branch_state(staged=["docs/example.md"])):
            blocked = closeout.build_report(
                root=Path("C:/ATLAS"),
                scope="root",
                session_label="blocked",
                touched_repos=[],
                commands_run=[],
            )
        self.assertTrue(clean["safe_to_close"])
        self.assertFalse(blocked["safe_to_close"])

    def test_main_writes_output_only_for_root_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_path = root / "tmp" / "closeout.json"
            with _patch_collectors(), mock.patch.object(closeout, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = closeout.main(["--json", "--session-label", "write", "--output", "tmp/closeout.json"])
            self.assertEqual(0, code)
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(closeout.SCHEMA_VERSION, payload["schema_version"])

    def test_main_rejects_protected_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with _patch_collectors(), mock.patch.object(closeout, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = closeout.main(["--json", "--session-label", "protected", "--output", "secrets/out.json"])
        self.assertEqual(2, code)

    def test_root_blocking_dirty_repo_blocks_closeout(self) -> None:
        with _patch_collectors(inventory=_inventory(root_blocking=["discordos"])):
            report = closeout.build_report(
                root=Path("C:/ATLAS"),
                scope="root",
                session_label="root-dirty",
                touched_repos=[],
                commands_run=[],
            )
        self.assertEqual(closeout.STATUS_BLOCKER, report["status"])
        self.assertIn("root_blocking_dirty_repos", {item["code"] for item in report["blockers"]})

    def test_collect_inventory_reads_current_repos_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inventory_path = root / "docs" / "registry" / "STACK-REPO-INVENTORY.json"
            inventory_path.parent.mkdir(parents=True)
            inventory_path.write_text(
                json.dumps(
                    {
                        "repo_count": 2,
                        "dirty_repo_count": 1,
                        "visible_dirty_repo_count": 2,
                        "advisory_dirty_repo_count": 1,
                        "repos": [
                            {"logical_id": "discordos", "dirty": True, "dirty_blocks_root": True},
                            {"logical_id": "fitness", "dirty": True, "dirty_blocks_root": False},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            inventory = closeout.collect_inventory(root)

        self.assertEqual(["discordos"], inventory["root_blocking_dirty_repos"])
        self.assertEqual(["fitness"], inventory["advisory_dirty_repos"])

    def test_collect_inventory_keeps_legacy_repositories_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inventory_path = root / "docs" / "registry" / "STACK-REPO-INVENTORY.json"
            inventory_path.parent.mkdir(parents=True)
            inventory_path.write_text(
                json.dumps(
                    {
                        "repo_count": 1,
                        "dirty_repo_count": 0,
                        "visible_dirty_repo_count": 1,
                        "advisory_dirty_repo_count": 1,
                        "repositories": [
                            {"logical_id": "fitness", "dirty": True, "dirty_blocks_root": False},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            inventory = closeout.collect_inventory(root)

        self.assertEqual([], inventory["root_blocking_dirty_repos"])
        self.assertEqual(["fitness"], inventory["advisory_dirty_repos"])


if __name__ == "__main__":
    unittest.main()
