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
from ops.cortex.kernel import default_rule_registry_path, default_state_model_path
from ops.cortex.ledger import default_ledger_latest_json_path
from ops.cortex.receipt_interpreter import (
    RECEIPT_INTERPRETATION_CONTRACT_VERSION,
    default_receipt_interpretation_latest_json_path,
)
from ops.cortex.stack_consumption_pilot import default_stack_consumption_pilot_latest_json_path
from ops.cortex.stack_handoff import default_stack_advisory_handoff_latest_json_path
from ops.cortex.worker_prompt import default_worker_prompt_latest_json_path

RECEIPT_INTERPRETATION_STACK_CONSUMPTION_CONTRACT_VERSION = (
    "atlas.cortex.receipt-interpretation-stack-consumption.v1"
)
RECEIPT_INTERPRETATION_STACK_CONSUMPTION_AUTHORITY_LEVEL = "read_only_advisory"
STACK_CONSUMER_ID = "_stack"
STACK_CONSUMER_ROLE = "receipt_interpretation_artifact_consumer"
STACK_CONSUMPTION_MODE = "artifact_refs_only"


def receipt_interpretation_stack_consumption_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "receipt-interpretation-stack-consumption"


def default_receipt_interpretation_stack_consumption_latest_json_path(root: Path | None = None) -> Path:
    return receipt_interpretation_stack_consumption_root(root) / "latest.json"


def default_receipt_interpretation_stack_consumption_latest_markdown_path(root: Path | None = None) -> Path:
    return receipt_interpretation_stack_consumption_root(root) / "latest.md"


@dataclass(frozen=True)
class PersistedReceiptInterpretationStackConsumptionArtifact:
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


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


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


def _check(check_id: str, passed: bool, summary: str, *, source_ref: str | None = None) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "passed" if passed else "failed",
        "summary": summary,
        "source_ref": source_ref,
    }


def _artifact_input(ref: str, role: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": role,
        "ref": ref,
        "contract_version": _string(payload.get("contract_version") or payload.get("schema_version")),
        "digest": stable_json_digest(payload),
    }


def _authority() -> dict[str, bool]:
    return {
        "stack_consumption_authorized": True,
        "automatic_dispatch_enabled": False,
        "final_receipt_authorized": False,
        "approval_authorized": False,
        "execution_authorized": False,
        "dispatch_authorized": False,
        "owner_truth_mutation_authorized": False,
        "lifeline_truth_mutation_authorized": False,
        "transcript_scraping_allowed": False,
    }


def _authority_guards() -> list[str]:
    return [
        "_stack may consume Cortex receipt interpretation only through explicit artifact refs.",
        "Receipt-interpretation stack consumption does not dispatch or execute _stack work.",
        "Receipt-interpretation stack consumption does not approve work, issue final receipts, or mutate owner or Lifeline truth.",
        "Receipt-interpretation stack consumption does not scrape transcripts.",
    ]


def _validation_counts(validation_payload: dict[str, Any]) -> dict[str, int]:
    summary = _dict(validation_payload.get("summary"))
    return {
        "critical": int(summary.get("critical", 0) or 0),
        "error": int(summary.get("error", 0) or 0),
        "warning": int(summary.get("warning", 0) or 0),
        "info": int(summary.get("info", 0) or 0),
        "total": int(summary.get("total", 0) or 0),
    }


def _validation_blockers(validation_payload: dict[str, Any]) -> list[str]:
    return [
        f"{_string(item.get('category'))}: {_string(item.get('message'))}"
        for item in _list(validation_payload.get("findings"))
        if isinstance(item, dict) and _string(item.get("severity")) in {"critical", "error"}
    ]


def _guard_widened(value: dict[str, Any], *keys: str) -> bool:
    return any(bool(value.get(key)) for key in keys)


def _transcript_refs(values: list[str]) -> list[str]:
    suspicious: list[str] = []
    for value in values:
        lowered = value.lower()
        if (
            "transcript" in lowered
            or "runtime/atlas/conversations" in lowered
            or "runtime/atlas/sessions" in lowered
        ):
            suspicious.append(value)
    return _ordered_unique_strings(suspicious)


