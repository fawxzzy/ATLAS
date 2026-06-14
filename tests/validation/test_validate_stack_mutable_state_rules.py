from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ops.validation.validate_stack import (
    apply_repo_generated_state_cleanup,
    is_repo_local_secret_candidate,
    iter_unique_repo_root_files,
    mutable_surface_requires_warning,
    mutable_surface_warning_map,
)


class ValidateStackMutableStateRulesTests(unittest.TestCase):
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
        root = Path(temp_dir.name)
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
