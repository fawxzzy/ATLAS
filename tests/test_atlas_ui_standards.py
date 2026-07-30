from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.ui_standards.validate import (
    CANDIDATE_CARDS_REF,
    REGISTRY_REF,
    load_json_object,
    validate_ascii_policy,
    validate_audit_finding,
    validate_candidate_cards,
    validate_finding_remediation_link,
    validate_foundation,
    validate_json_schema,
    validate_registry,
    validate_remediation_card,
)


def valid_finding() -> dict[str, object]:
    return {
        "contract_version": "atlas.ui.audit-finding.v1",
        "finding_id": "uif_fitness.login.focus",
        "standard_id": "ATLAS-UI-A11Y-001",
        "standard_version": "1.0.0",
        "owner_repo_id": "fitness",
        "audit_id": "uia_fitness.baseline.v1",
        "scope": {
            "routes": ["/login"],
            "surface_ids": ["auth-login"],
            "component_refs": ["src/Login"],
            "affected_lenses": ["iphone.webkit"],
        },
        "severity": "high",
        "state": "open",
        "detected_at": "2026-07-15T12:00:00Z",
        "detection": {
            "kind": "hybrid",
            "rule_ref": "ATLAS-UI-A11Y-001@1.0.0",
            "summary": "The focus order does not follow the visible order.",
        },
        "evidence": {
            "bundle_refs": ["runtime/evidence/fitness-login-focus.json"],
            "qa_result_refs": [],
            "runtime_refs": [],
            "accessibility_checks": [
                {
                    "check_kind": "keyboard",
                    "status": "failed",
                    "refs": ["runtime/evidence/fitness-login-focus.json"],
                }
            ],
        },
        "disposition": {
            "status": "unreviewed",
            "owner": None,
            "rationale": None,
            "expires_at": None,
        },
        "remediation_card_ids": ["uir_fitness.login.focus"],
    }


def valid_completed_remediation() -> dict[str, object]:
    return {
        "contract_version": "atlas.ui.remediation-card.v1",
        "remediation_id": "uir_fitness.login.focus",
        "finding_ids": ["uif_fitness.login.focus"],
        "program_lifecycle": "completed",
        "atlas_card": {
            "contract_version": "atlas.card-record.v2",
            "card_id": "ui-remediation-fitness-login-focus",
            "project_id": "fitness",
            "board_id": "fitness-board",
            "title": "Repair login focus order",
            "description": "Align keyboard focus with the visible login order.",
            "card_type": "bug",
            "lifecycle": "completed",
            "priority": "high",
            "owner": "fitness",
            "dependencies": [],
            "board_version": 4,
            "updated_at": "2026-07-15T13:00:00Z",
            "source_ref": "runtime/ui-findings/uif_fitness.login.focus.json",
            "extensions": {},
        },
        "evidence_requirements": [
            "routes",
            "devices",
            "accessibility",
            "visual",
            "runtime",
            "change_checklist",
        ],
        "requested_change_checklist": [
            {
                "item_id": "login.focus-order",
                "statement": "Focus follows the visible login order.",
                "status": "passed",
                "evidence_refs": ["runtime/evidence/fitness-login-focus-fixed.json"],
            }
        ],
        "verification": {
            "status": "verified",
            "evidence_bundle_refs": ["runtime/evidence/fitness-login-focus-fixed.json"],
            "qa_promotion_refs": [],
            "verified_at": "2026-07-15T13:00:00Z",
        },
    }


class AtlasUiStandardsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_json_object(ROOT / REGISTRY_REF)
        cls.candidates = load_json_object(ROOT / CANDIDATE_CARDS_REF)

    def test_canonical_foundation_is_valid(self) -> None:
        result = validate_foundation(root=ROOT)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertTrue(result["safe_to_adopt_root_foundation"])

    def test_duplicate_standard_id_is_rejected(self) -> None:
        registry = copy.deepcopy(self.registry)
        registry["standards"].append(copy.deepcopy(registry["standards"][0]))
        errors = validate_registry(registry, root=ROOT)
        self.assertTrue(any("duplicate standard_id" in error for error in errors), errors)

    def test_subjective_metric_shape_is_rejected(self) -> None:
        registry = copy.deepcopy(self.registry)
        registry["metrics"][0]["weights"] = {"visual": 0.5, "runtime": 0.5}
        errors = validate_registry(registry, root=ROOT)
        self.assertTrue(errors)

    def test_candidate_cards_are_non_mutating_and_unplanned(self) -> None:
        self.assertFalse(validate_candidate_cards(self.candidates, registry=self.registry, root=ROOT))
        mutated = copy.deepcopy(self.candidates)
        mutated["mutation_authorized"] = True
        mutated["packets"][0]["program_lifecycle"] = "ready"
        errors = validate_candidate_cards(mutated, registry=self.registry, root=ROOT)
        self.assertTrue(any("mutation_authorized=false" in error for error in errors), errors)
        self.assertTrue(any("must be unplanned" in error for error in errors), errors)

    def test_audit_finding_and_completed_remediation_link(self) -> None:
        finding = valid_finding()
        remediation = valid_completed_remediation()
        self.assertFalse(validate_audit_finding(finding, registry=self.registry, root=ROOT))
        self.assertFalse(validate_remediation_card(remediation, registry=self.registry, root=ROOT))
        self.assertFalse(validate_finding_remediation_link(finding, remediation))

    def test_lifecycle_mapping_mismatch_is_rejected(self) -> None:
        remediation = valid_completed_remediation()
        remediation["atlas_card"]["lifecycle"] = "review"
        errors = validate_remediation_card(remediation, registry=self.registry, root=ROOT)
        self.assertTrue(any("must map" in error for error in errors), errors)

    def test_completed_remediation_requires_proof_and_checklist_evidence(self) -> None:
        remediation = valid_completed_remediation()
        remediation["verification"]["evidence_bundle_refs"] = []
        remediation["requested_change_checklist"][0]["evidence_refs"] = []
        errors = validate_remediation_card(remediation, registry=self.registry, root=ROOT)
        self.assertTrue(any("requires evidence or QA promotion" in error for error in errors), errors)
        self.assertTrue(any("checklist item requires evidence" in error for error in errors), errors)

    def test_ascii_policy_rejects_non_ascii_normative_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "normative.md").write_text("bad \u2014 text\n", encoding="utf-8")
            registry = {
                "encoding_policy": {
                    "enforced_refs": ["normative.md"],
                    "evidence_exceptions": [],
                },
                "provenance": [],
            }
            errors = validate_ascii_policy(registry, root=root)
        self.assertTrue(any("ASCII policy" in error for error in errors), errors)

    def test_fallback_const_and_enum_use_json_typed_equality(self) -> None:
        cases = [
            ("const boolean exact", False, {"const": False}, True),
            ("const boolean integer mismatch", 0, {"const": False}, False),
            ("const boolean float mismatch", 1.0, {"const": True}, False),
            ("const integer float match", 1.0, {"const": 1}, True),
            ("const null exact", None, {"const": None}, True),
            ("const string number mismatch", "1", {"const": 1}, False),
            (
                "const nested match",
                [1, {"enabled": False, "weight": 2.0}],
                {"const": [1.0, {"weight": 2, "enabled": False}]},
                True,
            ),
            (
                "const nested boolean number mismatch",
                {"items": [{"enabled": 0}]},
                {"const": {"items": [{"enabled": False}]}},
                False,
            ),
            ("enum boolean integer mismatch", 0, {"enum": [False]}, False),
            ("enum boolean float mismatch", 1.0, {"enum": [True]}, False),
            ("enum integer float match", 1.0, {"enum": [1]}, True),
            ("enum null exact", None, {"enum": [None]}, True),
            ("enum string exact", "ready", {"enum": ["held", "ready"]}, True),
            ("enum array numeric match", [1.0, 2], {"enum": [[1, 2.0]]}, True),
            (
                "enum nested boolean number mismatch",
                {"enabled": 0},
                {"enum": [{"enabled": False}]},
                False,
            ),
        ]
        with (
            mock.patch("ops.atlas.ui_standards.validate.Draft202012Validator", None),
            mock.patch("ops.atlas.ui_standards.validate.FormatChecker", None),
        ):
            for name, value, schema, should_accept in cases:
                with self.subTest(name=name):
                    errors = validate_json_schema(value, schema)
                    self.assertEqual(not errors, should_accept, errors)

    def test_cli_returns_success_and_machine_readable_result(self) -> None:
        completed = subprocess.run(
            [sys.executable, "ops/atlas/ui_standards/validate.py", "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "valid")


if __name__ == "__main__":
    unittest.main()
