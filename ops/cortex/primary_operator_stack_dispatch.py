from __future__ import annotations

"""Prepare and reconcile bounded Cortex dispatches through the existing _stack runner."""

import argparse
import hashlib
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any

REQUEST_SCHEMA = "atlas.cortex.stack_dispatch_request.v1"
RESULT_SCHEMA = "atlas.cortex.stack_result_correlation.v1"
DURABLE_DECISION_SCHEMA = "atlas.cortex.primary_operator_durable_decision.v1"
ACCEPTANCE_SCHEMA = "atlas.cortex.primary_operator_acceptance.v1"
PRIMARY_RECEIPT_SCHEMA = "atlas.cortex.primary_operator_receipt.v1"
PLAN_SCHEMA = "atlas.cortex.execution_plan.v1"
CONTRACT_VERSION = "atlas.cortex.primary_operator_stack_dispatch_contract.v1"
STACK_JOB_SCHEMA = "atlas.job-envelope.v2"
STACK_RECEIPT_SCHEMA = "atlas.execution-receipt.v2"
STACK_TRACE_ARTIFACT = "codex.stdout.log"


def atlas_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return OrderedDict((str(key), _canonical(value[key])) for key in sorted(value, key=str))
    if isinstance(value, list):
        values = [_canonical(item) for item in value]
        return sorted(values, key=lambda item: json.dumps(item, ensure_ascii=False, separators=(",", ":")))
    return value


