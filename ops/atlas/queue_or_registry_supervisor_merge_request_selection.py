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
from ops.cortex._artifacts import merge_request_lineage_key

SESSION_CONTRACT_VERSION = "atlas.session.v1"
MERGE_REQUEST_CONTRACT_VERSION = "atlas.worker.merge-request.v1"
SUPERVISOR_CONSUMER_VERSION = "atlas.stack.supervisor-consumer.v1"
SESSIONS_ROOT_REF = "runtime/atlas/sessions"
SUPERVISOR_ROOT_REF = "runtime/cortex/supervisor"
SELECTION_NOTE = (
    "selection groups supervisor merge requests by overlap lineage instead of stack-lock-specific conflict key so "
    "older duplicate families collapse into residue once a later linked or completed lineage member exists"
)


class QueueOrRegistrySupervisorMergeRequestSelectionError(RuntimeError):
    pass


def _normalize_text(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise QueueOrRegistrySupervisorMergeRequestSelectionError(f"{field_name} must be a non-empty string.")
    normalized = value.strip()
    if not normalized:
        raise QueueOrRegistrySupervisorMergeRequestSelectionError(f"{field_name} must be a non-empty string.")
    return normalized


def _normalize_optional_text(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise QueueOrRegistrySupervisorMergeRequestSelectionError(f"{field_name} must be a string when present.")
    normalized = value.strip()
    return normalized or None


def _normalize_string_list(value: Any, *, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise QueueOrRegistrySupervisorMergeRequestSelectionError(f"{field_name} must be a list of strings.")
    items: list[str] = []
    seen: set[str] = set()
    for entry in value:
        normalized = _normalize_text(entry, field_name=field_name)
        if normalized in seen:
            continue
        seen.add(normalized)
        items.append(normalized)
    return items


def _parse_iso(value: str | None) -> datetime:
    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_json(path: Path, *, root: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise QueueOrRegistrySupervisorMergeRequestSelectionError(
            f"Malformed JSON artifact: {atlas_relative(path, root=root)}"
        ) from exc
    if not isinstance(payload, dict):
        raise QueueOrRegistrySupervisorMergeRequestSelectionError(
            f"Artifact must be a JSON object: {atlas_relative(path, root=root)}"
        )
    return payload


@dataclass(frozen=True)
class QueueOrRegistrySupervisorMergeRequestSelectionEntry:
    session_id: str
    session_ref: str | None
    updated_at: str | None
    lineage_key: str
    canonical_merge_request_ref: str
    canonical_merge_request_id: str
    canonical_selection_reason: str
    lineage_member_count: int
    linked_merge_request_ref_count: int
    completed_merge_request_id_count: int
    superseded_residue_refs: tuple[str, ...]
    retained_residue_refs: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "session_ref": self.session_ref,
            "updated_at": self.updated_at,
            "lineage_key": self.lineage_key,
            "canonical_merge_request_ref": self.canonical_merge_request_ref,
            "canonical_merge_request_id": self.canonical_merge_request_id,
            "canonical_selection_reason": self.canonical_selection_reason,
            "lineage_member_count": self.lineage_member_count,
            "linked_merge_request_ref_count": self.linked_merge_request_ref_count,
            "completed_merge_request_id_count": self.completed_merge_request_id_count,
            "superseded_residue_refs": list(self.superseded_residue_refs),
            "retained_residue_refs": list(self.retained_residue_refs),
        }


@dataclass(frozen=True)
class QueueOrRegistrySupervisorMergeRequestSelectionResult:
    selection_entries: tuple[QueueOrRegistrySupervisorMergeRequestSelectionEntry, ...]
    selected_lineage_count: int
    canonical_completed_lineage_count: int
    canonical_linked_lineage_count: int
    active_unlinked_lineage_count: int
    superseded_residue_ref_count: int
    retained_residue_ref_count: int
    selection_note: str = SELECTION_NOTE

    def to_payload(self) -> dict[str, Any]:
        return {
            "selection_entries": [item.to_payload() for item in self.selection_entries],
            "selected_lineage_count": self.selected_lineage_count,
            "canonical_completed_lineage_count": self.canonical_completed_lineage_count,
            "canonical_linked_lineage_count": self.canonical_linked_lineage_count,
            "active_unlinked_lineage_count": self.active_unlinked_lineage_count,
            "superseded_residue_ref_count": self.superseded_residue_ref_count,
            "retained_residue_ref_count": self.retained_residue_ref_count,
            "selection_note": self.selection_note,
        }


def build_queue_or_registry_supervisor_merge_request_selection(
    *,
    root: Path | None = None,
) -> QueueOrRegistrySupervisorMergeRequestSelectionResult:
    base_root = (root or atlas_root()).resolve()
    sessions_root = base_root / SESSIONS_ROOT_REF
    supervisor_root = base_root / SUPERVISOR_ROOT_REF

    session_meta_by_id: dict[str, dict[str, Any]] = {}
    linked_merge_refs_by_session_id: dict[str, set[str]] = {}
    completed_merge_ids_by_session_id: dict[str, set[str]] = {}

    if sessions_root.exists():
        for manifest_path in sorted(sessions_root.rglob("session.manifest.json")):
            payload = _load_json(manifest_path, root=base_root)
            if _normalize_text(payload.get("contract_version"), field_name="contract_version") != SESSION_CONTRACT_VERSION:
                raise QueueOrRegistrySupervisorMergeRequestSelectionError(
                    f"Unexpected session manifest contract_version at {atlas_relative(manifest_path, root=base_root)}"
                )
            session_id = _normalize_text(payload.get("session_id"), field_name="session_id")
            refs = payload.get("refs")
            if not isinstance(refs, dict):
                raise QueueOrRegistrySupervisorMergeRequestSelectionError(
                    f"refs must be a JSON object: {atlas_relative(manifest_path, root=base_root)}"
                )
            linked_merge_refs_by_session_id[session_id] = set(
                _normalize_string_list(refs.get("merge_request_refs", []), field_name="refs.merge_request_refs")
            )
            session_meta_by_id[session_id] = {
                "session_ref": atlas_relative(manifest_path, root=base_root),
                "updated_at": _normalize_optional_text(payload.get("updated_at"), field_name="updated_at"),
            }
            merge_completion_ref = _normalize_optional_text(refs.get("merge_completion_ref"), field_name="refs.merge_completion_ref")
            if merge_completion_ref is None:
                continue
            merge_completion_path = base_root / merge_completion_ref
            if not merge_completion_path.exists():
                continue
            completion_payload = _load_json(merge_completion_path, root=base_root)
            contract_version = _normalize_optional_text(
                completion_payload.get("schema_version"),
                field_name="schema_version",
            )
            if contract_version is not None and contract_version != SUPERVISOR_CONSUMER_VERSION:
                raise QueueOrRegistrySupervisorMergeRequestSelectionError(
                    f"Unexpected merge completion schema_version at {merge_completion_ref}"
                )
            merge_request_id = _normalize_optional_text(
                completion_payload.get("merge_request_id"),
                field_name="merge_request_id",
            )
            if merge_request_id:
                completed_merge_ids_by_session_id.setdefault(session_id, set()).add(merge_request_id)

    merge_requests_by_session_id: dict[str, list[dict[str, Any]]] = {}
    if supervisor_root.exists():
        for session_dir in sorted(path for path in supervisor_root.iterdir() if path.is_dir()):
            session_id = session_dir.name
            records: list[dict[str, Any]] = []
            for merge_request_path in sorted(session_dir.glob("merge-request-*.json")):
                payload = _load_json(merge_request_path, root=base_root)
                if _normalize_text(payload.get("contract_version"), field_name="contract_version") != MERGE_REQUEST_CONTRACT_VERSION:
                    raise QueueOrRegistrySupervisorMergeRequestSelectionError(
                        f"Unexpected merge request contract_version at {atlas_relative(merge_request_path, root=base_root)}"
                    )
                source_ref = atlas_relative(merge_request_path, root=base_root)
                records.append(
                    {
                        "source_ref": source_ref,
                        "merge_request_id": _normalize_text(payload.get("merge_request_id"), field_name="merge_request_id"),
                        "lineage_key": merge_request_lineage_key(payload, source_ref=source_ref),
                        "conflicting_workers": _normalize_string_list(
                            payload.get("conflicting_workers", []),
                            field_name="conflicting_workers",
                        ),
                    }
                )
            merge_requests_by_session_id[session_id] = records

    entries: list[QueueOrRegistrySupervisorMergeRequestSelectionEntry] = []
    canonical_completed_lineage_count = 0
    canonical_linked_lineage_count = 0
    active_unlinked_lineage_count = 0
    superseded_residue_ref_count = 0
    retained_residue_ref_count = 0

    for session_id, records in sorted(merge_requests_by_session_id.items()):
        by_lineage: dict[str, list[dict[str, Any]]] = {}
        for record in records:
            by_lineage.setdefault(str(record["lineage_key"]), []).append(record)

        linked_refs = linked_merge_refs_by_session_id.get(session_id, set())
        completed_ids = completed_merge_ids_by_session_id.get(session_id, set())
        session_meta = session_meta_by_id.get(session_id, {})

        for lineage_key, lineage_records in by_lineage.items():
            ordered = sorted(
                lineage_records,
                key=lambda item: (
                    str(item["merge_request_id"]) not in completed_ids,
                    str(item["source_ref"]) not in linked_refs,
                    -len(item["conflicting_workers"]),
                    str(item["source_ref"]),
                ),
            )
            canonical = ordered[0]
            canonical_ref = str(canonical["source_ref"])
            canonical_id = str(canonical["merge_request_id"])
            canonical_completed = canonical_id in completed_ids
            canonical_linked = canonical_ref in linked_refs

            superseded_residue_refs: list[str] = []
            retained_residue_refs: list[str] = []
            for record in ordered[1:]:
                target = superseded_residue_refs if canonical_completed else retained_residue_refs
                target.append(str(record["source_ref"]))

            if canonical_completed:
                canonical_completed_lineage_count += 1
                selection_reason = "completed-lineage-member"
            elif canonical_linked:
                canonical_linked_lineage_count += 1
                selection_reason = "manifest-linked-lineage-member"
            else:
                active_unlinked_lineage_count += 1
                selection_reason = "broadest-unlinked-lineage-member"

            superseded_residue_ref_count += len(superseded_residue_refs)
            retained_residue_ref_count += len(retained_residue_refs)

            entries.append(
                QueueOrRegistrySupervisorMergeRequestSelectionEntry(
                    session_id=session_id,
                    session_ref=session_meta.get("session_ref"),
                    updated_at=session_meta.get("updated_at"),
                    lineage_key=lineage_key,
                    canonical_merge_request_ref=canonical_ref,
                    canonical_merge_request_id=canonical_id,
                    canonical_selection_reason=selection_reason,
                    lineage_member_count=len(lineage_records),
                    linked_merge_request_ref_count=sum(
                        1 for item in lineage_records if str(item["source_ref"]) in linked_refs
                    ),
                    completed_merge_request_id_count=sum(
                        1 for item in lineage_records if str(item["merge_request_id"]) in completed_ids
                    ),
                    superseded_residue_refs=tuple(sorted(superseded_residue_refs)),
                    retained_residue_refs=tuple(sorted(retained_residue_refs)),
                )
            )

    entries.sort(key=lambda item: (_parse_iso(item.updated_at), item.session_id, item.lineage_key), reverse=True)
    return QueueOrRegistrySupervisorMergeRequestSelectionResult(
        selection_entries=tuple(entries),
        selected_lineage_count=len(entries),
        canonical_completed_lineage_count=canonical_completed_lineage_count,
        canonical_linked_lineage_count=canonical_linked_lineage_count,
        active_unlinked_lineage_count=active_unlinked_lineage_count,
        superseded_residue_ref_count=superseded_residue_ref_count,
        retained_residue_ref_count=retained_residue_ref_count,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Select canonical queue-or-registry supervisor merge-request lineage members across stack-lock-specific duplicates."
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    args = parser.parse_args(argv)

    try:
        payload = build_queue_or_registry_supervisor_merge_request_selection(root=args.root.resolve()).to_payload()
    except QueueOrRegistrySupervisorMergeRequestSelectionError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
