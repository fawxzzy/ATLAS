from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, normalize_slashes, resolve_atlas_path
from ops.atlas.awareness import list_attention, list_inventory
from ops.atlas.load_tool_registry import load_tool_registry_bundle
from ops.atlas.observations import build_observation, emit_observation
from ops.atlas.run_session import (
    CONTEXT_AUTOMATION_LEVEL,
    REQUEST_ACTION_AUTOMATION_LEVEL,
    isoformat,
    load_stack_lock_payload,
    sync_session_outputs,
    unique_refs,
)
from ops.cortex._artifacts import read_json, write_json

SESSION_CONTRACT_VERSION = "atlas.session.v1"
RESUME_REQUEST_CONTRACT_VERSION = "atlas.session.resume.request.v1"
RESUME_DISPATCH_CONTRACT_VERSION = "atlas.session.resume.dispatch.v1"
SUPERVISOR_COMPLETION_VERSION = "atlas.stack.supervisor-consumer.v1"
RESUME_CONTEXT_VERSION = "atlas.stack.resume-context.v1"
MERGE_REQUEST_VERSION = "atlas.worker.merge-request.v1"
WORKER_STATUS_VERSION = "atlas.worker.status.v1"
ATLAS_ADAPTER_PATH = ROOT / "repos" / "_stack" / "ops" / "codex" / "repos" / "atlas" / "adapter.json"
CODEX_RUNNER_PATH = ROOT / "repos" / "_stack" / "ops" / "codex" / "Invoke-CodexRepoTask.ps1"


