from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.cortex._artifacts import stable_json_digest


def _trim(text: str, limit: int = 220) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else f"{compact[: limit - 3]}..."


def _render_refs(refs: list[str]) -> str:
    ordered = [ref for ref in refs if isinstance(ref, str) and ref.strip()]
    return ", ".join(ordered[:4])


def _provider() -> dict[str, str]:
    return {
        "adapter": "deterministic-grounding-v1",
        "model": "atlas-grounded-rules",
    }


def compose_response(
    turn_context: dict[str, Any],
    *,
    proposed_session_refs: list[str] | None = None,
    authored_memory_refs: list[str] | None = None,
) -> dict[str, Any]:
    intent = str(turn_context.get("intent") or "status_overview")
    facts = turn_context.get("facts", {}) if isinstance(turn_context.get("facts"), dict) else {}
    refs = turn_context.get("retrieved_ref_set", {}) if isinstance(turn_context.get("retrieved_ref_set"), dict) else {}
    proposed_refs = [ref for ref in (proposed_session_refs or []) if isinstance(ref, str) and ref.strip()]
    memory_refs = [ref for ref in (authored_memory_refs or []) if isinstance(ref, str) and ref.strip()]
    text = "ATLAS grounded the turn but did not produce a specific response."

    if intent == "attention_overview":
        items = facts.get("attention", []) if isinstance(facts.get("attention"), list) else []
        if items:
            top = items[0] if isinstance(items[0], dict) else {}
            text = (
                f"{len(items)} attention items are open. Highest priority: "
                f"{top.get('summary') or top.get('kind') or 'attention'} "
                f"[refs: {_render_refs(refs.get('attention_refs', []))}]."
            )
        else:
            text = "No open attention items were returned from the awareness view."

    elif intent == "changes_today":
        changes = facts.get("changes_today", []) if isinstance(facts.get("changes_today"), list) else []
        if changes:
            first = changes[0] if isinstance(changes[0], dict) else {}
            text = (
                f"{len(changes)} observations were recorded today. "
                f"First change: {first.get('observation_type')} from {first.get('source_ref')}. "
                f"[refs: {_render_refs(refs.get('artifact_refs', []))}]"
            )
        else:
            text = "No world-model observations were recorded for today."

    elif intent == "active_initiatives":
        items = facts.get("initiatives", []) if isinstance(facts.get("initiatives"), list) else []
        if items:
            titles = ", ".join(
                str(item.get("title") or item.get("id"))
                for item in items[:3]
                if isinstance(item, dict)
            )
            text = f"Active initiatives: {titles}. [refs: {_render_refs(refs.get('initiative_refs', []))}]"
        else:
            text = "No active initiatives are currently surfaced."

    elif intent == "initiative_summary":
        initiative = facts.get("initiative")
        if isinstance(initiative, dict):
            text = (
                f"{initiative.get('title')}: {_trim(str(initiative.get('text') or initiative.get('title') or 'initiative'))} "
                f"[refs: {_render_refs(refs.get('initiative_refs', [])) or _render_refs(refs.get('memory_refs', []))}]."
            )
        else:
            text = "No matching initiative was found in the grounded search results."

    elif intent == "session_blocked_reason":
        session = facts.get("session")
        if isinstance(session, dict):
            manifest = session.get("manifest", {}) if isinstance(session.get("manifest"), dict) else {}
            resume = manifest.get("resume", {}) if isinstance(manifest.get("resume"), dict) else {}
            reason = resume.get("failure_reason") or resume.get("status") or manifest.get("session_state") or "blocked"
            text = (
                f"Session {session.get('session_id')} is currently constrained by '{reason}'. "
                f"[refs: {_render_refs(refs.get('session_refs', []))}]"
            )
        else:
            text = "No matching session was resolved for the blocked-session question."

    elif intent == "verta_trust_posture":
        text = (
            "Verta remains quarantined and metadata-only. No derived trust elevation was used in this turn. "
            f"[refs: {_render_refs(refs.get('knowledge_refs', []))}]"
        )

    elif intent in {"initiative_next_work", "request_resume_session", "request_read_only_scan"}:
        if proposed_refs:
            text = (
                "ATLAS authored a proposal-only next step instead of executing. "
                f"Proposed session refs: {_render_refs(proposed_refs)}."
            )
            if memory_refs:
                text += f" Memory refs: {_render_refs(memory_refs)}."
        else:
            text = "The turn requested action, but no proposal artifact was authored."

    else:
        status = facts.get("status", {}) if isinstance(facts.get("status"), dict) else {}
        active = status.get("active_session", {}) if isinstance(status.get("active_session"), dict) else {}
        initiatives = status.get("initiatives", {}) if isinstance(status.get("initiatives"), dict) else {}
        text = (
            f"ATLAS currently shows active_session={active.get('session_id') or 'none'} "
            f"and active_initiatives={initiatives.get('item_count', 0)}. "
            f"[refs: {_render_refs(refs.get('session_refs', []) + refs.get('initiative_refs', []))}]"
        )

    response_summary = _trim(text)
    return {
        "provider": _provider(),
        "response_text": text,
        "response_summary": response_summary,
        "response_digest": stable_json_digest(
            {
                "intent": intent,
                "response_summary": response_summary,
                "proposed_session_refs": proposed_refs,
                "authored_memory_refs": memory_refs,
            }
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compose a grounded ATLAS conversation response from a deterministic turn context.")
    parser.add_argument("--context-path", type=Path, required=True)
    args = parser.parse_args(argv)

    payload = json.loads(args.context_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Context payload must be a JSON object.")
    response = compose_response(payload)
    print(json.dumps(response, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
