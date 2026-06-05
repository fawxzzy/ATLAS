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
from ops.cortex.receipt_interpretation_stack_consumption import (
    RECEIPT_INTERPRETATION_STACK_CONSUMPTION_CONTRACT_VERSION,
    default_receipt_interpretation_stack_consumption_latest_json_path,
)
from ops.cortex.receipt_interpreter import (
    RECEIPT_INTERPRETATION_CONTRACT_VERSION,
    default_receipt_interpretation_latest_json_path,
)
from ops.cortex.stack_consumption_pilot import default_stack_consumption_pilot_latest_json_path
from ops.cortex.stack_handoff import default_stack_advisory_handoff_latest_json_path
from ops.cortex.worker_prompt import default_worker_prompt_latest_json_path

RECEIPT_INTERPRETATION_CONSUMPTION_FEEDBACK_CONTRACT_VERSION = (
    "atlas.cortex.receipt-interpretation-consumption-feedback.v1"
)
RECEIPT_INTERPRETATION_CONSUMPTION_FEEDBACK_AUTHORITY_LEVEL = "read_only_feedback"


def receipt_interpretation_consumption_feedback_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "receipt-interpretation-consumption-feedback"


def default_receipt_interpretation_consumption_feedback_latest_json_path(root: Path | None = None) -> Path:
    return receipt_interpretation_consumption_feedback_root(root) / "latest.json"


def default_receipt_interpretation_consumption_feedback_latest_markdown_path(root: Path | None = None) -> Path:
    return receipt_interpretation_consumption_feedback_root(root) / "latest.md"


@dataclass(frozen=True)
class PersistedReceiptInterpretationConsumptionFeedbackArtifact:
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
        "feedback_authorized": True,
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
        "Cortex feedback remains a read-only summary over explicit artifact refs.",
        "Feedback does not dispatch or execute _stack work.",
        "Feedback does not approve work, issue final receipts, or mutate owner or Lifeline truth.",
        "Feedback does not scrape transcripts.",
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
        if "transcript" in lowered or "runtime/atlas/conversations" in lowered or "runtime/atlas/sessions" in lowered:
            suspicious.append(value)
    return _ordered_unique_strings(suspicious)


def _feedback_blocked_reason(
    *,
    failed_checks: list[str],
    validation_blockers: list[str],
    upstream_blocked_reasons: list[str],
    transcript_refs: list[str],
) -> str:
    details = _ordered_unique_strings(
        [
            f"Failed feedback checks: {', '.join(failed_checks)}." if failed_checks else "",
            *upstream_blocked_reasons,
            *validation_blockers,
            (
                "Transcript-like refs are forbidden for feedback consumption: "
                f"{', '.join(transcript_refs)}."
            )
            if transcript_refs
            else "",
        ]
    )
    return " ".join(details) if details else "Receipt-interpretation consumption feedback is blocked."


