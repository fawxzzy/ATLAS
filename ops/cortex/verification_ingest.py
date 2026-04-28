from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from ops._atlas import normalize_slashes
from ops.cortex._artifacts import stable_json_digest
from ops.cortex.kernel import CortexProofSummary, VerificationResult
from ops.cortex.proof_receipt import ProofReceiptKnownDebtSummary

STACK_VALIDATION_COMMAND_TOKEN = "validate_stack.py"


def _ordered_unique_strings(values: Iterable[str]) -> tuple[str, ...]:
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
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = normalize_slashes(str(value).strip())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


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


def _require_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Expected integer for {field_name}.")
    return value


def _bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"Expected boolean for {field_name}.")
    return value


def _optional_string_list(value: Any, field_name: str, *, normalize_paths: bool = False) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"Expected list for {field_name}.")
    normalized = _normalize_paths(value) if normalize_paths else _ordered_unique_strings(value)
    if len(normalized) != len({item for item in normalized}):
        raise ValueError(f"Expected unique string entries for {field_name}.")
    return normalized


@dataclass(frozen=True)
class VerificationDebtCounts:
    critical: int = 0
    error: int = 0
    warning: int = 0

    def __post_init__(self) -> None:
        for field_name in ("critical", "error", "warning"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"Expected non-negative integer for debt.{field_name}.")

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, field_name: str) -> "VerificationDebtCounts":
        if not isinstance(payload, dict):
            raise ValueError(f"Expected object for {field_name}.")
        unexpected = sorted(key for key in payload.keys() if key not in {"critical", "error", "warning"})
        if unexpected:
            raise ValueError(f"Unexpected keys for {field_name}: {', '.join(unexpected)}.")
        return cls(
            critical=_require_int(payload.get("critical", 0), f"{field_name}.critical"),
            error=_require_int(payload.get("error", 0), f"{field_name}.error"),
            warning=_require_int(payload.get("warning", 0), f"{field_name}.warning"),
        )

    def to_payload(self) -> dict[str, int]:
        return {
            "critical": self.critical,
            "error": self.error,
            "warning": self.warning,
        }

    def render(self) -> str:
        return f"critical={self.critical}, error={self.error}, warning={self.warning}"


KNOWN_STACK_VALIDATION_BASELINE = VerificationDebtCounts(critical=345, error=14, warning=181)


@dataclass(frozen=True)
class VerificationOutcome:
    command: str
    exit_code: int
    owner_layer: str
    touched_files: tuple[str, ...] = ()
    stdout_summary: str | None = None
    stderr_summary: str | None = None
    expected_ambient_debt: VerificationDebtCounts | None = None
    observed_debt: VerificationDebtCounts | None = None
    current_tranche_failure: bool = False
    failures: tuple[str, ...] = ()
    next_required_layer: str | None = None
    proof_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "command", _require_non_empty_string(self.command, "command"))
        object.__setattr__(self, "exit_code", _require_int(self.exit_code, "exit_code"))
        object.__setattr__(self, "owner_layer", _require_non_empty_string(self.owner_layer, "owner_layer"))
        object.__setattr__(self, "touched_files", _normalize_paths(self.touched_files))
        object.__setattr__(self, "stdout_summary", _optional_string(self.stdout_summary, "stdout_summary"))
        object.__setattr__(self, "stderr_summary", _optional_string(self.stderr_summary, "stderr_summary"))
        object.__setattr__(self, "current_tranche_failure", _bool(self.current_tranche_failure, "current_tranche_failure"))
        object.__setattr__(self, "failures", _ordered_unique_strings(self.failures))
        if self.next_required_layer is not None:
            object.__setattr__(
                self,
                "next_required_layer",
                _require_non_empty_string(self.next_required_layer, "next_required_layer"),
            )
        if self.proof_id is not None:
            object.__setattr__(self, "proof_id", _require_non_empty_string(self.proof_id, "proof_id"))
        if self.expected_ambient_debt is not None and not isinstance(self.expected_ambient_debt, VerificationDebtCounts):
            raise ValueError("Expected VerificationDebtCounts or null for expected_ambient_debt.")
        if self.observed_debt is not None and not isinstance(self.observed_debt, VerificationDebtCounts):
            raise ValueError("Expected VerificationDebtCounts or null for observed_debt.")

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "VerificationOutcome":
        if not isinstance(payload, dict):
            raise ValueError("Expected verification outcome payload to be an object.")
        return cls(
            command=payload.get("command"),
            exit_code=payload.get("exit_code"),
            owner_layer=payload.get("owner_layer"),
            touched_files=_optional_string_list(payload.get("touched_files"), "touched_files", normalize_paths=True),
            stdout_summary=payload.get("stdout_summary"),
            stderr_summary=payload.get("stderr_summary"),
            expected_ambient_debt=(
                VerificationDebtCounts.from_payload(payload["expected_ambient_debt"], field_name="expected_ambient_debt")
                if payload.get("expected_ambient_debt") is not None
                else None
            ),
            observed_debt=(
                VerificationDebtCounts.from_payload(payload["observed_debt"], field_name="observed_debt")
                if payload.get("observed_debt") is not None
                else None
            ),
            current_tranche_failure=payload.get("current_tranche_failure", False),
            failures=_optional_string_list(payload.get("failures"), "failures"),
            next_required_layer=payload.get("next_required_layer"),
            proof_id=payload.get("proof_id"),
        )


