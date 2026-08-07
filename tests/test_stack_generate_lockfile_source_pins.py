from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from ops.stack.generate_lockfile import (
    PROMOTION_STATUS_NOT_CONFIGURED,
    PROMOTION_STATUS_NOT_PROMOTED,
    PROMOTION_STATUS_PROMOTED_DIRTY_WORKTREE,
    PROMOTION_STATUS_PROMOTED_VERIFIED_CLEAN,
    build_lock_payload,
    build_source_pins,
)


class StackGenerateLockfileSourcePinsTests(unittest.TestCase):
    """Covers the generator's source_pins mechanism for repos that are
    deliberately excluded from stack.lock.yaml's governed
    components/include_repo_ids set (e.g. unmanaged application repos such
    as Fitness/Mazer) but still need real, git-evidence-backed source-commit
    and production-promotion identity captured into the same
    digest-guarded stack.lock.yaml output, instead of being hand-typed into
    stack.yaml.
    """

    def setUp(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.root = Path(temp_dir.name)

    @staticmethod
    def _run_git(repo_path: Path, *args: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(repo_path), *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return completed.stdout.strip()

    def _init_repo(self, relative_path: str, *, initial_branch: str = "main") -> Path:
        repo_path = self.root / relative_path
        repo_path.mkdir(parents=True)
        self._run_git(repo_path, "init", "--quiet", f"--initial-branch={initial_branch}")
        self._run_git(repo_path, "config", "user.name", "ATLAS Test")
        self._run_git(repo_path, "config", "user.email", "atlas-test@example.invalid")
        return repo_path

    def _commit(self, repo_path: Path, message: str) -> str:
        self._run_git(repo_path, "commit", "--quiet", "--allow-empty", "-m", message)
        return self._run_git(repo_path, "rev-parse", "HEAD")

    @staticmethod
    def _config(
        *,
        source_pin_repo_ids: list[str],
        repo_paths: dict[str, str],
        repo_overrides: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        registry = {
            repo_id: {"path": path, "role": "application", "status": "unmanaged"}
            for repo_id, path in repo_paths.items()
        }
        return {
            "repo_registry": registry,
            "stack_lock": {
                "path": "stack.lock.yaml",
                "source_pin_repo_ids": source_pin_repo_ids,
                "repo_overrides": repo_overrides or {},
            },
        }

    # -- Determinism: running the generator twice against the same real
    # git evidence must produce byte-identical, digest-identical output. --

    def test_source_pins_are_deterministic_across_runs(self) -> None:
        repo_path = self._init_repo("repos/fitness")
        commit = self._commit(repo_path, "fixture commit")
        config = self._config(source_pin_repo_ids=["fitness"], repo_paths={"fitness": "repos/fitness"})

        first = build_lock_payload(config=config, root=self.root)
        second = build_lock_payload(config=config, root=self.root)

        self.assertEqual(first, second)
        self.assertEqual(first["lock_digest"], second["lock_digest"])
        self.assertEqual(commit, first["source_pins"]["fitness"]["commit"])
        self.assertFalse(first["source_pins"]["fitness"]["dirty"])
        self.assertEqual(
            PROMOTION_STATUS_NOT_CONFIGURED,
            first["source_pins"]["fitness"]["production_promotion_status"],
        )
        self.assertIsNone(first["source_pins"]["fitness"]["production_commit"])

    def test_source_pin_reflects_real_dirty_worktree_evidence(self) -> None:
        repo_path = self._init_repo("repos/fitness")
        self._commit(repo_path, "fixture commit")
        config = self._config(source_pin_repo_ids=["fitness"], repo_paths={"fitness": "repos/fitness"})

        clean_payload = build_lock_payload(config=config, root=self.root)
        self.assertFalse(clean_payload["source_pins"]["fitness"]["dirty"])

        (repo_path / "untracked.txt").write_text("dirty", encoding="utf-8")
        dirty_payload = build_lock_payload(config=config, root=self.root)
        self.assertTrue(dirty_payload["source_pins"]["fitness"]["dirty"])

    # -- Production-promotion status derived from a real `git ls-remote`
    # against the repo's own configured remote (no fabricated Vercel call,
    # no network dependency in the test: the "remote" is a real local bare
    # git repo, so ls-remote is a genuine git evidence-gathering call). --

    def test_production_promotion_status_promoted_verified_clean(self) -> None:
        remote_path = self.root / "remote-mazer.git"
        subprocess.run(["git", "init", "--quiet", "--bare", str(remote_path)], check=True)

        repo_path = self._init_repo("repos/mazer")
        commit = self._commit(repo_path, "production commit")
        self._run_git(repo_path, "remote", "add", "origin", str(remote_path))
        self._run_git(repo_path, "push", "--quiet", "origin", "main")

        config = self._config(
            source_pin_repo_ids=["mazer"],
            repo_paths={"mazer": "repos/mazer"},
            repo_overrides={"mazer": {"production_promotion_ref": "main"}},
        )
        pins = build_source_pins(config, self.root)

        self.assertEqual(PROMOTION_STATUS_PROMOTED_VERIFIED_CLEAN, pins["mazer"]["production_promotion_status"])
        self.assertEqual(commit, pins["mazer"]["production_commit"])
        self.assertEqual(commit, pins["mazer"]["commit"])

    def test_production_promotion_status_not_promoted_when_local_diverges(self) -> None:
        remote_path = self.root / "remote-mazer.git"
        subprocess.run(["git", "init", "--quiet", "--bare", str(remote_path)], check=True)

        repo_path = self._init_repo("repos/mazer")
        production_commit = self._commit(repo_path, "production commit")
        self._run_git(repo_path, "remote", "add", "origin", str(remote_path))
        self._run_git(repo_path, "push", "--quiet", "origin", "main")

        self._run_git(repo_path, "checkout", "--quiet", "-b", "feature")
        local_commit = self._commit(repo_path, "feature work not yet promoted to production main")

        config = self._config(
            source_pin_repo_ids=["mazer"],
            repo_paths={"mazer": "repos/mazer"},
            repo_overrides={"mazer": {"production_promotion_ref": "main"}},
        )
        pins = build_source_pins(config, self.root)

        self.assertNotEqual(local_commit, production_commit)
        self.assertEqual(PROMOTION_STATUS_NOT_PROMOTED, pins["mazer"]["production_promotion_status"])
        self.assertEqual(local_commit, pins["mazer"]["commit"])
        self.assertEqual(production_commit, pins["mazer"]["production_commit"])

    def test_production_promotion_status_promoted_dirty_worktree(self) -> None:
        remote_path = self.root / "remote-mazer.git"
        subprocess.run(["git", "init", "--quiet", "--bare", str(remote_path)], check=True)

        repo_path = self._init_repo("repos/mazer")
        commit = self._commit(repo_path, "production commit")
        self._run_git(repo_path, "remote", "add", "origin", str(remote_path))
        self._run_git(repo_path, "push", "--quiet", "origin", "main")
        (repo_path / "wip.txt").write_text("local edit", encoding="utf-8")

        config = self._config(
            source_pin_repo_ids=["mazer"],
            repo_paths={"mazer": "repos/mazer"},
            repo_overrides={"mazer": {"production_promotion_ref": "main"}},
        )
        pins = build_source_pins(config, self.root)

        self.assertEqual(PROMOTION_STATUS_PROMOTED_DIRTY_WORKTREE, pins["mazer"]["production_promotion_status"])
        self.assertEqual(commit, pins["mazer"]["production_commit"])

    # -- Feed a known SHA (via a mocked git backend that stands in for the
    # subprocess boundary only) and assert the exact expected rendered
    # source pin, matching the real evidence observed against the actual
    # fawxzzy/mazer repo at the time this generator extension was written:
    # a feature-branch HEAD that has not yet reached remote main. --

    def test_known_commit_sha_produces_exact_expected_source_pin(self) -> None:
        known_local_sha = "a537d2d17429bdf0482989c280373a6ea751f9c0"
        known_production_sha = "4c61943eb4c8b4e98a5cbb9054f3c927bb724950"

        def fake_git_output(repo_path: Path, *args: str) -> tuple[int, str]:
            if args == ("rev-parse", "HEAD"):
                return 0, known_local_sha
            if args == ("symbolic-ref", "--quiet", "--short", "HEAD"):
                return 0, "codex/player-goal-default-colors"
            if args == ("describe", "--tags", "--exact-match"):
                return 1, ""
            if args == ("remote", "get-url", "origin"):
                return 0, "https://github.com/fawxzzy/mazer.git"
            if args == ("remote",):
                return 0, "origin"
            if args == ("status", "--porcelain=v1", "--untracked-files=all"):
                return 0, " M docs/architecture.md"
            if args == ("ls-remote", "--exit-code", "origin", "refs/heads/main"):
                return 0, f"{known_production_sha}\trefs/heads/main"
            raise AssertionError(f"Unexpected git invocation: {args!r}")

        repo_path = self.root / "repos" / "mazer"
        repo_path.mkdir(parents=True)
        (repo_path / ".git").mkdir()

        config = self._config(
            source_pin_repo_ids=["mazer"],
            repo_paths={"mazer": "repos/mazer"},
            repo_overrides={"mazer": {"production_promotion_ref": "main"}},
        )

        with patch("ops.stack.generate_lockfile.git_output", side_effect=fake_git_output):
            pins = build_source_pins(config, self.root)

        self.assertEqual(
            {
                "path": "repos/mazer",
                "remote": "https://github.com/fawxzzy/mazer.git",
                "ref_type": "branch",
                "ref": "codex/player-goal-default-colors",
                "commit": known_local_sha,
                "dirty": True,
                "production_ref": "main",
                "production_commit": known_production_sha,
                "production_promotion_status": PROMOTION_STATUS_NOT_PROMOTED,
            },
            pins["mazer"],
        )

    def test_source_pins_do_not_alter_governed_component_set(self) -> None:
        fitness_path = self._init_repo("repos/fitness")
        self._commit(fitness_path, "fitness fixture commit")
        governed_path = self._init_repo("repos/foundation")
        self._commit(governed_path, "foundation fixture commit")

        config = {
            "repo_registry": {
                "fitness": {"path": "repos/fitness", "role": "application", "status": "unmanaged"},
                "foundation": {"path": "repos/foundation", "role": "shared-contract-foundation", "status": "active"},
            },
            "stack_lock": {
                "path": "stack.lock.yaml",
                "include_repo_ids": ["foundation"],
                "source_pin_repo_ids": ["fitness"],
            },
        }
        payload = build_lock_payload(config=config, root=self.root)

        self.assertIn("foundation", payload["components"])
        self.assertNotIn("fitness", payload["components"])
        self.assertIn("fitness", payload["source_pins"])
        self.assertEqual(1, payload["component_count"])
        self.assertEqual(1, payload["source_pin_count"])


if __name__ == "__main__":
    unittest.main()
