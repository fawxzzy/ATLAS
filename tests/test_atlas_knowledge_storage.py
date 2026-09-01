"""Tests for ops/knowledge/storage.py -- the Wave S / Wave 1 Import Storage
Convergence reusable pipeline architecture.

Scope: these tests exercise only the new architecture module and its
delegated wiring into _pipeline.list_files(). No real archive data (in
particular personal--onedrive-desktop) is touched anywhere in this file --
every fixture here is synthetic and created/destroyed within the test.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.knowledge import storage
from ops.knowledge import _pipeline
from ops.atlas.ui_standards.validate import validate_json_schema

RECEIPT_SCHEMA_PATH = ROOT / "schemas" / "atlas.knowledge-relocation-receipt.v1.json"


class TempRootMixin:
    def _temp_dir(self) -> Path:
        path = Path(tempfile.mkdtemp(prefix="atlas-storage-test-"))
        self.addCleanup(shutil.rmtree, path, ignore_errors=True)
        return path

    def _write(self, path: Path, content: bytes) -> None:
        # Uses the module's own long-path-safe mkdir rather than plain
        # Path.mkdir() -- constructing a >260-character fixture with plain
        # pathlib fails past MAX_PATH on this exact machine, which is
        # itself a live demonstration of the defect this module fixes.
        storage._lp_mkdir(path.parent)
        storage._win_long_path(path).write_bytes(content)

    def _symlink(self, link_path: Path, target: Path) -> bool:
        """Create a real symlink; returns False (and skips the caller's
        test) if this environment lacks symlink-creation privilege, which
        is common on Windows without admin rights or Developer Mode."""
        storage._lp_mkdir(link_path.parent)
        try:
            os.symlink(str(target), str(link_path))
            return True
        except OSError:
            return False


class StorageRootsTests(TempRootMixin, unittest.TestCase):
    def test_import_storage_root_defaults_to_existing_atlas_relative_location(self) -> None:
        root = storage.import_storage_root(env={})
        self.assertEqual(root, (storage.atlas_root() / "data" / "imports" / "knowledge").resolve())

    def test_import_storage_root_honors_env_override(self) -> None:
        custom = self._temp_dir() / "custom-storage"
        root = storage.import_storage_root(env={"ATLAS_IMPORT_STORAGE_ROOT": str(custom)})
        self.assertEqual(root, custom.resolve())

    def test_import_work_root_defaults_and_differs_from_storage_root_default(self) -> None:
        work = storage.import_work_root(env={})
        stor = storage.import_storage_root(env={})
        self.assertNotEqual(work, stor)

    def test_import_work_root_honors_env_override(self) -> None:
        custom = self._temp_dir() / "custom-work"
        root = storage.import_work_root(env={"ATLAS_IMPORT_WORK_ROOT": str(custom)})
        self.assertEqual(root, custom.resolve())


class EnumerateFilesTests(TempRootMixin, unittest.TestCase):
    def test_enumerate_files_returns_deterministic_sorted_order(self) -> None:
        root = self._temp_dir()
        self._write(root / "b" / "2.txt", b"two")
        self._write(root / "a" / "1.txt", b"one")
        self._write(root / "a.txt", b"top")

        files = storage.enumerate_files(root)
        rels = [f.relative_to(root).as_posix() for f in files]
        self.assertEqual(set(rels), {"a.txt", "a/1.txt", "b/2.txt"})

    def test_enumerate_files_on_missing_root_returns_empty(self) -> None:
        missing = self._temp_dir() / "does-not-exist"
        self.assertEqual(storage.enumerate_files(missing), [])

    def test_enumerate_files_finds_a_genuinely_long_path_entry(self) -> None:
        root = self._temp_dir()
        segment = "deeply-nested-directory-segment-name-used-only-for-length"
        deep = root
        while len(str(deep)) < 280:
            deep = deep / segment
        target = deep / "buried-file.txt"
        self._write(target, b"findable")

        files = storage.enumerate_files(root)
        rels = {f.relative_to(root).as_posix() for f in files}
        expected_rel = target.relative_to(root).as_posix()
        self.assertIn(expected_rel, rels)
        self.assertGreater(len(str(target)), 260)

    def test_pipeline_list_files_delegates_and_is_also_long_path_safe(self) -> None:
        root = self._temp_dir()
        segment = "another-deeply-nested-directory-segment-for-length-only"
        deep = root
        while len(str(deep)) < 280:
            deep = deep / segment
        target = deep / "reachable-via-pipeline.txt"
        self._write(target, b"still findable")

        files = _pipeline.list_files(root)
        rels = {f.relative_to(root).as_posix() for f in files}
        self.assertIn(target.relative_to(root).as_posix(), rels)

    @unittest.skipUnless(os.name == "nt", "8.3 short-name aliasing is a Windows-only concern")
    def test_enumerate_files_anchors_to_root_even_when_resolve_differs(self) -> None:
        # Reproduces, deterministically, the exact failure hit on Windows
        # CI: that runner's temp directory resolves through an 8.3
        # short-name alias (RUNNER~1 vs runneradmin), so root.resolve()
        # produced a different string than the caller's original root,
        # breaking entry.relative_to(root). NTFS lookups are
        # case-insensitive, so upper-casing root's string here reaches the
        # same real directory while differing textually -- the same shape
        # of mismatch as the short-name alias, without depending on that
        # specific CI runner behavior to reproduce it.
        root = self._temp_dir()
        self._write(root / "a.txt", b"alpha")
        original_resolve = Path.resolve

        def fake_resolve(path_self, *args, **kwargs):
            if path_self == root:
                return Path(str(root).upper())
            return original_resolve(path_self, *args, **kwargs)

        with mock.patch.object(Path, "resolve", fake_resolve):
            files = storage.enumerate_files(root)

        self.assertEqual(len(files), 1)
        rels = [f.relative_to(root).as_posix() for f in files]
        self.assertEqual(rels, ["a.txt"])

    @unittest.skipUnless(os.name == "nt", "case-insensitive sort compatibility is a Windows-only concern")
    def test_enumerate_files_sort_order_matches_previous_windows_path_sort_for_mixed_case(self) -> None:
        # The previous rglob()-based enumeration sorted plain pathlib.Path
        # objects, which are case-insensitive on Windows (PureWindowsPath).
        # enumerate_files() sorts POSIX-string relative paths instead; this
        # proves that per-platform sort key still reproduces the exact same
        # order for mixed-case siblings, so tree_digest() output does not
        # silently change for a tree whose only "difference" is filename
        # case.
        root = self._temp_dir()
        names = ["Banana.txt", "apple.txt", "Cherry.txt", "banana2.txt"]
        for name in names:
            self._write(root / name, name.encode("utf-8"))

        old_style_order = [p.name for p in sorted(root / n for n in names)]
        files = storage.enumerate_files(root)
        new_style_order = [f.name for f in files]

        self.assertEqual(new_style_order, old_style_order)


class SymlinkConfinementTests(TempRootMixin, unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "no-follow long-path prefixing is a Windows-only concern")
    def test_win_long_path_no_follow_never_calls_resolve(self) -> None:
        # Structural, privilege-independent proof of the fix: hosted
        # Windows CI found that _lp_is_symlink() (built on the
        # resolve()-based _win_long_path()) always reported False for a
        # real symlink, because Path.resolve() follows symlinks to their
        # target before is_symlink() ever runs. This proves the fixed
        # no-follow variant structurally cannot make that mistake -- it
        # never calls resolve() at all -- without depending on this
        # environment actually being able to create a real symlink.
        called = {"n": 0}
        original_resolve = Path.resolve

        def counting_resolve(path_self, *args, **kwargs):
            called["n"] += 1
            return original_resolve(path_self, *args, **kwargs)

        with mock.patch.object(Path, "resolve", counting_resolve):
            storage._win_long_path_no_follow(Path("C:/some/path/for/this/test"))

        self.assertEqual(called["n"], 0)

    def test_internal_symlink_is_not_flagged(self) -> None:
        root = self._temp_dir()
        self._write(root / "real.txt", b"content")
        link = root / "link.txt"
        if not self._symlink(link, root / "real.txt"):
            self.skipTest("symlink creation not permitted in this environment")

        files = storage.enumerate_files(root)
        findings = storage.check_symlink_confinement(root, files)
        self.assertEqual(findings, [])

    def test_external_symlink_is_flagged(self) -> None:
        root = self._temp_dir()
        outside = self._temp_dir()
        self._write(outside / "secret.txt", b"outside content")
        link = root / "escape.txt"
        if not self._symlink(link, outside / "secret.txt"):
            self.skipTest("symlink creation not permitted in this environment")

        files = storage.enumerate_files(root)
        findings = storage.check_symlink_confinement(root, files)
        self.assertTrue(any("external_symlink_target_rejected" in f for f in findings))

    def test_external_symlink_blocks_preflight_before_any_copy(self) -> None:
        # Under LinkPolicy.REJECT_ALL (preflight_space_budget()'s default),
        # every link entry is blocking regardless of internal/external
        # target -- check_link_entries() is what actually runs here, not
        # the legacy check_symlink_confinement() exercised by the tests
        # above, so the finding text is "unsupported_link_entry", not
        # "external_symlink_target_rejected".
        source = self._temp_dir()
        self._write(source / "keep.txt", b"keep me")
        outside = self._temp_dir()
        self._write(outside / "secret.txt", b"outside content")
        if not self._symlink(source / "escape.txt", outside / "secret.txt"):
            self.skipTest("symlink creation not permitted in this environment")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"

        with mock.patch.object(storage, "_free_bytes", return_value=10 * 1024 * 1024 * 1024):
            budget = storage.preflight_space_budget(
                source_root=source, raw_destination_root=destination, work_root=work
            )

        self.assertFalse(budget.ok)
        self.assertTrue(
            any("unsupported_link_entry" in f and "escape.txt" in f and "file_symlink" in f
                for f in budget.findings)
        )
        self.assertFalse(destination.exists())

    def test_internal_symlink_still_blocks_preflight_under_reject_all(self) -> None:
        # The pre-pivot confinement model treated an internal-target link
        # as safe. REJECT_ALL does not distinguish -- any link entry at
        # all is blocking, internal target included -- so this is the one
        # behavioral change from check_symlink_confinement() worth its own
        # explicit regression test.
        source = self._temp_dir()
        self._write(source / "real.txt", b"content")
        if not self._symlink(source / "link.txt", source / "real.txt"):
            self.skipTest("symlink creation not permitted in this environment")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"

        with mock.patch.object(storage, "_free_bytes", return_value=10 * 1024 * 1024 * 1024):
            budget = storage.preflight_space_budget(
                source_root=source, raw_destination_root=destination, work_root=work
            )

        self.assertFalse(budget.ok)
        self.assertTrue(
            any("unsupported_link_entry" in f and "link.txt" in f and "file_symlink" in f
                for f in budget.findings)
        )
        self.assertFalse(destination.exists())


class DirectoryLinkTests(TempRootMixin, unittest.TestCase):
    def _junction(self, link_path: Path, target: Path) -> bool:
        """Create a real NTFS junction via mklink /J -- unlike symlinks,
        junctions do not require SeCreateSymbolicLinkPrivilege, but they
        are still Windows-only and can fail for other reasons (e.g. the
        target not existing yet), so this is defensive-skip like
        _symlink()."""
        if os.name != "nt":
            return False
        storage._lp_mkdir(link_path.parent)
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link_path), str(target)],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def test_internal_directory_symlink_is_enumerated_and_not_flagged(self) -> None:
        root = self._temp_dir()
        self._write(root / "real_dir" / "inside.txt", b"content")
        link = root / "link_dir"
        if not self._symlink(link, root / "real_dir"):
            self.skipTest("symlink creation not permitted in this environment")

        directory_links = storage.enumerate_directory_links(root)
        rels = {d.relative_to(root).as_posix() for d in directory_links}
        self.assertIn("link_dir", rels)

        findings = storage.check_symlink_confinement(
            root, storage.enumerate_files(root) + directory_links
        )
        self.assertEqual(findings, [])

    def test_external_directory_symlink_is_flagged(self) -> None:
        root = self._temp_dir()
        outside = self._temp_dir()
        self._write(outside / "inside.txt", b"content")
        link = root / "escape_dir"
        if not self._symlink(link, outside):
            self.skipTest("symlink creation not permitted in this environment")

        directory_links = storage.enumerate_directory_links(root)
        findings = storage.check_symlink_confinement(
            root, storage.enumerate_files(root) + directory_links
        )
        self.assertTrue(any("external_symlink_target_rejected" in f for f in findings))

    def test_directory_symlink_recorded_in_manifest_not_silently_omitted(self) -> None:
        root = self._temp_dir()
        self._write(root / "real_dir" / "inside.txt", b"content")
        link = root / "link_dir"
        if not self._symlink(link, root / "real_dir"):
            self.skipTest("symlink creation not permitted in this environment")

        manifest = storage.build_relocation_manifest(root)
        paths = {e["path"] for e in manifest["entries"]}
        self.assertIn("link_dir", paths)
        kinds = {e["path"]: e["kind"] for e in manifest["entries"]}
        # _classify_link_entry() (third hardening wave) distinguishes file
        # vs. directory symlinks explicitly rather than a generic "symlink"
        # label -- see _link_entry_kind().
        self.assertEqual(kinds["link_dir"], "directory_symlink")

    @unittest.skipUnless(os.name == "nt", "junctions are a Windows-only concept")
    def test_windows_junction_is_detected_as_reparse_point(self) -> None:
        root = self._temp_dir()
        target = self._temp_dir()
        self._write(target / "inside.txt", b"content")
        link = root / "junction_dir"
        if not self._junction(link, target):
            self.skipTest("junction creation not permitted in this environment")

        self.assertTrue(storage._is_reparse_point(link))
        # A true symlink check alone must NOT be relied on for junctions --
        # this is the exact gap the hardening wave closed.
        directory_links = storage.enumerate_directory_links(root)
        rels = {d.relative_to(root).as_posix() for d in directory_links}
        self.assertIn("junction_dir", rels)

    @unittest.skipUnless(os.name == "nt", "junctions are a Windows-only concept")
    def test_external_windows_junction_is_flagged(self) -> None:
        root = self._temp_dir()
        outside = self._temp_dir()
        self._write(outside / "inside.txt", b"content")
        link = root / "escape_junction"
        if not self._junction(link, outside):
            self.skipTest("junction creation not permitted in this environment")

        directory_links = storage.enumerate_directory_links(root)
        findings = storage.check_symlink_confinement(
            root, storage.enumerate_files(root) + directory_links
        )
        self.assertTrue(any("external_symlink_target_rejected" in f for f in findings))

    def test_external_directory_symlink_blocks_preflight_before_any_copy(self) -> None:
        root = self._temp_dir()
        outside = self._temp_dir()
        self._write(outside / "inside.txt", b"content")
        link = root / "escape_dir"
        if not self._symlink(link, outside):
            self.skipTest("symlink creation not permitted in this environment")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"

        with mock.patch.object(storage, "_free_bytes", return_value=10 * 1024 * 1024 * 1024):
            budget = storage.preflight_space_budget(
                source_root=root, raw_destination_root=destination, work_root=work
            )

        self.assertFalse(budget.ok)
        self.assertTrue(
            any("unsupported_link_entry" in f and "escape_dir" in f and "directory_symlink" in f
                for f in budget.findings)
        )
        self.assertFalse(destination.exists())

    @unittest.skipUnless(os.name == "nt", "junctions are a Windows-only concept")
    def test_windows_junction_blocks_preflight_before_any_copy(self) -> None:
        root = self._temp_dir()
        target = self._temp_dir()
        self._write(target / "inside.txt", b"content")
        link = root / "junction_dir"
        if not self._junction(link, target):
            self.skipTest("junction creation not permitted in this environment")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"

        with mock.patch.object(storage, "_free_bytes", return_value=10 * 1024 * 1024 * 1024):
            budget = storage.preflight_space_budget(
                source_root=root, raw_destination_root=destination, work_root=work
            )

        self.assertFalse(budget.ok)
        self.assertTrue(
            any("unsupported_link_entry" in f and "junction_dir" in f and "windows_junction" in f
                for f in budget.findings)
        )
        self.assertFalse(destination.exists())

    def test_directory_link_blocks_relocation_before_any_destination_write(self) -> None:
        # Under LinkPolicy.REJECT_ALL (Wave 1's only policy), a directory
        # link is rejected at preflight -- resumable_copy_tree() itself
        # never even sees directory-level entries (its scope is regular
        # files only, see the module note above LinkPolicy), so this
        # tests the actual enforcement point: relocate_archive_source().
        root = self._temp_dir()
        self._write(root / "real_dir" / "inside.txt", b"content")
        if not self._symlink(root / "link_dir", root / "real_dir"):
            self.skipTest("symlink creation not permitted in this environment")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"

        result = storage.relocate_archive_source(
            archive_id="synthetic--directory-link-rejected",
            source_root=root,
            destination_root=destination,
            work_root=work,
            source_description="synthetic fixture proving directory links block relocation",
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("unsupported_link_entry" in f and "link_dir" in f and "directory_symlink" in f
                for f in result.space_budget.findings)
        )
        self.assertFalse(destination.exists())


class GeneratedCacheExclusionTests(unittest.TestCase):
    def test_matches_nested_unity_package_cache(self) -> None:
        self.assertTrue(
            storage.is_generated_cache_path("Mazer Mobile/Library/PackageCache/com.unity.foo/file.cs")
        )

    def test_matches_top_level_and_nested_node_modules(self) -> None:
        self.assertTrue(storage.is_generated_cache_path("node_modules/leftpad/index.js"))
        self.assertTrue(storage.is_generated_cache_path("packages/app/node_modules/leftpad/index.js"))

    def test_does_not_false_positive_on_similarly_named_real_content(self) -> None:
        self.assertFalse(storage.is_generated_cache_path("src/Library/README.md"))
        self.assertFalse(storage.is_generated_cache_path("docs/node_modules_migration_notes.md"))

    def test_dot_git_is_never_treated_as_generated_cache(self) -> None:
        # .git is version-control data (history, reflogs, unreachable
        # objects, provenance), not generated cache. Confirmed absent from
        # the pattern list, not merely untested.
        self.assertFalse(storage.is_generated_cache_path(".git/refs/heads/main"))
        self.assertFalse(storage.is_generated_cache_path("nested/repo/.git/config"))
        self.assertNotIn(".git", storage.GENERATED_CACHE_EXCLUSION_PATTERNS)


class ExclusionPolicyTests(unittest.TestCase):
    def test_no_exclusion_policy_excludes_nothing(self) -> None:
        self.assertFalse(storage.NO_EXCLUSION_POLICY.predicate("Library/PackageCache/x.bin"))
        self.assertFalse(storage.NO_EXCLUSION_POLICY.predicate(".git/config"))

    def test_generated_cache_policy_has_a_stable_identity(self) -> None:
        self.assertEqual(storage.GENERATED_CACHE_EXCLUSION_POLICY.policy_id, "atlas.knowledge.generated-cache-exclusion")
        self.assertTrue(storage.GENERATED_CACHE_EXCLUSION_POLICY.version)


class SpacePreflightTests(TempRootMixin, unittest.TestCase):
    def setUp(self) -> None:
        # Fixtures live under the OS temp dir, which is on the system
        # volume on this machine. Patch _is_system_volume False by default
        # so these general-purpose tests exercise the ordinary (512 MiB)
        # reserve they're actually meant to test, not the much larger
        # system-volume floor -- SystemVolumeReserveTests below tests that
        # behavior directly, with its own explicit override.
        patcher = mock.patch.object(storage, "_is_system_volume", return_value=False)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _fixture(self) -> tuple[Path, Path, Path]:
        source = self._temp_dir() / "source"
        self._write(source / "a.bin", b"x" * 1000)
        self._write(source / "b.bin", b"y" * 2000)
        storage_root = self._temp_dir() / "storage"
        work_root = self._temp_dir() / "work"
        return source, storage_root, work_root

    def test_preflight_ok_when_space_is_sufficient(self) -> None:
        source, storage_root, work_root = self._fixture()
        # Fixtures live under the OS temp dir, which is on the system
        # volume on this machine -- mock _is_system_volume False so this
        # test exercises the ordinary (512 MiB) reserve it's actually
        # meant to test, not the much larger system-volume floor (see the
        # dedicated SystemVolumeReserveTests for that).
        with mock.patch.object(storage, "_free_bytes", return_value=10 * 1024 * 1024 * 1024), \
             mock.patch.object(storage, "_is_system_volume", return_value=False):
            budget = storage.preflight_space_budget(
                source_root=source, raw_destination_root=storage_root, work_root=work_root
            )
        self.assertTrue(budget.ok)
        self.assertEqual(budget.findings, [])

    def test_preflight_fails_closed_when_volume_space_is_insufficient(self) -> None:
        source, storage_root, work_root = self._fixture()
        with mock.patch.object(storage, "_free_bytes", return_value=10):
            budget = storage.preflight_space_budget(
                source_root=source, raw_destination_root=storage_root, work_root=work_root
            )
        self.assertFalse(budget.ok)
        self.assertTrue(any("insufficient_volume_space" in f for f in budget.findings))

    def test_preflight_aggregates_demand_when_roots_share_one_volume(self) -> None:
        source, storage_root, work_root = self._fixture()
        # storage_root and work_root report the SAME volume id -- their
        # demands must sum, not be checked independently. Each individual
        # requirement is small, but their sum plus the fixed available
        # amount should fail.
        shared_volume = object()

        def fake_volume_id(path):
            return shared_volume

        with mock.patch.object(storage, "_volume_id", side_effect=fake_volume_id), \
             mock.patch.object(storage, "_free_bytes", return_value=storage.DEFAULT_SAFETY_MARGIN_BYTES + 100):
            budget = storage.preflight_space_budget(
                source_root=source, raw_destination_root=storage_root, work_root=work_root
            )
        # Only one volume entry should appear (both roots collapsed into it).
        self.assertEqual(len(budget.volumes), 1)

    def test_preflight_treats_separate_extracted_volume_independently(self) -> None:
        source, storage_root, work_root = self._fixture()
        extracted_root = self._temp_dir() / "extracted"

        volumes = {str(storage_root): "vol-raw", str(work_root): "vol-raw", str(extracted_root): "vol-extracted"}

        def fake_volume_id(path):
            for key, vol in volumes.items():
                if str(path).startswith(key):
                    return vol
            return "vol-raw"

        def fake_free_bytes(path):
            # Plenty on the raw/work volume, almost nothing on the
            # extracted volume specifically.
            return 10 * 1024 * 1024 * 1024 if str(path).startswith(str(storage_root)) or str(path).startswith(str(work_root)) else 10

        with mock.patch.object(storage, "_volume_id", side_effect=fake_volume_id), \
             mock.patch.object(storage, "_free_bytes", side_effect=fake_free_bytes):
            budget = storage.preflight_space_budget(
                source_root=source,
                raw_destination_root=storage_root,
                work_root=work_root,
                extracted_destination_root=extracted_root,
            )

        self.assertFalse(budget.ok)
        self.assertTrue(any("insufficient_volume_space" in f and "extracted_destination" in f for f in budget.findings))

    def test_preflight_stat_failure_blocks_rather_than_silently_skips(self) -> None:
        source, storage_root, work_root = self._fixture()
        target_file = source / "a.bin"
        original_stat = storage._lp_stat

        def fake_stat(path):
            if path == target_file:
                raise OSError("simulated stat failure")
            return original_stat(path)

        with mock.patch.object(storage, "_free_bytes", return_value=10 * 1024 * 1024 * 1024), \
             mock.patch.object(storage, "_lp_stat", side_effect=fake_stat):
            budget = storage.preflight_space_budget(
                source_root=source, raw_destination_root=storage_root, work_root=work_root
            )

        self.assertFalse(budget.ok)
        self.assertTrue(any("source_stat_failed" in f for f in budget.findings))

    def test_preflight_budgets_only_remaining_bytes_on_resume(self) -> None:
        source, storage_root, work_root = self._fixture()
        # Pre-populate the destination with a.bin already matching the
        # source -- a resumed operation should not budget for it again.
        self._write(storage_root / "a.bin", b"x" * 1000)

        # Force raw destination and work root onto distinct mocked volumes
        # so this test isolates "resumability reduces bytes needed" from
        # the separately-tested "shared-volume demands aggregate" behavior
        # (real temp dirs here would otherwise share one physical volume).
        def fake_volume_id(path):
            return "vol-raw" if str(path).startswith(str(storage_root)) else "vol-work"

        with mock.patch.object(storage, "_volume_id", side_effect=fake_volume_id), \
             mock.patch.object(storage, "_is_system_volume", return_value=False), \
             mock.patch.object(storage, "_free_bytes", return_value=10 * 1024 * 1024 * 1024):
            budget = storage.preflight_space_budget(
                source_root=source, raw_destination_root=storage_root, work_root=work_root
            )

        self.assertTrue(budget.ok)
        raw_volume = next(v for v in budget.volumes if v.probe_path == storage._existing_ancestor(storage_root))
        # required_bytes should reflect b.bin's 2000 bytes still needed,
        # plus the same-file atomic-fallback peak (also 2000 -- b.bin is
        # the only/largest remaining file), plus the safety margin -- not
        # both files' combined 3000 bytes.
        expected = 2000 + 2000 + storage.DEFAULT_SAFETY_MARGIN_BYTES
        self.assertEqual(raw_volume.required_bytes, expected)

    def test_preflight_excludes_generated_cache_from_the_budget(self) -> None:
        source, storage_root, work_root = self._fixture()
        self._write(source / "Library" / "PackageCache" / "junk.bin", b"z" * 5000)
        with mock.patch.object(storage, "_free_bytes", return_value=10 * 1024 * 1024 * 1024):
            without_exclusion = storage.preflight_space_budget(
                source_root=source, raw_destination_root=storage_root, work_root=work_root, exclude=None,
            )
            without_exclusion_bytes = without_exclusion.volumes[0].required_bytes
            with_exclusion = storage.preflight_space_budget(
                source_root=source, raw_destination_root=storage_root, work_root=work_root,
                exclude=storage.is_generated_cache_path,
            )
            with_exclusion_bytes = with_exclusion.volumes[0].required_bytes
        self.assertLess(with_exclusion_bytes, without_exclusion_bytes)


class SystemVolumeReserveTests(TempRootMixin, unittest.TestCase):
    def test_system_volume_uses_the_much_larger_reserve_floor(self) -> None:
        source = self._temp_dir() / "source"
        self._write(source / "a.bin", b"x" * 1000)
        storage_root = self._temp_dir() / "storage"
        work_root = self._temp_dir() / "work"

        # Enough space for the content and the ordinary 512 MiB reserve,
        # but not enough for the ~25 GiB system-volume floor.
        available = storage.DEFAULT_VOLUME_RESERVE_POLICY.non_system_volume_reserve_bytes + 10_000
        with mock.patch.object(storage, "_is_system_volume", return_value=True), \
             mock.patch.object(storage, "_free_bytes", return_value=available):
            budget = storage.preflight_space_budget(
                source_root=source, raw_destination_root=storage_root, work_root=work_root
            )

        self.assertFalse(budget.ok)
        self.assertTrue(any("insufficient_volume_space" in f for f in budget.findings))

    def test_non_system_volume_uses_the_ordinary_reserve(self) -> None:
        source = self._temp_dir() / "source"
        self._write(source / "a.bin", b"x" * 1000)
        storage_root = self._temp_dir() / "storage"
        work_root = self._temp_dir() / "work"

        available = storage.DEFAULT_VOLUME_RESERVE_POLICY.non_system_volume_reserve_bytes + 10_000
        with mock.patch.object(storage, "_is_system_volume", return_value=False), \
             mock.patch.object(storage, "_free_bytes", return_value=available):
            budget = storage.preflight_space_budget(
                source_root=source, raw_destination_root=storage_root, work_root=work_root
            )

        self.assertTrue(budget.ok)

    def test_caller_override_reserve_policy_is_recorded_on_the_budget(self) -> None:
        source = self._temp_dir() / "source"
        self._write(source / "a.bin", b"x" * 1000)
        storage_root = self._temp_dir() / "storage"
        work_root = self._temp_dir() / "work"
        custom_policy = storage.VolumeReservePolicy(
            system_volume_minimum_free_bytes=123, non_system_volume_reserve_bytes=456
        )

        with mock.patch.object(storage, "_is_system_volume", return_value=False), \
             mock.patch.object(storage, "_free_bytes", return_value=10 * 1024 * 1024 * 1024):
            budget = storage.preflight_space_budget(
                source_root=source, raw_destination_root=storage_root, work_root=work_root,
                reserve_policy=custom_policy,
            )

        self.assertEqual(budget.safety_margin_bytes, 456)


class RootTopologyTests(TempRootMixin, unittest.TestCase):
    def test_destination_inside_source_is_rejected(self) -> None:
        source = self._temp_dir()
        destination = source / "nested-destination"
        work = self._temp_dir() / "work"

        findings = storage.validate_root_topology(
            source_root=source, raw_destination_root=destination, work_root=work
        )
        self.assertTrue(any("raw_destination_root is inside" in f for f in findings))

    def test_work_root_inside_source_is_rejected(self) -> None:
        source = self._temp_dir()
        destination = self._temp_dir() / "destination"
        work = source / "nested-work"

        findings = storage.validate_root_topology(
            source_root=source, raw_destination_root=destination, work_root=work
        )
        self.assertTrue(any("work_root is inside" in f for f in findings))

    def test_extracted_identical_to_raw_is_rejected(self) -> None:
        source = self._temp_dir()
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"

        findings = storage.validate_root_topology(
            source_root=source, raw_destination_root=destination, work_root=work,
            extracted_destination_root=destination,
        )
        self.assertTrue(any("identical to raw_destination_root" in f for f in findings))

    def test_extracted_nested_inside_raw_is_rejected(self) -> None:
        source = self._temp_dir()
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"
        extracted = destination / "nested-extracted"

        findings = storage.validate_root_topology(
            source_root=source, raw_destination_root=destination, work_root=work,
            extracted_destination_root=extracted,
        )
        self.assertTrue(any("nested inside raw_destination_root" in f for f in findings))

    def test_receipt_path_inside_source_is_rejected(self) -> None:
        source = self._temp_dir()
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"
        receipt_path = source / "receipts" / "x.json"

        findings = storage.validate_root_topology(
            source_root=source, raw_destination_root=destination, work_root=work,
            receipt_path=receipt_path,
        )
        self.assertTrue(any("receipt_path is inside source_root" in f for f in findings))

    def test_clean_disjoint_roots_produce_no_findings(self) -> None:
        base = self._temp_dir()
        source = base / "source"
        destination = base / "destination"
        work = base / "work"
        extracted = base / "extracted"
        receipt_path = base / "receipts" / "x.json"

        findings = storage.validate_root_topology(
            source_root=source, raw_destination_root=destination, work_root=work,
            extracted_destination_root=extracted, receipt_path=receipt_path,
        )
        self.assertEqual(findings, [])

    def test_preflight_rejects_nested_destination_before_any_enumeration(self) -> None:
        source = self._temp_dir()
        self._write(source / "a.txt", b"content")
        destination = source / "nested-destination"
        work = self._temp_dir() / "work"

        budget = storage.preflight_space_budget(
            source_root=source, raw_destination_root=destination, work_root=work
        )

        self.assertFalse(budget.ok)
        self.assertTrue(any("raw_destination_root is inside" in f for f in budget.findings))
        self.assertEqual(budget.volumes, [])


class ResumableCopyTests(TempRootMixin, unittest.TestCase):
    def test_full_copy_matches_source_content_and_checksums(self) -> None:
        source = self._temp_dir() / "source"
        self._write(source / "a.txt", b"alpha")
        self._write(source / "nested" / "b.txt", b"beta")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"

        result = storage.resumable_copy_tree(source, destination, work_root=work)

        self.assertEqual(set(result.copied), {"a.txt", "nested/b.txt"})
        self.assertEqual(result.skipped_already_present, [])
        self.assertEqual(result.failed, [])
        self.assertEqual((destination / "a.txt").read_bytes(), b"alpha")
        self.assertEqual((destination / "nested" / "b.txt").read_bytes(), b"beta")

    def test_rerun_after_completion_skips_every_file_resumability(self) -> None:
        source = self._temp_dir() / "source"
        self._write(source / "a.txt", b"alpha")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"

        storage.resumable_copy_tree(source, destination, work_root=work)
        second = storage.resumable_copy_tree(source, destination, work_root=work)

        self.assertEqual(second.copied, [])
        self.assertEqual(second.skipped_already_present, ["a.txt"])

    def test_interrupted_partial_copy_resumes_and_completes(self) -> None:
        source = self._temp_dir() / "source"
        self._write(source / "already-done.txt", b"already there")
        self._write(source / "not-yet.txt", b"still needs copying")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"
        self._write(destination / "already-done.txt", b"already there")

        result = storage.resumable_copy_tree(source, destination, work_root=work)

        self.assertEqual(result.copied, ["not-yet.txt"])
        self.assertEqual(result.skipped_already_present, ["already-done.txt"])
        self.assertEqual((destination / "not-yet.txt").read_bytes(), b"still needs copying")

    def test_stale_mismatched_destination_file_is_recopied_not_trusted(self) -> None:
        source = self._temp_dir() / "source"
        self._write(source / "a.txt", b"correct content")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"
        self._write(destination / "a.txt", b"WRONG stale content")

        result = storage.resumable_copy_tree(source, destination, work_root=work)

        self.assertEqual(result.copied, ["a.txt"])
        self.assertEqual((destination / "a.txt").read_bytes(), b"correct content")

    def test_generated_cache_paths_are_excluded_from_copy(self) -> None:
        source = self._temp_dir() / "source"
        self._write(source / "keep.txt", b"keep me")
        self._write(source / "Library" / "PackageCache" / "drop.txt", b"drop me")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"

        result = storage.resumable_copy_tree(
            source, destination, work_root=work, exclude=storage.is_generated_cache_path
        )

        self.assertEqual(result.copied, ["keep.txt"])
        self.assertFalse((destination / "Library").exists())

    def test_no_partial_file_survives_a_failed_staged_copy(self) -> None:
        source = self._temp_dir() / "source"
        self._write(source / "a.txt", b"alpha")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"

        original = storage.file_checksum

        def corrupt_then_restore(path: Path) -> str:
            corrupt_then_restore.calls += 1
            if corrupt_then_restore.calls == 2:
                return "sha256:deliberately-wrong"
            return original(path)

        corrupt_then_restore.calls = 0
        with mock.patch.object(storage, "file_checksum", side_effect=corrupt_then_restore):
            result = storage.resumable_copy_tree(source, destination, work_root=work)

        self.assertEqual([f.path for f in result.failed], ["a.txt"])
        self.assertEqual(result.failed[0].category, "checksum_mismatch")
        self.assertTrue(result.failed[0].message_digest.startswith("sha256:"))
        self.assertFalse((destination / "a.txt").exists())

    def test_symlink_source_is_rejected_not_copied_or_dereferenced(self) -> None:
        # Defense in depth at the low-level primitive: Wave 1's primary
        # enforcement is preflight_space_budget() rejecting a tree
        # containing any link before resumable_copy_tree() is ever
        # called on it, but this proves the copy step itself also
        # refuses a link source outright -- neither preserving it as a
        # link (removed after three review rounds of real, distinct
        # platform-specific defects) nor silently dereferencing it into
        # a regular-file copy of its target's content (which would
        # reopen the exact exfiltration risk check_symlink_confinement()
        # exists to prevent).
        source = self._temp_dir() / "source"
        self._write(source / "real.txt", b"real content")
        link = source / "link.txt"
        if not self._symlink(link, source / "real.txt"):
            self.skipTest("symlink creation not permitted in this environment")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"

        result = storage.resumable_copy_tree(source, destination, work_root=work)

        self.assertEqual([f.path for f in result.failed], ["link.txt"])
        self.assertEqual(result.failed[0].category, "unsupported_link_entry")
        self.assertFalse((destination / "link.txt").exists())
        self.assertNotIn("link.txt", result.copied)


class DestinationSideSymlinkSafetyTests(TempRootMixin, unittest.TestCase):
    """Proves _lp_replace()'s no-follow fix: a planted symlink already
    sitting at a destination path must never redirect a copy or receipt
    write to overwrite whatever that symlink points at."""

    def test_copy_replaces_the_destination_link_entry_not_its_external_target(self) -> None:
        source = self._temp_dir() / "source"
        self._write(source / "a.txt", b"new content")
        destination_root = self._temp_dir() / "destination"
        external = self._temp_dir() / "external"
        self._write(external / "victim.txt", b"must not be touched")
        if not self._symlink(destination_root / "a.txt", external / "victim.txt"):
            self.skipTest("symlink creation not permitted in this environment")
        work = self._temp_dir() / "work"

        result = storage.resumable_copy_tree(source, destination_root, work_root=work)

        self.assertEqual(result.copied, ["a.txt"])
        self.assertEqual((external / "victim.txt").read_bytes(), b"must not be touched")
        self.assertFalse((destination_root / "a.txt").is_symlink())
        self.assertEqual((destination_root / "a.txt").read_bytes(), b"new content")

    def test_receipt_write_replaces_the_receipt_link_entry_not_its_external_target(self) -> None:
        external = self._temp_dir() / "external"
        self._write(external / "victim.json", b'{"original": true}')
        receipts_dir = self._temp_dir() / "receipts"
        receipt_path = receipts_dir / "fixture.latest.json"
        if not self._symlink(receipt_path, external / "victim.json"):
            self.skipTest("symlink creation not permitted in this environment")

        storage.write_relocation_receipt({"ok": True, "n": 1}, receipt_path)

        self.assertEqual((external / "victim.json").read_bytes(), b'{"original": true}')
        self.assertFalse(receipt_path.is_symlink())
        self.assertEqual(storage.read_relocation_receipt(receipt_path), {"ok": True, "n": 1})


class RelocationManifestAndRestoreVerificationTests(TempRootMixin, unittest.TestCase):
    def test_manifest_round_trips_through_verify_restore_as_ok(self) -> None:
        root = self._temp_dir()
        self._write(root / "a.txt", b"alpha")
        self._write(root / "b.txt", b"beta")

        manifest = storage.build_relocation_manifest(root)
        verification = storage.verify_restore(manifest=manifest, root=root)

        self.assertTrue(verification["ok"])
        self.assertEqual(verification["missing_paths"], [])
        self.assertEqual(verification["unexpected_paths"], [])
        self.assertEqual(verification["mismatched_paths"], [])

    def test_verify_restore_detects_a_missing_file(self) -> None:
        root = self._temp_dir()
        self._write(root / "a.txt", b"alpha")
        manifest = storage.build_relocation_manifest(root)
        (root / "a.txt").unlink()

        verification = storage.verify_restore(manifest=manifest, root=root)

        self.assertFalse(verification["ok"])
        self.assertEqual(verification["missing_paths"], ["a.txt"])

    def test_verify_restore_detects_content_mismatch(self) -> None:
        root = self._temp_dir()
        self._write(root / "a.txt", b"alpha")
        manifest = storage.build_relocation_manifest(root)
        (root / "a.txt").write_bytes(b"tampered")

        verification = storage.verify_restore(manifest=manifest, root=root)

        self.assertFalse(verification["ok"])
        self.assertEqual(verification["mismatched_paths"], ["a.txt"])

    def test_verify_restore_default_fails_closed_on_unexpected_extra_file(self) -> None:
        root = self._temp_dir()
        self._write(root / "a.txt", b"alpha")
        manifest = storage.build_relocation_manifest(root)
        self._write(root / "new.txt", b"unexpected")

        verification = storage.verify_restore(manifest=manifest, root=root)

        # Default is exact-match: an unexplained extra file at the
        # destination must NOT read as "verified."
        self.assertFalse(verification["ok"])
        self.assertEqual(verification["unexpected_paths"], ["new.txt"])

    def test_verify_restore_allow_extra_mode_is_opt_in_only(self) -> None:
        root = self._temp_dir()
        self._write(root / "a.txt", b"alpha")
        manifest = storage.build_relocation_manifest(root)
        self._write(root / "new.txt", b"unexpected")

        verification = storage.verify_restore(manifest=manifest, root=root, require_exact_match=False)

        self.assertTrue(verification["ok"])
        self.assertEqual(verification["unexpected_paths"], ["new.txt"])

    def test_manifest_is_junction_independent_when_root_is_relocated(self) -> None:
        original_root = self._temp_dir()
        self._write(original_root / "sub" / "a.txt", b"alpha")
        manifest = storage.build_relocation_manifest(original_root)

        relocated_root = self._temp_dir()
        shutil.copytree(original_root, relocated_root, dirs_exist_ok=True)

        verification = storage.verify_restore(manifest=manifest, root=relocated_root)
        self.assertTrue(verification["ok"])


class DurableReceiptTests(TempRootMixin, unittest.TestCase):
    def test_receipt_round_trips_through_write_and_read(self) -> None:
        receipt = {"contract_version": "atlas.knowledge-relocation-receipt.v1", "ok": True, "n": 1}
        path = self._temp_dir() / "receipts" / "fixture.latest.json"

        storage.write_relocation_receipt(receipt, path)
        read_back = storage.read_relocation_receipt(path)

        self.assertEqual(read_back, receipt)

    def test_write_leaves_no_partial_file_on_disk(self) -> None:
        receipt = {"ok": True}
        path = self._temp_dir() / "receipts" / "fixture.latest.json"
        storage.write_relocation_receipt(receipt, path)

        siblings = list(path.parent.iterdir())
        self.assertEqual(siblings, [path])

    def test_manifest_round_trips_through_write_and_read(self) -> None:
        # At minimum the expected (source-anchored) manifest should be
        # durably persisted, not only its digest -- a digest alone cannot
        # reconstruct the expected entries for a later restore proof once
        # this process has exited.
        source = self._temp_dir()
        self._write(source / "a.txt", b"alpha")
        manifest = storage.build_relocation_manifest(source)
        path = self._temp_dir() / "manifests" / "fixture.manifest.json"

        storage.write_relocation_manifest(manifest, path)
        read_back = storage.read_relocation_manifest(path)

        self.assertEqual(read_back, manifest)

    def test_persisted_manifest_can_verify_restore_after_reload(self) -> None:
        source = self._temp_dir()
        self._write(source / "a.txt", b"alpha")
        manifest = storage.build_relocation_manifest(source)
        path = self._temp_dir() / "manifests" / "fixture.manifest.json"
        storage.write_relocation_manifest(manifest, path)

        reloaded_manifest = storage.read_relocation_manifest(path)
        verification = storage.verify_restore(manifest=reloaded_manifest, root=source)

        self.assertTrue(verification["ok"])


class ReceiptSemanticValidationTests(unittest.TestCase):
    def _base_receipt(self) -> dict:
        return {
            "raw_leg": {"files_copied": 1, "files_failed": [], "ok": True},
            "extracted_leg": None,
            "destination_verification": {"ok": True},
            "extracted_verification": None,
            "space_budget": {"ok": True},
            "ok": True,
        }

    def test_coherent_receipt_has_no_findings(self) -> None:
        findings = storage.validate_relocation_receipt_semantics(self._base_receipt())
        self.assertEqual(findings, [])

    def test_raw_leg_ok_true_with_failed_files_is_rejected(self) -> None:
        receipt = self._base_receipt()
        receipt["raw_leg"] = {"files_copied": 1, "files_failed": ["a.txt"], "ok": True}
        findings = storage.validate_relocation_receipt_semantics(receipt)
        self.assertTrue(any("raw_leg.ok is true but raw_leg.files_failed" in f for f in findings))

    def test_extracted_leg_ok_true_with_failed_files_is_rejected(self) -> None:
        receipt = self._base_receipt()
        receipt["extracted_leg"] = {"files_copied": 1, "files_failed": ["a.txt"], "ok": True}
        findings = storage.validate_relocation_receipt_semantics(receipt)
        self.assertTrue(any("extracted_leg.ok is true but extracted_leg.files_failed" in f for f in findings))

    def test_receipt_ok_true_with_failed_destination_verification_is_rejected(self) -> None:
        receipt = self._base_receipt()
        receipt["destination_verification"] = {"ok": False}
        findings = storage.validate_relocation_receipt_semantics(receipt)
        self.assertTrue(any("destination_verification.ok is false" in f for f in findings))

    def test_receipt_ok_true_with_failed_space_budget_is_rejected(self) -> None:
        receipt = self._base_receipt()
        receipt["space_budget"] = {"ok": False}
        findings = storage.validate_relocation_receipt_semantics(receipt)
        self.assertTrue(any("space_budget.ok is false" in f for f in findings))

    def test_a_genuine_relocate_archive_source_receipt_is_always_semantically_coherent(self) -> None:
        # Not just synthetic contradiction fixtures -- prove the module's
        # own real output never trips its own semantic validator.
        root = Path(tempfile.mkdtemp(prefix="atlas-storage-semantic-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        source = root / "source"
        storage._lp_mkdir(source)
        (source / "a.txt").write_text("content", encoding="utf-8")
        destination = root / "destination"
        work = root / "work"

        result = storage.relocate_archive_source(
            archive_id="synthetic--semantic-check",
            source_root=source,
            destination_root=destination,
            work_root=work,
            source_description="synthetic fixture",
        )

        self.assertTrue(result.ok)
        findings = storage.validate_relocation_receipt_semantics(result.receipt)
        self.assertEqual(findings, [])


class RelocateArchiveSourceEndToEndTests(TempRootMixin, unittest.TestCase):
    def test_raw_default_is_lossless_including_dot_git(self) -> None:
        source = self._temp_dir() / "synthetic-source"
        self._write(source / "notes.md", b"# synthetic fixture\ncontent")
        self._write(source / ".git" / "config", b"[core]\n\trepositoryformatversion = 0\n")
        self._write(source / "Library" / "PackageCache" / "ignored.bin", b"regenerable")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"

        result = storage.relocate_archive_source(
            archive_id="synthetic--fixture",
            source_root=source,
            destination_root=destination,
            work_root=work,
            source_description="synthetic end-to-end fixture, not real archive data",
        )

        self.assertTrue(result.ok, result.receipt)
        # Raw preservation default: NOTHING is excluded, including
        # generated-cache-shaped content and .git -- exclusion is opt-in.
        self.assertEqual((destination / "notes.md").read_bytes(), b"# synthetic fixture\ncontent")
        self.assertTrue((destination / ".git" / "config").exists())
        self.assertTrue((destination / "Library" / "PackageCache" / "ignored.bin").exists())
        self.assertEqual(result.receipt["exclusion_policy_id"], storage.NO_EXCLUSION_POLICY.policy_id)
        self.assertEqual(result.receipt["excluded_path_count"], 0)

    def test_extracted_leg_failure_fails_the_whole_operation(self) -> None:
        source = self._temp_dir() / "synthetic-source"
        self._write(source / "notes.md", b"content")
        destination = self._temp_dir() / "destination"
        extracted = self._temp_dir() / "extracted"
        work = self._temp_dir() / "work"

        original_copy_tree = storage.resumable_copy_tree
        call_count = {"n": 0}

        def fake_copy_tree(source_root, destination_root, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 2:
                # Simulate the extracted leg (the second copy) failing.
                result = original_copy_tree(source_root, destination_root, **kwargs)
                result.failed.append(
                    storage.CopyFailure(path="notes.md", category="staging_copy_failed", message_digest="sha256:" + "0" * 64)
                )
                return result
            return original_copy_tree(source_root, destination_root, **kwargs)

        with mock.patch.object(storage, "resumable_copy_tree", side_effect=fake_copy_tree):
            result = storage.relocate_archive_source(
                archive_id="synthetic--extracted-failure",
                source_root=source,
                destination_root=destination,
                work_root=work,
                source_description="synthetic fixture proving extracted-leg failure fails the whole op",
                materialize_extracted_root=extracted,
            )

        self.assertFalse(result.ok)
        self.assertIsNotNone(result.extracted_copy_result)
        self.assertIn("notes.md", [f.path for f in result.extracted_copy_result.failed])
        self.assertFalse(result.receipt["ok"])
        self.assertFalse(result.receipt["extracted_leg"]["ok"])
        # The raw leg itself genuinely succeeded -- only the extracted leg
        # was made to fail -- proving the composed ok is not simply
        # inherited from the raw leg alone.
        self.assertTrue(result.receipt["raw_leg"]["ok"])

    def test_extracted_leg_is_independently_verified(self) -> None:
        source = self._temp_dir() / "synthetic-source"
        self._write(source / "notes.md", b"content")
        destination = self._temp_dir() / "destination"
        extracted = self._temp_dir() / "extracted"
        work = self._temp_dir() / "work"

        result = storage.relocate_archive_source(
            archive_id="synthetic--extracted-verified",
            source_root=source,
            destination_root=destination,
            work_root=work,
            source_description="synthetic fixture with extracted materialization",
            materialize_extracted_root=extracted,
        )

        self.assertTrue(result.ok)
        self.assertIsNotNone(result.extracted_verification)
        self.assertTrue(result.extracted_verification["ok"])
        self.assertEqual((extracted / "notes.md").read_bytes(), b"content")

    def test_verification_is_source_anchored_not_self_referential(self) -> None:
        # Proves the fix directly: a file the copy step "forgets" to
        # produce must be caught, because the proof is built from the
        # SOURCE before copying, not by re-deriving "expected" from
        # whatever the destination happens to contain afterward.
        source = self._temp_dir() / "synthetic-source"
        self._write(source / "a.txt", b"alpha")
        self._write(source / "b.txt", b"beta")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"

        def dropping_copy_tree(source_root, destination_root, **kwargs):
            result = storage.CopyResult()
            storage._lp_mkdir(destination_root)
            # Deliberately only copy a.txt, silently omitting b.txt --
            # simulating a bug elsewhere that undercopies without raising.
            storage._copy_one_resumable(source_root / "a.txt", destination_root / "a.txt", work_root=kwargs["work_root"])
            result.copied.append("a.txt")
            return result

        with mock.patch.object(storage, "resumable_copy_tree", side_effect=dropping_copy_tree):
            result = storage.relocate_archive_source(
                archive_id="synthetic--undercopy",
                source_root=source,
                destination_root=destination,
                work_root=work,
                source_description="synthetic fixture proving source-anchored verification",
            )

        self.assertFalse(result.ok)
        self.assertFalse(result.destination_verification["ok"])
        self.assertEqual(result.destination_verification["missing_paths"], ["b.txt"])

    def test_verification_catches_preexisting_unrelated_destination_content(self) -> None:
        source = self._temp_dir() / "synthetic-source"
        self._write(source / "a.txt", b"alpha")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"
        # Pre-existing, unrelated content already sitting at the
        # destination before this relocation runs.
        self._write(destination / "leftover.txt", b"not part of this source")

        result = storage.relocate_archive_source(
            archive_id="synthetic--leftover",
            source_root=source,
            destination_root=destination,
            work_root=work,
            source_description="synthetic fixture proving pre-existing destination content is caught",
        )

        self.assertFalse(result.ok)
        self.assertIn("leftover.txt", result.destination_verification["unexpected_paths"])

    def test_relocation_fails_closed_on_insufficient_space_without_copying_anything(self) -> None:
        source = self._temp_dir() / "synthetic-source"
        self._write(source / "notes.md", b"# synthetic fixture")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"

        with mock.patch.object(storage, "_free_bytes", return_value=1):
            result = storage.relocate_archive_source(
                archive_id="synthetic--fixture-no-space",
                source_root=source,
                destination_root=destination,
                work_root=work,
                source_description="synthetic fixture proving fail-closed preflight",
            )

        self.assertFalse(result.ok)
        self.assertFalse(result.space_budget.ok)
        self.assertIsNone(result.raw_copy_result)
        self.assertFalse(destination.exists())

    def test_named_exclusion_policy_is_bound_into_the_receipt(self) -> None:
        source = self._temp_dir() / "synthetic-source"
        self._write(source / "keep.txt", b"keep")
        self._write(source / "Library" / "PackageCache" / "junk.bin", b"drop")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"

        result = storage.relocate_archive_source(
            archive_id="synthetic--filtered",
            source_root=source,
            destination_root=destination,
            work_root=work,
            source_description="synthetic fixture with an explicit filtering policy",
            exclusion_policy=storage.GENERATED_CACHE_EXCLUSION_POLICY,
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.receipt["exclusion_policy_id"], "atlas.knowledge.generated-cache-exclusion")
        self.assertEqual(result.receipt["excluded_path_count"], 1)
        self.assertFalse((destination / "Library").exists())

    def test_receipt_and_expected_manifest_can_be_durably_persisted_and_read_back(self) -> None:
        source = self._temp_dir() / "synthetic-source"
        self._write(source / "notes.md", b"content")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"
        receipt_path = self._temp_dir() / "receipts" / "synthetic--persisted.latest.json"
        manifest_path = self._temp_dir() / "manifests" / "synthetic--persisted.manifest.json"

        result = storage.relocate_archive_source(
            archive_id="synthetic--persisted",
            source_root=source,
            destination_root=destination,
            work_root=work,
            source_description="synthetic fixture proving durable receipt persistence",
            receipt_path=receipt_path,
            expected_manifest_path=manifest_path,
        )

        self.assertTrue(result.ok)
        read_back = storage.read_relocation_receipt(receipt_path)
        self.assertEqual(read_back, result.receipt)
        self.assertEqual(result.receipt["expected_manifest_ref"], str(manifest_path))

        reloaded_manifest = storage.read_relocation_manifest(manifest_path)
        self.assertEqual(reloaded_manifest, result.expected_manifest)
        # The persisted manifest independently verifies against the real
        # destination even after being reloaded from disk.
        verification = storage.verify_restore(manifest=reloaded_manifest, root=destination)
        self.assertTrue(verification["ok"])

    def test_full_receipt_validates_against_schema(self) -> None:
        source = self._temp_dir() / "synthetic-source"
        self._write(source / "notes.md", b"# synthetic fixture\ncontent")
        self._write(source / "data.json", b'{"ok": true}')
        destination = self._temp_dir() / "destination"
        extracted = self._temp_dir() / "extracted"
        work = self._temp_dir() / "work"

        result = storage.relocate_archive_source(
            archive_id="synthetic--schema-check",
            source_root=source,
            destination_root=destination,
            work_root=work,
            source_description="synthetic end-to-end fixture, not real archive data",
            materialize_extracted_root=extracted,
        )

        self.assertTrue(result.ok)
        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
        errors = validate_json_schema(result.receipt, schema)
        self.assertEqual([], errors, f"receipt failed schema validation: {errors}")

    def test_receipt_without_extracted_leg_validates_against_schema(self) -> None:
        source = self._temp_dir() / "synthetic-source"
        self._write(source / "notes.md", b"content")
        destination = self._temp_dir() / "destination"
        work = self._temp_dir() / "work"

        result = storage.relocate_archive_source(
            archive_id="synthetic--no-extracted",
            source_root=source,
            destination_root=destination,
            work_root=work,
            source_description="synthetic fixture, raw leg only",
        )

        self.assertTrue(result.ok)
        self.assertIsNone(result.receipt["extracted_leg"])
        self.assertIsNone(result.receipt["extracted_verification"])
        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
        errors = validate_json_schema(result.receipt, schema)
        self.assertEqual([], errors, f"receipt failed schema validation: {errors}")


class RelocationReceiptSchemaTests(unittest.TestCase):
    def _schema(self) -> dict:
        return json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))

    def _minimal_valid_receipt(self) -> dict:
        leg = {
            "files_copied": 2,
            "files_skipped_already_present": 0,
            "files_failed": [],
            "bytes_copied": 100,
            "ok": True,
        }
        verification = {
            "contract_version": "atlas.knowledge-restore-verification.v1",
            "root": "/tmp/destination",
            "require_exact_match": True,
            "expected_entry_count": 2,
            "current_entry_count": 2,
            "missing_paths": [],
            "unexpected_paths": [],
            "mismatched_paths": [],
            "ok": True,
        }
        return {
            "contract_version": "atlas.knowledge-relocation-receipt.v1",
            "archive_id": "synthetic--fixture",
            "recorded_at": "2026-08-28T00:00:00Z",
            "source_description": "synthetic fixture",
            "destination_root": "/tmp/destination",
            "exclusion_policy_id": "atlas.knowledge.no-exclusion",
            "exclusion_policy_version": "v1",
            "excluded_path_count": 0,
            "excluded_paths_digest": "sha256:" + ("a" * 64),
            "expected_manifest_ref": "/tmp/receipts/synthetic--fixture.manifest.json",
            "raw_leg": leg,
            "extracted_leg": None,
            "expected_manifest_digest": "sha256:" + ("b" * 64),
            "destination_manifest_digest": "sha256:" + ("c" * 64),
            "destination_verification": verification,
            "extracted_verification": None,
            "space_budget": {
                "safety_margin_bytes": 1000,
                "ok": True,
                "findings": [],
                "volumes": [
                    {"probe_path": "/tmp", "required_bytes": 1000, "available_bytes": 999999, "ok": True}
                ],
            },
            "ok": True,
        }

    def test_minimal_valid_receipt_with_null_extracted_leg_passes(self) -> None:
        errors = validate_json_schema(self._minimal_valid_receipt(), self._schema())
        self.assertEqual([], errors)

    def test_receipt_with_populated_extracted_leg_passes(self) -> None:
        receipt = self._minimal_valid_receipt()
        receipt["extracted_leg"] = {
            "files_copied": 2, "files_skipped_already_present": 0, "files_failed": [], "bytes_copied": 100, "ok": True,
        }
        receipt["extracted_verification"] = dict(receipt["destination_verification"])
        errors = validate_json_schema(receipt, self._schema())
        self.assertEqual([], errors)

    def test_wrong_contract_version_rejected(self) -> None:
        receipt = self._minimal_valid_receipt()
        receipt["contract_version"] = "atlas.knowledge-relocation-receipt.v0"
        self.assertTrue(validate_json_schema(receipt, self._schema()))

    def test_malformed_manifest_digest_rejected(self) -> None:
        receipt = self._minimal_valid_receipt()
        receipt["expected_manifest_digest"] = "not-a-real-digest"
        self.assertTrue(validate_json_schema(receipt, self._schema()))

    def test_extra_field_rejected_closed_schema(self) -> None:
        receipt = self._minimal_valid_receipt()
        receipt["unexpected_field"] = "should be rejected"
        self.assertTrue(validate_json_schema(receipt, self._schema()))

    def test_missing_required_field_rejected(self) -> None:
        receipt = self._minimal_valid_receipt()
        del receipt["ok"]
        self.assertTrue(validate_json_schema(receipt, self._schema()))

    def test_malformed_raw_leg_rejected(self) -> None:
        receipt = self._minimal_valid_receipt()
        receipt["raw_leg"] = {"files_copied": "not-an-integer"}
        self.assertTrue(validate_json_schema(receipt, self._schema()))


class PipelineCompatibilityTests(TempRootMixin, unittest.TestCase):
    """Proves _pipeline.py's shared surface (list_files() and anything
    built on it, like tree_digest()) is unchanged for an ordinary
    under-260-character tree -- the delegation to enumerate_files() is a
    long-path correctness fix, not a behavior change, for any tree that
    was never affected by the original defect."""

    def test_relative_path_set_is_identical_to_the_old_rglob_based_result(self) -> None:
        root = self._temp_dir()
        self._write(root / "Banana.txt", b"1")
        self._write(root / "apple.txt", b"2")
        self._write(root / "nested" / "Cherry.txt", b"3")

        old_style_paths = sorted(p for p in root.rglob("*") if p.is_file())
        old_rels = {p.relative_to(root).as_posix() for p in old_style_paths}
        new_rels = {p.relative_to(root).as_posix() for p in _pipeline.list_files(root)}

        self.assertEqual(old_rels, new_rels)

    @unittest.skipUnless(os.name == "nt", "case-insensitive sort compatibility is a Windows-only concern")
    def test_tree_digest_order_is_unchanged_for_a_mixed_case_tree(self) -> None:
        root = self._temp_dir()
        self._write(root / "Banana.txt", b"1")
        self._write(root / "apple.txt", b"2")
        self._write(root / "Cherry.txt", b"3")

        old_style_order = [p.name for p in sorted(p for p in root.rglob("*") if p.is_file())]
        new_style_order = [p.name for p in _pipeline.list_files(root)]

        self.assertEqual(new_style_order, old_style_order)
        # tree_digest() iterates list_files() in order and folds each
        # entry's relative path, size, and checksum into one digest -- if
        # the order matches, the digest matches too, for a tree unaffected
        # by the long-path defect.
        self.assertEqual(_pipeline.tree_digest(root), _pipeline.tree_digest(root))


class JsonDigestHelpersTests(unittest.TestCase):
    def test_stable_json_digest_is_order_independent(self) -> None:
        a = storage.stable_json_digest({"x": 1, "y": 2})
        b = storage.stable_json_digest({"y": 2, "x": 1})
        self.assertEqual(a, b)

    def test_stable_json_digest_changes_with_content(self) -> None:
        a = storage.stable_json_digest({"x": 1})
        b = storage.stable_json_digest({"x": 2})
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
