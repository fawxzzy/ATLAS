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
import queue
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

from ops.atlas.atlas_runtime import AtlasRuntime, validate_continuation_turn_id
from ops.atlas.atlas_watchdog import AtlasWatchdog, DEFAULT_FALLBACK_SECONDS
from ops.atlas.persist_thread_context import (
    ThreadContextError,
    _digest as _thread_context_digest,
    _exclusive_file_lock as _exclusive_thread_context_lock,
    _load_index as _load_thread_context_index,
    _safe_path_component as _safe_thread_context_path_component,
    _validate_checkpoint_shape,
)


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
    visible_item_count: int = 0


class TriggerReadbackFailure(ValueError):
    """A closed host-readback failure safe to persist without payload echo."""

    def __init__(self, failure_code: str, message: str) -> None:
        super().__init__(message)
        self.failure_code = (
            failure_code
            if failure_code
            in {
                "APP_READBACK_NO_TURN",
                "APP_READBACK_NO_OUTPUT",
                "APP_READBACK_NO_CHECKPOINT",
                "APP_READBACK_FAILED",
            }
            else "APP_READBACK_FAILED"
        )


class FilesystemCheckpointProbe:
    """Read one validated compact owner checkpoint identity, never its content."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def __call__(self, thread_id: str) -> str | None:
        if (
            not thread_id
            or len(thread_id) > 128
            or thread_id in {".", ".."}
            or "/" in thread_id
            or "\\" in thread_id
            or "\0" in thread_id
        ):
            return None
        try:
            _safe_thread_context_path_component(thread_id, "thread_id")
            path = (self.root / thread_id / "latest.json").resolve()
            path.relative_to(self.root)
            lock_path = (self.root / ".thread-context.lock").resolve()
            lock_path.relative_to(self.root)
            with _exclusive_thread_context_lock(lock_path):
                raw = path.read_bytes()
                if len(raw) > 262_144:
                    return None
                checkpoint = json.loads(raw)
                payload = _validate_checkpoint_shape(checkpoint)
                if payload["thread_id"] != thread_id:
                    return None
                digest = _thread_context_digest(payload)
                checkpoint_id = checkpoint.get("checkpoint_id")
                if (
                    checkpoint.get("payload_digest") != digest
                    or checkpoint_id != "threadctx_" + digest.removeprefix("sha256:")
                ):
                    return None
                immutable_path = (path.parent / f"{checkpoint_id}.json").resolve()
                immutable_path.relative_to(self.root)
                immutable = json.loads(immutable_path.read_bytes())
                if immutable != checkpoint:
                    return None
                index = _load_thread_context_index(self.root / "index.json")
        except (OSError, ValueError, json.JSONDecodeError, ThreadContextError):
            return None
        if set(index) != {"schema", "threads", "index_digest"}:
            return None
        expected_index_digest = _thread_context_digest(
            {"schema": index["schema"], "threads": index["threads"]}
        )
        if index.get("index_digest") != expected_index_digest:
            return None
        records = [
            record
            for record in index["threads"]
            if isinstance(record, dict) and record.get("thread_id") == thread_id
        ]
        expected_record = {
            "thread_id": thread_id,
            "logical_role_id": payload["logical_role_id"],
            "visible_title": payload["visible_title"],
            "state": payload["state"],
            "recorded_at": payload["recorded_at"],
            "checkpoint_id": checkpoint_id,
            "payload_digest": digest,
            "latest_ref": f"runtime/atlas/thread-context/{thread_id}/latest.json",
        }
        if records != [expected_record]:
            return None
        return checkpoint_id


class TriggerAdapter(Protocol):
    def start_existing_turn(
        self,
        *,
        thread_id: str,
        trigger_key: str,
        continuation_input: str,
        acknowledge: Callable[[str, str], None] | None = None,
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
    if not all(isinstance(item, str) and item.strip() for item in (thread_id, status)):
        raise ValueError("trigger adapter readback fields must be non-empty strings")
    try:
        turn_id = validate_continuation_turn_id(turn_id)
    except ValueError:
        raise ValueError("trigger adapter readback exceeds structural limits") from None
    if len(thread_id) > 256 or len(status) > 32:
        raise ValueError("trigger adapter readback exceeds structural limits")
    if thread_id != expected_thread_id:
        raise ValueError("trigger adapter returned the wrong thread")
    if status not in {"accepted", "completed", "in_progress"}:
        raise ValueError("trigger adapter returned an unsupported status")
    visible_item_count = value.get("visible_item_count", 0)
    if (
        isinstance(visible_item_count, bool)
        or not isinstance(visible_item_count, int)
        or visible_item_count < 0
    ):
        raise ValueError("trigger adapter visible item count is invalid")
    return TriggerReadback(
        thread_id=thread_id,
        turn_id=turn_id,
        status=status,
        visible_item_count=visible_item_count,
    )


class CodexPersistentThreadAdapter:
    """Start one turn on an existing ATLAS-owned Codex thread.

    The adapter deliberately has no thread-creation method. The command runner
    is injectable so source tests never invoke Codex or the Desktop app.
    """

    def __init__(
        self,
        *,
        executable: str = "codex",
        runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
        popen_factory: Callable[..., subprocess.Popen[str]] = subprocess.Popen,
        acknowledgement_timeout_seconds: float = 30,
        execution_timeout_seconds: float = 1800,
    ) -> None:
        for label, value, maximum in (
            ("acknowledgement", acknowledgement_timeout_seconds, 300),
            ("execution", execution_timeout_seconds, 7200),
        ):
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
                or value <= 0
                or value > maximum
            ):
                raise ValueError(
                    f"{label} timeout must be finite and between 0 and {maximum} seconds"
                )
        self.executable = executable
        self.runner = runner
        self.popen_factory = popen_factory
        self.acknowledgement_timeout_seconds = float(acknowledgement_timeout_seconds)
        self.execution_timeout_seconds = float(execution_timeout_seconds)

    @staticmethod
    def _stop_process(process: subprocess.Popen[str]) -> None:
        try:
            process.terminate()
            process.wait(timeout=2)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

    def _run_streaming(
        self,
        command: list[str],
        *,
        expected_thread_id: str,
        acknowledge: Callable[[str, str], None] | None,
    ) -> tuple[subprocess.CompletedProcess[str], bool]:
        process = self.popen_factory(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=False,
            bufsize=0,
        )
        if process.stdout is None:
            self._stop_process(process)
            raise TriggerReadbackFailure(
                "APP_READBACK_FAILED", "existing-thread trigger has no lifecycle stream"
            )
        lines: queue.Queue[bytes | None] = queue.Queue(maxsize=1)
        stream_errors: list[TriggerReadbackFailure] = []
        cancelled = threading.Event()

        def bounded_put(value: bytes | None) -> bool:
            while not cancelled.is_set():
                try:
                    lines.put(value, timeout=0.1)
                    return True
                except queue.Full:
                    continue
            return False

        def read_lines() -> None:
            try:
                byte_count = 0
                record_count = 0
                while True:
                    remaining = 65_536 - byte_count
                    line = process.stdout.readline(remaining + 1)
                    if not line:
                        break
                    if isinstance(line, str):
                        line = line.encode("utf-8")
                    if len(line) > remaining:
                        stream_errors.append(
                            TriggerReadbackFailure(
                                "APP_READBACK_FAILED",
                                "existing-thread trigger readback is oversized",
                            )
                        )
                        break
                    byte_count += len(line)
                    record_count += 1
                    if record_count > 64:
                        stream_errors.append(
                            TriggerReadbackFailure(
                                "APP_READBACK_FAILED",
                                "existing-thread trigger returned too many records",
                            )
                        )
                        break
                    if not bounded_put(line):
                        return
            except Exception:
                stream_errors.append(
                    TriggerReadbackFailure(
                        "APP_READBACK_FAILED",
                        "existing-thread trigger lifecycle stream failed",
                    )
                )
            finally:
                bounded_put(None)

        reader = threading.Thread(
            target=read_lines,
            daemon=True,
            name="atlas-continuation-readback",
        )
        reader.start()
        acknowledgement_deadline = time.monotonic() + self.acknowledgement_timeout_seconds
        execution_deadline: float | None = None
        acknowledged = False
        seen_thread: str | None = None
        seen_turn: str | None = None
        buffered: list[str] = []
        try:
            while True:
                deadline = execution_deadline or acknowledgement_deadline
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TriggerReadbackFailure(
                        "APP_READBACK_FAILED",
                        "existing-thread trigger lifecycle deadline expired",
                    )
                try:
                    line = lines.get(timeout=remaining)
                except queue.Empty:
                    raise TriggerReadbackFailure(
                        "APP_READBACK_FAILED",
                        "existing-thread trigger lifecycle deadline expired",
                    ) from None
                if line is None:
                    if stream_errors:
                        raise stream_errors[0]
                    break
                try:
                    decoded = line.decode("utf-8")
                except UnicodeDecodeError:
                    raise TriggerReadbackFailure(
                        "APP_READBACK_FAILED", "existing-thread trigger lifecycle is malformed"
                    ) from None
                buffered.append(decoded)
                try:
                    event = json.loads(decoded)
                except (TypeError, json.JSONDecodeError):
                    raise TriggerReadbackFailure(
                        "APP_READBACK_FAILED", "existing-thread trigger lifecycle is malformed"
                    ) from None
                if not isinstance(event, dict):
                    raise TriggerReadbackFailure(
                        "APP_READBACK_FAILED", "existing-thread trigger lifecycle is malformed"
                    )
                if event.get("type") == "thread.started":
                    candidate = event.get("thread_id")
                    if seen_thread is not None or candidate != expected_thread_id:
                        raise TriggerReadbackFailure(
                            "APP_READBACK_FAILED", "existing-thread trigger identity is ambiguous"
                        )
                    seen_thread = candidate
                elif event.get("type") == "turn.started":
                    candidate = event.get("turn_id")
                    try:
                        candidate = validate_continuation_turn_id(candidate)
                    except ValueError:
                        raise TriggerReadbackFailure(
                            "APP_READBACK_FAILED", "existing-thread trigger identity is ambiguous"
                        ) from None
                    if seen_thread != expected_thread_id or seen_turn is not None:
                        raise TriggerReadbackFailure(
                            "APP_READBACK_FAILED", "existing-thread trigger identity is ambiguous"
                        )
                    seen_turn = candidate
                    if acknowledge is not None:
                        acknowledge(expected_thread_id, candidate)
                    acknowledged = True
                    execution_deadline = time.monotonic() + self.execution_timeout_seconds
            try:
                return_code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                raise TriggerReadbackFailure(
                    "APP_READBACK_FAILED", "existing-thread trigger did not close its stream"
                ) from None
            reader.join(timeout=2)
            if reader.is_alive():
                raise TriggerReadbackFailure(
                    "APP_READBACK_FAILED", "existing-thread trigger stream did not terminate"
                )
            return (
                subprocess.CompletedProcess(
                    args=command,
                    returncode=return_code,
                    stdout="".join(buffered),
                    stderr="",
                ),
                acknowledged,
            )
        except Exception:
            cancelled.set()
            self._stop_process(process)
            try:
                process.stdout.close()
            except Exception:
                pass
            while True:
                try:
                    lines.get_nowait()
                except queue.Empty:
                    break
            reader.join(timeout=2)
            raise

    def start_existing_turn(
        self,
        *,
        thread_id: str,
        trigger_key: str,
        continuation_input: str,
        acknowledge: Callable[[str, str], None] | None = None,
    ) -> TriggerReadback:
        if not thread_id.strip() or not trigger_key.strip() or not continuation_input.strip():
            raise ValueError("existing thread, trigger key, and continuation input are required")
        command = [
            self.executable, "exec", "resume", thread_id,
            f"ATLAS_TRIGGER={trigger_key}\n{continuation_input}",
            "--json",
        ]
        acknowledged = False
        if self.runner is None:
            result, acknowledged = self._run_streaming(
                command,
                expected_thread_id=thread_id,
                acknowledge=acknowledge,
            )
        else:
            try:
                result = self.runner(
                    command,
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=self.execution_timeout_seconds,
                )
            except subprocess.TimeoutExpired:
                raise TriggerReadbackFailure(
                    "APP_READBACK_FAILED", "existing-thread trigger readback timed out"
                ) from None
        if result.returncode != 0:
            raise TriggerReadbackFailure(
                "APP_READBACK_FAILED", "existing-thread trigger command failed"
            )
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
        turn_completed: list[int] = []
        visible_item_indexes: list[int] = []
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
                try:
                    candidate_turn = validate_continuation_turn_id(item.get("turn_id"))
                except ValueError:
                    raise ValueError(
                        "existing-thread trigger returned malformed lifecycle records"
                    ) from None
                if has_thread_id:
                    raise ValueError("existing-thread trigger returned malformed lifecycle records")
                turn_started.append((index, candidate_turn))
            elif event_type == "turn.completed":
                turn_completed.append(index)
            elif event_type == "item.completed":
                completed_item = item.get("item")
                item_type = completed_item.get("type") if isinstance(completed_item, dict) else None
                if isinstance(item_type, str) and item_type not in {"reasoning"}:
                    visible_item_indexes.append(index)
            elif has_thread_id or has_turn_id:
                raise ValueError("existing-thread trigger returned wrong lifecycle record types")

        if len(thread_started) == 0 or len(turn_started) == 0:
            raise TriggerReadbackFailure(
                "APP_READBACK_NO_TURN", "existing-thread trigger returned no correlated turn"
            )
        if (
            len(thread_started) != 1
            or len(turn_started) != 1
            or thread_started[0][0] >= turn_started[0][0]
            or thread_started[0][1] != thread_id
            or len(turn_completed) != 1
            or turn_completed[0] <= turn_started[0][0]
        ):
            raise TriggerReadbackFailure(
                "APP_READBACK_FAILED", "existing-thread trigger requires one correlated readback"
            )
        if any(
            index <= turn_started[0][0] or index >= turn_completed[0]
            for index in visible_item_indexes
        ):
            raise TriggerReadbackFailure(
                "APP_READBACK_FAILED",
                "existing-thread trigger returned an out-of-window owner item",
            )
        normalized = {
            "thread_id": thread_id,
            "turn_id": turn_started[0][1],
            "status": "completed",
            "visible_item_count": len(visible_item_indexes),
        }
        if acknowledge is not None and not acknowledged:
            acknowledge(thread_id, turn_started[0][1])
        return _closed_trigger_readback(normalized, expected_thread_id=thread_id)


class FixtureTriggerAdapter:
    """Deterministic local adapter for same-session and restart proofs."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def start_existing_turn(
        self,
        *,
        thread_id: str,
        trigger_key: str,
        continuation_input: str,
        acknowledge: Callable[[str, str], None] | None = None,
    ) -> TriggerReadback:
        self.calls.append((thread_id, trigger_key))
        turn_id = "turn_" + trigger_key.removeprefix("trg_")[:24]
        if acknowledge is not None:
            acknowledge(thread_id, turn_id)
        return TriggerReadback(
            thread_id=thread_id,
            turn_id=turn_id,
            status="completed",
            visible_item_count=1,
        )


