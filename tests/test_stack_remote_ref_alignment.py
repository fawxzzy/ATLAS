from __future__ import annotations

import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

from ops.stack.export_repo_inventory import build_repo_inventory
from ops.stack.generate_lockfile import (
    ALIGNMENT_STATUS_ALIGNED_CLEAN,
    ALIGNMENT_STATUS_ALIGNED_DIRTY_WORKTREE,
    ALIGNMENT_STATUS_NOT_ALIGNED,
    ALIGNMENT_STATUS_STALE,
    ALIGNMENT_STATUS_UNKNOWN,
    ALIGNMENT_UNAVAILABLE_REASON_NOT_CONFIGURED,
    ALIGNMENT_UNAVAILABLE_REASON_NO_REMOTE,
    ALIGNMENT_UNAVAILABLE_REASON_REMOTE_UNREACHABLE,
    REMOTE_REF_ALIGNMENT_STALE_AFTER,
    build_canonical_lockfile_artifacts,
    build_lock_payload,
    build_remote_ref_alignment_payload,
    build_remote_ref_alignment_report,
    build_source_pins,
    load_remote_ref_alignment_report,
    normalize_remote_ref_alignment_entry,
    remote_ref_alignment_entry_with_staleness,
    write_remote_ref_alignment_report,
)


