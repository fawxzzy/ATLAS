from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


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


def fetch_snapshot(base_url: str, token: str | None) -> dict[str, Any]:
    payload = request_json(
        base_url,
        "/atlas/artifacts/fetch",
        token=token,
        query={"ref": "runtime/state/atlas/world-model.snapshot.latest.json"},
    )
    snapshot = payload.get("json")
    if not isinstance(snapshot, dict):
        raise ValueError("World-model snapshot fetch did not return JSON.")
    return snapshot


def fetch_attention(base_url: str, token: str | None) -> dict[str, Any]:
    return request_json(base_url, "/atlas/attention", token=token)


def speak(text: str, *, enabled: bool) -> None:
    if not enabled or not text.strip():
        return
    script = (
        "Add-Type -AssemblyName System.Speech;"
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        f"$s.Speak({json.dumps(text)});"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def capture_push_to_talk() -> str | None:
    script = """
Add-Type -AssemblyName System.Speech
$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$recognizer.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
$recognizer.SetInputToDefaultAudioDevice()
$result = $recognizer.Recognize([TimeSpan]::FromSeconds(8))
if ($null -ne $result) { $result.Text }
"""
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    text = completed.stdout.strip()
    return text or None


def slugify(value: str) -> str:
    slug = "".join(character.lower() if character.isalnum() else "-" for character in value.strip())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "voice"


def render_lines(lines: list[str]) -> str:
    return "\n".join(line for line in lines if line).strip()


def handle_command(command: str, *, base_url: str, token: str | None, speak_enabled: bool) -> str:
    normalized = " ".join(command.lower().split())
    snapshot = None

    if "what needs attention" in normalized or normalized == "attention":
        attention = fetch_attention(base_url, token)
        items = attention.get("items", []) if isinstance(attention.get("items"), list) else []
        lines = [f"Attention items: {len(items)}"]
        for item in items[:5]:
            if isinstance(item, dict):
                lines.append(f"- [{item.get('severity', 'unknown')}] {item.get('summary', '')}")
        response = render_lines(lines)
        speak(response, enabled=speak_enabled)
        return response

    if "what changed today" in normalized or "changed today" in normalized:
        snapshot = fetch_snapshot(base_url, token)
        today = datetime.now(timezone.utc).date().isoformat()
        changed: list[str] = []
        for observation in snapshot.get("observations", []):
            if not isinstance(observation, dict):
                continue
            observed_at = str(observation.get("observed_at") or "")
            if observed_at.startswith(today):
                changed.append(
                    f"- {observation.get('observation_type', 'observation')} {observation.get('status', 'unknown')} from {observation.get('source_ref', '<unknown>')}"
                )
        response = render_lines([f"Observed changes on {today}: {len(changed)}", *changed[:8]])
        speak(response, enabled=speak_enabled)
        return response

    if "blocked sessions" in normalized:
        snapshot = snapshot or fetch_snapshot(base_url, token)
        blocked = [
            item
            for item in snapshot.get("inventory_entries", [])
            if isinstance(item, dict)
            and str(item.get("entry_type")) == "session"
            and str(item.get("status")) in {"resume_ready", "blocked", "paused", "merge_requested"}
        ]
        lines = [f"Blocked or resumable sessions: {len(blocked)}"]
        for item in blocked[:5]:
            lines.append(f"- {item.get('key')}: {item.get('status')}")
        response = render_lines(lines)
        speak(response, enabled=speak_enabled)
        return response

    if normalized.startswith("resume paused session") or normalized.startswith("resume session"):
        snapshot = snapshot or fetch_snapshot(base_url, token)
        requested_id = command.split()[-1] if command.strip().split() else ""
        candidates = [
            item
            for item in snapshot.get("inventory_entries", [])
            if isinstance(item, dict)
            and str(item.get("entry_type")) == "session"
            and str(item.get("status")) == "resume_ready"
        ]
        selected = None
        if requested_id:
            for item in candidates:
                if str(item.get("key")) == requested_id:
                    selected = item
                    break
        if selected is None and candidates:
            selected = candidates[0]
        if selected is None:
            response = "No resume_ready session is currently available."
            speak(response, enabled=speak_enabled)
            return response
        session_id = str(selected.get("key"))
        payload = run_python(
            [
                "ops/atlas/resume_session.py",
                "--session-id",
                session_id,
            ]
        )
        lines = [
            f"Dispatched governed resume for {session_id}.",
            f"- session_state: {payload.get('session_state')}",
            f"- final_status: {payload.get('final_status')}",
            f"- resume_run_manifest_ref: {payload.get('resume_run_manifest_ref')}",
        ]
        if payload.get("failure_reason"):
            lines.append(f"- failure_reason: {payload.get('failure_reason')}")
        response = render_lines(lines)
        speak(response, enabled=speak_enabled)
        return response

    if normalized.startswith("run read-only scan on "):
        target = command.split("run read-only scan on ", 1)[1].strip()
        payload = run_python(
            [
                "ops/atlas/run_session.py",
                "--task-id",
                f"voice-readonly-{slugify(target)}",
                "--title",
                f"Voice read-only scan: {target}",
                "--query-term",
                target,
            ]
        )
        session_id = payload.get("session_id") or payload.get("session", {}).get("session_id")
        response = render_lines(
            [
                f"Started governed read-only scan for {target}.",
                f"- session_id: {session_id}",
            ]
        )
        speak(response, enabled=speak_enabled)
        return response

    if "verta posture" in normalized:
        payload = request_json(base_url, "/atlas/artifacts/fetch", token=token, query={"id": "knowledge:personal--verta-core"})
        response = render_lines(
            [
                "Current Verta posture:",
                "- metadata-only trust gate remains in force",
                f"- source: {payload.get('id')}",
            ]
        )
        speak(response, enabled=speak_enabled)
        return response

    if "create a plan" in normalized or "create plan" in normalized or "create decision" in normalized:
        status = request_json(base_url, "/atlas/status", token=token)
        active = status.get("active_session") if isinstance(status.get("active_session"), dict) else {}
        session_id = str(active.get("session_id") or "").strip()
        if not session_id:
            response = "No active governed session is available to author from."
            speak(response, enabled=speak_enabled)
            return response
        args = ["ops/atlas/author_working_memory.py", "--session-id", session_id]
        if "decision" in normalized:
            args += ["--memory-kind", "decision"]
        if "plan" in normalized:
            args += ["--memory-kind", "plan"]
        if "plan" not in normalized and "decision" not in normalized:
            args += ["--memory-kind", "plan", "--memory-kind", "decision"]
        payload = run_python(args)
        lines = [f"Authored working memory from {session_id}."]
        for item in payload.get("items", [])[:4]:
            if isinstance(item, dict):
                lines.append(f"- {item.get('memory_kind')}: {item.get('id')}")
        response = render_lines(lines)
        speak(response, enabled=speak_enabled)
        return response

    response = "Supported intents: what needs attention, what changed today, show blocked sessions, resume paused session, run read-only scan on X, summarize current Verta posture, create a plan, create a decision."
    speak(response, enabled=speak_enabled)
    return response


def watch(base_url: str, token: str | None, *, poll_seconds: int, speak_enabled: bool) -> int:
    last_session_state: tuple[str | None, str | None] | None = None
    last_attention_keys: set[tuple[str, str]] = set()
    while True:
        status = request_json(base_url, "/atlas/status", token=token)
        attention = fetch_attention(base_url, token)
        active = status.get("active_session") if isinstance(status.get("active_session"), dict) else {}
        session_state = (
            str(active.get("session_id") or ""),
            str(active.get("final_status") or active.get("session_state") or ""),
        )
        if session_state != last_session_state and session_state[0]:
            speak(f"Session {session_state[0]} is now {session_state[1]}.", enabled=speak_enabled)
            print(f"session_update: {session_state[0]} -> {session_state[1]}")
            last_session_state = session_state
        current_attention_keys = {
            (str(item.get("kind") or ""), str(item.get("source_ref") or ""))
            for item in attention.get("items", [])
            if isinstance(item, dict)
        }
        new_attention = [
            item
            for item in attention.get("items", [])
            if isinstance(item, dict)
            and (str(item.get("kind") or ""), str(item.get("source_ref") or "")) not in last_attention_keys
            and str(item.get("kind") or "") in {"session_needs_resume", "blocked_worker", "open_merge_request", "execution_approval_pending", "resume_failed"}
        ]
        for item in new_attention:
            summary = str(item.get("summary") or item.get("kind") or "attention")
            speak(summary, enabled=speak_enabled)
            print(f"attention: {summary}")
        last_attention_keys = current_attention_keys
        time.sleep(max(poll_seconds, 2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the explicit-command ATLAS voice shell over the Awareness API.")
    parser.add_argument("--base-url", default=os.environ.get("ATLAS_AWARENESS_URL", "http://127.0.0.1:8765"))
    parser.add_argument("--auth-token")
    parser.add_argument("--auth-token-file")
    parser.add_argument("--command")
    parser.add_argument("--push-to-talk", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=10)
    parser.add_argument("--mute", action="store_true")
    args = parser.parse_args(argv)

    token = load_token(args)
    speak_enabled = not args.mute

    if args.watch:
        return watch(args.base_url, token, poll_seconds=args.poll_seconds, speak_enabled=speak_enabled)

    if args.command:
        print(handle_command(args.command, base_url=args.base_url, token=token, speak_enabled=speak_enabled))
        return 0

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
        if command.lower() in {"exit", "quit"}:
            return 0
        print(handle_command(command, base_url=args.base_url, token=token, speak_enabled=speak_enabled))


if __name__ == "__main__":
    raise SystemExit(main())
