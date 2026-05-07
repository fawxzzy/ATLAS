from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes
from ops.cortex._artifacts import stable_json_digest, write_json
from ops.cortex.context_assembler import default_context_latest_json_path
from ops.cortex.kernel import default_rule_registry_path, default_state_model_path
from ops.cortex.ledger import default_ledger_latest_json_path
from ops.cortex.operator_surface import default_operator_surface_latest_json_path
from ops.cortex.worker_prompt import (
    WORKER_PROMPT_AUTHORITY_LEVEL,
    WORKER_PROMPT_CONTRACT_VERSION,
    default_worker_prompt_latest_json_path,
)

STACK_CONSUMPTION_PILOT_CONTRACT_VERSION = "atlas.cortex.stack-consumption-pilot.v1"
STACK_CONSUMPTION_PILOT_AUTHORITY_LEVEL = "read_only_advisory"
STACK_CONSUMER_ID = "_stack"


def stack_consumption_pilot_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "stack-consumption-pilot"


def default_stack_consumption_pilot_latest_json_path(root: Path | None = None) -> Path:
    return stack_consumption_pilot_root(root) / "latest.json"


def default_stack_consumption_pilot_latest_markdown_path(root: Path | None = None) -> Path:
    return stack_consumption_pilot_root(root) / "latest.md"


@dataclass(frozen=True)
class PersistedStackConsumptionPilotArtifact:
    artifact_path: Path
    summary_path: Path | None
    payload_digest: str
    payload: dict[str, Any]
    summary: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {normalize_slashes(str(path))}.")
    return payload


def _require_json_object(path: Path, *, label: str) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"{label} not found: {normalize_slashes(str(resolved))}")
    return _read_json_object(resolved)


def _ordered_unique_strings(values: list[Any]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _separation_ref(worker_prompt_payload: dict[str, Any], key: str) -> str | None:
    section = _dict(_dict(worker_prompt_payload.get("separation_refs")).get(key))
    ref = section.get("ref")
    return ref.strip() if isinstance(ref, str) and ref.strip() else None


def _separation_status(worker_prompt_payload: dict[str, Any], key: str) -> str:
    section = _dict(_dict(worker_prompt_payload.get("separation_refs")).get(key))
    return _string(section.get("status"))


def _transcript_refs(values: list[str]) -> list[str]:
    suspicious: list[str] = []
    for value in values:
        lowered = value.lower()
        if "transcript" in lowered or "runtime/atlas/conversations" in lowered or "runtime/atlas/sessions" in lowered:
            suspicious.append(value)
    return _ordered_unique_strings(suspicious)


def _check(check_id: str, passed: bool, summary: str, *, source_ref: str | None = None) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "passed" if passed else "failed",
        "summary": summary,
        "source_ref": source_ref,
    }


def _authority_guards() -> list[str]:
    return [
        "Pilot is advisory only and does not dispatch _stack work.",
        "Pilot consumes explicit Cortex artifacts only; transcript scraping is not allowed.",
        "Pilot does not mutate owner repos, stack.yaml, Lifeline receipt authority, Playbook governance truth, or product truth.",
        "Planner, context, proof, receipt-draft, and final receipt remain separately referenceable by refs and digests.",
    ]


def _source_refs(
    *,
    worker_prompt_payload: dict[str, Any],
    worker_prompt_ref: str,
    context_ref: str,
    operator_surface_ref: str,
    ledger_ref: str,
    state_model_ref: str,
    rule_registry_ref: str,
) -> list[str]:
    values: list[Any] = [
        worker_prompt_ref,
        context_ref,
        operator_surface_ref,
        ledger_ref,
        state_model_ref,
        rule_registry_ref,
        *_list(worker_prompt_payload.get("source_refs")),
        *_list(worker_prompt_payload.get("top_evidence_refs")),
        _separation_ref(worker_prompt_payload, "planner"),
        _separation_ref(worker_prompt_payload, "context"),
        _separation_ref(worker_prompt_payload, "proof"),
        _separation_ref(worker_prompt_payload, "receipt_draft"),
        _separation_ref(worker_prompt_payload, "final_receipt"),
    ]
    return _ordered_unique_strings(values)


