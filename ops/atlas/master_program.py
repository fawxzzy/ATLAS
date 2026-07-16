from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SOURCE_SPEC = ROOT / "docs/programs/ATLAS-MASTER-PROGRAM-REGISTER.v1.source.json"
REGISTER = ROOT / "docs/registry/ATLAS-MASTER-PROGRAM-REGISTER.v1.json"
LANE_REGISTRY = ROOT / "docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json"

NEW_LANE_IDS = {
    "lane-fawxzzy-platform-migration",
    "lane-external-model-sidecar-deepseek-evaluation",
    "lane-atlas-book-playbook-corpus-convergence",
    "lane-atlas-post-preparation-development",
}

IMPORTS = (
    {
        "schema": "atlas.source-import-manifest.v1",
        "import_id": "fawxzzy-platform-supabase-migration-prompt-2026-07-16",
        "logical_locator": "operator-download:ATLAS_MAIN_FAWXZZY_PLATFORM_SUPABASE_MIGRATION_PROMPT_2026-07-16.md",
        "original_filename": "ATLAS_MAIN_FAWXZZY_PLATFORM_SUPABASE_MIGRATION_PROMPT_2026-07-16.md",
        "stored_ref": "data/imports/fawxzzy-platform/2026-07-16/ATLAS_MAIN_FAWXZZY_PLATFORM_SUPABASE_MIGRATION_PROMPT_2026-07-16.md",
        "manifest_ref": "data/imports/fawxzzy-platform/2026-07-16/IMPORT-MANIFEST.json",
        "sha256": "e79f9b1506e79fff5910520fec1652cedb123eac1bbaf3d77a18943f46d0da99",
        "byte_length": 37988,
        "line_count": 1520,
        "received_on": "2026-07-16",
        "trust_classification": "operator-provided-program-proposal-input",
        "review_status": "admitted-as-provenance-not-implementation-authority",
        "newline_style": "lf",
        "derived_artifacts": [
            "docs/registry/FAWXZZY-PLATFORM-MIGRATION-ADMISSION.json",
            "docs/memory/initiatives/initiative-fawxzzy-platform-migration.json",
            "docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json",
            "docs/registry/ATLAS-MASTER-PROGRAM-REGISTER.v1.json",
        ],
    },
    {
        "schema": "atlas.source-import-manifest.v1",
        "import_id": "deepseek-bridge-proposal-2026-07-13",
        "logical_locator": "codex-attachment:1e33f6ae-0f08-4601-811a-edf5d3feb03e/pasted-text.txt",
        "original_filename": "pasted-text.txt",
        "stored_ref": "data/imports/deepseek-bridge/2026-07-13/DEEPSEEK_BRIDGE_PROPOSAL_2026-07-13.txt",
        "manifest_ref": "data/imports/deepseek-bridge/2026-07-13/IMPORT-MANIFEST.json",
        "sha256": "957463349b17ab2a1362a54e3c04329cd67892a9e0c75644090e474621c76022",
        "byte_length": 13273,
        "line_count": 375,
        "received_on": "2026-07-13",
        "trust_classification": "untrusted-external-model-bridge-proposal-input",
        "review_status": "admitted-to-governed-backlog-not-approved-or-implemented",
        "newline_style": "crlf",
        "derived_artifacts": [
            "docs/registry/DEEPSEEK-BRIDGE-WAVE-0-ADMISSION.json",
            "docs/memory/initiatives/initiative-external-model-sidecar-deepseek-litellm-bridge.json",
            "docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json",
            "docs/registry/ATLAS-MASTER-PROGRAM-REGISTER.v1.json",
        ],
    },
)

HISTORICAL_FILE_GUARDS = {
    "docs/audits/ATLAS-FULL-SYSTEM-OPENING-AUDIT-2026-07-12.md": "42766699bfe91a0e034af69d93ddd0aaed497819578ee652555010bb19d4ce65",
    "docs/atlas-book/02-lanes-and-markers.md": "fce6f6444f7acbd094376922649e937760a5aaa2e3dd751499b126926f19116e",
    "docs/memory/initiatives/continuity-manifest-atlas-full-system-re-evaluation.json": "4e4315506fd251b4da2c2c6313d95ecb09fca561022d90b880094536a7d4f923",
    "docs/memory/initiatives/initiative-fawxzzy-tech-plan-convergence.json": "09aa9406595d23d3f1e78e0e568bb31587fee4a103be8e4c6ef1ef3b94d827a4",
    "docs/registry/FAWXZZY-TECH-PLAN-RECOVERY-ADMISSION.json": "e3fa1e0b33292717607b7b218613a648ab7f92d52118b92dd23fd5940d7dbb07",
    "docs/registry/ATLAS-EXTERNAL-MODEL-SIDECAR-RUNTIME-CONTRACT.json": "2fd76706b79431fcddb8b009eaed7c55ea0c6e45f45332afdf127170b2bfef0d",
}

