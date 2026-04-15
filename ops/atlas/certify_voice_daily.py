from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.talk import VoiceRunLogger, VOICE_RUN_ROOT, load_token, request_json, run_turn

DEFAULT_PROMPTS = [
    "what needs attention",
    "summarize initiative mazer d2 learning scorer",
    "what repo work is waiting on blessing review",
    "propose next work for initiative mazer d2 learning scorer",
]
RECEIPT_CONTRACT_VERSION = "atlas.voice.certification.v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_slashes(value: str) -> str:
    return value.replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def conversation_manifest_path(conversation_id: str) -> Path:
    return ROOT / "runtime" / "atlas" / "conversations" / conversation_id / "conversation.manifest.json"


def voice_run_latest_summary_path(conversation_id: str) -> Path:
    return VOICE_RUN_ROOT / conversation_id / "latest.summary.json"


def run_json_command(args: list[str]) -> tuple[int, dict[str, Any] | None, str]:
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    stdout = completed.stdout.strip()
    payload: dict[str, Any] | None = None
    if stdout:
        try:
            loaded = json.loads(stdout)
            if isinstance(loaded, dict):
                payload = loaded
        except json.JSONDecodeError:
            payload = None
    stderr = completed.stderr.strip()
    output = stderr or stdout
    return completed.returncode, payload, output


def run_stack_preflight() -> dict[str, Any]:
    code, _, output = run_json_command(["ops/validation/validate_stack.py", "--ratchet"])
    report_path = ROOT / "runtime" / "receipts" / "validation" / "stack-validation.latest.json"
    report = read_json(report_path) if report_path.exists() else {}
    ratchet = report.get("ratchet") if isinstance(report.get("ratchet"), dict) else {}
    return {
        "ok": code == 0,
        "exit_code": code,
        "report_path": normalize_slashes(str(report_path.relative_to(ROOT))) if report_path.exists() else None,
        "summary": report.get("summary"),
        "ratchet": ratchet,
        "new_blocking_count": int(ratchet.get("new_blocking_count", 0) or 0),
        "message": output,
    }


def run_awareness_preflight(base_url: str, token: str | None) -> dict[str, Any]:
    args = ["ops/atlas/check_awareness_health.py", "--base-url", base_url]
    if token:
        args.extend(["--auth-token", token])
    code, payload, output = run_json_command(args)
    return {
        "ok": code == 0 and isinstance(payload, dict) and bool(payload.get("ok")),
        "exit_code": code,
        "payload": payload,
        "message": output,
    }


def run_scripted_turns(
    *,
    prompts: list[str],
    conversation_id: str,
    base_url: str,
) -> dict[str, Any]:
    logger = VoiceRunLogger(
        conversation_id=conversation_id,
        mode="certification",
        base_url=base_url,
        speak_enabled=False,
        speech_rate=0,
    )
    turns: list[dict[str, Any]] = []
    outcome = "completed"
    error: str | None = None
    try:
        for prompt in prompts:
            payload = run_turn(prompt, conversation_id=conversation_id)
            logger.record_turn(payload)
            turns.append(
                {
                    "prompt": prompt,
                    "turn_id": payload.get("turn_id"),
                    "turn_ref": payload.get("turn_ref"),
                    "intent": payload.get("intent"),
                    "action_mode": payload.get("action_mode"),
                    "input_summary": payload.get("input_summary"),
                    "response_summary": payload.get("response_summary"),
                    "proposed_session_refs": payload.get("proposed_session_refs", []),
                    "authored_memory_refs": payload.get("authored_memory_refs", []),
                }
            )
        return {
            "ok": True,
            "turns": turns,
            "run_id": logger.run_id,
            "summary_path": normalize_slashes(str(logger.summary_path.relative_to(ROOT))),
            "events_path": normalize_slashes(str(logger.events_path.relative_to(ROOT))),
        }
    except Exception as exc:
        outcome = "error"
        error = str(exc)
        return {
            "ok": False,
            "error": error,
            "turns": turns,
            "run_id": logger.run_id,
            "summary_path": normalize_slashes(str(logger.summary_path.relative_to(ROOT))),
            "events_path": normalize_slashes(str(logger.events_path.relative_to(ROOT))),
        }
    finally:
        logger.close(outcome=outcome, error=error)


