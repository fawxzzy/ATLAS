"""Durable, observe-only liveness checks for the ATLAS Workflow V4 runtime."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Callable

from ops.atlas.atlas_runtime import AtlasRuntime, Task


WATCHDOG_SCHEMA = "atlas.watchdog.receipt.v1"
DEFAULT_FALLBACK_SECONDS = 30 * 60


@dataclass(frozen=True)
class WatchdogDecision:
    task_id: str
    action: str
    reason: str
    receipt_recorded: bool


@dataclass(frozen=True)
class WatchdogTick:
    checked: bool
    paused_runtime_tasks: tuple[str, ...]
    decisions: tuple[WatchdogDecision, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "checked": self.checked,
            "paused_runtime_tasks": list(self.paused_runtime_tasks),
            "decisions": [asdict(item) for item in self.decisions],
        }


class AtlasWatchdog:
    """Reconciles durable liveness truth without starting workers or chats."""

    def __init__(
        self,
        runtime: AtlasRuntime,
        *,
        clock: Callable[[], float] = time.time,
        name: str = "atlas.workflow.v4.watchdog",
        fallback_seconds: float = DEFAULT_FALLBACK_SECONDS,
    ) -> None:
        self.runtime = runtime
        self.clock = clock
        self.name = name
        self.fallback_seconds = fallback_seconds

    def tick(self, *, event_observed: bool = False) -> WatchdogTick:
        now = self.clock()
        if not self.runtime.reserve_watchdog_tick(
            name=self.name,
            now=now,
            fallback_seconds=self.fallback_seconds,
            event_observed=event_observed,
        ):
            return WatchdogTick(False, (), ())

        paused = tuple(self.runtime.reconcile(now=now))
        decisions = tuple(
            self._record_decision(task, has_valid_lease, now)
            for task, has_valid_lease in self.runtime.watchdog_tasks(now=now)
        )
        return WatchdogTick(True, paused, decisions)

    def _record_decision(self, task: Task, has_valid_lease: bool, now: float) -> WatchdogDecision:
        action, reason = self._classify(task, has_valid_lease)
        payload = {
            "schema": WATCHDOG_SCHEMA,
            "watchdog": self.name,
            "action": action,
            "reason": reason,
            "state": task.state,
            "scope": task.scope,
            "cooldown_window": int(now // self.fallback_seconds),
            "execution": "NOT_STARTED",
        }
        recorded = self.runtime.record_watchdog_receipt(task_id=task.task_id, payload=payload, now=now)
        return WatchdogDecision(task.task_id, action, reason, recorded)

    @staticmethod
    def _classify(task: Task, has_valid_lease: bool) -> tuple[str, str]:
        if has_valid_lease:
            return "HOLD", "VALID_ACTIVE_LEASE"
        if task.state == "QUEUED":
            if task.scope.startswith(("provider:", "production:")):
                return "HOLD", "PROVIDER_OR_PRODUCTION_GATE"
            return "WAKE_NEEDED", "STRANDED_READY_NO_VALID_LEASE"
        if task.state == "BLOCKED_DEPENDENCY":
            return "HOLD", "UNRESOLVED_DEPENDENCY"
        if task.state == "WAITING_MANUAL":
            return "HOLD", "MANUAL_DECISION_REQUIRED"
        if task.state == "WAITING_EXTERNAL":
            return "HOLD", "EXTERNAL_GATE"
        if task.state == "PAUSED_RUNTIME":
            return "HOLD", "PAUSED_RUNTIME_REQUIRES_RESUME"
        return "HOLD", "UNKNOWN_STATE"
