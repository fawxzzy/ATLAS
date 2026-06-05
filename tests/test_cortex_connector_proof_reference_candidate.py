from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.cortex.connector_evidence_inventory import (
    default_connector_evidence_latest_json_path,
    write_connector_evidence_inventory,
)
from ops.cortex.connector_proof_reference_candidate import (
    build_connector_proof_reference_candidates,
    default_connector_proof_reference_candidate_run_json_path,
    render_connector_proof_reference_candidate_summary,
    write_connector_proof_reference_candidates,
)
from ops.cortex.lifeline_audit_index import default_lifeline_audit_index_path
from ops.cortex.proof_reference_pack import default_proof_reference_pack_latest_json_path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _base_audit_index(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "receipt_count": 0,
        "valid_receipt_count": 0,
        "invalid_receipt_count": 0,
        "receipts_by_source_repo_id": {},
        "receipts_by_tranche_id": {},
        "proof_reference_count_total": 0,
        "receipts_with_ambient_debt": [],
        "receipts_with_current_validation_debt": [],
        "receipts_missing_boundary_statement": [],
        "receipts_with_auto_approved_not_false": [],
        "invalid_receipts": [],
        "receipt_inventory": [],
        "receipts_root": "repos/lifeline/.lifeline/receipts/proof-reference-accepted",
        "schema_path": "repos/lifeline/schemas/proof-reference-receipt.schema.json",
        "audit_artifact_written": True,
        "audit_artifact_path": "repos/lifeline/.lifeline/audits/proof-reference-receipt-index.json",
    }
    payload.update(overrides)
    return payload


def _invalid_receipt(receipt_path: str) -> dict[str, object]:
    return {
        "receipt_path": receipt_path,
        "path_source_repo_id": "fitness",
        "path_tranche_id": "F11",
        "source_repo_id": "fitness",
        "tranche_id": "F11",
        "receipt_id": "sha256:invalid-receipt",
        "parsed": True,
        "schema_valid": False,
        "blocked_reason": "receipt_invalid",
        "validation_errors": ["$.status is required."],
    }


def _github_evidence() -> dict[str, object]:
    return {
        "observed_at": "2026-04-28T21:15:00Z",
        "pull_request": {
            "number": 4,
            "url": "https://github.com/example/atlas/pull/4",
            "status": "open",
            "head_sha": "abc123def4567890",
        },
        "workflow_runs": [
            {
                "run_id": 101,
                "url": "https://github.com/example/atlas/actions/runs/101",
                "workflow": "ci",
                "conclusion": "success",
            }
        ],
        "commits": [
            {
                "sha": "abc123def4567890",
                "url": "https://github.com/example/atlas/commit/abc123def4567890",
            }
        ],
    }


def _vercel_evidence() -> dict[str, object]:
    return {
        "observed_at": "2026-04-28T21:20:00Z",
        "project": {
            "id": "prj_lane_aa",
            "name": "atlas-cortex",
            "url": "https://vercel.com/example/atlas-cortex",
            "status": "linked",
        },
        "deployment": {
            "id": "dpl_lane_aa",
            "url": "https://atlas-cortex-git-lane-aa.vercel.app",
            "state": "ready",
            "commit_sha": "abc123def4567890",
        },
    }


def _proof_reference_pack_payload() -> dict[str, object]:
    return {
        "contract_version": "atlas.cortex.proof-reference-pack.v1",
        "run_id": "lane-aa-run",
        "references": [
            {
                "reference_id": "run-artifact",
                "kind": "cortex_run_artifact",
                "owner_layer": "cortex",
                "artifact_path": "runtime/cortex/runs/latest.json",
                "command": None,
                "claim": "CortexRunResult records the selected action for Lane AA.",
                "status": "ready",
                "notes": [],
            },
            {
                "reference_id": "stack-validation",
                "kind": "stack_validation_command",
                "owner_layer": "stack",
                "artifact_path": None,
                "command": "python .\\ops\\validation\\validate_stack.py",
                "claim": "Stack validation remains reference-first.",
                "status": "tracked",
                "notes": [],
            },
        ],
    }


class CortexConnectorProofReferenceCandidateTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return Path(temp_dir.name)

    def _seed_proof_reference_pack(self, root: Path) -> Path:
        path = default_proof_reference_pack_latest_json_path(root)
        _write_json(path, _proof_reference_pack_payload())
        return path

    def _seed_lifeline_audit_index(self, root: Path, **overrides: object) -> Path:
        path = default_lifeline_audit_index_path(root)
        _write_json(path, _base_audit_index(**overrides))
        return path

    def _seed_inventory(
        self,
        root: Path,
        *,
        github_evidence: dict[str, object] | None = None,
        vercel_evidence: dict[str, object] | None = None,
        lifeline_audit_index_path: Path | None = None,
    ) -> Path:
        write_connector_evidence_inventory(
            github_evidence=github_evidence,
            vercel_evidence=vercel_evidence,
            lifeline_audit_index_path=lifeline_audit_index_path,
            root=root,
        )
        return default_connector_evidence_latest_json_path(root)

    def _assert_blocked_by(self, *, code: str, **audit_overrides: object) -> None:
        root = self._temp_root()
        receipt_path = ".lifeline/receipts/proof-reference-accepted/fitness/F11/sha256-one.json"
        audit_defaults: dict[str, object] = {
            "receipt_count": 1,
            "valid_receipt_count": 1,
            "receipts_by_source_repo_id": {"fitness": [receipt_path]},
            "receipts_by_tranche_id": {"F11": [receipt_path]},
            "proof_reference_count_total": 1,
        }
        audit_defaults.update(audit_overrides)
        audit_path = self._seed_lifeline_audit_index(
            root,
            **audit_defaults,
        )
        inventory_path = self._seed_inventory(
            root,
            github_evidence=_github_evidence(),
            lifeline_audit_index_path=audit_path,
        )

        candidate_set = build_connector_proof_reference_candidates(
            inventory_path,
            root=root,
        )

        blocker_codes = [item.code for item in candidate_set.candidate_set_blockers]
        self.assertTrue(candidate_set.candidate_set_blocked)
        self.assertIn(code, blocker_codes)

    def test_builds_proof_reference_candidates_from_eligible_github_evidence(self) -> None:
        root = self._temp_root()
        inventory_path = self._seed_inventory(root, github_evidence=_github_evidence())

        candidate_set = build_connector_proof_reference_candidates(inventory_path, root=root)

        self.assertEqual("connector-evidence.latest", candidate_set.run_id)
        self.assertEqual({"github": 3}, candidate_set.source_counts)
        self.assertEqual(3, candidate_set.eligible_candidate_count)
        candidates = {item.source_reference_id: item for item in candidate_set.candidates}
        self.assertEqual("github", candidates["github-pr-4"].source)
        self.assertTrue(candidates["github-pr-4"].eligible_for_proof_reference)
        self.assertEqual(
            "https://github.com/example/atlas/pull/4",
            candidates["github-pr-4"].artifact_or_url,
        )

    def test_builds_proof_reference_candidates_from_eligible_vercel_evidence(self) -> None:
        root = self._temp_root()
        inventory_path = self._seed_inventory(root, vercel_evidence=_vercel_evidence())

        candidate_set = build_connector_proof_reference_candidates(inventory_path, root=root)

        self.assertEqual({"vercel": 2}, candidate_set.source_counts)
        self.assertEqual(2, candidate_set.eligible_candidate_count)
        kinds = {(item.source, item.kind) for item in candidate_set.candidates}
        self.assertIn(("vercel", "project"), kinds)
        self.assertIn(("vercel", "deployment"), kinds)

    def test_carries_lifeline_audit_index_blockers_into_the_candidate_set(self) -> None:
        root = self._temp_root()
        self._seed_proof_reference_pack(root)
        receipt_path = ".lifeline/receipts/proof-reference-accepted/fitness/F11/sha256-invalid.json"
        audit_path = self._seed_lifeline_audit_index(
            root,
            receipt_count=1,
            invalid_receipt_count=1,
            receipts_by_source_repo_id={"fitness": [receipt_path]},
            receipts_by_tranche_id={"F11": [receipt_path]},
            invalid_receipts=[_invalid_receipt(receipt_path)],
            receipts_with_current_validation_debt=[receipt_path],
        )
        inventory_path = self._seed_inventory(
            root,
            github_evidence=_github_evidence(),
            lifeline_audit_index_path=audit_path,
        )

        candidate_set = build_connector_proof_reference_candidates(inventory_path, root=root)

        blocker_codes = [item.code for item in candidate_set.candidate_set_blockers]
        self.assertTrue(candidate_set.candidate_set_blocked)
        self.assertEqual(
            {"cortex_artifact": 2, "github": 3, "lifeline_audit": 1},
            candidate_set.source_counts,
        )
        self.assertIn("invalid_receipts_present", blocker_codes)
        self.assertIn("current_validation_debt_present", blocker_codes)
        github_candidate = next(
            item for item in candidate_set.candidates if item.source_reference_id == "github-pr-4"
        )
        self.assertFalse(github_candidate.eligible_for_proof_reference)
        self.assertIn("invalid_receipts_present", github_candidate.blockers)
        self.assertIn("current_validation_debt_present", github_candidate.blockers)

    def test_blocks_candidate_set_when_invalid_receipts_exist(self) -> None:
        receipt_path = ".lifeline/receipts/proof-reference-accepted/fitness/F11/sha256-invalid.json"
        self._assert_blocked_by(
            code="invalid_receipts_present",
            receipt_count=1,
            invalid_receipt_count=1,
            valid_receipt_count=0,
            invalid_receipts=[_invalid_receipt(receipt_path)],
        )

    def test_blocks_candidate_set_when_current_validation_debt_exists(self) -> None:
        receipt_path = ".lifeline/receipts/proof-reference-accepted/fitness/F11/sha256-debt.json"
        self._assert_blocked_by(
            code="current_validation_debt_present",
            receipts_with_current_validation_debt=[receipt_path],
        )

    def test_blocks_candidate_set_when_auto_approved_drift_exists(self) -> None:
        receipt_path = ".lifeline/receipts/proof-reference-accepted/fitness/F11/sha256-auto.json"
        self._assert_blocked_by(
            code="auto_approved_violation",
            receipts_with_auto_approved_not_false=[receipt_path],
        )

    def test_blocks_candidate_set_when_boundary_statement_violations_exist(self) -> None:
        receipt_path = ".lifeline/receipts/proof-reference-accepted/playbook/A02/sha256-boundary.json"
        self._assert_blocked_by(
            code="missing_boundary_statement",
            receipts_by_source_repo_id={"playbook": [receipt_path]},
            receipts_by_tranche_id={"A02": [receipt_path]},
            receipts_missing_boundary_statement=[receipt_path],
        )

    def test_fails_clearly_on_missing_inventory_path(self) -> None:
        root = self._temp_root()
        inventory_path = root / "runtime" / "cortex" / "connector-evidence" / "missing.json"

        with self.assertRaisesRegex(FileNotFoundError, "Connector evidence inventory not found at"):
            build_connector_proof_reference_candidates(inventory_path, root=root)

    def test_fails_clearly_on_malformed_inventory_json(self) -> None:
        root = self._temp_root()
        inventory_path = root / "runtime" / "cortex" / "connector-evidence" / "latest.json"
        inventory_path.parent.mkdir(parents=True, exist_ok=True)
        inventory_path.write_text("{not json}\n", encoding="utf-8")

        with self.assertRaisesRegex(
            ValueError,
            "Malformed connector evidence inventory JSON at",
        ):
            build_connector_proof_reference_candidates(inventory_path, root=root)

    def test_output_is_json_serializable(self) -> None:
        root = self._temp_root()
        self._seed_proof_reference_pack(root)
        inventory_path = self._seed_inventory(
            root,
            github_evidence=_github_evidence(),
            vercel_evidence=_vercel_evidence(),
        )

        candidate_set = build_connector_proof_reference_candidates(inventory_path, root=root)

        json.dumps(candidate_set.to_payload(), sort_keys=True)
        summary = render_connector_proof_reference_candidate_summary(candidate_set)
        self.assertIn("Cortex Connector Proof Reference Candidate Set", summary)

    def test_candidate_artifact_writer_writes_latest_and_run_scoped_json_and_text_artifacts(self) -> None:
        root = self._temp_root()
        self._seed_proof_reference_pack(root)
        inventory_path = self._seed_inventory(root, github_evidence=_github_evidence())

        artifact = write_connector_proof_reference_candidates(inventory_path, root=root)

        self.assertTrue(artifact.latest_artifact_path.exists())
        self.assertTrue(artifact.latest_summary_path.exists() if artifact.latest_summary_path else False)
        self.assertEqual(
            default_connector_proof_reference_candidate_run_json_path("lane-aa-run", root),
            artifact.run_artifact_path,
        )
        self.assertTrue(artifact.run_artifact_path.exists())
        self.assertTrue(artifact.run_summary_path.exists() if artifact.run_summary_path else False)
        self.assertIn("Candidate set blocked: no", artifact.summary)

    def test_candidate_builder_does_not_require_live_connectors(self) -> None:
        root = self._temp_root()
        inventory_path = self._seed_inventory(
            root,
            github_evidence=_github_evidence(),
            vercel_evidence=_vercel_evidence(),
        )

        candidate_set = build_connector_proof_reference_candidates(inventory_path, root=root)

        self.assertEqual({"github": 3, "vercel": 2}, candidate_set.source_counts)
        self.assertFalse(candidate_set.candidate_set_blocked)

    def test_candidate_builder_does_not_mutate_lifeline_receipts_or_proof_reference_packs(self) -> None:
        root = self._temp_root()
        self._seed_proof_reference_pack(root)
        self._seed_lifeline_audit_index(root)
        inventory_path = self._seed_inventory(
            root,
            github_evidence=_github_evidence(),
            lifeline_audit_index_path=default_lifeline_audit_index_path(root),
        )
        before = {
            str(path.relative_to(root)): path.read_text(encoding="utf-8")
            for path in sorted(root.rglob("*.json"))
        }

        build_connector_proof_reference_candidates(inventory_path, root=root)

        after = {
            str(path.relative_to(root)): path.read_text(encoding="utf-8")
            for path in sorted(root.rglob("*.json"))
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
