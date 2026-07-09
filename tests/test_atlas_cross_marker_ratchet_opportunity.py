from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import cross_marker_ratchet_opportunity as opportunity


POSITIVE_RECEIPT = "docs/ops/CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-CONSUMPTION-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-07-08.md"
PLAYBOOK_RECEIPT = "docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-SECOND-IMPLEMENTATION-BACKED-CONSUMER-CLASS-PROOF-RECONCILIATION-2026-07-08.md"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _manifest(marker: str, percent: int, current: str, refs: list[dict[str, str]] | None = None) -> dict[str, object]:
    return {
        "contract_version": "atlas.initiative.v1",
        "id": f"continuity-manifest-{marker.lower().replace(' ', '-').replace('+', 'plus')}",
        "title": marker,
        "evidence_refs": [current],
        "metadata": {
            "current_checkpoint_receipt": current,
            "marker_posture": [{"marker": marker, "percent": percent, "source": "docs/atlas-book/02-lanes-and-markers.md"}],
            "owner_truth_surfaces": refs or [],
            "governing_receipts": [current],
            "next_package_ladder": [{"package": f"No immediate {marker} same-lane packet", "mode": "held", "reason": "held"}],
        },
    }


def _seed_positive_root(root: Path) -> None:
    _write(root / POSITIVE_RECEIPT, "implementation-backed worker cluster reconciliation")
    _write(root / PLAYBOOK_RECEIPT, "second implementation-backed consumer class proof")
    cortex = _manifest("Cortex Readiness", 46, POSITIVE_RECEIPT)
    playbook = _manifest(
        "Playbook Everywhere + Cortex Interface",
        45,
        PLAYBOOK_RECEIPT,
        [
            {
                "path": POSITIVE_RECEIPT,
                "role": "second implementation-backed consumer class from Cortex second advisory substrate consumer",
            }
        ],
    )
    _write(root / "docs/memory/initiatives/continuity-manifest-cortex-readiness.json", json.dumps(cortex, indent=2))
    _write(root / "docs/memory/initiatives/continuity-manifest-playbook-everywhere-cortex-interface.json", json.dumps(playbook, indent=2))


