from __future__ import annotations

import argparse
import base64
import json
import os
import queue
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONVERSATION_ID = "voice-main"
VOICE_RUN_ROOT = ROOT / "runtime" / "atlas" / "voice" / "runs"
EXIT_COMMANDS = {"exit", "quit", "exit atlas", "quit atlas", "stop listening"}
INTERRUPT_COMMANDS = {"stop", "stop talking", "cancel response", "be quiet", "interrupt"}


def load_token(args: argparse.Namespace) -> str | None:
    if isinstance(args.auth_token, str) and args.auth_token.strip():
        return args.auth_token.strip()
    env_token = os.environ.get("ATLAS_AWARENESS_TOKEN", "").strip()
    if env_token:
        return env_token
    token_file = args.auth_token_file or os.environ.get("ATLAS_AWARENESS_TOKEN_FILE")
    if token_file:
        return Path(str(token_file)).expanduser().resolve().read_text(encoding="utf-8").strip()
    return None


def request_json(base_url: str, path: str, *, token: str | None = None, query: dict[str, Any] | None = None) -> dict[str, Any]:
    url = base_url.rstrip("/") + path
    if query:
        encoded = urllib.parse.urlencode({key: value for key, value in query.items() if value is not None})
        if encoded:
            url = f"{url}?{encoded}"
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object from {url}.")
    return payload


def run_python(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "command failed")
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise ValueError("Expected JSON output from helper command.")
    return payload


def split_response_segments(value: str, *, segment_limit: int = 220) -> list[str]:
    text = " ".join(value.split()).strip()
    if not text:
        return []
    segments: list[str] = []
    chunk = ""
    for word in text.split(" "):
        candidate = f"{chunk} {word}".strip()
        if chunk and len(candidate) > segment_limit:
            segments.append(chunk)
            chunk = word
        else:
            chunk = candidate
    if chunk:
        segments.append(chunk)
    return segments


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def slugify_fragment(value: str) -> str:
    cleaned = "".join(character if character.isalnum() or character in {"-", "_"} else "-" for character in value.lower())
    compact = "-".join(part for part in cleaned.split("-") if part)
    return compact or "voice"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def fetch_voice_runtime(base_url: str, token: str | None, *, conversation_id: str | None) -> dict[str, Any]:
    return request_json(
        base_url,
        "/atlas/voice",
        token=token,
        query={"conversation_id": conversation_id},
    )


def powershell_encoded_command(script: str) -> list[str]:
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return ["powershell", "-NoProfile", "-EncodedCommand", encoded]


