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

from ops._atlas import atlas_relative, atlas_root, resolve_atlas_path
from ops.atlas.backfill_legacy_runtime_artifacts import backfill_legacy_runtime_artifacts
from ops.atlas.load_tool_registry import load_tool_registry_bundle
from ops.cortex._artifacts import load_descriptors
from ops.cortex.index_working_memory import load_working_memory_catalog

STATUS_VERSION = "atlas.cortex.status.v2"
ACTIVE_SESSION_STATES = {
    "created",
    "context_built",
    "assignment_emitted",
    "executing",
    "execution_recorded",
    "merge_requested",
    "resume_ready",
}
BLOCKED_WORKER_STATES = {"blocked", "paused", "merge_wait"}
SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


def parse_timestamp(value: Any) -> tuple[int, str]:
    if not isinstance(value, str) or not value.strip():
        return (0, "")
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return (0, value.strip())
    return (int(parsed.timestamp()), value.strip())


def choose_latest_session(descriptors: list[dict[str, Any]]) -> dict[str, Any] | None:
    sessions = [item for item in descriptors if item.get("artifact_type") == "session_manifest"]
    if not sessions:
        return None
    sessions.sort(
        key=lambda item: (
            item.get("state", {}).get("session_state") not in ACTIVE_SESSION_STATES,
            -parse_timestamp(item.get("state", {}).get("updated_at"))[0],
            str(item.get("source_ref", "")),
        )
    )
    return sessions[0]


def latest_worker_states(descriptors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for descriptor in descriptors:
        if descriptor.get("artifact_type") != "worker_status":
            continue
        worker_id = str(descriptor.get("identity", {}).get("worker_id", "")).strip()
        if not worker_id:
            continue
        previous = latest.get(worker_id)
        if previous is None or parse_timestamp(descriptor.get("state", {}).get("heartbeat_at")) > parse_timestamp(previous.get("state", {}).get("heartbeat_at")):
            latest[worker_id] = descriptor
    return [latest[key] for key in sorted(latest)]


def artifact_inventory(descriptors: list[dict[str, Any]]) -> dict[str, Any]:
    by_type: dict[str, int] = {}
    artifacts: list[dict[str, Any]] = []
    for descriptor in descriptors:
        artifact_type = str(descriptor.get("artifact_type", "unknown"))
        by_type[artifact_type] = by_type.get(artifact_type, 0) + 1
        artifacts.append(
            {
                "artifact_type": artifact_type,
                "source_ref": descriptor.get("source_ref"),
                "digest": descriptor.get("digest"),
                "trust_class": descriptor.get("trust_class"),
            }
        )
    artifacts.sort(key=lambda item: (str(item["artifact_type"]), str(item["source_ref"])))
    return {
        "descriptor_count": len(descriptors),
        "by_type": dict(sorted(by_type.items())),
        "artifacts": artifacts,
    }


def load_registry_state() -> dict[str, Any]:
    try:
        bundle = load_tool_registry_bundle(root=atlas_root())
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
            "tool_ids": set(),
            "extension_ids": set(),
        }
    tool_entries = bundle.get("tool_registry", {}).get("entries", [])
    extension_entries = bundle.get("extension_registry", {}).get("entries", [])
    return {
        "ok": True,
        "bundle": bundle,
        "registry_digest": bundle.get("registry_digest"),
        "tool_registry_digest": bundle.get("tool_registry_digest"),
        "extension_registry_digest": bundle.get("extension_registry_digest"),
        "tool_count": bundle.get("tool_count"),
        "extension_count": bundle.get("extension_count"),
        "tool_ids": {
            str(entry.get("tool_id"))
            for entry in tool_entries
            if isinstance(entry, dict) and isinstance(entry.get("tool_id"), str)
        },
        "extension_ids": {
            str(entry.get("extension_id"))
            for entry in extension_entries
            if isinstance(entry, dict) and isinstance(entry.get("extension_id"), str)
        },
    }


def registry_summary(state: dict[str, Any]) -> dict[str, Any]:
    if not state.get("ok"):
        return {"ok": False, "error": state.get("error")}
    return {
        "ok": True,
        "registry_digest": state.get("registry_digest"),
        "tool_registry_digest": state.get("tool_registry_digest"),
        "extension_registry_digest": state.get("extension_registry_digest"),
        "tool_count": state.get("tool_count"),
        "extension_count": state.get("extension_count"),
    }


