from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ops._atlas import atlas_relative, atlas_root, normalize_slashes
from ops.cortex._artifacts import stable_json_digest, write_json
from ops.cortex.feedback import CortexFeedbackResult
from ops.cortex.kernel import CortexProofSummary
from ops.cortex.proof_receipt import ProofReceiptDraft, ProofReceiptKnownDebtSummary
from ops.cortex.run_ledger import CortexRunLedgerAppliedRules, CortexRunLedgerSummary


def _require_object(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Expected object for {field_name}.")
    return value


def _require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Expected non-empty string for {field_name}.")
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"Expected non-empty string for {field_name}.")
    return normalized


def _optional_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Expected string or null for {field_name}.")
    normalized = " ".join(value.strip().split())
    return normalized or None


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"Expected boolean for {field_name}.")
    return value


def _ordered_unique_strings(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"Expected list for {field_name}.")
    ordered: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"Expected string entries in {field_name}.")
        normalized = " ".join(item.strip().split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _coerce_known_debt_summary(value: Any, field_name: str) -> ProofReceiptKnownDebtSummary:
    payload = _require_object(value, field_name)
    return ProofReceiptKnownDebtSummary(
        ambient_debt=_ordered_unique_strings(payload.get("ambient_debt"), f"{field_name}.ambient_debt"),
        current_validation_debt=_ordered_unique_strings(
            payload.get("current_validation_debt"),
            f"{field_name}.current_validation_debt",
        ),
        owner_boundary_status=_require_non_empty_string(
            payload.get("owner_boundary_status"),
            f"{field_name}.owner_boundary_status",
        ),
        notes=_ordered_unique_strings(payload.get("notes"), f"{field_name}.notes"),
    )


def _coerce_receipt_draft(value: Any, field_name: str) -> ProofReceiptDraft:
    payload = _require_object(value, field_name)
    return ProofReceiptDraft(
        receipt_title=_require_non_empty_string(payload.get("receipt_title"), f"{field_name}.receipt_title"),
        owner_layer=_require_non_empty_string(payload.get("owner_layer"), f"{field_name}.owner_layer"),
        next_required_layer=_optional_string(payload.get("next_required_layer"), f"{field_name}.next_required_layer"),
        touched_files=_ordered_unique_strings(payload.get("touched_files"), f"{field_name}.touched_files"),
        passed_commands=_ordered_unique_strings(payload.get("passed_commands"), f"{field_name}.passed_commands"),
        failed_commands=_ordered_unique_strings(payload.get("failed_commands"), f"{field_name}.failed_commands"),
        known_debt=_coerce_known_debt_summary(payload.get("known_debt"), f"{field_name}.known_debt"),
        boundary_statement=_require_non_empty_string(
            payload.get("boundary_statement"),
            f"{field_name}.boundary_statement",
        ),
        next_action=_require_non_empty_string(payload.get("next_action"), f"{field_name}.next_action"),
        receipt_ready=_require_bool(payload.get("receipt_ready"), f"{field_name}.receipt_ready"),
    )


def _coerce_ledger_summary(value: Any, field_name: str) -> CortexRunLedgerSummary:
    payload = _require_object(value, field_name)
    return CortexRunLedgerSummary(
        latest_run_id=_require_non_empty_string(payload.get("latest_run_id"), f"{field_name}.latest_run_id"),
        latest_run_path=_require_non_empty_string(payload.get("latest_run_path"), f"{field_name}.latest_run_path"),
        selected_next_action=_require_non_empty_string(
            payload.get("selected_next_action"),
            f"{field_name}.selected_next_action",
        ),
        owner_layer=_require_non_empty_string(payload.get("owner_layer"), f"{field_name}.owner_layer"),
        next_required_layer=_optional_string(payload.get("next_required_layer"), f"{field_name}.next_required_layer"),
        receipt_ready=_require_bool(payload.get("receipt_ready"), f"{field_name}.receipt_ready"),
        proof_status=_require_non_empty_string(payload.get("proof_status"), f"{field_name}.proof_status"),
        known_ambient_debt=_ordered_unique_strings(payload.get("known_ambient_debt"), f"{field_name}.known_ambient_debt"),
        current_validation_debt=_ordered_unique_strings(
            payload.get("current_validation_debt"),
            f"{field_name}.current_validation_debt",
        ),
        applied_rules=CortexRunLedgerAppliedRules.from_payload(
            _require_object(payload.get("applied_rules"), f"{field_name}.applied_rules")
        ),
        failure_modes_avoided=_ordered_unique_strings(
            payload.get("failure_modes_avoided"),
            f"{field_name}.failure_modes_avoided",
        ),
        blocked_reason=_optional_string(payload.get("blocked_reason"), f"{field_name}.blocked_reason"),
    )


def _coerce_feedback_result(value: CortexFeedbackResult | dict[str, Any]) -> CortexFeedbackResult:
    if isinstance(value, CortexFeedbackResult):
        return value
    if not isinstance(value, dict):
        raise ValueError("Expected CortexFeedbackResult or payload dictionary.")
    return CortexFeedbackResult(
        run_id=_require_non_empty_string(value.get("run_id"), "run_id"),
        selected_next_action=_require_non_empty_string(value.get("selected_next_action"), "selected_next_action"),
        owner_layer=_require_non_empty_string(value.get("owner_layer"), "owner_layer"),
        next_required_layer=_optional_string(value.get("next_required_layer"), "next_required_layer"),
        targeted_verification_passed=_require_bool(
            value.get("targeted_verification_passed"),
            "targeted_verification_passed",
        ),
        stack_validation_status=_require_non_empty_string(
            value.get("stack_validation_status"),
            "stack_validation_status",
        ),
        known_ambient_debt=_ordered_unique_strings(value.get("known_ambient_debt"), "known_ambient_debt"),
        current_validation_debt=_ordered_unique_strings(
            value.get("current_validation_debt"),
            "current_validation_debt",
        ),
        receipt_ready=_require_bool(value.get("receipt_ready"), "receipt_ready"),
        tranche_complete=_require_bool(value.get("tranche_complete"), "tranche_complete"),
        blocked=_require_bool(value.get("blocked"), "blocked"),
        blocked_reason=_optional_string(value.get("blocked_reason"), "blocked_reason"),
        proof_summary=CortexProofSummary.from_payload(
            _require_object(value.get("proof_summary"), "proof_summary")
        ),
        receipt_draft=_coerce_receipt_draft(value.get("receipt_draft"), "receipt_draft"),
        ledger_summary=_coerce_ledger_summary(value.get("ledger_summary"), "ledger_summary"),
        applied_rules=CortexRunLedgerAppliedRules.from_payload(
            _require_object(value.get("applied_rules"), "applied_rules")
        ),
        failure_modes_avoided=_ordered_unique_strings(
            value.get("failure_modes_avoided"),
            "failure_modes_avoided",
        ),
    )


def _resolved_feedback_dir(*, root: Path | None = None, feedback_root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return feedback_root.resolve() if feedback_root is not None else base / "runtime" / "cortex" / "feedback"


def default_feedback_artifact_dir(root: Path | None = None) -> Path:
    return _resolved_feedback_dir(root=root)


def default_feedback_latest_json_path(root: Path | None = None, *, feedback_root: Path | None = None) -> Path:
    return _resolved_feedback_dir(root=root, feedback_root=feedback_root) / "latest.json"


def default_feedback_latest_summary_path(root: Path | None = None, *, feedback_root: Path | None = None) -> Path:
    return _resolved_feedback_dir(root=root, feedback_root=feedback_root) / "latest.txt"


def default_feedback_run_dir(root: Path | None = None, *, feedback_root: Path | None = None) -> Path:
    return _resolved_feedback_dir(root=root, feedback_root=feedback_root) / "runs"


def _run_artifact_stem(run_id: str) -> str:
    normalized = normalize_slashes(_require_non_empty_string(run_id, "run_id"))
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized.replace("/", "__"))
    stem = sanitized.strip(".-")
    if not stem:
        raise ValueError("Expected run_id to produce a usable artifact filename.")
    return stem


def default_feedback_run_json_path(
    run_id: str,
    root: Path | None = None,
    *,
    feedback_root: Path | None = None,
) -> Path:
    return default_feedback_run_dir(root=root, feedback_root=feedback_root) / f"{_run_artifact_stem(run_id)}.json"


def default_feedback_run_summary_path(
    run_id: str,
    root: Path | None = None,
    *,
    feedback_root: Path | None = None,
) -> Path:
    return default_feedback_run_dir(root=root, feedback_root=feedback_root) / f"{_run_artifact_stem(run_id)}.txt"


def _render_list(values: tuple[str, ...]) -> str:
    return " | ".join(values) if values else "none"


def _render_bool(value: bool) -> str:
    return "yes" if value else "no"


def _merged_rule_ids(applied_rules: CortexRunLedgerAppliedRules) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for group in (
        applied_rules.decision_rule_ids,
        applied_rules.plan_rule_ids,
        applied_rules.rule_ids,
    ):
        for rule_id in group:
            normalized = " ".join(rule_id.strip().split())
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
    return tuple(ordered)


def render_feedback_summary(result: CortexFeedbackResult | dict[str, Any]) -> str:
    resolved = _coerce_feedback_result(result)
    lines = [
        "Cortex Feedback Result",
        f"- Run id: {resolved.run_id}",
        f"- Selected next action: {resolved.selected_next_action}",
        f"- Owner layer: {resolved.owner_layer}",
        f"- Next required layer: {resolved.next_required_layer or 'none'}",
        f"- Targeted verification passed: {_render_bool(resolved.targeted_verification_passed)}",
        f"- Stack validation status: {resolved.stack_validation_status}",
        f"- Known ambient debt: {_render_list(resolved.known_ambient_debt)}",
        f"- Current validation debt: {_render_list(resolved.current_validation_debt)}",
        f"- Tranche complete: {_render_bool(resolved.tranche_complete)}",
        f"- Receipt ready: {_render_bool(resolved.receipt_ready)}",
        f"- Blocked: {_render_bool(resolved.blocked)}",
        f"- Blocked reason: {resolved.blocked_reason or 'none'}",
        f"- Applied rules: {_render_list(_merged_rule_ids(resolved.applied_rules))}",
        f"- Patterns applied: {_render_list(resolved.ledger_summary.applied_rules.pattern_ids)}",
        f"- Failure modes avoided: {_render_list(resolved.failure_modes_avoided)}",
        f"- Receipt draft title: {resolved.receipt_draft.receipt_title}",
        f"- Receipt draft status: {'ready' if resolved.receipt_draft.receipt_ready else 'not_ready'}",
        f"- Receipt draft next action: {resolved.receipt_draft.next_action}",
        f"- Receipt draft boundary: {resolved.receipt_draft.boundary_statement}",
        f"- Ledger proof status: {resolved.ledger_summary.proof_status}",
    ]
    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class PersistedCortexFeedbackArtifact:
    latest_artifact_path: Path
    latest_summary_path: Path | None
    run_artifact_path: Path
    run_summary_path: Path | None
    payload_digest: str
    payload: dict[str, object]
    summary: str

    def to_payload(self, *, root: Path | None = None) -> dict[str, object]:
        base = (root or atlas_root()).resolve()
        return {
            "latest_artifact_path": atlas_relative(self.latest_artifact_path, root=base),
            "latest_summary_path": (
                atlas_relative(self.latest_summary_path, root=base) if self.latest_summary_path is not None else None
            ),
            "run_artifact_path": atlas_relative(self.run_artifact_path, root=base),
            "run_summary_path": (
                atlas_relative(self.run_summary_path, root=base) if self.run_summary_path is not None else None
            ),
            "payload_digest": self.payload_digest,
            "summary": self.summary,
        }


def _write_summary(path: Path, summary: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(summary, encoding="utf-8")


class CortexFeedbackArtifactWriter:
    def write(
        self,
        result: CortexFeedbackResult | dict[str, Any],
        *,
        root: Path | None = None,
        feedback_root: Path | None = None,
        latest_json_path: Path | None = None,
        latest_summary_path: Path | None = None,
        run_json_path: Path | None = None,
        run_summary_path: Path | None = None,
        write_summary: bool = True,
    ) -> PersistedCortexFeedbackArtifact:
        resolved = _coerce_feedback_result(result)
        base = (root or atlas_root()).resolve()
        output_root = _resolved_feedback_dir(root=base, feedback_root=feedback_root)
        payload = resolved.to_payload()
        summary = render_feedback_summary(resolved)

        resolved_latest_json_path = (
            latest_json_path.resolve()
            if latest_json_path is not None
            else default_feedback_latest_json_path(base, feedback_root=output_root)
        )
        resolved_run_json_path = (
            run_json_path.resolve()
            if run_json_path is not None
            else default_feedback_run_json_path(resolved.run_id, base, feedback_root=output_root)
        )
        resolved_latest_summary_path = None
        resolved_run_summary_path = None
        if write_summary:
            resolved_latest_summary_path = (
                latest_summary_path.resolve()
                if latest_summary_path is not None
                else default_feedback_latest_summary_path(base, feedback_root=output_root)
            )
            resolved_run_summary_path = (
                run_summary_path.resolve()
                if run_summary_path is not None
                else default_feedback_run_summary_path(resolved.run_id, base, feedback_root=output_root)
            )

        write_json(resolved_latest_json_path, payload)
        write_json(resolved_run_json_path, payload)
        if resolved_latest_summary_path is not None:
            _write_summary(resolved_latest_summary_path, summary)
        if resolved_run_summary_path is not None:
            _write_summary(resolved_run_summary_path, summary)

        return PersistedCortexFeedbackArtifact(
            latest_artifact_path=resolved_latest_json_path,
            latest_summary_path=resolved_latest_summary_path,
            run_artifact_path=resolved_run_json_path,
            run_summary_path=resolved_run_summary_path,
            payload_digest=stable_json_digest(payload),
            payload=payload,
            summary=summary,
        )


def write_feedback_artifact(
    result: CortexFeedbackResult | dict[str, Any],
    *,
    root: Path | None = None,
    feedback_root: Path | None = None,
    latest_json_path: Path | None = None,
    latest_summary_path: Path | None = None,
    run_json_path: Path | None = None,
    run_summary_path: Path | None = None,
    write_summary: bool = True,
) -> PersistedCortexFeedbackArtifact:
    return CortexFeedbackArtifactWriter().write(
        result,
        root=root,
        feedback_root=feedback_root,
        latest_json_path=latest_json_path,
        latest_summary_path=latest_summary_path,
        run_json_path=run_json_path,
        run_summary_path=run_summary_path,
        write_summary=write_summary,
    )
