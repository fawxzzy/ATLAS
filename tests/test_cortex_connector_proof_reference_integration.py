from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.cortex.connector_proof_reference_integration import (
    default_integrated_proof_reference_pack_run_json_path,
    integrate_connector_candidates,
    render_integrated_pack_summary,
    write_integrated_proof_reference_pack,
)
from ops.cortex.proof_reference_pack import default_proof_reference_pack_latest_json_path
from ops.cortex.verification_ingest import KNOWN_STACK_VALIDATION_BASELINE


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _base_pack_payload(*, current_validation_debt: list[str] | None = None) -> dict[str, object]:
    return {
        "contract_version": "atlas.cortex.proof-reference-pack.v1",
        "run_id": "lane-ab-run",
        "owner_layer": "cortex",
        "selected_next_action": "lane-ac",
        "next_required_layer": "cortex",
        "receipt_ready": True,
        "blocked": False,
        "blocked_reason": None,
        "pack_status": "review_ready",
        "review_status": "review_ready",
        "known_ambient_debt": [],
        "current_validation_debt": current_validation_debt or [],
        "touched_files": [
            "ops/cortex/connector_proof_reference_integration.py",
            "tests/test_cortex_connector_proof_reference_integration.py",
        ],
        "applied_rules": {
            "decision_rule_ids": ["lane-ab"],
            "plan_rule_ids": ["lane-ac"],
            "rule_ids": ["lane-ab", "lane-ac"],
            "pattern_ids": ["connector-integration"],
            "failure_mode_ids": ["no-live-connectors"],
            "why_selected": ["artifact-gated"],
        },
        "failure_modes_avoided": ["no_lifeline_mutation"],
        "run_artifact_path": "runtime/cortex/runs/lane-ab-run.json",
        "feedback_artifact_path": "runtime/cortex/feedback/latest.json",
        "handoff_artifact_path": "runtime/cortex/receipt-drafts/latest.json",
        "targeted_verification_commands": [
            "python -m unittest tests.test_cortex_proof_reference_pack"
        ],
        "stack_validation": {
            "command": "python .\\ops\\validation\\validate_stack.py",
            "status": "passed",
            "known_ambient_baseline": KNOWN_STACK_VALIDATION_BASELINE.to_payload(),
            "known_ambient_debt": [],
            "current_validation_debt": current_validation_debt or [],
        },
        "references": [
            {
                "reference_id": "run-artifact",
                "kind": "cortex_run_artifact",
                "owner_layer": "cortex",
                "artifact_path": "runtime/cortex/runs/lane-ab-run.json",
                "command": None,
                "claim": "Base Cortex run artifact remains preserved.",
                "status": "ready",
                "notes": [],
            },
            {
                "reference_id": "stack-validation",
                "kind": "stack_validation_command",
                "owner_layer": "stack",
                "artifact_path": None,
                "command": "python .\\ops\\validation\\validate_stack.py",
                "claim": "Validation stays reference-first.",
                "status": "passed",
                "notes": [],
            },
        ],
        "rule_statement": "Base Cortex proof-reference pack.",
        "pattern_statement": "Base pack is preserved.",
        "failure_mode_statement": "Do not overwrite the original pack.",
        "final_receipt_owner": "lifeline",
    }


def _candidate_blocker(code: str, reference_ids: list[str] | None = None) -> dict[str, object]:
    return {
        "source": "lifeline",
        "code": code,
        "message": f"Blocker active: {code}.",
        "reference_ids": reference_ids or [],
    }


def _candidate(
    *,
    candidate_id: str,
    source: str,
    kind: str,
    source_reference_id: str,
    artifact_or_url: str,
    eligible: bool = True,
    blockers: list[str] | None = None,
    owner_layer: str = "github",
    claim: str | None = None,
    status: str = "ready",
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "source": source,
        "kind": kind,
        "owner_layer": owner_layer,
        "claim": claim or f"{source} {kind} evidence is ready.",
        "status": status,
        "artifact_or_url": artifact_or_url,
        "observed_at": "2026-04-29T03:40:00Z",
        "eligible_for_proof_reference": eligible,
        "blockers": blockers or [],
        "source_inventory_path": "runtime/cortex/connector-evidence/latest.json",
        "source_reference_id": source_reference_id,
        "notes": ["Seeded for integration tests."],
    }


