from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from ops.stack.generate_lockfile import (
    build_lock_payload,
    build_source_pins,
    normalize_lock_payload,
)


class StackGenerateLockfileSourcePinsTests(unittest.TestCase):
    """Covers `source_pins` — the deterministic, purely-local-git-evidence
    half of the generator's coverage for repos that are deliberately
    excluded from stack.lock.yaml's governed components/include_repo_ids set
    (e.g. unmanaged application repos such as Fitness/Mazer).

    `source_pins[repo_id]` (path/remote/ref_type/ref/commit/dirty) is read
    directly from the repo's local checkout via `git rev-parse`/`git
    status`/etc. and is reproducible byte-for-byte by anyone running this
    against the same local checkout state, with or without network access.
    It is part of `stack.lock.yaml` and covered by `lock_digest`.

    The live, `git ls-remote`-derived "does this repo's local commit line up
    with a remote ref" observation is a structurally SEPARATE concern named
    `remote_ref_alignment`, produced by a different function
    (`build_remote_ref_alignment_report` / `build_remote_ref_alignment_payload`)
    into a wholly different, explicitly-mutable, non-digest-guarded file
    (`stack.remote-ref-alignment.yaml`). `build_lock_payload` never calls
    that function, and `normalize_lock_payload` never reads its output — see
    `tests/test_stack_remote_ref_alignment.py` for that coverage, including
    the tests proving network unavailability and remote-branch movement
    cannot change `source_pins` or `lock_digest`.
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
        self.assertEqual(1, first["source_pin_count"])

        # The lock payload carries no remote-derived fields or keys at all —
        # not renamed, not nested, not present under any key.
        self.assertNotIn("production_commit", first["source_pins"]["fitness"])
        self.assertNotIn("production_promotion_status", first["source_pins"]["fitness"])
        self.assertNotIn("remote_commit", first["source_pins"]["fitness"])
        self.assertNotIn("alignment_status", first["source_pins"]["fitness"])
        self.assertNotIn("deployment_promotion_probes", first)
        self.assertNotIn("deployment_promotion_probe_count", first)
        self.assertNotIn("remote_ref_alignment", first)
        self.assertNotIn("remote_ref_alignment_count", first)
        self.assertEqual(
            {"path", "remote", "ref_type", "ref", "commit", "dirty"},
            set(first["source_pins"]["fitness"]),
        )

    def test_source_pin_reflects_real_dirty_worktree_evidence(self) -> None:
        repo_path = self._init_repo("repos/fitness")
        self._commit(repo_path, "fixture commit")
        config = self._config(source_pin_repo_ids=["fitness"], repo_paths={"fitness": "repos/fitness"})

        clean_payload = build_lock_payload(config=config, root=self.root)
        self.assertFalse(clean_payload["source_pins"]["fitness"]["dirty"])

        (repo_path / "untracked.txt").write_text("dirty", encoding="utf-8")
        dirty_payload = build_lock_payload(config=config, root=self.root)
        self.assertTrue(dirty_payload["source_pins"]["fitness"]["dirty"])

    def test_build_source_pins_never_invokes_git_ls_remote(self) -> None:
        """Structural proof, not just an outcome check: patch git_output to
        raise on any `ls-remote` invocation and confirm build_source_pins
        (and by extension build_lock_payload) never reaches it."""
        repo_path = self._init_repo("repos/fitness")
        self._commit(repo_path, "fixture commit")
        config = self._config(source_pin_repo_ids=["fitness"], repo_paths={"fitness": "repos/fitness"})

        from ops.stack import generate_lockfile as module

        real_git_output = module.git_output

        def guarded_git_output(repo_path_arg, *args):
            if args and args[0] == "ls-remote":
                raise AssertionError("build_source_pins must never call `git ls-remote`.")
            return real_git_output(repo_path_arg, *args)

        with patch("ops.stack.generate_lockfile.git_output", side_effect=guarded_git_output):
            pins = build_source_pins(config, self.root)
            payload = build_lock_payload(config=config, root=self.root)

        self.assertIn("fitness", pins)
        self.assertIn("fitness", payload["source_pins"])

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

    def test_normalize_lock_payload_ignores_legacy_deployment_promotion_probes_key(self) -> None:
        """A lockfile written by an earlier pass of this generator (or by any
        other caller) might still carry a `deployment_promotion_probes` key.
        normalize_lock_payload must never read it back into `body` — proving
        that even if network-derived data is *present* in an input payload,
        it cannot reach `lock_digest`."""
        payload_without_probes = {
            "schema_version": "atlas.stack.lock.v1",
            "stack_manifest_path": "stack.yaml",
            "stack_manifest_digest": "sha256:deadbeef",
            "components": {},
            "excluded_surfaces": {},
            "source_pins": {
                "mazer": {
                    "path": "repos/mazer",
                    "remote": "https://example.invalid/mazer.git",
                    "ref_type": "branch",
                    "ref": "main",
                    "commit": "a" * 40,
                    "dirty": False,
                }
            },
        }
        payload_with_legacy_probes = {
            **payload_without_probes,
            "deployment_promotion_probes": {
                "mazer": {
                    "production_ref": "main",
                    "production_commit": "b" * 40,
                    "production_promotion_status": "promoted_verified_clean",
                }
            },
        }

        clean = normalize_lock_payload(payload_without_probes)
        contaminated = normalize_lock_payload(payload_with_legacy_probes)

        self.assertNotIn("deployment_promotion_probes", clean)
        self.assertNotIn("deployment_promotion_probes", contaminated)
        self.assertEqual(clean["lock_digest"], contaminated["lock_digest"])
        self.assertEqual(clean, contaminated)


if __name__ == "__main__":
    unittest.main()
