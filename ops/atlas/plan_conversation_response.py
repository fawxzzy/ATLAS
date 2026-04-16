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


def _first_item(items: Any) -> dict[str, Any] | None:
    if not isinstance(items, list):
        return None
    for item in items:
        if isinstance(item, dict):
            return item
    return None


def _initiative_title(item: dict[str, Any] | None) -> str:
    if not isinstance(item, dict):
        return "initiative"
    return str(item.get("title") or item.get("id") or "initiative")


def _initiative_attention(item: dict[str, Any] | None) -> str:
    if not isinstance(item, dict):
        return ""
    return str(item.get("attention_summary") or "").strip()


def _trust_posture_line(trust_posture: dict[str, Any], *, prefer_verta: bool = False) -> str:
    items = trust_posture.get("items", []) if isinstance(trust_posture.get("items"), list) else []
    first = None
    if prefer_verta:
        first = next(
            (
                item
                for item in items
                if isinstance(item, dict) and "verta" in str(item.get("archive_id") or "").lower()
            ),
            None,
        )
    if first is None:
        first = _first_item(items)
    if prefer_verta and not isinstance(first, dict):
        return ""
    if not isinstance(first, dict):
        return ""
    archive_id = str(first.get("archive_id") or "knowledge surface")
    read_mode = str(first.get("read_mode") or "metadata_only").replace("_", "-")
    return f"{archive_id} remains {read_mode} and untrusted."


