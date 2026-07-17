from __future__ import annotations

"""Deterministic source-only Cortex refresh for accepted activation events."""

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.ui_standards.validate import validate_json_schema
from ops.cortex._artifacts import sha256_bytes
from ops.validation.runtime_placement_contract import (
    validate_registry_schema_contract,
    validate_runtime_placement_payloads,
)

REFRESH_CONTRACT_VERSION = "atlas.cortex.activation-read-model-refresh.v1"
EVENT_PATH = Path("runtime/cortex/events/cortex-event-refresh.step-6.accepted.v1.json")
EVENT_SCHEMA_PATH = Path("schemas/atlas.cortex.activation-state-event.v1.json")
READ_MODEL_SCHEMA_PATH = Path("schemas/atlas.cortex.event-refreshed-read-model.v1.json")
RECEIPT_SCHEMA_PATH = Path("schemas/atlas.cortex.event-refresh-receipt.v1.json")
REGISTRY_PATH = Path("docs/registry/ATLAS-RUNTIME-PLACEMENT-REGISTRY.v1.json")
REGISTRY_SCHEMA_PATH = Path("schemas/atlas.runtime-placement.registry.v1.json")
LANE_REGISTRY_PATH = Path("docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json")
MARKER_BOOK_PATH = Path("docs/atlas-book/02-lanes-and-markers.md")
CURRENT_STATE_JSON_PATH = Path("runtime/cortex/current-state/latest.json")
CURRENT_STATE_MARKDOWN_PATH = Path("runtime/cortex/current-state/latest.md")
CONTEXT_JSON_PATH = Path("runtime/cortex/context/latest.json")
CONTEXT_MARKDOWN_PATH = Path("runtime/cortex/context/latest.md")
OPERATOR_JSON_PATH = Path("runtime/cortex/operator-surface/latest.json")
OPERATOR_MARKDOWN_PATH = Path("runtime/cortex/operator-surface/latest.md")
RECEIPT_PATH = Path("runtime/receipts/cortex/cortex-event-refresh.step-6.execution-receipt.v1.json")
PROOF_RECEIPT_PATH = Path("docs/ops/CORTEX-EVENT-TRIGGERED-RUNTIME-READ-MODEL-REFRESH-PROOF-2026-07-17.md")
TEST_PATH = Path("tests/test_cortex_activation_read_model_refresh.py")

PINNED_SOURCE_PATHS = (
    REGISTRY_PATH,
    REGISTRY_SCHEMA_PATH,
    LANE_REGISTRY_PATH,
    MARKER_BOOK_PATH,
    Path("ops/validation/runtime_placement_contract.py"),
    Path("ops/cortex/_artifacts.py"),
    Path("ops/cortex/current_state.py"),
    Path("ops/cortex/context_assembler.py"),
    Path("ops/cortex/operator_surface.py"),
    Path("runtime/cortex/shadow-agent-registry.seed.v1.json"),
    Path("docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md"),
)
TRANSFORM_PATHS = (
    Path("ops/cortex/activation_read_model_refresh.py"),
    EVENT_SCHEMA_PATH,
    READ_MODEL_SCHEMA_PATH,
    RECEIPT_SCHEMA_PATH,
)
READ_MODEL_OUTPUT_PATHS = (
    CURRENT_STATE_JSON_PATH,
    CURRENT_STATE_MARKDOWN_PATH,
    CONTEXT_JSON_PATH,
    CONTEXT_MARKDOWN_PATH,
    OPERATOR_JSON_PATH,
    OPERATOR_MARKDOWN_PATH,
)
OUTPUT_PATHS = (*READ_MODEL_OUTPUT_PATHS, RECEIPT_PATH)
PRIOR_ARTIFACT_PATHS = tuple(path.as_posix() for path in READ_MODEL_OUTPUT_PATHS)
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class RefreshError(RuntimeError):
    def __init__(self, classification: str, code: str, message: str):
        super().__init__(message)
        self.classification = classification
        self.code = code

    def payload(self) -> dict[str, str]:
        return {
            "status": "blocked",
            "classification": self.classification,
            "code": self.code,
            "message": str(self),
        }


@dataclass(frozen=True)
class RefreshBuild:
    event: dict[str, Any]
    event_digest: str
    source_set_digest: str
    outputs: dict[Path, bytes]
    receipt: dict[str, Any]


