from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, load_repo_registry, normalize_slashes, path_is_within, resolve_atlas_path

HELPER_VERSION = "atlas.batch-entry-validator.v1"
ROOT_OWNER_LABELS = {
    "atlas root",
    "atlas root control-plane surfaces",
    "atlas-root",
    "stack-root",
}
ROOT_ALLOWED_PREFIXES = (
    "docs/",
    "ops/",
    "runtime/",
    "data/",
    "packages/",
    "tmp/",
    "stack.yaml",
    "README-STACK.md",
    "AGENTS.md",
)
REQUIRED_FIELDS = (
    "entry_id",
    "lane_name",
    "job_scope",
    "owner_repo",
    "target_branch_or_worktree",
    "allowed_write_scope",
    "checkpoint_surface",
    "verification_gate",
    "closeout_artifact",
    "park_or_escalation_rule",
    "protected_surface_exclusions",
    "status",
    "created_from_receipt",
    "last_reconciled_receipt",
)
OPTIONAL_FIELDS = ("blocking_class", "human_review_hold", "notes")
ALLOWED_STATUSES = (
    "proposed",
    "admitted",
    "execution-ready",
    "running-supervised",
    "parked",
    "blocked",
    "complete",
)
UNSUPPORTED_TOP_LEVEL_KEYS = {
    "candidate_entries",
    "dispatch_mode",
    "entries",
    "input_mode",
    "queue_home",
    "queue_path",
    "registry_home",
    "registry_path",
    "resume_mode",
    "storage_hint",
    "supervisor_state",
}
PROTECTED_SURFACE_RULES = (
    ("fitness", ("repos/fawxzzy-fitness", "fitness")),
    ("archive", ("archive/", "archive")),
    ("deploy/publication", ("deploy/publication", "publication", "deploy")),
    (".env", (".env",)),
    ("secrets", ("secrets", "secret")),
)


class BatchEntryValidatorError(RuntimeError):
    pass


@dataclass(frozen=True)
class ValidationResult:
    result: str
    entry_id: str | None = None
    owner_repo: str | None = None
    target_branch_or_worktree: str | None = None
    status: str | None = None
    missing_fields: tuple[str, ...] = ()
    invalid_fields: dict[str, Any] | None = None
    boundary_failure: str | None = None
    protected_surface_failure: tuple[str, ...] = ()
    input_failure_reason: str | None = None
    cited_receipt_fields: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"result": self.result}
        if self.entry_id:
            payload["entry_id"] = self.entry_id
        if self.owner_repo:
            payload["owner_repo"] = self.owner_repo
        if self.target_branch_or_worktree:
            payload["target_branch_or_worktree"] = self.target_branch_or_worktree
        if self.status:
            payload["status"] = self.status
        if self.missing_fields:
            payload["missing_fields"] = list(self.missing_fields)
        if self.invalid_fields:
            payload["invalid_fields"] = self.invalid_fields
        if self.boundary_failure:
            payload["boundary_failure"] = self.boundary_failure
        if self.protected_surface_failure:
            payload["protected_surface_failure"] = list(self.protected_surface_failure)
        if self.input_failure_reason:
            payload["input_failure_reason"] = self.input_failure_reason
        if self.cited_receipt_fields:
            payload["cited_receipt_fields"] = list(self.cited_receipt_fields)
        return payload


def _normalize_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def _normalize_pathish(value: str) -> str:
    return normalize_slashes(value.strip())


def _normalize_string_list(value: Any, *, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str):
        normalized = _normalize_text(value)
        return (normalized,) if normalized else ()
    if not isinstance(value, list):
        raise BatchEntryValidatorError(f"{field_name} must be a string or list of strings.")
    ordered: list[str] = []
    for item in value:
        normalized = _normalize_text(item)
        if normalized is None:
            raise BatchEntryValidatorError(f"{field_name} must contain only non-empty strings.")
        ordered.append(normalized)
    return tuple(ordered)