def _stack_handoff(worker_prompt_payload: dict[str, Any], *, worker_prompt_ref: str, context_ref: str) -> dict[str, Any]:
    return {
        "consumer_id": STACK_CONSUMER_ID,
        "consumption_mode": "artifact_refs_only",
        "worker_prompt_ref": worker_prompt_ref,
        "worker_prompt_contract_version": _string(worker_prompt_payload.get("contract_version")),
        "planner_ref": _separation_ref(worker_prompt_payload, "planner"),
        "context_ref": context_ref,
        "proof_ref": _separation_ref(worker_prompt_payload, "proof"),
        "receipt_draft_ref": _separation_ref(worker_prompt_payload, "receipt_draft"),
        "final_receipt_ref": _separation_ref(worker_prompt_payload, "final_receipt"),
        "execution_authorized": False,
        "receipt_authorized": False,
        "owner_truth_mutation_authorized": False,
        "default_routing_enabled": False,
        "transcript_scraping_allowed": False,
    }


def _advisory_assignment(worker_prompt_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": _string(worker_prompt_payload.get("run_id")),
        "assignment_id": _string(worker_prompt_payload.get("assignment_id")),
        "stack_lock_digest": _string(worker_prompt_payload.get("stack_lock_digest")),
        "owner_layer": _string(worker_prompt_payload.get("owner_layer")),
        "objective": _string(worker_prompt_payload.get("objective")),
        "implementation_plan": _ordered_unique_strings(_list(worker_prompt_payload.get("implementation_plan"))),
        "files_to_modify": _ordered_unique_strings(_list(worker_prompt_payload.get("files_to_modify"))),
        "files_to_avoid": _ordered_unique_strings(_list(worker_prompt_payload.get("files_to_avoid"))),
        "verification_steps": _ordered_unique_strings(_list(worker_prompt_payload.get("verification_steps"))),
        "matched_rule_ids": _ordered_unique_strings(_list(worker_prompt_payload.get("matched_rule_ids"))),
        "failure_modes_to_avoid": _ordered_unique_strings(_list(worker_prompt_payload.get("failure_modes_to_avoid"))),
    }


def _artifact_input(ref: str, role: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": role,
        "ref": ref,
        "contract_version": _string(payload.get("contract_version") or payload.get("schema_version")),
        "digest": stable_json_digest(payload),
    }


