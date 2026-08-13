"""ATLAS Workflow V4 local control-plane entrypoint.

The daemon deliberately owns only durable reconciliation in this wave.  Worker
launch is injected through a later adapter, so invoking this command cannot
start a chat, change a repository, or call a provider.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Mapping, Protocol

# Direct script execution (the documented operator command) does not place the
# repository root on sys.path. Keep module imports working in both modes.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ops.atlas.atlas_runtime import AtlasRuntime
from ops.atlas.atlas_watchdog import AtlasWatchdog, DEFAULT_FALLBACK_SECONDS


def _positive_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be finite and positive")
    return parsed


def _health(runtime: AtlasRuntime) -> dict[str, object]:
    rows = runtime.db.execute("SELECT state, COUNT(*) AS n FROM tasks GROUP BY state").fetchall()
    states = {row["state"]: row["n"] for row in rows}
    lease_count = runtime.db.execute(
        "SELECT COUNT(*) AS n FROM leases WHERE expires_at>?", (time.time(),)
    ).fetchone()["n"]
    return {
        "schema": "atlasd.health.v1",
        "generated_at": time.time(),
        "tasks_by_state": states,
        "running_worker_count": lease_count,
        "stranded_ready_count": states.get("QUEUED", 0),
        "legacy_scheduler_authoritative": True,
        "worker_launch_enabled": False,
    }


@dataclasses.dataclass(frozen=True)
class TriggerReadback:
    """Closed structural correlation returned by a persistent-thread adapter."""

    thread_id: str
    turn_id: str
    status: str


class TriggerAdapter(Protocol):
    def start_existing_turn(
        self, *, thread_id: str, trigger_key: str, continuation_input: str
    ) -> TriggerReadback: ...


def _closed_trigger_readback(value: object, *, expected_thread_id: str) -> TriggerReadback:
    """Validate hostile adapter output without retaining prompt/model content."""
    if not isinstance(value, Mapping):
        raise ValueError("trigger adapter readback must be an object")
    try:
        thread_id = value["thread_id"]
        turn_id = value["turn_id"]
        status = value["status"]
    except Exception as exc:
        raise ValueError("trigger adapter readback fields are unavailable") from None
    if not all(isinstance(item, str) and item.strip() for item in (thread_id, turn_id, status)):
        raise ValueError("trigger adapter readback fields must be non-empty strings")
    if len(thread_id) > 256 or len(turn_id) > 256 or len(status) > 32:
        raise ValueError("trigger adapter readback exceeds structural limits")
    if thread_id != expected_thread_id:
        raise ValueError("trigger adapter returned the wrong thread")
    if status not in {"accepted", "completed", "in_progress"}:
        raise ValueError("trigger adapter returned an unsupported status")
    return TriggerReadback(thread_id=thread_id, turn_id=turn_id, status=status)


class CodexPersistentThreadAdapter:
    """Start one turn on an existing ATLAS-owned Codex thread.

    The adapter deliberately has no thread-creation method. The command runner
    is injectable so source tests never invoke Codex or the Desktop app.
    """

    def __init__(
        self,
        *,
        executable: str = "codex",
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self.executable = executable
        self.runner = runner

    def start_existing_turn(
        self, *, thread_id: str, trigger_key: str, continuation_input: str
    ) -> TriggerReadback:
        if not thread_id.strip() or not trigger_key.strip() or not continuation_input.strip():
            raise ValueError("existing thread, trigger key, and continuation input are required")
        command = [
            self.executable, "exec", "resume", thread_id,
            f"ATLAS_TRIGGER={trigger_key}\n{continuation_input}",
            "--json",
        ]
        result = self.runner(
            command, check=False, capture_output=True, text=True, encoding="utf-8"
        )
        if result.returncode != 0:
            raise RuntimeError("existing-thread trigger command failed")
        if len(result.stdout.encode("utf-8")) > 65_536:
            raise ValueError("existing-thread trigger readback exceeds 65536 bytes")
        candidates: list[dict[str, object]] = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
            except (TypeError, json.JSONDecodeError):
                raise ValueError("existing-thread trigger returned malformed lifecycle records")
            if not isinstance(parsed, dict):
                raise ValueError("existing-thread trigger returned malformed lifecycle records")
            candidates.append(parsed)
            if len(candidates) > 64:
                raise ValueError("existing-thread trigger returned too many records")

        thread_started: list[tuple[int, str]] = []
        turn_started: list[tuple[int, str]] = []
        for index, item in enumerate(candidates):
            event_type = item.get("type")
            has_thread_id = "thread_id" in item
            has_turn_id = "turn_id" in item
            if event_type == "thread.started":
                candidate_thread = item.get("thread_id")
                if (
                    not isinstance(candidate_thread, str)
                    or not candidate_thread.strip()
                    or has_turn_id
                ):
                    raise ValueError("existing-thread trigger returned malformed lifecycle records")
                thread_started.append((index, candidate_thread))
            elif event_type == "turn.started":
                candidate_turn = item.get("turn_id")
                if (
                    not isinstance(candidate_turn, str)
                    or not candidate_turn.strip()
                    or has_thread_id
                ):
                    raise ValueError("existing-thread trigger returned malformed lifecycle records")
                turn_started.append((index, candidate_turn))
            elif has_thread_id or has_turn_id:
                raise ValueError("existing-thread trigger returned wrong lifecycle record types")

        if (
            len(thread_started) != 1
            or len(turn_started) != 1
            or thread_started[0][0] >= turn_started[0][0]
            or thread_started[0][1] != thread_id
        ):
            raise ValueError("existing-thread trigger requires one correlated readback")
        normalized = {
            "thread_id": thread_id,
            "turn_id": turn_started[0][1],
            "status": "accepted",
        }
        return _closed_trigger_readback(normalized, expected_thread_id=thread_id)


class FixtureTriggerAdapter:
    """Deterministic local adapter for same-session and restart proofs."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def start_existing_turn(
        self, *, thread_id: str, trigger_key: str, continuation_input: str
    ) -> TriggerReadback:
        self.calls.append((thread_id, trigger_key))
        turn_id = "turn_" + trigger_key.removeprefix("trg_")[:24]
        return TriggerReadback(thread_id=thread_id, turn_id=turn_id, status="accepted")


