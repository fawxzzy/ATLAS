from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from ops.stack import generate_lockfile as module


class MainRemoteRefAlignmentResilienceTests(unittest.TestCase):
    """`main()` writes the digest-guarded `stack.lock.yaml` first, then
    performs a best-effort `remote_ref_alignment` step as a separate,
    non-digest-guarded artifact. That second step must never be able to
    turn a *successful* lockfile write into an unhandled crash/traceback —
    it should degrade to a reported failure summary instead, exactly like a
    per-repo `git ls-remote` failure already degrades to
    `ALIGNMENT_STATUS_UNKNOWN`/`ALIGNMENT_UNAVAILABLE_REASON_REMOTE_UNREACHABLE`.
    """

    def setUp(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.root = Path(temp_dir.name)
        self.stack_file = self.root / "stack.yaml"
        self.stack_file.write_text(
            yaml.safe_dump(
                {
                    "repo_registry": {},
                    "stack_lock": {"path": "stack.lock.yaml"},
                }
            ),
            encoding="utf-8",
        )
        self.output_path = self.root / "stack.lock.yaml"

    def _run_main(self, argv_tail: list[str]) -> tuple[int, str]:
        argv = ["generate_lockfile.py", "--stack-file", str(self.stack_file), *argv_tail]
        stdout = io.StringIO()
        with patch("sys.argv", argv), contextlib.redirect_stdout(stdout):
            exit_code = module.main()
        return exit_code, stdout.getvalue()

    def test_unexpected_exception_in_alignment_step_does_not_crash_main(self) -> None:
        """The core proof: patch the alignment-artifact builder to raise an
        arbitrary, unexpected exception (not a git failure — a genuine bug
        or environment surprise) and confirm `main()` still returns cleanly
        (no exception propagates out of `main()`) with `stack.lock.yaml`
        already written to disk beforehand."""
        self.assertFalse(self.output_path.exists())

        with patch.object(
            module,
            "build_canonical_remote_ref_alignment_artifacts",
            side_effect=RuntimeError("simulated unexpected failure"),
        ):
            try:
                exit_code, stdout_text = self._run_main([])
            except Exception as error:  # pragma: no cover - the failure this test guards against
                self.fail(
                    "main() must not let an exception from the remote-ref-alignment "
                    f"step escape unhandled; got {type(error).__name__}: {error}"
                )

        self.assertEqual(0, exit_code)
        self.assertTrue(self.output_path.exists(), "stack.lock.yaml must still be written on disk")

        written_payload = yaml.safe_load(self.output_path.read_text(encoding="utf-8"))
        self.assertIn("lock_digest", written_payload)

        summary = json.loads(stdout_text)
        self.assertIn("error", summary["remote_ref_alignment"])
        self.assertIn("simulated unexpected failure", summary["remote_ref_alignment"]["error"])
        self.assertIsNotNone(summary["lock_digest"])

    def test_hung_ls_remote_during_main_degrades_cleanly_not_a_stall_or_crash(self) -> None:
        """End-to-end version of the timeout guarantee: a source-pinned repo
        whose `git ls-remote` genuinely hangs must not stall or crash
        `main()`; the run completes, `stack.lock.yaml` is written, and the
        alignment summary reflects a completed (not hung) run."""
        repo_path = self.root / "repos" / "mazer"
        repo_path.mkdir(parents=True)
        subprocess.run(["git", "init", "--quiet", "--initial-branch=main", str(repo_path)], check=True)
        subprocess.run(["git", "-C", str(repo_path), "config", "user.name", "ATLAS Test"], check=True)
        subprocess.run(["git", "-C", str(repo_path), "config", "user.email", "atlas-test@example.invalid"], check=True)
        subprocess.run(
            ["git", "-C", str(repo_path), "commit", "--quiet", "--allow-empty", "-m", "fixture"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(repo_path), "remote", "add", "origin", "https://example.invalid/does-not-matter.git"],
            check=True,
        )
        self.stack_file.write_text(
            yaml.safe_dump(
                {
                    "repo_registry": {"mazer": {"path": "repos/mazer", "role": "application", "status": "unmanaged"}},
                    "stack_lock": {
                        "path": "stack.lock.yaml",
                        "source_pin_repo_ids": ["mazer"],
                        "repo_overrides": {"mazer": {"remote_ref_alignment_ref": "main"}},
                    },
                }
            ),
            encoding="utf-8",
        )

        real_subprocess_run = subprocess.run

        def hang_only_on_ls_remote(cmd, *args, **kwargs):
            if isinstance(cmd, (list, tuple)) and "ls-remote" in cmd:
                raise subprocess.TimeoutExpired(cmd=cmd, timeout=kwargs.get("timeout"))
            return real_subprocess_run(cmd, *args, **kwargs)

        with patch("ops.stack.generate_lockfile.subprocess.run", side_effect=hang_only_on_ls_remote):
            try:
                exit_code, stdout_text = self._run_main([])
            except Exception as error:  # pragma: no cover - the failure this test guards against
                self.fail(f"main() must not hang or crash on a timed-out ls-remote; got {type(error).__name__}: {error}")

        self.assertEqual(0, exit_code)
        self.assertTrue(self.output_path.exists())
        summary = json.loads(stdout_text)
        self.assertEqual(1, summary["remote_ref_alignment"]["remote_ref_alignment_count"])


if __name__ == "__main__":
    unittest.main()
