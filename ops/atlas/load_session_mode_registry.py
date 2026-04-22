from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes, resolve_atlas_path
from ops.cortex._artifacts import stable_json_digest

SESSION_MODE_REGISTRY_VERSION = "atlas.session.mode.registry.v1"
REPO_INVENTORY_VERSION = "atlas.stack.repo-inventory.v1"
MODE_STATUSES = {"active", "disabled", "experimental"}
REPO_MATCH_ORDER = ("logical_id", "local_path", "local_path_basename", "explicit_path")


def read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {normalize_slashes(str(path))}.")
    return payload


def expect_mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object.")
    return value


def expect_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string.")
    return value.strip()


def expect_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean.")
    return value


def expect_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array of strings.")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(expect_string(item, f"{field}[{index}]"))
    return result


def normalize_mode_input(value: Any, *, index: int) -> dict[str, Any]:
    item = expect_mapping(value, f"mode[{index}].inputs[]")
    return {
        "name": expect_string(item.get("name"), f"mode[{index}].inputs[].name"),
        "required": expect_bool(item.get("required"), f"mode[{index}].inputs[].required"),
        "description": expect_string(item.get("description"), f"mode[{index}].inputs[].description"),
    }


def normalize_mode_entry(value: Any, *, index: int) -> dict[str, Any]:
    entry = expect_mapping(value, f"mode[{index}]")
    mode_id = expect_string(entry.get("mode_id"), f"mode[{index}].mode_id")
    status = expect_string(entry.get("status"), f"mode[{index}].status")
    if status not in MODE_STATUSES:
        raise ValueError(f"mode[{index}].status must be one of: {', '.join(sorted(MODE_STATUSES))}.")

    aliases = expect_string_list(entry.get("aliases", []), f"mode[{index}].aliases")
    if len(set(alias.lower() for alias in aliases)) != len(aliases):
        raise ValueError(f"mode[{index}].aliases must not contain duplicates.")

    inputs_raw = entry.get("inputs", [])
    if not isinstance(inputs_raw, list):
        raise ValueError(f"mode[{index}].inputs must be an array.")
    inputs = [normalize_mode_input(item, index=index) for item in inputs_raw]

    repo_resolution = expect_mapping(entry.get("repo_resolution"), f"mode[{index}].repo_resolution")
    match_order = expect_string_list(repo_resolution.get("match_order", []), f"mode[{index}].repo_resolution.match_order")
    for item in match_order:
        if item not in REPO_MATCH_ORDER:
            raise ValueError(f"mode[{index}].repo_resolution.match_order contains unsupported value '{item}'.")

    resolves_to = expect_mapping(entry.get("resolves_to"), f"mode[{index}].resolves_to")
    expected_first_response = expect_mapping(
        entry.get("expected_first_response"),
        f"mode[{index}].expected_first_response",
    )
    expected_patch_response = expect_mapping(
        entry.get("expected_patch_response"),
        f"mode[{index}].expected_patch_response",
    )

    normalized = {
        "mode_id": mode_id,
        "display_name": expect_string(entry.get("display_name"), f"mode[{index}].display_name"),
        "status": status,
        "description": expect_string(entry.get("description"), f"mode[{index}].description"),
        "aliases": aliases,
        "inputs": inputs,
        "repo_resolution": {
            "inventory_ref": expect_string(
                repo_resolution.get("inventory_ref"),
                f"mode[{index}].repo_resolution.inventory_ref",
            ),
            "match_order": match_order,
        },
        "resolves_to": {
            "workflow_doc": expect_string(
                resolves_to.get("workflow_doc"),
                f"mode[{index}].resolves_to.workflow_doc",
            ),
            "prompt_doc": expect_string(
                resolves_to.get("prompt_doc"),
                f"mode[{index}].resolves_to.prompt_doc",
            ),
            "startup_rules": expect_string_list(
                resolves_to.get("startup_rules", []),
                f"mode[{index}].resolves_to.startup_rules",
            ),
            "default_validation_mode": expect_string(
                resolves_to.get("default_validation_mode"),
                f"mode[{index}].resolves_to.default_validation_mode",
            ),
            "default_localhost_assumption": expect_string(
                resolves_to.get("default_localhost_assumption"),
                f"mode[{index}].resolves_to.default_localhost_assumption",
            ),
            "default_patch_style": expect_string(
                resolves_to.get("default_patch_style"),
                f"mode[{index}].resolves_to.default_patch_style",
            ),
        },
        "expected_first_response": {
            "fields": expect_string_list(
                expected_first_response.get("fields", []),
                f"mode[{index}].expected_first_response.fields",
            ),
            "template": expect_string_list(
                expected_first_response.get("template", []),
                f"mode[{index}].expected_first_response.template",
            ),
        },
        "expected_patch_response": {
            "fields": expect_string_list(
                expected_patch_response.get("fields", []),
                f"mode[{index}].expected_patch_response.fields",
            ),
        },
    }
    return normalized


def load_repo_inventory(*, root: Path | None = None) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    inventory_path = base_root / "docs" / "registry" / "STACK-REPO-INVENTORY.json"
    inventory = read_json_object(inventory_path)
    if expect_string(inventory.get("schema_version"), "repo_inventory.schema_version") != REPO_INVENTORY_VERSION:
        raise ValueError(f"repo_inventory.schema_version must be '{REPO_INVENTORY_VERSION}'.")
    repos = inventory.get("repos", [])
    if not isinstance(repos, list):
        raise ValueError("repo_inventory.repos must be an array.")
    return inventory