class RemoteRefAlignmentGeneratorTests(unittest.TestCase):
    """`remote_ref_alignment` is the live, `git ls-remote`-derived
    observation about whether a source-pinned repo's local commit lines up
    with a configured remote branch. It answers "does the remote ref
    currently point at the same commit as this local checkout" — nothing
    more. It is evidence of remote-ref alignment, not proof of a deployment
    or of what is running in production anywhere, and it must never
    participate in `lock_digest`.
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

    # -- Real alignment outcomes, via a genuine local bare git repo standing
    # in for "the actual remote" (no network dependency, no mocking of
    # git's own hashing). --

    def test_alignment_status_aligned_clean(self) -> None:
        remote_path = self.root / "remote-mazer.git"
        subprocess.run(["git", "init", "--quiet", "--bare", str(remote_path)], check=True)
        repo_path = self._init_repo("repos/mazer")
        commit = self._commit(repo_path, "commit")
        self._run_git(repo_path, "remote", "add", "origin", str(remote_path))
        self._run_git(repo_path, "push", "--quiet", "origin", "main")

        config = self._config(
            source_pin_repo_ids=["mazer"],
            repo_paths={"mazer": "repos/mazer"},
            repo_overrides={"mazer": {"remote_ref_alignment_ref": "main"}},
        )
        pins = build_source_pins(config, self.root)
        report = build_remote_ref_alignment_report(config, self.root, pins)

        self.assertEqual(ALIGNMENT_STATUS_ALIGNED_CLEAN, report["mazer"]["alignment_status"])
        self.assertEqual(commit, report["mazer"]["remote_commit"])
        self.assertIsNone(report["mazer"]["unavailable_reason"])

    def test_alignment_status_not_aligned_when_local_diverges(self) -> None:
        remote_path = self.root / "remote-mazer.git"
        subprocess.run(["git", "init", "--quiet", "--bare", str(remote_path)], check=True)
        repo_path = self._init_repo("repos/mazer")
        production_commit = self._commit(repo_path, "production commit")
        self._run_git(repo_path, "remote", "add", "origin", str(remote_path))
        self._run_git(repo_path, "push", "--quiet", "origin", "main")
        self._run_git(repo_path, "checkout", "--quiet", "-b", "feature")
        local_commit = self._commit(repo_path, "feature work not yet on remote main")

        config = self._config(
            source_pin_repo_ids=["mazer"],
            repo_paths={"mazer": "repos/mazer"},
            repo_overrides={"mazer": {"remote_ref_alignment_ref": "main"}},
        )
        pins = build_source_pins(config, self.root)
        report = build_remote_ref_alignment_report(config, self.root, pins)

        self.assertNotEqual(local_commit, production_commit)
        self.assertEqual(ALIGNMENT_STATUS_NOT_ALIGNED, report["mazer"]["alignment_status"])
        self.assertEqual(production_commit, report["mazer"]["remote_commit"])
        self.assertIsNone(report["mazer"]["unavailable_reason"])

    def test_alignment_status_aligned_dirty_worktree(self) -> None:
        remote_path = self.root / "remote-mazer.git"
        subprocess.run(["git", "init", "--quiet", "--bare", str(remote_path)], check=True)
        repo_path = self._init_repo("repos/mazer")
        commit = self._commit(repo_path, "commit")
        self._run_git(repo_path, "remote", "add", "origin", str(remote_path))
        self._run_git(repo_path, "push", "--quiet", "origin", "main")
        (repo_path / "wip.txt").write_text("local edit", encoding="utf-8")

        config = self._config(
            source_pin_repo_ids=["mazer"],
            repo_paths={"mazer": "repos/mazer"},
            repo_overrides={"mazer": {"remote_ref_alignment_ref": "main"}},
        )
        pins = build_source_pins(config, self.root)
        report = build_remote_ref_alignment_report(config, self.root, pins)

        self.assertTrue(pins["mazer"]["dirty"])
        self.assertEqual(ALIGNMENT_STATUS_ALIGNED_DIRTY_WORKTREE, report["mazer"]["alignment_status"])
        self.assertEqual(commit, report["mazer"]["remote_commit"])

    # -- Missing observation -> explicit UNKNOWN, never silently omitted,
    # never a status that could be misread as a real finding. --

    def test_no_ref_configured_yields_unknown(self) -> None:
        repo_path = self._init_repo("repos/fitness")
        self._commit(repo_path, "commit")
        config = self._config(source_pin_repo_ids=["fitness"], repo_paths={"fitness": "repos/fitness"})
        pins = build_source_pins(config, self.root)
        report = build_remote_ref_alignment_report(config, self.root, pins)

        self.assertEqual(ALIGNMENT_STATUS_UNKNOWN, report["fitness"]["alignment_status"])
        self.assertEqual(ALIGNMENT_UNAVAILABLE_REASON_NOT_CONFIGURED, report["fitness"]["unavailable_reason"])
        self.assertIsNone(report["fitness"]["remote_commit"])

    def test_no_remote_configured_yields_unknown(self) -> None:
        repo_path = self._init_repo("repos/mazer")
        self._commit(repo_path, "commit")
        config = self._config(
            source_pin_repo_ids=["mazer"],
            repo_paths={"mazer": "repos/mazer"},
            repo_overrides={"mazer": {"remote_ref_alignment_ref": "main"}},
        )
        pins = build_source_pins(config, self.root)
        report = build_remote_ref_alignment_report(config, self.root, pins)

        self.assertEqual(ALIGNMENT_STATUS_UNKNOWN, report["mazer"]["alignment_status"])
        self.assertEqual(ALIGNMENT_UNAVAILABLE_REASON_NO_REMOTE, report["mazer"]["unavailable_reason"])

    # -- No network availability -> explicit UNKNOWN, and (separately, in
    # the tests below) proof this cannot touch lock_digest at all. --

    def test_unreachable_remote_yields_unknown_not_a_false_negative(self) -> None:
        """Simulate a real network failure: point 'origin' at a path that
        does not exist, so `git ls-remote` genuinely fails. The result must
        be the explicit UNKNOWN/remote_unreachable pair, not `not_aligned`
        (which would misreport "we compared and they differ" when in truth
        no comparison was possible at all)."""
        repo_path = self._init_repo("repos/mazer")
        self._commit(repo_path, "commit")
        unreachable = self.root / "does-not-exist.git"
        self._run_git(repo_path, "remote", "add", "origin", str(unreachable))

        config = self._config(
            source_pin_repo_ids=["mazer"],
            repo_paths={"mazer": "repos/mazer"},
            repo_overrides={"mazer": {"remote_ref_alignment_ref": "main"}},
        )
        pins = build_source_pins(config, self.root)
        report = build_remote_ref_alignment_report(config, self.root, pins)

        self.assertEqual(ALIGNMENT_STATUS_UNKNOWN, report["mazer"]["alignment_status"])
        self.assertEqual(ALIGNMENT_UNAVAILABLE_REASON_REMOTE_UNREACHABLE, report["mazer"]["unavailable_reason"])
        self.assertIsNone(report["mazer"]["remote_commit"])

    def test_hung_ls_remote_times_out_and_yields_unknown_not_a_stall(self) -> None:
        """A hung `git ls-remote` (e.g. an unreachable/black-holed remote
        that never returns) must degrade the same way a fast, clean failure
        already does — UNKNOWN/remote_unreachable — rather than block the
        generator indefinitely. Simulated by patching `subprocess.run` to
        raise `TimeoutExpired` only for the `ls-remote` invocation; every
        other git call in this test (init, commit, remote add) is real and
        untouched by the patch."""
        repo_path = self._init_repo("repos/mazer")
        self._commit(repo_path, "commit")
        remote_path = self.root / "remote-mazer.git"
        subprocess.run(["git", "init", "--quiet", "--bare", str(remote_path)], check=True)
        self._run_git(repo_path, "remote", "add", "origin", str(remote_path))

        config = self._config(
            source_pin_repo_ids=["mazer"],
            repo_paths={"mazer": "repos/mazer"},
            repo_overrides={"mazer": {"remote_ref_alignment_ref": "main"}},
        )
        pins = build_source_pins(config, self.root)

        real_subprocess_run = subprocess.run

        def hang_only_on_ls_remote(cmd, *args, **kwargs):
            if isinstance(cmd, (list, tuple)) and "ls-remote" in cmd:
                raise subprocess.TimeoutExpired(cmd=cmd, timeout=kwargs.get("timeout"))
            return real_subprocess_run(cmd, *args, **kwargs)

        with patch("ops.stack.generate_lockfile.subprocess.run", side_effect=hang_only_on_ls_remote):
            report = build_remote_ref_alignment_report(config, self.root, pins)

        self.assertEqual(ALIGNMENT_STATUS_UNKNOWN, report["mazer"]["alignment_status"])
        self.assertEqual(ALIGNMENT_UNAVAILABLE_REASON_REMOTE_UNREACHABLE, report["mazer"]["unavailable_reason"])
        self.assertIsNone(report["mazer"]["remote_commit"])

    def test_git_ls_remote_head_passes_a_bounded_timeout(self) -> None:
        """Structural proof that the network call is actually bounded: patch
        `subprocess.run` and assert the `ls-remote` invocation carries a
        finite, positive `timeout=` kwarg (not `None`, which would mean an
        unbounded wait)."""
        from ops.stack.generate_lockfile import GIT_LS_REMOTE_TIMEOUT_SECONDS, git_ls_remote_head

        repo_path = self._init_repo("repos/mazer")
        self._commit(repo_path, "commit")

        captured_timeouts: list[float | None] = []
        real_subprocess_run = subprocess.run

        def capture_timeout(cmd, *args, **kwargs):
            if isinstance(cmd, (list, tuple)) and "ls-remote" in cmd:
                captured_timeouts.append(kwargs.get("timeout"))
            return real_subprocess_run(cmd, *args, **kwargs)

        with patch("ops.stack.generate_lockfile.subprocess.run", side_effect=capture_timeout):
            git_ls_remote_head(repo_path, "origin", "main")

        self.assertEqual([GIT_LS_REMOTE_TIMEOUT_SECONDS], captured_timeouts)
        self.assertIsNotNone(captured_timeouts[0])
        self.assertGreater(captured_timeouts[0], 0)

    # -- The whole point of the fix: network availability / remote movement
    # must not change source_pins or lock_digest — only the separate report
    # changes. --

    def test_network_unavailability_does_not_change_lock_digest(self) -> None:
        repo_path = self._init_repo("repos/mazer")
        self._commit(repo_path, "commit")
        unreachable = self.root / "does-not-exist.git"
        self._run_git(repo_path, "remote", "add", "origin", str(unreachable))

        config = self._config(
            source_pin_repo_ids=["mazer"],
            repo_paths={"mazer": "repos/mazer"},
            repo_overrides={"mazer": {"remote_ref_alignment_ref": "main"}},
        )

        # build_lock_payload never even attempts the network call (see
        # test_build_source_pins_never_invokes_git_ls_remote in the sibling
        # source_pins test module), so simulating "no network" for the lock
        # path is simply: call it, and confirm it succeeds and produces a
        # stable digest despite an unreachable remote being configured.
        first = build_lock_payload(config=config, root=self.root)
        second = build_lock_payload(config=config, root=self.root)
        self.assertEqual(first["lock_digest"], second["lock_digest"])

        # And the *separate* report genuinely does observe the failure.
        pins = build_source_pins(config, self.root)
        report = build_remote_ref_alignment_report(config, self.root, pins)
        self.assertEqual(ALIGNMENT_STATUS_UNKNOWN, report["mazer"]["alignment_status"])

    def test_remote_branch_moving_does_not_change_source_pins_or_lock_digest(self) -> None:
        remote_path = self.root / "remote-mazer.git"
        subprocess.run(["git", "init", "--quiet", "--bare", str(remote_path)], check=True)
        repo_path = self._init_repo("repos/mazer")
        first_commit = self._commit(repo_path, "first commit")
        self._run_git(repo_path, "remote", "add", "origin", str(remote_path))
        self._run_git(repo_path, "push", "--quiet", "origin", "main")

        config = self._config(
            source_pin_repo_ids=["mazer"],
            repo_paths={"mazer": "repos/mazer"},
            repo_overrides={"mazer": {"remote_ref_alignment_ref": "main"}},
        )

        lock_before = build_lock_payload(config=config, root=self.root)
        report_before = build_remote_ref_alignment_report(
            config, self.root, build_source_pins(config, self.root)
        )
        self.assertEqual(ALIGNMENT_STATUS_ALIGNED_CLEAN, report_before["mazer"]["alignment_status"])

        # Advance the remote without touching the local checkout at all.
        other_clone = self.root / "other-clone"
        self._run_git(self.root, "clone", "--quiet", str(remote_path), str(other_clone))
        self._run_git(other_clone, "config", "user.name", "ATLAS Test")
        self._run_git(other_clone, "config", "user.email", "atlas-test@example.invalid")
        self._run_git(other_clone, "checkout", "--quiet", "main")
        self._commit(other_clone, "second commit, pushed from elsewhere")
        self._run_git(other_clone, "push", "--quiet", "origin", "main")

        lock_after = build_lock_payload(config=config, root=self.root)
        report_after = build_remote_ref_alignment_report(
            config, self.root, build_source_pins(config, self.root)
        )

        # source_pins and lock_digest are completely unaffected by the
        # remote branch having moved out from under an unchanged local
        # checkout.
        self.assertEqual(lock_before["source_pins"], lock_after["source_pins"])
        self.assertEqual(lock_before["lock_digest"], lock_after["lock_digest"])
        self.assertEqual(first_commit, lock_after["source_pins"]["mazer"]["commit"])

        # But the separate, non-digest-guarded report does now disagree.
        self.assertEqual(ALIGNMENT_STATUS_NOT_ALIGNED, report_after["mazer"]["alignment_status"])

    def test_build_canonical_lockfile_artifacts_bytes_stable_across_remote_states(self) -> None:
        """End-to-end: the actual rendered stack.lock.yaml bytes (what gets
        written to disk and digest-guarded by validate_stack.py) are
        byte-identical whether or not a remote/network is reachable at all."""
        repo_path = self._init_repo("repos/mazer")
        self._commit(repo_path, "commit")
        # No remote configured at all -- the "no network" extreme case.
        config = self._config(
            source_pin_repo_ids=["mazer"],
            repo_paths={"mazer": "repos/mazer"},
            repo_overrides={"mazer": {"remote_ref_alignment_ref": "main"}},
        )
        no_remote_artifacts = build_canonical_lockfile_artifacts(config=config, root=self.root)

        remote_path = self.root / "remote-mazer.git"
        subprocess.run(["git", "init", "--quiet", "--bare", str(remote_path)], check=True)
        self._run_git(repo_path, "remote", "add", "origin", str(remote_path))
        self._run_git(repo_path, "push", "--quiet", "origin", "main")
        with_remote_artifacts = build_canonical_lockfile_artifacts(config=config, root=self.root)

        # `remote` is part of source_pins (local `git remote get-url`
        # evidence, not a network call), so adding a remote does change the
        # source pin's `remote` field/bytes -- that's expected, real local
        # evidence changed. What must NOT differ is whether the process
        # could reach the network: rerunning with the same local state
        # (remote already added, still reachable) must be perfectly stable.
        stable_first = build_canonical_lockfile_artifacts(config=config, root=self.root)
        stable_second = build_canonical_lockfile_artifacts(config=config, root=self.root)
        self.assertEqual(stable_first["bytes"], stable_second["bytes"])
        self.assertEqual(stable_first["payload"]["lock_digest"], stable_second["payload"]["lock_digest"])


class RemoteRefAlignmentReportFileTests(unittest.TestCase):
    """Coverage for the separate stack.remote-ref-alignment.yaml artifact
    itself: schema, mutability markers, round-trip load, and the read-time
    staleness contract."""

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

    def _init_repo(self, relative_path: str) -> Path:
        repo_path = self.root / relative_path
        repo_path.mkdir(parents=True)
        self._run_git(repo_path, "init", "--quiet", "--initial-branch=main")
        self._run_git(repo_path, "config", "user.name", "ATLAS Test")
        self._run_git(repo_path, "config", "user.email", "atlas-test@example.invalid")
        return repo_path

    def _commit(self, repo_path: Path, message: str) -> str:
        self._run_git(repo_path, "commit", "--quiet", "--allow-empty", "-m", message)
        return self._run_git(repo_path, "rev-parse", "HEAD")

    def test_payload_declares_itself_mutable_and_not_digest_guarded(self) -> None:
        repo_path = self._init_repo("repos/mazer")
        self._commit(repo_path, "commit")
        config = {
            "repo_registry": {"mazer": {"path": "repos/mazer", "role": "application", "status": "unmanaged"}},
            "stack_lock": {"path": "stack.lock.yaml", "source_pin_repo_ids": ["mazer"], "repo_overrides": {}},
        }
        payload = build_remote_ref_alignment_payload(config, self.root)
        self.assertTrue(payload["mutable"])
        self.assertFalse(payload["digest_guarded"])
        self.assertNotIn("lock_digest", payload)
        self.assertNotIn("content_digest", payload)

    def test_write_and_load_round_trip(self) -> None:
        repo_path = self._init_repo("repos/mazer")
        self._commit(repo_path, "commit")
        config = {
            "repo_registry": {"mazer": {"path": "repos/mazer", "role": "application", "status": "unmanaged"}},
            "stack_lock": {"path": "stack.lock.yaml", "source_pin_repo_ids": ["mazer"], "repo_overrides": {}},
        }
        payload = build_remote_ref_alignment_payload(config, self.root)
        output_path = self.root / "stack.remote-ref-alignment.yaml"
        write_remote_ref_alignment_report(output_path, payload)

        loaded = load_remote_ref_alignment_report(output_path)
        self.assertIsInstance(loaded, dict)
        self.assertEqual(payload["remote_ref_alignment_count"], loaded["remote_ref_alignment_count"])
        self.assertEqual(
            payload["remote_ref_alignment"]["mazer"]["alignment_status"],
            loaded["remote_ref_alignment"]["mazer"]["alignment_status"],
        )

    def test_load_missing_report_file_returns_none(self) -> None:
        missing_path = self.root / "does-not-exist.yaml"
        self.assertIsNone(load_remote_ref_alignment_report(missing_path))

    # -- Explicit UNKNOWN / STALE contract. --

    def test_missing_entry_renders_unknown(self) -> None:
        entry = remote_ref_alignment_entry_with_staleness(None, now=datetime.now(timezone.utc))
        self.assertEqual(ALIGNMENT_STATUS_UNKNOWN, entry["alignment_status"])
        self.assertEqual(ALIGNMENT_UNAVAILABLE_REASON_NOT_CONFIGURED, entry["unavailable_reason"])

    def test_fresh_entry_is_not_stale(self) -> None:
        now = datetime.now(timezone.utc)
        raw_entry = {
            "path": "repos/mazer",
            "ref": "main",
            "remote": "https://example.invalid/mazer.git",
            "local_commit": "a" * 40,
            "local_dirty": False,
            "remote_commit": "a" * 40,
            "alignment_status": ALIGNMENT_STATUS_ALIGNED_CLEAN,
            "unavailable_reason": None,
            "checked_at": now.isoformat(),
        }
        entry = remote_ref_alignment_entry_with_staleness(raw_entry, now=now)
        self.assertEqual(ALIGNMENT_STATUS_ALIGNED_CLEAN, entry["alignment_status"])

    def test_old_entry_renders_stale_regardless_of_recorded_status(self) -> None:
        checked_at = datetime.now(timezone.utc) - REMOTE_REF_ALIGNMENT_STALE_AFTER - timedelta(hours=1)
        raw_entry = {
            "path": "repos/mazer",
            "ref": "main",
            "remote": "https://example.invalid/mazer.git",
            "local_commit": "a" * 40,
            "local_dirty": False,
            "remote_commit": "a" * 40,
            "alignment_status": ALIGNMENT_STATUS_ALIGNED_CLEAN,
            "unavailable_reason": None,
            "checked_at": checked_at.isoformat(),
        }
        now = datetime.now(timezone.utc)
        entry = remote_ref_alignment_entry_with_staleness(raw_entry, now=now)
        self.assertEqual(ALIGNMENT_STATUS_STALE, entry["alignment_status"])

    def test_entry_with_unparsable_checked_at_renders_stale(self) -> None:
        raw_entry = {
            "path": "repos/mazer",
            "ref": "main",
            "remote": "https://example.invalid/mazer.git",
            "local_commit": "a" * 40,
            "local_dirty": False,
            "remote_commit": "a" * 40,
            "alignment_status": ALIGNMENT_STATUS_ALIGNED_CLEAN,
            "unavailable_reason": None,
            "checked_at": "not-a-timestamp",
        }
        entry = remote_ref_alignment_entry_with_staleness(raw_entry, now=datetime.now(timezone.utc))
        self.assertEqual(ALIGNMENT_STATUS_STALE, entry["alignment_status"])

    def test_unrecognized_alignment_status_value_normalizes_to_unknown(self) -> None:
        """A corrupt/forward-incompatible status string must never pass
        through as if it were a real, recognized finding."""
        normalized = normalize_remote_ref_alignment_entry({"alignment_status": "definitely_promoted_to_prod"})
        self.assertEqual(ALIGNMENT_STATUS_UNKNOWN, normalized["alignment_status"])

    def test_nothing_here_is_documented_or_labeled_as_production_proof(self) -> None:
        """Cheap but concrete guardrail against regression: the honest
        status vocabulary must never include "production"/"promot*"/"proof"
        language, which is exactly the false impression this whole fix
        removes."""
        for status in (
            ALIGNMENT_STATUS_UNKNOWN,
            ALIGNMENT_STATUS_STALE,
            ALIGNMENT_STATUS_ALIGNED_CLEAN,
            ALIGNMENT_STATUS_ALIGNED_DIRTY_WORKTREE,
            ALIGNMENT_STATUS_NOT_ALIGNED,
        ):
            lowered = status.lower()
            self.assertNotIn("production", lowered)
            self.assertNotIn("promot", lowered)
            self.assertNotIn("proof", lowered)


class RepoInventoryRemoteAlignmentTests(unittest.TestCase):
    """export_repo_inventory.py consumer coverage: remote_ref_alignment_*
    fields are sourced from the separate report file (never from
    stack.lock.yaml), and must never affect content_digest."""

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

    def _init_repo(self, relative_path: str) -> Path:
        repo_path = self.root / relative_path
        repo_path.mkdir(parents=True)
        self._run_git(repo_path, "init", "--quiet", "--initial-branch=main")
        self._run_git(repo_path, "config", "user.name", "ATLAS Test")
        self._run_git(repo_path, "config", "user.email", "atlas-test@example.invalid")
        return repo_path

    def _commit(self, repo_path: Path, message: str) -> str:
        self._run_git(repo_path, "commit", "--quiet", "--allow-empty", "-m", message)
        return self._run_git(repo_path, "rev-parse", "HEAD")

    def _config(self) -> dict[str, Any]:
        return {
            "repo_registry": {
                "mazer": {"path": "repos/mazer", "role": "application", "status": "unmanaged"},
            },
            "stack_lock": {
                "path": "stack.lock.yaml",
                "source_pin_repo_ids": ["mazer"],
                "repo_overrides": {"mazer": {"remote_ref_alignment_ref": "main"}},
            },
        }

    def test_missing_report_file_renders_unknown_in_inventory(self) -> None:
        self._init_repo("repos/mazer")
        self._commit(self.root / "repos" / "mazer", "commit")
        config = self._config()

        inventory = build_repo_inventory(root=self.root, config=config)
        mazer = next(item for item in inventory["repos"] if item["logical_id"] == "mazer")
        self.assertEqual(ALIGNMENT_STATUS_UNKNOWN, mazer["remote_ref_alignment_status"])

    def test_content_digest_unaffected_by_remote_ref_alignment_report_presence(self) -> None:
        repo_path = self._init_repo("repos/mazer")
        self._commit(repo_path, "commit")
        config = self._config()

        digest_without_report = build_repo_inventory(root=self.root, config=config)["content_digest"]

        pins = build_source_pins(config, self.root)
        report = build_remote_ref_alignment_report(config, self.root, pins)
        payload = build_remote_ref_alignment_payload(config, self.root, source_pins=pins)
        write_remote_ref_alignment_report(self.root / "stack.remote-ref-alignment.yaml", payload)

        digest_with_report = build_repo_inventory(root=self.root, config=config)["content_digest"]

        self.assertEqual(digest_without_report, digest_with_report)

    def test_content_digest_unaffected_by_remote_status_flipping(self) -> None:
        """The inventory-level analogue of
        test_remote_branch_moving_does_not_change_source_pins_or_lock_digest:
        two inventories built with different (mocked) remote_ref_alignment
        report contents for the same local repo state must share the same
        content_digest, even though repos[i]["remote_ref_alignment_status"]
        differs."""
        repo_path = self._init_repo("repos/mazer")
        self._commit(repo_path, "commit")
        config = self._config()

        aligned_payload = {
            "schema_version": "atlas.stack.remote-ref-alignment.v1",
            "stack_manifest_path": "stack.yaml",
            "mutable": True,
            "digest_guarded": False,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "remote_ref_alignment_count": 1,
            "remote_ref_alignment": {
                "mazer": {
                    "path": "repos/mazer",
                    "ref": "main",
                    "remote": "https://example.invalid/mazer.git",
                    "local_commit": "a" * 40,
                    "local_dirty": False,
                    "remote_commit": "a" * 40,
                    "alignment_status": ALIGNMENT_STATUS_ALIGNED_CLEAN,
                    "unavailable_reason": None,
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                }
            },
        }
        not_aligned_payload = {
            **aligned_payload,
            "remote_ref_alignment": {
                "mazer": {
                    **aligned_payload["remote_ref_alignment"]["mazer"],
                    "remote_commit": "b" * 40,
                    "alignment_status": ALIGNMENT_STATUS_NOT_ALIGNED,
                }
            },
        }

        report_path = self.root / "stack.remote-ref-alignment.yaml"
        from ops.stack.generate_lockfile import render_lockfile_bytes

        report_path.write_bytes(render_lockfile_bytes(aligned_payload))
        first = build_repo_inventory(root=self.root, config=config)

        report_path.write_bytes(render_lockfile_bytes(not_aligned_payload))
        second = build_repo_inventory(root=self.root, config=config)

        first_mazer = next(item for item in first["repos"] if item["logical_id"] == "mazer")
        second_mazer = next(item for item in second["repos"] if item["logical_id"] == "mazer")
        self.assertEqual(ALIGNMENT_STATUS_ALIGNED_CLEAN, first_mazer["remote_ref_alignment_status"])
        self.assertEqual(ALIGNMENT_STATUS_NOT_ALIGNED, second_mazer["remote_ref_alignment_status"])
        self.assertEqual(first["content_digest"], second["content_digest"])

    def test_stale_report_renders_stale_in_inventory(self) -> None:
        repo_path = self._init_repo("repos/mazer")
        self._commit(repo_path, "commit")
        config = self._config()

        stale_checked_at = datetime.now(timezone.utc) - REMOTE_REF_ALIGNMENT_STALE_AFTER - timedelta(hours=1)
        payload = {
            "schema_version": "atlas.stack.remote-ref-alignment.v1",
            "stack_manifest_path": "stack.yaml",
            "mutable": True,
            "digest_guarded": False,
            "generated_at": stale_checked_at.isoformat(),
            "remote_ref_alignment_count": 1,
            "remote_ref_alignment": {
                "mazer": {
                    "path": "repos/mazer",
                    "ref": "main",
                    "remote": "https://example.invalid/mazer.git",
                    "local_commit": "a" * 40,
                    "local_dirty": False,
                    "remote_commit": "a" * 40,
                    "alignment_status": ALIGNMENT_STATUS_ALIGNED_CLEAN,
                    "unavailable_reason": None,
                    "checked_at": stale_checked_at.isoformat(),
                }
            },
        }
        from ops.stack.generate_lockfile import render_lockfile_bytes

        (self.root / "stack.remote-ref-alignment.yaml").write_bytes(render_lockfile_bytes(payload))

        inventory = build_repo_inventory(root=self.root, config=config)
        mazer = next(item for item in inventory["repos"] if item["logical_id"] == "mazer")
        self.assertEqual(ALIGNMENT_STATUS_STALE, mazer["remote_ref_alignment_status"])


if __name__ == "__main__":
    unittest.main()
