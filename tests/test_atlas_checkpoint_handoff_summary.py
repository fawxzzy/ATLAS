from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.atlas.checkpoint_handoff_summary import build_summary, main, render_markdown


class AtlasCheckpointHandoffSummaryTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return Path(temp_dir.name)

    def _git_runner(self, command_map: dict[tuple[str, ...], str]):
        def runner(root: Path, *args: str) -> str:
            key = tuple(args)
            if key not in command_map:
                raise AssertionError(f"Unexpected git command: {key}")
            return command_map[key]

        return runner

    def test_build_summary_classifies_receipts_helpers_and_book_files(self) -> None:
        root = self._temp_root()
        git_runner = self._git_runner(
            {
                ("rev-parse", "--verify", "base"): "1111111111111111111111111111111111111111\n",
                ("rev-parse", "--verify", "HEAD"): "2222222222222222222222222222222222222222\n",
                ("log", "-1", "--format=%s", "1111111111111111111111111111111111111111"): "Base commit\n",
                ("log", "-1", "--format=%s", "2222222222222222222222222222222222222222"): "Head commit\n",
                (
                    "log",
                    "--format=%H%x1f%s",
                    "1111111111111111111111111111111111111111..2222222222222222222222222222222222222222",
                ): (
                    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\x1fAdd helper\n"
                    "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\x1fRefresh docs\n"
                ),
                (
                    "diff",
                    "--name-only",
                    "1111111111111111111111111111111111111111..2222222222222222222222222222222222222222",
                ): (
                    "ops/atlas/checkpoint_handoff_summary.py\n"
                    "tests/test_atlas_checkpoint_handoff_summary.py\n"
                    "docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-CHECKPOINT-HANDOFF-SUMMARY-HELPER-2026-06-28.md\n"
                    "docs/atlas-book/01-current-state.md\n"
                    "runtime/cortex/catalog/memory/working-memory.latest.json\n"
                ),
                ("status", "--short"): "",
            }
        )

        summary = build_summary(root=root, since_ref="base", git_runner=git_runner)

        self.assertEqual("atlas.checkpoint_handoff_summary.v1", summary["contract_version"])
        self.assertEqual(2, summary["commit_count"])
        self.assertEqual(5, summary["changed_file_count"])
        self.assertTrue(summary["worktree_clean"])
        self.assertEqual(
            ["docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-CHECKPOINT-HANDOFF-SUMMARY-HELPER-2026-06-28.md"],
            summary["categories"]["receipt_refs"],
        )
        self.assertEqual(["docs/atlas-book/01-current-state.md"], summary["categories"]["book_refs"])
        self.assertEqual(["ops/atlas/checkpoint_handoff_summary.py"], summary["categories"]["atlas_helper_refs"])
        self.assertEqual(["tests/test_atlas_checkpoint_handoff_summary.py"], summary["categories"]["test_refs"])
        self.assertEqual(
            ["runtime/cortex/catalog/memory/working-memory.latest.json"],
            summary["categories"]["runtime_refs"],
        )

    def test_render_markdown_reports_dirty_worktree(self) -> None:
        rendered = render_markdown(
            {
                "since_commit": {"ref": "base", "short_sha": "11111111", "subject": "Base"},
                "until_commit": {"ref": "HEAD", "short_sha": "22222222", "subject": "Head"},
                "commit_count": 0,
                "changed_file_count": 0,
                "worktree_clean": False,
                "worktree_status": [" M docs/atlas-book/01-current-state.md"],
                "commits": [],
                "categories": {key: [] for key in ("receipt_refs", "book_refs", "atlas_helper_refs", "stack_helper_refs", "test_refs", "runtime_refs", "other_refs")},
            }
        )

        self.assertIn("- worktree: `dirty`", rendered)
        self.assertIn("- ` M docs/atlas-book/01-current-state.md`", rendered)
        self.assertIn("- no commits in range", rendered)

    def test_main_writes_json_output(self) -> None:
        root = self._temp_root()

        def fake_build_summary(*, root: Path, since_ref: str, until_ref: str = "HEAD", git_runner=None):
            self.assertEqual("base", since_ref)
            self.assertEqual("HEAD", until_ref)
            return {
                "contract_version": "atlas.checkpoint_handoff_summary.v1",
                "since_commit": {"ref": "base", "sha": "1" * 40, "short_sha": "11111111", "subject": "Base"},
                "until_commit": {"ref": "HEAD", "sha": "2" * 40, "short_sha": "22222222", "subject": "Head"},
                "commit_count": 1,
                "changed_file_count": 1,
                "worktree_clean": True,
                "worktree_status": [],
                "commits": [{"sha": "2" * 40, "short_sha": "22222222", "subject": "Head"}],
                "categories": {key: [] for key in ("receipt_refs", "book_refs", "atlas_helper_refs", "stack_helper_refs", "test_refs", "runtime_refs", "other_refs")},
            }

        output_ref = root / "tmp" / "summary.json"
        from ops.atlas import checkpoint_handoff_summary as module

        original = module.build_summary
        module.build_summary = fake_build_summary
        try:
            exit_code = main(["--root", str(root), "--since-ref", "base", "--format", "json", "--output", str(output_ref)])
        finally:
            module.build_summary = original

        self.assertEqual(0, exit_code)
        payload = json.loads(output_ref.read_text(encoding="utf-8"))
        self.assertEqual("atlas.checkpoint_handoff_summary.v1", payload["contract_version"])
        self.assertEqual(1, payload["commit_count"])


if __name__ == "__main__":
    unittest.main()