def _candidate_set_payload(
    candidates: list[dict[str, object]],
    *,
    candidate_set_blocked: bool = False,
    candidate_set_blockers: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "contract_version": "atlas.cortex.connector-proof-reference-candidates.v1",
        "run_id": "lane-ab-candidates",
        "owner_layer": "cortex",
        "source_inventory_path": "runtime/cortex/connector-evidence/latest.json",
        "source_inventory_run_id": "lane-ab-inventory",
        "lifeline_audit_index_path": "repos/lifeline/.lifeline/audits/proof-reference-receipt-index.json",
        "candidate_set_blocked": candidate_set_blocked,
        "candidate_set_blockers": candidate_set_blockers or [],
        "candidate_count": len(candidates),
        "eligible_candidate_count": sum(
            1 for candidate in candidates if candidate.get("eligible_for_proof_reference")
        ),
        "source_counts": {
            key: sum(1 for candidate in candidates if candidate["source"] == key)
            for key in sorted({candidate["source"] for candidate in candidates})
        },
        "candidates": candidates,
        "rule_statement": "Candidates remain pre-publication.",
        "pattern_statement": "Inventory flows to candidates before integration.",
        "failure_mode_statement": "Do not publish candidates directly.",
        "lifeline_receipt_truth_owner": "lifeline",
    }


class CortexConnectorProofReferenceIntegrationTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return Path(temp_dir.name)

    def _seed_base_pack(self, root: Path, *, current_validation_debt: list[str] | None = None) -> Path:
        path = default_proof_reference_pack_latest_json_path(root)
        _write_json(path, _base_pack_payload(current_validation_debt=current_validation_debt))
        return path

    def _seed_candidate_set(
        self,
        root: Path,
        candidates: list[dict[str, object]],
        *,
        candidate_set_blocked: bool = False,
        candidate_set_blockers: list[dict[str, object]] | None = None,
    ) -> Path:
        path = root / "runtime" / "cortex" / "connector-proof-reference-candidates" / "latest.json"
        _write_json(
            path,
            _candidate_set_payload(
                candidates,
                candidate_set_blocked=candidate_set_blocked,
                candidate_set_blockers=candidate_set_blockers,
            ),
        )
        return path

    def test_integrates_eligible_github_candidate_into_a_proof_reference_pack(self) -> None:
        root = self._temp_root()
        self._seed_base_pack(root)
        self._seed_candidate_set(
            root,
            [
                _candidate(
                    candidate_id="github-pr-4",
                    source="github",
                    kind="pull_request",
                    owner_layer="github",
                    source_reference_id="github-pr-4",
                    artifact_or_url="https://github.com/example/atlas/pull/4",
                )
            ],
        )

        result = integrate_connector_candidates(root=root)

        connector_refs = [reference for reference in result.references if reference.source == "connector_candidate"]
        self.assertEqual(1, len(connector_refs))
        self.assertEqual("https://github.com/example/atlas/pull/4", connector_refs[0].url)
        self.assertEqual("github-pr-4", connector_refs[0].source_candidate_id)
        self.assertEqual("github-pr-4", connector_refs[0].source_reference_id)

    def test_integrates_eligible_vercel_candidate_into_a_proof_reference_pack(self) -> None:
        root = self._temp_root()
        self._seed_base_pack(root)
        self._seed_candidate_set(
            root,
            [
                _candidate(
                    candidate_id="vercel-deployment-1",
                    source="vercel",
                    kind="deployment",
                    owner_layer="vercel",
                    source_reference_id="vercel-deployment-1",
                    artifact_or_url="https://atlas-cortex-git-lane-ab.vercel.app",
                )
            ],
        )

        result = integrate_connector_candidates(root=root)

        connector_ref = next(reference for reference in result.references if reference.source == "connector_candidate")
        self.assertEqual(1, result.candidate_source_counts["vercel"])
        self.assertEqual("vercel-deployment-1", connector_ref.source_candidate_id)
        self.assertEqual("vercel-deployment-1", connector_ref.source_reference_id)
        self.assertEqual("https://atlas-cortex-git-lane-ab.vercel.app", connector_ref.url)

    def test_preserves_existing_base_proof_references(self) -> None:
        root = self._temp_root()
        self._seed_base_pack(root)
        self._seed_candidate_set(
            root,
            [
                _candidate(
                    candidate_id="github-pr-4",
                    source="github",
                    kind="pull_request",
                    owner_layer="github",
                    source_reference_id="github-pr-4",
                    artifact_or_url="https://github.com/example/atlas/pull/4",
                )
            ],
        )

        result = integrate_connector_candidates(root=root)

        reference_ids = [reference.reference_id for reference in result.references]
        self.assertIn("run-artifact", reference_ids)
        self.assertIn("stack-validation", reference_ids)

    def test_deduplicates_connector_references_deterministically(self) -> None:
        root = self._temp_root()
        self._seed_base_pack(root)
        duplicate_candidates = [
            _candidate(
                candidate_id="dup-a",
                source="github",
                kind="pull_request",
                owner_layer="github",
                source_reference_id="github-pr-4",
                artifact_or_url="https://github.com/example/atlas/pull/4",
            ),
            _candidate(
                candidate_id="dup-b",
                source="github",
                kind="pull_request",
                owner_layer="github",
                source_reference_id="github-pr-4",
                artifact_or_url="https://github.com/example/atlas/pull/4",
            ),
        ]
        self._seed_candidate_set(root, duplicate_candidates)

        result = integrate_connector_candidates(root=root)

        connector_refs = [reference for reference in result.references if reference.source == "connector_candidate"]
        self.assertEqual(1, len(connector_refs))
        self.assertEqual("dup-a", connector_refs[0].source_candidate_id)

    def test_blocks_integration_when_candidate_set_blocked_true(self) -> None:
        root = self._temp_root()
        self._seed_base_pack(root)
        self._seed_candidate_set(
            root,
            [
                _candidate(
                    candidate_id="github-pr-4",
                    source="github",
                    kind="pull_request",
                    owner_layer="github",
                    source_reference_id="github-pr-4",
                    artifact_or_url="https://github.com/example/atlas/pull/4",
                )
            ],
            candidate_set_blocked=True,
            candidate_set_blockers=[_candidate_blocker("invalid_receipts_present")],
        )

        result = integrate_connector_candidates(root=root)

        self.assertTrue(result.blocked)
        self.assertEqual("blocked", result.pack_status)
        self.assertIn("invalid_receipts_present", result.blocked_reason or "")
        self.assertEqual(0, result.integrated_candidate_count)

    def test_blocks_integration_when_invalid_receipts_exist(self) -> None:
        root = self._temp_root()
        self._seed_base_pack(root)
        self._seed_candidate_set(
            root,
            [],
            candidate_set_blocked=True,
            candidate_set_blockers=[_candidate_blocker("invalid_receipts_present")],
        )

        result = integrate_connector_candidates(root=root)

        self.assertEqual(
            ["invalid_receipts_present"],
            [blocker.code for blocker in result.integration_blockers],
        )

    def test_blocks_integration_when_current_validation_debt_exists(self) -> None:
        root = self._temp_root()
        self._seed_base_pack(root)
        self._seed_candidate_set(
            root,
            [],
            candidate_set_blocked=True,
            candidate_set_blockers=[_candidate_blocker("current_validation_debt_present")],
        )

        result = integrate_connector_candidates(root=root)

        self.assertIn(
            "current_validation_debt_present",
            [blocker.code for blocker in result.integration_blockers],
        )

    def test_blocks_integration_when_auto_approved_drift_exists(self) -> None:
        root = self._temp_root()
        self._seed_base_pack(root)
        self._seed_candidate_set(
            root,
            [],
            candidate_set_blocked=True,
            candidate_set_blockers=[_candidate_blocker("auto_approved_violation")],
        )

        result = integrate_connector_candidates(root=root)

        self.assertIn(
            "auto_approved_violation",
            [blocker.code for blocker in result.integration_blockers],
        )

    def test_blocks_integration_when_boundary_violations_exist(self) -> None:
        root = self._temp_root()
        self._seed_base_pack(root)
        self._seed_candidate_set(
            root,
            [],
            candidate_set_blocked=True,
            candidate_set_blockers=[_candidate_blocker("missing_boundary_statement")],
        )

        result = integrate_connector_candidates(root=root)

        self.assertIn(
            "missing_boundary_statement",
            [blocker.code for blocker in result.integration_blockers],
        )

    def test_skips_ineligible_or_blocked_individual_candidates(self) -> None:
        root = self._temp_root()
        self._seed_base_pack(root)
        self._seed_candidate_set(
            root,
            [
                _candidate(
                    candidate_id="github-pr-4",
                    source="github",
                    kind="pull_request",
                    owner_layer="github",
                    source_reference_id="github-pr-4",
                    artifact_or_url="https://github.com/example/atlas/pull/4",
                ),
                _candidate(
                    candidate_id="github-pr-5",
                    source="github",
                    kind="pull_request",
                    owner_layer="github",
                    source_reference_id="github-pr-5",
                    artifact_or_url="https://github.com/example/atlas/pull/5",
                    eligible=False,
                ),
                _candidate(
                    candidate_id="github-pr-6",
                    source="github",
                    kind="pull_request",
                    owner_layer="github",
                    source_reference_id="github-pr-6",
                    artifact_or_url="https://github.com/example/atlas/pull/6",
                    blockers=["invalid_receipts_present"],
                ),
            ],
        )

        result = integrate_connector_candidates(root=root)

        connector_refs = [reference for reference in result.references if reference.source == "connector_candidate"]
        self.assertEqual(1, len(connector_refs))
        self.assertEqual(2, result.skipped_candidate_count)

    def test_fails_clearly_on_missing_base_proof_reference_pack(self) -> None:
        root = self._temp_root()
        self._seed_candidate_set(root, [])

        with self.assertRaisesRegex(FileNotFoundError, "Base proof-reference pack not found at"):
            integrate_connector_candidates(root=root)

    def test_fails_clearly_on_missing_candidate_artifact(self) -> None:
        root = self._temp_root()
        self._seed_base_pack(root)

        with self.assertRaisesRegex(
            FileNotFoundError,
            "Connector proof-reference candidate artifact not found at",
        ):
            integrate_connector_candidates(root=root)

    def test_fails_clearly_on_malformed_json(self) -> None:
        root = self._temp_root()
        self._seed_base_pack(root)
        malformed_path = root / "runtime" / "cortex" / "connector-proof-reference-candidates" / "latest.json"
        _write_text(malformed_path, "{not json}\n")

        with self.assertRaisesRegex(
            ValueError,
            "Malformed connector proof-reference candidate artifact JSON at",
        ):
            integrate_connector_candidates(root=root)

    def test_writes_latest_and_run_scoped_json_and_text_artifacts(self) -> None:
        root = self._temp_root()
        self._seed_base_pack(root)
        self._seed_candidate_set(
            root,
            [
                _candidate(
                    candidate_id="github-pr-4",
                    source="github",
                    kind="pull_request",
                    owner_layer="github",
                    source_reference_id="github-pr-4",
                    artifact_or_url="https://github.com/example/atlas/pull/4",
                )
            ],
        )

        artifact = write_integrated_proof_reference_pack(root=root)

        self.assertTrue(artifact.latest_artifact_path.exists())
        self.assertTrue(artifact.latest_summary_path.exists() if artifact.latest_summary_path else False)
        self.assertEqual(
            default_integrated_proof_reference_pack_run_json_path("lane-ab-run", root),
            artifact.run_artifact_path,
        )
        self.assertTrue(artifact.run_artifact_path.exists())
        self.assertTrue(artifact.run_summary_path.exists() if artifact.run_summary_path else False)

    def test_output_is_json_serializable(self) -> None:
        root = self._temp_root()
        self._seed_base_pack(root)
        self._seed_candidate_set(
            root,
            [
                _candidate(
                    candidate_id="vercel-deployment-1",
                    source="vercel",
                    kind="deployment",
                    owner_layer="vercel",
                    source_reference_id="vercel-deployment-1",
                    artifact_or_url="https://atlas-cortex-git-lane-ab.vercel.app",
                )
            ],
        )

        result = integrate_connector_candidates(root=root)
        summary = render_integrated_pack_summary(result)
        payload = result.to_payload(root=root)

        json.dumps(payload, sort_keys=True)
        connector_payload = next(
            reference for reference in payload["references"] if reference["source"] == "connector_candidate"
        )
        self.assertEqual("vercel-deployment-1", connector_payload["source_reference_id"])
        self.assertIn("Cortex Integrated Proof Reference Pack", summary)

    def test_does_not_require_live_connectors(self) -> None:
        root = self._temp_root()
        self._seed_base_pack(root)
        self._seed_candidate_set(
            root,
            [
                _candidate(
                    candidate_id="github-pr-4",
                    source="github",
                    kind="pull_request",
                    owner_layer="github",
                    source_reference_id="github-pr-4",
                    artifact_or_url="https://github.com/example/atlas/pull/4",
                ),
                _candidate(
                    candidate_id="vercel-deployment-1",
                    source="vercel",
                    kind="deployment",
                    owner_layer="vercel",
                    source_reference_id="vercel-deployment-1",
                    artifact_or_url="https://atlas-cortex-git-lane-ab.vercel.app",
                ),
            ],
        )

        result = integrate_connector_candidates(root=root)

        self.assertFalse(result.blocked)
        self.assertEqual(2, result.integrated_candidate_count)

    def test_does_not_mutate_lifeline_receipts_or_original_proof_reference_packs(self) -> None:
        root = self._temp_root()
        base_pack_path = self._seed_base_pack(root)
        self._seed_candidate_set(
            root,
            [
                _candidate(
                    candidate_id="github-pr-4",
                    source="github",
                    kind="pull_request",
                    owner_layer="github",
                    source_reference_id="github-pr-4",
                    artifact_or_url="https://github.com/example/atlas/pull/4",
                )
            ],
        )
        receipt_path = root / "repos" / "lifeline" / ".lifeline" / "receipts" / "proof-reference-accepted" / "fitness" / "F11" / "sha256-one.json"
        _write_json(receipt_path, {"receipt_id": "sha256:one"})
        before = {
            "base_pack": base_pack_path.read_text(encoding="utf-8"),
            "receipt": receipt_path.read_text(encoding="utf-8"),
        }

        write_integrated_proof_reference_pack(root=root)

        after = {
            "base_pack": base_pack_path.read_text(encoding="utf-8"),
            "receipt": receipt_path.read_text(encoding="utf-8"),
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
