from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes
from ops.cortex._artifacts import stable_json_digest

TOOL_REGISTRY_VERSION = "atlas.tool.registry.v1"
EXTENSION_REGISTRY_VERSION = "atlas.extension.registry.v1"
TOOL_ENTRY_VERSION = "atlas.tool.catalog.entry.v1"
EXTENSION_ENTRY_VERSION = "atlas.extension.manifest.v1"
CAPABILITY_PROFILE_VERSION = "atlas.capability.profile.v1"
AWARENESS_CONNECTOR_SCHEMA_VERSION = "atlas.awareness.connector.toolset.v1"
CONNECTOR_TOOL_IDS = [
    "search",
    "fetch",
    "atlas_status",
    "atlas_session_fetch",
    "atlas_query_knowledge",
]
CONNECTOR_TOOL_SPECS: dict[str, dict[str, Any]] = {
    "search": {
        "description": "Search ATLAS inventory, sessions, attention items, and governed knowledge surfaces.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["query"],
            "properties": {
                "query": {"type": "string", "minLength": 1},
                "limit": {"type": "integer", "minimum": 1},
            },
        },
    },
    "fetch": {
        "description": "Fetch a full ATLAS search result document by id.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["id"],
            "properties": {
                "id": {"type": "string", "minLength": 1},
            },
        },
    },
    "atlas_status": {
        "description": "Return the current ATLAS awareness status with snapshot and attention digests.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {},
        },
    },
    "atlas_session_fetch": {
        "description": "Fetch a governed ATLAS session by session_id.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["session_id"],
            "properties": {
                "session_id": {"type": "string", "minLength": 1},
            },
        },
    },
    "atlas_query_knowledge": {
        "description": "Query the ATLAS knowledge bundle under indexing policy constraints.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["query"],
            "properties": {
                "query": {"type": "string", "minLength": 1},
                "limit": {"type": "integer", "minimum": 1},
            },
        },
    },
}


def read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {normalize_slashes(str(path))}.")
    return payload


def expect_mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object.")
    return value


def expect_string(value: Any, field: str, *, allow_null: bool = False) -> str | None:
    if value is None and allow_null:
        return None
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
    for index, entry in enumerate(value):
        result.append(expect_string(entry, f"{field}[{index}]") or "")
    return result


def normalize_capability_profile(value: Any, field: str) -> dict[str, Any]:
    profile = expect_mapping(value, field)
    if expect_string(profile.get("contract_version"), f"{field}.contract_version") != CAPABILITY_PROFILE_VERSION:
        raise ValueError(f"{field}.contract_version must be '{CAPABILITY_PROFILE_VERSION}'.")

    filesystem_scopes = expect_mapping(profile.get("filesystem_scopes"), f"{field}.filesystem_scopes")
    network_scopes = expect_mapping(profile.get("network_scopes"), f"{field}.network_scopes")
    process_permissions = expect_mapping(
        profile.get("process_execution_permissions"),
        f"{field}.process_execution_permissions",
    )
    package_permissions = expect_mapping(
        profile.get("package_manager_permissions"),
        f"{field}.package_manager_permissions",
    )
    resource_budgets = expect_mapping(profile.get("resource_budgets"), f"{field}.resource_budgets")

    return {
        "contract_version": CAPABILITY_PROFILE_VERSION,
        "capability_profile_id": expect_string(profile.get("capability_profile_id"), f"{field}.capability_profile_id"),
        "description": expect_string(profile.get("description"), f"{field}.description", allow_null=True),
        "filesystem_scopes": {
            "read": expect_string_list(filesystem_scopes.get("read", []), f"{field}.filesystem_scopes.read"),
            "write": expect_string_list(filesystem_scopes.get("write", []), f"{field}.filesystem_scopes.write"),
            "create": expect_string_list(filesystem_scopes.get("create", []), f"{field}.filesystem_scopes.create"),
            "deny": expect_string_list(filesystem_scopes.get("deny", []), f"{field}.filesystem_scopes.deny"),
        },
        "network_scopes": {
            "mode": expect_string(network_scopes.get("mode"), f"{field}.network_scopes.mode"),
            "allowed_domains": expect_string_list(
                network_scopes.get("allowed_domains", []),
                f"{field}.network_scopes.allowed_domains",
            ),
            "blocked_domains": expect_string_list(
                network_scopes.get("blocked_domains", []),
                f"{field}.network_scopes.blocked_domains",
            ),
        },
        "process_execution_permissions": {
            "allow_spawn": expect_bool(
                process_permissions.get("allow_spawn"),
                f"{field}.process_execution_permissions.allow_spawn",
            ),
            "allow_shell": expect_bool(
                process_permissions.get("allow_shell"),
                f"{field}.process_execution_permissions.allow_shell",
            ),
            "allow_python": expect_bool(
                process_permissions.get("allow_python"),
                f"{field}.process_execution_permissions.allow_python",
            ),
            "allowed_commands": expect_string_list(
                process_permissions.get("allowed_commands", []),
                f"{field}.process_execution_permissions.allowed_commands",
            ),
            "denied_commands": expect_string_list(
                process_permissions.get("denied_commands", []),
                f"{field}.process_execution_permissions.denied_commands",
            ),
        },
        "package_manager_permissions": {
            "allow_install": expect_bool(
                package_permissions.get("allow_install"),
                f"{field}.package_manager_permissions.allow_install",
            ),
            "allow_update": expect_bool(
                package_permissions.get("allow_update"),
                f"{field}.package_manager_permissions.allow_update",
            ),
            "allowed_managers": expect_string_list(
                package_permissions.get("allowed_managers", []),
                f"{field}.package_manager_permissions.allowed_managers",
            ),
            "blocked_managers": expect_string_list(
                package_permissions.get("blocked_managers", []),
                f"{field}.package_manager_permissions.blocked_managers",
            ),
        },
        "elevation_requirement": expect_string(
            profile.get("elevation_requirement"),
            f"{field}.elevation_requirement",
        ),
        "resource_budgets": {
            "wall_clock_seconds": resource_budgets.get("wall_clock_seconds"),
            "cpu_seconds": resource_budgets.get("cpu_seconds"),
            "memory_mb": resource_budgets.get("memory_mb"),
            "disk_mb": resource_budgets.get("disk_mb"),
        },
        "allowed_data_classes": expect_string_list(
            profile.get("allowed_data_classes", []),
            f"{field}.allowed_data_classes",
        ),
        "audit_class": expect_string(profile.get("audit_class"), f"{field}.audit_class", allow_null=True),
    }


