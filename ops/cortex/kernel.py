from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ops._atlas import atlas_root
from ops.cortex._artifacts import read_json

KERNEL_STATE_CONTRACT_VERSION = "atlas.cortex.kernel-state.v1"
RULE_REGISTRY_CONTRACT_VERSION = "atlas.cortex.rule-registry.v1"
PROOF_SUMMARY_EXAMPLES_CONTRACT_VERSION = "atlas.cortex.proof-summary.examples.v1"
RULE_KINDS = {"rule", "pattern", "failure_mode"}


def runtime_cortex_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex"


def default_state_model_path(root: Path | None = None) -> Path:
    return runtime_cortex_root(root) / "kernel.state-model.seed.v1.json"


def default_rule_registry_path(root: Path | None = None) -> Path:
    return runtime_cortex_root(root) / "kernel.rule-registry.seed.v1.json"


def default_proof_summary_examples_path(root: Path | None = None) -> Path:
    return runtime_cortex_root(root) / "kernel.proof-summary.examples.v1.json"


def _required_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Expected non-empty string for {field}.")
    return value.strip()


def _optional_string(payload: dict[str, Any], field: str) -> str | None:
    value = payload.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Expected string or null for {field}.")
    stripped = value.strip()
    return stripped or None


def _string_list(payload: dict[str, Any], field: str) -> tuple[str, ...]:
    value = payload.get(field, [])
    if not isinstance(value, list):
        raise ValueError(f"Expected list for {field}.")
    ordered: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"Expected string entries in {field}.")
        stripped = item.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        ordered.append(stripped)
    return tuple(ordered)


def _dict(payload: dict[str, Any], field: str) -> dict[str, Any]:
    value = payload.get(field)
    if not isinstance(value, dict):
        raise ValueError(f"Expected object for {field}.")
    return value


@dataclass(frozen=True)
class CleanStep:
    step_id: str
    owner_layer: str
    summary: str
    status: str = "clean"
    evidence: tuple[str, ...] = ()
    source_inputs: tuple[str, ...] = ()
    completed_at: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CleanStep":
        return cls(
            step_id=_required_string(payload, "step_id"),
            owner_layer=_required_string(payload, "owner_layer"),
            summary=_required_string(payload, "summary"),
            status=_required_string(payload, "status"),
            evidence=_string_list(payload, "evidence"),
            source_inputs=_string_list(payload, "source_inputs"),
            completed_at=_optional_string(payload, "completed_at"),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "owner_layer": self.owner_layer,
            "summary": self.summary,
            "status": self.status,
            "evidence": list(self.evidence),
            "source_inputs": list(self.source_inputs),
            "completed_at": self.completed_at,
        }


@dataclass(frozen=True)
class DirtyLane:
    lane_id: str
    owner_layer: str
    summary: str
    status: str
    blocking_reason: str
    evidence: tuple[str, ...] = ()
    source_inputs: tuple[str, ...] = ()

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "DirtyLane":
        return cls(
            lane_id=_required_string(payload, "lane_id"),
            owner_layer=_required_string(payload, "owner_layer"),
            summary=_required_string(payload, "summary"),
            status=_required_string(payload, "status"),
            blocking_reason=_required_string(payload, "blocking_reason"),
            evidence=_string_list(payload, "evidence"),
            source_inputs=_string_list(payload, "source_inputs"),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "lane_id": self.lane_id,
            "owner_layer": self.owner_layer,
            "summary": self.summary,
            "status": self.status,
            "blocking_reason": self.blocking_reason,
            "evidence": list(self.evidence),
            "source_inputs": list(self.source_inputs),
        }


