from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ops.validation.validate_stack import (
    is_repo_local_secret_candidate,
    iter_unique_repo_root_files,
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


if __name__ == "__main__":
    unittest.main()
