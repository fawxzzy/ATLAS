from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "atlas.codex.handoff.v1"
SCHEMA_ID = "atlas://codex/change_handoff.schema.json"
TITLE_LINE_PATTERN = re.compile(r"^[^\r\n]+$")
ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")
RELATIVE_PATH_PATTERN = re.compile(r"^(?![A-Za-z]:[\\/])(?!/)(?!file:).+")
MUTATION_MODES = {"read_only", "scoped_write", "stack_only"}
PRODUCER_KINDS = {"codex", "wrapper", "manual", "test"}
CAPTURE_MODES = {"schema_json", "explicit_json_file"}
FILE_STATUSES = {"added", "modified", "deleted", "renamed"}
VALIDATION_STATUSES = {"passed", "failed", "not_run"}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def normalize_slashes(value: str) -> str:
    return value.replace("\\", "/")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def ensure(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_relative_contract_path(value: Any) -> bool:
    return is_non_empty_string(value) and bool(RELATIVE_PATH_PATTERN.fullmatch(value))


def validate_iso_datetime(value: Any) -> bool:
    if not is_non_empty_string(value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_schema_definition(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    ensure(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "Schema $schema must target draft 2020-12.", errors)
    ensure(schema.get("$id") == SCHEMA_ID, f"Schema $id must be '{SCHEMA_ID}'.", errors)
    ensure(schema.get("type") == "object", "Schema root type must be object.", errors)
    ensure(schema.get("title") == "ATLAS Codex change handoff", "Schema title must match the contract title.", errors)
    ensure(schema.get("additionalProperties") is False, "Schema root must disallow additionalProperties.", errors)
    required = schema.get("required")
    ensure(isinstance(required, list), "Schema required must be an array.", errors)
    properties = schema.get("properties")
    ensure(isinstance(properties, dict), "Schema properties must be an object.", errors)
    expected_fields = {
        "contract_version",
        "handoff_id",
        "generated_at",
        "producer",
        "task_name",
        "workspace_root",
        "summary",
        "changed_files",
        "validation",
        "commit_title",
        "commit_body",
        "pr_title",
        "pr_body",
    }
    if isinstance(required, list):
        missing = sorted(expected_fields - set(required))
        ensure(not missing, f"Schema required is missing fields: {', '.join(missing)}", errors)
    if isinstance(properties, dict):
        missing_props = sorted(expected_fields - set(properties.keys()))
        ensure(not missing_props, f"Schema properties is missing fields: {', '.join(missing_props)}", errors)
        contract_version = properties.get("contract_version", {})
        if isinstance(contract_version, dict):
            ensure(contract_version.get("const") == CONTRACT_VERSION, f"contract_version const must be '{CONTRACT_VERSION}'.", errors)
        else:
            errors.append("contract_version property must be an object.")
    try:
        import jsonschema  # type: ignore

        jsonschema.Draft202012Validator.check_schema(schema)
    except ModuleNotFoundError:
        pass
    except Exception as exc:
        errors.append(f"jsonschema rejected the schema definition: {exc}")
    return errors


def validate_handoff_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    ensure(payload.get("contract_version") == CONTRACT_VERSION, f"contract_version must be '{CONTRACT_VERSION}'.", errors)
    ensure(is_non_empty_string(payload.get("handoff_id")) and bool(ID_PATTERN.fullmatch(payload["handoff_id"])), "handoff_id must be a non-empty identifier.", errors)
    ensure(validate_iso_datetime(payload.get("generated_at")), "generated_at must be an ISO 8601 timestamp.", errors)
    ensure(is_non_empty_string(payload.get("task_name")), "task_name must be a non-empty string.", errors)
    ensure(is_relative_contract_path(payload.get("workspace_root")), "workspace_root must be an ATLAS-relative path.", errors)
    ensure(is_non_empty_string(payload.get("summary")), "summary must be a non-empty string.", errors)

    producer = payload.get("producer")
    ensure(isinstance(producer, dict), "producer must be an object.", errors)
    if isinstance(producer, dict):
        ensure(producer.get("kind") in PRODUCER_KINDS, f"producer.kind must be one of: {', '.join(sorted(PRODUCER_KINDS))}.", errors)
        ensure(is_non_empty_string(producer.get("name")), "producer.name must be a non-empty string.", errors)
        ensure(producer.get("capture_mode") in CAPTURE_MODES, f"producer.capture_mode must be one of: {', '.join(sorted(CAPTURE_MODES))}.", errors)

    scope_paths = payload.get("scope_paths")
    if scope_paths is not None:
        ensure(isinstance(scope_paths, list), "scope_paths must be an array when present.", errors)
        if isinstance(scope_paths, list):
            for index, item in enumerate(scope_paths):
                ensure(is_relative_contract_path(item), f"scope_paths[{index}] must be an ATLAS-relative path.", errors)

    repo_ids = payload.get("repo_ids")
    if repo_ids is not None:
        ensure(isinstance(repo_ids, list), "repo_ids must be an array when present.", errors)
        if isinstance(repo_ids, list):
            for index, item in enumerate(repo_ids):
                ensure(is_non_empty_string(item), f"repo_ids[{index}] must be a non-empty string.", errors)

    mutation_mode = payload.get("mutation_mode")
    if mutation_mode is not None:
        ensure(mutation_mode in MUTATION_MODES, f"mutation_mode must be one of: {', '.join(sorted(MUTATION_MODES))}.", errors)

    changed_files = payload.get("changed_files")
    ensure(isinstance(changed_files, list) and bool(changed_files), "changed_files must be a non-empty array.", errors)
    if isinstance(changed_files, list):
        for index, item in enumerate(changed_files):
            ensure(isinstance(item, dict), f"changed_files[{index}] must be an object.", errors)
            if not isinstance(item, dict):
                continue
            unexpected = sorted(set(item.keys()) - {"path", "summary", "status"})
            ensure(not unexpected, f"changed_files[{index}] contains unsupported fields: {', '.join(unexpected)}.", errors)
            ensure(is_relative_contract_path(item.get("path")), f"changed_files[{index}].path must be an ATLAS-relative path.", errors)
            ensure(is_non_empty_string(item.get("summary")), f"changed_files[{index}].summary must be a non-empty string.", errors)
            ensure(item.get("status") in FILE_STATUSES, f"changed_files[{index}].status must be one of: {', '.join(sorted(FILE_STATUSES))}.", errors)

    validation = payload.get("validation")
    ensure(isinstance(validation, dict), "validation must be an object.", errors)
    if isinstance(validation, dict):
        unexpected = sorted(set(validation.keys()) - {"status", "summary", "commands"})
        ensure(not unexpected, f"validation contains unsupported fields: {', '.join(unexpected)}.", errors)
        ensure(validation.get("status") in VALIDATION_STATUSES, f"validation.status must be one of: {', '.join(sorted(VALIDATION_STATUSES))}.", errors)
        ensure(is_non_empty_string(validation.get("summary")), "validation.summary must be a non-empty string.", errors)
        commands = validation.get("commands")
        ensure(isinstance(commands, list), "validation.commands must be an array.", errors)
        if isinstance(commands, list):
            for index, item in enumerate(commands):
                ensure(isinstance(item, dict), f"validation.commands[{index}] must be an object.", errors)
                if not isinstance(item, dict):
                    continue
                unexpected_item = sorted(set(item.keys()) - {"command", "status", "details"})
                ensure(not unexpected_item, f"validation.commands[{index}] contains unsupported fields: {', '.join(unexpected_item)}.", errors)
                ensure(is_non_empty_string(item.get("command")), f"validation.commands[{index}].command must be a non-empty string.", errors)
                ensure(item.get("status") in VALIDATION_STATUSES, f"validation.commands[{index}].status must be one of: {', '.join(sorted(VALIDATION_STATUSES))}.", errors)
                details = item.get("details")
                if details is not None:
                    ensure(isinstance(details, str), f"validation.commands[{index}].details must be a string when present.", errors)

    for key, max_length in (("commit_title", 72), ("pr_title", 120)):
        value = payload.get(key)
        ensure(is_non_empty_string(value), f"{key} must be a non-empty string.", errors)
        if isinstance(value, str):
            ensure(len(value) <= max_length, f"{key} must be {max_length} characters or fewer.", errors)
            ensure(bool(TITLE_LINE_PATTERN.fullmatch(value)), f"{key} must be a single line.", errors)

    for key in ("commit_body", "pr_body"):
        ensure(is_non_empty_string(payload.get(key)), f"{key} must be a non-empty string.", errors)

    unexpected_root = sorted(
        set(payload.keys())
        - {
            "contract_version",
            "handoff_id",
            "generated_at",
            "producer",
            "task_name",
            "workspace_root",
            "scope_paths",
            "repo_ids",
            "mutation_mode",
            "summary",
            "changed_files",
            "validation",
            "commit_title",
            "commit_body",
            "pr_title",
            "pr_body",
        }
    )
    ensure(not unexpected_root, f"Handoff contains unsupported fields: {', '.join(unexpected_root)}.", errors)

    try:
        import jsonschema  # type: ignore

        schema = load_json(repo_root() / "ops" / "codex" / "schemas" / "change_handoff.schema.json")
        jsonschema.validate(payload, schema)
    except ModuleNotFoundError:
        pass
    except Exception as exc:
        errors.append(f"jsonschema rejected the handoff payload: {exc}")

    return errors


def build_synthetic_handoff() -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "handoff_id": "handoff-20260409T150000Z-sample",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "producer": {
            "kind": "test",
            "name": "atlas-synthetic-example",
            "capture_mode": "schema_json",
            "version": "1",
        },
        "task_name": "atlas-codex-handoff",
        "workspace_root": ".",
        "scope_paths": [
            "docs/architecture",
            "docs/ops",
            "ops/codex",
        ],
        "repo_ids": [
            "stack",
        ],
        "mutation_mode": "stack_only",
        "summary": "Add an ATLAS-owned structured handoff flow for commit and PR preparation.",
        "changed_files": [
            {
                "path": "docs/architecture/CODEX-HANDOFF-CONTRACT.md",
                "summary": "Document the ATLAS handoff contract.",
                "status": "added",
            },
            {
                "path": "ops/codex/commit_from_handoff.ps1",
                "summary": "Generate preview-first commit text from handoff JSON.",
                "status": "added",
            },
        ],
        "validation": {
            "status": "passed",
            "summary": "Schema and synthetic handoff validation passed.",
            "commands": [
                {
                    "command": "python .\\ops\\codex\\validate_handoff.py --schema-file .\\ops\\codex\\schemas\\change_handoff.schema.json",
                    "status": "passed",
                },
                {
                    "command": "python .\\ops\\codex\\validate_handoff.py --handoff-file .\\tmp\\scratch\\handoff.synthetic.json",
                    "status": "passed",
                },
            ],
        },
        "commit_title": "ops: add Codex handoff contract",
        "commit_body": "Add an ATLAS-owned JSON handoff contract for Codex final output.\n\nInclude validation and helper scripts for preview-first commit and PR preparation.",
        "pr_title": "Add ATLAS Codex handoff flow",
        "pr_body": "## Summary\n- add an ATLAS-owned JSON handoff contract for Codex final output\n- add preview-first scripts for commit and PR preparation\n- validate the schema and a synthetic handoff example\n\n## Validation\n- python .\\ops\\codex\\validate_handoff.py --schema-file .\\ops\\codex\\schemas\\change_handoff.schema.json\n- python .\\ops\\codex\\validate_handoff.py --handoff-file .\\tmp\\scratch\\handoff.synthetic.json",
    }


def print_preview(payload: dict[str, Any], source: Path) -> None:
    print(f"Handoff file : {normalize_slashes(str(source))}")
    print(f"Task         : {payload['task_name']}")
    print(f"Workspace    : {payload['workspace_root']}")
    print(f"Summary      : {payload['summary']}")
    print(f"Files        : {len(payload['changed_files'])}")
    for item in payload["changed_files"]:
        print(f"  - {item['status']}: {item['path']} :: {item['summary']}")
    print(f"Validation   : {payload['validation']['status']}")
    print(f"Commit title : {payload['commit_title']}")
    print(f"PR title     : {payload['pr_title']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the ATLAS Codex handoff contract and payload.")
    parser.add_argument("--schema-file", default=str(repo_root() / "ops" / "codex" / "schemas" / "change_handoff.schema.json"))
    parser.add_argument("--handoff-file")
    parser.add_argument("--write-synthetic")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args(argv)

    schema_path = Path(args.schema_file).resolve()
    if not schema_path.exists():
        print(f"Schema file not found: {normalize_slashes(str(schema_path))}", file=sys.stderr)
        return 1

    schema = load_json(schema_path)
    schema_errors = validate_schema_definition(schema)
    if schema_errors:
        print("Schema validation failed:", file=sys.stderr)
        for error in schema_errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Schema valid: {normalize_slashes(str(schema_path))}")

    handoff_path: Path | None = None
    if args.write_synthetic:
        handoff_path = Path(args.write_synthetic).resolve()
        handoff_path.parent.mkdir(parents=True, exist_ok=True)
        synthetic = build_synthetic_handoff()
        handoff_path.write_text(json.dumps(synthetic, indent=2), encoding="utf-8")
        print(f"Synthetic handoff written: {normalize_slashes(str(handoff_path))}")

    if args.handoff_file:
        handoff_path = Path(args.handoff_file).resolve()

    if handoff_path is None:
        return 0

    if not handoff_path.exists():
        print(f"Handoff file not found: {normalize_slashes(str(handoff_path))}", file=sys.stderr)
        return 1

    payload = load_json(handoff_path)
    if not isinstance(payload, dict):
        print("Handoff file must deserialize to a JSON object.", file=sys.stderr)
        return 1

    payload_errors = validate_handoff_payload(payload)
    if payload_errors:
        print("Handoff validation failed:", file=sys.stderr)
        for error in payload_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Handoff valid: {normalize_slashes(str(handoff_path))}")
    if args.preview:
        print_preview(payload, handoff_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
