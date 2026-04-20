from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes
from ops.cortex._artifacts import stable_json_digest, write_json

UI_OBSERVATION_CONTRACT_VERSION = "atlas.ui.observation.v1"
UI_OBSERVATION_SCHEMA_ID = "atlas://schemas/atlas.ui.observation.v1.json"
UI_CAPTURE_INPUTS_CONTRACT_VERSION = "atlas.ui.capture-inputs.v1"
UI_CAPTURE_MAP_CONTRACT_VERSION = "atlas.ui.capture-map.v1"
OBSERVER_VERSION = "atlas.ui.observe.fitness.v1"
EXPECTED_TRAIT_KEYS = (
    "spacing",
    "typography",
    "header_shape",
    "card_shape",
    "tag_usage",
    "section_layout",
)
EXPECTED_PRIMITIVE_SLOTS = ("header", "card", "tag", "section_layout")
TOKEN_SCALE_NAMES = ("spacing", "typography", "colors", "radii", "shadows", "borders")
TOKEN_REF_PATTERN = re.compile(r"\b(?P<scale>spacing|typography|colors|radii|shadows|borders)\.[A-Za-z0-9._-]+\b")
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stamp_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def capture_mapping_key(screen_key: str, state_key: str) -> str:
    return f"{screen_key}::{state_key}"


def default_capture_inputs_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "ops" / "atlas" / "ui_observe" / "fitness_capture_inputs.v1.json"


def default_capture_map_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "ops" / "atlas" / "ui_observe" / "fitness_capture_map.v1.json"


def default_schema_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "schemas" / "atlas.ui.observation.v1.json"


def default_capture_map_schema_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "schemas" / "atlas.ui.capture-map.v1.json"


def default_output_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "atlas" / "ui-observe" / "fitness"


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {normalize_slashes(str(path))}.")
    return payload


def _resolve_ref(ref: str, *, root: Path) -> Path:
    candidate = Path(ref)
    return candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()


