from __future__ import annotations

import argparse
from html import escape
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.awareness import cockpit_status
from ops.atlas.http_boundary import (
    authenticate_bearer,
    enforce_remote_bind_policy,
    load_auth_tokens,
    load_optional_token,
)

DEFAULT_REFRESH_SECONDS = 60


def _normalize_awareness_endpoint(value: str) -> str:
    normalized = value.rstrip("/")
    return normalized if normalized.endswith("/atlas/cockpit") else f"{normalized}/atlas/cockpit"


def _fetch_remote_cockpit(endpoint: str, *, auth_token: str | None, refresh: bool) -> dict[str, Any]:
    separator = "&" if "?" in endpoint else "?"
    url = f"{endpoint}{separator}{urlencode({'refresh': 'true' if refresh else 'false'})}"
    headers = {"Accept": "application/json"}
    if isinstance(auth_token, str) and auth_token.strip():
        headers["Authorization"] = f"Bearer {auth_token.strip()}"
    try:
        with urlopen(Request(url, headers=headers), timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"Awareness API returned HTTP {exc.code}.") from exc
    except URLError as exc:
        raise RuntimeError(f"Unable to reach Awareness API: {exc.reason}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Awareness API returned a non-object cockpit payload.")
    return payload


def _state_tone(value: Any) -> str:
    if value is None or value == "" or value == []:
        return "neutral"
    text = str(value).strip().lower()
    if text in {"frozen", "clear", "active", "pending_manual_review", "true"}:
        return "ok"
    if text in {"pending", "medium", "adjacent", "drifted", "restricted", "metadata_only"}:
        return "warn"
    if text in {"error", "failed", "critical", "high", "untrusted", "missing", "false"}:
        return "danger"
    return "neutral"


def _normalized_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def _bool_tone(value: Any, *, truthy: str, falsy: str, unknown: str = "neutral") -> str:
    normalized = _normalized_bool(value)
    if normalized is None:
        return unknown
    return truthy if normalized else falsy


def _count_tone(value: Any, *, zero: str, nonzero: str, unknown: str = "neutral") -> str:
    if value is None or value == "":
        return unknown
    try:
        count = int(value)
    except (TypeError, ValueError):
        return _state_tone(value)
    return zero if count == 0 else nonzero


def _badge(label: str, value: Any, *, tone: str | None = None) -> str:
    if value is None or value == "" or value == []:
        return ""
    return f'<span class="badge {tone or _state_tone(value)}">{escape(label)}: {escape(str(value))}</span>'


def _metric(label: str, value: Any, *, tone: str | None = None) -> str:
    return (
        f"<div class='metric'><div class='label'>{escape(label)}</div>"
        f"<div class='value {tone or _state_tone(value)}'>{escape(str(value))}</div></div>"
    )


def _pairs(rows: list[tuple[str, Any]]) -> str:
    parts = []
    for key, value in rows:
        if value is None or value == "" or value == []:
            continue
        rendered = ", ".join(str(item) for item in value) if isinstance(value, list) else str(value)
        parts.append(f"<div class='k'>{escape(key)}</div><div>{escape(rendered)}</div>")
    return f"<div class='pairs'>{''.join(parts)}</div>" if parts else ""


def _stack(items: list[str], empty_text: str) -> str:
    return "".join(items) if items else f"<div class='empty'>{escape(empty_text)}</div>"


def _item(title: str, eyebrow: str | None = None, badges: list[str] | None = None, body: str = "", featured: bool = False) -> str:
    classes = "item featured" if featured else "item"
    return (
        f"<div class='{classes}'>"
        f"{f'<div class=\"eyebrow\">{escape(eyebrow)}</div>' if eyebrow else ''}"
        f"<div class='title'>{escape(title)}</div>"
        f"{''.join(badges or [])}"
        f"{body}"
        "</div>"
    )


def _card(title: str, body: str, width: str = "span-12") -> str:
    return f"<section class='card {width}'><h2>{escape(title)}</h2>{body}</section>"