def blocked_workers(descriptors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for descriptor in latest_worker_states(descriptors):
        state = str(descriptor.get("state", {}).get("worker_state", ""))
        if state not in BLOCKED_WORKER_STATES:
            continue
        results.append(
            {
                "worker_id": descriptor.get("identity", {}).get("worker_id"),
                "assignment_id": descriptor.get("identity", {}).get("assignment_id"),
                "tool_id": descriptor.get("identity", {}).get("tool_id"),
                "extension_id": descriptor.get("identity", {}).get("extension_id"),
                "state": state,
                "blocked_reason": descriptor.get("state", {}).get("blocked_reason"),
                "registry_digest": descriptor.get("state", {}).get("registry_digest"),
                "source_ref": descriptor.get("source_ref"),
            }
        )
    return results


def open_merge_requests(descriptors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    completed_ids = {
        str(item.get("identity", {}).get("merge_request_id"))
        for item in descriptors
        if item.get("artifact_type") == "supervisor_merge_completion"
    }
    results: list[dict[str, Any]] = []
    for descriptor in descriptors:
        if descriptor.get("artifact_type") != "merge_request":
            continue
        merge_request_id = str(descriptor.get("identity", {}).get("merge_request_id", ""))
        if merge_request_id in completed_ids:
            continue
        results.append(
            {
                "merge_request_id": merge_request_id,
                "tool_id": descriptor.get("identity", {}).get("tool_id"),
                "extension_id": descriptor.get("identity", {}).get("extension_id"),
                "registry_digest": descriptor.get("state", {}).get("registry_digest"),
                "conflicting_workers": descriptor.get("links", {}).get("conflicting_workers", []),
                "source_ref": descriptor.get("source_ref"),
            }
        )
    return results


def trust_surfaces(descriptors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for descriptor in descriptors:
        if descriptor.get("artifact_type") != "knowledge_catalog":
            continue
        if descriptor.get("trust_class") == "trusted":
            continue
        results.append(
            {
                "archive_id": descriptor.get("identity", {}).get("archive_id"),
                "trust_class": descriptor.get("trust_class"),
                "indexing_profile": descriptor.get("state", {}).get("indexing_profile"),
                "promotion_status": descriptor.get("state", {}).get("promotion_status"),
                "source_ref": descriptor.get("source_ref"),
            }
        )
    results.sort(key=lambda item: (str(item["trust_class"]), str(item["archive_id"])))
    return results


def closure_receipts(
    descriptors: list[dict[str, Any]],
    *,
    session_descriptor: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if session_descriptor is None:
        return []
    refs = session_descriptor.get("links", {}).get("close_receipt_refs", [])
    if not isinstance(refs, list):
        return []
    by_source_ref = {
        str(descriptor.get("source_ref", "")): descriptor
        for descriptor in descriptors
    }
    results: list[dict[str, Any]] = []
    for ref in refs:
        if not isinstance(ref, str):
            continue
        descriptor = by_source_ref.get(ref)
        if descriptor is None:
            results.append({"source_ref": ref, "missing": True})
            continue
        results.append(
            {
                "source_ref": ref,
                "artifact_type": descriptor.get("artifact_type"),
                "receipt_id": descriptor.get("identity", {}).get("receipt_id"),
                "tool_id": descriptor.get("identity", {}).get("tool_id"),
                "extension_id": descriptor.get("identity", {}).get("extension_id"),
                "result": descriptor.get("state", {}).get("result"),
                "registry_digest": descriptor.get("state", {}).get("registry_digest"),
            }
        )
    return results


def load_source_payload(source_ref: Any) -> dict[str, Any] | None:
    if not isinstance(source_ref, str) or not source_ref.strip():
        return None
    candidate = resolve_atlas_path(source_ref, root=atlas_root())
    if not candidate.exists():
        return None
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def legacy_compatibility_surfaces(descriptors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for descriptor in descriptors:
        if str(descriptor.get("artifact_type", "")) != "legacy_runtime_backfill":
            continue
        source_ref = str(descriptor.get("source_ref", "")).strip()
        identity = descriptor.get("identity", {}) if isinstance(descriptor.get("identity"), dict) else {}
        state = descriptor.get("state", {}) if isinstance(descriptor.get("state"), dict) else {}
        links = descriptor.get("links", {}) if isinstance(descriptor.get("links"), dict) else {}
        governed_identity = links.get("governed_identity") if isinstance(links.get("governed_identity"), dict) else {}
        if not source_ref:
            continue
        items.append(
            {
                "session_id": identity.get("session_id"),
                "source_ref": source_ref,
                "original_session_ref": links.get("original_session_ref"),
                "epoch": state.get("compatibility_class"),
                "cutover_at": state.get("cutover_at"),
                "observed_at": state.get("observed_at"),
                "recorded_at": state.get("recorded_at"),
                "missing_governed_requirements": links.get("missing_governed_requirements", []),
                "governed_identity": governed_identity,
            }
        )
    items.sort(
        key=lambda item: (
            str(item.get("observed_at") or ""),
            str(item.get("session_id") or ""),
            str(item.get("source_ref") or ""),
        )
    )
    return items


def attention_item(
    *,
    kind: str,
    severity: str,
    summary: str,
    source_ref: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    item = {
        "kind": kind,
        "severity": severity,
        "summary": summary,
    }
    if source_ref:
        item["source_ref"] = source_ref
    if details:
        item["details"] = details
    return item


def validate_surface_ref(
    *,
    tool_id: Any,
    extension_id: Any,
    source_ref: str | None,
    scope: str,
    registry_state: dict[str, Any],
) -> list[dict[str, Any]]:
    if not registry_state.get("ok"):
        return []
    items: list[dict[str, Any]] = []
    tool_text = str(tool_id).strip() if isinstance(tool_id, str) else ""
    extension_text = str(extension_id).strip() if isinstance(extension_id, str) else ""
    if tool_text and tool_text not in registry_state.get("tool_ids", set()):
        items.append(
            attention_item(
                kind="unknown_tool_surface",
                severity="high",
                summary=f"{scope} references unknown tool_id '{tool_text}'.",
                source_ref=source_ref,
                details={
                    "scope": scope,
                    "tool_id": tool_text,
                    "extension_id": extension_text or None,
                },
            )
        )
    if extension_text and extension_text not in registry_state.get("extension_ids", set()):
        items.append(
            attention_item(
                kind="unknown_extension_surface",
                severity="high",
                summary=f"{scope} references unknown extension_id '{extension_text}'.",
                source_ref=source_ref,
                details={
                    "scope": scope,
                    "tool_id": tool_text or None,
                    "extension_id": extension_text,
                },
            )
        )
    return items


def attention_queue(
    *,
    active_session: dict[str, Any] | None,
    blocked_workers_payload: list[dict[str, Any]],
    open_merge_requests_payload: list[dict[str, Any]],
    closure_receipts_payload: list[dict[str, Any]],
    legacy_compatibility_payload: list[dict[str, Any]],
    trust_surfaces_payload: list[dict[str, Any]],
    registry_state: dict[str, Any],
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []

    if not registry_state.get("ok"):
        items.append(
            attention_item(
                kind="registry_error",
                severity="critical",
                summary="The governed tool registry could not be loaded.",
                source_ref="docs/registry",
                details={"error": registry_state.get("error")},
            )
        )

    if active_session is not None:
        session_state = str(active_session.get("session_state", "")).strip()
        final_status = str(active_session.get("final_status", "")).strip()
        registry_digest = active_session.get("registry_digest")
        current_digest = registry_state.get("registry_digest")
        if registry_state.get("ok") and registry_digest and current_digest and registry_digest != current_digest:
            items.append(
                attention_item(
                    kind="registry_drift",
                    severity="high",
                    summary="The active session was created against a different registry digest.",
                    source_ref=active_session.get("source_ref"),
                    details={
                        "session_id": active_session.get("session_id"),
                        "session_registry_digest": registry_digest,
                        "current_registry_digest": current_digest,
                    },
                )
            )
        if session_state == "resume_ready" or final_status == "resume_ready":
            items.append(
                attention_item(
                    kind="session_needs_resume",
                    severity="medium",
                    summary="The active session is waiting for an explicit resume or merge follow-up.",
                    source_ref=active_session.get("source_ref"),
                    details={
                        "session_id": active_session.get("session_id"),
                        "task_id": active_session.get("task_id"),
                    },
                )
            )
        if session_state == "failed" or final_status == "failed":
            items.append(
                attention_item(
                    kind="session_failed",
                    severity="high",
                    summary="The active session ended in a failed state.",
                    source_ref=active_session.get("source_ref"),
                    details={
                        "session_id": active_session.get("session_id"),
                        "task_id": active_session.get("task_id"),
                    },
                )
            )
        governed_surfaces = active_session.get("governed_surfaces", {})
        if isinstance(governed_surfaces, dict):
            for scope_name in ("context", "supervision", "execution"):
                scope = governed_surfaces.get(scope_name)
                if not isinstance(scope, dict):
                    continue
                items.extend(
                    validate_surface_ref(
                        tool_id=scope.get("tool_id"),
                        extension_id=scope.get("extension_id"),
                        source_ref=active_session.get("source_ref"),
                        scope=f"active_session.{scope_name}",
                        registry_state=registry_state,
                    )
                )

    for worker in blocked_workers_payload:
        worker_state = str(worker.get("state", "")).strip()
        severity = "high" if worker_state == "blocked" else "medium"
        items.append(
            attention_item(
                kind="blocked_worker",
                severity=severity,
                summary=f"Worker '{worker.get('worker_id')}' is {worker_state or 'blocked'}.",
                source_ref=worker.get("source_ref"),
                details={
                    "worker_id": worker.get("worker_id"),
                    "assignment_id": worker.get("assignment_id"),
                    "state": worker_state or None,
                    "blocked_reason": worker.get("blocked_reason"),
                },
            )
        )
        items.extend(
            validate_surface_ref(
                tool_id=worker.get("tool_id"),
                extension_id=worker.get("extension_id"),
                source_ref=worker.get("source_ref"),
                scope="blocked_worker",
                registry_state=registry_state,
            )
        )

    for merge_request in open_merge_requests_payload:
        items.append(
            attention_item(
                kind="open_merge_request",
                severity="high",
                summary=f"Merge request '{merge_request.get('merge_request_id')}' remains open.",
                source_ref=merge_request.get("source_ref"),
                details={
                    "merge_request_id": merge_request.get("merge_request_id"),
                    "conflicting_workers": merge_request.get("conflicting_workers", []),
                },
            )
        )
        items.extend(
            validate_surface_ref(
                tool_id=merge_request.get("tool_id"),
                extension_id=merge_request.get("extension_id"),
                source_ref=merge_request.get("source_ref"),
                scope="merge_request",
                registry_state=registry_state,
            )
        )

    for receipt in closure_receipts_payload:
        if receipt.get("missing"):
            items.append(
                attention_item(
                    kind="missing_closure_receipt",
                    severity="high",
                    summary="A session closure receipt ref could not be resolved.",
                    source_ref=receipt.get("source_ref"),
                )
            )
            continue
        result = str(receipt.get("result", "")).strip()
        if result and result != "succeeded":
            items.append(
                attention_item(
                    kind="closure_receipt_issue",
                    severity="high" if result == "failed" else "medium",
                    summary=f"Closure receipt '{receipt.get('receipt_id')}' ended with result '{result}'.",
                    source_ref=receipt.get("source_ref"),
                    details={
                        "receipt_id": receipt.get("receipt_id"),
                        "result": result,
                    },
                )
            )
        items.extend(
            validate_surface_ref(
                tool_id=receipt.get("tool_id"),
                extension_id=receipt.get("extension_id"),
                source_ref=receipt.get("source_ref"),
                scope="closure_receipt",
                registry_state=registry_state,
            )
        )

    for trust_surface in trust_surfaces_payload:
        if trust_surface.get("trust_class") != "untrusted":
            continue
        items.append(
            attention_item(
                kind="quarantined_trust_surface",
                severity="medium",
                summary=f"Knowledge surface '{trust_surface.get('archive_id')}' remains untrusted.",
                source_ref=trust_surface.get("source_ref"),
                details={
                    "archive_id": trust_surface.get("archive_id"),
                    "indexing_profile": trust_surface.get("indexing_profile"),
                    "promotion_status": trust_surface.get("promotion_status"),
                },
            )
        )

    items.sort(
        key=lambda item: (
            SEVERITY_ORDER.get(str(item.get("severity")), 99),
            str(item.get("kind", "")),
            str(item.get("source_ref", "")),
            str(item.get("summary", "")),
        )
    )
    highest = items[0]["severity"] if items else None
    return {
        "status": "needs_review" if items else "clear",
        "item_count": len(items),
        "highest_severity": highest,
        "items": items,
    }


def world_model_state() -> dict[str, Any]:
    snapshot_path = atlas_root() / "runtime" / "state" / "atlas" / "world-model.snapshot.latest.json"
    attention_path = atlas_root() / "runtime" / "state" / "atlas" / "world-model.attention.latest.json"
    result: dict[str, Any] = {
        "snapshot_ref": atlas_relative(snapshot_path, root=atlas_root()),
        "attention_ref": atlas_relative(attention_path, root=atlas_root()),
        "snapshot_present": snapshot_path.exists(),
        "attention_present": attention_path.exists(),
    }
    for prefix, path in (("snapshot", snapshot_path), ("attention", attention_path)):
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        result[f"{prefix}_content_digest"] = payload.get("content_digest")
        if prefix == "snapshot":
            inventory_entries = payload.get("inventory_entries", [])
            observations = payload.get("observations", [])
            result["inventory_entry_count"] = len(inventory_entries) if isinstance(inventory_entries, list) else 0
            result["observation_count"] = len(observations) if isinstance(observations, list) else 0
        if prefix == "attention":
            attention_items = payload.get("attention_items", [])
            result["attention_item_count"] = len(attention_items) if isinstance(attention_items, list) else 0
    return result


def working_memory_summary() -> dict[str, Any]:
    catalog = load_working_memory_catalog(atlas_root())
    return {
        "catalog_ref": catalog.get("output_path"),
        "content_digest": catalog.get("content_digest"),
        "item_count": catalog.get("item_count", 0),
        "kind_counts": catalog.get("kind_counts", {}),
        "status_counts": catalog.get("status_counts", {}),
    }


def session_overview(session_descriptor: dict[str, Any] | None) -> dict[str, Any] | None:
    if session_descriptor is None:
        return None
    identity = session_descriptor.get("identity", {})
    state = session_descriptor.get("state", {})
    links = session_descriptor.get("links", {})
    governed_surfaces = links.get("governed_surfaces", {})
    return {
        "session_id": identity.get("session_id"),
        "task_id": identity.get("task_id"),
        "worker_id": identity.get("worker_id"),
        "assignment_id": identity.get("assignment_id"),
        "session_state": state.get("session_state"),
        "scenario": state.get("scenario"),
        "final_status": state.get("final_status"),
        "updated_at": state.get("updated_at"),
        "registry_digest": state.get("registry_digest"),
        "governed_surfaces": governed_surfaces if isinstance(governed_surfaces, dict) else {},
        "execution_receipt_ref": links.get("execution_receipt_ref"),
        "merge_request_refs": links.get("merge_request_refs", []),
        "source_ref": session_descriptor.get("source_ref"),
    }


def render_status_payload(
    descriptor_root: Path,
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    backfill_legacy_runtime_artifacts(root=atlas_root(), descriptor_root=descriptor_root)
    descriptors = load_descriptors(descriptor_root)
    registry_state = load_registry_state()
    target_session = None
    if session_id:
        for descriptor in descriptors:
            if descriptor.get("artifact_type") != "session_manifest":
                continue
            if descriptor.get("identity", {}).get("session_id") == session_id:
                target_session = descriptor
                break
    else:
        target_session = choose_latest_session(descriptors)
    active_session = session_overview(target_session)
    blocked_workers_payload = blocked_workers(descriptors)
    open_merge_requests_payload = open_merge_requests(descriptors)
    closure_receipts_payload = closure_receipts(descriptors, session_descriptor=target_session)
    legacy_compatibility_payload = legacy_compatibility_surfaces(descriptors)
    trust_surfaces_payload = trust_surfaces(descriptors)

    return {
        "schema_version": STATUS_VERSION,
        "descriptor_root": atlas_relative(descriptor_root, root=atlas_root()),
        "registry": registry_summary(registry_state),
        "active_session": active_session,
        "artifact_inventory": artifact_inventory(descriptors),
        "blocked_workers": blocked_workers_payload,
        "open_merge_requests": open_merge_requests_payload,
        "closure_receipts": closure_receipts_payload,
        "legacy_compatibility": legacy_compatibility_payload,
        "trust_surfaces": trust_surfaces_payload,
        "working_memory": working_memory_summary(),
        "attention_queue": attention_queue(
            active_session=active_session,
            blocked_workers_payload=blocked_workers_payload,
            open_merge_requests_payload=open_merge_requests_payload,
            closure_receipts_payload=closure_receipts_payload,
            legacy_compatibility_payload=legacy_compatibility_payload,
            trust_surfaces_payload=trust_surfaces_payload,
            registry_state=registry_state,
        ),
        "world_model": world_model_state(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render a stable ATLAS status view from registered artifact descriptors only."
    )
    parser.add_argument("--descriptor-root", default="runtime/cortex/artifacts")
    parser.add_argument("--session-id")
    args = parser.parse_args(argv)

    descriptor_root = resolve_atlas_path(args.descriptor_root, root=atlas_root())
    payload = render_status_payload(descriptor_root, session_id=args.session_id)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