def load_session_mode_registry_bundle(*, root: Path | None = None) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    registry_path = base_root / "docs" / "registry" / "ATLAS-SESSION-MODE-REGISTRY.json"
    registry = read_json_object(registry_path)
    if expect_string(registry.get("schema_version"), "session_mode_registry.schema_version") != SESSION_MODE_REGISTRY_VERSION:
        raise ValueError(f"session_mode_registry.schema_version must be '{SESSION_MODE_REGISTRY_VERSION}'.")

    published_refs = expect_mapping(registry.get("published_refs"), "session_mode_registry.published_refs")
    modes_raw = registry.get("modes", [])
    if not isinstance(modes_raw, list):
        raise ValueError("session_mode_registry.modes must be an array.")
    modes = [normalize_mode_entry(item, index=index) for index, item in enumerate(modes_raw)]

    mode_ids = [entry["mode_id"] for entry in modes]
    if len(set(mode_ids)) != len(mode_ids):
        raise ValueError("session_mode_registry.modes contains duplicate mode_id values.")

    alias_map: dict[str, str] = {}
    for entry in modes:
        canonical_terms = [entry["mode_id"], *entry["aliases"]]
        for term in canonical_terms:
            normalized = term.lower()
            prior = alias_map.get(normalized)
            if prior and prior != entry["mode_id"]:
                raise ValueError(f"Alias collision detected for '{term}' between '{prior}' and '{entry['mode_id']}'.")
            alias_map[normalized] = entry["mode_id"]

    normalized_registry = {
        "schema_version": SESSION_MODE_REGISTRY_VERSION,
        "kind": expect_string(registry.get("kind"), "session_mode_registry.kind"),
        "published_refs": {
            "registry": expect_string(published_refs.get("registry"), "session_mode_registry.published_refs.registry"),
            "repo_inventory": expect_string(
                published_refs.get("repo_inventory"),
                "session_mode_registry.published_refs.repo_inventory",
            ),
        },
        "modes": sorted(modes, key=lambda entry: entry["mode_id"]),
    }

    inventory = load_repo_inventory(root=base_root)
    return {
        "schema_version": "atlas.session.mode.bundle.v1",
        "root_ref": atlas_relative(base_root, root=base_root),
        "registry_ref": atlas_relative(registry_path, root=base_root),
        "repo_inventory_ref": normalized_registry["published_refs"]["repo_inventory"],
        "registry_digest": stable_json_digest(normalized_registry),
        "mode_count": len(normalized_registry["modes"]),
        "session_mode_registry": normalized_registry,
        "repo_inventory": inventory,
        "alias_map": alias_map,
    }


def select_mode_entry(bundle: dict[str, Any], mode_id: str) -> dict[str, Any]:
    for entry in bundle.get("session_mode_registry", {}).get("modes", []):
        if isinstance(entry, dict) and entry.get("mode_id") == mode_id:
            return entry
    raise KeyError(f"Unknown mode_id '{mode_id}'.")


def resolve_mode_from_invocation(bundle: dict[str, Any], invocation_text: str) -> dict[str, Any]:
    normalized_text = invocation_text.strip().lower()
    if not normalized_text:
        raise ValueError("invocation_text must be a non-empty string.")

    candidates: list[tuple[int, str]] = []
    for alias, mode_id in bundle.get("alias_map", {}).items():
        if alias == normalized_text:
            candidates.append((len(alias), mode_id))
            continue
        if alias in normalized_text:
            candidates.append((len(alias), mode_id))
    if not candidates:
        raise KeyError(f"No session mode matched invocation '{invocation_text}'.")
    _, selected_mode_id = max(candidates, key=lambda item: item[0])
    return select_mode_entry(bundle, selected_mode_id)


def resolve_repo_input(repo_input: str, *, root: Path | None = None) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    inventory = load_repo_inventory(root=base_root)
    repos = inventory.get("repos", [])
    if not isinstance(repos, list):
        raise ValueError("repo_inventory.repos must be an array.")

    normalized_input = normalize_slashes(repo_input).strip().strip("/")
    lowered_input = normalized_input.lower()
    if not lowered_input:
        raise ValueError("repo_input must be a non-empty string.")

    for repo in repos:
        if isinstance(repo, dict) and str(repo.get("logical_id", "")).lower() == lowered_input:
            return repo
    for repo in repos:
        if isinstance(repo, dict) and normalize_slashes(str(repo.get("local_path", ""))).lower() == lowered_input:
            return repo
    for repo in repos:
        local_path = normalize_slashes(str(repo.get("local_path", ""))).strip("/")
        if local_path and Path(local_path).name.lower() == Path(lowered_input).name.lower():
            return repo

    candidate = resolve_atlas_path(normalized_input, root=base_root)
    if candidate.exists():
        candidate_text = atlas_relative(candidate, root=base_root).lower()
        for repo in repos:
            local_path = normalize_slashes(str(repo.get("local_path", ""))).lower()
            if local_path == candidate_text:
                return repo
    raise KeyError(f"Could not resolve repo input '{repo_input}' against the stack repo inventory.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Load and normalize the root-owned ATLAS session mode registry.",
    )
    parser.add_argument("--mode-id")
    parser.add_argument("--invocation")
    parser.add_argument("--repo")
    args = parser.parse_args(argv)

    bundle = load_session_mode_registry_bundle(root=atlas_root())
    if args.mode_id:
        bundle["selected_mode"] = select_mode_entry(bundle, args.mode_id)
    if args.invocation:
        bundle["resolved_mode_from_invocation"] = resolve_mode_from_invocation(bundle, args.invocation)
    if args.repo:
        bundle["resolved_repo"] = resolve_repo_input(args.repo, root=atlas_root())
    print(json.dumps(bundle, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
