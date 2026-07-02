from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, load_stack_config, normalize_slashes, resolve_atlas_path
from ops.cortex._artifacts import stable_json_digest
from ops.cortex.index_working_memory import build_working_memory_catalog
from ops.stack.generate_lockfile import (
    current_ref,
    current_remote,
    default_lockfile_path,
    git_output,
    git_status_lines,
    load_lockfile,
    parse_porcelain_path,
    repo_is_git_root,
    repo_release_eligible,
    repo_trust_class,
)

REPO_INVENTORY_SCHEMA_VERSION = "atlas.stack.repo-inventory.v1"
REPO_INVENTORY_SUMMARY_VERSION = "atlas.stack.repo-inventory.summary.v1"
DEFAULT_JSON_OUTPUT = Path("docs/registry/STACK-REPO-INVENTORY.json")
DEFAULT_MARKDOWN_OUTPUT = Path("docs/audits/STACK-REPO-INVENTORY.md")


def _collect_strings(value: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(value, str):
        strings.append(value)
    elif isinstance(value, dict):
        for nested in value.values():
            strings.extend(_collect_strings(nested))
    elif isinstance(value, list):
        for nested in value:
            strings.extend(_collect_strings(nested))
    return strings


def _repo_root_ref(ref: str) -> str | None:
    normalized = normalize_slashes(ref).strip()
    if normalized in {"", "."}:
        return "."
    if not normalized.startswith("repos/"):
        return None
    parts = [part for part in normalized.split("/") if part]
    if len(parts) < 2:
        return None
    return "/".join(parts[:2])


def _initiative_repo_paths(item: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    metadata = item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {}
    repo_refs = metadata.get("repo_refs")
    if isinstance(repo_refs, list):
        refs.extend(str(value) for value in repo_refs if isinstance(value, str))
    for key, value in item.items():
        if key == "path" or key.endswith("_refs") or key == "metadata":
            refs.extend(_collect_strings(value))
    results = {
        repo_ref
        for repo_ref in (_repo_root_ref(candidate) for candidate in refs)
        if repo_ref
    }
    return sorted(results)


def _initiative_records(root: Path) -> list[dict[str, Any]]:
    catalog = build_working_memory_catalog(root)
    items = catalog.get("items", []) if isinstance(catalog.get("items"), list) else []
    records: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict) or str(item.get("memory_kind", "")).strip() != "initiative":
            continue
        metadata = item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {}
        initiative_id = str(item.get("id") or "").strip()
        if not initiative_id:
            continue
        repo_ids: list[str] = []
        repo_id = metadata.get("repo_id")
        if isinstance(repo_id, str) and repo_id.strip():
            repo_ids.append(repo_id.strip())
        records.append(
            {
                "initiative_ref": f"initiative:{initiative_id}",
                "title": str(item.get("title") or initiative_id),
                "path": str(item.get("path") or ""),
                "status": str(item.get("status") or ""),
                "repo_ids": sorted({value for value in repo_ids if value}),
                "repo_paths": _initiative_repo_paths(item),
            }
        )
    records.sort(key=lambda item: (str(item["initiative_ref"]), str(item["path"])))
    return records


def _initiative_index(root: Path, repo_paths: dict[str, str]) -> tuple[dict[str, list[dict[str, Any]]], str]:
    by_repo_id: dict[str, list[dict[str, Any]]] = {}
    records = _initiative_records(root)
    for record in records:
        normalized_paths = {
            normalize_slashes(path).strip()
            for path in record.get("repo_paths", [])
            if isinstance(path, str) and path.strip()
        }
        for path, repo_id in repo_paths.items():
            if path in normalized_paths:
                by_repo_id.setdefault(repo_id, []).append(record)
        for repo_id in record.get("repo_ids", []):
            if isinstance(repo_id, str) and repo_id.strip():
                by_repo_id.setdefault(repo_id.strip(), []).append(record)

    for repo_id, items in by_repo_id.items():
        deduped: dict[str, dict[str, Any]] = {}
        for item in items:
            deduped[str(item["initiative_ref"])] = {
                "initiative_ref": item["initiative_ref"],
                "title": item["title"],
                "path": item["path"],
                "status": item["status"],
            }
        by_repo_id[repo_id] = [deduped[key] for key in sorted(deduped)]

    digest_payload = {
        repo_id: items
        for repo_id, items in sorted(by_repo_id.items())
    }
    return by_repo_id, stable_json_digest(digest_payload)


def _is_repo_dirty(repo_path: Path, *, ignored_paths: set[str] | None = None) -> bool:
    ignored = {normalize_slashes(path).strip() for path in (ignored_paths or set()) if path.strip()}
    for line in git_status_lines(repo_path):
        path = parse_porcelain_path(line)
        if not path or path not in ignored:
            return True
    return False


def _live_repo_state(repo_path: Path, *, ignored_dirty_paths: set[str] | None = None) -> dict[str, Any]:
    if not repo_path.exists() or not repo_path.is_dir():
        return {
            "exists": False,
            "is_git_root": False,
            "remote_url": None,
            "current_commit": None,
            "current_ref_type": None,
            "current_ref": None,
            "branch": None,
            "dirty": None,
        }
    if not repo_is_git_root(repo_path):
        return {
            "exists": True,
            "is_git_root": False,
            "remote_url": None,
            "current_commit": None,
            "current_ref_type": None,
            "current_ref": None,
            "branch": None,
            "dirty": None,
        }
    code, commit = git_output(repo_path, "rev-parse", "HEAD")
    if code != 0 or not commit:
        raise ValueError(f"Unable to resolve HEAD for repo inventory path: {repo_path}")
    ref_type, ref = current_ref(repo_path, commit)
    return {
        "exists": True,
        "is_git_root": True,
        "remote_url": current_remote(repo_path),
        "current_commit": commit,
        "current_ref_type": ref_type,
        "current_ref": ref,
        "branch": ref if ref_type == "branch" else None,
        "dirty": _is_repo_dirty(repo_path, ignored_paths=ignored_dirty_paths),
    }


def _repo_blocks_root(repo_id: str, repo_info: dict[str, Any], lock_config: dict[str, Any]) -> bool:
    overrides = lock_config.get("repo_overrides", {})
    if isinstance(overrides, dict):
        repo_override = overrides.get(repo_id, {})
        if isinstance(repo_override, dict) and "root_blocking" in repo_override:
            return bool(repo_override["root_blocking"])
    if "root_blocking" in repo_info:
        return bool(repo_info["root_blocking"])
    return str(repo_info.get("status", "unknown")) != "unmanaged"


def build_repo_inventory(
    *,
    root: Path | None = None,
    config: dict[str, Any] | None = None,
    lock_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    stack_config = config or load_stack_config(base_root / "stack.yaml")
    resolved_lock_path = default_lockfile_path(stack_config, base_root)
    loaded_lock = lock_payload
    if loaded_lock is None and resolved_lock_path.exists():
        loaded_lock = load_lockfile(resolved_lock_path)
    if not isinstance(loaded_lock, dict):
        loaded_lock = {}

    registry = stack_config.get("repo_registry", {}) if isinstance(stack_config.get("repo_registry"), dict) else {}
    repo_paths = {
        normalize_slashes(str(repo_info.get("path", ""))).strip(): str(repo_id)
        for repo_id, repo_info in registry.items()
        if isinstance(repo_info, dict) and isinstance(repo_info.get("path"), str)
    }
    initiative_index, initiative_digest = _initiative_index(base_root, repo_paths)
    lock_components = loaded_lock.get("components", {}) if isinstance(loaded_lock.get("components"), dict) else {}
    lock_config = stack_config.get("stack_lock", {}) if isinstance(stack_config.get("stack_lock"), dict) else {}

    repos: list[dict[str, Any]] = []
    for repo_id in sorted(str(item) for item in registry.keys()):
        repo_info = registry.get(repo_id)
        if not isinstance(repo_info, dict) or not isinstance(repo_info.get("path"), str):
            continue
        repo_path = resolve_atlas_path(repo_info["path"], root=base_root)
        ignored_dirty_paths: set[str] = set()
        if repo_id == "stack" and repo_path == base_root:
            # The inventory/lock refresh flow writes these generated stack
            # surfaces itself, so they should not make the stack entry look
            # dirty in the same read.
            ignored_dirty_paths = {
                normalize_slashes(str(DEFAULT_JSON_OUTPUT)),
                normalize_slashes(str(DEFAULT_MARKDOWN_OUTPUT)),
                atlas_relative(resolved_lock_path, root=base_root),
            }
        live_state = _live_repo_state(repo_path, ignored_dirty_paths=ignored_dirty_paths)
        lock_component = lock_components.get(repo_id) if isinstance(lock_components.get(repo_id), dict) else {}
        related_initiatives = initiative_index.get(repo_id, [])
        root_blocking = _repo_blocks_root(repo_id, repo_info, lock_config)
        dirty_blocks_root = bool(live_state["dirty"] is True and root_blocking)
        repos.append(
            {
                "logical_id": repo_id,
                "local_path": atlas_relative(repo_path, root=base_root),
                "role": str(repo_info.get("role", "")),
                "status": str(repo_info.get("status", "unknown")),
                "remote_url": live_state["remote_url"],
                "pinned_commit": lock_component.get("commit"),
                "current_commit": live_state["current_commit"],
                "pinned_ref_type": lock_component.get("ref_type"),
                "pinned_ref": lock_component.get("ref"),
                "current_ref_type": live_state["current_ref_type"],
                "current_ref": live_state["current_ref"],
                "branch": live_state["branch"],
                "dirty": live_state["dirty"],
                "root_blocking": root_blocking,
                "dirty_blocks_root": dirty_blocks_root,
                "trust_class": lock_component.get("trust_class") or repo_trust_class(repo_id, repo_info, lock_config),
                "release_eligible": (
                    bool(lock_component.get("release_eligible"))
                    if "release_eligible" in lock_component
                    else repo_release_eligible(repo_id, repo_info, lock_config)
                ),
                "exists": live_state["exists"],
                "is_git_root": live_state["is_git_root"],
                "related_initiatives": related_initiatives,
                "related_initiative_refs": [
                    item["initiative_ref"]
                    for item in related_initiatives
                    if isinstance(item, dict) and isinstance(item.get("initiative_ref"), str)
                ],
            }
        )

    excluded_surfaces_raw = loaded_lock.get("excluded_surfaces", {}) if isinstance(loaded_lock.get("excluded_surfaces"), dict) else {}
    excluded_surfaces: list[dict[str, Any]] = []
    for surface_id in sorted(str(item) for item in excluded_surfaces_raw.keys()):
        surface = excluded_surfaces_raw.get(surface_id)
        if not isinstance(surface, dict):
            continue
        excluded_surfaces.append(
            {
                "surface_id": surface_id,
                "local_path": normalize_slashes(str(surface.get("path", ""))),
                "present": bool(surface.get("present", False)),
                "trust_class": str(surface.get("trust_class", "")),
                "release_eligible": bool(surface.get("release_eligible", False)),
                "reason": str(surface.get("reason", "")),
                "visibility_mode": "metadata_only" if str(surface.get("trust_class", "")).strip() != "trusted" else "full",
            }
        )

    body = {
        "schema_version": REPO_INVENTORY_SCHEMA_VERSION,
        "stack_manifest_ref": atlas_relative(base_root / "stack.yaml", root=base_root),
        "stack_manifest_digest": stable_json_digest(stack_config),
        "stack_lock_ref": atlas_relative(resolved_lock_path, root=base_root),
        "stack_lock_digest": loaded_lock.get("lock_digest"),
        "working_memory_digest": initiative_digest,
        "published_refs": {
            "json": normalize_slashes(str(DEFAULT_JSON_OUTPUT)),
            "markdown": normalize_slashes(str(DEFAULT_MARKDOWN_OUTPUT)),
        },
        "repo_count": len(repos),
        "dirty_repo_count": sum(1 for item in repos if item.get("dirty_blocks_root") is True),
        "visible_dirty_repo_count": sum(1 for item in repos if item.get("dirty") is True),
        "advisory_dirty_repo_count": sum(1 for item in repos if item.get("dirty") is True and not item.get("root_blocking")),
        "release_eligible_count": sum(1 for item in repos if bool(item.get("release_eligible"))),
        "repos": repos,
        "excluded_surface_count": len(excluded_surfaces),
        "excluded_surfaces": excluded_surfaces,
    }
    return body | {"content_digest": stable_json_digest(body)}


def summarize_repo_inventory(payload: dict[str, Any]) -> dict[str, Any]:
    repos = payload.get("repos", []) if isinstance(payload.get("repos"), list) else []
    excluded_surfaces = (
        payload.get("excluded_surfaces", [])
        if isinstance(payload.get("excluded_surfaces"), list)
        else []
    )
    items = [
        {
            "logical_id": item.get("logical_id"),
            "local_path": item.get("local_path"),
            "branch": item.get("branch"),
            "dirty": item.get("dirty"),
            "root_blocking": item.get("root_blocking"),
            "dirty_blocks_root": item.get("dirty_blocks_root"),
            "trust_class": item.get("trust_class"),
            "release_eligible": item.get("release_eligible"),
            "related_initiative_refs": item.get("related_initiative_refs", []),
        }
        for item in repos
        if isinstance(item, dict)
    ]
    return {
        "schema_version": REPO_INVENTORY_SUMMARY_VERSION,
        "content_digest": payload.get("content_digest"),
        "published_refs": payload.get("published_refs"),
        "item_count": len(items),
        "dirty_item_count": sum(1 for item in items if item.get("dirty_blocks_root") is True),
        "visible_dirty_item_count": sum(1 for item in items if item.get("dirty") is True),
        "advisory_dirty_item_count": sum(1 for item in items if item.get("dirty") is True and not item.get("root_blocking")),
        "release_eligible_count": sum(1 for item in items if bool(item.get("release_eligible"))),
        "repo_ids": [item.get("logical_id") for item in items],
        "excluded_surface_count": len(excluded_surfaces),
        "items": items,
    }


def find_repo_inventory_entry(
    payload: dict[str, Any],
    *,
    repo_id: str | None = None,
    repo_path: str | None = None,
) -> dict[str, Any] | None:
    repos = payload.get("repos", []) if isinstance(payload.get("repos"), list) else []
    normalized_path = normalize_slashes(repo_path or "").strip() if repo_path else None
    for item in repos:
        if not isinstance(item, dict):
            continue
        if repo_id is not None and str(item.get("logical_id", "")).strip() == repo_id.strip():
            return item
        if normalized_path is not None and str(item.get("local_path", "")).strip() == normalized_path:
            return item
    return None


def find_excluded_surface(payload: dict[str, Any], surface_id: str) -> dict[str, Any] | None:
    surfaces = payload.get("excluded_surfaces", []) if isinstance(payload.get("excluded_surfaces"), list) else []
    for item in surfaces:
        if isinstance(item, dict) and str(item.get("surface_id", "")).strip() == surface_id.strip():
            return item
    return None


def render_repo_inventory_markdown(payload: dict[str, Any]) -> str:
    repos = payload.get("repos", []) if isinstance(payload.get("repos"), list) else []
    excluded_surfaces = payload.get("excluded_surfaces", []) if isinstance(payload.get("excluded_surfaces"), list) else []

    lines = [
        "# Stack Repo Inventory",
        "",
        "This inventory is the stack-level visibility surface for child repos under `repos/**`.",
        "",
        "ATLAS root remains the control repo and coordination layer. Child repos remain independent git roots and are not vendored, mirrored, or installed into the root as a second source of truth.",
        "",
        "Operational rule:",
        "",
        "- `stack.yaml` declares topology",
        "- `stack.lock.yaml` pins the working set",
        "- this inventory publishes the visible topology for root status, chat, search, and future cockpit surfaces",
        "- `dirty_repo_count` counts only root-blocking repos; unmanaged owner-lane dirtiness remains visible as advisory dirtiness",
        "- `repos/**` stays untracked by the root repo except for explicit stack-owned docs and audits outside that tree",
        "",
        "## Summary",
        "",
        f"- Repo count: `{payload.get('repo_count', 0)}`",
        f"- Root-blocking dirty repo count: `{payload.get('dirty_repo_count', 0)}`",
        f"- Visible dirty repo count: `{payload.get('visible_dirty_repo_count', 0)}`",
        f"- Advisory dirty repo count: `{payload.get('advisory_dirty_repo_count', 0)}`",
        f"- Release-eligible repo count: `{payload.get('release_eligible_count', 0)}`",
        f"- Excluded surface count: `{payload.get('excluded_surface_count', 0)}`",
        f"- Stack manifest: `{payload.get('stack_manifest_ref')}`",
        f"- Stack lock: `{payload.get('stack_lock_ref')}`",
        f"- Inventory digest: `{payload.get('content_digest')}`",
        "",
        "## Managed Repos",
        "",
        "| Repo id | Path | Branch | Pinned commit | Current commit | Dirty | Root-blocking | Dirty blocks root | Trust | Release | Related initiatives |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for item in repos:
        if not isinstance(item, dict):
            continue
        initiatives = item.get("related_initiative_refs", [])
        initiative_text = "<br>".join(
            str(value) for value in initiatives if isinstance(value, str)
        ) or "-"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item.get("logical_id") or "-"),
                    str(item.get("local_path") or "-"),
                    str(item.get("branch") or "-"),
                    str(item.get("pinned_commit") or "-"),
                    str(item.get("current_commit") or "-"),
                    str(item.get("dirty") if item.get("dirty") is not None else "-"),
                    str(item.get("root_blocking")),
                    str(item.get("dirty_blocks_root")),
                    str(item.get("trust_class") or "-"),
                    str(item.get("release_eligible")),
                    initiative_text,
                ]
            )
            + " |"
        )

    if excluded_surfaces:
        lines.extend(
            [
                "",
                "## Excluded Surfaces",
                "",
                "| Surface id | Path | Present | Trust | Release | Visibility | Reason |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for item in excluded_surfaces:
            if not isinstance(item, dict):
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(item.get("surface_id") or "-"),
                        str(item.get("local_path") or "-"),
                        str(item.get("present")),
                        str(item.get("trust_class") or "-"),
                        str(item.get("release_eligible")),
                        str(item.get("visibility_mode") or "-"),
                        str(item.get("reason") or "-"),
                    ]
                )
                + " |"
            )
    return "\n".join(lines).strip() + "\n"


