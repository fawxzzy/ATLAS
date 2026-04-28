from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ops._atlas import normalize_slashes
from ops.cortex.kernel import CortexProofSummary

VALID_BOUNDARY_STATUSES = {"clean", "dirty", "unknown"}


def _ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = " ".join(str(value).strip().split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _normalize_paths(values: Iterable[str]) -> tuple[str, ...]:
    return _ordered_unique(normalize_slashes(str(value)) for value in values)


def _require_non_empty(value: str, field_name: str) -> str:
    stripped = " ".join(str(value).strip().split())
    if not stripped:
        raise ValueError(f"Expected non-empty string for {field_name}.")
    return stripped


def _validate_owner_match(expected: str, actual: str, field_name: str) -> None:
    if expected != actual:
        raise ValueError(f"{field_name} does not match CortexProofSummary.{field_name}.")


@dataclass(frozen=True)
class ProofReceiptKnownDebtSummary:
    ambient_debt: tuple[str, ...] = ()
    current_validation_debt: tuple[str, ...] = ()
    owner_boundary_status: str = "unknown"
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        owner_boundary_status = _require_non_empty(self.owner_boundary_status, "owner_boundary_status")
        if owner_boundary_status not in VALID_BOUNDARY_STATUSES:
            raise ValueError(f"Unsupported owner_boundary_status: {owner_boundary_status}")
        object.__setattr__(self, "ambient_debt", _ordered_unique(self.ambient_debt))
        object.__setattr__(self, "current_validation_debt", _ordered_unique(self.current_validation_debt))
        object.__setattr__(self, "owner_boundary_status", owner_boundary_status)
        object.__setattr__(self, "notes", _ordered_unique(self.notes))

    def to_payload(self) -> dict[str, object]:
        return {
            "ambient_debt": list(self.ambient_debt),
            "current_validation_debt": list(self.current_validation_debt),
            "owner_boundary_status": self.owner_boundary_status,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ProofReceiptDraftInput:
    proof_summary: CortexProofSummary
    touched_files: tuple[str, ...]
    owner_layer: str
    next_required_layer: str | None
    known_debt_summary: ProofReceiptKnownDebtSummary

    def __post_init__(self) -> None:
        object.__setattr__(self, "touched_files", _normalize_paths(self.touched_files))
        object.__setattr__(self, "owner_layer", _require_non_empty(self.owner_layer, "owner_layer"))
        if self.next_required_layer is not None:
            object.__setattr__(
                self,
                "next_required_layer",
                _require_non_empty(self.next_required_layer, "next_required_layer"),
            )


@dataclass(frozen=True)
class ProofReceiptDraft:
    receipt_title: str
    owner_layer: str
    next_required_layer: str | None
    touched_files: tuple[str, ...]
    passed_commands: tuple[str, ...]
    failed_commands: tuple[str, ...]
    known_debt: ProofReceiptKnownDebtSummary
    boundary_statement: str
    next_action: str
    receipt_ready: bool

    def to_payload(self) -> dict[str, object]:
        return {
            "receipt_title": self.receipt_title,
            "owner_layer": self.owner_layer,
            "next_required_layer": self.next_required_layer,
            "touched_files": list(self.touched_files),
            "passed_commands": list(self.passed_commands),
            "failed_commands": list(self.failed_commands),
            "known_debt": self.known_debt.to_payload(),
            "boundary_statement": self.boundary_statement,
            "next_action": self.next_action,
            "receipt_ready": self.receipt_ready,
        }


class ProofReceiptDraftBuilder:
    def build(self, request: ProofReceiptDraftInput) -> ProofReceiptDraft:
        _validate_owner_match(request.proof_summary.owner_layer, request.owner_layer, "owner_layer")
        _validate_owner_match(
            "" if request.proof_summary.next_required_layer is None else request.proof_summary.next_required_layer,
            "" if request.next_required_layer is None else request.next_required_layer,
            "next_required_layer",
        )

        passed_commands = _ordered_unique(request.proof_summary.verification.passed)
        failed_commands = _ordered_unique(request.proof_summary.verification.failed)
        ambient_debt = _ordered_unique(request.known_debt_summary.ambient_debt)
        explicit_current_debt = _ordered_unique(request.known_debt_summary.current_validation_debt)
        observed_known_debt = _ordered_unique(request.proof_summary.verification.known_debt)

        ambient_lookup = set(ambient_debt)
        derived_current_debt = explicit_current_debt + tuple(item for item in observed_known_debt if item not in ambient_lookup)
        current_validation_debt = _ordered_unique(item for item in derived_current_debt if item not in ambient_lookup)

        known_debt = ProofReceiptKnownDebtSummary(
            ambient_debt=ambient_debt,
            current_validation_debt=current_validation_debt,
            owner_boundary_status=request.known_debt_summary.owner_boundary_status,
            notes=request.known_debt_summary.notes,
        )
        boundary_clean = known_debt.owner_boundary_status == "clean"
        has_current_failure = bool(failed_commands)
        has_new_validation_debt = bool(known_debt.current_validation_debt)
        has_ambient_debt = bool(known_debt.ambient_debt)
        receipt_ready = (
            bool(request.proof_summary.receipt_ready)
            and not has_current_failure
            and not has_new_validation_debt
            and not has_ambient_debt
            and boundary_clean
        )

        boundary_statement = self._boundary_statement(
            owner_layer=request.owner_layer,
            next_required_layer=request.next_required_layer,
            boundary_status=known_debt.owner_boundary_status,
            has_current_failure=has_current_failure,
            has_ambient_debt=has_ambient_debt,
            has_new_validation_debt=has_new_validation_debt,
        )
        next_action = self._next_action(
            owner_layer=request.owner_layer,
            next_required_layer=request.next_required_layer,
            receipt_ready=receipt_ready,
            has_current_failure=has_current_failure,
            has_ambient_debt=has_ambient_debt,
            has_new_validation_debt=has_new_validation_debt,
            boundary_status=known_debt.owner_boundary_status,
        )

        receipt_title = f"{request.owner_layer.title()} proof receipt draft: {request.proof_summary.proof_id}"
        return ProofReceiptDraft(
            receipt_title=receipt_title,
            owner_layer=request.owner_layer,
            next_required_layer=request.next_required_layer,
            touched_files=request.touched_files,
            passed_commands=passed_commands,
            failed_commands=failed_commands,
            known_debt=known_debt,
            boundary_statement=boundary_statement,
            next_action=next_action,
            receipt_ready=receipt_ready,
        )

    @staticmethod
    def _boundary_statement(
        *,
        owner_layer: str,
        next_required_layer: str | None,
        boundary_status: str,
        has_current_failure: bool,
        has_ambient_debt: bool,
        has_new_validation_debt: bool,
    ) -> str:
        target_layer = next_required_layer or "the next required layer"
        if has_current_failure:
            return f"{owner_layer} boundary is blocked by a current-tranche command failure before {target_layer}."
        if has_new_validation_debt:
            return f"{owner_layer} boundary has new validation debt that is separate from the ambient baseline."
        if has_ambient_debt:
            return f"{owner_layer} boundary has known ambient debt only; no current-tranche regression was introduced."
        if boundary_status == "clean":
            return f"{owner_layer} boundary is clean for {target_layer}."
        if boundary_status == "dirty":
            return f"{owner_layer} boundary is dirty for {target_layer}."
        return f"{owner_layer} boundary status is unknown for {target_layer}."

    @staticmethod
    def _next_action(
        *,
        owner_layer: str,
        next_required_layer: str | None,
        receipt_ready: bool,
        has_current_failure: bool,
        has_ambient_debt: bool,
        has_new_validation_debt: bool,
        boundary_status: str,
    ) -> str:
        target_layer = next_required_layer or "the next required layer"
        if receipt_ready:
            return f"Promote this draft into the {target_layer} receipt handoff."
        if has_current_failure:
            return "Fix the current-tranche command failure before drafting a receipt."
        if has_new_validation_debt:
            return "Classify and resolve the new validation debt before drafting a receipt."
        if has_ambient_debt:
            return "Keep the ambient debt on the ledger and do not mark this tranche receipt-ready yet."
        if boundary_status != "clean":
            return f"Restore the {owner_layer} boundary to clean before drafting a receipt."
        return f"Review the {target_layer} boundary before drafting a receipt."


def build_proof_receipt_draft(request: ProofReceiptDraftInput) -> ProofReceiptDraft:
    return ProofReceiptDraftBuilder().build(request)
