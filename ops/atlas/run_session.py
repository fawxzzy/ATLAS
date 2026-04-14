from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, load_stack_config, normalize_slashes
from ops.atlas.load_tool_registry import load_tool_registry_bundle, select_tool_entry
from ops.cortex._artifacts import register_artifact_descriptors, sha256_bytes, write_json
from ops.cortex.build_worker_context import build_worker_context_payload, normalize_query_terms
from ops.cortex.render_status import render_status_payload

DEFAULT_CONTEXT_LIMIT = 5
SESSION_CONTRACT_VERSION = "atlas.session.v1"
CONTEXT_TOOL_ID = "cortex.build_worker_context"
SUPERVISION_TOOL_ID = "cortex.supervise_workers"
READ_ONLY_EXECUTION_TOOL_ID = "read_only_scan"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat(value: datetime | None = None) -> str:
    timestamp = value or utc_now()
    return timestamp.isoformat().replace("+00:00", "Z")


def lifeline_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True).encode("utf-8")
    return sha256_bytes(encoded)


def slugify(value: str) -> str:
    slug = "".join(character.lower() if character.isalnum() else "-" for character in value.strip())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "session"


def git_output(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def ps_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def unique_refs(values: list[str | None]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        ordered.append(stripped)
    return ordered


def load_stack_lock_payload() -> dict[str, Any]:
    payload = load_stack_config(ROOT / "stack.lock.yaml")
    if not isinstance(payload, dict):
        raise ValueError("stack.lock.yaml must deserialize to a mapping.")
    return payload


def ensure_query_bundle() -> Path:
    bundle_path = ROOT / "runtime" / "cortex" / "query" / "knowledge" / "bundle.json"
    if bundle_path.exists():
        return bundle_path
    completed = subprocess.run(
        [sys.executable, str(ROOT / "ops" / "knowledge" / "build_query_bundle.py")],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
    )
    if completed.returncode != 0:
        error = completed.stderr.strip() or completed.stdout.strip() or "bundle build failed"
        raise RuntimeError(f"Unable to build the Cortex query bundle: {error}")
    if not bundle_path.exists():
        raise RuntimeError("Query bundle build completed without writing runtime/cortex/query/knowledge/bundle.json.")
    return bundle_path


def component_snapshot(lock_payload: dict[str, Any], component_id: str, *, fallback_path: str) -> dict[str, Any]:
    components = lock_payload.get("components", {})
    if isinstance(components, dict) and isinstance(components.get(component_id), dict):
        return dict(components[component_id])
    repo_root = ROOT / fallback_path
    return {
        "path": fallback_path,
        "ref": git_output(repo_root, "rev-parse", "--abbrev-ref", "HEAD") or "unknown",
        "commit": git_output(repo_root, "rev-parse", "HEAD") or "unknown",
        "dirty": bool(git_output(repo_root, "status", "--porcelain=v1")),
    }


def session_manifest_template(
    *,
    session_id: str,
    title: str,
    task_id: str,
    scenario: str,
    stack_lock_digest: str,
    lock_payload: dict[str, Any],
    worker_id: str,
    assignment_id: str,
    registry_digest: str,
    context_tool: dict[str, Any],
    supervision_tool: dict[str, Any],
    execution_tool: dict[str, Any],
) -> dict[str, Any]:
    return {
        "contract_version": SESSION_CONTRACT_VERSION,
        "session_id": session_id,
        "title": title,
        "task_id": task_id,
        "scenario": scenario,
        "session_state": "created",
        "stack_lock_digest": stack_lock_digest,
        "stack_manifest_ref": "stack.yaml",
        "created_at": isoformat(),
        "updated_at": isoformat(),
        "closed_at": None,
        "orchestrator": {
            "owner": "stack-root",
            "stack_component": component_snapshot(lock_payload, "stack", fallback_path="."),
            "orchestrator_component": component_snapshot(lock_payload, "_stack", fallback_path="repos/_stack"),
            "supervisor_component": {
                "path": "runtime/cortex",
                "model": "root-owned-subsystem",
            },
            "executor_component": component_snapshot(lock_payload, "lifeline", fallback_path="repos/fawxzzy-lifeline"),
        },
        "governed_surfaces": {
            "registry_digest": registry_digest,
            "context": {
                "tool_id": context_tool["tool_id"],
                "extension_id": context_tool["extension_id"],
            },
            "supervision": {
                "tool_id": supervision_tool["tool_id"],
                "extension_id": supervision_tool["extension_id"],
            },
            "execution": {
                "tool_id": execution_tool["tool_id"],
                "extension_id": execution_tool["extension_id"],
            },
        },
        "worker": {
            "worker_id": worker_id,
            "assignment_id": assignment_id,
            "context_ref": None,
            "assignment_ref": None,
        },
        "refs": {
            "status_refs": [],
            "capability_profile_ref": None,
            "request_ref": None,
            "approval_receipt_ref": None,
            "execution_receipt_ref": None,
            "bridge_record_ref": None,
            "merge_request_refs": [],
            "pause_status_refs": [],
            "resume_context_refs": [],
            "merge_assignment_ref": None,
            "merge_prompt_ref": None,
            "merge_context_ref": None,
            "merge_completion_ref": None,
        },
        "completion": {
            "final_status": None,
            "final_status_ref": None,
            "close_receipt_refs": [],
        },
    }


def build_worker_assignment(
    *,
    assignment_id: str,
    worker_id: str,
    task_id: str,
    stack_lock_digest: str,
    context_ref: str,
    tool_id: str,
    extension_id: str | None,
    registry_digest: str,
) -> dict[str, Any]:
    return {
        "contract_version": "atlas.worker.assignment.v1",
        "assignment_id": assignment_id,
        "worker_id": worker_id,
        "task_id": task_id,
        "stack_lock_digest": stack_lock_digest,
        "tool_id": tool_id,
        "extension_id": extension_id,
        "registry_digest": registry_digest,
        "allowed_globs": [
            "docs/**",
            "ops/**",
            "runtime/**",
        ],
        "forbidden_globs": [
            "secrets/**",
            "repos/Verta-Core/**",
            "data/imports/knowledge/personal/verta-core/**",
        ],
        "input_handoff_refs": [context_ref],
        "expected_outputs": [
            "runtime/lifeline/worker-execution",
            context_ref,
        ],
        "notes": "Root-owned ATLAS session assignment.",
    }


def build_worker_status(
    *,
    worker_id: str,
    assignment_id: str,
    state: str,
    tool_id: str,
    extension_id: str | None,
    registry_digest: str,
    output_refs: list[str] | None = None,
    touched_ranges: list[dict[str, Any]] | None = None,
    blocked_reason: str | None = None,
    merge_request_ref: str | None = None,
    heartbeat_at: datetime | None = None,
) -> dict[str, Any]:
    return {
        "contract_version": "atlas.worker.status.v1",
        "worker_id": worker_id,
        "assignment_id": assignment_id,
        "tool_id": tool_id,
        "extension_id": extension_id,
        "registry_digest": registry_digest,
        "state": state,
        "heartbeat_at": isoformat(heartbeat_at),
        "touched_ranges": touched_ranges or [],
        "output_refs": output_refs or [],
        "blocked_reason": blocked_reason,
        "merge_request_ref": merge_request_ref,
    }


def build_capability_profile(tool_entry: dict[str, Any]) -> dict[str, Any]:
    capability_profile = tool_entry.get("capability_profile")
    if not isinstance(capability_profile, dict):
        raise ValueError(f"Tool entry '{tool_entry.get('tool_id')}' is missing capability_profile.")
    return json.loads(json.dumps(capability_profile))


def build_privileged_action_request(
    *,
    request_id: str,
    worker_id: str,
    assignment_id: str,
    stack_lock_digest: str,
    session_manifest_ref: str,
    assignment_ref: str,
    status_ref: str,
    context_ref: str,
    capability_profile: dict[str, Any],
    tool_id: str,
    extension_id: str | None,
    registry_digest: str,
) -> dict[str, Any]:
    return {
        "contract_version": "atlas.privileged-action.request.v1",
        "request_id": request_id,
        "requested_at": isoformat(),
        "worker_id": worker_id,
        "assignment_id": assignment_id,
        "stack_lock_digest": stack_lock_digest,
        "tool_id": tool_id,
        "extension_id": extension_id,
        "registry_digest": registry_digest,
        "source_refs": [
            session_manifest_ref,
            assignment_ref,
            status_ref,
            context_ref,
        ],
        "action": {
            "summary": "Inspect the ATLAS root with a read-only Node command.",
            "operation": "read_only_scan",
            "command": ["node", "--version"],
            "cwd": ".",
        },
        "target_paths": [
            "README-STACK.md",
            "stack.yaml",
        ],
        "target_resources": ["node"],
        "requested_capability": capability_profile,
        "dry_run_output": "Read-only scan will report the local Node runtime version only.",
        "justification": "Verify the root-owned session bridge and receipt flow without mutation authority.",
    }


def build_approval_receipt(
    *,
    approval_receipt_id: str,
    request: dict[str, Any],
) -> dict[str, Any]:
    return {
        "contract_version": "atlas.approval.receipt.v1",
        "approval_receipt_id": approval_receipt_id,
        "request_id": request["request_id"],
        "worker_id": request["worker_id"],
        "assignment_id": request["assignment_id"],
        "stack_lock_digest": request["stack_lock_digest"],
        "tool_id": request["tool_id"],
        "extension_id": request["extension_id"],
        "registry_digest": request["registry_digest"],
        "approver": {
            "kind": "system",
            "name": "atlas-session-policy-gate",
        },
        "approval_status": "approved",
        "granted_scope": request["requested_capability"],
        "expiry_at": isoformat(utc_now() + timedelta(hours=1)),
        "request_digest": lifeline_digest(request),
        "issued_at": isoformat(),
    }


def build_touched_range(relative_path: str, *, repo_commit: str, file_digest_before: str) -> dict[str, Any]:
    return {
        "repo_path": ".",
        "repo_commit": repo_commit,
        "file_digest_before": file_digest_before,
        "path": relative_path,
        "start_line": 1,
        "end_line": 12,
        "op": "modify",
    }


def write_context_artifact(
    *,
    assignment_id: str,
    worker_id: str,
    task_id: str,
    stack_lock_digest: str,
    query_terms: list[str],
    task_tags: list[str],
    output_path: Path,
) -> None:
    bundle_path = ensure_query_bundle()
    payload = build_worker_context_payload(
        assignment_id=assignment_id,
        worker_id=worker_id,
        task_id=task_id,
        stack_lock_digest=stack_lock_digest,
        query_terms=normalize_query_terms(query_terms),
        task_tags=normalize_query_terms(task_tags),
        bundle_path=bundle_path,
        limit=DEFAULT_CONTEXT_LIMIT,
    )
    write_json(output_path, payload)


def run_python_json(*args: str) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
    )
    if completed.returncode != 0:
        error = completed.stderr.strip() or completed.stdout.strip() or "python command failed"
        raise RuntimeError(error)
    payload = json.loads(completed.stdout.strip())
    if not isinstance(payload, dict):
        raise ValueError("Expected JSON object from python subprocess.")
    return payload


def run_stack_function(function_name: str, **parameters: str) -> dict[str, Any]:
    stack_repo_root = ROOT / "repos" / "_stack"
    stack_script = stack_repo_root / "ops" / "stack" / "StackWorkerArtifacts.ps1"
    if not stack_script.exists():
        raise FileNotFoundError(f"Missing _stack artifact helper: {normalize_slashes(str(stack_script))}")
    arguments = " ".join(f"-{name} {ps_literal(value)}" for name, value in parameters.items())
    script = "\n".join(
        [
            "$ErrorActionPreference = 'Stop'",
            f". {ps_literal(str(stack_script))}",
            f"$result = {function_name} {arguments}",
            "$result | ConvertTo-Json -Depth 32",
        ]
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
    )
    if completed.returncode != 0:
        error = completed.stderr.strip() or completed.stdout.strip() or f"{function_name} failed"
        raise RuntimeError(error)
    payload = json.loads(completed.stdout.strip())
    if not isinstance(payload, dict):
        raise ValueError(f"{function_name} did not return a JSON object.")
    return payload


def register_session_descriptors(
    *,
    session_root: Path,
    receipt_root: Path | None,
    supervisor_root: Path | None,
) -> list[dict[str, Any]]:
    paths = [session_root, ROOT / "runtime" / "cortex" / "catalog" / "knowledge"]
    if receipt_root is not None:
        paths.append(receipt_root)
    if supervisor_root is not None:
        paths.append(supervisor_root)
    return register_artifact_descriptors(
        paths,
        output_dir=ROOT / "runtime" / "cortex" / "artifacts",
        root=ROOT,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a root-owned ATLAS session through context build, _stack orchestration, Lifeline execution, and Cortex supervision."
    )
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--title")
    parser.add_argument("--session-id")
    parser.add_argument("--scenario", choices=["read-only", "conflict"], default="read-only")
    parser.add_argument("--query-term", action="append", dest="query_terms")
    parser.add_argument("--task-tag", action="append", dest="task_tags")
    args = parser.parse_args(argv)

    task_id = args.task_id.strip()
    title = args.title.strip() if isinstance(args.title, str) and args.title.strip() else f"ATLAS session for {task_id}"
    scenario = args.scenario
    session_id = args.session_id.strip() if isinstance(args.session_id, str) and args.session_id.strip() else (
        f"session-{slugify(task_id)}-{utc_now().strftime('%Y%m%dT%H%M%SZ')}"
    )
    worker_id = f"{session_id}-worker"
    assignment_id = f"{session_id}-assignment"
    request_id = f"{session_id}-request"
    approval_receipt_id = f"{session_id}-approval"

    session_root = ROOT / "runtime" / "atlas" / "sessions" / session_id
    artifact_root = session_root / "artifacts"
    context_path = artifact_root / "worker.context.json"
    assignment_path = artifact_root / "worker.assignment.json"
    running_status_path = artifact_root / "worker.status.running.json"
    capability_path = artifact_root / "capability-profile.json"
    request_path = artifact_root / "privileged-action.request.json"
    approval_path = artifact_root / "approval.receipt.json"
    session_manifest_path = session_root / "session.manifest.json"
    supervisor_root = ROOT / "runtime" / "cortex" / "supervisor" / session_id

    lock_payload = load_stack_lock_payload()
    registry_bundle = load_tool_registry_bundle(root=ROOT)
    context_tool = select_tool_entry(registry_bundle, CONTEXT_TOOL_ID)
    supervision_tool = select_tool_entry(registry_bundle, SUPERVISION_TOOL_ID)
    execution_tool = select_tool_entry(registry_bundle, READ_ONLY_EXECUTION_TOOL_ID)
    registry_digest = str(registry_bundle["registry_digest"])
    stack_lock_digest = str(lock_payload.get("lock_digest", "")).strip()
    if not stack_lock_digest:
        raise ValueError("stack.lock.yaml does not declare lock_digest.")

    manifest = session_manifest_template(
        session_id=session_id,
        title=title,
        task_id=task_id,
        scenario="conflict_fixture" if scenario == "conflict" else "read_only",
        stack_lock_digest=stack_lock_digest,
        lock_payload=lock_payload,
        worker_id=worker_id,
        assignment_id=assignment_id,
        registry_digest=registry_digest,
        context_tool=context_tool,
        supervision_tool=supervision_tool,
        execution_tool=execution_tool,
    )

    def persist_manifest() -> None:
        manifest["updated_at"] = isoformat()
        write_json(session_manifest_path, manifest)

    persist_manifest()
    receipt_root: Path | None = None

    try:
        query_terms = args.query_terms or [task_id]
        task_tags = args.task_tags or ["atlas", "session"]

        write_context_artifact(
            assignment_id=assignment_id,
            worker_id=worker_id,
            task_id=task_id,
            stack_lock_digest=stack_lock_digest,
            query_terms=query_terms,
            task_tags=task_tags,
            output_path=context_path,
        )
        manifest["session_state"] = "context_built"
        manifest["worker"]["context_ref"] = atlas_relative(context_path, root=ROOT)
        persist_manifest()

        assignment = build_worker_assignment(
            assignment_id=assignment_id,
            worker_id=worker_id,
            task_id=task_id,
            stack_lock_digest=stack_lock_digest,
            context_ref=manifest["worker"]["context_ref"],
            tool_id=execution_tool["tool_id"],
            extension_id=execution_tool["extension_id"],
            registry_digest=registry_digest,
        )
        write_json(assignment_path, assignment)
        manifest["session_state"] = "assignment_emitted"
        manifest["worker"]["assignment_ref"] = atlas_relative(assignment_path, root=ROOT)
        persist_manifest()

        running_status = build_worker_status(
            worker_id=worker_id,
            assignment_id=assignment_id,
            state="running",
            tool_id=execution_tool["tool_id"],
            extension_id=execution_tool["extension_id"],
            registry_digest=registry_digest,
        )
        write_json(running_status_path, running_status)
        manifest["refs"]["status_refs"] = unique_refs(
            [*manifest["refs"]["status_refs"], atlas_relative(running_status_path, root=ROOT)]
        )
        manifest["session_state"] = "executing"
        persist_manifest()

        capability_profile = build_capability_profile(execution_tool)
        write_json(capability_path, capability_profile)
        manifest["refs"]["capability_profile_ref"] = atlas_relative(capability_path, root=ROOT)

        request = build_privileged_action_request(
            request_id=request_id,
            worker_id=worker_id,
            assignment_id=assignment_id,
            stack_lock_digest=stack_lock_digest,
            session_manifest_ref=atlas_relative(session_manifest_path, root=ROOT),
            assignment_ref=manifest["worker"]["assignment_ref"],
            status_ref=atlas_relative(running_status_path, root=ROOT),
            context_ref=manifest["worker"]["context_ref"],
            capability_profile=capability_profile,
            tool_id=execution_tool["tool_id"],
            extension_id=execution_tool["extension_id"],
            registry_digest=registry_digest,
        )
        approval = build_approval_receipt(
            approval_receipt_id=approval_receipt_id,
            request=request,
        )
        write_json(request_path, request)
        write_json(approval_path, approval)
        manifest["refs"]["request_ref"] = atlas_relative(request_path, root=ROOT)
        manifest["refs"]["approval_receipt_ref"] = atlas_relative(approval_path, root=ROOT)
        persist_manifest()

        execution = run_stack_function(
            "Invoke-StackLifelineExecution",
            RepoRoot=str(ROOT / "repos" / "_stack"),
            WorkerAssignmentRef=manifest["worker"]["assignment_ref"],
            WorkerStatusRef=atlas_relative(running_status_path, root=ROOT),
            RequestRef=manifest["refs"]["request_ref"],
            ApprovalReceiptRef=manifest["refs"]["approval_receipt_ref"],
            CapabilityProfileRef=manifest["refs"]["capability_profile_ref"],
        )
        manifest["session_state"] = "execution_recorded"
        manifest["refs"]["execution_receipt_ref"] = str(execution.get("receipt_ref"))
        manifest["refs"]["bridge_record_ref"] = str(execution.get("bridge_record_ref"))
        manifest["refs"]["status_refs"] = unique_refs(
            [
                *manifest["refs"]["status_refs"],
                str(execution.get("worker_status_update_ref")),
            ]
        )
        receipt_ref = str(execution.get("receipt_ref", "")).strip()
        receipt_root = (ROOT / receipt_ref).resolve().parent if receipt_ref else None
        persist_manifest()

        if scenario == "conflict":
            repo_commit = git_output(ROOT, "rev-parse", "HEAD") or "unknown"
            target_relative = "README-STACK.md"
            file_digest_before = sha256_bytes((ROOT / target_relative).read_bytes())
            conflict_range = build_touched_range(
                target_relative,
                repo_commit=repo_commit,
                file_digest_before=file_digest_before,
            )
            completion_status_path = artifact_root / "worker.status.completed.json"
            completion_status = build_worker_status(
                worker_id=worker_id,
                assignment_id=assignment_id,
                state="completed",
                tool_id=execution_tool["tool_id"],
                extension_id=execution_tool["extension_id"],
                registry_digest=registry_digest,
                output_refs=unique_refs(
                    [
                        manifest["refs"]["request_ref"],
                        manifest["refs"]["approval_receipt_ref"],
                        manifest["refs"]["execution_receipt_ref"],
                    ]
                ),
                touched_ranges=[conflict_range],
                heartbeat_at=utc_now() + timedelta(seconds=2),
            )
            write_json(completion_status_path, completion_status)
            manifest["refs"]["status_refs"] = unique_refs(
                [*manifest["refs"]["status_refs"], atlas_relative(completion_status_path, root=ROOT)]
            )

            fixture_assignment_path = artifact_root / "fixture.worker.assignment.json"
            fixture_status_path = artifact_root / "fixture.worker.status.completed.json"
            fixture_worker_id = f"{worker_id}-fixture"
            fixture_assignment_id = f"{assignment_id}-fixture"
            write_json(
                fixture_assignment_path,
                build_worker_assignment(
                    assignment_id=fixture_assignment_id,
                    worker_id=fixture_worker_id,
                    task_id=f"{task_id}-fixture",
                    stack_lock_digest=stack_lock_digest,
                    context_ref=manifest["worker"]["context_ref"],
                    tool_id=execution_tool["tool_id"],
                    extension_id=execution_tool["extension_id"],
                    registry_digest=registry_digest,
                ),
            )
            write_json(
                fixture_status_path,
                build_worker_status(
                    worker_id=fixture_worker_id,
                    assignment_id=fixture_assignment_id,
                    state="completed",
                    tool_id=execution_tool["tool_id"],
                    extension_id=execution_tool["extension_id"],
                    registry_digest=registry_digest,
                    output_refs=["fixture://conflict"],
                    touched_ranges=[conflict_range],
                    heartbeat_at=utc_now() + timedelta(seconds=3),
                ),
            )

            supervisor_report = run_python_json(
                str(ROOT / "ops" / "cortex" / "supervise_workers.py"),
                "--artifact-path",
                str(artifact_root),
                "--output-dir",
                str(supervisor_root),
            )
            merge_request_paths = [
                atlas_relative(Path(str(path)), root=ROOT)
                for path in supervisor_report.get("written_merge_request_paths", [])
            ]
            manifest["session_state"] = "merge_requested"
            manifest["refs"]["merge_request_refs"] = unique_refs(merge_request_paths)
            persist_manifest()

            consumer = run_stack_function(
                "Invoke-StackSupervisorConsumer",
                RepoRoot=str(ROOT / "repos" / "_stack"),
                ArtifactSearchRoot=str(artifact_root),
                SupervisorOutputRoot=str(supervisor_root),
                TargetWorkerId=worker_id,
            )
            processed = consumer.get("merge_requests", [])
            first_processed = processed[0] if isinstance(processed, list) and processed else {}
            manifest["refs"]["pause_status_refs"] = unique_refs(
                item.get("path")
                for item in first_processed.get("pause_statuses", [])
                if isinstance(item, dict)
            )
            manifest["refs"]["resume_context_refs"] = unique_refs(
                item.get("path")
                for item in first_processed.get("resume_contexts", [])
                if isinstance(item, dict)
            )
            manifest["refs"]["merge_assignment_ref"] = first_processed.get("merge_assignment_ref")
            manifest["refs"]["merge_prompt_ref"] = first_processed.get("merge_prompt_ref")
            manifest["refs"]["merge_context_ref"] = first_processed.get("merge_context_ref")
            manifest["refs"]["merge_completion_ref"] = first_processed.get("completion_path")
            manifest["refs"]["status_refs"] = unique_refs(
                [*manifest["refs"]["status_refs"], *manifest["refs"]["pause_status_refs"]]
            )
            manifest["session_state"] = "resume_ready"
            manifest["completion"]["final_status"] = "resume_ready"
            manifest["completion"]["final_status_ref"] = first_processed.get("completion_path")
        else:
            manifest["session_state"] = "completed"
            manifest["completion"]["final_status"] = "completed"
            manifest["completion"]["final_status_ref"] = execution.get("worker_status_update_ref")

        manifest["completion"]["close_receipt_refs"] = unique_refs(
            [manifest["refs"]["execution_receipt_ref"]]
        )
        manifest["closed_at"] = isoformat()
        persist_manifest()

        written_descriptors = register_session_descriptors(
            session_root=session_root,
            receipt_root=receipt_root,
            supervisor_root=supervisor_root if supervisor_root.exists() else None,
        )
        status_snapshot = render_status_payload(
            ROOT / "runtime" / "cortex" / "artifacts",
            session_id=session_id,
        )
        write_json(session_root / "status.snapshot.json", status_snapshot)

        print(
            json.dumps(
                {
                    "session_id": session_id,
                    "session_manifest_ref": atlas_relative(session_manifest_path, root=ROOT),
                    "session_state": manifest["session_state"],
                    "final_status": manifest["completion"]["final_status"],
                    "execution_receipt_ref": manifest["refs"]["execution_receipt_ref"],
                    "merge_request_refs": manifest["refs"]["merge_request_refs"],
                    "descriptor_count": len(written_descriptors),
                    "status_snapshot_ref": atlas_relative(session_root / "status.snapshot.json", root=ROOT),
                },
                indent=2,
            )
        )
        return 0
    except Exception:
        manifest["session_state"] = "failed"
        manifest["completion"]["final_status"] = "failed"
        manifest["completion"]["final_status_ref"] = manifest["refs"].get("execution_receipt_ref")
        manifest["closed_at"] = isoformat()
        persist_manifest()
        raise


if __name__ == "__main__":
    raise SystemExit(main())
