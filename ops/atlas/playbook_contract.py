from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from ops._atlas import atlas_relative, atlas_root
from ops.stack.export_repo_inventory import build_repo_inventory, find_repo_inventory_entry

PLAYBOOK_CONTRACT_EXPORT = "exports/playbook.contract.example.v1.json"
PLAYBOOK_CONTRACT_SCHEMA = "exports/playbook.contract.schema.v1.json"
PLAYBOOK_CONTRACT_DOC = "docs/contracts/PLAYBOOK-CONTRACT.md"
PLAYBOOK_EXPORT_TEST = "packages/engine/test/playbookContractExport.test.ts"
REPORT_SCHEMA_VERSION = "atlas.playbook.adoption.report.v1"
REPO_ADOPTION_EXPORT_TEMPLATE = "exports/{repo_id}.playbook.adoption.evidence.v1.json"
REPO_ADOPTION_SCHEMA_PATH = "exports/repo.playbook.adoption.evidence.schema.v1.json"
REPO_ADOPTION_DOC_TEMPLATE = "docs/ops/{repo_name}-PLAYBOOK-ADOPTION.md"
REPO_ADOPTION_TEST_PATH = "tests/playbook-adoption-evidence.test.mjs"
REPO_VERIFICATION_REPORT_TEMPLATE = "exports/{repo_id}.playbook.verification.report.v1.json"

REQUIRED_EXPORT_FIELDS = {
    "contract_id",
    "contract_version",
    "status",
    "intent",
    "canonical_principles",
    "operating_loop",
    "owner_domains",
    "conformance_classes",
    "patterns",
    "continuity_requirements",
    "adoption_statuses",
    "evidence_types",
    "exception_requirements",
    "adoption_checks",
    "verification_hooks",
    "anti_patterns",
}

ADOPTION_STATUSES = {
    "unassessed",
    "planned",
    "partial",
    "adopted",
    "verified",
    "exception",
}
VERIFICATION_STATES = {"none", "targeted", "full", "exception_documented", "unknown"}
CONTINUITY_STATES = {"missing", "planned", "partial", "structured", "verified", "unknown"}
DRIFT_STATES = {"unknown", "none_detected", "possible", "detected", "exception"}
REPO_ADOPTION_ITEM_STATES = {"missing", "planned", "partial", "implemented", "not_applicable", "exception"}
REPO_ADOPTION_CONTINUITY_STATES = {"unknown", "planned", "structured", "promoted"}
REPO_ADOPTION_DRIFT_STATES = {"unknown", "none_detected", "suspected", "detected"}
VERIFICATION_STATUSES = {"missing", "partial", "blocked", "verified", "unknown"}
VERIFICATION_CRITERION_STATES = {"passed", "failed", "blocked", "missing"}
VERIFICATION_SCOPE_KINDS = {"targeted", "full", "exception_documented"}
REPORT_REPO_ORDER = [
    "playbook",
    "stack",
    "lifeline",
    "_stack",
    "atlas",
    "fitness",
    "mazer",
    "stream",
    "nat1-games",
    "playbook-demo",
]


def _normalize_repo_adoption_continuity_status(value: Any) -> str:
    normalized = str(value or "").strip()
    if normalized == "promoted":
        return "verified"
    return normalized if normalized in CONTINUITY_STATES else "unknown"


def _normalize_repo_adoption_drift_status(value: Any) -> str:
    normalized = str(value or "").strip()
    if normalized == "suspected":
        return "possible"
    return normalized if normalized in DRIFT_STATES else "unknown"