def validate_schema_definition(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("Schema $schema must target draft 2020-12.")
    if schema.get("$id") != UI_OBSERVATION_SCHEMA_ID:
        errors.append(f"Schema $id must be '{UI_OBSERVATION_SCHEMA_ID}'.")
    if schema.get("title") != "ATLAS UI observation v1":
        errors.append("Schema title must be 'ATLAS UI observation v1'.")
    if schema.get("type") != "object":
        errors.append("Schema root type must be object.")
    if schema.get("additionalProperties") is not False:
        errors.append("Schema root must disallow additionalProperties.")
    required = schema.get("required")
    if not isinstance(required, list):
        errors.append("Schema required must be an array.")
    else:
        for field in (
            "contract_version",
            "observation_id",
            "comparison_key",
            "comparison_digest",
            "observer_version",
            "source_kind",
            "owner_repo_id",
            "owner_repo_path",
            "owner_contract_refs",
            "capture",
            "observed_at",
            "snapshot",
            "traits",
            "provenance",
        ):
            if field not in required:
                errors.append(f"Schema required is missing '{field}'.")
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        errors.append("Schema properties must be an object.")
    else:
        traits = properties.get("traits")
        if not isinstance(traits, dict):
            errors.append("Schema properties.traits must be present.")
        else:
            required_traits = traits.get("required")
            if not isinstance(required_traits, list):
                errors.append("Schema traits.required must be an array.")
            else:
                for key in EXPECTED_TRAIT_KEYS:
                    if key not in required_traits:
                        errors.append(f"Schema traits.required is missing '{key}'.")
    return errors


def validate_capture_map_schema_definition(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("Schema $schema must target draft 2020-12.")
    if schema.get("$id") != "atlas://schemas/atlas.ui.capture-map.v1.json":
        errors.append("Schema $id must be 'atlas://schemas/atlas.ui.capture-map.v1.json'.")
    if schema.get("title") != "ATLAS UI capture map v1":
        errors.append("Schema title must be 'ATLAS UI capture map v1'.")
    return errors


def validate_capture_inputs(inputs: dict[str, Any], *, root: Path) -> list[str]:
    errors: list[str] = []
    if inputs.get("contract_version") != UI_CAPTURE_INPUTS_CONTRACT_VERSION:
        errors.append(f"contract_version must be '{UI_CAPTURE_INPUTS_CONTRACT_VERSION}'.")

    owner_repo_id = inputs.get("owner_repo_id")
    if not isinstance(owner_repo_id, str) or not owner_repo_id.strip():
        errors.append("owner_repo_id must be a non-empty string.")
    owner_repo_path = inputs.get("owner_repo_path")
    if not isinstance(owner_repo_path, str) or not owner_repo_path.strip():
        errors.append("owner_repo_path must be a non-empty string.")
    elif not _resolve_ref(owner_repo_path, root=root).exists():
        errors.append(f"owner_repo_path does not exist: {owner_repo_path}")

    contract_refs = inputs.get("owner_contract_refs")
    if not isinstance(contract_refs, dict):
        errors.append("owner_contract_refs must be an object.")
    else:
        for key in ("tokens_ref", "primitives_ref"):
            value = contract_refs.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"owner_contract_refs.{key} must be a non-empty string.")
            elif not _resolve_ref(value, root=root).exists():
                errors.append(f"owner_contract_refs.{key} does not exist: {value}")

    capture_map_ref = inputs.get("capture_map_ref")
    if not isinstance(capture_map_ref, str) or not capture_map_ref.strip():
        errors.append("capture_map_ref must be a non-empty string.")
    elif not _resolve_ref(capture_map_ref, root=root).exists():
        errors.append(f"capture_map_ref does not exist: {capture_map_ref}")

    capture_set = inputs.get("capture_set")
    if not isinstance(capture_set, list) or not capture_set:
        errors.append("capture_set must be a non-empty array.")
        return errors

    seen_selectors: set[str] = set()
    for index, selector in enumerate(capture_set):
        path = f"capture_set[{index}]"
        if not isinstance(selector, dict):
            errors.append(f"{path} must be an object.")
            continue
        screen_key = selector.get("screen_key")
        state_key = selector.get("state_key")
        if not isinstance(screen_key, str) or not screen_key.strip():
            errors.append(f"{path}.screen_key must be a non-empty string.")
        if not isinstance(state_key, str) or not state_key.strip():
            errors.append(f"{path}.state_key must be a non-empty string.")
        if isinstance(screen_key, str) and isinstance(state_key, str) and screen_key.strip() and state_key.strip():
            selector_key = capture_mapping_key(screen_key.strip(), state_key.strip())
            if selector_key in seen_selectors:
                errors.append(f"{path} duplicates selector '{selector_key}'.")
            else:
                seen_selectors.add(selector_key)
    return errors


def validate_capture_map(capture_map: dict[str, Any], *, root: Path) -> list[str]:
    errors: list[str] = []
    if capture_map.get("contract_version") != UI_CAPTURE_MAP_CONTRACT_VERSION:
        errors.append(f"contract_version must be '{UI_CAPTURE_MAP_CONTRACT_VERSION}'.")

    owner_repo_id = capture_map.get("owner_repo_id")
    if not isinstance(owner_repo_id, str) or not owner_repo_id.strip():
        errors.append("owner_repo_id must be a non-empty string.")
    owner_repo_path = capture_map.get("owner_repo_path")
    if not isinstance(owner_repo_path, str) or not owner_repo_path.strip():
        errors.append("owner_repo_path must be a non-empty string.")
    elif not _resolve_ref(owner_repo_path, root=root).exists():
        errors.append(f"owner_repo_path does not exist: {owner_repo_path}")

    captures = capture_map.get("captures")
    if not isinstance(captures, list) or not captures:
        errors.append("captures must be a non-empty array.")
        return errors

    seen_capture_ids: set[str] = set()
    seen_mapping_keys: set[str] = set()
    for index, capture in enumerate(captures):
        path = f"captures[{index}]"
        if not isinstance(capture, dict):
            errors.append(f"{path} must be an object.")
            continue
        capture_id = capture.get("capture_id")
        screen_key = capture.get("screen_key")
        state_key = capture.get("state_key")
        if not isinstance(capture_id, str) or not capture_id.strip():
            errors.append(f"{path}.capture_id must be a non-empty string.")
        elif capture_id in seen_capture_ids:
            errors.append(f"{path}.capture_id '{capture_id}' is duplicated.")
        else:
            seen_capture_ids.add(capture_id)
        for key in ("screen_key", "screen_label", "state_key", "state_label", "route_family"):
            value = capture.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{path}.{key} must be a non-empty string.")
        if isinstance(screen_key, str) and isinstance(state_key, str) and screen_key.strip() and state_key.strip():
            map_key = capture_mapping_key(screen_key.strip(), state_key.strip())
            if map_key in seen_mapping_keys:
                errors.append(f"{path} duplicates mapping key '{map_key}'.")
            else:
                seen_mapping_keys.add(map_key)

        primitive_variants = capture.get("primitive_variants")
        if not isinstance(primitive_variants, dict):
            errors.append(f"{path}.primitive_variants must be an object.")
        else:
            for slot in EXPECTED_PRIMITIVE_SLOTS:
                config = primitive_variants.get(slot)
                if not isinstance(config, dict):
                    errors.append(f"{path}.primitive_variants.{slot} must be an object.")
                    continue
                primitive_id = config.get("primitive_id")
                variant_id = config.get("variant_id")
                if not isinstance(primitive_id, str) or not primitive_id.strip():
                    errors.append(f"{path}.primitive_variants.{slot}.primitive_id must be a non-empty string.")
                if not isinstance(variant_id, str) or not variant_id.strip():
                    errors.append(f"{path}.primitive_variants.{slot}.variant_id must be a non-empty string.")

        owner_surface_refs = capture.get("owner_surface_refs")
        if not isinstance(owner_surface_refs, list) or not owner_surface_refs:
            errors.append(f"{path}.owner_surface_refs must be a non-empty array.")
        else:
            for ref in owner_surface_refs:
                if not isinstance(ref, str) or not ref.strip():
                    errors.append(f"{path}.owner_surface_refs entries must be non-empty strings.")
                    continue
                if not _resolve_ref(ref, root=root).exists():
                    errors.append(f"{path}.owner_surface_refs entry does not exist: {ref}")
    return errors


def _normalize_primitive_index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    primitives = payload.get("primitiveContracts")
    if primitives is None:
        primitives = payload.get("primitives")
    index: dict[str, dict[str, Any]] = {}
    if isinstance(primitives, dict):
        for primitive_id, value in primitives.items():
            if isinstance(value, dict):
                index[str(primitive_id)] = {"primitive_id": str(primitive_id), **value}
        return index
    if isinstance(primitives, list):
        for value in primitives:
            if not isinstance(value, dict):
                continue
            primitive_id = value.get("primitive_id")
            if not isinstance(primitive_id, str) or not primitive_id.strip():
                primitive_id = value.get("id")
            if isinstance(primitive_id, str) and primitive_id.strip():
                index[primitive_id] = {"primitive_id": primitive_id, **value}
    return index


def _normalize_variants(primitive: dict[str, Any]) -> dict[str, dict[str, Any]]:
    variants = primitive.get("variants")
    normalized: dict[str, dict[str, Any]] = {}
    if isinstance(variants, dict):
        for variant_id, value in variants.items():
            if isinstance(value, dict):
                normalized[str(variant_id)] = {"variant_id": str(variant_id), **value}
        return normalized
    if isinstance(variants, list):
        for value in variants:
            if not isinstance(value, dict):
                continue
            variant_id = value.get("variant_id")
            if not isinstance(variant_id, str) or not variant_id.strip():
                variant_id = value.get("id")
            if isinstance(variant_id, str) and variant_id.strip():
                normalized[variant_id] = {"variant_id": variant_id, **value}
    return normalized


def validate_capture_map_contract_bindings(capture_map: dict[str, Any], primitives: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    primitive_index = _normalize_primitive_index(primitives)
    captures = capture_map.get("captures")
    if not isinstance(captures, list):
        return ["capture map captures must be a list before binding validation."]

    for capture in captures:
        if not isinstance(capture, dict):
            continue
        capture_id = str(capture.get("capture_id", "unknown"))
        primitive_variants = capture.get("primitive_variants")
        if not isinstance(primitive_variants, dict):
            continue
        for slot in EXPECTED_PRIMITIVE_SLOTS:
            selection = primitive_variants.get(slot)
            if not isinstance(selection, dict):
                continue
            primitive_id = str(selection.get("primitive_id", "")).strip()
            variant_id = str(selection.get("variant_id", "")).strip()
            primitive = primitive_index.get(primitive_id)
            if not primitive_id or not isinstance(primitive, dict):
                errors.append(f"Capture '{capture_id}' slot '{slot}' references missing primitive '{primitive_id}'.")
                continue
            variants = _normalize_variants(primitive)
            if variant_id not in variants:
                errors.append(
                    f"Capture '{capture_id}' slot '{slot}' references missing variant '{variant_id}' on primitive '{primitive_id}'."
                )
    return errors


def _collect_token_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, str):
        refs.update(match.group(0) for match in TOKEN_REF_PATTERN.finditer(value))
        return refs
    if isinstance(value, list):
        for item in value:
            refs.update(_collect_token_refs(item))
        return refs
    if isinstance(value, dict):
        for item in value.values():
            refs.update(_collect_token_refs(item))
    return refs


def _group_token_refs_by_scale(token_refs: set[str]) -> dict[str, list[str]]:
    grouped = {scale: [] for scale in TOKEN_SCALE_NAMES}
    for ref in sorted(token_refs):
        scale, _, _ = ref.partition(".")
        if scale in grouped:
            grouped[scale].append(ref)
    return grouped


def _compact_trait_snapshot(variant: dict[str, Any]) -> dict[str, Any]:
    if isinstance(variant.get("traits"), dict):
        return dict(variant["traits"])
    if isinstance(variant.get("semanticRefs"), dict):
        return {"semanticRefs": dict(variant["semanticRefs"])}
    snapshot: dict[str, Any] = {}
    for key in (
        "shape",
        "surface",
        "layout",
        "alignment",
        "density",
        "tone",
        "size",
        "grammar",
        "hierarchy",
        "orientation",
        "insets",
        "slots",
        "usage",
        "states",
    ):
        value = variant.get(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            snapshot[key] = value
        elif isinstance(value, list):
            snapshot[key] = value
        elif isinstance(value, dict):
            snapshot[key] = value
    return snapshot


def _trait_payload(
    *,
    primitive_id: str,
    variant_id: str,
    variant: dict[str, Any],
    contract_ref: str,
) -> dict[str, Any]:
    token_refs = sorted(_collect_token_refs(variant))
    return {
        "primitive_id": primitive_id,
        "variant_id": variant_id,
        "contract_ref": contract_ref,
        "token_refs": token_refs,
        "trait_snapshot": _compact_trait_snapshot(variant),
    }


def _load_owner_contracts(inputs: dict[str, Any], *, root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    contract_refs = inputs["owner_contract_refs"]
    tokens_path = _resolve_ref(str(contract_refs["tokens_ref"]), root=root)
    primitives_path = _resolve_ref(str(contract_refs["primitives_ref"]), root=root)
    tokens = load_json_object(tokens_path)
    primitives = load_json_object(primitives_path)
    refs = {
        "tokens_ref": atlas_relative(tokens_path, root=root),
        "primitives_ref": atlas_relative(primitives_path, root=root),
    }
    manifest_ref = contract_refs.get("manifest_ref")
    if isinstance(manifest_ref, str) and manifest_ref.strip():
        manifest_path = _resolve_ref(manifest_ref, root=root)
        if manifest_path.exists():
            refs["manifest_ref"] = atlas_relative(manifest_path, root=root)
    return tokens, primitives, refs


def _load_capture_map(inputs: dict[str, Any], *, root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    capture_map_path = _resolve_ref(str(inputs["capture_map_ref"]), root=root)
    capture_map = load_json_object(capture_map_path)
    refs = {"capture_map_ref": atlas_relative(capture_map_path, root=root)}
    return capture_map, refs


def _capture_map_index(capture_map: dict[str, Any]) -> dict[str, dict[str, Any]]:
    captures = capture_map.get("captures")
    if not isinstance(captures, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for capture in captures:
        if not isinstance(capture, dict):
            continue
        screen_key = capture.get("screen_key")
        state_key = capture.get("state_key")
        if isinstance(screen_key, str) and isinstance(state_key, str) and screen_key.strip() and state_key.strip():
            result[capture_mapping_key(screen_key.strip(), state_key.strip())] = capture
    return result


def resolve_capture_set(inputs: dict[str, Any], capture_map: dict[str, Any]) -> list[dict[str, Any]]:
    selectors = inputs.get("capture_set")
    if not isinstance(selectors, list):
        raise ValueError("capture_set must be a list.")
    capture_index = _capture_map_index(capture_map)
    resolved: list[dict[str, Any]] = []
    for selector in selectors:
        if not isinstance(selector, dict):
            raise ValueError("capture_set selectors must be objects.")
        screen_key = str(selector.get("screen_key", "")).strip()
        state_key = str(selector.get("state_key", "")).strip()
        key = capture_mapping_key(screen_key, state_key)
        capture = capture_index.get(key)
        if not isinstance(capture, dict):
            raise ValueError(f"capture_set selector '{key}' does not exist in the capture map.")
        resolved.append(capture)
    return resolved


def _resolve_variant(primitive: dict[str, Any], *, variant_id: str) -> dict[str, Any]:
    variants = _normalize_variants(primitive)
    if variant_id not in variants:
        raise ValueError(
            f"Primitive '{primitive.get('primitive_id', 'unknown')}' is missing required variant '{variant_id}'."
        )
    return variants[variant_id]


def _build_observation(
    *,
    inputs: dict[str, Any],
    capture: dict[str, Any],
    tokens: dict[str, Any],
    primitives: dict[str, Any],
    contract_refs: dict[str, str],
    capture_contract_refs: dict[str, str],
    root: Path,
) -> dict[str, Any]:
    primitive_index = _normalize_primitive_index(primitives)
    selected_primitives: list[dict[str, Any]] = []

    for slot, trait_name in (
        ("header", "header_shape"),
        ("card", "card_shape"),
        ("tag", "tag_usage"),
        ("section_layout", "section_layout"),
    ):
        selection = capture["primitive_variants"][slot]
        primitive_id = str(selection["primitive_id"])
        variant_id = str(selection["variant_id"])
        primitive = primitive_index.get(primitive_id)
        if not isinstance(primitive, dict):
            raise ValueError(f"Capture '{capture['capture_id']}' references missing primitive '{primitive_id}'.")
        variant = _resolve_variant(primitive, variant_id=variant_id)
        selected_primitives.append(
            {
                "slot": slot,
                "trait_name": trait_name,
                **_trait_payload(
                    primitive_id=primitive_id,
                    variant_id=variant_id,
                    variant=variant,
                    contract_ref=f"{contract_refs['primitives_ref']}#primitiveContracts.{primitive_id}.variants.{variant_id}",
                ),
            }
        )

    all_token_refs: set[str] = set()
    for item in selected_primitives:
        all_token_refs.update(item["token_refs"])
    token_refs_by_scale = _group_token_refs_by_scale(all_token_refs)

    selected_by_trait = {item["trait_name"]: item for item in selected_primitives}
    spacing_sources = [
        {
            "primitive_id": item["primitive_id"],
            "variant_id": item["variant_id"],
            "contract_ref": item["contract_ref"],
        }
        for item in selected_primitives
        if any(ref.startswith("spacing.") for ref in item["token_refs"])
    ]
    typography_sources = [
        {
            "primitive_id": item["primitive_id"],
            "variant_id": item["variant_id"],
            "contract_ref": item["contract_ref"],
        }
        for item in selected_primitives
        if any(ref.startswith("typography.") for ref in item["token_refs"])
    ]

    traits = {
        "spacing": {
            "token_refs": token_refs_by_scale["spacing"],
            "source_primitives": spacing_sources,
        },
        "typography": {
            "token_refs": token_refs_by_scale["typography"],
            "source_primitives": typography_sources,
        },
        "header_shape": {
            "primitive_id": selected_by_trait["header_shape"]["primitive_id"],
            "variant_id": selected_by_trait["header_shape"]["variant_id"],
            "contract_ref": selected_by_trait["header_shape"]["contract_ref"],
            "token_refs": selected_by_trait["header_shape"]["token_refs"],
            "trait_snapshot": selected_by_trait["header_shape"]["trait_snapshot"],
        },
        "card_shape": {
            "primitive_id": selected_by_trait["card_shape"]["primitive_id"],
            "variant_id": selected_by_trait["card_shape"]["variant_id"],
            "contract_ref": selected_by_trait["card_shape"]["contract_ref"],
            "token_refs": selected_by_trait["card_shape"]["token_refs"],
            "trait_snapshot": selected_by_trait["card_shape"]["trait_snapshot"],
        },
        "tag_usage": {
            "primitive_id": selected_by_trait["tag_usage"]["primitive_id"],
            "variant_id": selected_by_trait["tag_usage"]["variant_id"],
            "contract_ref": selected_by_trait["tag_usage"]["contract_ref"],
            "token_refs": selected_by_trait["tag_usage"]["token_refs"],
            "trait_snapshot": selected_by_trait["tag_usage"]["trait_snapshot"],
        },
        "section_layout": {
            "primitive_id": selected_by_trait["section_layout"]["primitive_id"],
            "variant_id": selected_by_trait["section_layout"]["variant_id"],
            "contract_ref": selected_by_trait["section_layout"]["contract_ref"],
            "token_refs": selected_by_trait["section_layout"]["token_refs"],
            "trait_snapshot": selected_by_trait["section_layout"]["trait_snapshot"],
        },
    }

    snapshot = {
        "selected_primitives": selected_primitives,
        "token_refs_by_scale": token_refs_by_scale,
        "token_contract_ref": contract_refs["tokens_ref"],
    }
    comparison_payload = {
        "owner_repo_id": inputs["owner_repo_id"],
        "capture_id": capture["capture_id"],
        "screen_key": capture["screen_key"],
        "state_key": capture["state_key"],
        "snapshot": snapshot,
        "traits": traits,
    }
    comparison_digest = stable_json_digest(comparison_payload)
    observation_id = stable_json_digest(
        {
            "contract_version": UI_OBSERVATION_CONTRACT_VERSION,
            "comparison_key": f"{inputs['owner_repo_id']}:{capture['capture_id']}",
            "comparison_digest": comparison_digest,
        }
    )
    contracts_digest = stable_json_digest(
        {
            "tokens_digest": stable_json_digest(tokens),
            "primitives_digest": stable_json_digest(primitives),
        }
    )
    inputs_digest = stable_json_digest(
        {
            "owner_repo_id": inputs["owner_repo_id"],
            "capture_set": inputs["capture_set"],
            "capture_map_ref": inputs["capture_map_ref"],
        }
    )
    capture_map_digest = stable_json_digest(capture)
    return {
        "contract_version": UI_OBSERVATION_CONTRACT_VERSION,
        "observation_id": observation_id,
        "comparison_key": f"{inputs['owner_repo_id']}:{capture['capture_id']}",
        "comparison_digest": comparison_digest,
        "observer_version": OBSERVER_VERSION,
        "source_kind": "owner_contracts",
        "owner_repo_id": inputs["owner_repo_id"],
        "owner_repo_path": normalize_slashes(str(inputs["owner_repo_path"])),
        "owner_contract_refs": contract_refs,
        "capture": {
            "capture_id": capture["capture_id"],
            "screen_key": capture["screen_key"],
            "screen_label": capture["screen_label"],
            "state_key": capture["state_key"],
            "state_label": capture["state_label"],
            "route_family": capture["route_family"],
            "capture_map_ref": capture_contract_refs["capture_map_ref"],
            "owner_surface_refs": [normalize_slashes(str(item)) for item in capture["owner_surface_refs"]],
            "primitive_variants": {
                item["slot"]: {
                    "primitive_id": item["primitive_id"],
                    "variant_id": item["variant_id"],
                    "contract_ref": item["contract_ref"],
                }
                for item in selected_primitives
            },
        },
        "observed_at": utc_now(),
        "snapshot": snapshot,
        "traits": traits,
        "provenance": {
            "inputs_digest": inputs_digest,
            "contracts_digest": contracts_digest,
            "capture_map_digest": capture_map_digest,
            "observer_root": atlas_relative(root, root=root),
        },
    }


def validate_observation_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("contract_version") != UI_OBSERVATION_CONTRACT_VERSION:
        errors.append(f"contract_version must be '{UI_OBSERVATION_CONTRACT_VERSION}'.")
    for key in ("observation_id", "comparison_digest"):
        value = payload.get(key)
        if not isinstance(value, str) or not SHA256_PATTERN.fullmatch(value):
            errors.append(f"{key} must be a sha256 digest string.")
    for key in ("comparison_key", "observer_version", "source_kind", "owner_repo_id", "owner_repo_path", "observed_at"):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string.")
    if payload.get("source_kind") != "owner_contracts":
        errors.append("source_kind must be 'owner_contracts'.")

    contract_refs = payload.get("owner_contract_refs")
    if not isinstance(contract_refs, dict):
        errors.append("owner_contract_refs must be an object.")
    else:
        for key in ("tokens_ref", "primitives_ref"):
            value = contract_refs.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"owner_contract_refs.{key} must be a non-empty string.")

    capture = payload.get("capture")
    if not isinstance(capture, dict):
        errors.append("capture must be an object.")
    else:
        for key in ("capture_id", "screen_key", "screen_label", "state_key", "state_label", "route_family", "capture_map_ref"):
            value = capture.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"capture.{key} must be a non-empty string.")
        owner_surface_refs = capture.get("owner_surface_refs")
        if not isinstance(owner_surface_refs, list) or not owner_surface_refs:
            errors.append("capture.owner_surface_refs must be a non-empty array.")

    snapshot = payload.get("snapshot")
    if not isinstance(snapshot, dict):
        errors.append("snapshot must be an object.")
    else:
        selected_primitives = snapshot.get("selected_primitives")
        if not isinstance(selected_primitives, list) or not selected_primitives:
            errors.append("snapshot.selected_primitives must be a non-empty array.")
        token_refs_by_scale = snapshot.get("token_refs_by_scale")
        if not isinstance(token_refs_by_scale, dict):
            errors.append("snapshot.token_refs_by_scale must be an object.")
        else:
            for scale in TOKEN_SCALE_NAMES:
                value = token_refs_by_scale.get(scale)
                if not isinstance(value, list):
                    errors.append(f"snapshot.token_refs_by_scale.{scale} must be an array.")

    traits = payload.get("traits")
    if not isinstance(traits, dict):
        errors.append("traits must be an object.")
    else:
        for key in EXPECTED_TRAIT_KEYS:
            if not isinstance(traits.get(key), dict):
                errors.append(f"traits.{key} must be an object.")

    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance must be an object.")
    else:
        for key in ("inputs_digest", "contracts_digest", "capture_map_digest"):
            value = provenance.get(key)
            if not isinstance(value, str) or not SHA256_PATTERN.fullmatch(value):
                errors.append(f"provenance.{key} must be a sha256 digest string.")
    return errors


def _write_observation(observation: dict[str, Any], *, output_root: Path, root: Path) -> dict[str, str]:
    capture_id = str(observation["capture"]["capture_id"])
    target_dir = output_root / capture_id
    latest_path = target_dir / "latest.json"
    stamped_path = target_dir / f"{stamp_now()}-{str(observation['observation_id']).replace('sha256:', '')[:16]}.json"
    write_json(latest_path, observation)
    write_json(stamped_path, observation)
    return {
        "capture_id": capture_id,
        "latest_ref": atlas_relative(latest_path, root=root),
        "receipt_ref": atlas_relative(stamped_path, root=root),
    }


def observe_fitness_ui(
    *,
    root: Path | None = None,
    inputs_path: Path | None = None,
    capture_map_path: Path | None = None,
    schema_path: Path | None = None,
    capture_map_schema_path: Path | None = None,
    output_root: Path | None = None,
    capture_ids: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    inputs_target = (inputs_path or default_capture_inputs_path(base_root)).resolve()
    schema_target = (schema_path or default_schema_path(base_root)).resolve()
    capture_map_schema_target = (capture_map_schema_path or default_capture_map_schema_path(base_root)).resolve()
    output_target = (output_root or default_output_root(base_root)).resolve()

    schema = load_json_object(schema_target)
    schema_errors = validate_schema_definition(schema)
    if schema_errors:
        raise ValueError("; ".join(schema_errors))

    capture_map_schema = load_json_object(capture_map_schema_target)
    capture_map_schema_errors = validate_capture_map_schema_definition(capture_map_schema)
    if capture_map_schema_errors:
        raise ValueError("; ".join(capture_map_schema_errors))

    inputs = load_json_object(inputs_target)
    input_errors = validate_capture_inputs(inputs, root=base_root)
    if input_errors:
        raise ValueError("; ".join(input_errors))

    if capture_map_path is not None:
        inputs = {**inputs, "capture_map_ref": atlas_relative(capture_map_path.resolve(), root=base_root)}

    capture_map, capture_contract_refs = _load_capture_map(inputs, root=base_root)
    capture_map_errors = validate_capture_map(capture_map, root=base_root)
    if capture_map_errors:
        raise ValueError("; ".join(capture_map_errors))

    if capture_map.get("owner_repo_id") != inputs.get("owner_repo_id"):
        raise ValueError("capture map owner_repo_id does not match capture inputs owner_repo_id.")
    if capture_map.get("owner_repo_path") != inputs.get("owner_repo_path"):
        raise ValueError("capture map owner_repo_path does not match capture inputs owner_repo_path.")

    tokens, primitives, contract_refs = _load_owner_contracts(inputs, root=base_root)
    binding_errors = validate_capture_map_contract_bindings(capture_map, primitives)
    if binding_errors:
        raise ValueError("; ".join(binding_errors))

    captures = resolve_capture_set(inputs, capture_map)
    requested_capture_ids = {item.strip() for item in (capture_ids or []) if item.strip()}
    observations: list[dict[str, Any]] = []
    outputs: list[dict[str, str]] = []

    for capture in captures:
        capture_id = str(capture["capture_id"])
        if requested_capture_ids and capture_id not in requested_capture_ids:
            continue
        observation = _build_observation(
            inputs=inputs,
            capture=capture,
            tokens=tokens,
            primitives=primitives,
            contract_refs=contract_refs,
            capture_contract_refs=capture_contract_refs,
            root=base_root,
        )
        payload_errors = validate_observation_payload(observation)
        if payload_errors:
            raise ValueError("; ".join(payload_errors))
        observations.append(observation)
        if not dry_run:
            outputs.append(_write_observation(observation, output_root=output_target, root=base_root))

    observations.sort(key=lambda item: str(item["capture"]["capture_id"]))
    outputs.sort(key=lambda item: item["capture_id"])
    return {
        "ok": True,
        "observer_version": OBSERVER_VERSION,
        "schema_ref": atlas_relative(schema_target, root=base_root),
        "capture_map_schema_ref": atlas_relative(capture_map_schema_target, root=base_root),
        "inputs_ref": atlas_relative(inputs_target, root=base_root),
        "capture_map_ref": capture_contract_refs["capture_map_ref"],
        "output_root": atlas_relative(output_target, root=base_root),
        "capture_count": len(observations),
        "comparison_keys": [str(item["comparison_key"]) for item in observations],
        "observations": observations,
        "outputs": outputs,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture deterministic Fitness UI observations from owner contracts.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--inputs-file", type=Path)
    parser.add_argument("--capture-map-file", type=Path)
    parser.add_argument("--schema-file", type=Path)
    parser.add_argument("--capture-map-schema-file", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--capture-id", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    result = observe_fitness_ui(
        root=args.root.resolve(),
        inputs_path=args.inputs_file.resolve() if isinstance(args.inputs_file, Path) else None,
        capture_map_path=args.capture_map_file.resolve() if isinstance(args.capture_map_file, Path) else None,
        schema_path=args.schema_file.resolve() if isinstance(args.schema_file, Path) else None,
        capture_map_schema_path=(
            args.capture_map_schema_file.resolve() if isinstance(args.capture_map_schema_file, Path) else None
        ),
        output_root=args.output_root.resolve() if isinstance(args.output_root, Path) else None,
        capture_ids=list(args.capture_id),
        dry_run=bool(args.dry_run),
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
