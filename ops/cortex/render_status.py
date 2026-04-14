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
from ops.cortex._artifacts import load_descriptors

STATUS_VERSION = "atlas.cortex.status.v1"
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
                "state": state,
                "blocked_reason": descriptor.get("state", {}).get("blocked_reason"),
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
                "result": descriptor.get("state", {}).get("result"),
            }
        )
    return results


def session_overview(session_descriptor: dict[str, Any] | None) -> dict[str, Any] | None:
    if session_descriptor is None:
        return None
    identity = session_descriptor.get("identity", {})
    state = session_descriptor.get("state", {})
    links = session_descriptor.get("links", {})
    return {
        "session_id": identity.get("session_id"),
        "task_id": identity.get("task_id"),
        "worker_id": identity.get("worker_id"),
        "assignment_id": identity.get("assignment_id"),
        "session_state": state.get("session_state"),
        "scenario": state.get("scenario"),
        "final_status": state.get("final_status"),
        "updated_at": state.get("updated_at"),
        "execution_receipt_ref": links.get("execution_receipt_ref"),
        "merge_request_refs": links.get("merge_request_refs", []),
        "source_ref": session_descriptor.get("source_ref"),
    }


def render_status_payload(
    descriptor_root: Path,
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    descriptors = load_descriptors(descriptor_root)
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

    return {
        "schema_version": STATUS_VERSION,
        "descriptor_root": atlas_relative(descriptor_root, root=atlas_root()),
        "active_session": session_overview(target_session),
        "artifact_inventory": artifact_inventory(descriptors),
        "blocked_workers": blocked_workers(descriptors),
        "open_merge_requests": open_merge_requests(descriptors),
        "closure_receipts": closure_receipts(descriptors, session_descriptor=target_session),
        "trust_surfaces": trust_surfaces(descriptors),
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
