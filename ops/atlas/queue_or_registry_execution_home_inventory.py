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
RECEIPT_CONTRACT_VERSION = "atlas.privileged-action.receipt.v1"
SESSIONS_ROOT_REF = "runtime/atlas/sessions"
EXECUTION_HOME_ROOT_REF = "runtime/lifeline/worker-execution"
INVENTORY_NOTE = (
    "inventory proves only present Lifeline execution-home receipt population and manifest linkage; "
    "it does not infer canonical supersession unless a reconciled receipt is explicitly present"
)


class QueueOrRegistryExecutionHomeInventoryError(RuntimeError):
    pass


def _normalize_text(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise QueueOrRegistryExecutionHomeInventoryError(f"{field_name} must be a non-empty string.")
    normalized = value.strip()
    if not normalized:
        raise QueueOrRegistryExecutionHomeInventoryError(f"{field_name} must be a non-empty string.")
    return normalized


def _normalize_optional_text(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise QueueOrRegistryExecutionHomeInventoryError(f"{field_name} must be a string when present.")
    normalized = value.strip()
    return normalized or None


def _normalize_string_list(value: Any, *, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise QueueOrRegistryExecutionHomeInventoryError(f"{field_name} must be a list of strings.")
    return [_normalize_text(item, field_name=field_name) for item in value]


def _parse_iso(value: str | None) -> datetime:
    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_json(path: Path, *, root: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise QueueOrRegistryExecutionHomeInventoryError(
            f"Malformed JSON artifact: {atlas_relative(path, root=root)}"
        ) from exc
    if not isinstance(payload, dict):
        raise QueueOrRegistryExecutionHomeInventoryError(
            f"Artifact must be a JSON object: {atlas_relative(path, root=root)}"
        )
    return payload


@dataclass(frozen=True)
class QueueOrRegistryExecutionHomeInventoryEntry:
    session_id: str
    session_ref: str | None
    session_state: str | None
    updated_at: str | None
    assignment_id: str | None
    execution_receipt_ref_present: bool
    close_receipt_ref_count: int
    assignment_root_exists: bool
    receipt_file_count: int
    linked_receipt_ref_count: int
    missing_manifest_receipt_link_count: int
    unlinked_receipt_ref_count: int
    reconciled_receipt_file_count: int

    def to_payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "session_ref": self.session_ref,
            "session_state": self.session_state,
            "updated_at": self.updated_at,
            "assignment_id": self.assignment_id,
            "execution_receipt_ref_present": self.execution_receipt_ref_present,
            "close_receipt_ref_count": self.close_receipt_ref_count,
            "assignment_root_exists": self.assignment_root_exists,
            "receipt_file_count": self.receipt_file_count,
            "linked_receipt_ref_count": self.linked_receipt_ref_count,
            "missing_manifest_receipt_link_count": self.missing_manifest_receipt_link_count,
            "unlinked_receipt_ref_count": self.unlinked_receipt_ref_count,
            "reconciled_receipt_file_count": self.reconciled_receipt_file_count,
        }


@dataclass(frozen=True)
class QueueOrRegistryExecutionHomeInventoryResult:
    execution_home_entries: tuple[QueueOrRegistryExecutionHomeInventoryEntry, ...]
    execution_home_session_count: int
    assignment_root_count: int
    total_receipt_file_count: int
    linked_receipt_ref_count: int
    missing_manifest_receipt_link_count: int
    unlinked_receipt_ref_count: int
    reconciled_receipt_file_count: int
    sessions_with_reconciled_receipts: int
    inventory_note: str = INVENTORY_NOTE
    execution_home_root_ref: str = EXECUTION_HOME_ROOT_REF

    def to_payload(self) -> dict[str, Any]:
        return {
            "execution_home_entries": [item.to_payload() for item in self.execution_home_entries],
            "execution_home_session_count": self.execution_home_session_count,
            "assignment_root_count": self.assignment_root_count,
            "total_receipt_file_count": self.total_receipt_file_count,
            "linked_receipt_ref_count": self.linked_receipt_ref_count,
            "missing_manifest_receipt_link_count": self.missing_manifest_receipt_link_count,
            "unlinked_receipt_ref_count": self.unlinked_receipt_ref_count,
            "reconciled_receipt_file_count": self.reconciled_receipt_file_count,
            "sessions_with_reconciled_receipts": self.sessions_with_reconciled_receipts,
            "inventory_note": self.inventory_note,
            "execution_home_root_ref": self.execution_home_root_ref,
        }


def build_queue_or_registry_execution_home_inventory(
    *,
    root: Path | None = None,
) -> QueueOrRegistryExecutionHomeInventoryResult:
    base_root = (root or atlas_root()).resolve()
    sessions_root = base_root / SESSIONS_ROOT_REF
    execution_home_root = base_root / EXECUTION_HOME_ROOT_REF

    manifest_meta_by_session_id: dict[str, dict[str, Any]] = {}
    manifest_receipt_refs_by_session_id: dict[str, set[str]] = {}

    if sessions_root.exists():
        for manifest_path in sorted(sessions_root.rglob("session.manifest.json")):
            payload = _load_json(manifest_path, root=base_root)
            if _normalize_text(payload.get("contract_version"), field_name="contract_version") != SESSION_CONTRACT_VERSION:
                raise QueueOrRegistryExecutionHomeInventoryError(
                    f"Unexpected session manifest contract_version at {atlas_relative(manifest_path, root=base_root)}"
                )
            session_id = _normalize_text(payload.get("session_id"), field_name="session_id")
            refs = payload.get("refs")
            if not isinstance(refs, dict):
                raise QueueOrRegistryExecutionHomeInventoryError(
                    f"refs must be a JSON object: {atlas_relative(manifest_path, root=base_root)}"
                )
            completion = payload.get("completion")
            if not isinstance(completion, dict):
                raise QueueOrRegistryExecutionHomeInventoryError(
                    f"completion must be a JSON object: {atlas_relative(manifest_path, root=base_root)}"
                )
            linked_receipts = set(
                ref
                for ref in [
                    _normalize_optional_text(refs.get("execution_receipt_ref"), field_name="refs.execution_receipt_ref"),
                    *_normalize_string_list(completion.get("close_receipt_refs", []), field_name="completion.close_receipt_refs"),
                ]
                if ref is not None
            )
            worker = payload.get("worker")
            if not isinstance(worker, dict):
                raise QueueOrRegistryExecutionHomeInventoryError(
                    f"worker must be a JSON object: {atlas_relative(manifest_path, root=base_root)}"
                )
            manifest_meta_by_session_id[session_id] = {
                "session_ref": atlas_relative(manifest_path, root=base_root),
                "session_state": _normalize_optional_text(payload.get("session_state"), field_name="session_state"),
                "updated_at": _normalize_optional_text(payload.get("updated_at"), field_name="updated_at"),
                "assignment_id": _normalize_optional_text(worker.get("assignment_id"), field_name="worker.assignment_id"),
                "close_receipt_ref_count": len(
                    _normalize_string_list(completion.get("close_receipt_refs", []), field_name="completion.close_receipt_refs")
                ),
                "execution_receipt_ref_present": _normalize_optional_text(
                    refs.get("execution_receipt_ref"),
                    field_name="refs.execution_receipt_ref",
                )
                is not None,
            }
            manifest_receipt_refs_by_session_id[session_id] = linked_receipts

    execution_receipt_refs_by_session_id: dict[str, set[str]] = {}
    assignment_root_exists_by_session_id: dict[str, bool] = {}
    reconciled_receipt_counts_by_session_id: dict[str, int] = {}

    if execution_home_root.exists():
        for assignment_root in sorted(path for path in execution_home_root.iterdir() if path.is_dir()):
            assignment_name = assignment_root.name
            if not assignment_name.endswith("-assignment"):
                continue
            session_id = assignment_name[: -len("-assignment")]
            receipt_refs: set[str] = set()
            reconciled_count = 0
            for receipt_path in sorted(assignment_root.glob("receipt*.json")):
                payload = _load_json(receipt_path, root=base_root)
                if _normalize_text(payload.get("contract_version"), field_name="contract_version") != RECEIPT_CONTRACT_VERSION:
                    raise QueueOrRegistryExecutionHomeInventoryError(
                        f"Unexpected execution receipt contract_version at {atlas_relative(receipt_path, root=base_root)}"
                    )
                receipt_refs.add(atlas_relative(receipt_path, root=base_root))
                if _normalize_optional_text(payload.get("supersedes_receipt_ref"), field_name="supersedes_receipt_ref") is not None:
                    reconciled_count += 1
            execution_receipt_refs_by_session_id[session_id] = receipt_refs
            assignment_root_exists_by_session_id[session_id] = True
            reconciled_receipt_counts_by_session_id[session_id] = reconciled_count

    all_session_ids = sorted(set(manifest_meta_by_session_id) | set(execution_receipt_refs_by_session_id))
    entries: list[QueueOrRegistryExecutionHomeInventoryEntry] = []
    linked_total = 0
    missing_total = 0
    unlinked_total = 0
    reconciled_total = 0
    sessions_with_reconciled_receipts = 0

    for session_id in all_session_ids:
        manifest_meta = manifest_meta_by_session_id.get(session_id, {})
        manifest_receipts = manifest_receipt_refs_by_session_id.get(session_id, set())
        execution_receipts = execution_receipt_refs_by_session_id.get(session_id, set())
        linked_refs = manifest_receipts & execution_receipts
        missing_refs = manifest_receipts - execution_receipts
        unlinked_refs = execution_receipts - manifest_receipts
        reconciled_count = reconciled_receipt_counts_by_session_id.get(session_id, 0)

        linked_total += len(linked_refs)
        missing_total += len(missing_refs)
        unlinked_total += len(unlinked_refs)
        reconciled_total += reconciled_count
        if reconciled_count:
            sessions_with_reconciled_receipts += 1

        entries.append(
            QueueOrRegistryExecutionHomeInventoryEntry(
                session_id=session_id,
                session_ref=manifest_meta.get("session_ref"),
                session_state=manifest_meta.get("session_state"),
                updated_at=manifest_meta.get("updated_at"),
                assignment_id=manifest_meta.get("assignment_id"),
                execution_receipt_ref_present=bool(manifest_meta.get("execution_receipt_ref_present")),
                close_receipt_ref_count=int(manifest_meta.get("close_receipt_ref_count", 0)),
                assignment_root_exists=bool(assignment_root_exists_by_session_id.get(session_id)),
                receipt_file_count=len(execution_receipts),
                linked_receipt_ref_count=len(linked_refs),
                missing_manifest_receipt_link_count=len(missing_refs),
                unlinked_receipt_ref_count=len(unlinked_refs),
                reconciled_receipt_file_count=reconciled_count,
            )
        )

    entries.sort(key=lambda item: (_parse_iso(item.updated_at), item.session_id), reverse=True)

    return QueueOrRegistryExecutionHomeInventoryResult(
        execution_home_entries=tuple(entries),
        execution_home_session_count=len(entries),
        assignment_root_count=sum(1 for item in entries if item.assignment_root_exists),
        total_receipt_file_count=sum(item.receipt_file_count for item in entries),
        linked_receipt_ref_count=linked_total,
        missing_manifest_receipt_link_count=missing_total,
        unlinked_receipt_ref_count=unlinked_total,
        reconciled_receipt_file_count=reconciled_total,
        sessions_with_reconciled_receipts=sessions_with_reconciled_receipts,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inventory queue-or-registry execution-home receipt runtime and manifest linkage."
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    args = parser.parse_args(argv)

    try:
        payload = build_queue_or_registry_execution_home_inventory(root=args.root.resolve()).to_payload()
    except QueueOrRegistryExecutionHomeInventoryError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