def _blocked_reason(
    *,
    failed_checks: list[str],
    interpretation_blocked_reason: str,
    validation_blockers: list[str],
    transcript_refs: list[str],
) -> str:
    details = _ordered_unique_strings(
        [
            f"Failed consumption checks: {', '.join(failed_checks)}." if failed_checks else "",
            interpretation_blocked_reason,
            *validation_blockers,
            (
                "Transcript-like refs are forbidden for stack consumption: "
                f"{', '.join(transcript_refs)}."
            )
            if transcript_refs
            else "",
        ]
    )
    return " ".join(details) if details else "Receipt interpretation stack consumption is blocked."


def build_receipt_interpretation_stack_consumption_payload(
    *,
    root: Path | None = None,
    receipt_interpretation_path: Path | None = None,
    stack_handoff_path: Path | None = None,
    stack_consumption_pilot_path: Path | None = None,
    worker_prompt_path: Path | None = None,
    ledger_path: Path | None = None,
    validation_receipt_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
) -> dict[str, Any]:
    base = (root or atlas_root()).resolve()
    resolved_receipt_interpretation = (
        receipt_interpretation_path or default_receipt_interpretation_latest_json_path(base)
    ).resolve()
    resolved_stack_handoff = (stack_handoff_path or default_stack_advisory_handoff_latest_json_path(base)).resolve()
    resolved_pilot = (stack_consumption_pilot_path or default_stack_consumption_pilot_latest_json_path(base)).resolve()
    resolved_worker_prompt = (worker_prompt_path or default_worker_prompt_latest_json_path(base)).resolve()
    resolved_ledger = (ledger_path or default_ledger_latest_json_path(base)).resolve()
    resolved_validation = (
        validation_receipt_path or base / "runtime" / "receipts" / "validation" / "stack-validation.latest.json"
    ).resolve()
    resolved_state_model = (state_model_path or default_state_model_path(base)).resolve()
    resolved_rule_registry = (rule_registry_path or default_rule_registry_path(base)).resolve()

    receipt_interpretation_payload = _require_json_object(
        resolved_receipt_interpretation,
        label="Cortex receipt-interpretation artifact",
    )
    stack_handoff_payload = _require_json_object(
        resolved_stack_handoff,
        label="Cortex stack-advisory-handoff artifact",
    )
    pilot_payload = _require_json_object(
        resolved_pilot,
        label="Cortex stack-consumption-pilot artifact",
    )
    worker_prompt_payload = _require_json_object(
        resolved_worker_prompt,
        label="Cortex worker-prompt artifact",
    )
    ledger_payload = _require_json_object(resolved_ledger, label="Cortex ledger artifact")
    validation_payload = _require_json_object(resolved_validation, label="Stack validation receipt")
    state_model_payload = _require_json_object(resolved_state_model, label="Cortex state model seed")
    rule_registry_payload = _require_json_object(resolved_rule_registry, label="Cortex rule registry seed")

    receipt_interpretation_ref = atlas_relative(resolved_receipt_interpretation, root=base)
    stack_handoff_ref = atlas_relative(resolved_stack_handoff, root=base)
    pilot_ref = atlas_relative(resolved_pilot, root=base)
    worker_prompt_ref = atlas_relative(resolved_worker_prompt, root=base)
    ledger_ref = atlas_relative(resolved_ledger, root=base)
    validation_ref = atlas_relative(resolved_validation, root=base)
    state_model_ref = atlas_relative(resolved_state_model, root=base)
    rule_registry_ref = atlas_relative(resolved_rule_registry, root=base)

    artifact_inputs = [
        _artifact_input(receipt_interpretation_ref, "receipt_interpretation", receipt_interpretation_payload),
        _artifact_input(stack_handoff_ref, "stack_advisory_handoff", stack_handoff_payload),
        _artifact_input(pilot_ref, "stack_consumption_pilot", pilot_payload),
        _artifact_input(worker_prompt_ref, "worker_prompt", worker_prompt_payload),
        _artifact_input(ledger_ref, "ledger", ledger_payload),
        _artifact_input(validation_ref, "validation_receipt", validation_payload),
        _artifact_input(state_model_ref, "state_model_seed", state_model_payload),
        _artifact_input(rule_registry_ref, "rule_registry_seed", rule_registry_payload),
    ]

    interpretation_result = _dict(receipt_interpretation_payload.get("interpretation_result"))
    interpreted_proof_summary = _dict(receipt_interpretation_payload.get("interpreted_proof_summary"))
    interpretation_authority = _dict(receipt_interpretation_payload.get("authority"))
    handoff_result = _dict(stack_handoff_payload.get("handoff_result"))
    routing_contract = _dict(stack_handoff_payload.get("routing_contract"))
    pilot_result = _dict(pilot_payload.get("pilot_result"))
    pilot_handoff = _dict(pilot_payload.get("stack_handoff"))
    validation_counts = _validation_counts(validation_payload)
    validation_blockers = _validation_blockers(validation_payload)

    source_refs = _ordered_unique_strings(
        [
            receipt_interpretation_ref,
            stack_handoff_ref,
            pilot_ref,
            worker_prompt_ref,
            ledger_ref,
            validation_ref,
            state_model_ref,
            rule_registry_ref,
            *_list(receipt_interpretation_payload.get("source_refs")),
            *_list(stack_handoff_payload.get("source_refs")),
            *_list(pilot_payload.get("source_refs")),
            *_list(worker_prompt_payload.get("source_refs")),
            *[item["ref"] for item in artifact_inputs],
        ]
    )
    transcript_refs = _transcript_refs(source_refs)

    receipt_interpretation_ready = (
        _string(receipt_interpretation_payload.get("contract_version")) == RECEIPT_INTERPRETATION_CONTRACT_VERSION
        and _string(interpretation_result.get("status")) == "ready"
        and bool(interpretation_result.get("ready_for_stack_consumer"))
    )
    receipt_interpretation_authority_clean = not _guard_widened(
        interpretation_authority,
        "final_receipt_authorized",
        "approval_authorized",
        "execution_authorized",
        "dispatch_authorized",
        "owner_truth_mutation_authorized",
        "lifeline_truth_mutation_authorized",
        "transcript_scraping_allowed",
    )
    handoff_ready = _string(handoff_result.get("status")) == "ready"
    handoff_authority_clean = not _guard_widened(
        routing_contract,
        "automatic_dispatch_enabled",
        "execution_authorized",
        "receipt_authorized",
        "owner_truth_mutation_authorized",
        "transcript_scraping_allowed",
    )
    pilot_ready = _string(pilot_result.get("status")) == "ready"
    pilot_authority_clean = not _guard_widened(
        pilot_handoff,
        "automatic_dispatch_enabled",
        "default_routing_enabled",
        "execution_authorized",
        "receipt_authorized",
        "owner_truth_mutation_authorized",
        "transcript_scraping_allowed",
    )
    validation_ready = validation_counts["critical"] == 0 and validation_counts["error"] == 0

    checks = [
        _check(
            "receipt-interpretation-ready",
            receipt_interpretation_ready,
            "Receipt interpretation contract is present and ready for stack consumption.",
            source_ref=receipt_interpretation_ref,
        ),
        _check(
            "receipt-interpretation-authority-guard-clean",
            receipt_interpretation_authority_clean,
            "Receipt interpretation does not widen final receipt, approval, execution, dispatch, truth-mutation, or transcript authority.",
            source_ref=receipt_interpretation_ref,
        ),
        _check(
            "stack-advisory-handoff-ready",
            handoff_ready,
            "Stack advisory handoff is ready.",
            source_ref=stack_handoff_ref,
        ),
        _check(
            "stack-advisory-handoff-authority-guard-clean",
            handoff_authority_clean,
            "Stack advisory handoff does not widen dispatch, execution, receipt, owner-truth, or transcript authority.",
            source_ref=stack_handoff_ref,
        ),
        _check(
            "stack-consumption-pilot-ready",
            pilot_ready,
            "Stack-consumption pilot is ready.",
            source_ref=pilot_ref,
        ),
        _check(
            "stack-consumption-pilot-authority-guard-clean",
            pilot_authority_clean,
            "Stack-consumption pilot does not widen dispatch, execution, receipt, owner-truth, or transcript authority.",
            source_ref=pilot_ref,
        ),
        _check(
            "validation-critical-error-absent",
            validation_ready,
            "Stack validation has no critical or error findings.",
            source_ref=validation_ref,
        ),
        _check(
            "transcript-scraping-absent",
            not transcript_refs,
            "Consumed source refs and artifact refs do not include transcripts, runtime/atlas/conversations, or runtime/atlas/sessions.",
            source_ref=receipt_interpretation_ref,
        ),
    ]
    failed_checks = [check["check_id"] for check in checks if check["status"] != "passed"]
    ready = not failed_checks

    next_lane = _dict(receipt_interpretation_payload.get("next_recommended_lane")) or _dict(
        ledger_payload.get("next_recommended_lane")
    )
    lane_id = _string(next_lane.get("lane_id"))
    interpretation_blocked_reason = _string(interpretation_result.get("blocked_reason"))
    interpreted_status = _string(interpreted_proof_summary.get("status")) or (
        "proof_ready" if ready else "proof_blocked"
    )

    blocked_reason = (
        _blocked_reason(
            failed_checks=failed_checks,
            interpretation_blocked_reason=interpretation_blocked_reason,
            validation_blockers=validation_blockers,
            transcript_refs=transcript_refs,
        )
        if not ready
        else ""
    )
    proof_blockers = _ordered_unique_strings(
        [
            *_list(interpreted_proof_summary.get("what_remains_blocked")),
            interpretation_blocked_reason,
            *validation_blockers,
            blocked_reason,
        ]
    )

    return {
        "contract_version": RECEIPT_INTERPRETATION_STACK_CONSUMPTION_CONTRACT_VERSION,
        "generated_at": _utc_now(),
        "authority_level": RECEIPT_INTERPRETATION_STACK_CONSUMPTION_AUTHORITY_LEVEL,
        "stack_root": normalize_slashes(str(base)),
        "consumption_id": f"receipt-interpretation-stack-consumption-{lane_id or 'unknown'}",
        "consumer": {
            "consumer_id": STACK_CONSUMER_ID,
            "consumer_role": STACK_CONSUMER_ROLE,
            "consumption_mode": STACK_CONSUMPTION_MODE,
        },
        "next_recommended_lane": {
            "lane_id": lane_id,
            "owner_layer": _string(next_lane.get("owner_layer")),
            "rationale": _string(next_lane.get("rationale")),
        },
        "authority": _authority(),
        "artifact_inputs": artifact_inputs,
        "receipt_interpretation_ref": receipt_interpretation_ref,
        "receipt_interpretation_digest": stable_json_digest(receipt_interpretation_payload),
        "consumption_checks": checks,
        "consumption_result": {
            "status": "ready" if ready else "blocked",
            "ready_for_stack_consumer": ready,
            "blocked_reason": None if ready else blocked_reason,
            "failed_checks": failed_checks,
        },
        "consumption_summary": {
            "interpreted_status": interpreted_status,
            "what_changed": _ordered_unique_strings(
                [
                    "_stack consumed the Cortex receipt interpretation artifact through explicit artifact refs only.",
                    *_list(interpreted_proof_summary.get("what_changed")),
                ]
            ),
            "what_proved": _ordered_unique_strings(
                [
                    f"Receipt interpretation proof posture is {interpreted_status}.",
                    *_list(interpreted_proof_summary.get("what_proved")),
                ]
            ),
            "what_remains_blocked": proof_blockers,
            "receipt_authority_summary": _string(interpreted_proof_summary.get("receipt_authority_summary"))
            or "Lifeline owns final receipt authority; _stack consumption remains advisory only.",
        },
        "authority_guards": _authority_guards(),
        "boundary_reminders": _ordered_unique_strings(
            [
                "_stack may consume Cortex receipt interpretation artifacts only through explicit artifact refs.",
                "_stack consumption ready does not mean dispatch, execution, approval, or final receipt authority.",
                "Lifeline owns final receipt authority.",
                *_list(receipt_interpretation_payload.get("boundary_reminders")),
            ]
        ),
        "source_refs": source_refs,
    }


