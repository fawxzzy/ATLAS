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
        self.assertEqual(rels, sorted(rels))
        self.assertEqual(set(rels), {"a.txt", "a/1.txt", "b/2.txt"})

    def test_enumerate_files_on_missing_root_returns_empty(self) -> None:
        missing = self._temp_dir() / "does-not-exist"
        self.assertEqual(storage.enumerate_files(missing), [])

    def test_enumerate_files_finds_a_genuinely_long_path_entry(self) -> None:
        # Construct a path whose full length exceeds Windows' classic
        # 260-character MAX_PATH, to directly prove enumerate_files() can
        # see it -- not just assume the \\?\ prefixing works.
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


class SpacePreflightTests(TempRootMixin, unittest.TestCase):
    def _fixture(self) -> tuple[Path, Path, Path]:
        source = self._temp_dir() / "source"
        self._write(source / "a.bin", b"x" * 1000)
        self._write(source / "b.bin", b"y" * 2000)
        storage_root = self._temp_dir() / "storage"
        work_root = self._temp_dir() / "work"
        return source, storage_root, work_root

    def test_preflight_ok_when_space_is_sufficient(self) -> None:
        source, storage_root, work_root = self._fixture()
        with mock.patch.object(storage, "_free_bytes", return_value=10 * 1024 * 1024 * 1024):
            budget = storage.preflight_space_budget(
                source_root=source, storage_root=storage_root, work_root=work_root
            )
        self.assertTrue(budget.ok)
        self.assertEqual(budget.findings, [])

    def test_preflight_fails_closed_when_storage_root_space_is_insufficient(self) -> None:
        source, storage_root, work_root = self._fixture()
        with mock.patch.object(storage, "_free_bytes", return_value=10):
            budget = storage.preflight_space_budget(
                source_root=source, storage_root=storage_root, work_root=work_root
            )
        self.assertFalse(budget.ok)
        self.assertTrue(any("insufficient_storage_root_space" in f for f in budget.findings))

    def test_preflight_doubles_storage_requirement_when_materializing_extracted(self) -> None:
        source, storage_root, work_root = self._fixture()
        with mock.patch.object(storage, "_free_bytes", return_value=10 * 1024 * 1024 * 1024):
            raw_only = storage.preflight_space_budget(
                source_root=source, storage_root=storage_root, work_root=work_root,
                materialize_extracted=False,
            )
            with_extracted = storage.preflight_space_budget(
                source_root=source, storage_root=storage_root, work_root=work_root,
                materialize_extracted=True,
            )
        self.assertGreater(
            with_extracted.required_storage_bytes - with_extracted.safety_margin_bytes,
            raw_only.required_storage_bytes - raw_only.safety_margin_bytes,
        )

    def test_preflight_excludes_generated_cache_from_the_budget(self) -> None:
        source, storage_root, work_root = self._fixture()
        self._write(source / "Library" / "PackageCache" / "junk.bin", b"z" * 5000)
        with mock.patch.object(storage, "_free_bytes", return_value=10 * 1024 * 1024 * 1024):
            without_exclusion = storage.preflight_space_budget(
                source_root=source, storage_root=storage_root, work_root=work_root, exclude=None,
            )
            with_exclusion = storage.preflight_space_budget(
                source_root=source, storage_root=storage_root, work_root=work_root,
                exclude=storage.is_generated_cache_path,
            )
        self.assertLess(
            with_exclusion.required_storage_bytes, without_exclusion.required_storage_bytes
        )


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
        # Simulate an interruption: one file already fully present at the
        # destination (as if a prior run completed it before being killed),
        # the other not yet copied at all.
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
            # Force exactly one checksum mismatch to simulate a corrupted
            # staged copy, then behave normally afterward.
            corrupt_then_restore.calls += 1
            if corrupt_then_restore.calls == 2:
                return "sha256:deliberately-wrong"
            return original(path)

        corrupt_then_restore.calls = 0
        with mock.patch.object(storage, "file_checksum", side_effect=corrupt_then_restore):
            result = storage.resumable_copy_tree(source, destination, work_root=work)

        self.assertEqual(result.failed, ["a.txt"])
        self.assertFalse((destination / "a.txt").exists())


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

    def test_verify_restore_detects_unexpected_extra_file(self) -> None:
        root = self._temp_dir()
        self._write(root / "a.txt", b"alpha")
        manifest = storage.build_relocation_manifest(root)
        self._write(root / "new.txt", b"unexpected")

        verification = storage.verify_restore(manifest=manifest, root=root)

        # Extra content is surfaced but does not by itself fail 'ok' -- a
        # manifest recorded before new legitimate content was added should
        # not be treated as data loss.
        self.assertTrue(verification["ok"])
        self.assertEqual(verification["unexpected_paths"], ["new.txt"])

    def test_manifest_is_junction_independent_when_root_is_relocated(self) -> None:
        # A manifest built at one location must reconcile identically when
        # the same content is reachable at a different path -- proving the
        # manifest itself carries no path/junction-specific assumption.
        original_root = self._temp_dir()
        self._write(original_root / "sub" / "a.txt", b"alpha")
        manifest = storage.build_relocation_manifest(original_root)

        relocated_root = self._temp_dir()
        shutil.copytree(original_root, relocated_root, dirs_exist_ok=True)

        verification = storage.verify_restore(manifest=manifest, root=relocated_root)
        self.assertTrue(verification["ok"])


