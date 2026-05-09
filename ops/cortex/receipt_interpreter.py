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
from ops.cortex.lifeline_receipt_payload import (
    LIFELINE_RECEIPT_CANDIDATE_CONTRACT_VERSION,
    default_lifeline_receipt_candidate_latest_json_path,
)
from ops.cortex.stack_consumption_pilot import default_stack_consumption_pilot_latest_json_path
from ops.cortex.stack_handoff import default_stack_advisory_handoff_latest_json_path
from ops.cortex.worker_prompt import default_worker_prompt_latest_json_path

RECEIPT_INTERPRETATION_CONTRACT_VERSION = "atlas.cortex.receipt-interpretation.v1"
RECEIPT_INTERPRETATION_AUTHORITY_LEVEL = "read_only_interpretation"


def receipt_interpretation_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "receipt-interpretation"


def default_receipt_interpretation_latest_json_path(root: Path | None = None) -> Path:
    return receipt_interpretation_root(root) / "latest.json"


def default_receipt_interpretation_latest_markdown_path(root: Path | None = None) -> Path:
    return receipt_interpretation_root(root) / "latest.md"


@dataclass(frozen=True)
class PersistedReceiptInterpretationArtifact:
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


def _optional_json_object(path: Path) -> dict[str, Any] | None:
    resolved = path.resolve()
    if not resolved.exists():
        return None
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
        "interpretation_authorized": True,
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
        "Cortex receipt interpretation is a read-only proof-summary surface.",
        "Lifeline remains the final receipt authority.",
        "Receipt interpretation does not approve work, execute work, dispatch _stack work, or mutate owner truth.",
        "Receipt interpretation consumes explicit artifacts only and does not scrape transcripts.",
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


def _final_receipt_owner_claim(payload: dict[str, Any]) -> str:
    candidates: list[str] = []
    for key in ("final_receipt_owner", "owner", "prepared_by"):
        value = payload.get(key)
        if isinstance(value, str):
            candidates.append(value)
    boundary = _dict(payload.get("boundary"))
    for key in ("final_receipt_owner", "owner", "prepared_by"):
        value = boundary.get(key)
        if isinstance(value, str):
            candidates.append(value)
    return " ".join(candidates).lower()


