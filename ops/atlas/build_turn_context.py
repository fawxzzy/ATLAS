from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.awareness import atlas_status, fetch, fetch_memory, fetch_session, list_attention, search
from ops.cortex._artifacts import stable_json_digest


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _slug(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return cleaned or "conversation"


def _trim(text: str, limit: int = 220) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else f"{compact[: limit - 3]}..."


def _unique(values: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        stripped = value.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        ordered.append(stripped)
    return ordered


def _parse_json_text(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _classify_intent(user_input: str) -> dict[str, Any]:
    normalized = _normalize(user_input)
    if normalized in {"what is active", "what's active", "what is going on", "what's going on", "active"}:
        return {"intent": "active_overview", "target": None, "action_mode": "informational"}
    if normalized in {"attention", "what needs attention"} or "needs attention" in normalized:
        return {"intent": "attention_overview", "target": None, "action_mode": "informational"}
    if "what changed today" in normalized or "changed today" in normalized:
        return {"intent": "changes_today", "target": None, "action_mode": "informational"}
    if "what initiatives are active" in normalized or normalized == "active initiatives":
        return {"intent": "active_initiatives", "target": None, "action_mode": "informational"}
    if "proposal" in normalized and "pending" in normalized:
        return {"intent": "pending_proposal", "target": None, "action_mode": "informational"}
    if "repo work" in normalized and ("blessing" in normalized or "review" in normalized):
        return {"intent": "repo_waiting_on_review", "target": None, "action_mode": "informational"}
    if normalized.startswith("summarize initiative "):
        return {
            "intent": "initiative_summary",
            "target": user_input.split("summarize initiative ", 1)[1].strip(),
            "action_mode": "informational",
        }
    if normalized.startswith("propose next work for initiative "):
        return {
            "intent": "initiative_next_work",
            "target": user_input.split("propose next work for initiative ", 1)[1].strip(),
            "action_mode": "proposal_required",
        }
    if normalized.startswith("why session ") and " blocked" in normalized:
        match = re.search(r"why session\s+(.+?)\s+is blocked", normalized)
        return {
            "intent": "session_blocked_reason",
            "target": match.group(1).strip() if match else None,
            "action_mode": "informational",
        }
    if "verta" in normalized and ("trust" in normalized or "posture" in normalized):
        return {"intent": "verta_trust_posture", "target": "personal--verta-core", "action_mode": "informational"}
    if normalized.startswith("run read-only scan on "):
        return {
            "intent": "request_read_only_scan",
            "target": user_input.split("run read-only scan on ", 1)[1].strip(),
            "action_mode": "proposal_required",
        }
    if normalized.startswith("resume paused session") or normalized.startswith("resume session"):
        parts = user_input.strip().split()
        requested = parts[-1] if len(parts) >= 3 else ""
        return {
            "intent": "request_resume_session",
            "target": requested or None,
            "action_mode": "proposal_required",
        }
    return {"intent": "status_overview", "target": None, "action_mode": "informational"}


def _empty_ref_set() -> dict[str, list[str]]:
    return {
        "inventory_refs": [],
        "attention_refs": [],
        "session_refs": [],
        "initiative_refs": [],
        "memory_refs": [],
        "knowledge_refs": [],
        "artifact_refs": [],
    }


def _register_ref(ref_set: dict[str, list[str]], bucket: str, ref: str | None) -> None:
    if isinstance(ref, str) and ref.strip():
        ref_set[bucket] = _unique([*ref_set[bucket], ref.strip()])


def _trace(surface: str, query: str, refs: list[str]) -> dict[str, Any]:
    ordered = sorted(_unique(refs))
    return {
        "surface": surface,
        "query": query,
        "ref_count": len(ordered),
        "sample_refs": ordered[:5],
    }


def _status_slices(status: dict[str, Any]) -> dict[str, Any]:
    return status.get("slices", {}) if isinstance(status.get("slices"), dict) else {}


def _register_initiative_item_refs(ref_set: dict[str, list[str]], item: dict[str, Any]) -> None:
    initiative_id = str(item.get("id") or "").strip()
    if initiative_id:
        _register_ref(ref_set, "initiative_refs", f"initiative:{initiative_id}")
    initiative_path = str(item.get("path") or "").strip()
    if initiative_path:
        _register_ref(ref_set, "memory_refs", initiative_path)
    proposal_ref = str(item.get("proposal_ref") or "").strip()
    if proposal_ref:
        _register_ref(ref_set, "artifact_refs", proposal_ref)
    for proposal_ref in item.get("proposed_next_session_refs", []):
        _register_ref(ref_set, "artifact_refs", str(proposal_ref))


def _register_trust_refs(ref_set: dict[str, list[str]], item: dict[str, Any]) -> None:
    source_ref = str(item.get("source_ref") or "").strip()
    if source_ref:
        _register_ref(ref_set, "artifact_refs", source_ref)
    knowledge_ref = str(item.get("knowledge_ref") or "").strip()
    if knowledge_ref:
        _register_ref(ref_set, "knowledge_refs", knowledge_ref)


def build_turn_context(
    user_input: str,
    *,
    root: Path | None = None,
    conversation_id: str | None = None,
    mode: str = "text",
    refresh: bool = False,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    classification = _classify_intent(user_input)
    intent = str(classification["intent"])
    target = classification.get("target")
    action_mode = str(classification["action_mode"])
    retrieved_ref_set = _empty_ref_set()
    query_trace: list[dict[str, Any]] = []
    facts: dict[str, Any] = {
        "conversation_id": conversation_id,
        "mode": mode,
        "intent": intent,
        "target": target,
    }

    if intent == "attention_overview":
        payload = list_attention(root=base_root, refresh=refresh, limit=8)
        items = payload.get("items", []) if isinstance(payload.get("items"), list) else []
        refs = [f"attention:{item.get('attention_id')}" for item in items if isinstance(item, dict)]
        for ref in refs:
            _register_ref(retrieved_ref_set, "attention_refs", ref)
        facts["attention"] = items
        query_trace.append(_trace("attention", "open attention items", refs))

    elif intent == "changes_today":
        snapshot = fetch("artifact:runtime/state/atlas/world-model.snapshot.latest.json", root=base_root, refresh=refresh)
        snapshot_json = json.loads(snapshot["text"])
        changes = [
            item
            for item in snapshot_json.get("observations", [])
            if isinstance(item, dict)
            and isinstance(item.get("observed_at"), str)
            and str(item.get("observed_at")).startswith(str(datetime.now(timezone.utc).date().isoformat()))
        ]
        refs = [str(item.get("source_ref")) for item in changes if isinstance(item.get("source_ref"), str)]
        for ref in refs:
            _register_ref(retrieved_ref_set, "artifact_refs", ref)
        facts["changes_today"] = changes
        query_trace.append(_trace("snapshot", "today observations", refs))

    elif intent == "active_initiatives":
        status = atlas_status(root=base_root, refresh=refresh)
        initiatives = _status_slices(status).get("active_initiatives", [])
        refs: list[str] = []
        for item in initiatives if isinstance(initiatives, list) else []:
            if not isinstance(item, dict):
                continue
            _register_initiative_item_refs(retrieved_ref_set, item)
            if item.get("id"):
                refs.append(f"initiative:{item.get('id')}")
        facts["initiatives"] = initiatives
        query_trace.append(_trace("status", "active initiatives", refs))

    elif intent == "active_overview":
        status = atlas_status(root=base_root, refresh=refresh)
        slices = _status_slices(status)
        active_items = slices.get("active_initiatives", []) if isinstance(slices.get("active_initiatives"), list) else []
        waiting_items = slices.get("waiting_on_review", []) if isinstance(slices.get("waiting_on_review"), list) else []
        pending_items = slices.get("pending_proposals", []) if isinstance(slices.get("pending_proposals"), list) else []
        trust_posture = slices.get("trust_posture", {}) if isinstance(slices.get("trust_posture"), dict) else {}
        refs: list[str] = []
        for bucket in (active_items, waiting_items, pending_items):
            for item in bucket:
                if not isinstance(item, dict):
                    continue
                _register_initiative_item_refs(retrieved_ref_set, item)
                if item.get("id"):
                    refs.append(f"initiative:{item.get('id')}")
        for item in trust_posture.get("items", []) if isinstance(trust_posture.get("items"), list) else []:
            if not isinstance(item, dict):
                continue
            _register_trust_refs(retrieved_ref_set, item)
            if item.get("knowledge_ref"):
                refs.append(str(item.get("knowledge_ref")))
        facts["status"] = status
        facts["active_initiatives"] = active_items
        facts["waiting_on_review"] = waiting_items
        facts["pending_proposals"] = pending_items
        facts["trust_posture"] = trust_posture
        query_trace.append(_trace("status", "active overview", refs))

    elif intent == "pending_proposal":
        status = atlas_status(root=base_root, refresh=refresh)
        pending_items = _status_slices(status).get("pending_proposals", [])
        refs: list[str] = []
        for item in pending_items if isinstance(pending_items, list) else []:
            if not isinstance(item, dict):
                continue
            _register_initiative_item_refs(retrieved_ref_set, item)
            if item.get("id"):
                refs.append(f"initiative:{item.get('id')}")
        facts["pending_proposals"] = pending_items
        facts["status"] = status
        query_trace.append(_trace("status", "pending proposals", refs))

    elif intent == "repo_waiting_on_review":
        status = atlas_status(root=base_root, refresh=refresh)
        filtered = _status_slices(status).get("waiting_on_review", [])
        refs = []
        for item in filtered if isinstance(filtered, list) else []:
            identifier = str(item.get("id") or "").strip()
            if not identifier:
                continue
            refs.append(f"initiative:{identifier}")
            _register_initiative_item_refs(retrieved_ref_set, item)
        facts["repo_waiting"] = filtered
        query_trace.append(_trace("status", "repo work waiting on blessing or review", refs))

    elif intent in {"initiative_summary", "initiative_next_work"}:
        query = str(target or "").strip()
        results = search(query, root=base_root, refresh=refresh, limit=8)
        candidates = [
            item
            for item in results.get("results", [])
            if isinstance(item, dict) and str(item.get("metadata", {}).get("source_kind")) == "initiative"
        ]
        if candidates:
            selected = candidates[0]
            initiative_id = str(selected.get("id", "")).split(":", 1)[-1]
            initiative_payload = fetch_memory(initiative_id, root=base_root, refresh=refresh)
            _register_ref(retrieved_ref_set, "initiative_refs", f"initiative:{initiative_id}")
            _register_ref(retrieved_ref_set, "memory_refs", str(initiative_payload.get("metadata", {}).get("path")))
            facts["initiative"] = initiative_payload
            facts["initiative_document"] = _parse_json_text(initiative_payload.get("text"))
            try:
                proposal_payload = fetch(f"proposal:{initiative_id}", root=base_root, refresh=refresh)
            except FileNotFoundError:
                proposal_payload = None
            if isinstance(proposal_payload, dict):
                facts["proposal"] = proposal_payload
                _register_ref(retrieved_ref_set, "artifact_refs", str(proposal_payload.get("metadata", {}).get("proposal_ref")))
            query_trace.append(_trace("search", query, [str(item.get("id")) for item in candidates]))
        else:
            facts["initiative"] = None
            facts["initiative_document"] = None
            facts["proposal"] = None
            query_trace.append(_trace("search", query, []))

    elif intent == "session_blocked_reason":
        session_id = str(target or "").strip()
        session_payload = fetch_session(session_id, root=base_root, refresh=refresh)
        _register_ref(retrieved_ref_set, "session_refs", f"session:{session_id}")
        manifest_ref = session_payload.get("manifest_ref")
        _register_ref(retrieved_ref_set, "artifact_refs", str(manifest_ref) if isinstance(manifest_ref, str) else None)
        facts["session"] = session_payload
        query_trace.append(_trace("session", session_id, [f"session:{session_id}", str(manifest_ref or "")]))

    elif intent == "verta_trust_posture":
        status = atlas_status(root=base_root, refresh=refresh)
        trust_posture = _status_slices(status).get("trust_posture", {})
        items = [
            item
            for item in trust_posture.get("items", [])
            if isinstance(item, dict) and "verta" in str(item.get("archive_id") or "").lower()
        ] if isinstance(trust_posture, dict) else []
        refs: list[str] = []
        for item in items:
            _register_trust_refs(retrieved_ref_set, item)
            if item.get("knowledge_ref"):
                refs.append(str(item.get("knowledge_ref")))
        facts["trust_posture"] = trust_posture
        facts["trust_items"] = items
        query_trace.append(_trace("status", "verta trust posture", refs))

    elif intent == "request_resume_session":
        snapshot = fetch("artifact:runtime/state/atlas/world-model.snapshot.latest.json", root=base_root, refresh=refresh)
        snapshot_json = json.loads(snapshot["text"])
        requested = str(target or "").strip()
        resumable = [
            item
            for item in snapshot_json.get("inventory_entries", [])
            if isinstance(item, dict)
            and str(item.get("entry_type")) == "session"
            and str(item.get("status")) == "resume_ready"
        ]
        selected = None
        for item in resumable:
            if requested and str(item.get("key")) == requested:
                selected = item
                break
        if selected is None and resumable:
            selected = resumable[0]
        if isinstance(selected, dict):
            session_id = str(selected.get("key"))
            session_payload = fetch_session(session_id, root=base_root, refresh=refresh)
            _register_ref(retrieved_ref_set, "session_refs", f"session:{session_id}")
            _register_ref(retrieved_ref_set, "artifact_refs", str(session_payload.get("manifest_ref")))
            facts["session"] = session_payload
            query_trace.append(_trace("inventory", "resume_ready sessions", [f"session:{session_id}"]))
        else:
            facts["session"] = None
            query_trace.append(_trace("inventory", "resume_ready sessions", []))

    elif intent == "request_read_only_scan":
        query = str(target or "").strip()
        results = search(query, root=base_root, refresh=refresh, limit=6)
        refs = [str(item.get("id")) for item in results.get("results", []) if isinstance(item, dict)]
        for ref in refs:
            if ref.startswith("session:"):
                _register_ref(retrieved_ref_set, "session_refs", ref)
            elif ref.startswith("initiative:"):
                _register_ref(retrieved_ref_set, "initiative_refs", ref)
            elif ref.startswith("memory:"):
                _register_ref(retrieved_ref_set, "memory_refs", ref)
            elif ref.startswith("attention:"):
                _register_ref(retrieved_ref_set, "attention_refs", ref)
            elif ref.startswith("knowledge:"):
                _register_ref(retrieved_ref_set, "knowledge_refs", ref)
        facts["search_results"] = results.get("results", [])
        query_trace.append(_trace("search", query, refs))

    else:
        status = atlas_status(root=base_root, refresh=refresh)
        slices = _status_slices(status)
        active_items = slices.get("active_initiatives", []) if isinstance(slices.get("active_initiatives"), list) else []
        waiting_items = slices.get("waiting_on_review", []) if isinstance(slices.get("waiting_on_review"), list) else []
        pending_items = slices.get("pending_proposals", []) if isinstance(slices.get("pending_proposals"), list) else []
        trust_posture = slices.get("trust_posture", {}) if isinstance(slices.get("trust_posture"), dict) else {}
        active_session = status.get("active_session") if isinstance(status.get("active_session"), dict) else None
        for bucket in (waiting_items, pending_items, active_items):
            for item in bucket:
                if not isinstance(item, dict):
                    continue
                _register_initiative_item_refs(retrieved_ref_set, item)
        for item in trust_posture.get("items", []) if isinstance(trust_posture.get("items"), list) else []:
            if not isinstance(item, dict):
                continue
            _register_trust_refs(retrieved_ref_set, item)
        if not any(retrieved_ref_set.values()) and isinstance(active_session, dict) and active_session.get("session_id"):
            _register_ref(retrieved_ref_set, "session_refs", f"session:{active_session.get('session_id')}")
        facts["status"] = status
        facts["active_initiatives"] = active_items
        facts["waiting_on_review"] = waiting_items
        facts["pending_proposals"] = pending_items
        facts["trust_posture"] = trust_posture
        query_trace.append(
            _trace(
                "status",
                "status overview",
                [
                    *retrieved_ref_set["initiative_refs"],
                    *retrieved_ref_set["artifact_refs"],
                    *retrieved_ref_set["knowledge_refs"],
                    *retrieved_ref_set["session_refs"],
                ],
            )
        )

    input_summary = _trim(user_input)
    body = {
        "conversation_id": conversation_id or f"{mode}-{_slug(user_input)}",
        "mode": mode,
        "intent": intent,
        "target": target,
        "action_mode": action_mode,
        "input_summary": input_summary,
        "retrieved_ref_set": {
            key: sorted(_unique(value))
            for key, value in retrieved_ref_set.items()
        },
        "facts": facts,
        "query_trace": query_trace,
    }
    body["context_digest"] = stable_json_digest(body)
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the deterministic ATLAS turn context for a conversation input.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--conversation-id")
    parser.add_argument("--mode", choices=["text", "voice"], default="text")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args(argv)

    payload = build_turn_context(
        args.input,
        root=atlas_root(),
        conversation_id=args.conversation_id,
        mode=args.mode,
        refresh=args.refresh,
    )
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
