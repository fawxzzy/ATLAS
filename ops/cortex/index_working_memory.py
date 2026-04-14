from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.cortex._artifacts import stable_json_digest, write_json

WORKING_MEMORY_CATALOG_VERSION = "atlas.working-memory.catalog.v1"
WORKING_MEMORY_OUTPUT = Path("runtime/cortex/catalog/memory/working-memory.latest.json")
MEMORY_ARRAY_FIELDS = (
    "related_session_refs",
    "related_artifact_refs",
    "evidence_refs",
    "supersedes",
    "superseded_by",
)
MEMORY_KIND_CONFIG = {
    "plan": {
        "contract_version": "atlas.plan.v1",
        "directory": Path("docs/memory/plans"),
    },
    "decision": {
        "contract_version": "atlas.decision.v1",
        "directory": Path("docs/memory/decisions"),
    },
    "initiative": {
        "contract_version": "atlas.initiative.v1",
        "directory": Path("docs/memory/initiatives"),
    },
    "hypothesis": {
        "contract_version": "atlas.hypothesis.v1",
        "directory": Path("docs/memory/hypotheses"),
    },
}


def parse_iso_timestamp(value: str, *, field: str, relative_path: str) -> str:
    normalized = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{relative_path}: field '{field}' must be an ISO timestamp ({exc}).") from exc
    return value