class ContinuationDispatcher:
    """One-shot outbox dispatcher. It has no loop, timer, or task creation seam."""

    def __init__(self, runtime: AtlasRuntime, adapter: TriggerAdapter) -> None:
        self.runtime = runtime
        self.adapter = adapter

    def dispatch_one(self, *, worker_id: str) -> dict[str, str] | None:
        item = self.runtime.lease_continuation_trigger(worker_id=worker_id)
        if item is None:
            return None
        context = self.runtime.continuation_context(item.context_pack_id)
        continuation_input = json.dumps(
            {
                "schema": "atlas.continuation-input.v1",
                "packet_id": item.packet_id,
                "context_pack_id": item.context_pack_id,
                "references": context,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        try:
            self.runtime.record_continuation_process_event(
                event_id=f"process:{item.trigger_key}:starting",
                owner_id=item.owner_id,
                packet_id=item.packet_id,
                process_state="STARTING",
            )
            # Persist the ambiguous external-effect boundary before the call.
            # Once this succeeds, no exception may make the trigger retryable.
            self.runtime.mark_continuation_trigger_dispatched(
                trigger_key=item.trigger_key, worker_id=worker_id
            )
            readback = self.adapter.start_existing_turn(
                thread_id=item.thread_id,
                trigger_key=item.trigger_key,
                continuation_input=continuation_input,
            )
            self.runtime.confirm_continuation_trigger(
                trigger_key=item.trigger_key,
                thread_id=readback.thread_id,
                turn_id=readback.turn_id,
            )
            self.runtime.record_continuation_process_event(
                event_id=f"process:{item.trigger_key}:exited",
                owner_id=item.owner_id,
                packet_id=item.packet_id,
                process_state="EXITED",
            )
            return dataclasses.asdict(readback) | {
                "trigger_key": item.trigger_key,
                "packet_id": item.packet_id,
            }
        except Exception:
            # The adapter may have accepted the turn before readback failed.
            # Leave the row sent-unconfirmed; startup reconciliation confirms
            # exact readback or dead-letters the ambiguity. Never infer capacity.
            row = self.runtime.db.execute(
                "SELECT state FROM continuation_outbox WHERE trigger_key=?", (item.trigger_key,)
            ).fetchone()
            if row and row["state"] == "DISPATCHED":
                self.runtime.mark_continuation_trigger_uncertain(trigger_key=item.trigger_key)
            self.runtime.record_continuation_process_event(
                event_id=f"process:{item.trigger_key}:failed",
                owner_id=item.owner_id,
                packet_id=item.packet_id,
                process_state="FAILED",
            )
            raise


class SingleInstanceGuard:
    """OS file lock for one event-driven continuation worker instance."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.handle = None

    def __enter__(self) -> "SingleInstanceGuard":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a+b")
        self.handle.seek(0)
        self.handle.write(b"0")
        self.handle.flush()
        try:
            if os.name == "nt":
                import msvcrt
                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.handle.close()
            self.handle = None
            raise RuntimeError("continuation worker instance is already active") from None
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.handle is None:
            return
        try:
            if os.name == "nt":
                import msvcrt
                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        finally:
            self.handle.close()
            self.handle = None


class EventDrivenContinuationWorker:
    """Handle one explicit ingress or one-shot timer event; never polls."""

    def __init__(
        self, runtime: AtlasRuntime, adapter: TriggerAdapter, *, guard_path: str | Path
    ) -> None:
        self.runtime = runtime
        self.adapter = adapter
        self.guard_path = Path(guard_path)

    def handle_event(self, *, event_id: str, worker_id: str) -> dict[str, object]:
        with SingleInstanceGuard(self.guard_path):
            # Ingress alone is not authoritative evidence that an active owner
            # has become idle. A caller with a complete turn inventory may run
            # reconciliation explicitly with observed_turns; this event seam
            # deliberately performs recovery without inventing liveness.
            recovery = self.runtime.reconcile_continuation_startup()
            dispatch = ContinuationDispatcher(self.runtime, self.adapter).dispatch_one(
                worker_id=worker_id
            )
            if dispatch:
                self.runtime.record_continuation_process_event(
                    event_id=f"{event_id}:accepted",
                    owner_id=self.runtime.db.execute(
                        "SELECT owner_id FROM continuation_outbox WHERE trigger_key=?",
                        (dispatch["trigger_key"],),
                    ).fetchone()["owner_id"],
                    packet_id=dispatch["packet_id"],
                    process_state="STARTED",
                    process_id=None,
                )
            return {"event_id": event_id, "recovery": recovery, "dispatch": dispatch}

    def one_shot(self, *, delay_seconds: float, event_id: str, worker_id: str) -> threading.Timer:
        if not math.isfinite(delay_seconds) or delay_seconds < 0:
            raise ValueError("one-shot delay must be finite and non-negative")
        timer = threading.Timer(
            delay_seconds,
            lambda: self.handle_event(event_id=event_id, worker_id=worker_id),
        )
        timer.daemon = True
        timer.start()
        return timer


def _fixture_demo(runtime: AtlasRuntime, *, restart: bool = False) -> dict[str, object]:
    if runtime.db.execute("SELECT COUNT(*) FROM continuation_owners").fetchone()[0]:
        raise ValueError("fixture demo requires an empty continuation database")
    runtime.register_continuation_owner(owner_id="fixture.owner", thread_id="fixture-thread")
    first = runtime.create_context_pack({"summary": "fixture A", "source_refs": ["fixture:A"]})
    second = runtime.create_context_pack({"summary": "fixture B", "source_refs": ["fixture:B"]})
    runtime.register_continuation_packet(
        packet_id="fixture-A", owner_id="fixture.owner", conflict_key="fixture:A",
        context_pack_id=first,
    )
    runtime.register_continuation_packet(
        packet_id="fixture-B", owner_id="fixture.owner", conflict_key="fixture:B",
        context_pack_id=second, after_packet_id="fixture-A",
    )
    runtime.activate_continuation_packet(packet_id="fixture-A")
    committed = runtime.commit_continuation(
        packet_id="fixture-A",
        terminal_receipt={"event_id": "fixture-terminal-A", "result": "SEALED"},
        expected_owner_revision=1,
    )
    decision = {} if restart else runtime.stop_hook_decision(
        owner_id="fixture.owner", thread_id="fixture-thread"
    )
    recovery: tuple[dict[str, str], ...] = ()
    active_runtime = runtime
    if restart:
        lease = runtime.lease_continuation_trigger(worker_id="fixture-crash", lease_seconds=0.001)
        database = runtime.database
        runtime.close()
        active_runtime = AtlasRuntime(database)
        recovery = active_runtime.reconcile_continuation_startup(now=lease.leased_until + 1)
    adapter = FixtureTriggerAdapter()
    try:
        dispatch = ContinuationDispatcher(active_runtime, adapter).dispatch_one(worker_id="fixture-worker")
    finally:
        if active_runtime is not runtime:
            active_runtime.close()
    return {
        "schema": "atlas.durable-continuation-kernel.fixture-demo.v1",
        "mode": "restart" if restart else "same_session",
        "terminal_packet": committed.packet_id,
        "successor_packet": committed.successor_packet_id,
        "trigger_key": committed.trigger_key,
        "stop_hook_decision": decision,
        "recovery": recovery,
        "dispatch": dispatch,
        "provider_actions": 0,
        "new_threads": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ATLAS Workflow V4 runtime control plane")
    parser.add_argument("--database", required=True, help="local SQLite database path")
    parser.add_argument(
        "command",
        choices=(
            "init", "health", "reconcile", "watchdog",
            "continuation-status", "continuation-reconcile", "continuation-dispatch",
            "continuation-demo", "continuation-restart-demo",
        ),
    )
    parser.add_argument(
        "--heartbeat-timeout",
        type=_positive_float,
        default=120,
        help="seconds before a missing worker heartbeat is stale",
    )
    parser.add_argument("--event", action="store_true", help="record an observed local runtime event")
    parser.add_argument(
        "--fallback-seconds",
        type=_positive_float,
        default=DEFAULT_FALLBACK_SECONDS,
        help="seconds between successful fallback watchdog checks",
    )
    args = parser.parse_args(argv)
    runtime = AtlasRuntime(Path(args.database))
    try:
        if args.command == "reconcile":
            paused = runtime.reconcile(heartbeat_timeout=args.heartbeat_timeout)
            output = _health(runtime) | {
                "paused_runtime_tasks": paused,
                "recovery_dispositions": [item.__dict__ for item in runtime.recovery_dispositions()],
            }
        elif args.command == "watchdog":
            tick = AtlasWatchdog(
                runtime,
                fallback_seconds=args.fallback_seconds,
                heartbeat_timeout=args.heartbeat_timeout,
            ).tick(event_observed=args.event)
            output = _health(runtime) | {"watchdog": tick.as_dict()}
        elif args.command == "continuation-status":
            output = _health(runtime) | {"continuation": runtime.continuation_status()}
        elif args.command == "continuation-reconcile":
            output = _health(runtime) | {
                "continuation": runtime.continuation_status(),
                "reconciliation": runtime.reconcile_continuation_startup(),
            }
        elif args.command == "continuation-dispatch":
            dispatch = ContinuationDispatcher(runtime, CodexPersistentThreadAdapter()).dispatch_one(
                worker_id="atlasd-one-shot"
            )
            output = _health(runtime) | {
                "continuation": runtime.continuation_status(),
                "dispatch": dispatch,
            }
        elif args.command == "continuation-demo":
            output = _health(runtime) | {"demo": _fixture_demo(runtime)}
        elif args.command == "continuation-restart-demo":
            output = _health(runtime) | {"demo": _fixture_demo(runtime, restart=True)}
        else:
            output = _health(runtime)
        print(json.dumps(output, sort_keys=True))
        return 0
    finally:
        runtime.close()


if __name__ == "__main__":
    raise SystemExit(main())