def build_stack_consumption_pilot_payload(
    *,
    root: Path | None = None,
    worker_prompt_path: Path | None = None,
    context_path: Path | None = None,
    operator_surface_path: Path | None = None,
    ledger_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
) -> dict[str, Any]:
    base = (root or atlas_root()).resolve()
    resolved_worker_prompt = (worker_prompt_path or default_worker_prompt_latest_json_path(base)).resolve()
    resolved_context = (context_path or default_context_latest_json_path(base)).resolve()
    resolved_operator_surface = (operator_surface_path or default_operator_surface_latest_json_path(base)).resolve()
    resolved_ledger = (ledger_path or default_ledger_latest_json_path(base)).resolve()
    resolved_state_model = (state_model_path or default_state_model_path(base)).resolve()
    resolved_rule_registry = (rule_registry_path or default_rule_registry_path(base)).resolve()

    worker_prompt_payload = _require_json_object(resolved_worker_prompt, label="Cortex worker-prompt artifact")
    context_payload = _require_json_object(resolved_context, label="Cortex context artifact")
    operator_payload = _require_json_object(resolved_operator_surface, label="Cortex operator-surface artifact")
    ledger_payload = _require_json_object(resolved_ledger, label="Cortex ledger artifact")
    state_model_payload = _require_json_object(resolved_state_model, label="Cortex state model seed")
    rule_registry_payload = _require_json_object(resolved_rule_registry, label="Cortex rule registry seed")

    worker_prompt_ref = atlas_relative(resolved_worker_prompt, root=base)
    context_ref = atlas_relative(resolved_context, root=base)
    operator_ref = atlas_relative(resolved_operator_surface, root=base)
    ledger_ref = atlas_relative(resolved_ledger, root=base)
    state_model_ref = atlas_relative(resolved_state_model, root=base)
    rule_registry_ref = atlas_relative(resolved_rule_registry, root=base)

    next_lane = _dict(worker_prompt_payload.get("next_recommended_lane"))
    lane_id = _string(next_lane.get("lane_id")) or _string(_dict(ledger_payload.get("next_recommended_lane")).get("lane_id"))
    context_packet_id = _string(context_payload.get("packet_id"))
    ledger_lane_id = _string(_dict(ledger_payload.get("next_recommended_lane")).get("lane_id"))
    stack_handoff = _stack_handoff(worker_prompt_payload, worker_prompt_ref=worker_prompt_ref, context_ref=context_ref)
    source_refs = _source_refs(
        worker_prompt_payload=worker_prompt_payload,
        worker_prompt_ref=worker_prompt_ref,
        context_ref=context_ref,
        operator_surface_ref=operator_ref,
        ledger_ref=ledger_ref,
        state_model_ref=state_model_ref,
        rule_registry_ref=rule_registry_ref,
    )
    transcript_refs = _transcript_refs(source_refs)
    separated_surfaces_present = all(
        _separation_status(worker_prompt_payload, key)
        for key in ("planner", "context", "proof", "receipt_draft", "final_receipt")
    ) and _separation_status(worker_prompt_payload, "final_receipt") == "not_emitted_by_cortex"

    checks = [
        _check(
            "worker-prompt-contract-version",
            _string(worker_prompt_payload.get("contract_version")) == WORKER_PROMPT_CONTRACT_VERSION,
            "Worker prompt uses the promoted Cortex worker-prompt contract.",
            source_ref=worker_prompt_ref,
        ),
        _check(
            "worker-prompt-authority-read-only",
            _string(worker_prompt_payload.get("authority_level")) == WORKER_PROMPT_AUTHORITY_LEVEL,
            "Worker prompt remains read-only advisory.",
            source_ref=worker_prompt_ref,
        ),
        _check(
            "stack-lock-digest-present",
            _string(worker_prompt_payload.get("stack_lock_digest")).startswith("sha256:"),
            "Worker prompt carries a stack lock digest for _stack consumption.",
            source_ref=worker_prompt_ref,
        ),
        _check(
            "context-packet-matches-lane",
            bool(lane_id) and context_packet_id == f"context-{lane_id}",
            "Context packet is explicitly linked to the selected lane.",
            source_ref=context_ref,
        ),
        _check(
            "ledger-lane-matches-worker-prompt",
            bool(lane_id) and ledger_lane_id == lane_id,
            "Ledger and worker prompt agree on the next lane.",
            source_ref=ledger_ref,
        ),
        _check(
            "transcript-scraping-absent",
            not transcript_refs and not stack_handoff["transcript_scraping_allowed"],
            "Pilot consumes artifact refs only and does not scrape transcripts.",
            source_ref=worker_prompt_ref,
        ),
        _check(
            "separated-surfaces-preserved",
            separated_surfaces_present,
            "Planner, context, proof, receipt-draft, and final receipt stay separately referenceable.",
            source_ref=worker_prompt_ref,
        ),
        _check(
            "no-execution-or-receipt-authority",
            not stack_handoff["execution_authorized"]
            and not stack_handoff["receipt_authorized"]
            and not stack_handoff["owner_truth_mutation_authorized"]
            and not stack_handoff["default_routing_enabled"],
            "Pilot does not authorize execution, final receipts, owner-truth mutation, or default routing.",
            source_ref=worker_prompt_ref,
        ),
    ]
    ready = all(item["status"] == "passed" for item in checks)
    failed_checks = [item["check_id"] for item in checks if item["status"] != "passed"]

    return {
        "contract_version": STACK_CONSUMPTION_PILOT_CONTRACT_VERSION,
        "generated_at": _utc_now(),
        "authority_level": STACK_CONSUMPTION_PILOT_AUTHORITY_LEVEL,
        "stack_root": normalize_slashes(str(base)),
        "pilot_id": f"stack-consumption-pilot-{lane_id or 'unknown'}",
        "consumer_id": STACK_CONSUMER_ID,
        "next_recommended_lane": {
            "lane_id": lane_id,
            "owner_layer": _string(next_lane.get("owner_layer")),
            "rationale": _string(next_lane.get("rationale")),
        },
        "pilot_result": {
            "status": "ready" if ready else "blocked",
            "ready_for_stack_consumer": ready,
            "blocked_reason": None if ready else f"Failed pilot checks: {', '.join(failed_checks)}",
            "failed_checks": failed_checks,
        },
        "stack_handoff": stack_handoff,
        "advisory_assignment": _advisory_assignment(worker_prompt_payload),
        "artifact_consumption": [
            _artifact_input(worker_prompt_ref, "worker_prompt", worker_prompt_payload),
            _artifact_input(context_ref, "context", context_payload),
            _artifact_input(operator_ref, "operator_surface", operator_payload),
            _artifact_input(ledger_ref, "ledger", ledger_payload),
            _artifact_input(state_model_ref, "state_model_seed", state_model_payload),
            _artifact_input(rule_registry_ref, "rule_registry_seed", rule_registry_payload),
        ],
        "pilot_checks": checks,
        "transcript_scraping": {
            "allowed": False,
            "detected": bool(transcript_refs),
            "detected_refs": transcript_refs,
            "forbidden_source_patterns": [
                "runtime/atlas/conversations/**",
                "runtime/atlas/sessions/**",
                "**/*transcript*",
            ],
        },
        "authority_guards": _authority_guards(),
        "boundary_reminders": _ordered_unique_strings(
            [
                *_list(worker_prompt_payload.get("boundary_reminders")),
                *_list(operator_payload.get("boundary_reminders")),
                "_stack owns orchestration and enforcement truth.",
                "Lifeline owns receipt and approval truth.",
            ]
        ),
        "source_refs": source_refs,
        "source_artifact_refs": {
            "worker_prompt": worker_prompt_ref,
            "context": context_ref,
            "operator_surface": operator_ref,
            "ledger": ledger_ref,
            "seed": state_model_ref,
            "rules": rule_registry_ref,
        },
    }