def normalize_tool_entry(value: Any, *, extension_ids: set[str], index: int) -> dict[str, Any]:
    entry = expect_mapping(value, f"tool_entry[{index}]")
    if expect_string(entry.get("contract_version"), f"tool_entry[{index}].contract_version") != TOOL_ENTRY_VERSION:
        raise ValueError(f"tool_entry[{index}].contract_version must be '{TOOL_ENTRY_VERSION}'.")

    executor = expect_mapping(entry.get("executor"), f"tool_entry[{index}].executor")
    contracts = expect_mapping(entry.get("contracts"), f"tool_entry[{index}].contracts")
    invocation = expect_mapping(entry.get("invocation"), f"tool_entry[{index}].invocation")
    approval = expect_mapping(entry.get("approval"), f"tool_entry[{index}].approval")
    extension_id = expect_string(entry.get("extension_id"), f"tool_entry[{index}].extension_id", allow_null=True)

    if extension_id is not None and extension_id not in extension_ids:
        raise ValueError(f"tool_entry[{index}].extension_id references unknown extension '{extension_id}'.")

    normalized = {
        "contract_version": TOOL_ENTRY_VERSION,
        "tool_id": expect_string(entry.get("tool_id"), f"tool_entry[{index}].tool_id"),
        "display_name": expect_string(entry.get("display_name"), f"tool_entry[{index}].display_name"),
        "description": expect_string(entry.get("description"), f"tool_entry[{index}].description"),
        "surface_kind": expect_string(entry.get("surface_kind"), f"tool_entry[{index}].surface_kind"),
        "status": expect_string(entry.get("status"), f"tool_entry[{index}].status"),
        "owner": expect_string(entry.get("owner"), f"tool_entry[{index}].owner"),
        "extension_id": extension_id,
        "trust_class": expect_string(entry.get("trust_class"), f"tool_entry[{index}].trust_class"),
        "release_eligible": expect_bool(entry.get("release_eligible"), f"tool_entry[{index}].release_eligible"),
        "executor": {
            "component_id": expect_string(executor.get("component_id"), f"tool_entry[{index}].executor.component_id"),
            "entrypoint": expect_string(executor.get("entrypoint"), f"tool_entry[{index}].executor.entrypoint"),
            "mode": expect_string(executor.get("mode"), f"tool_entry[{index}].executor.mode"),
        },
        "contracts": {
            "request": expect_string(contracts.get("request"), f"tool_entry[{index}].contracts.request", allow_null=True),
            "receipt": expect_string(contracts.get("receipt"), f"tool_entry[{index}].contracts.receipt", allow_null=True),
        },
        "invocation": {
            "kind": expect_string(invocation.get("kind"), f"tool_entry[{index}].invocation.kind"),
            "action_operation": expect_string(
                invocation.get("action_operation"),
                f"tool_entry[{index}].invocation.action_operation",
                allow_null=True,
            ),
            "execution_mode": expect_string(
                invocation.get("execution_mode"),
                f"tool_entry[{index}].invocation.execution_mode",
                allow_null=True,
            ),
        },
        "capability_profile": normalize_capability_profile(
            entry.get("capability_profile"),
            f"tool_entry[{index}].capability_profile",
        ),
        "approval": {
            "required": expect_bool(approval.get("required"), f"tool_entry[{index}].approval.required"),
            "approver_kind": expect_string(
                approval.get("approver_kind"),
                f"tool_entry[{index}].approval.approver_kind",
                allow_null=True,
            ),
            "required_status": expect_string(
                approval.get("required_status"),
                f"tool_entry[{index}].approval.required_status",
                allow_null=True,
            ),
            "granted_scope_required": expect_bool(
                approval.get("granted_scope_required"),
                f"tool_entry[{index}].approval.granted_scope_required",
            ),
        },
    }

    if normalized["surface_kind"] == "builtin" and normalized["extension_id"] is not None:
        raise ValueError(f"tool_entry[{index}].extension_id must be null for builtin tools.")
    if normalized["surface_kind"] == "extension" and normalized["extension_id"] is None:
        raise ValueError(f"tool_entry[{index}] must declare extension_id for extension-backed tools.")
    if normalized["trust_class"] != "trusted" and normalized["release_eligible"]:
        raise ValueError(f"tool_entry[{index}] may not be release_eligible unless trust_class is trusted.")
    if normalized["invocation"]["kind"] == "execution":
        if normalized["contracts"]["request"] is None or normalized["contracts"]["receipt"] is None:
            raise ValueError(f"tool_entry[{index}] execution tools must declare request and receipt contracts.")
        if normalized["invocation"]["action_operation"] is None or normalized["invocation"]["execution_mode"] is None:
            raise ValueError(f"tool_entry[{index}] execution tools must declare action_operation and execution_mode.")
    return normalized


