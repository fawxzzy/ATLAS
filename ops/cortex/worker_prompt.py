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

from ops._atlas import atlas_relative, atlas_root, load_stack_config, normalize_slashes
from ops.cortex._artifacts import stable_json_digest, write_json
from ops.cortex.context_assembler import default_context_latest_json_path
from ops.cortex.current_state import (
    default_current_state_latest_json_path,
    default_validation_receipt_path,
)
from ops.cortex.kernel import (
    default_proof_summary_examples_path,
    default_rule_registry_path,
    default_state_model_path,
)
from ops.cortex.ledger import default_ledger_latest_json_path
from ops.cortex.loop import load_and_run_cortex_loop
from ops.cortex.operator_surface import default_operator_surface_latest_json_path
from ops.cortex.rail_state_reader import default_rail_state_latest_json_path

WORKER_PROMPT_CONTRACT_VERSION = "atlas.cortex.worker-prompt.v1"
WORKER_PROMPT_AUTHORITY_LEVEL = "read_only_advisory"


def worker_prompt_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "worker-prompts"


def default_worker_prompt_latest_json_path(root: Path | None = None) -> Path:
    return worker_prompt_root(root) / "latest.json"


def default_worker_prompt_latest_markdown_path(root: Path | None = None) -> Path:
    return worker_prompt_root(root) / "latest.md"


@dataclass(frozen=True)
class PersistedCortexWorkerPromptArtifact:
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


def _load_stack_lock_digest(path: Path) -> str:
    payload = load_stack_config(path)
    digest = str(payload.get("lock_digest", "")).strip()
    if not digest:
        raise ValueError(f"stack.lock.yaml missing lock_digest: {normalize_slashes(str(path.resolve()))}")
    return digest


def _assignment_id_for_lane(lane_id: str) -> str:
    return f"assignment-{lane_id}"


def _run_id_for_lane(lane_id: str) -> str:
    return f"cortex-run-{lane_id}"


def _non_execution_guards() -> list[str]:
    return [
        "Advisory only: this worker prompt does not authorize execution, approval, or receipt issuance.",
        "Cortex remains read-only over owner repos and does not become _stack authority, owner truth, or Lifeline receipt authority.",
        "Planner, context, proof, receipt-draft, and final receipt surfaces must stay separately referenceable even when this prompt is consumed by _stack.",
    ]


def _proof_preview(run_result: Any) -> dict[str, Any]:
    return {
        "status": "advisory_example_source",
        "verification_expectation": list(run_result.verification_expectation),
        "receipt_ready_candidate": bool(run_result.receipt_ready),
        "next_required_layer": run_result.next_required_layer,
        "known_ambient_debt": list(run_result.known_ambient_debt),
        "selected_next_action_id": str(run_result.selected_next_action.get("action_id", "")).strip(),
    }


def _source_refs(
    *,
    task_frame_required_inputs: list[Any],
    current_ref: str,
    rail_ref: str,
    context_ref: str,
    operator_ref: str,
    ledger_ref: str,
    validation_ref: str,
    state_model_ref: str,
    rule_registry_ref: str,
    proof_examples_ref: str,
    stack_lock_ref: str,
    workflow_profile_refs: list[str],
) -> list[str]:
    values: list[Any] = [
        current_ref,
        rail_ref,
        context_ref,
        operator_ref,
        ledger_ref,
        validation_ref,
        state_model_ref,
        rule_registry_ref,
        proof_examples_ref,
        stack_lock_ref,
        *workflow_profile_refs,
        *task_frame_required_inputs,
    ]
    return _ordered_unique_strings(values)


def _matched_rule_ids(
    *,
    context_payload: dict[str, Any],
    fallback_rule_ids: tuple[str, ...],
) -> list[str]:
    highlights = context_payload.get("rule_highlights")
    if isinstance(highlights, list):
        ids: list[Any] = []
        for item in highlights:
            if isinstance(item, dict):
                ids.append(item.get("id"))
        resolved = _ordered_unique_strings(ids)
        if resolved:
            return resolved
    return _ordered_unique_strings(list(fallback_rule_ids))


