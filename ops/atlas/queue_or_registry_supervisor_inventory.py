from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root

SESSION_CONTRACT_VERSION = "atlas.session.v1"
MERGE_REQUEST_CONTRACT_VERSION = "atlas.worker.merge-request.v1"
SESSIONS_ROOT_REF = "runtime/atlas/sessions"
SUPERVISOR_ROOT_REF = "runtime/cortex/supervisor"
INVENTORY_NOTE = (
    "inventory proves only present supervisor merge-request population and manifest linkage; "
    "it does not infer merge-consumer completion from extra or unlinked artifacts"
)


class QueueOrRegistrySupervisorInventoryError(RuntimeError):
    pass


def _normalize_text(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise QueueOrRegistrySupervisorInventoryError(f"{field_name} must be a non-empty string.")
    normalized = value.strip()
    if not normalized:
        raise QueueOrRegistrySupervisorInventoryError(f"{field_name} must be a non-empty string.")
    return normalized


def _normalize_optional_text(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise QueueOrRegistrySupervisorInventoryError(f"{field_name} must be a string when present.")
    normalized = value.strip()
    return normalized or None


def _normalize_string_list(value: Any, *, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise QueueOrRegistrySupervisorInventoryError(f"{field_name} must be a list of strings.")
    return [_normalize_text(item, field_name=field_name) for item in value]


def _parse_iso(value: str | None) -> datetime:
    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_json(path: Path, *, root: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise QueueOrRegistrySupervisorInventoryError(
            f"Malformed JSON artifact: {atlas_relative(path, root=root)}"
        ) from exc
    if not isinstance(payload, dict):
        raise QueueOrRegistrySupervisorInventoryError(
            f"Artifact must be a JSON object: {atlas_relative(path, root=root)}"
        )
    return payload


@dataclass(frozen=True)
class QueueOrRegistrySupervisorInventoryEntry:
    session_id: str
    session_ref: str | None
    scenario: str | None
    session_state: str | None
    updated_at: str | None
    manifest_merge_request_ref_count: int
    supervisor_merge_request_file_count: int
    linked_supervisor_merge_request_ref_count: int
    missing_manifest_link_count: int
    unlinked_supervisor_merge_request_ref_count: int
    conflicting_worker_count: int

    def to_payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "session_ref": self.session_ref,
            "scenario": self.scenario,
            "session_state": self.session_state,
            "updated_at": self.updated_at,
            "manifest_merge_request_ref_count": self.manifest_merge_request_ref_count,
            "supervisor_merge_request_file_count": self.supervisor_merge_request_file_count,
            "linked_supervisor_merge_request_ref_count": self.linked_supervisor_merge_request_ref_count,
            "missing_manifest_link_count": self.missing_manifest_link_count,
            "unlinked_supervisor_merge_request_ref_count": self.unlinked_supervisor_merge_request_ref_count,
            "conflicting_worker_count": self.conflicting_worker_count,
        }


@dataclass(frozen=True)
class QueueOrRegistrySupervisorInventoryResult:
    supervisor_session_entries: tuple[QueueOrRegistrySupervisorInventoryEntry, ...]
    supervisor_session_count: int
    total_merge_request_file_count: int
    linked_merge_request_ref_count: int
    missing_manifest_link_count: int
    unlinked_merge_request_ref_count: int
    multi_merge_request_session_count: int
    sessions_with_supervisor_artifacts_and_no_manifest_links: int
    inventory_note: str = INVENTORY_NOTE
    supervisor_root_ref: str = SUPERVISOR_ROOT_REF

    def to_payload(self) -> dict[str, Any]:
        return {
            "supervisor_session_entries": [item.to_payload() for item in self.supervisor_session_entries],
            "supervisor_session_count": self.supervisor_session_count,
            "total_merge_request_file_count": self.total_merge_request_file_count,
            "linked_merge_request_ref_count": self.linked_merge_request_ref_count,
            "missing_manifest_link_count": self.missing_manifest_link_count,
            "unlinked_merge_request_ref_count": self.unlinked_merge_request_ref_count,
            "multi_merge_request_session_count": self.multi_merge_request_session_count,
            "sessions_with_supervisor_artifacts_and_no_manifest_links": self.sessions_with_supervisor_artifacts_and_no_manifest_links,
            "inventory_note": self.inventory_note,
            "supervisor_root_ref": self.supervisor_root_ref,
        }


def build_queue_or_registry_supervisor_inventory(
    *,
    root: Path | None = None,
) -> QueueOrRegistrySupervisorInventoryResult:
    base_root = (root or atlas_root()).resolve()
    sessions_root = base_root / SESSIONS_ROOT_REF
    supervisor_root = base_root / SUPERVISOR_ROOT_REF

    manifest_by_session_id: dict[str, dict[str, Any]] = {}
    manifest_merge_refs_by_session_id: dict[str, set[str]] = {}

    if sessions_root.exists():
        for manifest_path in sorted(sessions_root.rglob("session.manifest.json")):
            payload = _load_json(manifest_path, root=base_root)
            if _normalize_text(payload.get("contract_version"), field_name="contract_version") != SESSION_CONTRACT_VERSION:
                raise QueueOrRegistrySupervisorInventoryError(
                    f"Unexpected session manifest contract_version at {atlas_relative(manifest_path, root=base_root)}"
                )
            session_id = _normalize_text(payload.get("session_id"), field_name="session_id")
            refs = payload.get("refs")
            if not isinstance(refs, dict):
                raise QueueOrRegistrySupervisorInventoryError(
                    f"refs must be a JSON object: {atlas_relative(manifest_path, root=base_root)}"
                )
            merge_refs = set(_normalize_string_list(refs.get("merge_request_refs", []), field_name="refs.merge_request_refs"))
            manifest_by_session_id[session_id] = {
                "session_ref": atlas_relative(manifest_path, root=base_root),
                "scenario": _normalize_optional_text(payload.get("scenario"), field_name="scenario"),
                "session_state": _normalize_optional_text(payload.get("session_state"), field_name="session_state"),
                "updated_at": _normalize_optional_text(payload.get("updated_at"), field_name="updated_at"),
            }
            manifest_merge_refs_by_session_id[session_id] = merge_refs

    supervisor_merge_refs_by_session_id: dict[str, set[str]] = {}
    conflicting_worker_counts_by_session_id: dict[str, int] = {}

    if supervisor_root.exists():
        for session_dir in sorted(path for path in supervisor_root.iterdir() if path.is_dir()):
            session_id = session_dir.name
            merge_refs: set[str] = set()
            conflicting_worker_count = 0
            for merge_request_path in sorted(session_dir.glob("merge-request-*.json")):
                payload = _load_json(merge_request_path, root=base_root)
                if (
                    _normalize_text(payload.get("contract_version"), field_name="contract_version")
                    != MERGE_REQUEST_CONTRACT_VERSION
                ):
                    raise QueueOrRegistrySupervisorInventoryError(
                        f"Unexpected merge request contract_version at {atlas_relative(merge_request_path, root=base_root)}"
                    )
                merge_refs.add(atlas_relative(merge_request_path, root=base_root))
                conflicting_workers = payload.get("conflicting_workers", [])
                conflicting_worker_count += len(
                    _normalize_string_list(conflicting_workers, field_name="conflicting_workers")
                )
            supervisor_merge_refs_by_session_id[session_id] = merge_refs
            conflicting_worker_counts_by_session_id[session_id] = conflicting_worker_count

    all_session_ids = sorted(set(manifest_by_session_id) | set(supervisor_merge_refs_by_session_id))
    entries: list[QueueOrRegistrySupervisorInventoryEntry] = []
    linked_total = 0
    missing_total = 0
    unlinked_total = 0
    multi_merge_request_session_count = 0
    sessions_with_supervisor_artifacts_and_no_manifest_links = 0

    for session_id in all_session_ids:
        manifest_meta = manifest_by_session_id.get(session_id, {})
        manifest_refs = manifest_merge_refs_by_session_id.get(session_id, set())
        supervisor_refs = supervisor_merge_refs_by_session_id.get(session_id, set())
        linked_refs = manifest_refs & supervisor_refs
        missing_refs = manifest_refs - supervisor_refs
        unlinked_refs = supervisor_refs - manifest_refs

        if len(supervisor_refs) > 1:
            multi_merge_request_session_count += 1
        if supervisor_refs and not linked_refs:
            sessions_with_supervisor_artifacts_and_no_manifest_links += 1

        linked_total += len(linked_refs)
        missing_total += len(missing_refs)
        unlinked_total += len(unlinked_refs)

        entries.append(
            QueueOrRegistrySupervisorInventoryEntry(
                session_id=session_id,
                session_ref=manifest_meta.get("session_ref"),
                scenario=manifest_meta.get("scenario"),
                session_state=manifest_meta.get("session_state"),
                updated_at=manifest_meta.get("updated_at"),
                manifest_merge_request_ref_count=len(manifest_refs),
                supervisor_merge_request_file_count=len(supervisor_refs),
                linked_supervisor_merge_request_ref_count=len(linked_refs),
                missing_manifest_link_count=len(missing_refs),
                unlinked_supervisor_merge_request_ref_count=len(unlinked_refs),
                conflicting_worker_count=conflicting_worker_counts_by_session_id.get(session_id, 0),
            )
        )

    entries.sort(key=lambda item: (_parse_iso(item.updated_at), item.session_id), reverse=True)

    return QueueOrRegistrySupervisorInventoryResult(
        supervisor_session_entries=tuple(entries),
        supervisor_session_count=len(entries),
        total_merge_request_file_count=sum(item.supervisor_merge_request_file_count for item in entries),
        linked_merge_request_ref_count=linked_total,
        missing_manifest_link_count=missing_total,
        unlinked_merge_request_ref_count=unlinked_total,
        multi_merge_request_session_count=multi_merge_request_session_count,
        sessions_with_supervisor_artifacts_and_no_manifest_links=sessions_with_supervisor_artifacts_and_no_manifest_links,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inventory queue-or-registry supervisor merge-request runtime and manifest linkage."
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    args = parser.parse_args(argv)

    try:
        payload = build_queue_or_registry_supervisor_inventory(root=args.root.resolve()).to_payload()
    except QueueOrRegistrySupervisorInventoryError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
