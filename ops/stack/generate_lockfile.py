from __future__ import annotations

import argparse
import functools
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, load_stack_config, normalize_slashes, resolve_atlas_path

STACK_LOCK_SCHEMA_VERSION = "atlas.stack.lock.v1"
TRUST_CLASSES = {"trusted", "adjacent", "untrusted"}
DEFAULT_INCLUDED_STATUSES = {"active", "incubating", "demo", "unmanaged"}
LOCK_COMPONENT_FIELDS = (
    "path",
    "role",
    "status",
    "remote",
    "ref_type",
    "ref",
    "commit",
    "dirty",
    "trust_class",
    "release_eligible",
)
LOCK_METADATA_FIELDS = (
    "schema_version",
    "stack_manifest_path",
    "stack_manifest_digest",
    "component_count",
)
LOCK_EXCLUDED_SURFACE_FIELDS = (
    "path",
    "present",
    "trust_class",
    "release_eligible",
    "reason",
)


def stable_json_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def git_output(repo_path: Path, *args: str) -> tuple[int, str]:
    completed = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.returncode, completed.stdout.rstrip("\n").rstrip("\r")


def git_lines(repo_path: Path, *args: str) -> list[str]:
    code, stdout = git_output(repo_path, *args)
    if code != 0:
        return []
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def git_status_lines(repo_path: Path) -> list[str]:
    code, stdout = git_output(repo_path, "status", "--porcelain=v1", "--untracked-files=all")
    if code != 0:
        return []
    return [line.rstrip("\r") for line in stdout.splitlines() if line]


def parse_porcelain_path(line: str) -> str:
    entry = line[3:] if len(line) > 3 else ""
    if " -> " in entry:
        entry = entry.split(" -> ", 1)[1]
    entry = entry.strip()
    if entry.startswith('"') and entry.endswith('"'):
        try:
            decoded = json.loads(entry)
            if isinstance(decoded, str):
                entry = decoded
        except json.JSONDecodeError:
            entry = entry[1:-1]
    return normalize_slashes(entry)


def status_paths(status_lines: list[str]) -> list[str]:
    return [path for path in (parse_porcelain_path(line) for line in status_lines) if path]


@functools.lru_cache(maxsize=None)
def _repo_is_git_root_cached(repo_path_str: str) -> bool:
    repo_path = Path(repo_path_str)
    git_entry = repo_path / ".git"
    return git_entry.exists()


def repo_is_git_root(repo_path: Path) -> bool:
    return _repo_is_git_root_cached(str(repo_path.resolve()))


def current_ref(repo_path: Path, commit: str) -> tuple[str, str]:
    code, branch = git_output(repo_path, "symbolic-ref", "--quiet", "--short", "HEAD")
    if code == 0 and branch:
        return "branch", branch
    code, tag = git_output(repo_path, "describe", "--tags", "--exact-match")
    if code == 0 and tag:
        return "tag", tag
    return "commit", commit


def current_remote(repo_path: Path) -> str | None:
    code, remote = git_output(repo_path, "remote", "get-url", "origin")
    if code == 0 and remote:
        return normalize_slashes(remote)
    remotes = git_lines(repo_path, "remote")
    for name in remotes:
        code, value = git_output(repo_path, "remote", "get-url", name)
        if code == 0 and value:
            return normalize_slashes(value)
    return None


def repo_trust_class(repo_id: str, repo_info: dict[str, Any], lock_config: dict[str, Any]) -> str:
    overrides = lock_config.get("repo_overrides", {})
    if isinstance(overrides, dict):
        repo_override = overrides.get(repo_id, {})
        if isinstance(repo_override, dict) and isinstance(repo_override.get("trust_class"), str):
            trust_class = str(repo_override["trust_class"])
            if trust_class not in TRUST_CLASSES:
                raise ValueError(f"Unsupported trust_class '{trust_class}' for repo '{repo_id}'.")
            return trust_class
    status = str(repo_info.get("status", "unknown"))
    if status == "unmanaged":
        return "adjacent"
    return "trusted"


def repo_release_eligible(repo_id: str, repo_info: dict[str, Any], lock_config: dict[str, Any]) -> bool:
    overrides = lock_config.get("repo_overrides", {})
    if isinstance(overrides, dict):
        repo_override = overrides.get(repo_id, {})
        if isinstance(repo_override, dict) and "release_eligible" in repo_override:
            return bool(repo_override["release_eligible"])
    return str(repo_info.get("status", "unknown")) == "active" and repo_id != "stack"


