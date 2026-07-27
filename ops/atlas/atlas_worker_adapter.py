"""Adapter-neutral worker/run contracts for the ATLAS Workflow V4 runtime.

This module deliberately does *not* start Codex, write to the V4 database, or
call an external service.  It supplies the durable identity and receipt shape a
future executor must prove before the runtime core is allowed to treat a task
as actively worked.
"""

from __future__ import annotations

import json
import os
import shlex
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence


RECEIPT_SCHEMA = "atlas.worker.receipt.v1"


class ReceiptValidationError(ValueError):
    """A worker receipt is incomplete, malformed, or identity-inconsistent."""


@dataclass(frozen=True)
class ModelProfile:
    """Requested and actually-effective model/effort, both always receipted."""

    requested_model: str
    requested_reasoning_effort: str
    effective_model: str
    effective_reasoning_effort: str

    def __post_init__(self) -> None:
        for label, value in asdict(self).items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{label} must be a non-empty string")


@dataclass(frozen=True)
class WorkerRun:
    """Non-secret identity for one future worker process and one claimed run."""

    worker_id: str
    run_id: str
    process_id: int
    task_id: str
    profile: ModelProfile
    started_at: float

    def __post_init__(self) -> None:
        for label in ("worker_id", "run_id", "task_id"):
            if not getattr(self, label):
                raise ValueError(f"{label} must be non-empty")
        if not isinstance(self.process_id, int) or self.process_id <= 0:
            raise ValueError("process_id must be a positive integer")
        if self.started_at <= 0:
            raise ValueError("started_at must be positive")


@dataclass(frozen=True)
class WorkerHeartbeat:
    """Identity-bound heartbeat payload a runtime can persist independently."""

    worker_id: str
    run_id: str
    process_id: int
    task_id: str
    observed_at: float


def new_worker_run(
    *,
    task_id: str,
    profile: ModelProfile,
    worker_id: str | None = None,
    run_id: str | None = None,
    process_id: int | None = None,
    started_at: float | None = None,
) -> WorkerRun:
    """Construct identity only; this function neither claims nor starts work."""
    return WorkerRun(
        worker_id=worker_id or f"worker:{uuid.uuid4()}",
        run_id=run_id or f"run:{uuid.uuid4()}",
        process_id=os.getpid() if process_id is None else process_id,
        task_id=task_id,
        profile=profile,
        started_at=time.time() if started_at is None else started_at,
    )


def heartbeat_for(run: WorkerRun, *, observed_at: float | None = None) -> WorkerHeartbeat:
    """Build a heartbeat. It is intentionally not sent or persisted here."""
    return WorkerHeartbeat(
        worker_id=run.worker_id,
        run_id=run.run_id,
        process_id=run.process_id,
        task_id=run.task_id,
        observed_at=time.time() if observed_at is None else observed_at,
    )


def receipt_for(
    run: WorkerRun,
    *,
    state: str,
    evidence: Mapping[str, Any],
    emitted_at: float | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    """Build a structured receipt that can be validated before runtime intake."""
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "event_id": event_id or f"receipt:{run.run_id}",
        "task_id": run.task_id,
        "state": state,
        "worker": {
            "worker_id": run.worker_id,
            "run_id": run.run_id,
            "process_id": run.process_id,
            "requested_model": run.profile.requested_model,
            "requested_reasoning_effort": run.profile.requested_reasoning_effort,
            "effective_model": run.profile.effective_model,
            "effective_reasoning_effort": run.profile.effective_reasoning_effort,
        },
        "evidence": dict(evidence),
        "emitted_at": time.time() if emitted_at is None else emitted_at,
    }
    validate_receipt(receipt, run=run)
    return receipt


