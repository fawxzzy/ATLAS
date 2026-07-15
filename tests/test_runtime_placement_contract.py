from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from ops.validation import runtime_placement_contract as contract


ROOT = Path(__file__).resolve().parents[1]


def _payloads() -> tuple[dict[str, object], dict[str, object], str]:
    registry = json.loads((ROOT / contract.REGISTRY_REF).read_text(encoding="utf-8-sig"))
    lane_registry = json.loads((ROOT / contract.LANE_REGISTRY_REF).read_text(encoding="utf-8-sig"))
    marker_book = (ROOT / contract.MARKER_BOOK_REF).read_text(encoding="utf-8-sig")
    return registry, lane_registry, marker_book


def _schema() -> dict[str, object]:
    return json.loads((ROOT / contract.SCHEMA_REF).read_text(encoding="utf-8-sig"))


class RuntimePlacementContractTests(unittest.TestCase):
    def test_canonical_contract_is_valid(self) -> None:
        self.assertEqual([], contract.validate_contract_files(root=ROOT))

    def test_percentage_must_remain_unset(self) -> None:
        registry, lane_registry, marker_book = _payloads()
        mutated = copy.deepcopy(registry)
        mutated["marker_lanes"][0]["percentage"] = 0
        issues = contract.validate_runtime_placement_payloads(mutated, lane_registry, marker_book, root=ROOT)
        self.assertIn("runtime-placement-marker-unset", {issue.category for issue in issues})

    def test_fixed_denominator_must_match_units(self) -> None:
        registry, lane_registry, marker_book = _payloads()
        mutated = copy.deepcopy(registry)
        mutated["marker_lanes"][1]["units"].pop()
        issues = contract.validate_runtime_placement_payloads(mutated, lane_registry, marker_book, root=ROOT)
        self.assertIn("runtime-placement-marker-units", {issue.category for issue in issues})

    def test_forbidden_component_cannot_receive_public_hosting(self) -> None:
        registry, lane_registry, marker_book = _payloads()
        mutated = copy.deepcopy(registry)
        atlas = next(component for component in mutated["components"] if component["id"] == "atlas-root")
        atlas["intended_placement"] = "Vercel"
        issues = contract.validate_runtime_placement_payloads(mutated, lane_registry, marker_book, root=ROOT)
        self.assertIn("runtime-placement-public-hosting-forbidden", {issue.category for issue in issues})

    def test_activation_sequence_is_exact(self) -> None:
        registry, lane_registry, marker_book = _payloads()
        mutated = copy.deepcopy(registry)
        mutated["activation_sequence"][0], mutated["activation_sequence"][1] = (
            mutated["activation_sequence"][1],
            mutated["activation_sequence"][0],
        )
        issues = contract.validate_runtime_placement_payloads(mutated, lane_registry, marker_book, root=ROOT)
        self.assertIn("runtime-placement-activation-sequence", {issue.category for issue in issues})

    def test_schema_only_required_governance_violation_is_rejected(self) -> None:
        registry, lane_registry, marker_book = _payloads()
        mutated = copy.deepcopy(registry)
        mutated.pop("governance")

        self.assertEqual(
            [],
            contract.validate_runtime_placement_payloads(mutated, lane_registry, marker_book, root=ROOT),
        )
        with patch.object(contract, "_read_json", side_effect=[mutated, _schema(), lane_registry]):
            issues = contract.validate_contract_files(root=ROOT)

        self.assertIn("runtime-placement-registry-schema-invalid", {issue.category for issue in issues})

    def test_invalid_schema_definition_is_rejected(self) -> None:
        registry, _lane_registry, _marker_book = _payloads()
        mutated_schema = copy.deepcopy(_schema())
        mutated_schema["$defs"] = []

        issues = contract.validate_registry_schema_contract(registry, mutated_schema)

        self.assertIn("runtime-placement-schema-invalid", {issue.category for issue in issues})

    def test_schema_date_time_format_violation_is_rejected(self) -> None:
        registry, _lane_registry, _marker_book = _payloads()
        mutated = copy.deepcopy(registry)
        mutated["generated_at"] = "not-a-date-time"

        issues = contract.validate_registry_schema_contract(mutated, _schema())

        self.assertIn("runtime-placement-registry-schema-invalid", {issue.category for issue in issues})

    def test_unavailable_shared_schema_validator_fails_closed(self) -> None:
        registry, _lane_registry, _marker_book = _payloads()
        with (
            patch.object(contract, "_validate_json_schema", None),
            patch.object(contract, "_validate_schema_definition", None),
            patch.object(contract, "_SCHEMA_VALIDATION_IMPORT_ERROR", "simulated import failure"),
        ):
            issues = contract.validate_registry_schema_contract(registry, _schema())

        self.assertIn("runtime-placement-jsonschema-unavailable", {issue.category for issue in issues})


if __name__ == "__main__":
    unittest.main()
