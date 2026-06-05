from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ops.validation.validate_stack import (
    is_repo_local_secret_candidate,
    iter_unique_repo_root_files,
    mutable_surface_requires_warning,
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


if __name__ == "__main__":
    unittest.main()
