from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterable

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ModuleNotFoundError:  # Keep root validation runnable without an optional package.
    Draft202012Validator = None  # type: ignore[assignment,misc]
    FormatChecker = None  # type: ignore[assignment,misc]

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, load_repo_registry

REGISTRY_CONTRACT_VERSION = "atlas.ui.standard-registry.v1"
AUDIT_FINDING_CONTRACT_VERSION = "atlas.ui.audit-finding.v1"
REMEDIATION_CARD_CONTRACT_VERSION = "atlas.ui.remediation-card.v1"
CARD_RECORD_CONTRACT_VERSION = "atlas.card-record.v2"

REGISTRY_REF = "docs/registry/ATLAS-UI-STANDARDS-REGISTRY.v1.json"
CANDIDATE_CARDS_REF = "docs/registry/ATLAS-UI-STANDARDS-CANDIDATE-CARDS.v1.json"
REGISTRY_SCHEMA_REF = "schemas/atlas.ui.standard-registry.v1.json"
AUDIT_FINDING_SCHEMA_REF = "schemas/atlas.ui.audit-finding.v1.json"
REMEDIATION_CARD_SCHEMA_REF = "schemas/atlas.ui.remediation-card.v1.json"
CARD_RECORD_SCHEMA_REF = "packages/atlas-contracts/schemas/atlas.card-record.v2.schema.json"

SCHEMA_IDENTITIES = {
    REGISTRY_SCHEMA_REF: (
        "atlas://schemas/atlas.ui.standard-registry.v1.json",
        "ATLAS UI standard registry v1",
    ),
    AUDIT_FINDING_SCHEMA_REF: (
        "atlas://schemas/atlas.ui.audit-finding.v1.json",
        "ATLAS UI audit finding v1",
    ),
    REMEDIATION_CARD_SCHEMA_REF: (
        "atlas://schemas/atlas.ui.remediation-card.v1.json",
        "ATLAS UI remediation card v1",
    ),
}

PROGRAM_STATES = [
    "unplanned",
    "planned",
    "ready",
    "in_progress",
    "review",
    "completed",
    "blocked",
]
LIFECYCLE_MAPPING = {
    "unplanned": "intake",
    "planned": "planning",
    "ready": "ready",
    "in_progress": "in-progress",
    "review": "review",
    "completed": "completed",
    "blocked": "blocked",
}
EVIDENCE_DIMENSIONS = {
    "routes",
    "devices",
    "accessibility",
    "visual",
    "runtime",
    "change_checklist",
}
ENFORCEMENT_TIERS = {"local", "ci", "release"}
FORBIDDEN_METRIC_KEYS = {
    "weight",
    "weights",
    "penalty",
    "penalties",
    "score",
    "percent_complete",
}
MOJIBAKE_FRAGMENTS = (
    "\u00c2",
    "\u00c3",
    "\u00e2\u20ac",
    "\u00ee\u02c6",
)


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}.")
    return payload


def _json_path(parts: Iterable[Any]) -> str:
    rendered = "$"
    for part in parts:
        if isinstance(part, int):
            rendered += f"[{part}]"
        else:
            rendered += f".{part}"
    return rendered


def _resolve_local_ref(root_schema: dict[str, Any], ref: str) -> Any:
    if not ref.startswith("#/"):
        raise ValueError(f"Unsupported schema ref: {ref}")
    current: Any = root_schema
    for raw_segment in ref[2:].split("/"):
        segment = raw_segment.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or segment not in current:
            raise ValueError(f"Unresolvable schema ref: {ref}")
        current = current[segment]
    return current