class CrossMarkerRatchetOpportunityTests(unittest.TestCase):
    def test_live_root_input_returns_ok_or_no_opportunities(self) -> None:
        report = opportunity.build_report(root=Path.cwd())

        self.assertEqual(opportunity.SCHEMA_VERSION, report["schema_version"])
        self.assertIn(report["status"], {opportunity.STATUS_OK, opportunity.STATUS_NO_OPPORTUNITIES})
        self.assertFalse(report["marker_write_authority"])
        self.assertFalse(report["final_receipt_authority"])
        self.assertIn("Fitness app work stays in the Fitness owner lane.", report["owner_lane_exclusions"])

    def test_positive_opportunity_detects_cortex_proof_reuse_for_playbook_cortex(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_positive_root(root)
            report = opportunity.build_report(root=root)

        self.assertEqual(opportunity.STATUS_OK, report["status"])
        self.assertEqual(1, report["opportunity_count"])
        item = report["opportunities"][0]
        self.assertEqual(POSITIVE_RECEIPT, item["source_receipt"])
        self.assertEqual("Cortex Readiness", item["source_marker"])
        self.assertEqual("Playbook Everywhere + Cortex Interface", item["candidate_marker"])
        self.assertEqual(45, item["candidate_marker_percent"])
        self.assertEqual("implementation_backed_cross_marker_proof", item["evidence_class"])
        self.assertTrue(item["safe_to_use"])

    def test_deterministic_top_level_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_positive_root(root)
            report = opportunity.build_report(root=root)

        self.assertEqual(
            [
                "schema_version",
                "status",
                "safe_to_use",
                "basis_commit",
                "source_receipts",
                "candidate_count",
                "opportunity_count",
                "opportunities",
                "blocked_candidates",
                "authority_denials",
                "owner_lane_exclusions",
                "protected_surface_exclusions",
                "marker_write_authority",
                "final_receipt_authority",
            ],
            list(report.keys()),
        )

    def test_selector_contract_admission_prompt_pack_and_readiness_are_docs_only(self) -> None:
        cases = [
            "docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-POST-CROSS-MARKER-RATCHET-EVIDENCE-NEXT-SLICE-SELECTION-2026-07-08.md",
            "docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-CROSS-MARKER-RATCHET-OPPORTUNITY-CONTRACT-FREEZE-2026-07-08.md",
            "docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-CROSS-MARKER-RATCHET-OPPORTUNITY-FIRST-IMPLEMENTATION-ADMISSION-2026-07-08.md",
            "docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-CROSS-MARKER-RATCHET-OPPORTUNITY-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-08.md",
            "docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-CROSS-MARKER-RATCHET-OPPORTUNITY-IMPLEMENTATION-READINESS-CLOSEOUT-AND-WORKER-ROUTING-2026-07-08.md",
        ]
        for source in cases:
            with self.subTest(source=source), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                _write(root / source, "docs-only receipt")
                manifest = _manifest("AI Long-Run Batch Orchestration", 69, source)
                _write(root / "docs/memory/initiatives/continuity-manifest-ai-long-run-batch-orchestration.json", json.dumps(manifest, indent=2))
                report = opportunity.build_report(root=root, source_refs=[source])

                self.assertEqual(opportunity.STATUS_BLOCKED, report["status"])
                self.assertEqual(opportunity.BLOCKER_DOCS_ONLY, report["blocked_candidates"][0]["blocker_class"])
                self.assertEqual(0, report["opportunity_count"])

    def test_owner_lane_protected_secret_deploy_workflow_absolute_and_parent_sources_block(self) -> None:
        blocked_refs = [
            ("repos/fitness/docs/ops/receipt.md", opportunity.BLOCKER_OWNER_LANE),
            ("archive/old.md", opportunity.BLOCKER_PROTECTED),
            ("secrets/token.txt", opportunity.BLOCKER_DEPLOY_SECRET),
            (".env", opportunity.BLOCKER_DEPLOY_SECRET),
            ("deploy/output.json", opportunity.BLOCKER_DEPLOY_SECRET),
            (".github/workflows/proof.yml", opportunity.BLOCKER_WORKFLOW),
            ("../outside.md", opportunity.BLOCKER_PROTECTED),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for source, expected in blocked_refs:
                with self.subTest(source=source):
                    if not source.startswith("../"):
                        _write(root / source, "blocked")
                    report = opportunity.build_report(root=root, source_refs=[source])
                    self.assertEqual(opportunity.STATUS_BLOCKED, report["status"])
                    self.assertEqual(expected, report["blocked_candidates"][0]["blocker_class"])

            absolute = str(root / "docs" / "ops" / "receipt.md")
            report = opportunity.build_report(root=root, source_refs=[absolute])
            self.assertEqual(opportunity.STATUS_BLOCKED, report["status"])
            self.assertEqual(opportunity.BLOCKER_PROTECTED, report["blocked_candidates"][0]["blocker_class"])

    def test_missing_receipt_and_manifest_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            receipt_report = opportunity.build_report(root=root, source_refs=["docs/ops/MISSING.md"])
            manifest_report = opportunity.build_report(root=root, source_refs=["docs/memory/initiatives/continuity-manifest-missing.json"])

        self.assertEqual(opportunity.STATUS_BLOCKED, receipt_report["status"])
        self.assertEqual(opportunity.BLOCKER_MISSING_RECEIPT, receipt_report["blocked_candidates"][0]["blocker_class"])
        self.assertEqual(opportunity.STATUS_BLOCKED, manifest_report["status"])
        self.assertEqual(opportunity.BLOCKER_MISSING_MANIFEST, manifest_report["blocked_candidates"][0]["blocker_class"])

    def test_conflicting_marker_values_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = "docs/ops/CURRENT-WORKER-CLUSTER-RECONCILIATION.md"
            _write(root / source, "implementation-backed")
            manifest = _manifest("Cortex Readiness", 46, source)
            manifest["metadata"]["marker_posture"].append({"marker": "Cortex Readiness", "percent": 45, "source": "docs/atlas-book/02-lanes-and-markers.md"})
            _write(root / "docs/memory/initiatives/continuity-manifest-cortex-readiness.json", json.dumps(manifest, indent=2))
            report = opportunity.build_report(root=root)

        self.assertEqual(opportunity.STATUS_BLOCKED, report["status"])
        self.assertEqual(opportunity.BLOCKER_CONFLICTING_MARKER, report["blocked_candidates"][0]["blocker_class"])

    def test_owner_mutation_deploy_secret_and_workflow_authority_receipts_block(self) -> None:
        cases = [
            ("docs/ops/OWNER-REPO-MUTATION-WORKER-CLUSTER-RECONCILIATION.md", "implementation-backed", opportunity.BLOCKER_OWNER_MUTATION),
            ("docs/ops/DEPLOY-SECRET-WORKER-CLUSTER-RECONCILIATION.md", "requires secret and deploy required", opportunity.BLOCKER_DEPLOY_SECRET),
            ("docs/ops/WORKFLOW-WORKER-CLUSTER-RECONCILIATION.md", "workflow dispatch required", opportunity.BLOCKER_WORKFLOW),
        ]
        for source, text, expected in cases:
            with self.subTest(source=source), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                _write(root / source, text)
                manifest = _manifest("AI Long-Run Batch Orchestration", 69, source)
                _write(root / "docs/memory/initiatives/continuity-manifest-ai-long-run-batch-orchestration.json", json.dumps(manifest, indent=2))
                report = opportunity.build_report(root=root, source_refs=[source])

                self.assertEqual(opportunity.STATUS_BLOCKED, report["status"])
                self.assertEqual(expected, report["blocked_candidates"][0]["blocker_class"])

    def test_main_writes_output_only_to_tmp_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_positive_root(root)
            output = root / "tmp" / "atlas" / "opportunity.json"
            with mock.patch.object(opportunity, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = opportunity.main(["--json", "--output", "tmp/atlas/opportunity.json"])

            self.assertEqual(0, code)
            self.assertTrue(output.exists())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(opportunity.SCHEMA_VERSION, payload["schema_version"])

    def test_main_rejects_protected_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _seed_positive_root(root)
            with mock.patch.object(opportunity, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = opportunity.main(["--json", "--output", "docs/ops/out.json"])

        self.assertEqual(2, code)

    def test_strict_no_opportunities_returns_nonzero(self) -> None:
        self.assertEqual(1, opportunity.report_exit_code(status=opportunity.STATUS_NO_OPPORTUNITIES, strict=True))
        self.assertEqual(0, opportunity.report_exit_code(status=opportunity.STATUS_NO_OPPORTUNITIES, strict=False))


if __name__ == "__main__":
    unittest.main()
