from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REQUIRED_PROTECTED_SURFACE_EXCLUSIONS = (
    "deploy",
    "publication",
    "archive_delete",
    "env_mutation",
    "secret_mutation",
)
ALLOWED_TARGET_KINDS = {"worktree", "branch"}
PROTECTED_SCOPE_TOKENS = (
    "deploy",
    "publish",
    "publication",
    "archive/delete",
    ".env",
    "secret",
)


def _normalized_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _normalized_exclusions(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _normalized_text(item).lower()
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized


def _objective_is_bounded(value: str) -> bool:
    return bool(value) and "\n" not in value and "\r" not in value


def _scope_has_protected_violation(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in PROTECTED_SCOPE_TOKENS)


def evaluate_pilot_selection_criteria(card: Mapping[str, Any]) -> dict[str, Any]:
    owner_repo_count = card.get("owner_repo_count")
    target_kind = _normalized_text(card.get("target_kind")).lower()
    target_ref = _normalized_text(card.get("target_ref"))
    objective_summary = _normalized_text(card.get("objective_summary"))
    allowed_write_scope = _normalized_text(card.get("allowed_write_scope"))
    checkpoint_surface = _normalized_text(card.get("checkpoint_surface"))
    verification_gate = _normalized_text(card.get("verification_gate"))
    closeout_artifact = _normalized_text(card.get("closeout_artifact"))
    park_or_escalation_rule = _normalized_text(card.get("park_or_escalation_rule"))
    protected_surface_exclusions = _normalized_exclusions(card.get("protected_surface_exclusions"))

    rejection_reasons: list[str] = []

    if not isinstance(owner_repo_count, int) or isinstance(owner_repo_count, bool) or owner_repo_count != 1:
        rejection_reasons.append("owner_repo_count_not_one")

    if target_kind not in ALLOWED_TARGET_KINDS or not target_ref:
        rejection_reasons.append("target_not_explicit")

    if not _objective_is_bounded(objective_summary):
        rejection_reasons.append("objective_not_bounded")

    if not allowed_write_scope:
        rejection_reasons.append("allowed_write_scope_missing")

    if not checkpoint_surface:
        rejection_reasons.append("checkpoint_surface_missing")

    if not verification_gate:
        rejection_reasons.append("verification_gate_missing")

    if not closeout_artifact:
        rejection_reasons.append("closeout_artifact_missing")

    if not park_or_escalation_rule:
        rejection_reasons.append("park_rule_missing")

    if not protected_surface_exclusions or any(
        exclusion not in protected_surface_exclusions for exclusion in REQUIRED_PROTECTED_SURFACE_EXCLUSIONS
    ):
        rejection_reasons.append("protected_surface_exclusions_missing")
    elif _scope_has_protected_violation(allowed_write_scope):
        rejection_reasons.append("protected_surface_violation")

    return {
        "owner_repo_count": owner_repo_count,
        "target_kind": target_kind,
        "target_ref": target_ref,
        "objective_summary": objective_summary,
        "allowed_write_scope": allowed_write_scope,
        "checkpoint_surface": checkpoint_surface,
        "verification_gate": verification_gate,
        "closeout_artifact": closeout_artifact,
        "park_or_escalation_rule": park_or_escalation_rule,
        "protected_surface_exclusions": protected_surface_exclusions,
        "status": "admissible" if not rejection_reasons else "not_admissible",
        "rejection_reasons": rejection_reasons,
    }
