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
    del base_url
    del token
    payload = run_python(
        [
            "ops/atlas/converse.py",
            "--conversation-id",
            "voice-main",
            "--mode",
            "voice",
            "--input",
            command,
        ]
    )
    response = str(payload.get("response") or payload.get("response_summary") or "No response was produced.")
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
            and str(item.get("kind") or "") in {"session_needs_resume", "blocked_worker", "open_merge_request", "execution_approval_pending", "resume_failed", "initiative_open_attention"}
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
