from __future__ import annotations

import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import ai_work_session_preflight as preflight


def _base_report(*, status: str = preflight.STATUS_OK) -> dict[str, object]:
    return {
        "schema_version": preflight.SCHEMA_VERSION,
        "status": status,
        "scope": "root",
        "root": "C:/ATLAS",
        "branch": "main",
        "head": "abc123",
        "remote_tracking": "origin/main",
        "parity": {"status": "clean", "behind": 0, "ahead": 0},
        "validation": {"available": True, "critical": 0, "error": 0, "warning": 3, "info": 0},
        "markers": {
            "status": preflight.STATUS_OK,
            "active_lane": "Sandbox Simulation Readiness",
            "active_lane_is_held": True,
            "operator_action": "hold_current_lane",
            "current_packet": "Sandbox hold",
            "next_packet": "AI Work Session Stability & Auto-Sync Loop read-only preflight aggregator first-implementation worker packet 1",
            "current_basis_ref": "docs/ops/sandbox.md",
            "next_basis_ref": "docs/ops/ai-preflight.md",
        },
        "continuity": {
            "status": preflight.STATUS_OK,
            "manifest_health": {"status": "ok", "ok_count": 20, "warning_count": 0, "error_count": 0},
            "restart_index": {
                "status": "ok",
                "eligible_open_marker_count": 7,
                "restart_ready_count": 7,
                "restart_ready_percent": 100.0,
                "items": [{"marker": "Sandbox Simulation Readiness"}],
            },
            "coverage": {"status": "structured", "pending_review_count": 0},
        },
        "stack_inventory": {
            "status": preflight.STATUS_OK,
            "published_ref": "docs/registry/STACK-REPO-INVENTORY.json",
            "published_digest": "sha256:1",
            "live_digest": "sha256:1",
            "repo_count": 12,
            "dirty_repo_count": 1,
            "release_eligible_count": 5,
        },
        "projection_freshness": {
            "status": preflight.STATUS_OK,
            "lockfile_matches_live_working_set": True,
            "lockfile_drift": {"metadata_fields": [], "components": {}, "excluded_surfaces": {}},
            "inventory_matches_live_working_set": True,
            "published_inventory_ref": "docs/registry/STACK-REPO-INVENTORY.json",
        },
        "qa_release_readiness": {
            "status": "blocked",
            "source_ref": "runtime/atlas/qa/github-secret-readiness.latest.json",
            "available_secret_count": 0,
            "missing_required_secret_names": [
                "BROWSERSTACK_ACCESS_KEY",
                "BROWSERSTACK_USERNAME",
            ],
        },
        "playbook": {
            "status": preflight.STATUS_OK,
            "repo_present": True,
            "branch": "main",
            "dirty": False,
            "adoption_signal": "playbook_repo_visible",
            "stack_inventory_digest": "sha256:1",
        },
        "platform": {"status": "not_requested", "requested": False},
        "protected_surfaces": {
            "status": preflight.STATUS_OK,
            "entries": [{"path": "archive", "present": False}],
            "env_files": [],
        },
        "local_residue": {
            "status": preflight.STATUS_OK,
            "root_dirty_paths": [],
            "owner_dirty_paths": [],
        },
        "required_followups": [
            {
                "kind": "packet",
                "scope": "root",
                "action": "execute",
                "target": "AI Work Session Stability & Auto-Sync Loop read-only preflight aggregator first-implementation worker packet 1",
            }
        ],
        "blockers": [],
        "warnings": [],
    }