def _separation_refs(
    *,
    context_ref: str,
    proof_examples_ref: str,
    worker_prompt_ref: str,
) -> dict[str, dict[str, Any]]:
    return {
        "planner": {
            "ref": f"{worker_prompt_ref}#/planner_contract",
            "status": "embedded_preview",
            "contract_version": "atlas.cortex.worker-plan.v1",
            "note": "Planner payload is previewed here for _stack consumption and remains advisory.",
        },
        "context": {
            "ref": context_ref,
            "status": "external_artifact",
            "contract_version": "atlas.cortex.context-packet.v1",
            "note": "Context remains a separate Cortex artifact.",
        },
        "proof": {
            "ref": proof_examples_ref,
            "status": "source_artifact",
            "contract_version": "atlas.cortex.proof-summary.examples.v1",
            "note": "Proof selection still comes from the explicit Cortex proof-summary examples source.",
        },
        "receipt_draft": {
            "ref": f"{worker_prompt_ref}#/receipt_draft_preview",
            "status": "embedded_preview",
            "contract_version": "atlas.cortex.proof-receipt-draft.v1",
            "note": "Receipt-draft preview is advisory only and does not change Lifeline authority.",
        },
        "final_receipt": {
            "ref": None,
            "status": "not_emitted_by_cortex",
            "contract_version": "atlas.lifeline.receipt.v1",
            "note": "Final receipt authority remains outside Cortex.",
        },
    }


