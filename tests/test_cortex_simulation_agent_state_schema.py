from __future__ import annotations

import copy
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "atlas.cortex.simulation.agent-state.v1.json"
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
DIGEST_C = "sha256:" + "c" * 64
DIGEST_D = "sha256:" + "d" * 64


def valid_payload() -> dict[str, object]:
    return {
        "contract_version": "atlas.cortex.simulation.agent-state.v1",
        "state_id": DIGEST_A,
        "scenario_id": "scenario-fixture-1",
        "agent_id": "agent-fixture-1",
        "generated_at": "2026-07-14T04:20:00-04:00",
        "source_refs": ["docs/ops/example-receipt.md"],
        "memories": [
            {
                "memory_id": DIGEST_B,
                "observed_at": "2026-07-14T04:10:00-04:00",
                "content_summary": "A proof-backed lane observation.",
                "source_refs": ["docs/ops/example-receipt.md"],
                "source_digest": DIGEST_C,
                "importance": 0.8,
                "confidence": 0.9,
                "retention_class": "project",
                "rights_class": "operator_owned",
                "privacy_class": "internal",
                "injection_state": "trusted",
                "supersedes": [],
            }
        ],
        "retrieval_context": {
            "query_summary": "Select evidence for a bounded plan.",
            "candidate_memory_ids": [DIGEST_B],
            "selected_memory_ids": [DIGEST_B],
            "scoring": {
                "recency_weight": 0.3,
                "importance_weight": 0.3,
                "relevance_weight": 0.4,
            },
            "minimum_confidence": 0.7,
            "deterministic_tiebreaker": "score_desc_then_memory_id_asc",
            "excluded": [],
        },
        "reflections": [
            {
                "reflection_id": DIGEST_C,
                "generated_at": "2026-07-14T04:15:00-04:00",
                "trigger": "replay_checkpoint",
                "source_memory_ids": [DIGEST_B],
                "summary": "The evidence supports an advisory next step.",
                "confidence": 0.85,
                "source_refs": ["docs/ops/example-receipt.md"],
                "derived_not_observed": True,
                "approval_state": "advisory_only",
                "retention_class": "project",
            }
        ],
        "active_plan": {
            "plan_id": DIGEST_D,
            "objective": "Describe a safe read-only next step.",
            "status": "candidate",
            "source_memory_ids": [DIGEST_B],
            "source_reflection_ids": [DIGEST_C],
            "steps": [
                {
                    "step_id": "step-1",
                    "objective": "Inspect admitted evidence.",
                    "state": "ready",
                    "proposed_action": "Read root-owned receipts.",
                    "evidence_required": ["receipt digest"],
                    "authority_check": "advisory_only",
                }
            ],
            "success_criteria": ["advisory output cites admitted proof"],
            "termination_reason": None,
            "confidence": 0.8,
            "execution_authorized": False,
        },
        "authority": {
            "advisory_only": True,
            "execution_authorized": False,
            "owner_repo_mutation_authorized": False,
            "platform_mutation_authorized": False,
            "discord_write_authorized": False,
            "marker_movement_authorized": False,
        },
    }


def validate_contract(instance: object, schema: dict[str, object], root_schema: dict[str, object]) -> None:
    if "$ref" in schema:
        ref = str(schema["$ref"])
        if not ref.startswith("#/$defs/"):
            raise AssertionError(f"unsupported ref: {ref}")
        validate_contract(instance, root_schema["$defs"][ref.removeprefix("#/$defs/")], root_schema)  # type: ignore[index]
        return

    if "oneOf" in schema:
        matches = 0
        for candidate in schema["oneOf"]:  # type: ignore[assignment]
            try:
                validate_contract(instance, candidate, root_schema)
                matches += 1
            except AssertionError:
                pass
        if matches != 1:
            raise AssertionError(f"oneOf expected exactly one match, got {matches}")
        return

    expected_type = schema.get("type")
    expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
    type_matches = {
        "object": lambda value: isinstance(value, dict),
        "array": lambda value: isinstance(value, list),
        "string": lambda value: isinstance(value, str),
        "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": lambda value: isinstance(value, bool),
        "null": lambda value: value is None,
    }
    if expected_type is not None and not any(type_matches[item](instance) for item in expected_types):
        raise AssertionError(f"type mismatch: expected {expected_types}, got {type(instance).__name__}")
    if "const" in schema and instance != schema["const"]:
        raise AssertionError(f"const mismatch: {instance!r}")
    if "enum" in schema and instance not in schema["enum"]:  # type: ignore[operator]
        raise AssertionError(f"enum mismatch: {instance!r}")

    if isinstance(instance, str):
        if len(instance) < int(schema.get("minLength", 0)):
            raise AssertionError("string shorter than minLength")
        if "pattern" in schema and re.fullmatch(str(schema["pattern"]), instance) is None:
            raise AssertionError(f"pattern mismatch: {instance!r}")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:  # type: ignore[operator]
            raise AssertionError("number below minimum")
        if "maximum" in schema and instance > schema["maximum"]:  # type: ignore[operator]
            raise AssertionError("number above maximum")
    if isinstance(instance, list):
        if len(instance) < int(schema.get("minItems", 0)):
            raise AssertionError("array shorter than minItems")
        if schema.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in instance}) != len(instance):
            raise AssertionError("array items are not unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for item in instance:
                validate_contract(item, item_schema, root_schema)
    if isinstance(instance, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in instance]  # type: ignore[union-attr]
        if missing:
            raise AssertionError(f"missing required keys: {missing}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(instance) - set(properties))  # type: ignore[arg-type]
            if unknown:
                raise AssertionError(f"unknown properties: {unknown}")
        for key, value in instance.items():
            if key in properties:  # type: ignore[operator]
                validate_contract(value, properties[key], root_schema)  # type: ignore[index]


class CortexSimulationAgentStateSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        if cls.schema["$schema"] != "https://json-schema.org/draft/2020-12/schema":
            raise AssertionError("unexpected JSON Schema draft")
        if cls.schema["$id"] != "atlas://schemas/atlas.cortex.simulation.agent-state.v1.json":
            raise AssertionError("unexpected schema identifier")

    def test_valid_advisory_state_passes(self) -> None:
        validate_contract(valid_payload(), self.schema, self.schema)

    def test_execution_authority_is_rejected(self) -> None:
        payload = valid_payload()
        payload["authority"]["execution_authorized"] = True  # type: ignore[index]
        with self.assertRaises(AssertionError):
            validate_contract(payload, self.schema, self.schema)

    def test_plan_execution_authority_is_rejected(self) -> None:
        payload = valid_payload()
        payload["active_plan"]["execution_authorized"] = True  # type: ignore[index]
        with self.assertRaises(AssertionError):
            validate_contract(payload, self.schema, self.schema)

    def test_unknown_or_raw_memory_fields_are_rejected(self) -> None:
        payload = valid_payload()
        payload["memories"][0]["raw_content"] = "not admitted"  # type: ignore[index]
        with self.assertRaises(AssertionError):
            validate_contract(payload, self.schema, self.schema)

    def test_reflection_must_remain_derived_and_advisory(self) -> None:
        payload = copy.deepcopy(valid_payload())
        payload["reflections"][0]["derived_not_observed"] = False  # type: ignore[index]
        with self.assertRaises(AssertionError):
            validate_contract(payload, self.schema, self.schema)


if __name__ == "__main__":
    unittest.main()
