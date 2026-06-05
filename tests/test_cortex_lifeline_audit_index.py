from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.cortex.lifeline_audit_index import (
    default_lifeline_audit_index_path,
    summarize_lifeline_audit_index,
)


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


def _invalid_receipt(
    *,
    receipt_path: str,
    source_repo_id: str = "fitness",
    tranche_id: str = "F11",
    blocked_reason: str = "receipt_invalid",
    validation_errors: list[str] | None = None,
) -> dict[str, object]:
    return {
        "receipt_path": receipt_path,
        "path_source_repo_id": source_repo_id,
        "path_tranche_id": tranche_id,
        "source_repo_id": source_repo_id,
        "tranche_id": tranche_id,
        "receipt_id": "sha256:invalid-receipt",
        "parsed": True,
        "schema_valid": False,
        "blocked_reason": blocked_reason,
        "validation_errors": validation_errors or ["$.status is required."],
    }


class CortexLifelineAuditIndexTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return Path(temp_dir.name)

    def test_reads_a_valid_empty_lifeline_audit_index(self) -> None:
        root = self._temp_root()
        audit_path = default_lifeline_audit_index_path(root)
        _write_json(audit_path, _base_audit_index())

        summary = summarize_lifeline_audit_index(audit_path, root=root)

        self.assertEqual(0, summary.receipt_count)
        self.assertEqual(0, summary.valid_receipt_count)
        self.assertEqual(0, summary.invalid_receipt_count)
        self.assertEqual({}, summary.receipts_by_source_repo_id)
        self.assertEqual({}, summary.receipts_by_tranche_id)
        self.assertEqual((), summary.invalid_receipts)
        self.assertEqual((), summary.connector_publication_blockers)
        self.assertFalse(summary.connector_publication_blocked)
        self.assertTrue(summary.cortex_read_only)

    def test_reads_a_valid_index_with_one_receipt_from_the_conventional_path(self) -> None:
        root = self._temp_root()
        audit_path = default_lifeline_audit_index_path(root)
        receipt_path = ".lifeline/receipts/proof-reference-accepted/fitness/F11/sha256-one.json"
        _write_json(
            audit_path,
            _base_audit_index(
                receipt_count=1,
                valid_receipt_count=1,
                receipts_by_source_repo_id={"fitness": [receipt_path]},
                receipts_by_tranche_id={"F11": [receipt_path]},
                proof_reference_count_total=2,
                receipts_with_ambient_debt=[receipt_path],
            ),
        )

        summary = summarize_lifeline_audit_index(root=root)

        self.assertEqual(1, summary.receipt_count)
        self.assertEqual(1, summary.valid_receipt_count)
        self.assertEqual(0, summary.invalid_receipt_count)
        self.assertEqual("repos/lifeline/.lifeline/audits/proof-reference-receipt-index.json", summary.lifeline_audit_index_path)
        self.assertEqual((receipt_path,), summary.receipts_with_ambient_debt)
        self.assertFalse(summary.connector_publication_blocked)

    def test_preserves_source_repo_and_tranche_grouping(self) -> None:
        root = self._temp_root()
        audit_path = root / "tmp" / "lifeline-index.json"
        receipt_a = ".lifeline/receipts/proof-reference-accepted/fitness/F10/sha256-a.json"
        receipt_b = ".lifeline/receipts/proof-reference-accepted/playbook/A02/sha256-b.json"
        _write_json(
            audit_path,
            _base_audit_index(
                receipt_count=2,
                valid_receipt_count=2,
                receipts_by_source_repo_id={
                    "fitness": [receipt_a],
                    "playbook": [receipt_b],
                },
                receipts_by_tranche_id={
                    "A02": [receipt_b],
                    "F10": [receipt_a],
                },
                proof_reference_count_total=4,
            ),
        )

        summary = summarize_lifeline_audit_index(audit_path, root=root)

        self.assertEqual({"fitness": (receipt_a,), "playbook": (receipt_b,)}, summary.receipts_by_source_repo_id)
        self.assertEqual({"A02": (receipt_b,), "F10": (receipt_a,)}, summary.receipts_by_tranche_id)

    def test_surfaces_invalid_receipts(self) -> None:
        root = self._temp_root()
        audit_path = root / "tmp" / "lifeline-index.json"
        invalid_path = ".lifeline/receipts/proof-reference-accepted/fitness/F11/sha256-invalid.json"
        _write_json(
            audit_path,
            _base_audit_index(
                receipt_count=1,
                invalid_receipt_count=1,
                receipts_by_source_repo_id={"fitness": [invalid_path]},
                receipts_by_tranche_id={"F11": [invalid_path]},
                invalid_receipts=[_invalid_receipt(receipt_path=invalid_path)],
            ),
        )

        summary = summarize_lifeline_audit_index(audit_path, root=root)

        self.assertTrue(summary.connector_publication_blocked)
        self.assertEqual(1, summary.invalid_receipt_count)
        self.assertEqual(invalid_path, summary.invalid_receipts[0].receipt_path)
        self.assertEqual(
            "invalid_receipts_present",
            summary.connector_publication_blockers[0].code,
        )

    def test_surfaces_current_validation_debt_as_a_blocker(self) -> None:
        root = self._temp_root()
        audit_path = root / "tmp" / "lifeline-index.json"
        debt_path = ".lifeline/receipts/proof-reference-accepted/fitness/F09/sha256-debt.json"
        _write_json(
            audit_path,
            _base_audit_index(
                receipt_count=1,
                valid_receipt_count=1,
                receipts_by_source_repo_id={"fitness": [debt_path]},
                receipts_by_tranche_id={"F09": [debt_path]},
                proof_reference_count_total=2,
                receipts_with_current_validation_debt=[debt_path],
            ),
        )

        summary = summarize_lifeline_audit_index(audit_path, root=root)

        blocker_codes = [item.code for item in summary.connector_publication_blockers]
        self.assertIn("current_validation_debt_present", blocker_codes)
        self.assertTrue(summary.connector_publication_blocked)

    def test_surfaces_auto_approved_violations_as_blockers(self) -> None:
        root = self._temp_root()
        audit_path = root / "tmp" / "lifeline-index.json"
        receipt_path = ".lifeline/receipts/proof-reference-accepted/fitness/F10/sha256-auto.json"
        _write_json(
            audit_path,
            _base_audit_index(
                receipt_count=1,
                valid_receipt_count=1,
                receipts_by_source_repo_id={"fitness": [receipt_path]},
                receipts_by_tranche_id={"F10": [receipt_path]},
                proof_reference_count_total=2,
                receipts_with_auto_approved_not_false=[receipt_path],
            ),
        )

        summary = summarize_lifeline_audit_index(audit_path, root=root)

        blocker_codes = [item.code for item in summary.connector_publication_blockers]
        self.assertIn("auto_approved_violation", blocker_codes)
        self.assertTrue(summary.connector_publication_blocked)

    def test_surfaces_missing_boundary_statement_violations_as_blockers(self) -> None:
        root = self._temp_root()
        audit_path = root / "tmp" / "lifeline-index.json"
        receipt_path = ".lifeline/receipts/proof-reference-accepted/playbook/A02/sha256-boundary.json"
        _write_json(
            audit_path,
            _base_audit_index(
                receipt_count=1,
                valid_receipt_count=1,
                receipts_by_source_repo_id={"playbook": [receipt_path]},
                receipts_by_tranche_id={"A02": [receipt_path]},
                proof_reference_count_total=2,
                receipts_missing_boundary_statement=[receipt_path],
            ),
        )

        summary = summarize_lifeline_audit_index(audit_path, root=root)

        blocker_codes = [item.code for item in summary.connector_publication_blockers]
        self.assertIn("missing_boundary_statement", blocker_codes)
        self.assertTrue(summary.connector_publication_blocked)

    def test_fails_clearly_on_missing_audit_index_path(self) -> None:
        root = self._temp_root()
        audit_path = root / "tmp" / "missing-index.json"

        with self.assertRaisesRegex(FileNotFoundError, "Lifeline audit index not found at"):
            summarize_lifeline_audit_index(audit_path, root=root)

    def test_fails_clearly_on_malformed_audit_index_json(self) -> None:
        root = self._temp_root()
        audit_path = root / "tmp" / "lifeline-index.json"
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text("{not json}\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "Malformed Lifeline audit index JSON at"):
            summarize_lifeline_audit_index(audit_path, root=root)

    def test_output_is_json_serializable(self) -> None:
        root = self._temp_root()
        audit_path = root / "tmp" / "lifeline-index.json"
        receipt_path = ".lifeline/receipts/proof-reference-accepted/fitness/F11/sha256-one.json"
        _write_json(
            audit_path,
            _base_audit_index(
                receipt_count=1,
                valid_receipt_count=1,
                receipts_by_source_repo_id={"fitness": [receipt_path]},
                receipts_by_tranche_id={"F11": [receipt_path]},
                proof_reference_count_total=2,
            ),
        )

        summary = summarize_lifeline_audit_index(audit_path, root=root)

        json.dumps(summary.to_payload(), sort_keys=True)

    def test_read_only_summary_does_not_require_writes_or_external_connectors(self) -> None:
        root = self._temp_root()
        audit_path = root / "tmp" / "lifeline-index.json"
        receipt_path = ".lifeline/receipts/proof-reference-accepted/fitness/F11/sha256-one.json"
        _write_json(
            audit_path,
            _base_audit_index(
                receipt_count=1,
                valid_receipt_count=1,
                receipts_by_source_repo_id={"fitness": [receipt_path]},
                receipts_by_tranche_id={"F11": [receipt_path]},
                proof_reference_count_total=2,
            ),
        )
        before_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())

        summary = summarize_lifeline_audit_index(audit_path, root=root)

        after_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        self.assertEqual(before_files, after_files)
        self.assertTrue(summary.cortex_read_only)
        self.assertEqual([], summary.to_payload()["connector_publication_blockers"])


if __name__ == "__main__":
    unittest.main()
