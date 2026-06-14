from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root

SESSION_CONTRACT_VERSION = "atlas.session.v1"
OPEN_SESSION_STATES = {
    "created",
    "context_built",
    "assignment_emitted",
    "executing",
    "execution_recorded",
    "merge_requested",
    "resume_ready",
    "resume_requested",
    "running",
}
TERMINAL_SESSION_STATES = {"completed", "failed", "resume_failed"}
READ_MODEL_NOTE = (
    "broader queue-state history is grounded in governed runtime/atlas/sessions manifests until live "
    "queue-home or registry-home runtime-state surfaces are materially populated"
)


class QueueOrRegistryHistoryError(RuntimeError):
    pass


def _normalize_text(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise QueueOrRegistryHistoryError(f"{field_name} must be a non-empty string.")
    normalized = value.strip()
    if not normalized:
        raise QueueOrRegistryHistoryError(f"{field_name} must be a non-empty string.")
    return normalized


def _normalize_optional_text(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise QueueOrRegistryHistoryError(f"{field_name} must be a string when present.")
    normalized = value.strip()
    return normalized or None


def _normalize_string_list(value: Any, *, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise QueueOrRegistryHistoryError(f"{field_name} must be a list of strings.")
    values: list[str] = []
    for item in value:
        values.append(_normalize_text(item, field_name=field_name))
    return values


def _parse_iso(value: str | None) -> datetime:
    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise QueueOrRegistryHistoryError(
            f"Malformed JSON session manifest: {atlas_relative(path, root=ROOT)}"
        ) from exc
    if not isinstance(payload, dict):
        raise QueueOrRegistryHistoryError(
            f"Session manifest must be a JSON object: {atlas_relative(path, root=ROOT)}"
        )
    return payload


@dataclass(frozen=True)
class QueueOrRegistryHistoryEntry:
    session_id: str
    task_id: str
    session_ref: str
    scenario: str
    session_state: str
    resume_status: str
    final_status: str | None
    created_at: str | None
    updated_at: str | None
    closed_at: str | None
    status_ref_count: int
    merge_request_ref_count: int
    pause_status_ref_count: int
    resume_context_ref_count: int
    close_receipt_ref_count: int
    has_resume_request_ref: bool
    has_resume_dispatch_ref: bool
    has_resume_run_manifest_ref: bool
    has_resumed_assignment_ref: bool
    has_resumed_running_status_ref: bool
    has_resumed_completed_status_ref: bool

    def to_payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "task_id": self.task_id,
            "session_ref": self.session_ref,
            "scenario": self.scenario,
            "session_state": self.session_state,
            "resume_status": self.resume_status,
            "final_status": self.final_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "closed_at": self.closed_at,
            "status_ref_count": self.status_ref_count,
            "merge_request_ref_count": self.merge_request_ref_count,
            "pause_status_ref_count": self.pause_status_ref_count,
            "resume_context_ref_count": self.resume_context_ref_count,
            "close_receipt_ref_count": self.close_receipt_ref_count,
            "has_resume_request_ref": self.has_resume_request_ref,
            "has_resume_dispatch_ref": self.has_resume_dispatch_ref,
            "has_resume_run_manifest_ref": self.has_resume_run_manifest_ref,
            "has_resumed_assignment_ref": self.has_resumed_assignment_ref,
            "has_resumed_running_status_ref": self.has_resumed_running_status_ref,
            "has_resumed_completed_status_ref": self.has_resumed_completed_status_ref,
        }


@dataclass(frozen=True)
class QueueOrRegistryHistoryResult:
    session_entries: tuple[QueueOrRegistryHistoryEntry, ...]
    session_count: int
    open_session_count: int
    terminal_session_count: int
    state_counts: dict[str, int]
    final_status_counts: dict[str, int]
    scenario_counts: dict[str, int]
    resume_transition_counts: dict[str, int]
    oldest_created_at: str | None
    latest_updated_at: str | None
    read_model_basis: str = "runtime/atlas/sessions"
    read_model_note: str = READ_MODEL_NOTE

    def to_payload(self) -> dict[str, Any]:
        return {
            "session_entries": [item.to_payload() for item in self.session_entries],
            "session_count": self.session_count,
            "open_session_count": self.open_session_count,
            "terminal_session_count": self.terminal_session_count,
            "state_counts": self.state_counts,
            "final_status_counts": self.final_status_counts,
            "scenario_counts": self.scenario_counts,
            "resume_transition_counts": self.resume_transition_counts,
            "oldest_created_at": self.oldest_created_at,
            "latest_updated_at": self.latest_updated_at,
            "read_model_basis": self.read_model_basis,
            "read_model_note": self.read_model_note,
        }


def _build_entry(path: Path, payload: dict[str, Any], *, root: Path) -> QueueOrRegistryHistoryEntry:
    contract_version = _normalize_text(payload.get("contract_version"), field_name="contract_version")
    if contract_version != SESSION_CONTRACT_VERSION:
        raise QueueOrRegistryHistoryError(
            f"Unexpected session manifest contract_version at {atlas_relative(path, root=root)}: {contract_version!r}"
        )

    refs = payload.get("refs")
    if not isinstance(refs, dict):
        raise QueueOrRegistryHistoryError(f"refs must be a JSON object: {atlas_relative(path, root=root)}")
    completion = payload.get("completion")
    if not isinstance(completion, dict):
        raise QueueOrRegistryHistoryError(f"completion must be a JSON object: {atlas_relative(path, root=root)}")
    resume = payload.get("resume")
    if resume is None:
        resume = {}
    if not isinstance(resume, dict):
        raise QueueOrRegistryHistoryError(f"resume must be a JSON object: {atlas_relative(path, root=root)}")

    status_refs = _normalize_string_list(refs.get("status_refs", []), field_name="refs.status_refs")
    merge_request_refs = _normalize_string_list(
        refs.get("merge_request_refs", []),
        field_name="refs.merge_request_refs",
    )
    pause_status_refs = _normalize_string_list(
        refs.get("pause_status_refs", []),
        field_name="refs.pause_status_refs",
    )
    resume_context_refs = _normalize_string_list(
        refs.get("resume_context_refs", []),
        field_name="refs.resume_context_refs",
    )
    close_receipt_refs = _normalize_string_list(
        completion.get("close_receipt_refs", []),
        field_name="completion.close_receipt_refs",
    )

    return QueueOrRegistryHistoryEntry(
        session_id=_normalize_text(payload.get("session_id"), field_name="session_id"),
        task_id=_normalize_text(payload.get("task_id"), field_name="task_id"),
        session_ref=atlas_relative(path, root=root),
        scenario=_normalize_text(payload.get("scenario"), field_name="scenario"),
        session_state=_normalize_text(payload.get("session_state"), field_name="session_state"),
        resume_status=_normalize_optional_text(resume.get("status"), field_name="resume.status") or "not_requested",
        final_status=_normalize_optional_text(completion.get("final_status"), field_name="completion.final_status"),
        created_at=_normalize_optional_text(payload.get("created_at"), field_name="created_at"),
        updated_at=_normalize_optional_text(payload.get("updated_at"), field_name="updated_at"),
        closed_at=_normalize_optional_text(payload.get("closed_at"), field_name="closed_at"),
        status_ref_count=len(status_refs),
        merge_request_ref_count=len(merge_request_refs),
        pause_status_ref_count=len(pause_status_refs),
        resume_context_ref_count=len(resume_context_refs),
        close_receipt_ref_count=len(close_receipt_refs),
        has_resume_request_ref=_normalize_optional_text(
            refs.get("resume_request_ref"),
            field_name="refs.resume_request_ref",
        )
        is not None,
        has_resume_dispatch_ref=_normalize_optional_text(
            refs.get("resume_dispatch_ref"),
            field_name="refs.resume_dispatch_ref",
        )
        is not None,
        has_resume_run_manifest_ref=_normalize_optional_text(
            refs.get("resume_run_manifest_ref"),
            field_name="refs.resume_run_manifest_ref",
        )
        is not None,
        has_resumed_assignment_ref=_normalize_optional_text(
            refs.get("resumed_assignment_ref"),
            field_name="refs.resumed_assignment_ref",
        )
        is not None,
        has_resumed_running_status_ref=_normalize_optional_text(
            refs.get("resumed_running_status_ref"),
            field_name="refs.resumed_running_status_ref",
        )
        is not None,
        has_resumed_completed_status_ref=_normalize_optional_text(
            refs.get("resumed_completed_status_ref"),
            field_name="refs.resumed_completed_status_ref",
        )
        is not None,
    )


def build_queue_or_registry_history(*, root: Path | None = None) -> QueueOrRegistryHistoryResult:
    base_root = (root or atlas_root()).resolve()
    sessions_root = base_root / "runtime" / "atlas" / "sessions"
    if not sessions_root.exists():
        return QueueOrRegistryHistoryResult(
            session_entries=(),
            session_count=0,
            open_session_count=0,
            terminal_session_count=0,
            state_counts={},
            final_status_counts={},
            scenario_counts={},
            resume_transition_counts={
                "resume_ready_sessions": 0,
                "resume_requested_sessions": 0,
                "resume_dispatched_sessions": 0,
                "resumed_completion_sessions": 0,
            },
            oldest_created_at=None,
            latest_updated_at=None,
        )

    entries: list[QueueOrRegistryHistoryEntry] = []
    for path in sorted(sessions_root.rglob("session.manifest.json")):
        entries.append(_build_entry(path, _load_json(path), root=base_root))

    entries.sort(
        key=lambda item: (
            _parse_iso(item.updated_at or item.created_at),
            item.session_id,
        ),
        reverse=True,
    )

    state_counts = Counter(item.session_state for item in entries)
    final_status_counts = Counter(item.final_status for item in entries if item.final_status)
    scenario_counts = Counter(item.scenario for item in entries)
    open_session_count = sum(1 for item in entries if item.session_state in OPEN_SESSION_STATES)
    terminal_session_count = sum(1 for item in entries if item.session_state in TERMINAL_SESSION_STATES)
    oldest_created_at = min((_parse_iso(item.created_at), item.created_at) for item in entries)[1]
    latest_updated_at = max((_parse_iso(item.updated_at or item.created_at), item.updated_at or item.created_at) for item in entries)[1]

    resume_transition_counts = {
        "resume_ready_sessions": sum(
            1
            for item in entries
            if item.session_state == "resume_ready" or item.resume_status == "resume_ready"
        ),
        "resume_requested_sessions": sum(
            1
            for item in entries
            if item.has_resume_request_ref or item.resume_status in {"resume_requested", "running", "completed", "resume_failed"}
        ),
        "resume_dispatched_sessions": sum(
            1
            for item in entries
            if item.has_resume_dispatch_ref or item.resume_status in {"running", "completed", "resume_failed"}
        ),
        "resumed_completion_sessions": sum(
            1
            for item in entries
            if item.has_resumed_completed_status_ref or item.final_status == "completed"
        ),
    }

    return QueueOrRegistryHistoryResult(
        session_entries=tuple(entries),
        session_count=len(entries),
        open_session_count=open_session_count,
        terminal_session_count=terminal_session_count,
        state_counts=dict(sorted(state_counts.items())),
        final_status_counts=dict(sorted(final_status_counts.items())),
        scenario_counts=dict(sorted(scenario_counts.items())),
        resume_transition_counts=resume_transition_counts,
        oldest_created_at=oldest_created_at,
        latest_updated_at=latest_updated_at,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Render the broader queue-or-registry session-history read model from governed runtime/atlas/sessions manifests."
        )
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    args = parser.parse_args(argv)

    try:
        payload = build_queue_or_registry_history(root=args.root.resolve()).to_payload()
    except QueueOrRegistryHistoryError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