class RelocateArchiveSourceEndToEndTests(TempRootMixin, unittest.TestCase):
    def test_synthetic_end_to_end_relocation_raw_only_by_default(self) -> None:
        source = self._temp_dir() / "synthetic-source"
        self._write(source / "notes.md", b"# synthetic fixture\ncontent")
        self._write(source / "data.json", b'{"ok": true}')
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

        self.assertTrue(result.ok)
        self.assertTrue(result.space_budget.ok)
        self.assertEqual(set(result.copy_result.copied), {"notes.md", "data.json"})
        self.assertFalse((destination / "Library").exists())
        self.assertEqual(result.manifest["entry_count"], 2)
        self.assertTrue(result.receipt["ok"])
        self.assertEqual(result.receipt["contract_version"], storage.RELOCATION_RECEIPT_VERSION)
        self.assertTrue(result.restore_verification["ok"])

        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
        errors = validate_json_schema(result.receipt, schema)
        self.assertEqual([], errors, f"receipt failed schema validation: {errors}")

    def test_synthetic_end_to_end_relocation_with_selective_extracted_materialization(self) -> None:
        source = self._temp_dir() / "synthetic-source"
        self._write(source / "notes.md", b"# synthetic fixture")
        destination = self._temp_dir() / "destination"
        extracted = self._temp_dir() / "extracted"
        work = self._temp_dir() / "work"

        result = storage.relocate_archive_source(
            archive_id="synthetic--fixture-extracted",
            source_root=source,
            destination_root=destination,
            work_root=work,
            source_description="synthetic end-to-end fixture with extracted materialization",
            materialize_extracted_root=extracted,
        )

        self.assertTrue(result.ok)
        self.assertEqual((destination / "notes.md").read_bytes(), b"# synthetic fixture")
        self.assertEqual((extracted / "notes.md").read_bytes(), b"# synthetic fixture")

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
        self.assertIsNone(result.copy_result)
        self.assertFalse(destination.exists())


class RelocationReceiptSchemaTests(unittest.TestCase):
    def _schema(self) -> dict:
        return json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))

    def _minimal_valid_receipt(self) -> dict:
        return {
            "contract_version": "atlas.knowledge-relocation-receipt.v1",
            "archive_id": "synthetic--fixture",
            "recorded_at": "2026-08-27T00:00:00Z",
            "source_description": "synthetic fixture",
            "destination_root": "/tmp/destination",
            "files_copied": 2,
            "files_skipped_already_present": 0,
            "files_failed": [],
            "bytes_copied": 100,
            "manifest_entry_count": 2,
            "manifest_total_bytes": 100,
            "manifest_digest": "sha256:" + ("a" * 64),
            "space_budget": {
                "required_storage_bytes": 1000,
                "required_work_bytes": 100,
                "available_storage_bytes": 999999,
                "available_work_bytes": 999999,
                "ok": True,
                "findings": [],
            },
            "ok": True,
        }

    def test_minimal_valid_receipt_passes(self) -> None:
        errors = validate_json_schema(self._minimal_valid_receipt(), self._schema())
        self.assertEqual([], errors)

    def test_wrong_contract_version_rejected(self) -> None:
        receipt = self._minimal_valid_receipt()
        receipt["contract_version"] = "atlas.knowledge-relocation-receipt.v0"
        self.assertTrue(validate_json_schema(receipt, self._schema()))

    def test_malformed_manifest_digest_rejected(self) -> None:
        receipt = self._minimal_valid_receipt()
        receipt["manifest_digest"] = "not-a-real-digest"
        self.assertTrue(validate_json_schema(receipt, self._schema()))

    def test_extra_field_rejected_closed_schema(self) -> None:
        receipt = self._minimal_valid_receipt()
        receipt["unexpected_field"] = "should be rejected"
        self.assertTrue(validate_json_schema(receipt, self._schema()))

    def test_missing_required_field_rejected(self) -> None:
        receipt = self._minimal_valid_receipt()
        del receipt["ok"]
        self.assertTrue(validate_json_schema(receipt, self._schema()))


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
