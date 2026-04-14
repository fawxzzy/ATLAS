from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.observations import (
    GOVERNED_ARTIFACT_EPOCH_LEGACY_PRE_REGISTRY,
    GOVERNED_ARTIFACT_TIME_FIELDS,
    build_observation,
    emit_observation_if_missing,
    governed_artifact_epoch_details,
)
from ops.cortex._artifacts import (
    LEGACY_RUNTIME_BACKFILL_VERSION,
    read_json,
    register_artifact_descriptors,
    sha256_bytes,
    stable_json_digest,
    write_json_if_changed,
)

BACKFILL_TOOL_VERSION = "atlas-legacy-runtime-backfill.v1"


def _optional_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _parse_iso_timestamp(value: Any) -> datetime | None:
    text = _optional_string(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalize_ref(value: Any) -> str | None:
    return _optional_string(value)


def _unique_refs(*values: Any) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for value in values:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped and stripped not in seen:
                seen.add(stripped)
                refs.append(stripped)
        elif isinstance(value, Path):
            stripped = atlas_relative(value, root=atlas_root())
            if stripped and stripped not in seen:
                seen.add(stripped)
                refs.append(stripped)
        elif isinstance(value, list):
            for item in value:
                normalized = _normalize_ref(item)
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    refs.append(normalized)
    return refs


def _load_payload(root: Path, source_ref: str) -> dict[str, Any] | None:
    candidate = (root / Path(source_ref)).resolve()
    if not candidate.exists() or not candidate.is_file():
        return None
    try:
        payload = read_json(candidate)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _source_digest(root: Path, source_ref: str) -> str | None:
    candidate = (root / Path(source_ref)).resolve()
    if not candidate.exists() or not candidate.is_file():
        return None
    try:
        return sha256_bytes(candidate.read_bytes())
    except OSError:
        return None


def _scan_json_refs(base_root: Path, target_root: Path, *, exclude_names: set[str] | None = None) -> list[str]:
    if not target_root.exists():
        return []
    refs: list[str] = []
    for path in sorted(target_root.rglob("*.json")):
        if not path.is_file():
            continue
        if exclude_names and path.name in exclude_names:
            continue
        refs.append(atlas_relative(path, root=base_root))
    return refs


def _legacy_session_manifest_paths(root: Path) -> list[Path]:
    sessions_root = root / "runtime" / "atlas" / "sessions"
    if not sessions_root.exists():
        return []
    paths: list[Path] = []
    for path in sorted(sessions_root.rglob("session.manifest.json")):
        payload = _load_payload(root, atlas_relative(path, root=root))
        if not isinstance(payload, dict):
            continue
        epoch = governed_artifact_epoch_details(payload, source_ref=atlas_relative(path, root=root))
        if not isinstance(epoch, dict) or epoch.get("epoch") != GOVERNED_ARTIFACT_EPOCH_LEGACY_PRE_REGISTRY:
            continue
        paths.append(path.resolve())
    return paths


def _timestamp_candidates(payload: dict[str, Any]) -> list[datetime]:
    candidates: list[datetime] = []
    for field in GOVERNED_ARTIFACT_TIME_FIELDS:
        parsed = _parse_iso_timestamp(payload.get(field))
        if parsed is not None:
            candidates.append(parsed)
    return candidates


def _derived_recorded_at(payloads: list[dict[str, Any]], fallback: str | None) -> str | None:
    timestamps: list[datetime] = []
    for payload in payloads:
        timestamps.extend(_timestamp_candidates(payload))
    if not timestamps:
        return fallback
    latest = max(timestamps)
    return latest.isoformat().replace("+00:00", "Z")


def _session_source_refs(root: Path, session_ref: str, session_payload: dict[str, Any]) -> list[str]:
    session_path = (root / Path(session_ref)).resolve()
    session_root = session_path.parent
    refs = session_payload.get("refs") if isinstance(session_payload.get("refs"), dict) else {}
    completion = session_payload.get("completion") if isinstance(session_payload.get("completion"), dict) else {}
    worker = session_payload.get("worker") if isinstance(session_payload.get("worker"), dict) else {}
    assignment_id = _optional_string(worker.get("assignment_id"))
    session_id = _optional_string(session_payload.get("session_id"))
    lifeline_root = root / "runtime" / "lifeline" / "worker-execution" / assignment_id if assignment_id else None
    supervisor_root = root / "runtime" / "cortex" / "supervisor" / session_id if session_id else None
    return _unique_refs(
        session_ref,
        _scan_json_refs(root, session_root, exclude_names={"status.snapshot.json"}),
        worker.get("context_ref"),
        worker.get("assignment_ref"),
        refs.get("status_refs"),
        refs.get("capability_profile_ref"),
        refs.get("request_ref"),
        refs.get("approval_receipt_ref"),
        refs.get("execution_receipt_ref"),
        refs.get("bridge_record_ref"),
        refs.get("merge_request_refs"),
        refs.get("pause_status_refs"),
        refs.get("resume_context_refs"),
        refs.get("merge_assignment_ref"),
        refs.get("merge_prompt_ref"),
        refs.get("merge_context_ref"),
        refs.get("merge_completion_ref"),
        completion.get("final_status_ref"),
        completion.get("close_receipt_refs"),
        _scan_json_refs(root, lifeline_root, exclude_names=set()) if lifeline_root is not None else [],
        _scan_json_refs(root, supervisor_root, exclude_names=set()) if supervisor_root is not None else [],
    )


def _resolve_scalar(
    candidates: list[tuple[str, str]],
    *,
    field: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    values_by_key: dict[str, list[str]] = {}
    for source_ref, value in candidates:
        values_by_key.setdefault(value, []).append(source_ref)
    basis: dict[str, Any]
    if not values_by_key:
        resolution = {"value": None, "resolution": "unknown_legacy", "basis": []}
        basis = {
            "field": field,
            "resolution": "unknown_legacy",
            "source_refs": [],
            "rationale": "No explicit value was provable from legacy sources.",
        }
        return resolution, basis
    if len(values_by_key) == 1:
        value = next(iter(values_by_key))
        resolution = {
            "value": value,
            "resolution": "provable",
            "basis": sorted(values_by_key[value]),
        }
        basis = {
            "field": field,
            "resolution": "provable",
            "source_refs": sorted(values_by_key[value]),
            "rationale": "All explicit legacy sources agreed on the same value.",
        }
        return resolution, basis
    resolution = {
        "value": None,
        "resolution": "conflict_legacy",
        "basis": sorted({ref for refs in values_by_key.values() for ref in refs}),
        "candidates": [
            {"value": value, "source_refs": sorted(refs)}
            for value, refs in sorted(values_by_key.items(), key=lambda item: item[0])
        ],
    }
    basis = {
        "field": field,
        "resolution": "conflict_legacy",
        "source_refs": resolution["basis"],
        "rationale": "Legacy sources disagreed, so no governed value was inferred.",
    }
    return resolution, basis


def _resolve_surface(
    candidates: list[tuple[str, str, str | None]],
    *,
    field: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    variants: dict[tuple[str, str | None], list[str]] = {}
    for source_ref, tool_id, extension_id in candidates:
        variants.setdefault((tool_id, extension_id), []).append(source_ref)
    if not variants:
        resolution = {
            "tool_id": None,
            "extension_id": None,
            "resolution": "unknown_legacy",
            "basis": [],
        }
        basis = {
            "field": field,
            "resolution": "unknown_legacy",
            "source_refs": [],
            "rationale": "No explicit governed surface identity was provable from legacy sources.",
        }
        return resolution, basis
    if len(variants) == 1:
        (tool_id, extension_id), refs = next(iter(variants.items()))
        resolution = {
            "tool_id": tool_id,
            "extension_id": extension_id,
            "resolution": "provable",
            "basis": sorted(refs),
        }
        basis = {
            "field": field,
            "resolution": "provable",
            "source_refs": sorted(refs),
            "rationale": "All explicit legacy sources agreed on the same governed surface identity.",
        }
        return resolution, basis
    resolution = {
        "tool_id": None,
        "extension_id": None,
        "resolution": "conflict_legacy",
        "basis": sorted({ref for refs in variants.values() for ref in refs}),
        "candidates": [
            {
                "tool_id": tool_id,
                "extension_id": extension_id,
                "source_refs": sorted(refs),
            }
            for (tool_id, extension_id), refs in sorted(variants.items(), key=lambda item: (item[0][0], item[0][1] or ""))
        ],
    }
    basis = {
        "field": field,
        "resolution": "conflict_legacy",
        "source_refs": resolution["basis"],
        "rationale": "Legacy sources disagreed, so no governed surface identity was inferred.",
    }
    return resolution, basis


def _explicit_surface_candidates(source_payloads: list[tuple[str, dict[str, Any]]]) -> dict[str, list[tuple[str, str, str | None]]]:
    context: list[tuple[str, str, str | None]] = []
    supervision: list[tuple[str, str, str | None]] = []
    execution: list[tuple[str, str, str | None]] = []
    registry: list[tuple[str, str]] = []
    for source_ref, payload in source_payloads:
        governed_surfaces = payload.get("governed_surfaces") if isinstance(payload.get("governed_surfaces"), dict) else {}
        for surface_name, target in (
            ("context", context),
            ("supervision", supervision),
            ("execution", execution),
        ):
            surface = governed_surfaces.get(surface_name) if isinstance(governed_surfaces, dict) else None
            if isinstance(surface, dict):
                tool_id = _optional_string(surface.get("tool_id"))
                if tool_id:
                    target.append((source_ref, tool_id, _optional_string(surface.get("extension_id"))))
        governed_registry = _optional_string(governed_surfaces.get("registry_digest")) if isinstance(governed_surfaces, dict) else None
        if governed_registry:
            registry.append((source_ref, governed_registry))

        contract_version = _optional_string(payload.get("contract_version"))
        tool_id = _optional_string(payload.get("tool_id"))
        extension_id = _optional_string(payload.get("extension_id"))
        registry_digest = _optional_string(payload.get("registry_digest"))
        if tool_id and contract_version in {
            "atlas.worker.assignment.v1",
            "atlas.worker.status.v1",
            "atlas.worker.merge-request.v1",
            "atlas.privileged-action.request.v1",
            "atlas.approval.receipt.v1",
            "atlas.privileged-action.receipt.v1",
        }:
            execution.append((source_ref, tool_id, extension_id))
        if registry_digest:
            registry.append((source_ref, registry_digest))
    return {
        "context": context,
        "supervision": supervision,
        "execution": execution,
        "registry": registry,
    }


def _build_backfill_record(root: Path, session_ref: str, session_payload: dict[str, Any]) -> dict[str, Any]:
    epoch = governed_artifact_epoch_details(session_payload, source_ref=session_ref)
    if not isinstance(epoch, dict):
        raise ValueError(f"Unable to classify legacy epoch for {session_ref}.")
    source_refs = _session_source_refs(root, session_ref, session_payload)
    source_payloads = [
        (source_ref, payload)
        for source_ref in source_refs
        if isinstance((payload := _load_payload(root, source_ref)), dict)
    ]
    explicit_candidates = _explicit_surface_candidates(source_payloads)
    context_resolution, context_basis = _resolve_surface(
        explicit_candidates["context"],
        field="governed_identity.context",
    )
    supervision_resolution, supervision_basis = _resolve_surface(
        explicit_candidates["supervision"],
        field="governed_identity.supervision",
    )
    execution_resolution, execution_basis = _resolve_surface(
        explicit_candidates["execution"],
        field="governed_identity.execution",
    )
    registry_resolution, registry_basis = _resolve_scalar(
        explicit_candidates["registry"],
        field="governed_identity.registry_digest",
    )
    worker = session_payload.get("worker") if isinstance(session_payload.get("worker"), dict) else {}
    completion = session_payload.get("completion") if isinstance(session_payload.get("completion"), dict) else {}
    recorded_at = _derived_recorded_at([payload for _, payload in source_payloads], epoch.get("observed_at"))
    source_ref_digests = [
        {"source_ref": source_ref, "digest": digest}
        for source_ref in source_refs
        if (digest := _source_digest(root, source_ref))
    ]
    record: dict[str, Any] = {
        "contract_version": LEGACY_RUNTIME_BACKFILL_VERSION,
        "record_type": "legacy_runtime_session",
        "tool_version": BACKFILL_TOOL_VERSION,
        "backfill_status": "backfilled",
        "compatibility_class": GOVERNED_ARTIFACT_EPOCH_LEGACY_PRE_REGISTRY,
        "cutover_at": epoch.get("cutover_at"),
        "observed_at": epoch.get("observed_at"),
        "recorded_at": recorded_at,
        "session_id": _optional_string(session_payload.get("session_id")) or session_ref,
        "task_id": _optional_string(session_payload.get("task_id")),
        "session_state": _optional_string(session_payload.get("session_state")) or "unknown",
        "final_status": _optional_string(completion.get("final_status")),
        "original_session_ref": session_ref,
        "original_contract_version": _optional_string(session_payload.get("contract_version")),
        "source_refs": source_refs,
        "source_ref_count": len(source_refs),
        "source_ref_digests": source_ref_digests,
        "missing_governed_requirements": epoch.get("missing_requirements", []),
        "worker": {
            "worker_id": _optional_string(worker.get("worker_id")),
            "assignment_id": _optional_string(worker.get("assignment_id")),
        },
        "governed_identity": {
            "registry_digest": registry_resolution,
            "context": context_resolution,
            "supervision": supervision_resolution,
            "execution": execution_resolution,
        },
        "inference_basis": sorted(
            [context_basis, supervision_basis, execution_basis, registry_basis],
            key=lambda item: str(item.get("field", "")),
        ),
    }
    record["backfill_id"] = stable_json_digest(record)
    return record


def backfill_legacy_runtime_artifacts(
    *,
    root: Path | None = None,
    output_dir: Path | None = None,
    descriptor_root: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    resolved_output_dir = (output_dir or (base_root / "runtime" / "state" / "atlas" / "legacy-backfill")).resolve()
    resolved_descriptor_root = (descriptor_root or (base_root / "runtime" / "cortex" / "artifacts")).resolve()
    session_paths = _legacy_session_manifest_paths(base_root)
    written_records: list[str] = []
    updated_records: list[str] = []
    records: list[dict[str, Any]] = []

    for session_path in session_paths:
        session_ref = atlas_relative(session_path, root=base_root)
        session_payload = _load_payload(base_root, session_ref)
        if not isinstance(session_payload, dict):
            continue
        record = _build_backfill_record(base_root, session_ref, session_payload)
        records.append(record)
        target_path = resolved_output_dir / f"{str(record['session_id']).strip()}.json"
        if not dry_run:
            changed = write_json_if_changed(target_path, record)
            written_records.append(atlas_relative(target_path, root=base_root))
            if changed:
                updated_records.append(atlas_relative(target_path, root=base_root))
            emit_observation_if_missing(
                build_observation(
                    observation_type="governed_compatibility",
                    source_kind="legacy_backfill",
                    status="backfilled",
                    observed_at=record.get("recorded_at"),
                    source_ref=atlas_relative(target_path, root=base_root),
                    scope_ref=str(record.get("session_id")),
                    details={
                        "compatibility_class": record.get("compatibility_class"),
                        "original_session_ref": record.get("original_session_ref"),
                        "missing_governed_requirements": record.get("missing_governed_requirements", []),
                        "source_refs": record.get("source_refs", []),
                    },
                ),
                owner="legacy-backfill",
                root=base_root,
            )

    registered = []
    if not dry_run and resolved_output_dir.exists():
        registered = register_artifact_descriptors(
            [resolved_output_dir],
            output_dir=resolved_descriptor_root,
            root=base_root,
        )

    return {
        "tool_version": BACKFILL_TOOL_VERSION,
        "record_count": len(records),
        "written_record_refs": written_records,
        "updated_record_refs": updated_records,
        "registered_descriptor_count": len(registered),
        "registered_descriptors": registered,
        "compatibility_class": GOVERNED_ARTIFACT_EPOCH_LEGACY_PRE_REGISTRY,
        "dry_run": dry_run,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill descriptor-backed legacy runtime compatibility records.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--descriptor-root", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    result = backfill_legacy_runtime_artifacts(
        root=args.root.resolve(),
        output_dir=args.output_dir.resolve() if args.output_dir else None,
        descriptor_root=args.descriptor_root.resolve() if args.descriptor_root else None,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