@dataclass(frozen=True)
class VerificationIngestResult:
    classification: str
    proof_summary: CortexProofSummary
    current_tranche_failure: bool
    ambient_debt: tuple[str, ...] = ()
    current_validation_debt: tuple[str, ...] = ()
    expected_ambient_debt: VerificationDebtCounts | None = None
    observed_debt: VerificationDebtCounts | None = None

    def to_known_debt_summary(self, *, owner_boundary_status: str = "clean") -> ProofReceiptKnownDebtSummary:
        return ProofReceiptKnownDebtSummary(
            ambient_debt=self.ambient_debt,
            current_validation_debt=self.current_validation_debt,
            owner_boundary_status=owner_boundary_status,
        )


def _is_stack_validation_command(command: str) -> bool:
    return STACK_VALIDATION_COMMAND_TOKEN in normalize_slashes(command).lower()


def _default_proof_id(*, outcome: VerificationOutcome, classification: str) -> str:
    digest = stable_json_digest(
        {
            "classification": classification,
            "command": outcome.command,
            "owner_layer": outcome.owner_layer,
            "exit_code": outcome.exit_code,
            "touched_files": list(outcome.touched_files),
        }
    ).removeprefix("sha256:")
    return f"verification-{digest[:12]}"


def _targeted_pass_summary(outcome: VerificationOutcome) -> str:
    return outcome.stdout_summary or f"Targeted verification passed: {outcome.command}."


def _targeted_failure_messages(outcome: VerificationOutcome) -> tuple[str, ...]:
    if outcome.failures:
        return outcome.failures
    if outcome.stderr_summary:
        return (outcome.stderr_summary,)
    return (f"Targeted verification failed: {outcome.command} exited with code {outcome.exit_code}.",)


def _result_notes(outcome: VerificationOutcome, *extra: str) -> tuple[str, ...]:
    return _ordered_unique_strings(
        item
        for item in (
            outcome.stdout_summary,
            outcome.stderr_summary,
            *extra,
        )
        if item
    )


