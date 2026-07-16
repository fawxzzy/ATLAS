from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import vercel_observability_surface_visibility as visibility


def _payload() -> dict[str, object]:
    project_id = "prj_rtlFVOMFAWCRoJ3SQjHloi89881K"
    return {
        "schema_version": visibility.WRAPPER_SCHEMA_VERSION,
        "source": visibility.WRAPPER_SOURCE,
        "captured_at_utc": "2026-07-14T14:00:00Z",
        "project_id": project_id,
        "project_name": visibility.GOVERNED_PROJECTS[project_id]["project_name"],
        "surfaces": {
            surface: {"state": "unproven", "evidence_class": "not_queried", "mutation_capable": False}
            for surface in visibility.SURFACES
        },
    }


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class VercelObservabilitySurfaceVisibilityTests(unittest.TestCase):
    def test_complete_unproven_wrapper_is_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _write(root / "tmp" / "visibility.json", _payload())
            report = visibility.build_report(root=root, inputs=["tmp/visibility.json"])
        self.assertEqual(visibility.STATUS_ADVISORY_GAP, report["status"])
        self.assertFalse(report["mutation_performed"])
        self.assertFalse(report["entitlement_claimed"])

    def test_legacy_fawxzzyweb_project_name_is_accepted_and_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = _payload()
            payload["project_id"] = "prj_vhUyajI4AL6BgCF40VnKtdxrBLuV"
            payload["project_name"] = "fawxzzy-trove"
            _write(root / "tmp" / "visibility.json", payload)
            report = visibility.build_report(root=root, inputs=["tmp/visibility.json"])

        self.assertEqual(visibility.STATUS_ADVISORY_GAP, report["status"])
        self.assertEqual("fawxzzyweb", report["projects"][0]["project_name"])

    def test_canonical_fawxzzyweb_project_name_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = _payload()
            payload["project_id"] = "prj_vhUyajI4AL6BgCF40VnKtdxrBLuV"
            payload["project_name"] = "fawxzzyweb"
            _write(root / "tmp" / "visibility.json", payload)
            report = visibility.build_report(root=root, inputs=["tmp/visibility.json"])

        self.assertEqual(visibility.STATUS_ADVISORY_GAP, report["status"])
        self.assertEqual("fawxzzyweb", report["projects"][0]["project_name"])

    def test_unknown_fawxzzyweb_project_name_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = _payload()
            payload["project_id"] = "prj_vhUyajI4AL6BgCF40VnKtdxrBLuV"
            payload["project_name"] = "unknown-fawxzzyweb"
            _write(root / "tmp" / "visibility.json", payload)
            report = visibility.build_report(root=root, inputs=["tmp/visibility.json"])

        self.assertEqual(visibility.STATUS_BLOCKER, report["status"])
        self.assertEqual("project_identity_mismatch", report["blockers"][0]["code"])

    def test_visible_requires_direct_readback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = _payload()
            payload["surfaces"]["web_analytics"]["state"] = "visible"
            _write(root / "tmp" / "visibility.json", payload)
            report = visibility.build_report(root=root, inputs=["tmp/visibility.json"])
        self.assertEqual("unsupported_visibility_claim", report["blockers"][0]["code"])

    def test_mutation_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = _payload()
            payload["surfaces"]["drains"]["destination"] = "forbidden"
            _write(root / "tmp" / "visibility.json", payload)
            report = visibility.build_report(root=root, inputs=["tmp/visibility.json"])
        self.assertEqual("forbidden_mutation_or_secret_field", report["blockers"][0]["code"])

    def test_missing_surface_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = _payload()
            del payload["surfaces"]["traces"]
            _write(root / "tmp" / "visibility.json", payload)
            report = visibility.build_report(root=root, inputs=["tmp/visibility.json"])
        self.assertEqual("surface_set_mismatch", report["blockers"][0]["code"])

    def test_unknown_state_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = _payload()
            payload["surfaces"]["alerts"]["state"] = "enabled"
            _write(root / "tmp" / "visibility.json", payload)
            report = visibility.build_report(root=root, inputs=["tmp/visibility.json"])
        self.assertEqual("invalid_visibility_state", report["blockers"][0]["code"])

    def test_unknown_project_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = _payload()
            payload["project_id"] = "prj_unknown"
            _write(root / "tmp" / "visibility.json", payload)
            report = visibility.build_report(root=root, inputs=["tmp/visibility.json"])
        self.assertEqual("unknown_project_id", report["blockers"][0]["code"])

    def test_protected_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            report = visibility.build_report(root=Path(temp), inputs=["docs/visibility.json"])
        self.assertEqual("protected_path", report["blockers"][0]["code"])

    def test_main_writes_safe_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _write(root / "tmp" / "visibility.json", _payload())
            with mock.patch.object(visibility, "atlas_root", return_value=root), mock.patch("sys.stdout", io.StringIO()):
                code = visibility.main(["--json", "--input", "tmp/visibility.json", "--output", "tmp/report.json"])
            report = json.loads((root / "tmp" / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(0, code)
        self.assertFalse(report["mutation_performed"])


if __name__ == "__main__":
    unittest.main()
