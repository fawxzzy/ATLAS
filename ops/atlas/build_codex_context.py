from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, load_stack_config, resolve_atlas_path
from ops.atlas.awareness import atlas_status, fetch, fetch_memory, fetch_status_slice, list_attention, query_knowledge
from ops.cortex._artifacts import read_json, sha256_bytes, stable_json_digest, write_json
from ops.cortex.index_working_memory import load_working_memory_catalog
from ops.stack.export_repo_inventory import find_repo_inventory_entry

SCHEMA_VERSION = "atlas.codex.context-pack.v1"
DEFAULT_OUTPUT_ROOT = Path("runtime/atlas/context-packs")
MAX_ROUTE_SURFACES = 8
MAX_ATTENTION_ITEMS = 6
MAX_WORKING_MEMORY_ITEMS = 8
MAX_KNOWLEDGE_ITEMS = 4
MAX_DEFERRED_REPO_REFS = 10

INTENT_ALIASES = {
    "doctrine_platform": "doctrine/platform",
    "doctrine": "doctrine/platform",
    "platform": "doctrine/platform",
    "topology": "topology/git",
    "git": "topology/git",
    "operator": "operator/conversation",
    "conversation": "operator/conversation",
}

INTENT_ROUTING = {
    "governance": {
        "owner_lane": "playbook",
        "routing_rule": "governance / policy / verification -> Playbook",
        "awareness_slices": ["trust_posture"],
        "route_surfaces": [
            {
                "ref": "repos/fawxzzy-playbook/AGENTS.md",
                "owner": "playbook",
                "kind": "owner_contract",
                "why": "Playbook is the governance owner for rules, verify flow, and policy work.",
            },
            {
                "ref": "repos/fawxzzy-playbook/README.md",
                "owner": "playbook",
                "kind": "owner_overview",
                "why": "Playbook README is the top-level command and governance surface overview.",
            },
            {
                "ref": "repos/fawxzzy-playbook/docs/commands/verify.md",
                "owner": "playbook",
                "kind": "owner_runbook",
                "why": "Verify is the canonical governance and policy entrypoint.",
            },
            {
                "ref": "repos/fawxzzy-playbook/docs/rules/verify-rules.md",
                "owner": "playbook",
                "kind": "owner_rules",
                "why": "Verify rule inventory is the stable rules and bindings surface.",
            },
            {
                "ref": "repos/fawxzzy-playbook/docs/contracts/verify-output.md",
                "owner": "playbook",
                "kind": "owner_contract",
                "why": "Verify output contract defines the machine-readable bindings this lane consumes.",
            },
        ],
    },
    "execution": {
        "owner_lane": "lifeline",
        "routing_rule": "execution / capability / approvals / tools -> Lifeline",
        "awareness_slices": ["trust_posture"],
        "route_surfaces": [
            {
                "ref": "docs/registry/ATLAS-TOOL-REGISTRY.json",
                "owner": "stack-root",
                "kind": "root_registry",
                "why": "Tool registry is the governed capability source of truth for execution.",
            },
            {
                "ref": "docs/ops/ATLAS-TOOL-REGISTRY-RUNBOOK.md",
                "owner": "stack-root",
                "kind": "root_runbook",
                "why": "Root runbook explains how Playbook, Lifeline, and root sessions consume the registry.",
            },
            {
                "ref": "docs/ops/AUTOMATION-LEVELS.md",
                "owner": "stack-root",
                "kind": "root_policy",
                "why": "Automation levels define approval boundaries and execution ceilings.",
            },
            {
                "ref": "repos/fawxzzy-lifeline/AGENTS.md",
                "owner": "lifeline",
                "kind": "owner_contract",
                "why": "Lifeline AGENTS defines the repo-local execution contract.",
            },
            {
                "ref": "repos/fawxzzy-lifeline/README.md",
                "owner": "lifeline",
                "kind": "owner_overview",
                "why": "Lifeline README is the execution-surface overview.",
            },
            {
                "ref": "repos/fawxzzy-lifeline/docs/privileged-execution.md",
                "owner": "lifeline",
                "kind": "owner_runbook",
                "why": "Privileged execution docs define approval-gated action flow and receipts.",
            },
            {
                "ref": "repos/fawxzzy-lifeline/examples/privileged-execution/read-only-scan.request.json",
                "owner": "lifeline",
                "kind": "owner_example",
                "why": "Request example shows the canonical read-only execution request shape.",
            },
            {
                "ref": "repos/fawxzzy-lifeline/examples/privileged-execution/read-only-scan.approval.json",
                "owner": "lifeline",
                "kind": "owner_example",
                "why": "Approval example shows the canonical approval receipt shape.",
            },
        ],
    },
    "orchestration": {
        "owner_lane": "_stack",
        "routing_rule": "orchestration / worker flow / resume / merge -> _stack",
        "awareness_slices": ["pending_proposals", "waiting_on_review", "trust_posture"],
        "route_surfaces": [
            {
                "ref": "docs/ops/ATLAS-SESSION-RUNBOOK.md",
                "owner": "stack-root",
                "kind": "root_runbook",
                "why": "ATLAS session runbook defines the root coordination boundary over _stack and Lifeline.",
            },
            {
                "ref": "docs/ops/ATLAS-STATUS-RUNBOOK.md",
                "owner": "stack-root",
                "kind": "root_runbook",
                "why": "Status runbook defines resume and merge visibility surfaces.",
            },
            {
                "ref": "repos/_stack/README.md",
                "owner": "_stack",
                "kind": "owner_overview",
                "why": "_stack README is the workflow-operator overview.",
            },
            {
                "ref": "repos/_stack/docs/runbooks/STACK-WORKER-FLOW.md",
                "owner": "_stack",
                "kind": "owner_runbook",
                "why": "Worker flow runbook is the canonical orchestration path for assignments and merge flow.",
            },
            {
                "ref": "repos/_stack/docs/dispatcher-protocol.md",
                "owner": "_stack",
                "kind": "owner_contract",
                "why": "Dispatcher protocol defines worker dispatch and resume mechanics.",
            },
            {
                "ref": "repos/_stack/docs/codex-orchestration.md",
                "owner": "_stack",
                "kind": "owner_runbook",
                "why": "Codex orchestration docs explain how root-launched work maps into worker flow.",
            },
            {
                "ref": "repos/_stack/ops/codex/Invoke-CodexRepoTask.ps1",
                "owner": "_stack",
                "kind": "owner_operator_surface",
                "why": "Repo task launcher is the operator handoff surface for Codex-driven orchestration.",
            },
        ],
    },
    "doctrine/platform": {
        "owner_lane": "atlas",
        "routing_rule": "doctrine / UAPI / platform contracts -> Atlas repo",
        "awareness_slices": ["trust_posture"],
        "route_surfaces": [
            {
                "ref": "repos/fawxzzy-atlas/AGENTS.md",
                "owner": "atlas",
                "kind": "owner_contract",
                "why": "Atlas AGENTS defines architecture-truth boundaries for doctrine work.",
            },
            {
                "ref": "repos/fawxzzy-atlas/README.md",
                "owner": "atlas",
                "kind": "owner_overview",
                "why": "Atlas README is the platform doctrine overview.",
            },
            {
                "ref": "repos/fawxzzy-atlas/docs/ATLAS_PLATFORM_MODEL.md",
                "owner": "atlas",
                "kind": "owner_doctrine",
                "why": "Platform model is the canonical architecture doctrine surface.",
            },
            {
                "ref": "repos/fawxzzy-atlas/docs/ATLAS_UAPI.md",
                "owner": "atlas",
                "kind": "owner_contract",
                "why": "UAPI defines the platform contract surface for clients and tools.",
            },
            {
                "ref": "repos/fawxzzy-atlas/docs/OWNERSHIP_BOUNDARIES.md",
                "owner": "atlas",
                "kind": "owner_doctrine",
                "why": "Ownership boundaries define the stable repo and subsystem splits.",
            },
            {
                "ref": "repos/fawxzzy-atlas/docs/ATLAS_TOOL_CATALOG.md",
                "owner": "atlas",
                "kind": "owner_catalog",
                "why": "Tool catalog is the doctrine-facing catalog for platform capabilities.",
            },
        ],
    },
    "knowledge": {
        "owner_lane": "knowledge lane",
        "routing_rule": "knowledge / evidence / promotion / query -> knowledge lane",
        "awareness_slices": ["trust_posture"],
        "route_surfaces": [
            {
                "ref": "docs/knowledge/QUERY-CONTRACT.md",
                "owner": "stack-root",
                "kind": "root_contract",
                "why": "Query contract defines the deterministic knowledge query bundle and privacy policy.",
            },
            {
                "ref": "runtime/cortex/query/knowledge/bundle.json",
                "owner": "stack-root",
                "kind": "runtime_query_bundle",
                "why": "Knowledge bundle is the rebuildable query-plane artifact for promoted knowledge.",
            },
            {
                "ref": "docs/architecture/AWARENESS-FIRST-WORLD-MODEL.md",
                "owner": "stack-root",
                "kind": "root_doctrine",
                "why": "Awareness-first doctrine defines promotion, query, and no-dark-state behavior.",
            },
        ],
    },
    "topology/git": {
        "owner_lane": "repo inventory + lock + debt ledger",
        "routing_rule": "topology / git / repo visibility -> repo inventory + lock + debt ledger",
        "awareness_slices": ["repo_inventory", "trust_posture"],
        "route_surfaces": [
            {
                "ref": "docs/audits/STACK-REPO-INVENTORY.md",
                "owner": "stack-root",
                "kind": "root_audit",
                "why": "Rendered repo inventory is the human audit surface for topology truth.",
            },
            {
                "ref": "docs/audits/STACK-DEBT-LEDGER.md",
                "owner": "stack-root",
                "kind": "root_audit",
                "why": "Debt ledger is the current source for topology and inherited-blocker posture.",
            },
            {
                "ref": "runtime/receipts/validation/stack-validation.latest.json",
                "owner": "stack-root",
                "kind": "validation_receipt",
                "why": "Validation receipt is the current ratchet-backed topology and policy health surface.",
            },
        ],
    },
    "operator/conversation": {
        "owner_lane": "awareness + status + working memory",
        "routing_rule": "operator / chat / session / initiative -> awareness + status + working memory",
        "awareness_slices": ["active_initiatives", "pending_proposals", "waiting_on_review", "trust_posture"],
        "route_surfaces": [
            {
                "ref": "docs/architecture/AWARENESS-FIRST-WORLD-MODEL.md",
                "owner": "stack-root",
                "kind": "root_doctrine",
                "why": "Awareness-first doctrine defines the read-first client model and no-dark-state rule.",
            },
            {
                "ref": "docs/ops/ATLAS-STATUS-RUNBOOK.md",
                "owner": "stack-root",
                "kind": "root_runbook",
                "why": "Status runbook explains attention, trust, and initiative slices.",
            },
            {
                "ref": "docs/ops/ATLAS-SESSION-RUNBOOK.md",
                "owner": "stack-root",
                "kind": "root_runbook",
                "why": "Session runbook defines proposed-session and governed-session boundaries.",
            },
            {
                "ref": "docs/ops/ATLAS-INITIATIVE-RUNBOOK.md",
                "owner": "stack-root",
                "kind": "root_runbook",
                "why": "Initiative runbook defines how initiative truth sits above sessions.",
            },
            {
                "ref": "docs/ops/ATLAS-INITIATIVE-LOOP-RUNBOOK.md",
                "owner": "stack-root",
                "kind": "root_runbook",
                "why": "Initiative loop runbook explains proposal flow and attention-to-session handoff.",
            },
            {
                "ref": "runtime/cortex/catalog/memory/working-memory.latest.json",
                "owner": "stack-root",
                "kind": "runtime_catalog",
                "why": "Working-memory catalog is the rebuildable active-memory surface for operator context.",
            },
        ],
    },
}


