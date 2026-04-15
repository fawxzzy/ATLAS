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

from ops._atlas import atlas_relative, atlas_root, resolve_atlas_path
from ops.atlas.build_turn_context import build_turn_context
from ops.atlas.plan_conversation_response import compose_response
from ops.atlas.run_initiative_loop import (
    Cluster,
    build_initiative_payload,
    build_proposal_payload,
    initiative_path,
    proposal_session_path,
    refresh_descriptors_and_world_model,
    validate_proposal_payload,
)
from ops.atlas.run_session import load_stack_lock_payload
from ops.cortex._artifacts import stable_json_digest, write_json, write_json_if_changed
from ops.cortex.index_working_memory import normalize_working_memory_document, write_working_memory_catalog

CONVERSATION_AUTOMATION_LEVEL_CEILING = "request_action"
CONVERSATION_CONTRACT_VERSION = "atlas.conversation.v1"
TURN_CONTRACT_VERSION = "atlas.conversation.turn.v1"
RECENT_TURN_LIMIT = 8


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat(value: datetime | None = None) -> str:
    return (value or utc_now()).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._:-]+", "-", value.strip().lower()).strip("-")
    return cleaned or "conversation"


def trim_text(value: str, limit: int = 220) -> str:
    compact = " ".join(value.split())
    return compact if len(compact) <= limit else f"{compact[: limit - 3]}..."