def _matches_schema_type(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return False


def _json_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if isinstance(left, (int, float)) or isinstance(right, (int, float)):
        return (
            isinstance(left, (int, float))
            and isinstance(right, (int, float))
            and left == right
        )
    if left is None or right is None:
        return left is None and right is None
    if isinstance(left, str) or isinstance(right, str):
        return isinstance(left, str) and isinstance(right, str) and left == right
    if isinstance(left, list) or isinstance(right, list):
        return (
            isinstance(left, list)
            and isinstance(right, list)
            and len(left) == len(right)
            and all(
                _json_equal(left_item, right_item)
                for left_item, right_item in zip(left, right)
            )
        )
    if isinstance(left, dict) or isinstance(right, dict):
        return (
            isinstance(left, dict)
            and isinstance(right, dict)
            and left.keys() == right.keys()
            and all(_json_equal(left[key], right[key]) for key in left)
        )
    return False


def _valid_iso_datetime(value: str) -> bool:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _validate_schema_subset(
    value: Any,
    schema: dict[str, Any],
    *,
    root_schema: dict[str, Any],
    at: str = "$",
) -> list[str]:
    if "$ref" in schema:
        try:
            target = _resolve_local_ref(root_schema, str(schema["$ref"]))
        except ValueError as exc:
            return [f"{at}: {exc}"]
        if not isinstance(target, dict):
            return [f"{at}: schema ref must resolve to an object"]
        return _validate_schema_subset(value, target, root_schema=root_schema, at=at)

    errors: list[str] = []
    if "const" in schema and not _json_equal(value, schema["const"]):
        errors.append(f"{at}: must equal {schema['const']!r}")
    if "enum" in schema and not any(_json_equal(value, item) for item in schema["enum"]):
        errors.append(f"{at}: must be one of {schema['enum']!r}")

    raw_types = schema.get("type")
    if raw_types is not None:
        allowed_types = raw_types if isinstance(raw_types, list) else [raw_types]
        if not all(isinstance(item, str) for item in allowed_types):
            return [f"{at}: schema type declaration is invalid"]
        if not any(_matches_schema_type(value, item) for item in allowed_types):
            return [f"{at}: must be of type {' | '.join(allowed_types)}"]

    if isinstance(value, str):
        if isinstance(schema.get("minLength"), int) and len(value) < schema["minLength"]:
            errors.append(f"{at}: must have length >= {schema['minLength']}")
        if isinstance(schema.get("maxLength"), int) and len(value) > schema["maxLength"]:
            errors.append(f"{at}: must have length <= {schema['maxLength']}")
        if isinstance(schema.get("pattern"), str) and re.search(schema["pattern"], value) is None:
            errors.append(f"{at}: must match pattern {schema['pattern']}")
        if schema.get("format") == "date-time" and not _valid_iso_datetime(value):
            errors.append(f"{at}: must be an ISO 8601 UTC timestamp")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(schema.get("minimum"), (int, float)) and value < schema["minimum"]:
            errors.append(f"{at}: must be >= {schema['minimum']}")
        if isinstance(schema.get("maximum"), (int, float)) and value > schema["maximum"]:
            errors.append(f"{at}: must be <= {schema['maximum']}")

    if isinstance(value, list):
        if isinstance(schema.get("minItems"), int) and len(value) < schema["minItems"]:
            errors.append(f"{at}: must contain at least {schema['minItems']} items")
        if isinstance(schema.get("maxItems"), int) and len(value) > schema["maxItems"]:
            errors.append(f"{at}: must contain at most {schema['maxItems']} items")
        if schema.get("uniqueItems") is True:
            serialized = [json.dumps(item, sort_keys=True) for item in value]
            if len(serialized) != len(set(serialized)):
                errors.append(f"{at}: items must be unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(
                    _validate_schema_subset(item, item_schema, root_schema=root_schema, at=f"{at}[{index}]")
                )

    if isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in value:
                    errors.append(f"{at}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, child_schema in properties.items():
                if key in value and isinstance(child_schema, dict):
                    errors.extend(
                        _validate_schema_subset(
                            value[key], child_schema, root_schema=root_schema, at=f"{at}.{key}"
                        )
                    )
            if schema.get("additionalProperties") is False:
                for key in sorted(set(value) - set(properties)):
                    errors.append(f"{at}: unsupported property {key!r}")
    return errors


def validate_json_schema(payload: Any, schema: dict[str, Any]) -> list[str]:
    if Draft202012Validator is not None and FormatChecker is not None:
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            return [f"Schema definition is invalid: {exc}"]
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        return [
            f"{_json_path(error.absolute_path)}: {error.message}"
            for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path))
        ]
    return _validate_schema_subset(payload, schema, root_schema=schema)