def _trust_posture_ref(trust_posture: dict[str, Any], *, prefer_verta: bool = False) -> str | None:
    items = trust_posture.get("items", []) if isinstance(trust_posture.get("items"), list) else []
    selected = None
    if prefer_verta:
        selected = next(
            (
                item
                for item in items
                if isinstance(item, dict) and "verta" in str(item.get("archive_id") or "").lower()
            ),
            None,
        )
    if selected is None:
        selected = _first_item(items)
    if not isinstance(selected, dict):
        return None
    for key in ("knowledge_ref", "source_ref"):
        value = str(selected.get(key) or "").strip()
        if value:
            return value
    return None


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
            summaries = []
            for item in items[:3]:
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title") or item.get("id") or "initiative")
                next_refs = item.get("proposed_next_session_refs", [])
                if isinstance(next_refs, list) and next_refs:
                    summaries.append(f"{title} (proposal ready)")
                else:
                    summaries.append(title)
            text = f"Active initiatives: {', '.join(summaries)}. [refs: {_render_refs(refs.get('initiative_refs', []))}]"
        else:
            text = "No active initiatives are currently surfaced."

    elif intent == "active_overview":
        waiting = facts.get("waiting_on_review", []) if isinstance(facts.get("waiting_on_review"), list) else []
        pending = facts.get("pending_proposals", []) if isinstance(facts.get("pending_proposals"), list) else []
        active = facts.get("active_initiatives", []) if isinstance(facts.get("active_initiatives"), list) else []
        trust_posture = facts.get("trust_posture", {}) if isinstance(facts.get("trust_posture"), dict) else {}
        lead = _first_item(waiting) or _first_item(pending) or _first_item(active)
        trust_line = _trust_posture_line(trust_posture, prefer_verta=True)
        if isinstance(lead, dict):
            summary = _initiative_attention(lead) or f"{_initiative_title(lead)} is the current active initiative."
            proposal_ref = str(lead.get("proposal_ref") or "").strip()
            ref_sample = []
            initiative_ref = str(lead.get("id") or "").strip()
            if initiative_ref:
                ref_sample.append(f"initiative:{initiative_ref}")
            if proposal_ref:
                ref_sample.append(proposal_ref)
            trust_ref = _trust_posture_ref(trust_posture, prefer_verta=True)
            if trust_line and trust_ref:
                ref_sample.append(trust_ref)
            text = f"Active work is centered on {_initiative_title(lead)}. {summary}"
            if proposal_ref:
                text += f" Pending proposal: {proposal_ref}."
            if trust_line:
                text += f" {trust_line}"
            text += f" [refs: {_render_refs(ref_sample or refs.get('initiative_refs', []))}]"
        elif trust_line:
            trust_ref = _trust_posture_ref(trust_posture, prefer_verta=True)
            text = f"No active initiative slice is currently populated. {trust_line} [refs: {_render_refs([trust_ref] if trust_ref else refs.get('knowledge_refs', []))}]"
        else:
            text = "No active initiative or proposal slice is currently populated."

    elif intent == "pending_proposal":
        items = facts.get("pending_proposals", []) if isinstance(facts.get("pending_proposals"), list) else []
        first = _first_item(items)
        if isinstance(first, dict):
            next_step = str(first.get("next_step") or "").strip()
            proposal_ref = str(first.get("proposal_ref") or "").strip()
            text = f"Pending proposal: {_initiative_title(first)}."
            if next_step:
                text += f" Next proposed work: {next_step}."
            if proposal_ref:
                text += f" Proposal ref: {proposal_ref}."
            text += f" It remains proposal-only. [refs: {_render_refs(refs.get('initiative_refs', []) + refs.get('artifact_refs', []))}]"
        else:
            text = "No pending proposal slice is currently populated."

    elif intent == "repo_waiting_on_review":
        items = facts.get("repo_waiting", []) if isinstance(facts.get("repo_waiting"), list) else []
        if items:
            first = items[0] if isinstance(items[0], dict) else {}
            repo_refs = first.get("repo_refs", []) if isinstance(first.get("repo_refs"), list) else []
            proposal_ref = str(first.get("proposal_ref") or "").strip()
            text = (
                f"Repo-linked work waiting on blessing or review: {first.get('title') or first.get('id')}. "
                f"{first.get('attention_summary') or 'Operator review is still pending.'} "
                f"{f'Pending proposal: {proposal_ref}. ' if proposal_ref else ''}"
                f"[refs: {_render_refs(refs.get('initiative_refs', []) + refs.get('artifact_refs', []) + repo_refs)}]"
            )
        else:
            text = "No repo-linked initiatives currently advertise blessing or review follow-up."

    elif intent == "initiative_summary":
        initiative = facts.get("initiative")
        initiative_document = facts.get("initiative_document") if isinstance(facts.get("initiative_document"), dict) else {}
        proposal = facts.get("proposal") if isinstance(facts.get("proposal"), dict) else {}
        metadata = initiative_document.get("metadata", {}) if isinstance(initiative_document.get("metadata"), dict) else {}
        if isinstance(initiative, dict):
            next_step = str(metadata.get("next_step") or "").strip()
            follow_up = str(metadata.get("follow_up") or "").strip()
            tail = []
            if next_step:
                tail.append(f"Next: {next_step}.")
            if follow_up:
                tail.append(f"After that: {follow_up}.")
            proposal_ref = str(proposal.get("metadata", {}).get("proposal_ref") or "").strip() if isinstance(proposal.get("metadata"), dict) else ""
            if proposal_ref:
                tail.append(f"Proposal remains at {proposal_ref}.")
            text = (
                f"{initiative.get('title')}: {initiative_document.get('summary') or initiative.get('title') or 'initiative'} "
                f"{' '.join(tail)} "
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
        trust_items = facts.get("trust_items", []) if isinstance(facts.get("trust_items"), list) else []
        first = _first_item(trust_items)
        text = (
            f"{str(first.get('archive_id') or 'Verta')} remains quarantined and metadata-only. "
            "No derived trust elevation was used in this turn. "
            f"[refs: {_render_refs(refs.get('knowledge_refs', []) + refs.get('artifact_refs', []))}]"
        )

    elif intent in {"initiative_next_work", "request_resume_session", "request_read_only_scan"}:
        initiative_document = facts.get("initiative_document") if isinstance(facts.get("initiative_document"), dict) else {}
        metadata = initiative_document.get("metadata", {}) if isinstance(initiative_document.get("metadata"), dict) else {}
        if proposed_refs:
            next_step = str(metadata.get("next_step") or turn_context.get("target") or "").strip()
            text = (
                "ATLAS authored a proposal-only next step instead of executing. "
                f"{f'Next step: {next_step}. ' if next_step else ''}"
                f"Proposed session refs: {_render_refs(proposed_refs)}."
            )
            if memory_refs:
                text += f" Memory refs: {_render_refs(memory_refs)}."
        else:
            text = "The turn requested action, but no proposal artifact was authored."

    else:
        status = facts.get("status", {}) if isinstance(facts.get("status"), dict) else {}
        waiting = facts.get("waiting_on_review", []) if isinstance(facts.get("waiting_on_review"), list) else []
        pending = facts.get("pending_proposals", []) if isinstance(facts.get("pending_proposals"), list) else []
        active_items = facts.get("active_initiatives", []) if isinstance(facts.get("active_initiatives"), list) else []
        trust_posture = facts.get("trust_posture", {}) if isinstance(facts.get("trust_posture"), dict) else {}
        active_session = status.get("active_session", {}) if isinstance(status.get("active_session"), dict) else {}
        lead = _first_item(waiting) or _first_item(pending) or _first_item(active_items)
        trust_line = _trust_posture_line(trust_posture, prefer_verta=True)
        if isinstance(lead, dict):
            summary = _initiative_attention(lead) or f"{_initiative_title(lead)} is currently active."
            text = f"{summary}"
            proposal_ref = str(lead.get("proposal_ref") or "").strip()
            ref_sample = []
            initiative_ref = str(lead.get("id") or "").strip()
            if initiative_ref:
                ref_sample.append(f"initiative:{initiative_ref}")
            if proposal_ref:
                text += f" Pending proposal: {proposal_ref}."
                ref_sample.append(proposal_ref)
            if trust_line:
                text += f" {trust_line}"
                trust_ref = _trust_posture_ref(trust_posture, prefer_verta=True)
                if trust_ref:
                    ref_sample.append(trust_ref)
            text += f" [refs: {_render_refs(ref_sample or refs.get('initiative_refs', []))}]"
        elif isinstance(active_session, dict) and active_session.get("session_id"):
            text = (
                f"ATLAS currently shows session {active_session.get('session_id')} in state "
                f"{active_session.get('session_state') or active_session.get('final_status') or 'unknown'}. "
                f"[refs: {_render_refs(refs.get('session_refs', []))}]"
            )
        elif trust_line:
            trust_ref = _trust_posture_ref(trust_posture, prefer_verta=True)
            text = f"{trust_line} [refs: {_render_refs([trust_ref] if trust_ref else refs.get('knowledge_refs', []) + refs.get('artifact_refs', []))}]"
        else:
            text = "ATLAS grounded the turn but no active initiative, proposal, or session slice is currently populated."

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
