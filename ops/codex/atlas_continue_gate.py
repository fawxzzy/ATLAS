from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "atlas.codex.result.v1"
DECISION_VERSION = "atlas.codex.continue_gate.decision.v1"
SCHEMA_ID = "atlas://codex/atlas_codex_result.schema.json"
ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")
RELATIVE_PATH_PATTERN = re.compile(r"^(?![A-Za-z]:[\\/])(?!/)(?!file:).+")
NONE_NEXT_MOVE_PATTERN = re.compile(r"^\s*none\b", re.IGNORECASE)
ALLOWED_RESULT_MODES = {"codex"}
ALLOWED_PRODUCER_KINDS = {"codex", "wrapper", "manual", "test"}
ALLOWED_CAPTURE_MODES = {"schema_json", "explicit_json_file", "jsonl_final_message"}
DEFAULT_ALLOWED_CLASSIFICATIONS = {
    "expected_in_flight_stack_lock_dirty_state_drift",
    "expected_dirty_state_drift",
    "expected_in_flight_stack_stack_lock_yaml_dirty_state_drift",
}
JSONL_RESULT_CONTAINER_KEYS = ("result", "payload", "final_result")
JSONL_NESTED_CONTAINER_KEYS = ("data", "message")
ADMITTED_RESUME_EXECUTABLE_NAMES = {"codex", "codex.exe"}
ADMITTED_RESUME_SUFFIX = ("exec", "resume", "--last")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def normalize_slashes(value: str) -> str:
    return value.replace("\\", "/")


