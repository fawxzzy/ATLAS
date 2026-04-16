from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, load_stack_config, normalize_slashes

SCHEMA_VERSION = "atlas.topology.manifest.v1"
SCHEMA_ID = "atlas://architecture/lifeline-topology-manifest.schema.json"
HOSTNAME_MODES = {"default", "intentional", "optional", "none"}
APP_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ZONE_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$")
FORBIDDEN_HOSTNAME_TOKENS = ("machine", "host", "node", "provider", "placement", "instance")
REQUIRED_SOURCE_DOCS = {
    "docs/LIFELINE_HOSTING_TOPOLOGY.md",
    "docs/LIFELINE_ENV_AND_DOMAIN_CONTRACT.md",
}
REQUIRED_PATH_ROUTING_ALLOWLIST = {
    "docs",
    "admin",
    "internal-tools",
    "tightly-coupled-surfaces",
}
EXPECTED_NAMED_ENVIRONMENTS = {
    "dev": ("local", "none"),
    "preview": ("shared-preview", "default"),
    "prod": ("production", "default"),
}
EXPECTED_EPHEMERAL_ENVIRONMENTS = {
    "pr": ("pr-{number}", "^pr-[1-9][0-9]*$", "default"),
}
EXPECTED_RULES: dict[str, dict[str, str]] = {
    "prod": {
        "kind": "named",
        "environment": "prod",
        "hostname_template": "{app}.{zone}",
        "service_key_template": "{app}/prod",
        "default_hostname_mode": "default",
    },
    "preview": {
        "kind": "named",
        "environment": "preview",
        "hostname_template": "preview-{app}.{zone}",
        "service_key_template": "{app}/preview",
        "default_hostname_mode": "default",
    },
    "pr-preview": {
        "kind": "ephemeral",
        "environment_template": "pr-{number}",
        "hostname_template": "pr-{number}.{app}.{zone}",
        "service_key_template": "{app}/pr-{number}",
        "default_hostname_mode": "default",
    },
}


@dataclass
class ContractIssue:
    severity: str
    category: str
    path: str
    message: str
    details: dict[str, Any] | None = None


def atlas_repo_root() -> Path:
    return atlas_root() / "repos" / "fawxzzy-atlas"


def default_manifest_path() -> Path:
    return atlas_repo_root() / "docs" / "LIFELINE_TOPOLOGY_MANIFEST.json"


def default_schema_path() -> Path:
    return atlas_repo_root() / "docs" / "LIFELINE_TOPOLOGY_MANIFEST.schema.json"


def atlas_rel(path: Path) -> str:
    resolved = path.resolve()
    root = atlas_root().resolve()
    if resolved.is_relative_to(root):
        return normalize_slashes(str(resolved.relative_to(root)))
    return normalize_slashes(str(resolved))


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON payload must contain an object at the root.")
    return payload