def validate_schema_definition(schema: dict[str, Any], *, expected_id: str, expected_title: str) -> list[str]:
    errors: list[str] = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("Schema $schema must target draft 2020-12.")
    if schema.get("$id") != expected_id:
        errors.append(f"Schema $id must be {expected_id!r}.")
    if schema.get("title") != expected_title:
        errors.append(f"Schema title must be {expected_title!r}.")
    if Draft202012Validator is not None:
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            errors.append(f"jsonschema rejected the schema definition: {exc}")
    else:
        if schema.get("type") != "object" or not isinstance(schema.get("properties"), dict):
            errors.append("Schema must define an object with properties.")
        if not isinstance(schema.get("$defs"), dict):
            errors.append("Schema must define reusable $defs.")
    return errors


def _duplicates(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _is_portable_ref(value: str) -> bool:
    base = value.split("#", 1)[0]
    if not base:
        return False
    if re.match(r"^[a-z][a-z0-9+.-]*:", base):
        return base.startswith(("https://", "http://", "git:", "github:", "codex-thread:"))
    if PureWindowsPath(base).is_absolute() or PurePosixPath(base).is_absolute():
        return False
    return all(part not in {"", ".", ".."} for part in PurePosixPath(base.replace("\\", "/")).parts)


def _looks_like_local_ref(value: str) -> bool:
    base = value.split("#", 1)[0]
    if re.match(r"^[a-z][a-z0-9+.-]*:", base):
        return False
    return "/" in base or base.endswith((".md", ".json", ".py", ".yaml", ".yml")) or base == "AGENTS.md"


def _validate_ref(value: Any, *, root: Path, context: str, require_exists: bool = True) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        return [f"{context} must be a non-empty reference."]
    if not _is_portable_ref(value):
        return [f"{context} must be an ATLAS-relative portable ref or an admitted external URI: {value!r}"]
    if require_exists and _looks_like_local_ref(value):
        base = value.split("#", 1)[0]
        if not (root / base).exists():
            return [f"{context} does not exist: {base}"]
    return []


def _walk_keys(value: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield child_path, str(key)
            yield from _walk_keys(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_keys(child, f"{path}[{index}]")


def _validate_unique(records: Any, field: str, context: str) -> list[str]:
    if not isinstance(records, list):
        return []
    values = [str(item.get(field)) for item in records if isinstance(item, dict) and isinstance(item.get(field), str)]
    duplicates = _duplicates(values)
    return [f"{context} contains duplicate {field}: {item}" for item in duplicates]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_ascii_policy(registry: dict[str, Any], *, root: Path) -> list[str]:
    errors: list[str] = []
    policy = registry.get("encoding_policy")
    if not isinstance(policy, dict):
        return ["encoding_policy must be an object."]

    enforced_refs = policy.get("enforced_refs")
    if not isinstance(enforced_refs, list):
        return ["encoding_policy.enforced_refs must be an array."]
    for index, ref in enumerate(enforced_refs):
        errors.extend(_validate_ref(ref, root=root, context=f"encoding_policy.enforced_refs[{index}]"))
        if not isinstance(ref, str):
            continue
        path = root / ref
        if not path.exists() or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"{ref} is not valid UTF-8: {exc}")
            continue
        non_ascii = sorted({f"U+{ord(char):04X}" for char in text if ord(char) > 127})
        if non_ascii:
            errors.append(f"{ref} violates the normative ASCII policy: {', '.join(non_ascii[:12])}")
        for fragment in MOJIBAKE_FRAGMENTS:
            if fragment in text:
                escaped = fragment.encode("unicode_escape").decode("ascii")
                errors.append(f"{ref} contains forbidden mojibake fragment {escaped}.")

    exception_refs: set[str] = set()
    exceptions = policy.get("evidence_exceptions")
    if not isinstance(exceptions, list):
        return [*errors, "encoding_policy.evidence_exceptions must be an array."]
    for index, item in enumerate(exceptions):
        if not isinstance(item, dict):
            errors.append(f"encoding_policy.evidence_exceptions[{index}] must be an object.")
            continue
        ref = item.get("ref")
        digest = item.get("sha256")
        errors.extend(_validate_ref(ref, root=root, context=f"encoding_policy.evidence_exceptions[{index}].ref"))
        if not isinstance(ref, str):
            continue
        exception_refs.add(ref)
        if ref in enforced_refs:
            errors.append(f"{ref} cannot be both ASCII-enforced and an evidence exception.")
        path = root / ref
        if path.exists() and isinstance(digest, str) and _sha256(path) != digest:
            errors.append(f"Evidence exception digest mismatch for {ref}.")

    provenance = registry.get("provenance")
    if isinstance(provenance, list):
        for item in provenance:
            if not isinstance(item, dict) or item.get("classification") != "external-input":
                continue
            ref = item.get("ref")
            if isinstance(ref, str) and ref not in exception_refs:
                errors.append(f"External input {ref} must be a digest-bound encoding exception.")
    return errors


def validate_registry(payload: dict[str, Any], *, root: Path | None = None) -> list[str]:
    base_root = (root or atlas_root()).resolve()
    schema = load_json_object(base_root / REGISTRY_SCHEMA_REF)
    errors = validate_json_schema(payload, schema)
    if errors:
        return errors

    for collection, field in (
        ("provenance", "source_id"),
        ("source_hierarchy", "source_id"),
        ("evidence_dimensions", "dimension_id"),
        ("enforcement_tiers", "tier_id"),
        ("standards", "standard_id"),
        ("adoption_profiles", "profile_id"),
        ("metrics", "metric_id"),
        ("migration_waves", "wave_id"),
        ("collision_rules", "rule_id"),
    ):
        errors.extend(_validate_unique(payload.get(collection), field, collection))

    hierarchy = payload.get("source_hierarchy", [])
    ranks = [item.get("rank") for item in hierarchy if isinstance(item, dict)]
    if ranks != list(range(1, len(ranks) + 1)):
        errors.append("source_hierarchy ranks must be unique, ordered, and contiguous from 1.")

    lifecycle = payload.get("lifecycle", {})
    if lifecycle.get("program_states") != PROGRAM_STATES:
        errors.append(f"lifecycle.program_states must equal {PROGRAM_STATES!r}.")
    if lifecycle.get("wire_mapping") != LIFECYCLE_MAPPING:
        errors.append("lifecycle.wire_mapping must preserve the exact atlas.card-record.v2 mapping.")
    transitions = lifecycle.get("allowed_transitions", [])
    transition_sources = [item.get("from") for item in transitions if isinstance(item, dict)]
    if transition_sources != PROGRAM_STATES:
        errors.append("lifecycle.allowed_transitions must define every program state once in canonical order.")
    for item in transitions:
        if not isinstance(item, dict):
            continue
        invalid = sorted(set(item.get("to", [])) - set(PROGRAM_STATES))
        if invalid:
            errors.append(f"Lifecycle transition {item.get('from')} references invalid states: {invalid}")

    dimensions = payload.get("evidence_dimensions", [])
    dimension_ids = {
        item.get("dimension_id") for item in dimensions if isinstance(item, dict) and isinstance(item.get("dimension_id"), str)
    }
    if dimension_ids != EVIDENCE_DIMENSIONS:
        errors.append(f"evidence_dimensions must cover exactly {sorted(EVIDENCE_DIMENSIONS)!r}.")

    tiers = payload.get("enforcement_tiers", [])
    tier_ids = {item.get("tier_id") for item in tiers if isinstance(item, dict)}
    if tier_ids != ENFORCEMENT_TIERS:
        errors.append(f"enforcement_tiers must cover exactly {sorted(ENFORCEMENT_TIERS)!r}.")
    for index, tier in enumerate(tiers):
        if not isinstance(tier, dict):
            continue
        invalid = sorted(set(tier.get("required_dimensions", [])) - dimension_ids)
        if invalid:
            errors.append(f"enforcement_tiers[{index}] references invalid dimensions: {invalid}")

    standards = payload.get("standards", [])
    standard_ids = {
        item.get("standard_id") for item in standards if isinstance(item, dict) and isinstance(item.get("standard_id"), str)
    }
    for index, standard in enumerate(standards):
        if not isinstance(standard, dict):
            continue
        invalid_dimensions = sorted(set(standard.get("evidence_dimensions", [])) - dimension_ids)
        invalid_tiers = sorted(set(standard.get("enforcement_tiers", [])) - tier_ids)
        invalid_successors = sorted(set(standard.get("successor_ids", [])) - standard_ids)
        if invalid_dimensions:
            errors.append(f"standards[{index}] references invalid evidence dimensions: {invalid_dimensions}")
        if invalid_tiers:
            errors.append(f"standards[{index}] references invalid enforcement tiers: {invalid_tiers}")
        if invalid_successors:
            errors.append(f"standards[{index}] references unknown successors: {invalid_successors}")
        if standard.get("status") == "accepted" and not standard.get("enforcement_tiers"):
            errors.append(f"standards[{index}] accepted standards must declare enforcement tiers.")
        for ref_index, ref in enumerate(standard.get("source_refs", [])):
            errors.extend(
                _validate_ref(ref, root=base_root, context=f"standards[{index}].source_refs[{ref_index}]")
            )

    profiles = payload.get("adoption_profiles", [])
    profile_ids = {
        item.get("profile_id") for item in profiles if isinstance(item, dict) and isinstance(item.get("profile_id"), str)
    }
    for index, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            continue
        invalid_standards = sorted(set(profile.get("required_standard_ids", [])) - standard_ids)
        invalid_dimensions = sorted(set(profile.get("required_evidence_dimensions", [])) - dimension_ids)
        extends = profile.get("extends")
        if invalid_standards:
            errors.append(f"adoption_profiles[{index}] references unknown standards: {invalid_standards}")
        if invalid_dimensions:
            errors.append(f"adoption_profiles[{index}] references invalid dimensions: {invalid_dimensions}")
        if isinstance(extends, str) and extends not in profile_ids:
            errors.append(f"adoption_profiles[{index}].extends references unknown profile {extends!r}.")
        if extends == profile.get("profile_id"):
            errors.append(f"adoption_profiles[{index}] must not extend itself.")

    migration_waves = payload.get("migration_waves", [])
    wave_ids = {
        item.get("wave_id") for item in migration_waves if isinstance(item, dict) and isinstance(item.get("wave_id"), str)
    }
    sequences = [item.get("sequence") for item in migration_waves if isinstance(item, dict)]
    if sequences != list(range(len(sequences))):
        errors.append("migration_waves sequences must be unique, ordered, and contiguous from 0.")
    for index, wave in enumerate(migration_waves):
        if not isinstance(wave, dict):
            continue
        invalid = sorted(set(wave.get("depends_on", [])) - wave_ids)
        if invalid:
            errors.append(f"migration_waves[{index}] references unknown dependencies: {invalid}")

    for path, key in _walk_keys(payload):
        if key.lower() in FORBIDDEN_METRIC_KEYS:
            errors.append(f"{path} uses forbidden subjective metric key {key!r}.")

    for collection in ("provenance", "source_hierarchy"):
        for index, item in enumerate(payload.get(collection, [])):
            if isinstance(item, dict):
                errors.extend(_validate_ref(item.get("ref"), root=base_root, context=f"{collection}[{index}].ref"))

    errors.extend(validate_ascii_policy(payload, root=base_root))
    return errors


def validate_candidate_cards(
    payload: dict[str, Any],
    *,
    registry: dict[str, Any],
    root: Path | None = None,
) -> list[str]:
    base_root = (root or atlas_root()).resolve()
    errors: list[str] = []
    expected_keys = {
        "registry_version",
        "generated_at",
        "source_registry_ref",
        "mutation_authorized",
        "packets",
    }
    if set(payload) != expected_keys:
        errors.append(f"Candidate card registry keys must equal {sorted(expected_keys)!r}.")
    if payload.get("registry_version") != "atlas.ui-standards.candidate-cards.v1":
        errors.append("Candidate card registry version is invalid.")
    if payload.get("source_registry_ref") != REGISTRY_REF:
        errors.append(f"source_registry_ref must be {REGISTRY_REF!r}.")
    if payload.get("mutation_authorized") is not False:
        errors.append("Candidate card registry must keep mutation_authorized=false.")

    packets = payload.get("packets")
    if not isinstance(packets, list) or not packets:
        return [*errors, "Candidate card registry must contain packets."]
    errors.extend(_validate_unique(packets, "packet_id", "packets"))
    card_ids = [
        str(packet.get("card", {}).get("card_id"))
        for packet in packets
        if isinstance(packet, dict) and isinstance(packet.get("card"), dict)
    ]
    for duplicate in _duplicates(card_ids):
        errors.append(f"packets contain duplicate card_id: {duplicate}")

    card_schema = load_json_object(base_root / CARD_RECORD_SCHEMA_REF)
    repo_registry = load_repo_registry(root=base_root)
    profile_ids = {
        item.get("profile_id")
        for item in registry.get("adoption_profiles", [])
        if isinstance(item, dict) and isinstance(item.get("profile_id"), str)
    }

    required_packet_keys = {
        "packet_id",
        "packet_kind",
        "target_repo_id",
        "target_repo_path",
        "profile_candidate",
        "program_lifecycle",
        "card",
        "objective",
        "acceptance_criteria",
        "scope",
        "verification",
        "dependencies",
        "marker",
    }
    for index, packet in enumerate(packets):
        at = f"packets[{index}]"
        if not isinstance(packet, dict):
            errors.append(f"{at} must be an object.")
            continue
        if set(packet) != required_packet_keys:
            errors.append(f"{at} keys must equal {sorted(required_packet_keys)!r}.")
        if packet.get("program_lifecycle") != "unplanned":
            errors.append(f"{at}.program_lifecycle must be unplanned.")
        target_repo_id = packet.get("target_repo_id")
        entry = repo_registry.get(str(target_repo_id))
        if entry is None:
            errors.append(f"{at}.target_repo_id is not registered in stack.yaml: {target_repo_id!r}")
        elif packet.get("target_repo_path") != entry.atlas_path:
            errors.append(f"{at}.target_repo_path must equal stack.yaml path {entry.atlas_path!r}.")
        profile_candidate = packet.get("profile_candidate")
        if isinstance(profile_candidate, str) and profile_candidate not in profile_ids:
            errors.append(f"{at}.profile_candidate references unknown profile {profile_candidate!r}.")
        if not isinstance(packet.get("objective"), str) or not packet["objective"].strip():
            errors.append(f"{at}.objective must be non-empty.")
        if not isinstance(packet.get("acceptance_criteria"), list) or not packet["acceptance_criteria"]:
            errors.append(f"{at}.acceptance_criteria must be non-empty.")
        if not isinstance(packet.get("verification"), list) or not packet["verification"]:
            errors.append(f"{at}.verification must be non-empty.")

        marker = packet.get("marker")
        if not isinstance(marker, dict) or set(marker) != {"status", "percentage", "denominator"}:
            errors.append(f"{at}.marker must contain status, percentage, and denominator only.")
        elif marker != {"status": "unmeasured", "percentage": None, "denominator": None}:
            errors.append(f"{at}.marker must remain unmeasured with null percentage and denominator.")

        card = packet.get("card")
        if not isinstance(card, dict):
            errors.append(f"{at}.card must be an atlas.card-record.v2 object.")
            continue
        for error in validate_json_schema(card, card_schema):
            errors.append(f"{at}.card {error}")
        if card.get("lifecycle") != "intake":
            errors.append(f"{at}.card.lifecycle must map unplanned to intake.")
        if card.get("project_id") != target_repo_id:
            errors.append(f"{at}.card.project_id must equal target_repo_id.")
        if card.get("board_id") != "candidate:atlas-ui-standards":
            errors.append(f"{at}.card.board_id must identify the non-live candidate registry.")
        source_ref = card.get("source_ref")
        expected_prefix = f"{CANDIDATE_CARDS_REF}#"
        if not isinstance(source_ref, str) or not source_ref.startswith(expected_prefix):
            errors.append(f"{at}.card.source_ref must start with {expected_prefix!r}.")
        extensions = card.get("extensions")
        if not isinstance(extensions, dict):
            errors.append(f"{at}.card.extensions must be an object.")
            continue
        if extensions.get("ui_standards_program_lifecycle") != "unplanned":
            errors.append(f"{at}.card.extensions must preserve unplanned lifecycle.")
        if extensions.get("projection_authorized") is not False:
            errors.append(f"{at}.card.extensions.projection_authorized must be false.")
        if extensions.get("percentage") is not None or extensions.get("denominator_status") != "unaccepted":
            errors.append(f"{at}.card extensions must keep percentage null and denominator unaccepted.")
    return errors


def validate_audit_finding(
    payload: dict[str, Any],
    *,
    registry: dict[str, Any],
    root: Path | None = None,
) -> list[str]:
    base_root = (root or atlas_root()).resolve()
    schema = load_json_object(base_root / AUDIT_FINDING_SCHEMA_REF)
    errors = validate_json_schema(payload, schema)
    if errors:
        return errors

    standards = {
        item["standard_id"]: item
        for item in registry.get("standards", [])
        if isinstance(item, dict) and isinstance(item.get("standard_id"), str)
    }
    standard = standards.get(payload.get("standard_id"))
    if standard is None:
        errors.append(f"standard_id is not present in the active registry: {payload.get('standard_id')!r}")
    elif payload.get("standard_version") != standard.get("version"):
        errors.append("standard_version must equal the active registry version for standard_id.")

    evidence = payload.get("evidence", {})
    evidence_refs = [
        *evidence.get("bundle_refs", []),
        *evidence.get("qa_result_refs", []),
        *evidence.get("runtime_refs", []),
    ]
    if payload.get("state") == "verified" and not evidence_refs:
        errors.append("A verified finding must retain at least one evidence reference.")
    disposition = payload.get("disposition", {})
    if payload.get("state") == "waived":
        if disposition.get("status") != "accept-risk" or not disposition.get("expires_at"):
            errors.append("A waived finding requires accept-risk disposition and expires_at.")
    if payload.get("state") == "superseded" and disposition.get("status") != "superseded":
        errors.append("A superseded finding requires superseded disposition.")

    for index, ref in enumerate(evidence_refs):
        errors.extend(_validate_ref(ref, root=base_root, context=f"evidence ref[{index}]", require_exists=False))
    return errors


def validate_remediation_card(
    payload: dict[str, Any],
    *,
    registry: dict[str, Any],
    root: Path | None = None,
) -> list[str]:
    base_root = (root or atlas_root()).resolve()
    schema = load_json_object(base_root / REMEDIATION_CARD_SCHEMA_REF)
    errors = validate_json_schema(payload, schema)
    if errors:
        return errors

    card = payload.get("atlas_card", {})
    card_schema = load_json_object(base_root / CARD_RECORD_SCHEMA_REF)
    for error in validate_json_schema(card, card_schema):
        errors.append(f"atlas_card {error}")

    lifecycle = payload.get("program_lifecycle")
    expected_wire = LIFECYCLE_MAPPING.get(str(lifecycle))
    if card.get("lifecycle") != expected_wire:
        errors.append(
            f"program_lifecycle {lifecycle!r} must map to atlas_card.lifecycle {expected_wire!r}."
        )
    if card.get("contract_version") != CARD_RECORD_CONTRACT_VERSION:
        errors.append(f"atlas_card.contract_version must be {CARD_RECORD_CONTRACT_VERSION!r}.")

    evidence_requirements = payload.get("evidence_requirements", [])
    if _duplicates(str(item) for item in evidence_requirements):
        errors.append("evidence_requirements must not contain duplicates.")
    invalid_dimensions = sorted(set(evidence_requirements) - EVIDENCE_DIMENSIONS)
    if invalid_dimensions:
        errors.append(f"evidence_requirements contains invalid dimensions: {invalid_dimensions}")
    finding_ids = payload.get("finding_ids", [])
    if _duplicates(str(item) for item in finding_ids):
        errors.append("finding_ids must not contain duplicates.")

    checklist = payload.get("requested_change_checklist", [])
    errors.extend(_validate_unique(checklist, "item_id", "requested_change_checklist"))
    verification = payload.get("verification", {})
    if lifecycle == "completed":
        if verification.get("status") != "verified":
            errors.append("A completed remediation requires verification.status=verified.")
        if not verification.get("verified_at"):
            errors.append("A completed remediation requires verification.verified_at.")
        if not verification.get("evidence_bundle_refs") and not verification.get("qa_promotion_refs"):
            errors.append("A completed remediation requires evidence or QA promotion refs.")
        if not checklist or any(item.get("status") != "passed" for item in checklist if isinstance(item, dict)):
            errors.append("A completed remediation requires a non-empty all-passed checklist.")
        if any(not item.get("evidence_refs") for item in checklist if isinstance(item, dict)):
            errors.append("Every completed remediation checklist item requires evidence refs.")
    elif verification.get("status") == "verified":
        errors.append("verification.status=verified is reserved for completed remediation lifecycle.")
    return errors


def validate_finding_remediation_link(
    finding: dict[str, Any],
    remediation: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    finding_id = finding.get("finding_id")
    remediation_id = remediation.get("remediation_id")
    if finding_id not in remediation.get("finding_ids", []):
        errors.append("Remediation finding_ids must include the supplied finding_id.")
    linked_cards = finding.get("remediation_card_ids", [])
    if remediation_id not in linked_cards:
        errors.append("Finding remediation_card_ids must include the supplied remediation_id.")
    return errors


def validate_foundation(
    *,
    root: Path | None = None,
    registry_path: Path | None = None,
    candidate_path: Path | None = None,
    finding_path: Path | None = None,
    remediation_path: Path | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    registry_target = (registry_path or (base_root / REGISTRY_REF)).resolve()
    candidate_target = (candidate_path or (base_root / CANDIDATE_CARDS_REF)).resolve()
    errors: list[str] = []
    checks: list[dict[str, Any]] = []

    for schema_ref, (schema_id, title) in SCHEMA_IDENTITIES.items():
        schema = load_json_object(base_root / schema_ref)
        schema_errors = validate_schema_definition(schema, expected_id=schema_id, expected_title=title)
        checks.append({"check": f"schema:{schema_ref}", "ok": not schema_errors})
        errors.extend(f"{schema_ref}: {item}" for item in schema_errors)

    registry = load_json_object(registry_target)
    registry_errors = validate_registry(registry, root=base_root)
    checks.append({"check": "registry", "ok": not registry_errors, "standard_count": len(registry.get("standards", []))})
    errors.extend(f"registry: {item}" for item in registry_errors)

    candidates = load_json_object(candidate_target)
    candidate_errors = validate_candidate_cards(candidates, registry=registry, root=base_root)
    checks.append({"check": "candidate_cards", "ok": not candidate_errors, "packet_count": len(candidates.get("packets", []))})
    errors.extend(f"candidate_cards: {item}" for item in candidate_errors)

    finding: dict[str, Any] | None = None
    remediation: dict[str, Any] | None = None
    if finding_path is not None:
        finding = load_json_object(finding_path.resolve())
        finding_errors = validate_audit_finding(finding, registry=registry, root=base_root)
        checks.append({"check": "audit_finding", "ok": not finding_errors})
        errors.extend(f"audit_finding: {item}" for item in finding_errors)
    if remediation_path is not None:
        remediation = load_json_object(remediation_path.resolve())
        remediation_errors = validate_remediation_card(remediation, registry=registry, root=base_root)
        checks.append({"check": "remediation_card", "ok": not remediation_errors})
        errors.extend(f"remediation_card: {item}" for item in remediation_errors)
    if finding is not None and remediation is not None:
        link_errors = validate_finding_remediation_link(finding, remediation)
        checks.append({"check": "finding_remediation_link", "ok": not link_errors})
        errors.extend(f"finding_remediation_link: {item}" for item in link_errors)

    return {
        "contract_version": "atlas.ui-standards.foundation-validation.v1",
        "status": "valid" if not errors else "invalid",
        "safe_to_adopt_root_foundation": not errors,
        "registry_ref": atlas_relative(registry_target, root=base_root),
        "candidate_cards_ref": atlas_relative(candidate_target, root=base_root),
        "checks": checks,
        "errors": errors,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the ATLAS UI standards root foundation.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--registry-file", type=Path)
    parser.add_argument("--candidate-file", type=Path)
    parser.add_argument("--finding-file", type=Path)
    parser.add_argument("--remediation-file", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate_foundation(
        root=args.root,
        registry_path=args.registry_file,
        candidate_path=args.candidate_file,
        finding_path=args.finding_file,
        remediation_path=args.remediation_file,
    )
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        print(f"ATLAS UI standards foundation: {result['status']}")
        for check in result["checks"]:
            print(f"- {check['check']}: {'ok' if check['ok'] else 'failed'}")
        for error in result["errors"]:
            print(f"ERROR: {error}")
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