def validate_repo_adoption_payload(payload: dict[str, Any], *, expected_repo_id: str | None = None) -> list[str]:
    errors: list[str] = []
    for field in (
        "artifact_id",
        "generated_at",
        "repo",
        "contract_claim",
        "summary",
        "implemented_patterns",
        "adoption_checks",
        "continuity",
        "evidence_refs",
    ):
        if field not in payload:
            errors.append(f"Missing top-level field: {field}")

    repo = payload.get("repo")
    if not isinstance(repo, dict):
        errors.append("repo must be an object.")
    else:
        repo_id = str(repo.get("repo_id") or "").strip()
        if not repo_id:
            errors.append("repo.repo_id is required.")
        elif expected_repo_id is not None and repo_id != expected_repo_id:
            errors.append(f"repo.repo_id must be {expected_repo_id}.")
        if str(repo.get("role") or "").strip() == "":
            errors.append("repo.role is required.")
        if repo.get("repo_identity") not in {"remote", "local_only", "unknown"}:
            errors.append("repo.repo_identity is invalid.")

    contract_claim = payload.get("contract_claim")
    if not isinstance(contract_claim, dict):
        errors.append("contract_claim must be an object.")
    else:
        for field in ("contract_id", "contract_version", "source_repo_id", "source_export_path", "claim_state"):
            if str(contract_claim.get(field) or "").strip() == "":
                errors.append(f"contract_claim.{field} is required.")

    summary = payload.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary must be an object.")
    else:
        if summary.get("adoption_status") not in ADOPTION_STATUSES:
            errors.append("summary.adoption_status is invalid.")
        if summary.get("verification_state") not in {"none", "targeted", "full"}:
            errors.append("summary.verification_state is invalid.")
        if summary.get("continuity_status") not in REPO_ADOPTION_CONTINUITY_STATES:
            errors.append("summary.continuity_status is invalid.")
        if summary.get("drift_status") not in REPO_ADOPTION_DRIFT_STATES:
            errors.append("summary.drift_status is invalid.")

    continuity = payload.get("continuity")
    if not isinstance(continuity, dict):
        errors.append("continuity must be an object.")
    else:
        if not isinstance(continuity.get("structured_handoff_required"), bool):
            errors.append("continuity.structured_handoff_required must be a boolean.")
        if continuity.get("transcript_role") not in {"trace_only", "working_input", "unknown"}:
            errors.append("continuity.transcript_role is invalid.")

    evidence_refs = payload.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not any(isinstance(ref, str) and ref.strip() for ref in evidence_refs):
        errors.append("evidence_refs must contain at least one non-empty string ref.")

    for field_name in ("implemented_patterns", "adoption_checks"):
        items = payload.get(field_name)
        if not isinstance(items, list):
            errors.append(f"{field_name} must be an array.")
            continue
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{field_name}[{index}] must be an object.")
                continue
            item_id = str(item.get("id") or "").strip()
            if not item_id:
                errors.append(f"{field_name}[{index}].id is required.")
            status = item.get("status")
            if status not in REPO_ADOPTION_ITEM_STATES:
                errors.append(f"{field_name}[{index}].status is invalid.")
            notes = item.get("notes", [])
            if status == "not_applicable" and not any(isinstance(note, str) and note.strip() for note in notes if isinstance(notes, list)):
                errors.append(f"{field_name}[{index}] marked not_applicable must include a justification note.")
    return errors


def validate_playbook_verification_report(
    payload: dict[str, Any],
    *,
    expected_repo_id: str | None = None,
) -> list[str]:
    errors: list[str] = []
    for field in ("artifact_id", "generated_at", "repo", "summary", "scope", "criteria", "evidence_refs"):
        if field not in payload:
            errors.append(f"Missing top-level field: {field}")

    repo = payload.get("repo")
    if not isinstance(repo, dict):
        errors.append("repo must be an object.")
    else:
        repo_id = str(repo.get("repo_id") or "").strip()
        if not repo_id:
            errors.append("repo.repo_id is required.")
        elif expected_repo_id is not None and repo_id != expected_repo_id:
            errors.append(f"repo.repo_id must be {expected_repo_id}.")
        if repo.get("repo_identity") not in {"remote", "local_only", "unknown"}:
            errors.append("repo.repo_identity is invalid.")

    summary = payload.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary must be an object.")
    else:
        if summary.get("adoption_status") not in ADOPTION_STATUSES:
            errors.append("summary.adoption_status is invalid.")
        if summary.get("verification_status") not in VERIFICATION_STATUSES:
            errors.append("summary.verification_status is invalid.")
        blocking_gaps = summary.get("blocking_gaps")
        if not isinstance(blocking_gaps, list):
            errors.append("summary.blocking_gaps must be an array.")
        if summary.get("verification_status") == "verified":
            if not isinstance(summary.get("last_verified_at"), str) or not str(summary.get("last_verified_at")).strip():
                errors.append("summary.last_verified_at is required when verification_status is verified.")
            if isinstance(blocking_gaps, list) and any(
                isinstance(gap, str) and gap.strip()
                for gap in blocking_gaps
            ):
                errors.append("summary.blocking_gaps must be empty when verification_status is verified.")

    scope = payload.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope must be an object.")
    else:
        if scope.get("verification_kind") not in VERIFICATION_SCOPE_KINDS:
            errors.append("scope.verification_kind is invalid.")
        covered_surfaces = scope.get("covered_surfaces")
        if not isinstance(covered_surfaces, list) or not any(
            isinstance(item, str) and item.strip()
            for item in covered_surfaces
        ):
            errors.append("scope.covered_surfaces must contain at least one non-empty string.")
        notes = scope.get("notes")
        if not isinstance(notes, list):
            errors.append("scope.notes must be an array.")

    criteria = payload.get("criteria")
    if not isinstance(criteria, dict):
        errors.append("criteria must be an object.")
    else:
        for field in ("adoption_export", "adoption_test", "verification_path"):
            criterion = criteria.get(field)
            if not isinstance(criterion, dict):
                errors.append(f"criteria.{field} must be an object.")
                continue
            if criterion.get("status") not in VERIFICATION_CRITERION_STATES:
                errors.append(f"criteria.{field}.status is invalid.")
            if field == "verification_path":
                commands = criterion.get("commands")
                if not isinstance(commands, list) or not any(isinstance(command, str) and command.strip() for command in commands):
                    errors.append("criteria.verification_path.commands must contain at least one command.")

    evidence_refs = payload.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not any(isinstance(ref, str) and ref.strip() for ref in evidence_refs):
        errors.append("evidence_refs must contain at least one non-empty string ref.")
    return errors


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}.")
    return payload


