from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from ops.validation.validate_stack import (
    build_absolute_path_finding,
    collect_excluded_surface_roots,
    summarize_excluded_surface_findings,
    summarize_findings,
    validate_archive_registry,
)


class ValidateStackQuarantinePolicyTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "stack.yaml").write_text("name: temp\n", encoding="utf-8")
        return root

    def _config(self) -> dict[str, object]:
        return {
            "archives": {
                "archive_register": "docs/registry/ATLAS-ARCHIVE-REGISTRY.json",
                "backups": "repos/repo-backups",
                "media": [
                    "repos/Realm Blade",
                    "repos/Hard Pill To Swallow",
                ],
                "zip_snapshots": [
                    "repos/CORTEX-AND-PLAYBOOK-20260408.zip",
                    "repos/dev.zip",
                    "repos/mazer-legacy-unreal.zip",
                ],
            },
            "stack_lock": {
                "excluded_surfaces": {
                    "cortex_playbook_snapshot_archive": {
                        "path": "repos/CORTEX-AND-PLAYBOOK-20260408.zip",
                        "trust_class": "untrusted",
                        "release_eligible": False,
                        "reason": "Mixed-owner snapshot reference remains manifest-visible for provenance only.",
                    },
                    "dev_workspace_snapshot_archive": {
                        "path": "repos/dev.zip",
                        "trust_class": "untrusted",
                        "release_eligible": False,
                        "reason": "Generic legacy workspace snapshot remains manifest-visible for provenance only.",
                    },
                    "verta_core_checkout": {
                        "path": "repos/Verta-Core",
                        "trust_class": "untrusted",
                        "release_eligible": False,
                        "reason": "Token-bearing Verta checkout remains quarantined.",
                    },
                    "lifeline_operator_evidence_worktree": {
                        "path": "repos/fawxzzy-lifeline-operator-evidence",
                        "trust_class": "trusted",
                        "release_eligible": False,
                        "reason": "Temporary trusted evidence lane.",
                    },
                    "repo_backups_archive_surface": {
                        "path": "repos/repo-backups",
                        "trust_class": "trusted",
                        "release_eligible": False,
                        "reason": "Legacy bundle and patch backup drop remains visible for recovery provenance.",
                    },
                    "verta_core_archive": {
                        "path": "repos/Verta-Core.zip",
                        "trust_class": "untrusted",
                        "release_eligible": False,
                        "reason": "Token-bearing Verta archive remains quarantined private evidence.",
                    },
                }
            }
        }

    def _write_archive_registry(self, root: Path, entries: list[dict[str, object]]) -> None:
        registry_path = root / "docs" / "registry" / "ATLAS-ARCHIVE-REGISTRY.json"
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "atlas.archive.registry.v1",
            "kind": "atlas-archive-registry",
            "stack_manifest_ref": "stack.yaml",
            "published_refs": {
                "json": "docs/registry/ATLAS-ARCHIVE-REGISTRY.json",
                "runbook": "docs/ops/ATLAS-ARCHIVE-ADMISSION-RUNBOOK.md",
            },
            "policy": {
                "admission_mode": "manifest_first_selective_ingest",
                "default_raw_archive_posture": "provenance_only",
                "canonical_snapshot_root": "packages/snapshots",
                "canonical_bundle_root": "packages/bundles",
                "canonical_patch_root": "packages/patches",
            },
            "entries": entries,
        }
        registry_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _current_archive_entries(self) -> list[dict[str, object]]:
        return [
            {
                "surface_id": "cortex_playbook_snapshot_archive",
                "path": "repos/CORTEX-AND-PLAYBOOK-20260408.zip",
                "present": False,
                "surface_kind": "source_snapshot",
                "verification_state": "reference_only_manifest_surface",
                "trust_class": "untrusted",
                "release_eligible": False,
                "owner_scope": "mixed_owner_unresolved",
                "retention_reason": "provenance_only_until_owner_split",
                "canonical_destination": "packages/snapshots",
                "recommended_action": "catalog_and_owner_split_before_any_extract",
            },
            {
                "surface_id": "dev_workspace_snapshot_archive",
                "path": "repos/dev.zip",
                "present": False,
                "surface_kind": "source_snapshot",
                "verification_state": "reference_only_manifest_surface",
                "trust_class": "untrusted",
                "release_eligible": False,
                "owner_scope": "unknown",
                "retention_reason": "provenance_only_until_cataloged",
                "canonical_destination": "packages/snapshots",
                "recommended_action": "catalog_before_any_extract_or_relocation",
            },
            {
                "surface_id": "repo_backups_archive_surface",
                "path": "repos/repo-backups",
                "present": True,
                "surface_kind": "bundle_patch_backup_drop",
                "verification_state": "direct_current_surface",
                "trust_class": "trusted",
                "release_eligible": False,
                "owner_scope": "stack_root",
                "retention_reason": "recovery_artifacts",
                "canonical_destination": [
                    "packages/bundles",
                    "packages/patches",
                ],
                "recommended_action": "treat_as_package_layer_backup_surface_and_relocate_when_convenient",
            },
            {
                "surface_id": "verta_core_archive",
                "path": "repos/Verta-Core.zip",
                "present": True,
                "surface_kind": "quarantined_archive",
                "verification_state": "direct_current_surface",
                "trust_class": "untrusted",
                "release_eligible": False,
                "owner_scope": "quarantined_adjacent_surface",
                "retention_reason": "private_evidence_and_derivative_only_review",
                "canonical_destination": None,
                "recommended_action": "keep_quarantined_metadata_only",
            },
        ]

    def test_quarantined_path_leak_is_reported_as_warning(self) -> None:
        root = self._temp_root()
        file_path = root / "repos" / "Verta-Core" / "Verta-Core" / "CONSOLIDATED_INDEX.md"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("<windows-home-path>\n", encoding="utf-8")

        finding = build_absolute_path_finding(
            root=root,
            file_path=file_path,
            severity="critical",
            category="windows-user-path",
            line_number=1,
            line_preview="<windows-home-path>",
            excluded_surface_roots=collect_excluded_surface_roots(root / "stack.yaml", self._config()),
        )

        self.assertEqual("warning", finding.severity)
        self.assertEqual("windows-user-path", finding.category)
        self.assertEqual("repos/Verta-Core/Verta-Core/CONSOLIDATED_INDEX.md", finding.path)
        self.assertEqual(
            "Absolute path leak detected in quarantined excluded surface.",
            finding.message,
        )
        self.assertEqual(
            {
                "critical": 0,
                "error": 0,
                "warning": 1,
                "info": 0,
                "total": 1,
            },
            summarize_findings([finding]),
        )

    def test_non_quarantined_path_leak_remains_active_critical(self) -> None:
        root = self._temp_root()
        file_path = root / "repos" / "fawxzzy-lifeline-operator-evidence" / "README.md"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("<trusted-evidence-home-path>\n", encoding="utf-8")

        finding = build_absolute_path_finding(
            root=root,
            file_path=file_path,
            severity="critical",
            category="windows-user-path",
            line_number=4,
            line_preview="<trusted-evidence-home-path>",
            excluded_surface_roots=collect_excluded_surface_roots(root / "stack.yaml", self._config()),
        )

        self.assertEqual("critical", finding.severity)
        self.assertEqual(
            "Absolute path leak detected in excluded surface.",
            finding.message,
        )
        details = finding.details or {}
        excluded_surface = details.get("excluded_surface")
        self.assertIsInstance(excluded_surface, dict)
        self.assertEqual("excluded-surface", excluded_surface.get("label"))

    def test_excluded_surface_metadata_and_counts_are_preserved(self) -> None:
        root = self._temp_root()
        excluded_surface_roots = collect_excluded_surface_roots(root / "stack.yaml", self._config())
        first_path = root / "repos" / "Verta-Core" / "Verta-Core" / "docs" / "HOMEOSTASIS_AUDIT.md"
        second_path = root / "repos" / "Verta-Core" / "Verta-Core" / ".claude" / "settings.local.json"
        first_path.parent.mkdir(parents=True, exist_ok=True)
        second_path.parent.mkdir(parents=True, exist_ok=True)

        findings = [
            build_absolute_path_finding(
                root=root,
                file_path=first_path,
                severity="critical",
                category="windows-user-path",
                line_number=7,
                line_preview="<windows-home-path>",
                excluded_surface_roots=excluded_surface_roots,
            ),
            build_absolute_path_finding(
                root=root,
                file_path=second_path,
                severity="critical",
                category="unix-home-path",
                line_number=9,
                line_preview="<unix-home-path>",
                excluded_surface_roots=excluded_surface_roots,
            ),
        ]

        summary = summarize_excluded_surface_findings([asdict(finding) for finding in findings])

        self.assertEqual(1, len(summary))
        surface_summary = summary[0]
        self.assertEqual("verta_core_checkout", surface_summary["surface_id"])
        self.assertEqual("repos/Verta-Core", surface_summary["path"])
        self.assertEqual("quarantined-excluded-surface", surface_summary["label"])
        self.assertEqual(2, surface_summary["finding_count"])
        self.assertEqual(0, surface_summary["blocking_count"])
        self.assertEqual({"warning": 2}, surface_summary["severity_counts"])
        self.assertEqual(
            {
                "unix-home-path": 1,
                "windows-user-path": 1,
            },
            surface_summary["category_counts"],
        )
        self.assertEqual(
            [
                "repos/Verta-Core/Verta-Core/.claude/settings.local.json",
                "repos/Verta-Core/Verta-Core/docs/HOMEOSTASIS_AUDIT.md",
            ],
            sorted(item["path"] for item in surface_summary["paths"]),
        )

    def test_current_archive_registry_passes(self) -> None:
        root = self._temp_root()
        (root / "repos" / "repo-backups").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "Verta-Core.zip").write_text("archive", encoding="utf-8")
        self._write_archive_registry(root, self._current_archive_entries())

        findings = validate_archive_registry(root / "stack.yaml", self._config())

        self.assertEqual([], findings)

    def test_present_archive_missing_fails_full_validation(self) -> None:
        root = self._temp_root()
        (root / "repos").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "Verta-Core.zip").write_text("archive", encoding="utf-8")
        self._write_archive_registry(root, self._current_archive_entries())

        findings = validate_archive_registry(root / "stack.yaml", self._config())

        self.assertIn("archive-present-state-drift", {finding.category for finding in findings})

    def test_present_archive_missing_warns_in_sparse_validation(self) -> None:
        root = self._temp_root()
        (root / "repos").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "Verta-Core.zip").write_text("archive", encoding="utf-8")
        self._write_archive_registry(root, self._current_archive_entries())

        findings = validate_archive_registry(
            root / "stack.yaml",
            self._config(),
            allow_missing_present_surfaces=True,
        )

        self.assertFalse(any(finding.category == "archive-present-state-drift" for finding in findings))
        self.assertTrue(
            any(
                finding.category == "archive-present-state-unverified"
                and finding.severity == "warning"
                and finding.path == "docs/registry/ATLAS-ARCHIVE-REGISTRY.json#entries[2]"
                for finding in findings
            )
        )

    def test_unregistered_archive_surface_fails(self) -> None:
        root = self._temp_root()
        (root / "repos" / "repo-backups").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "Verta-Core.zip").write_text("archive", encoding="utf-8")
        (root / "repos" / "random.zip").write_text("archive", encoding="utf-8")
        self._write_archive_registry(root, self._current_archive_entries())

        findings = validate_archive_registry(root / "stack.yaml", self._config())

        categories = {finding.category for finding in findings}
        self.assertIn("archive-unregistered-surface", categories)
        self.assertIn("repos/random.zip", {finding.path for finding in findings})

    def test_archive_under_canonical_packages_is_ignored(self) -> None:
        root = self._temp_root()
        (root / "repos" / "repo-backups").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "Verta-Core.zip").write_text("archive", encoding="utf-8")
        package_zip = root / "packages" / "snapshots" / "example.zip"
        package_zip.parent.mkdir(parents=True, exist_ok=True)
        package_zip.write_text("archive", encoding="utf-8")
        self._write_archive_registry(root, self._current_archive_entries())

        findings = validate_archive_registry(root / "stack.yaml", self._config())

        self.assertEqual([], findings)

    def test_duplicate_registry_paths_fail(self) -> None:
        root = self._temp_root()
        (root / "repos" / "repo-backups").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "Verta-Core.zip").write_text("archive", encoding="utf-8")
        entries = self._current_archive_entries()
        duplicate = dict(entries[0])
        duplicate["surface_id"] = "duplicate-entry"
        entries.append(duplicate)
        self._write_archive_registry(root, entries)

        findings = validate_archive_registry(root / "stack.yaml", self._config())

        self.assertIn("archive-registry-invalid", {finding.category for finding in findings})
        self.assertTrue(any("duplicated" in finding.message for finding in findings))

    def test_release_eligible_raw_archive_fails(self) -> None:
        root = self._temp_root()
        (root / "repos" / "repo-backups").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "Verta-Core.zip").write_text("archive", encoding="utf-8")
        entries = self._current_archive_entries()
        entries[0] = dict(entries[0])
        entries[0]["release_eligible"] = True
        self._write_archive_registry(root, entries)

        findings = validate_archive_registry(root / "stack.yaml", self._config())

        self.assertIn("archive-registry-invalid", {finding.category for finding in findings})
        self.assertTrue(any("must not be release eligible" in finding.message for finding in findings))

    def test_present_false_reference_only_archives_are_allowed(self) -> None:
        root = self._temp_root()
        (root / "repos" / "repo-backups").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "Verta-Core.zip").write_text("archive", encoding="utf-8")
        self._write_archive_registry(root, self._current_archive_entries())

        findings = validate_archive_registry(root / "stack.yaml", self._config())

        self.assertFalse(any(finding.path.endswith("repos/dev.zip") for finding in findings))
        self.assertFalse(any("CORTEX-AND-PLAYBOOK-20260408.zip" in finding.path for finding in findings))

    def test_mazer_legacy_archive_is_scope_exempt(self) -> None:
        root = self._temp_root()
        (root / "repos" / "repo-backups").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "Verta-Core.zip").write_text("archive", encoding="utf-8")
        (root / "repos" / "mazer-legacy-unreal.zip").write_text("archive", encoding="utf-8")
        self._write_archive_registry(root, self._current_archive_entries())

        findings = validate_archive_registry(root / "stack.yaml", self._config())

        self.assertFalse(any(finding.path == "repos/mazer-legacy-unreal.zip" for finding in findings))

    def test_documented_media_and_legacy_zip_exemptions_are_allowed(self) -> None:
        root = self._temp_root()
        (root / "repos" / "repo-backups").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "Verta-Core.zip").write_text("archive", encoding="utf-8")
        (root / "repos" / "Realm Blade.zip").write_text("archive", encoding="utf-8")
        (root / "repos" / "Hard Pill To Swallow.zip").write_text("archive", encoding="utf-8")
        (root / "repos" / "playbook-old.zip").write_text("archive", encoding="utf-8")
        self._write_archive_registry(root, self._current_archive_entries())

        findings = validate_archive_registry(root / "stack.yaml", self._config())

        self.assertFalse(any(finding.path == "repos/Realm Blade.zip" for finding in findings))
        self.assertFalse(any(finding.path == "repos/Hard Pill To Swallow.zip" for finding in findings))
        self.assertFalse(any(finding.path == "repos/playbook-old.zip" for finding in findings))

    def test_quarantined_archive_cannot_point_to_owner_repo_truth(self) -> None:
        root = self._temp_root()
        (root / "repos" / "repo-backups").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "Verta-Core.zip").write_text("archive", encoding="utf-8")
        entries = self._current_archive_entries()
        entries[3] = dict(entries[3])
        entries[3]["canonical_destination"] = "repos/fawxzzy-playbook"
        self._write_archive_registry(root, entries)

        findings = validate_archive_registry(root / "stack.yaml", self._config())

        self.assertIn("archive-registry-invalid", {finding.category for finding in findings})
        self.assertTrue(any("must not point to owner-repo truth" in finding.message for finding in findings))


if __name__ == "__main__":
    unittest.main()