def normalize_extension_entry(value: Any, *, index: int) -> dict[str, Any]:
    entry = expect_mapping(value, f"extension_entry[{index}]")
    if expect_string(entry.get("contract_version"), f"extension_entry[{index}].contract_version") != EXTENSION_ENTRY_VERSION:
        raise ValueError(f"extension_entry[{index}].contract_version must be '{EXTENSION_ENTRY_VERSION}'.")
    normalized = {
        "contract_version": EXTENSION_ENTRY_VERSION,
        "extension_id": expect_string(entry.get("extension_id"), f"extension_entry[{index}].extension_id"),
        "display_name": expect_string(entry.get("display_name"), f"extension_entry[{index}].display_name"),
        "description": expect_string(entry.get("description"), f"extension_entry[{index}].description"),
        "owner": expect_string(entry.get("owner"), f"extension_entry[{index}].owner"),
        "status": expect_string(entry.get("status"), f"extension_entry[{index}].status"),
        "trust_class": expect_string(entry.get("trust_class"), f"extension_entry[{index}].trust_class"),
        "release_eligible": expect_bool(entry.get("release_eligible"), f"extension_entry[{index}].release_eligible"),
        "tool_ids": expect_string_list(entry.get("tool_ids", []), f"extension_entry[{index}].tool_ids"),
    }
    if normalized["trust_class"] != "trusted" and normalized["release_eligible"]:
        raise ValueError(f"extension_entry[{index}] may not be release_eligible unless trust_class is trusted.")
    return normalized