HISTORICAL_LANE_GUARDS = {
    "lanes": {
        "count": 20,
        "sha256": "4886e1f3e566ac2037e61a55dacdb830b53714a37cfc133268364a03f8c88b90",
    },
    "backlog_candidates": {
        "count": 44,
        "sha256": "241b63460851a15a26af2f1064a2e9c0125eff12c077fdb9de025f6b870d43ca",
    },
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _canonical_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_import_manifest(spec: dict[str, Any]) -> dict[str, Any]:
    source = ROOT / spec["stored_ref"]
    raw = source.read_bytes()
    actual_digest = hashlib.sha256(raw).hexdigest()
    if len(raw) != spec["byte_length"] or actual_digest != spec["sha256"]:
        raise ValueError(
            f"fail-closed import mismatch for {spec['stored_ref']}: "
            f"bytes={len(raw)} sha256={actual_digest}"
        )
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"unexpected UTF-8 BOM in {spec['stored_ref']}")
    raw.decode("utf-8")
    return {
        "schema": spec["schema"],
        "import_id": spec["import_id"],
        "source": {
            "logical_locator": spec["logical_locator"],
            "original_filename": spec["original_filename"],
            "received_on": spec["received_on"],
            "bytes": spec["byte_length"],
            "sha256": spec["sha256"],
            "machine_specific_path_committed": False,
        },
        "stored": {
            "path": spec["stored_ref"],
            "bytes": len(raw),
            "sha256": actual_digest,
            "encoding": "utf-8",
            "bom": False,
            "line_endings": spec["newline_style"],
            "line_count": len(raw.splitlines()),
            "terminal_newline": raw.endswith(b"\n"),
        },
        "copy_policy": {
            "byte_for_byte": True,
            "normalization": False,
            "fail_closed": True,
        },
        "trust_classification": spec["trust_classification"],
        "review_status": spec["review_status"],
        "derived_artifacts": spec["derived_artifacts"],
    }


def build_master_register() -> dict[str, Any]:
    spec = _load_json(SOURCE_SPEC)
    lanes = _load_json(LANE_REGISTRY)
    lane_ids = [item["id"] for item in lanes["lanes"]]
    backlog_ids = [item["id"] for item in lanes["backlog_candidates"]]
    result = dict(spec)
    result["authority_indexes"] = {
        "clean_and_resync_lane_registry": {
            "authority_ref": "docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json",
            "lane_ids": lane_ids,
            "backlog_ids": backlog_ids,
            "status_rule": "Resolve status, percentages, denominators, timestamps, and evidence from the authority_ref; this master register does not restate or replace them.",
        },
        "mandatory_closing_audit": {
            "authority_ref": "docs/memory/initiatives/continuity-manifest-atlas-full-system-re-evaluation.json",
            "marker_authority_ref": "docs/atlas-book/02-lanes-and-markers.md",
            "status": "pending",
            "accepted_opening_gate_count": 1,
            "fixed_gate_denominator": 2,
            "historical_percentage": 50,
            "rule": "No discovered lane contributes a point; only the accepted later exhaustive closing audit can complete gate 2 of 2.",
        },
    }
    return result


def _schema_validate(instance: dict[str, Any], schema_ref: str) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return _schema_subset_validate(instance, _load_json(ROOT / schema_ref))
    schema = _load_json(ROOT / schema_ref)
    validator = jsonschema.Draft202012Validator(schema)
    return [error.message for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path))]