def write_repo_inventory(
    *,
    root: Path | None = None,
    json_output: Path | None = None,
    markdown_output: Path | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    payload = build_repo_inventory(root=base_root)
    resolved_json_output = resolve_atlas_path(json_output or DEFAULT_JSON_OUTPUT, root=base_root)
    resolved_markdown_output = resolve_atlas_path(markdown_output or DEFAULT_MARKDOWN_OUTPUT, root=base_root)
    resolved_json_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_markdown_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    resolved_markdown_output.write_text(render_repo_inventory_markdown(payload), encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export the ATLAS stack repo inventory visibility surface."
    )
    parser.add_argument("--stack-file", default=str(atlas_root() / "stack.yaml"))
    parser.add_argument("--json-output")
    parser.add_argument("--markdown-output")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    stack_file = resolve_atlas_path(args.stack_file)
    root = stack_file.parent.resolve()
    config = load_stack_config(stack_file)
    payload = build_repo_inventory(root=root, config=config)
    if not args.dry_run:
        write_repo_inventory(
            root=root,
            json_output=Path(args.json_output) if args.json_output else DEFAULT_JSON_OUTPUT,
            markdown_output=Path(args.markdown_output) if args.markdown_output else DEFAULT_MARKDOWN_OUTPUT,
        )
    print(
        json.dumps(
            {
                "dry_run": args.dry_run,
                "stack_file": atlas_relative(stack_file, root=root),
                "json_output": normalize_slashes(str(Path(args.json_output))) if args.json_output else normalize_slashes(str(DEFAULT_JSON_OUTPUT)),
                "markdown_output": normalize_slashes(str(Path(args.markdown_output))) if args.markdown_output else normalize_slashes(str(DEFAULT_MARKDOWN_OUTPUT)),
                "repo_count": payload.get("repo_count"),
                "dirty_repo_count": payload.get("dirty_repo_count"),
                "content_digest": payload.get("content_digest"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
