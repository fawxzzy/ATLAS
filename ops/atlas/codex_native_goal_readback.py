"""Read a named Codex owner's current native turn from the task service.

This narrow adapter supplies evidence to the Goal assessor. It cannot send a
task message, resume a Goal, dispatch work, or perform a provider effect.
Environment values and caller-supplied MCP metadata are lookup hints, not
proof of the invoking process's identity. The assessor separately requires a
host-recorded owner-origin item bound to the exact audit and program.
"""

from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4


class NativeReadbackError(RuntimeError):
    pass


def _exact_uuid(value: Any, label: str) -> str:
    try:
        if not isinstance(value, str) or str(UUID(value)) != value:
            raise ValueError
    except (ValueError, AttributeError):
        raise NativeReadbackError(f"INVALID_{label}") from None
    return value


class CodexNativeReadbackClient:
    """Bounded stdio MCP client exposing only read_thread for its executor."""

    def __init__(self, *, timeout_seconds: float = 15.0) -> None:
        self.timeout_seconds = timeout_seconds
        self.process: subprocess.Popen[str] | None = None
        self.messages: queue.Queue[dict[str, Any] | BaseException] = queue.Queue()
        self.stderr_lines: list[str] = []
        self.next_id = 1
        self.reader_threads: list[threading.Thread] = []

    @staticmethod
    def _command() -> tuple[list[str], Path]:
        codex_home = Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))
        plugin_root = codex_home / "plugins/cache/openai-bundled/codex-app-tools"
        candidates = sorted(
            (p for p in plugin_root.iterdir() if p.is_dir() and (p / "server.mjs").is_file()),
            key=lambda p: tuple(int(x) for x in re.findall(r"\d+", p.name)),
            reverse=True,
        ) if plugin_root.is_dir() else []
        node = os.environ.get("CODEX_MCP_NODE_PATH") or shutil.which("node")
        if not candidates or not node or not Path(node).is_file():
            raise NativeReadbackError("BUNDLED_READBACK_RUNTIME_UNAVAILABLE")
        return [node, str(candidates[0] / "server.mjs")], candidates[0]

    def __enter__(self) -> "CodexNativeReadbackClient":
        command, cwd = self._command()
        self.process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        text=True, encoding="utf-8", errors="replace", bufsize=1)
        process = self.process

        def read_stdout() -> None:
            try:
                for line in process.stdout:
                    if line.strip():
                        self.messages.put(json.loads(line))
            except BaseException as error:  # fail closed on malformed or lost transport
                self.messages.put(error)

        def read_stderr() -> None:
            for line in process.stderr:
                if len(self.stderr_lines) < 100:
                    self.stderr_lines.append(line.rstrip())

        try:
            if process.stdout is None or process.stderr is None or process.stdin is None:
                raise NativeReadbackError("READBACK_STREAMS_UNAVAILABLE")
            for target in (read_stdout, read_stderr):
                reader = threading.Thread(target=target, daemon=True)
                reader.start()
                self.reader_threads.append(reader)
            self._request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                         "clientInfo": {"name": "atlas-goal-readback", "version": "1.0.0"}})
            self._write({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *_: Any) -> None:
        process = self.process
        if process is None:
            return
        stdin_closed = process.stdin is None
        try:
            if process.stdin is not None:
                try:
                    process.stdin.close()
                    stdin_closed = True
                except OSError:
                    pass
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    process.terminate()
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    try:
                        process.kill()
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=2)
        finally:
            # Process exit lets both pipe readers finish. Join only readers
            # whose start succeeded, before closing their owned streams.
            try:
                for reader in self.reader_threads:
                    reader.join(timeout=2)
            finally:
                if not stdin_closed and process.stdin is not None:
                    try:
                        process.stdin.close()
                    except OSError:
                        pass
                for pipe in (process.stdout, process.stderr):
                    if pipe is not None:
                        try:
                            pipe.close()
                        except OSError:
                            pass
                self.reader_threads.clear()
                self.process = None

    def _write(self, message: dict[str, Any]) -> None:
        if self.process is None or self.process.stdin is None:
            raise NativeReadbackError("READBACK_PROCESS_NOT_RUNNING")
        self.process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def _request(self, method: str, params: dict[str, Any]) -> Any:
        request_id = self.next_id
        self.next_id += 1
        self._write({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise NativeReadbackError(f"READBACK_TIMEOUT:{method}")
            try:
                message = self.messages.get(timeout=remaining)
            except queue.Empty as error:
                raise NativeReadbackError(f"READBACK_TIMEOUT:{method}") from error
            if isinstance(message, BaseException):
                raise NativeReadbackError("READBACK_TRANSPORT_FAILED") from message
            if not isinstance(message, dict):
                raise NativeReadbackError("READBACK_TRANSPORT_INVALID")
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise NativeReadbackError(f"READBACK_TOOL_ERROR:{method}")
            return message.get("result")

    def read_current_thread(self, caller: str, turn_id: str) -> dict[str, Any]:
        caller = _exact_uuid(caller, "CALLER")
        turn_id = _exact_uuid(turn_id, "TURN")
        if os.environ.get("CODEX_THREAD_ID") != caller or os.environ.get("CODEX_TURN_ID") not in (None, "", turn_id):
            raise NativeReadbackError("EXECUTOR_IDENTITY_DRIFT")
        metadata = {"openai/threadId": caller, "openai/toolCallId": "goal-readback-" + uuid4().hex}
        if os.environ.get("CODEX_TURN_ID"):
            metadata["openai/turnId"] = turn_id
        result = self._request("tools/call", {"name": "read_thread",
                                              "arguments": {"threadId": caller, "hostId": "local",
                                                            "turnLimit": 1, "includeOutputs": False,
                                                            "maxOutputCharsPerItem": 100},
                                              "_meta": metadata})
        if not isinstance(result, dict) or result.get("isError") or not isinstance(result.get("content"), list):
            raise NativeReadbackError("READBACK_TOOL_RESULT_INVALID")
        for item in result["content"]:
            if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                try:
                    payload = json.loads(item["text"])
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    return payload
        raise NativeReadbackError("READBACK_PAYLOAD_MISSING")


def read_current_native_turn(caller: str, turn_id: str) -> dict[str, Any]:
    """Return supported read_thread evidence for the named owner, once."""
    caller = _exact_uuid(caller, "CALLER")
    turn_id = _exact_uuid(turn_id, "TURN")
    if os.environ.get("CODEX_THREAD_ID") != caller or os.environ.get("CODEX_TURN_ID") not in (None, "", turn_id):
        raise NativeReadbackError("EXECUTOR_IDENTITY_DRIFT")
    with CodexNativeReadbackClient() as client:
        return client.read_current_thread(caller, turn_id)
