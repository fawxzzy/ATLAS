from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, resolve_atlas_path
from ops.cortex._artifacts import write_json_if_changed
from ops.cortex.index_working_memory import MEMORY_KIND_CONFIG, normalize_working_memory_document, write_working_memory_catalog


def parse_iso(value: str | None) -> datetime:
    if not isinstance(value, str) or not value.strip():
        return datetime.fromtimestamp(0, tz=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def slugify(value: str) -> str:
    slug = "".join(character.lower() if character.isalnum() else "-" for character in value.strip())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "memory"


def humanize_task(value: str) -> str:
    parts = [part for part in value.replace("_", "-").split("-") if part]
    return " ".join(part.capitalize() for part in parts) or value


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}.")
    return payload


def session_manifest_path(*, root: Path, session_id: str | None, session_ref: str | None) -> Path:
    if session_ref:
        return resolve_atlas_path(session_ref, root=root)
    if not session_id:
        raise ValueError("Provide --session-id or --session-ref.")
    candidate = root / "runtime" / "atlas" / "sessions" / session_id / "session.manifest.json"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"Unknown session manifest for session_id '{session_id}'.")


def all_session_manifests(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    manifests: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted((root / "runtime" / "atlas" / "sessions").rglob("session.manifest.json")):
        try:
            manifests.append((path, load_json(path)))
        except Exception:
            continue
    return manifests


def unique_strings(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        ordered.append(stripped)
    return ordered


def session_related_refs(manifest: dict[str, Any], *, session_ref: str, status_snapshot_ref: str | None) -> tuple[list[str], list[str]]:
    refs = manifest.get("refs") if isinstance(manifest.get("refs"), dict) else {}
    completion = manifest.get("completion") if isinstance(manifest.get("completion"), dict) else {}
    related_artifact_refs = unique_strings(
        [
            refs.get("request_ref"),
            refs.get("approval_receipt_ref"),
            refs.get("execution_receipt_ref"),
            refs.get("bridge_record_ref"),
            refs.get("merge_assignment_ref"),
            refs.get("merge_prompt_ref"),
            refs.get("merge_context_ref"),
            refs.get("merge_completion_ref"),
            *refs.get("status_refs", []),
            *refs.get("merge_request_refs", []),
            *refs.get("pause_status_refs", []),
            *refs.get("resume_context_refs", []),
            *completion.get("close_receipt_refs", []),
        ]
    )
    evidence_refs = unique_strings(
        [
            session_ref,
            status_snapshot_ref,
            completion.get("final_status_ref"),
            *completion.get("close_receipt_refs", []),
        ]
    )
    return related_artifact_refs, evidence_refs


def session_status(session_payload: dict[str, Any]) -> str:
    completion = session_payload.get("completion") if isinstance(session_payload.get("completion"), dict) else {}
    final_status = str(completion.get("final_status") or "").strip()
    if final_status:
        return final_status
    return str(session_payload.get("session_state") or "active")


def base_memory_payload(
    *,
    contract_version: str,
    memory_id: str,
    title: str,
    summary: str,
    status: str,
    created_at: str,
    updated_at: str,
    related_session_refs: list[str],
    related_artifact_refs: list[str],
    evidence_refs: list[str],
    metadata: dict[str, Any],
    existing: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "contract_version": contract_version,
        "id": memory_id,
        "title": title,
        "summary": summary,
        "status": status,
        "owner": "stack-root",
        "created_at": str(existing.get("created_at")) if isinstance(existing, dict) and existing.get("created_at") else created_at,
        "updated_at": updated_at,
        "related_session_refs": related_session_refs,
        "related_artifact_refs": related_artifact_refs,
        "evidence_refs": evidence_refs,
        "supersedes": existing.get("supersedes", []) if isinstance(existing, dict) and isinstance(existing.get("supersedes"), list) else [],
        "superseded_by": existing.get("superseded_by", []) if isinstance(existing, dict) and isinstance(existing.get("superseded_by"), list) else [],
        "metadata": metadata,
    }


def read_existing_memory(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return load_json(path)
    except Exception:
        return None


def author_plan(
    *,
    manifest: dict[str, Any],
    session_ref: str,
    status_snapshot_ref: str | None,
    path: Path,
) -> dict[str, Any]:
    task_id = str(manifest.get("task_id") or manifest.get("session_id") or "session")
    session_id = str(manifest.get("session_id") or task_id)
    related_artifact_refs, evidence_refs = session_related_refs(manifest, session_ref=session_ref, status_snapshot_ref=status_snapshot_ref)
    existing = read_existing_memory(path)
    memory_id = f"plan-{slugify(task_id)}"
    title = f"{humanize_task(task_id)} Plan"
    summary = (
        f"Carry forward the governed {task_id} objective with durable provenance from session {session_id} instead of transcript-only closure."
    )
    status = "active" if session_status(manifest) in {"created", "context_built", "assignment_emitted", "executing", "execution_recorded", "resume_ready"} else "completed"
    payload = base_memory_payload(
        contract_version="atlas.plan.v1",
        memory_id=memory_id,
        title=title,
        summary=summary,
        status=status,
        created_at=str(manifest.get("created_at") or manifest.get("updated_at")),
        updated_at=str(manifest.get("updated_at") or manifest.get("closed_at") or manifest.get("created_at")),
        related_session_refs=[session_ref],
        related_artifact_refs=related_artifact_refs,
        evidence_refs=evidence_refs,
        metadata={
            "authoring_source": "session-closure",
            "task_id": task_id,
            "session_id": session_id,
            "scenario": manifest.get("scenario"),
            "final_status": session_status(manifest),
        },
        existing=existing,
    )
    normalize_working_memory_document(payload, memory_kind="plan", relative_path=atlas_relative(path, root=ROOT))
    return payload


def author_decision(
    *,
    manifest: dict[str, Any],
    session_ref: str,
    status_snapshot_ref: str | None,
    path: Path,
) -> dict[str, Any]:
    task_id = str(manifest.get("task_id") or manifest.get("session_id") or "session")
    session_id = str(manifest.get("session_id") or task_id)
    related_artifact_refs, evidence_refs = session_related_refs(manifest, session_ref=session_ref, status_snapshot_ref=status_snapshot_ref)
    existing = read_existing_memory(path)
    final_status = session_status(manifest)
    payload = base_memory_payload(
        contract_version="atlas.decision.v1",
        memory_id=f"decision-{slugify(session_id)}",
        title=f"{humanize_task(task_id)} Decision",
        summary=(
            f"Session {session_id} established a governed closure record for {task_id} with final status '{final_status}'."
        ),
        status="accepted" if final_status == "completed" else "proposed",
        created_at=str(manifest.get("closed_at") or manifest.get("updated_at") or manifest.get("created_at")),
        updated_at=str(manifest.get("closed_at") or manifest.get("updated_at") or manifest.get("created_at")),
        related_session_refs=[session_ref],
        related_artifact_refs=related_artifact_refs,
        evidence_refs=evidence_refs,
        metadata={
            "authoring_source": "session-closure",
            "decision_type": "session-closure",
            "task_id": task_id,
            "session_id": session_id,
            "scenario": manifest.get("scenario"),
            "final_status": final_status,
        },
        existing=existing,
    )
    normalize_working_memory_document(payload, memory_kind="decision", relative_path=atlas_relative(path, root=ROOT))
    return payload


def author_initiative(
    *,
    root: Path,
    manifest: dict[str, Any],
    path: Path,
) -> dict[str, Any] | None:
    task_id = str(manifest.get("task_id") or manifest.get("session_id") or "session")
    clustered = [
        (candidate_path, candidate)
        for candidate_path, candidate in all_session_manifests(root)
        if str(candidate.get("task_id") or "") == task_id
    ]
    if len(clustered) < 2:
        return None
    sorted_cluster = sorted(
        clustered,
        key=lambda item: (
            parse_iso(str(item[1].get("updated_at") or item[1].get("created_at"))),
            str(item[1].get("session_id") or ""),
        ),
    )
    related_session_refs = [
        atlas_relative(item[0], root=root)
        for item in sorted_cluster
    ]
    related_artifact_refs = unique_strings(
        [
            ref
            for _, candidate in sorted_cluster
            for ref in (
                (candidate.get("completion") if isinstance(candidate.get("completion"), dict) else {}).get("close_receipt_refs", [])
            )
        ]
    )
    created_at = str(sorted_cluster[0][1].get("created_at") or sorted_cluster[0][1].get("updated_at"))
    updated_at = str(sorted_cluster[-1][1].get("updated_at") or sorted_cluster[-1][1].get("created_at"))
    status_counts = Counter(session_status(candidate) for _, candidate in sorted_cluster)
    existing = read_existing_memory(path)
    payload = base_memory_payload(
        contract_version="atlas.initiative.v1",
        memory_id=f"initiative-{slugify(task_id)}",
        title=f"{humanize_task(task_id)} Initiative",
        summary=(
            f"Cluster repeated governed sessions under the shared {task_id} objective so progress survives across session boundaries."
        ),
        status="active" if status_counts.get("completed", 0) != len(sorted_cluster) else "completed",
        created_at=created_at,
        updated_at=updated_at,
        related_session_refs=related_session_refs,
        related_artifact_refs=related_artifact_refs,
        evidence_refs=unique_strings([related_session_refs[-1], *related_artifact_refs]),
        metadata={
            "authoring_source": "session-cluster",
            "task_id": task_id,
            "session_count": len(sorted_cluster),
            "status_counts": dict(sorted(status_counts.items())),
        },
        existing=existing,
    )
    normalize_working_memory_document(payload, memory_kind="initiative", relative_path=atlas_relative(path, root=ROOT))
    return payload


def author_hypothesis(
    *,
    manifest: dict[str, Any],
    session_ref: str,
    status_snapshot_ref: str | None,
    path: Path,
) -> dict[str, Any] | None:
    final_status = session_status(manifest)
    if final_status == "completed":
        return None
    task_id = str(manifest.get("task_id") or manifest.get("session_id") or "session")
    session_id = str(manifest.get("session_id") or task_id)
    related_artifact_refs, evidence_refs = session_related_refs(manifest, session_ref=session_ref, status_snapshot_ref=status_snapshot_ref)
    existing = read_existing_memory(path)
    payload = base_memory_payload(
        contract_version="atlas.hypothesis.v1",
        memory_id=f"hypothesis-{slugify(task_id)}",
        title=f"{humanize_task(task_id)} Hypothesis",
        summary=(
            f"Session {session_id} remains unresolved with final status '{final_status}', so the next operator pass should test the recorded resume and closure evidence rather than recreating private state."
        ),
        status="active",
        created_at=str(manifest.get("updated_at") or manifest.get("created_at")),
        updated_at=str(manifest.get("updated_at") or manifest.get("created_at")),
        related_session_refs=[session_ref],
        related_artifact_refs=related_artifact_refs,
        evidence_refs=evidence_refs,
        metadata={
            "authoring_source": "session-unresolved",
            "task_id": task_id,
            "session_id": session_id,
            "final_status": final_status,
            "resume_context_refs": (manifest.get("refs") if isinstance(manifest.get("refs"), dict) else {}).get("resume_context_refs", []),
        },
        existing=existing,
    )
    normalize_working_memory_document(payload, memory_kind="hypothesis", relative_path=atlas_relative(path, root=ROOT))
    return payload


def write_payload(path: Path, payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    changed = write_json_if_changed(path, payload)
    return {
        "path": atlas_relative(path, root=ROOT),
        "id": payload["id"],
        "changed": changed,
        "memory_kind": payload["contract_version"].split(".")[1],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Author deterministic ATLAS working-memory artifacts from governed session state.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--session-id")
    parser.add_argument("--session-ref")
    parser.add_argument("--memory-kind", action="append", choices=["plan", "decision", "initiative", "hypothesis"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    manifest_path = session_manifest_path(root=root, session_id=args.session_id, session_ref=args.session_ref)
    manifest = load_json(manifest_path)
    session_ref = atlas_relative(manifest_path, root=root)
    status_snapshot_path = manifest_path.parent / "status.snapshot.json"
    status_snapshot_ref = atlas_relative(status_snapshot_path, root=root) if status_snapshot_path.exists() else None
    requested_kinds = args.memory_kind or ["plan", "decision", "initiative", "hypothesis"]

    outputs: list[dict[str, Any]] = []
    authored: list[tuple[Path, dict[str, Any] | None]] = []
    for kind in requested_kinds:
        directory = root / MEMORY_KIND_CONFIG[kind]["directory"]
        if kind == "plan":
            authored.append((directory / f"plan-{slugify(str(manifest.get('task_id') or manifest.get('session_id') or 'session'))}.json", author_plan(manifest=manifest, session_ref=session_ref, status_snapshot_ref=status_snapshot_ref, path=directory / f"plan-{slugify(str(manifest.get('task_id') or manifest.get('session_id') or 'session'))}.json")))
        elif kind == "decision":
            authored.append((directory / f"decision-{slugify(str(manifest.get('session_id') or manifest.get('task_id') or 'session'))}.json", author_decision(manifest=manifest, session_ref=session_ref, status_snapshot_ref=status_snapshot_ref, path=directory / f"decision-{slugify(str(manifest.get('session_id') or manifest.get('task_id') or 'session'))}.json")))
        elif kind == "initiative":
            authored.append((directory / f"initiative-{slugify(str(manifest.get('task_id') or manifest.get('session_id') or 'session'))}.json", author_initiative(root=root, manifest=manifest, path=directory / f"initiative-{slugify(str(manifest.get('task_id') or manifest.get('session_id') or 'session'))}.json")))
        elif kind == "hypothesis":
            authored.append((directory / f"hypothesis-{slugify(str(manifest.get('task_id') or manifest.get('session_id') or 'session'))}.json", author_hypothesis(manifest=manifest, session_ref=session_ref, status_snapshot_ref=status_snapshot_ref, path=directory / f"hypothesis-{slugify(str(manifest.get('task_id') or manifest.get('session_id') or 'session'))}.json")))

    for path, payload in authored:
        if payload is None:
            continue
        outputs.append(
            {
                "path": atlas_relative(path, root=root),
                "id": payload["id"],
                "memory_kind": payload["contract_version"].split(".")[1],
                "status": payload["status"],
                "dry_run": args.dry_run,
                "changed": False,
            }
        )
        if not args.dry_run:
            written = write_payload(path, payload)
            if written is not None:
                outputs[-1]["changed"] = bool(written["changed"])

    if not args.dry_run:
        catalog_summary = write_working_memory_catalog(root)
    else:
        catalog_summary = {
            "output_path": atlas_relative(root / "runtime" / "cortex" / "catalog" / "memory" / "working-memory.latest.json", root=root),
            "item_count": None,
            "content_digest": None,
        }

    print(
        json.dumps(
            {
                "session_ref": session_ref,
                "status_snapshot_ref": status_snapshot_ref,
                "memory_count": len(outputs),
                "items": outputs,
                "catalog": catalog_summary,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
