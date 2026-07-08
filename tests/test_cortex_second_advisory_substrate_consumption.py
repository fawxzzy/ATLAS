from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops.cortex.second_advisory_substrate_consumption import (
    AUTHORITY_DENIALS,
    SCHEMA_VERSION,
    build_consumption_report,
    main,
    validate_output_path,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class SecondAdvisorySubstrateConsumptionTests(unittest.TestCase):
    def _temp_root(self, *, validation_error: bool = False) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        summary = {"critical": 0, "error": 1 if validation_error else 0, "warning": 0, "info": 0}
        _write(root / "runtime/receipts/validation/stack-validation.latest.json", json.dumps({"summary": summary}) + "\n")
        return root

    def _manifest_payload(self) -> dict[str, object]:
        return {
            "contract_version": "atlas.initiative.v1",
            "id": "continuity-manifest-cortex-readiness",
            "title": "Continuity Manifest Cortex Readiness",
            "status": "active",
            "metadata": {
                "current_checkpoint_receipt": "docs/ops/current.md",
                "marker_posture": [{"marker": "Cortex Readiness", "percent": 45, "source": "docs/atlas-book/02-lanes-and-markers.md"}],
                "next_package_ladder": [{"package": "Cortex worker packet", "mode": "implementation", "reason": "fixture"}],
            },
        }

    def _write_manifest(self, root: Path, payload: dict[str, object] | str | None = None) -> Path:
        path = root / "docs/memory/initiatives/continuity-manifest-cortex-readiness.json"
        if payload is None:
            payload = self._manifest_payload()
        text = payload if isinstance(payload, str) else json.dumps(payload, indent=2) + "\n"
        _write(path, text)
        return path

    def test_consumes_valid_manifest_and_preserves_denials(self) -> None:
        root = self._temp_root()
        self._write_manifest(root)

        with patch("ops.cortex.second_advisory_substrate_consumption.collect_git_state", return_value=("main", "abc123")):
            payload = build_consumption_report(root=root, source="docs/memory/initiatives/continuity-manifest-cortex-readiness.json")

        self.assertEqual(SCHEMA_VERSION, payload["schema_version"])
        self.assertEqual("ok", payload["status"])
        self.assertTrue(payload["safe_to_use"])
        self.assertEqual("cortex_continuity_manifest", payload["substrate_class"])
        self.assertTrue(str(payload["source_digest"]).startswith("sha256:"))
        self.assertEqual(list(AUTHORITY_DENIALS), payload["preserved_authority_denials"])
        self.assertFalse(payload["advisory_payload"]["execution_authorized"])
        self.assertFalse(payload["advisory_payload"]["owner_truth_authorized"])
        self.assertFalse(payload["advisory_payload"]["final_receipt_authorized"])
        self.assertFalse(payload["advisory_payload"]["deploy_authorized"])
        self.assertFalse(payload["advisory_payload"]["secret_handling_authorized"])
        self.assertFalse(payload["advisory_payload"]["workflow_dispatch_authorized"])
        self.assertEqual(
            [
                "schema_version",
                "status",
                "root",
                "branch",
                "head",
                "source_ref",
                "source_digest",
                "substrate_class",
                "consumption_result",
                "preserved_authority_denials",
                "advisory_payload",
                "forbidden_surfaces",
                "warnings",
                "blockers",
                "safe_to_use",
            ],
            list(payload.keys()),
        )
        json.dumps(payload, sort_keys=True)

    def test_missing_source_argument_is_advisory_gap(self) -> None:
        root = self._temp_root()

        payload = build_consumption_report(root=root)

        self.assertEqual("advisory_gap", payload["status"])
        self.assertFalse(payload["safe_to_use"])
        self.assertEqual("source_required", payload["warnings"][0]["code"])

    def test_missing_source_file_is_blocker(self) -> None:
        root = self._temp_root()

        payload = build_consumption_report(root=root, source="docs/memory/initiatives/continuity-manifest-cortex-readiness.json")

        self.assertEqual("blocker", payload["status"])
        self.assertEqual("source_missing", payload["blockers"][0]["code"])

    def test_malformed_manifest_fails_closed(self) -> None:
        root = self._temp_root()
        self._write_manifest(root, "{not json")

        payload = build_consumption_report(root=root, source="docs/memory/initiatives/continuity-manifest-cortex-readiness.json")

        self.assertEqual("blocker", payload["status"])
        self.assertEqual("source_malformed", payload["blockers"][0]["code"])

    def test_manifest_missing_required_fields_fails_closed(self) -> None:
        root = self._temp_root()
        self._write_manifest(root, {"contract_version": "atlas.initiative.v1", "id": "continuity-manifest-cortex-readiness", "metadata": {}})

        payload = build_consumption_report(root=root, source="docs/memory/initiatives/continuity-manifest-cortex-readiness.json")

        self.assertEqual("blocker", payload["status"])
        codes = {item["code"] for item in payload["blockers"]}
        self.assertIn("manifest_next_package_missing", codes)
        self.assertIn("manifest_checkpoint_missing", codes)

    def test_owner_and_protected_sources_are_rejected(self) -> None:
        root = self._temp_root()
        for candidate in (
            "repos/fawxzzy-fitness/docs/ops/receipt.md",
            "repos/mazer/README.md",
            "secrets/token.txt",
            ".vercel/project.json",
            ".playwright-mcp/state.json",
            "archive/old.md",
            ".env",
        ):
            payload = build_consumption_report(root=root, source=candidate)
            self.assertEqual("blocker", payload["status"], candidate)
            self.assertFalse(payload["safe_to_use"], candidate)

    def test_hidden_deploy_platform_and_absolute_sources_are_rejected(self) -> None:
        root = self._temp_root()
        for candidate in (
            "runtime/transcripts/session.json",
            "tmp/chats/chat.json",
            "deploy/output.json",
            "platform/output.json",
            "vercel/output.json",
            "../outside.json",
            str(root / "docs/memory/initiatives/continuity-manifest-cortex-readiness.json"),
        ):
            payload = build_consumption_report(root=root, source=candidate)
            self.assertEqual("blocker", payload["status"], candidate)
            self.assertFalse(payload["safe_to_use"], candidate)

    def test_unsupported_root_owned_source_is_rejected(self) -> None:
        root = self._temp_root()
        _write(root / "docs/README.md", "# root docs\n")

        payload = build_consumption_report(root=root, source="docs/README.md")

        self.assertEqual("blocker", payload["status"])
        self.assertEqual("source_not_admitted", payload["blockers"][0]["code"])

    def test_markdown_receipt_source_is_consumed_as_advisory(self) -> None:
        root = self._temp_root()
        _write(root / "docs/ops/CORTEX-READINESS-EXAMPLE-2026-07-08.md", "# Cortex receipt\n")

        payload = build_consumption_report(root=root, source="docs/ops/CORTEX-READINESS-EXAMPLE-2026-07-08.md")

        self.assertEqual("ok", payload["status"])
        self.assertEqual("cortex_readiness_receipt", payload["substrate_class"])

    def test_validation_error_blocks_consumption(self) -> None:
        root = self._temp_root(validation_error=True)
        self._write_manifest(root)

        payload = build_consumption_report(root=root, source="docs/memory/initiatives/continuity-manifest-cortex-readiness.json")

        self.assertEqual("blocker", payload["status"])
        self.assertEqual("validation_not_safe", payload["blockers"][0]["code"])

    def test_output_path_guards(self) -> None:
        root = self._temp_root()

        allowed, error = validate_output_path(root, "tmp/cortex/second-advisory.json")
        self.assertIsNotNone(allowed)
        self.assertIsNone(error)

        for candidate in ("docs/ops/out.json", "tmp/cortex/out.txt", "repos/x/out.json", "../out.json", str(root / "tmp/out.json")):
            allowed, error = validate_output_path(root, candidate)
            self.assertIsNone(allowed, candidate)
            self.assertIsNotNone(error, candidate)

    def test_main_default_writes_no_files(self) -> None:
        root = self._temp_root()
        self._write_manifest(root)
        output = root / "tmp/cortex/second-advisory.json"

        with patch("ops.cortex.second_advisory_substrate_consumption.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--json", "--source", "docs/memory/initiatives/continuity-manifest-cortex-readiness.json"])

        self.assertEqual(0, exit_code)
        self.assertFalse(output.exists())
        self.assertEqual("ok", json.loads(stdout.getvalue())["status"])

    def test_main_writes_only_with_explicit_safe_output(self) -> None:
        root = self._temp_root()
        self._write_manifest(root)
        output = root / "tmp/cortex/second-advisory.json"

        with patch("ops.cortex.second_advisory_substrate_consumption.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--json",
                        "--source",
                        "docs/memory/initiatives/continuity-manifest-cortex-readiness.json",
                        "--output",
                        "tmp/cortex/second-advisory.json",
                    ]
                )

        self.assertEqual(0, exit_code)
        self.assertTrue(output.exists())
        self.assertEqual("ok", json.loads(output.read_text(encoding="utf-8"))["status"])
        self.assertEqual("ok", json.loads(stdout.getvalue())["status"])

    def test_main_rejects_protected_output_without_writing(self) -> None:
        root = self._temp_root()
        self._write_manifest(root)

        with patch("ops.cortex.second_advisory_substrate_consumption.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--json",
                        "--source",
                        "docs/memory/initiatives/continuity-manifest-cortex-readiness.json",
                        "--output",
                        "secrets/second-advisory.json",
                    ]
                )

        self.assertEqual(2, exit_code)
        payload = json.loads(stdout.getvalue())
        self.assertEqual("blocker", payload["status"])
        self.assertEqual("protected_path_forbidden", payload["blockers"][0]["code"])
        self.assertFalse((root / "secrets/second-advisory.json").exists())

    def test_strict_returns_nonzero_for_advisory_gap(self) -> None:
        root = self._temp_root()

        with patch("ops.cortex.second_advisory_substrate_consumption.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--json", "--strict"])

        self.assertEqual(1, exit_code)
        self.assertEqual("advisory_gap", json.loads(stdout.getvalue())["status"])


if __name__ == "__main__":
    unittest.main()