def included_repo_ids(config: dict[str, Any]) -> list[str]:
    lock_config = config.get("stack_lock", {})
    if isinstance(lock_config, dict):
        explicit = lock_config.get("include_repo_ids")
        if isinstance(explicit, list) and explicit:
            return [str(item) for item in explicit]
    repo_registry = config.get("repo_registry", {})
    result: list[str] = []
    for repo_id, repo_info in repo_registry.items():
        if not isinstance(repo_info, dict):
            continue
        if str(repo_info.get("status", "unknown")) in DEFAULT_INCLUDED_STATUSES:
            result.append(str(repo_id))
    return sorted(result)


def stack_component_repo_id(config: dict[str, Any], root: Path) -> str | None:
    registry = config.get("repo_registry", {})
    for repo_id in included_repo_ids(config):
        repo_info = registry.get(repo_id)
        if not isinstance(repo_info, dict) or not isinstance(repo_info.get("path"), str):
            continue
        if resolve_atlas_path(repo_info["path"], root=root).resolve() == root.resolve():
            return str(repo_id)
    return None


def default_lockfile_path(config: dict[str, Any] | None = None, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    stack_config = config or load_stack_config(base / "stack.yaml")
    lock_config = stack_config.get("stack_lock", {})
    if isinstance(lock_config, dict) and isinstance(lock_config.get("path"), str):
        return resolve_atlas_path(lock_config["path"], root=base)
    return base / "stack.lock.yaml"


def excluded_surfaces(config: dict[str, Any], root: Path) -> dict[str, dict[str, Any]]:
    lock_config = config.get("stack_lock", {})
    surfaces: dict[str, dict[str, Any]] = {}
    if not isinstance(lock_config, dict):
        return surfaces
    raw_surfaces = lock_config.get("excluded_surfaces", {})
    if not isinstance(raw_surfaces, dict):
        return surfaces
    for surface_id in sorted(raw_surfaces):
        value = raw_surfaces[surface_id]
        if not isinstance(value, dict) or not isinstance(value.get("path"), str):
            raise ValueError(f"Excluded surface '{surface_id}' must declare a path.")
        trust_class = str(value.get("trust_class", "untrusted"))
        if trust_class not in TRUST_CLASSES:
            raise ValueError(f"Unsupported trust_class '{trust_class}' for excluded surface '{surface_id}'.")
        surface_path = resolve_atlas_path(value["path"], root=root)
        surfaces[str(surface_id)] = {
            "path": atlas_relative(surface_path, root=root),
            "present": surface_path.exists(),
            "trust_class": trust_class,
            "release_eligible": bool(value.get("release_eligible", False)),
            "reason": str(value.get("reason", "")),
        }
    return surfaces


def normalize_lock_component(component: dict[str, Any]) -> dict[str, Any]:
    remote = component.get("remote")
    return {
        "path": normalize_slashes(str(component.get("path", ""))),
        "role": str(component.get("role", "")),
        "status": str(component.get("status", "unknown")),
        "remote": normalize_slashes(str(remote)) if isinstance(remote, str) and remote else None,
        "ref_type": str(component.get("ref_type", "")),
        "ref": str(component.get("ref", "")),
        "commit": str(component.get("commit", "")),
        "dirty": bool(component.get("dirty", False)),
        "trust_class": str(component.get("trust_class", "")),
        "release_eligible": bool(component.get("release_eligible", False)),
    }


def normalize_excluded_surface(surface: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": normalize_slashes(str(surface.get("path", ""))),
        "present": bool(surface.get("present", False)),
        "trust_class": str(surface.get("trust_class", "")),
        "release_eligible": bool(surface.get("release_eligible", False)),
        "reason": str(surface.get("reason", "")),
    }


def normalize_lock_payload(payload: dict[str, Any]) -> dict[str, Any]:
    raw_components = payload.get("components", {})
    components: dict[str, dict[str, Any]] = {}
    if isinstance(raw_components, dict):
        for component_id, component in sorted(
            ((str(raw_key), raw_value) for raw_key, raw_value in raw_components.items()),
            key=lambda item: item[0],
        ):
            if isinstance(component, dict):
                components[component_id] = normalize_lock_component(component)

    raw_excluded_surfaces = payload.get("excluded_surfaces", {})
    excluded: dict[str, dict[str, Any]] = {}
    if isinstance(raw_excluded_surfaces, dict):
        for surface_id, surface in sorted(
            ((str(raw_key), raw_value) for raw_key, raw_value in raw_excluded_surfaces.items()),
            key=lambda item: item[0],
        ):
            if isinstance(surface, dict):
                excluded[surface_id] = normalize_excluded_surface(surface)

    body = {
        "schema_version": str(payload.get("schema_version", STACK_LOCK_SCHEMA_VERSION)),
        "stack_manifest_path": normalize_slashes(str(payload.get("stack_manifest_path", "stack.yaml"))),
        "stack_manifest_digest": str(payload.get("stack_manifest_digest", "")),
        "component_count": len(components),
        "components": components,
        "excluded_surfaces": excluded,
    }
    return body | {"lock_digest": stable_json_digest(body)}


def stack_root_dirty_state(
    config: dict[str, Any],
    *,
    root: Path,
    lockfile_path: Path | None = None,
) -> dict[str, Any]:
    resolved_root = root.resolve()
    resolved_lockfile = (
        resolve_atlas_path(lockfile_path, root=resolved_root)
        if lockfile_path is not None
        else default_lockfile_path(config=config, root=resolved_root)
    )
    repo_id = stack_component_repo_id(config, resolved_root)
    status_lines = git_status_lines(resolved_root)
    modified_paths = sorted(status_paths(status_lines))
    lockfile_rel = atlas_relative(resolved_lockfile, root=resolved_root)
    self_refresh_only = bool(repo_id) and modified_paths == [lockfile_rel]
    dirty_actual = bool(status_lines)
    dirty_effective = dirty_actual and not self_refresh_only
    return {
        "repo_id": repo_id,
        "lockfile_path": resolved_lockfile,
        "lockfile_rel": lockfile_rel,
        "modified_paths": modified_paths,
        "dirty_actual": dirty_actual,
        "dirty_effective": dirty_effective,
        "self_refresh_only": self_refresh_only,
    }


def lock_component_field_drift(
    locked: dict[str, Any],
    generated: dict[str, Any],
) -> list[str]:
    return [field for field in LOCK_COMPONENT_FIELDS if locked.get(field) != generated.get(field)]


def lock_surface_field_drift(
    locked: dict[str, Any],
    generated: dict[str, Any],
) -> list[str]:
    return [field for field in LOCK_EXCLUDED_SURFACE_FIELDS if locked.get(field) != generated.get(field)]


def classify_component_drift_fields(drift_fields: list[str]) -> str:
    return "worktree" if drift_fields == ["dirty"] else "pin"


def describe_lock_payload_drift(
    locked_payload: dict[str, Any],
    generated_payload: dict[str, Any],
) -> dict[str, Any]:
    locked = normalize_lock_payload(locked_payload)
    generated = normalize_lock_payload(generated_payload)

    component_drift: dict[str, dict[str, Any]] = {}
    locked_components = locked.get("components") if isinstance(locked.get("components"), dict) else {}
    generated_components = generated.get("components") if isinstance(generated.get("components"), dict) else {}
    for component_id in sorted(set(locked_components) | set(generated_components)):
        locked_component = locked_components.get(component_id)
        generated_component = generated_components.get(component_id)
        if not isinstance(locked_component, dict) or not isinstance(generated_component, dict):
            component_drift[component_id] = {"kind": "membership", "fields": []}
            continue
        drift_fields = lock_component_field_drift(locked_component, generated_component)
        if drift_fields:
            component_drift[component_id] = {
                "kind": classify_component_drift_fields(drift_fields),
                "fields": drift_fields,
            }

    excluded_surface_drift: dict[str, dict[str, Any]] = {}
    locked_surfaces = locked.get("excluded_surfaces") if isinstance(locked.get("excluded_surfaces"), dict) else {}
    generated_surfaces = generated.get("excluded_surfaces") if isinstance(generated.get("excluded_surfaces"), dict) else {}
    for surface_id in sorted(set(locked_surfaces) | set(generated_surfaces)):
        locked_surface = locked_surfaces.get(surface_id)
        generated_surface = generated_surfaces.get(surface_id)
        if not isinstance(locked_surface, dict) or not isinstance(generated_surface, dict):
            excluded_surface_drift[surface_id] = {"kind": "membership", "fields": []}
            continue
        drift_fields = lock_surface_field_drift(locked_surface, generated_surface)
        if drift_fields:
            excluded_surface_drift[surface_id] = {"kind": "fields", "fields": drift_fields}

    metadata_fields = [field for field in LOCK_METADATA_FIELDS if locked.get(field) != generated.get(field)]
    return {
        "locked": locked,
        "generated": generated,
        "components": component_drift,
        "excluded_surfaces": excluded_surface_drift,
        "metadata_fields": metadata_fields,
        "has_drift": bool(component_drift or excluded_surface_drift or metadata_fields),
    }


def build_lock_payload(
    config: dict[str, Any] | None = None,
    root: Path | None = None,
    *,
    dirty_overrides: dict[str, bool] | None = None,
) -> dict[str, Any]:
    base = (root or atlas_root()).resolve()
    stack_config = config or load_stack_config(base / "stack.yaml")
    registry = stack_config.get("repo_registry", {})
    lock_config = stack_config.get("stack_lock", {}) if isinstance(stack_config.get("stack_lock"), dict) else {}
    components: dict[str, dict[str, Any]] = {}

    for repo_id in included_repo_ids(stack_config):
        repo_info = registry.get(repo_id)
        if not isinstance(repo_info, dict) or not isinstance(repo_info.get("path"), str):
            raise ValueError(f"Included repo '{repo_id}' is missing a valid repo_registry entry.")
        repo_path = resolve_atlas_path(repo_info["path"], root=base)
        if not repo_path.exists():
            raise FileNotFoundError(f"Included repo path does not exist: {atlas_relative(repo_path, root=base)}")
        if not repo_path.is_dir():
            raise ValueError(f"Included repo path is not a directory: {atlas_relative(repo_path, root=base)}")
        if not repo_is_git_root(repo_path):
            raise ValueError(f"Included repo is not a git root: {atlas_relative(repo_path, root=base)}")

        code, commit = git_output(repo_path, "rev-parse", "HEAD")
        if code != 0 or not commit:
            raise ValueError(f"Unable to resolve HEAD for repo '{repo_id}'.")
        ref_type, ref = current_ref(repo_path, commit)
        status_lines = git_status_lines(repo_path)
        dirty = bool(status_lines)
        if dirty_overrides and repo_id in dirty_overrides:
            dirty = bool(dirty_overrides[repo_id])
        components[repo_id] = {
            "path": atlas_relative(repo_path, root=base),
            "role": str(repo_info.get("role", "")),
            "status": str(repo_info.get("status", "unknown")),
            "remote": current_remote(repo_path),
            "ref_type": ref_type,
            "ref": ref,
            "commit": commit,
            "dirty": dirty,
            "trust_class": repo_trust_class(repo_id, repo_info, lock_config),
            "release_eligible": repo_release_eligible(repo_id, repo_info, lock_config),
        }

    payload = {
        "schema_version": STACK_LOCK_SCHEMA_VERSION,
        "stack_manifest_path": atlas_relative(base / "stack.yaml", root=base),
        "stack_manifest_digest": stable_json_digest(stack_config),
        "component_count": len(components),
        "components": components,
        "excluded_surfaces": excluded_surfaces(stack_config, base),
    }
    return normalize_lock_payload(payload)


def load_lockfile(path: Path) -> dict[str, Any]:
    payload = load_stack_config(path)
    if not isinstance(payload, dict):
        raise ValueError("Lockfile must deserialize to a mapping.")
    return payload


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def render_yaml(value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, dict):
                lines.append(f"{prefix}{key}:")
                lines.extend(render_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {yaml_scalar(item)}")
        return lines
    raise TypeError(f"Unsupported YAML value: {type(value)!r}")


def render_lockfile_text(payload: dict[str, Any]) -> str:
    return "\n".join(render_yaml(payload)) + "\n"


def render_lockfile_bytes(payload: dict[str, Any]) -> bytes:
    return render_lockfile_text(payload).encode("utf-8")


def build_canonical_lockfile_artifacts(
    config: dict[str, Any] | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    base = (root or atlas_root()).resolve()
    stack_config = config or load_stack_config(base / "stack.yaml")
    dirty_state = stack_root_dirty_state(stack_config, root=base)
    dirty_overrides: dict[str, bool] | None = None
    repo_id = dirty_state.get("repo_id")
    if dirty_state.get("self_refresh_only") and isinstance(repo_id, str):
        dirty_overrides = {repo_id: bool(dirty_state["dirty_effective"])}
    payload = build_lock_payload(config=stack_config, root=base, dirty_overrides=dirty_overrides)
    text = render_lockfile_text(payload)
    return {
        "payload": payload,
        "text": text,
        "bytes": text.encode("utf-8"),
        "lockfile_path": dirty_state["lockfile_path"],
        "stack_root": dirty_state,
    }


def write_lockfile(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(render_lockfile_bytes(payload))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the deterministic ATLAS stack lockfile from the current managed git working set."
    )
    parser.add_argument("--stack-file", type=Path, default=atlas_root() / "stack.yaml")
    parser.add_argument("--output-path", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    stack_file = resolve_atlas_path(args.stack_file)
    root = stack_file.parent.resolve()
    config = load_stack_config(stack_file)
    artifacts = build_canonical_lockfile_artifacts(config=config, root=root)
    payload = artifacts["payload"]
    output_path = resolve_atlas_path(args.output_path, root=root) if args.output_path else default_lockfile_path(config, root)
    if not args.dry_run:
        write_lockfile(output_path, payload)

    print(
        json.dumps(
            {
                "dry_run": args.dry_run,
                "stack_file": atlas_relative(stack_file, root=root),
                "output_path": atlas_relative(output_path, root=root),
                "component_count": payload["component_count"],
                "excluded_surface_count": len(payload["excluded_surfaces"]),
                "lock_digest": payload["lock_digest"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