def _schema_subset_validate(instance: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Fail-closed validator for the JSON-Schema subset used by this packet.

    The repository does not declare jsonschema as a required runtime dependency. When it is
    available we use Draft 2020-12 directly; otherwise this deliberately small validator keeps
    the producer runnable while covering every assertion used by the three packet schemas and
    atlas.initiative.v1.
    """

    errors: list[str] = []
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value is not in enum")

    expected_type = schema.get("type")
    type_checks = {
        "object": lambda value: isinstance(value, dict),
        "array": lambda value: isinstance(value, list),
        "string": lambda value: isinstance(value, str),
        "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
        "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": lambda value: isinstance(value, bool),
        "null": lambda value: value is None,
    }
    if expected_type and not type_checks[expected_type](instance):
        errors.append(f"{path}: expected type {expected_type}")
        return errors

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{path}: missing required property {key}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in properties:
                    errors.append(f"{path}: unexpected property {key}")
        if len(instance) < schema.get("minProperties", 0):
            errors.append(f"{path}: has fewer than {schema['minProperties']} properties")
        for key, child_schema in properties.items():
            if key in instance:
                errors.extend(_schema_subset_validate(instance[key], child_schema, f"{path}.{key}"))

    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{path}: has fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: has more than {schema['maxItems']} items")
        if schema.get("uniqueItems"):
            canonical = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in instance]
            if len(canonical) != len(set(canonical)):
                errors.append(f"{path}: items are not unique")
        child_schema = schema.get("items")
        if child_schema:
            for index, item in enumerate(instance):
                errors.extend(_schema_subset_validate(item, child_schema, f"{path}[{index}]"))

    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: string is shorter than {schema['minLength']}")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            errors.append(f"{path}: string does not match {schema['pattern']}")
        if schema.get("format") == "date":
            try:
                dt.date.fromisoformat(instance)
            except ValueError:
                errors.append(f"{path}: invalid date")
        if schema.get("format") == "date-time":
            try:
                dt.datetime.fromisoformat(instance.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{path}: invalid date-time")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: number is below minimum {schema['minimum']}")
    return errors


def _validate_historical_guards(lanes: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for ref, expected in HISTORICAL_FILE_GUARDS.items():
        actual = _file_digest(ROOT / ref)
        if actual != expected:
            errors.append(f"historical provenance changed: {ref}: {actual} != {expected}")
    for key, expected in HISTORICAL_LANE_GUARDS.items():
        historical = [item for item in lanes[key] if item.get("id") not in NEW_LANE_IDS]
        actual = _canonical_digest(historical)
        if len(historical) != expected["count"] or actual != expected["sha256"]:
            errors.append(
                f"historical {key} projection changed: count={len(historical)} sha256={actual}"
            )
    return errors


def _validate_deepseek_historical_snapshot() -> list[str]:
    ref = "docs/memory/initiatives/initiative-external-model-sidecar-deepseek-litellm-bridge.json"
    initiative = _load_json(ROOT / ref)
    expected_progress = {
        "numerator": 2,
        "denominator": 6,
        "percent": 33.3,
        "marker": "33.3%",
        "admission_completes_no_unit": False,
    }
    errors: list[str] = []
    if initiative.get("created_at") != "2026-07-13T00:00:00Z":
        errors.append(f"DeepSeek historical created_at changed: {ref}")
    if initiative.get("metadata", {}).get("progress") != expected_progress:
        errors.append(f"DeepSeek historical 2-of-6 / 33.3 percent snapshot changed: {ref}")
    if initiative.get("metadata", {}).get("marker_movement") != (
        "Only this lane moved from 16.7% to 33.3%; no other marker moved."
    ):
        errors.append(f"DeepSeek historical marker movement changed: {ref}")
    current = initiative.get("metadata", {}).get("current_measurement", {})
    if current != {"status": "UNMEASURED", "percentage": None, "denominator": None}:
        errors.append(f"DeepSeek current measurement must be percentage-null / UNMEASURED: {ref}")
    return errors


def _validate_raw_import_git_attributes() -> list[str]:
    rules = {
        line.strip()
        for line in (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    return [
        f"raw byte-preserved import must be marked binary in .gitattributes: {spec['stored_ref']}"
        for spec in IMPORTS
        if f"{spec['stored_ref']} binary" not in rules
    ]


def _validate_reference_integrity(register: dict[str, Any], lanes: dict[str, Any]) -> list[str]:
    refs: list[tuple[str, str]] = []
    refs.extend((ref, "master source_refs") for ref in register.get("source_refs", []))
    for program in register.get("programs", []):
        refs.extend((ref, f"{program.get('id')} evidence") for ref in program.get("evidence", []))

    admission_refs = (
        "docs/registry/FAWXZZY-PLATFORM-MIGRATION-ADMISSION.json",
        "docs/registry/DEEPSEEK-BRIDGE-WAVE-0-ADMISSION.json",
    )
    for admission_ref in admission_refs:
        admission = _load_json(ROOT / admission_ref)
        refs.extend((ref, f"{admission_ref} evidence") for ref in admission.get("evidence", []))
        source_import = admission.get("source_import", {})
        refs.extend(
            (source_import[key], f"{admission_ref} source_import.{key}")
            for key in ("stored_ref", "manifest_ref")
        )

    initiative_refs = (
        "docs/memory/initiatives/initiative-atlas-post-preparation-development.json",
        "docs/memory/initiatives/initiative-fawxzzy-platform-migration.json",
        "docs/memory/initiatives/initiative-external-model-sidecar-deepseek-litellm-bridge.json",
    )
    for initiative_ref in initiative_refs:
        initiative = _load_json(ROOT / initiative_ref)
        refs.extend((ref, f"{initiative_ref} evidence_refs") for ref in initiative.get("evidence_refs", []))

    by_id = {item.get("id"): item for item in lanes["lanes"] + lanes["backlog_candidates"]}
    for lane_id in NEW_LANE_IDS:
        lane = by_id.get(lane_id)
        if lane:
            refs.extend((ref, f"{lane_id} evidence_sources") for ref in lane.get("evidence_sources", []))

    errors: list[str] = []
    for ref, owner in refs:
        relative = Path(ref)
        if relative.is_absolute() or ".." in relative.parts or "\\" in ref:
            errors.append(f"non-portable reference in {owner}: {ref}")
        elif not (ROOT / relative).exists():
            errors.append(f"missing reference in {owner}: {ref}")
    return errors


def validate_repository() -> list[str]:
    errors: list[str] = []
    lanes = _load_json(LANE_REGISTRY)
    errors.extend(_validate_historical_guards(lanes))
    errors.extend(_validate_deepseek_historical_snapshot())
    errors.extend(_validate_raw_import_git_attributes())

    for spec in IMPORTS:
        try:
            expected_manifest = build_import_manifest(spec)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            errors.append(str(exc))
            continue
        manifest_path = ROOT / spec["manifest_ref"]
        if not manifest_path.exists():
            errors.append(f"missing generated manifest: {spec['manifest_ref']}")
        elif manifest_path.read_bytes() != _json_bytes(expected_manifest):
            errors.append(f"generated manifest drift: {spec['manifest_ref']}")
        errors.extend(
            f"{spec['manifest_ref']}: {message}"
            for message in _schema_validate(
                expected_manifest,
                "schemas/atlas.source-import-manifest.v1.json",
            )
        )

    expected_register = build_master_register()
    if not REGISTER.exists():
        errors.append("missing generated master register")
    elif REGISTER.read_bytes() != _json_bytes(expected_register):
        errors.append("generated master register drift")
    errors.extend(
        f"master register: {message}"
        for message in _schema_validate(
            expected_register,
            "schemas/atlas.master-program-register.v1.json",
        )
    )
    errors.extend(_validate_reference_integrity(expected_register, lanes))

    admission_paths = (
        "docs/registry/FAWXZZY-PLATFORM-MIGRATION-ADMISSION.json",
        "docs/registry/DEEPSEEK-BRIDGE-WAVE-0-ADMISSION.json",
    )
    for ref in admission_paths:
        path = ROOT / ref
        if not path.exists():
            errors.append(f"missing admission: {ref}")
            continue
        errors.extend(
            f"{ref}: {message}"
            for message in _schema_validate(
                _load_json(path),
                "schemas/atlas.program-admission.v1.json",
            )
        )

    initiative_paths = (
        "docs/memory/initiatives/initiative-atlas-post-preparation-development.json",
        "docs/memory/initiatives/initiative-fawxzzy-platform-migration.json",
    )
    for ref in initiative_paths:
        path = ROOT / ref
        if not path.exists():
            errors.append(f"missing initiative: {ref}")
            continue
        errors.extend(
            f"{ref}: {message}"
            for message in _schema_validate(_load_json(path), "schemas/atlas.initiative.v1.json")
        )

    indexed = lanes["lanes"] + lanes["backlog_candidates"]
    by_id = {item.get("id"): item for item in indexed}
    for lane_id in sorted(NEW_LANE_IDS):
        lane = by_id.get(lane_id)
        if lane is None:
            errors.append(f"missing required lane: {lane_id}")
            continue
        for key in (
            "owner",
            "authority",
            "scope",
            "dependencies",
            "serialization_rules",
            "approval_gates",
            "evidence_sources",
            "definition_of_done",
            "status",
            "next_packet",
            "measurement_status",
        ):
            if key not in lane:
                errors.append(f"{lane_id} missing {key}")
        if lane.get("percentage") is not None or lane.get("measurement_status") != "UNMEASURED":
            errors.append(f"{lane_id} must remain percentage-null / UNMEASURED")

    if expected_register.get("measurement_policy", {}).get("new_work") != "UNMEASURED":
        errors.append("master register new-work measurement policy must be UNMEASURED")
    program_ids = [item.get("id") for item in expected_register.get("programs", [])]
    if len(program_ids) != len(set(program_ids)):
        errors.append("master register program ids must be unique")
    return errors


def write_generated() -> None:
    for spec in IMPORTS:
        manifest_path = ROOT / spec["manifest_ref"]
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_bytes(_json_bytes(build_import_manifest(spec)))
    REGISTER.parent.mkdir(parents=True, exist_ok=True)
    REGISTER.write_bytes(_json_bytes(build_master_register()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate and validate the ATLAS master-program Wave 0 artifacts.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Regenerate producer-owned artifacts.")
    mode.add_argument("--check", action="store_true", help="Fail on drift or contract violations.")
    args = parser.parse_args(argv)
    if args.write:
        write_generated()
    errors = validate_repository()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("ATLAS master program validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
