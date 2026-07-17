from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import text_corpus_inventory as inventory


ROOT = Path(__file__).resolve().parents[1]


def _git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_bytes,
        check=True,
        capture_output=True,
    )
    return completed.stdout


def _write_files(repo: Path, files: dict[str, bytes]) -> None:
    for relative_path, raw in files.items():
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def _init_repo(repo: Path, files: dict[str, bytes], *, special_entries: bool = False) -> str:
    repo.mkdir(parents=True)
    _git(repo, "init", "--quiet")
    _git(repo, "config", "user.name", "Corpus Test")
    _git(repo, "config", "user.email", "corpus@example.invalid")
    _git(repo, "config", "core.autocrlf", "false")
    _write_files(repo, files)
    _git(repo, "add", "-f", ".")
    _git(repo, "commit", "--quiet", "-m", "fixture")
    if special_entries:
        symlink_oid = _git(repo, "hash-object", "-w", "--stdin", input_bytes=b"../outside.md").decode().strip()
        head = _git(repo, "rev-parse", "HEAD").decode().strip()
        _git(repo, "update-index", "--add", "--cacheinfo", f"120000,{symlink_oid},linked.md")
        _git(repo, "update-index", "--add", "--cacheinfo", f"160000,{head},nested-repo")
        _git(repo, "commit", "--quiet", "-m", "special entries")
    return _git(repo, "rev-parse", "HEAD").decode().strip()


def _specs(atlas_commit: str, playbook_commit: str) -> tuple[inventory.SourceSpec, inventory.SourceSpec]:
    return (
        inventory.SourceSpec(
            source_id="github:test/atlas",
            component_id="atlas-root",
            repository_owner="test",
            repository_name="atlas",
            pinned_commit=atlas_commit,
            authority_tier="atlas_inventory_adoption_owner",
        ),
        inventory.SourceSpec(
            source_id="github:test/playbook",
            component_id="playbook",
            repository_owner="test",
            repository_name="playbook",
            pinned_commit=playbook_commit,
            authority_tier="playbook_doctrine_owner",
        ),
    )


class AtlasTextCorpusInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name)
        self.atlas_repo = self.base / "atlas"
        self.playbook_repo = self.base / "playbook.git"
        fixture_files = {
            ".gitignore": b"ignored.md\n",
            "docs/guide.md": b"PUBLIC BODY MUST NOT BE COPIED\n",
            "src/main.py": b"print('ok')\n",
            "runtime/session.md": b"runtime body\n",
            "tmp/scratch.md": b"scratch body\n",
            "vendor/library.ts": b"vendored body\n",
            "generated/report.json": b"{\"generated\":true}\n",
            "private/notes.md": b"private body\n",
            "transcripts/chat.md": b"transcript body\n",
            "secrets/key.txt": b"secret body\n",
            ".env.local": b"TOKEN=secret\n",
            "config/credentials.yml": b"password: secret\n",
            "config/credentials.properties": b"password=secret\n",
            "config/secrets.yaml": b"password: secret\n",
            "config/token.json": b"{\"token\":\"secret\"}\n",
            "config/token.npmrc": b"token=secret\n",
            "config/token.xml": b"<token>secret</token>\n",
            "assets/fake.md": b"binary\x00body",
            "assets/logo.png": b"\x89PNG\r\n\x1a\n",
        }
        fixture_files.update(
            {f"config/secret{suffix}": b"protected configuration fixture\n" for suffix in sorted(inventory.SECRET_MANIFEST_SUFFIXES)}
        )
        self.atlas_commit = _init_repo(self.atlas_repo, fixture_files, special_entries=True)
        self.playbook_commit = _init_repo(
            self.playbook_repo,
            {
                "README.md": b"Playbook doctrine\n",
                "docs/RULES.md": b"Rule: deterministic sources.\n",
            },
        )
        (self.atlas_repo / "ignored.md").write_text("untracked and ignored\n", encoding="utf-8")
        self.specs = _specs(self.atlas_commit, self.playbook_commit)
        self.repo_paths = {"atlas-root": self.atlas_repo, "playbook": self.playbook_repo}
        self.schema = json.loads((ROOT / inventory.SCHEMA_PATH).read_text(encoding="utf-8"))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _components(self) -> list[dict[str, object]]:
        return inventory.build_components(self.specs, self.repo_paths)

    def _atlas_records(self) -> dict[str, dict[str, object]]:
        component = self._components()[0]
        return {record["relative_path"]: record for record in component["records"]}

    def test_two_run_replay_is_byte_identical_with_stable_aggregate_digest(self) -> None:
        first_components = self._components()
        second_components = self._components()
        first_index = inventory.build_index(first_components)
        second_index = inventory.build_index(second_components)
        self.assertEqual(inventory.stable_json_bytes(first_components), inventory.stable_json_bytes(second_components))
        self.assertEqual(inventory.stable_json_bytes(first_index), inventory.stable_json_bytes(second_index))
        self.assertEqual(first_index["aggregate"]["aggregate_digest"], second_index["aggregate"]["aggregate_digest"])

    def test_included_row_resolves_to_pinned_blob_and_digest(self) -> None:
        record = self._atlas_records()["docs/guide.md"]
        raw = _git(self.atlas_repo, "show", f"{self.atlas_commit}:docs/guide.md")
        oid = _git(self.atlas_repo, "rev-parse", f"{self.atlas_commit}:docs/guide.md").decode().strip()
        self.assertEqual("included", record["disposition"])
        self.assertEqual(oid, record["git_blob_id"])
        self.assertEqual(f"sha256:{hashlib.sha256(raw).hexdigest()}", record["sha256"])
        self.assertEqual(len(raw), record["byte_size"])

    def test_inventory_never_copies_corpus_bodies(self) -> None:
        component = self._components()[0]
        serialized = inventory.stable_json_bytes(component)
        self.assertNotIn(b"PUBLIC BODY MUST NOT BE COPIED", serialized)
        self.assertNotIn(b"secret body", serialized)
        self.assertNotIn(b"transcript body", serialized)

    def test_hard_exclusions_fail_closed_without_content_sha256(self) -> None:
        records = self._atlas_records()
        expected = {
            "runtime/session.md": "MUTABLE_RUNTIME_SURFACE",
            "tmp/scratch.md": "MUTABLE_RUNTIME_SURFACE",
            "vendor/library.ts": "DEPENDENCY_OR_VENDOR_TREE",
            "generated/report.json": "GENERATED_OR_BUILD_TREE",
            "private/notes.md": "PRIVATE_OR_TRANSCRIPT_SURFACE",
            "transcripts/chat.md": "PRIVATE_OR_TRANSCRIPT_SURFACE",
            "secrets/key.txt": "SECRET_SURFACE",
            ".env.local": "SECRET_SURFACE",
            "config/credentials.yml": "SECRET_SURFACE",
            "config/credentials.properties": "SECRET_SURFACE",
            "config/secrets.yaml": "SECRET_SURFACE",
            "config/token.json": "SECRET_SURFACE",
            "config/token.npmrc": "SECRET_SURFACE",
            "config/token.xml": "SECRET_SURFACE",
            "assets/fake.md": "BINARY_CONTENT",
            "assets/logo.png": "UNSUPPORTED_MEDIA_TYPE",
            "linked.md": "SYMLINK_ENTRY",
            "nested-repo": "GITLINK_ENTRY",
        }
        expected.update({f"config/secret{suffix}": "SECRET_SURFACE" for suffix in inventory.SECRET_MANIFEST_SUFFIXES})
        for path, reason in expected.items():
            with self.subTest(path=path):
                self.assertEqual("excluded", records[path]["disposition"])
                self.assertEqual(reason, records[path]["reason"])
                self.assertEqual(inventory.UNKNOWN, records[path]["sha256"])

    def test_ignored_and_untracked_worktree_bytes_are_not_sources(self) -> None:
        self.assertNotIn("ignored.md", self._atlas_records())

    def test_secret_paths_are_rejected_before_blob_reads(self) -> None:
        protected_suffix_paths = {suffix: f"config/secret{suffix}" for suffix in inventory.SECRET_MANIFEST_SUFFIXES}
        secret_paths = sorted(
            {
                ".env.local",
                "config/credentials.yml",
                "config/credentials.properties",
                "config/secrets.yaml",
                "config/token.json",
                "config/token.npmrc",
                "config/token.xml",
                *protected_suffix_paths.values(),
            }
        )
        secret_oids = {
            _git(self.atlas_repo, "rev-parse", f"{self.atlas_commit}:{path}").decode().strip()
            for path in secret_paths
        }
        original = inventory.batch_read_blobs
        with mock.patch.object(inventory, "batch_read_blobs", wraps=original) as reader:
            inventory.build_component(self.specs[0], self.atlas_repo.resolve())
        requested = set(reader.call_args.args[1])
        self.assertTrue(secret_oids.isdisjoint(requested))
        for suffix, path in protected_suffix_paths.items():
            with self.subTest(suffix=suffix):
                oid = _git(self.atlas_repo, "rev-parse", f"{self.atlas_commit}:{path}").decode().strip()
                self.assertNotIn(oid, requested)

    def test_traversal_absolute_and_backslash_paths_are_rejected(self) -> None:
        for value in ("../escape.md", "docs/../escape.md", "/absolute.md", "C:/absolute.md", "docs\\file.md"):
            with self.subTest(value=value), self.assertRaises(inventory.InventoryError):
                inventory.validate_relative_path(value)

    def test_duplicate_source_identity_is_rejected(self) -> None:
        duplicate = inventory.SourceSpec(
            source_id=self.specs[0].source_id,
            component_id="playbook",
            repository_owner="test",
            repository_name="playbook",
            pinned_commit=self.playbook_commit,
            authority_tier="playbook_doctrine_owner",
        )
        with self.assertRaisesRegex(inventory.InventoryError, "Duplicate source source_id"):
            inventory.build_components((self.specs[0], duplicate), self.repo_paths)

    def test_ambiguous_real_repository_roots_are_rejected(self) -> None:
        same_commit_specs = _specs(self.atlas_commit, self.atlas_commit)
        with self.assertRaisesRegex(inventory.InventoryError, "same repository root"):
            inventory.build_components(
                same_commit_specs,
                {"atlas-root": self.atlas_repo, "playbook": self.atlas_repo},
            )

    def test_replacement_refs_cannot_change_pinned_object_reads(self) -> None:
        repo = self.base / "replacement-refs"
        original_commit = _init_repo(repo, {"guide.md": b"original body\n"})
        (repo / "guide.md").write_bytes(b"replacement body\n")
        _git(repo, "add", "guide.md")
        _git(repo, "commit", "--quiet", "-m", "replacement")
        replacement_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
        _git(repo, "replace", original_commit, replacement_commit)
        spec = inventory.SourceSpec(
            source_id="github:test/atlas-replacement",
            component_id="atlas-root",
            repository_owner="test",
            repository_name="atlas-replacement",
            pinned_commit=original_commit,
            authority_tier="atlas_inventory_adoption_owner",
        )
        component = inventory.build_component(spec, repo.resolve())
        record = component["records"][0]
        self.assertEqual("guide.md", record["relative_path"])
        self.assertEqual(inventory.sha256_bytes(b"original body\n"), record["sha256"])

    def test_missing_promisor_blob_fails_without_mutating_source_store(self) -> None:
        source = self.base / "promisor-source"
        commit = _init_repo(source, {"guide.md": b"promised body\n"})
        tree = _git(source, "rev-parse", f"{commit}^{{tree}}").decode().strip()
        commit_raw = _git(source, "cat-file", "commit", commit)
        tree_raw = _git(source, "cat-file", "tree", tree)
        partial = self.base / "partial.git"
        partial.mkdir()
        _git(partial, "init", "--bare", "--quiet")
        written_commit = _git(partial, "hash-object", "-t", "commit", "-w", "--stdin", input_bytes=commit_raw).decode().strip()
        written_tree = _git(partial, "hash-object", "-t", "tree", "-w", "--stdin", input_bytes=tree_raw).decode().strip()
        self.assertEqual(commit, written_commit)
        self.assertEqual(tree, written_tree)
        _git(partial, "config", "core.repositoryformatversion", "1")
        _git(partial, "config", "extensions.partialClone", "origin")
        _git(partial, "config", "remote.origin.url", source.resolve().as_uri())
        _git(partial, "config", "remote.origin.promisor", "true")
        _git(partial, "config", "remote.origin.partialclonefilter", "blob:none")
        before = sorted((path.relative_to(partial).as_posix(), path.stat().st_size) for path in (partial / "objects").rglob("*") if path.is_file())
        spec = inventory.SourceSpec(
            source_id="github:test/atlas-partial",
            component_id="atlas-root",
            repository_owner="test",
            repository_name="atlas-partial",
            pinned_commit=commit,
            authority_tier="atlas_inventory_adoption_owner",
        )
        with self.assertRaises(inventory.InventoryError) as raised:
            inventory.build_component(spec, partial.resolve())
        self.assertEqual("GIT_BLOB_UNAVAILABLE", raised.exception.code)
        after = sorted((path.relative_to(partial).as_posix(), path.stat().st_size) for path in (partial / "objects").rglob("*") if path.is_file())
        self.assertEqual(before, after)
        self.assertEqual("1", inventory.git_read_env()["GIT_NO_LAZY_FETCH"])

    def test_blob_digest_mismatch_fails_closed(self) -> None:
        def tampered(repo: Path, oids: object) -> dict[str, bytes]:
            return {oid: b"tampered" for oid in oids}

        with mock.patch.object(inventory, "batch_read_blobs", side_effect=tampered):
            with self.assertRaises(inventory.InventoryError) as raised:
                inventory.build_component(self.specs[0], self.atlas_repo.resolve())
        self.assertEqual("BLOB_DIGEST_MISMATCH", raised.exception.code)

    def test_large_blob_batch_reader_does_not_pipe_deadlock(self) -> None:
        repo = self.base / "large-batch"
        files = {f"docs/item-{index:03d}.md": (f"item {index}\n".encode() + b"x" * 8192) for index in range(256)}
        commit = _init_repo(repo, files)
        entries = _git(repo, "ls-tree", "-r", commit).decode().splitlines()
        oids = [line.split(None, 3)[2] for line in entries]
        oids_path = self.base / "large-batch-oids.json"
        oids_path.write_text(json.dumps(oids), encoding="utf-8", newline="\n")
        code = (
            "import json,sys; from pathlib import Path; "
            "from ops.atlas.text_corpus_inventory import batch_read_blobs; "
            "oids=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')); "
            "blobs=batch_read_blobs(Path(sys.argv[1]),oids); "
            "assert len(blobs)==len(oids); print('ok')"
        )
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        completed = subprocess.run(
            [sys.executable, "-c", code, str(repo), str(oids_path)],
            cwd=ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("ok", completed.stdout.strip())

    def test_malformed_records_fail_schema_and_semantic_validation(self) -> None:
        component = self._components()[0]
        malformed = copy.deepcopy(component)
        del malformed["records"][0]["provenance_ref"]
        errors = inventory.validate_document(malformed, self.schema)
        self.assertTrue(any("provenance_ref" in error for error in errors), errors)

    def test_unavailable_source_denominator_remains_unknown(self) -> None:
        components = inventory.build_components(
            self.specs,
            {"atlas-root": self.atlas_repo, "playbook": self.base / "missing-playbook.git"},
        )
        index = inventory.build_index(components)
        playbook = components[1]
        self.assertEqual(inventory.UNKNOWN, playbook["source"]["availability"])
        self.assertEqual(inventory.UNKNOWN, playbook["counts"]["total"])
        self.assertEqual(inventory.UNKNOWN, index["aggregate"]["counts"]["total"])
        self.assertEqual(inventory.UNKNOWN, index["aggregate"]["aggregate_digest"])
        for field in ("total", "included", "excluded", "unknown", "exclusion_reasons"):
            with self.subTest(field=field):
                malformed = copy.deepcopy(index)
                malformed["aggregate"]["counts"][field] = {} if field == "exclusion_reasons" else 0
                errors = inventory.validate_index_semantics(malformed)
                self.assertIn("unavailable source denominator must remain UNKNOWN", errors)

    def test_resolved_path_escape_regression_is_cross_platform_and_non_skipped(self) -> None:
        workspace = (self.base / "workspace").resolve()
        outside = (self.base / "outside").resolve()
        workspace.mkdir()
        outside.mkdir()
        with self.assertRaises(inventory.InventoryError) as raised:
            inventory.ensure_resolved_contained(workspace, outside)
        self.assertEqual("RESOLVED_PATH_ESCAPE", raised.exception.code)

    def test_real_symlink_or_junction_output_escape_is_rejected_when_supported(self) -> None:
        workspace = self.base / "workspace-link-test"
        outside = self.base / "outside-link-test"
        workspace.mkdir()
        outside.mkdir()
        link = workspace / "redirected"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"real symlink creation unavailable: {exc}")
        with self.assertRaises(inventory.InventoryError):
            inventory.validate_output_root(workspace, link)

    def test_output_escape_is_rejected_before_generation_or_hashing(self) -> None:
        workspace = self.base / "workspace-prehash"
        outside = self.base / "outside-prehash"
        workspace.mkdir()
        outside.mkdir()
        with mock.patch.object(inventory, "build_outputs") as builder:
            code = inventory.main(
                [
                    "--workspace-root",
                    str(workspace),
                    "--output-root",
                    str(outside),
                    "--playbook-repo",
                    str(self.playbook_repo),
                ]
            )
        self.assertEqual(2, code)
        builder.assert_not_called()

    def test_in_workspace_symlink_resolution_cannot_escape_output_root(self) -> None:
        workspace = (self.base / "workspace-output-containment").resolve()
        output = workspace / "stage"
        escaped_target = workspace / "docs" / "inventory.json"
        output.mkdir(parents=True)
        escaped_target.parent.mkdir(parents=True)
        # Deterministically model stage/docs as a symlink or junction to
        # workspace/docs without requiring platform-specific link privileges.
        with mock.patch.object(inventory, "resolve_real_path", return_value=escaped_target):
            with self.assertRaises(inventory.InventoryError) as raised:
                inventory.materialize_outputs(
                    workspace_root=workspace,
                    output_root=output,
                    outputs={Path("docs/inventory.json"): b"{}\n"},
                    check=False,
                )
        self.assertEqual("RESOLVED_PATH_ESCAPE", raised.exception.code)
        self.assertFalse(escaped_target.exists())

    def test_component_and_index_schema_semantics_validate(self) -> None:
        components = self._components()
        index = inventory.build_index(components)
        self.assertEqual([], inventory.schema_contract_errors(self.schema))
        for document in [*components, index]:
            self.assertEqual([], inventory.validate_document(document, self.schema))
        self.assertEqual([], inventory.validate_cross_document(index, components))
        malformed_index = copy.deepcopy(index)
        malformed_index["aggregate"]["counts"]["total"] = 0
        errors = inventory.validate_document(malformed_index, self.schema)
        self.assertTrue(any("aggregate counts" in error for error in errors), errors)

    def test_record_identity_is_stable_across_content_change(self) -> None:
        before = self._atlas_records()["docs/guide.md"]
        (self.atlas_repo / "docs" / "guide.md").write_text("changed body\n", encoding="utf-8", newline="\n")
        _git(self.atlas_repo, "add", "docs/guide.md")
        _git(self.atlas_repo, "commit", "--quiet", "-m", "change guide")
        new_commit = _git(self.atlas_repo, "rev-parse", "HEAD").decode().strip()
        changed_spec = copy.copy(self.specs[0])
        changed_spec = inventory.SourceSpec(
            source_id=changed_spec.source_id,
            component_id=changed_spec.component_id,
            repository_owner=changed_spec.repository_owner,
            repository_name=changed_spec.repository_name,
            pinned_commit=new_commit,
            authority_tier=changed_spec.authority_tier,
        )
        after_component = inventory.build_component(changed_spec, self.atlas_repo.resolve())
        after = {record["relative_path"]: record for record in after_component["records"]}["docs/guide.md"]
        self.assertEqual(before["record_id"], after["record_id"])
        self.assertNotEqual(before["sha256"], after["sha256"])

    def test_materialization_is_lf_deterministic_and_check_detects_drift(self) -> None:
        workspace = self.base / "workspace-materialize"
        (workspace / inventory.SCHEMA_PATH.parent).mkdir(parents=True)
        (workspace / inventory.SCHEMA_PATH).write_bytes((ROOT / inventory.SCHEMA_PATH).read_bytes())
        workspace_real, output_real = inventory.validate_output_root(workspace, workspace)
        outputs, _index = inventory.build_outputs(
            workspace_root=workspace_real,
            repo_paths=self.repo_paths,
            specs=self.specs,
        )
        self.assertEqual([], inventory.materialize_outputs(workspace_root=workspace_real, output_root=output_real, outputs=outputs, check=False))
        self.assertEqual([], inventory.materialize_outputs(workspace_root=workspace_real, output_root=output_real, outputs=outputs, check=True))
        index_path = workspace / inventory.INDEX_PATH
        self.assertNotIn(b"\r\n", index_path.read_bytes())
        index_path.write_text("{}\n", encoding="utf-8", newline="\n")
        drift = inventory.materialize_outputs(workspace_root=workspace_real, output_root=output_real, outputs=outputs, check=True)
        self.assertEqual([inventory.INDEX_PATH.as_posix()], drift)


if __name__ == "__main__":
    unittest.main()
