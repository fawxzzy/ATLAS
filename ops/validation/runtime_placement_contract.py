from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_SCHEMA_VALIDATION_IMPORT_ERROR: str | None = None
try:
    from ops.atlas.ui_standards.validate import (
        validate_json_schema as _validate_json_schema,
        validate_schema_definition as _validate_schema_definition,
    )
except Exception as exc:
    _validate_json_schema = None
    _validate_schema_definition = None
    _SCHEMA_VALIDATION_IMPORT_ERROR = str(exc)

REGISTRY_REF = Path("docs/registry/ATLAS-RUNTIME-PLACEMENT-REGISTRY.v1.json")
SCHEMA_REF = Path("schemas/atlas.runtime-placement.registry.v1.json")
LANE_REGISTRY_REF = Path("docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json")
MARKER_BOOK_REF = Path("docs/atlas-book/02-lanes-and-markers.md")
SCHEMA_ID = "atlas://schemas/atlas.runtime-placement.registry.v1.json"
SCHEMA_TITLE = "ATLAS runtime placement registry v1"

PLACEMENT_TYPES = (
    "no_server/on_demand",
    "local_persistent",
    "local_scheduled",
    "Vercel",
    "Supabase",
    "GitHub Actions",
    "hybrid",
    "owner_lane",
)
PUBLIC_PLACEMENTS = frozenset({"Vercel", "Supabase", "GitHub Actions", "hybrid"})
DO_NOT_DEPLOY = (
    "atlas-root",
    "_stack",
    "playbook-observer",
    "lifeline",
    "cortex-artifacts",
    "atlas-book",
    "socials-os",
    "playbook-demo",
    "external-model-sidecar",
    "lifeline-pilot-caddy",
)
ACTIVATION_SEQUENCE = (
    "playbook-bootstrap-foreground-observer-proof",
    "lifeline-bootstrap-state-contract",
    "lifeline-supervised-restart",
    "lifeline-logon-restore",
    "stack-single-scheduled-worker",
    "cortex-event-refresh",
    "discordos-interaction-first-reliability-review",
    "owner-export-integration",
)
STEP_STATUSES = frozenset({"accepted", "pending", "blocked", "unknown"})
MARKER_SPECS: dict[str, dict[str, Any]] = {
    "lane-runtime-activation-readiness": {
        "title": "Runtime Activation Readiness",
        "denominator": 8,
        "measurement_unit": "binary activation gate",
        "units": (
            "placement-contract",
            "playbook-build",
            "observer-foreground-health",
            "lifeline-build-doctor",
            "lifeline-state-placement",
            "lifeline-supervision-restart",
            "logon-restore",
            "stack-single-worker-proof",
        ),
    },
    "lane-runtime-correlation-reliability": {
        "title": "Runtime Correlation Reliability",
        "denominator": 5,
        "measurement_unit": "correlated runtime scenario",
        "units": (
            "successful-task",
            "failed-task",
            "duplicate-task",
            "interrupted-restarted-task",
            "stale-receipt-rejection",
        ),
    },
    "lane-operator-surface-adoption": {
        "title": "Operator Surface Adoption",
        "denominator": 4,
        "measurement_unit": "non-duplicative operator role",
        "units": (
            "foundation-portfolio",
            "playbook-operations",
            "atlas-book-doctrine",
            "stack-action-routing",
        ),
    },
}
COMPONENT_REQUIRED_FIELDS = (
    "id",
    "runtime_responsibility",
    "authority_owner",
    "implemented_surface",
    "intended_placement",
    "current_availability",
    "consumer",
    "lifecycle",
    "persistence",
    "secrets_boundary",
    "port",
    "availability_target",
    "failure_modes",
    "activation_deployment_gate",
    "evidence_refs",
)


@dataclass(frozen=True)
class RuntimePlacementIssue:
    severity: str
    category: str
    path: str
    message: str
    details: dict[str, Any] | None = None