def validate_receipt(receipt: Mapping[str, Any], *, run: WorkerRun | None = None) -> None:
    """Fail closed on missing fields or an identity/profile mismatch."""
    required = ("schema", "event_id", "task_id", "state", "worker", "evidence", "emitted_at")
    missing = [field for field in required if field not in receipt]
    if missing:
        raise ReceiptValidationError(f"missing receipt fields: {', '.join(missing)}")
    if receipt["schema"] != RECEIPT_SCHEMA:
        raise ReceiptValidationError("unsupported receipt schema")
    if not isinstance(receipt["event_id"], str) or not receipt["event_id"]:
        raise ReceiptValidationError("event_id must be a non-empty string")
    if not isinstance(receipt["task_id"], str) or not receipt["task_id"]:
        raise ReceiptValidationError("task_id must be a non-empty string")
    if not isinstance(receipt["state"], str) or not receipt["state"]:
        raise ReceiptValidationError("state must be a non-empty string")
    if not isinstance(receipt["evidence"], Mapping):
        raise ReceiptValidationError("evidence must be an object")
    if not isinstance(receipt["emitted_at"], (int, float)) or receipt["emitted_at"] <= 0:
        raise ReceiptValidationError("emitted_at must be positive")
    worker = receipt["worker"]
    if not isinstance(worker, Mapping):
        raise ReceiptValidationError("worker must be an object")
    needed_worker = (
        "worker_id", "run_id", "process_id", "requested_model", "requested_reasoning_effort",
        "effective_model", "effective_reasoning_effort",
    )
    missing_worker = [field for field in needed_worker if field not in worker]
    if missing_worker:
        raise ReceiptValidationError(f"missing worker fields: {', '.join(missing_worker)}")
    if not isinstance(worker["process_id"], int) or worker["process_id"] <= 0:
        raise ReceiptValidationError("worker.process_id must be a positive integer")
    if any(not isinstance(worker[field], str) or not worker[field] for field in needed_worker if field != "process_id"):
        raise ReceiptValidationError("worker identity and model fields must be non-empty strings")
    if run is not None:
        expected = {
            "task_id": run.task_id,
            "worker_id": run.worker_id,
            "run_id": run.run_id,
            "process_id": run.process_id,
            "requested_model": run.profile.requested_model,
            "requested_reasoning_effort": run.profile.requested_reasoning_effort,
            "effective_model": run.profile.effective_model,
            "effective_reasoning_effort": run.profile.effective_reasoning_effort,
        }
        actual = {"task_id": receipt["task_id"], **{key: worker[key] for key in expected if key != "task_id"}}
        mismatched = [key for key, value in expected.items() if actual[key] != value]
        if mismatched:
            raise ReceiptValidationError(f"receipt does not match worker run: {', '.join(mismatched)}")


class DryRunCodexAdapter:
    """Renders a future Codex CLI invocation without executing anything."""

    @staticmethod
    def build_command(*, prompt_path: str, profile: ModelProfile) -> tuple[str, ...]:
        if not prompt_path:
            raise ValueError("prompt_path must be non-empty")
        return (
            "codex", "exec", "--model", profile.effective_model,
            "--config", f'model_reasoning_effort="{profile.effective_reasoning_effort}"',
            "--", "@" + prompt_path,
        )

    @classmethod
    def render_plan(cls, *, prompt_path: str, profile: ModelProfile) -> dict[str, Any]:
        """Return JSON-safe dry-run metadata; no subprocess is spawned."""
        command: Sequence[str] = cls.build_command(prompt_path=prompt_path, profile=profile)
        return {
            "adapter": "atlas.codex.dry-run.v1",
            "execution": "NOT_STARTED",
            "command": list(command),
            "display": shlex.join(command),
            "requested_model": profile.requested_model,
            "requested_reasoning_effort": profile.requested_reasoning_effort,
            "effective_model": profile.effective_model,
            "effective_reasoning_effort": profile.effective_reasoning_effort,
        }


def render_receipt_json(receipt: Mapping[str, Any]) -> str:
    """Canonicalize an already-validated receipt for deterministic handoff."""
    validate_receipt(receipt)
    return json.dumps(receipt, sort_keys=True, separators=(",", ":"))
