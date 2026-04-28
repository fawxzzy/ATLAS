from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ops._atlas import atlas_relative, atlas_root, normalize_slashes
from ops.cortex._artifacts import iter_candidate_json_paths, read_json
from ops.cortex.kernel import CortexProofSummary
from ops.cortex.loop import CORTEX_RUN_RESULT_CONTRACT_VERSION
from ops.cortex.verification_ingest import VerificationIngestResult


def default_run_ledger_dir(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "runs"


def _ordered_unique_strings(values: Any, *, field_name: str, allow_none: bool = True) -> tuple[str, ...]:
    if values is None and allow_none:
        return ()
    if not isinstance(values, list):
        raise ValueError(f"Expected list for {field_name}.")
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise ValueError(f"Expected string entries in {field_name}.")
        normalized = " ".join(value.strip().split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


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


def _merge_ordered_strings(*groups: tuple[str, ...]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for value in group:
            normalized = " ".join(str(value).strip().split())
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
    return tuple(ordered)


@dataclass(frozen=True)
class CortexRunLedgerAppliedRules:
    decision_rule_ids: tuple[str, ...] = ()
    plan_rule_ids: tuple[str, ...] = ()
    rule_ids: tuple[str, ...] = ()
    pattern_ids: tuple[str, ...] = ()
    failure_mode_ids: tuple[str, ...] = ()
    why_selected: tuple[str, ...] = ()

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CortexRunLedgerAppliedRules":
        return cls(
            decision_rule_ids=_ordered_unique_strings(payload.get("decision_rule_ids"), field_name="decision_rule_ids"),
            plan_rule_ids=_ordered_unique_strings(payload.get("plan_rule_ids"), field_name="plan_rule_ids"),
            rule_ids=_ordered_unique_strings(payload.get("rule_ids"), field_name="rule_ids"),
            pattern_ids=_ordered_unique_strings(payload.get("pattern_ids"), field_name="pattern_ids"),
            failure_mode_ids=_ordered_unique_strings(payload.get("failure_mode_ids"), field_name="failure_mode_ids"),
            why_selected=_ordered_unique_strings(payload.get("why_selected"), field_name="why_selected"),
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "decision_rule_ids": list(self.decision_rule_ids),
            "plan_rule_ids": list(self.plan_rule_ids),
            "rule_ids": list(self.rule_ids),
            "pattern_ids": list(self.pattern_ids),
            "failure_mode_ids": list(self.failure_mode_ids),
            "why_selected": list(self.why_selected),
        }


@dataclass(frozen=True)
class CortexRunLedgerEntry:
    run_id: str
    run_path: str
    sort_key: tuple[int, int, str]
    selected_next_action: str
    owner_layer: str
    next_required_layer: str | None
    receipt_ready: bool
    proof_status: str
    known_ambient_debt: tuple[str, ...] = ()
    current_validation_debt: tuple[str, ...] = ()
    applied_rules: CortexRunLedgerAppliedRules = field(default_factory=CortexRunLedgerAppliedRules)
    failure_modes_avoided: tuple[str, ...] = ()
    blocked_reason: str | None = None
    failed_commands: tuple[str, ...] = ()
    boundary_statement: str | None = None
    receipt_next_action: str | None = None

    def to_summary(self) -> "CortexRunLedgerSummary":
        return CortexRunLedgerSummary(
            latest_run_id=self.run_id,
            latest_run_path=self.run_path,
            selected_next_action=self.selected_next_action,
            owner_layer=self.owner_layer,
            next_required_layer=self.next_required_layer,
            receipt_ready=self.receipt_ready,
            proof_status=self.proof_status,
            known_ambient_debt=self.known_ambient_debt,
            current_validation_debt=self.current_validation_debt,
            applied_rules=self.applied_rules,
            failure_modes_avoided=self.failure_modes_avoided,
            blocked_reason=self.blocked_reason,
        )


@dataclass(frozen=True)
class CortexRunLedgerSummary:
    latest_run_id: str
    latest_run_path: str
    selected_next_action: str
    owner_layer: str
    next_required_layer: str | None
    receipt_ready: bool
    proof_status: str
    known_ambient_debt: tuple[str, ...] = ()
    current_validation_debt: tuple[str, ...] = ()
    applied_rules: CortexRunLedgerAppliedRules = field(default_factory=CortexRunLedgerAppliedRules)
    failure_modes_avoided: tuple[str, ...] = ()
    blocked_reason: str | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "latest_run_id": self.latest_run_id,
            "latest_run_path": self.latest_run_path,
            "selected_next_action": self.selected_next_action,
            "owner_layer": self.owner_layer,
            "next_required_layer": self.next_required_layer,
            "receipt_ready": self.receipt_ready,
            "proof_status": self.proof_status,
            "known_ambient_debt": list(self.known_ambient_debt),
            "current_validation_debt": list(self.current_validation_debt),
            "applied_rules": self.applied_rules.to_payload(),
            "failure_modes_avoided": list(self.failure_modes_avoided),
            "blocked_reason": self.blocked_reason,
        }


@dataclass(frozen=True)
class CortexRunLedger:
    runs_root: Path
    entries: tuple[CortexRunLedgerEntry, ...]

    def latest(self) -> CortexRunLedgerEntry | None:
        return self.entries[0] if self.entries else None


def _derive_run_id(payload: dict[str, Any], path: Path) -> str:
    explicit = payload.get("run_id")
    if explicit is not None:
        return _require_non_empty_string(explicit, "run_id")
    return _require_non_empty_string(path.name.removesuffix(path.suffix), "run_id")


def _derive_artifact_proof_status(
    *,
    receipt_ready: bool,
    failed_commands: tuple[str, ...],
    current_validation_debt: tuple[str, ...],
    known_ambient_debt: tuple[str, ...],
) -> str:
    if failed_commands:
        return "failed"
    if current_validation_debt:
        return "completed_with_changed_debt"
    if known_ambient_debt and not receipt_ready:
        return "completed_with_known_debt"
    if receipt_ready:
        return "passed"
    return "blocked"


def _blocked_reason(
    *,
    receipt_ready: bool,
    failed_commands: tuple[str, ...],
    current_validation_debt: tuple[str, ...],
    known_ambient_debt: tuple[str, ...],
    boundary_statement: str | None,
    receipt_next_action: str | None,
    proof_status: str,
) -> str | None:
    if receipt_ready:
        return None
    if failed_commands:
        return failed_commands[0]
    if current_validation_debt:
        return current_validation_debt[0]
    if boundary_statement:
        return boundary_statement
    if known_ambient_debt:
        return known_ambient_debt[0]
    if receipt_next_action:
        return receipt_next_action
    return f"Cortex run is blocked with proof status {proof_status}."


def _artifact_sort_key(path: Path, *, root: Path) -> tuple[int, int, str]:
    normalized_path = atlas_relative(path, root=root)
    latest_marker = 1 if "latest" in path.name.lower() else 0
    return (latest_marker, path.stat().st_mtime_ns, normalized_path)


def _coerce_proof_summary(value: CortexProofSummary | dict[str, Any] | None) -> CortexProofSummary | None:
    if value is None:
        return None
    if isinstance(value, CortexProofSummary):
        return value
    if isinstance(value, dict):
        return CortexProofSummary.from_payload(value)
    raise ValueError("Expected CortexProofSummary, payload dictionary, or null for proof_summary.")


def _load_run_entry(path: Path, *, root: Path) -> CortexRunLedgerEntry:
    payload = read_json(path)
    if payload.get("contract_version") != CORTEX_RUN_RESULT_CONTRACT_VERSION:
        raise ValueError(
            f"Malformed Cortex run artifact at {normalize_slashes(str(path.resolve()))}: "
            f"expected contract_version {CORTEX_RUN_RESULT_CONTRACT_VERSION}."
        )

    selected_next_action = _require_object(payload.get("selected_next_action"), "selected_next_action")
    selected_next_action_id = _require_non_empty_string(
        selected_next_action.get("action_id"),
        "selected_next_action.action_id",
    )
    owner_layer = _require_non_empty_string(
        selected_next_action.get("owner_layer"),
        "selected_next_action.owner_layer",
    )

    proof_receipt_draft = _require_object(payload.get("proof_receipt_draft"), "proof_receipt_draft")
    known_debt = _require_object(proof_receipt_draft.get("known_debt"), "proof_receipt_draft.known_debt")
    applied_rule_trace_payload = _require_object(payload.get("applied_rule_trace"), "applied_rule_trace")
    applied_rules = CortexRunLedgerAppliedRules.from_payload(applied_rule_trace_payload)
    trace_action_id = _require_non_empty_string(
        applied_rule_trace_payload.get("selected_next_action_id"),
        "applied_rule_trace.selected_next_action_id",
    )
    trace_owner_layer = _require_non_empty_string(
        applied_rule_trace_payload.get("selected_owner_layer"),
        "applied_rule_trace.selected_owner_layer",
    )
    if trace_action_id != selected_next_action_id:
        raise ValueError(
            f"Malformed Cortex run artifact at {normalize_slashes(str(path.resolve()))}: "
            "selected_next_action.action_id does not match applied_rule_trace.selected_next_action_id."
        )
    if trace_owner_layer != owner_layer:
        raise ValueError(
            f"Malformed Cortex run artifact at {normalize_slashes(str(path.resolve()))}: "
            "selected_next_action.owner_layer does not match applied_rule_trace.selected_owner_layer."
        )

    run_id = _derive_run_id(payload, path)
    run_path = atlas_relative(path, root=root)
    receipt_ready = _require_bool(payload.get("receipt_ready"), "receipt_ready")
    next_required_layer = _optional_string(payload.get("next_required_layer"), "next_required_layer")
    known_ambient_debt = _ordered_unique_strings(payload.get("known_ambient_debt"), field_name="known_ambient_debt")
    current_validation_debt = _ordered_unique_strings(
        known_debt.get("current_validation_debt"),
        field_name="proof_receipt_draft.known_debt.current_validation_debt",
    )
    failure_modes_avoided = _ordered_unique_strings(
        payload.get("failure_modes_avoided"),
        field_name="failure_modes_avoided",
    )
    failed_commands = _ordered_unique_strings(
        proof_receipt_draft.get("failed_commands"),
        field_name="proof_receipt_draft.failed_commands",
    )
    boundary_statement = _optional_string(
        proof_receipt_draft.get("boundary_statement"),
        "proof_receipt_draft.boundary_statement",
    )
    receipt_next_action = _optional_string(
        proof_receipt_draft.get("next_action"),
        "proof_receipt_draft.next_action",
    )
    proof_status = _derive_artifact_proof_status(
        receipt_ready=receipt_ready,
        failed_commands=failed_commands,
        current_validation_debt=current_validation_debt,
        known_ambient_debt=known_ambient_debt,
    )
    blocked_reason = _blocked_reason(
        receipt_ready=receipt_ready,
        failed_commands=failed_commands,
        current_validation_debt=current_validation_debt,
        known_ambient_debt=known_ambient_debt,
        boundary_statement=boundary_statement,
        receipt_next_action=receipt_next_action,
        proof_status=proof_status,
    )

    return CortexRunLedgerEntry(
        run_id=run_id,
        run_path=run_path,
        sort_key=_artifact_sort_key(path, root=root),
        selected_next_action=selected_next_action_id,
        owner_layer=owner_layer,
        next_required_layer=next_required_layer,
        receipt_ready=receipt_ready,
        proof_status=proof_status,
        known_ambient_debt=known_ambient_debt,
        current_validation_debt=current_validation_debt,
        applied_rules=applied_rules,
        failure_modes_avoided=failure_modes_avoided,
        blocked_reason=blocked_reason,
        failed_commands=failed_commands,
        boundary_statement=boundary_statement,
        receipt_next_action=receipt_next_action,
    )


def load_cortex_run_ledger(
    *,
    root: Path | None = None,
    runs_root: Path | None = None,
) -> CortexRunLedger:
    base = (root or atlas_root()).resolve()
    resolved_runs_root = (runs_root or default_run_ledger_dir(base)).resolve()
    paths = iter_candidate_json_paths([resolved_runs_root]) if resolved_runs_root.exists() else []
    entries = tuple(sorted((_load_run_entry(path, root=base) for path in paths), key=lambda item: item.sort_key, reverse=True))
    return CortexRunLedger(runs_root=resolved_runs_root, entries=entries)


def summarize_run_ledger(
    *,
    root: Path | None = None,
    runs_root: Path | None = None,
    proof_summary: CortexProofSummary | dict[str, Any] | None = None,
    verification_ingest: VerificationIngestResult | None = None,
) -> CortexRunLedgerSummary:
    base = (root or atlas_root()).resolve()
    ledger = load_cortex_run_ledger(root=base, runs_root=runs_root)
    latest = ledger.latest()
    if latest is None:
        raise FileNotFoundError(f"No Cortex run artifacts found under {normalize_slashes(str(ledger.runs_root))}.")

    resolved_proof_summary = _coerce_proof_summary(proof_summary)
    if verification_ingest is not None and not isinstance(verification_ingest, VerificationIngestResult):
        raise ValueError("Expected VerificationIngestResult or null for verification_ingest.")

    receipt_ready = latest.receipt_ready
    proof_status = latest.proof_status
    next_required_layer = latest.next_required_layer
    known_ambient_debt = latest.known_ambient_debt
    current_validation_debt = latest.current_validation_debt
    failed_commands = latest.failed_commands
    boundary_statement = latest.boundary_statement
    receipt_next_action = latest.receipt_next_action

    if resolved_proof_summary is not None:
        proof_status = resolved_proof_summary.verification.status
        receipt_ready = resolved_proof_summary.receipt_ready
        next_required_layer = resolved_proof_summary.next_required_layer or next_required_layer
        failed_commands = resolved_proof_summary.verification.failed or failed_commands
        if resolved_proof_summary.verification.known_debt:
            if resolved_proof_summary.verification.status == "completed_with_known_debt":
                known_ambient_debt = _merge_ordered_strings(
                    known_ambient_debt,
                    resolved_proof_summary.verification.known_debt,
                )
            elif resolved_proof_summary.verification.status == "completed_with_changed_debt":
                current_validation_debt = _merge_ordered_strings(
                    current_validation_debt,
                    resolved_proof_summary.verification.known_debt,
                )

    if verification_ingest is not None:
        proof_status = verification_ingest.proof_summary.verification.status
        receipt_ready = verification_ingest.proof_summary.receipt_ready
        next_required_layer = verification_ingest.proof_summary.next_required_layer or next_required_layer
        known_ambient_debt = _merge_ordered_strings(known_ambient_debt, verification_ingest.ambient_debt)
        current_validation_debt = _merge_ordered_strings(
            current_validation_debt,
            verification_ingest.current_validation_debt,
        )
        failed_commands = verification_ingest.proof_summary.verification.failed or failed_commands

    blocked_reason = _blocked_reason(
        receipt_ready=receipt_ready,
        failed_commands=failed_commands,
        current_validation_debt=current_validation_debt,
        known_ambient_debt=known_ambient_debt,
        boundary_statement=boundary_statement,
        receipt_next_action=receipt_next_action,
        proof_status=proof_status,
    )

    return CortexRunLedgerSummary(
        latest_run_id=latest.run_id,
        latest_run_path=latest.run_path,
        selected_next_action=latest.selected_next_action,
        owner_layer=latest.owner_layer,
        next_required_layer=next_required_layer,
        receipt_ready=receipt_ready,
        proof_status=proof_status,
        known_ambient_debt=known_ambient_debt,
        current_validation_debt=current_validation_debt,
        applied_rules=latest.applied_rules,
        failure_modes_avoided=latest.failure_modes_avoided,
        blocked_reason=blocked_reason,
    )