def _issue(category: str, path: str, message: str, **details: Any) -> RuntimePlacementIssue:
    return RuntimePlacementIssue("error", category, path, message, details or None)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def validate_registry_schema_contract(
    registry: dict[str, Any],
    schema: dict[str, Any],
) -> list[RuntimePlacementIssue]:
    schema_path = SCHEMA_REF.as_posix()
    registry_path = REGISTRY_REF.as_posix()
    if _validate_json_schema is None or _validate_schema_definition is None:
        return [
            _issue(
                "runtime-placement-jsonschema-unavailable",
                schema_path,
                "The shared Draft 2020-12 schema-validation capability is unavailable.",
                import_error=_SCHEMA_VALIDATION_IMPORT_ERROR,
            )
        ]

    try:
        schema_errors = _validate_schema_definition(
            schema,
            expected_id=SCHEMA_ID,
            expected_title=SCHEMA_TITLE,
        )
    except Exception as exc:
        schema_errors = [f"Schema definition validation raised {type(exc).__name__}: {exc}"]
    if schema_errors:
        return [
            _issue(
                "runtime-placement-schema-invalid",
                schema_path,
                "Runtime placement schema definition is invalid.",
                error_count=len(schema_errors),
                errors=schema_errors,
            )
        ]

    try:
        registry_errors = _validate_json_schema(registry, schema)
    except Exception as exc:
        registry_errors = [f"Registry schema validation raised {type(exc).__name__}: {exc}"]
    if registry_errors:
        return [
            _issue(
                "runtime-placement-registry-schema-invalid",
                registry_path,
                "Runtime placement registry does not conform to its Draft 2020-12 schema.",
                error_count=len(registry_errors),
                errors=registry_errors,
            )
        ]
    return []


def _non_empty_strings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def _machine_specific_path(value: str) -> bool:
    return bool(
        re.search(r"^[A-Za-z]:[\\/]", value)
        or re.search(r"(?:^|/)(?:Users|home)/[^/]+/", value.replace("\\", "/"))
    )


def _relative_evidence_context_available(root: Path, evidence_ref: str) -> bool:
    relative_ref = evidence_ref.split("#", 1)[0].split("@", 1)[0].replace("\\", "/")
    parts = PurePosixPath(relative_ref).parts
    if len(parts) >= 2 and parts[0] == "repos":
        return (root / parts[0] / parts[1]).exists()
    if parts and parts[0] == "runtime":
        context_parts = parts[:2] if len(parts) >= 2 else parts[:1]
        return root.joinpath(*context_parts).exists()
    return True


def _validate_evidence_refs(evidence_refs: Any, path: str, root: Path) -> list[RuntimePlacementIssue]:
    if not _non_empty_strings(evidence_refs):
        return []
    issues: list[RuntimePlacementIssue] = []
    for evidence_ref in evidence_refs:
        if _machine_specific_path(evidence_ref):
            issues.append(_issue("runtime-placement-machine-path", path, "Evidence refs must not contain machine-specific absolute paths.", evidence_ref=evidence_ref))
        if "://" not in evidence_ref and not evidence_ref.startswith("git:"):
            evidence_path = root / evidence_ref.split("#", 1)[0].split("@", 1)[0]
            if _relative_evidence_context_available(root, evidence_ref) and not evidence_path.exists():
                issues.append(_issue("runtime-placement-evidence-missing", path, "Relative evidence ref does not exist.", evidence_ref=evidence_ref))
    return issues