def unique_strings(values: list[Any]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        ordered.append(stripped)
    return ordered


def conversation_root(root: Path, conversation_id: str) -> Path:
    return root / "runtime" / "atlas" / "conversations" / conversation_id


def conversation_manifest_path(root: Path, conversation_id: str) -> Path:
    return conversation_root(root, conversation_id) / "conversation.manifest.json"


def turn_artifact_path(root: Path, conversation_id: str, turn_id: str) -> Path:
    return conversation_root(root, conversation_id) / "turns" / f"{turn_id}.json"


def load_json_if_present(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def conversation_template(*, conversation_id: str, mode: str) -> dict[str, Any]:
    now = isoformat()
    return {
        "contract_version": CONVERSATION_CONTRACT_VERSION,
        "conversation_id": conversation_id,
        "mode": mode,
        "status": "active",
        "created_at": now,
        "updated_at": now,
        "automation_level_ceiling": CONVERSATION_AUTOMATION_LEVEL_CEILING,
        "active_initiative_refs": [],
        "active_session_refs": [],
        "recent_turn_refs": [],
        "related_memory_refs": [],
        "related_attention_refs": [],
        "summary": {
            "turn_count": 0,
            "last_turn_at": None,
            "last_input_summary": None,
            "last_response_summary": None,
            "last_intent": None,
        },
        "provider": {
            "adapter": "deterministic-grounding-v1",
            "model": "atlas-grounded-rules",
        },
    }


def ensure_conversation_manifest(*, root: Path, conversation_id: str, mode: str) -> dict[str, Any]:
    path = conversation_manifest_path(root, conversation_id)
    existing = load_json_if_present(path)
    if existing is not None:
        return existing
    payload = conversation_template(conversation_id=conversation_id, mode=mode)
    write_json(path, payload)
    return payload


def known_attention_ref_for_turn(root: Path, turn_ref: str) -> str | None:
    attention_path = root / "runtime" / "state" / "atlas" / "world-model.attention.latest.json"
    payload = load_json_if_present(attention_path)
    if not isinstance(payload, dict):
        return None
    for item in payload.get("attention_items", []):
        if not isinstance(item, dict):
            continue
        if str(item.get("source_ref") or "").strip() != turn_ref:
            continue
        if str(item.get("kind") or "").strip() != "conversation_action_request":
            continue
        attention_id = str(item.get("attention_id") or "").strip()
        if attention_id:
            return f"attention:{attention_id}"
    return None


def collect_source_refs(value: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(value, dict):
        source_ref = value.get("source_ref")
        if isinstance(source_ref, str) and source_ref.strip():
            refs.append(source_ref.strip())
        for nested in value.values():
            refs.extend(collect_source_refs(nested))
    elif isinstance(value, list):
        for nested in value:
            refs.extend(collect_source_refs(nested))
    return unique_strings(refs)


def durable_turn_source_refs(root: Path, turn_context: dict[str, Any]) -> list[str]:
    ref_set = turn_context.get("retrieved_ref_set", {}) if isinstance(turn_context.get("retrieved_ref_set"), dict) else {}
    artifact_refs = [
        ref
        for ref in unique_strings(list(ref_set.get("artifact_refs", [])))
        if resolve_atlas_path(ref, root=root).exists()
    ]
    facts = turn_context.get("facts", {})
    return unique_strings([*artifact_refs, *collect_source_refs(facts)])


def source_refs_by_token(refs: list[str], *, token: str) -> list[str]:
    normalized_token = f"/{token}/"
    return sorted(ref for ref in unique_strings(refs) if normalized_token in ref.replace("\\", "/"))


def memory_refs_by_kind(refs: list[str], *, token: str) -> list[str]:
    return sorted(
        ref
        for ref in unique_strings(refs)
        if f"/{token}/" in ref.replace("\\", "/")
    )


def ensure_conversation_initiative(
    *,
    root: Path,
    turn_ref: str,
    turn_context: dict[str, Any],
    attention_ref: str | None,
) -> str:
    ref_set = turn_context.get("retrieved_ref_set", {}) if isinstance(turn_context.get("retrieved_ref_set"), dict) else {}
    durable_refs = durable_turn_source_refs(root, turn_context)
    existing_initiative_refs = unique_strings(list(ref_set.get("initiative_refs", [])))
    if existing_initiative_refs:
        initiative_id = existing_initiative_refs[0].split(":", 1)[-1]
        initiative_ref = atlas_relative(initiative_path(root, initiative_id), root=root)
        if resolve_atlas_path(initiative_ref, root=root).exists():
            return initiative_ref

    target = str(turn_context.get("target") or turn_context.get("intent") or "conversation").strip()
    initiative_id = f"initiative-{slugify(target)}"
    initiative_ref = atlas_relative(initiative_path(root, initiative_id), root=root)
    cluster = Cluster(
        key=initiative_id,
        initiative_id=initiative_id,
        initiative_ref=initiative_ref,
        task_id=slugify(target),
        title=f"{trim_text(target, limit=80).title()} Initiative",
        summary=(
            "Track the conversation-requested work above the session layer so proposals stay durable, "
            "queryable, and grounded in explicit refs."
        ),
    )
    cluster.related_session_refs.update(source_refs_by_token(durable_refs, token="sessions"))
    cluster.related_attention_refs.update(unique_strings([attention_ref, *list(ref_set.get("attention_refs", []))]))
    cluster.evidence_refs.update(
        unique_strings(
            [
                turn_ref,
                *durable_refs,
            ]
        )
    )
    cluster.related_plan_refs.update(memory_refs_by_kind(durable_refs, token="plans"))
    cluster.related_decision_refs.update(memory_refs_by_kind(durable_refs, token="decisions"))
    cluster.related_hypothesis_refs.update(memory_refs_by_kind(durable_refs, token="hypotheses"))
    cluster.created_candidates.append(isoformat())
    cluster.updated_candidates.append(isoformat())
    cluster.metadata.update(
        {
            "authoring_source": "conversation-runtime",
            "conversation_turn_ref": turn_ref,
        }
    )
    payload = build_initiative_payload(cluster)
    normalize_working_memory_document(payload, memory_kind="initiative", relative_path=initiative_ref)
    write_json_if_changed(resolve_atlas_path(initiative_ref, root=root), payload)
    write_working_memory_catalog(root)
    return initiative_ref


def ensure_proposed_session(
    *,
    root: Path,
    turn_ref: str,
    turn_context: dict[str, Any],
    initiative_ref: str,
    attention_ref: str,
) -> str:
    ref_set = turn_context.get("retrieved_ref_set", {}) if isinstance(turn_context.get("retrieved_ref_set"), dict) else {}
    durable_refs = durable_turn_source_refs(root, turn_context)
    initiative_id = resolve_atlas_path(initiative_ref, root=root).stem
    target = str(turn_context.get("target") or turn_context.get("intent") or initiative_id).strip()
    cluster = Cluster(
        key=initiative_id,
        initiative_id=initiative_id,
        initiative_ref=initiative_ref,
        task_id=slugify(target),
        title=trim_text(target, limit=80).title(),
        summary="Conversation-authored proposal that stays non-executing until a governed session is explicitly started.",
    )
    cluster.actionable_attention_refs.update(unique_strings([attention_ref]))
    cluster.related_attention_refs.update(unique_strings([attention_ref, *list(ref_set.get("attention_refs", []))]))
    cluster.related_session_refs.update(source_refs_by_token(durable_refs, token="sessions"))
    cluster.related_plan_refs.update(memory_refs_by_kind(durable_refs, token="plans"))
    cluster.related_decision_refs.update(memory_refs_by_kind(durable_refs, token="decisions"))
    cluster.related_hypothesis_refs.update(memory_refs_by_kind(durable_refs, token="hypotheses"))
    cluster.evidence_refs.update(
        unique_strings(
            [
                turn_ref,
                initiative_ref,
                *durable_refs,
                *cluster.related_session_refs,
                *cluster.related_plan_refs,
                *cluster.related_decision_refs,
                *cluster.related_hypothesis_refs,
            ]
        )
    )
    cluster.created_candidates.append(isoformat())
    cluster.updated_candidates.append(isoformat())

    from ops.atlas.load_tool_registry import load_tool_registry_bundle

    tool_bundle = load_tool_registry_bundle(root=root)
    stack_lock_payload = load_stack_lock_payload()
    payload = build_proposal_payload(cluster=cluster, tool_bundle=tool_bundle, stack_lock_payload=stack_lock_payload)
    known_attention_refs = {attention_ref}
    known_file_refs = set(cluster.evidence_refs) | {
        initiative_ref,
        *cluster.related_session_refs,
        *cluster.related_plan_refs,
        *cluster.related_decision_refs,
        *cluster.related_hypothesis_refs,
    }
    errors = validate_proposal_payload(
        payload,
        known_attention_refs=known_attention_refs,
        known_file_refs=known_file_refs,
        root=root,
    )
    if errors:
        raise ValueError("; ".join(errors))
    proposal_path = proposal_session_path(root, payload["session_id"])
    write_json_if_changed(proposal_path, payload)
    return atlas_relative(proposal_path, root=root)


def build_turn_payload(
    *,
    conversation_id: str,
    turn_id: str,
    created_at: str,
    turn_context: dict[str, Any],
) -> dict[str, Any]:
    return {
        "contract_version": TURN_CONTRACT_VERSION,
        "conversation_id": conversation_id,
        "turn_id": turn_id,
        "role": "user",
        "created_at": created_at,
        "input_summary": str(turn_context.get("input_summary") or "").strip(),
        "retrieved_ref_set": turn_context.get("retrieved_ref_set", {}),
        "response_summary": "Response pending.",
        "proposed_session_refs": [],
        "authored_memory_refs": [],
        "tool_trace_refs": [],
        "query_trace": turn_context.get("query_trace", []),
        "provenance": {
            "intent": str(turn_context.get("intent") or "status_overview"),
            "provider": "deterministic-grounding-v1",
            "context_digest": str(turn_context.get("context_digest") or stable_json_digest(turn_context)),
            "action_mode": str(turn_context.get("action_mode") or "informational"),
        },
    }


def update_conversation_manifest(
    manifest: dict[str, Any],
    *,
    mode: str,
    updated_at: str,
    turn_ref: str,
    turn_context: dict[str, Any],
    turn_payload: dict[str, Any],
    response_summary: str,
) -> dict[str, Any]:
    ref_set = turn_context.get("retrieved_ref_set", {}) if isinstance(turn_context.get("retrieved_ref_set"), dict) else {}
    related_memory_refs = unique_strings(
        [
            *list(manifest.get("related_memory_refs", [])),
            *list(ref_set.get("memory_refs", [])),
            *list(turn_payload.get("authored_memory_refs", [])),
        ]
    )
    related_attention_refs = unique_strings(
        [
            *list(manifest.get("related_attention_refs", [])),
            *list(ref_set.get("attention_refs", [])),
        ]
    )
    active_initiative_refs = unique_strings(
        [
            *list(manifest.get("active_initiative_refs", [])),
            *list(ref_set.get("initiative_refs", [])),
            *[ref for ref in turn_payload.get("authored_memory_refs", []) if "/initiatives/" in ref],
        ]
    )
    active_session_refs = unique_strings(
        [
            *list(manifest.get("active_session_refs", [])),
            *list(ref_set.get("session_refs", [])),
            *list(turn_payload.get("proposed_session_refs", [])),
        ]
    )
    recent_turns = unique_strings([*list(manifest.get("recent_turn_refs", [])), turn_ref])[-RECENT_TURN_LIMIT:]
    summary = manifest.get("summary", {}) if isinstance(manifest.get("summary"), dict) else {}
    turn_count = int(summary.get("turn_count", 0) or 0) + 1
    return {
        **manifest,
        "mode": mode,
        "status": "active",
        "updated_at": updated_at,
        "active_initiative_refs": active_initiative_refs,
        "active_session_refs": active_session_refs,
        "recent_turn_refs": recent_turns,
        "related_memory_refs": related_memory_refs,
        "related_attention_refs": related_attention_refs,
        "summary": {
            "turn_count": turn_count,
            "last_turn_at": updated_at,
            "last_input_summary": turn_payload.get("input_summary"),
            "last_response_summary": response_summary,
            "last_intent": turn_payload.get("provenance", {}).get("intent"),
        },
    }


def run_conversation_turn(
    *,
    root: Path,
    conversation_id: str,
    mode: str,
    user_input: str,
    refresh: bool = False,
) -> dict[str, Any]:
    manifest = ensure_conversation_manifest(root=root, conversation_id=conversation_id, mode=mode)
    turn_context = build_turn_context(
        user_input,
        root=root,
        conversation_id=conversation_id,
        mode=mode,
        refresh=refresh,
    )
    created_at = isoformat()
    turn_id = f"turn-{utc_now().strftime('%Y%m%dT%H%M%S%fZ')}"
    turn_path = turn_artifact_path(root, conversation_id, turn_id)
    turn_ref = atlas_relative(turn_path, root=root)
    turn_payload = build_turn_payload(
        conversation_id=conversation_id,
        turn_id=turn_id,
        created_at=created_at,
        turn_context=turn_context,
    )
    write_json(turn_path, turn_payload)
    refresh_descriptors_and_world_model(root)

    authored_memory_refs: list[str] = []
    proposed_session_refs: list[str] = []
    if str(turn_payload.get("provenance", {}).get("action_mode")) == "proposal_required":
        attention_ref = known_attention_ref_for_turn(root, turn_ref)
        if attention_ref:
            initiative_ref = ensure_conversation_initiative(
                root=root,
                turn_ref=turn_ref,
                turn_context=turn_context,
                attention_ref=attention_ref,
            )
            authored_memory_refs.append(initiative_ref)
            write_working_memory_catalog(root)
            refresh_descriptors_and_world_model(root)
            proposal_ref = ensure_proposed_session(
                root=root,
                turn_ref=turn_ref,
                turn_context=turn_context,
                initiative_ref=initiative_ref,
                attention_ref=attention_ref,
            )
            proposed_session_refs.append(proposal_ref)
            refresh_descriptors_and_world_model(root)

    response = compose_response(
        turn_context,
        proposed_session_refs=proposed_session_refs,
        authored_memory_refs=authored_memory_refs,
    )
    turn_payload["response_summary"] = response["response_summary"]
    turn_payload["proposed_session_refs"] = proposed_session_refs
    turn_payload["authored_memory_refs"] = authored_memory_refs
    turn_payload["provenance"]["provider"] = str(response.get("provider", {}).get("adapter") or "deterministic-grounding-v1")
    write_json(turn_path, turn_payload)

    updated_manifest = update_conversation_manifest(
        manifest,
        mode=mode,
        updated_at=isoformat(),
        turn_ref=turn_ref,
        turn_context=turn_context,
        turn_payload=turn_payload,
        response_summary=response["response_summary"],
    )
    write_json(conversation_manifest_path(root, conversation_id), updated_manifest)
    refresh_descriptors_and_world_model(root)

    return {
        "conversation_id": conversation_id,
        "conversation_ref": atlas_relative(conversation_manifest_path(root, conversation_id), root=root),
        "turn_id": turn_id,
        "turn_ref": turn_ref,
        "response": response["response_text"],
        "response_summary": response["response_summary"],
        "provider": response["provider"],
        "proposed_session_refs": proposed_session_refs,
        "authored_memory_refs": authored_memory_refs,
        "retrieved_ref_set": turn_payload["retrieved_ref_set"],
        "context_digest": turn_payload["provenance"]["context_digest"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an ATLAS grounded conversation turn above awareness, memory, and proposal-only runtime surfaces.")
    parser.add_argument("--conversation-id", required=True)
    parser.add_argument("--mode", choices=["text", "voice"], default="text")
    parser.add_argument("--input", required=True)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args(argv)

    payload = run_conversation_turn(
        root=atlas_root(),
        conversation_id=args.conversation_id,
        mode=args.mode,
        user_input=args.input,
        refresh=args.refresh,
    )
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
