from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import vercel_log_runtime_error_inventory as inventory


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _required_receipts(root: Path) -> None:
    audit = "\n".join(
        [
            "# Vercel Observability Audit",
            "billing-webhook-stripe",
            "/api/billing/webhook/stripe",
            "dpl_HUsDUbhofhJFEKxLCazcDfQk8pTM",
            *[
                f"{slug} {meta['project_id']}"
                for slug, meta in inventory.GOVERNED_PROJECTS.items()
            ],
            "",
        ]
    )
    project_coverage = "\n".join(["5/5", "fawxzzy-foundation", "fawxzzy-trove", ""])
    contract = "\n".join(["request logs", "runtime logs", "grouped runtime errors", "tmp/atlas/vercel-observability/", ""])
    admission = "\n".join(
        [
            "ops/atlas/vercel_log_runtime_error_inventory.py",
            "tests/test_atlas_vercel_log_runtime_error_inventory.py",
            "--strict",
            "",
        ]
    )
    prompt_pack = "\n".join([inventory.SCHEMA_VERSION, "runtime_error_group", "build_log_summary", "tmp/**.json", ""])
    readiness = "\n".join(
        [
            "implementation_ready",
            "ops/atlas/vercel_log_runtime_error_inventory.py",
            "worker-cluster reconciliation",
            "",
        ]
    )
    for ref, text in (
        (inventory.AUDIT_RECEIPT, audit),
        (inventory.PROJECT_COVERAGE_RECEIPT, project_coverage),
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


def _runtime_error_wrapper(project_slug: str) -> dict[str, object]:
    meta = inventory.GOVERNED_PROJECTS[project_slug]
    return {
        "schema_version": inventory.WRAPPER_SCHEMA_VERSION,
        "source_class": "runtime_error_group",
        "project_slug": project_slug,
        "project_id": meta["project_id"],
        "environment": "production",
        "deployment_id": "dpl_HUsDUbhofhJFEKxLCazcDfQk8pTM",
        "records": [
            {
                "cluster_label": "billing-webhook-stripe",
                "route_pattern": "/api/billing/webhook/stripe",
                "status_code_family": "500",
                "level": "error",
                "first_seen": "2026-07-01T20:54:17.000Z",
                "last_seen": "2026-07-09T05:34:02.000Z",
                "occurrence_count": 168,
                "sample_count": 7,
                "redaction_status": "redacted",
            }
        ],
    }


def _record(project_slug: str, *, source_class: str = "request_log", route_pattern: str = "/api/jobs/123", status_code_family: str = "200") -> dict[str, object]:
    meta = inventory.GOVERNED_PROJECTS[project_slug]
    return {
        "schema_version": inventory.RECORD_SCHEMA_VERSION,
        "source_class": source_class,
        "project_slug": project_slug,
        "project_id": meta["project_id"],
        "environment": "production",
        "deployment_id": f"dpl_{project_slug.split('-')[-1]}",
        "cluster_label": source_class,
        "route_pattern": route_pattern,
        "status_code_family": status_code_family,
        "level": "info" if source_class != "runtime_error_group" else "error",
        "first_seen": "2026-07-09T01:00:00Z",
        "last_seen": "2026-07-09T01:05:00Z",
        "occurrence_count": 3,
        "sample_count": 1,
        "redaction_status": "redacted",
    }


class VercelLogRuntimeErrorInventoryTests(unittest.TestCase):
    def test_valid_wrapper_and_jsonl_records_aggregate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            wrapper_path = root / "tmp" / "atlas" / "vercel-observability" / "fitness.json"
            jsonl_path = root / "tmp" / "atlas" / "vercel-observability" / "discordos.jsonl"
            _write(wrapper_path, json.dumps(_runtime_error_wrapper("fawxzzy-fitness"), indent=2))
            _write(
                jsonl_path,
                "\n".join(
                    [
                        json.dumps(_record("fawxzzy-discordos", route_pattern="/api/users/42")),
                        json.dumps(_record("fawxzzy-discordos", source_class="runtime_log", route_pattern="/api/users/42")),
                    ]
                ),
            )

            report = inventory.build_report(
                root=root,
                inputs=[
                    "tmp/atlas/vercel-observability/fitness.json",
                    "tmp/atlas/vercel-observability/discordos.jsonl",
                ],
            )

        self.assertEqual(inventory.STATUS_ADVISORY_GAP, report["status"])
        self.assertTrue(report["safe_to_use"])
        self.assertEqual(2, report["captured_project_count"])
        self.assertEqual(5, report["project_count"])
        self.assertEqual(1, report["runtime_error_cluster_count"])
        runtime_error_clusters = [item for item in report["clusters"] if item["source_class"] == "runtime_error_group"]
        self.assertEqual(1, len(runtime_error_clusters))
        self.assertEqual("billing-webhook-stripe", runtime_error_clusters[0]["cluster_label"])
        self.assertEqual("/api/billing/webhook/stripe", runtime_error_clusters[0]["route_pattern"])
        self.assertEqual("partial_capture_coverage", report["warnings"][0]["code"])

    def test_env_value_pattern_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            payload = _record("fawxzzy-mazer")
            payload["note"] = "DATABASE_URL=postgres://super-secret"
            path = root / "tmp" / "atlas" / "vercel-observability" / "mazer.json"
            _write(path, json.dumps(payload, indent=2))

            report = inventory.build_report(root=root, inputs=["tmp/atlas/vercel-observability/mazer.json"])

        self.assertEqual(inventory.STATUS_BLOCKER, report["status"])
        self.assertEqual("forbidden_sensitive_value", report["blockers"][0]["code"])
        self.assertEqual("env_value_pattern", report["blockers"][0]["details"]["detector"])

    def test_token_value_pattern_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            payload = _record("fawxzzy-trove")
            payload["note"] = "Bearer sk_live_1234567890"
            path = root / "tmp" / "atlas" / "vercel-observability" / "trove.json"
            _write(path, json.dumps(payload, indent=2))

            report = inventory.build_report(root=root, inputs=["tmp/atlas/vercel-observability/trove.json"])

        self.assertEqual(inventory.STATUS_BLOCKER, report["status"])
        self.assertEqual("token_value_pattern", report["blockers"][0]["details"]["detector"])

    def test_cookie_and_request_body_keys_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            payload = _record("fawxzzy-foundation")
            payload["authorization_header"] = "Bearer hidden"
            payload["request_body"] = {"card_number": "4242"}
            path = root / "tmp" / "atlas" / "vercel-observability" / "foundation.json"
            _write(path, json.dumps(payload, indent=2))

            report = inventory.build_report(root=root, inputs=["tmp/atlas/vercel-observability/foundation.json"])

        self.assertEqual(inventory.STATUS_BLOCKER, report["status"])
        self.assertEqual("forbidden_sensitive_key", report["blockers"][0]["code"])
        self.assertEqual(2, len(report["forbidden_fields_detected"]))

    def test_unknown_project_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            payload = _record("fawxzzy-discordos")
            payload["project_slug"] = "fawxzzy-unknown"
            path = root / "tmp" / "atlas" / "vercel-observability" / "unknown.json"
            _write(path, json.dumps(payload, indent=2))

            report = inventory.build_report(root=root, inputs=["tmp/atlas/vercel-observability/unknown.json"])

        self.assertEqual(inventory.STATUS_BLOCKER, report["status"])
        self.assertEqual("unknown_project_slug", report["blockers"][-1]["code"])

    def test_unsupported_source_class_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            payload = _record("fawxzzy-fitness")
            payload["source_class"] = "edge_log"
            path = root / "tmp" / "atlas" / "vercel-observability" / "edge.json"
            _write(path, json.dumps(payload, indent=2))

            report = inventory.build_report(root=root, inputs=["tmp/atlas/vercel-observability/edge.json"])

        self.assertEqual(inventory.STATUS_BLOCKER, report["status"])
        self.assertEqual("unsupported_source_class", report["blockers"][-1]["code"])

    def test_main_rejects_input_outside_tmp(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            path = root / "docs" / "ops" / "bad.json"
            _write(path, json.dumps(_record("fawxzzy-discordos"), indent=2))

            with mock.patch.object(inventory, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = inventory.main(["--json", "--input", "docs/ops/bad.json"])

        self.assertEqual(2, code)

    def test_main_writes_safe_tmp_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            capture_path = root / "tmp" / "atlas" / "vercel-observability" / "discordos.ndjson"
            output_path = root / "tmp" / "atlas" / "vercel-observability" / "out.json"
            _write(capture_path, json.dumps(_record("fawxzzy-discordos")))

            with mock.patch.object(inventory, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = inventory.main(
                        [
                            "--json",
                            "--input",
                            "tmp/atlas/vercel-observability/discordos.ndjson",
                            "--output",
                            "tmp/atlas/vercel-observability/out.json",
                        ]
                    )

            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(0, code)
        self.assertEqual(inventory.SCHEMA_VERSION, payload["schema_version"])

    def test_main_rejects_absolute_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            capture_path = root / "tmp" / "atlas" / "vercel-observability" / "fitness.json"
            _write(capture_path, json.dumps(_record("fawxzzy-fitness"), indent=2))

            with mock.patch.object(inventory, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = inventory.main(
                        [
                            "--json",
                            "--input",
                            "tmp/atlas/vercel-observability/fitness.json",
                            "--output",
                            str(root / "out.json"),
                        ]
                    )

        self.assertEqual(2, code)

    def test_deterministic_top_level_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            path = root / "tmp" / "atlas" / "vercel-observability" / "foundation.json"
            _write(path, json.dumps(_record("fawxzzy-foundation"), indent=2))

            report = inventory.build_report(root=root, inputs=["tmp/atlas/vercel-observability/foundation.json"])

        self.assertEqual(
            [
                "schema_version",
                "status",
                "safe_to_use",
                "captured_project_count",
                "project_count",
                "runtime_error_cluster_count",
                "log_record_count",
                "redaction_status",
                "projects",
                "clusters",
                "warnings",
                "blockers",
                "forbidden_fields_detected",
                "next_recommended_packet",
            ],
            list(report.keys()),
        )

    def test_strict_mode_is_nonzero_on_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _required_receipts(root)
            payload = _record("fawxzzy-fitness")
            payload["note"] = "token=abcdefghi12345"
            capture_path = root / "tmp" / "atlas" / "vercel-observability" / "strict.json"
            _write(capture_path, json.dumps(payload, indent=2))

            with mock.patch.object(inventory, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = inventory.main(["--json", "--strict", "--input", "tmp/atlas/vercel-observability/strict.json"])

        self.assertEqual(2, code)


if __name__ == "__main__":
    unittest.main()
