from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ops.validation.validate_stack import (
    apply_repo_generated_state_cleanup,
    build_archive_declared_paths,
    build_archive_scope_exempt_paths,
    collect_text_scan_roots,
    declared_stack_coordinate,
    is_repo_local_secret_candidate,
    iter_unique_repo_root_files,
    mutable_surface_requires_warning,
    mutable_surface_warning_map,
    repo_status_allows_internal_validation,
    validate_declared_stack_coordinates,
)


class ValidateStackMutableStateRulesTests(unittest.TestCase):
    def test_archive_policy_preserves_declared_relative_coordinates(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        stack_file = root / "stack.yaml"
        config = {
            "archives": {
                "backups": "repos/repo-backups",
                "zip_snapshots": ["repos/dev.zip"],
                "media": ["data/media"],
            },
            "stack_lock": {
                "excluded_surfaces": {
                    "archive": {"path": "repos/archive.zip"},
                }
            },
        }

        self.assertEqual(
            {"repos/repo-backups", "repos/dev.zip", "data/media", "data/media.zip", "repos/archive.zip"},
            build_archive_declared_paths(stack_file, config),
        )
        self.assertTrue({"data/media", "data/media.zip"}.issubset(build_archive_scope_exempt_paths(stack_file, config)))

    def test_declared_stack_coordinates_reject_escape_before_matching_or_reporting(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        stack_file = root / "stack.yaml"
        config = {
            "repo_registry": {"outside": {"path": "../outside-repo"}},
            "archives": {
                "archive_register": "docs/registry/ATLAS-ARCHIVE-REGISTRY.json",
                "zip_snapshots": ["../outside.zip"],
                "media": [str(root.parent / "outside-media")],
            },
            "stack_lock": {
                "path": "stack.lock.yaml",
                "excluded_surfaces": {"outside": {"path": "../outside-surface"}},
            },
        }

        findings = validate_declared_stack_coordinates(stack_file, config)

        self.assertEqual(4, len(findings))
        self.assertEqual({"stack-path-outside-root"}, {finding.category for finding in findings})
        self.assertEqual(set(), build_archive_declared_paths(stack_file, config))

    def test_lexical_lookalike_is_valid_but_not_equal_to_canonical_repo(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        stack_file = root / "stack.yaml"

        canonical = declared_stack_coordinate(stack_file, "repos/trove", label="repo")
        lookalike = declared_stack_coordinate(stack_file, "repos/trove-archive", label="repo")

        self.assertEqual("repos/trove", canonical)
        self.assertEqual("repos/trove-archive", lookalike)
        self.assertNotEqual(canonical, lookalike)

    def test_internal_validation_statuses_exclude_unmanaged_owner_lanes(self) -> None:
        self.assertTrue(repo_status_allows_internal_validation("active"))
        self.assertTrue(repo_status_allows_internal_validation("incubating"))
        self.assertFalse(repo_status_allows_internal_validation("unmanaged"))
        self.assertFalse(repo_status_allows_internal_validation("demo"))

    def test_unmanaged_repo_is_not_a_text_scan_root(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        # Resolve immediately so this test's own `root`-derived paths use
        # the same long-form path as `collect_text_scan_roots`, which
        # resolves internally via `stack_file.parent.resolve()`. On some
        # hosted CI runners (observed on GitHub Actions windows-latest)
        # the raw tempfile path is a short (8.3-style) alias that differs
        # from the resolved long form, breaking membership assertions
        # below on path form alone.
        root = Path(temp_dir.name).resolve()
        stack_file = root / "stack.yaml"
        stack_file.write_text("name: temp\n", encoding="utf-8")
        (root / "docs").mkdir(parents=True, exist_ok=True)
        unmanaged_repo = root / "repos" / "owner-app"
        unmanaged_repo.mkdir(parents=True, exist_ok=True)
        active_repo = root / "repos" / "operator"
        active_repo.mkdir(parents=True, exist_ok=True)

        roots = collect_text_scan_roots(
            root,
            {
                "repo_registry": {
                    "owner-app": {
                        "path": "repos/owner-app",
                        "status": "unmanaged",
                    },
                    "operator": {
                        "path": "repos/operator",
                        "status": "active",
                    },
                }
            },
            stack_file,
        )

        self.assertIn(active_repo, roots)
        self.assertNotIn(unmanaged_repo, roots)

    def test_env_example_variants_are_not_secret_candidates(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)

        self.assertFalse(is_repo_local_secret_candidate(root / ".env.example"))
        self.assertFalse(is_repo_local_secret_candidate(root / ".env.sample"))
        self.assertFalse(is_repo_local_secret_candidate(root / ".env.template"))
        self.assertFalse(is_repo_local_secret_candidate(root / ".env.dist"))
        self.assertFalse(is_repo_local_secret_candidate(root / ".env.local.example"))
        self.assertTrue(is_repo_local_secret_candidate(root / ".env"))
        self.assertTrue(is_repo_local_secret_candidate(root / ".env.local"))

    def test_unique_repo_root_file_iteration_deduplicates_overlapping_patterns(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        err_log = root / "tmp-dev-server.err.log"
        normal_log = root / "tmp-dev-server.log"
        err_log.write_text("err\n", encoding="utf-8")
        normal_log.write_text("log\n", encoding="utf-8")

        matches = iter_unique_repo_root_files(root, ["*.log", "*.err.log"])

        self.assertEqual(
            [
                (err_log, "*.log"),
                (normal_log, "*.log"),
            ],
            matches,
        )

    def test_tracked_clean_mutable_surface_does_not_warn(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / ".playbook").mkdir(parents=True, exist_ok=True)
        (root / ".playbook" / "repo-index.json").write_text("{}\n", encoding="utf-8")

        def git_output_side_effect(repo_path: Path, *args: str) -> tuple[int, str]:
            self.assertEqual(root, repo_path)
            if args[:2] == ("ls-files", "--"):
                return 0, ".playbook/repo-index.json\n"
            if args[:4] == ("status", "--short", "--ignored", "--untracked-files=all"):
                return 0, ""
            raise AssertionError(f"Unexpected git invocation: {args!r}")

        with patch("ops.validation.validate_stack.git_output", side_effect=git_output_side_effect):
            self.assertFalse(mutable_surface_requires_warning(root, ".playbook"))

    def test_ignored_mutable_surface_still_warns(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / ".playbook").mkdir(parents=True, exist_ok=True)
        (root / ".playbook" / "repo-index.json").write_text("{}\n", encoding="utf-8")

        def git_output_side_effect(repo_path: Path, *args: str) -> tuple[int, str]:
            self.assertEqual(root, repo_path)
            if args[:2] == ("ls-files", "--"):
                return 0, ""
            if args[:4] == ("status", "--short", "--ignored", "--untracked-files=all"):
                return 0, "!! .playbook/repo-index.json\n"
            raise AssertionError(f"Unexpected git invocation: {args!r}")

        with patch("ops.validation.validate_stack.git_output", side_effect=git_output_side_effect):
            self.assertTrue(mutable_surface_requires_warning(root, ".playbook"))

    def test_generated_state_cleanup_hook_removes_declared_residue(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "node_modules").mkdir(parents=True, exist_ok=True)
        (root / ".playbook").mkdir(parents=True, exist_ok=True)

        def runner(command: str, **kwargs: object) -> SimpleNamespace:
            self.assertEqual("npm run cleanup:repo:validation", command)
            self.assertEqual(root, kwargs.get("cwd"))
            shutil.rmtree(root / "node_modules", ignore_errors=True)
            shutil.rmtree(root / ".playbook", ignore_errors=True)
            return SimpleNamespace(returncode=0, stdout="removed node_modules and .playbook\n", stderr="")

        findings = apply_repo_generated_state_cleanup(
            repo_id="fitness",
            repo_path=root,
            repo_rel="repos/fawxzzy-fitness",
            repo_info={
                "validation": {
                    "generated_state_cleanup": {
                        "command": "npm run cleanup:repo:validation",
                        "paths": ["node_modules", ".playbook"],
                    }
                }
            },
            run_command=runner,
        )

        cleanup_findings, suppressed_paths = findings
        self.assertEqual([], cleanup_findings)
        self.assertEqual(set(), suppressed_paths)
        self.assertFalse((root / "node_modules").exists())
        self.assertFalse((root / ".playbook").exists())
        self.assertEqual({}, mutable_surface_warning_map(root))

    def test_generated_state_cleanup_hook_skips_when_declared_paths_absent(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        calls: list[str] = []

        def runner(command: str, **kwargs: object) -> SimpleNamespace:
            calls.append(command)
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        findings = apply_repo_generated_state_cleanup(
            repo_id="fitness",
            repo_path=root,
            repo_rel="repos/fawxzzy-fitness",
            repo_info={
                "validation": {
                    "generated_state_cleanup": {
                        "command": "npm run cleanup:repo:validation",
                        "paths": ["node_modules", ".next"],
                    }
                }
            },
            run_command=runner,
        )

        cleanup_findings, suppressed_paths = findings
        self.assertEqual([], cleanup_findings)
        self.assertEqual(set(), suppressed_paths)
        self.assertEqual([], calls)

    def test_generated_state_cleanup_hook_can_reuse_report_without_mutating_repo(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "node_modules").mkdir(parents=True, exist_ok=True)
        report_path = root / "cleanup-report.json"
        report_path.write_text(
            """{
  "retained_paths": [
    {
      "path": "node_modules",
      "suppress_validation_warning": true
    }
  ]
}
""",
            encoding="utf-8",
        )
        calls: list[str] = []

        cleanup_findings, suppressed_paths = apply_repo_generated_state_cleanup(
            repo_id="playbook",
            repo_path=root,
            repo_rel="repos/playbook",
            repo_info={
                "validation": {
                    "generated_state_cleanup": {
                        "command": "npm run cleanup:repo:validation",
                        "report_path": "cleanup-report.json",
                        "paths": ["node_modules"],
                    }
                }
            },
            execute=False,
            run_command=lambda command, **_kwargs: calls.append(command),
        )

        self.assertEqual([], cleanup_findings)
        self.assertEqual({"node_modules"}, suppressed_paths)
        self.assertEqual([], calls)
        self.assertTrue((root / "node_modules").exists())

    def test_generated_state_cleanup_hook_reports_failure(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / ".next").mkdir(parents=True, exist_ok=True)

        findings = apply_repo_generated_state_cleanup(
            repo_id="fitness",
            repo_path=root,
            repo_rel="repos/fawxzzy-fitness",
            repo_info={
                "validation": {
                    "generated_state_cleanup": {
                        "command": "npm run cleanup:repo:validation",
                        "paths": [".next"],
                    }
                }
            },
            run_command=lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="", stderr="cleanup failed"),
        )

        cleanup_findings, suppressed_paths = findings
        self.assertEqual(set(), suppressed_paths)
        self.assertEqual(1, len(cleanup_findings))
        self.assertEqual("generated-state-cleanup-failed", cleanup_findings[0].category)
        self.assertEqual("fitness", cleanup_findings[0].details["repo_id"])
        self.assertEqual("cleanup failed", cleanup_findings[0].details["stderr_excerpt"])
        self.assertTrue((root / ".next").exists())

    def test_generated_state_cleanup_report_suppresses_declared_active_lock_paths(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        # Mirror the real stack-root layout (`<root>/repos/<owner-repo>`)
        # instead of treating the bare tempdir as the repo path directly.
        # `report_path` below is declared "../../runtime/..." relative to
        # the repo path by design (mirroring the real two-levels-deep
        # `repos/<owner>-<name>` nesting under the stack root) — walking
        # that from an un-nested tempdir root previously escaped outside
        # the sandboxed temp directory entirely (e.g. to "/runtime" on
        # Linux), which failed with a real PermissionError on hosted CI
        # (observed on GitHub Actions ubuntu-latest) even though it
        # happened to be silently tolerated on this dev machine.
        sandbox = Path(temp_dir.name).resolve()
        root = sandbox / "repos" / "fawxzzy-fitness"
        root.mkdir(parents=True, exist_ok=True)
        (root / "node_modules").mkdir(parents=True, exist_ok=True)
        report_path = root / ".." / ".." / "runtime" / "state" / "repo-cleanup" / "fitness.validation.latest.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            """{
  "contract_version": "atlas.repo.generated-state-cleanup.report.v1",
  "status": "retained_active_lock",
  "retained_paths": [
    {
      "path": "node_modules",
      "reason": "active_lock",
      "suppress_validation_warning": true
    }
  ]
}
""",
            encoding="utf-8",
        )

        findings = apply_repo_generated_state_cleanup(
            repo_id="fitness",
            repo_path=root,
            repo_rel="repos/fawxzzy-fitness",
            repo_info={
                "validation": {
                    "generated_state_cleanup": {
                        "command": "npm run cleanup:repo:validation",
                        "report_path": "../../runtime/state/repo-cleanup/fitness.validation.latest.json",
                        "paths": ["node_modules"],
                    }
                }
            },
            run_command=lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
        )

        cleanup_findings, suppressed_paths = findings
        self.assertEqual([], cleanup_findings)
        self.assertEqual({"node_modules"}, suppressed_paths)
        def git_output_side_effect(repo_path: Path, *args: str) -> tuple[int, str]:
            self.assertEqual(root, repo_path)
            if args[:2] == ("ls-files", "--"):
                return 0, ""
            if args[:4] == ("status", "--short", "--ignored", "--untracked-files=all"):
                return 0, "?? node_modules/native-addon.node\n"
            raise AssertionError(f"Unexpected git invocation: {args!r}")

        with patch("ops.validation.validate_stack.git_output", side_effect=git_output_side_effect):
            self.assertEqual(
                {"node_modules": False},
                mutable_surface_warning_map(root, suppressed_paths=suppressed_paths),
            )


if __name__ == "__main__":
    unittest.main()