def _all_lane_records(lane_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for section in ("lanes", "backlog_candidates"):
        values = lane_payload.get(section)
        if not isinstance(values, list):
            continue
        for value in values:
            if isinstance(value, dict) and isinstance(value.get("id"), str):
                records[value["id"]] = value
    return records


def validate_runtime_placement_payloads(
    registry: dict[str, Any],
    lane_registry: dict[str, Any],
    marker_book: str,
    *,
    root: Path = ROOT,
) -> list[RuntimePlacementIssue]:
    issues: list[RuntimePlacementIssue] = []
    registry_path = str(REGISTRY_REF).replace("\\", "/")

    if registry.get("schema_version") != "atlas.runtime-placement.registry.v1":
        issues.append(_issue("runtime-placement-schema", registry_path, "Unexpected runtime placement schema_version."))
    if registry.get("kind") != "atlas-runtime-placement-registry":
        issues.append(_issue("runtime-placement-kind", registry_path, "Unexpected runtime placement kind."))
    if registry.get("authority") != "ATLAS root governance":
        issues.append(_issue("runtime-placement-authority", registry_path, "Runtime placement authority must remain ATLAS root governance."))

    placement_types = registry.get("placement_types")
    if placement_types != list(PLACEMENT_TYPES):
        issues.append(
            _issue(
                "runtime-placement-types",
                f"{registry_path}#placement_types",
                "Placement types must remain the exact ordered eight-type contract.",
                expected=list(PLACEMENT_TYPES),
                actual=placement_types,
            )
        )

    components = registry.get("components")
    if not isinstance(components, list) or not components:
        issues.append(_issue("runtime-placement-components", f"{registry_path}#components", "Components must be a non-empty array."))
        components = []

    component_ids: set[str] = set()
    responsibilities: set[str] = set()
    component_index: dict[str, dict[str, Any]] = {}
    used_placements: set[str] = set()
    for index, component in enumerate(components):
        path = f"{registry_path}#components[{index}]"
        if not isinstance(component, dict):
            issues.append(_issue("runtime-placement-component-shape", path, "Component must be an object."))
            continue
        missing = [field for field in COMPONENT_REQUIRED_FIELDS if field not in component]
        if missing:
            issues.append(_issue("runtime-placement-component-fields", path, "Component is missing required fields.", missing=missing))
            continue

        component_id = component.get("id")
        responsibility = component.get("runtime_responsibility")
        if not isinstance(component_id, str) or not component_id.strip():
            issues.append(_issue("runtime-placement-component-id", path, "Component id must be a non-empty string."))
        elif component_id in component_ids:
            issues.append(_issue("runtime-placement-component-id", path, "Component id must be unique.", component_id=component_id))
        else:
            component_ids.add(component_id)
            component_index[component_id] = component
        if not isinstance(responsibility, str) or not responsibility.strip():
            issues.append(_issue("runtime-placement-responsibility", path, "Runtime responsibility must be a non-empty string."))
        elif responsibility in responsibilities:
            issues.append(_issue("runtime-placement-responsibility", path, "Runtime responsibility must be unique.", responsibility=responsibility))
        else:
            responsibilities.add(responsibility)

        placement = component.get("intended_placement")
        if placement not in PLACEMENT_TYPES:
            issues.append(_issue("runtime-placement-value", path, "Component uses an unsupported placement.", placement=placement))
        else:
            used_placements.add(placement)

        for field in ("implemented_surface", "consumer", "failure_modes", "evidence_refs"):
            if not _non_empty_strings(component.get(field)):
                issues.append(_issue("runtime-placement-component-list", f"{path}.{field}", f"{field} must be a non-empty string array."))

        availability = component.get("current_availability")
        if not isinstance(availability, dict) or not isinstance(availability.get("state"), str) or not _non_empty_strings(availability.get("proof")):
            issues.append(_issue("runtime-placement-availability", f"{path}.current_availability", "Current availability must record state, observed_at, and non-empty proof."))
        elif not isinstance(availability.get("observed_at"), str) or not availability["observed_at"].endswith("Z"):
            issues.append(_issue("runtime-placement-availability", f"{path}.current_availability.observed_at", "Availability observed_at must be UTC and end in Z."))

        persistence = component.get("persistence")
        if not isinstance(persistence, dict) or set(persistence) != {"mode", "path"} or not isinstance(persistence.get("mode"), str):
            issues.append(_issue("runtime-placement-persistence", f"{path}.persistence", "Persistence must contain exactly mode and path."))

        ports = component.get("port")
        if ports is not None and (
            not isinstance(ports, list)
            or len(ports) != len(set(ports))
            or any(not isinstance(port, int) or port < 1 or port > 65535 for port in ports)
        ):
            issues.append(_issue("runtime-placement-port", f"{path}.port", "Port must be null or a unique array of valid TCP port integers."))

        issues.extend(_validate_evidence_refs(component.get("evidence_refs"), f"{path}.evidence_refs", root))

    if used_placements != set(PLACEMENT_TYPES):
        issues.append(
            _issue(
                "runtime-placement-type-coverage",
                f"{registry_path}#components",
                "Every placement type must be represented by at least one component.",
                missing=sorted(set(PLACEMENT_TYPES) - used_placements),
            )
        )

    do_not_deploy = registry.get("do_not_deploy")
    if do_not_deploy != list(DO_NOT_DEPLOY):
        issues.append(_issue("runtime-placement-do-not-deploy", f"{registry_path}#do_not_deploy", "Do-not-deploy list must remain exact and ordered.", expected=list(DO_NOT_DEPLOY), actual=do_not_deploy))
    for component_id in DO_NOT_DEPLOY:
        component = component_index.get(component_id)
        if component is None:
            issues.append(_issue("runtime-placement-do-not-deploy", f"{registry_path}#do_not_deploy", "Do-not-deploy component is missing from components.", component_id=component_id))
        elif component.get("intended_placement") in PUBLIC_PLACEMENTS:
            issues.append(_issue("runtime-placement-public-hosting-forbidden", f"{registry_path}#components/{component_id}", "Do-not-deploy component must not be assigned public hosting.", placement=component.get("intended_placement")))

    activation_sequence = registry.get("activation_sequence")
    if activation_sequence != list(ACTIVATION_SEQUENCE):
        issues.append(
            _issue(
                "runtime-placement-activation-sequence",
                f"{registry_path}#activation_sequence",
                "The v1 activation_sequence must remain the exact ordered string-ID array.",
                expected=list(ACTIVATION_SEQUENCE),
                actual=activation_sequence,
            )
        )

    activation_steps = registry.get("activation_steps")
    expected_selector: str | None = None
    if not isinstance(activation_steps, list):
        issues.append(_issue("runtime-placement-activation-steps", f"{registry_path}#activation_steps", "Structured activation_steps must be an array."))
    else:
        ids = [step.get("id") if isinstance(step, dict) else None for step in activation_steps]
        orders = [step.get("order") if isinstance(step, dict) else None for step in activation_steps]
        if ids != list(ACTIVATION_SEQUENCE) or orders != list(range(1, 9)):
            issues.append(_issue("runtime-placement-activation-steps", f"{registry_path}#activation_steps", "Structured activation steps must map one-to-one and in order to the frozen v1 activation_sequence.", expected=list(ACTIVATION_SEQUENCE), actual=ids))
        unresolved_seen = False
        packet_owners: dict[str, str | None] = {}
        for step_index, step in enumerate(activation_steps):
            step_path = f"{registry_path}#activation_steps[{step_index}]"
            if not isinstance(step, dict):
                issues.append(_issue("runtime-placement-activation-step-shape", step_path, "Activation step must be an object."))
                unresolved_seen = True
                continue
            packet = step.get("packet")
            status = step.get("status")
            if not isinstance(packet, str) or not packet.strip():
                issues.append(_issue("runtime-placement-activation-step-packet", step_path, "Activation step packet must be a non-empty string."))
            elif packet in packet_owners:
                issues.append(
                    _issue(
                        "runtime-placement-activation-step-packet-duplicate",
                        step_path,
                        "Activation step packet names must be unique so the public selector resolves unambiguously.",
                        packet=packet,
                        first_step_id=packet_owners[packet],
                        duplicate_step_id=step.get("id"),
                    )
                )
            else:
                packet_owners[packet] = step.get("id")
            if status not in STEP_STATUSES:
                issues.append(_issue("runtime-placement-activation-step-status", step_path, "Activation step status must preserve accepted, pending, blocked, or unknown distinctly.", actual=status))
            if not _non_empty_strings(step.get("evidence_refs")):
                issues.append(_issue("runtime-placement-activation-step-evidence", step_path, "Activation step must cite non-empty structured evidence refs."))
            else:
                issues.extend(_validate_evidence_refs(step.get("evidence_refs"), f"{step_path}.evidence_refs", root))

            if status == "accepted":
                if unresolved_seen:
                    issues.append(_issue("runtime-placement-activation-accepted-prefix", step_path, "Accepted activation steps must form a contiguous prefix of the frozen sequence."))
            else:
                unresolved_seen = True
                if expected_selector is None and isinstance(packet, str) and packet.strip():
                    expected_selector = packet

    marker_lanes = registry.get("marker_lanes")
    marker_index = {
        marker.get("id"): marker
        for marker in marker_lanes
        if isinstance(marker_lanes, list) and isinstance(marker, dict) and isinstance(marker.get("id"), str)
    } if isinstance(marker_lanes, list) else {}
    lane_records = _all_lane_records(lane_registry)
    for marker_id, spec in MARKER_SPECS.items():
        marker = marker_index.get(marker_id)
        marker_path = f"{registry_path}#marker_lanes/{marker_id}"
        if marker is None:
            issues.append(_issue("runtime-placement-marker-missing", marker_path, "Required runtime marker contract is missing."))
            continue
        unit_ids = [unit.get("id") for unit in marker.get("units", []) if isinstance(unit, dict)]
        if marker.get("title") != spec["title"] or marker.get("denominator") != spec["denominator"] or marker.get("measurement_unit") != spec["measurement_unit"]:
            issues.append(_issue("runtime-placement-marker-contract", marker_path, "Marker title, denominator, or measurement unit drifted.", expected=spec))
        if unit_ids != list(spec["units"]) or len(unit_ids) != spec["denominator"]:
            issues.append(_issue("runtime-placement-marker-units", marker_path, "Marker units must remain the exact fixed denominator.", expected=list(spec["units"]), actual=unit_ids))

        accepted_units = 0
        for unit_index, unit in enumerate(marker.get("units", [])):
            unit_path = f"{marker_path}.units[{unit_index}]"
            if not isinstance(unit, dict):
                issues.append(_issue("runtime-placement-marker-unit-shape", unit_path, "Marker unit must be an object."))
                continue
            status = unit.get("status")
            if status not in STEP_STATUSES:
                issues.append(_issue("runtime-placement-marker-unit-status", unit_path, "Marker unit status must preserve accepted, pending, blocked, or unknown distinctly.", actual=status))
            if status == "accepted":
                accepted_units += 1
            if not _non_empty_strings(unit.get("evidence_refs")):
                issues.append(_issue("runtime-placement-marker-unit-evidence", unit_path, "Marker unit must cite non-empty evidence refs."))
            else:
                issues.extend(_validate_evidence_refs(unit.get("evidence_refs"), f"{unit_path}.evidence_refs", root))

        expected_completed_units = accepted_units if accepted_units else None
        expected_percentage = (accepted_units * 100 / spec["denominator"]) if accepted_units else None
        if marker.get("completed_units") != expected_completed_units or marker.get("percentage") != expected_percentage:
            issues.append(
                _issue(
                    "runtime-placement-marker-calculation",
                    marker_path,
                    "Marker completed units and percentage must derive from accepted fixed-denominator units.",
                    expected_completed_units=expected_completed_units,
                    expected_percentage=expected_percentage,
                    actual_completed_units=marker.get("completed_units"),
                    actual_percentage=marker.get("percentage"),
                )
            )

        lane = lane_records.get(marker_id)
        lane_path = f"{LANE_REGISTRY_REF.as_posix()}#{marker_id}"
        if lane is None:
            issues.append(_issue("runtime-placement-marker-projection", lane_path, "Runtime marker lane is missing from the canonical lane registry."))
            continue
        denominator = lane.get("denominator")
        denominator_value = denominator.get("value") if isinstance(denominator, dict) else None
        if lane.get("title") != spec["title"] or lane.get("measurement_unit") != spec["measurement_unit"] or denominator_value != spec["denominator"]:
            issues.append(_issue("runtime-placement-marker-projection", lane_path, "Canonical lane projection conflicts with the runtime marker contract."))
        if lane.get("percentage") != marker.get("percentage") or lane.get("completed_units") != marker.get("completed_units"):
            issues.append(_issue("runtime-placement-marker-projection-value", lane_path, "Canonical runtime lane values conflict with the runtime marker contract."))
        expected_status = "complete" if accepted_units == spec["denominator"] else "candidate"
        if lane.get("status") != expected_status:
            issues.append(_issue("runtime-placement-marker-projection-status", lane_path, "Canonical runtime lane status conflicts with accepted marker units.", expected=expected_status, actual=lane.get("status")))

    if set(marker_index) != set(MARKER_SPECS):
        issues.append(_issue("runtime-placement-marker-set", f"{registry_path}#marker_lanes", "Runtime placement registry must contain exactly the three admitted marker lanes.", actual=sorted(marker_index)))

    contracts_mesh = lane_records.get("lane-atlas-contracts-mesh", {})
    contracts_denominator = contracts_mesh.get("denominator")
    if not (
        contracts_mesh.get("percentage") == 100
        and contracts_mesh.get("completed_units") == 11
        and isinstance(contracts_denominator, dict)
        and contracts_denominator.get("value") == 11
    ):
        issues.append(_issue("runtime-placement-unchanged-marker", str(LANE_REGISTRY_REF), "Atlas Contracts Mesh must remain exactly 11/11 and 100%."))

    marker_integrity = lane_records.get("lane-marker-integrity", {})
    marker_denominator = marker_integrity.get("denominator")
    if not (
        marker_integrity.get("percentage") == 100
        and marker_integrity.get("completed_units") == 51
        and isinstance(marker_denominator, dict)
        and marker_denominator.get("value") == 51
    ):
        issues.append(_issue("runtime-placement-unchanged-marker", str(LANE_REGISTRY_REF), "Marker Integrity must remain exactly 51/51 and 100%."))

    if "- Atlas Full-System Re-evaluation: `50%`" not in marker_book or "opening gate is accepted at `1 / 2`" not in marker_book:
        issues.append(_issue("runtime-placement-unchanged-marker", str(MARKER_BOOK_REF), "Atlas Full-System Re-evaluation must remain exactly 1/2 and 50%."))
    for marker_id, spec in MARKER_SPECS.items():
        marker = marker_index.get(marker_id, {})
        expected_line = f"- {spec['title']}: `{marker.get('percentage')}%` (`{marker.get('completed_units')} / {spec['denominator']}`)"
        if expected_line not in marker_book:
            issues.append(_issue("runtime-placement-marker-book", str(MARKER_BOOK_REF), "Atlas Book runtime marker projection is missing or stale.", expected_line=expected_line))

    resource_observations = registry.get("advisory_resource_observations")
    if not isinstance(resource_observations, list) or not resource_observations:
        issues.append(_issue("runtime-placement-resource-observations", registry_path, "Advisory resource observations must be a non-empty array."))
    else:
        observation_ids: set[str] = set()
        for index, observation in enumerate(resource_observations):
            path = f"{registry_path}#advisory_resource_observations[{index}]"
            if not isinstance(observation, dict):
                issues.append(_issue("runtime-placement-resource-observation-shape", path, "Advisory resource observation must be an object."))
                continue
            observation_id = observation.get("id")
            if not isinstance(observation_id, str) or not observation_id.strip() or observation_id in observation_ids:
                issues.append(_issue("runtime-placement-resource-observation-id", path, "Advisory resource observation id must be non-empty and unique.", actual=observation_id))
            else:
                observation_ids.add(observation_id)
            if observation.get("action") != "observe_only_no_mutation":
                issues.append(_issue("runtime-placement-resource-observation-authority", path, "Resource observations must remain advisory and non-mutating."))
            observed_at = observation.get("observed_at")
            if not isinstance(observed_at, str) or not observed_at.endswith("Z"):
                issues.append(_issue("runtime-placement-resource-observation-time", path, "Resource observation timestamps must be UTC and end in Z."))

    if not _non_empty_strings(registry.get("current_unknowns")):
        issues.append(_issue("runtime-placement-current-unknowns", registry_path, "Current UNKNOWNs must be a non-empty string array."))

    if registry.get("next_owner_side_activation_packet") != expected_selector:
        issues.append(
            _issue(
                "runtime-placement-selector",
                f"{registry_path}#next_owner_side_activation_packet",
                "Runtime placement selector must name the first unexecuted activation-sequence packet.",
                expected=expected_selector,
                actual=registry.get("next_owner_side_activation_packet"),
            )
        )

    return issues


def validate_contract_files(*, root: Path = ROOT) -> list[RuntimePlacementIssue]:
    paths = {
        "registry": root / REGISTRY_REF,
        "schema": root / SCHEMA_REF,
        "lane_registry": root / LANE_REGISTRY_REF,
        "marker_book": root / MARKER_BOOK_REF,
    }
    issues: list[RuntimePlacementIssue] = []
    for label, path in paths.items():
        if not path.exists():
            issues.append(_issue("runtime-placement-file-missing", path.relative_to(root).as_posix(), f"Required {label} file is missing."))
    if issues:
        return issues
    try:
        registry = _read_json(paths["registry"])
        schema = _read_json(paths["schema"])
        lane_registry = _read_json(paths["lane_registry"])
        marker_book = paths["marker_book"].read_text(encoding="utf-8-sig")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [_issue("runtime-placement-file-invalid", str(REGISTRY_REF), f"Runtime placement inputs could not be loaded: {exc}")]
    issues.extend(validate_registry_schema_contract(registry, schema))
    issues.extend(validate_runtime_placement_payloads(registry, lane_registry, marker_book, root=root))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the canonical ATLAS runtime placement registry and marker projections.")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    issues = validate_contract_files(root=args.root.resolve())
    print(
        json.dumps(
            {
                "schema_version": "atlas.runtime-placement.validation.v1",
                "status": "ok" if not issues else "blocked",
                "issue_count": len(issues),
                "issues": [asdict(issue) for issue in issues],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