def _load_json_payload(*, input_path: Path | None, inline_json: str | None) -> Any:
    if bool(input_path) == bool(inline_json):
        raise BatchEntryValidatorError("Provide exactly one of --input or --json.")
    if input_path is not None:
        try:
            return json.loads(input_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise BatchEntryValidatorError(f"Input file not found: {normalize_slashes(str(input_path))}") from exc
        except json.JSONDecodeError as exc:
            raise BatchEntryValidatorError(f"Malformed JSON input file: {exc}") from exc
    assert inline_json is not None
    try:
        return json.loads(inline_json)
    except json.JSONDecodeError as exc:
        raise BatchEntryValidatorError(f"Malformed inline JSON payload: {exc}") from exc


def _detect_unsupported_input(payload: dict[str, Any]) -> str | None:
    for key in payload:
        if key in UNSUPPORTED_TOP_LEVEL_KEYS:
            return f"unsupported input field: {key}"
    return None


def _classify_scope_owner(scope: str, *, registry: dict[str, Any], root: Path) -> str | None:
    normalized = _normalize_pathish(scope)
    lowered = normalized.lower()
    if any(lowered == prefix.lower() or lowered.startswith(prefix.lower()) for prefix in ROOT_ALLOWED_PREFIXES):
        return "atlas-root"

    candidate_path = resolve_atlas_path(normalized, root=root)
    if path_is_within(candidate_path, root):
        atlas_relative_path = normalize_slashes(str(candidate_path.relative_to(root)))
        if any(
            atlas_relative_path == prefix.rstrip("/")
            or atlas_relative_path.startswith(prefix)
            for prefix in ROOT_ALLOWED_PREFIXES
            if prefix.endswith("/")
        ):
            return "atlas-root"

    root_entry_seen = False
    for entry in registry.values():
        atlas_path = entry.atlas_path.rstrip("/")
        if atlas_path in {"", "."} or entry.root == root:
            root_entry_seen = True
            continue
        if normalized == atlas_path or normalized.startswith(f"{atlas_path}/"):
            return entry.repo_id
        if path_is_within(candidate_path, entry.root):
            return entry.repo_id
    if root_entry_seen and path_is_within(candidate_path, root):
        return "atlas-root"
    return None


def _owner_token(owner_repo: str, *, registry: dict[str, Any]) -> str | None:
    normalized = owner_repo.strip().lower()
    if normalized in ROOT_OWNER_LABELS | {"stack"}:
        return "atlas-root"
    for entry in registry.values():
        atlas_path = entry.atlas_path.rstrip("/").lower()
        repo_id = entry.repo_id.lower()
        if atlas_path in {"", "."}:
            if normalized in {repo_id, "stack"}:
                return "atlas-root"
            continue
        if normalized in {repo_id, atlas_path, entry.root.name.lower()}:
            return entry.repo_id
    return None


def _looks_multi_value(value: str) -> bool:
    return any(token in value for token in ("\n", "|", ";", ","))


def _validate_optional_fields(payload: dict[str, Any]) -> dict[str, Any] | None:
    invalid: dict[str, Any] = {}
    status = _normalize_text(payload.get("status"))

    if "blocking_class" in payload:
        if status != "blocked":
            invalid["blocking_class"] = "blocking_class requires status=blocked"
        elif _normalize_text(payload.get("blocking_class")) is None:
            invalid["blocking_class"] = "blocking_class must be a non-empty string"

    if "human_review_hold" in payload:
        hold_value = payload.get("human_review_hold")
        if hold_value is not True:
            invalid["human_review_hold"] = "human_review_hold must be the boolean true when present"

    if "notes" in payload:
        if _normalize_text(payload.get("notes")) is None:
            invalid["notes"] = "notes must be a non-empty string"
        elif status not in {"blocked", "parked"} and payload.get("human_review_hold") is not True:
            invalid["notes"] = "notes require blocked, parked, or held review context"

    return invalid or None


def _protected_surface_failures(
    *,
    allowed_write_scope: tuple[str, ...],
    protected_surface_exclusions: tuple[str, ...],
) -> tuple[str, ...]:
    exclusion_text = " ".join(item.lower() for item in protected_surface_exclusions)
    failures: list[str] = []
    for label, aliases in PROTECTED_SURFACE_RULES:
        if not any(alias.lower() in exclusion_text for alias in aliases):
            failures.append(f"protected_surface_exclusions missing canonical exclusion for {label}")

    for scope in allowed_write_scope:
        lowered = _normalize_pathish(scope).lower()
        if lowered.startswith("repos/fawxzzy-fitness"):
            failures.append("allowed_write_scope touches repos/fawxzzy-fitness")
        if lowered.startswith("archive/") or lowered == "archive":
            failures.append("allowed_write_scope touches archive/")
        if "/.env" in lowered or lowered.endswith(".env") or "/.env." in lowered:
            failures.append("allowed_write_scope touches .env")
        if lowered.startswith("secrets/") or "/secrets/" in lowered:
            failures.append("allowed_write_scope touches secrets")
        if "publish" in lowered or "deploy" in lowered:
            failures.append("allowed_write_scope implies deploy/publication surfaces")
    return tuple(dict.fromkeys(failures))


def validate_batch_entry_payload(
    payload: Any,
    *,
    root: Path | None = None,
) -> ValidationResult:
    base_root = (root or atlas_root()).resolve()
    registry = load_repo_registry(root=base_root)

    if isinstance(payload, list):
        return ValidationResult(result="invalid-input", input_failure_reason="multi-entry payloads are unsupported")
    if not isinstance(payload, dict):
        return ValidationResult(result="invalid-input", input_failure_reason="candidate entry must be a JSON object")

    unsupported_reason = _detect_unsupported_input(payload)
    if unsupported_reason:
        return ValidationResult(result="invalid-input", input_failure_reason=unsupported_reason)

    entry_id = _normalize_text(payload.get("entry_id"))
    owner_repo = _normalize_text(payload.get("owner_repo"))
    target = _normalize_text(payload.get("target_branch_or_worktree"))
    status = _normalize_text(payload.get("status"))

    missing_fields: list[str] = []
    invalid_fields: dict[str, Any] = {}

    for field_name in REQUIRED_FIELDS:
        if field_name == "allowed_write_scope":
            value = payload.get(field_name)
            try:
                scope_values = _normalize_string_list(value, field_name=field_name)
            except BatchEntryValidatorError:
                scope_values = ()
            if not scope_values:
                missing_fields.append(field_name)
            continue
        if field_name == "protected_surface_exclusions":
            value = payload.get(field_name)
            try:
                exclusion_values = _normalize_string_list(value, field_name=field_name)
            except BatchEntryValidatorError:
                exclusion_values = ()
            if not exclusion_values:
                missing_fields.append(field_name)
            continue
        if _normalize_text(payload.get(field_name)) is None:
            missing_fields.append(field_name)

    if missing_fields:
        cited_receipt_fields = tuple(
            field_name
            for field_name in ("created_from_receipt", "last_reconciled_receipt")
            if field_name in missing_fields
        )
        return ValidationResult(
            result="invalid-missing-field",
            entry_id=entry_id,
            owner_repo=owner_repo,
            target_branch_or_worktree=target,
            status=status,
            missing_fields=tuple(missing_fields),
            cited_receipt_fields=cited_receipt_fields,
        )

    allowed_write_scope = _normalize_string_list(payload.get("allowed_write_scope"), field_name="allowed_write_scope")
    protected_surface_exclusions = _normalize_string_list(
        payload.get("protected_surface_exclusions"),
        field_name="protected_surface_exclusions",
    )

    if status not in ALLOWED_STATUSES:
        invalid_fields["status"] = payload.get("status")
        return ValidationResult(
            result="invalid-status",
            entry_id=entry_id,
            owner_repo=owner_repo,
            target_branch_or_worktree=target,
            status=status,
            invalid_fields=invalid_fields,
        )

    optional_field_failures = _validate_optional_fields(payload)
    if optional_field_failures:
        return ValidationResult(
            result="invalid-optional-field",
            entry_id=entry_id,
            owner_repo=owner_repo,
            target_branch_or_worktree=target,
            status=status,
            invalid_fields=optional_field_failures,
        )

    if owner_repo is None or _looks_multi_value(owner_repo) or isinstance(payload.get("owner_repo"), list):
        return ValidationResult(
            result="invalid-owner-boundary",
            entry_id=entry_id,
            owner_repo=owner_repo,
            target_branch_or_worktree=target,
            status=status,
            boundary_failure="multiple owner repos are implied by owner_repo",
        )

    owner_token = _owner_token(owner_repo, registry=registry)
    scope_tokens = {
        token
        for token in (
            _classify_scope_owner(scope, registry=registry, root=base_root)
            for scope in allowed_write_scope
        )
        if token is not None
    }
    if len(scope_tokens) > 1 or (owner_token is not None and scope_tokens and scope_tokens != {owner_token}):
        return ValidationResult(
            result="invalid-owner-boundary",
            entry_id=entry_id,
            owner_repo=owner_repo,
            target_branch_or_worktree=target,
            status=status,
            boundary_failure="allowed_write_scope implies more than one owner surface",
        )

    if target is None or _looks_multi_value(target) or isinstance(payload.get("target_branch_or_worktree"), list):
        return ValidationResult(
            result="invalid-target-boundary",
            entry_id=entry_id,
            owner_repo=owner_repo,
            target_branch_or_worktree=target,
            status=status,
            boundary_failure="multiple target branches or worktrees are implied",
        )

    protected_surface_failure = _protected_surface_failures(
        allowed_write_scope=allowed_write_scope,
        protected_surface_exclusions=protected_surface_exclusions,
    )
    if protected_surface_failure:
        return ValidationResult(
            result="invalid-protected-surface-exclusion",
            entry_id=entry_id,
            owner_repo=owner_repo,
            target_branch_or_worktree=target,
            status=status,
            protected_surface_failure=protected_surface_failure,
        )

    return ValidationResult(
        result="valid",
        entry_id=entry_id,
        owner_repo=owner_repo,
        target_branch_or_worktree=target,
        status=status,
    )


def run_validator(
    *,
    input_path: Path | None = None,
    inline_json: str | None = None,
    root: Path | None = None,
) -> ValidationResult:
    try:
        payload = _load_json_payload(input_path=input_path, inline_json=inline_json)
    except BatchEntryValidatorError as exc:
        return ValidationResult(result="invalid-input", input_failure_reason=str(exc))
    return validate_batch_entry_payload(payload, root=root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate one bounded queue-or-registry batch-entry candidate.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", type=Path)
    group.add_argument("--json")
    args = parser.parse_args(argv)

    result = run_validator(
        input_path=args.input.resolve() if isinstance(args.input, Path) else None,
        inline_json=args.json,
        root=args.root.resolve(),
    )
    print(json.dumps(result.to_payload(), indent=2))
    return 0 if result.result == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