class ContinuationDispatcher:
    """One-shot outbox dispatcher. It has no loop, timer, or task creation seam."""

    def __init__(
        self,
        runtime: AtlasRuntime,
        adapter: TriggerAdapter,
        *,
        checkpoint_probe: Callable[[str], str | None] | None = None,
    ) -> None:
        if checkpoint_probe is None and not isinstance(adapter, FixtureTriggerAdapter):
            raise ValueError(
                "production continuation dispatch requires a checkpoint probe"
            )
        self.runtime = runtime
        self.adapter = adapter
        self.checkpoint_probe = checkpoint_probe

    def dispatch_one(self, *, worker_id: str) -> dict[str, object] | None:
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
        checkpoint_before = (
            self.checkpoint_probe(item.thread_id) if self.checkpoint_probe is not None else None
        )
        if self.checkpoint_probe is not None and checkpoint_before is None:
            self.runtime.fail_continuation_trigger(
                trigger_key=item.trigger_key,
                worker_id=worker_id,
                error_class="APP_READBACK_NO_CHECKPOINT",
            )
            return {
                "trigger_key": item.trigger_key,
                "packet_id": item.packet_id,
                "thread_id": item.thread_id,
                "status": "blocked",
                "failure_code": "APP_READBACK_NO_CHECKPOINT",
                "retry_class": "RECONCILE_ONLY",
            }

        def acknowledge(thread_id: str, turn_id: str) -> None:
            self.runtime.acknowledge_continuation_trigger(
                trigger_key=item.trigger_key,
                thread_id=thread_id,
                turn_id=turn_id,
                checkpoint_before_id=checkpoint_before,
                execution_seconds=float(
                    getattr(self.adapter, "execution_timeout_seconds", 1800)
                ),
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
                acknowledge=acknowledge if self.checkpoint_probe is not None else None,
            )
            if self.checkpoint_probe is None:
                self.runtime.confirm_continuation_trigger(
                    trigger_key=item.trigger_key,
                    thread_id=readback.thread_id,
                    turn_id=readback.turn_id,
                )
                readback_class = "TRIGGER_CONFIRMED_COMPATIBILITY"
                checkpoint_after = None
            else:
                self.runtime.acknowledge_continuation_trigger(
                    trigger_key=item.trigger_key,
                    thread_id=readback.thread_id,
                    turn_id=readback.turn_id,
                    checkpoint_before_id=checkpoint_before,
                )
                checkpoint_after = self.checkpoint_probe(item.thread_id)
                readback_class = self.runtime.finalize_continuation_owner_readback(
                    trigger_key=item.trigger_key,
                    thread_id=readback.thread_id,
                    turn_id=readback.turn_id,
                    visible_item_count=readback.visible_item_count,
                    checkpoint_after_id=checkpoint_after,
                )
            self.runtime.record_continuation_process_event(
                event_id=f"process:{item.trigger_key}:exited",
                owner_id=item.owner_id,
                packet_id=item.packet_id,
                process_state="EXITED",
            )
            result: dict[str, object] = dataclasses.asdict(readback) | {
                "trigger_key": item.trigger_key,
                "packet_id": item.packet_id,
                "readback_class": readback_class,
            }
            if checkpoint_after is not None:
                result["checkpoint_id"] = checkpoint_after
            if readback_class != "OWNER_EXECUTION_CONFIRMED" and self.checkpoint_probe is not None:
                result["status"] = "blocked"
                result["failure_code"] = readback_class
                result["retry_class"] = "RECONCILE_ONLY"
            return result
        except TriggerReadbackFailure as exc:
            self.runtime.fail_continuation_trigger(
                trigger_key=item.trigger_key,
                worker_id=worker_id,
                error_class=exc.failure_code,
            )
            self.runtime.record_continuation_process_event(
                event_id=f"process:{item.trigger_key}:failed",
                owner_id=item.owner_id,
                packet_id=item.packet_id,
                process_state="FAILED",
            )
            return {
                "trigger_key": item.trigger_key,
                "packet_id": item.packet_id,
                "thread_id": item.thread_id,
                "status": "blocked",
                "failure_code": exc.failure_code,
                "retry_class": "RECONCILE_ONLY",
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
        self,
        runtime: AtlasRuntime,
        adapter: TriggerAdapter,
        *,
        guard_path: str | Path,
        checkpoint_probe: Callable[[str], str | None],
    ) -> None:
        self.runtime = runtime
        self.adapter = adapter
        self.guard_path = Path(guard_path)
        self.checkpoint_probe = checkpoint_probe

    def handle_event(self, *, event_id: str, worker_id: str) -> dict[str, object]:
        with SingleInstanceGuard(self.guard_path):
            # Ingress alone is not authoritative evidence that an active owner
            # has become idle. A caller with a complete turn inventory may run
            # reconciliation explicitly with observed_turns; this event seam
            # deliberately performs recovery without inventing liveness.
            recovery = self.runtime.reconcile_continuation_startup()
            dispatch = ContinuationDispatcher(
                self.runtime,
                self.adapter,
                checkpoint_probe=self.checkpoint_probe,
            ).dispatch_one(worker_id=worker_id)
            if dispatch:
                trigger_key = dispatch.get("trigger_key")
                packet_id = dispatch.get("packet_id")
                if not isinstance(trigger_key, str) or not isinstance(packet_id, str):
                    raise ValueError("dispatch result is missing durable trigger identity")
                self.runtime.record_continuation_process_started_if_running(
                    event_id=f"{event_id}:accepted",
                    trigger_key=trigger_key,
                    packet_id=packet_id,
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
    checkpoint_before = "threadctx_" + "a" * 64
    checkpoint_after = "threadctx_" + "b" * 64
    decision = {} if restart else runtime.stop_hook_decision(
        owner_id="fixture.owner",
        thread_id="fixture-thread",
        checkpoint_before_id=checkpoint_before,
    )
    stop_hook_readback_class = None
    if not restart:
        stop_hook_readback_class = runtime.finalize_stop_hook_continuation(
            trigger_key=committed.trigger_key,
            thread_id="fixture-thread",
            turn_id="fixture-turn",
            visible_item_count=1,
            checkpoint_after_id=checkpoint_after,
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
        "stop_hook_readback_class": stop_hook_readback_class,
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
            checkpoint_root = Path(__file__).resolve().parents[2] / "runtime" / "atlas" / "thread-context"
            dispatch = ContinuationDispatcher(
                runtime,
                CodexPersistentThreadAdapter(),
                checkpoint_probe=FilesystemCheckpointProbe(checkpoint_root),
            ).dispatch_one(worker_id="atlasd-one-shot")
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
