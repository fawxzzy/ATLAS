from __future__ import annotations

import io
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from ops.atlas import vercel_deployment_freshness_inventory as inventory


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _required_receipts(root: Path) -> None:
    audit = "\n".join(
        [
            "# Vercel Observability Audit",
            *[f"{project_id} {meta['project_name']}" for project_id, meta in inventory.GOVERNED_PROJECTS.items()],
            "",
        ]
    )
    coverage = "\n".join(["5/5", "deployment freshness", "fawxzzy-foundation", "fawxzzy-trove", ""])
    contract = "\n".join(["latest_production_deployment_created_at", "deployment_age_days", "age_over_30_days", ""])
    admission = "\n".join(
        [
            "ops/atlas/vercel_deployment_freshness_inventory.py",
            "tests/test_atlas_vercel_deployment_freshness_inventory.py",
            "--strict",
            "",
        ]
    )
    prompt_pack = "\n".join(
        [
            inventory.SCHEMA_VERSION,
            inventory.EXPORT_SCHEMA_VERSION,
            inventory.REPORT_SCHEMA_VERSION,
            "same_day",
            "age_over_30_days",
            "",
        ]
    )
    readiness = "\n".join(
        [
            "implementation_ready",
            "worker-cluster reconciliation",
            "ops/atlas/vercel_deployment_freshness_inventory.py",
            "",
        ]
    )
    for ref, text in (
        (inventory.AUDIT_RECEIPT, audit),
        (inventory.PROJECT_CONTRACT_RECEIPT, "# project contract\n"),
        (inventory.PROJECT_EXECUTION_RECEIPT, "# project execution\n"),
        (inventory.PROJECT_COVERAGE_RECEIPT, coverage),
        (inventory.CONTRACT_RECEIPT, contract),
        (inventory.ADMISSION_RECEIPT, admission),
        (inventory.PROMPT_PACK_RECEIPT, prompt_pack),
        (inventory.READINESS_RECEIPT, readiness),
        (inventory.CURRENT_STATE, "# current state\n"),
        (inventory.RECEIPT_INDEX, "# receipt index\n"),
        (inventory.RESTART_GUIDE, "# restart guide\n"),
    ):
        _write(root / ref, text)

    repo_inventory = {
        "schema_version": "atlas.stack.repo-inventory.v1",
        "repos": [{"logical_id": repo_id} for repo_id in inventory.REQUIRED_INVENTORY_IDS],
    }
    _write(root / inventory.STACK_REPO_INVENTORY, json.dumps(repo_inventory, indent=2))


def _report_payload() -> dict[str, object]:
    return {
        "schema_version": inventory.REPORT_SCHEMA_VERSION,
        "projects": [
            {
                "project_name": "fawxzzy-discordos",
                "project_id": "prj_C2RSEa34OblHfhuEpVChRQQZSjuG",
                "repo_logical_id": "discordos",
                "latest_production_deployment_id": "dpl_discordos",
                "latest_production_deployment_created_at": "2026-07-09T16:33:54.692000Z",
                "latest_production_commit_sha": "a" * 40,
            },
            {
                "project_name": "fawxzzy-trove",
                "project_id": "prj_vhUyajI4AL6BgCF40VnKtdxrBLuV",
                "repo_logical_id": "trove",
                "latest_production_deployment_id": "dpl_trove",
                "latest_production_deployment_created_at": "2026-05-23T03:31:42.635000Z",
                "latest_production_commit_sha": "b" * 40,
            },
        ],
    }


def _export_payload(project_id: str, created_at: str) -> dict[str, object]:
    meta = inventory.GOVERNED_PROJECTS[project_id]
    return {
        "schema_version": inventory.EXPORT_SCHEMA_VERSION,
        "project": {
            "id": project_id,
            "name": meta["project_name"],
            "repo_logical_id": meta["repo_logical_id"],
        },
        "deployments": [
            {
                "id": "dpl_old",
                "target": "production",
                "created_at": "2026-07-01T10:00:00Z",
                "commit_sha": "c" * 40,
            },
            {
                "id": "dpl_new",
                "target": "production",
                "created_at": created_at,
                "commit_sha": "d" * 40,
            },
        ],
    }