def optional_string(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            return stripped
    return None


def normalize_extension_id(value: Any) -> str | None:
    normalized = optional_string(value)
    return normalized or None


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def is_uri_ref(value: str) -> bool:
    return "://" in value and not value.startswith("./") and not value.startswith("../")


def normalize_ref(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip().replace("\\", "/")
    return None


def normalize_output_ref(value: Any) -> str | None:
    normalized = normalize_ref(value)
    if normalized is None:
        return None
    candidate = Path(normalized)
    if candidate.is_absolute():
        return atlas_relative(candidate, root=ROOT)
    return normalized


def require_artifact_ref(ref: str, *, field: str, allow_uri: bool = False) -> Path | None:
    normalized = optional_string(ref)
    if not normalized:
        raise ValueError(f"{field} is required.")
    if allow_uri and is_uri_ref(normalized):
        return None
    resolved = resolve_atlas_path(normalized, root=ROOT)
    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(f"{field} does not resolve to a readable file: {normalized}")
    return resolved


def load_json_artifact(ref: str, *, field: str) -> tuple[str, dict[str, Any]]:
    require_artifact_ref(ref, field=field)
    normalized_ref = normalize_ref(ref)
    if normalized_ref is None:
        raise ValueError(f"{field} is required.")
    return normalized_ref, read_json(resolve_atlas_path(normalized_ref, root=ROOT))


def emit_resume_observation(
    *,
    observation_type: str,
    status: str,
    session_id: str,
    source_ref: str,
    observed_at: str | None,
    details: dict[str, Any] | None = None,
) -> None:
    emit_observation(
        build_observation(
            observation_type=observation_type,
            source_kind="governed_flow",
            status=status,
            observed_at=observed_at,
            source_ref=source_ref,
            scope_ref=session_id,
            details=details or {},
        ),
        owner="atlas-resume-executor",
        root=ROOT,
    )


def validate_identity_match(*, label: str, expected: Any, actual: Any) -> None:
    expected_text = normalize_extension_id(expected) if label == "extension_id" else optional_string(expected)
    actual_text = normalize_extension_id(actual) if label == "extension_id" else optional_string(actual)
    if expected_text != actual_text:
        raise ValueError(
            f"Governed surface identity is inconsistent for {label}: expected {expected_text!r}, got {actual_text!r}."
        )


def collect_run_manifest_paths() -> list[Path]:
    log_root = ROOT / ".codex" / "logs"
    if not log_root.exists():
        return []
    return sorted(path.resolve() for path in log_root.rglob("run.json") if path.is_file())


def select_resume_context_ref(
    manifest: dict[str, Any],
    *,
    session_worker_id: str,
) -> str:
    resume = manifest.get("resume") if isinstance(manifest.get("resume"), dict) else {}
    refs = manifest.get("refs") if isinstance(manifest.get("refs"), dict) else {}
    explicit_ref = optional_string(resume.get("resume_context_ref"))
    if explicit_ref:
        return explicit_ref
    for candidate in string_list(refs.get("resume_context_refs")):
        payload = read_json(resolve_atlas_path(candidate, root=ROOT))
        if optional_string(payload.get("worker_id")) == session_worker_id:
            return candidate
    candidates = string_list(refs.get("resume_context_refs"))
    if candidates:
        return candidates[0]
    raise ValueError("Session manifest is missing a resume_context_ref for the resume_ready state.")


def validate_resume_ready_session(session_id: str) -> dict[str, Any]:
    session_root = ROOT / "runtime" / "atlas" / "sessions" / session_id
    session_manifest_path = session_root / "session.manifest.json"
    if not session_manifest_path.exists():
        raise FileNotFoundError(f"Unknown session manifest for {session_id}.")

    manifest = read_json(session_manifest_path)
    if manifest.get("contract_version") != SESSION_CONTRACT_VERSION:
        raise ValueError(f"Session manifest must declare {SESSION_CONTRACT_VERSION}.")

    session_state = optional_string(manifest.get("session_state"))
    if session_state != "resume_ready":
        raise ValueError(f"Session {session_id} is not resume_ready; current state is {session_state!r}.")

    worker = manifest.get("worker") if isinstance(manifest.get("worker"), dict) else {}
    refs = manifest.get("refs") if isinstance(manifest.get("refs"), dict) else {}
    governed_surfaces = (
        manifest.get("governed_surfaces") if isinstance(manifest.get("governed_surfaces"), dict) else {}
    )
    execution_surface = governed_surfaces.get("execution") if isinstance(governed_surfaces.get("execution"), dict) else {}

    session_worker_id = optional_string(worker.get("worker_id"))
    assignment_id = optional_string(worker.get("assignment_id"))
    manifest_registry_digest = optional_string(governed_surfaces.get("registry_digest"))
    manifest_tool_id = optional_string(execution_surface.get("tool_id"))
    manifest_extension_id = normalize_extension_id(execution_surface.get("extension_id"))
    manifest_stack_lock_digest = optional_string(manifest.get("stack_lock_digest"))
    if not session_worker_id or not assignment_id or not manifest_registry_digest or not manifest_tool_id or not manifest_stack_lock_digest:
        raise ValueError("Session manifest is missing the governed identity required for resume.")

    current_lock_payload = load_stack_lock_payload()
    current_stack_lock_digest = optional_string(current_lock_payload.get("lock_digest"))
    if current_stack_lock_digest != manifest_stack_lock_digest:
        raise ValueError(
            f"Session stack_lock_digest is stale. expected {current_stack_lock_digest}, got {manifest_stack_lock_digest}."
        )

    registry_bundle = load_tool_registry_bundle(root=ROOT)
    current_registry_digest = optional_string(registry_bundle.get("registry_digest"))
    if current_registry_digest != manifest_registry_digest:
        raise ValueError(
            f"Session governed registry_digest is stale. expected {current_registry_digest}, got {manifest_registry_digest}."
        )

    inventory = list_inventory(root=ROOT, refresh=False, entry_type="session", limit=200)
    inventory_entry = next(
        (
            item
            for item in inventory.get("entries", [])
            if isinstance(item, dict) and str(item.get("key")) == session_id
        ),
        None,
    )
    if inventory_entry is None or str(inventory_entry.get("status")) != "resume_ready":
        raise ValueError("World-model inventory does not confirm the target session as resume_ready.")

    attention = list_attention(root=ROOT, refresh=False, query=session_id, limit=50)

    merge_completion_ref = optional_string(refs.get("merge_completion_ref"))
    if not merge_completion_ref:
        raise ValueError("Session manifest is missing refs.merge_completion_ref.")
    merge_completion_ref, merge_completion = load_json_artifact(
        merge_completion_ref,
        field="refs.merge_completion_ref",
    )
    if optional_string(merge_completion.get("schema_version")) != SUPERVISOR_COMPLETION_VERSION:
        raise ValueError("merge_completion_ref must point to an atlas.stack.supervisor-consumer.v1 artifact.")
    validate_identity_match(label="tool_id", expected=manifest_tool_id, actual=merge_completion.get("tool_id"))
    validate_identity_match(
        label="extension_id",
        expected=manifest_extension_id,
        actual=merge_completion.get("extension_id"),
    )
    validate_identity_match(
        label="registry_digest",
        expected=manifest_registry_digest,
        actual=merge_completion.get("registry_digest"),
    )
    validate_identity_match(
        label="stack_lock_digest",
        expected=manifest_stack_lock_digest,
        actual=merge_completion.get("stack_lock_digest"),
    )

    resume_context_ref = select_resume_context_ref(manifest, session_worker_id=session_worker_id)
    resume_context_ref, resume_context = load_json_artifact(
        resume_context_ref,
        field="resume.resume_context_ref",
    )
    if optional_string(resume_context.get("schema_version")) != RESUME_CONTEXT_VERSION:
        raise ValueError("resume_context_ref must point to an atlas.stack.resume-context.v1 artifact.")
    if optional_string(resume_context.get("worker_id")) != session_worker_id:
        raise ValueError("resume_context_ref does not target the paused session worker.")
    if optional_string(resume_context.get("assignment_id")) != assignment_id:
        raise ValueError("resume_context_ref does not match the paused session assignment.")
    validate_identity_match(label="tool_id", expected=manifest_tool_id, actual=resume_context.get("tool_id"))
    validate_identity_match(
        label="extension_id",
        expected=manifest_extension_id,
        actual=resume_context.get("extension_id"),
    )
    validate_identity_match(
        label="registry_digest",
        expected=manifest_registry_digest,
        actual=resume_context.get("registry_digest"),
    )
    validate_identity_match(
        label="stack_lock_digest",
        expected=manifest_stack_lock_digest,
        actual=resume_context.get("stack_lock_digest"),
    )
    if normalize_ref(resume_context.get("merge_request_ref")) != normalize_ref(merge_completion.get("merge_request_ref")):
        raise ValueError("resume_context_ref and merge_completion_ref do not agree on merge_request_ref.")

    merge_request_ref = optional_string(resume_context.get("merge_request_ref"))
    if not merge_request_ref:
        raise ValueError("resume_context_ref is missing merge_request_ref.")
    merge_request_ref, merge_request = load_json_artifact(
        merge_request_ref,
        field="resume_context.merge_request_ref",
    )
    if optional_string(merge_request.get("contract_version")) != MERGE_REQUEST_VERSION:
        raise ValueError("merge_request_ref must point to an atlas.worker.merge-request.v1 artifact.")
    validate_identity_match(label="tool_id", expected=manifest_tool_id, actual=merge_request.get("tool_id"))
    validate_identity_match(
        label="extension_id",
        expected=manifest_extension_id,
        actual=merge_request.get("extension_id"),
    )
    validate_identity_match(
        label="registry_digest",
        expected=manifest_registry_digest,
        actual=merge_request.get("registry_digest"),
    )
    validate_identity_match(
        label="stack_lock_digest",
        expected=manifest_stack_lock_digest,
        actual=merge_request.get("stack_lock_digest"),
    )

    paused_status_ref = optional_string(resume_context.get("paused_status_ref"))
    if not paused_status_ref:
        raise ValueError("resume_context_ref is missing paused_status_ref.")
    paused_status_ref, paused_status = load_json_artifact(
        paused_status_ref,
        field="resume_context.paused_status_ref",
    )
    if optional_string(paused_status.get("contract_version")) != WORKER_STATUS_VERSION:
        raise ValueError("paused_status_ref must point to an atlas.worker.status.v1 artifact.")
    if optional_string(paused_status.get("state")) != "paused":
        raise ValueError("paused_status_ref does not represent a paused worker state.")
    if optional_string(paused_status.get("worker_id")) != session_worker_id:
        raise ValueError("paused_status_ref does not match the paused session worker.")
    if optional_string(paused_status.get("assignment_id")) != assignment_id:
        raise ValueError("paused_status_ref does not match the paused session assignment.")
    validate_identity_match(label="tool_id", expected=manifest_tool_id, actual=paused_status.get("tool_id"))
    validate_identity_match(
        label="extension_id",
        expected=manifest_extension_id,
        actual=paused_status.get("extension_id"),
    )
    validate_identity_match(
        label="registry_digest",
        expected=manifest_registry_digest,
        actual=paused_status.get("registry_digest"),
    )

    paused_handoff_refs = string_list(resume_context.get("paused_handoff_refs"))
    if not paused_handoff_refs:
        raise ValueError("resume_context_ref is missing paused worker handoff refs.")
    for index, handoff_ref in enumerate(paused_handoff_refs):
        require_artifact_ref(
            handoff_ref,
            field=f"resume_context.paused_handoff_refs[{index}]",
            allow_uri=True,
        )

    merge_handoff_ref = optional_string(resume_context.get("merge_handoff_ref"))
    if not merge_handoff_ref:
        raise ValueError("resume_context_ref is missing merge_handoff_ref.")

    merge_prompt_ref = optional_string(refs.get("merge_prompt_ref"))
    merge_context_ref = optional_string(refs.get("merge_context_ref"))
    merge_assignment_ref = optional_string(refs.get("merge_assignment_ref"))
    if merge_prompt_ref:
        require_artifact_ref(merge_prompt_ref, field="refs.merge_prompt_ref")
    if merge_context_ref:
        require_artifact_ref(merge_context_ref, field="refs.merge_context_ref")
    if merge_assignment_ref:
        require_artifact_ref(merge_assignment_ref, field="refs.merge_assignment_ref")

    completion_resume_contexts = merge_completion.get("resume_contexts")
    if isinstance(completion_resume_contexts, list):
        completion_refs = {
            normalize_ref(item.get("path"))
            for item in completion_resume_contexts
            if isinstance(item, dict)
        }
        if normalize_ref(resume_context_ref) not in completion_refs:
            raise ValueError("merge_completion_ref does not include the selected resume_context_ref.")

    return {
        "session_id": session_id,
        "session_root": session_root,
        "session_manifest_path": session_manifest_path,
        "manifest": manifest,
        "inventory_entry": inventory_entry,
        "attention": attention,
        "registry_digest": manifest_registry_digest,
        "stack_lock_digest": manifest_stack_lock_digest,
        "tool_id": manifest_tool_id,
        "extension_id": manifest_extension_id,
        "worker_id": session_worker_id,
        "assignment_id": assignment_id,
        "merge_request_ref": merge_request_ref,
        "merge_completion_ref": merge_completion_ref,
        "merge_prompt_ref": merge_prompt_ref,
        "merge_context_ref": merge_context_ref,
        "merge_assignment_ref": merge_assignment_ref,
        "resume_context_ref": resume_context_ref,
        "paused_handoff_refs": paused_handoff_refs,
        "merge_handoff_ref": merge_handoff_ref,
    }


def build_resume_prompt_text(context: dict[str, Any]) -> str:
    merge_prompt_text = None
    merge_prompt_ref = context.get("merge_prompt_ref")
    if isinstance(merge_prompt_ref, str) and merge_prompt_ref.strip():
        merge_prompt_text = resolve_atlas_path(merge_prompt_ref, root=ROOT).read_text(encoding="utf-8")

    paused_refs = ", ".join(context["paused_handoff_refs"])
    lines = [
        f"Title: Resume {context['session_id']}",
        f"Branch: resume-{context['session_id']}",
        "Verify: python ops/validation/validate_stack.py --ratchet",
        f"HandoffRefs: {context['resume_context_ref']}, {context['merge_completion_ref']}",
        f"PausedHandoffRefs: {paused_refs}",
        f"MergeRequestRefs: {context['merge_request_ref']}",
        f"QueryTerms: {context['session_id']}, {context['tool_id']}",
        "TaskTags: resume, operator, governed",
        "",
        f"Resume the paused governed ATLAS session {context['session_id']} through the existing _stack worker flow.",
        "",
        "Use only the governed resume boundary below:",
        f"- session manifest ref: {atlas_relative(context['session_manifest_path'], root=ROOT)}",
        f"- resume context ref: {context['resume_context_ref']}",
        f"- merge completion ref: {context['merge_completion_ref']}",
        f"- merge request ref: {context['merge_request_ref']}",
        f"- paused worker handoff refs: {paused_refs}",
        f"- reserved merged handoff ref: {context['merge_handoff_ref']}",
        "",
        "Rules:",
        "- Do not reconstruct or depend on raw hidden transcript history.",
        "- Treat the paused handoff refs and resume context as the only resume boundary.",
        "- Keep stack_lock_digest, tool_id, extension_id, and registry_digest unchanged.",
        "- Finish on the existing _stack path rather than inventing a second merge or resume flow.",
    ]
    if isinstance(merge_prompt_ref, str) and merge_prompt_ref.strip():
        lines.append(f"- Existing merge prompt ref: {merge_prompt_ref}")
    if merge_prompt_text:
        lines.extend(
            [
                "",
                "Canonical merge prompt to honor:",
                "",
                merge_prompt_text.rstrip(),
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def run_resume_dispatch(
    *,
    prompt_path: Path,
    no_commit: bool,
) -> subprocess.CompletedProcess[str]:
    if not CODEX_RUNNER_PATH.exists():
        raise FileNotFoundError(f"Missing _stack runner: {normalize_slashes(str(CODEX_RUNNER_PATH))}")
    if not ATLAS_ADAPTER_PATH.exists():
        raise FileNotFoundError(f"Missing ATLAS runner adapter: {normalize_slashes(str(ATLAS_ADAPTER_PATH))}")

    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(CODEX_RUNNER_PATH),
        "-PromptPath",
        str(prompt_path),
        "-RepoRoot",
        str(ROOT),
        "-AdapterPath",
        str(ATLAS_ADAPTER_PATH),
    ]
    if no_commit:
        command.append("-NoCommit")
    return subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def resolve_new_run_manifest(before: list[Path], after: list[Path]) -> Path:
    before_set = {path.resolve() for path in before}
    candidates = [path.resolve() for path in after if path.resolve() not in before_set]
    if not candidates:
        raise RuntimeError("Resume dispatch did not create a new _stack run manifest.")
    candidates.sort(key=lambda item: item.stat().st_mtime)
    return candidates[-1]


def resume_session(*, session_id: str, no_commit: bool = False) -> dict[str, Any]:
    context = validate_resume_ready_session(session_id)
    session_root = context["session_root"]
    session_manifest_path = context["session_manifest_path"]
    manifest = context["manifest"]
    refs = manifest["refs"]
    resume = manifest["resume"]

    artifact_root = session_root / "artifacts"
    resume_request_path = artifact_root / "resume.request.json"
    resume_dispatch_path = artifact_root / "resume.dispatch.json"
    resume_prompt_path = artifact_root / "resume.prompt.md"
    receipt_ref = optional_string(refs.get("execution_receipt_ref"))
    receipt_root = resolve_atlas_path(receipt_ref, root=ROOT).parent if receipt_ref else None
    supervisor_root = ROOT / "runtime" / "cortex" / "supervisor" / session_id

    resume_requested_at = isoformat()
    resume_request = {
        "contract_version": RESUME_REQUEST_CONTRACT_VERSION,
        "session_id": session_id,
        "requested_at": resume_requested_at,
        "stack_lock_digest": context["stack_lock_digest"],
        "tool_id": context["tool_id"],
        "extension_id": context["extension_id"],
        "registry_digest": context["registry_digest"],
        "automation_level": REQUEST_ACTION_AUTOMATION_LEVEL,
        "session_manifest_ref": atlas_relative(session_manifest_path, root=ROOT),
        "merge_completion_ref": context["merge_completion_ref"],
        "merge_request_ref": context["merge_request_ref"],
        "resume_context_ref": context["resume_context_ref"],
        "paused_handoff_refs": context["paused_handoff_refs"],
        "merge_handoff_ref": context["merge_handoff_ref"],
    }
    write_json(resume_request_path, resume_request)
    refs["resume_request_ref"] = atlas_relative(resume_request_path, root=ROOT)
    manifest["session_state"] = "resume_requested"
    manifest["automation_level"] = REQUEST_ACTION_AUTOMATION_LEVEL
    resume["status"] = "resume_requested"
    resume["requested_at"] = resume_requested_at
    resume["requested_worker_id"] = context["worker_id"]
    resume["resume_context_ref"] = context["resume_context_ref"]
    resume["merge_completion_ref"] = context["merge_completion_ref"]
    resume["dispatched_at"] = None
    resume["completed_at"] = None
    resume["failure_reason"] = None
    manifest["closed_at"] = None
    manifest["updated_at"] = isoformat()
    write_json(session_manifest_path, manifest)
    emit_resume_observation(
        observation_type="resume_requested",
        status="requested",
        session_id=session_id,
        source_ref=refs["resume_request_ref"],
        observed_at=resume_requested_at,
        details={
            "worker_id": context["worker_id"],
            "assignment_id": context["assignment_id"],
            "tool_id": context["tool_id"],
            "automation_level": REQUEST_ACTION_AUTOMATION_LEVEL,
        },
    )

    resume_prompt_path.write_text(build_resume_prompt_text(context), encoding="utf-8")
    before_run_manifests = collect_run_manifest_paths()

    resume_dispatched_at = isoformat()
    resume_dispatch = {
        "contract_version": RESUME_DISPATCH_CONTRACT_VERSION,
        "session_id": session_id,
        "dispatched_at": resume_dispatched_at,
        "stack_lock_digest": context["stack_lock_digest"],
        "tool_id": context["tool_id"],
        "extension_id": context["extension_id"],
        "registry_digest": context["registry_digest"],
        "automation_level": REQUEST_ACTION_AUTOMATION_LEVEL,
        "prompt_ref": atlas_relative(resume_prompt_path, root=ROOT),
        "runner": {
            "entrypoint": atlas_relative(CODEX_RUNNER_PATH, root=ROOT),
            "adapter_ref": atlas_relative(ATLAS_ADAPTER_PATH, root=ROOT),
            "no_commit": no_commit,
        },
    }
    write_json(resume_dispatch_path, resume_dispatch)
    refs["resume_dispatch_ref"] = atlas_relative(resume_dispatch_path, root=ROOT)
    manifest["session_state"] = "running"
    manifest["automation_level"] = REQUEST_ACTION_AUTOMATION_LEVEL
    resume["status"] = "running"
    resume["dispatched_at"] = resume_dispatched_at
    manifest["updated_at"] = isoformat()
    write_json(session_manifest_path, manifest)
    emit_resume_observation(
        observation_type="resume_dispatched",
        status="running",
        session_id=session_id,
        source_ref=refs["resume_dispatch_ref"],
        observed_at=resume_dispatched_at,
        details={
            "worker_id": context["worker_id"],
            "assignment_id": context["assignment_id"],
            "tool_id": context["tool_id"],
            "automation_level": REQUEST_ACTION_AUTOMATION_LEVEL,
            "prompt_ref": resume_dispatch["prompt_ref"],
        },
    )

    completed = run_resume_dispatch(prompt_path=resume_prompt_path, no_commit=no_commit)
    after_run_manifests = collect_run_manifest_paths()
    run_manifest_path = resolve_new_run_manifest(before_run_manifests, after_run_manifests)
    run_manifest_payload = read_json(run_manifest_path)
    run_manifest_ref = atlas_relative(run_manifest_path, root=ROOT)
    refs["resume_run_manifest_ref"] = run_manifest_ref
    resume_dispatch["run_manifest_ref"] = run_manifest_ref
    resume_dispatch["runner"]["exit_code"] = completed.returncode
    resume_dispatch["runner"]["status"] = optional_string(run_manifest_payload.get("status")) or "unknown"
    write_json(resume_dispatch_path, resume_dispatch)

    worker_artifacts = (
        run_manifest_payload.get("workerArtifacts")
        if isinstance(run_manifest_payload.get("workerArtifacts"), dict)
        else {}
    )
    resumed_assignment_ref = normalize_output_ref(worker_artifacts.get("assignment"))
    resumed_running_status_ref = normalize_output_ref(worker_artifacts.get("runningStatus"))
    resumed_completed_status_ref = normalize_output_ref(worker_artifacts.get("completedStatus"))
    refs["resumed_assignment_ref"] = resumed_assignment_ref
    refs["resumed_running_status_ref"] = resumed_running_status_ref
    refs["resumed_completed_status_ref"] = resumed_completed_status_ref
    refs["status_refs"] = unique_refs(
        [
            *string_list(refs.get("status_refs")),
            resumed_running_status_ref,
            resumed_completed_status_ref,
        ]
    )

    run_status = optional_string(run_manifest_payload.get("status")) or "unknown"
    completed_status_payload = (
        read_json(resolve_atlas_path(resumed_completed_status_ref, root=ROOT))
        if isinstance(resumed_completed_status_ref, str) and resumed_completed_status_ref.strip()
        else {}
    )
    completed_worker_state = optional_string(completed_status_payload.get("state"))

    if completed.returncode != 0 or run_status != "success" or completed_worker_state != "completed":
        failure_reason = (
            completed.stderr.strip()
            or completed.stdout.strip()
            or f"resume runner failed with status={run_status!r}, worker_state={completed_worker_state!r}"
        )
        manifest["session_state"] = "resume_failed"
        manifest["automation_level"] = REQUEST_ACTION_AUTOMATION_LEVEL
        resume["status"] = "resume_failed"
        resume["completed_at"] = isoformat()
        resume["failure_reason"] = failure_reason
        manifest["completion"]["final_status"] = "resume_failed"
        manifest["completion"]["final_status_ref"] = run_manifest_ref
        manifest["closed_at"] = isoformat()
        manifest["updated_at"] = isoformat()
        write_json(session_manifest_path, manifest)
        emit_resume_observation(
            observation_type="resume_failed",
            status="failed",
            session_id=session_id,
            source_ref=run_manifest_ref,
            observed_at=resume["completed_at"],
            details={
                "worker_id": context["worker_id"],
                "assignment_id": context["assignment_id"],
                "tool_id": context["tool_id"],
                "automation_level": REQUEST_ACTION_AUTOMATION_LEVEL,
                "run_status": run_status,
                "runner_exit_code": completed.returncode,
                "worker_state": completed_worker_state,
                "failure_reason": failure_reason,
            },
        )
        sync_summary = sync_session_outputs(
            session_root=session_root,
            session_id=session_id,
            receipt_root=receipt_root,
            supervisor_root=supervisor_root,
        )
        return {
            "session_id": session_id,
            "session_manifest_ref": atlas_relative(session_manifest_path, root=ROOT),
            "session_state": manifest["session_state"],
            "final_status": manifest["completion"]["final_status"],
            "resume_run_manifest_ref": run_manifest_ref,
            "status_snapshot_ref": sync_summary["status_snapshot_ref"],
            "world_model_snapshot_ref": sync_summary["world_model_summary"]["snapshot_ref"],
            "world_model_attention_ref": sync_summary["world_model_summary"]["attention_ref"],
            "failure_reason": failure_reason,
        }

    manifest["session_state"] = "completed"
    manifest["automation_level"] = REQUEST_ACTION_AUTOMATION_LEVEL
    resume["status"] = "completed"
    resume["completed_at"] = isoformat()
    resume["failure_reason"] = None
    manifest["completion"]["final_status"] = "completed"
    manifest["completion"]["final_status_ref"] = resumed_completed_status_ref or run_manifest_ref
    manifest["closed_at"] = isoformat()
    manifest["updated_at"] = isoformat()
    write_json(session_manifest_path, manifest)
    emit_resume_observation(
        observation_type="resume_completed",
        status="completed",
        session_id=session_id,
        source_ref=resumed_completed_status_ref or run_manifest_ref,
        observed_at=resume["completed_at"],
        details={
            "worker_id": context["worker_id"],
            "assignment_id": context["assignment_id"],
            "tool_id": context["tool_id"],
            "automation_level": REQUEST_ACTION_AUTOMATION_LEVEL,
            "run_status": run_status,
            "resume_run_manifest_ref": run_manifest_ref,
        },
    )
    sync_summary = sync_session_outputs(
        session_root=session_root,
        session_id=session_id,
        receipt_root=receipt_root,
        supervisor_root=supervisor_root,
    )
    return {
        "session_id": session_id,
        "session_manifest_ref": atlas_relative(session_manifest_path, root=ROOT),
        "session_state": manifest["session_state"],
        "final_status": manifest["completion"]["final_status"],
        "resume_run_manifest_ref": run_manifest_ref,
        "status_snapshot_ref": sync_summary["status_snapshot_ref"],
        "world_model_snapshot_ref": sync_summary["world_model_summary"]["snapshot_ref"],
        "world_model_attention_ref": sync_summary["world_model_summary"]["attention_ref"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resume a resume_ready ATLAS session through the root-owned governed _stack path."
    )
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--no-commit", action="store_true")
    args = parser.parse_args(argv)

    payload = resume_session(session_id=args.session_id.strip(), no_commit=bool(args.no_commit))
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
