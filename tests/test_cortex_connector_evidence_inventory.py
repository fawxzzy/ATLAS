from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.cortex.connector_evidence_inventory import (
    build_connector_evidence_inventory,
    default_connector_evidence_run_json_path,
    render_connector_evidence_inventory_summary,
    write_connector_evidence_inventory,
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
        "receipts_root": "repos/fawxzzy-lifeline/.lifeline/receipts/proof-reference-accepted",
        "schema_path": "repos/fawxzzy-lifeline/schemas/proof-reference-receipt.schema.json",
        "audit_artifact_written": True,
        "audit_artifact_path": "repos/fawxzzy-lifeline/.lifeline/audits/proof-reference-receipt-index.json",
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


class CortexConnectorEvidenceInventoryTests(unittest.TestCase):
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

    def test_builds_inventory_from_explicit_github_input_and_writes_runtime_artifacts(self) -> None:
        root = self._temp_root()
        self._seed_proof_reference_pack(root)

        artifact = write_connector_evidence_inventory(
            github_evidence=_github_evidence(),
            root=root,
        )

        payload = artifact.payload
        self.assertTrue(artifact.latest_artifact_path.exists())
        self.assertTrue(artifact.latest_summary_path.exists() if artifact.latest_summary_path else False)
        self.assertEqual("latest.json", artifact.latest_artifact_path.name)
        self.assertEqual(
            default_connector_evidence_run_json_path("lane-aa-run", root),
            artifact.run_artifact_path,
        )
        self.assertEqual(5, payload["evidence_count"])
        self.assertEqual({"cortex": 2, "github": 3}, payload["source_counts"])
        reference_ids = {item["reference_id"] for item in payload["evidence"]}
        self.assertIn("github-pr-4", reference_ids)
        self.assertIn("github-workflow-run-101", reference_ids)
        self.assertIn("github-commit-abc123def456", reference_ids)
        self.assertIn("run-artifact", reference_ids)
        self.assertIn("stack-validation", reference_ids)
        self.assertIn("Inventory only: yes", artifact.summary)

    def test_builds_inventory_from_explicit_vercel_input(self) -> None:
        root = self._temp_root()

        inventory = build_connector_evidence_inventory(
            vercel_evidence=_vercel_evidence(),
            run_id="lane-aa-vercel",
            root=root,
        )

        self.assertEqual("lane-aa-vercel", inventory.run_id)
        self.assertEqual({"vercel": 2}, inventory.source_counts)
        kinds = {(item.source, item.kind) for item in inventory.evidence}
        self.assertIn(("vercel", "project"), kinds)
        self.assertIn(("vercel", "deployment"), kinds)
        self.assertEqual(2, inventory.eligible_candidate_count)

    def test_includes_lifeline_audit_index_blockers_when_present(self) -> None:
        root = self._temp_root()
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

        inventory = build_connector_evidence_inventory(
            github_evidence=_github_evidence(),
            lifeline_audit_index_path=audit_path,
            root=root,
        )

        blocker_codes = [item.code for item in inventory.connector_publication_blockers]
        self.assertIn("invalid_receipts_present", blocker_codes)
        self.assertIn("current_validation_debt_present", blocker_codes)
        self.assertTrue(inventory.connector_publication_blocked)
        github_pull_request = next(
            item for item in inventory.evidence if item.reference_id == "github-pr-4"
        )
        self.assertFalse(github_pull_request.eligible_for_proof_reference)
        self.assertIn("invalid_receipts_present", github_pull_request.blockers)

    def test_marks_invalid_receipts_and_current_validation_debt_as_connector_publication_blockers(self) -> None:
        root = self._temp_root()
        receipt_path = ".lifeline/receipts/proof-reference-accepted/fitness/F09/sha256-debt.json"
        audit_path = self._seed_lifeline_audit_index(
            root,
            receipt_count=1,
            invalid_receipt_count=1,
            receipts_by_source_repo_id={"fitness": [receipt_path]},
            receipts_by_tranche_id={"F09": [receipt_path]},
            invalid_receipts=[_invalid_receipt(receipt_path)],
            receipts_with_current_validation_debt=[receipt_path],
        )

        payload = build_connector_evidence_inventory(
            github_evidence=_github_evidence(),
            lifeline_audit_index_path=audit_path,
            root=root,
        ).to_payload()

        codes = [item["code"] for item in payload["connector_publication_blockers"]]
        self.assertEqual(
            ["current_validation_debt_present", "invalid_receipts_present"],
            sorted(codes),
        )

    def test_does_not_require_live_connectors(self) -> None:
        root = self._temp_root()

        inventory = build_connector_evidence_inventory(
            github_evidence=_github_evidence(),
            vercel_evidence=_vercel_evidence(),
            run_id="lane-aa-offline",
            root=root,
        )

        self.assertEqual("lane-aa-offline", inventory.run_id)
        self.assertEqual({"github": 3, "vercel": 2}, inventory.source_counts)

    def test_does_not_mutate_lifeline_or_cortex_receipt_artifacts(self) -> None:
        root = self._temp_root()
        self._seed_proof_reference_pack(root)
        self._seed_lifeline_audit_index(root)
        receipt_path = root / "runtime" / "cortex" / "lifeline-write-ready" / "latest.json"
        _write_json(receipt_path, {"contract_version": "atlas.cortex.lifeline-write-ready.v1"})
        before = {
            str(path.relative_to(root)): path.read_text(encoding="utf-8")
            for path in sorted(root.rglob("*.json"))
        }

        build_connector_evidence_inventory(
            github_evidence=_github_evidence(),
            vercel_evidence=_vercel_evidence(),
            root=root,
        )

        after = {
            str(path.relative_to(root)): path.read_text(encoding="utf-8")
            for path in sorted(root.rglob("*.json"))
        }
        self.assertEqual(before, after)

    def test_output_is_json_serializable(self) -> None:
        root = self._temp_root()
        self._seed_proof_reference_pack(root)

        inventory = build_connector_evidence_inventory(
            github_evidence=_github_evidence(),
            vercel_evidence=_vercel_evidence(),
            root=root,
        )

        json.dumps(inventory.to_payload(), sort_keys=True)
        summary = render_connector_evidence_inventory_summary(inventory)
        self.assertIn("Cortex Connector Evidence Inventory", summary)

    def test_malformed_evidence_input_fails_clearly(self) -> None:
        root = self._temp_root()

        with self.assertRaisesRegex(
            ValueError,
            "Expected list for github_evidence.workflow_runs",
        ):
            build_connector_evidence_inventory(
                github_evidence={"workflow_runs": "not-a-list"},
                run_id="lane-aa-bad",
                root=root,
            )

    def test_inventory_is_deterministic(self) -> None:
        root = self._temp_root()
        self._seed_proof_reference_pack(root)
        github_a = _github_evidence()
        github_b = {
            "observed_at": "2026-04-28T21:15:00Z",
            "commits": list(reversed(github_a["commits"])),  # type: ignore[index]
            "workflow_runs": list(reversed(github_a["workflow_runs"])),  # type: ignore[index]
            "pull_request": github_a["pull_request"],  # type: ignore[index]
        }

        payload_a = build_connector_evidence_inventory(
            github_evidence=github_a,
            vercel_evidence=_vercel_evidence(),
            root=root,
        ).to_payload()
        payload_b = build_connector_evidence_inventory(
            github_evidence=github_b,
            vercel_evidence=_vercel_evidence(),
            root=root,
        ).to_payload()

        self.assertEqual(payload_a, payload_b)

    def test_evidence_candidates_are_not_treated_as_final_proof_references(self) -> None:
        root = self._temp_root()
        inventory = build_connector_evidence_inventory(
            github_evidence=_github_evidence(),
            run_id="lane-aa-inventory-only",
            root=root,
        )

        payload = inventory.to_payload()
        self.assertTrue(payload["inventory_only"])
        self.assertFalse(payload["connector_observations_are_final_proof_references"])
        self.assertEqual(
            "Cortex may inventory connector-backed evidence candidates, but connector observations are not final proof references or Lifeline receipts.",
            payload["rule_statement"],
        )


if __name__ == "__main__":
    unittest.main()