def compare_read_model(
    *,
    conversation_id: str,
    base_url: str,
    token: str | None,
    scripted_turns: list[dict[str, Any]],
) -> dict[str, Any]:
    latest_summary_path = voice_run_latest_summary_path(conversation_id)
    manifest_path = conversation_manifest_path(conversation_id)
    latest_summary = read_json(latest_summary_path)
    manifest = read_json(manifest_path)
    voice_payload = request_json(
        base_url,
        "/atlas/voice",
        token=token,
        query={"conversation_id": conversation_id},
    )

    manifest_turn_refs = manifest.get("recent_turn_refs", []) if isinstance(manifest.get("recent_turn_refs"), list) else []
    voice_conversation = voice_payload.get("conversation") if isinstance(voice_payload.get("conversation"), dict) else {}
    voice_recent_turns = voice_conversation.get("recent_turns", []) if isinstance(voice_conversation.get("recent_turns"), list) else []
    expected_recent_turns = scripted_turns[-len(voice_recent_turns) :] if voice_recent_turns else []

    voice_turn_match = True
    for expected, actual in zip(expected_recent_turns, voice_recent_turns):
        if not isinstance(actual, dict):
            voice_turn_match = False
            break
        if str(actual.get("input_summary") or "").strip() != str(expected.get("input_summary") or "").strip():
            voice_turn_match = False
            break
        if str(actual.get("response_summary") or "").strip() != str(expected.get("response_summary") or "").strip():
            voice_turn_match = False
            break

    proposal_turns = [turn for turn in scripted_turns if str(turn.get("action_mode")) == "proposal_required"]
    proposal_refs_present = all(bool(turn.get("proposed_session_refs")) for turn in proposal_turns)
    turn_refs_present = all(str(turn.get("turn_ref") or "") in manifest_turn_refs for turn in scripted_turns)

    return {
        "ok": (
            latest_summary.get("conversation_id") == conversation_id
            and int(latest_summary.get("counts", {}).get("turns", 0) or 0) == len(scripted_turns)
            and turn_refs_present
            and voice_turn_match
            and proposal_refs_present
        ),
        "latest_summary_path": normalize_slashes(str(latest_summary_path.relative_to(ROOT))),
        "manifest_path": normalize_slashes(str(manifest_path.relative_to(ROOT))),
        "voice_view_turn_match": voice_turn_match,
        "manifest_contains_turn_refs": turn_refs_present,
        "proposal_refs_present": proposal_refs_present,
        "latest_summary": {
            "run_id": latest_summary.get("run_id"),
            "counts": latest_summary.get("counts"),
            "outcome": latest_summary.get("outcome"),
        },
        "voice_view": {
            "conversation_id": voice_payload.get("conversation_id"),
            "notifications_count": len(voice_payload.get("notifications", []))
            if isinstance(voice_payload.get("notifications"), list)
            else 0,
            "recent_turns": voice_recent_turns,
        },
        "manifest_summary": manifest.get("summary"),
    }


def build_receipt(
    *,
    conversation_id: str,
    base_url: str,
    prompts: list[str],
    stack_preflight: dict[str, Any],
    awareness_preflight: dict[str, Any],
    scripted_run: dict[str, Any] | None,
    read_model: dict[str, Any] | None,
) -> dict[str, Any]:
    deterministic_ok = (
        bool(stack_preflight.get("ok"))
        and bool(awareness_preflight.get("ok"))
        and isinstance(scripted_run, dict)
        and bool(scripted_run.get("ok"))
        and isinstance(read_model, dict)
        and bool(read_model.get("ok"))
    )
    return {
        "contract_version": RECEIPT_CONTRACT_VERSION,
        "generated_at": utc_now(),
        "conversation_id": conversation_id,
        "prompts": prompts,
        "preflight": {
            "stack": stack_preflight,
            "awareness": awareness_preflight,
        },
        "scripted_run": scripted_run,
        "read_model": read_model,
        "manual_gate": {
            "required": True,
            "status": "pending",
            "remaining_proof": "real human mic -> spoken response -> human barge-in interrupt -> clean continued state on the same conversation id",
            "stream_command": (
                f"python .\\ops\\atlas\\talk.py --base-url {base_url} "
                f"--auth-token <token> --conversation-id {conversation_id} --stream --print-partials"
            ),
        },
        "overall": {
            "deterministic_gate_ok": deterministic_ok,
            "release_gate_status": "pending_live_barge_in" if deterministic_ok else "blocked",
        },
    }
def receipt_paths(conversation_id: str) -> tuple[Path, Path]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = ROOT / "runtime" / "receipts" / "validation"
    latest = output_dir / f"voice-cert-{conversation_id}.latest.json"
    timestamped = output_dir / f"voice-cert-{conversation_id}-{timestamp}.json"
    return latest, timestamped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the deterministic half of the ATLAS daily voice certification gate.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--auth-token")
    parser.add_argument("--auth-token-file")
    parser.add_argument("--conversation-id", default="voice-daily-cert")
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--skip-scripted-run", action="store_true")
    parser.add_argument("--skip-read-model-check", action="store_true")
    parser.add_argument("--prompt", action="append", dest="prompts")
    args = parser.parse_args(argv)

    token = load_token(args)
    prompts = [prompt.strip() for prompt in (args.prompts or DEFAULT_PROMPTS) if isinstance(prompt, str) and prompt.strip()]

    stack_preflight = {"ok": True, "skipped": True}
    awareness_preflight = {"ok": True, "skipped": True}
    if not args.skip_preflight:
        stack_preflight = run_stack_preflight()
        awareness_preflight = run_awareness_preflight(args.base_url, token)

    scripted_run: dict[str, Any] | None = None
    if not args.skip_scripted_run:
        scripted_run = run_scripted_turns(
            prompts=prompts,
            conversation_id=args.conversation_id,
            base_url=args.base_url,
        )

    read_model: dict[str, Any] | None = None
    if (
        not args.skip_read_model_check
        and isinstance(scripted_run, dict)
        and scripted_run.get("ok")
        and bool(awareness_preflight.get("ok"))
    ):
        try:
            read_model = compare_read_model(
                conversation_id=args.conversation_id,
                base_url=args.base_url,
                token=token,
                scripted_turns=scripted_run.get("turns", []),
            )
        except Exception as exc:
            read_model = {
                "ok": False,
                "error": str(exc),
            }

    receipt = build_receipt(
        conversation_id=args.conversation_id,
        base_url=args.base_url,
        prompts=prompts,
        stack_preflight=stack_preflight,
        awareness_preflight=awareness_preflight,
        scripted_run=scripted_run,
        read_model=read_model,
    )
    latest_path, timestamped_path = receipt_paths(args.conversation_id)
    write_json(latest_path, receipt)
    write_json(timestamped_path, receipt)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["overall"]["release_gate_status"] == "pending_live_barge_in" else 1


if __name__ == "__main__":
    raise SystemExit(main())