def load_tool_registry_bundle(*, root: Path | None = None) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    tool_registry_path = base_root / "docs" / "registry" / "ATLAS-TOOL-REGISTRY.json"
    extension_registry_path = base_root / "docs" / "registry" / "ATLAS-EXTENSION-REGISTRY.json"

    tool_registry = read_json_object(tool_registry_path)
    extension_registry = read_json_object(extension_registry_path)

    if expect_string(tool_registry.get("schema_version"), "tool_registry.schema_version") != TOOL_REGISTRY_VERSION:
        raise ValueError(f"tool_registry.schema_version must be '{TOOL_REGISTRY_VERSION}'.")
    if expect_string(extension_registry.get("schema_version"), "extension_registry.schema_version") != EXTENSION_REGISTRY_VERSION:
        raise ValueError(f"extension_registry.schema_version must be '{EXTENSION_REGISTRY_VERSION}'.")

    extension_entries_raw = extension_registry.get("entries", [])
    if not isinstance(extension_entries_raw, list):
        raise ValueError("extension_registry.entries must be an array.")
    extensions = [normalize_extension_entry(entry, index=index) for index, entry in enumerate(extension_entries_raw)]
    extension_ids = {entry["extension_id"] for entry in extensions}
    if len(extension_ids) != len(extensions):
        raise ValueError("extension_registry.entries contains duplicate extension_id values.")

    tool_entries_raw = tool_registry.get("entries", [])
    if not isinstance(tool_entries_raw, list):
        raise ValueError("tool_registry.entries must be an array.")
    tools = [normalize_tool_entry(entry, extension_ids=extension_ids, index=index) for index, entry in enumerate(tool_entries_raw)]
    tool_ids = {entry["tool_id"] for entry in tools}
    if len(tool_ids) != len(tools):
        raise ValueError("tool_registry.entries contains duplicate tool_id values.")

    by_tool_id = {entry["tool_id"]: entry for entry in tools}
    for extension in extensions:
        unknown_tools = [tool_id for tool_id in extension["tool_ids"] if tool_id not in by_tool_id]
        if unknown_tools:
            raise ValueError(
                f"extension '{extension['extension_id']}' references unknown tool ids: {', '.join(sorted(unknown_tools))}."
            )

    normalized_tool_registry = {
        "schema_version": TOOL_REGISTRY_VERSION,
        "kind": expect_string(tool_registry.get("kind"), "tool_registry.kind"),
        "entries": sorted(tools, key=lambda entry: entry["tool_id"]),
    }
    normalized_extension_registry = {
        "schema_version": EXTENSION_REGISTRY_VERSION,
        "kind": expect_string(extension_registry.get("kind"), "extension_registry.kind"),
        "entries": sorted(extensions, key=lambda entry: entry["extension_id"]),
    }
    registry_digest = stable_json_digest(
        {
            "tool_registry": normalized_tool_registry,
            "extension_registry": normalized_extension_registry,
        }
    )

    return {
        "schema_version": "atlas.tool-extension.registry.bundle.v1",
        "root_ref": atlas_relative(base_root, root=base_root),
        "tool_registry_ref": atlas_relative(tool_registry_path, root=base_root),
        "extension_registry_ref": atlas_relative(extension_registry_path, root=base_root),
        "tool_registry_digest": stable_json_digest(normalized_tool_registry),
        "extension_registry_digest": stable_json_digest(normalized_extension_registry),
        "registry_digest": registry_digest,
        "tool_count": len(normalized_tool_registry["entries"]),
        "extension_count": len(normalized_extension_registry["entries"]),
        "tool_registry": normalized_tool_registry,
        "extension_registry": normalized_extension_registry,
    }


def select_tool_entry(bundle: dict[str, Any], tool_id: str) -> dict[str, Any]:
    tools = bundle.get("tool_registry", {}).get("entries", [])
    for entry in tools:
        if isinstance(entry, dict) and entry.get("tool_id") == tool_id:
            return entry
    raise KeyError(f"Unknown tool_id '{tool_id}'.")


def select_extension_entry(bundle: dict[str, Any], extension_id: str) -> dict[str, Any]:
    extensions = bundle.get("extension_registry", {}).get("entries", [])
    for entry in extensions:
        if isinstance(entry, dict) and entry.get("extension_id") == extension_id:
            return entry
    raise KeyError(f"Unknown extension_id '{extension_id}'.")


def load_awareness_connector_toolset(*, root: Path | None = None) -> dict[str, Any]:
    bundle = load_tool_registry_bundle(root=root)
    tools: list[dict[str, Any]] = []
    for tool_id in CONNECTOR_TOOL_IDS:
        entry = select_tool_entry(bundle, tool_id)
        spec = CONNECTOR_TOOL_SPECS.get(tool_id)
        if spec is None:
            raise KeyError(f"Missing awareness connector tool spec for '{tool_id}'.")
        tools.append(
            {
                "name": tool_id,
                "description": spec["description"],
                "inputSchema": spec["inputSchema"],
                "tool_id": entry["tool_id"],
                "display_name": entry["display_name"],
                "owner": entry["owner"],
                "status": entry["status"],
                "surface_kind": entry["surface_kind"],
                "trust_class": entry["trust_class"],
                "release_eligible": entry["release_eligible"],
                "registry_digest": bundle["registry_digest"],
                "executor": entry["executor"],
                "capability_profile": entry["capability_profile"],
            }
        )
    toolset_body = {
        "schema_version": AWARENESS_CONNECTOR_SCHEMA_VERSION,
        "registry_digest": bundle["registry_digest"],
        "tools": [
            {
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": tool["inputSchema"],
            }
            for tool in tools
        ],
    }
    return {
        **toolset_body,
        "toolset_digest": stable_json_digest(toolset_body),
        "tools": tools,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Load and normalize the root-owned ATLAS tool and extension registries.",
    )
    parser.add_argument("--tool-id")
    parser.add_argument("--extension-id")
    args = parser.parse_args(argv)

    bundle = load_tool_registry_bundle(root=atlas_root())
    if args.tool_id:
        bundle["selected_tool"] = select_tool_entry(bundle, args.tool_id)
    if args.extension_id:
        bundle["selected_extension"] = select_extension_entry(bundle, args.extension_id)
    print(json.dumps(bundle, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
