from __future__ import annotations

import copy
import json
import shutil
import tempfile
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


def _write_source_only_contract_root(root: Path) -> None:
    registry, lane_registry, marker_book = _payloads()
    required_payloads = {
        contract.REGISTRY_REF: json.dumps(registry, indent=2) + "\n",
        contract.SCHEMA_REF: json.dumps(_schema(), indent=2) + "\n",
        contract.LANE_REGISTRY_REF: json.dumps(lane_registry, indent=2) + "\n",
        contract.MARKER_BOOK_REF: marker_book,
    }
    for relative_path, content in required_payloads.items():
        destination = root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    evidence_owners = [*registry["components"], *registry["activation_steps"]]
    evidence_owners.extend(unit for marker in registry["marker_lanes"] for unit in marker["units"])
    for owner in evidence_owners:
        for evidence_ref in owner["evidence_refs"]:
            if (
                "://" in evidence_ref
                or evidence_ref.startswith("git:")
                or evidence_ref.startswith("repos/")
                or evidence_ref.startswith("runtime/")
            ):
                continue
            relative_path = Path(evidence_ref.split("#", 1)[0].split("@", 1)[0])
            source = ROOT / relative_path
            destination = root / relative_path
            if source.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)


class RuntimePlacementContractTests(unittest.TestCase):
    def test_canonical_contract_is_valid(self) -> None:
        self.assertEqual([], contract.validate_contract_files(root=ROOT))

    def test_percentage_must_match_accepted_fixed_denominator_units(self) -> None:
        registry, lane_registry, marker_book = _payloads()
        mutated = copy.deepcopy(registry)
        mutated["marker_lanes"][0]["percentage"] = 0
        issues = contract.validate_runtime_placement_payloads(mutated, lane_registry, marker_book, root=ROOT)
        self.assertIn("runtime-placement-marker-calculation", {issue.category for issue in issues})

    def test_unknown_unit_cannot_remain_counted_as_accepted(self) -> None:
        registry, lane_registry, marker_book = _payloads()
        mutated = copy.deepcopy(registry)
        mutated["marker_lanes"][0]["units"][0]["status"] = "unknown"
        issues = contract.validate_runtime_placement_payloads(mutated, lane_registry, marker_book, root=ROOT)
        self.assertIn("runtime-placement-marker-calculation", {issue.category for issue in issues})

    def test_marker_unit_relative_evidence_must_be_retrievable(self) -> None:
        registry, lane_registry, marker_book = _payloads()
        mutated = copy.deepcopy(registry)
        mutated["marker_lanes"][0]["units"][0]["evidence_refs"] = ["definitely/missing-marker-evidence.json"]

        issues = contract.validate_runtime_placement_payloads(mutated, lane_registry, marker_book, root=ROOT)

        self.assertIn("runtime-placement-evidence-missing", {issue.category for issue in issues})

    def test_blocked_marker_unit_remains_distinct_and_unaccepted(self) -> None:
        registry, lane_registry, marker_book = _payloads()
        mutated = copy.deepcopy(registry)
        mutated["marker_lanes"][0]["units"][0]["status"] = "blocked"
        semantic_issues = contract.validate_runtime_placement_payloads(mutated, lane_registry, marker_book, root=ROOT)
        self.assertNotIn("runtime-placement-marker-unit-status", {issue.category for issue in semantic_issues})
        self.assertIn("runtime-placement-marker-calculation", {issue.category for issue in semantic_issues})
        self.assertEqual([], contract.validate_registry_schema_contract(mutated, _schema()))

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

    def test_v1_activation_sequence_remains_an_ordered_string_id_array(self) -> None:
        registry, _lane_registry, _marker_book = _payloads()

        self.assertEqual(list(contract.ACTIVATION_SEQUENCE), registry["activation_sequence"])
        self.assertTrue(all(isinstance(step_id, str) for step_id in registry["activation_sequence"]))
        self.assertEqual([], contract.validate_registry_schema_contract(registry, _schema()))

    def test_structured_activation_steps_map_one_to_one_to_v1_sequence(self) -> None:
        registry, lane_registry, marker_book = _payloads()
        mutations = {
            "missing": lambda steps: steps.pop(),
            "duplicate": lambda steps: steps.__setitem__(1, copy.deepcopy(steps[0])),
            "reordered": lambda steps: steps.__setitem__(slice(0, 2), [steps[1], steps[0]]),
        }

        for name, mutate in mutations.items():
            with self.subTest(name=name):
                mutated = copy.deepcopy(registry)
                mutate(mutated["activation_steps"])
                issues = contract.validate_runtime_placement_payloads(mutated, lane_registry, marker_book, root=ROOT)
                self.assertIn("runtime-placement-activation-steps", {issue.category for issue in issues})

    def test_selector_must_name_the_first_unexecuted_packet(self) -> None:
        registry, lane_registry, marker_book = _payloads()
        mutated = copy.deepcopy(registry)
        mutated["next_owner_side_activation_packet"] = "Playbook bootstrap and foreground Observer health proof"
        issues = contract.validate_runtime_placement_payloads(mutated, lane_registry, marker_book, root=ROOT)
        self.assertIn("runtime-placement-selector", {issue.category for issue in issues})

    def test_activation_packet_names_must_be_unique(self) -> None:
        registry, lane_registry, marker_book = _payloads()
        mutated = copy.deepcopy(registry)
        current_index = next(
            index for index, step in enumerate(mutated["activation_steps"]) if step["status"] != "accepted"
        )
        duplicate_packet = mutated["activation_steps"][0]["packet"]
        mutated["activation_steps"][current_index]["packet"] = duplicate_packet
        mutated["next_owner_side_activation_packet"] = duplicate_packet

        issues = contract.validate_runtime_placement_payloads(mutated, lane_registry, marker_book, root=ROOT)

        self.assertIn("runtime-placement-activation-step-packet-duplicate", {issue.category for issue in issues})

    def test_activation_step_relative_evidence_must_be_retrievable(self) -> None:
        registry, lane_registry, marker_book = _payloads()
        mutated = copy.deepcopy(registry)
        mutated["activation_steps"][0]["evidence_refs"] = ["definitely/missing-activation-evidence.json"]

        issues = contract.validate_runtime_placement_payloads(mutated, lane_registry, marker_book, root=ROOT)

        self.assertIn("runtime-placement-evidence-missing", {issue.category for issue in issues})

    def test_selector_advances_when_current_step_becomes_accepted(self) -> None:
        registry, lane_registry, marker_book = _payloads()
        mutated = copy.deepcopy(registry)
        selected_index = next(
            index
            for index, step in enumerate(mutated["activation_steps"])
            if step["packet"] == mutated["next_owner_side_activation_packet"]
        )
        mutated["activation_steps"][selected_index]["status"] = "accepted"
        mutated["next_owner_side_activation_packet"] = mutated["activation_steps"][selected_index + 1]["packet"]

        issues = contract.validate_runtime_placement_payloads(mutated, lane_registry, marker_book, root=ROOT)

        self.assertEqual([], issues)

    def test_resource_observations_cannot_grant_mutation_authority(self) -> None:
        registry, lane_registry, marker_book = _payloads()
        mutated = copy.deepcopy(registry)
        mutated["advisory_resource_observations"][0]["action"] = "cleanup"
        issues = contract.validate_runtime_placement_payloads(mutated, lane_registry, marker_book, root=ROOT)
        self.assertIn("runtime-placement-resource-observation-authority", {issue.category for issue in issues})

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

    def test_source_only_root_without_owner_repos_or_runtime_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_only_root = Path(temp_dir)
            _write_source_only_contract_root(source_only_root)

            issues = contract.validate_contract_files(root=source_only_root)

        self.assertEqual([], issues)

    def test_present_owner_repo_with_missing_evidence_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_only_root = Path(temp_dir)
            _write_source_only_contract_root(source_only_root)
            (source_only_root / "repos" / "foundation").mkdir(parents=True)

            issues = contract.validate_contract_files(root=source_only_root)

        missing_refs = {
            issue.details.get("evidence_ref")
            for issue in issues
            if issue.category == "runtime-placement-evidence-missing" and issue.details
        }
        self.assertIn("repos/foundation/vercel.json", missing_refs)

    def test_present_runtime_surface_does_not_require_ignored_generated_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_only_root = Path(temp_dir)
            _write_source_only_contract_root(source_only_root)
            (source_only_root / "runtime" / "cortex").mkdir(parents=True)

            issues = contract.validate_contract_files(root=source_only_root)

        self.assertEqual([], issues)

    def test_missing_committed_root_owned_evidence_ref_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_only_root = Path(temp_dir)
            _write_source_only_contract_root(source_only_root)
            (source_only_root / "AGENTS.md").unlink()

            issues = contract.validate_contract_files(root=source_only_root)

        missing_refs = {
            issue.details.get("evidence_ref")
            for issue in issues
            if issue.category == "runtime-placement-evidence-missing" and issue.details
        }
        self.assertIn("AGENTS.md", missing_refs)


if __name__ == "__main__":
    unittest.main()