def speak_blocking(text: str, *, enabled: bool, rate: int = 0) -> None:
    if not enabled or not text.strip():
        return
    script = (
        "$ErrorActionPreference='Stop';"
        "Add-Type -AssemblyName System.Speech;"
        "$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        f"$speaker.Rate = {int(rate)};"
        f"$speaker.Speak({json.dumps(text)});"
    )
    subprocess.run(
        powershell_encoded_command(script),
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def capture_push_to_talk() -> str | None:
    script = """
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Speech
$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$recognizer.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
$recognizer.SetInputToDefaultAudioDevice()
$result = $recognizer.Recognize([TimeSpan]::FromSeconds(8))
if ($null -ne $result) { $result.Text }
"""
    completed = subprocess.run(
        powershell_encoded_command(script),
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    text = completed.stdout.strip()
    return text or None


def run_turn(command: str, *, conversation_id: str) -> dict[str, Any]:
    payload = run_python(
        [
            "ops/atlas/converse.py",
            "--conversation-id",
            conversation_id,
            "--mode",
            "voice",
            "--input",
            command,
        ]
    )
    response = str(payload.get("response") or payload.get("response_summary") or "No response was produced.")
    segments = payload.get("response_segments")
    if not isinstance(segments, list) or not all(isinstance(item, str) for item in segments):
        payload["response_segments"] = split_response_segments(response)
    return payload


class VoiceRunLogger:
    def __init__(
        self,
        *,
        conversation_id: str,
        mode: str,
        base_url: str,
        speak_enabled: bool,
        poll_seconds: int | None = None,
        speech_rate: int | None = None,
        min_confidence: float | None = None,
        print_partials: bool = False,
    ) -> None:
        self.conversation_id = conversation_id
        self.mode = mode
        self.started_at = utc_now()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        slug = slugify_fragment(conversation_id)
        self.run_id = f"voice-run-{slug}-{timestamp}"
        self.run_dir = (VOICE_RUN_ROOT / slug).resolve()
        self.events_path = self.run_dir / f"{self.run_id}.jsonl"
        self.summary_path = self.run_dir / f"{self.run_id}.summary.json"
        self.latest_summary_path = self.run_dir / "latest.summary.json"
        self.counts = {
            "turns": 0,
            "notifications": 0,
            "interrupts": 0,
            "low_confidence_ignored": 0,
            "diagnostics": 0,
        }
        self._closed = False
        self._append(
            "run_started",
            {
                "conversation_id": conversation_id,
                "mode": mode,
                "base_url": base_url,
                "speak_enabled": speak_enabled,
                "poll_seconds": poll_seconds,
                "speech_rate": speech_rate,
                "min_confidence": min_confidence,
                "print_partials": print_partials,
                "stores_raw_transcript": False,
                "stores_raw_audio": False,
            },
        )

    def _append(self, event: str, payload: dict[str, Any]) -> None:
        append_jsonl(
            self.events_path,
            {
                "recorded_at": utc_now(),
                "run_id": self.run_id,
                "event": event,
                **payload,
            },
        )

    def record_notification(self, payload: dict[str, Any]) -> None:
        self.counts["notifications"] += 1
        self._append(
            "notification",
            {
                "category": payload.get("category"),
                "kind": payload.get("kind"),
                "summary": payload.get("summary"),
                "source_ref": payload.get("source_ref"),
                "key": payload.get("key"),
            },
        )

    def record_turn(self, payload: dict[str, Any]) -> None:
        self.counts["turns"] += 1
        self._append(
            "grounded_turn",
            {
                "turn_id": payload.get("turn_id"),
                "turn_ref": payload.get("turn_ref"),
                "conversation_ref": payload.get("conversation_ref"),
                "created_at": payload.get("created_at"),
                "input_summary": payload.get("input_summary"),
                "response_summary": payload.get("response_summary"),
                "intent": payload.get("intent"),
                "action_mode": payload.get("action_mode"),
                "proposed_session_refs": payload.get("proposed_session_refs"),
                "authored_memory_refs": payload.get("authored_memory_refs"),
            },
        )

    def record_interrupt(self, *, reason: str, interrupted_source: str | None) -> None:
        self.counts["interrupts"] += 1
        self._append(
            "interrupt",
            {
                "reason": reason,
                "interrupted_source": interrupted_source,
            },
        )

    def record_low_confidence(self, confidence: float) -> None:
        self.counts["low_confidence_ignored"] += 1
        self._append(
            "low_confidence_ignored",
            {
                "confidence": round(confidence, 3),
            },
        )

    def record_diagnostic(self, text: str) -> None:
        self.counts["diagnostics"] += 1
        self._append(
            "diagnostic",
            {
                "message": text,
            },
        )

    def close(self, *, outcome: str, error: str | None = None) -> None:
        if self._closed:
            return
        self._closed = True
        finished_at = utc_now()
        summary = {
            "contract_version": "atlas.voice.run.summary.v1",
            "run_id": self.run_id,
            "conversation_id": self.conversation_id,
            "mode": self.mode,
            "started_at": self.started_at,
            "finished_at": finished_at,
            "outcome": outcome,
            "error": error,
            "counts": self.counts,
            "artifacts": {
                "events_path": str(self.events_path.relative_to(ROOT)).replace("\\", "/"),
                "summary_path": str(self.summary_path.relative_to(ROOT)).replace("\\", "/"),
            },
            "privacy": {
                "stores_raw_transcript": False,
                "stores_raw_audio": False,
                "stores_grounded_turn_summaries": True,
            },
        }
        self._append("run_finished", {"finished_at": finished_at, "outcome": outcome, "error": error})
        write_json(self.summary_path, summary)
        write_json(self.latest_summary_path, summary)


def handle_command(
    command: str,
    *,
    conversation_id: str,
    speak_enabled: bool,
    speech_rate: int,
    logger: VoiceRunLogger | None = None,
) -> str:
    payload = run_turn(command, conversation_id=conversation_id)
    if logger is not None:
        logger.record_turn(payload)
    response = str(payload.get("response") or payload.get("response_summary") or "No response was produced.")
    speak_blocking(response, enabled=speak_enabled, rate=speech_rate)
    return response


class PowerShellSpeaker:
    def __init__(self, *, enabled: bool, rate: int = 0) -> None:
        self.enabled = enabled
        self.rate = rate
        self._jobs: queue.Queue[dict[str, Any] | None] = queue.Queue()
        self._lock = threading.Lock()
        self._generation = 0
        self._current_process: subprocess.Popen[str] | None = None
        self._current_source: str | None = None
        self._closed = False
        self._worker = threading.Thread(target=self._run, name="atlas-voice-speaker", daemon=True)
        self._worker.start()

    def _speak_process(self, text: str) -> subprocess.Popen[str]:
        script = (
            "$ErrorActionPreference='Stop';"
            "Add-Type -AssemblyName System.Speech;"
            "$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            f"$speaker.Rate = {int(self.rate)};"
            f"$speaker.Speak({json.dumps(text)});"
        )
        return subprocess.Popen(
            powershell_encoded_command(script),
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )

    def _run(self) -> None:
        while True:
            job = self._jobs.get()
            if job is None:
                return
            generation = int(job["generation"])
            if not self.enabled or generation != self._generation:
                continue
            for segment in job["segments"]:
                if not isinstance(segment, str) or not segment.strip():
                    continue
                if generation != self._generation or self._closed:
                    break
                process = self._speak_process(segment)
                with self._lock:
                    self._current_process = process
                    self._current_source = str(job.get("source") or "unknown")
                process.wait()
                with self._lock:
                    if self._current_process is process:
                        self._current_process = None
                        self._current_source = None
                if generation != self._generation or self._closed:
                    break

    def enqueue_text(self, text: str, *, source: str) -> None:
        self.enqueue_segments(split_response_segments(text), source=source)

    def enqueue_segments(self, segments: list[str], *, source: str) -> None:
        clean_segments = [segment.strip() for segment in segments if isinstance(segment, str) and segment.strip()]
        if not clean_segments:
            return
        self._jobs.put({"generation": self._generation, "source": source, "segments": clean_segments})

    def interrupt(self) -> str | None:
        with self._lock:
            self._generation += 1
            process = self._current_process
            source = self._current_source
            self._current_process = None
            self._current_source = None
        if process is not None and process.poll() is None:
            process.terminate()
        return source

    def is_speaking(self) -> bool:
        with self._lock:
            return self._current_process is not None and self._current_process.poll() is None

    def close(self) -> None:
        self._closed = True
        self.interrupt()
        self._jobs.put(None)
        self._worker.join(timeout=2)


class PowerShellSpeechRecognizer:
    def __init__(self) -> None:
        self._events: queue.Queue[dict[str, Any]] = queue.Queue()
        self._closed = False
        script = """
$ErrorActionPreference='Stop'
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Speech
$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$recognizer.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
$recognizer.InitialSilenceTimeout = [TimeSpan]::FromSeconds(6)
$recognizer.BabbleTimeout = [TimeSpan]::FromSeconds(2)
$recognizer.EndSilenceTimeout = [TimeSpan]::FromMilliseconds(650)
$recognizer.EndSilenceTimeoutAmbiguous = [TimeSpan]::FromMilliseconds(900)
$recognizer.SetInputToDefaultAudioDevice()
Register-ObjectEvent -InputObject $recognizer -EventName SpeechDetected -Action {
  $payload = [ordered]@{
    event = 'speech_start'
    timestamp = [DateTime]::UtcNow.ToString('o')
    text = ''
    confidence = 0.0
  }
  [Console]::Out.WriteLine(($payload | ConvertTo-Json -Compress))
  [Console]::Out.Flush()
} | Out-Null
Register-ObjectEvent -InputObject $recognizer -EventName SpeechHypothesized -Action {
  $result = $Event.SourceEventArgs.Result
  if ($null -eq $result -or [string]::IsNullOrWhiteSpace($result.Text)) { return }
  $payload = [ordered]@{
    event = 'partial'
    timestamp = [DateTime]::UtcNow.ToString('o')
    text = $result.Text
    confidence = [double]$result.Confidence
  }
  [Console]::Out.WriteLine(($payload | ConvertTo-Json -Compress))
  [Console]::Out.Flush()
} | Out-Null
Register-ObjectEvent -InputObject $recognizer -EventName SpeechRecognized -Action {
  $result = $Event.SourceEventArgs.Result
  if ($null -eq $result -or [string]::IsNullOrWhiteSpace($result.Text)) { return }
  $payload = [ordered]@{
    event = 'final'
    timestamp = [DateTime]::UtcNow.ToString('o')
    text = $result.Text
    confidence = [double]$result.Confidence
  }
  [Console]::Out.WriteLine(($payload | ConvertTo-Json -Compress))
  [Console]::Out.Flush()
} | Out-Null
Register-ObjectEvent -InputObject $recognizer -EventName SpeechRecognitionRejected -Action {
  $payload = [ordered]@{
    event = 'rejected'
    timestamp = [DateTime]::UtcNow.ToString('o')
    text = ''
    confidence = 0.0
  }
  [Console]::Out.WriteLine(($payload | ConvertTo-Json -Compress))
  [Console]::Out.Flush()
} | Out-Null
$recognizer.RecognizeAsync([System.Speech.Recognition.RecognizeMode]::Multiple)
try {
  while ($true) {
    $evt = Wait-Event -Timeout 1
    if ($null -ne $evt) {
      Remove-Event -EventIdentifier $evt.EventIdentifier -ErrorAction SilentlyContinue
    }
  }
} finally {
  $recognizer.RecognizeAsyncCancel()
  $recognizer.Dispose()
}
"""
        self._process = subprocess.Popen(
            powershell_encoded_command(script),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self._stdout_thread = threading.Thread(target=self._read_stdout, name="atlas-voice-recognizer-stdout", daemon=True)
        self._stderr_thread = threading.Thread(target=self._read_stderr, name="atlas-voice-recognizer-stderr", daemon=True)
        self._stdout_thread.start()
        self._stderr_thread.start()
        time.sleep(0.75)
        if self._process.poll() is not None:
            stderr = ""
            if self._process.stderr is not None:
                stderr = self._process.stderr.read().strip()
            raise RuntimeError(stderr or "Streaming speech recognition failed to start.")

    def _read_stdout(self) -> None:
        assert self._process.stdout is not None
        for line in self._process.stdout:
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                payload = {"event": "diagnostic", "text": text, "confidence": 0.0}
            if isinstance(payload, dict):
                self._events.put(payload)

    def _read_stderr(self) -> None:
        assert self._process.stderr is not None
        for line in self._process.stderr:
            text = line.strip()
            if text:
                self._events.put({"event": "diagnostic", "text": text, "confidence": 0.0})

    def next_event(self, *, timeout: float) -> dict[str, Any] | None:
        try:
            return self._events.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()


class VoiceNotificationWatcher:
    def __init__(
        self,
        *,
        base_url: str,
        token: str | None,
        conversation_id: str,
        poll_seconds: int,
    ) -> None:
        self.base_url = base_url
        self.token = token
        self.conversation_id = conversation_id
        self.poll_seconds = max(poll_seconds, 2)
        self._events: queue.Queue[dict[str, Any]] = queue.Queue()
        self._closed = threading.Event()
        self._thread = threading.Thread(target=self._run, name="atlas-voice-notifications", daemon=True)
        self._seen_keys: set[str] = set()
        self._thread.start()

    def _run(self) -> None:
        first_snapshot = True
        while not self._closed.is_set():
            try:
                payload = fetch_voice_runtime(self.base_url, self.token, conversation_id=self.conversation_id)
                notifications = payload.get("notifications", []) if isinstance(payload.get("notifications"), list) else []
                current_keys = {
                    str(item.get("key"))
                    for item in notifications
                    if isinstance(item, dict) and str(item.get("key") or "").strip()
                }
                if first_snapshot:
                    self._seen_keys = current_keys
                    first_snapshot = False
                else:
                    for item in notifications:
                        if not isinstance(item, dict):
                            continue
                        key = str(item.get("key") or "").strip()
                        summary = str(item.get("summary") or "").strip()
                        if key and summary and key not in self._seen_keys:
                            self._events.put(item)
                    self._seen_keys = current_keys
            except Exception:
                pass
            self._closed.wait(self.poll_seconds)

    def drain(self) -> list[dict[str, Any]]:
        notifications: list[dict[str, Any]] = []
        while True:
            try:
                notifications.append(self._events.get_nowait())
            except queue.Empty:
                return notifications

    def close(self) -> None:
        self._closed.set()
        self._thread.join(timeout=2)


def print_voice_banner(conversation_id: str) -> None:
    print(f"ATLAS streaming voice ready on conversation '{conversation_id}'.")
    print("Speak naturally. Say 'stop' to interrupt speech or 'exit atlas' to quit.")


def normalize_control_text(text: str) -> str:
    return " ".join(text.lower().split())


def stream_voice(
    *,
    base_url: str,
    token: str | None,
    conversation_id: str,
    speak_enabled: bool,
    speech_rate: int,
    poll_seconds: int,
    min_confidence: float,
    print_partials: bool,
) -> int:
    speaker = PowerShellSpeaker(enabled=speak_enabled, rate=speech_rate)
    recognizer = PowerShellSpeechRecognizer()
    logger = VoiceRunLogger(
        conversation_id=conversation_id,
        mode="stream",
        base_url=base_url,
        speak_enabled=speak_enabled,
        poll_seconds=poll_seconds,
        speech_rate=speech_rate,
        min_confidence=min_confidence,
        print_partials=print_partials,
    )
    notifications = VoiceNotificationWatcher(
        base_url=base_url,
        token=token,
        conversation_id=conversation_id,
        poll_seconds=poll_seconds,
    )
    atexit_registered = False

    def _cleanup() -> None:
        notifications.close()
        recognizer.close()
        speaker.close()

    try:
        import atexit

        atexit.register(_cleanup)
        atexit_registered = True
    except Exception:
        pass

    print_voice_banner(conversation_id)
    last_partial = ""
    outcome = "completed"
    error: str | None = None
    try:
        while True:
            for notification in notifications.drain():
                summary = str(notification.get("summary") or "").strip()
                print(f"notify> {summary}")
                logger.record_notification(notification)
                speaker.enqueue_text(summary, source="notification")

            event = recognizer.next_event(timeout=0.25)
            if event is None:
                continue
            event_name = str(event.get("event") or "").strip()
            text = str(event.get("text") or "").strip()
            confidence = float(event.get("confidence") or 0.0)

            if event_name == "diagnostic":
                print(f"voice-diagnostic> {text}")
                logger.record_diagnostic(text)
                continue

            if event_name == "partial":
                if speaker.is_speaking() and text:
                    interrupted_source = speaker.interrupt()
                    print("atlas> interrupted")
                    logger.record_interrupt(reason="barge_in_partial", interrupted_source=interrupted_source)
                if print_partials and text and text != last_partial:
                    print(f"heard> {text}")
                    last_partial = text
                continue

            if event_name == "rejected":
                last_partial = ""
                continue

            if event_name != "final" or not text:
                continue

            last_partial = ""
            if confidence < min_confidence:
                print(f"heard> ignored low-confidence speech ({confidence:.2f})")
                logger.record_low_confidence(confidence)
                continue

            normalized = normalize_control_text(text)
            if normalized in EXIT_COMMANDS:
                outcome = "operator_exit"
                return 0
            if normalized in INTERRUPT_COMMANDS:
                interrupted_source = speaker.interrupt()
                print("atlas> interrupted")
                logger.record_interrupt(reason="control_phrase", interrupted_source=interrupted_source)
                continue

            print(f"user> {text}")
            payload = run_turn(text, conversation_id=conversation_id)
            response = str(payload.get("response") or payload.get("response_summary") or "No response was produced.")
            logger.record_turn(payload)
            print(f"atlas> {response}")
            speaker.enqueue_segments(
                payload.get("response_segments", split_response_segments(response)),
                source="response",
            )
    except KeyboardInterrupt:
        outcome = "keyboard_interrupt"
        return 130
    except Exception as exc:
        outcome = "error"
        error = str(exc)
        raise
    finally:
        logger.close(outcome=outcome, error=error)
        _cleanup()
        if atexit_registered:
            try:
                import atexit

                atexit.unregister(_cleanup)
            except Exception:
                pass


def watch(
    base_url: str,
    token: str | None,
    *,
    conversation_id: str,
    poll_seconds: int,
    speak_enabled: bool,
    speech_rate: int,
) -> int:
    last_seen: set[str] | None = None
    logger = VoiceRunLogger(
        conversation_id=conversation_id,
        mode="watch",
        base_url=base_url,
        speak_enabled=speak_enabled,
        poll_seconds=poll_seconds,
        speech_rate=speech_rate,
    )
    while True:
        try:
            payload = fetch_voice_runtime(base_url, token, conversation_id=conversation_id)
            notifications = payload.get("notifications", []) if isinstance(payload.get("notifications"), list) else []
            current_keys = {
                str(item.get("key"))
                for item in notifications
                if isinstance(item, dict) and str(item.get("key") or "").strip()
            }
            if last_seen is None:
                last_seen = current_keys
            else:
                for item in notifications:
                    if not isinstance(item, dict):
                        continue
                    key = str(item.get("key") or "").strip()
                    summary = str(item.get("summary") or item.get("kind") or "attention").strip()
                    if key and key not in last_seen:
                        logger.record_notification(item)
                        print(f"attention: {summary}")
                        speak_blocking(summary, enabled=speak_enabled, rate=speech_rate)
                last_seen = current_keys
            time.sleep(max(poll_seconds, 2))
        except KeyboardInterrupt:
            logger.close(outcome="keyboard_interrupt")
            return 130
        except Exception as exc:
            logger.close(outcome="error", error=str(exc))
            raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ATLAS voice client on top of the Awareness API and grounded conversation runtime.")
    parser.add_argument("--base-url", default=os.environ.get("ATLAS_AWARENESS_URL", "http://127.0.0.1:8765"))
    parser.add_argument("--auth-token")
    parser.add_argument("--auth-token-file")
    parser.add_argument("--conversation-id", default=DEFAULT_CONVERSATION_ID)
    parser.add_argument("--command")
    parser.add_argument("--push-to-talk", action="store_true")
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=10)
    parser.add_argument("--min-confidence", type=float, default=0.45)
    parser.add_argument("--speech-rate", type=int, default=0)
    parser.add_argument("--print-partials", action="store_true")
    parser.add_argument("--mute", action="store_true")
    args = parser.parse_args(argv)

    token = load_token(args)
    speak_enabled = not args.mute

    if args.watch:
        return watch(
            args.base_url,
            token,
            conversation_id=args.conversation_id,
            poll_seconds=args.poll_seconds,
            speak_enabled=speak_enabled,
            speech_rate=args.speech_rate,
        )

    if args.command:
        logger = VoiceRunLogger(
            conversation_id=args.conversation_id,
            mode="command",
            base_url=args.base_url,
            speak_enabled=speak_enabled,
            speech_rate=args.speech_rate,
        )
        try:
            print(
                handle_command(
                    args.command,
                    conversation_id=args.conversation_id,
                    speak_enabled=speak_enabled,
                    speech_rate=args.speech_rate,
                    logger=logger,
                )
            )
            logger.close(outcome="completed")
            return 0
        except KeyboardInterrupt:
            logger.close(outcome="keyboard_interrupt")
            return 130
        except Exception as exc:
            logger.close(outcome="error", error=str(exc))
            raise

    if args.stream:
        return stream_voice(
            base_url=args.base_url,
            token=token,
            conversation_id=args.conversation_id,
            speak_enabled=speak_enabled,
            speech_rate=args.speech_rate,
            poll_seconds=args.poll_seconds,
            min_confidence=args.min_confidence,
            print_partials=args.print_partials,
        )

    while True:
        if args.push_to_talk:
            print("Push-to-talk: press Enter, then speak one command.")
            input()
            command = capture_push_to_talk()
            if not command:
                command = input("Speech recognition was unavailable. Type command: ").strip()
        else:
            command = input("ATLAS talk> ").strip()
        if not command:
            continue
        if normalize_control_text(command) in EXIT_COMMANDS:
            return 0
        print(
            handle_command(
                command,
                conversation_id=args.conversation_id,
                speak_enabled=speak_enabled,
                speech_rate=args.speech_rate,
            )
        )


if __name__ == "__main__":
    raise SystemExit(main())
