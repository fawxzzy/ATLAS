from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import vercel_environment_name_inventory as inventory


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _payload(project_id: str = "prj_rtlFVOMFAWCRoJ3SQjHloi89881K") -> dict[str, object]:
    meta = inventory.GOVERNED_PROJECTS[project_id]
    return {
        "schema_version": inventory.WRAPPER_SCHEMA_VERSION,
        "source": inventory.WRAPPER_SOURCE,
        "captured_at_utc": "2026-07-14T12:00:00Z",
        "project_id": project_id,
        "project_name": meta["project_name"],
        "variables": [
            {
                "name": "SUPABASE_SERVICE_ROLE_KEY",
                "targets": ["production", "preview"],
                "presence": "configured",
                "type_posture": "sensitive",
            }
        ],
    }


class VercelEnvironmentNameInventoryTests(unittest.TestCase):
    def test_valid_name_only_wrapper_is_normalized_without_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / "tmp" / "vercel" / "fitness.json"
            _write(path, _payload())
            report = inventory.build_report(root=root, inputs=["tmp/vercel/fitness.json"])

        self.assertEqual(inventory.STATUS_ADVISORY_GAP, report["status"])
        self.assertTrue(report["safe_to_use"])
        self.assertFalse(report["environment_value_accessed"])
        self.assertEqual("SUPABASE_SERVICE_ROLE_KEY", report["projects"][0]["variables"][0]["name"])
        self.assertNotIn("value", report["projects"][0]["variables"][0])

    def test_value_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = _payload()
            payload["variables"][0]["value"] = "forbidden"
            path = root / "tmp" / "vercel" / "bad.json"
            _write(path, payload)
            report = inventory.build_report(root=root, inputs=["tmp/vercel/bad.json"])

        self.assertEqual(inventory.STATUS_BLOCKER, report["status"])
        self.assertEqual("forbidden_value_field", report["blockers"][0]["code"])

    def test_assignment_in_name_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = _payload()
            payload["variables"][0]["name"] = "API_KEY=forbidden"
            path = root / "tmp" / "vercel" / "bad.json"
            _write(path, payload)
            report = inventory.build_report(root=root, inputs=["tmp/vercel/bad.json"])

        self.assertEqual("invalid_environment_name", report["blockers"][0]["code"])

    def test_unknown_variable_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = _payload()
            payload["variables"][0]["description"] = "not admitted"
            path = root / "tmp" / "vercel" / "bad.json"
            _write(path, payload)
            report = inventory.build_report(root=root, inputs=["tmp/vercel/bad.json"])

        self.assertEqual("unknown_variable_field", report["blockers"][0]["code"])

    def test_unknown_project_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = _payload()
            payload["project_id"] = "prj_unknown"
            path = root / "tmp" / "vercel" / "bad.json"
            _write(path, payload)
            report = inventory.build_report(root=root, inputs=["tmp/vercel/bad.json"])

        self.assertEqual("unknown_project_id", report["blockers"][0]["code"])

    def test_malformed_capture_timestamp_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = _payload()
            payload["captured_at_utc"] = "not-a-timestamp"
            path = root / "tmp" / "vercel" / "bad.json"
            _write(path, payload)
            report = inventory.build_report(root=root, inputs=["tmp/vercel/bad.json"])

        self.assertEqual("invalid_capture_timestamp", report["blockers"][0]["code"])

    def test_duplicate_project_capture_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "tmp" / "vercel" / "one.json", _payload())
            _write(root / "tmp" / "vercel" / "two.json", _payload())
            report = inventory.build_report(root=root, inputs=["tmp/vercel/one.json", "tmp/vercel/two.json"])

        self.assertEqual("duplicate_project_capture", report["blockers"][-1]["code"])

    def test_protected_input_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "docs" / "bad.json", _payload())
            report = inventory.build_report(root=root, inputs=["docs/bad.json"])

        self.assertEqual("protected_path", report["blockers"][0]["code"])

    def test_main_writes_only_safe_tmp_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "tmp" / "vercel" / "fitness.json", _payload())
            output = root / "tmp" / "vercel" / "report.json"
            with mock.patch.object(inventory, "atlas_root", return_value=root), mock.patch("sys.stdout", io.StringIO()):
                code = inventory.main(
                    [
                        "--json",
                        "--input",
                        "tmp/vercel/fitness.json",
                        "--output",
                        "tmp/vercel/report.json",
                    ]
                )
            report = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(0, code)
        self.assertEqual(inventory.SCHEMA_VERSION, report["schema_version"])
        self.assertFalse(report["environment_value_accessed"])

    def test_strict_partial_coverage_returns_one(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "tmp" / "vercel" / "fitness.json", _payload())
            with mock.patch.object(inventory, "atlas_root", return_value=root), mock.patch("sys.stdout", io.StringIO()):
                code = inventory.main(["--json", "--strict", "--input", "tmp/vercel/fitness.json"])

        self.assertEqual(1, code)


if __name__ == "__main__":
    unittest.main()
