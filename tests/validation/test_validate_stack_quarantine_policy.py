from __future__ import annotations

import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from ops.validation.validate_stack import (
    build_absolute_path_finding,
    collect_excluded_surface_roots,
    summarize_excluded_surface_findings,
    summarize_findings,
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
            "stack_lock": {
                "excluded_surfaces": {
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
                }
            }
        }

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


if __name__ == "__main__":
    unittest.main()
