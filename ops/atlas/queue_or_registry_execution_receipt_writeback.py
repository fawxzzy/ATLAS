from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.queue_or_registry_execution_receipt_selection import (
    QueueOrRegistryExecutionReceiptSelectionError,
    build_queue_or_registry_execution_receipt_selection,
)
from ops.cortex._artifacts import register_artifact_descriptors, write_json
from ops.cortex.render_status import render_status_payload
from ops.cortex.world_model import world_model_state_root, write_world_model_state

SESSION_CONTRACT_VERSION = "atlas.session.v1"
SUPERVISOR_ROOT_REF = "runtime/cortex/supervisor"
EXECUTION_HOME_ROOT_REF = "runtime/lifeline/worker-execution"
ARTIFACTS_ROOT_REF = "runtime/cortex/artifacts"
KNOWLEDGE_ROOT_REF = "runtime/cortex/catalog/knowledge"
SELECTION_REASON = "reconciled-supersedes-manifest-linked-receipt"


class QueueOrRegistryExecutionReceiptWritebackError(RuntimeError):
    pass


def _normalize_text(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise QueueOrRegistryExecutionReceiptWritebackError(f"{field_name} must be a non-empty string.")
    normalized = value.strip()
    if not normalized:
        raise QueueOrRegistryExecutionReceiptWritebackError(f"{field_name} must be a non-empty string.")
    return normalized


def _normalize_string_list(value: Any, *, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise QueueOrRegistryExecutionReceiptWritebackError(f"{field_name} must be a list when present.")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise QueueOrRegistryExecutionReceiptWritebackError(f"{field_name} must contain only strings.")
        stripped = item.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        normalized.append(stripped)
    return normalized


def _load_json(path: Path, *, root: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise QueueOrRegistryExecutionReceiptWritebackError(
            f"Malformed JSON artifact: {atlas_relative(path, root=root)}"
        ) from exc
    if not isinstance(payload, dict):
        raise QueueOrRegistryExecutionReceiptWritebackError(
            f"Artifact must be a JSON object: {atlas_relative(path, root=root)}"
        )
    return payload


@dataclass(frozen=True)
class QueueOrRegistryExecutionReceiptWritebackEntry:
    session_id: str
    session_ref: str
    selection_reason: str
    execution_receipt_ref_before: str
    execution_receipt_ref_after: str
    close_receipt_refs_before: tuple[str, ...]
    close_receipt_refs_after: tuple[str, ...]
    stale_receipt_refs_removed: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "session_ref": self.session_ref,
            "selection_reason": self.selection_reason,
            "execution_receipt_ref_before": self.execution_receipt_ref_before,
            "execution_receipt_ref_after": self.execution_receipt_ref_after,
            "close_receipt_refs_before": list(self.close_receipt_refs_before),
            "close_receipt_refs_after": list(self.close_receipt_refs_after),
            "stale_receipt_refs_removed": list(self.stale_receipt_refs_removed),
        }


@dataclass(frozen=True)
class QueueOrRegistryExecutionReceiptWritebackResult:
    mode: str
    sync_outputs: bool
    candidate_session_count: int
    updated_session_count: int
    world_model: dict[str, Any] | None
    updated_sessions: tuple[QueueOrRegistryExecutionReceiptWritebackEntry, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "sync_outputs": self.sync_outputs,
            "candidate_session_count": self.candidate_session_count,
            "updated_session_count": self.updated_session_count,
            "world_model": self.world_model,
            "updated_sessions": [item.to_payload() for item in self.updated_sessions],
        }


def _register_session_outputs(
    *,
    session_root: Path,
    receipt_root: Path | None,
    supervisor_root: Path | None,
    root: Path,
) -> None:
    paths = [session_root, root / KNOWLEDGE_ROOT_REF]
    if receipt_root is not None and receipt_root.exists():
        paths.append(receipt_root)
    if supervisor_root is not None and supervisor_root.exists():
        paths.append(supervisor_root)
    register_artifact_descriptors(
        paths,
        output_dir=root / ARTIFACTS_ROOT_REF,
        root=root,
    )


def _sync_updated_sessions(*, sessions: list[dict[str, Any]], root: Path) -> dict[str, Any]:
    for item in sessions:
        _register_session_outputs(
            session_root=item["session_root"],
            receipt_root=item["receipt_root"],
            supervisor_root=item["supervisor_root"],
            root=root,
        )

    world_model_summary = write_world_model_state(
        descriptor_root=root / ARTIFACTS_ROOT_REF,
        root=root,
    )
    register_artifact_descriptors(
        [world_model_state_root(root)],
        output_dir=root / ARTIFACTS_ROOT_REF,
        root=root,
    )

    for item in sessions:
        status_snapshot = render_status_payload(
            root / ARTIFACTS_ROOT_REF,
            session_id=item["session_id"],
        )
        write_json(item["session_root"] / "status.snapshot.json", status_snapshot)

    return world_model_summary


def reconcile_queue_or_registry_execution_receipt_links(
    *,
    root: Path | None = None,
    apply_changes: bool = False,
    sync_outputs: bool = True,
) -> QueueOrRegistryExecutionReceiptWritebackResult:
    base_root = (root or atlas_root()).resolve()
    selection = build_queue_or_registry_execution_receipt_selection(root=base_root)

    updated_entries: list[QueueOrRegistryExecutionReceiptWritebackEntry] = []
    sessions_to_sync: list[dict[str, Any]] = []

    for entry in selection.session_entries:
        if entry.selection_reason != SELECTION_REASON:
            continue
        canonical_ref = entry.canonical_execution_receipt_ref
        current_ref = entry.manifest_execution_receipt_ref
        if not canonical_ref or not current_ref or canonical_ref == current_ref:
            continue

        manifest_path = base_root / entry.session_ref
        payload = _load_json(manifest_path, root=base_root)
        if _normalize_text(payload.get("contract_version"), field_name="contract_version") != SESSION_CONTRACT_VERSION:
            raise QueueOrRegistryExecutionReceiptWritebackError(
                f"Unexpected session manifest contract_version at {entry.session_ref}"
            )
        refs = payload.get("refs")
        completion = payload.get("completion")
        worker = payload.get("worker")
        if not isinstance(refs, dict) or not isinstance(completion, dict) or not isinstance(worker, dict):
            raise QueueOrRegistryExecutionReceiptWritebackError(
                f"refs, completion, and worker must be JSON objects: {entry.session_ref}"
            )

        close_receipt_refs_before = _normalize_string_list(
            completion.get("close_receipt_refs"),
            field_name="completion.close_receipt_refs",
        )
        stale_refs = set(entry.stale_receipt_refs)
        preserved_close_refs = [
            ref for ref in close_receipt_refs_before
            if ref not in stale_refs and ref != canonical_ref
        ]
        close_receipt_refs_after = [canonical_ref, *preserved_close_refs]
        refs["execution_receipt_ref"] = canonical_ref
        completion["close_receipt_refs"] = close_receipt_refs_after

        updated_entries.append(
            QueueOrRegistryExecutionReceiptWritebackEntry(
                session_id=entry.session_id,
                session_ref=entry.session_ref,
                selection_reason=entry.selection_reason,
                execution_receipt_ref_before=current_ref,
                execution_receipt_ref_after=canonical_ref,
                close_receipt_refs_before=tuple(close_receipt_refs_before),
                close_receipt_refs_after=tuple(close_receipt_refs_after),
                stale_receipt_refs_removed=tuple(sorted(ref for ref in close_receipt_refs_before if ref in stale_refs)),
            )
        )

        if apply_changes:
            write_json(manifest_path, payload)
            assignment_id = worker.get("assignment_id")
            receipt_root = (
                base_root / EXECUTION_HOME_ROOT_REF / str(assignment_id).strip()
                if isinstance(assignment_id, str) and assignment_id.strip()
                else None
            )
            supervisor_root = base_root / SUPERVISOR_ROOT_REF / entry.session_id
            sessions_to_sync.append(
                {
                    "session_id": entry.session_id,
                    "session_root": manifest_path.parent,
                    "receipt_root": receipt_root,
                    "supervisor_root": supervisor_root,
                }
            )

    world_model_summary: dict[str, Any] | None = None
    if apply_changes and sync_outputs and sessions_to_sync:
        world_model_summary = _sync_updated_sessions(sessions=sessions_to_sync, root=base_root)

    return QueueOrRegistryExecutionReceiptWritebackResult(
        mode="apply" if apply_changes else "dry_run",
        sync_outputs=sync_outputs,
        candidate_session_count=len(updated_entries),
        updated_session_count=len(updated_entries),
        world_model=world_model_summary,
        updated_sessions=tuple(updated_entries),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Align session manifests with canonical reconciled execution-home receipts when truthful superseding "
            "receipt lineage is explicit."
        )
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--apply", action="store_true", help="Rewrite session manifests in place.")
    parser.add_argument(
        "--no-sync",
        action="store_true",
        help="Skip descriptor, world-model, and status snapshot refresh after apply.",
    )
    args = parser.parse_args(argv)

    try:
        payload = reconcile_queue_or_registry_execution_receipt_links(
            root=args.root.resolve(),
            apply_changes=args.apply,
            sync_outputs=not args.no_sync,
        ).to_payload()
    except (QueueOrRegistryExecutionReceiptSelectionError, QueueOrRegistryExecutionReceiptWritebackError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
