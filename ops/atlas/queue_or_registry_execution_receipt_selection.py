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
SELECTION_NOTE = (
    "selection chooses canonical execution-home receipt truth only when manifest linkage and explicit supersedes "
    "relations make one receipt deterministically stronger than the others"
)


class QueueOrRegistryExecutionReceiptSelectionError(RuntimeError):
    pass


def _normalize_text(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise QueueOrRegistryExecutionReceiptSelectionError(f"{field_name} must be a non-empty string.")
    normalized = value.strip()
    if not normalized:
        raise QueueOrRegistryExecutionReceiptSelectionError(f"{field_name} must be a non-empty string.")
    return normalized


def _normalize_optional_text(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise QueueOrRegistryExecutionReceiptSelectionError(f"{field_name} must be a string when present.")
    normalized = value.strip()
    return normalized or None


def _parse_iso(value: str | None) -> datetime:
    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_json(path: Path, *, root: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise QueueOrRegistryExecutionReceiptSelectionError(
            f"Malformed JSON artifact: {atlas_relative(path, root=root)}"
        ) from exc
    if not isinstance(payload, dict):
        raise QueueOrRegistryExecutionReceiptSelectionError(
            f"Artifact must be a JSON object: {atlas_relative(path, root=root)}"
        )
    return payload


@dataclass(frozen=True)
class QueueOrRegistryExecutionReceiptSelectionEntry:
    session_id: str
    session_ref: str
    updated_at: str | None
    manifest_execution_receipt_ref: str | None
    canonical_execution_receipt_ref: str | None
    selection_reason: str
    stale_receipt_refs: tuple[str, ...]
    unselected_receipt_refs: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "session_ref": self.session_ref,
            "updated_at": self.updated_at,
            "manifest_execution_receipt_ref": self.manifest_execution_receipt_ref,
            "canonical_execution_receipt_ref": self.canonical_execution_receipt_ref,
            "selection_reason": self.selection_reason,
            "stale_receipt_refs": list(self.stale_receipt_refs),
            "unselected_receipt_refs": list(self.unselected_receipt_refs),
        }


@dataclass(frozen=True)
class QueueOrRegistryExecutionReceiptSelectionResult:
    session_entries: tuple[QueueOrRegistryExecutionReceiptSelectionEntry, ...]
    session_count: int
    reconciled_canonical_session_count: int
    manifest_primary_canonical_session_count: int
    unresolved_session_count: int
    selection_note: str = SELECTION_NOTE

    def to_payload(self) -> dict[str, Any]:
        return {
            "session_entries": [item.to_payload() for item in self.session_entries],
            "session_count": self.session_count,
            "reconciled_canonical_session_count": self.reconciled_canonical_session_count,
            "manifest_primary_canonical_session_count": self.manifest_primary_canonical_session_count,
            "unresolved_session_count": self.unresolved_session_count,
            "selection_note": self.selection_note,
        }


def build_queue_or_registry_execution_receipt_selection(
    *,
    root: Path | None = None,
) -> QueueOrRegistryExecutionReceiptSelectionResult:
    base_root = (root or atlas_root()).resolve()
    sessions_root = base_root / SESSIONS_ROOT_REF
    execution_home_root = base_root / EXECUTION_HOME_ROOT_REF

    entries: list[QueueOrRegistryExecutionReceiptSelectionEntry] = []
    reconciled_canonical_session_count = 0
    manifest_primary_canonical_session_count = 0
    unresolved_session_count = 0

    if not sessions_root.exists():
        return QueueOrRegistryExecutionReceiptSelectionResult(
            session_entries=(),
            session_count=0,
            reconciled_canonical_session_count=0,
            manifest_primary_canonical_session_count=0,
            unresolved_session_count=0,
        )

    for manifest_path in sorted(sessions_root.rglob("session.manifest.json")):
        payload = _load_json(manifest_path, root=base_root)
        if _normalize_text(payload.get("contract_version"), field_name="contract_version") != SESSION_CONTRACT_VERSION:
            raise QueueOrRegistryExecutionReceiptSelectionError(
                f"Unexpected session manifest contract_version at {atlas_relative(manifest_path, root=base_root)}"
            )
        session_id = _normalize_text(payload.get("session_id"), field_name="session_id")
        updated_at = _normalize_optional_text(payload.get("updated_at"), field_name="updated_at")
        refs = payload.get("refs")
        worker = payload.get("worker")
        if not isinstance(refs, dict) or not isinstance(worker, dict):
            raise QueueOrRegistryExecutionReceiptSelectionError(
                f"refs and worker must be JSON objects: {atlas_relative(manifest_path, root=base_root)}"
            )
        manifest_execution_receipt_ref = _normalize_optional_text(
            refs.get("execution_receipt_ref"),
            field_name="refs.execution_receipt_ref",
        )
        assignment_id = _normalize_optional_text(worker.get("assignment_id"), field_name="worker.assignment_id")
        assignment_root = execution_home_root / assignment_id if assignment_id else None

        receipt_refs: list[str] = []
        supersedes_map: dict[str, list[str]] = {}
        if assignment_root is not None and assignment_root.exists():
            for receipt_path in sorted(assignment_root.glob("receipt*.json")):
                receipt_payload = _load_json(receipt_path, root=base_root)
                if _normalize_text(receipt_payload.get("contract_version"), field_name="contract_version") != RECEIPT_CONTRACT_VERSION:
                    raise QueueOrRegistryExecutionReceiptSelectionError(
                        f"Unexpected execution receipt contract_version at {atlas_relative(receipt_path, root=base_root)}"
                    )
                receipt_ref = atlas_relative(receipt_path, root=base_root)
                receipt_refs.append(receipt_ref)
                supersedes_ref = _normalize_optional_text(
                    receipt_payload.get("supersedes_receipt_ref"),
                    field_name="supersedes_receipt_ref",
                )
                if supersedes_ref is not None:
                    supersedes_map.setdefault(supersedes_ref, []).append(receipt_ref)

        canonical_ref: str | None = None
        selection_reason = "no-receipt-files-present"
        stale_receipt_refs: list[str] = []
        unselected_receipt_refs: list[str] = []

        if manifest_execution_receipt_ref is not None:
            superseding_receipts = supersedes_map.get(manifest_execution_receipt_ref, [])
            if len(superseding_receipts) > 1:
                raise QueueOrRegistryExecutionReceiptSelectionError(
                    f"Multiple reconciled receipts supersede {manifest_execution_receipt_ref} for {session_id}."
                )
            if len(superseding_receipts) == 1:
                canonical_ref = superseding_receipts[0]
                selection_reason = "reconciled-supersedes-manifest-linked-receipt"
                stale_receipt_refs = [manifest_execution_receipt_ref]
                unselected_receipt_refs = sorted(
                    ref
                    for ref in receipt_refs
                    if ref not in {canonical_ref, manifest_execution_receipt_ref}
                )
                reconciled_canonical_session_count += 1
            elif manifest_execution_receipt_ref in receipt_refs:
                canonical_ref = manifest_execution_receipt_ref
                selection_reason = "manifest-linked-primary-receipt"
                unselected_receipt_refs = sorted(ref for ref in receipt_refs if ref != canonical_ref)
                manifest_primary_canonical_session_count += 1
            else:
                selection_reason = "manifest-linked-receipt-missing-on-disk"
                unselected_receipt_refs = sorted(receipt_refs)
                unresolved_session_count += 1
        elif len(receipt_refs) == 1:
            canonical_ref = receipt_refs[0]
            selection_reason = "single-unlinked-receipt-only"
            unresolved_session_count += 1
        elif len(receipt_refs) > 1:
            selection_reason = "multiple-unlinked-receipts-without-manifest-link"
            unselected_receipt_refs = sorted(receipt_refs)
            unresolved_session_count += 1
        else:
            unresolved_session_count += 1

        entries.append(
            QueueOrRegistryExecutionReceiptSelectionEntry(
                session_id=session_id,
                session_ref=atlas_relative(manifest_path, root=base_root),
                updated_at=updated_at,
                manifest_execution_receipt_ref=manifest_execution_receipt_ref,
                canonical_execution_receipt_ref=canonical_ref,
                selection_reason=selection_reason,
                stale_receipt_refs=tuple(sorted(stale_receipt_refs)),
                unselected_receipt_refs=tuple(unselected_receipt_refs),
            )
        )

    entries.sort(key=lambda item: (_parse_iso(item.updated_at), item.session_id), reverse=True)
    return QueueOrRegistryExecutionReceiptSelectionResult(
        session_entries=tuple(entries),
        session_count=len(entries),
        reconciled_canonical_session_count=reconciled_canonical_session_count,
        manifest_primary_canonical_session_count=manifest_primary_canonical_session_count,
        unresolved_session_count=unresolved_session_count,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Select canonical queue-or-registry execution-home receipts from manifest-linked and reconciled variants."
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    args = parser.parse_args(argv)

    try:
        payload = build_queue_or_registry_execution_receipt_selection(root=args.root.resolve()).to_payload()
    except QueueOrRegistryExecutionReceiptSelectionError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