def render_receipt_interpretation_stack_consumption_summary(payload: dict[str, Any]) -> str:
    next_lane = payload["next_recommended_lane"]
    authority = payload["authority"]
    result = payload["consumption_result"]
    summary = payload["consumption_summary"]
    lines = [
        "# Cortex Receipt Interpretation Stack Consumption",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Consumption id: `{payload['consumption_id']}`",
        f"- Authority level: `{payload['authority_level']}`",
        f"- Consumer: `{payload['consumer']['consumer_id']}`",
        f"- Consumer role: `{payload['consumer']['consumer_role']}`",
        f"- Consumption mode: `{payload['consumer']['consumption_mode']}`",
        f"- Next recommended lane: `{next_lane['lane_id']}` ({next_lane['owner_layer']})",
        f"- Consumption status: `{result['status']}`",
        f"- Ready for _stack consumer: `{'yes' if result['ready_for_stack_consumer'] else 'no'}`",
        f"- Stack consumption authorized: `{'yes' if authority['stack_consumption_authorized'] else 'no'}`",
        f"- Final receipt authorized: `{'yes' if authority['final_receipt_authorized'] else 'no'}`",
        f"- Approval authorized: `{'yes' if authority['approval_authorized'] else 'no'}`",
        f"- Execution authorized: `{'yes' if authority['execution_authorized'] else 'no'}`",
        f"- Dispatch authorized: `{'yes' if authority['dispatch_authorized'] else 'no'}`",
        f"- No transcript scraping: `{'yes' if not authority['transcript_scraping_allowed'] else 'no'}`",
        "- Lifeline owns final receipt authority.",
        "",
        "## Consumption Checks",
    ]
    for check in payload["consumption_checks"]:
        lines.append(f"- `{check['check_id']}`: {check['status']} - {check['summary']}")

    lines.extend(["", "## What Proved"])
    for item in summary["what_proved"]:
        lines.append(f"- {item}")

    lines.extend(["", "## What Remains Blocked"])
    for item in summary["what_remains_blocked"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Authority Guards"])
    for guard in payload["authority_guards"]:
        lines.append(f"- {guard}")
    return "\n".join(lines) + "\n"


def persist_receipt_interpretation_stack_consumption_artifact(
    *,
    root: Path | None = None,
    receipt_interpretation_path: Path | None = None,
    stack_handoff_path: Path | None = None,
    stack_consumption_pilot_path: Path | None = None,
    worker_prompt_path: Path | None = None,
    ledger_path: Path | None = None,
    validation_receipt_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    output_json_path: Path | None = None,
    output_markdown_path: Path | None = None,
    write_markdown: bool = True,
) -> PersistedReceiptInterpretationStackConsumptionArtifact:
    base = (root or atlas_root()).resolve()
    artifact_path = (
        output_json_path or default_receipt_interpretation_stack_consumption_latest_json_path(base)
    ).resolve()
    summary_path = (
        (output_markdown_path or default_receipt_interpretation_stack_consumption_latest_markdown_path(base)).resolve()
        if write_markdown
        else None
    )
    payload = build_receipt_interpretation_stack_consumption_payload(
        root=base,
        receipt_interpretation_path=receipt_interpretation_path.resolve() if receipt_interpretation_path else None,
        stack_handoff_path=stack_handoff_path.resolve() if stack_handoff_path else None,
        stack_consumption_pilot_path=stack_consumption_pilot_path.resolve()
        if stack_consumption_pilot_path
        else None,
        worker_prompt_path=worker_prompt_path.resolve() if worker_prompt_path else None,
        ledger_path=ledger_path.resolve() if ledger_path else None,
        validation_receipt_path=validation_receipt_path.resolve() if validation_receipt_path else None,
        state_model_path=state_model_path.resolve() if state_model_path else None,
        rule_registry_path=rule_registry_path.resolve() if rule_registry_path else None,
    )
    summary = render_receipt_interpretation_stack_consumption_summary(payload)
    write_json(artifact_path, payload)
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
    return PersistedReceiptInterpretationStackConsumptionArtifact(
        artifact_path=artifact_path,
        summary_path=summary_path,
        payload_digest=stable_json_digest(payload),
        payload=payload,
        summary=summary,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Persist the Cortex receipt-interpretation stack-consumption artifact."
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--receipt-interpretation-path", type=Path)
    parser.add_argument("--stack-handoff-path", type=Path)
    parser.add_argument("--stack-consumption-pilot-path", type=Path)
    parser.add_argument("--worker-prompt-path", type=Path)
    parser.add_argument("--ledger-path", type=Path)
    parser.add_argument("--validation-receipt-path", type=Path)
    parser.add_argument("--state-model-path", type=Path)
    parser.add_argument("--rule-registry-path", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-markdown", type=Path)
    parser.add_argument("--no-write-markdown", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    try:
        artifact = persist_receipt_interpretation_stack_consumption_artifact(
            root=args.root.resolve(),
            receipt_interpretation_path=args.receipt_interpretation_path.resolve()
            if args.receipt_interpretation_path
            else None,
            stack_handoff_path=args.stack_handoff_path.resolve() if args.stack_handoff_path else None,
            stack_consumption_pilot_path=args.stack_consumption_pilot_path.resolve()
            if args.stack_consumption_pilot_path
            else None,
            worker_prompt_path=args.worker_prompt_path.resolve() if args.worker_prompt_path else None,
            ledger_path=args.ledger_path.resolve() if args.ledger_path else None,
            validation_receipt_path=args.validation_receipt_path.resolve() if args.validation_receipt_path else None,
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
