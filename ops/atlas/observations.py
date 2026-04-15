from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.load_tool_registry import load_tool_registry_bundle
from ops.cortex._artifacts import stable_json_digest, write_json

OBSERVATION_CONTRACT_VERSION = "atlas.observation.v1"
GOVERNED_ARTIFACT_EPOCH_LEGACY_PRE_REGISTRY = "legacy_pre_registry"
GOVERNED_ARTIFACT_EPOCH_GOVERNED_V1 = "governed_v1"
GOVERNED_ARTIFACT_REGISTRY_CUTOVER = "2026-04-14T08:06:53Z"
GOVERNED_ARTIFACT_TIMESTAMP_PATTERN = re.compile(r"(20\d{6}T\d{6}Z)", re.IGNORECASE)
GOVERNED_ARTIFACT_TIME_FIELDS = (
    "created_at",
    "updated_at",
    "closed_at",
    "requested_at",
    "issued_at",
    "executed_at",
    "heartbeat_at",
    "recorded_at",
)
GOVERNED_SURFACE_CONTRACT_VERSIONS = {
    "atlas.worker.assignment.v1",
    "atlas.worker.status.v1",
    "atlas.worker.merge-request.v1",
    "atlas.privileged-action.request.v1",
    "atlas.approval.receipt.v1",
    "atlas.privileged-action.receipt.v1",
}
LEGACY_OBSERVATION_TYPE_ALIASES = {
    "assignment.created": "assignment_created",
    "execution.requested": "execution_requested",
    "execution.completed": "execution_completed",
    "execution.result": "execution_completed",
    "session.merge_requested": "merge_requested",
    "worker.paused": "paused",
    "session.resume_ready": "resume_ready",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stamp_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def stable_item_id(payload: dict[str, Any]) -> str:
    return stable_json_digest(payload)


def _optional_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _parse_iso_timestamp(value: str | None) -> datetime | None:
    text = _optional_string(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_embedded_timestamp(value: str | None) -> datetime | None:
    text = _optional_string(value)
    if not text:
        return None
    match = GOVERNED_ARTIFACT_TIMESTAMP_PATTERN.search(text)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1).upper(), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def governed_artifact_cutover_datetime() -> datetime:
    parsed = _parse_iso_timestamp(GOVERNED_ARTIFACT_REGISTRY_CUTOVER)
    if parsed is None:
        raise ValueError("GOVERNED_ARTIFACT_REGISTRY_CUTOVER must be a valid ISO timestamp.")
    return parsed


def _non_empty_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _session_missing_governed_requirements(payload: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    governed_surfaces = payload.get("governed_surfaces")
    if not isinstance(governed_surfaces, dict):
        return [
            "governed_surfaces.registry_digest",
            "governed_surfaces.context.tool_id",
            "governed_surfaces.supervision.tool_id",
            "governed_surfaces.execution.tool_id",
            "worker.assignment_ref",
            "refs.status_refs",
            "refs.request_ref",
            "refs.approval_receipt_ref",
            "refs.execution_receipt_ref",
            "completion.final_status",
            "completion.final_status_ref",
            "completion.close_receipt_refs",
        ]

    if not _optional_string(governed_surfaces.get("registry_digest")):
        missing.append("governed_surfaces.registry_digest")
    for scope_name in ("context", "supervision", "execution"):
        scope = governed_surfaces.get(scope_name)
        if not isinstance(scope, dict) or not _optional_string(scope.get("tool_id")):
            missing.append(f"governed_surfaces.{scope_name}.tool_id")

    worker = payload.get("worker") if isinstance(payload.get("worker"), dict) else {}
    refs = payload.get("refs") if isinstance(payload.get("refs"), dict) else {}
    completion = payload.get("completion") if isinstance(payload.get("completion"), dict) else {}

    if not (_optional_string(worker.get("assignment_ref")) or _optional_string(refs.get("assignment_ref"))):
        missing.append("worker.assignment_ref")
    if not _non_empty_string_list(refs.get("status_refs")):
        missing.append("refs.status_refs")
    if not _optional_string(refs.get("request_ref")):
        missing.append("refs.request_ref")
    if not _optional_string(refs.get("approval_receipt_ref")):
        missing.append("refs.approval_receipt_ref")
    if not _optional_string(refs.get("execution_receipt_ref")):
        missing.append("refs.execution_receipt_ref")

    final_status = _optional_string(completion.get("final_status"))
    if not final_status:
        missing.append("completion.final_status")
    if not _optional_string(completion.get("final_status_ref")):
        missing.append("completion.final_status_ref")
    if final_status in {None, "completed", "failed", "resume_ready"} and not _non_empty_string_list(
        completion.get("close_receipt_refs")
    ):
        missing.append("completion.close_receipt_refs")
    return missing


def _surface_missing_governed_requirements(payload: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if not _optional_string(payload.get("tool_id")):
        missing.append("tool_id")
    if not _optional_string(payload.get("registry_digest")):
        missing.append("registry_digest")
    return missing


def governed_artifact_epoch_details(
    payload: dict[str, Any],
    *,
    source_ref: str | None = None,
) -> dict[str, Any] | None:
    contract_version = _optional_string(payload.get("contract_version"))
    if contract_version == "atlas.session.v1":
        missing_requirements = _session_missing_governed_requirements(payload)
    elif contract_version in GOVERNED_SURFACE_CONTRACT_VERSIONS:
        missing_requirements = _surface_missing_governed_requirements(payload)
    else:
        return None

    observed_at = None
    for field in GOVERNED_ARTIFACT_TIME_FIELDS:
        observed_at = _parse_iso_timestamp(_optional_string(payload.get(field)))
        if observed_at is not None:
            break
    if observed_at is None:
        observed_at = _parse_embedded_timestamp(source_ref)
    if observed_at is None:
        observed_at = _parse_embedded_timestamp(_optional_string(payload.get("session_id")))
    if observed_at is None:
        observed_at = _parse_embedded_timestamp(_optional_string(payload.get("assignment_id")))

    cutover_at = governed_artifact_cutover_datetime()
    predates_cutover = observed_at is not None and observed_at < cutover_at
    epoch = (
        GOVERNED_ARTIFACT_EPOCH_LEGACY_PRE_REGISTRY
        if predates_cutover and bool(missing_requirements)
        else GOVERNED_ARTIFACT_EPOCH_GOVERNED_V1
    )
    return {
        "epoch": epoch,
        "contract_version": contract_version,
        "cutover_at": GOVERNED_ARTIFACT_REGISTRY_CUTOVER,
        "observed_at": observed_at.isoformat().replace("+00:00", "Z") if observed_at else None,
        "predates_cutover": predates_cutover,
        "missing_requirements": missing_requirements,
    }


def canonical_observation_type(
    observation_type: str,
    *,
    status: str | None = None,
) -> str:
    raw_type = str(observation_type or "").strip()
    raw_status = str(status or "").strip().lower()
    if raw_type == "execution.approval":
        if raw_status == "expired":
            return "execution_expired"
        if raw_status == "rejected":
            return "execution_rejected"
        return "execution_approved"
    return LEGACY_OBSERVATION_TYPE_ALIASES.get(raw_type, raw_type)


def observation_matches_type(
    observation: dict[str, Any],
    expected_type: str,
) -> bool:
    return canonical_observation_type(
        str(observation.get("observation_type", "")),
        status=str(observation.get("status", "")),
    ) == expected_type


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower()).strip("-")
    return cleaned or "scope"


def _stable_segment(value: str) -> str:
    slug = _slugify(value)
    if len(slug) <= 48:
        return slug
    digest = stable_json_digest({"value": value}).replace("sha256:", "")[:12]
    return f"{slug[:35]}-{digest}"


def observation_state_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "state" / "atlas" / "observations"


def build_observation(
    *,
    observation_type: str,
    source_kind: str,
    status: str,
    source_ref: str,
    observed_at: str | None,
    scope_ref: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = {
        "contract_version": OBSERVATION_CONTRACT_VERSION,
        "observation_type": observation_type,
        "source_kind": source_kind,
        "status": status,
        "observed_at": observed_at,
        "source_ref": source_ref,
        "scope_ref": scope_ref,
        "details": details or {},
    }
    return {
        **base,
        "observation_id": stable_item_id(base),
    }


def observation_directory(
    observation: dict[str, Any],
    *,
    owner: str,
    root: Path | None = None,
) -> Path:
    base = observation_state_root(root)
    scope_value = (
        str(observation.get("scope_ref"))
        if isinstance(observation.get("scope_ref"), str) and str(observation.get("scope_ref")).strip()
        else str(observation.get("source_ref") or observation.get("observation_id") or "scope")
    )
    source_value = str(observation.get("source_ref") or observation.get("observation_id") or "source")
    return (
        base
        / _stable_segment(owner)
        / _stable_segment(str(observation.get("observation_type", "observation")))
        / _stable_segment(scope_value)
        / _stable_segment(source_value)
    )


def emit_observation(
    observation: dict[str, Any],
    *,
    owner: str,
    root: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    target_dir = observation_directory(observation, owner=owner, root=base_root)
    latest_path = target_dir / "latest.json"
    stamped_path = target_dir / f"{stamp_now()}-{str(observation['observation_id']).replace('sha256:', '')[:16]}.json"

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        write_json(stamped_path, observation)
        write_json(latest_path, observation)

    return {
        "observation_id": observation["observation_id"],
        "source_ref": observation["source_ref"],
        "latest_ref": atlas_relative(latest_path, root=base_root),
        "receipt_ref": atlas_relative(stamped_path, root=base_root),
        "owner": owner,
    }


def emit_observation_if_missing(
    observation: dict[str, Any],
    *,
    owner: str,
    root: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any] | None:
    observation_id = str(observation.get("observation_id", "")).strip()
    if not observation_id:
        return None
    if observation_id in emitted_observation_ids(root):
        return None
    return emit_observation(
        observation,
        owner=owner,
        root=root,
        dry_run=dry_run,
    )


def iter_observation_paths(root: Path | None = None) -> list[Path]:
    base = observation_state_root(root)
    if not base.exists():
        return []
    return sorted(path.resolve() for path in base.rglob("latest.json") if path.is_file())


def load_observations(root: Path | None = None) -> list[dict[str, Any]]:
    base_root = (root or atlas_root()).resolve()
    observations: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for path in iter_observation_paths(base_root):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("contract_version") != OBSERVATION_CONTRACT_VERSION:
            continue
        observation_id = str(payload.get("observation_id", "")).strip()
        if not observation_id or observation_id in seen_ids:
            continue
        seen_ids.add(observation_id)
        observations.append(payload)
    observations.sort(
        key=lambda item: (
            str(item.get("observation_type", "")),
            str(item.get("source_ref", "")),
            str(item.get("status", "")),
        )
    )
    return observations


def emitted_observation_ids(root: Path | None = None) -> set[str]:
    return {
        str(item.get("observation_id"))
        for item in load_observations(root)
        if isinstance(item.get("observation_id"), str)
    }


def _parse_details_json(value: str) -> dict[str, Any]:
    if not value.strip():
        return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("Observation details must decode to a JSON object.")
    return parsed


def _iter_json_paths(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path.resolve() for path in root.rglob("*.json") if path.is_file())


def _execution_receipt_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "lifeline" / "worker-execution"


def load_execution_receipt_payloads(root: Path | None = None) -> dict[str, dict[str, Any]]:
    base_root = (root or atlas_root()).resolve()
    results: dict[str, dict[str, Any]] = {}
    for path in _iter_json_paths(_execution_receipt_root(base_root)):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("contract_version") != "atlas.privileged-action.receipt.v1":
            continue
        results[atlas_relative(path, root=base_root)] = payload
    return results


def _current_registry_digest(root: Path | None = None) -> str | None:
    try:
        bundle = load_tool_registry_bundle(root=(root or atlas_root()).resolve())
    except Exception:
        return None
    digest = _optional_string(bundle.get("registry_digest"))
    return digest


def _is_truthful_superseding_receipt(
    payload: dict[str, Any],
    *,
    source_ref: str,
    current_registry_digest: str | None,
) -> bool:
    repair_basis_refs = payload.get("repair_basis_refs")
    return (
        current_registry_digest is not None
        and _optional_string(payload.get("registry_digest")) == current_registry_digest
        and _optional_string(payload.get("supersedes_receipt_ref")) == source_ref
        and isinstance(repair_basis_refs, list)
        and any(isinstance(item, str) and item.strip() for item in repair_basis_refs)
        and _optional_string(payload.get("reconciled_at")) is not None
        and _optional_string(payload.get("reconciled_by_tool_version")) is not None
    )


def execution_receipt_supersession_index(root: Path | None = None) -> dict[str, dict[str, Any]]:
    receipts = load_execution_receipt_payloads(root)
    current_registry_digest = _current_registry_digest(root)
    superseders: dict[str, list[dict[str, Any]]] = {}
    for source_ref, payload in receipts.items():
        supersedes_ref = _optional_string(payload.get("supersedes_receipt_ref"))
        if not supersedes_ref:
            continue
        superseders.setdefault(supersedes_ref, []).append(
            {
                "source_ref": source_ref,
                "payload": payload,
                "reconciled_at": _optional_string(payload.get("reconciled_at")),
                "executed_at": _optional_string(payload.get("executed_at")),
            }
        )

    selected: dict[str, dict[str, Any]] = {}
    for source_ref, candidates in superseders.items():
        truthful_candidates = [
            item
            for item in candidates
            if _is_truthful_superseding_receipt(
                item["payload"],
                source_ref=source_ref,
                current_registry_digest=current_registry_digest,
            )
        ]
        if not truthful_candidates:
            continue
        candidates = truthful_candidates
        candidates.sort(
            key=lambda item: (
                item.get("reconciled_at") or "",
                item.get("executed_at") or "",
                item.get("source_ref") or "",
            )
        )
        selected[source_ref] = candidates[-1]
    return selected


def resolve_preferred_execution_receipt_ref(
    source_ref: str | None,
    *,
    root: Path | None = None,
) -> str | None:
    current = _optional_string(source_ref)
    if not current:
        return None
    supersession_index = execution_receipt_supersession_index(root)
    seen: set[str] = set()
    while current not in seen:
        seen.add(current)
        candidate = supersession_index.get(current)
        if not isinstance(candidate, dict):
            return current
        next_ref = _optional_string(candidate.get("source_ref"))
        if not next_ref:
            return current
        current = next_ref
    return current


def execution_receipt_residue_records(root: Path | None = None) -> list[dict[str, Any]]:
    receipts = load_execution_receipt_payloads(root)
    current_registry_digest = _current_registry_digest(root)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for source_ref, payload in receipts.items():
        supersedes_ref = _optional_string(payload.get("supersedes_receipt_ref"))
        if not supersedes_ref:
            continue
        grouped.setdefault(supersedes_ref, []).append(
            {
                "source_ref": source_ref,
                "payload": payload,
                "reconciled_at": _optional_string(payload.get("reconciled_at")),
                "executed_at": _optional_string(payload.get("executed_at")),
            }
        )

    residue: list[dict[str, Any]] = []
    for original_ref, candidates in grouped.items():
        ordered = sorted(
            candidates,
            key=lambda item: (
                item.get("reconciled_at") or "",
                item.get("executed_at") or "",
                item.get("source_ref") or "",
            ),
        )
        canonical: dict[str, Any] | None = None
        truthful_candidates = [
            item
            for item in ordered
            if _is_truthful_superseding_receipt(
                item["payload"],
                source_ref=original_ref,
                current_registry_digest=current_registry_digest,
            )
        ]
        if truthful_candidates:
            canonical = truthful_candidates[-1]

        canonical_source_ref = (
            _optional_string(canonical.get("source_ref")) if isinstance(canonical, dict) else None
        ) or original_ref
        for candidate in ordered:
            candidate_source_ref = _optional_string(candidate.get("source_ref"))
            if not candidate_source_ref:
                continue
            if canonical is not None and candidate_source_ref == canonical_source_ref:
                continue
            status = (
                "superseded_residue"
                if _is_truthful_superseding_receipt(
                    candidate["payload"],
                    source_ref=original_ref,
                    current_registry_digest=current_registry_digest,
                )
                else "retained_residue"
            )
            residue.append(
                {
                    "source_ref": candidate_source_ref,
                    "supersedes_receipt_ref": original_ref,
                    "canonical_source_ref": canonical_source_ref,
                    "status": status,
                    "registry_digest": candidate["payload"].get("registry_digest"),
                    "reconciled_at": candidate["payload"].get("reconciled_at"),
                    "reconciled_by_tool_version": candidate["payload"].get("reconciled_by_tool_version"),
                }
            )
    residue.sort(
        key=lambda item: (
            str(item.get("supersedes_receipt_ref", "")),
            str(item.get("status", "")),
            str(item.get("source_ref", "")),
        )
    )
    return residue


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ATLAS observation helpers.")
    subparsers = parser.add_subparsers(dest="command")

    emit_parser = subparsers.add_parser("emit", help="Emit one atlas.observation.v1 record.")
    emit_parser.add_argument("--owner", required=True)
    emit_parser.add_argument("--root", type=Path, default=atlas_root())
    emit_parser.add_argument("--observation-type", required=True)
    emit_parser.add_argument("--source-kind", required=True)
    emit_parser.add_argument("--status", required=True)
    emit_parser.add_argument("--source-ref", required=True)
    emit_parser.add_argument("--observed-at")
    emit_parser.add_argument("--scope-ref")
    emit_parser.add_argument("--details-json", default="{}")
    emit_parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    if args.command != "emit":
        parser.print_help(sys.stderr)
        return 1

    details = _parse_details_json(args.details_json)
    observation = build_observation(
        observation_type=args.observation_type,
        source_kind=args.source_kind,
        status=args.status,
        source_ref=args.source_ref,
        observed_at=args.observed_at,
        scope_ref=args.scope_ref,
        details=details,
    )
    result = emit_observation(
        observation,
        owner=args.owner,
        root=args.root.resolve(),
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
