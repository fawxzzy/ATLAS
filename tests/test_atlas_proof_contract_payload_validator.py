from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import proof_contract_candidate_contract as contract
from ops.atlas import proof_contract_payload_validator as validator


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_sources(root: Path) -> list[str]:
    _write(
        root / "docs" / "ops" / "contract.md",
        "Reusable workflow proof-contract with workflow_call typed inputs, workflow_dispatch manual proof inputs, artifact-backed proof, receipt-backed proof, least privilege.",
    )
    _write(root / "docs" / "PLAYBOOK_NOTES.md", "Rule: proof artifact and fallback path are explicit.")
    _write(root / "docs" / "architecture" / "ATLAS-CORTEX-PLAYBOOK-CODEX.md", "Cortex consumes explicit artifact refs without dispatch authority.")
    _write(root / "docs" / "standards" / "WORKER-ORCHESTRATION.md", "Workers resume from handoff artifacts.")
    return [
        "docs/ops/contract.md",
        "docs/PLAYBOOK_NOTES.md",
        "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md",
        "docs/standards/WORKER-ORCHESTRATION.md",
    ]


class ProofContractPayloadValidatorTests(unittest.TestCase):
    def test_live_artifact_contract_validates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sources = _seed_sources(root)
            report = validator.build_report(root=root, candidate_id="artifact-backed-proof-contract", source_refs=sources)

        self.assertEqual(validator.STATUS_VALID, report["status"])
        self.assertTrue(report["safe_to_use"])
        self.assertEqual(contract.SCHEMA_VERSION, report["contract_schema"])
        self.assertFalse(report["blockers"])
        self.assertNotIn("marker", report)
        self.assertNotIn("marker_movement", report)

    def test_live_manual_contract_accepts_secret_names_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sources = _seed_sources(root)
            report = validator.build_report(root=root, candidate_id="manual-protected-proof-contract", source_refs=sources)

        self.assertEqual(validator.STATUS_VALID, report["status"])
        self.assertTrue(report["secret_boundary"]["valid"])
        self.assertEqual([], report["secret_boundary"]["forbidden_secret_value_keys"])

    def test_missing_contract_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = validator.validate_report(
                root=Path(temp_dir),
                report={"schema_version": contract.SCHEMA_VERSION, "status": contract.STATUS_OK, "candidate_id": "artifact-backed-proof-contract"},
            )

        self.assertEqual(validator.STATUS_BLOCKER, report["status"])
        self.assertFalse(report["safe_to_use"])
        self.assertIn("missing_contract", [blocker["code"] for blocker in report["blockers"]])

    def test_missing_authority_denial_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sources = _seed_sources(root)
            payload = contract.build_report(root=root, candidate_id="artifact-backed-proof-contract", source_refs=sources)
            payload["contract"]["authority_denials"].remove("no_workflow_dispatch")
            report = validator.validate_report(root=root, report=payload)

        self.assertEqual(validator.STATUS_BLOCKER, report["status"])
        self.assertIn("missing_authority_denial", [blocker["code"] for blocker in report["blockers"]])

    def test_secret_value_field_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sources = _seed_sources(root)
            payload = contract.build_report(root=root, candidate_id="manual-protected-proof-contract", source_refs=sources)
            payload["contract"]["secret_values"] = {"BROWSERSTACK_ACCESS_KEY": "example"}
            report = validator.validate_report(root=root, report=payload)

        self.assertEqual(validator.STATUS_BLOCKER, report["status"])
        self.assertIn("secret_values", report["secret_boundary"]["forbidden_secret_value_keys"])

    def test_input_must_be_tmp_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "docs" / "ops" / "payload.json", "{}")
            report = validator.build_report(root=root, candidate_id="artifact-backed-proof-contract", input_path="docs/ops/payload.json")

        self.assertEqual(validator.STATUS_BLOCKER, report["status"])
        self.assertIn("protected_input_path", [blocker["code"] for blocker in report["blockers"]])

    def test_main_validates_tmp_input_and_writes_tmp_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sources = _seed_sources(root)
            payload = contract.build_report(root=root, candidate_id="artifact-backed-proof-contract", source_refs=sources)
            _write(root / "tmp" / "contract.json", json.dumps(payload, indent=2) + "\n")
            output_path = root / "tmp" / "validation.json"
            with mock.patch.object(validator, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = validator.main(["--json", "--input", "tmp/contract.json", "--output", "tmp/validation.json"])
            written = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(0, code)
        self.assertEqual(validator.SCHEMA_VERSION, written["schema_version"])
        self.assertEqual(validator.STATUS_VALID, written["status"])

    def test_main_rejects_protected_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sources = _seed_sources(root)
            payload = contract.build_report(root=root, candidate_id="artifact-backed-proof-contract", source_refs=sources)
            _write(root / "tmp" / "contract.json", json.dumps(payload, indent=2) + "\n")
            with mock.patch.object(validator, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = validator.main(["--json", "--input", "tmp/contract.json", "--output", "docs/ops/validation.json"])

        self.assertEqual(2, code)

    def test_deterministic_top_level_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sources = _seed_sources(root)
            report = validator.build_report(root=root, candidate_id="artifact-backed-proof-contract", source_refs=sources)

        self.assertEqual(
            [
                "schema_version",
                "status",
                "candidate_id",
                "contract_schema",
                "contract_status",
                "required_field_results",
                "authority_denial_results",
                "secret_boundary",
                "proof_reference_results",
                "source_ref_results",
                "safe_to_use",
                "root",
                "branch",
                "head",
                "input_ref",
                "source_refs",
                "blockers",
                "warnings",
            ],
            list(report.keys()),
        )


if __name__ == "__main__":
    unittest.main()