class AtlasAiWorkSessionPreflightTests(unittest.TestCase):
    def _init_repo(self, path: Path, *, remote: str = "https://github.com/fawxzzy/ATLAS.git") -> None:
        path.mkdir(parents=True)
        subprocess.run(["git", "init", "--quiet", str(path)], check=True)
        subprocess.run(["git", "-C", str(path), "remote", "add", "origin", remote], check=True)

    def _write_validation_receipt(self, root: Path, *, stack_root: Path | str | None = None) -> None:
        receipt_path = root / "runtime/receipts/validation/stack-validation.latest.json"
        receipt_path.parent.mkdir(parents=True)
        receipt_path.write_text(
            json.dumps(
                {
                    "stack_root": str(stack_root if stack_root is not None else root.resolve()),
                    "summary": {"critical": 0, "error": 0, "warning": 2, "info": 1},
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def _patch_collectors(self, *, projection_status: str = preflight.STATUS_OK, continuity_items: list[dict[str, object]] | None = None):
        branch_state = {
            "branch": "main",
            "head": "abc123",
            "remote_tracking": "origin/main",
            "parity": {"status": "clean", "behind": 0, "ahead": 0},
            "dirty_paths": [],
        }
        validation = {"available": True, "critical": 0, "error": 0, "warning": 3, "info": 0, "report_ref": "runtime/receipts/validation/stack-validation.latest.json"}
        markers = {
            "status": preflight.STATUS_OK,
            "active_lane": "Sandbox Simulation Readiness",
            "active_lane_is_held": True,
            "operator_action": "hold_current_lane",
            "current_packet": "Sandbox hold",
            "next_packet": "AI Work Session Stability & Auto-Sync Loop read-only preflight aggregator first-implementation worker packet 1",
            "current_basis_ref": "docs/ops/sandbox.md",
            "next_basis_ref": "docs/ops/ai-preflight.md",
        }
        continuity = {
            "status": preflight.STATUS_OK,
            "manifest_health": {"status": "ok", "ok_count": 20, "warning_count": 0, "error_count": 0},
            "restart_index": {
                "status": "ok",
                "eligible_open_marker_count": 7,
                "restart_ready_count": 7,
                "restart_ready_percent": 100.0,
                "items": continuity_items or [{"marker": "Sandbox Simulation Readiness"}],
            },
            "coverage": {"status": "structured", "pending_review_count": 0},
        }
        stack_inventory = {
            "status": preflight.STATUS_OK,
            "published_ref": "docs/registry/STACK-REPO-INVENTORY.json",
            "published_digest": "sha256:1",
            "live_digest": "sha256:1",
            "repo_count": 12,
            "dirty_repo_count": 1,
            "release_eligible_count": 5,
        }
        projection = {
            "status": projection_status,
            "lockfile_matches_live_working_set": projection_status == preflight.STATUS_OK,
            "lockfile_drift": {"metadata_fields": [], "components": {}, "excluded_surfaces": {}},
            "inventory_matches_live_working_set": projection_status == preflight.STATUS_OK,
            "published_inventory_ref": "docs/registry/STACK-REPO-INVENTORY.json",
        }
        qa = {
            "status": "blocked",
            "source_ref": "runtime/atlas/qa/github-secret-readiness.latest.json",
            "available_secret_count": 0,
            "missing_required_secret_names": ["BROWSERSTACK_ACCESS_KEY", "BROWSERSTACK_USERNAME"],
        }
        playbook = {
            "status": preflight.STATUS_OK,
            "repo_present": True,
            "branch": "main",
            "dirty": False,
            "adoption_signal": "playbook_repo_visible",
            "stack_inventory_digest": "sha256:1",
        }
        protected = {"status": preflight.STATUS_OK, "entries": [], "env_files": []}

        return mock.patch.multiple(
            preflight,
            collect_branch_state=mock.DEFAULT,
            collect_validation=mock.DEFAULT,
            collect_markers=mock.DEFAULT,
            collect_continuity=mock.DEFAULT,
            collect_stack_state=mock.DEFAULT,
            collect_qa_release_readiness=mock.DEFAULT,
            collect_playbook=mock.DEFAULT,
            collect_platform=mock.DEFAULT,
            collect_protected_surfaces=mock.DEFAULT,
        ), {
            "collect_branch_state": branch_state,
            "collect_validation": validation,
            "collect_markers": markers,
            "collect_continuity": continuity,
            "collect_stack_state": (stack_inventory, projection),
            "collect_qa_release_readiness": qa,
            "collect_playbook": playbook,
            "collect_platform": {"status": "not_requested", "requested": False},
            "collect_protected_surfaces": protected,
        }

    def test_root_scope_clean_read_returns_ok(self) -> None:
        patcher, values = self._patch_collectors()
        with patcher as mocks:
            for name, value in values.items():
                mocks[name].return_value = value
            report = preflight.build_report(root=Path("C:/ATLAS"), scope="root")
        self.assertEqual(preflight.STATUS_ADVISORY, report["status"])
        self.assertEqual("root", report["scope"])
        self.assertEqual("main", report["branch"])
        self.assertEqual("abc123", report["head"])

    def test_projection_drift_becomes_advisory_drift(self) -> None:
        patcher, values = self._patch_collectors(projection_status=preflight.STATUS_ADVISORY)
        with patcher as mocks:
            for name, value in values.items():
                mocks[name].return_value = value
            report = preflight.build_report(root=Path("C:/ATLAS"), scope="root")
        warning_codes = {item["code"] for item in report["warnings"]}
        self.assertEqual(preflight.STATUS_ADVISORY, report["status"])
        self.assertIn("projection_freshness_drift", warning_codes)

    def test_owner_scope_read_only_classification(self) -> None:
        patcher, values = self._patch_collectors()
        owner_scope = {
            "status": preflight.STATUS_OK,
            "owner": "mazer",
            "repo_path": "repos/mazer",
            "branch": "main",
            "head": "def456",
            "dirty_paths": [],
        }
        with patcher as mocks, mock.patch.object(preflight, "resolve_owner_scope", return_value=owner_scope):
            for name, value in values.items():
                mocks[name].return_value = value
            report = preflight.build_report(root=Path("C:/ATLAS"), scope="owner", owner="mazer")
        self.assertEqual(preflight.STATUS_ADVISORY, report["status"])
        self.assertEqual("owner", report["scope"])

    def test_platform_scope_read_only_classification(self) -> None:
        patcher, values = self._patch_collectors()
        values["collect_platform"] = {"status": "blocked", "requested": True}
        with patcher as mocks:
            for name, value in values.items():
                mocks[name].return_value = value
            report = preflight.build_report(root=Path("C:/ATLAS"), scope="platform")
        self.assertEqual(preflight.STATUS_ADVISORY, report["status"])
        self.assertEqual("platform", report["scope"])

    def test_research_scope_read_only_classification(self) -> None:
        patcher, values = self._patch_collectors()
        with patcher as mocks:
            for name, value in values.items():
                mocks[name].return_value = value
            report = preflight.build_report(root=Path("C:/ATLAS"), scope="research")
        self.assertEqual(preflight.STATUS_ADVISORY, report["status"])
        self.assertEqual("research", report["scope"])

    def test_validate_output_path_rejects_protected_path(self) -> None:
        resolved, error = preflight.validate_output_path(root=Path("C:/ATLAS"), output_path="secrets/out.json")
        self.assertIsNone(resolved)
        self.assertEqual("protected_output_path", error["code"])

    def test_validate_output_path_rejects_absolute_path(self) -> None:
        resolved, error = preflight.validate_output_path(root=Path("C:/ATLAS"), output_path="C:/temp/out.json")
        self.assertIsNone(resolved)
        self.assertEqual("absolute_output_path", error["code"])

    def test_collect_validation_defaults_to_source_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "source"
            self._init_repo(source_root)
            self._write_validation_receipt(source_root)

            validation = preflight.collect_validation(source_root)

        self.assertTrue(validation["available"])
        self.assertEqual("exact", validation["binding_status"])
        self.assertEqual(validation["source_root"], validation["validation_root"])
        self.assertEqual("github.com/fawxzzy/atlas", validation["repository"])

    def test_collect_validation_accepts_explicit_same_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "source"
            validation_root = Path(temp_dir) / "validation"
            self._init_repo(source_root)
            self._init_repo(validation_root, remote="git@github.com:fawxzzy/ATLAS.git")
            self._write_validation_receipt(validation_root)

            validation = preflight.collect_validation(source_root, validation_root=validation_root)

        self.assertTrue(validation["available"])
        self.assertEqual("exact", validation["binding_status"])
        self.assertEqual(2, validation["warning"])
        self.assertEqual(1, validation["info"])

    def test_collect_validation_rejects_different_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "source"
            validation_root = Path(temp_dir) / "validation"
            self._init_repo(source_root)
            self._init_repo(validation_root, remote="https://github.com/fawxzzy/other.git")
            self._write_validation_receipt(validation_root)

            validation = preflight.collect_validation(source_root, validation_root=validation_root)

        self.assertFalse(validation["available"])
        self.assertEqual("blocked", validation["binding_status"])
        self.assertEqual("validation_root_repository_mismatch", validation["binding_error"]["code"])

    def test_collect_validation_rejects_receipt_stack_root_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "source"
            validation_root = Path(temp_dir) / "validation"
            self._init_repo(source_root)
            self._init_repo(validation_root)
            self._write_validation_receipt(validation_root, stack_root=Path(temp_dir) / "other")

            validation = preflight.collect_validation(source_root, validation_root=validation_root)

        self.assertFalse(validation["available"])
        self.assertEqual("validation_receipt_root_mismatch", validation["binding_error"]["code"])

    def test_collect_validation_rejects_relative_receipt_stack_root_even_when_cwd_matches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "source"
            validation_root = Path(temp_dir) / "validation"
            self._init_repo(source_root)
            self._init_repo(validation_root)
            self._write_validation_receipt(validation_root, stack_root="validation")

            original_cwd = Path.cwd()
            try:
                os.chdir(temp_dir)
                validation = preflight.collect_validation(source_root, validation_root=validation_root)
            finally:
                os.chdir(original_cwd)

        self.assertFalse(validation["available"])
        self.assertEqual("blocked", validation["binding_status"])
        self.assertEqual("validation_receipt_root_mismatch", validation["binding_error"]["code"])
        self.assertEqual("validation", validation["receipt_stack_root"])

    def test_collect_validation_rejects_missing_explicit_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "source"
            self._init_repo(source_root)

            validation = preflight.collect_validation(
                source_root,
                validation_root=Path(temp_dir) / "missing",
            )

        self.assertFalse(validation["available"])
        self.assertEqual("validation_root_unavailable", validation["binding_error"]["code"])

    def test_collect_validation_rejects_relative_explicit_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "source"
            self._init_repo(source_root)

            validation = preflight.collect_validation(
                source_root,
                validation_root=Path("implicit-validation-root"),
            )

        self.assertFalse(validation["available"])
        self.assertEqual("validation_root_not_absolute", validation["binding_error"]["code"])

    def test_root_binding_rejects_windows_reparse_attribute(self) -> None:
        candidate = mock.Mock(spec=Path)
        candidate.exists.return_value = True
        candidate.is_dir.return_value = True
        candidate.is_symlink.return_value = False
        candidate.lstat.return_value = mock.Mock(st_file_attributes=0x400)
        candidate.__str__ = mock.Mock(return_value="C:/junctioned-root")

        identity, error = preflight._root_binding_identity(candidate, label="validation_root")

        self.assertIsNone(identity)
        self.assertEqual("validation_root_ambiguous", error["code"])

    def test_root_binding_rejects_indirect_symlink_or_junction_alias(self) -> None:
        candidate = mock.Mock(spec=Path)
        candidate.exists.return_value = True
        candidate.is_dir.return_value = True
        candidate.is_symlink.return_value = False
        candidate.lstat.return_value = mock.Mock(st_file_attributes=0)
        candidate.resolve.return_value = Path("C:/real/root")
        candidate.__fspath__ = mock.Mock(return_value="C:/alias/root")
        candidate.__str__ = mock.Mock(return_value="C:/alias/root")

        identity, error = preflight._root_binding_identity(candidate, label="validation_root")

        self.assertIsNone(identity)
        self.assertEqual("validation_root_ambiguous", error["code"])

    def test_contradictory_authoritative_inputs_fail_closed(self) -> None:
        patcher, values = self._patch_collectors(continuity_items=[{"marker": "AI Work Session Stability & Auto-Sync Loop"}])
        with patcher as mocks:
            for name, value in values.items():
                mocks[name].return_value = value
            report = preflight.build_report(root=Path("C:/ATLAS"), scope="root")
        blocker_codes = {item["code"] for item in report["blockers"]}
        self.assertEqual(preflight.STATUS_BLOCKER, report["status"])
        self.assertIn("contradictory_authoritative_inputs", blocker_codes)

    def test_strict_mode_maps_advisory_to_exit_one(self) -> None:
        self.assertEqual(1, preflight.report_exit_code(status=preflight.STATUS_ADVISORY, strict=True))

    def test_blocker_exit_code_is_two(self) -> None:
        self.assertEqual(2, preflight.report_exit_code(status=preflight.STATUS_BLOCKER, strict=False))

    def test_internal_error_exit_code_is_three(self) -> None:
        self.assertEqual(3, preflight.report_exit_code(status=preflight.STATUS_INTERNAL_ERROR, strict=False))

    def test_render_stdout_emits_summary_before_json(self) -> None:
        report = _base_report(status=preflight.STATUS_ADVISORY)
        rendered = preflight.render_stdout(report, json_only=False)
        summary, payload_text = rendered.split("\n\n", 1)
        payload = json.loads(payload_text)
        self.assertIn("Status: advisory_drift", summary)
        self.assertEqual(preflight.SCHEMA_VERSION, payload["schema_version"])

    def test_main_writes_output_only_for_root_relative_paths(self) -> None:
        report = _base_report(status=preflight.STATUS_OK)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_path = root / "tmp" / "preflight.json"
            with mock.patch.object(preflight, "atlas_root", return_value=root), mock.patch.object(
                preflight, "build_report", return_value=report
            ):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = preflight.main(["--json", "--output", "tmp/preflight.json"])
            self.assertEqual(0, code)
            self.assertTrue(output_path.exists())

    def test_main_forwards_explicit_validation_root(self) -> None:
        report = _base_report(status=preflight.STATUS_OK)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            validation_root = root / "validation"
            with mock.patch.object(preflight, "atlas_root", return_value=root), mock.patch.object(
                preflight, "build_report", return_value=report
            ) as build_report:
                with mock.patch("sys.stdout", io.StringIO()):
                    code = preflight.main(["--json", "--validation-root", str(validation_root)])

        self.assertEqual(0, code)
        build_report.assert_called_once_with(
            root=root.resolve(),
            scope="root",
            owner=None,
            validation_root=validation_root,
        )

    def test_main_returns_blocker_for_protected_output_path(self) -> None:
        report = _base_report(status=preflight.STATUS_OK)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(preflight, "atlas_root", return_value=root), mock.patch.object(
                preflight, "build_report", return_value=report
            ):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = preflight.main(["--json", "--output", "runtime/out.json"])
        self.assertEqual(2, code)


if __name__ == "__main__":
    unittest.main()