@dataclass(frozen=True)
class VerificationResult:
    status: str
    passed: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()
    known_debt: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "VerificationResult":
        return cls(
            status=_required_string(payload, "status"),
            passed=_string_list(payload, "passed"),
            failed=_string_list(payload, "failed"),
            known_debt=_string_list(payload, "known_debt"),
            notes=_string_list(payload, "notes"),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": list(self.passed),
            "failed": list(self.failed),
            "known_debt": list(self.known_debt),
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class NextAction:
    action_id: str
    owner_layer: str
    title: str
    rationale: str
    required_inputs: tuple[str, ...] = ()
    verification_plan: tuple[str, ...] = ()
    receipt_scope: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "NextAction":
        return cls(
            action_id=_required_string(payload, "action_id"),
            owner_layer=_required_string(payload, "owner_layer"),
            title=_required_string(payload, "title"),
            rationale=_required_string(payload, "rationale"),
            required_inputs=_string_list(payload, "required_inputs"),
            verification_plan=_string_list(payload, "verification_plan"),
            receipt_scope=_optional_string(payload, "receipt_scope"),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "owner_layer": self.owner_layer,
            "title": self.title,
            "rationale": self.rationale,
            "required_inputs": list(self.required_inputs),
            "verification_plan": list(self.verification_plan),
            "receipt_scope": self.receipt_scope,
        }


@dataclass(frozen=True)
class RailState:
    rail_id: str
    owner_layer: str
    latest_clean_step: CleanStep
    dirty_lanes: tuple[DirtyLane, ...]
    verification: tuple[VerificationResult, ...]
    next_action: NextAction
    boundary_reminders: tuple[str, ...] = ()

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "RailState":
        dirty_lanes = payload.get("dirty_lanes", [])
        verification = payload.get("verification", [])
        if not isinstance(dirty_lanes, list):
            raise ValueError("Expected list for dirty_lanes.")
        if not isinstance(verification, list):
            raise ValueError("Expected list for verification.")
        return cls(
            rail_id=_required_string(payload, "rail_id"),
            owner_layer=_required_string(payload, "owner_layer"),
            latest_clean_step=CleanStep.from_payload(_dict(payload, "latest_clean_step")),
            dirty_lanes=tuple(DirtyLane.from_payload(item) for item in dirty_lanes if isinstance(item, dict)),
            verification=tuple(VerificationResult.from_payload(item) for item in verification if isinstance(item, dict)),
            next_action=NextAction.from_payload(_dict(payload, "next_action")),
            boundary_reminders=_string_list(payload, "boundary_reminders"),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "rail_id": self.rail_id,
            "owner_layer": self.owner_layer,
            "latest_clean_step": self.latest_clean_step.to_payload(),
            "dirty_lanes": [item.to_payload() for item in self.dirty_lanes],
            "verification": [item.to_payload() for item in self.verification],
            "next_action": self.next_action.to_payload(),
            "boundary_reminders": list(self.boundary_reminders),
        }


@dataclass(frozen=True)
class CortexPosture:
    posture_id: str
    classification: str
    summary: str
    handoff_summaries: tuple[str, ...]
    git_status_summaries: tuple[str, ...]
    verification_summaries: tuple[str, ...]
    stack_validation_summaries: tuple[str, ...]
    rail_state: RailState
    boundary_reminders: tuple[str, ...] = ()

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CortexPosture":
        return cls(
            posture_id=_required_string(payload, "posture_id"),
            classification=_required_string(payload, "classification"),
            summary=_required_string(payload, "summary"),
            handoff_summaries=_string_list(payload, "handoff_summaries"),
            git_status_summaries=_string_list(payload, "git_status_summaries"),
            verification_summaries=_string_list(payload, "verification_summaries"),
            stack_validation_summaries=_string_list(payload, "stack_validation_summaries"),
            rail_state=RailState.from_payload(_dict(payload, "rail_state")),
            boundary_reminders=_string_list(payload, "boundary_reminders"),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "posture_id": self.posture_id,
            "classification": self.classification,
            "summary": self.summary,
            "handoff_summaries": list(self.handoff_summaries),
            "git_status_summaries": list(self.git_status_summaries),
            "verification_summaries": list(self.verification_summaries),
            "stack_validation_summaries": list(self.stack_validation_summaries),
            "rail_state": self.rail_state.to_payload(),
            "boundary_reminders": list(self.boundary_reminders),
        }


@dataclass(frozen=True)
class CortexRuleRecord:
    rule_id: str
    kind: str
    statement: str
    applies_to: tuple[str, ...]
    evidence: tuple[str, ...]
    next_action_hint: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CortexRuleRecord":
        kind = _required_string(payload, "kind")
        if kind not in RULE_KINDS:
            raise ValueError(f"Unsupported rule kind: {kind}")
        return cls(
            rule_id=_required_string(payload, "id"),
            kind=kind,
            statement=_required_string(payload, "statement"),
            applies_to=_string_list(payload, "applies_to"),
            evidence=_string_list(payload, "evidence"),
            next_action_hint=_required_string(payload, "next_action_hint"),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.rule_id,
            "kind": self.kind,
            "statement": self.statement,
            "applies_to": list(self.applies_to),
            "evidence": list(self.evidence),
            "next_action_hint": self.next_action_hint,
        }


@dataclass(frozen=True)
class CortexProofSummary:
    proof_id: str
    command: str
    verification: VerificationResult
    touched_files: tuple[str, ...]
    owner_layer: str
    next_required_layer: str | None
    receipt_ready: bool
    evidence: tuple[str, ...] = ()

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CortexProofSummary":
        receipt_ready = payload.get("receipt_ready")
        if not isinstance(receipt_ready, bool):
            raise ValueError("Expected boolean for receipt_ready.")
        verification = VerificationResult.from_payload(payload)
        return cls(
            proof_id=_required_string(payload, "proof_id"),
            command=_required_string(payload, "command"),
            verification=verification,
            touched_files=_string_list(payload, "touched_files"),
            owner_layer=_required_string(payload, "owner_layer"),
            next_required_layer=_optional_string(payload, "next_required_layer"),
            receipt_ready=receipt_ready,
            evidence=_string_list(payload, "evidence"),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "proof_id": self.proof_id,
            "command": self.command,
            **self.verification.to_payload(),
            "touched_files": list(self.touched_files),
            "owner_layer": self.owner_layer,
            "next_required_layer": self.next_required_layer,
            "receipt_ready": self.receipt_ready,
            "evidence": list(self.evidence),
        }


def load_kernel_state_model(
    path: Path | None = None,
    *,
    root: Path | None = None,
) -> CortexPosture:
    payload = read_json(path or default_state_model_path(root))
    if payload.get("contract_version") != KERNEL_STATE_CONTRACT_VERSION:
        raise ValueError("Unexpected Cortex kernel state contract version.")
    return CortexPosture.from_payload(_dict(payload, "posture"))


def load_rule_registry(
    path: Path | None = None,
    *,
    root: Path | None = None,
) -> list[CortexRuleRecord]:
    payload = read_json(path or default_rule_registry_path(root))
    if payload.get("contract_version") != RULE_REGISTRY_CONTRACT_VERSION:
        raise ValueError("Unexpected Cortex rule registry contract version.")
    rules = payload.get("rules", [])
    if not isinstance(rules, list):
        raise ValueError("Expected list for rules.")
    result = [CortexRuleRecord.from_payload(item) for item in rules if isinstance(item, dict)]
    if len({item.rule_id for item in result}) != len(result):
        raise ValueError("Duplicate Cortex rule ids are not allowed.")
    return result


def load_proof_summary_examples(
    path: Path | None = None,
    *,
    root: Path | None = None,
) -> list[CortexProofSummary]:
    payload = read_json(path or default_proof_summary_examples_path(root))
    if payload.get("contract_version") != PROOF_SUMMARY_EXAMPLES_CONTRACT_VERSION:
        raise ValueError("Unexpected Cortex proof summary examples contract version.")
    examples = payload.get("examples", [])
    if not isinstance(examples, list):
        raise ValueError("Expected list for examples.")
    result = [CortexProofSummary.from_payload(item) for item in examples if isinstance(item, dict)]
    if len({item.proof_id for item in result}) != len(result):
        raise ValueError("Duplicate Cortex proof example ids are not allowed.")
    return result