class VerificationIngestor:
    def __init__(self, *, stack_validation_baseline: VerificationDebtCounts = KNOWN_STACK_VALIDATION_BASELINE) -> None:
        self._stack_validation_baseline = stack_validation_baseline

    def ingest(self, outcome: VerificationOutcome | dict[str, Any]) -> VerificationIngestResult:
        resolved = VerificationOutcome.from_payload(outcome) if isinstance(outcome, dict) else outcome
        if not isinstance(resolved, VerificationOutcome):
            raise ValueError("Expected VerificationOutcome or payload dictionary.")

        if _is_stack_validation_command(resolved.command):
            return self._ingest_stack_validation(resolved)
        return self._ingest_targeted_command(resolved)

    def _ingest_targeted_command(self, outcome: VerificationOutcome) -> VerificationIngestResult:
        has_current_failure = outcome.exit_code != 0 or outcome.current_tranche_failure or bool(outcome.failures)
        classification = "targeted_failed" if has_current_failure else "targeted_passed"
        verification = VerificationResult(
            status="failed" if has_current_failure else "passed",
            passed=() if has_current_failure else (_targeted_pass_summary(outcome),),
            failed=_targeted_failure_messages(outcome) if has_current_failure else (),
            known_debt=(),
            notes=_result_notes(outcome),
        )
        proof_summary = CortexProofSummary(
            proof_id=outcome.proof_id or _default_proof_id(outcome=outcome, classification=classification),
            command=outcome.command,
            verification=verification,
            touched_files=outcome.touched_files,
            owner_layer=outcome.owner_layer,
            next_required_layer=outcome.next_required_layer,
            receipt_ready=not has_current_failure,
            evidence=(),
        )
        return VerificationIngestResult(
            classification=classification,
            proof_summary=proof_summary,
            current_tranche_failure=has_current_failure,
        )

    def _ingest_stack_validation(self, outcome: VerificationOutcome) -> VerificationIngestResult:
        if outcome.exit_code == 0 and outcome.observed_debt is not None and outcome.observed_debt != VerificationDebtCounts():
            raise ValueError("Stack validation with exit_code=0 cannot report nonzero observed_debt.")

        if outcome.exit_code == 0 and not outcome.current_tranche_failure and not outcome.failures:
            verification = VerificationResult(
                status="passed",
                passed=("Stack validation passed with no observed debt.",),
                failed=(),
                known_debt=(),
                notes=_result_notes(outcome),
            )
            proof_summary = CortexProofSummary(
                proof_id=outcome.proof_id or _default_proof_id(outcome=outcome, classification="targeted_passed"),
                command=outcome.command,
                verification=verification,
                touched_files=outcome.touched_files,
                owner_layer=outcome.owner_layer,
                next_required_layer=outcome.next_required_layer,
                receipt_ready=True,
                evidence=(),
            )
            return VerificationIngestResult(
                classification="targeted_passed",
                proof_summary=proof_summary,
                current_tranche_failure=False,
                observed_debt=outcome.observed_debt,
            )

        if outcome.observed_debt is None:
            raise ValueError("Stack validation ingestion requires observed_debt for nonzero exit codes.")

        expected_debt = outcome.expected_ambient_debt or self._stack_validation_baseline
        if outcome.observed_debt == expected_debt:
            ambient_message = f"Known ambient stack debt matches baseline: {outcome.observed_debt.render()}."
            verification = VerificationResult(
                status="completed_with_known_debt",
                passed=("Stack validation completed; ambient debt matches the expected baseline.",),
                failed=(),
                known_debt=(ambient_message,),
                notes=_result_notes(outcome),
            )
            proof_summary = CortexProofSummary(
                proof_id=outcome.proof_id or _default_proof_id(
                    outcome=outcome,
                    classification="stack_validation_known_ambient_debt",
                ),
                command=outcome.command,
                verification=verification,
                touched_files=outcome.touched_files,
                owner_layer=outcome.owner_layer,
                next_required_layer=outcome.next_required_layer,
                receipt_ready=False,
                evidence=(),
            )
            return VerificationIngestResult(
                classification="stack_validation_known_ambient_debt",
                proof_summary=proof_summary,
                current_tranche_failure=False,
                ambient_debt=(ambient_message,),
                expected_ambient_debt=expected_debt,
                observed_debt=outcome.observed_debt,
            )

        changed_message = (
            "Stack validation debt changed from baseline: "
            f"expected {expected_debt.render()}; observed {outcome.observed_debt.render()}."
        )
        verification = VerificationResult(
            status="completed_with_changed_debt",
            passed=("Stack validation completed; observed debt differs from the expected baseline.",),
            failed=(),
            known_debt=(changed_message,),
            notes=_result_notes(outcome),
        )
        proof_summary = CortexProofSummary(
            proof_id=outcome.proof_id or _default_proof_id(
                outcome=outcome,
                classification="stack_validation_changed_debt",
            ),
            command=outcome.command,
            verification=verification,
            touched_files=outcome.touched_files,
            owner_layer=outcome.owner_layer,
            next_required_layer=outcome.next_required_layer,
            receipt_ready=False,
            evidence=(),
        )
        return VerificationIngestResult(
            classification="stack_validation_changed_debt",
            proof_summary=proof_summary,
            current_tranche_failure=False,
            current_validation_debt=(changed_message,),
            expected_ambient_debt=expected_debt,
            observed_debt=outcome.observed_debt,
        )


def ingest_verification_outcome(outcome: VerificationOutcome | dict[str, Any]) -> VerificationIngestResult:
    return VerificationIngestor().ingest(outcome)