def _digest(value: Any) -> str:
    encoded = json.dumps(_canonical(value), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _finding(code: str, detail: str, **extra: Any) -> OrderedDict[str, Any]:
    return OrderedDict((("code", code), ("detail", detail), *sorted(extra.items())))


def _safe_relative(argument: str) -> tuple[str | None, OrderedDict[str, Any] | None]:
    normalized = argument.replace("\\", "/")
    path = Path(argument)
    parts = [part.lower() for part in normalized.split("/") if part not in ("", ".")]
    if path.is_absolute() or (len(argument) > 1 and argument[1] == ":"):
        return None, _finding("absolute_path", "Durable paths must be Atlas-root relative.", path=argument)
    if ".." in parts:
        return None, _finding("parent_traversal", "Path escapes the Atlas root.", path=argument)
    if any(part in {"secrets", "repos", ".codex", ".vercel"} or part.startswith(".env") for part in parts):
        return None, _finding("protected_path", "Path enters a protected source class.", path=argument)
    return normalized, None


def validate_input_path(root: Path, argument: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    normalized, error = _safe_relative(argument)
    if error:
        return None, error
    assert normalized is not None
    if not normalized.endswith(".json") or not (normalized.startswith("tmp/atlas/") or normalized.startswith("runtime/atlas/")):
        return None, _finding("unadmitted_input_path", "Input must be explicit tmp/atlas or runtime/atlas JSON.", path=argument)
    path = root / Path(normalized)
    if not path.is_file():
        return None, _finding("missing_input", "Explicit input does not exist.", path=argument)
    return path, None


def validate_stack_runtime_input(root: Path, argument: str, *, artifact: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    allowed_names = {
        "run_manifest": "run.json",
        "job_envelope": "atlas.job-envelope.v2.json",
        "execution_receipt": "atlas.execution-receipt.v2.json",
        "codex_trace": STACK_TRACE_ARTIFACT,
    }
    expected_name = allowed_names[artifact]
    candidate = Path(argument)
    path = candidate if candidate.is_absolute() else root / candidate
    resolved = path.resolve()
    stack_logs = (root / "repos" / "_stack" / ".codex" / "logs").resolve()
    try:
        resolved.relative_to(stack_logs)
    except ValueError:
        return None, _finding(
            "unadmitted_stack_runtime_path",
            "Stack result inputs must resolve beneath the canonical _stack runtime log root.",
            path=argument,
            artifact=artifact,
        )
    if resolved.name != expected_name:
        return None, _finding(
            "unexpected_stack_runtime_artifact",
            "Stack result input filename does not match the required artifact class.",
            path=argument,
            artifact=artifact,
            expected_name=expected_name,
        )
    if not resolved.is_file():
        return None, _finding("missing_input", "Explicit input does not exist.", path=argument)
    return resolved, None


def validate_output_path(root: Path, argument: str, *, kind: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    normalized, error = _safe_relative(argument)
    if error:
        return None, error
    assert normalized is not None
    allowed = (
        kind == "prompt" and normalized.startswith("tmp/atlas/") and normalized.endswith(".md")
    ) or (
        kind == "request" and normalized.startswith("runtime/atlas/sessions/") and normalized.endswith("/cortex-stack-dispatch-request.json")
    ) or (
        kind == "decision" and normalized.startswith("runtime/atlas/sessions/") and normalized.endswith("/cortex-primary-operator-decision.json")
    ) or (
        kind == "result" and normalized.startswith("runtime/atlas/sessions/") and normalized.endswith("/cortex-stack-result-correlation.json")
    )
    if not allowed:
        return None, _finding("unadmitted_output_path", "Output path does not match the requested dispatch artifact class.", path=argument, kind=kind)
    return root / Path(normalized), None


def _read_json(path: Path) -> tuple[dict[str, Any] | None, OrderedDict[str, Any] | None, str | None]:
    try:
        raw_bytes = path.read_bytes()
        raw = raw_bytes.decode("utf-8")
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, _finding("invalid_json", "Input must be valid UTF-8 JSON.", path=str(path), exception=str(exc)), None
    if not isinstance(value, dict):
        return None, _finding("invalid_json_shape", "Input JSON must be an object.", path=str(path)), None
    return value, None, hashlib.sha256(raw_bytes).hexdigest()


def build_durable_decision(
    *, acceptance: dict[str, Any], primary_receipt: dict[str, Any], plan: dict[str, Any]
) -> OrderedDict[str, Any]:
    seed = OrderedDict(
        (("contract_version", CONTRACT_VERSION), ("acceptance", acceptance),
         ("primary_receipt", primary_receipt), ("plan", plan))
    )
    return OrderedDict(
        (("schema_version", DURABLE_DECISION_SCHEMA),
         ("decision_id", "primary-decision-" + _digest(seed)[:20]),
         ("acceptance_id", acceptance.get("acceptance_id")),
         ("primary_receipt_id", primary_receipt.get("receipt_id")),
         ("plan_id", plan.get("plan_id")),
         ("acceptance", acceptance), ("primary_receipt", primary_receipt), ("plan", plan))
    )


def _render_json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def build_dispatch_request(
    *, acceptance: dict[str, Any], primary_receipt: dict[str, Any], plan: dict[str, Any],
    runtime: dict[str, Any] | None = None, durable_decision_ref: str | None = None,
    durable_decision_sha256: str | None = None,
) -> tuple[OrderedDict[str, Any], list[OrderedDict[str, Any]]]:
    blockers: list[OrderedDict[str, Any]] = []
    if acceptance.get("schema_version") != ACCEPTANCE_SCHEMA or acceptance.get("state") != "accepted":
        blockers.append(_finding("acceptance_not_admitted", "Only an accepted primary-operator decision may dispatch."))
    if primary_receipt.get("schema_version") != PRIMARY_RECEIPT_SCHEMA or primary_receipt.get("status") != "completed":
        blockers.append(_finding("primary_receipt_not_complete", "Primary-operator receipt must be completed."))
    if plan.get("schema_version") != PLAN_SCHEMA or plan.get("safe_to_admit") is not True:
        blockers.append(_finding("plan_not_safe", "Execution plan must be the admitted safe schema."))
    acceptance_id = acceptance.get("acceptance_id")
    plan_id = acceptance.get("plan_id")
    if not isinstance(acceptance_id, str) or not acceptance_id:
        blockers.append(_finding("missing_acceptance_id", "Acceptance identity is required."))
    if primary_receipt.get("acceptance_id") != acceptance_id or primary_receipt.get("plan_id") != plan_id:
        blockers.append(_finding("primary_receipt_correlation_mismatch", "Primary receipt does not correlate to acceptance and plan."))
    if plan.get("plan_id") != plan_id:
        blockers.append(_finding("plan_correlation_mismatch", "Plan does not correlate to the accepted decision."))
    if not durable_decision_ref or not durable_decision_sha256:
        blockers.append(_finding("durable_decision_missing", "Dispatch requires a durable primary-operator decision artifact."))
    runtime_value = OrderedDict(
        (("model", str((runtime or {}).get("model", "gpt-5.6-luna"))),
         ("reasoning", str((runtime or {}).get("reasoning", "low"))),
         ("speed", str((runtime or {}).get("speed", "standard"))),
         ("permissions", "full-access"), ("approval_policy", "never"), ("web_search", "disabled"))
    )
    seed = OrderedDict(
        (("contract_version", CONTRACT_VERSION), ("acceptance", acceptance),
         ("primary_receipt", primary_receipt), ("plan", plan), ("runtime", runtime_value),
         ("durable_decision_ref", durable_decision_ref), ("durable_decision_sha256", durable_decision_sha256))
    )
    request_id = "dispatch-" + _digest(seed)[:20]
    request = OrderedDict(
        (("schema_version", REQUEST_SCHEMA), ("request_id", request_id),
         ("session_id", acceptance_id), ("acceptance_id", acceptance_id),
         ("primary_receipt_id", primary_receipt.get("receipt_id")), ("plan_id", plan_id),
         ("durable_decision", OrderedDict((("path", durable_decision_ref), ("sha256", durable_decision_sha256)))),
         ("target_operator", "_stack"), ("operator_command", "codex:stack:task"),
         ("execution_class", "codex:repo:task"), ("target_repository", "stack"),
         ("runtime", runtime_value),
         ("verified_no_change", OrderedDict((("allowed", True), ("proof_path", ".codex/no-change-proof.json"),
                                             ("assertion_ids", ["dispatch-request-consumed", "no-mutation-confirmed", "read-scope-confirmed"])))),
         ("authority", OrderedDict((("local_capability", "full-access"), ("external_actions", []),
                                    ("push", False), ("deploy", False), ("production", False),
                                    ("discord", False), ("board", False), ("data_mutation", False)))),
         ("no_commit", True), ("manual_push_only", True),
         ("status", "blocked" if blockers else "ready_for_stack_dispatch"),
         ("blockers", sorted(blockers, key=lambda item: (item["code"], item["detail"])))))
    return request, blockers


def render_prompt(request: dict[str, Any], *, request_path: Path) -> str:
    if request.get("status") != "ready_for_stack_dispatch":
        raise ValueError("dispatch_request_not_ready")
    runtime = request["runtime"]
    assertions = request["verified_no_change"]["assertion_ids"]
    return "\n".join(
        [
            "Title: Cortex primary-operator _stack verified no-change canary",
            f"Runtime Model: {runtime['model']}",
            f"Runtime Reasoning: {runtime['reasoning']}",
            f"Runtime Speed: {runtime['speed']}",
            "Runtime Permissions: full-access",
            "Runtime Permission Profile: :danger-full-access",
            "Runtime Approval Policy: never",
            "Runtime Web Search Mode: disabled",
            f"Handoff Ref: {request_path}",
            "Allow No Changes: true",
            "No-Change Proof Path: .codex/no-change-proof.json",
            f"No-Change Assertion IDs: {', '.join(assertions)}",
            "",
            "Objective:",
            "Read the exact Cortex dispatch request named by Handoff Ref and prove this bounded operator canary.",
            "The only Atlas-root file this worker may read directly is the exact Handoff Ref. Repo-local _stack files may be read only as needed for git status and the no-change proof.",
            "Do not recursively enumerate or search C:\\ATLAS. Do not read C:\\ATLAS\\secrets or any secrets/**, .env*, credential, token, or browser-profile path.",
            "Do not modify tracked files. Do not stage, commit, push, deploy, write Discord or boards, or mutate data.",
            "Write UTF-8 JSON to `.codex/no-change-proof.json` with schemaVersion `1.0`, status `passed`, blockers `[]`,",
            "and exactly these passed assertions:",
            "- `dispatch-request-consumed`: evidence includes the request_id and acceptance_id read from the handoff.",
            "- `no-mutation-confirmed`: evidence records changed_paths `[]` and external_actions `[]`.",
            "- `read-scope-confirmed`: evidence records atlas_root_recursive_reads `[]`, secret_reads `[]`, and the exact handoff path read.",
            "Stop after producing the proof and a concise summary.",
            "",
        ]
    )


def _trace_read_scope(trace_text: str, *, root: Path) -> OrderedDict[str, Any]:
    commands: list[str] = []
    violations: list[OrderedDict[str, Any]] = []
    root_windows = str(root.resolve()).replace("/", "\\").lower()
    root_forward = str(root.resolve()).replace("\\", "/").lower()
    for line_number, raw_line in enumerate(trace_text.splitlines(), start=1):
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        item = event.get("item") if isinstance(event, dict) else None
        if not isinstance(item, dict) or item.get("type") != "command_execution":
            continue
        command = item.get("command")
        if not isinstance(command, str):
            continue
        commands.append(command)
        normalized = command.replace("/", "\\").lower()
        if "\\secrets\\" in normalized or "\\secrets'" in normalized or '\\secrets"' in normalized:
            violations.append(_finding("secret_read_command", "Codex command references the protected secrets path.", line=line_number))
        broad_root = root_windows in normalized or root_forward in command.replace("\\", "/").lower()
        recursive = "-recurse" in normalized or " /s " in normalized or "--recursive" in normalized
        if broad_root and recursive:
            violations.append(_finding("atlas_root_recursive_read", "Codex command recursively reads the Atlas root.", line=line_number))
    return OrderedDict(
        (("trace_sha256", hashlib.sha256(trace_text.encode("utf-8")).hexdigest()),
         ("command_count", len(commands)), ("violations", violations),
         ("safe", not violations))
    )


def correlate_result(
    *, request: dict[str, Any], durable_decision: dict[str, Any] | None,
    durable_decision_sha256: str | None, run_manifest: dict[str, Any],
    job_envelope: dict[str, Any], execution_receipt: dict[str, Any], codex_trace: str | None,
    root: Path | None = None,
) -> OrderedDict[str, Any]:
    blockers: list[OrderedDict[str, Any]] = []
    acceptance_id = request.get("acceptance_id")
    if request.get("schema_version") != REQUEST_SCHEMA or request.get("status") != "ready_for_stack_dispatch":
        blockers.append(_finding("invalid_dispatch_request", "Dispatch request is not admitted."))
    durable_ref = request.get("durable_decision") if isinstance(request.get("durable_decision"), dict) else {}
    if (
        not isinstance(durable_decision, dict)
        or durable_decision.get("schema_version") != DURABLE_DECISION_SCHEMA
        or durable_decision.get("acceptance_id") != acceptance_id
        or durable_decision.get("primary_receipt_id") != request.get("primary_receipt_id")
        or durable_decision.get("plan_id") != request.get("plan_id")
        or durable_decision_sha256 != durable_ref.get("sha256")
    ):
        blockers.append(_finding("durable_decision_correlation_mismatch", "Durable primary-operator decision is missing or does not match the dispatch request."))
    if job_envelope.get("contract_version") != STACK_JOB_SCHEMA:
        blockers.append(_finding("invalid_stack_job_envelope", "Stack JobEnvelope schema is not admitted."))
    correlations = job_envelope.get("correlations") if isinstance(job_envelope.get("correlations"), dict) else {}
    if correlations.get("parent_job_id") != acceptance_id:
        blockers.append(_finding("parent_job_correlation_mismatch", "JobEnvelope parent_job_id does not equal the Cortex acceptance identity."))
    job_id = job_envelope.get("job_id")
    if execution_receipt.get("contract_version") != STACK_RECEIPT_SCHEMA or execution_receipt.get("job_id") != job_id:
        blockers.append(_finding("execution_receipt_job_mismatch", "ExecutionReceipt does not correlate to the Stack job."))
    run_id = run_manifest.get("runId") or run_manifest.get("run_id")
    envelope_run = (job_envelope.get("extensions") or {}).get("run_id") if isinstance(job_envelope.get("extensions"), dict) else None
    receipt_run = (execution_receipt.get("extensions") or {}).get("run_id") if isinstance(execution_receipt.get("extensions"), dict) else None
    if not isinstance(run_id, str) or run_id != envelope_run or run_id != receipt_run:
        blockers.append(_finding("run_identity_mismatch", "Run identity is not preserved across manifest, envelope, and receipt."))
    stack_surface = run_manifest.get("atlasContractsV2") if isinstance(run_manifest.get("atlasContractsV2"), dict) else {}
    validation = stack_surface.get("validation") if isinstance(stack_surface.get("validation"), dict) else {}
    for name in ("jobEnvelope", "executionReceipt"):
        record = validation.get(name)
        if not isinstance(record, dict) or record.get("ok") is not True:
            blockers.append(_finding("stack_contract_validation_missing", "Required Atlas Contracts v2 validation did not pass.", artifact=name))
    status = str(run_manifest.get("status", "unknown"))
    changed_paths = run_manifest.get("changedPaths", [])
    if not isinstance(changed_paths, list) or changed_paths:
        blockers.append(_finding("unexpected_changed_paths", "Verified no-change canary must have zero changed paths."))
    if run_manifest.get("commitSha") not in (None, ""):
        blockers.append(_finding("unexpected_commit", "Verified no-change canary must not create a commit."))
    authority_actions = execution_receipt.get("authority_actions", [])
    if not isinstance(authority_actions, list) or authority_actions:
        blockers.append(_finding("unexpected_authority_action", "ExecutionReceipt must contain no authority actions."))
    read_scope = _trace_read_scope(codex_trace, root=root or atlas_root()) if isinstance(codex_trace, str) else OrderedDict((("trace_sha256", None), ("command_count", 0), ("violations", [_finding("missing_codex_trace", "Codex trace is required for read-scope proof.")]), ("safe", False)))
    blockers.extend(read_scope["violations"])
    terminal_success = status == "success_no_changes" and execution_receipt.get("status") == "succeeded"
    terminal_failure = status != "success_no_changes" and execution_receipt.get("status") in {"failed", "blocked"}
    if not (terminal_success or terminal_failure):
        blockers.append(_finding("terminal_status_mismatch", "Runner and ExecutionReceipt terminal states are incompatible."))
    result_status = "succeeded" if terminal_success and not blockers else "failed_correlated" if terminal_failure and not blockers else "blocked"
    seed = OrderedDict((("contract_version", CONTRACT_VERSION), ("request", request), ("run_id", run_id), ("job_id", job_id), ("receipt_id", execution_receipt.get("receipt_id"))))
    return OrderedDict(
        (("schema_version", RESULT_SCHEMA), ("result_id", "stack-result-" + _digest(seed)[:20]),
         ("request_id", request.get("request_id")), ("acceptance_id", acceptance_id),
         ("plan_id", request.get("plan_id")), ("stack_job_id", job_id),
         ("stack_run_id", run_id), ("stack_receipt_id", execution_receipt.get("receipt_id")),
         ("status", result_status), ("runner_status", status),
         ("changed_paths", changed_paths if isinstance(changed_paths, list) else []),
         ("commit_sha", run_manifest.get("commitSha")), ("authority_actions", authority_actions if isinstance(authority_actions, list) else []),
         ("durable_decision_id", durable_decision.get("decision_id") if isinstance(durable_decision, dict) else None),
         ("read_scope", read_scope),
         ("external_mutation_performed", False), ("correlation_complete", not blockers),
         ("safe_to_close", terminal_success and not blockers),
         ("blockers", sorted(blockers, key=lambda item: (item["code"], item["detail"])))))


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _load_admitted(root: Path, argument: str) -> tuple[dict[str, Any] | None, OrderedDict[str, Any] | None]:
    path, error = validate_input_path(root, argument)
    if error:
        return None, error
    assert path is not None
    value, read_error, _ = _read_json(path)
    return value, read_error


def _load_stack_runtime(
    root: Path, argument: str, *, artifact: str,
) -> tuple[dict[str, Any] | None, OrderedDict[str, Any] | None]:
    path, error = validate_stack_runtime_input(root, argument, artifact=artifact)
    if error:
        return None, error
    assert path is not None
    value, read_error, _ = _read_json(path)
    return value, read_error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare or reconcile Cortex dispatch through the existing _stack runner.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--acceptance", required=True)
    prepare.add_argument("--primary-receipt", required=True)
    prepare.add_argument("--plan", required=True)
    prepare.add_argument("--request-output", required=True)
    prepare.add_argument("--prompt-output", required=True)
    prepare.add_argument("--model", default="gpt-5.6-luna")
    prepare.add_argument("--reasoning", default="low")
    prepare.add_argument("--speed", default="standard")
    correlate = subparsers.add_parser("correlate")
    correlate.add_argument("--request", required=True)
    correlate.add_argument("--run-manifest", required=True)
    correlate.add_argument("--job-envelope", required=True)
    correlate.add_argument("--execution-receipt", required=True)
    correlate.add_argument("--codex-trace", required=True)
    correlate.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    root = atlas_root()
    if args.command == "prepare":
        values: dict[str, dict[str, Any]] = {}
        errors: list[OrderedDict[str, Any]] = []
        for name, argument in (("acceptance", args.acceptance), ("primary_receipt", args.primary_receipt), ("plan", args.plan)):
            value, error = _load_admitted(root, argument)
            if error:
                errors.append(error)
            elif value is not None:
                values[name] = value
        request_output, request_error = validate_output_path(root, args.request_output, kind="request")
        prompt_output, prompt_error = validate_output_path(root, args.prompt_output, kind="prompt")
        errors.extend(error for error in (request_error, prompt_error) if error)
        if errors:
            print(json.dumps(OrderedDict((("status", "blocked"), ("blockers", errors))), indent=2))
            return 2
        assert request_output is not None and prompt_output is not None
        decision_output = request_output.with_name("cortex-primary-operator-decision.json")
        decision_ref = decision_output.resolve().relative_to(root.resolve()).as_posix()
        durable_decision = build_durable_decision(
            acceptance=values["acceptance"], primary_receipt=values["primary_receipt"], plan=values["plan"]
        )
        durable_text = _render_json(durable_decision)
        request, blockers = build_dispatch_request(
            acceptance=values["acceptance"], primary_receipt=values["primary_receipt"], plan=values["plan"],
            runtime={"model": args.model, "reasoning": args.reasoning, "speed": args.speed},
            durable_decision_ref=decision_ref,
            durable_decision_sha256=hashlib.sha256(durable_text.encode("utf-8")).hexdigest(),
        )
        if blockers:
            print(json.dumps(request, indent=2))
            return 2
        decision_output.parent.mkdir(parents=True, exist_ok=True)
        decision_output.write_bytes(durable_text.encode("utf-8"))
        _write(request_output, _render_json(request))
        _write(prompt_output, render_prompt(request, request_path=request_output.resolve()))
        print(json.dumps(OrderedDict((("status", "ready"), ("request", request), ("request_path", args.request_output), ("prompt_path", args.prompt_output))), indent=2))
        return 0
    values = {}
    errors = []
    for name, argument in (("request", args.request), ("run_manifest", args.run_manifest), ("job_envelope", args.job_envelope), ("execution_receipt", args.execution_receipt)):
        value, error = (
            _load_admitted(root, argument)
            if name == "request"
            else _load_stack_runtime(root, argument, artifact=name)
        )
        if error:
            errors.append(error)
        elif value is not None:
            values[name] = value
    durable_decision = None
    durable_decision_digest = None
    if "request" in values:
        durable_ref = values["request"].get("durable_decision")
        durable_path = durable_ref.get("path") if isinstance(durable_ref, dict) else None
        if not isinstance(durable_path, str):
            errors.append(_finding("durable_decision_missing", "Dispatch request does not name its durable decision."))
        else:
            admitted_path, admitted_error = validate_input_path(root, durable_path)
            if admitted_error:
                errors.append(admitted_error)
            else:
                assert admitted_path is not None
                durable_decision, read_error, durable_decision_digest = _read_json(admitted_path)
                if read_error:
                    errors.append(read_error)
    trace_path, trace_error = validate_stack_runtime_input(root, args.codex_trace, artifact="codex_trace")
    codex_trace = None
    if trace_error:
        errors.append(trace_error)
    else:
        assert trace_path is not None
        try:
            codex_trace = trace_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(_finding("invalid_codex_trace", "Codex trace must be readable UTF-8.", exception=str(exc)))
    output, output_error = validate_output_path(root, args.output, kind="result")
    if output_error:
        errors.append(output_error)
    if errors:
        print(json.dumps(OrderedDict((("status", "blocked"), ("blockers", errors))), indent=2))
        return 2
    result = correlate_result(
        request=values["request"], durable_decision=durable_decision,
        durable_decision_sha256=durable_decision_digest, run_manifest=values["run_manifest"],
        job_envelope=values["job_envelope"], execution_receipt=values["execution_receipt"],
        codex_trace=codex_trace, root=root,
    )
    assert output is not None
    _write(output, json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["safe_to_close"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