def build_cortex_worker_prompt_payload(
    *,
    root: Path | None = None,
    current_state_path: Path | None = None,
    rail_state_path: Path | None = None,
    context_path: Path | None = None,
    operator_surface_path: Path | None = None,
    ledger_path: Path | None = None,
    validation_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    proof_examples_path: Path | None = None,
    stack_lock_path: Path | None = None,
    worker_prompt_ref: str | None = None,
) -> dict[str, Any]:
    base = (root or atlas_root()).resolve()
    resolved_current_state = (current_state_path or default_current_state_latest_json_path(base)).resolve()
    resolved_rail_state = (rail_state_path or default_rail_state_latest_json_path(base)).resolve()
    resolved_context = (context_path or default_context_latest_json_path(base)).resolve()
    resolved_operator_surface = (operator_surface_path or default_operator_surface_latest_json_path(base)).resolve()
    resolved_ledger = (ledger_path or default_ledger_latest_json_path(base)).resolve()
    resolved_validation = (validation_path or default_validation_receipt_path(base)).resolve()
    resolved_state_model = (state_model_path or default_state_model_path(base)).resolve()
    resolved_rule_registry = (rule_registry_path or default_rule_registry_path(base)).resolve()
    resolved_proof_examples = (proof_examples_path or default_proof_summary_examples_path(base)).resolve()
    resolved_stack_lock = (stack_lock_path or (base / "stack.lock.yaml")).resolve()

    current_payload = _require_json_object(resolved_current_state, label="Cortex current-state artifact")
    rail_payload = _require_json_object(resolved_rail_state, label="Cortex rail-state artifact")
    context_payload = _require_json_object(resolved_context, label="Cortex context artifact")
    operator_payload = _require_json_object(resolved_operator_surface, label="Cortex operator-surface artifact")
    ledger_payload = _require_json_object(resolved_ledger, label="Cortex ledger artifact")
    validation_payload = _require_json_object(resolved_validation, label="Stack validation receipt")
    _require_json_object(resolved_state_model, label="Cortex state model seed")
    _require_json_object(resolved_rule_registry, label="Cortex rule registry seed")
    _require_json_object(resolved_proof_examples, label="Cortex proof summary examples")

    run_result = load_and_run_cortex_loop(
        root=base,
        state_model_path=resolved_state_model,
        rule_registry_path=resolved_rule_registry,
        proof_summary_examples_path=resolved_proof_examples,
    )
    lane_id = str(run_result.selected_next_action.get("action_id", "")).strip()
    if not lane_id:
        raise ValueError("Cortex worker prompt requires a selected next action id.")

    current_ref = atlas_relative(resolved_current_state, root=base)
    rail_ref = atlas_relative(resolved_rail_state, root=base)
    context_ref = atlas_relative(resolved_context, root=base)
    operator_ref = atlas_relative(resolved_operator_surface, root=base)
    ledger_ref = atlas_relative(resolved_ledger, root=base)
    validation_ref = atlas_relative(resolved_validation, root=base)
    state_model_ref = atlas_relative(resolved_state_model, root=base)
    rule_registry_ref = atlas_relative(resolved_rule_registry, root=base)
    proof_examples_ref = atlas_relative(resolved_proof_examples, root=base)
    stack_lock_ref = atlas_relative(resolved_stack_lock, root=base)
    resolved_worker_prompt_ref = worker_prompt_ref or atlas_relative(default_worker_prompt_latest_json_path(base), root=base)

    task_frame = context_payload.get("task_frame") if isinstance(context_payload.get("task_frame"), dict) else {}
    top_evidence_refs = (
        operator_payload.get("top_evidence_refs")
        if isinstance(operator_payload.get("top_evidence_refs"), list)
        else []
    )
    source_refs = _source_refs(
        task_frame_required_inputs=task_frame.get("required_inputs", []) if isinstance(task_frame.get("required_inputs"), list) else [],
        current_ref=current_ref,
        rail_ref=rail_ref,
        context_ref=context_ref,
        operator_ref=operator_ref,
        ledger_ref=ledger_ref,
        validation_ref=validation_ref,
        state_model_ref=state_model_ref,
        rule_registry_ref=rule_registry_ref,
        proof_examples_ref=proof_examples_ref,
        stack_lock_ref=stack_lock_ref,
        workflow_profile_refs=[
            str(context_payload.get("workflow_profile", {}).get("canonical_refs", {}).get("markdown", "")).strip(),
            str(context_payload.get("workflow_profile", {}).get("canonical_refs", {}).get("metadata", "")).strip(),
        ],
    )
    next_lane = (
        ledger_payload.get("next_recommended_lane")
        if isinstance(ledger_payload.get("next_recommended_lane"), dict)
        else {}
    )
    validation_counts = (
        validation_payload.get("summary")
        if isinstance(validation_payload.get("summary"), dict)
        else {}
    )
    workflow_profile = (
        context_payload.get("workflow_profile") if isinstance(context_payload.get("workflow_profile"), dict) else {}
    )
    response_contract = (
        workflow_profile.get("response_contract")
        if isinstance(workflow_profile.get("response_contract"), dict)
        else {}
    )
    style_preferences = (
        workflow_profile.get("style_preferences")
        if isinstance(workflow_profile.get("style_preferences"), dict)
        else {}
    )

    payload = {
        "contract_version": WORKER_PROMPT_CONTRACT_VERSION,
        "generated_at": _utc_now(),
        "authority_level": WORKER_PROMPT_AUTHORITY_LEVEL,
        "stack_root": normalize_slashes(str(base)),
        "run_id": _run_id_for_lane(lane_id),
        "assignment_id": _assignment_id_for_lane(lane_id),
        "stack_lock_digest": _load_stack_lock_digest(resolved_stack_lock),
        "owner_layer": run_result.worker_plan.owner_layer,
        "objective": run_result.worker_plan.objective,
        "implementation_plan": list(run_result.worker_plan.implementation_plan),
        "files_to_modify": list(run_result.worker_plan.files_to_modify),
        "files_to_avoid": list(run_result.worker_plan.files_to_avoid),
        "verification_steps": list(run_result.worker_plan.verification_steps),
        "source_refs": source_refs,
        "matched_rule_ids": _matched_rule_ids(
            context_payload=context_payload,
            fallback_rule_ids=run_result.worker_plan.matched_rule_ids,
        ),
        "failure_modes_to_avoid": list(run_result.worker_plan.failure_modes_to_avoid),
        "next_recommended_lane": {
            "lane_id": str(next_lane.get("lane_id", lane_id)).strip(),
            "owner_layer": str(next_lane.get("owner_layer", run_result.worker_plan.owner_layer)).strip(),
            "rationale": str(next_lane.get("rationale", "")).strip(),
        },
        "validation_counts": {
            "critical": int(validation_counts.get("critical", 0) or 0),
            "error": int(validation_counts.get("error", 0) or 0),
            "warning": int(validation_counts.get("warning", 0) or 0),
            "info": int(validation_counts.get("info", 0) or 0),
            "total": int(validation_counts.get("total", 0) or 0),
        },
        "context_packet_id": str(context_payload.get("packet_id", "")).strip(),
        "workflow_profile": {
            "profile_id": str(workflow_profile.get("profile_id", "")).strip(),
            "title": str(workflow_profile.get("title", "")).strip(),
            "summary": str(workflow_profile.get("summary", "")).strip(),
            "canonical_refs": workflow_profile.get("canonical_refs", {}),
            "response_contract": response_contract,
            "style_keywords": (
                style_preferences.get("preferred_style")
                if isinstance(style_preferences.get("preferred_style"), list)
                else []
            ),
            "reasoning_routes": (
                workflow_profile.get("reasoning_routes")
                if isinstance(workflow_profile.get("reasoning_routes"), list)
                else []
            ),
            "canonical_memory_rules": (
                workflow_profile.get("canonical_memory_rules")
                if isinstance(workflow_profile.get("canonical_memory_rules"), dict)
                else {}
            ),
        },
        "task_frame_summary": ledger_payload.get("task_frame_summary") if isinstance(ledger_payload.get("task_frame_summary"), dict) else {},
        "publication_posture": ledger_payload.get("remote_status"),
        "top_evidence_refs": _ordered_unique_strings(top_evidence_refs),
        "boundary_reminders": _ordered_unique_strings(
            ledger_payload.get("boundary_reminders", [])
            if isinstance(ledger_payload.get("boundary_reminders"), list)
            else []
        ),
        "non_execution_guards": _non_execution_guards(),
        "planner_contract": run_result.worker_plan.to_payload(),
        "proof_preview": _proof_preview(run_result),
        "receipt_draft_preview": run_result.proof_receipt_draft.to_payload(),
        "separation_refs": _separation_refs(
            context_ref=context_ref,
            proof_examples_ref=proof_examples_ref,
            worker_prompt_ref=resolved_worker_prompt_ref,
        ),
        "source_artifact_refs": {
            "current_state": current_ref,
            "rail_state": rail_ref,
            "context": context_ref,
            "operator_surface": operator_ref,
            "ledger": ledger_ref,
            "validation": validation_ref,
            "seed": state_model_ref,
            "rules": rule_registry_ref,
            "proof_examples": proof_examples_ref,
            "stack_lock": stack_lock_ref,
        },
    }
    return payload


