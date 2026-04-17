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

    verification_state = str(summary.get("verification_state") or "").strip()
    if verification_state not in VERIFICATION_STATES:
        verification_state = "unknown"

    continuity_status = str(summary.get("continuity_status") or "").strip()
    if continuity_status not in CONTINUITY_STATES:
        continuity_status = "unknown"

    drift_status = str(summary.get("drift_status") or "").strip()
    if drift_status not in DRIFT_STATES:
        drift_status = "unknown"

    initiative_refs = [
        str(ref)
        for ref in summary.get("initiative_refs", [])
        if isinstance(ref, str) and str(ref).strip()
    ]

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
    continuity_status = "unknown"
    drift_status = "unknown"
    contract_version_claimed: str | None = None
    repo_adoption = _load_repo_adoption_projection(root=root, repo_entry=repo_entry)

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

    return {
        "repo_id": repo_id,
        "role": _role_for_repo(repo_id),
        "repo_identity": repo_identity,
        "contract_version_claimed": contract_version_claimed,
        "adoption_status": adoption_status,
        "verification_state": verification_state,
        "continuity_status": continuity_status,
        "drift_status": drift_status,
        "evidence_types": evidence_types,
        "evidence_refs": sorted({ref for ref in evidence_refs if ref}),
        "initiative_refs": sorted({ref for ref in initiative_refs if isinstance(ref, str) and ref}),
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
        if row.get("continuity_status") not in CONTINUITY_STATES:
            errors.append(f"repos[{index}].continuity_status is invalid.")
        if row.get("drift_status") not in DRIFT_STATES:
            errors.append(f"repos[{index}].drift_status is invalid.")
        if row.get("repo_identity") not in {"remote", "local_only", "unknown"}:
            errors.append(f"repos[{index}].repo_identity is invalid.")
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
            "adopted_count": status_counts.get("adopted", 0),
            "verified_count": status_counts.get("verified", 0),
            "exception_count": status_counts.get("exception", 0),
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
