from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import marker_aware_next_packet_planner as planner


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _manifest(marker: str, percent: int, package: str, mode: str, reason: str = "", blocked: list[dict[str, str]] | None = None) -> dict[str, object]:
    return {
        "contract_version": "atlas.initiative.v1",
        "id": f"continuity-manifest-{marker.lower().replace(' ', '-')}",
        "title": marker,
        "metadata": {
            "current_checkpoint_receipt": "docs/ops/current.md",
            "marker_posture": [{"marker": marker, "percent": percent, "source": "docs/atlas-book/02-lanes-and-markers.md"}],
            "blocked_or_gated_work": blocked or [],
            "next_package_ladder": [{"package": package, "mode": mode, "reason": reason}],
        },
    }


def _seed_manifest(root: Path, name: str, manifest: dict[str, object]) -> str:
    relative = f"docs/memory/initiatives/{name}.json"
    _write(root / relative, json.dumps(manifest, indent=2))
    return relative


class MarkerAwareNextPacketPlannerTests(unittest.TestCase):
    def test_implementation_ready_packet_is_selected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_manifest(
                root,
                "continuity-manifest-ai-long-run-batch-orchestration",
                _manifest(
                    "AI Long-Run Batch Orchestration",
                    66,
                    "AI Long-Run Batch Orchestration marker-aware next-packet planner first-implementation worker-cluster reconciliation",
                    "root-local implementation worker cluster",
                ),
            )
            report = planner.build_report(root=root)

        self.assertEqual(planner.STATUS_OK, report["status"])
        self.assertEqual("AI Long-Run Batch Orchestration", report["selected_marker"])
        self.assertEqual(planner.CLASS_IMPLEMENTATION_READY, report["candidate_scores"][0]["classification"])
        self.assertTrue(report["safe_to_continue"])

    def test_numbered_worker_packet_is_selected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_manifest(
                root,
                "continuity-manifest-cortex-readiness",
                _manifest(
                    "Cortex Readiness",
                    45,
                    "Cortex Readiness second advisory substrate consumption first-implementation worker packet 1",
                    "implement one bounded second advisory substrate consumer helper and focused test file",
                    "implementation-readiness closeout routed this exact worker packet",
                ),
            )
            report = planner.build_report(root=root)

        self.assertEqual(planner.STATUS_OK, report["status"])
        self.assertEqual("Cortex Readiness", report["selected_marker"])
        self.assertEqual(planner.CLASS_IMPLEMENTATION_READY, report["candidate_scores"][0]["classification"])
        self.assertEqual(
            "Cortex Readiness second advisory substrate consumption first-implementation worker packet 1",
            report["selected_packet"],
        )

    def test_held_lane_classification(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_manifest(root, "continuity-manifest-sandbox-simulation-readiness", _manifest("Sandbox Simulation Readiness", 99, "No immediate Sandbox Simulation Readiness same-lane packet", "hold-flat after boundary freeze"))
            report = planner.build_report(root=root)

        self.assertEqual(planner.STATUS_ADVISORY_RECOMMENDATION, report["status"])
        self.assertEqual(planner.CLASS_HELD, report["candidate_scores"][0]["classification"])
        self.assertEqual(1, len(report["held_lanes"]))

    def test_proof_and_external_proof_classification(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_manifest(root, "continuity-manifest-inventory-and-truth-map", _manifest("Inventory & Truth Map", 99, "Fitness protected proof refresh", "proof-gated provider proof", "BrowserStack protected proof missing"))
            _seed_manifest(root, "continuity-manifest-release", _manifest("Release Lane", 50, "manual fallback proof", "docs-only", "external proof required"))
            report = planner.build_report(root=root)

        classes = {item["classification"] for item in report["candidate_scores"]}
        self.assertIn(planner.CLASS_PROOF_GATED, classes)
        self.assertIn(planner.CLASS_EXTERNAL_PROOF, classes)
        self.assertEqual(2, len(report["proof_gated_lanes"]))

    def test_docs_only_packet_classification(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_manifest(root, "continuity-manifest-cortex-readiness", _manifest("Cortex Readiness", 45, "Cortex docs-only contract freeze", "docs-only root-bounded contract freeze"))
            report = planner.build_report(root=root)

        self.assertEqual(planner.STATUS_OK, report["status"])
        self.assertEqual(planner.CLASS_DOCS_ONLY, report["candidate_scores"][0]["classification"])

    def test_unsafe_authority_risk_rejected_from_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_manifest(root, "continuity-manifest-unsafe", _manifest("Unsafe Lane", 1, "Deploy and touch secrets", "root-local implementation worker cluster"))
            report = planner.build_report(root=root)

        self.assertEqual(planner.STATUS_ADVISORY_RECOMMENDATION, report["status"])
        self.assertIsNone(report["selected_packet"])
        self.assertEqual(planner.CLASS_UNSAFE, report["candidate_scores"][0]["classification"])
        self.assertEqual(1, len(report["rejected_candidates"]))

    def test_rejects_forbidden_sources(self) -> None:
        blocked_refs = [
            "repos/fitness/docs/ops/receipt.md",
            ".codex/transcripts/session.json",
            "secrets/token.txt",
            ".env",
            "deploy/output.json",
            ".github/workflows/proof.yml",
            "archive/old.md",
            ".vercel/project.json",
            ".playwright-mcp/state.json",
            "../docs/ops/receipt.md",
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for ref in blocked_refs:
                if not ref.startswith("../"):
                    _write(root / ref, "{}")
            for ref in blocked_refs:
                report = planner.build_report(root=root, source_refs=[ref])
                self.assertEqual(planner.STATUS_BLOCKED, report["status"], ref)
                self.assertFalse(report["safe_to_continue"], ref)

    def test_absolute_source_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = planner.build_report(root=root, source_refs=[str(root / "docs" / "ops" / "receipt.md")])

        self.assertEqual(planner.STATUS_BLOCKED, report["status"])

    def test_playbook_and_cortex_refs_are_evidence_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_manifest(root, "continuity-manifest-playbook", _manifest("Playbook Everywhere + Cortex Interface", 40, "No immediate Playbook packet", "held after Foundation proof"))
            report = planner.build_report(root=root)

        self.assertTrue(report["playbook_rule_refs"])
        self.assertTrue(report["pattern_refs"])
        self.assertTrue(report["failure_mode_refs"])
        self.assertIn("Cortex output is advisory substrate, not execution authority", report["pattern_refs"])
        self.assertNotIn("marker_movement", report)

    def test_main_writes_output_only_to_tmp_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_manifest(root, "continuity-manifest-ai-long-run-batch-orchestration", _manifest("AI Long-Run Batch Orchestration", 66, "Worker packet", "root-local implementation worker cluster"))
            output_path = root / "tmp" / "planner.json"
            with mock.patch.object(planner, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = planner.main(["--json", "--output", "tmp/planner.json"])

            self.assertEqual(0, code)
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(planner.SCHEMA_VERSION, payload["schema_version"])

    def test_main_rejects_protected_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_manifest(root, "continuity-manifest-ai-long-run-batch-orchestration", _manifest("AI Long-Run Batch Orchestration", 66, "Worker packet", "root-local implementation worker cluster"))
            with mock.patch.object(planner, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = planner.main(["--json", "--output", "docs/ops/planner.json"])

        self.assertEqual(2, code)

    def test_deterministic_top_level_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_manifest(root, "continuity-manifest-ai-long-run-batch-orchestration", _manifest("AI Long-Run Batch Orchestration", 66, "Worker packet", "root-local implementation worker cluster"))
            report = planner.build_report(root=root)

        self.assertEqual(
            [
                "schema_version",
                "status",
                "selected_marker",
                "selected_packet",
                "candidate_count",
                "candidate_scores",
                "held_lanes",
                "proof_gated_lanes",
                "owner_lane_boundaries",
                "playbook_rule_refs",
                "pattern_refs",
                "failure_mode_refs",
                "authority_risks",
                "rejected_candidates",
                "proof_requirements",
                "safe_to_continue",
                "blockers",
                "branch",
                "head",
            ],
            list(report.keys()),
        )

    def test_strict_returns_nonzero_for_advisory_recommendation(self) -> None:
        self.assertEqual(1, planner.report_exit_code(status=planner.STATUS_ADVISORY_RECOMMENDATION, strict=True))


if __name__ == "__main__":
    unittest.main()
