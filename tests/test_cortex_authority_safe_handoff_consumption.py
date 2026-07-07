from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops.cortex.authority_safe_handoff_consumption import (
    EXPECTED_AUTHORITY_DENIALS,
    SCHEMA_VERSION,
    build_consumption_report,
    main,
    validate_output_path,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class AuthoritySafeHandoffConsumptionTests(unittest.TestCase):
    def _temp_root(self, *, validation_error: bool = False) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        summary = {"critical": 0, "error": 1 if validation_error else 0, "warning": 0, "info": 0}
        _write(root / "runtime/receipts/validation/stack-validation.latest.json", json.dumps({"summary": summary}) + "\n")
        return root

    def _handoff_payload(self, *, safe_to_use: bool = True, denials: list[str] | None = None) -> dict[str, object]:
        return {
            "schema_version": "atlas.cortex.authority-safe-interface-handoff.v1",
            "status": "ok" if safe_to_use else "blocker",
            "root": "C:/ATLAS",
            "branch": "main",
            "head": "abc123",
            "source_refs": [],
            "consumed_surfaces": [],
            "handoff_payload": {"advisory_only": True},
            "authority_denials": denials if denials is not None else list(EXPECTED_AUTHORITY_DENIALS),
            "forbidden_surfaces": ["repos/**", "secrets/**"],
            "warnings": [],
            "blockers": [] if safe_to_use else [{"code": "fixture", "message": "fixture"}],
            "safe_to_use": safe_to_use,
        }

    def _write_handoff(self, root: Path, payload: dict[str, object] | str = None) -> Path:
        handoff = root / "tmp/cortex/interface-handoff.json"
        if payload is None:
            payload = self._handoff_payload()
        text = payload if isinstance(payload, str) else json.dumps(payload, indent=2) + "\n"
        _write(handoff, text)
        return handoff

    def test_consumes_valid_handoff_and_preserves_denials(self) -> None:
        root = self._temp_root()
        self._write_handoff(root)

        with patch("ops.cortex.authority_safe_handoff_consumption.collect_git_state", return_value=("main", "abc123")):
            payload = build_consumption_report(root=root, handoff="tmp/cortex/interface-handoff.json")

        self.assertEqual(SCHEMA_VERSION, payload["schema_version"])
        self.assertEqual("ok", payload["status"])
        self.assertTrue(payload["safe_to_use"])
        self.assertEqual("tmp/cortex/interface-handoff.json", payload["handoff_ref"])
        self.assertTrue(str(payload["handoff_digest"]).startswith("sha256:"))
        self.assertEqual(list(EXPECTED_AUTHORITY_DENIALS), payload["consumed_authority_denials"])
        self.assertEqual(payload["consumed_authority_denials"], payload["preserved_authority_denials"])
        self.assertFalse(payload["advisory_payload"]["execution_authorized"])
        self.assertFalse(payload["advisory_payload"]["final_receipt_authorized"])
        self.assertEqual(
            [
                "schema_version",
                "status",
                "root",
                "branch",
                "head",
                "handoff_ref",
                "handoff_digest",
                "consumption_result",
                "consumed_authority_denials",
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

    def test_missing_handoff_is_advisory_gap_without_writes(self) -> None:
        root = self._temp_root()

        payload = build_consumption_report(root=root)

        self.assertEqual("advisory_gap", payload["status"])
        self.assertFalse(payload["safe_to_use"])
        self.assertEqual("handoff_required", payload["warnings"][0]["code"])

    def test_rejects_forbidden_handoff_paths(self) -> None:
        root = self._temp_root()

        for candidate in ("repos/mazer/handoff.json", "secrets/handoff.json", "../handoff.json", str(root / "tmp/handoff.json")):
            payload = build_consumption_report(root=root, handoff=candidate)
            self.assertEqual("blocker", payload["status"])
            self.assertFalse(payload["safe_to_use"])

    def test_malformed_handoff_fails_closed(self) -> None:
        root = self._temp_root()
        self._write_handoff(root, "{not json")

        payload = build_consumption_report(root=root, handoff="tmp/cortex/interface-handoff.json")

        self.assertEqual("blocker", payload["status"])
        self.assertEqual("handoff_malformed", payload["blockers"][0]["code"])

    def test_missing_authority_denial_fails_closed(self) -> None:
        root = self._temp_root()
        self._write_handoff(root, self._handoff_payload(denials=["execution"]))

        payload = build_consumption_report(root=root, handoff="tmp/cortex/interface-handoff.json")

        self.assertEqual("blocker", payload["status"])
        self.assertEqual("authority_denials_incomplete", payload["blockers"][0]["code"])

    def test_source_handoff_not_safe_is_advisory_gap(self) -> None:
        root = self._temp_root()
        self._write_handoff(root, self._handoff_payload(safe_to_use=False))

        payload = build_consumption_report(root=root, handoff="tmp/cortex/interface-handoff.json")

        self.assertEqual("advisory_gap", payload["status"])
        self.assertFalse(payload["safe_to_use"])
        self.assertEqual("handoff_not_safe_to_use", payload["warnings"][0]["code"])

    def test_validation_error_blocks_consumption(self) -> None:
        root = self._temp_root(validation_error=True)
        self._write_handoff(root)

        payload = build_consumption_report(root=root, handoff="tmp/cortex/interface-handoff.json")

        self.assertEqual("blocker", payload["status"])
        self.assertEqual("validation_not_safe", payload["blockers"][0]["code"])

    def test_output_path_must_be_explicit_tmp_relative(self) -> None:
        root = self._temp_root()

        allowed, error = validate_output_path(root, "tmp/cortex/consumption.json")
        self.assertIsNotNone(allowed)
        self.assertIsNone(error)

        for candidate in ("docs/ops/not-allowed.md", "repos/x/out.json", "../out.json", str(root / "tmp/out.json")):
            allowed, error = validate_output_path(root, candidate)
            self.assertIsNone(allowed)
            self.assertIsNotNone(error)

    def test_main_writes_only_with_explicit_safe_output(self) -> None:
        root = self._temp_root()
        self._write_handoff(root)
        output = root / "tmp/cortex/consumption.json"

        with patch("ops.cortex.authority_safe_handoff_consumption.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--json", "--handoff", "tmp/cortex/interface-handoff.json", "--output", "tmp/cortex/consumption.json"])

        self.assertEqual(0, exit_code)
        self.assertTrue(output.exists())
        self.assertEqual("ok", json.loads(output.read_text(encoding="utf-8"))["status"])
        self.assertEqual("ok", json.loads(stdout.getvalue())["status"])

    def test_main_rejects_protected_output_without_writing(self) -> None:
        root = self._temp_root()
        self._write_handoff(root)

        with patch("ops.cortex.authority_safe_handoff_consumption.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--json", "--handoff", "tmp/cortex/interface-handoff.json", "--output", "secrets/consumption.json"])

        self.assertEqual(2, exit_code)
        payload = json.loads(stdout.getvalue())
        self.assertEqual("blocker", payload["status"])
        self.assertEqual("protected_path_forbidden", payload["blockers"][0]["code"])
        self.assertFalse((root / "secrets/consumption.json").exists())


if __name__ == "__main__":
    unittest.main()