def render_stack_consumption_pilot_summary(payload: dict[str, Any]) -> str:
    next_lane = payload["next_recommended_lane"]
    result = payload["pilot_result"]
    handoff = payload["stack_handoff"]
    lines = [
        "# Cortex Stack Consumption Pilot",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Pilot id: `{payload['pilot_id']}`",
        f"- Authority level: `{payload['authority_level']}`",
        f"- Consumer: `{payload['consumer_id']}`",
        f"- Consumption mode: `{handoff['consumption_mode']}`",
        f"- Next recommended lane: `{next_lane['lane_id']}` ({next_lane['owner_layer']})",
        f"- Pilot status: `{result['status']}`",
        f"- Ready for _stack consumer: `{'yes' if result['ready_for_stack_consumer'] else 'no'}`",
        f"- Worker prompt: `{handoff['worker_prompt_ref']}`",
        f"- Context: `{handoff['context_ref']}`",
        f"- Transcript scraping: `{'yes' if payload['transcript_scraping']['detected'] else 'no'}`",
        f"- Execution authorized: `{'yes' if handoff['execution_authorized'] else 'no'}`",
        f"- Receipt authorized: `{'yes' if handoff['receipt_authorized'] else 'no'}`",
        "",
        "## Pilot Checks",
    ]
    for check in payload["pilot_checks"]:
        lines.append(f"- `{check['check_id']}`: {check['status']} — {check['summary']}")

    lines.extend(["", "## Advisory Assignment"])
    assignment = payload["advisory_assignment"]
    lines.append(f"- Run id: `{assignment['run_id']}`")
    lines.append(f"- Assignment id: `{assignment['assignment_id']}`")
    lines.append(f"- Stack lock digest: `{assignment['stack_lock_digest']}`")
    lines.append(f"- Objective: {assignment['objective']}")

    lines.extend(["", "## Authority Guards"])
    for guard in payload["authority_guards"]:
        lines.append(f"- {guard}")

    lines.extend(["", "## Source Refs"])
    for ref in payload["source_refs"]:
        lines.append(f"- `{ref}`")
    return "\n".join(lines) + "\n"