def _normalize_intent(intent_class: str) -> str:
    normalized = intent_class.strip().lower()
    canonical = INTENT_ALIASES.get(normalized, normalized)
    if canonical not in INTENT_ROUTING:
        raise ValueError(f"Unsupported intent class: {intent_class}")
    return canonical


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "task"


def _unique_strings(values: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        candidate = value.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        ordered.append(candidate)
    return ordered


def _unique_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for record in records:
        ref = str(record.get("ref") or "")
        kind = str(record.get("kind") or "")
        key = (kind, ref)
        if not ref or key in seen:
            continue
        seen.add(key)
        ordered.append(record)
    return ordered


def _score_terms(query: str, *haystacks: str) -> int:
    normalized = _normalize_text(query).lower()
    if not normalized:
        return 0
    tokens = [token for token in normalized.split(" ") if token]
    score = 0
    for haystack in haystacks:
        text = haystack.lower()
        if normalized in text:
            score += 20
        for token in tokens:
            if token in text:
                score += 5
    return score


def _sha_for_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _path_summary(path: Path) -> str:
    if path.suffix.lower() == ".json":
        payload = read_json(path)
        for primary, secondary in (
            ("title", "summary"),
            ("display_name", "description"),
            ("id", "summary"),
            ("archive_id", "derived_summary_text"),
        ):
            if payload.get(primary):
                first = str(payload.get(primary))
                second = str(payload.get(secondary) or "")
                summary = f"{first}: {second}" if second else first
                return _normalize_text(summary)[:240]
        return _normalize_text(json.dumps(payload, ensure_ascii=True))[:240]
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return path.name
    if lines[0].startswith("#"):
        heading = lines[0].lstrip("#").strip()
        remainder = next((line for line in lines[1:] if not line.startswith("#")), "")
        summary = f"{heading}: {remainder}" if remainder else heading
        return _normalize_text(summary)[:240]
    return _normalize_text(lines[0])[:240]


def _file_record(
    ref: str,
    *,
    owner: str,
    kind: str,
    why: str,
    root: Path,
    hydration_mode: str = "full",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = resolve_atlas_path(ref, root=root)
    return {
        "ref": atlas_relative(path, root=root),
        "kind": kind,
        "owner": owner,
        "why": why,
        "title": path.name,
        "summary": _path_summary(path),
        "digest": _sha_for_path(path),
        "hydration_mode": hydration_mode,
        "details": details or {},
    }


def _slice_record(
    slice_name: str,
    slice_payload: dict[str, Any],
    *,
    why: str,
) -> dict[str, Any]:
    payload = json.loads(slice_payload["text"])
    metadata = slice_payload.get("metadata", {}) if isinstance(slice_payload.get("metadata"), dict) else {}
    return {
        "ref": f"slice:{slice_name}",
        "kind": "awareness_slice",
        "owner": "stack-root",
        "why": why,
        "title": str(slice_payload.get("title") or slice_name),
        "summary": f"{slice_name} items={metadata.get('item_count', 0)}",
        "digest": stable_json_digest(payload),
        "hydration_mode": "summary_only",
        "details": {
            "item_count": metadata.get("item_count"),
            "payload": payload,
        },
    }


def _attention_record(item: dict[str, Any], *, why: str) -> dict[str, Any]:
    return {
        "ref": f"attention:{item.get('attention_id')}",
        "kind": "attention",
        "owner": "stack-root",
        "why": why,
        "title": str(item.get("summary") or item.get("attention_id") or "attention"),
        "summary": _normalize_text(str(item.get("summary") or ""))[:240],
        "digest": stable_json_digest(item),
        "hydration_mode": "summary_only",
        "details": {
            "severity": item.get("severity"),
            "source_ref": item.get("source_ref"),
            "kind": item.get("kind"),
        },
    }


def _repo_inventory_record(entry: dict[str, Any], *, why: str) -> dict[str, Any]:
    logical_id = str(entry.get("logical_id") or entry.get("surface_id") or "")
    local_path = str(entry.get("local_path") or "")
    kind = "excluded_surface" if entry.get("surface_id") else "repo_inventory"
    ref = f"excluded_surface:{logical_id}" if kind == "excluded_surface" else f"repo:{logical_id}"
    summary = local_path
    if kind == "repo_inventory":
        summary = f"{local_path} trust={entry.get('trust_class')} dirty={entry.get('dirty')}"
    else:
        summary = f"{local_path} trust={entry.get('trust_class')} visibility={entry.get('visibility_mode')}"
    return {
        "ref": ref,
        "kind": kind,
        "owner": "stack-root",
        "why": why,
        "title": logical_id or local_path,
        "summary": summary,
        "digest": stable_json_digest(entry),
        "hydration_mode": "summary_only",
        "details": entry,
    }


def _memory_record(item: dict[str, Any], *, why: str) -> dict[str, Any]:
    memory_kind = str(item.get("memory_kind") or "memory")
    memory_id = str(item.get("id") or "")
    ref_kind = "initiative" if memory_kind == "initiative" else memory_kind
    return {
        "ref": f"{ref_kind}:{memory_id}",
        "kind": memory_kind,
        "owner": "stack-root",
        "why": why,
        "title": str(item.get("title") or memory_id),
        "summary": _normalize_text(str(item.get("summary") or item.get("title") or memory_id))[:240],
        "digest": str(item.get("content_digest") or stable_json_digest(item)),
        "hydration_mode": "summary_only",
        "details": {
            "path": item.get("path"),
            "status": item.get("status"),
            "related_plan_refs": item.get("related_plan_refs", []),
            "related_decision_refs": item.get("related_decision_refs", []),
            "related_hypothesis_refs": item.get("related_hypothesis_refs", []),
            "proposed_next_session_refs": item.get("proposed_next_session_refs", []),
            "metadata": item.get("metadata", {}),
        },
    }


def _proposal_record(proposal_payload: dict[str, Any], *, why: str) -> dict[str, Any]:
    payload = json.loads(str(proposal_payload.get("text") or "{}"))
    metadata = proposal_payload.get("metadata", {}) if isinstance(proposal_payload.get("metadata"), dict) else {}
    proposal_ref = str(metadata.get("proposal_ref") or "")
    session_payload = payload.get("proposal_session", {}) if isinstance(payload.get("proposal_session"), dict) else {}
    return {
        "ref": proposal_ref or str(proposal_payload.get("id") or ""),
        "kind": "proposal",
        "owner": "stack-root",
        "why": why,
        "title": str(payload.get("initiative_title") or proposal_payload.get("title") or "proposal"),
        "summary": _normalize_text(str(session_payload.get("title") or proposal_ref or "proposal"))[:240],
        "digest": stable_json_digest(payload),
        "hydration_mode": "summary_only",
        "details": {
            "initiative_id": payload.get("initiative_id"),
            "proposal_ref": proposal_ref,
            "session_id": session_payload.get("session_id"),
            "proposal_session": session_payload,
        },
    }


def _trust_record(item: dict[str, Any], *, why: str, root: Path) -> dict[str, Any]:
    source_ref = str(item.get("source_ref") or "")
    path = resolve_atlas_path(source_ref, root=root)
    return {
        "ref": str(item.get("knowledge_ref") or source_ref),
        "kind": "trust_posture",
        "owner": "stack-root",
        "why": why,
        "title": str(item.get("archive_id") or item.get("knowledge_ref") or "trust"),
        "summary": (
            f"trust={item.get('trust_class')} "
            f"read_mode={item.get('read_mode')} "
            f"promotion={item.get('promotion_status')}"
        ),
        "digest": _sha_for_path(path),
        "hydration_mode": str(item.get("read_mode") or "metadata_only"),
        "details": item,
    }


def _knowledge_record(item: dict[str, Any], *, why: str) -> dict[str, Any]:
    metadata = item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {}
    return {
        "ref": str(item.get("url") or item.get("archive_id") or ""),
        "kind": "knowledge",
        "owner": "stack-root",
        "why": why,
        "title": str(item.get("title") or metadata.get("archive_id") or "knowledge"),
        "summary": _normalize_text(str(item.get("text") or ""))[:240],
        "digest": stable_json_digest(item),
        "hydration_mode": "summary_only",
        "details": metadata,
    }


def _deferred_repo_record(ref: str, *, why: str) -> dict[str, Any]:
    return {
        "ref": ref,
        "kind": "deferred_repo_ref",
        "owner": "target-repo",
        "why": why,
        "title": Path(ref).name,
        "summary": ref,
        "digest": None,
        "hydration_mode": "reference_only",
        "details": {},
    }


def _resolve_target_repo_entries(
    inventory: dict[str, Any],
    *,
    repo_ids: list[str],
    repo_paths: list[str],
) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []
    for repo_id in repo_ids:
        entry = find_repo_inventory_entry(inventory, repo_id=repo_id)
        if entry is None:
            raise FileNotFoundError(f"Unknown repo id in inventory: {repo_id}")
        resolved.append(entry)
    for repo_path in repo_paths:
        normalized = repo_path.replace("\\", "/")
        entry = find_repo_inventory_entry(inventory, repo_path=normalized)
        if entry is None:
            raise FileNotFoundError(f"Unknown repo path in inventory: {repo_path}")
        resolved.append(entry)
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in resolved:
        logical_id = str(entry.get("logical_id") or "")
        if logical_id in seen:
            continue
        seen.add(logical_id)
        deduped.append(entry)
    return deduped


def _objective_query(
    objective: str,
    *,
    target_entries: list[dict[str, Any]],
    initiative_records: list[dict[str, Any]],
) -> str:
    terms = [objective]
    for entry in target_entries:
        terms.append(str(entry.get("logical_id") or ""))
        terms.append(str(entry.get("local_path") or ""))
    for initiative in initiative_records:
        terms.append(str(initiative.get("title") or ""))
    return _normalize_text(" ".join(term for term in terms if term))


def _working_memory_items_by_path(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items_by_path: dict[str, dict[str, Any]] = {}
    for item in catalog.get("items", []):
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        if path:
            items_by_path[path] = item
    return items_by_path


def _collect_related_initiatives(
    *,
    objective: str,
    target_entries: list[dict[str, Any]],
    catalog: dict[str, Any],
    root: Path,
) -> list[dict[str, Any]]:
    initiative_ids: list[str] = []
    target_repo_ids = {str(entry.get("logical_id") or "") for entry in target_entries}
    target_repo_paths = {str(entry.get("local_path") or "") for entry in target_entries}
    for entry in target_entries:
        refs = entry.get("related_initiative_refs", []) if isinstance(entry.get("related_initiative_refs"), list) else []
        for ref in refs:
            if isinstance(ref, str) and ref.startswith("initiative:"):
                initiative_ids.append(ref.split(":", 1)[1])
    for item in catalog.get("items", []):
        if not isinstance(item, dict) or str(item.get("memory_kind")) != "initiative":
            continue
        score = _score_terms(
            objective,
            str(item.get("id") or ""),
            str(item.get("title") or ""),
            str(item.get("summary") or ""),
            json.dumps(item.get("metadata", {}), ensure_ascii=True),
        )
        metadata = item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {}
        metadata_repo_id = str(metadata.get("repo_id") or "")
        metadata_repo_refs = metadata.get("repo_refs", []) if isinstance(metadata.get("repo_refs"), list) else []
        matches_target_repo = (
            not target_entries
            or metadata_repo_id in target_repo_ids
            or any(str(ref) in target_repo_paths for ref in metadata_repo_refs if isinstance(ref, str))
        )
        if score > 0 and matches_target_repo:
            initiative_ids.append(str(item.get("id") or ""))
    records: list[dict[str, Any]] = []
    for initiative_id in _unique_strings(initiative_ids):
        initiative_payload = fetch_memory(initiative_id, root=root)
        initiative_document = json.loads(str(initiative_payload.get("text") or "{}"))
        if isinstance(initiative_document, dict):
            initiative_document.setdefault("memory_kind", "initiative")
            records.append(initiative_document)
    records.sort(key=lambda item: str(item.get("title") or item.get("id") or ""))
    return records


def _collect_related_working_memory(
    *,
    catalog: dict[str, Any],
    initiative_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    items_by_path = _working_memory_items_by_path(catalog)
    related_paths: list[str] = []
    for initiative in initiative_records:
        for key in ("related_plan_refs", "related_decision_refs", "related_hypothesis_refs"):
            values = initiative.get(key, [])
            if isinstance(values, list):
                related_paths.extend(str(value) for value in values if isinstance(value, str))
    related_items = [items_by_path[path] for path in _unique_strings(related_paths) if path in items_by_path]
    related_items.sort(key=lambda item: str(item.get("title") or item.get("id") or ""))
    return related_items[:MAX_WORKING_MEMORY_ITEMS]


def _collect_related_proposals(
    *,
    initiative_records: list[dict[str, Any]],
    root: Path,
) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    for initiative in initiative_records:
        initiative_id = str(initiative.get("id") or "").strip()
        if not initiative_id:
            continue
        try:
            proposals.append(fetch(f"proposal:{initiative_id}", root=root))
        except FileNotFoundError:
            continue
    proposals.sort(key=lambda item: str(item.get("title") or item.get("id") or ""))
    return proposals


def _collect_deferred_repo_refs(
    *,
    initiative_records: list[dict[str, Any]],
    proposal_payloads: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    refs: list[str] = []
    for initiative in initiative_records:
        evidence_refs = initiative.get("evidence_refs", [])
        if isinstance(evidence_refs, list):
            refs.extend(str(ref) for ref in evidence_refs if isinstance(ref, str) and ref.startswith("repos/"))
    for proposal_payload in proposal_payloads:
        proposal_json = json.loads(str(proposal_payload.get("text") or "{}"))
        session_payload = proposal_json.get("proposal_session", {}) if isinstance(proposal_json.get("proposal_session"), dict) else {}
        proposal = session_payload.get("proposal", {}) if isinstance(session_payload.get("proposal"), dict) else {}
        supporting_refs = proposal.get("supporting_evidence_refs", [])
        if isinstance(supporting_refs, list):
            refs.extend(str(ref) for ref in supporting_refs if isinstance(ref, str) and ref.startswith("repos/"))
    records = [_deferred_repo_record(ref, why="Relevant repo-owned evidence; open only after root bootstrap is complete.") for ref in _unique_strings(refs)]
    records.sort(key=lambda item: str(item.get("ref") or ""))
    return records[:MAX_DEFERRED_REPO_REFS]


def _collect_knowledge(
    *,
    objective_query: str,
    intent_class: str,
    root: Path,
) -> list[dict[str, Any]]:
    if intent_class != "knowledge":
        return []
    payload = query_knowledge(objective_query, root=root, limit=MAX_KNOWLEDGE_ITEMS)
    records = payload.get("results", []) if isinstance(payload.get("results"), list) else []
    return [record for record in records if isinstance(record, dict)]


def _collect_initiative_attention_records(
    *,
    initiative_records: list[dict[str, Any]],
    root: Path,
) -> list[dict[str, Any]]:
    attention_snapshot = read_json(root / "runtime" / "state" / "atlas" / "world-model.attention.latest.json")
    attention_items = attention_snapshot.get("attention_items", []) if isinstance(attention_snapshot.get("attention_items"), list) else []
    wanted_refs: set[str] = set()
    initiative_paths: set[str] = set()
    for initiative in initiative_records:
        related_attention_refs = initiative.get("related_attention_refs", [])
        if isinstance(related_attention_refs, list):
            wanted_refs.update(str(ref) for ref in related_attention_refs if isinstance(ref, str))
        initiative_path = str(initiative.get("path") or "")
        if initiative_path:
            initiative_paths.add(initiative_path)
    records: list[dict[str, Any]] = []
    for item in attention_items:
        if not isinstance(item, dict):
            continue
        attention_ref = f"attention:{item.get('attention_id')}"
        source_ref = str(item.get("source_ref") or "")
        if attention_ref in wanted_refs or source_ref in initiative_paths:
            records.append(
                _attention_record(
                    item,
                    why="Current attention surface linked directly from the selected initiative.",
                )
            )
    return records


def _bootstrap_records(
    *,
    root: Path,
    slice_records: list[dict[str, Any]],
    initiative_records: list[dict[str, Any]],
    proposal_records: list[dict[str, Any]],
    trust_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    records = [
        _file_record(
            "stack.yaml",
            owner="stack-root",
            kind="root_manifest",
            why="Stack manifest is the root coordination contract and path policy source.",
            root=root,
        ),
        _file_record(
            "stack.lock.yaml",
            owner="stack-root",
            kind="root_lock",
            why="Stack lock fixes current repo and trust posture truth for this task.",
            root=root,
        ),
        _file_record(
            "docs/registry/STACK-REPO-INVENTORY.json",
            owner="stack-root",
            kind="root_inventory",
            why="Repo inventory is the root visibility surface over the polyrepo.",
            root=root,
        ),
    ]
    records.extend(slice_records)
    records.extend(initiative_records)
    records.extend(proposal_records)
    records.extend(trust_records)
    return _unique_records(records)


def build_codex_context(
    *,
    task_id: str,
    objective: str,
    intent_class: str,
    target_repo_ids: list[str] | None = None,
    target_repo_paths: list[str] | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    canonical_intent = _normalize_intent(intent_class)
    objective_text = _normalize_text(objective)
    target_repo_ids = _unique_strings(target_repo_ids or [])
    target_repo_paths = _unique_strings([path.replace("\\", "/") for path in (target_repo_paths or [])])

    stack_manifest = load_stack_config(base_root / "stack.yaml")
    stack_lock = load_stack_config(base_root / "stack.lock.yaml")
    inventory = read_json(base_root / "docs" / "registry" / "STACK-REPO-INVENTORY.json")
    status = atlas_status(root=base_root)
    working_memory_catalog = load_working_memory_catalog(base_root)

    target_entries = _resolve_target_repo_entries(
        inventory,
        repo_ids=target_repo_ids,
        repo_paths=target_repo_paths,
    )

    route_config = INTENT_ROUTING[canonical_intent]
    awareness_slice_names = list(route_config["awareness_slices"])
    if target_entries and "repo_linked_initiatives" not in awareness_slice_names:
        awareness_slice_names.append("repo_linked_initiatives")

    slice_records: list[dict[str, Any]] = []
    for slice_name in awareness_slice_names:
        slice_payload = fetch_status_slice(slice_name, root=base_root)
        slice_records.append(
            _slice_record(
                slice_name,
                slice_payload,
                why=f"Relevant awareness slice for {canonical_intent} routing.",
            )
        )

    initiative_documents = _collect_related_initiatives(
        objective=objective_text,
        target_entries=target_entries,
        catalog=working_memory_catalog,
        root=base_root,
    )
    initiative_records = [
        _memory_record(item, why="Related initiative selected from repo inventory and intent-aware search.")
        for item in initiative_documents
    ]

    proposal_payloads = _collect_related_proposals(
        initiative_records=initiative_documents,
        root=base_root,
    )
    proposal_records = [
        _proposal_record(item, why="Related proposed session selected from the initiative lane.")
        for item in proposal_payloads
    ]

    related_working_memory_docs = _collect_related_working_memory(
        catalog=working_memory_catalog,
        initiative_records=initiative_documents,
    )
    working_memory_records = [
        _memory_record(item, why="Related plan, decision, or hypothesis linked from selected initiatives.")
        for item in related_working_memory_docs
    ]

    objective_query = _objective_query(
        objective_text,
        target_entries=target_entries,
        initiative_records=initiative_documents,
    )
    attention_payload = list_attention(root=base_root, query=objective_query, limit=MAX_ATTENTION_ITEMS)
    attention_records = [
        _attention_record(item, why="Current attention surface relevant to the target repo or initiative.")
        for item in attention_payload.get("items", [])
        if isinstance(item, dict)
    ]
    attention_records.extend(
        _collect_initiative_attention_records(
            initiative_records=initiative_documents,
            root=base_root,
        )
    )

    trust_posture = status.get("trust_posture", {}) if isinstance(status.get("trust_posture"), dict) else {}
    trust_items = trust_posture.get("items", []) if isinstance(trust_posture.get("items"), list) else []
    trust_records = [
        _trust_record(item, why="Trust posture stays visible in every routed context pack.", root=base_root)
        for item in trust_items
        if isinstance(item, dict)
    ]

    route_surface_records = [
        _file_record(
            surface["ref"],
            owner=str(surface["owner"]),
            kind=str(surface["kind"]),
            why=str(surface["why"]),
            root=base_root,
        )
        for surface in route_config["route_surfaces"][:MAX_ROUTE_SURFACES]
    ]

    repo_inventory_records = [
        _repo_inventory_record(entry, why="Selected target repo inventory entry for task routing.")
        for entry in target_entries
    ]

    excluded_surface_records: list[dict[str, Any]] = []
    if canonical_intent == "topology/git":
        excluded_surface_records = [
            _repo_inventory_record(item, why="Excluded surface remains visible as metadata-only topology truth.")
            for item in inventory.get("excluded_surfaces", [])
            if isinstance(item, dict)
        ]

    knowledge_items = _collect_knowledge(
        objective_query=objective_query,
        intent_class=canonical_intent,
        root=base_root,
    )
    knowledge_records = [
        _knowledge_record(item, why="Knowledge result selected from the governed query bundle.")
        for item in knowledge_items
    ]

    deferred_repo_records = _collect_deferred_repo_refs(
        initiative_records=initiative_documents,
        proposal_payloads=proposal_payloads,
    )

    bootstrap_records = _bootstrap_records(
        root=base_root,
        slice_records=slice_records,
        initiative_records=initiative_records,
        proposal_records=proposal_records,
        trust_records=trust_records,
    )

    selected_refs = {
        "bootstrap": bootstrap_records,
        "route_surfaces": _unique_records(route_surface_records),
        "repo_inventory": _unique_records(repo_inventory_records),
        "attention": _unique_records(attention_records),
        "working_memory": _unique_records(working_memory_records),
        "knowledge": _unique_records(knowledge_records),
        "excluded_surfaces": _unique_records(excluded_surface_records),
        "deferred_repo_refs": _unique_records(deferred_repo_records),
    }

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "task_id": task_id,
        "objective": objective_text,
        "intent_class": canonical_intent,
        "target_repo_ids": [str(entry.get("logical_id") or "") for entry in target_entries],
        "target_repo_paths": [str(entry.get("local_path") or "") for entry in target_entries],
        "policy": {
            "federate_dont_duplicate": True,
            "raw_repo_truth_stays_owned": True,
            "runtime_query_artifacts_are_rebuildable": True,
            "no_raw_repo_dumps": True,
            "open_target_repo_only_after_root_bootstrap": True,
        },
        "routing": {
            "intent_class": canonical_intent,
            "owner_lane": route_config["owner_lane"],
            "rule": route_config["routing_rule"],
        },
        "selection_limits": {
            "route_surfaces": MAX_ROUTE_SURFACES,
            "attention_items": MAX_ATTENTION_ITEMS,
            "working_memory_items": MAX_WORKING_MEMORY_ITEMS,
            "knowledge_items": MAX_KNOWLEDGE_ITEMS,
            "deferred_repo_refs": MAX_DEFERRED_REPO_REFS,
        },
        "bootstrap_contract": {
            "rule": (
                "Read stack.yaml + stack.lock.yaml + docs/registry/STACK-REPO-INVENTORY.json + "
                "the relevant awareness slices + related initiative/proposal/trust refs before opening target repo docs or code."
            ),
            "ordered_reads": bootstrap_records,
        },
        "selected_refs": selected_refs,
        "digests": {
            "stack_manifest_digest": _sha_for_path(base_root / "stack.yaml"),
            "stack_lock_digest": _sha_for_path(base_root / "stack.lock.yaml"),
            "repo_inventory_digest": str(inventory.get("content_digest")),
            "registry_digest": status.get("digests", {}).get("registry_digest") if isinstance(status.get("digests"), dict) else None,
            "world_model_digest": status.get("digests", {}).get("world_model_digest") if isinstance(status.get("digests"), dict) else None,
            "attention_digest": status.get("digests", {}).get("attention_digest") if isinstance(status.get("digests"), dict) else None,
            "working_memory_digest": status.get("digests", {}).get("working_memory_digest") if isinstance(status.get("digests"), dict) else None,
            "repo_inventory_status_digest": status.get("digests", {}).get("repo_inventory_digest") if isinstance(status.get("digests"), dict) else None,
            "stack_manifest_declared_digest": str(stack_lock.get("stack_manifest_digest")),
            "repo_inventory_declared_stack_manifest_digest": str(inventory.get("stack_manifest_digest")),
            "repo_inventory_declared_stack_lock_digest": str(inventory.get("stack_lock_digest")),
        },
        "source_refs": {
            "stack_manifest_ref": "stack.yaml",
            "stack_lock_ref": "stack.lock.yaml",
            "repo_inventory_ref": "docs/registry/STACK-REPO-INVENTORY.json",
            "working_memory_ref": "runtime/cortex/catalog/memory/working-memory.latest.json",
            "knowledge_query_ref": "runtime/cortex/query/knowledge/bundle.json",
        },
        "stack_summary": {
            "name": stack_manifest.get("name"),
            "version": stack_manifest.get("version"),
            "path_mode": stack_manifest.get("path_mode"),
            "repo_registry_count": len(stack_manifest.get("repo_registry", {})),
            "lock_component_count": stack_lock.get("component_count"),
            "excluded_surface_count": inventory.get("excluded_surface_count"),
        },
    }
    payload["context_digest"] = stable_json_digest(payload)
    return payload


def render_codex_context_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Codex Context Pack: {payload['task_id']}",
        "",
        f"- Objective: `{payload['objective']}`",
        f"- Intent: `{payload['intent_class']}`",
        f"- Owner lane: `{payload['routing']['owner_lane']}`",
        f"- Routing rule: `{payload['routing']['rule']}`",
        f"- Target repos: `{', '.join(payload['target_repo_ids']) or 'none'}`",
        f"- Context digest: `{payload['context_digest']}`",
        "",
        "## Bootstrap Order",
        "",
    ]
    for index, record in enumerate(payload["bootstrap_contract"]["ordered_reads"], start=1):
        lines.append(f"{index}. `{record['ref']}` - {record['why']}")
    lines += ["", "## Selected Surfaces", ""]
    for group_name in (
        "route_surfaces",
        "repo_inventory",
        "attention",
        "working_memory",
        "knowledge",
        "excluded_surfaces",
        "deferred_repo_refs",
    ):
        records = payload["selected_refs"].get(group_name, [])
        if not records:
            continue
        lines.append(f"### {group_name.replace('_', ' ').title()}")
        lines.append("")
        for record in records:
            lines.append(f"- `{record['ref']}` - {record['summary']}")
        lines.append("")
    lines += [
        "## Rules",
        "",
        "- Federate, don't duplicate.",
        "- Raw evidence stays where it lives; promoted truth is tracked deliberately.",
        "- Runtime and query artifacts are rebuildable and should not become second truth sources.",
        "- Open target repo docs or code only after the root bootstrap contract is complete.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_codex_prompt(payload: dict[str, Any]) -> str:
    lines = [
        "ATLAS root task bootstrap",
        "",
        f"Objective: {payload['objective']}",
        f"Intent class: {payload['intent_class']}",
        f"Target repos: {', '.join(payload['target_repo_ids']) or 'none'}",
        f"Routing rule: {payload['routing']['rule']}",
        "",
        "Follow the root bootstrap contract in this order before opening target repo docs or code:",
    ]
    for index, record in enumerate(payload["bootstrap_contract"]["ordered_reads"], start=1):
        lines.append(f"{index}. Read `{record['ref']}`. Reason: {record['why']}")
    route_surfaces = payload["selected_refs"].get("route_surfaces", [])
    if route_surfaces:
        lines += ["", "After the bootstrap contract, use these owner-controlled surfaces:"]
        for record in route_surfaces:
            lines.append(f"- `{record['ref']}` ({record['owner']}): {record['why']}")
    repo_inventory = payload["selected_refs"].get("repo_inventory", [])
    if repo_inventory:
        lines += ["", "Target repo inventory entries:"]
        for record in repo_inventory:
            lines.append(f"- `{record['ref']}`: {record['summary']}")
    deferred_refs = payload["selected_refs"].get("deferred_repo_refs", [])
    if deferred_refs:
        lines += ["", "Only after the bootstrap contract, open these repo-owned refs if needed:"]
        for record in deferred_refs:
            lines.append(f"- `{record['ref']}`")
    lines += [
        "",
        "Rules:",
        "- Federate, don't duplicate.",
        "- Do not vendor child repos into ATLAS root.",
        "- Use ATLAS resources by task intent instead of dumping the whole stack into the task.",
        f"- Context digest: {payload['context_digest']}",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_codex_context_pack(
    *,
    task_id: str,
    objective: str,
    intent_class: str,
    target_repo_ids: list[str] | None = None,
    target_repo_paths: list[str] | None = None,
    root: Path | None = None,
    output_root: Path | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    runtime_root = (output_root or (base_root / DEFAULT_OUTPUT_ROOT)).resolve()
    task_dir = runtime_root / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    context_payload = payload or build_codex_context(
        task_id=task_id,
        objective=objective,
        intent_class=intent_class,
        target_repo_ids=target_repo_ids,
        target_repo_paths=target_repo_paths,
        root=base_root,
    )
    write_json(task_dir / "context.json", context_payload)
    (task_dir / "context.md").write_text(render_codex_context_markdown(context_payload), encoding="utf-8")
    return context_payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic ATLAS Codex context pack.")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--intent-class", required=True)
    parser.add_argument("--target-repo", action="append", default=[])
    parser.add_argument("--target-path", action="append", default=[])
    parser.add_argument("--output-root")
    args = parser.parse_args(argv)

    payload = write_codex_context_pack(
        task_id=_slug(args.task_id),
        objective=args.objective,
        intent_class=args.intent_class,
        target_repo_ids=args.target_repo,
        target_repo_paths=args.target_path,
        root=atlas_root(),
        output_root=Path(args.output_root).resolve() if args.output_root else None,
    )
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