def _repo_identity(repo_entry: dict[str, Any] | None) -> str:
    if not isinstance(repo_entry, dict):
        return "unknown"
    remote_url = str(repo_entry.get("remote_url") or "").strip()
    if remote_url:
        return "remote"
    if bool(repo_entry.get("exists")):
        return "local_only"
    return "unknown"


def _repo_path(repo_entry: dict[str, Any] | None) -> str | None:
    if not isinstance(repo_entry, dict):
        return None
    path = str(repo_entry.get("local_path") or "").strip()
    return path or None


def _existing_refs(paths: list[Path]) -> list[str]:
    return [atlas_relative(path) for path in paths if path.exists()]


def _normalize_repo_evidence_ref(*, root: Path, repo_root: Path, repo_path: str, ref: str) -> str | None:
    normalized = str(ref or "").strip().replace("\\", "/")
    if not normalized:
        return None
    repo_candidate = (repo_root / normalized).resolve()
    if repo_candidate.exists():
        return f"{repo_path.rstrip('/')}/{normalized}".replace("\\", "/")
    root_candidate = (root / normalized).resolve()
    if root_candidate.exists():
        return normalized
    return f"{repo_path.rstrip('/')}/{normalized}".replace("\\", "/")


def _load_repo_adoption_projection(
    *,
    root: Path,
    repo_entry: dict[str, Any],
) -> dict[str, Any] | None:
    repo_id = str(repo_entry.get("logical_id") or "").strip()
    repo_path = _repo_path(repo_entry)
    if not repo_id or not repo_path:
        return None

    repo_root = (root / repo_path).resolve()
    export_path = repo_root / REPO_ADOPTION_EXPORT_TEMPLATE.format(repo_id=repo_id)
    if not export_path.exists():
        return None

    try:
        payload = _load_json(export_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None

    validation_errors = validate_repo_adoption_payload(payload, expected_repo_id=repo_id)

    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    contract_claim = payload.get("contract_claim") if isinstance(payload.get("contract_claim"), dict) else {}
    notes = [str(note) for note in summary.get("notes", []) if isinstance(note, str)]
    notes.append("Projected read-only from repo-local Playbook adoption evidence.")

    repo_name = repo_id.upper()
    schema_path = repo_root / REPO_ADOPTION_SCHEMA_PATH
    doc_path = repo_root / REPO_ADOPTION_DOC_TEMPLATE.format(repo_name=repo_name)
    test_path = repo_root / REPO_ADOPTION_TEST_PATH

    evidence_refs: list[str] = []
    for path in (export_path, schema_path, doc_path, test_path):
        if path.exists():
            evidence_refs.append(atlas_relative(path, root=root))
    for ref in payload.get("evidence_refs", []):
        if isinstance(ref, str):
            normalized = _normalize_repo_evidence_ref(
                root=root,
                repo_root=repo_root,
                repo_path=repo_path,
                ref=ref,
            )
            if normalized:
                evidence_refs.append(normalized)

    evidence_types = ["repo_adoption_export"]
    if schema_path.exists():
        evidence_types.append("repo_adoption_schema")
    if doc_path.exists():
        evidence_types.append("repo_adoption_doc")
    if test_path.exists():
        evidence_types.append("repo_adoption_targeted_test")

    adoption_status = str(summary.get("adoption_status") or "").strip()
    if adoption_status not in ADOPTION_STATUSES:
        adoption_status = "partial"
    elif validation_errors and adoption_status in {"adopted", "verified"}:
        adoption_status = "partial"

    verification_state = str(summary.get("verification_state") or "").strip()
    if verification_state not in VERIFICATION_STATES:
        verification_state = "unknown"

    continuity_status = _normalize_repo_adoption_continuity_status(summary.get("continuity_status"))

    drift_status = _normalize_repo_adoption_drift_status(summary.get("drift_status"))

    initiative_refs = [
        str(ref)
        for ref in summary.get("initiative_refs", [])
        if isinstance(ref, str) and str(ref).strip()
    ]

    if validation_errors:
        notes.append("Repo-local adoption evidence failed root-side validation and cannot promote to verified.")
        notes.extend(f"Validation error: {error}" for error in validation_errors)

    return {
        "contract_version_claimed": str(contract_claim.get("contract_version") or "").strip() or None,
        "adoption_status": adoption_status,
        "verification_state": verification_state,
        "continuity_status": continuity_status,
        "drift_status": drift_status,
        "evidence_types": evidence_types,
        "evidence_refs": sorted(set(evidence_refs)),
        "initiative_refs": sorted(set(initiative_refs)),
        "notes": notes,
        "payload": payload,
        "validation_errors": validation_errors,
        "validation_state": "valid" if not validation_errors else "invalid",
    }


def _load_repo_verification_projection(
    *,
    root: Path,
    repo_entry: dict[str, Any],
    repo_adoption: dict[str, Any] | None,
) -> dict[str, Any]:
    repo_id = str(repo_entry.get("logical_id") or "").strip()
    repo_path = _repo_path(repo_entry)
    repo_identity = _repo_identity(repo_entry)
    base_projection = {
        "verification_status": "missing",
        "verification_scope": None,
        "blocking_gaps": [],
        "evidence_refs": [],
        "evidence_types": [],
        "last_verified_at": None,
        "notes": [],
    }
    if not repo_id or not repo_path:
        return base_projection | {
            "verification_status": "unknown",
            "blocking_gaps": ["Repo inventory entry is missing a stable repo path."],
            "notes": ["Verification gate cannot be evaluated without a stable repo path."],
        }

    repo_root = (root / repo_path).resolve()
    report_path = repo_root / REPO_VERIFICATION_REPORT_TEMPLATE.format(repo_id=repo_id)
    evidence_refs = []
    evidence_types = []
    blocking_gaps: list[str] = []
    notes: list[str] = []
    last_verified_at: str | None = None
    verification_scope: str | None = None

    if repo_adoption is None:
        blocking_gaps.append("Repo-owned adoption export is missing.")
    else:
        evidence_refs.extend(
            ref
            for ref in repo_adoption.get("evidence_refs", [])
            if isinstance(ref, str) and ref.strip()
        )
        if repo_adoption.get("validation_state") != "valid":
            blocking_gaps.append("Repo-owned adoption export does not validate at the root.")
        if str(repo_adoption.get("adoption_status") or "").strip() not in {"adopted", "verified"}:
            blocking_gaps.append("Root does not currently see the repo as adopted.")
        payload = repo_adoption.get("payload")
        if isinstance(payload, dict):
            for field_name in ("implemented_patterns", "adoption_checks"):
                items = payload.get(field_name, [])
                if not isinstance(items, list):
                    continue
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    if str(item.get("status") or "").strip() != "not_applicable":
                        continue
                    notes_list = item.get("notes", [])
                    if not any(
                        isinstance(note, str) and note.strip()
                        for note in notes_list
                        if isinstance(notes_list, list)
                    ):
                        blocking_gaps.append(
                            f"{field_name}:{item.get('id')} is marked not_applicable without a justification."
                        )

    if repo_identity != "remote":
        blocking_gaps.append(f"Repo identity {repo_identity} is not stable enough for verified promotion.")

    trust_class = str(repo_entry.get("trust_class") or "").strip()
    if trust_class and trust_class != "trusted":
        blocking_gaps.append(f"Repo trust class {trust_class} contradicts verified promotion.")

    if not report_path.exists():
        blocking_gaps.append("Repo-owned verification report is missing.")
        notes.append("Verified promotion requires a repo-owned verification report.")
        return base_projection | {
            "verification_status": "missing",
            "blocking_gaps": sorted(set(blocking_gaps)),
            "evidence_refs": sorted(set(evidence_refs)),
            "evidence_types": evidence_types,
            "last_verified_at": None,
            "notes": notes,
        }

    evidence_refs.append(atlas_relative(report_path, root=root))
    evidence_types.append("repo_verification_report")

    try:
        payload = _load_json(report_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        blocking_gaps.append(f"Repo-owned verification report could not be parsed: {exc}")
        return base_projection | {
            "verification_status": "blocked",
            "blocking_gaps": sorted(set(blocking_gaps)),
            "evidence_refs": sorted(set(evidence_refs)),
            "evidence_types": evidence_types,
            "last_verified_at": None,
            "notes": notes,
        }

    validation_errors = validate_playbook_verification_report(payload, expected_repo_id=repo_id)
    if validation_errors:
        blocking_gaps.extend(validation_errors)
        notes.append("Repo-owned verification report failed root-side validation.")
        return base_projection | {
            "verification_status": "blocked",
            "blocking_gaps": sorted(set(blocking_gaps)),
            "evidence_refs": sorted(set(evidence_refs)),
            "evidence_types": evidence_types,
            "last_verified_at": None,
            "notes": notes,
        }

    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    scope = payload.get("scope") if isinstance(payload.get("scope"), dict) else {}
    criteria = payload.get("criteria") if isinstance(payload.get("criteria"), dict) else {}
    declared_status = str(summary.get("verification_status") or "").strip()
    if declared_status not in VERIFICATION_STATUSES:
        declared_status = "unknown"
    last_verified_value = str(summary.get("last_verified_at") or "").strip()
    last_verified_at = last_verified_value or None
    declared_scope = str(scope.get("verification_kind") or "").strip()
    if declared_scope in VERIFICATION_SCOPE_KINDS:
        verification_scope = declared_scope

    for ref in payload.get("evidence_refs", []):
        if isinstance(ref, str):
            normalized = _normalize_repo_evidence_ref(
                root=root,
                repo_root=repo_root,
                repo_path=repo_path,
                ref=ref,
            )
            if normalized:
                evidence_refs.append(normalized)

    summary_gaps = summary.get("blocking_gaps", [])
    if isinstance(summary_gaps, list):
        blocking_gaps.extend(str(gap) for gap in summary_gaps if isinstance(gap, str) and gap.strip())

    criterion_labels = {
        "adoption_export": "Repo-owned adoption export validation",
        "adoption_test": "Repo-owned adoption test",
        "verification_path": "Repo-owned verification path",
    }
    for criterion_name, label in criterion_labels.items():
        criterion = criteria.get(criterion_name) if isinstance(criteria.get(criterion_name), dict) else {}
        state = str(criterion.get("status") or "").strip()
        if state != "passed":
            if state in {"failed", "blocked"}:
                blocking_gaps.append(f"{label} is not green ({state}).")
            else:
                blocking_gaps.append(f"{label} is incomplete ({state or 'missing'}).")
        for ref in criterion.get("evidence_refs", []):
            if isinstance(ref, str):
                normalized = _normalize_repo_evidence_ref(
                    root=root,
                    repo_root=repo_root,
                    repo_path=repo_path,
                    ref=ref,
                )
                if normalized:
                    evidence_refs.append(normalized)
        if criterion_name == "verification_path":
            commands = criterion.get("commands", [])
            if not isinstance(commands, list) or not any(isinstance(command, str) and command.strip() for command in commands):
                blocking_gaps.append("Repo-owned verification path does not declare any reproducible commands.")
            else:
                evidence_types.append("repo_verification_path")

    if declared_status == "verified" and not last_verified_at:
        blocking_gaps.append("Verification report does not record last_verified_at.")

    if not blocking_gaps and declared_status == "verified":
        verification_status = "verified"
    elif declared_status == "blocked" or any(
        str((criteria.get(name) or {}).get("status") or "").strip() in {"failed", "blocked"}
        for name in criterion_labels
    ):
        verification_status = "blocked"
    elif declared_status == "verified":
        verification_status = "blocked"
    elif declared_status in {"partial", "missing"}:
        verification_status = declared_status
    else:
        verification_status = "partial"

    if verification_status == "verified":
        notes.append("Repo-owned verification report satisfies the root verified gate.")
    else:
        notes.append("Repo remains below verified until the verification report and root gate are fully green.")

    return base_projection | {
        "verification_status": verification_status,
        "verification_scope": verification_scope,
        "blocking_gaps": sorted(set(blocking_gaps)),
        "evidence_refs": sorted(set(evidence_refs)),
        "evidence_types": sorted(set(evidence_types)),
        "last_verified_at": last_verified_at,
        "notes": notes,
    }


def inspect_playbook_contract_source(
    *,
    export_path: Path,
    schema_path: Path,
    doc_path: Path,
    repo_id: str,
    repo_path: str | None,
    repo_identity: str,
    owner_test_path: Path | None = None,
) -> dict[str, Any]:
    contract_id: str | None = None
    contract_version: str | None = None
    contract_status: str | None = None
    warnings: list[str] = []
    evidence_refs = _existing_refs(
        [path for path in [export_path, schema_path, doc_path, owner_test_path] if isinstance(path, Path)]
    )

    if not export_path.exists():
        return {
            "repo_id": repo_id,
            "repo_identity": repo_identity,
            "repo_path": repo_path,
            "export_relpath": atlas_relative(export_path),
            "schema_relpath": atlas_relative(schema_path),
            "doc_relpath": atlas_relative(doc_path),
            "contract_id": contract_id,
            "contract_version": contract_version,
            "contract_status": contract_status,
            "source_status": "missing",
            "validation_state": "schema_invalid",
            "evidence_refs": evidence_refs,
            "warnings": ["Playbook export is missing from the owner repo path."],
        }

    try:
        export_payload = _load_json(export_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "repo_id": repo_id,
            "repo_identity": repo_identity,
            "repo_path": repo_path,
            "export_relpath": atlas_relative(export_path),
            "schema_relpath": atlas_relative(schema_path),
            "doc_relpath": atlas_relative(doc_path),
            "contract_id": contract_id,
            "contract_version": contract_version,
            "contract_status": contract_status,
            "source_status": "malformed",
            "validation_state": "schema_invalid",
            "evidence_refs": evidence_refs,
            "warnings": [f"Playbook export could not be parsed: {exc}"],
        }

    missing_fields = sorted(REQUIRED_EXPORT_FIELDS.difference(export_payload.keys()))
    if missing_fields:
        warnings.append(
            "Playbook export is missing required top-level fields: " + ", ".join(missing_fields)
        )

    contract_id = str(export_payload.get("contract_id") or "").strip() or None
    contract_version = str(export_payload.get("contract_version") or "").strip() or None
    contract_status = str(export_payload.get("status") or "").strip() or None

    try:
        _ = _load_json(schema_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        warnings.append(f"Playbook schema could not be parsed: {exc}")

    if not doc_path.exists():
        warnings.append("Human-readable Playbook contract doc is missing.")
    if owner_test_path is None or not owner_test_path.exists():
        warnings.append("Owner export test surface is not visible from the stack root.")

    validation_state = "schema_valid" if not warnings else "schema_invalid"
    source_status = "present" if validation_state == "schema_valid" else "malformed"
    return {
        "repo_id": repo_id,
        "repo_identity": repo_identity,
        "repo_path": repo_path,
        "export_relpath": atlas_relative(export_path),
        "schema_relpath": atlas_relative(schema_path),
        "doc_relpath": atlas_relative(doc_path),
        "contract_id": contract_id,
        "contract_version": contract_version,
        "contract_status": contract_status,
        "source_status": source_status,
        "validation_state": validation_state,
        "evidence_refs": evidence_refs,
        "warnings": warnings,
    }


def load_playbook_contract_source(
    *,
    root: Path | None = None,
    inventory_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    inventory = inventory_payload or build_repo_inventory(root=base_root)
    repo_entry = find_repo_inventory_entry(inventory, repo_id="playbook")
    repo_path = _repo_path(repo_entry)
    repo_identity = _repo_identity(repo_entry)
    if repo_path is None:
        return {
            "repo_id": "playbook",
            "repo_identity": repo_identity,
            "repo_path": repo_path,
            "export_relpath": PLAYBOOK_CONTRACT_EXPORT,
            "schema_relpath": PLAYBOOK_CONTRACT_SCHEMA,
            "doc_relpath": PLAYBOOK_CONTRACT_DOC,
            "contract_id": None,
            "contract_version": None,
            "contract_status": None,
            "source_status": "unknown",
            "validation_state": "unknown",
            "evidence_refs": [],
            "warnings": ["Playbook repo is missing from the live repo inventory."],
        }

    repo_root = (base_root / repo_path).resolve()
    return inspect_playbook_contract_source(
        export_path=repo_root / PLAYBOOK_CONTRACT_EXPORT,
        schema_path=repo_root / PLAYBOOK_CONTRACT_SCHEMA,
        doc_path=repo_root / PLAYBOOK_CONTRACT_DOC,
        repo_id="playbook",
        repo_path=repo_path,
        repo_identity=repo_identity,
        owner_test_path=repo_root / PLAYBOOK_EXPORT_TEST,
    )


def _role_for_repo(repo_id: str) -> str:
    role_map = {
        "stack": "atlas_root",
        "playbook": "playbook",
        "lifeline": "lifeline",
        "_stack": "stack_orchestrator",
        "atlas": "atlas_platform_repo",
        "fitness": "vertical_owner_repo",
        "mazer": "vertical_owner_repo",
        "stream": "vertical_owner_repo",
        "nat1-games": "vertical_owner_repo",
        "playbook-demo": "demo_surface",
    }
    return role_map.get(repo_id, "unknown")


def _repo_row(repo_entry: dict[str, Any], *, contract_source: dict[str, Any], root: Path) -> dict[str, Any]:
    repo_id = str(repo_entry.get("logical_id") or "").strip()
    repo_identity = _repo_identity(repo_entry)
    contract_version = str(contract_source.get("contract_version") or "").strip() or None
    initiative_refs = list(repo_entry.get("related_initiative_refs", [])) if isinstance(
        repo_entry.get("related_initiative_refs"), list
    ) else []
    evidence_types = ["inventory_export"]
    evidence_refs = [str(repo_entry.get("local_path") or "")]
    notes: list[str] = []
    adoption_status = "unassessed"
    verification_state = "none"
    verification_status = "missing"
    verification_scope: str | None = None
    continuity_status = "unknown"
    drift_status = "unknown"
    blocking_gaps: list[str] = []
    last_verified_at: str | None = None
    contract_version_claimed: str | None = None
    repo_adoption = _load_repo_adoption_projection(root=root, repo_entry=repo_entry)
    repo_verification = _load_repo_verification_projection(
        root=root,
        repo_entry=repo_entry,
        repo_adoption=repo_adoption,
    )

    if repo_adoption is not None:
        contract_version_claimed = repo_adoption["contract_version_claimed"] or contract_version
        adoption_status = str(repo_adoption["adoption_status"])
        verification_state = str(repo_adoption["verification_state"])
        continuity_status = str(repo_adoption["continuity_status"])
        drift_status = str(repo_adoption["drift_status"])
        evidence_types = list(repo_adoption["evidence_types"])
        evidence_refs = list(repo_adoption["evidence_refs"])
        initiative_refs = sorted(
            {
                *initiative_refs,
                *[
                    ref
                    for ref in repo_adoption["initiative_refs"]
                    if isinstance(ref, str) and ref
                ],
            }
        )
        notes.extend(note for note in repo_adoption["notes"] if isinstance(note, str) and note)
    evidence_types.extend(repo_verification.get("evidence_types", []))
    evidence_refs.extend(
        ref
        for ref in repo_verification.get("evidence_refs", [])
        if isinstance(ref, str) and ref
    )
    notes.extend(
        note
        for note in repo_verification.get("notes", [])
        if isinstance(note, str) and note
    )
    verification_status = str(repo_verification.get("verification_status") or "missing")
    verification_scope = (
        str(repo_verification.get("verification_scope")).strip()
        if isinstance(repo_verification.get("verification_scope"), str)
        else None
    )
    blocking_gaps = [
        str(gap)
        for gap in repo_verification.get("blocking_gaps", [])
        if isinstance(gap, str) and gap.strip()
    ]
    last_verified_at = (
        str(repo_verification.get("last_verified_at")).strip()
        if isinstance(repo_verification.get("last_verified_at"), str)
        else None
    )

    if repo_id == "playbook":
        adoption_status = "adopted" if contract_source.get("source_status") == "present" else "partial"
        verification_state = "targeted"
        continuity_status = "structured"
        drift_status = "none_detected" if contract_source.get("source_status") == "present" else "detected"
        contract_version_claimed = contract_version
        evidence_types = ["contract_example", "schema_validation", "runbook_reference", "unit_test"]
        evidence_refs = list(contract_source.get("evidence_refs", []))
        notes.extend(
            [
                "Owner-truth export remains the canonical Playbook contract surface.",
                "ATLAS consumes the export read-only from the owner repo path.",
            ]
        )
    elif repo_id == "stack":
        adoption_status = "partial"
        verification_state = "targeted"
        continuity_status = "structured"
        drift_status = "possible"
        contract_version_claimed = contract_version
        evidence_types = ["status_surface", "runbook_reference", "inventory_export"]
        evidence_refs = [
            "docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md",
            "docs/ops/PLAYBOOK-ADOPTION-MATRIX.md",
            "ops/atlas/playbook_contract.py",
            "ops/atlas/continuity.py",
        ]
        notes.append("Root read models project owner truth without creating a second doctrine store.")
    elif repo_id in {"lifeline", "_stack", "atlas"}:
        adoption_status = "partial"
        continuity_status = "partial"
        drift_status = "possible"
        evidence_types = ["inventory_export", "runbook_reference"]
        evidence_refs = ["docs/ops/PLAYBOOK-ADOPTION-MATRIX.md", str(repo_entry.get("local_path") or "")]
        notes.append("Visible from stack doctrine, but no repo-local contract proof is projected yet.")
    elif repo_id == "fitness":
        if repo_adoption is None:
            adoption_status = "planned"
            continuity_status = "planned"
            notes.append("First vertical adoption tranche.")
    elif repo_id == "mazer":
        if repo_adoption is None:
            adoption_status = "planned"
            continuity_status = "planned"
            evidence_types.append("status_surface")
            if "initiative:initiative-mazer-d2-learning-scorer" not in initiative_refs:
                initiative_refs.append("initiative:initiative-mazer-d2-learning-scorer")
            notes.extend(["Primary operator fixture.", "Second vertical adoption candidate."])
    elif repo_id == "stream":
        notes.append("Local-only incubating repo stays visible without being overclaimed.")
    elif repo_id == "nat1-games":
        notes.append("Incubating remote repo remains outside the first rollout until explicitly adopted.")
    elif repo_id == "playbook-demo":
        notes.append("Demo surface is visible but not part of the current adoption gate.")

    if repo_identity == "local_only":
        notes.append("Local-only identity does not imply verification.")
    if repo_identity == "unknown":
        notes.append("Repo identity could not be proven from the live inventory.")
    if adoption_status == "verified":
        adoption_status = "adopted"
        notes.append("Verified is projected through verification_status, not as a separate adoption label.")

    return {
        "repo_id": repo_id,
        "role": _role_for_repo(repo_id),
        "repo_identity": repo_identity,
        "contract_version_claimed": contract_version_claimed,
        "adoption_status": adoption_status,
        "verification_state": verification_state,
        "verification_scope": verification_scope or verification_state,
        "verification_status": verification_status if verification_status in VERIFICATION_STATUSES else "unknown",
        "continuity_status": continuity_status,
        "drift_status": drift_status,
        "evidence_types": evidence_types,
        "evidence_refs": sorted({ref for ref in evidence_refs if ref}),
        "initiative_refs": sorted({ref for ref in initiative_refs if isinstance(ref, str) and ref}),
        "blocking_gaps": blocking_gaps,
        "last_verified_at": last_verified_at,
        "notes": notes,
    }


def validate_playbook_adoption_report(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["Adoption report must be a JSON object."]
    for field in ("report_id", "generated_at", "contract_source", "summary", "repos"):
        if field not in payload:
            errors.append(f"Missing top-level field: {field}")
    contract_source = payload.get("contract_source")
    if isinstance(contract_source, dict):
        if contract_source.get("repo_identity") not in {"remote", "local_only", "unknown"}:
            errors.append("contract_source.repo_identity is invalid.")
        if contract_source.get("source_status") not in {"present", "missing", "malformed", "unknown"}:
            errors.append("contract_source.source_status is invalid.")
        if contract_source.get("validation_state") not in {
            "schema_valid",
            "schema_invalid",
            "owner_slice_verified",
            "owner_slice_not_verified",
            "unknown",
        }:
            errors.append("contract_source.validation_state is invalid.")
    repos = payload.get("repos")
    if not isinstance(repos, list):
        errors.append("repos must be an array.")
        return errors
    for index, row in enumerate(repos):
        if not isinstance(row, dict):
            errors.append(f"repos[{index}] must be an object.")
            continue
        if row.get("adoption_status") not in ADOPTION_STATUSES:
            errors.append(f"repos[{index}].adoption_status is invalid.")
        if row.get("verification_state") not in VERIFICATION_STATES:
            errors.append(f"repos[{index}].verification_state is invalid.")
        if row.get("verification_status") not in VERIFICATION_STATUSES:
            errors.append(f"repos[{index}].verification_status is invalid.")
        if row.get("verification_scope") not in {*VERIFICATION_STATES, *VERIFICATION_SCOPE_KINDS}:
            errors.append(f"repos[{index}].verification_scope is invalid.")
        if row.get("continuity_status") not in CONTINUITY_STATES:
            errors.append(f"repos[{index}].continuity_status is invalid.")
        if row.get("drift_status") not in DRIFT_STATES:
            errors.append(f"repos[{index}].drift_status is invalid.")
        if row.get("repo_identity") not in {"remote", "local_only", "unknown"}:
            errors.append(f"repos[{index}].repo_identity is invalid.")
        blocking_gaps = row.get("blocking_gaps")
        if not isinstance(blocking_gaps, list):
            errors.append(f"repos[{index}].blocking_gaps must be an array.")
    return errors


def build_playbook_adoption_report(
    *,
    root: Path | None = None,
    inventory_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    inventory = inventory_payload or build_repo_inventory(root=base_root)
    contract_source = load_playbook_contract_source(root=base_root, inventory_payload=inventory)
    inventory_repos = inventory.get("repos", []) if isinstance(inventory.get("repos"), list) else []
    repo_index = {
        str(item.get("logical_id") or ""): item
        for item in inventory_repos
        if isinstance(item, dict) and str(item.get("logical_id") or "").strip()
    }
    ordered_repo_ids = REPORT_REPO_ORDER + sorted(
        repo_id for repo_id in repo_index.keys() if repo_id not in REPORT_REPO_ORDER
    )
    repos = [
        _repo_row(repo_index[repo_id], contract_source=contract_source, root=base_root)
        for repo_id in ordered_repo_ids
        if repo_id in repo_index
    ]
    identity_counts = Counter(str(row.get("repo_identity") or "unknown") for row in repos)
    status_counts = Counter(str(row.get("adoption_status") or "unassessed") for row in repos)
    verification_counts = Counter(str(row.get("verification_status") or "unknown") for row in repos)
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_id": "playbook_adoption_report_root_projection",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "contract_source": contract_source,
        "summary": {
            "repo_count": len(repos),
            "remote_count": identity_counts.get("remote", 0),
            "local_only_count": identity_counts.get("local_only", 0),
            "unassessed_count": status_counts.get("unassessed", 0),
            "planned_count": status_counts.get("planned", 0),
            "partial_count": status_counts.get("partial", 0),
            "adopted_count": sum(
                1
                for row in repos
                if isinstance(row, dict)
                and str(row.get("adoption_status") or "") == "adopted"
                and str(row.get("verification_status") or "") != "verified"
            ),
            "verified_count": verification_counts.get("verified", 0),
            "exception_count": status_counts.get("exception", 0),
            "verification_missing_count": verification_counts.get("missing", 0),
            "verification_partial_count": verification_counts.get("partial", 0),
            "verification_blocked_count": verification_counts.get("blocked", 0),
        },
        "repos": repos,
    }
    errors = validate_playbook_adoption_report(report)
    if errors:
        raise ValueError("Invalid playbook adoption report: " + "; ".join(errors))
    return report


def build_playbook_status_slices(
    *,
    root: Path | None = None,
    inventory_payload: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    report = build_playbook_adoption_report(root=root, inventory_payload=inventory_payload)
    repos = report.get("repos", []) if isinstance(report.get("repos"), list) else []
    drift_items = [
        row
        for row in repos
        if isinstance(row, dict) and str(row.get("drift_status") or "unknown") != "none_detected"
    ]
    slices = {
        "playbook_contract_status": {
            "item_count": 1,
            "items": [report["contract_source"]],
            "contract_source": report["contract_source"],
        },
        "playbook_adoption_summary": {
            "item_count": 1,
            "items": [report["summary"]],
            "summary": report["summary"],
        },
        "playbook_repo_adoption": {
            "item_count": len(repos),
            "items": repos,
            "summary": report["summary"],
        },
        "playbook_drift": {
            "item_count": len(drift_items),
            "items": drift_items,
            "summary": {
                "item_count": len(drift_items),
                "non_green_repo_ids": [row.get("repo_id") for row in drift_items if isinstance(row, dict)],
            },
        },
    }
    return report, slices