def normalize_label(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def split_command_tokens(command: str) -> list[str] | None:
    try:
        return shlex.split(command, posix=False)
    except ValueError:
        return None


def extract_admitted_resume_command(command: str | None) -> tuple[list[str] | None, str | None]:
    if not is_non_empty_string(command):
        return None, "live execution requires an explicit continuation command."
    tokens = split_command_tokens(command)
    if not tokens:
        return None, "continuation command could not be parsed."
    if len(tokens) not in {4, 5}:
        return None, "live execution only admits the exact real `codex exec resume --last` shape or one exact inline-prompt variant."
    executable_token = tokens[0].strip()
    normalized_executable = executable_token.strip("\"'")
    executable_name = Path(normalized_executable).name.lower()
    if executable_name not in ADMITTED_RESUME_EXECUTABLE_NAMES:
        return None, "live execution only admits the exact real `codex exec resume --last` shape or one exact inline-prompt variant."
    normalized_suffix = tuple(token.lower() for token in tokens[1:4])
    if normalized_suffix != ADMITTED_RESUME_SUFFIX:
        return None, "live execution only admits the exact real `codex exec resume --last` shape or one exact inline-prompt variant."
    if len(tokens) == 4:
        return [normalized_executable, *ADMITTED_RESUME_SUFFIX], None
    prompt_token = tokens[4]
    if not isinstance(prompt_token, str) or not prompt_token.strip():
        return None, "prompt-bearing live execution requires one non-empty inline prompt argument."
    if prompt_token.strip() == "-":
        return None, "prompt-bearing live execution does not yet admit dash-stdin prompt injection; only one inline prompt argument is admitted."
    return [normalized_executable, *ADMITTED_RESUME_SUFFIX, prompt_token], None


def classify_admitted_resume_command(admitted_command: list[str]) -> str:
    if len(admitted_command) == 4:
        return "promptless_resume_last"
    if len(admitted_command) == 5:
        return "inline_prompt_resume_last"
    return "unknown_resume_shape"


def resolve_command_path(executable: str) -> str:
    resolved = shutil.which(executable)
    return resolved or executable


def build_resume_runtime_probe(executable: str) -> dict[str, Any]:
    resolved = resolve_command_path(executable)
    resolved_path = Path(resolved)
    resolved_text = normalize_slashes(str(resolved_path))
    path_casefold = resolved_text.casefold()
    exists = resolved_path.exists()
    is_windowsapps = "/windowsapps/" in path_casefold
    is_codex_package = "openai.codex_" in path_casefold
    readable = exists and os.access(resolved, os.R_OK)
    executable_ok = exists and os.access(resolved, os.X_OK)
    return {
        "resolved_executable": resolved_text,
        "exists": exists,
        "readable": readable,
        "executable": executable_ok,
        "windowsapps_packaged": is_windowsapps,
        "openai_codex_packaged": is_codex_package,
    }


def list_command_resolutions(executable: str) -> list[str]:
    if os.name != "nt":
        return []
    try:
        completed = subprocess.run(
            ["where.exe", executable],
            cwd=repo_root(),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []
    if completed.returncode != 0:
        return []
    return [
        normalize_slashes(line.strip())
        for line in completed.stdout.splitlines()
        if line.strip()
    ]


def read_npm_global_prefix() -> str | None:
    npm_executable = resolve_command_path("npm")
    try:
        completed = subprocess.run(
            [npm_executable, "config", "get", "prefix"],
            cwd=repo_root(),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    prefix = completed.stdout.strip()
    return normalize_slashes(prefix) if prefix else None


def classify_runtime_surface_probe(
    probe: dict[str, Any],
    *,
    version_status: str,
    version_returncode: int | None,
    under_npm_global_prefix: bool,
) -> str:
    if version_status == "blocked":
        blocked_classification = probe.get("version_failure_classification")
        if is_non_empty_string(blocked_classification):
            return str(blocked_classification)
        return "runtime_start_failure"
    if version_status == "passed":
        if under_npm_global_prefix:
            return "non_packaged_npm_codex_launchable"
        if probe.get("windowsapps_packaged"):
            return "windowsapps_packaged_codex_launchable"
        return "non_packaged_codex_launchable"
    if not probe.get("exists"):
        return "command_path_unavailable"
    if version_returncode is not None:
        return "runtime_version_command_failed"
    return "runtime_surface_probe_incomplete"


def build_runtime_surface_probe(executable: str) -> dict[str, Any]:
    probe = build_resume_runtime_probe(executable)
    command_order = list_command_resolutions(executable)
    npm_global_prefix = read_npm_global_prefix()
    resolved_executable = str(probe["resolved_executable"])
    resolved_casefold = resolved_executable.casefold()
    npm_prefix_casefold = normalize_slashes(npm_global_prefix).casefold() if npm_global_prefix else None
    under_npm_global_prefix = bool(npm_prefix_casefold and resolved_casefold.startswith(npm_prefix_casefold.rstrip("/") + "/"))
    windowsapps_candidates_present = any("/windowsapps/" in item.casefold() for item in command_order)
    lower_priority_windowsapps_present = bool(command_order) and not command_order[0].casefold().count("/windowsapps/") and windowsapps_candidates_present

    probe.update(
        {
            "requested_executable": executable,
            "command_order": command_order,
            "windowsapps_candidates_present": windowsapps_candidates_present,
            "lower_priority_windowsapps_present": lower_priority_windowsapps_present,
            "npm_global_prefix": npm_global_prefix,
            "under_npm_global_prefix": under_npm_global_prefix,
            "version_command": f"{resolved_executable} --version",
        }
    )

    try:
        completed = subprocess.run(
            [resolved_executable, "--version"],
            cwd=repo_root(),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        version_status = "blocked"
        version_classification = classify_runtime_start_failure(probe, exc)
        probe.update(
            {
                "version_status": version_status,
                "version_failure_classification": version_classification,
                "version_details": f"runtime surface probe could not start `{resolved_executable} --version`: {exc}",
            }
        )
    else:
        version_status = "passed" if completed.returncode == 0 else "failed"
        version_stdout = completed.stdout.strip()
        version_stderr = completed.stderr.strip()
        version_output = version_stdout or version_stderr
        probe.update(
            {
                "version_status": version_status,
                "version_returncode": completed.returncode,
                "version_stdout": version_stdout,
                "version_stderr": version_stderr,
                "version_output": version_output,
            }
        )

    probe["classification"] = classify_runtime_surface_probe(
        probe,
        version_status=str(probe.get("version_status", "unknown")),
        version_returncode=probe.get("version_returncode"),
        under_npm_global_prefix=under_npm_global_prefix,
    )
    return probe


def classify_runtime_start_failure(probe: dict[str, Any], exc: OSError) -> str:
    winerror = getattr(exc, "winerror", None)
    if winerror == 5 and probe.get("windowsapps_packaged") and probe.get("openai_codex_packaged"):
        return "windowsapps_packaged_codex_start_access_denied"
    if winerror == 5:
        return "start_access_denied"
    if winerror in {2, 3}:
        return "command_path_unavailable"
    if winerror == 193:
        return "invalid_executable_format"
    return "runtime_start_failure"


def build_resume_launch_command(admitted_command: list[str], runtime_probe: dict[str, Any]) -> tuple[list[str], str]:
    resolved_executable = str(runtime_probe["resolved_executable"])
    suffix = Path(resolved_executable).suffix.casefold()
    if os.name == "nt" and suffix in {".cmd", ".bat"}:
        return ["cmd.exe", "/c", resolved_executable, *admitted_command[1:]], "windows_cmd_shim"
    if os.name == "nt" and suffix == ".ps1":
        return ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", resolved_executable, *admitted_command[1:]], "powershell_script"
    return [resolved_executable, *admitted_command[1:]], "direct_executable"


def classify_resume_command_completion(completed: subprocess.CompletedProcess[str]) -> str:
    if completed.returncode == 0:
        return "resume_command_executed"
    stderr = (completed.stderr or "").casefold()
    stdout = (completed.stdout or "").casefold()
    combined = "\n".join(part for part in (stderr, stdout) if part)
    if "reading prompt from stdin" in combined and "no prompt provided via stdin" in combined:
        return "resume_requires_stdin_prompt"
    return "resume_command_failed"


def parse_resume_contract_help(help_text: str) -> dict[str, Any]:
    lines = [line.rstrip() for line in help_text.splitlines()]
    usage_lines = [line.strip() for line in lines if line.strip().startswith("Usage:")]
    prompt_argument_supported = any("[PROMPT]" in line and "resume" in line.casefold() for line in usage_lines)
    session_id_supported = any("[SESSION_ID]" in line and "resume" in line.casefold() for line in usage_lines)
    stdin_dash_supported = "If `-` is used, read from stdin" in help_text
    return {
        "usage_lines": usage_lines,
        "prompt_argument_supported": prompt_argument_supported,
        "prompt_argument_optional": prompt_argument_supported,
        "session_id_supported": session_id_supported,
        "stdin_dash_supported": stdin_dash_supported,
    }


def classify_resume_contract_probe(
    *,
    help_status: str,
    help_returncode: int | None,
    prompt_argument_supported: bool,
    stdin_dash_supported: bool,
) -> str:
    if help_status == "blocked":
        return "resume_contract_probe_blocked"
    if help_status == "failed":
        return "resume_help_command_failed"
    if prompt_argument_supported and stdin_dash_supported:
        return "resume_prompt_arg_and_stdin_dash_supported"
    if prompt_argument_supported:
        return "resume_prompt_arg_supported"
    return "resume_prompt_contract_not_detected"


def build_resume_contract_probe(executable: str) -> dict[str, Any]:
    runtime_probe = build_resume_runtime_probe(executable)
    resolved_executable = str(runtime_probe["resolved_executable"])
    launch_command, launch_mode = build_resume_launch_command(
        [resolved_executable, "exec", "resume", "--help"],
        runtime_probe,
    )
    probe: dict[str, Any] = {
        "requested_executable": executable,
        "resolved_executable": resolved_executable,
        "launch_command": launch_command,
        "launch_mode": launch_mode,
        "current_admitted_command_shape": "codex exec resume --last",
        "current_admitted_shape_omits_prompt": True,
    }
    try:
        completed = subprocess.run(
            launch_command,
            cwd=repo_root(),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        probe["help_status"] = "blocked"
        probe["classification"] = classify_runtime_start_failure(runtime_probe, exc)
        probe["details"] = f"resume contract probe could not start `{resolved_executable} exec resume --help`: {exc}"
        probe["runtime_probe"] = runtime_probe
        return probe

    help_status = "passed" if completed.returncode == 0 else "failed"
    help_text = completed.stdout or completed.stderr or ""
    parsed = parse_resume_contract_help(help_text)
    probe.update(parsed)
    probe["help_status"] = help_status
    probe["help_returncode"] = completed.returncode
    probe["help_output_excerpt"] = help_text[:4000]
    probe["classification"] = classify_resume_contract_probe(
        help_status=help_status,
        help_returncode=completed.returncode,
        prompt_argument_supported=bool(parsed["prompt_argument_supported"]),
        stdin_dash_supported=bool(parsed["stdin_dash_supported"]),
    )
    return probe


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


def schema_path_default() -> Path:
    return repo_root() / "ops" / "codex" / "schemas" / "atlas_codex_result.schema.json"


def validate_schema_definition(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    ensure(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "Schema $schema must target draft 2020-12.", errors)
    ensure(schema.get("$id") == SCHEMA_ID, f"Schema $id must be '{SCHEMA_ID}'.", errors)
    ensure(schema.get("type") == "object", "Schema root type must be object.", errors)
    ensure(schema.get("title") == "ATLAS Codex continuation result", "Schema title must match the contract title.", errors)
    ensure(schema.get("additionalProperties") is False, "Schema root must disallow additionalProperties.", errors)
    required = schema.get("required")
    properties = schema.get("properties")
    ensure(isinstance(required, list), "Schema required must be an array.", errors)
    ensure(isinstance(properties, dict), "Schema properties must be an object.", errors)
    expected_fields = {
        "contract_version",
        "result_id",
        "generated_at",
        "producer",
        "lane_id",
        "active_slice",
        "summary",
        "changed_files",
        "validation_snapshot",
        "marker_outcome",
        "next_move",
        "scope_guard",
    }
    if isinstance(required, list):
        missing = sorted(expected_fields - set(required))
        ensure(not missing, f"Schema required is missing fields: {', '.join(missing)}.", errors)
    if isinstance(properties, dict):
        missing_props = sorted(expected_fields - set(properties.keys()))
        ensure(not missing_props, f"Schema properties is missing fields: {', '.join(missing_props)}.", errors)
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


def validate_result_payload(payload: dict[str, Any], schema: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []

    ensure(payload.get("contract_version") == CONTRACT_VERSION, f"contract_version must be '{CONTRACT_VERSION}'.", errors)
    ensure(is_non_empty_string(payload.get("result_id")) and bool(ID_PATTERN.fullmatch(payload["result_id"])), "result_id must be a non-empty identifier.", errors)
    ensure(validate_iso_datetime(payload.get("generated_at")), "generated_at must be an ISO 8601 timestamp.", errors)
    ensure(is_non_empty_string(payload.get("lane_id")), "lane_id must be a non-empty string.", errors)
    ensure(is_non_empty_string(payload.get("active_slice")), "active_slice must be a non-empty string.", errors)
    ensure(is_non_empty_string(payload.get("summary")), "summary must be a non-empty string.", errors)

    producer = payload.get("producer")
    ensure(isinstance(producer, dict), "producer must be an object.", errors)
    if isinstance(producer, dict):
        ensure(producer.get("kind") in ALLOWED_PRODUCER_KINDS, f"producer.kind must be one of: {', '.join(sorted(ALLOWED_PRODUCER_KINDS))}.", errors)
        ensure(is_non_empty_string(producer.get("name")), "producer.name must be a non-empty string.", errors)
        ensure(producer.get("capture_mode") in ALLOWED_CAPTURE_MODES, f"producer.capture_mode must be one of: {', '.join(sorted(ALLOWED_CAPTURE_MODES))}.", errors)

    decisive_receipt_path = payload.get("decisive_receipt_path")
    if decisive_receipt_path is not None:
        ensure(is_relative_contract_path(decisive_receipt_path), "decisive_receipt_path must be an ATLAS-relative path when present.", errors)

    changed_files = payload.get("changed_files")
    ensure(isinstance(changed_files, list), "changed_files must be an array.", errors)
    if isinstance(changed_files, list):
        for index, item in enumerate(changed_files):
            ensure(isinstance(item, dict), f"changed_files[{index}] must be an object.", errors)
            if not isinstance(item, dict):
                continue
            unexpected = sorted(set(item.keys()) - {"path", "summary", "status"})
            ensure(not unexpected, f"changed_files[{index}] contains unsupported fields: {', '.join(unexpected)}.", errors)
            ensure(is_relative_contract_path(item.get("path")), f"changed_files[{index}].path must be an ATLAS-relative path.", errors)
            ensure(is_non_empty_string(item.get("summary")), f"changed_files[{index}].summary must be a non-empty string.", errors)
            ensure(is_non_empty_string(item.get("status")), f"changed_files[{index}].status must be a non-empty string.", errors)

    validation_snapshot = payload.get("validation_snapshot")
    ensure(isinstance(validation_snapshot, dict), "validation_snapshot must be an object.", errors)
    if isinstance(validation_snapshot, dict):
        unexpected = sorted(set(validation_snapshot.keys()) - {"command", "critical", "error", "warning", "info", "classification", "summary"})
        ensure(not unexpected, f"validation_snapshot contains unsupported fields: {', '.join(unexpected)}.", errors)
        ensure(is_non_empty_string(validation_snapshot.get("command")), "validation_snapshot.command must be a non-empty string.", errors)
        for key in ("critical", "error", "warning", "info"):
            value = validation_snapshot.get(key)
            ensure(isinstance(value, int) and value >= 0, f"validation_snapshot.{key} must be a non-negative integer.", errors)
        ensure(is_non_empty_string(validation_snapshot.get("classification")), "validation_snapshot.classification must be a non-empty string.", errors)
        ensure(is_non_empty_string(validation_snapshot.get("summary")), "validation_snapshot.summary must be a non-empty string.", errors)

    marker_outcome = payload.get("marker_outcome")
    ensure(isinstance(marker_outcome, dict), "marker_outcome must be an object.", errors)
    if isinstance(marker_outcome, dict):
        unexpected = sorted(set(marker_outcome.keys()) - {"justified", "summary", "items"})
        ensure(not unexpected, f"marker_outcome contains unsupported fields: {', '.join(unexpected)}.", errors)
        ensure(isinstance(marker_outcome.get("justified"), bool), "marker_outcome.justified must be a boolean.", errors)
        ensure(is_non_empty_string(marker_outcome.get("summary")), "marker_outcome.summary must be a non-empty string.", errors)
        items = marker_outcome.get("items")
        ensure(isinstance(items, list), "marker_outcome.items must be an array.", errors)
        if isinstance(items, list):
            for index, item in enumerate(items):
                ensure(isinstance(item, dict), f"marker_outcome.items[{index}] must be an object.", errors)
                if not isinstance(item, dict):
                    continue
                unexpected_item = sorted(set(item.keys()) - {"marker", "movement", "reason"})
                ensure(not unexpected_item, f"marker_outcome.items[{index}] contains unsupported fields: {', '.join(unexpected_item)}.", errors)
                ensure(is_non_empty_string(item.get("marker")), f"marker_outcome.items[{index}].marker must be a non-empty string.", errors)
                ensure(is_non_empty_string(item.get("movement")), f"marker_outcome.items[{index}].movement must be a non-empty string.", errors)
                reason = item.get("reason")
                if reason is not None:
                    ensure(isinstance(reason, str), f"marker_outcome.items[{index}].reason must be a string when present.", errors)

    next_move = payload.get("next_move")
    ensure(isinstance(next_move, dict), "next_move must be an object.", errors)
    if isinstance(next_move, dict):
        unexpected = sorted(set(next_move.keys()) - {"package", "mode", "reason"})
        ensure(not unexpected, f"next_move contains unsupported fields: {', '.join(unexpected)}.", errors)
        ensure(is_non_empty_string(next_move.get("package")), "next_move.package must be a non-empty string.", errors)
        ensure(is_non_empty_string(next_move.get("mode")), "next_move.mode must be a non-empty string.", errors)
        reason = next_move.get("reason")
        if reason is not None:
            ensure(isinstance(reason, str), "next_move.reason must be a string when present.", errors)

    scope_guard = payload.get("scope_guard")
    ensure(isinstance(scope_guard, dict), "scope_guard must be an object.", errors)
    if isinstance(scope_guard, dict):
        unexpected = sorted(set(scope_guard.keys()) - {"widened_scope", "held_lanes_preserved", "non_automated_attempted", "out_of_scope_admissions"})
        ensure(not unexpected, f"scope_guard contains unsupported fields: {', '.join(unexpected)}.", errors)
        ensure(isinstance(scope_guard.get("widened_scope"), bool), "scope_guard.widened_scope must be a boolean.", errors)
        ensure(isinstance(scope_guard.get("held_lanes_preserved"), bool), "scope_guard.held_lanes_preserved must be a boolean.", errors)
        for key in ("non_automated_attempted", "out_of_scope_admissions"):
            value = scope_guard.get(key)
            ensure(isinstance(value, list), f"scope_guard.{key} must be an array.", errors)
            if isinstance(value, list):
                for index, item in enumerate(value):
                    ensure(is_non_empty_string(item), f"scope_guard.{key}[{index}] must be a non-empty string.", errors)

    unexpected_root = sorted(
        set(payload.keys())
        - {
            "contract_version",
            "result_id",
            "generated_at",
            "producer",
            "lane_id",
            "active_slice",
            "summary",
            "changed_files",
            "decisive_receipt_path",
            "validation_snapshot",
            "marker_outcome",
            "next_move",
            "scope_guard",
        }
    )
    ensure(not unexpected_root, f"Result contains unsupported fields: {', '.join(unexpected_root)}.", errors)

    if schema is None:
        schema = load_json(schema_path_default())
    try:
        import jsonschema  # type: ignore

        jsonschema.validate(payload, schema)
    except ModuleNotFoundError:
        pass
    except Exception as exc:
        errors.append(f"jsonschema rejected the result payload: {exc}")

    return errors


def build_synthetic_result() -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "result_id": "result-20260604T180000Z-sample",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "producer": {
            "kind": "test",
            "name": "atlas-synthetic-continuation-result",
            "capture_mode": "schema_json",
            "version": "1",
        },
        "lane_id": "AI Repetition-to-Automation Pipeline",
        "active_slice": "Guarded Codex Continuation Gate Inline-Prompt Resume Execution Proof Pass 23",
        "summary": "Run one bounded live proof for the admitted inline-prompt resume shape and classify timeout or returned-result behavior durably.",
        "changed_files": [
            {
                "path": "ops/codex/atlas_continue_gate.py",
                "summary": "Add bounded live execution timeout classification for inline-prompt resume proof and preserve durable decision receipts on timeout.",
                "status": "modified",
            },
            {
                "path": "docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-GUARDED-CODEX-CONTINUATION-GATE-INLINE-PROMPT-RESUME-EXECUTION-PROOF-PASS-23-2026-06-04.md",
                "summary": "Record one bounded live proof attempt for the admitted inline-prompt resume shape.",
                "status": "added",
            },
        ],
        "decisive_receipt_path": "docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-GUARDED-CODEX-CONTINUATION-GATE-INLINE-PROMPT-RESUME-EXECUTION-PROOF-PASS-23-2026-06-04.md",
        "validation_snapshot": {
            "command": "python ops/validation/validate_stack.py",
            "critical": 0,
            "error": 3,
            "warning": 498,
            "info": 0,
            "classification": "expected in-flight _stack stack.lock.yaml dirty-state drift",
            "summary": "critical=0 error=3 warning=498 info=0",
        },
        "marker_outcome": {
            "justified": False,
            "summary": "No marker movement: this packet freezes the contract boundary around the existing stdin blocker but does not clear a blocker or add repeatable governed execution proof.",
            "items": [
                {
                    "marker": "AI Repetition-to-Automation Pipeline",
                    "movement": "none",
                    "reason": "The lane already ratcheted to 31% when the non-packaged launch blocker was cleared; this pass only freezes the remaining command-contract seam.",
                }
            ],
        },
        "next_move": {
            "package": "AI Repetition-to-Automation Pipeline Guarded Codex Continuation Gate Inline-Prompt Resume Timeout-Boundary And Receipt Discipline Pass 24",
            "mode": "Codex",
            "reason": "The next bounded question is whether the timeout-class result is stable enough to freeze as the new execution boundary or whether one narrower receipt-discipline packet is required.",
        },
        "scope_guard": {
            "widened_scope": False,
            "held_lanes_preserved": True,
            "non_automated_attempted": [],
            "out_of_scope_admissions": [],
        },
    }


def build_synthetic_jsonl_lines(result_payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "event": "session_start",
            "session_id": "atlas-continue-gate-synthetic-session",
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
        {
            "event": "task_start",
            "task_name": "atlas-continue-gate-live-receipt-capture",
        },
        {
            "event": "assistant_output",
            "message": {
                "kind": "summary",
                "text": "Bounded slice finished and wrapper is preparing final capture.",
            },
        },
        {
            "event": "codex_result",
            "payload": result_payload,
        },
    ]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    content = "\n".join(json.dumps(record) for record in records) + "\n"
    path.write_text(content, encoding="utf-8")


def _collect_jsonl_candidates(record: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    candidates: list[tuple[str, dict[str, Any]]] = []
    candidates.append(("root", record))
    for key in JSONL_RESULT_CONTAINER_KEYS:
        value = record.get(key)
        if isinstance(value, dict):
            candidates.append((key, value))
    for key in JSONL_NESTED_CONTAINER_KEYS:
        nested = record.get(key)
        if not isinstance(nested, dict):
            continue
        for nested_key in JSONL_RESULT_CONTAINER_KEYS:
            value = nested.get(nested_key)
            if isinstance(value, dict):
                candidates.append((f"{key}.{nested_key}", value))
    return candidates


def extract_result_payload_from_jsonl(path: Path, schema: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    best_payload: dict[str, Any] | None = None
    best_capture: dict[str, Any] | None = None

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number} is not valid JSON: {exc}")
            continue
        if not isinstance(record, dict):
            continue
        event_label = ""
        for label_key in ("event", "event_type", "type"):
            label_value = record.get(label_key)
            if isinstance(label_value, str) and label_value.strip():
                event_label = label_value.strip()
                break
        for field_path, candidate in _collect_jsonl_candidates(record):
            payload_errors = validate_result_payload(candidate, schema)
            if payload_errors:
                continue
            best_payload = candidate
            best_capture = {
                "kind": "jsonl_final_message",
                "line_number": line_number,
                "field_path": field_path,
                "event_label": event_label or "unknown",
            }

    if best_payload is None:
        if not errors:
            errors.append("no valid ATLAS continuation result payload was found in the JSONL transcript.")
        return None, None, errors
    return best_payload, best_capture, errors


def evaluate_gate(
    payload: dict[str, Any],
    *,
    attempt_count: int,
    max_automatic_continuations: int,
    expected_critical: int,
    expected_error: int,
    allowed_classifications: set[str],
) -> dict[str, Any]:
    reasons: list[str] = []
    notes: list[str] = []
    validation_snapshot = payload["validation_snapshot"]
    classification = normalize_label(validation_snapshot["classification"])
    next_move = payload["next_move"]
    next_move_mode = normalize_label(next_move["mode"])
    next_move_package = str(next_move["package"]).strip()
    scope_guard = payload["scope_guard"]
    marker_outcome = payload["marker_outcome"]

    if attempt_count >= max_automatic_continuations:
        reasons.append(
            f"automatic continuation cap reached: attempt_count={attempt_count}, max_automatic_continuations={max_automatic_continuations}"
        )

    if validation_snapshot["critical"] > expected_critical:
        reasons.append(
            f"validator critical count worsened beyond expected baseline: {validation_snapshot['critical']} > {expected_critical}"
        )

    if validation_snapshot["error"] > expected_error:
        reasons.append(f"validator error count worsened beyond expected baseline: {validation_snapshot['error']} > {expected_error}")

    if classification not in allowed_classifications:
        reasons.append(
            "validator classification is not admitted for unattended continuation: "
            f"{validation_snapshot['classification']}"
        )

    if NONE_NEXT_MOVE_PATTERN.match(next_move_package):
        reasons.append("next_move.package does not provide a machine-readable bounded continuation target.")

    if next_move_mode not in ALLOWED_RESULT_MODES:
        reasons.append(f"next_move.mode is not an admitted continuation mode: {next_move['mode']}")

    if scope_guard["widened_scope"]:
        reasons.append("scope widened beyond the active admitted slice.")

    if not scope_guard["held_lanes_preserved"]:
        reasons.append("held lanes were not preserved.")

    if scope_guard["out_of_scope_admissions"]:
        reasons.append(
            "out-of-scope admissions were reported: " + ", ".join(scope_guard["out_of_scope_admissions"])
        )

    if scope_guard["non_automated_attempted"]:
        reasons.append(
            "explicitly non-automated classes were attempted: " + ", ".join(scope_guard["non_automated_attempted"])
        )

    marker_items = marker_outcome["items"]
    moved_items = [item for item in marker_items if normalize_label(item["movement"]) != "none"]
    if moved_items and not marker_outcome["justified"]:
        reasons.append("marker movement was reported without explicit justification.")
    elif moved_items:
        notes.append("marker movement is present and explicitly justified.")
    else:
        notes.append("no marker movement reported.")

    decision = "continue" if not reasons else "stop"
    return {
        "decision": decision,
        "reasons": reasons,
        "notes": notes,
        "next_move": payload["next_move"],
        "validation_snapshot": payload["validation_snapshot"],
    }


def render_markdown_summary(result_payload: dict[str, Any], decision_payload: dict[str, Any]) -> str:
    validation = result_payload["validation_snapshot"]
    next_move = result_payload["next_move"]
    lines = [
        f"# ATLAS Codex Continuation Gate Decision - {result_payload['result_id']}",
        "",
        f"- Evaluated at: `{decision_payload['evaluated_at']}`",
        f"- Decision: `{decision_payload['decision']}`",
        f"- Dry run: `{str(decision_payload['dry_run']).lower()}`",
        f"- Result file: `{decision_payload['result_file']}`",
        f"- Lane: `{result_payload['lane_id']}`",
        f"- Active slice: `{result_payload['active_slice']}`",
        f"- Validation snapshot: `{validation['summary']}`",
        f"- Validation classification: `{validation['classification']}`",
        f"- Next move: `{next_move['package']}`",
        f"- Next mode: `{next_move['mode']}`",
    ]
    capture_source = decision_payload.get("capture_source")
    if isinstance(capture_source, dict):
        lines.append(
            "- Capture source: "
            f"`{capture_source.get('kind', 'unknown')}` "
            f"line `{capture_source.get('line_number', 'unknown')}` "
            f"field `{capture_source.get('field_path', 'unknown')}`"
        )
    execution = decision_payload.get("execution")
    if isinstance(execution, dict):
        lines.append(f"- Execution status: `{execution.get('status', 'unknown')}`")
        lines.append(f"- Live execution requested: `{str(decision_payload.get('live_execution_requested', False)).lower()}`")
        lines.append(f"- Live execution explicitly allowed: `{str(decision_payload.get('live_execution_explicitly_allowed', False)).lower()}`")
        classification = execution.get("classification")
        if isinstance(classification, str) and classification.strip():
            lines.append(f"- Execution classification: `{classification}`")
        command_shape = execution.get("command_shape")
        if isinstance(command_shape, str) and command_shape.strip():
            lines.append(f"- Execution command shape: `{command_shape}`")
        resolved_executable = execution.get("resolved_executable")
        if isinstance(resolved_executable, str) and resolved_executable.strip():
            lines.append(f"- Resolved executable: `{resolved_executable}`")
        launch_mode = execution.get("launch_mode")
        if isinstance(launch_mode, str) and launch_mode.strip():
            lines.append(f"- Execution launch mode: `{launch_mode}`")
        returncode = execution.get("returncode")
        if isinstance(returncode, int):
            lines.append(f"- Execution returncode: `{returncode}`")
        timeout_seconds = execution.get("timeout_seconds")
        if isinstance(timeout_seconds, int):
            lines.append(f"- Execution timeout boundary: `{timeout_seconds}s`")
        launch_command = execution.get("launch_command")
        if isinstance(launch_command, list) and launch_command:
            lines.append("- Execution launch command:")
            for item in launch_command:
                lines.append(f"  - `{item}`")
        timeout_teardown_method = execution.get("timeout_teardown_method")
        if isinstance(timeout_teardown_method, str) and timeout_teardown_method.strip():
            lines.append(f"- Timeout teardown method: `{timeout_teardown_method}`")
        timeout_teardown_returncode = execution.get("timeout_teardown_returncode")
        if isinstance(timeout_teardown_returncode, int):
            lines.append(f"- Timeout teardown returncode: `{timeout_teardown_returncode}`")
        details = execution.get("details")
        if isinstance(details, str) and details.strip():
            lines.append(f"- Execution details: `{details}`")
        stderr = execution.get("stderr")
        if isinstance(stderr, str) and stderr.strip():
            lines.append("- Execution stderr:")
            for line in stderr.rstrip().splitlines():
                lines.append(f"  - `{line}`")
        timeout_teardown_stdout = execution.get("timeout_teardown_stdout")
        if isinstance(timeout_teardown_stdout, str) and timeout_teardown_stdout.strip():
            lines.append("- Timeout teardown stdout:")
            for line in timeout_teardown_stdout.rstrip().splitlines():
                lines.append(f"  - `{line}`")
        timeout_teardown_stderr = execution.get("timeout_teardown_stderr")
        if isinstance(timeout_teardown_stderr, str) and timeout_teardown_stderr.strip():
            lines.append("- Timeout teardown stderr:")
            for line in timeout_teardown_stderr.rstrip().splitlines():
                lines.append(f"  - `{line}`")
    runtime_surface_probe = decision_payload.get("runtime_surface_probe")
    if isinstance(runtime_surface_probe, dict):
        lines.append(f"- Runtime surface classification: `{runtime_surface_probe.get('classification', 'unknown')}`")
        lines.append(f"- Runtime resolved executable: `{runtime_surface_probe.get('resolved_executable', 'unknown')}`")
        lines.append(f"- Runtime version status: `{runtime_surface_probe.get('version_status', 'unknown')}`")
        version_output = runtime_surface_probe.get("version_output")
        if isinstance(version_output, str) and version_output.strip():
            lines.append(f"- Runtime version output: `{version_output}`")
        lines.append(
            "- Lower-priority WindowsApps present: "
            f"`{str(runtime_surface_probe.get('lower_priority_windowsapps_present', False)).lower()}`"
        )
        command_order = runtime_surface_probe.get("command_order")
        if isinstance(command_order, list) and command_order:
            lines.append("- Runtime command order:")
            for item in command_order:
                lines.append(f"  - `{item}`")
    resume_contract_probe = decision_payload.get("resume_contract_probe")
    if isinstance(resume_contract_probe, dict):
        lines.append(f"- Resume contract classification: `{resume_contract_probe.get('classification', 'unknown')}`")
        lines.append(f"- Resume contract status: `{resume_contract_probe.get('help_status', 'unknown')}`")
        lines.append(f"- Resume contract resolved executable: `{resume_contract_probe.get('resolved_executable', 'unknown')}`")
        lines.append(
            "- Resume prompt argument supported: "
            f"`{str(resume_contract_probe.get('prompt_argument_supported', False)).lower()}`"
        )
        lines.append(
            "- Resume dash-stdin supported: "
            f"`{str(resume_contract_probe.get('stdin_dash_supported', False)).lower()}`"
        )
        lines.append(
            "- Current admitted command omits prompt: "
            f"`{str(resume_contract_probe.get('current_admitted_shape_omits_prompt', False)).lower()}`"
        )
        usage_lines = resume_contract_probe.get("usage_lines")
        if isinstance(usage_lines, list) and usage_lines:
            lines.append("- Resume usage lines:")
            for item in usage_lines:
                lines.append(f"  - `{item}`")
    lines.extend(
        [
            "",
            "## Reasons",
        ]
    )
    reasons = decision_payload["reasons"] or ["none"]
    for reason in reasons:
        lines.append(f"- {reason}")
    lines.extend(
        [
            "",
            "## Notes",
        ]
    )
    notes = decision_payload["notes"] or ["none"]
    for note in notes:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def write_decision_artifacts(result_path: Path, result_payload: dict[str, Any], decision_payload: dict[str, Any]) -> list[str]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = repo_root() / "runtime" / "receipts" / "codex-continuation" / datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{stamp}-{result_payload['result_id']}"
    json_path = output_dir / f"{stem}.decision.json"
    md_path = output_dir / f"{stem}.decision.md"

    decision_payload = dict(decision_payload)
    decision_payload["artifact_version"] = DECISION_VERSION
    decision_payload["result_id"] = result_payload["result_id"]
    decision_payload["result_file"] = normalize_slashes(str(result_path.relative_to(repo_root())))
    decision_payload["lane_id"] = result_payload["lane_id"]
    decision_payload["active_slice"] = result_payload["active_slice"]

    json_path.write_text(json.dumps(decision_payload, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown_summary(result_payload, decision_payload), encoding="utf-8")
    return [
        normalize_slashes(str(json_path.relative_to(repo_root()))),
        normalize_slashes(str(md_path.relative_to(repo_root()))),
    ]


def maybe_execute_continue(
    command: str | None,
    *,
    dry_run: bool,
    allow_live_execution: bool,
    gate_decision: dict[str, Any],
    capture_details: dict[str, Any] | None,
    execution_timeout_seconds: int,
) -> dict[str, Any] | None:
    if command is None:
        return None
    if gate_decision["decision"] != "continue":
        return {
            "status": "blocked",
            "classification": "gate_not_continue",
            "details": "gate decision is not continue; execution remains blocked.",
            "command": command,
        }
    admitted_command, admission_error = extract_admitted_resume_command(command)
    if admitted_command is None:
        return {
            "status": "blocked",
            "classification": "non_resume_command_shape",
            "details": admission_error or "live execution only admits one exact resume command shape.",
            "command": command,
        }
    command_shape = classify_admitted_resume_command(admitted_command)
    if dry_run:
        return {
            "status": "skipped",
            "classification": "dry_run",
            "details": "dry_run=true; continuation command was not executed.",
            "command": " ".join(admitted_command),
            "command_shape": command_shape,
        }
    if not allow_live_execution:
        return {
            "status": "blocked",
            "classification": "missing_live_allow",
            "details": "live execution requires --allow-live-execution in addition to --no-dry-run.",
            "command": " ".join(admitted_command),
            "command_shape": command_shape,
        }
    if capture_details is None or capture_details.get("kind") != "jsonl_final_message":
        return {
            "status": "blocked",
            "classification": "missing_wrapper_capture",
            "details": "live execution requires wrapper-bound JSONL receipt capture before the command may run.",
            "command": " ".join(admitted_command),
            "command_shape": command_shape,
        }
    runtime_probe = build_resume_runtime_probe(admitted_command[0])
    launch_command, launch_mode = build_resume_launch_command(admitted_command, runtime_probe)
    try:
        process = subprocess.Popen(
            launch_command,
            cwd=repo_root(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as exc:
        classification = classify_runtime_start_failure(runtime_probe, exc)
        return {
            "status": "blocked",
            "classification": classification,
            "details": f"real Codex resume command could not start on this host: {exc}",
            "command": " ".join(admitted_command),
            "command_shape": command_shape,
            "launch_command": launch_command,
            "launch_mode": launch_mode,
            "resolved_executable": runtime_probe["resolved_executable"],
            "runtime_probe": runtime_probe,
        }

    try:
        stdout, stderr = process.communicate(timeout=execution_timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        teardown_method = "process_kill"
        teardown_returncode: int | None = None
        teardown_stdout = ""
        teardown_stderr = ""
        if os.name == "nt":
            teardown_method = "taskkill_tree_force"
            teardown_completed = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                text=True,
                check=False,
            )
            teardown_returncode = teardown_completed.returncode
            teardown_stdout = teardown_completed.stdout or ""
            teardown_stderr = teardown_completed.stderr or ""
        else:
            process.kill()
        try:
            stdout, stderr = process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            stdout = ""
            stderr = ""
        return {
            "status": "blocked",
            "classification": "resume_command_timeout",
            "details": f"bounded live execution exceeded {execution_timeout_seconds}s before a durable result returned.",
            "command": " ".join(admitted_command),
            "command_shape": command_shape,
            "launch_command": launch_command,
            "launch_mode": launch_mode,
            "resolved_executable": runtime_probe["resolved_executable"],
            "runtime_probe": runtime_probe,
            "timeout_seconds": execution_timeout_seconds,
            "returncode": process.returncode,
            "stdout": (stdout or exc.stdout or "")[-4000:],
            "stderr": (stderr or exc.stderr or "")[-4000:],
            "timeout_teardown_method": teardown_method,
            "timeout_teardown_returncode": teardown_returncode,
            "timeout_teardown_stdout": teardown_stdout[-4000:],
            "timeout_teardown_stderr": teardown_stderr[-4000:],
        }
    completed = subprocess.CompletedProcess(
        args=launch_command,
        returncode=process.returncode,
        stdout=stdout,
        stderr=stderr,
    )
    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "classification": classify_resume_command_completion(completed),
        "command": " ".join(admitted_command),
        "command_shape": command_shape,
        "launch_command": launch_command,
        "launch_mode": launch_mode,
        "resolved_executable": runtime_probe["resolved_executable"],
        "runtime_probe": runtime_probe,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }


def print_preview(payload: dict[str, Any], gate_decision: dict[str, Any]) -> None:
    print(f"Result id    : {payload['result_id']}")
    print(f"Lane         : {payload['lane_id']}")
    print(f"Active slice : {payload['active_slice']}")
    print(f"Decision     : {gate_decision['decision']}")
    print(f"Validation   : {payload['validation_snapshot']['summary']}")
    print(f"Next move    : {payload['next_move']['package']}")
    execution = gate_decision.get("execution")
    if isinstance(execution, dict):
        print(f"Execution    : {execution.get('status', 'unknown')}")
        classification = execution.get("classification")
        if isinstance(classification, str) and classification.strip():
            print(f"Exec class   : {classification}")
        command_shape = execution.get("command_shape")
        if isinstance(command_shape, str) and command_shape.strip():
            print(f"Exec shape   : {command_shape}")
        resolved_executable = execution.get("resolved_executable")
        if isinstance(resolved_executable, str) and resolved_executable.strip():
            print(f"Exec path    : {resolved_executable}")
        launch_mode = execution.get("launch_mode")
        if isinstance(launch_mode, str) and launch_mode.strip():
            print(f"Exec launch  : {launch_mode}")
        returncode = execution.get("returncode")
        if isinstance(returncode, int):
            print(f"Exec code    : {returncode}")
        timeout_seconds = execution.get("timeout_seconds")
        if isinstance(timeout_seconds, int):
            print(f"Exec timeout : {timeout_seconds}s")
        timeout_teardown_method = execution.get("timeout_teardown_method")
        if isinstance(timeout_teardown_method, str) and timeout_teardown_method.strip():
            print(f"Exec teardown: {timeout_teardown_method}")
        timeout_teardown_returncode = execution.get("timeout_teardown_returncode")
        if isinstance(timeout_teardown_returncode, int):
            print(f"Exec tk code : {timeout_teardown_returncode}")
        details = execution.get("details")
        if isinstance(details, str) and details.strip():
            print(f"Exec detail  : {details}")
    runtime_surface_probe = gate_decision.get("runtime_surface_probe")
    if isinstance(runtime_surface_probe, dict):
        print(f"Runtime surf : {runtime_surface_probe.get('classification', 'unknown')}")
        print(f"Runtime path : {runtime_surface_probe.get('resolved_executable', 'unknown')}")
        version_output = runtime_surface_probe.get("version_output")
        if isinstance(version_output, str) and version_output.strip():
            print(f"Runtime ver  : {version_output}")
    resume_contract_probe = gate_decision.get("resume_contract_probe")
    if isinstance(resume_contract_probe, dict):
        print(f"Resume contr : {resume_contract_probe.get('classification', 'unknown')}")
        print(f"Resume path  : {resume_contract_probe.get('resolved_executable', 'unknown')}")
        print(f"Resume prompt: {str(resume_contract_probe.get('prompt_argument_supported', False)).lower()}")
        print(f"Resume dash  : {str(resume_contract_probe.get('stdin_dash_supported', False)).lower()}")
    if gate_decision["reasons"]:
        print("Reasons      :")
        for reason in gate_decision["reasons"]:
            print(f"  - {reason}")


def run_self_test(schema: dict[str, Any]) -> int:
    cases: list[tuple[str, dict[str, Any], str]] = []

    valid = build_synthetic_result()
    cases.append(("valid bounded next move is admitted", valid, "continue"))

    doctrine_block = json.loads(json.dumps(valid))
    doctrine_block["scope_guard"]["non_automated_attempted"] = ["doctrine admission"]
    cases.append(("forbidden doctrine admission blocks continuation", doctrine_block, "stop"))

    missing_validation = json.loads(json.dumps(valid))
    missing_validation.pop("validation_snapshot", None)
    cases.append(("missing validator snapshot blocks continuation", missing_validation, "invalid"))

    widened_scope = json.loads(json.dumps(valid))
    widened_scope["scope_guard"]["widened_scope"] = True
    widened_scope["scope_guard"]["out_of_scope_admissions"] = ["reopened held lane"]
    cases.append(("widened scope blocks continuation", widened_scope, "stop"))

    destructive_cleanup = json.loads(json.dumps(valid))
    destructive_cleanup["scope_guard"]["non_automated_attempted"] = ["destructive cleanup / secret approval"]
    cases.append(("explicitly non-automated class blocks continuation", destructive_cleanup, "stop"))

    expected_dirty_state = json.loads(json.dumps(valid))
    expected_dirty_state["validation_snapshot"]["classification"] = "expected dirty-state drift"
    cases.append(("expected dirty-state drift classification stays admissible", expected_dirty_state, "continue"))

    passed = 0
    for name, payload, expected in cases:
        payload_errors = validate_result_payload(payload, schema)
        if expected == "invalid":
            ok = bool(payload_errors)
        else:
            if payload_errors:
                ok = False
            else:
                decision = evaluate_gate(
                    payload,
                    attempt_count=0,
                    max_automatic_continuations=3,
                    expected_critical=0,
                    expected_error=3,
                    allowed_classifications={normalize_label(item) for item in DEFAULT_ALLOWED_CLASSIFICATIONS},
                )
                ok = decision["decision"] == expected
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}")
        if not ok and payload_errors:
            for error in payload_errors:
                print(f"  - {error}")
        passed += 1 if ok else 0

    live_capture = {
        "kind": "jsonl_final_message",
        "line_number": 4,
        "field_path": "payload",
        "event_label": "codex_result",
    }
    exact_resume_tokens, exact_resume_error = extract_admitted_resume_command("codex exec resume --last")
    exact_resume_ok = exact_resume_tokens == ["codex", "exec", "resume", "--last"] and exact_resume_error is None
    print(f"[{'PASS' if exact_resume_ok else 'FAIL'}] exact real resume command shape is admitted")
    passed += 1 if exact_resume_ok else 0

    quoted_resume_tokens, quoted_resume_error = extract_admitted_resume_command('"C:\\tools\\codex.exe" exec resume --last')
    quoted_resume_ok = quoted_resume_tokens == ['C:\\tools\\codex.exe', "exec", "resume", "--last"] and quoted_resume_error is None
    print(f"[{'PASS' if quoted_resume_ok else 'FAIL'}] quoted codex executable path with exact resume suffix is admitted")
    passed += 1 if quoted_resume_ok else 0

    inline_prompt_tokens, inline_prompt_error = extract_admitted_resume_command('codex exec resume --last "Continue only the next already-admitted bounded slice."')
    inline_prompt_ok = (
        inline_prompt_tokens == ["codex", "exec", "resume", "--last", '"Continue only the next already-admitted bounded slice."']
        and inline_prompt_error is None
        and classify_admitted_resume_command(inline_prompt_tokens) == "inline_prompt_resume_last"
    )
    print(f"[{'PASS' if inline_prompt_ok else 'FAIL'}] inline prompt-bearing resume shape is admitted")
    passed += 1 if inline_prompt_ok else 0

    dash_prompt_tokens, dash_prompt_error = extract_admitted_resume_command("codex exec resume --last -")
    dash_prompt_ok = dash_prompt_tokens is None and dash_prompt_error is not None and "dash-stdin" in dash_prompt_error
    print(f"[{'PASS' if dash_prompt_ok else 'FAIL'}] dash-stdin prompt injection remains blocked")
    passed += 1 if dash_prompt_ok else 0

    windowsapps_probe = build_resume_runtime_probe(r"C:\Program Files\WindowsApps\OpenAI.Codex_26.601.2237.0_x64__2p2nqsd0c76g0\app\resources\codex.exe")
    windowsapps_probe_ok = windowsapps_probe["windowsapps_packaged"] and windowsapps_probe["openai_codex_packaged"]
    print(f"[{'PASS' if windowsapps_probe_ok else 'FAIL'}] WindowsApps Codex probe classification is detected")
    passed += 1 if windowsapps_probe_ok else 0

    synthetic_access_denied = PermissionError(5, "Access is denied")
    synthetic_access_denied.winerror = 5  # type: ignore[attr-defined]
    runtime_failure_classification = classify_runtime_start_failure(windowsapps_probe, synthetic_access_denied)
    runtime_failure_classification_ok = runtime_failure_classification == "windowsapps_packaged_codex_start_access_denied"
    print(f"[{'PASS' if runtime_failure_classification_ok else 'FAIL'}] WindowsApps access-denied start failure gets exact runtime classification")
    passed += 1 if runtime_failure_classification_ok else 0

    non_packaged_probe = {
        "exists": True,
        "windowsapps_packaged": False,
        "version_failure_classification": None,
    }
    non_packaged_classification = classify_runtime_surface_probe(
        non_packaged_probe,
        version_status="passed",
        version_returncode=0,
        under_npm_global_prefix=True,
    )
    non_packaged_classification_ok = non_packaged_classification == "non_packaged_npm_codex_launchable"
    print(f"[{'PASS' if non_packaged_classification_ok else 'FAIL'}] non-packaged npm Codex launchable surface gets exact runtime classification")
    passed += 1 if non_packaged_classification_ok else 0

    synthetic_cmd_shim = "tmp/synthetic-npm-bin/codex.cmd"
    synthetic_resolved_cmd_shim = "tmp/synthetic-npm-bin/codex.CMD"
    cmd_launch_command, cmd_launch_mode = build_resume_launch_command(
        [synthetic_cmd_shim, "exec", "resume", "--last"],
        {"resolved_executable": synthetic_resolved_cmd_shim},
    )
    cmd_launch_ok = cmd_launch_command[:3] == ["cmd.exe", "/c", synthetic_resolved_cmd_shim] and cmd_launch_mode == "windows_cmd_shim"
    print(f"[{'PASS' if cmd_launch_ok else 'FAIL'}] Windows .cmd Codex surfaces launch through cmd.exe shims")
    passed += 1 if cmd_launch_ok else 0

    stdin_required_completed = subprocess.CompletedProcess(
        args=["codex", "exec", "resume", "--last"],
        returncode=1,
        stdout="",
        stderr="Reading prompt from stdin...\nNo prompt provided via stdin.\n",
    )
    stdin_required_classification = classify_resume_command_completion(stdin_required_completed)
    stdin_required_ok = stdin_required_classification == "resume_requires_stdin_prompt"
    print(f"[{'PASS' if stdin_required_ok else 'FAIL'}] stdin-required resume failure gets exact runtime classification")
    passed += 1 if stdin_required_ok else 0

    sample_resume_help = """Resume a previous session by id or pick the most recent with --last

Usage: codex exec resume [OPTIONS] [SESSION_ID] [PROMPT]

Arguments:
  [SESSION_ID]
          Conversation/session id (UUID) or thread name.

  [PROMPT]
          Prompt to send after resuming the session. If `-` is used, read from stdin
"""
    parsed_resume_help = parse_resume_contract_help(sample_resume_help)
    parsed_resume_help_ok = (
        parsed_resume_help["prompt_argument_supported"]
        and parsed_resume_help["stdin_dash_supported"]
        and parsed_resume_help["session_id_supported"]
    )
    print(f"[{'PASS' if parsed_resume_help_ok else 'FAIL'}] resume help parsing detects prompt and dash-stdin support")
    passed += 1 if parsed_resume_help_ok else 0

    resume_contract_classification = classify_resume_contract_probe(
        help_status="passed",
        help_returncode=0,
        prompt_argument_supported=True,
        stdin_dash_supported=True,
    )
    resume_contract_classification_ok = resume_contract_classification == "resume_prompt_arg_and_stdin_dash_supported"
    print(f"[{'PASS' if resume_contract_classification_ok else 'FAIL'}] resume contract probe classifies prompt-bearing dash-stdin support exactly")
    passed += 1 if resume_contract_classification_ok else 0

    timeout_capture = maybe_execute_continue(
        "codex exec resume --last continue",
        dry_run=False,
        allow_live_execution=True,
        gate_decision={"decision": "continue"},
        capture_details=live_capture,
        execution_timeout_seconds=0,
    )
    timeout_ok = (
        timeout_capture is not None
        and timeout_capture["status"] == "blocked"
        and timeout_capture["classification"] == "resume_command_timeout"
    )
    print(f"[{'PASS' if timeout_ok else 'FAIL'}] bounded live execution timeout is classified durably")
    passed += 1 if timeout_ok else 0

    blocked_without_allow = maybe_execute_continue(
        "codex exec resume --last",
        dry_run=False,
        allow_live_execution=False,
        gate_decision={"decision": "continue"},
        capture_details=live_capture,
        execution_timeout_seconds=30,
    )
    blocked_without_allow_ok = blocked_without_allow is not None and blocked_without_allow["status"] == "blocked"
    print(f"[{'PASS' if blocked_without_allow_ok else 'FAIL'}] live execution stays blocked without explicit allow flag")
    passed += 1 if blocked_without_allow_ok else 0

    blocked_without_jsonl = maybe_execute_continue(
        "codex exec resume --last",
        dry_run=False,
        allow_live_execution=True,
        gate_decision={"decision": "continue"},
        capture_details=None,
        execution_timeout_seconds=30,
    )
    blocked_without_jsonl_ok = blocked_without_jsonl is not None and blocked_without_jsonl["status"] == "blocked"
    print(f"[{'PASS' if blocked_without_jsonl_ok else 'FAIL'}] live execution stays blocked without wrapper-bound JSONL capture")
    passed += 1 if blocked_without_jsonl_ok else 0

    blocked_non_resume_shape = maybe_execute_continue(
        f'"{sys.executable}" -c "print(\'continuation-enable-proof\')"',
        dry_run=False,
        allow_live_execution=True,
        gate_decision={"decision": "continue"},
        capture_details=live_capture,
        execution_timeout_seconds=30,
    )
    blocked_non_resume_shape_ok = (
        blocked_non_resume_shape is not None
        and blocked_non_resume_shape["status"] == "blocked"
        and "inline-prompt variant" in blocked_non_resume_shape.get("details", "")
    )
    print(f"[{'PASS' if blocked_non_resume_shape_ok else 'FAIL'}] explicit allow plus wrapper capture still block non-resume command shapes")
    passed += 1 if blocked_non_resume_shape_ok else 0

    with tempfile.TemporaryDirectory() as temp_dir:
        jsonl_path = Path(temp_dir) / "atlas-continue-gate.live-shaped.jsonl"
        write_jsonl(jsonl_path, build_synthetic_jsonl_lines(valid))
        extracted_payload, capture_details, extraction_errors = extract_result_payload_from_jsonl(jsonl_path, schema)
        extraction_ok = (
            not extraction_errors
            and extracted_payload is not None
            and extracted_payload["result_id"] == valid["result_id"]
            and capture_details is not None
            and capture_details["field_path"] == "payload"
        )
        print(f"[{'PASS' if extraction_ok else 'FAIL'}] live-shaped JSONL receipt capture extracts one valid result payload")
        if not extraction_ok:
            for error in extraction_errors:
                print(f"  - {error}")
        passed += 1 if extraction_ok else 0
        total_cases = len(cases) + 16
    print(f"Self-test summary: {passed}/{total_cases} passed")
    return 0 if passed == total_cases else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate whether an ATLAS Codex result is safe for guarded continuation.")
    parser.add_argument("--schema-file", default=str(schema_path_default()))
    parser.add_argument("--result-file")
    parser.add_argument("--jsonl-file")
    parser.add_argument("--write-synthetic")
    parser.add_argument("--write-synthetic-jsonl")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--attempt-count", type=int, default=0)
    parser.add_argument("--max-automatic-continuations", type=int, default=3)
    parser.add_argument("--expected-critical", type=int, default=0)
    parser.add_argument("--expected-error", type=int, default=3)
    parser.add_argument(
        "--allowed-classification",
        action="append",
        dest="allowed_classifications",
        default=[],
        help="Repeatable admitted validation classification. Defaults admit expected dirty-state drift.",
    )
    parser.add_argument("--probe-runtime-surface", action="store_true", help="Record the currently active Codex runtime surface classification without running live continuation.")
    parser.add_argument("--probe-resume-contract", action="store_true", help="Record the current `codex exec resume --help` prompt/stdin contract without running live prompt-bearing continuation.")
    parser.add_argument("--runtime-executable", default="codex", help="Executable name to classify when --probe-runtime-surface is used.")
    parser.add_argument("--allow-live-execution", action="store_true", help="Explicitly allow one bounded live command after the gate passes, wrapper-bound JSONL capture exists, and the command matches one admitted resume shape.")
    parser.add_argument("--execute-command", help="Optional continuation command to run only after the gate passes. Live execution admits only the exact real `codex exec resume --last` shape or one exact inline-prompt variant.")
    parser.add_argument("--execution-timeout-seconds", type=int, default=90, help="Maximum seconds to allow one bounded live command before classifying timeout and stopping.")
    parser.add_argument("--no-dry-run", action="store_true", help="Allow the execute command to run when the gate passes.")
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

    if args.self_test:
        return run_self_test(schema)

    result_path: Path | None = None
    jsonl_path: Path | None = None
    if args.write_synthetic:
        result_path = Path(args.write_synthetic).resolve()
        result_path.parent.mkdir(parents=True, exist_ok=True)
        synthetic = build_synthetic_result()
        result_path.write_text(json.dumps(synthetic, indent=2), encoding="utf-8")
        print(f"Synthetic result written: {normalize_slashes(str(result_path))}")
    else:
        synthetic = build_synthetic_result()

    if args.write_synthetic_jsonl:
        jsonl_path = Path(args.write_synthetic_jsonl).resolve()
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        write_jsonl(jsonl_path, build_synthetic_jsonl_lines(synthetic))
        print(f"Synthetic JSONL transcript written: {normalize_slashes(str(jsonl_path))}")

    if args.result_file:
        result_path = Path(args.result_file).resolve()

    if args.jsonl_file:
        jsonl_path = Path(args.jsonl_file).resolve()

    if result_path is None and jsonl_path is None:
        print("No input file provided. Use --result-file, --jsonl-file, --write-synthetic, --write-synthetic-jsonl, or --self-test.", file=sys.stderr)
        return 1

    capture_details: dict[str, Any] | None = None
    input_path: Path
    if jsonl_path is not None:
        if not jsonl_path.exists():
            print(f"JSONL transcript not found: {normalize_slashes(str(jsonl_path))}", file=sys.stderr)
            return 1
        payload, capture_details, extraction_errors = extract_result_payload_from_jsonl(jsonl_path, schema)
        if extraction_errors:
            print("JSONL extraction failed:", file=sys.stderr)
            for error in extraction_errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        if payload is None:
            print("JSONL extraction failed: no valid result payload was extracted.", file=sys.stderr)
            return 1
        input_path = jsonl_path
    else:
        if result_path is None or not result_path.exists():
            print(f"Result file not found: {normalize_slashes(str(result_path))}", file=sys.stderr)
            return 1
        payload = load_json(result_path)
        if not isinstance(payload, dict):
            print("Result file must deserialize to a JSON object.", file=sys.stderr)
            return 1
        payload_errors = validate_result_payload(payload, schema)
        if payload_errors:
            print("Result validation failed:", file=sys.stderr)
            for error in payload_errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        input_path = result_path

    gate_decision = evaluate_gate(
        payload,
        attempt_count=args.attempt_count,
        max_automatic_continuations=args.max_automatic_continuations,
        expected_critical=args.expected_critical,
        expected_error=args.expected_error,
        allowed_classifications={
            normalize_label(item) for item in (args.allowed_classifications or list(DEFAULT_ALLOWED_CLASSIFICATIONS))
        },
    )
    evaluated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    decision_payload: dict[str, Any] = {
        "evaluated_at": evaluated_at,
        "decision": gate_decision["decision"],
        "dry_run": not args.no_dry_run,
        "live_execution_requested": bool(args.execute_command and args.no_dry_run),
        "live_execution_explicitly_allowed": args.allow_live_execution,
        "attempt_count": args.attempt_count,
        "max_automatic_continuations": args.max_automatic_continuations,
        "reasons": gate_decision["reasons"],
        "notes": gate_decision["notes"],
        "validation_snapshot": gate_decision["validation_snapshot"],
        "next_move": gate_decision["next_move"],
    }
    if capture_details is not None:
        decision_payload["capture_source"] = capture_details
    if args.probe_runtime_surface:
        runtime_surface_probe = build_runtime_surface_probe(args.runtime_executable)
        decision_payload["runtime_surface_probe"] = runtime_surface_probe
        gate_decision["runtime_surface_probe"] = runtime_surface_probe
    if args.probe_resume_contract:
        resume_contract_probe = build_resume_contract_probe(args.runtime_executable)
        decision_payload["resume_contract_probe"] = resume_contract_probe
        gate_decision["resume_contract_probe"] = resume_contract_probe
    execution = maybe_execute_continue(
        args.execute_command,
        dry_run=not args.no_dry_run,
        allow_live_execution=args.allow_live_execution,
        gate_decision=gate_decision,
        capture_details=capture_details,
        execution_timeout_seconds=args.execution_timeout_seconds,
    )
    if execution is not None:
        decision_payload["execution"] = execution
        gate_decision["execution"] = execution

    written = write_decision_artifacts(input_path, payload, decision_payload)
    decision_payload["written_artifacts"] = written

    print(f"Result valid: {normalize_slashes(str(input_path))}")
    if capture_details is not None:
        print(
            "Extracted from JSONL: "
            f"line={capture_details['line_number']} field={capture_details['field_path']} event={capture_details['event_label']}"
        )
    print(f"Gate decision: {gate_decision['decision']}")
    for path in written:
        print(f"Decision artifact: {path}")
    if args.preview:
        print_preview(payload, gate_decision)
    return 0 if gate_decision["decision"] == "continue" else 2


if __name__ == "__main__":
    raise SystemExit(main())