def _render_html(payload: dict[str, Any], *, refresh_seconds: int) -> str:
    overview = payload.get("overview", {}) if isinstance(payload.get("overview"), dict) else {}
    session = payload.get("conversation_state", {}) if isinstance(payload.get("conversation_state"), dict) else {}
    active_session = session.get("active_session", {}) if isinstance(session.get("active_session"), dict) else {}
    conversations = session.get("conversations", {}) if isinstance(session.get("conversations"), dict) else {}
    active_initiatives = payload.get("active_initiatives", {}) if isinstance(payload.get("active_initiatives"), dict) else {}
    attention = payload.get("attention_queue", {}) if isinstance(payload.get("attention_queue"), dict) else {}
    review = payload.get("review_queue", {}) if isinstance(payload.get("review_queue"), dict) else {}
    latest_proposal = payload.get("latest_governed_proposal", {}) if isinstance(payload.get("latest_governed_proposal"), dict) else {}
    proposal_only = payload.get("proposal_only_state", {}) if isinstance(payload.get("proposal_only_state"), dict) else {}
    playbook = payload.get("playbook_convergence", {}) if isinstance(payload.get("playbook_convergence"), dict) else {}
    playbook_contract = playbook.get("contract_source", {}) if isinstance(playbook.get("contract_source"), dict) else {}
    playbook_summary = playbook.get("summary", {}) if isinstance(playbook.get("summary"), dict) else {}
    continuity = payload.get("continuity", {}) if isinstance(payload.get("continuity"), dict) else {}
    continuity_coverage = continuity.get("coverage", {}) if isinstance(continuity.get("coverage"), dict) else {}
    continuity_promotion_queue = continuity.get("promotion_queue", {}) if isinstance(continuity.get("promotion_queue"), dict) else {}
    continuity_source_groups = continuity.get("source_groups", {}) if isinstance(continuity.get("source_groups"), dict) else {}
    repo_inventory = payload.get("repo_inventory", {}) if isinstance(payload.get("repo_inventory"), dict) else {}
    lock_hygiene = payload.get("lock_worktree_hygiene", {}) if isinstance(payload.get("lock_worktree_hygiene"), dict) else {}
    trust = payload.get("trust_posture", {}) if isinstance(payload.get("trust_posture"), dict) else {}
    featured_paths = payload.get("featured_paths", []) if isinstance(payload.get("featured_paths"), list) else []

    metrics = "".join(
        [
            _metric("Conversations", overview.get("active_conversation_count", "—")),
            _metric("Initiatives", overview.get("active_initiative_count", "—")),
            _metric(
                "Attention",
                overview.get("attention_item_count", "—"),
                tone=_count_tone(overview.get("attention_item_count"), zero="ok", nonzero="warn"),
            ),
            _metric(
                "Review Queue",
                overview.get("review_queue_count", "—"),
                tone=_count_tone(overview.get("review_queue_count"), zero="ok", nonzero="warn"),
            ),
            _metric(
                "Pending Proposals",
                overview.get("pending_proposal_count", "—"),
                tone=_count_tone(overview.get("pending_proposal_count"), zero="ok", nonzero="warn"),
            ),
            _metric(
                "Lock Frozen",
                overview.get("lock_frozen", "—"),
                tone=_bool_tone(overview.get("lock_frozen"), truthy="ok", falsy="danger"),
            ),
            _metric(
                "Dirty Repos",
                overview.get("dirty_repo_count", "—"),
                tone=_count_tone(overview.get("dirty_repo_count"), zero="ok", nonzero="danger"),
            ),
            _metric("Playbook Repos", overview.get("playbook_repo_count", "—")),
            _metric(
                "Playbook Drift",
                overview.get("playbook_non_green_count", "—"),
                tone=_count_tone(overview.get("playbook_non_green_count"), zero="ok", nonzero="warn"),
            ),
            _metric(
                "Continuity Review",
                overview.get("continuity_pending_review_count", "—"),
                tone=_count_tone(overview.get("continuity_pending_review_count"), zero="ok", nonzero="warn"),
            ),
            _metric(
                "Verta Visible",
                overview.get("verta_visible_untrusted", "—"),
                tone=_bool_tone(overview.get("verta_visible_untrusted"), truthy="warn", falsy="danger"),
            ),
        ]
    )

    session_items = [
        _item(
            active_session.get("task_id") or active_session.get("scenario") or "No active session",
            eyebrow=active_session.get("session_id"),
            badges=[
                _badge("state", active_session.get("session_state")),
                _badge("resume", active_session.get("resume_status")),
                _badge("mode", active_session.get("automation_level")),
            ],
            body=_pairs(
                [
                    ("worker", active_session.get("worker_id")),
                    ("assignment", active_session.get("assignment_id")),
                    ("initiative", active_session.get("initiative_ref")),
                    ("updated", active_session.get("updated_at")),
                ]
            ),
        )
        if active_session
        else "<div class='empty'>No active session is published.</div>"
    ]
    session_items.extend(
        _item(
            item.get("conversation_id") or "conversation",
            badges=[
                _badge("status", item.get("status")),
                _badge("mode", item.get("mode")),
                _badge(
                    "turns",
                    item.get("turn_count"),
                    tone=_count_tone(item.get("turn_count"), zero="warn", nonzero="ok"),
                ),
            ],
            body=_pairs(
                [
                    ("last_turn", item.get("last_turn_at")),
                    ("initiative_refs", item.get("active_initiative_refs", [])),
                    ("session_refs", item.get("active_session_refs", [])),
                ]
            ),
        )
        for item in (conversations.get("recent_items", []) if isinstance(conversations.get("recent_items"), list) else [])[:4]
        if isinstance(item, dict)
    )

    initiative_items = [
        _item(
            item.get("title") or item.get("id") or "initiative",
            eyebrow=item.get("id"),
            badges=[
                _badge("status", item.get("status")),
                _badge("blessing", item.get("blessing_state")),
                _badge("branch", item.get("branch_ref")),
            ],
            body=(f"<p>{escape(str(item.get('summary') or item.get('attention_summary') or ''))}</p>" + _pairs(
                [
                    ("next_step", item.get("next_step")),
                    ("follow_up", item.get("follow_up")),
                    ("waiting_on", item.get("waiting_on", [])),
                    ("repo_refs", item.get("repo_refs", [])),
                    ("proposal_ref", item.get("proposal_ref")),
                ]
            )),
        )
        for item in (active_initiatives.get("items", []) if isinstance(active_initiatives.get("items"), list) else [])[:6]
        if isinstance(item, dict)
    ]

    attention_items = [
        _item(
            item.get("summary") or item.get("kind") or "attention",
            eyebrow=item.get("kind"),
            badges=[_badge("severity", item.get("severity")), _badge("source", item.get("source_ref"))],
        )
        for item in (attention.get("items", []) if isinstance(attention.get("items"), list) else [])[:8]
        if isinstance(item, dict)
    ]

    review_items = [
        _item(
            item.get("title") or item.get("id") or "review",
            eyebrow=item.get("id"),
            badges=[_badge("blessing", item.get("blessing_state")), _badge("next", item.get("next_step"))],
            body=_pairs(
                [
                    ("follow_up", item.get("follow_up")),
                    ("waiting_on", item.get("waiting_on", [])),
                    ("repo_refs", item.get("repo_refs", [])),
                ]
            ),
        )
        for item in (review.get("items", []) if isinstance(review.get("items"), list) else [])[:6]
        if isinstance(item, dict)
    ]

    proposal_body = (
        _item(
            latest_proposal.get("title") or "No governed proposal pending",
            eyebrow=latest_proposal.get("session_id") or latest_proposal.get("proposal_ref"),
            badges=[
                _badge("state", latest_proposal.get("session_state")),
                _badge("scenario", latest_proposal.get("scenario")),
                _badge("blessing", latest_proposal.get("blessing_state")),
            ],
            body=_pairs(
                [
                    ("initiative", latest_proposal.get("initiative_id")),
                    ("initiative_title", latest_proposal.get("initiative_title")),
                    ("proposal_ref", latest_proposal.get("proposal_ref")),
                    ("updated", latest_proposal.get("updated_at")),
                    ("next_step", latest_proposal.get("next_step")),
                    ("follow_up", latest_proposal.get("follow_up")),
                    ("repo_refs", latest_proposal.get("repo_refs", [])),
                ]
            ),
            featured=bool(latest_proposal),
        )
        if latest_proposal
        else "<div class='empty'>No governed proposal is currently pending.</div>"
    )
    proposal_body += _stack(
        [
            _item(
                item.get("summary") or "proposal-only state",
                eyebrow=item.get("turn_id") or item.get("source_ref"),
                badges=[_badge("severity", item.get("severity")), _badge("intent", item.get("intent"))],
                body=_pairs([("conversation", item.get("conversation_id")), ("source_ref", item.get("source_ref"))]),
            )
            for item in (proposal_only.get("items", []) if isinstance(proposal_only.get("items"), list) else [])
            if isinstance(item, dict)
        ],
        "No proposal-only conversation state is pending.",
    )

    path_items = [
        _item(
            item.get("title") or item.get("initiative_id") or "operator path",
            eyebrow=item.get("initiative_id"),
            badges=[
                _badge("branch", item.get("branch_ref")),
                _badge("blessing", item.get("blessing_state")),
                _badge("next", item.get("next_step")),
            ],
            body=_pairs(
                [
                    ("initiative_ref", item.get("initiative_ref")),
                    ("attention", item.get("attention", {}).get("summary") if isinstance(item.get("attention"), dict) else None),
                    ("proposal_session", item.get("proposal_session", {}).get("session_id") if isinstance(item.get("proposal_session"), dict) else None),
                    ("proposal_ref", item.get("proposal_session", {}).get("proposal_ref") if isinstance(item.get("proposal_session"), dict) else None),
                    ("waiting_on", item.get("waiting_on", [])),
                    ("repo_refs", item.get("repo_refs", [])),
                ]
            ),
            featured=str(item.get("initiative_id", "")).strip() == "initiative-mazer-d2-learning-scorer",
        )
        for item in featured_paths[:6]
        if isinstance(item, dict)
    ]

    repo_items = [
        _item(
            item.get("logical_id") or item.get("local_path") or "repo",
            badges=[
                _badge("branch", item.get("branch")),
                _badge("dirty", item.get("dirty"), tone=_bool_tone(item.get("dirty"), truthy="danger", falsy="ok")),
                _badge("trust", item.get("trust_class")),
            ],
            body=_pairs(
                [
                    ("path", item.get("local_path")),
                    ("release_eligible", item.get("release_eligible")),
                    ("initiative_refs", item.get("related_initiative_refs", [])),
                ]
            ),
        )
        for item in (repo_inventory.get("items", []) if isinstance(repo_inventory.get("items"), list) else [])[:8]
        if isinstance(item, dict)
    ]

    dirty_repo_items = [
        _item(
            item.get("logical_id") or item.get("path") or "dirty-repo",
            badges=[
                _badge("dirty", item.get("dirty"), tone=_bool_tone(item.get("dirty"), truthy="danger", falsy="ok")),
                _badge("ref", item.get("ref")),
            ],
            body=_pairs([("path", item.get("path"))]),
        )
        for item in (lock_hygiene.get("dirty_repos", []) if isinstance(lock_hygiene.get("dirty_repos"), list) else [])
        if isinstance(item, dict)
    ]

    trust_items = [
        _item(
            item.get("archive_id") or "knowledge-surface",
            badges=[_badge("trust", item.get("trust_class")), _badge("mode", item.get("read_mode")), _badge("promotion", item.get("promotion_status"))],
            body=_pairs(
                [
                    ("knowledge_ref", item.get("knowledge_ref")),
                    ("indexing_profile", item.get("indexing_profile")),
                    ("source_ref", item.get("source_ref")),
                ]
            ),
            featured="verta" in str(item.get("archive_id", "")).lower(),
        )
        for item in (trust.get("items", []) if isinstance(trust.get("items"), list) else [])[:10]
        if isinstance(item, dict)
    ]

    playbook_items = [
        _item(
            "Owner Contract Export",
            eyebrow=playbook_contract.get("repo_id"),
            badges=[
                _badge("source", playbook_contract.get("source_status")),
                _badge("validation", playbook_contract.get("validation_state")),
                _badge("version", playbook_contract.get("contract_version")),
            ],
            body=_pairs(
                [
                    ("repo_path", playbook_contract.get("repo_path")),
                    ("export", playbook_contract.get("export_relpath")),
                    ("schema", playbook_contract.get("schema_relpath")),
                    ("doc", playbook_contract.get("doc_relpath")),
                    ("warnings", playbook_contract.get("warnings", [])),
                ]
            ),
            featured=str(playbook_contract.get("source_status") or "") == "present",
        )
        if playbook_contract
        else "<div class='empty'>Playbook contract status is unavailable.</div>"
    ]
    playbook_items.extend(
        _item(
            item.get("repo_id") or "repo",
            badges=[
                _badge("identity", item.get("repo_identity")),
                _badge("adoption", item.get("adoption_status")),
                _badge("verify", item.get("verification_status")),
                _badge("continuity", item.get("continuity_status")),
            ],
            body=_pairs(
                [
                    ("drift", item.get("drift_status")),
                    ("contract_version", item.get("contract_version_claimed")),
                    ("verification_scope", item.get("verification_scope") or item.get("verification_state")),
                    ("last_verified_at", item.get("last_verified_at")),
                    ("blocking_gaps", item.get("blocking_gaps", [])),
                    ("initiative_refs", item.get("initiative_refs", [])),
                    ("notes", item.get("notes", [])),
                ]
            ),
        )
        for item in (playbook.get("repos", []) if isinstance(playbook.get("repos"), list) else [])[:6]
        if isinstance(item, dict)
    )

    continuity_items = [
        _item(
            "Continuity Coverage",
            badges=[
                _badge("status", continuity_coverage.get("status")),
                _badge("sources", continuity_coverage.get("source_count")),
                _badge("pending_review", continuity_coverage.get("pending_review_count")),
            ],
            body=_pairs(
                [
                    ("handoff_schema", continuity_coverage.get("handoff_schema_ref")),
                    ("handoff_receipts", continuity_coverage.get("handoff_receipt_count")),
                    ("lane_docs", continuity_coverage.get("lane_doc_refs", [])),
                    ("transcript_role", continuity_coverage.get("transcript_role")),
                ]
            ),
            featured=str(continuity_coverage.get("status") or "") == "structured",
        )
        if continuity_coverage
        else "<div class='empty'>Continuity coverage is unavailable.</div>"
    ]
    continuity_items.extend(
        _item(
            item.get("source_id") or "promotion-candidate",
            eyebrow=item.get("lane"),
            badges=[
                _badge("status", item.get("status")),
                _badge("class", item.get("content_class")),
            ],
            body=_pairs(
                [
                    ("path", item.get("source_path")),
                    ("promotion_targets", item.get("promotion_targets", [])),
                    ("summary", item.get("source_summary")),
                ]
            ),
        )
        for item in (continuity_promotion_queue.get("items", []) if isinstance(continuity_promotion_queue.get("items"), list) else [])[:4]
        if isinstance(item, dict)
    )
    continuity_group_items = [
        _item(
            item.get("lane") or "lane",
            badges=[
                _badge("sources", item.get("source_count")),
                _badge("pending", item.get("pending_review_count")),
                _badge("promotion", item.get("promotion_candidate_count")),
            ],
        )
        for item in (continuity_source_groups.get("items", []) if isinstance(continuity_source_groups.get("items"), list) else [])[:5]
        if isinstance(item, dict)
    ]

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="{refresh_seconds}">
  <title>ATLAS Cockpit</title>
  <style>
    :root {{ --bg:#f4efe2; --ink:#1d2630; --muted:#57616d; --line:rgba(29,38,48,.12); --card:rgba(255,251,245,.88); --ok:#1b6b57; --warn:#9a5c11; --danger:#922f35; --shadow:0 18px 38px rgba(29,38,48,.08); }}
    * {{ box-sizing:border-box; }} body {{ margin:0; color:var(--ink); background:radial-gradient(circle at top left, rgba(27,107,87,.12), transparent 26rem), linear-gradient(180deg, var(--bg), #ece2cf); font:16px "Aptos","Segoe UI Variable Text","Trebuchet MS",sans-serif; }}
    header {{ padding:2.4rem 1.25rem 1rem; border-bottom:1px solid var(--line); }} main, .head {{ width:min(1440px, calc(100vw - 2rem)); margin:0 auto; }}
    h1, h2 {{ font-family:"Iowan Old Style","Palatino Linotype","Book Antiqua",serif; margin:0; }} h1 {{ font-size:clamp(2.4rem,4vw,4rem); line-height:.95; }} h2 {{ font-size:1.35rem; margin-bottom:.8rem; }}
    .sub {{ margin-top:.7rem; color:var(--muted); display:flex; gap:.75rem; flex-wrap:wrap; }} .chip {{ display:inline-flex; padding:.32rem .64rem; border-radius:999px; background:rgba(27,107,87,.12); color:var(--ok); font-size:.74rem; font-weight:700; text-transform:uppercase; letter-spacing:.05em; }}
    .grid {{ display:grid; gap:1rem; grid-template-columns:repeat(12,minmax(0,1fr)); padding:1rem 0 2rem; }} .card {{ grid-column:span 12; background:var(--card); border:1px solid var(--line); border-radius:1.1rem; box-shadow:var(--shadow); padding:1rem; }}
    .span-6 {{ grid-column:span 6; }} .span-4 {{ grid-column:span 4; }} .span-8 {{ grid-column:span 8; }}
    .metrics {{ display:grid; gap:.8rem; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); }} .metric,.item,.empty {{ border:1px solid rgba(29,38,48,.08); border-radius:1rem; background:rgba(255,255,255,.68); padding:.84rem .94rem; }}
    .label,.eyebrow,.k {{ color:var(--muted); font:12px "Cascadia Code","IBM Plex Mono","Consolas",monospace; text-transform:uppercase; letter-spacing:.05em; }} .value {{ font-size:1.5rem; font-weight:700; margin-top:.3rem; }} .ok {{ color:var(--ok); }} .warn {{ color:var(--warn); }} .danger {{ color:var(--danger); }}
    .badge {{ display:inline-flex; padding:.2rem .52rem; border-radius:999px; margin:.1rem .3rem .2rem 0; background:rgba(29,38,48,.08); }} .badge.ok {{ background:rgba(27,107,87,.12); }} .badge.warn {{ background:rgba(154,92,17,.14); }} .badge.danger {{ background:rgba(146,47,53,.14); }}
    .item {{ margin-top:.7rem; }} .featured {{ border-color:rgba(27,107,87,.28); background:linear-gradient(135deg, rgba(27,107,87,.08), rgba(255,255,255,.72)); }} .title {{ font-weight:700; margin:.28rem 0; }} .pairs {{ display:grid; grid-template-columns:minmax(120px,180px) 1fr; gap:.2rem .75rem; margin-top:.55rem; }} p {{ margin:.45rem 0 0; color:var(--muted); line-height:1.45; }}
    @media (max-width:1100px) {{ .span-6,.span-4,.span-8 {{ grid-column:span 12; }} }}
  </style>
</head>
<body>
  <header><div class="head"><div class="chip">Read Only</div><h1>ATLAS Cockpit</h1><div class="sub"><span>Thin operator view over Awareness API and the root read model.</span><span>Auto-refresh every {refresh_seconds}s.</span><span>{escape(str(payload.get('generated_at') or ''))}</span></div></div></header>
  <main class="grid">
    {_card("Stack Signal", f"<div class='metrics'>{metrics}</div>")}
    {_card("Session And Conversation State", _stack(session_items, "No session or conversation state is published."), "span-6")}
    {_card("Active Initiatives", _stack(initiative_items, "No active initiatives are published."), "span-6")}
    {_card("Attention Queue", _stack(attention_items, "Attention queue is clear."), "span-8")}
    {_card("Blessing Review Queue", _stack(review_items, "No repo work is currently waiting on blessing review."), "span-4")}
    {_card("Governed Proposal And Proposal-Only State", proposal_body, "span-6")}
    {_card("Operator Paths", _stack(path_items, "No focused operator paths are pending."), "span-6")}
    {_card("Playbook Convergence", "<div class='metrics'>" + "".join([
      f"<div class='metric'><div class='label'>Repos</div><div class='value'>{escape(str(playbook_summary.get('repo_count', '—')))}</div></div>",
      f"<div class='metric'><div class='label'>Planned</div><div class='value'>{escape(str(playbook_summary.get('planned_count', '-')))}</div></div>",
      f"<div class='metric'><div class='label'>Adopted</div><div class='value'>{escape(str(playbook_summary.get('adopted_count', '—')))}</div></div>",
      f"<div class='metric'><div class='label'>Verified</div><div class='value {_count_tone(playbook_summary.get('verified_count'), zero='warn', nonzero='ok')}'>{escape(str(playbook_summary.get('verified_count', '-')))}</div></div>",
      f"<div class='metric'><div class='label'>Blocked</div><div class='value {_count_tone(playbook_summary.get('verification_blocked_count'), zero='ok', nonzero='danger')}'>{escape(str(playbook_summary.get('verification_blocked_count', '-')))}</div></div>",
    ]) + "</div>" + _stack(playbook_items, "No Playbook convergence state is published."), "span-6")}
    {_card("Continuity Coverage", "<div class='metrics'>" + "".join([
      f"<div class='metric'><div class='label'>Sources</div><div class='value'>{escape(str(continuity_coverage.get('source_count', '—')))}</div></div>",
      f"<div class='metric'><div class='label'>Pending Review</div><div class='value {_count_tone(continuity_coverage.get('pending_review_count'), zero='ok', nonzero='warn')}'>{escape(str(continuity_coverage.get('pending_review_count', '—')))}</div></div>",
      f"<div class='metric'><div class='label'>Indexed</div><div class='value'>{escape(str(continuity_coverage.get('indexed_count', '—')))}</div></div>",
      f"<div class='metric'><div class='label'>Handoffs</div><div class='value'>{escape(str(continuity_coverage.get('handoff_receipt_count', '—')))}</div></div>",
    ]) + "</div>" + _stack(continuity_items, "No continuity coverage is published.") + _stack(continuity_group_items, "No continuity lane groups are published."), "span-6")}
    {_card("Repo Inventory State", "<div class='metrics'>" + "".join([
      f"<div class='metric'><div class='label'>Repos</div><div class='value'>{escape(str(repo_inventory.get('item_count', '—')))}</div></div>",
      f"<div class='metric'><div class='label'>Dirty</div><div class='value {_count_tone(repo_inventory.get('dirty_item_count'), zero='ok', nonzero='danger')}'>{escape(str(repo_inventory.get('dirty_item_count', '—')))}</div></div>",
      f"<div class='metric'><div class='label'>Release</div><div class='value'>{escape(str(repo_inventory.get('release_eligible_count', '—')))}</div></div>",
      f"<div class='metric'><div class='label'>Excluded</div><div class='value'>{escape(str(repo_inventory.get('excluded_surface_count', '—')))}</div></div>",
    ]) + "</div>" + _stack(repo_items, "Repo inventory is empty."), "span-6")}
    {_card("Lock And Worktree Hygiene", "<div class='metrics'>" + "".join([
      f"<div class='metric'><div class='label'>Lock</div><div class='value {_state_tone(lock_hygiene.get('status'))}'>{escape(str(lock_hygiene.get('status', '—')))}</div></div>",
      f"<div class='metric'><div class='label'>Dirty Repos</div><div class='value {_count_tone(lock_hygiene.get('dirty_repo_count'), zero='ok', nonzero='danger')}'>{escape(str(lock_hygiene.get('dirty_repo_count', '—')))}</div></div>",
      f"<div class='metric'><div class='label'>Component Drift</div><div class='value {_count_tone(lock_hygiene.get('drifted_component_count'), zero='ok', nonzero='warn')}'>{escape(str(lock_hygiene.get('drifted_component_count', '—')))}</div></div>",
      f"<div class='metric'><div class='label'>Surface Drift</div><div class='value {_count_tone(lock_hygiene.get('drifted_excluded_surface_count'), zero='ok', nonzero='warn')}'>{escape(str(lock_hygiene.get('drifted_excluded_surface_count', '—')))}</div></div>",
    ]) + "</div>" + _item("Current lock posture", badges=[_badge("frozen", lock_hygiene.get("lock_frozen"), tone=_bool_tone(lock_hygiene.get("lock_frozen"), truthy="ok", falsy="danger")), _badge("root_dirty", lock_hygiene.get("stack_root", {}).get("dirty_effective") if isinstance(lock_hygiene.get("stack_root"), dict) else None, tone=_bool_tone(lock_hygiene.get("stack_root", {}).get("dirty_effective") if isinstance(lock_hygiene.get("stack_root"), dict) else None, truthy="danger", falsy="ok")), _badge("self_refresh_only", lock_hygiene.get("stack_root", {}).get("self_refresh_only") if isinstance(lock_hygiene.get("stack_root"), dict) else None, tone=_bool_tone(lock_hygiene.get("stack_root", {}).get("self_refresh_only") if isinstance(lock_hygiene.get("stack_root"), dict) else None, truthy="warn", falsy="ok"))], body=_pairs([("stack_lock_ref", lock_hygiene.get("stack_lock_ref")), ("stack_lock_digest", lock_hygiene.get("stack_lock_digest")), ("generated_lock_digest", lock_hygiene.get("generated_lock_digest")), ("drifted_components", lock_hygiene.get("drifted_component_ids", [])), ("drifted_surfaces", lock_hygiene.get("drifted_excluded_surface_ids", [])), ("metadata_drift", lock_hygiene.get("metadata_drift_fields", [])), ("modified_paths", lock_hygiene.get("stack_root", {}).get("modified_paths", []) if isinstance(lock_hygiene.get("stack_root"), dict) else [])])) + _stack(dirty_repo_items, "No dirty repos are currently pinned by the generated lock view."), "span-6")}
    {_card("Trust Posture", "<div class='metrics'>" + "".join([
      f"<div class='metric'><div class='label'>Status</div><div class='value {_state_tone(trust.get('status'))}'>{escape(str(trust.get('status', '—')))}</div></div>",
      f"<div class='metric'><div class='label'>Visible</div><div class='value'>{escape(str(trust.get('item_count', '—')))}</div></div>",
      f"<div class='metric'><div class='label'>Untrusted</div><div class='value {_count_tone(trust.get('untrusted_item_count'), zero='ok', nonzero='danger')}'>{escape(str(trust.get('untrusted_item_count', '—')))}</div></div>",
      f"<div class='metric'><div class='label'>Metadata Only</div><div class='value {_count_tone(trust.get('metadata_only_item_count'), zero='ok', nonzero='warn')}'>{escape(str(trust.get('metadata_only_item_count', '—')))}</div></div>",
    ]) + "</div>" + _stack(trust_items, "No trust posture items are published."))}
  </main>
</body>
</html>"""


class CockpitServer(ThreadingHTTPServer):
    awareness_endpoint: str | None
    auth_token: str | None
    refresh_seconds: int
    server_auth_tokens: list[str]


class CockpitHandler(BaseHTTPRequestHandler):
    server_version = "ATLASCockpit/1.0"

    def _config(self) -> CockpitServer:
        return self.server  # type: ignore[return-value]

    def _payload(self, *, refresh: bool) -> dict[str, Any]:
        config = self._config()
        if isinstance(config.awareness_endpoint, str) and config.awareness_endpoint.strip():
            return _fetch_remote_cockpit(config.awareness_endpoint, auth_token=config.auth_token, refresh=refresh)
        return cockpit_status(refresh=refresh)

    def _authenticate(self) -> tuple[bool, str, str | None]:
        return authenticate_bearer(self.headers, self._config().server_auth_tokens)

    def _send_json(
        self,
        payload: dict[str, Any],
        *,
        status: int = HTTPStatus.OK,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        encoded = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "private, no-store")
        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(encoded)

    def _send_html(self, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "private, no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        refresh = parse_qs(parsed.query, keep_blank_values=False).get("refresh", ["false"])[0].strip().lower() == "true"
        try:
            if parsed.path in {"/", "/api/cockpit"}:
                authenticated, _, _ = self._authenticate()
                if not authenticated:
                    self._send_json(
                        {
                            "ok": False,
                            "error": "unauthorized",
                            "message": "A valid bearer token is required for the ATLAS cockpit.",
                        },
                        status=HTTPStatus.UNAUTHORIZED,
                        extra_headers={"WWW-Authenticate": 'Bearer realm="atlas-cockpit"'},
                    )
                    return
            if parsed.path == "/":
                self._send_html(_render_html(self._payload(refresh=refresh), refresh_seconds=self._config().refresh_seconds))
                return
            if parsed.path == "/api/cockpit":
                self._send_json(self._payload(refresh=refresh))
                return
            if parsed.path == "/health":
                self._send_json(
                    {
                        "ok": True,
                        "service": "atlas-cockpit",
                        "read_only": True,
                        "auth_required": bool(self._config().server_auth_tokens),
                    }
                )
                return
            self._send_json({"ok": False, "error": "not_found", "path": parsed.path}, status=HTTPStatus.NOT_FOUND)
        except Exception as exc:  # pragma: no cover - defensive path
            self._send_json({"ok": False, "error": "cockpit_error", "message": str(exc)}, status=HTTPStatus.BAD_GATEWAY)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve the ATLAS read-only operator cockpit.")
    parser.add_argument("--host", default=os.environ.get("ATLAS_COCKPIT_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("ATLAS_COCKPIT_PORT", "8786")))
    parser.add_argument("--awareness-base-url")
    parser.add_argument("--awareness-auth-token", "--auth-token", dest="awareness_auth_token")
    parser.add_argument("--awareness-auth-token-file", "--auth-token-file", dest="awareness_auth_token_file")
    parser.add_argument("--server-auth-token")
    parser.add_argument("--server-auth-token-file")
    parser.add_argument("--server-auth-token-previous")
    parser.add_argument("--server-auth-token-previous-file")
    parser.add_argument("--allow-unauthenticated", action="store_true")
    parser.add_argument("--refresh-seconds", type=int, default=DEFAULT_REFRESH_SECONDS)
    parser.add_argument("--dump-json", action="store_true")
    args = parser.parse_args(argv)

    awareness_endpoint = _normalize_awareness_endpoint(args.awareness_base_url) if args.awareness_base_url else None
    auth_token = load_optional_token(
        direct_value=args.awareness_auth_token,
        file_value=args.awareness_auth_token_file,
        env_key="ATLAS_AWARENESS_TOKEN",
        env_file_key="ATLAS_AWARENESS_TOKEN_FILE",
    )
    server_auth_tokens = load_auth_tokens(
        specs=[
            (
                args.server_auth_token,
                args.server_auth_token_file,
                "ATLAS_COCKPIT_TOKEN",
                "ATLAS_COCKPIT_TOKEN_FILE",
            ),
            (
                args.server_auth_token_previous,
                args.server_auth_token_previous_file,
                "ATLAS_COCKPIT_PREVIOUS_TOKEN",
                "ATLAS_COCKPIT_PREVIOUS_TOKEN_FILE",
            ),
        ]
    )

    if args.dump_json:
        payload = _fetch_remote_cockpit(awareness_endpoint, auth_token=auth_token, refresh=False) if awareness_endpoint else cockpit_status(refresh=False)
        print(json.dumps(payload, indent=2))
        return 0

    enforce_remote_bind_policy(
        parser=parser,
        host=args.host,
        auth_tokens=server_auth_tokens,
        allow_unauthenticated=args.allow_unauthenticated,
        error_message="Remote ATLAS cockpit binds require --server-auth-token or --server-auth-token-file unless --allow-unauthenticated is set.",
    )

    server = CockpitServer((args.host, args.port), CockpitHandler)
    server.awareness_endpoint = awareness_endpoint
    server.auth_token = auth_token
    server.refresh_seconds = max(args.refresh_seconds, 5)
    server.server_auth_tokens = server_auth_tokens
    print(json.dumps({"service": "atlas-cockpit", "host": args.host, "port": args.port, "read_only": True, "auth_required": bool(server_auth_tokens), "awareness_endpoint": awareness_endpoint, "refresh_seconds": server.refresh_seconds}, indent=2))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