def _receipt_observation_for_candidate(ref: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    if payload.get("contract_version") != LIFELINE_RECEIPT_CANDIDATE_CONTRACT_VERSION:
        return None
    if payload.get("final_receipt_owner") != "lifeline":
        return None
    if payload.get("final_receipt_written") is not False:
        return None
    return {
        "role": "lifeline_receipt_candidate",
        "ref": ref,
        "contract_version": LIFELINE_RECEIPT_CANDIDATE_CONTRACT_VERSION,
        "digest": stable_json_digest(payload),
        "summary": "Cortex observed a Lifeline-owned receipt candidate; no final receipt was written by Cortex.",
    }


def _receipt_observation_for_explicit(ref: str, payload: dict[str, Any]) -> tuple[dict[str, Any] | None, bool]:
    owner_claim = _final_receipt_owner_claim(payload)
    if "cortex" in owner_claim and "lifeline" not in owner_claim:
        return None, True
    if "lifeline" not in owner_claim:
        return None, False
    return (
        {
            "role": "explicit_receipt",
            "ref": ref,
            "contract_version": _string(payload.get("contract_version") or payload.get("schema_version")),
            "digest": stable_json_digest(payload),
            "summary": "Cortex observed an explicit Lifeline-owned final receipt artifact.",
        },
        False,
    )


def build_receipt_interpretation_payload(
    *,
    root: Path | None = None,
    worker_prompt_path: Path | None = None,
    stack_handoff_path: Path | None = None,
    stack_consumption_pilot_path: Path | None = None,
    ledger_path: Path | None = None,
    validation_receipt_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    lifeline_receipt_candidate_path: Path | None = None,
    receipt_paths: list[Path] | None = None,
) -> dict[str, Any]:
    base = (root or atlas_root()).resolve()
    resolved_worker_prompt = (worker_prompt_path or default_worker_prompt_latest_json_path(base)).resolve()
    resolved_stack_handoff = (stack_handoff_path or default_stack_advisory_handoff_latest_json_path(base)).resolve()
    resolved_pilot = (stack_consumption_pilot_path or default_stack_consumption_pilot_latest_json_path(base)).resolve()
    resolved_ledger = (ledger_path or default_ledger_latest_json_path(base)).resolve()
    resolved_validation = (
        validation_receipt_path or base / "runtime" / "receipts" / "validation" / "stack-validation.latest.json"
    ).resolve()
    resolved_state_model = (state_model_path or default_state_model_path(base)).resolve()
    resolved_rule_registry = (rule_registry_path or default_rule_registry_path(base)).resolve()
    resolved_candidate = (lifeline_receipt_candidate_path or default_lifeline_receipt_candidate_latest_json_path(base)).resolve()

    worker_prompt_payload = _require_json_object(resolved_worker_prompt, label="Cortex worker-prompt artifact")
    stack_handoff_payload = _require_json_object(resolved_stack_handoff, label="Cortex stack-advisory-handoff artifact")
    pilot_payload = _require_json_object(resolved_pilot, label="Cortex stack-consumption-pilot artifact")
    ledger_payload = _require_json_object(resolved_ledger, label="Cortex ledger artifact")
    validation_payload = _require_json_object(resolved_validation, label="Stack validation receipt")
    state_model_payload = _require_json_object(resolved_state_model, label="Cortex state model seed")
    rule_registry_payload = _require_json_object(resolved_rule_registry, label="Cortex rule registry seed")

    worker_prompt_ref = atlas_relative(resolved_worker_prompt, root=base)
    stack_handoff_ref = atlas_relative(resolved_stack_handoff, root=base)
    pilot_ref = atlas_relative(resolved_pilot, root=base)
    ledger_ref = atlas_relative(resolved_ledger, root=base)
    validation_ref = atlas_relative(resolved_validation, root=base)
    state_model_ref = atlas_relative(resolved_state_model, root=base)
    rule_registry_ref = atlas_relative(resolved_rule_registry, root=base)

    artifact_inputs = [
        _artifact_input(worker_prompt_ref, "worker_prompt", worker_prompt_payload),
        _artifact_input(stack_handoff_ref, "stack_advisory_handoff", stack_handoff_payload),
        _artifact_input(pilot_ref, "stack_consumption_pilot", pilot_payload),
        _artifact_input(ledger_ref, "ledger", ledger_payload),
        _artifact_input(validation_ref, "validation_receipt", validation_payload),
        _artifact_input(state_model_ref, "state_model_seed", state_model_payload),
        _artifact_input(rule_registry_ref, "rule_registry_seed", rule_registry_payload),
    ]

    receipt_observations: list[dict[str, Any]] = []
    explicit_cortex_owner_claim = False
    candidate_payload = _optional_json_object(resolved_candidate)
    if candidate_payload is not None:
        candidate_ref = atlas_relative(resolved_candidate, root=base)
        artifact_inputs.append(_artifact_input(candidate_ref, "lifeline_receipt_candidate", candidate_payload))
        candidate_observation = _receipt_observation_for_candidate(candidate_ref, candidate_payload)
        if candidate_observation is not None:
            receipt_observations.append(candidate_observation)

    for receipt_path in receipt_paths or []:
        resolved_receipt = receipt_path.resolve()
        receipt_payload = _require_json_object(resolved_receipt, label="Explicit receipt artifact")
        receipt_ref = atlas_relative(resolved_receipt, root=base)
        artifact_inputs.append(_artifact_input(receipt_ref, "explicit_receipt", receipt_payload))
        observation, cortex_claim = _receipt_observation_for_explicit(receipt_ref, receipt_payload)
        explicit_cortex_owner_claim = explicit_cortex_owner_claim or cortex_claim
        if observation is not None:
            receipt_observations.append(observation)

    validation_counts = _validation_counts(validation_payload)
    validation_ready = validation_counts["critical"] == 0 and validation_counts["error"] == 0
    validation_blockers = _validation_blockers(validation_payload)
    handoff_result = _dict(stack_handoff_payload.get("handoff_result"))
    routing_contract = _dict(stack_handoff_payload.get("routing_contract"))
    pilot_result = _dict(pilot_payload.get("pilot_result"))
    pilot_handoff = _dict(pilot_payload.get("stack_handoff"))
    handoff_ready = _string(handoff_result.get("status")) == "ready"
    pilot_ready = _string(pilot_result.get("status")) == "ready"
    handoff_authority_clean = not _guard_widened(
        routing_contract,
        "automatic_dispatch_enabled",
        "default_routing_enabled",
        "execution_authorized",
        "receipt_authorized",
        "owner_truth_mutation_authorized",
        "transcript_scraping_allowed",
    )
    pilot_authority_clean = not _guard_widened(
        pilot_handoff,
        "automatic_dispatch_enabled",
        "default_routing_enabled",
        "execution_authorized",
        "receipt_authorized",
        "owner_truth_mutation_authorized",
        "transcript_scraping_allowed",
    )

    checks = [
        _check(
            "validation-critical-error-absent",
            validation_ready,
            "Stack validation has no critical or error findings.",
            source_ref=validation_ref,
        ),
        _check(
            "stack-advisory-handoff-ready",
            handoff_ready,
            "Canonical stack advisory handoff is ready.",
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
            "Stack-consumption pilot does not widen execution, receipt, owner-truth, routing, or transcript authority.",
            source_ref=pilot_ref,
        ),
        _check(
            "cortex-final-receipt-authority-absent",
            not explicit_cortex_owner_claim,
            "Observed receipt artifacts do not claim Cortex as final receipt owner.",
        ),
    ]
    ready = all(check["status"] == "passed" for check in checks)
    failed_checks = [check["check_id"] for check in checks if check["status"] != "passed"]
    next_lane = _dict(stack_handoff_payload.get("next_recommended_lane")) or _dict(ledger_payload.get("next_recommended_lane"))
    lane_id = _string(next_lane.get("lane_id"))

    what_changed = _ordered_unique_strings(
        [
            f"Cortex selected lane {lane_id} for read-only receipt interpretation.",
            "Receipt interpretation joins worker prompt, stack handoff, stack pilot, ledger, validation, seed, and rule artifacts.",
        ]
    )
    what_proved = _ordered_unique_strings(
        [
            "Stack advisory handoff is ready." if handoff_ready else "",
            "Stack-consumption pilot is ready." if pilot_ready else "",
            "Validation has no critical or error findings." if validation_ready else "",
        ]
    )
    what_remains_blocked = _ordered_unique_strings(
        [
            *validation_blockers,
            "No final Lifeline receipt artifact observed; Cortex interpretation remains advisory."
            if not receipt_observations
            else "",
            "Cortex final receipt authority was claimed by an explicit receipt artifact."
            if explicit_cortex_owner_claim
            else "",
        ]
    )
    observed_roles = {observation["role"] for observation in receipt_observations}
    if not ready:
        proof_status = "proof_blocked"
    elif "explicit_receipt" in observed_roles:
        proof_status = "final_receipt_observed"
    elif "lifeline_receipt_candidate" in observed_roles:
        proof_status = "receipt_candidate_observed"
    else:
        proof_status = "proof_ready"

    source_refs = _ordered_unique_strings(
        [
            worker_prompt_ref,
            stack_handoff_ref,
            pilot_ref,
            ledger_ref,
            validation_ref,
            state_model_ref,
            rule_registry_ref,
            *[item["ref"] for item in receipt_observations],
        ]
    )

    return {
        "contract_version": RECEIPT_INTERPRETATION_CONTRACT_VERSION,
        "generated_at": _utc_now(),
        "authority_level": RECEIPT_INTERPRETATION_AUTHORITY_LEVEL,
        "stack_root": normalize_slashes(str(base)),
        "interpretation_id": f"receipt-interpretation-{lane_id or 'unknown'}",
        "next_recommended_lane": {
            "lane_id": lane_id,
            "owner_layer": _string(next_lane.get("owner_layer")),
            "rationale": _string(next_lane.get("rationale")),
        },
        "authority": _authority(),
        "artifact_inputs": artifact_inputs,
        "receipt_observations": receipt_observations,
        "interpreted_proof_summary": {
            "status": proof_status,
            "what_changed": what_changed,
            "what_proved": what_proved,
            "what_remains_blocked": what_remains_blocked,
            "receipt_authority_summary": "Lifeline owns final receipt authority; Cortex interpretation is advisory only.",
        },
        "interpretation_checks": checks,
        "interpretation_result": {
            "status": "ready" if ready else "blocked",
            "ready_for_stack_consumer": ready,
            "blocked_reason": None if ready else f"Failed interpretation checks: {', '.join(failed_checks)}",
            "failed_checks": failed_checks,
        },
        "authority_guards": _authority_guards(),
        "boundary_reminders": _ordered_unique_strings(
            [
                "Cortex may interpret explicit receipt artifacts and summarize proof posture only.",
                "Lifeline owns final receipt authority.",
                "_stack owns orchestration and dispatch truth.",
                "Cortex must not issue final receipts, approve work, mutate owner truth, or scrape transcripts.",
                *_list(ledger_payload.get("boundary_reminders")),
            ]
        ),
        "source_refs": source_refs,
    }


def render_receipt_interpretation_summary(payload: dict[str, Any]) -> str:
    lane = payload["next_recommended_lane"]
    result = payload["interpretation_result"]
    authority = payload["authority"]
    proof = payload["interpreted_proof_summary"]
    lines = [
        "# Cortex Receipt Interpretation",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Interpretation id: `{payload['interpretation_id']}`",
        f"- Authority level: `{payload['authority_level']}`",
        f"- Next recommended lane: `{lane['lane_id']}` ({lane['owner_layer']})",
        f"- Interpretation status: `{result['status']}`",
        f"- Proof status: `{proof['status']}`",
        f"- Ready for _stack consumer: `{'yes' if result['ready_for_stack_consumer'] else 'no'}`",
        f"- Final receipt authorized: `{'yes' if authority['final_receipt_authorized'] else 'no'}`",
        f"- Execution authorized: `{'yes' if authority['execution_authorized'] else 'no'}`",
        f"- Dispatch authorized: `{'yes' if authority['dispatch_authorized'] else 'no'}`",
        f"- No transcript scraping: `{'yes' if not authority['transcript_scraping_allowed'] else 'no'}`",
        "- Lifeline owns final receipt authority.",
        "",
        "## Interpretation Checks",
    ]
    for check in payload["interpretation_checks"]:
        lines.append(f"- `{check['check_id']}`: {check['status']} - {check['summary']}")
    lines.extend(["", "## What Proved"])
    for item in proof["what_proved"]:
        lines.append(f"- {item}")
    lines.extend(["", "## What Remains Blocked"])
    for item in proof["what_remains_blocked"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Authority Guards"])
    for guard in payload["authority_guards"]:
        lines.append(f"- {guard}")
    return "\n".join(lines) + "\n"


def persist_receipt_interpretation_artifact(
    *,
    root: Path | None = None,
    worker_prompt_path: Path | None = None,
    stack_handoff_path: Path | None = None,
    stack_consumption_pilot_path: Path | None = None,
    ledger_path: Path | None = None,
    validation_receipt_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    lifeline_receipt_candidate_path: Path | None = None,
    receipt_paths: list[Path] | None = None,
    output_json_path: Path | None = None,
    output_markdown_path: Path | None = None,
    write_markdown: bool = True,
) -> PersistedReceiptInterpretationArtifact:
    base = (root or atlas_root()).resolve()
    artifact_path = (output_json_path or default_receipt_interpretation_latest_json_path(base)).resolve()
    summary_path = (
        (output_markdown_path or default_receipt_interpretation_latest_markdown_path(base)).resolve()
        if write_markdown
        else None
    )
    payload = build_receipt_interpretation_payload(
        root=base,
        worker_prompt_path=worker_prompt_path.resolve() if worker_prompt_path else None,
        stack_handoff_path=stack_handoff_path.resolve() if stack_handoff_path else None,
        stack_consumption_pilot_path=stack_consumption_pilot_path.resolve() if stack_consumption_pilot_path else None,
        ledger_path=ledger_path.resolve() if ledger_path else None,
        validation_receipt_path=validation_receipt_path.resolve() if validation_receipt_path else None,
        state_model_path=state_model_path.resolve() if state_model_path else None,
        rule_registry_path=rule_registry_path.resolve() if rule_registry_path else None,
        lifeline_receipt_candidate_path=lifeline_receipt_candidate_path.resolve()
        if lifeline_receipt_candidate_path
        else None,
        receipt_paths=[path.resolve() for path in receipt_paths or []],
    )
    summary = render_receipt_interpretation_summary(payload)
    write_json(artifact_path, payload)
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
    return PersistedReceiptInterpretationArtifact(
        artifact_path=artifact_path,
        summary_path=summary_path,
        payload_digest=stable_json_digest(payload),
        payload=payload,
        summary=summary,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Persist the Cortex receipt interpretation artifact.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--worker-prompt-path", type=Path)
    parser.add_argument("--stack-handoff-path", type=Path)
    parser.add_argument("--stack-consumption-pilot-path", type=Path)
    parser.add_argument("--ledger-path", type=Path)
    parser.add_argument("--validation-receipt-path", type=Path)
    parser.add_argument("--state-model-path", type=Path)
    parser.add_argument("--rule-registry-path", type=Path)
    parser.add_argument("--lifeline-receipt-candidate-path", type=Path)
    parser.add_argument("--receipt-path", type=Path, action="append", default=[])
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-markdown", type=Path)
    parser.add_argument("--no-write-markdown", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    try:
        artifact = persist_receipt_interpretation_artifact(
            root=args.root.resolve(),
            worker_prompt_path=args.worker_prompt_path.resolve() if args.worker_prompt_path else None,
            stack_handoff_path=args.stack_handoff_path.resolve() if args.stack_handoff_path else None,
            stack_consumption_pilot_path=args.stack_consumption_pilot_path.resolve()
            if args.stack_consumption_pilot_path
            else None,
            ledger_path=args.ledger_path.resolve() if args.ledger_path else None,
            validation_receipt_path=args.validation_receipt_path.resolve() if args.validation_receipt_path else None,
            state_model_path=args.state_model_path.resolve() if args.state_model_path else None,
            rule_registry_path=args.rule_registry_path.resolve() if args.rule_registry_path else None,
            lifeline_receipt_candidate_path=args.lifeline_receipt_candidate_path.resolve()
            if args.lifeline_receipt_candidate_path
            else None,
            receipt_paths=[path.resolve() for path in args.receipt_path],
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