def _canonical_json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def _json_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RefreshError("malformed", "invalid_json", f"Malformed JSON at {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RefreshError("malformed", "invalid_shape", f"Expected a JSON object at {label}.")
    return payload


def _read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise RefreshError("unknown", "missing_input", f"Required input is unavailable at {label}.") from exc


def _git_output(repo_root: Path, *args: str, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=not binary,
        encoding=None if binary else "utf-8",
        errors=None if binary else "replace",
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace") if binary else completed.stderr
        raise RefreshError("stale", "git_source_unavailable", stderr.strip() or "Pinned Git source is unavailable.")
    return completed.stdout


def _git_blob(repo_root: Path, revision: str, path: Path) -> tuple[str, bytes]:
    spec = f"{revision}:{path.as_posix()}"
    oid = str(_git_output(repo_root, "rev-parse", spec)).strip()
    raw = _git_output(repo_root, "cat-file", "blob", oid, binary=True)
    assert isinstance(raw, bytes)
    return oid, raw


def _length_prefixed_digest(components: list[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for label, raw in sorted(components, key=lambda item: item[0]):
        label_raw = label.encode("utf-8")
        digest.update(len(label_raw).to_bytes(8, "big"))
        digest.update(label_raw)
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return f"sha256:{digest.hexdigest()}"


def _validate_schema(payload: dict[str, Any], schema_raw: bytes, label: str) -> None:
    schema = _json_object(schema_raw, f"schema for {label}")
    errors = validate_json_schema(payload, schema)
    if errors:
        raise RefreshError("malformed", "schema_invalid", f"{label} failed schema validation: {'; '.join(errors)}")


def _validate_relative_refs(refs: Any) -> list[str]:
    if not isinstance(refs, list) or not refs:
        raise RefreshError("malformed", "acceptance_evidence_invalid", "acceptance_evidence_refs must be non-empty.")
    normalized: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        if not isinstance(ref, str) or not ref.strip():
            raise RefreshError("malformed", "acceptance_evidence_invalid", "Acceptance evidence refs must be strings.")
        value = ref.strip()
        path = PurePosixPath(value)
        if value != path.as_posix() or path.is_absolute() or ".." in path.parts or "\\" in value:
            raise RefreshError("malformed", "acceptance_evidence_invalid", f"Non-portable evidence ref: {value}")
        if value not in seen:
            seen.add(value)
            normalized.append(value)
    return normalized


def _source_material(
    *, repo_root: Path, source_revision: str, event_raw: bytes
) -> tuple[dict[Path, bytes], list[dict[str, Any]], str, str]:
    pinned: dict[Path, bytes] = {}
    records: list[dict[str, Any]] = []
    digest_components: list[tuple[str, bytes]] = [(f"event:{EVENT_PATH.as_posix()}", event_raw)]
    for path in PINNED_SOURCE_PATHS:
        oid, raw = _git_blob(repo_root, source_revision, path)
        pinned[path] = raw
        digest_components.append((f"git:{source_revision}:{path.as_posix()}", raw))
        records.append(
            {
                "path": path.as_posix(),
                "revision": source_revision,
                "git_blob": oid,
                "sha256": sha256_bytes(raw),
                "byte_length": len(raw),
            }
        )
    for path in TRANSFORM_PATHS:
        raw = _read_bytes(repo_root / path, path.as_posix())
        digest_components.append((f"transform:{path.as_posix()}", raw))
        records.append(
            {
                "path": path.as_posix(),
                "revision": "refresh-transform",
                "git_blob": None,
                "sha256": sha256_bytes(raw),
                "byte_length": len(raw),
            }
        )
    tree = str(_git_output(repo_root, "rev-parse", f"{source_revision}^{{tree}}")).strip()
    return pinned, records, _length_prefixed_digest(digest_components), tree


def _validate_pinned_registry(
    *, repo_root: Path, pinned: dict[Path, bytes]
) -> dict[str, Any]:
    registry = _json_object(pinned[REGISTRY_PATH], REGISTRY_PATH.as_posix())
    registry_schema = _json_object(pinned[REGISTRY_SCHEMA_PATH], REGISTRY_SCHEMA_PATH.as_posix())
    lane_registry = _json_object(pinned[LANE_REGISTRY_PATH], LANE_REGISTRY_PATH.as_posix())
    marker_book = pinned[MARKER_BOOK_PATH].decode("utf-8-sig")
    issues = validate_registry_schema_contract(registry, registry_schema)
    issues.extend(validate_runtime_placement_payloads(registry, lane_registry, marker_book, root=repo_root))
    if issues:
        detail = "; ".join(f"{issue.category}:{issue.path}" for issue in issues)
        raise RefreshError("stale", "source_contract_invalid", f"Pinned runtime-placement authority is invalid: {detail}")
    return registry


def _apply_event(
    registry: dict[str, Any], event: dict[str, Any], acceptance_refs: list[str]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    change = event["change"]
    steps = registry.get("activation_steps")
    if not isinstance(steps, list):
        raise RefreshError("stale", "source_steps_invalid", "Pinned activation steps are unavailable.")
    unresolved = [step for step in steps if isinstance(step, dict) and step.get("status") != "accepted"]
    if not unresolved:
        raise RefreshError("stale", "source_already_complete", "Pinned activation sequence has no unresolved step.")
    selected = unresolved[0]
    if registry.get("next_owner_side_activation_packet") != change.get("selector_before"):
        raise RefreshError("stale", "selector_before_stale", "Trigger selector_before does not match pinned authority.")
    if selected.get("id") != change.get("activation_step_id") or selected.get("order") != change.get("order"):
        raise RefreshError("stale", "step_selection_stale", "Trigger does not target the first unresolved activation step.")
    if selected.get("status") != change.get("from_status"):
        raise RefreshError("stale", "from_status_stale", "Trigger from_status does not match pinned authority.")
    if event.get("event_status") != "accepted" or change.get("to_status") != "accepted":
        raise RefreshError("not_accepted", "trigger_not_accepted", "Only an explicitly accepted activation-state event may refresh Cortex.")

    derived = copy.deepcopy(registry)
    target = next(step for step in derived["activation_steps"] if step["id"] == change["activation_step_id"])
    target["status"] = "accepted"
    target["evidence_refs"] = acceptance_refs
    remaining = [step for step in derived["activation_steps"] if step.get("status") != "accepted"]
    selector_after = remaining[0]["packet"] if remaining else None
    if selector_after != change.get("selector_after"):
        raise RefreshError("conflict", "selector_after_conflict", "Trigger selector_after conflicts with the frozen activation sequence.")
    derived["next_owner_side_activation_packet"] = selector_after

    resolved_unknowns = event.get("resolved_unknowns", [])
    source_unknowns = list(registry.get("current_unknowns", []))
    if not isinstance(resolved_unknowns, list) or not resolved_unknowns:
        raise RefreshError("malformed", "resolved_unknowns_invalid", "Trigger must name the stale Cortex UNKNOWN it resolves.")
    missing_unknowns = [item for item in resolved_unknowns if item not in source_unknowns]
    if missing_unknowns:
        raise RefreshError("stale", "resolved_unknown_stale", "Trigger resolves an UNKNOWN absent from pinned authority.")
    derived["current_unknowns"] = [item for item in source_unknowns if item not in resolved_unknowns]

    before_statuses = {step["id"]: step["status"] for step in registry["activation_steps"]}
    after_statuses = {step["id"]: step["status"] for step in derived["activation_steps"]}
    changed = [step_id for step_id in before_statuses if before_statuses[step_id] != after_statuses[step_id]]
    if changed != [change["activation_step_id"]]:
        raise RefreshError("conflict", "change_cardinality_conflict", "Accepted event must change exactly one activation step.")
    return derived, selected, remaining[0] if remaining else {}


def _source_ref(source_revision: str, registry_component: dict[str, Any]) -> str:
    return f"git:{source_revision}:{REGISTRY_PATH.as_posix()}@{registry_component['git_blob']}"


def _shadow_agent_summary(agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent_id": agent.get("id"),
        "contract_id": agent.get("contract_id"),
        "family_name": agent.get("family_name"),
        "trigger": agent.get("trigger"),
        "admissibility_state": agent.get("admissibility_state"),
        "stage": agent.get("stage"),
        "runnable": agent.get("runnable"),
        "owner_boundary": agent.get("owner_boundary"),
        "non_claim_boundary": agent.get("non_claim_boundary"),
    }


def _build_read_models(
    *,
    event: dict[str, Any],
    event_digest: str,
    source_set_digest: str,
    source_components: list[dict[str, Any]],
    source_tree: str,
    registry: dict[str, Any],
    derived: dict[str, Any],
    selected_before: dict[str, Any],
    selected_after: dict[str, Any],
    acceptance_refs: list[str],
    shadow_registry: dict[str, Any],
) -> dict[Path, bytes]:
    generated_at = event["occurred_at"]
    source_revision = event["source"]["commit"]
    registry_component = next(item for item in source_components if item["path"] == REGISTRY_PATH.as_posix())
    source_authority = {
        "repository": event["source"]["repository"],
        "ref": event["source"]["ref"],
        "commit": source_revision,
        "tree": source_tree,
        "registry_path": REGISTRY_PATH.as_posix(),
        "registry_git_blob": registry_component["git_blob"],
        "registry_sha256": registry_component["sha256"],
    }
    refresh = {
        "event_id": event["event_id"],
        "event_digest": event_digest,
        "event_ref": EVENT_PATH.as_posix(),
        "source_set_digest": source_set_digest,
        "transition": {
            "activation_step_id": event["change"]["activation_step_id"],
            "from_status": event["change"]["from_status"],
            "to_status": event["change"]["to_status"],
            "selector_before": event["change"]["selector_before"],
            "selector_after": event["change"]["selector_after"],
            "changed_step_count": 1,
        },
    }
    blocked = [
        {"step_id": step["id"], "packet": step["packet"], "status": step["status"]}
        for step in derived["activation_steps"]
        if step["status"] == "blocked"
    ]
    pending = [
        {"step_id": step["id"], "packet": step["packet"], "status": step["status"]}
        for step in derived["activation_steps"]
        if step["status"] == "pending"
    ]
    status_boundaries = {
        "unknown": list(derived["current_unknowns"]),
        "blocked": blocked,
        "stale": [],
        "pending": pending,
        "resolved_stale": event["prior_artifacts"],
    }
    marker_snapshot = [
        {
            "id": marker["id"],
            "title": marker["title"],
            "completed_units": marker["completed_units"],
            "denominator": marker["denominator"],
            "percentage": marker["percentage"],
        }
        for marker in derived["marker_lanes"]
    ]
    next_lane = {
        "lane_id": selected_after.get("id"),
        "owner_layer": selected_after.get("owner"),
        "packet": selected_after.get("packet"),
        "status": selected_after.get("status"),
        "rationale": "The selector advances to the first non-accepted step in the frozen activation sequence.",
        "blocked_by": [],
        "source_refs": acceptance_refs,
    }
    eligible_agents = [
        agent
        for agent in shadow_registry.get("agents", [])
        if isinstance(agent, dict) and agent.get("admissibility_state") == "shadow-only"
    ]
    blocked_agents = [
        agent
        for agent in shadow_registry.get("agents", [])
        if isinstance(agent, dict) and agent.get("admissibility_state") == "blocked"
    ]
    projected_agents: list[dict[str, Any]] = []
    for agent in sorted(eligible_agents, key=lambda item: str(item.get("id", ""))):
        agent_id = str(agent.get("id", ""))
        authority: dict[str, bool] = {"can_mutate_truth": False, "has_production_authority": False}
        if agent_id == "marker-checkpoint-shadow":
            authority["can_ratchet_markers"] = False
        elif agent_id == "receipt-doctrine-draft-shadow":
            authority["can_admit_doctrine"] = False
            authority["can_finalize_receipts"] = False
        elif agent_id == "validation-summary-shadow":
            authority["can_waive_findings"] = False
        projected_agents.append(
            {
                "agent_id": agent_id,
                "contract_id": agent.get("contract_id"),
                "family_name": agent.get("family_name"),
                "trigger": agent.get("trigger"),
                "admissibility_state": agent.get("admissibility_state"),
                "artifact_ref": f"runtime/cortex/shadow-agent-consumption/{agent_id.removesuffix('-shadow')}.latest.json",
                "contract_version": "atlas.cortex.source-only-shadow-projection.v1",
                "generated_at": generated_at,
                "consumption_status": "source-only-projected",
                "stage": agent.get("stage"),
                "authority": authority,
            }
        )
    common = {
        "refresh_contract_version": REFRESH_CONTRACT_VERSION,
        "generated_at": generated_at,
        "stack_root": ".",
        "source_authority": source_authority,
        "refresh": refresh,
        "status_boundaries": status_boundaries,
        "source_refs": [
            _source_ref(source_revision, registry_component),
            EVENT_PATH.as_posix(),
            *acceptance_refs,
        ],
    }
    validation_unknowns = {"critical": None, "error": None, "warning": None, "info": None, "total": None}
    current = {
        "contract_version": "atlas.cortex.current-state.v1",
        "model_kind": "current_state",
        **common,
        "authority": {
            "mode": "source-only-advisory",
            "read_only": True,
            "owner_health_inference": False,
            "external_mutation": False,
        },
        "branch": "main",
        "head": source_revision,
        "worktree_status": "source-only",
        "changed_files": [],
        "untracked_files": [],
        "retained_untracked_files": [],
        "remote_status": {"status": "pinned", "upstream": "origin/main", "ahead": None, "behind": None},
        "remote_publication_state": {
            "status": "pinned-source-only",
            "branch": "main",
            "head": source_revision,
            "published": True,
            "upstream": "origin/main",
            "pr_state": None,
            "pr_url": None,
            "notes": ["No owner health or mutable checkout state was sampled."],
        },
        "validation_receipt": {
            "status": "UNKNOWN",
            "generated_at": None,
            "path": None,
            "counts": validation_unknowns,
            "reason": "Source-only refresh does not infer current owner or runtime health.",
        },
        "validation_counts": validation_unknowns,
        "active_blockers": blocked,
        "latest_clean_step": {
            "step_id": selected_before["id"],
            "owner_layer": selected_before["owner"],
            "summary": selected_before["admission_proof"],
            "status": "accepted",
            "evidence": acceptance_refs,
            "source_inputs": [EVENT_PATH.as_posix(), _source_ref(source_revision, registry_component)],
            "completed_at": generated_at,
            "source_ref": EVENT_PATH.as_posix(),
        },
        "rail_state": None,
        "operator_surface_projection": {
            "artifact_ref": OPERATOR_JSON_PATH.as_posix(),
            "artifact_generated_at": generated_at,
            "authority": "read-only-advisory",
        },
        "activation": {
            "source_registry_generated_at": registry["generated_at"],
            "accepted_prefix_count": 6,
            "sequence": list(derived["activation_sequence"]),
            "steps": list(derived["activation_steps"]),
            "selector_before": event["change"]["selector_before"],
            "selector_after": event["change"]["selector_after"],
        },
        "marker_snapshot": marker_snapshot,
        "next_recommended_lane": next_lane,
    }
    context = {
        "contract_version": "atlas.cortex.context-packet.v1",
        "model_kind": "context",
        **common,
        "packet_id": f"context-{selected_after.get('id')}",
        "active_rail": "runtime-placement-activation",
        "rail_status": "source-only",
        "context_summary": f"Source-only Cortex context for {selected_after.get('packet')}.",
        "posture_snapshot": {
            "branch": "main",
            "head": source_revision,
            "worktree_status": "source-only",
            "active_blocker_count": len(blocked),
            "latest_clean_step_id": selected_before["id"],
            "dirty_lanes": [],
            "validation_status": "UNKNOWN",
            "validation_counts": validation_unknowns,
        },
        "task_frame": {
            "lane_id": selected_after.get("id"),
            "owner_layer": selected_after.get("owner"),
            "title": selected_after.get("packet"),
            "status": selected_after.get("status"),
            "rationale": selected_after.get("admission_proof"),
            "blocked_by": [],
            "required_inputs": list(selected_after.get("evidence_refs", [])),
            "verification_steps": [],
            "receipt_scope": "Owner-side DiscordOS reliability review only; no Cortex or root mutation authority is inferred.",
            "ready_to_execute": False,
        },
        "deferred_lane": None,
        "rule_highlights": [],
        "workflow_profile": None,
        "operator_surface_projection": current["operator_surface_projection"],
        "boundary_reminders": [
            "Cortex observes, interprets, and proves.",
            "Unavailable owner and runtime surfaces remain UNKNOWN.",
            "No Discord, board, repository, scheduler, service, database, secret, or production mutation is authorized.",
        ],
        "evidence_list": [
            {"ref": _source_ref(source_revision, registry_component), "kind": "immutable_git_blob", "role": "pinned root authority"},
            {"ref": EVENT_PATH.as_posix(), "kind": "accepted_activation_event", "role": "single refresh trigger"},
            {"ref": RECEIPT_PATH.as_posix(), "kind": "refresh_receipt", "role": "correlated output proof"},
        ],
    }
    operator = {
        "contract_version": "atlas.cortex.operator-surface.v1",
        "model_kind": "operator_surface",
        **common,
        "operator_summary": f"Cortex operator readback selects {selected_after.get('packet')} without owner-health inference.",
        "active_rail": "runtime-placement-activation",
        "rail_status": "source-only",
        "next_recommended_lane": next_lane,
        "active_blockers": blocked,
        "dirty_lanes": [],
        "validation_status": "UNKNOWN",
        "validation_counts": validation_unknowns,
        "context_packet_id": context["packet_id"],
        "context_summary": context["context_summary"],
        "task_frame_summary": context["task_frame"],
        "top_evidence_refs": context["source_refs"],
        "boundary_reminders": context["boundary_reminders"],
        "publication_posture": {
            "branch": "main",
            "head": source_revision,
            "worktree_status": "source-only",
            "remote_status": "pinned",
            "upstream": "origin/main",
            "published": True,
            "pr_state": None,
            "pr_url": None,
        },
        "marker_snapshot": marker_snapshot,
        "authority": {
            "read_only": True,
            "advisory": True,
            "owner_health_inference": False,
            "repository_mutation": False,
            "discord_mutation": False,
            "board_mutation": False,
            "deployment": False,
            "database_mutation": False,
            "secret_access": False,
            "scheduler_or_service_creation": False,
        },
        "shadow_agents": {
            "registry_ref": "runtime/cortex/shadow-agent-registry.seed.v1.json",
            "source_receipts": list(shadow_registry.get("source_receipts", [])),
            "exportable_contract_ids": [],
            "shadow_contract_ids": [agent.get("contract_id") for agent in eligible_agents],
            "blocked_contract_ids": [agent.get("contract_id") for agent in blocked_agents],
            "eligible_agent_ids": [agent.get("id") for agent in eligible_agents],
            "blocked_agent_ids": [agent.get("id") for agent in blocked_agents],
            "eligible_agents": [_shadow_agent_summary(agent) for agent in eligible_agents],
            "blocked_agents": [_shadow_agent_summary(agent) for agent in blocked_agents],
        },
        "shadow_consumption": {
            "artifact_root": "runtime/cortex/shadow-agent-consumption",
            "projected_agent_ids": [agent["agent_id"] for agent in projected_agents],
            "projected_contract_ids": [agent["contract_id"] for agent in projected_agents],
            "missing_eligible_agent_ids": [],
            "missing_eligible_contract_ids": [],
            "consumed_agents": projected_agents,
        },
    }

    payloads = {
        CURRENT_STATE_JSON_PATH: current,
        CONTEXT_JSON_PATH: context,
        OPERATOR_JSON_PATH: operator,
    }
    outputs: dict[Path, bytes] = {path: _canonical_json_bytes(payload) for path, payload in payloads.items()}
    outputs[CURRENT_STATE_MARKDOWN_PATH] = _render_current_markdown(current, sha256_bytes(outputs[CURRENT_STATE_JSON_PATH])).encode("utf-8")
    outputs[CONTEXT_MARKDOWN_PATH] = _render_context_markdown(context, sha256_bytes(outputs[CONTEXT_JSON_PATH])).encode("utf-8")
    outputs[OPERATOR_MARKDOWN_PATH] = _render_operator_markdown(operator, sha256_bytes(outputs[OPERATOR_JSON_PATH])).encode("utf-8")
    return outputs


def _render_current_markdown(payload: dict[str, Any], json_digest: str) -> str:
    activation = payload["activation"]
    return (
        "# Cortex Current State\n\n"
        f"- Generated: `{payload['generated_at']}`\n"
        f"- Source commit: `{payload['head']}`\n"
        f"- Trigger: `{payload['refresh']['event_id']}`\n"
        f"- JSON digest: `{json_digest}`\n"
        f"- Accepted activation prefix: `{activation['accepted_prefix_count']} / 8`\n"
        f"- Selector before: `{activation['selector_before']}`\n"
        f"- Selector after: `{activation['selector_after']}`\n"
        "- Owner/runtime health: `UNKNOWN` (not inferred)\n\n"
        "## Status Boundaries\n\n"
        f"- UNKNOWN: `{len(payload['status_boundaries']['unknown'])}`\n"
        f"- Blocked: `{len(payload['status_boundaries']['blocked'])}`\n"
        f"- Stale: `{len(payload['status_boundaries']['stale'])}`\n"
        f"- Pending: `{len(payload['status_boundaries']['pending'])}`\n"
    )


def _render_context_markdown(payload: dict[str, Any], json_digest: str) -> str:
    frame = payload["task_frame"]
    return (
        "# Cortex Context Packet\n\n"
        f"- Generated: `{payload['generated_at']}`\n"
        f"- Packet id: `{payload['packet_id']}`\n"
        f"- JSON digest: `{json_digest}`\n"
        f"- Next packet: `{frame['title']}`\n"
        f"- Status: `{frame['status']}`\n"
        "- Owner/runtime health: `UNKNOWN` (not inferred)\n\n"
        "## Boundary\n\n"
        "- Read-only advisory projection.\n"
        "- Discord mutation remains false.\n"
        "- No daemon, scheduler, standing server, or second queue is created.\n"
    )


def _render_operator_markdown(payload: dict[str, Any], json_digest: str) -> str:
    lane = payload["next_recommended_lane"]
    return (
        "# Cortex Operator Surface\n\n"
        f"- Generated: `{payload['generated_at']}`\n"
        f"- JSON digest: `{json_digest}`\n"
        f"- Next packet: `{lane['packet']}`\n"
        f"- Status: `{lane['status']}`\n"
        "- Validation/owner health: `UNKNOWN`\n"
        "- Discord mutation authorized: `false`\n"
        "- External mutation authorized: `false`\n"
    )


def _build_receipt(
    *,
    event: dict[str, Any],
    event_digest: str,
    source_set_digest: str,
    source_components: list[dict[str, Any]],
    source_tree: str,
    outputs: dict[Path, bytes],
) -> dict[str, Any]:
    output_records = [
        {
            "path": path.as_posix(),
            "sha256": sha256_bytes(outputs[path]),
            "byte_length": len(outputs[path]),
            "generated_at": event["occurred_at"],
        }
        for path in READ_MODEL_OUTPUT_PATHS
    ]
    output_set_digest = _length_prefixed_digest(
        [(path.as_posix(), outputs[path]) for path in READ_MODEL_OUTPUT_PATHS]
    )
    return {
        "schema_version": "atlas.cortex.event-refresh-receipt.v1",
        "receipt_id": "cortex-event-refresh-step-6-90f9de1d",
        "event_id": event["event_id"],
        "event_digest": event_digest,
        "recorded_at": event["occurred_at"],
        "status": "accepted",
        "outcome": "refreshed",
        "refresh_count": 1,
        "source_authority": {
            "repository": event["source"]["repository"],
            "ref": event["source"]["ref"],
            "commit": event["source"]["commit"],
            "tree": source_tree,
        },
        "source_set_digest": source_set_digest,
        "source_components": source_components,
        "state_change": {
            **event["change"],
            "changed_step_count": 1,
            "step_7_status": "pending",
            "step_8_status": "pending",
        },
        "prior_artifacts": event["prior_artifacts"],
        "generated_outputs": output_records,
        "deterministic_replay": {
            "same_inputs_byte_stable": True,
            "output_set_digest": output_set_digest,
            "idempotent_duplicate_outcome": "noop",
            "conflicting_duplicate_outcome": "rejected",
        },
        "verification": {
            "event_schema": "passed",
            "pinned_registry_schema": "passed",
            "pinned_registry_semantics": "passed",
            "read_model_schema": "passed",
            "receipt_schema": "passed",
            "single_state_change": "passed",
            "source_only_authority": "passed",
        },
        "unchanged_markers": event["unchanged_markers"],
        "historical_snapshots_mutated": False,
        "authority": {
            "read_only": True,
            "advisory": True,
            "owner_health_inference": False,
            "repository_mutation": False,
            "discord_mutation": False,
            "board_mutation": False,
            "vercel_mutation": False,
            "supabase_mutation": False,
            "database_mutation": False,
            "secret_access": False,
            "scheduler_or_service_creation": False,
            "production_mutation": False,
        },
        "next_packet": event["change"]["selector_after"],
    }


def build_refresh(
    *,
    repo_root: Path = ROOT,
    event_path: Path | None = None,
    expected_source_revision: str | None = None,
) -> RefreshBuild:
    root = repo_root.resolve()
    resolved_event = (event_path or root / EVENT_PATH).resolve()
    event_raw = _read_bytes(resolved_event, EVENT_PATH.as_posix())
    event = _json_object(event_raw, EVENT_PATH.as_posix())
    _validate_schema(event, _read_bytes(root / EVENT_SCHEMA_PATH, EVENT_SCHEMA_PATH.as_posix()), EVENT_PATH.as_posix())
    event_digest = sha256_bytes(event_raw)
    source_revision = event["source"]["commit"]
    if not COMMIT_PATTERN.fullmatch(source_revision):
        raise RefreshError("malformed", "source_revision_invalid", "Trigger source commit must be a full lowercase Git commit.")
    if expected_source_revision is not None and source_revision != expected_source_revision:
        raise RefreshError("stale", "source_revision_stale", "Trigger source commit does not match the admitted source revision.")
    pinned, source_components, source_set_digest, source_tree = _source_material(
        repo_root=root, source_revision=source_revision, event_raw=event_raw
    )
    if source_tree != event["source"]["tree"]:
        raise RefreshError("stale", "source_tree_stale", "Trigger source tree does not match the pinned commit.")
    registry_component = next(item for item in source_components if item["path"] == REGISTRY_PATH.as_posix())
    if (
        registry_component["git_blob"] != event["source"]["registry_git_blob"]
        or registry_component["sha256"] != event["source"]["registry_sha256"]
    ):
        raise RefreshError("stale", "registry_source_stale", "Trigger registry blob binding does not match pinned Git authority.")
    registry = _validate_pinned_registry(repo_root=root, pinned=pinned)
    acceptance_refs = _validate_relative_refs(event["acceptance_evidence_refs"])
    prior_paths = [item.get("path") for item in event["prior_artifacts"] if isinstance(item, dict)]
    if tuple(prior_paths) != PRIOR_ARTIFACT_PATHS:
        raise RefreshError("conflict", "prior_artifact_set_conflict", "Trigger prior-artifact set must name the six principal Cortex latest outputs exactly.")
    derived, selected_before, selected_after = _apply_event(registry, event, acceptance_refs)
    shadow_registry_path = Path("runtime/cortex/shadow-agent-registry.seed.v1.json")
    shadow_registry = _json_object(pinned[shadow_registry_path], shadow_registry_path.as_posix())
    outputs = _build_read_models(
        event=event,
        event_digest=event_digest,
        source_set_digest=source_set_digest,
        source_components=source_components,
        source_tree=source_tree,
        registry=registry,
        derived=derived,
        selected_before=selected_before,
        selected_after=selected_after,
        acceptance_refs=acceptance_refs,
        shadow_registry=shadow_registry,
    )
    read_model_schema_raw = _read_bytes(root / READ_MODEL_SCHEMA_PATH, READ_MODEL_SCHEMA_PATH.as_posix())
    for path in (CURRENT_STATE_JSON_PATH, CONTEXT_JSON_PATH, OPERATOR_JSON_PATH):
        _validate_schema(_json_object(outputs[path], path.as_posix()), read_model_schema_raw, path.as_posix())
    receipt = _build_receipt(
        event=event,
        event_digest=event_digest,
        source_set_digest=source_set_digest,
        source_components=source_components,
        source_tree=source_tree,
        outputs=outputs,
    )
    _validate_schema(receipt, _read_bytes(root / RECEIPT_SCHEMA_PATH, RECEIPT_SCHEMA_PATH.as_posix()), RECEIPT_PATH.as_posix())
    outputs[RECEIPT_PATH] = _canonical_json_bytes(receipt)
    return RefreshBuild(event, event_digest, source_set_digest, outputs, receipt)


def _matching_prior_output_set(build: RefreshBuild, *, output_root: Path) -> bool:
    expected = {
        Path(item["path"]): item["sha256"]
        for item in build.event["prior_artifacts"]
    }
    return all(
        (output_root / path).is_file()
        and sha256_bytes((output_root / path).read_bytes()) == expected[path]
        for path in READ_MODEL_OUTPUT_PATHS
    )


def _replace_path(source: Path, target: Path) -> None:
    source.replace(target)


def _rollback_outputs(
    *,
    output_root: Path,
    stage_root: Path,
    originals: dict[Path, bytes],
) -> list[str]:
    errors: list[str] = []
    for index, path in enumerate(OUTPUT_PATHS):
        target = output_root / path
        try:
            if path in originals:
                rollback_source = stage_root / f"rollback-{index:02d}"
                rollback_source.write_bytes(originals[path])
                _replace_path(rollback_source, target)
            elif target.exists():
                target.unlink()
        except OSError as exc:
            errors.append(f"{path.as_posix()}: {exc}")
    return errors


def _publish_outputs(build: RefreshBuild, *, output_root: Path) -> None:
    originals = {
        path: (output_root / path).read_bytes()
        for path in OUTPUT_PATHS
        if (output_root / path).is_file()
    }
    try:
        output_root.mkdir(parents=True, exist_ok=True)
        for path in OUTPUT_PATHS:
            (output_root / path).parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=".cortex-refresh-",
            dir=output_root,
            ignore_cleanup_errors=True,
        ) as temporary:
            stage_root = Path(temporary)
            staged: dict[Path, Path] = {}
            for index, path in enumerate(OUTPUT_PATHS):
                stage_path = stage_root / f"publish-{index:02d}"
                stage_path.write_bytes(build.outputs[path])
                staged[path] = stage_path
            try:
                for path in OUTPUT_PATHS:
                    _replace_path(staged[path], output_root / path)
            except OSError as exc:
                rollback_errors = _rollback_outputs(
                    output_root=output_root,
                    stage_root=stage_root,
                    originals=originals,
                )
                if rollback_errors:
                    raise RefreshError(
                        "write_failure",
                        "publication_rollback_failed",
                        "Cortex output publication failed and rollback was incomplete: "
                        + "; ".join(rollback_errors),
                    ) from exc
                raise RefreshError(
                    "write_failure",
                    "publication_failed_rolled_back",
                    f"Cortex output publication failed and the prior set was restored: {exc}",
                ) from exc
    except RefreshError:
        raise
    except OSError as exc:
        raise RefreshError(
            "write_failure",
            "output_staging_failed",
            f"Cortex outputs could not be staged; no output was published: {exc}",
        ) from exc


def write_or_check(build: RefreshBuild, *, output_root: Path, check: bool) -> str:
    root = output_root.resolve()
    matches = {
        path: (root / path).is_file() and (root / path).read_bytes() == raw
        for path, raw in build.outputs.items()
    }
    if all(matches.values()):
        return "noop"
    receipt_target = root / RECEIPT_PATH
    existing_targets = [path for path in build.outputs if (root / path).exists()]
    if receipt_target.exists():
        existing_receipt = _json_object(receipt_target.read_bytes(), RECEIPT_PATH.as_posix())
        if (
            existing_receipt.get("event_id") != build.event.get("event_id")
            or existing_receipt.get("event_digest") != build.event_digest
        ):
            raise RefreshError("conflict", "duplicate_event_conflict", "Existing refresh receipt conflicts with this event.")
        raise RefreshError("conflict", "duplicate_output_conflict", "Existing outputs drifted for an already-recorded event.")
    if existing_targets:
        if set(existing_targets) != set(READ_MODEL_OUTPUT_PATHS):
            raise RefreshError("conflict", "partial_output_conflict", "Partial outputs exist without the correlated refresh receipt.")
        if not _matching_prior_output_set(build, output_root=root):
            raise RefreshError(
                "conflict",
                "prior_output_conflict",
                "Complete receipt-less outputs do not match the prior artifact digests admitted by the event.",
            )
    if check:
        raise RefreshError("stale", "output_drift", "Expected event-refreshed Cortex outputs are missing or stale.")
    _publish_outputs(build, output_root=root)
    return "refreshed"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--event", type=Path)
    parser.add_argument("--source-revision")
    parser.add_argument("--output-root", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    try:
        build = build_refresh(
            repo_root=root,
            event_path=args.event.resolve() if args.event else None,
            expected_source_revision=args.source_revision,
        )
        outcome = write_or_check(
            build,
            output_root=(args.output_root or root).resolve(),
            check=args.check,
        )
    except RefreshError as exc:
        print(json.dumps(exc.payload(), sort_keys=True), file=sys.stderr)
        return 2
    result = {
        "status": "ok",
        "outcome": outcome,
        "event_id": build.event["event_id"],
        "event_digest": build.event_digest,
        "source_set_digest": build.source_set_digest,
        "output_set_digest": build.receipt["deterministic_replay"]["output_set_digest"],
        "refresh_count": 0 if outcome == "noop" else 1,
        "next_packet": build.receipt["next_packet"],
        "discord_mutation_authorized": False,
    }
    if args.json or not args.check:
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
