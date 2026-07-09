from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import vercel_observability_project_inventory as inventory


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _required_receipts(root: Path) -> None:
    audit = "\n".join(
        [
            "# Vercel Audit",
            inventory.EXPECTED_TEAM_ID,
            inventory.EXPECTED_TEAM_NAME,
            "vercel_observability_mutation_risk",
            *[f"{project_id} {meta['project_name']}" for project_id, meta in inventory.GOVERNED_PROJECTS.items()],
            "",
        ]
    )
    contract = "\n".join(
        [
            "ops/atlas/vercel_observability_project_inventory.py",
            "env-name-only",
            "vercel_observability_mutation_risk",
        ]
    )
    for ref, text in (
        (inventory.AUDIT_RECEIPT, audit),
        (inventory.CONTRACT_RECEIPT, contract),
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


def _capture_wrapper(project_id: str) -> dict[str, object]:
    project_meta = inventory.GOVERNED_PROJECTS[project_id]
    return {
        "schema_version": inventory.EXPORT_SCHEMA_VERSION,
        "captured_at": "2026-07-09T16:30:00Z",
        "source": inventory.EXPORT_SOURCE,
        "team": {
            "id": inventory.EXPECTED_TEAM_ID,
            "name": inventory.EXPECTED_TEAM_NAME,
            "slug": inventory.EXPECTED_TEAM_NAME,
        },
        "project": {
            "id": project_id,
            "name": project_meta["project_name"],
            "repo_logical_id": project_meta["repo_logical_id"],
            "inventory_scope": "in_scope_governed_repo",
            "framework": "nextjs" if project_meta["repo_logical_id"] == "fitness" else None,
            "node_version": "24.x",
            "domains": [f"{project_meta['project_name']}.vercel.app"],
        },
        "deployments": [
            {
                "id": "dpl_old",
                "url": "old.example.vercel.app",
                "created_at": "2026-07-08T10:00:00Z",
                "state": "READY",
                "target": "production",
                "commit_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "branch": "main",
                "creator": "zachariahredfield",
                "inspector_url": "https://vercel.com/example/old",
                "rollback_candidate": False,
            },
            {
                "id": "dpl_new",
                "url": "new.example.vercel.app",
                "created_at": "2026-07-09T10:00:00Z",
                "state": "READY",
                "target": "production",
                "commit_sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                "branch": "main",
                "creator": "zachariahredfield",
                "inspector_url": "https://vercel.com/example/new",
                "rollback_candidate": True,
            },
        ],
        "log_surfaces": {
            "build_logs_queryable": True,
            "runtime_logs_queryable": True,
            "runtime_errors_queryable": True,
        },
        "runtime_error_observations": [
            {
                "error_group": "billing-webhook-stripe",
                "count": 168,
                "route": "/api/billing/webhook/stripe",
                "first_seen": "2026-07-01T20:54:17.000Z",
                "last_seen": "2026-07-09T05:34:02.000Z",
                "last_deployment_id": "dpl_new",
            }
        ],
        "observability_surfaces": {
            "web_analytics": "unproven",
            "speed_insights": "unproven",
            "drains": "forbidden",
            "alerts": "unproven",
            "env_name_only": "forbidden",
        },
        "posture_classes": [
            "vercel_observability_connector_visible",
            "vercel_observability_atlas_visible",
            "vercel_observability_partial",
            "vercel_observability_mutation_risk",
        ],
    }


class VercelObservabilityProjectInventoryTests(unittest.TestCase):
    def test_valid_single_capture_returns_ok(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            capture_path = root / "tmp" / "atlas" / "vercel-observability" / "discordos.json"
            _write(capture_path, json.dumps(_capture_wrapper("prj_C2RSEa34OblHfhuEpVChRQQZSjuG"), indent=2))

            report = inventory.build_report(root=root, inputs=["tmp/atlas/vercel-observability/discordos.json"])

        self.assertEqual(inventory.STATUS_OK, report["status"])
        self.assertEqual(1, report["captured_project_count"])
        self.assertEqual("fawxzzy-discordos", report["projects"][0]["project_name"])
        self.assertEqual("dpl_new", report["projects"][0]["latest_production_deployment_id"])
        self.assertEqual(4, len(report["missing_projects"]))

    def test_unknown_project_id_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            payload = _capture_wrapper("prj_C2RSEa34OblHfhuEpVChRQQZSjuG")
            assert isinstance(payload["project"], dict)
            payload["project"]["id"] = "prj_unknown"
            capture_path = root / "tmp" / "atlas" / "vercel-observability" / "unknown.json"
            _write(capture_path, json.dumps(payload, indent=2))

            report = inventory.build_report(root=root, inputs=["tmp/atlas/vercel-observability/unknown.json"])

        self.assertEqual(inventory.STATUS_BLOCKER, report["status"])
        self.assertEqual("unknown_project_id", report["blockers"][-1]["code"])

    def test_duplicate_project_capture_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            first = root / "tmp" / "atlas" / "vercel-observability" / "one.json"
            second = root / "tmp" / "atlas" / "vercel-observability" / "two.json"
            _write(first, json.dumps(_capture_wrapper("prj_rtlFVOMFAWCRoJ3SQjHloi89881K"), indent=2))
            _write(second, json.dumps(_capture_wrapper("prj_rtlFVOMFAWCRoJ3SQjHloi89881K"), indent=2))

            report = inventory.build_report(
                root=root,
                inputs=[
                    "tmp/atlas/vercel-observability/one.json",
                    "tmp/atlas/vercel-observability/two.json",
                ],
            )

        self.assertEqual(inventory.STATUS_BLOCKER, report["status"])
        self.assertEqual("duplicate_project_capture", report["blockers"][-1]["code"])

    def test_inconsistent_team_identity_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            first_payload = _capture_wrapper("prj_C2RSEa34OblHfhuEpVChRQQZSjuG")
            second_payload = _capture_wrapper("prj_rtlFVOMFAWCRoJ3SQjHloi89881K")
            assert isinstance(second_payload["team"], dict)
            second_payload["team"]["id"] = "team_other"
            first = root / "tmp" / "atlas" / "vercel-observability" / "one.json"
            second = root / "tmp" / "atlas" / "vercel-observability" / "two.json"
            _write(first, json.dumps(first_payload, indent=2))
            _write(second, json.dumps(second_payload, indent=2))

            report = inventory.build_report(
                root=root,
                inputs=[
                    "tmp/atlas/vercel-observability/one.json",
                    "tmp/atlas/vercel-observability/two.json",
                ],
            )

        self.assertEqual(inventory.STATUS_BLOCKER, report["status"])
        self.assertEqual("unexpected_team_id", report["blockers"][0]["code"])

    def test_forbidden_sensitive_key_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            payload = _capture_wrapper("prj_t3zothbtj9DExrh3FjMsH98hwwSZ")
            payload["env_values"] = {"SECRET": "nope"}
            capture_path = root / "tmp" / "atlas" / "vercel-observability" / "mazer.json"
            _write(capture_path, json.dumps(payload, indent=2))

            report = inventory.build_report(root=root, inputs=["tmp/atlas/vercel-observability/mazer.json"])

        self.assertEqual(inventory.STATUS_BLOCKER, report["status"])
        self.assertEqual("forbidden_sensitive_key", report["blockers"][0]["code"])

    def test_invalid_posture_class_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            payload = _capture_wrapper("prj_vhUyajI4AL6BgCF40VnKtdxrBLuV")
            assert isinstance(payload["posture_classes"], list)
            payload["posture_classes"] = ["not_real"]
            capture_path = root / "tmp" / "atlas" / "vercel-observability" / "trove.json"
            _write(capture_path, json.dumps(payload, indent=2))

            report = inventory.build_report(root=root, inputs=["tmp/atlas/vercel-observability/trove.json"])

        self.assertEqual(inventory.STATUS_BLOCKER, report["status"])
        self.assertEqual("invalid_posture_class", report["blockers"][-1]["code"])

    def test_main_writes_output_only_to_tmp_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            capture_path = root / "tmp" / "atlas" / "vercel-observability" / "fitness.json"
            output_path = root / "tmp" / "atlas" / "vercel-observability" / "out.json"
            _write(capture_path, json.dumps(_capture_wrapper("prj_rtlFVOMFAWCRoJ3SQjHloi89881K"), indent=2))

            with mock.patch.object(inventory, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = inventory.main(
                        [
                            "--json",
                            "--input",
                            "tmp/atlas/vercel-observability/fitness.json",
                            "--output",
                            "tmp/atlas/vercel-observability/out.json",
                        ]
                    )

            self.assertEqual(0, code)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(inventory.SCHEMA_VERSION, payload["schema_version"])

    def test_main_rejects_protected_input_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            protected_path = root / "docs" / "ops" / "bad.json"
            _write(protected_path, json.dumps(_capture_wrapper("prj_o37CPLlESB6Zybe8GB74BX3wrkpy"), indent=2))

            with mock.patch.object(inventory, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = inventory.main(["--json", "--input", "docs/ops/bad.json"])

        self.assertEqual(2, code)

    def test_top_level_order_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            capture_path = root / "tmp" / "atlas" / "vercel-observability" / "foundation.json"
            _write(capture_path, json.dumps(_capture_wrapper("prj_o37CPLlESB6Zybe8GB74BX3wrkpy"), indent=2))

            report = inventory.build_report(root=root, inputs=["tmp/atlas/vercel-observability/foundation.json"])

        self.assertEqual(
            [
                "schema_version",
                "status",
                "safe_to_use",
                "basis_receipts",
                "input_count",
                "team",
                "posture_classes",
                "captured_project_count",
                "projects",
                "missing_projects",
                "blockers",
                "warnings",
            ],
            list(report.keys()),
        )


if __name__ == "__main__":
    unittest.main()