def persist_stack_consumption_pilot_artifact(
    *,
    root: Path | None = None,
    worker_prompt_path: Path | None = None,
    context_path: Path | None = None,
    operator_surface_path: Path | None = None,
    ledger_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    output_json_path: Path | None = None,
    output_markdown_path: Path | None = None,
    write_markdown: bool = True,
) -> PersistedStackConsumptionPilotArtifact:
    base = (root or atlas_root()).resolve()
    artifact_path = (output_json_path or default_stack_consumption_pilot_latest_json_path(base)).resolve()
    summary_path = (
        (output_markdown_path or default_stack_consumption_pilot_latest_markdown_path(base)).resolve()
        if write_markdown
        else None
    )
    payload = build_stack_consumption_pilot_payload(
        root=base,
        worker_prompt_path=worker_prompt_path.resolve() if worker_prompt_path is not None else None,
        context_path=context_path.resolve() if context_path is not None else None,
        operator_surface_path=operator_surface_path.resolve() if operator_surface_path is not None else None,
        ledger_path=ledger_path.resolve() if ledger_path is not None else None,
        state_model_path=state_model_path.resolve() if state_model_path is not None else None,
        rule_registry_path=rule_registry_path.resolve() if rule_registry_path is not None else None,
    )
    summary = render_stack_consumption_pilot_summary(payload)
    write_json(artifact_path, payload)
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
    return PersistedStackConsumptionPilotArtifact(
        artifact_path=artifact_path,
        summary_path=summary_path,
        payload_digest=stable_json_digest(payload),
        payload=payload,
        summary=summary,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Persist the bounded Cortex _stack worker-prompt consumption pilot.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--worker-prompt-path", type=Path)
    parser.add_argument("--context-path", type=Path)
    parser.add_argument("--operator-surface-path", type=Path)
    parser.add_argument("--ledger-path", type=Path)
    parser.add_argument("--state-model-path", type=Path)
    parser.add_argument("--rule-registry-path", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-markdown", type=Path)
    parser.add_argument("--no-write-markdown", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    try:
        artifact = persist_stack_consumption_pilot_artifact(
            root=args.root.resolve(),
            worker_prompt_path=args.worker_prompt_path.resolve() if args.worker_prompt_path else None,
            context_path=args.context_path.resolve() if args.context_path else None,
            operator_surface_path=args.operator_surface_path.resolve() if args.operator_surface_path else None,
            ledger_path=args.ledger_path.resolve() if args.ledger_path else None,
            state_model_path=args.state_model_path.resolve() if args.state_model_path else None,
            rule_registry_path=args.rule_registry_path.resolve() if args.rule_registry_path else None,
            output_json_path=args.output_json.resolve() if args.output_json else None,
            output_markdown_path=args.output_markdown.resolve() if args.output_markdown else None,
            write_markdown=not args.no_write_markdown,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.print_json:
        print(json.dumps(artifact.payload, indent=2))
    elif not args.quiet:
        print(artifact.summary, end="")
        print(f"JSON artifact: {normalize_slashes(str(artifact.artifact_path))}")
        if artifact.summary_path is not None:
            print(f"Markdown summary: {normalize_slashes(str(artifact.summary_path))}")
        print(f"Payload digest: {artifact.payload_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