def build_receipt_interpretation_consumption_feedback_payload(
    *,
    root: Path | None = None,
    receipt_interpretation_stack_consumption_path: Path | None = None,
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
    resolved_consumption = (
        receipt_interpretation_stack_consumption_path
        or default_receipt_interpretation_stack_consumption_latest_json_path(base)
    ).resolve()
    resolved_interpretation = (
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

    consumption_payload = _require_json_object(
        resolved_consumption,
        label="Cortex receipt-interpretation stack-consumption artifact",
    )
    interpretation_payload = _require_json_object(
        resolved_interpretation,
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

    consumption_ref = atlas_relative(resolved_consumption, root=base)
    interpretation_ref = atlas_relative(resolved_interpretation, root=base)
    stack_handoff_ref = atlas_relative(resolved_stack_handoff, root=base)
    pilot_ref = atlas_relative(resolved_pilot, root=base)
    worker_prompt_ref = atlas_relative(resolved_worker_prompt, root=base)
    ledger_ref = atlas_relative(resolved_ledger, root=base)
    validation_ref = atlas_relative(resolved_validation, root=base)
    state_model_ref = atlas_relative(resolved_state_model, root=base)
    rule_registry_ref = atlas_relative(resolved_rule_registry, root=base)

    artifact_inputs = [
        _artifact_input(consumption_ref, "receipt_interpretation_stack_consumption", consumption_payload),
        _artifact_input(interpretation_ref, "receipt_interpretation", interpretation_payload),
        _artifact_input(stack_handoff_ref, "stack_advisory_handoff", stack_handoff_payload),
        _artifact_input(pilot_ref, "stack_consumption_pilot", pilot_payload),
        _artifact_input(worker_prompt_ref, "worker_prompt", worker_prompt_payload),
        _artifact_input(ledger_ref, "ledger", ledger_payload),
        _artifact_input(validation_ref, "validation_receipt", validation_payload),
        _artifact_input(state_model_ref, "state_model_seed", state_model_payload),
        _artifact_input(rule_registry_ref, "rule_registry_seed", rule_registry_payload),
    ]

    validation_counts = _validation_counts(validation_payload)
    validation_blockers = _validation_blockers(validation_payload)
    consumption_result = _dict(consumption_payload.get("consumption_result"))
    interpretation_result = _dict(interpretation_payload.get("interpretation_result"))
    handoff_result = _dict(stack_handoff_payload.get("handoff_result"))
    pilot_result = _dict(pilot_payload.get("pilot_result"))
    next_recommended_lane = _dict(worker_prompt_payload.get("next_recommended_lane"))

    widened = _guard_widened(
        _dict(consumption_payload.get("authority")),
        "final_receipt_authorized",
        "approval_authorized",
        "execution_authorized",
        "dispatch_authorized",
        "owner_truth_mutation_authorized",
        "lifeline_truth_mutation_authorized",
        "transcript_scraping_allowed",
    )
    transcript_refs = _transcript_refs(
        _ordered_unique_strings(
            [
                *_list(consumption_payload.get("source_refs")),
                *_list(interpretation_payload.get("source_refs")),
                *_list(stack_handoff_payload.get("source_refs")),
                *_list(pilot_payload.get("source_refs")),
            ]
        )
    )

    checks = [
        _check(
            "receipt-interpretation-stack-consumption-contract-version",
            _string(consumption_payload.get("contract_version"))
            == RECEIPT_INTERPRETATION_STACK_CONSUMPTION_CONTRACT_VERSION,
            "Receipt-interpretation stack-consumption artifact uses the promoted contract.",
            source_ref=consumption_ref,
        ),
        _check(
            "receipt-interpretation-contract-version",
            _string(interpretation_payload.get("contract_version")) == RECEIPT_INTERPRETATION_CONTRACT_VERSION,
            "Receipt-interpretation artifact uses the promoted contract.",
            source_ref=interpretation_ref,
        ),
        _check(
            "receipt-interpretation-stack-consumption-ready",
            _string(consumption_result.get("status")) == "ready" and bool(consumption_result.get("ready_for_stack_consumer")),
            "Receipt-interpretation stack consumption is ready.",
            source_ref=consumption_ref,
        ),
        _check(
            "receipt-interpretation-ready",
            _string(interpretation_result.get("status")) == "ready",
            "Receipt interpretation is ready.",
            source_ref=interpretation_ref,
        ),
        _check(
            "stack-advisory-handoff-ready",
            _string(handoff_result.get("status")) == "ready" and bool(handoff_result.get("ready_for_stack_consumer")),
            "Stack advisory handoff is ready.",
            source_ref=stack_handoff_ref,
        ),
        _check(
            "stack-consumption-pilot-ready",
            _string(pilot_result.get("status")) == "ready" and bool(pilot_result.get("ready_for_stack_consumer")),
            "Stack-consumption pilot is ready.",
            source_ref=pilot_ref,
        ),
        _check(
            "validation-critical-error-absent",
            validation_counts["critical"] == 0 and validation_counts["error"] == 0,
            "Validation receipt reports no critical/error findings.",
            source_ref=validation_ref,
        ),
        _check(
            "receipt-interpretation-stack-consumption-authority-guard-clean",
            not widened,
            "Receipt-interpretation stack consumption keeps all authority-widening guards disabled.",
            source_ref=consumption_ref,
        ),
        _check(
            "transcript-scraping-absent",
            not transcript_refs,
            "Feedback consumption remains explicit-artifact-only with no transcript scraping.",
            source_ref=consumption_ref,
        ),
    ]

    failed_checks = [check["check_id"] for check in checks if check["status"] != "passed"]
    upstream_blocked_reasons = _ordered_unique_strings(
        [
            _string(consumption_result.get("blocked_reason")),
            _string(interpretation_result.get("blocked_reason")),
        ]
    )
    blocked_reason = (
        _feedback_blocked_reason(
            failed_checks=failed_checks,
            validation_blockers=validation_blockers,
            upstream_blocked_reasons=upstream_blocked_reasons,
            transcript_refs=transcript_refs,
        )
        if failed_checks
        else None
    )

    what_changed = _ordered_unique_strings(
        [
            *_list(_dict(consumption_payload.get("consumption_summary")).get("what_changed")),
            (
                "Validation receipt refreshed to "
                f"critical={validation_counts['critical']} error={validation_counts['error']} "
                f"warning={validation_counts['warning']} info={validation_counts['info']}."
            ),
        ]
    )
    what_proved = _ordered_unique_strings(
        [
            *_list(_dict(interpretation_payload.get("interpreted_proof_summary")).get("what_proved")),
            *_list(_dict(consumption_payload.get("consumption_summary")).get("what_proved")),
            "Feedback remains read-only and keeps all authority-widening guards false.",
        ]
    )
    what_remains_blocked = _ordered_unique_strings(
        [
            *_list(_dict(interpretation_payload.get("interpreted_proof_summary")).get("what_remains_blocked")),
            *_list(_dict(consumption_payload.get("consumption_summary")).get("what_remains_blocked")),
            blocked_reason or "",
        ]
    )

    feedback_result = {
        "status": "ready" if not failed_checks else "blocked",
        "ready_for_feedback_consumer": not failed_checks,
        "blocked_reason": blocked_reason,
        "failed_checks": failed_checks,
    }

    return {
        "contract_version": RECEIPT_INTERPRETATION_CONSUMPTION_FEEDBACK_CONTRACT_VERSION,
        "generated_at": _utc_now(),
        "authority_level": RECEIPT_INTERPRETATION_CONSUMPTION_FEEDBACK_AUTHORITY_LEVEL,
        "stack_root": normalize_slashes(str(base)),
        "feedback_id": f"receipt-interpretation-consumption-feedback-{_string(next_recommended_lane.get('lane_id')) or 'unknown'}",
        "next_recommended_lane": next_recommended_lane,
        "receipt_interpretation_ref": interpretation_ref,
        "receipt_interpretation_digest": stable_json_digest(interpretation_payload),
        "receipt_interpretation_stack_consumption_ref": consumption_ref,
        "receipt_interpretation_stack_consumption_digest": stable_json_digest(consumption_payload),
        "artifact_inputs": artifact_inputs,
        "authority": _authority(),
        "authority_guards": _authority_guards(),
        "feedback_checks": checks,
        "feedback_result": feedback_result,
        "feedback_summary": {
            "status": "feedback_ready" if not failed_checks else "feedback_blocked",
            "what_changed": what_changed,
            "what_proved": what_proved,
            "what_remains_blocked": what_remains_blocked,
        },
        "boundary_reminders": _ordered_unique_strings(
            [
                *_list(worker_prompt_payload.get("boundary_reminders")),
                *_list(consumption_payload.get("boundary_reminders")),
            ]
        ),
        "source_refs": _ordered_unique_strings(
            [
                consumption_ref,
                interpretation_ref,
                stack_handoff_ref,
                pilot_ref,
                worker_prompt_ref,
                ledger_ref,
                validation_ref,
                state_model_ref,
                rule_registry_ref,
            ]
        ),
    }


def render_receipt_interpretation_consumption_feedback_summary(payload: dict[str, Any]) -> str:
    result = _dict(payload.get("feedback_result"))
    summary = _dict(payload.get("feedback_summary"))
    lane = _dict(payload.get("next_recommended_lane"))
    lines = [
        "# Cortex Receipt Interpretation Consumption Feedback",
        "",
        f"- Generated: `{_string(payload.get('generated_at'))}`",
        f"- Feedback id: `{_string(payload.get('feedback_id'))}`",
        f"- Authority level: `{_string(payload.get('authority_level'))}`",
        f"- Next recommended lane: `{_string(lane.get('lane_id'))}` ({_string(lane.get('owner_layer'))})",
        f"- Feedback status: `{_string(result.get('status'))}`",
        f"- Ready for feedback consumer: `{'yes' if result.get('ready_for_feedback_consumer') else 'no'}`",
        "",
        "## What Changed",
    ]
    changed = _list(summary.get("what_changed"))
    if changed:
        lines.extend([f"- {item}" for item in changed if isinstance(item, str) and item.strip()])
    else:
        lines.append("- none")

    lines.extend(["", "## What Proved"])
    proved = _list(summary.get("what_proved"))
    if proved:
        lines.extend([f"- {item}" for item in proved if isinstance(item, str) and item.strip()])
    else:
        lines.append("- none")

    lines.extend(["", "## What Remains Blocked"])
    blocked = _list(summary.get("what_remains_blocked"))
    if blocked:
        lines.extend([f"- {item}" for item in blocked if isinstance(item, str) and item.strip()])
    else:
        lines.append("- none")

    lines.extend(["", "## Authority Guards"])
    lines.extend([f"- {item}" for item in _list(payload.get("authority_guards")) if isinstance(item, str) and item.strip()])

    lines.extend(["", "## Feedback Checks"])
    for check in _list(payload.get("feedback_checks")):
        if not isinstance(check, dict):
            continue
        lines.append(f"- `{_string(check.get('check_id'))}`: {_string(check.get('status'))} - {_string(check.get('summary'))}")

    return "\n".join(lines) + "\n"


def persist_receipt_interpretation_consumption_feedback_artifact(
    *,
    root: Path | None = None,
    receipt_interpretation_stack_consumption_path: Path | None = None,
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
) -> PersistedReceiptInterpretationConsumptionFeedbackArtifact:
    base = (root or atlas_root()).resolve()
    artifact_path = (
        output_json_path or default_receipt_interpretation_consumption_feedback_latest_json_path(base)
    ).resolve()
    summary_path = (
        (output_markdown_path or default_receipt_interpretation_consumption_feedback_latest_markdown_path(base)).resolve()
        if write_markdown
        else None
    )
    payload = build_receipt_interpretation_consumption_feedback_payload(
        root=base,
        receipt_interpretation_stack_consumption_path=(
            receipt_interpretation_stack_consumption_path.resolve()
            if receipt_interpretation_stack_consumption_path is not None
            else None
        ),
        receipt_interpretation_path=receipt_interpretation_path.resolve() if receipt_interpretation_path is not None else None,
        stack_handoff_path=stack_handoff_path.resolve() if stack_handoff_path is not None else None,
        stack_consumption_pilot_path=stack_consumption_pilot_path.resolve() if stack_consumption_pilot_path is not None else None,
        worker_prompt_path=worker_prompt_path.resolve() if worker_prompt_path is not None else None,
        ledger_path=ledger_path.resolve() if ledger_path is not None else None,
        validation_receipt_path=validation_receipt_path.resolve() if validation_receipt_path is not None else None,
        state_model_path=state_model_path.resolve() if state_model_path is not None else None,
        rule_registry_path=rule_registry_path.resolve() if rule_registry_path is not None else None,
    )
    summary = render_receipt_interpretation_consumption_feedback_summary(payload)
    write_json(artifact_path, payload)
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
    return PersistedReceiptInterpretationConsumptionFeedbackArtifact(
        artifact_path=artifact_path,
        summary_path=summary_path,
        payload_digest=stable_json_digest(payload),
        payload=payload,
        summary=summary,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Persist the read-only Cortex receipt-interpretation consumption feedback artifact."
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--receipt-interpretation-stack-consumption-path", type=Path)
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
        artifact = persist_receipt_interpretation_consumption_feedback_artifact(
            root=args.root.resolve(),
            receipt_interpretation_stack_consumption_path=(
                args.receipt_interpretation_stack_consumption_path.resolve()
                if args.receipt_interpretation_stack_consumption_path
                else None
            ),
            receipt_interpretation_path=args.receipt_interpretation_path.resolve() if args.receipt_interpretation_path else None,
            stack_handoff_path=args.stack_handoff_path.resolve() if args.stack_handoff_path else None,
            stack_consumption_pilot_path=args.stack_consumption_pilot_path.resolve() if args.stack_consumption_pilot_path else None,
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
