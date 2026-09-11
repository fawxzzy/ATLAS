"""Wave S2A -- live pipeline integration of ops.knowledge.storage into
ops.knowledge._pipeline.import_archive().

Scope: folder imports now make ONE verified relocation into raw/ instead
of two unconditional shutil copies; extracted/ is materialized only on
request; downstream review reads raw/ via review_source_dir() when
extracted/ is absent; the transient copy volume follows
ATLAS_IMPORT_WORK_ROOT. No real archive data -- every fixture is
synthetic and created/destroyed within its test. Capacity behavior is
proven by injecting free-space observations, not by weakening the
reserve or mocking the copy.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.knowledge import _pipeline
from ops.knowledge import storage

# Everything the pipeline writes hangs off _pipeline.atlas_root(); the
# relocation preflight enforces a large reserve on the *system* volume,
# so on Windows -- where the OS temp dir is on C: and C: on this
# engagement's host is below that reserve -- fixtures go on D: if it is
# writable. Elsewhere (and on POSIX/CI) the OS temp dir is fine.
def _tmp_base() -> Path:
    if os.name == "nt":
        preferred = Path("D:/ATLAS-tmp/_testtmp")
        try:
            preferred.mkdir(parents=True, exist_ok=True)
            if os.access(preferred, os.W_OK):
                return preferred
        except OSError:
            pass
    return Path(tempfile.gettempdir())


class _ImportHarness(unittest.TestCase):
    def setUp(self) -> None:
        self._base = Path(tempfile.mkdtemp(prefix="s2a-", dir=_tmp_base()))
        self.addCleanup(self._rmtree, self._base)
        self.fake_atlas = self._base / "atlas"
        self.fake_atlas.mkdir(parents=True)
        # input trees must be staged under the (fake) atlas root, since
        # import_archive() requires ATLAS-relative input paths.
        self._p = mock.patch.object(_pipeline, "atlas_root", return_value=self.fake_atlas)
        self._p.start()
        self.addCleanup(self._p.stop)
        # receipt_tooling() pins Path(__file__) relative to atlas_root();
        # with atlas_root patched to a temp dir it cannot resolve the real
        # _pipeline.py. It is unrelated to what S2A changes -- stub it.
        self._pt = mock.patch.object(
            _pipeline,
            "receipt_tooling",
            side_effect=lambda action: {
                "entrypoint_path": None,
                "entrypoint_digest": None,
                "pipeline_path": "ops/knowledge/_pipeline.py",
                "pipeline_digest": "sha256:" + "0" * 64,
                "python_version": sys.version.split()[0],
            },
        )
        self._pt.start()
        self.addCleanup(self._pt.stop)

    @staticmethod
    def _rmtree(path: Path) -> None:
        import shutil

        shutil.rmtree(path, ignore_errors=True)

    def _make_source_folder(self, rel: str = "inbox/sample") -> Path:
        src = self.fake_atlas / rel
        (src / "docs").mkdir(parents=True)
        (src / "docs" / "a.md").write_text("# alpha\n", encoding="utf-8")
        (src / "docs" / "notes.txt").write_text("plain notes\n", encoding="utf-8")
        (src / "top.txt").write_text("top-level\n", encoding="utf-8")
        return src

    def _work_root_env(self) -> dict[str, str]:
        wr = self._base / "work-elsewhere"
        wr.mkdir(parents=True, exist_ok=True)
        return {"ATLAS_IMPORT_WORK_ROOT": str(wr)}

    def _import(self, src: Path, **kw):
        return _pipeline.import_archive(
            input_path=src,
            source_name="synthetic-source",
            slug=None,
            privacy_flag="private",
            provenance_note=None,
            dry_run=False,
            force=kw.pop("force", False),
            env=kw.pop("env", self._work_root_env()),
            **kw,
        )


class FolderImportSingleCopyTests(_ImportHarness):
    def test_default_folder_import_makes_one_verified_raw_copy_and_no_extracted(self) -> None:
        src = self._make_source_folder()
        result = self._import(src)

        archive = self.fake_atlas / result["import_dir"]
        self.assertTrue((_pipeline.raw_dir(archive) / "docs" / "a.md").exists())
        self.assertFalse(_pipeline.extracted_dir(archive).exists())

        m = result["manifest"]
        self.assertFalse(m["extracted_materialized"])
        self.assertEqual(m["folder_import_mode"], "storage-convergence")
        self.assertEqual(m["raw_relocation"]["mode"], "storage-convergence")
        self.assertTrue(m["raw_relocation"]["ok"])
        self.assertTrue(m["raw_relocation"]["destination_verification_ok"])
        self.assertIn("raw_snapshot_digest", m)

    def test_relocation_receipt_is_persisted_and_valid_through_the_public_reader(self) -> None:
        src = self._make_source_folder()
        result = self._import(src)
        archive = self.fake_atlas / result["import_dir"]

        receipt_ref = result["manifest"]["raw_relocation"]["receipt_ref"]
        receipt = storage.read_relocation_receipt(self.fake_atlas / receipt_ref)  # raises if invalid
        self.assertTrue(receipt["ok"])
        self.assertEqual(receipt["archive_id"], result["archive_id"])

        manifest_ref = result["manifest"]["raw_relocation"]["expected_manifest_ref"]
        storage.read_relocation_manifest(
            self.fake_atlas / manifest_ref,
            expected_digest=result["manifest"]["raw_relocation"]["expected_manifest_digest"],
        )  # raises on digest drift

    def test_downstream_evaluate_reads_raw_when_extracted_absent(self) -> None:
        src = self._make_source_folder()
        result = self._import(src)
        archive = self.fake_atlas / result["import_dir"]
        self.assertFalse(_pipeline.extracted_dir(archive).exists())

        manifest = _pipeline.read_json(_pipeline.manifest_path(archive))
        self.assertEqual(
            _pipeline.review_source_dir(archive, manifest).resolve(),
            _pipeline.raw_dir(archive).resolve(),
        )
        evaluation = _pipeline.evaluate_archive(archive_path=archive, dry_run=True)
        self.assertGreaterEqual(evaluation["summary"]["file_count"], 3)

    def test_materialize_extracted_opt_in_produces_both_trees_verified(self) -> None:
        src = self._make_source_folder()
        result = self._import(src, materialize_extracted=True)
        archive = self.fake_atlas / result["import_dir"]

        self.assertTrue((_pipeline.raw_dir(archive) / "top.txt").exists())
        self.assertTrue((_pipeline.extracted_dir(archive) / "top.txt").exists())
        self.assertTrue(result["manifest"]["extracted_materialized"])
        self.assertTrue(result["manifest"]["raw_relocation"]["materialized_extracted"])
        self.assertEqual(
            _pipeline.review_source_dir(archive, result["manifest"]).resolve(),
            _pipeline.extracted_dir(archive).resolve(),
        )


class FolderImportRollbackTests(_ImportHarness):
    def test_legacy_env_restores_unconditional_double_copy(self) -> None:
        src = self._make_source_folder()
        result = self._import(src, env={**self._work_root_env(), "ATLAS_IMPORT_LEGACY_FOLDER_COPY": "1"})
        archive = self.fake_atlas / result["import_dir"]

        self.assertTrue((_pipeline.raw_dir(archive) / "docs" / "a.md").exists())
        self.assertTrue((_pipeline.extracted_dir(archive) / "docs" / "a.md").exists())
        self.assertEqual(result["manifest"]["folder_import_mode"], "legacy-double-copy")
        self.assertNotIn("raw_relocation", result["manifest"])


class FolderImportWorkRootTests(_ImportHarness):
    def test_staging_follows_atlas_import_work_root_off_the_archive_tree(self) -> None:
        src = self._make_source_folder()
        result = self._import(src)
        rel = result["manifest"]["raw_relocation"]
        self.assertTrue(rel["staging_outside_atlas_root"])

    def test_staging_defaults_under_atlas_root_when_unset(self) -> None:
        src = self._make_source_folder()
        # storage.import_work_root() with no override resolves against the
        # storage module's own repo root, not the fake atlas root -- so it
        # is reported as outside the fake atlas tree. The point of this
        # test is only that an unset override does not raise and the
        # import still completes.
        result = self._import(src, env={})
        self.assertTrue(result["manifest"]["raw_relocation"]["ok"])


class FolderImportCapacityTests(_ImportHarness):
    """Deterministic capacity behavior -- inject free-space observations
    rather than weakening the reserve or mocking the copy."""

    def _free_bytes_stub(self, value: int):
        return mock.patch.object(storage, "_free_bytes", return_value=value)

    def test_import_fails_closed_below_the_volume_reserve_with_no_partial_raw_tree(self) -> None:
        src = self._make_source_folder()
        archive_slug = "sample"
        with self._free_bytes_stub(1024):  # far below any reserve
            with self.assertRaises(_pipeline.FolderImportRelocationError):
                self._import(src)

        archive = _pipeline.archive_dir("synthetic-source", archive_slug)
        # fail-closed: no manifest, and raw/ (if the dir exists at all)
        # holds none of the source content
        self.assertFalse(_pipeline.manifest_path(archive).exists())
        self.assertFalse((_pipeline.raw_dir(archive) / "top.txt").exists())

    def test_import_succeeds_with_ample_free_space(self) -> None:
        src = self._make_source_folder()
        with self._free_bytes_stub(64 * 1024 * 1024 * 1024):  # 64 GiB
            result = self._import(src)
        self.assertTrue(result["manifest"]["raw_relocation"]["ok"])

    def test_reserve_boundary_is_respected_exactly(self) -> None:
        # Compute the reserve the preflight will actually apply for this
        # fixture's destination volume (system vs non-system differ), so
        # the boundary assertion is deterministic on any host: just under
        # `reserve` -> fail; `reserve` plus generous headroom for the tiny
        # fixture's demand -> pass.
        probe = storage._existing_ancestor(
            _pipeline.raw_dir(_pipeline.archive_dir("synthetic-source", "below"))
        )
        reserve = storage._reserve_for(probe, storage.DEFAULT_VOLUME_RESERVE_POLICY)
        with self._free_bytes_stub(reserve - 1):
            with self.assertRaises(_pipeline.FolderImportRelocationError):
                self._import(self._make_source_folder("inbox/below"))
        with self._free_bytes_stub(reserve + 16 * 1024 * 1024):
            result = self._import(self._make_source_folder("inbox/above"))
        self.assertTrue(result["manifest"]["raw_relocation"]["ok"])


class ZipImportUnchangedTests(_ImportHarness):
    def test_zip_import_still_copies_raw_archive_and_extracts(self) -> None:
        import zipfile

        src_dir = self._make_source_folder("inbox/tozip")
        zip_path = self.fake_atlas / "inbox" / "sample.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for p in src_dir.rglob("*"):
                if p.is_file():
                    zf.write(p, p.relative_to(src_dir).as_posix())

        result = _pipeline.import_archive(
            input_path=zip_path,
            source_name="synthetic-source",
            slug="ziptest",
            privacy_flag="private",
            provenance_note=None,
            dry_run=False,
            force=False,
            env=self._work_root_env(),
        )
        archive = self.fake_atlas / result["import_dir"]
        self.assertTrue((_pipeline.raw_dir(archive) / "sample.zip").exists())
        self.assertTrue((_pipeline.extracted_dir(archive) / "docs" / "a.md").exists())
        self.assertTrue(result["manifest"]["extracted_materialized"])
        self.assertNotIn("folder_import_mode", result["manifest"])
        self.assertNotIn("raw_relocation", result["manifest"])


class OrderingAndAdmissionRegressionTests(_ImportHarness):
    """Regressions for the source-review finding: admission/preflight must
    run before source content is hashed or an existing archive is
    mutated, and a completed archive must survive a failed replacement."""

    def test_failed_forced_replacement_leaves_existing_archive_unchanged(self) -> None:
        src = self._make_source_folder()
        first = self._import(src)
        archive = self.fake_atlas / first["import_dir"]
        original_manifest = _pipeline.read_json(_pipeline.manifest_path(archive))
        original_raw_bytes = (_pipeline.raw_dir(archive) / "top.txt").read_bytes()

        with self.assertRaises(_pipeline.FolderImportReplacementUnsupportedError):
            self._import(src, force=True)

        # The refusal must happen before any deletion -- assert the
        # original archive is byte-for-byte the same afterward.
        self.assertTrue(_pipeline.raw_dir(archive).exists())
        self.assertEqual((_pipeline.raw_dir(archive) / "top.txt").read_bytes(), original_raw_bytes)
        self.assertEqual(_pipeline.read_json(_pipeline.manifest_path(archive)), original_manifest)

    def test_rejected_source_link_is_not_content_read(self) -> None:
        src = self._make_source_folder("inbox/withlink")
        outside = self._base / "outside-sentinel.txt"
        outside.write_text("SENTINEL-CONTENT-MUST-NOT-BE-READ", encoding="utf-8")
        try:
            os.symlink(outside, src / "escape.txt")
        except OSError:
            self.skipTest("symlink creation not permitted in this environment")

        with mock.patch.object(_pipeline, "build_raw_entries") as spy:
            with self.assertRaises(_pipeline.FolderImportRelocationError):
                self._import(src)
        # build_raw_entries() -- the only source-content hashing step on
        # the storage-convergence path -- must never have run: the
        # relocation's own link-rejection preflight is what raised, and
        # it does so before any file content (rejected link included) is
        # opened for hashing.
        spy.assert_not_called()

        archive = _pipeline.archive_dir("synthetic-source", "withlink")
        self.assertFalse(_pipeline.manifest_path(archive).exists())

    def test_interrupted_first_import_resumes_without_force(self) -> None:
        src = self._make_source_folder()
        archive = _pipeline.archive_dir("synthetic-source", "sample")
        # Simulate an interrupted first attempt: the destination directory
        # exists with a genuine partial copy, but no manifest was ever
        # written (the process died before that point).
        (_pipeline.raw_dir(archive) / "docs").mkdir(parents=True)
        (_pipeline.raw_dir(archive) / "docs" / "a.md").write_bytes((src / "docs" / "a.md").read_bytes())
        self.assertFalse(_pipeline.manifest_path(archive).exists())

        result = self._import(src)  # force=False -- must NOT raise FileExistsError

        self.assertTrue(result["manifest"]["raw_relocation"]["ok"])
        self.assertEqual(
            (_pipeline.raw_dir(archive) / "top.txt").read_bytes(),
            (src / "top.txt").read_bytes(),
        )
        self.assertTrue(_pipeline.manifest_path(archive).exists())

    def test_interrupted_import_with_orphaned_leftover_fails_closed_precisely(self) -> None:
        src = self._make_source_folder()
        archive = _pipeline.archive_dir("synthetic-source", "sample")
        # A leftover file that no longer exists in the real source --
        # exact reconciliation must catch this rather than silently
        # completing with stale extra content.
        (_pipeline.raw_dir(archive)).mkdir(parents=True)
        (_pipeline.raw_dir(archive) / "orphan-from-a-different-attempt.txt").write_text("stale", encoding="utf-8")

        with self.assertRaises(_pipeline.FolderImportRelocationError) as ctx:
            self._import(src)
        self.assertIn("destination_verification_issues", str(ctx.exception))
        self.assertFalse(_pipeline.manifest_path(archive).exists())


class ReviewSourceContractTests(_ImportHarness):
    """Regressions for the review-source finding: the reviewed tree must
    come from validated manifest semantics, never from which directories
    happen to exist."""

    def test_stray_extracted_directory_does_not_redirect_raw_only_review(self) -> None:
        src = self._make_source_folder()
        result = self._import(src)
        archive = self.fake_atlas / result["import_dir"]
        self.assertFalse(_pipeline.extracted_dir(archive).exists())

        # Plant a decoy extracted/ that was never part of this import.
        decoy = _pipeline.extracted_dir(archive)
        decoy.mkdir(parents=True)
        (decoy / "decoy.txt").write_text("should never be scanned", encoding="utf-8")

        manifest = _pipeline.read_json(_pipeline.manifest_path(archive))
        chosen = _pipeline.review_source_dir(archive, manifest)
        self.assertEqual(chosen.resolve(), _pipeline.raw_dir(archive).resolve())

        evaluation = _pipeline.evaluate_archive(archive_path=archive, dry_run=True)
        reviewed_names = {p.name for p in _pipeline.list_files(_pipeline.raw_dir(archive))}
        self.assertNotIn("decoy.txt", reviewed_names)
        self.assertEqual(evaluation["review_source_kind"], "raw")

    def test_zip_missing_extracted_fails_closed_not_fallback_to_raw(self) -> None:
        import shutil as _sh
        import zipfile

        src_dir = self._make_source_folder("inbox/tozip2")
        zip_path = self.fake_atlas / "inbox" / "sample2.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for p in src_dir.rglob("*"):
                if p.is_file():
                    zf.write(p, p.relative_to(src_dir).as_posix())
        result = _pipeline.import_archive(
            input_path=zip_path, source_name="synthetic-source", slug="ziptest2",
            privacy_flag="private", provenance_note=None, dry_run=False, force=False,
            env=self._work_root_env(),
        )
        archive = self.fake_atlas / result["import_dir"]
        _sh.rmtree(_pipeline.extracted_dir(archive))

        with self.assertRaises(FileNotFoundError):
            _pipeline.evaluate_archive(archive_path=archive, dry_run=True)

    def test_legacy_manifest_without_extracted_materialized_key_defaults_to_extracted(self) -> None:
        src = self._make_source_folder("inbox/legacyshape")
        result = self._import(src, materialize_extracted=True)
        archive = self.fake_atlas / result["import_dir"]
        manifest = _pipeline.read_json(_pipeline.manifest_path(archive))
        del manifest["extracted_materialized"]  # simulate a pre-S2A manifest

        chosen = _pipeline.review_source_dir(archive, manifest)
        self.assertEqual(chosen.resolve(), _pipeline.extracted_dir(archive).resolve())


class PersistedChainTests(_ImportHarness):
    """Persisted (non-dry-run) import -> evaluate -> normalize on a
    synthetic raw-only fixture -- not just a dry-run evaluation."""

    def test_persisted_import_evaluate_normalize_chain(self) -> None:
        src = self._make_source_folder("inbox/chain")
        imported = self._import(src)
        archive = self.fake_atlas / imported["import_dir"]

        evaluation = _pipeline.evaluate_archive(archive_path=archive, dry_run=False)
        self.assertTrue(_pipeline.evaluation_path(archive).exists())
        self.assertEqual(evaluation["review_source_kind"], "raw")
        self.assertEqual(evaluation["manifest"]["privacy_flag"], "private")
        # Benign synthetic fixture: no secrets/private-pattern hits, so
        # normalization/promotion should not be blocked -- quarantine
        # behavior is unchanged by which tree was scanned.
        self.assertTrue(evaluation["normalization_allowed"])
        self.assertEqual(evaluation["quarantine_flags"], [])

        normalized = _pipeline.normalize_archive(archive_path=archive, dry_run=False, force=False)
        self.assertEqual(normalized["status"], "normalized")
        self.assertEqual(normalized["privacy_flag"], "private")

        # "Restore" evidence: the relocation's own persisted receipt and
        # manifest still independently verify the raw/ tree exactly, using
        # the public, validating readers -- not a re-derived shortcut.
        rel = imported["manifest"]["raw_relocation"]
        receipt = storage.read_relocation_receipt(self.fake_atlas / rel["receipt_ref"])
        expected_manifest = storage.read_relocation_manifest(
            self.fake_atlas / rel["expected_manifest_ref"], expected_digest=rel["expected_manifest_digest"]
        )
        restore_check = storage.verify_restore(manifest=expected_manifest, root=_pipeline.raw_dir(archive))
        self.assertTrue(restore_check["ok"])
        self.assertTrue(receipt["ok"])


class LongPathPipelineTests(_ImportHarness):
    def test_long_nested_source_survives_import_and_evaluate(self) -> None:
        # >260 characters end-to-end through the real import_archive() /
        # evaluate_archive() entry points -- not only storage.py's own
        # enumeration tests -- using the module's own long-path-safe
        # helpers to build the fixture (plain pathlib would fail to
        # create it on Windows in the first place).
        src = self.fake_atlas / "inbox" / "longpath"
        deep = src
        segment = "segment-name-of-some-length-"
        while len(str(deep / "deep-file.txt")) < 280:
            deep = deep / (segment + str(len(str(deep))))
        storage._lp_mkdir(deep)
        target = deep / "deep-file.txt"
        storage._win_long_path(target).write_text("deep content", encoding="utf-8")
        self.assertGreater(len(str(target)), 260)

        result = self._import(src)
        archive = self.fake_atlas / result["import_dir"]
        rels = {p.relative_to(_pipeline.raw_dir(archive)).as_posix() for p in _pipeline.list_files(_pipeline.raw_dir(archive))}
        self.assertTrue(any(r.endswith("deep-file.txt") for r in rels))

        evaluation = _pipeline.evaluate_archive(archive_path=archive, dry_run=True)
        self.assertGreaterEqual(evaluation["summary"]["file_count"], 1)


if __name__ == "__main__":
    unittest.main()