def render_cortex_worker_prompt_summary(payload: dict[str, Any]) -> str:
    counts = payload["validation_counts"]
    next_lane = payload["next_recommended_lane"]
    lines = [
        "# Cortex Worker Prompt",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Run id: `{payload['run_id']}`",
        f"- Assignment id: `{payload['assignment_id']}`",
        f"- Authority level: `{payload['authority_level']}`",
        f"- Owner layer: `{payload['owner_layer']}`",
        f"- Next recommended lane: `{next_lane['lane_id']}` ({next_lane['owner_layer']})",
        (
            f"- Validation: `critical={counts['critical']} error={counts['error']} "
            f"warning={counts['warning']} info={counts['info']} total={counts['total']}`"
        ),
        f"- Context packet: `{payload['context_packet_id']}`",
        f"- Stack lock digest: `{payload['stack_lock_digest']}`",
        "",
        "## Objective",
        f"- {payload['objective']}",
        "",
        "## Implementation Plan",
    ]
    for step in payload["implementation_plan"]:
        lines.append(f"- {step}")

    lines.extend(["", "## Verification Steps"])
    for step in payload["verification_steps"]:
        lines.append(f"- `{step}`")

    lines.extend(["", "## Source Refs"])
    for ref in payload["source_refs"]:
        lines.append(f"- `{ref}`")

    workflow_profile = payload.get("workflow_profile")
    if isinstance(workflow_profile, dict) and workflow_profile:
        response_contract = (
            workflow_profile.get("response_contract")
            if isinstance(workflow_profile.get("response_contract"), dict)
            else {}
        )
        lines.extend(["", "## Workflow Profile"])
        lines.append(f"- `{workflow_profile.get('profile_id', '')}`: {workflow_profile.get('summary', '')}")
        if response_contract:
            lines.append(
                f"- Response block: `{', '.join(response_contract.get('status_block_labels', []))}`"
            )
        style_keywords = workflow_profile.get("style_keywords")
        if isinstance(style_keywords, list) and style_keywords:
            lines.append(f"- Style keywords: `{', '.join(style_keywords)}`")

    lines.extend(["", "## Non-Execution Guards"])
    for guard in payload["non_execution_guards"]:
        lines.append(f"- {guard}")
    return "\n".join(lines) + "\n"


