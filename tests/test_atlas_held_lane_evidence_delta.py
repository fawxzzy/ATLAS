from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.atlas import held_lane_evidence_delta as resolver


CONTRACT_REF = "docs/registry/case.json"
HELD_REF = "docs/ops/held.md"
EVIDENCE_REF = "ops/atlas/proof.py"


def _write(path: Path, value: str | dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2) + "\n" if isinstance(value, dict) else value
    path.write_text(text, encoding="utf-8", newline="\n")


def _contract(*, evidence_ref: str = EVIDENCE_REF) -> dict[str, object]:
    return {
        "contract_version": resolver.CONTRACT_VERSION,
        "case_id": "test-held-lane",
        "marker": "Test Marker",
        "blocker_class": "implementation",
        "held_checkpoint": {
            "class": "held_checkpoint",
            "ref": HELD_REF,
            "assertions": [
                {"id": "held", "type": "literal", "value": "held evidence"},
                {
                    "id": "held-hash",
                    "type": "sha256",
                    "equals": resolver._sha256(b"held evidence\n"),
                },
            ],
        },
        "required_evidence_classes": ["implementation"],
        "evidence": [{
            "class": "implementation",
            "ref": evidence_ref,
            "assertions": [{"id": "implemented", "type": "literal", "value": "implemented = True"}],
        }],
        "authority": {
            "marker_movement": False,
            "selector_mutation": False,
            "dispatch": False,
            "owner_repo_mutation": False,
            "deploy": False,
            "discord": False,
            "secret_access": False,
            "final_receipt": False,
        },
        "expected_decision": "reopen_eligible",
    }


class HeldLaneEvidenceDeltaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        _write(self.root / HELD_REF, "held evidence\n")
        _write(self.root / EVIDENCE_REF, "implemented = True\n")
        _write(self.root / CONTRACT_REF, _contract())

    def test_matching_source_bound_case_is_reopen_eligible(self) -> None:
        receipt = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        self.assertEqual("reopen_eligible", receipt["decision"])
        self.assertEqual(["implementation"], receipt["passed_evidence_classes"])
        self.assertEqual([], receipt["authority_actions"])
        self.assertTrue(receipt["advisory_only"])
        self.assertTrue(receipt["expectation_met"])
        self.assertNotIn("marker_movement", receipt)
        self.assertNotIn("final_receipt", receipt)

    def test_receipt_identity_is_deterministic(self) -> None:
        first = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        second = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        self.assertEqual(first, second)
        self.assertRegex(first["receipt_id"], r"^ahd_[0-9a-f]{24}$")

    def test_digest_drift_changes_receipt_identity(self) -> None:
        first = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        _write(self.root / EVIDENCE_REF, "# drift\nimplemented = True\n")
        second = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        self.assertNotEqual(first["receipt_id"], second["receipt_id"])

    def test_assertion_mismatch_stays_held(self) -> None:
        _write(self.root / EVIDENCE_REF, "implemented = False\n")
        receipt = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        self.assertEqual("still_held", receipt["decision"])
        self.assertEqual(["implementation"], receipt["missing_evidence_classes"])

    def test_missing_source_is_blocked(self) -> None:
        (self.root / EVIDENCE_REF).unlink()
        receipt = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        self.assertEqual("blocked", receipt["decision"])
        self.assertIn("missing_source", receipt["blockers"][0])

    def test_evidence_cannot_alias_the_held_checkpoint(self) -> None:
        contract = _contract(evidence_ref=HELD_REF)
        contract["evidence"][0]["assertions"] = [
            {"id": "same-source", "type": "literal", "value": "held evidence"}
        ]
        _write(self.root / CONTRACT_REF, contract)

        receipt = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)

        self.assertEqual("blocked", receipt["decision"])
        self.assertIn("evidence_not_delta", receipt["blockers"][0])

    def test_held_checkpoint_requires_exact_sha256_binding(self) -> None:
        contract = _contract()
        contract["held_checkpoint"]["assertions"] = [
            {"id": "held", "type": "literal", "value": "held evidence"}
        ]
        _write(self.root / CONTRACT_REF, contract)

        receipt = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)

        self.assertEqual("blocked", receipt["decision"])
        self.assertIn("held_checkpoint_sha256_required", receipt["blockers"][0])

    def test_whitespace_subject_is_blocked(self) -> None:
        contract = _contract()
        contract["marker"] = "   "
        _write(self.root / CONTRACT_REF, contract)

        receipt = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)

        self.assertEqual("blocked", receipt["decision"])
        self.assertIn("missing_contract_field:marker", receipt["blockers"][0])

    def test_json_value_assertion(self) -> None:
        json_ref = "data/state.json"
        _write(self.root / json_ref, {"state": {"percent": 100}})
        contract = _contract(evidence_ref=json_ref)
        contract["evidence"][0]["assertions"] = [{
            "id": "percent", "type": "json_value", "path": ["state", "percent"], "equals": 100
        }]
        _write(self.root / CONTRACT_REF, contract)
        receipt = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        self.assertEqual("reopen_eligible", receipt["decision"])

    def test_json_path_mismatch_stays_held(self) -> None:
        json_ref = "data/state.json"
        _write(self.root / json_ref, {"state": {"percent": 99}})
        contract = _contract(evidence_ref=json_ref)
        contract["evidence"][0]["assertions"] = [{
            "id": "percent", "type": "json_value", "path": ["state", "percent"], "equals": 100
        }]
        _write(self.root / CONTRACT_REF, contract)
        receipt = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        self.assertEqual("still_held", receipt["decision"])

    def test_owner_repo_source_is_rejected(self) -> None:
        _write(self.root / CONTRACT_REF, _contract(evidence_ref="repos/owner/proof.md"))
        receipt = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        self.assertEqual("blocked", receipt["decision"])
        self.assertIn("protected_source_ref", receipt["blockers"][0])

    def test_secret_source_is_rejected(self) -> None:
        _write(self.root / CONTRACT_REF, _contract(evidence_ref="secrets/value.txt"))
        receipt = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        self.assertEqual("blocked", receipt["decision"])

    def test_env_source_is_rejected(self) -> None:
        _write(self.root / CONTRACT_REF, _contract(evidence_ref="data/.env.production"))
        receipt = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        self.assertEqual("blocked", receipt["decision"])

    def test_deploy_and_workflow_sources_are_rejected(self) -> None:
        for ref in (
            "docs/ops/deploy-proof.md",
            "ops/atlas/release_workflow.py",
            "ops/deployments/proof.txt",
            "docs/workflows/proof.txt",
        ):
            with self.subTest(ref=ref):
                _write(self.root / CONTRACT_REF, _contract(evidence_ref=ref))
                receipt = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
                self.assertEqual("blocked", receipt["decision"])
                self.assertIn("mutation_surface_ref", receipt["blockers"][0])

    def test_sha256_assertion_binds_exact_source_bytes(self) -> None:
        raw = (self.root / EVIDENCE_REF).read_bytes()
        contract = _contract()
        contract["evidence"][0]["assertions"] = [{
            "id": "source-hash", "type": "sha256", "equals": resolver._sha256(raw)
        }]
        _write(self.root / CONTRACT_REF, contract)
        first = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        self.assertEqual("reopen_eligible", first["decision"])
        _write(self.root / EVIDENCE_REF, "implemented = True\n# changed\n")
        second = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        self.assertEqual("still_held", second["decision"])
        self.assertFalse(second["expectation_met"])

    def test_invalid_expected_decision_is_blocked(self) -> None:
        contract = _contract()
        contract["expected_decision"] = "approve_everything"
        _write(self.root / CONTRACT_REF, contract)
        receipt = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        self.assertEqual("blocked", receipt["decision"])
        self.assertIn("invalid_expected_decision", receipt["blockers"])

    def test_authority_drift_is_blocked(self) -> None:
        contract = _contract()
        contract["authority"]["marker_movement"] = True
        _write(self.root / CONTRACT_REF, contract)
        receipt = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        self.assertEqual("blocked", receipt["decision"])
        self.assertIn("authority_guard_drift", receipt["blockers"])

    def test_output_must_be_tmp_atlas_json(self) -> None:
        receipt = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        with self.assertRaisesRegex(resolver.HeldLaneEvidenceDeltaError, "output_not_tmp_atlas_json"):
            resolver.write_output(root=self.root, output_ref="docs/result.json", receipt=receipt)

    def test_valid_output_is_written(self) -> None:
        receipt = resolver.evaluate_contract(root=self.root, contract_ref=CONTRACT_REF)
        resolver.write_output(root=self.root, output_ref="tmp/atlas/evidence/result.json", receipt=receipt)
        written = json.loads((self.root / "tmp/atlas/evidence/result.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt, written)


if __name__ == "__main__":
    unittest.main()