def as_string(value: Any, *, field: str, relative_path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{relative_path}: field '{field}' must be a non-empty string.")
    return value.strip()


def as_string_list(value: Any, *, field: str, relative_path: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{relative_path}: field '{field}' must be an array of non-empty strings.")
    return sorted({item.strip() for item in value})


def discover_working_memory_files(root: Path | None = None) -> list[tuple[str, Path]]:
    base_root = (root or atlas_root()).resolve()
    discovered: list[tuple[str, Path]] = []
    for memory_kind, config in MEMORY_KIND_CONFIG.items():
        directory = base_root / config["directory"]
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.json")):
            if path.is_file():
                discovered.append((memory_kind, path.resolve()))
    return discovered


def validate_working_memory_documents(root: Path | None = None) -> list[dict[str, Any]]:
    base_root = (root or atlas_root()).resolve()
    errors: list[dict[str, Any]] = []
    seen_ids: dict[str, str] = {}
    for memory_kind, path in discover_working_memory_files(base_root):
        relative_path = atlas_relative(path, root=base_root)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(
                {
                    "path": relative_path,
                    "message": f"Working-memory artifact could not be parsed as JSON ({exc}).",
                }
            )
            continue
        try:
            normalized = normalize_working_memory_document(
                payload,
                memory_kind=memory_kind,
                relative_path=relative_path,
            )
        except ValueError as exc:
            errors.append({"path": relative_path, "message": str(exc)})
            continue
        existing = seen_ids.get(normalized["id"])
        if existing is not None:
            errors.append(
                {
                    "path": relative_path,
                    "message": f"Working-memory id '{normalized['id']}' duplicates '{existing}'.",
                }
            )
            continue
        seen_ids[normalized["id"]] = relative_path
    return errors


def normalize_working_memory_document(
    payload: Any,
    *,
    memory_kind: str,
    relative_path: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"{relative_path}: working-memory artifact must be a JSON object.")
    contract_version = str(MEMORY_KIND_CONFIG[memory_kind]["contract_version"])
    if payload.get("contract_version") != contract_version:
        raise ValueError(
            f"{relative_path}: contract_version must be '{contract_version}'."
        )

    normalized = {
        "contract_version": contract_version,
        "memory_kind": memory_kind,
        "id": as_string(payload.get("id"), field="id", relative_path=relative_path),
        "title": as_string(payload.get("title"), field="title", relative_path=relative_path),
        "summary": as_string(payload.get("summary"), field="summary", relative_path=relative_path),
        "status": as_string(payload.get("status"), field="status", relative_path=relative_path),
        "owner": as_string(payload.get("owner"), field="owner", relative_path=relative_path),
        "created_at": parse_iso_timestamp(
            as_string(payload.get("created_at"), field="created_at", relative_path=relative_path),
            field="created_at",
            relative_path=relative_path,
        ),
        "updated_at": parse_iso_timestamp(
            as_string(payload.get("updated_at"), field="updated_at", relative_path=relative_path),
            field="updated_at",
            relative_path=relative_path,
        ),
        "path": relative_path,
    }
    for field in MEMORY_ARRAY_FIELDS:
        normalized[field] = as_string_list(payload.get(field), field=field, relative_path=relative_path)

    metadata = payload.get("metadata", {})
    if metadata is not None and not isinstance(metadata, dict):
        raise ValueError(f"{relative_path}: field 'metadata' must be an object when provided.")
    normalized["metadata"] = metadata or {}
    normalized["content_digest"] = stable_json_digest(
        {
            "contract_version": normalized["contract_version"],
            "memory_kind": normalized["memory_kind"],
            "id": normalized["id"],
            "title": normalized["title"],
            "summary": normalized["summary"],
            "status": normalized["status"],
            "owner": normalized["owner"],
            "created_at": normalized["created_at"],
            "updated_at": normalized["updated_at"],
            "related_session_refs": normalized["related_session_refs"],
            "related_artifact_refs": normalized["related_artifact_refs"],
            "evidence_refs": normalized["evidence_refs"],
            "supersedes": normalized["supersedes"],
            "superseded_by": normalized["superseded_by"],
            "metadata": normalized["metadata"],
        }
    )
    return normalized


def build_working_memory_catalog(root: Path | None = None) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    items: list[dict[str, Any]] = []
    for memory_kind, path in discover_working_memory_files(base_root):
        relative_path = atlas_relative(path, root=base_root)
        payload = json.loads(path.read_text(encoding="utf-8"))
        items.append(
            normalize_working_memory_document(
                payload,
                memory_kind=memory_kind,
                relative_path=relative_path,
            )
        )
    items.sort(key=lambda item: (item["memory_kind"], item["status"], item["id"], item["path"]))
    body = {
        "schema_version": WORKING_MEMORY_CATALOG_VERSION,
        "output_path": atlas_relative(base_root / WORKING_MEMORY_OUTPUT, root=base_root),
        "item_count": len(items),
        "kind_counts": dict(sorted(Counter(item["memory_kind"] for item in items).items())),
        "status_counts": dict(sorted(Counter(item["status"] for item in items).items())),
        "items": items,
    }
    return body | {"content_digest": stable_json_digest(body)}


def write_working_memory_catalog(root: Path | None = None) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    errors = validate_working_memory_documents(base_root)
    if errors:
        messages = "; ".join(error["message"] for error in errors)
        raise ValueError(messages)
    catalog = build_working_memory_catalog(base_root)
    output_path = base_root / WORKING_MEMORY_OUTPUT
    write_json(output_path, catalog)
    return {
        "output_path": atlas_relative(output_path, root=base_root),
        "item_count": catalog["item_count"],
        "content_digest": catalog["content_digest"],
        "catalog": catalog,
    }


def load_working_memory_catalog(root: Path | None = None) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    output_path = base_root / WORKING_MEMORY_OUTPUT
    if not output_path.exists():
        return {
            "schema_version": WORKING_MEMORY_CATALOG_VERSION,
            "output_path": atlas_relative(output_path, root=base_root),
            "item_count": 0,
            "kind_counts": {},
            "status_counts": {},
            "items": [],
            "content_digest": stable_json_digest(
                {
                    "schema_version": WORKING_MEMORY_CATALOG_VERSION,
                    "output_path": atlas_relative(output_path, root=base_root),
                    "item_count": 0,
                    "kind_counts": {},
                    "status_counts": {},
                    "items": [],
                }
            ),
        }
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Working-memory catalog must be a JSON object.")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Index structured ATLAS working-memory artifacts.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    base_root = args.root.resolve()
    errors = validate_working_memory_documents(base_root)
    if errors:
        print(json.dumps({"errors": errors}, indent=2))
        return 1

    catalog = build_working_memory_catalog(base_root)
    if not args.dry_run:
        write_json(base_root / WORKING_MEMORY_OUTPUT, catalog)
    print(
        json.dumps(
            {
                "dry_run": args.dry_run,
                "output_path": atlas_relative(base_root / WORKING_MEMORY_OUTPUT, root=base_root),
                "item_count": catalog["item_count"],
                "content_digest": catalog["content_digest"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