def persist_cortex_worker_prompt_artifact(
    *,
    root: Path | None = None,
    current_state_path: Path | None = None,
    rail_state_path: Path | None = None,
    context_path: Path | None = None,
    operator_surface_path: Path | None = None,
    ledger_path: Path | None = None,
    validation_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    proof_examples_path: Path | None = None,
    stack_lock_path: Path | None = None,
    output_json_path: Path | None = None,
    output_markdown_path: Path | None = None,
    write_markdown: bool = True,
) -> PersistedCortexWorkerPromptArtifact:
    base = (root or atlas_root()).resolve()
    artifact_path = (output_json_path or default_worker_prompt_latest_json_path(base)).resolve()
    summary_path = (
        (output_markdown_path or default_worker_prompt_latest_markdown_path(base)).resolve()
        if write_markdown
        else None
    )
    worker_prompt_ref = atlas_relative(artifact_path, root=base)
    payload = build_cortex_worker_prompt_payload(
        root=base,
        current_state_path=current_state_path.resolve() if current_state_path is not None else None,
        rail_state_path=rail_state_path.resolve() if rail_state_path is not None else None,
        context_path=context_path.resolve() if context_path is not None else None,
        operator_surface_path=operator_surface_path.resolve() if operator_surface_path is not None else None,
        ledger_path=ledger_path.resolve() if ledger_path is not None else None,
        validation_path=validation_path.resolve() if validation_path is not None else None,
        state_model_path=state_model_path.resolve() if state_model_path is not None else None,
        rule_registry_path=rule_registry_path.resolve() if rule_registry_path is not None else None,
        proof_examples_path=proof_examples_path.resolve() if proof_examples_path is not None else None,
        stack_lock_path=stack_lock_path.resolve() if stack_lock_path is not None else None,
        worker_prompt_ref=worker_prompt_ref,
    )
    summary = render_cortex_worker_prompt_summary(payload)
    write_json(artifact_path, payload)
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
    return PersistedCortexWorkerPromptArtifact(
        artifact_path=artifact_path,
        summary_path=summary_path,
        payload_digest=stable_json_digest(payload),
        payload=payload,
        summary=summary,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Persist the Cortex worker-prompt contract artifact for ATLAS.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--current-state-path", type=Path)
    parser.add_argument("--rail-state-path", type=Path)
    parser.add_argument("--context-path", type=Path)
    parser.add_argument("--operator-surface-path", type=Path)
    parser.add_argument("--ledger-path", type=Path)
    parser.add_argument("--validation-path", type=Path)
    parser.add_argument("--state-model-path", type=Path)
    parser.add_argument("--rule-registry-path", type=Path)
    parser.add_argument("--proof-examples-path", type=Path)
    parser.add_argument("--stack-lock-path", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-markdown", type=Path)
    parser.add_argument("--no-write-markdown", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    try:
        artifact = persist_cortex_worker_prompt_artifact(
            root=args.root.resolve(),
            current_state_path=args.current_state_path.resolve() if args.current_state_path else None,
            rail_state_path=args.rail_state_path.resolve() if args.rail_state_path else None,
            context_path=args.context_path.resolve() if args.context_path else None,
            operator_surface_path=args.operator_surface_path.resolve() if args.operator_surface_path else None,
            ledger_path=args.ledger_path.resolve() if args.ledger_path else None,
            validation_path=args.validation_path.resolve() if args.validation_path else None,
            state_model_path=args.state_model_path.resolve() if args.state_model_path else None,
            rule_registry_path=args.rule_registry_path.resolve() if args.rule_registry_path else None,
            proof_examples_path=args.proof_examples_path.resolve() if args.proof_examples_path else None,
            stack_lock_path=args.stack_lock_path.resolve() if args.stack_lock_path else None,
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
