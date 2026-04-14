from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.load_tool_registry import load_tool_registry_bundle, select_tool_entry
from ops.atlas.observations import GOVERNED_ARTIFACT_EPOCH_GOVERNED_V1, governed_artifact_epoch_details
from ops.atlas.run_session import (
    CONTEXT_TOOL_ID,
    SUPERVISION_TOOL_ID,
    build_approval_receipt,
    build_capability_profile,
    build_privileged_action_request,
    build_worker_assignment,
    build_worker_status,
    load_stack_lock_payload,
    register_session_descriptors,
    session_manifest_template,
)
from ops.cortex._artifacts import read_json, register_artifact_descriptors, write_json, write_json_if_changed
from ops.cortex.render_status import render_status_payload
from ops.cortex.world_model import world_model_state_root, write_world_model_state

REPORT_VERSION = "atlas.governed-runtime-repair.report.v1"


def _optional_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _parse_iso(value: Any) -> datetime | None:
    text = _optional_string(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalize_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _load_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        payload = read_json(path)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _collect_post_cutover_sessions(root: Path) -> list[Path]:
    sessions_root = root / "runtime" / "atlas" / "sessions"
    if not sessions_root.exists():
        return []
    results: list[Path] = []
    for path in sorted(sessions_root.rglob("session.manifest.json")):
        payload = _load_json_object(path)
        if not payload:
            continue
        epoch = governed_artifact_epoch_details(payload, source_ref=atlas_relative(path, root=root))
        if isinstance(epoch, dict) and epoch.get("epoch") == GOVERNED_ARTIFACT_EPOCH_GOVERNED_V1:
            results.append(path.resolve())
    return results


def _write_report(root: Path, report: dict[str, Any]) -> Path:
    output_path = root / "runtime" / "state" / "atlas" / "governed-runtime-repair" / "latest.json"
    write_json(output_path, report)
    return output_path


def _tool_entry_for(bundle: dict[str, Any], tool_id: str | None, fallback_tool_id: str) -> dict[str, Any]:
    resolved_tool_id = tool_id or fallback_tool_id
    return select_tool_entry(bundle, resolved_tool_id)


def _rebuild_session_manifest(
    *,
    session_payload: dict[str, Any],
    stack_lock_digest: str,
    registry_digest: str,
    lock_payload: dict[str, Any],
    context_tool: dict[str, Any],
    supervision_tool: dict[str, Any],
    execution_tool: dict[str, Any],
) -> dict[str, Any]:
    worker = session_payload.get("worker") if isinstance(session_payload.get("worker"), dict) else {}
    manifest = session_manifest_template(
        session_id=str(session_payload.get("session_id")),
        title=str(session_payload.get("title") or f"ATLAS session for {session_payload.get('task_id')}"),
        task_id=str(session_payload.get("task_id")),
        scenario=str(session_payload.get("scenario") or "read_only"),
        stack_lock_digest=stack_lock_digest,
        lock_payload=lock_payload,
        worker_id=str(worker.get("worker_id")),
        assignment_id=str(worker.get("assignment_id")),
        registry_digest=registry_digest,
        context_tool=context_tool,
        supervision_tool=supervision_tool,
        execution_tool=execution_tool,
    )
    manifest["orchestrator"] = session_payload.get("orchestrator")
    manifest["created_at"] = session_payload.get("created_at")
    manifest["updated_at"] = session_payload.get("updated_at")
    manifest["closed_at"] = session_payload.get("closed_at")
    manifest["session_state"] = session_payload.get("session_state")
    manifest["stack_manifest_ref"] = session_payload.get("stack_manifest_ref")
    manifest["worker"] = session_payload.get("worker")
    manifest["refs"] = session_payload.get("refs")
    manifest["completion"] = session_payload.get("completion")
    return manifest


def _rebuild_assignment(
    *,
    existing: dict[str, Any],
    session_payload: dict[str, Any],
    stack_lock_digest: str,
    registry_digest: str,
    execution_tool: dict[str, Any],
) -> dict[str, Any]:
    worker = session_payload.get("worker") if isinstance(session_payload.get("worker"), dict) else {}
    return build_worker_assignment(
        assignment_id=str(existing.get("assignment_id")),
        worker_id=str(existing.get("worker_id")),
        task_id=str(existing.get("task_id") or session_payload.get("task_id")),
        stack_lock_digest=stack_lock_digest,
        context_ref=str(worker.get("context_ref") or (existing.get("input_handoff_refs") or [""])[0]),
        tool_id=str(execution_tool["tool_id"]),
        extension_id=execution_tool.get("extension_id"),
        registry_digest=registry_digest,
    )


def _rebuild_status(
    *,
    existing: dict[str, Any],
    registry_digest: str,
    execution_tool: dict[str, Any],
) -> dict[str, Any]:
    return build_worker_status(
        worker_id=str(existing.get("worker_id")),
        assignment_id=str(existing.get("assignment_id")),
        state=str(existing.get("state")),
        tool_id=str(execution_tool["tool_id"]),
        extension_id=execution_tool.get("extension_id"),
        registry_digest=registry_digest,
        output_refs=list(existing.get("output_refs", [])) if isinstance(existing.get("output_refs"), list) else [],
        touched_ranges=list(existing.get("touched_ranges", [])) if isinstance(existing.get("touched_ranges"), list) else [],
        blocked_reason=_normalize_optional_string(existing.get("blocked_reason")),
        merge_request_ref=_normalize_optional_string(existing.get("merge_request_ref")),
        heartbeat_at=_parse_iso(existing.get("heartbeat_at")),
    )


def _rebuild_request(
    *,
    existing: dict[str, Any],
    session_manifest_ref: str,
    assignment_ref: str,
    running_status_ref: str,
    context_ref: str,
    stack_lock_digest: str,
    registry_digest: str,
    capability_profile: dict[str, Any],
    execution_tool: dict[str, Any],
) -> dict[str, Any]:
    payload = build_privileged_action_request(
        request_id=str(existing.get("request_id")),
        worker_id=str(existing.get("worker_id")),
        assignment_id=str(existing.get("assignment_id")),
        stack_lock_digest=stack_lock_digest,
        session_manifest_ref=session_manifest_ref,
        assignment_ref=assignment_ref,
        status_ref=running_status_ref,
        context_ref=context_ref,
        capability_profile=capability_profile,
        tool_id=str(execution_tool["tool_id"]),
        extension_id=execution_tool.get("extension_id"),
        registry_digest=registry_digest,
    )
    payload["requested_at"] = existing.get("requested_at")
    return payload


def _rebuild_approval(*, existing: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    payload = build_approval_receipt(
        approval_receipt_id=str(existing.get("approval_receipt_id")),
        request=request,
    )
    payload["issued_at"] = existing.get("issued_at")
    payload["expiry_at"] = existing.get("expiry_at")
    return payload


def _rebuild_merge_request(
    *,
    existing: dict[str, Any],
    registry_digest: str,
    execution_tool: dict[str, Any],
) -> dict[str, Any]:
    payload = json.loads(json.dumps(existing))
    payload["tool_id"] = execution_tool["tool_id"]
    payload["extension_id"] = execution_tool.get("extension_id")
    payload["registry_digest"] = registry_digest
    merge_worker_handoff = payload.get("merge_worker_handoff")
    if isinstance(merge_worker_handoff, dict):
        merge_worker_handoff["tool_id"] = execution_tool["tool_id"]
        merge_worker_handoff["extension_id"] = execution_tool.get("extension_id")
        merge_worker_handoff["registry_digest"] = registry_digest
    return payload


def _repair_session(
    *,
    session_path: Path,
    registry_bundle: dict[str, Any],
    lock_payload: dict[str, Any],
    apply_changes: bool,
) -> dict[str, Any]:
    session_payload = read_json(session_path)
    if not isinstance(session_payload, dict):
        raise ValueError(f"Expected JSON object at {atlas_relative(session_path, root=ROOT)}")

    session_root = session_path.parent
    artifact_root = session_root / "artifacts"
    session_ref = atlas_relative(session_path, root=ROOT)
    session_id = str(session_payload.get("session_id"))
    registry_digest = str(registry_bundle["registry_digest"])
    stack_lock_digest = str(lock_payload.get("lock_digest") or session_payload.get("stack_lock_digest") or "")
    governed_surfaces = session_payload.get("governed_surfaces") if isinstance(session_payload.get("governed_surfaces"), dict) else {}
    worker = session_payload.get("worker") if isinstance(session_payload.get("worker"), dict) else {}
    refs = session_payload.get("refs") if isinstance(session_payload.get("refs"), dict) else {}

    context_tool = _tool_entry_for(registry_bundle, _optional_string((governed_surfaces.get("context") or {}).get("tool_id") if isinstance(governed_surfaces.get("context"), dict) else None), CONTEXT_TOOL_ID)
    supervision_tool = _tool_entry_for(registry_bundle, _optional_string((governed_surfaces.get("supervision") or {}).get("tool_id") if isinstance(governed_surfaces.get("supervision"), dict) else None), SUPERVISION_TOOL_ID)
    execution_tool_id = _optional_string((governed_surfaces.get("execution") or {}).get("tool_id") if isinstance(governed_surfaces.get("execution"), dict) else None) or _optional_string(worker.get("tool_id")) or _optional_string((read_json(artifact_root / "worker.assignment.json").get("tool_id") if (artifact_root / "worker.assignment.json").exists() else None))
    if execution_tool_id is None:
        raise ValueError(f"{session_ref} does not declare an execution tool_id.")
    execution_tool = select_tool_entry(registry_bundle, execution_tool_id)
    capability_profile = build_capability_profile(execution_tool)

    repaired: list[str] = []
    unchanged: list[str] = []
    replay_required: list[str] = []

    def persist(path: Path, payload: dict[str, Any], reason: str) -> None:
        changed = write_json_if_changed(path, payload) if apply_changes else _load_json_object(path) != payload
        ref = atlas_relative(path, root=ROOT)
        if changed:
            repaired.append(f"{ref} ({reason})")
        else:
            unchanged.append(ref)

    manifest_payload = _rebuild_session_manifest(
        session_payload=session_payload,
        stack_lock_digest=stack_lock_digest,
        registry_digest=registry_digest,
        lock_payload=lock_payload,
        context_tool=context_tool,
        supervision_tool=supervision_tool,
        execution_tool=execution_tool,
    )
    persist(session_path, manifest_payload, "rebuild_session_manifest")

    capability_ref = _optional_string(refs.get("capability_profile_ref"))
    if capability_ref:
        persist((ROOT / capability_ref).resolve(), capability_profile, "rebuild_capability_profile")

    assignment_paths = sorted(path for path in artifact_root.rglob("*.json") if _load_json_object(path) and _load_json_object(path).get("contract_version") == "atlas.worker.assignment.v1")
    for assignment_path in assignment_paths:
        existing = read_json(assignment_path)
        if not isinstance(existing, dict):
            continue
        persist(
            assignment_path,
            _rebuild_assignment(
                existing=existing,
                session_payload=session_payload,
                stack_lock_digest=stack_lock_digest,
                registry_digest=registry_digest,
                execution_tool=execution_tool,
            ),
            "rebuild_worker_assignment",
        )

    status_paths = sorted(path for path in artifact_root.rglob("*.json") if _load_json_object(path) and _load_json_object(path).get("contract_version") == "atlas.worker.status.v1")
    for status_path in status_paths:
        existing = read_json(status_path)
        if not isinstance(existing, dict):
            continue
        persist(
            status_path,
            _rebuild_status(
                existing=existing,
                registry_digest=registry_digest,
                execution_tool=execution_tool,
            ),
            "rebuild_worker_status",
        )

    request_ref = _optional_string(refs.get("request_ref"))
    running_status_ref = next(
        (
            ref
            for ref in refs.get("status_refs", [])
            if isinstance(ref, str) and "running" in ref
        ),
        None,
    )
    context_ref = _optional_string(worker.get("context_ref"))
    assignment_ref = _optional_string(worker.get("assignment_ref"))
    if request_ref and running_status_ref and context_ref and assignment_ref:
        request_path = (ROOT / request_ref).resolve()
        existing_request = _load_json_object(request_path)
        if existing_request:
            request_payload = _rebuild_request(
                existing=existing_request,
                session_manifest_ref=session_ref,
                assignment_ref=assignment_ref,
                running_status_ref=running_status_ref,
                context_ref=context_ref,
                stack_lock_digest=stack_lock_digest,
                registry_digest=registry_digest,
                capability_profile=capability_profile,
                execution_tool=execution_tool,
            )
            persist(request_path, request_payload, "rebuild_privileged_action_request")

            approval_ref = _optional_string(refs.get("approval_receipt_ref"))
            if approval_ref:
                approval_path = (ROOT / approval_ref).resolve()
                existing_approval = _load_json_object(approval_path)
                if existing_approval:
                    persist(
                        approval_path,
                        _rebuild_approval(existing=existing_approval, request=request_payload),
                        "rebuild_approval_receipt",
                    )

    receipt_ref = _optional_string(refs.get("execution_receipt_ref"))
    receipt_root: Path | None = None
    if receipt_ref:
        receipt_path = (ROOT / receipt_ref).resolve()
        receipt_root = receipt_path.parent if receipt_path.exists() else None
        receipt_payload = _load_json_object(receipt_path)
        if receipt_payload and _optional_string(receipt_payload.get("registry_digest")) != registry_digest:
            replay_required.append(f"{atlas_relative(receipt_path, root=ROOT)} (receipt builder unavailable in root lane)")

    merge_request_refs = [item for item in refs.get("merge_request_refs", []) if isinstance(item, str) and item.strip()]
    supervisor_root: Path | None = None
    if merge_request_refs:
        supervisor_root = ROOT / "runtime" / "cortex" / "supervisor" / session_id
        for merge_request_ref in merge_request_refs:
            merge_request_path = (ROOT / merge_request_ref).resolve()
            existing_merge_request = _load_json_object(merge_request_path)
            if not existing_merge_request:
                replay_required.append(f"{merge_request_ref} (merge request artifact missing)")
                continue
            persist(
                merge_request_path,
                _rebuild_merge_request(
                    existing=existing_merge_request,
                    registry_digest=registry_digest,
                    execution_tool=execution_tool,
                ),
                "rebuild_merge_request",
            )

    if apply_changes:
        register_session_descriptors(
            session_root=session_root,
            receipt_root=receipt_root,
            supervisor_root=supervisor_root if supervisor_root and supervisor_root.exists() else None,
        )
        status_snapshot = render_status_payload(ROOT / "runtime" / "cortex" / "artifacts", session_id=session_id)
        persist(session_root / "status.snapshot.json", status_snapshot, "rebuild_status_snapshot")

    return {
        "session_id": session_id,
        "session_ref": session_ref,
        "registry_digest": registry_digest,
        "repaired": repaired,
        "unchanged": unchanged,
        "replay_required": replay_required,
    }


def reconcile_governed_runtime_artifacts(*, root: Path | None = None, apply_changes: bool = False) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    registry_bundle = load_tool_registry_bundle(root=base_root)
    lock_payload = load_stack_lock_payload()
    session_reports = [
        _repair_session(
            session_path=session_path,
            registry_bundle=registry_bundle,
            lock_payload=lock_payload,
            apply_changes=apply_changes,
        )
        for session_path in _collect_post_cutover_sessions(base_root)
    ]

    if apply_changes:
        summary = write_world_model_state(
            descriptor_root=base_root / "runtime" / "cortex" / "artifacts",
            root=base_root,
        )
        register_artifact_descriptors(
            [world_model_state_root(base_root)],
            output_dir=base_root / "runtime" / "cortex" / "artifacts",
            root=base_root,
        )
    else:
        summary = {
            "snapshot_ref": atlas_relative(world_model_state_root(base_root) / "world-model.snapshot.latest.json", root=base_root),
            "attention_ref": atlas_relative(world_model_state_root(base_root) / "world-model.attention.latest.json", root=base_root),
        }

    report = {
        "schema_version": REPORT_VERSION,
        "mode": "apply" if apply_changes else "dry_run",
        "registry_digest": registry_bundle["registry_digest"],
        "session_count": len(session_reports),
        "repaired_count": sum(len(item["repaired"]) for item in session_reports),
        "replay_required_count": sum(len(item["replay_required"]) for item in session_reports),
        "world_model": summary,
        "sessions": session_reports,
    }
    report["report_ref"] = atlas_relative(_write_report(base_root, report), root=base_root)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reconcile post-cutover governed runtime artifacts against the current ATLAS registry.")
    parser.add_argument("--apply", action="store_true", help="Rewrite rebuildable runtime artifacts in place.")
    args = parser.parse_args(argv)
    report = reconcile_governed_runtime_artifacts(root=atlas_root(), apply_changes=args.apply)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