class VercelDeploymentFreshnessInventoryTests(unittest.TestCase):
    def test_valid_report_input_classifies_same_day_and_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            input_path = root / "tmp" / "atlas" / "vercel-observability" / "report.json"
            _write(input_path, json.dumps(_report_payload(), indent=2))

            with mock.patch.object(inventory, "_utc_date_today", return_value=date(2026, 7, 9)):
                report = inventory.build_report(root=root, inputs=["tmp/atlas/vercel-observability/report.json"])

        self.assertEqual(inventory.STATUS_ADVISORY_GAP, report["status"])
        self.assertTrue(report["safe_to_use"])
        self.assertEqual(2, report["captured_project_count"])
        self.assertEqual(1, report["freshness_counts"]["same_day"])
        self.assertEqual(1, report["freshness_counts"]["age_over_30_days"])
        self.assertEqual("same_day", report["projects"][0]["freshness_bucket"])

    def test_valid_export_input_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            input_path = root / "tmp" / "atlas" / "vercel-observability" / "fitness.json"
            _write(
                input_path,
                json.dumps(_export_payload("prj_rtlFVOMFAWCRoJ3SQjHloi89881K", "2026-07-08T10:00:00Z"), indent=2),
            )

            with mock.patch.object(inventory, "_utc_date_today", return_value=date(2026, 7, 9)):
                report = inventory.build_report(root=root, inputs=["tmp/atlas/vercel-observability/fitness.json"])

        self.assertEqual(inventory.STATUS_ADVISORY_GAP, report["status"])
        self.assertEqual("age_1_to_7_days", report["projects"][0]["freshness_bucket"])

    def test_duplicate_project_capture_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            first = root / "tmp" / "atlas" / "vercel-observability" / "one.json"
            second = root / "tmp" / "atlas" / "vercel-observability" / "two.json"
            payload = _export_payload("prj_rtlFVOMFAWCRoJ3SQjHloi89881K", "2026-07-09T10:00:00Z")
            _write(first, json.dumps(payload, indent=2))
            _write(second, json.dumps(payload, indent=2))

            report = inventory.build_report(
                root=root,
                inputs=[
                    "tmp/atlas/vercel-observability/one.json",
                    "tmp/atlas/vercel-observability/two.json",
                ],
            )

        self.assertEqual(inventory.STATUS_BLOCKER, report["status"])
        self.assertEqual("duplicate_project_capture", report["blockers"][-1]["code"])

    def test_unknown_project_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            payload = _report_payload()
            assert isinstance(payload["projects"], list)
            payload["projects"][0]["project_id"] = "prj_unknown"
            input_path = root / "tmp" / "atlas" / "vercel-observability" / "bad.json"
            _write(input_path, json.dumps(payload, indent=2))

            report = inventory.build_report(root=root, inputs=["tmp/atlas/vercel-observability/bad.json"])

        self.assertEqual(inventory.STATUS_BLOCKER, report["status"])
        self.assertEqual("unknown_project_id", report["blockers"][-1]["code"])

    def test_malformed_timestamp_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            payload = _report_payload()
            assert isinstance(payload["projects"], list)
            payload["projects"][0]["latest_production_deployment_created_at"] = "not-a-date"
            input_path = root / "tmp" / "atlas" / "vercel-observability" / "bad-date.json"
            _write(input_path, json.dumps(payload, indent=2))

            report = inventory.build_report(root=root, inputs=["tmp/atlas/vercel-observability/bad-date.json"])

        self.assertEqual(inventory.STATUS_BLOCKER, report["status"])
        self.assertEqual("malformed_production_timestamp", report["blockers"][-1]["code"])

    def test_main_rejects_protected_input_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            protected_path = root / "docs" / "ops" / "bad.json"
            _write(protected_path, json.dumps(_report_payload(), indent=2))

            with mock.patch.object(inventory, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = inventory.main(["--json", "--input", "docs/ops/bad.json"])

        self.assertEqual(2, code)

    def test_main_writes_safe_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            input_path = root / "tmp" / "atlas" / "vercel-observability" / "report.json"
            output_path = root / "tmp" / "atlas" / "vercel-observability" / "out.json"
            _write(input_path, json.dumps(_report_payload(), indent=2))

            with mock.patch.object(inventory, "atlas_root", return_value=root), mock.patch.object(inventory, "_utc_date_today", return_value=date(2026, 7, 9)):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = inventory.main(
                        [
                            "--json",
                            "--input",
                            "tmp/atlas/vercel-observability/report.json",
                            "--output",
                            "tmp/atlas/vercel-observability/out.json",
                        ]
                    )

            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(0, code)
        self.assertEqual(inventory.SCHEMA_VERSION, payload["schema_version"])

    def test_deterministic_top_level_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            input_path = root / "tmp" / "atlas" / "vercel-observability" / "report.json"
            _write(input_path, json.dumps(_report_payload(), indent=2))

            with mock.patch.object(inventory, "_utc_date_today", return_value=date(2026, 7, 9)):
                report = inventory.build_report(root=root, inputs=["tmp/atlas/vercel-observability/report.json"])

        self.assertEqual(
            [
                "schema_version",
                "status",
                "safe_to_use",
                "basis_receipts",
                "input_count",
                "captured_project_count",
                "project_count",
                "as_of_date",
                "freshness_counts",
                "projects",
                "missing_projects",
                "warnings",
                "blockers",
                "next_recommended_packet",
            ],
            list(report.keys()),
        )

    def test_strict_mode_returns_nonzero_on_advisory_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            input_path = root / "tmp" / "atlas" / "vercel-observability" / "report.json"
            _write(input_path, json.dumps(_report_payload(), indent=2))

            with mock.patch.object(inventory, "atlas_root", return_value=root), mock.patch.object(inventory, "_utc_date_today", return_value=date(2026, 7, 9)):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = inventory.main(["--json", "--strict", "--input", "tmp/atlas/vercel-observability/report.json"])

        self.assertEqual(1, code)


if __name__ == "__main__":
    unittest.main()