def stable_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def validate_schema_definition(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("Schema $schema must target draft 2020-12.")
    if schema.get("$id") != SCHEMA_ID:
        errors.append(f"Schema $id must be '{SCHEMA_ID}'.")
    if schema.get("title") != "ATLAS Lifeline topology manifest":
        errors.append("Schema title must be 'ATLAS Lifeline topology manifest'.")
    if schema.get("type") != "object":
        errors.append("Schema root type must be object.")
    if schema.get("additionalProperties") is not False:
        errors.append("Schema root must disallow additionalProperties.")
    required = schema.get("required")
    if not isinstance(required, list):
        errors.append("Schema required must be an array.")
    else:
        missing = [
            field
            for field in [
                "schema_version",
                "source_docs",
                "identity",
                "apps",
                "zones",
                "environments",
                "hostname_rules",
                "routing",
                "placement",
            ]
            if field not in required
        ]
        if missing:
            errors.append(f"Schema required is missing fields: {', '.join(missing)}")
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        errors.append("Schema $defs must be an object.")
    else:
        for key in ["identity", "app", "zone", "environments", "hostname_rule", "routing", "placement"]:
            if key not in defs:
                errors.append(f"Schema $defs is missing '{key}'.")
    return errors


def validate_topology_manifest(
    manifest: dict[str, Any],
    *,
    manifest_path: Path,
    stack_config: dict[str, Any],
) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    manifest_ref = atlas_rel(manifest_path)
    repo_root = atlas_repo_root()

    if manifest.get("schema_version") != SCHEMA_VERSION:
        issues.append(
            ContractIssue(
                "error",
                "atlas-topology-manifest-version",
                manifest_ref,
                f"schema_version must be '{SCHEMA_VERSION}'.",
            )
        )

    source_docs = manifest.get("source_docs")
    if not isinstance(source_docs, list) or not source_docs:
        issues.append(
            ContractIssue(
                "error",
                "atlas-topology-source-docs",
                manifest_ref,
                "source_docs must be a non-empty array.",
            )
        )
        source_docs = []
    else:
        seen_docs: set[str] = set()
        for item in source_docs:
            if not isinstance(item, str) or not item.strip():
                issues.append(
                    ContractIssue(
                        "error",
                        "atlas-topology-source-docs",
                        manifest_ref,
                        "source_docs entries must be non-empty strings.",
                    )
                )
                continue
            normalized = normalize_slashes(item)
            if normalized in seen_docs:
                issues.append(
                    ContractIssue(
                        "error",
                        "atlas-topology-source-docs",
                        manifest_ref,
                        f"Duplicate source_docs entry: {normalized}",
                    )
                )
                continue
            seen_docs.add(normalized)
            if not (repo_root / normalized).exists():
                issues.append(
                    ContractIssue(
                        "error",
                        "atlas-topology-source-doc-missing",
                        manifest_ref,
                        f"Referenced source doc does not exist: {normalized}",
                    )
                )
        missing_required_docs = sorted(REQUIRED_SOURCE_DOCS - set(normalize_slashes(item) for item in source_docs if isinstance(item, str)))
        for missing_doc in missing_required_docs:
            issues.append(
                ContractIssue(
                    "error",
                    "atlas-topology-source-doc-missing",
                    manifest_ref,
                    f"Required doctrine source doc is missing from source_docs: {missing_doc}",
                )
            )

    identity = manifest.get("identity")
    if not isinstance(identity, dict):
        issues.append(
            ContractIssue(
                "error",
                "atlas-topology-identity",
                manifest_ref,
                "identity must be an object.",
            )
        )
    else:
        expected_identity = {
            "service_key_template": "{app}/{environment}",
            "stable_public_unit": "app/environment",
            "machine_identity_visibility": "hidden",
            "routing_default": "subdomain-first",
        }
        for key, expected_value in expected_identity.items():
            if identity.get(key) != expected_value:
                issues.append(
                    ContractIssue(
                        "error",
                        "atlas-topology-identity",
                        manifest_ref,
                        f"identity.{key} must be '{expected_value}'.",
                    )
                )

    zones = manifest.get("zones")
    zone_names: set[str] = set()
    if not isinstance(zones, list) or not zones:
        issues.append(
            ContractIssue(
                "error",
                "atlas-topology-zones",
                manifest_ref,
                "zones must be a non-empty array.",
            )
        )
    else:
        for index, zone in enumerate(zones):
            path = f"{manifest_ref}#zones[{index}]"
            if not isinstance(zone, dict):
                issues.append(ContractIssue("error", "atlas-topology-zones", path, "Zone entry must be an object."))
                continue
            zone_name = str(zone.get("zone", ""))
            if not ZONE_PATTERN.fullmatch(zone_name):
                issues.append(ContractIssue("error", "atlas-topology-zone-name", path, f"Invalid zone name '{zone_name}'."))
            elif zone_name in zone_names:
                issues.append(ContractIssue("error", "atlas-topology-zone-name", path, f"Duplicate zone '{zone_name}'."))
            else:
                zone_names.add(zone_name)

    repo_registry = stack_config.get("repo_registry", {})
    known_repo_ids = {str(repo_id) for repo_id in repo_registry} if isinstance(repo_registry, dict) else set()
    apps = manifest.get("apps")
    app_ids: set[str] = set()
    if not isinstance(apps, list) or not apps:
        issues.append(
            ContractIssue(
                "error",
                "atlas-topology-apps",
                manifest_ref,
                "apps must be a non-empty array.",
            )
        )
        apps = []
    else:
        for index, app in enumerate(apps):
            path = f"{manifest_ref}#apps[{index}]"
            if not isinstance(app, dict):
                issues.append(ContractIssue("error", "atlas-topology-apps", path, "App entry must be an object."))
                continue
            app_id = str(app.get("app_id", ""))
            repo_id = str(app.get("repo_id", ""))
            surface = str(app.get("surface", ""))
            default_zone = str(app.get("default_zone", ""))
            if not APP_ID_PATTERN.fullmatch(app_id):
                issues.append(ContractIssue("error", "atlas-topology-app-id", path, f"Invalid app_id '{app_id}'."))
            elif app_id in app_ids:
                issues.append(ContractIssue("error", "atlas-topology-app-id", path, f"Duplicate app_id '{app_id}'."))
            else:
                app_ids.add(app_id)
            if not APP_ID_PATTERN.fullmatch(repo_id):
                issues.append(ContractIssue("error", "atlas-topology-repo-id", path, f"Invalid repo_id '{repo_id}'."))
            elif repo_id not in known_repo_ids:
                issues.append(ContractIssue("error", "atlas-topology-repo-id", path, f"repo_id '{repo_id}' is not present in stack.yaml repo_registry."))
            if default_zone and default_zone not in zone_names:
                issues.append(ContractIssue("error", "atlas-topology-app-zone", path, f"default_zone '{default_zone}' is not declared in zones."))
            if surface not in {"product", "operator"}:
                issues.append(ContractIssue("error", "atlas-topology-app-surface", path, f"Unsupported surface '{surface}'."))
            for field in ["prod_hostname_mode", "preview_hostname_mode", "pr_preview_hostname_mode"]:
                value = str(app.get(field, ""))
                if value not in HOSTNAME_MODES:
                    issues.append(ContractIssue("error", "atlas-topology-hostname-mode", path, f"{field} must be one of: {', '.join(sorted(HOSTNAME_MODES))}."))
            if surface == "product":
                for field in ["prod_hostname_mode", "preview_hostname_mode", "pr_preview_hostname_mode"]:
                    if app.get(field) != "default":
                        issues.append(ContractIssue("error", "atlas-topology-product-hostname-mode", path, f"Product apps must keep {field} set to 'default'."))
            if app_id == "lifeline":
                if app.get("prod_hostname_mode") != "intentional":
                    issues.append(ContractIssue("error", "atlas-topology-lifeline-mode", path, "lifeline prod_hostname_mode must be 'intentional'."))
                if app.get("preview_hostname_mode") != "none" or app.get("pr_preview_hostname_mode") != "none":
                    issues.append(ContractIssue("error", "atlas-topology-lifeline-mode", path, "lifeline preview and PR preview hostname modes must stay 'none'."))

    environments = manifest.get("environments")
    if not isinstance(environments, dict):
        issues.append(ContractIssue("error", "atlas-topology-environments", manifest_ref, "environments must be an object."))
    else:
        named = environments.get("named")
        named_map: dict[str, tuple[str, str]] = {}
        if not isinstance(named, list):
            issues.append(ContractIssue("error", "atlas-topology-named-environments", manifest_ref, "environments.named must be an array."))
        else:
            for index, item in enumerate(named):
                path = f"{manifest_ref}#environments.named[{index}]"
                if not isinstance(item, dict):
                    issues.append(ContractIssue("error", "atlas-topology-named-environments", path, "Named environment entry must be an object."))
                    continue
                name = str(item.get("name", ""))
                named_map[name] = (str(item.get("kind", "")), str(item.get("public_hostname_mode", "")))
            for env_name, expected in EXPECTED_NAMED_ENVIRONMENTS.items():
                actual = named_map.get(env_name)
                if actual != expected:
                    issues.append(ContractIssue("error", "atlas-topology-named-environments", manifest_ref, f"Named environment '{env_name}' must be {expected!r}, got {actual!r}."))

        ephemeral = environments.get("ephemeral")
        ephemeral_map: dict[str, tuple[str, str, str]] = {}
        if not isinstance(ephemeral, list):
            issues.append(ContractIssue("error", "atlas-topology-ephemeral-environments", manifest_ref, "environments.ephemeral must be an array."))
        else:
            for index, item in enumerate(ephemeral):
                path = f"{manifest_ref}#environments.ephemeral[{index}]"
                if not isinstance(item, dict):
                    issues.append(ContractIssue("error", "atlas-topology-ephemeral-environments", path, "Ephemeral environment entry must be an object."))
                    continue
                kind = str(item.get("kind", ""))
                ephemeral_map[kind] = (
                    str(item.get("environment_template", "")),
                    str(item.get("match", "")),
                    str(item.get("public_hostname_mode", "")),
                )
                try:
                    re.compile(str(item.get("match", "")))
                except re.error as exc:
                    issues.append(ContractIssue("error", "atlas-topology-ephemeral-regex", path, f"Invalid match regex: {exc}"))
            for kind, expected in EXPECTED_EPHEMERAL_ENVIRONMENTS.items():
                actual = ephemeral_map.get(kind)
                if actual != expected:
                    issues.append(ContractIssue("error", "atlas-topology-ephemeral-environments", manifest_ref, f"Ephemeral environment '{kind}' must be {expected!r}, got {actual!r}."))

    hostname_rules = manifest.get("hostname_rules")
    if not isinstance(hostname_rules, list) or not hostname_rules:
        issues.append(ContractIssue("error", "atlas-topology-hostname-rules", manifest_ref, "hostname_rules must be a non-empty array."))
    else:
        rules_by_id: dict[str, dict[str, Any]] = {}
        for index, rule in enumerate(hostname_rules):
            path = f"{manifest_ref}#hostname_rules[{index}]"
            if not isinstance(rule, dict):
                issues.append(ContractIssue("error", "atlas-topology-hostname-rules", path, "Hostname rule entry must be an object."))
                continue
            rule_id = str(rule.get("rule_id", ""))
            if rule_id in rules_by_id:
                issues.append(ContractIssue("error", "atlas-topology-hostname-rules", path, f"Duplicate hostname rule '{rule_id}'."))
                continue
            rules_by_id[rule_id] = rule
            template = str(rule.get("hostname_template", ""))
            lowered = template.lower()
            if any(token in lowered for token in FORBIDDEN_HOSTNAME_TOKENS):
                issues.append(ContractIssue("error", "atlas-topology-hostname-template", path, "Hostname templates must not encode machine or placement identity."))
            if "/" in template:
                issues.append(ContractIssue("error", "atlas-topology-hostname-template", path, "Hostname templates must not contain path separators."))
            if "{app}" in str(rule.get("service_key_template", "")) and "{environment}" in str(rule.get("service_key_template", "")):
                issues.append(ContractIssue("error", "atlas-topology-service-key-template", path, "Hostname rules must target a concrete environment or environment template, not '{environment}'."))
        for rule_id, expected in EXPECTED_RULES.items():
            actual = rules_by_id.get(rule_id)
            if not isinstance(actual, dict):
                issues.append(ContractIssue("error", "atlas-topology-hostname-rules", manifest_ref, f"Missing required hostname rule '{rule_id}'."))
                continue
            for key, expected_value in expected.items():
                if str(actual.get(key, "")) != expected_value:
                    issues.append(ContractIssue("error", "atlas-topology-hostname-rules", manifest_ref, f"Hostname rule '{rule_id}' field '{key}' must be '{expected_value}'."))
        lifeline_rule = rules_by_id.get("lifeline-prod")
        if not isinstance(lifeline_rule, dict):
            issues.append(ContractIssue("error", "atlas-topology-hostname-rules", manifest_ref, "Missing required hostname rule 'lifeline-prod'."))
        else:
            expected_lifeline = {
                "kind": "named",
                "environment": "prod",
                "app_id": "lifeline",
                "hostname_template": "lifeline.{zone}",
                "service_key_template": "lifeline/prod",
                "default_hostname_mode": "intentional",
            }
            for key, expected_value in expected_lifeline.items():
                if str(lifeline_rule.get(key, "")) != expected_value:
                    issues.append(ContractIssue("error", "atlas-topology-hostname-rules", manifest_ref, f"Hostname rule 'lifeline-prod' field '{key}' must be '{expected_value}'."))

    routing = manifest.get("routing")
    if not isinstance(routing, dict):
        issues.append(ContractIssue("error", "atlas-topology-routing", manifest_ref, "routing must be an object."))
    else:
        if routing.get("default_strategy") != "subdomain-first":
            issues.append(ContractIssue("error", "atlas-topology-routing", manifest_ref, "routing.default_strategy must be 'subdomain-first'."))
        if routing.get("path_routing_default") != "disallowed-for-distinct-apps":
            issues.append(ContractIssue("error", "atlas-topology-routing", manifest_ref, "routing.path_routing_default must be 'disallowed-for-distinct-apps'."))
        allowed_for = routing.get("path_routing_allowed_for")
        if not isinstance(allowed_for, list):
            issues.append(ContractIssue("error", "atlas-topology-routing", manifest_ref, "routing.path_routing_allowed_for must be an array."))
        else:
            missing = sorted(REQUIRED_PATH_ROUTING_ALLOWLIST - {str(item) for item in allowed_for})
            if missing:
                issues.append(ContractIssue("error", "atlas-topology-routing", manifest_ref, f"routing.path_routing_allowed_for is missing: {', '.join(missing)}"))
        if routing.get("gateway_resolves_service_before_placement") is not True:
            issues.append(ContractIssue("error", "atlas-topology-routing", manifest_ref, "routing.gateway_resolves_service_before_placement must be true."))
        if routing.get("tls_termination") != "gateway":
            issues.append(ContractIssue("error", "atlas-topology-routing", manifest_ref, "routing.tls_termination must be 'gateway'."))
        if routing.get("cookie_boundary") != "application-hostname":
            issues.append(ContractIssue("error", "atlas-topology-routing", manifest_ref, "routing.cookie_boundary must be 'application-hostname'."))
        hidden = routing.get("public_hostname_must_hide")
        if not isinstance(hidden, list):
            issues.append(ContractIssue("error", "atlas-topology-routing", manifest_ref, "routing.public_hostname_must_hide must be an array."))
        else:
            missing = [field for field in ["machine_id", "provider_instance_id", "placement"] if field not in hidden]
            if missing:
                issues.append(ContractIssue("error", "atlas-topology-routing", manifest_ref, f"routing.public_hostname_must_hide is missing: {', '.join(missing)}"))

    placement = manifest.get("placement")
    if not isinstance(placement, dict):
        issues.append(ContractIssue("error", "atlas-topology-placement", manifest_ref, "placement must be an object."))
    else:
        if placement.get("stable_contract_unit") != "app/environment":
            issues.append(ContractIssue("error", "atlas-topology-placement", manifest_ref, "placement.stable_contract_unit must be 'app/environment'."))
        if placement.get("public_hostname_changes_with_placement") is not False:
            issues.append(ContractIssue("error", "atlas-topology-placement", manifest_ref, "placement.public_hostname_changes_with_placement must be false."))
        if placement.get("default_topology") != "shared-gateway-isolated-services":
            issues.append(ContractIssue("error", "atlas-topology-placement", manifest_ref, "placement.default_topology must be 'shared-gateway-isolated-services'."))
        stage_progression = placement.get("stage_progression")
        expected_stages = [
            "single-host-many-services",
            "shared-gateway-plus-worker-hosts",
            "lifeline-controlled-multi-host",
        ]
        if stage_progression != expected_stages:
            issues.append(ContractIssue("error", "atlas-topology-placement", manifest_ref, f"placement.stage_progression must be {expected_stages!r}."))
        exclusions = placement.get("lifeline_v1_exclusions")
        expected_exclusions = [
            "hosted-control-plane",
            "reverse-proxy-ownership",
            "domain-automation",
            "tls-automation",
            "multi-node-orchestration",
        ]
        if exclusions != expected_exclusions:
            issues.append(ContractIssue("error", "atlas-topology-placement", manifest_ref, f"placement.lifeline_v1_exclusions must be {expected_exclusions!r}."))

    return issues


def validate_contract_files(
    *,
    manifest_path: Path | None = None,
    schema_path: Path | None = None,
    stack_file: Path | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[ContractIssue]]:
    manifest_target = (manifest_path or default_manifest_path()).resolve()
    schema_target = (schema_path or default_schema_path()).resolve()
    stack_target = (stack_file or (atlas_root() / "stack.yaml")).resolve()
    issues: list[ContractIssue] = []
    manifest_payload: dict[str, Any] | None = None
    schema_payload: dict[str, Any] | None = None

    if not schema_target.exists():
        issues.append(ContractIssue("error", "atlas-topology-schema-missing", atlas_rel(schema_target), "Topology schema file is missing."))
    else:
        try:
            schema_payload = load_json(schema_target)
        except Exception as exc:
            issues.append(ContractIssue("error", "atlas-topology-schema-invalid", atlas_rel(schema_target), f"Topology schema could not be loaded: {exc}"))
        if isinstance(schema_payload, dict):
            for message in validate_schema_definition(schema_payload):
                issues.append(ContractIssue("error", "atlas-topology-schema-invalid", atlas_rel(schema_target), message))

    if not manifest_target.exists():
        issues.append(ContractIssue("error", "atlas-topology-manifest-missing", atlas_rel(manifest_target), "Topology manifest file is missing."))
    else:
        try:
            manifest_payload = load_json(manifest_target)
        except Exception as exc:
            issues.append(ContractIssue("error", "atlas-topology-manifest-invalid", atlas_rel(manifest_target), f"Topology manifest could not be loaded: {exc}"))

    if isinstance(manifest_payload, dict):
        try:
            stack_config = load_stack_config(stack_target)
        except Exception as exc:
            issues.append(ContractIssue("error", "atlas-topology-stack-config", atlas_rel(stack_target), f"stack.yaml could not be loaded while validating topology manifest: {exc}"))
        else:
            issues.extend(validate_topology_manifest(manifest_payload, manifest_path=manifest_target, stack_config=stack_config))

    return schema_payload, manifest_payload, issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the Atlas-owned machine-readable topology manifest.")
    parser.add_argument("--manifest-file", default=str(default_manifest_path()))
    parser.add_argument("--schema-file", default=str(default_schema_path()))
    parser.add_argument("--stack-file", default=str(atlas_root() / "stack.yaml"))
    args = parser.parse_args(argv)

    schema_payload, manifest_payload, issues = validate_contract_files(
        manifest_path=Path(args.manifest_file),
        schema_path=Path(args.schema_file),
        stack_file=Path(args.stack_file),
    )

    output = {
        "ok": not issues,
        "manifest_ref": atlas_rel(Path(args.manifest_file)),
        "schema_ref": atlas_rel(Path(args.schema_file)),
        "stack_file_ref": atlas_rel(Path(args.stack_file)),
        "manifest_digest": stable_digest(manifest_payload) if isinstance(manifest_payload, dict) else None,
        "schema_digest": stable_digest(schema_payload) if isinstance(schema_payload, dict) else None,
        "issue_count": len(issues),
        "issues": [asdict(issue) for issue in issues],
    }
    print(json.dumps(output, indent=2))
    return 0 if not issues else 2


if __name__ == "__main__":
    raise SystemExit(main())
