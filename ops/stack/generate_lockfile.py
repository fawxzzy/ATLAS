from __future__ import annotations

import argparse
import functools
import hashlib
import json
import subprocess
import sys
from pathlib import Path, PureWindowsPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, load_stack_config, normalize_slashes, parse_simple_yaml, resolve_atlas_path

STACK_LOCK_SCHEMA_VERSION = "atlas.stack.lock.v1"
TRUST_CLASSES = {"trusted", "adjacent", "untrusted"}
DEFAULT_INCLUDED_STATUSES = {"active", "incubating", "demo"}
LOCK_COMPONENT_FIELDS = (
    "path",
    "role",
    "playbook_adoption_status",
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
    "source_pin_count",
    "refresh_scope",
)
LOCK_EXCLUDED_SURFACE_FIELDS = (
    "path",
    "present",
    "trust_class",
    "release_eligible",
    "reason",
)
SCOPED_PIN_FIELDS = ("remote", "ref_type", "ref", "commit", "dirty")
SOURCE_PIN_FIELDS = (
    "path",
    "remote",
    "ref_type",
    "ref",
    "commit",
    "dirty",
    "production_ref",
    "production_commit",
    "production_promotion_status",
)

# Source pins cover repos that are deliberately excluded from stack.lock.yaml's
# governed `components`/`include_repo_ids` release-management set (unmanaged
# application repos such as Fitness/Mazer) but still need their real, current
# source-commit identity captured from git evidence rather than hand-typed
# into stack.yaml. They never affect trust_class/release_eligible semantics.
PROMOTION_STATUS_NOT_CONFIGURED = "not_configured"
PROMOTION_STATUS_NO_REMOTE = "no_remote"
PROMOTION_STATUS_REMOTE_UNREACHABLE = "remote_unreachable"
PROMOTION_STATUS_NOT_PROMOTED = "not_promoted"
PROMOTION_STATUS_PROMOTED_DIRTY_WORKTREE = "promoted_dirty_worktree"
PROMOTION_STATUS_PROMOTED_VERIFIED_CLEAN = "promoted_verified_clean"


def declared_root_coordinate(raw_path: str, *, root: Path, label: str = "Path") -> str:
    """Return a canonical root-relative presentation coordinate.

    Containment is intentionally lexical. A declared coordinate may be backed by
    a junction whose resolved target is outside an isolated worktree, but the
    declaration itself must remain relative to the ATLAS root and may not use
    parent traversal.
    """
    normalized = normalize_slashes(str(raw_path).strip())
    if not normalized:
        raise ValueError(f"{label} must be a non-empty root-relative path.")
    candidate = Path(normalized)
    windows_candidate = PureWindowsPath(normalized)
    if (
        candidate.is_absolute()
        or candidate.drive
        or candidate.root
        or windows_candidate.is_absolute()
        or windows_candidate.drive
        or windows_candidate.root
    ):
        raise ValueError(f"{label} must be root-relative: {normalized}")
    if any(part == ".." for part in candidate.parts):
        raise ValueError(f"{label} must not contain parent traversal: {normalized}")

    parts = tuple(part for part in candidate.parts if part not in {"", "."})
    coordinate = "/".join(parts) if parts else "."
    lexical_root = root.absolute()
    lexical_target = lexical_root.joinpath(*parts)
    if not lexical_target.is_relative_to(lexical_root):
        raise ValueError(f"{label} escapes the ATLAS root: {normalized}")
    return coordinate


def resolve_declared_root_path(raw_path: str, *, root: Path, label: str = "Path") -> tuple[str, Path]:
    coordinate = declared_root_coordinate(raw_path, root=root, label=label)
    return coordinate, resolve_atlas_path(coordinate, root=root)


def scoped_refresh_repo_ids(payload: dict[str, Any]) -> set[str] | None:
    scope = payload.get("refresh_scope")
    if scope is None:
        return None
    if not isinstance(scope, dict) or scope.get("mode") != "scoped":
        raise ValueError("refresh_scope must declare mode 'scoped'.")
    raw_repo_ids = scope.get("repo_ids")
    if not isinstance(raw_repo_ids, dict) or not raw_repo_ids:
        raise ValueError("refresh_scope.repo_ids must be a non-empty mapping.")
    repo_ids = {
        str(repo_id)
        for repo_id, selected in raw_repo_ids.items()
        if bool(selected) and str(repo_id).strip()
    }
    if len(repo_ids) != len(raw_repo_ids):
        raise ValueError("refresh_scope.repo_ids entries must map non-empty repo ids to true.")
    return repo_ids


def scoped_refresh_baseline_ref(payload: dict[str, Any]) -> str | None:
    scope = payload.get("refresh_scope")
    if scope is None:
        return None
    if not isinstance(scope, dict):
        raise ValueError("refresh_scope must be a mapping.")
    baseline_ref = scope.get("baseline_ref")
    if not isinstance(baseline_ref, str) or not baseline_ref.strip():
        raise ValueError("refresh_scope.baseline_ref must be a non-empty string.")
    normalized = baseline_ref.strip().lower()
    if len(normalized) != 40 or any(character not in "0123456789abcdef" for character in normalized):
        raise ValueError("refresh_scope.baseline_ref must be a full 40-character commit object id.")
    return normalized


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


def current_remote_name(repo_path: Path) -> str | None:
    code, stdout = git_output(repo_path, "remote")
    if code != 0:
        return None
    names = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not names:
        return None
    return "origin" if "origin" in names else names[0]


def git_ls_remote_head(repo_path: Path, remote_name: str, ref: str) -> str | None:
    """Resolve the current tip commit of `ref` on `remote_name` via a live `git ls-remote`.

    This is a real network query against the repo's own configured remote — it
    reports the remote's current state directly, independent of whatever the
    local checkout happens to have fetched or have checked out.
    """
    code, stdout = git_output(repo_path, "ls-remote", "--exit-code", remote_name, f"refs/heads/{ref}")
    if code != 0 or not stdout:
        return None
    first_line = stdout.splitlines()[0].strip()
    if not first_line:
        return None
    sha = first_line.split()[0].strip()
    if len(sha) != 40 or any(character not in "0123456789abcdef" for character in sha.lower()):
        return None
    return sha.lower()


def source_pin_repo_ids(config: dict[str, Any]) -> list[str]:
    lock_config = config.get("stack_lock", {})
    if not isinstance(lock_config, dict):
        return []
    raw = lock_config.get("source_pin_repo_ids")
    if not isinstance(raw, list):
        return []
    return sorted({str(item) for item in raw if str(item).strip()})


def source_pin_production_ref(repo_id: str, lock_config: dict[str, Any]) -> str | None:
    overrides = lock_config.get("repo_overrides", {})
    if not isinstance(overrides, dict):
        return None
    repo_override = overrides.get(repo_id, {})
    if not isinstance(repo_override, dict):
        return None
    ref = repo_override.get("production_promotion_ref")
    return ref.strip() if isinstance(ref, str) and ref.strip() else None


def resolve_production_promotion(
    repo_path: Path,
    *,
    commit: str,
    dirty: bool,
    remote_name: str | None,
    production_ref: str | None,
) -> tuple[str | None, str]:
    if not production_ref:
        return None, PROMOTION_STATUS_NOT_CONFIGURED
    if not remote_name:
        return None, PROMOTION_STATUS_NO_REMOTE
    remote_commit = git_ls_remote_head(repo_path, remote_name, production_ref)
    if remote_commit is None:
        return None, PROMOTION_STATUS_REMOTE_UNREACHABLE
    if remote_commit != commit:
        return remote_commit, PROMOTION_STATUS_NOT_PROMOTED
    status = PROMOTION_STATUS_PROMOTED_DIRTY_WORKTREE if dirty else PROMOTION_STATUS_PROMOTED_VERIFIED_CLEAN
    return remote_commit, status


def build_source_pins(config: dict[str, Any], root: Path) -> dict[str, dict[str, Any]]:
    registry = config.get("repo_registry", {})
    lock_config = config.get("stack_lock", {}) if isinstance(config.get("stack_lock"), dict) else {}
    pins: dict[str, dict[str, Any]] = {}

    for repo_id in source_pin_repo_ids(config):
        repo_info = registry.get(repo_id)
        if not isinstance(repo_info, dict) or not isinstance(repo_info.get("path"), str):
            raise ValueError(f"Source-pinned repo '{repo_id}' is missing a valid repo_registry entry.")
        coordinate, repo_path = resolve_declared_root_path(
            repo_info["path"],
            root=root,
            label=f"repo_registry.{repo_id}.path",
        )
        if not repo_path.exists():
            raise FileNotFoundError(f"Source-pinned repo path does not exist: {atlas_relative(repo_path, root=root)}")
        if not repo_path.is_dir():
            raise ValueError(f"Source-pinned repo path is not a directory: {atlas_relative(repo_path, root=root)}")
        if not repo_is_git_root(repo_path):
            raise ValueError(f"Source-pinned repo is not a git root: {atlas_relative(repo_path, root=root)}")

        code, commit = git_output(repo_path, "rev-parse", "HEAD")
        if code != 0 or not commit:
            raise ValueError(f"Unable to resolve HEAD for source-pinned repo '{repo_id}'.")
        ref_type, ref = current_ref(repo_path, commit)
        dirty = bool(git_status_lines(repo_path))
        remote_url = current_remote(repo_path)
        remote_name = current_remote_name(repo_path)
        production_ref = source_pin_production_ref(repo_id, lock_config)
        production_commit, production_promotion_status = resolve_production_promotion(
            repo_path,
            commit=commit,
            dirty=dirty,
            remote_name=remote_name,
            production_ref=production_ref,
        )
        pins[repo_id] = {
            "path": coordinate,
            "remote": remote_url,
            "ref_type": ref_type,
            "ref": ref,
            "commit": commit,
            "dirty": dirty,
            "production_ref": production_ref,
            "production_commit": production_commit,
            "production_promotion_status": production_promotion_status,
        }
    return pins


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
        _, repo_path = resolve_declared_root_path(
            repo_info["path"],
            root=root,
            label=f"repo_registry.{repo_id}.path",
        )
        if repo_path.resolve() == root.resolve():
            return str(repo_id)
    return None


def default_lockfile_path(config: dict[str, Any] | None = None, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    stack_config = config or load_stack_config(base / "stack.yaml")
    lock_config = stack_config.get("stack_lock", {})
    if isinstance(lock_config, dict) and isinstance(lock_config.get("path"), str):
        _, lockfile_path = resolve_declared_root_path(
            lock_config["path"],
            root=base,
            label="stack_lock.path",
        )
        return lockfile_path
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
        coordinate, surface_path = resolve_declared_root_path(
            value["path"],
            root=root,
            label=f"stack_lock.excluded_surfaces.{surface_id}.path",
        )
        surfaces[str(surface_id)] = {
            # Preserve the declared stack coordinate even when a local junction
            # supplies the repo during isolated generation.
            "path": coordinate,
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
        "playbook_adoption_status": str(component.get("playbook_adoption_status", "")),
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


def normalize_source_pin(pin: dict[str, Any]) -> dict[str, Any]:
    remote = pin.get("remote")
    production_commit = pin.get("production_commit")
    production_ref = pin.get("production_ref")
    return {
        "path": normalize_slashes(str(pin.get("path", ""))),
        "remote": normalize_slashes(str(remote)) if isinstance(remote, str) and remote else None,
        "ref_type": str(pin.get("ref_type", "")),
        "ref": str(pin.get("ref", "")),
        "commit": str(pin.get("commit", "")),
        "dirty": bool(pin.get("dirty", False)),
        "production_ref": str(production_ref) if isinstance(production_ref, str) and production_ref else None,
        "production_commit": (
            str(production_commit) if isinstance(production_commit, str) and production_commit else None
        ),
        "production_promotion_status": str(pin.get("production_promotion_status", PROMOTION_STATUS_NOT_CONFIGURED)),
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

    raw_source_pins = payload.get("source_pins", {})
    source_pins: dict[str, dict[str, Any]] = {}
    if isinstance(raw_source_pins, dict):
        for pin_id, pin in sorted(
            ((str(raw_key), raw_value) for raw_key, raw_value in raw_source_pins.items()),
            key=lambda item: item[0],
        ):
            if isinstance(pin, dict):
                source_pins[pin_id] = normalize_source_pin(pin)

    body = {
        "schema_version": str(payload.get("schema_version", STACK_LOCK_SCHEMA_VERSION)),
        "stack_manifest_path": normalize_slashes(str(payload.get("stack_manifest_path", "stack.yaml"))),
        "stack_manifest_digest": str(payload.get("stack_manifest_digest", "")),
        "component_count": len(components),
        "components": components,
        "excluded_surfaces": excluded,
        "source_pin_count": len(source_pins),
        "source_pins": source_pins,
    }
    if payload.get("refresh_scope") is not None:
        repo_ids = scoped_refresh_repo_ids(payload)
        baseline_ref = scoped_refresh_baseline_ref(payload)
        body["refresh_scope"] = {
            "mode": "scoped",
            "baseline_ref": baseline_ref,
            "repo_ids": {repo_id: True for repo_id in sorted(repo_ids or set())},
        }
    return body | {"lock_digest": stable_json_digest(body)}


def apply_scoped_component_refresh(
    live_payload: dict[str, Any],
    *,
    baseline_payload: dict[str, Any],
    refresh_repo_ids: set[str],
    baseline_ref: str,
) -> dict[str, Any]:
    normalized_live = normalize_lock_payload(live_payload)
    normalized_baseline = normalize_lock_payload(baseline_payload)
    live_components = normalized_live.get("components", {})
    baseline_components = normalized_baseline.get("components", {})
    if not isinstance(live_components, dict) or not isinstance(baseline_components, dict):
        raise ValueError("Scoped lock refresh requires component mappings.")
    unknown = sorted(refresh_repo_ids - set(live_components))
    if unknown:
        raise ValueError(f"Scoped lock refresh contains unknown repo ids: {', '.join(unknown)}")
    if not refresh_repo_ids:
        raise ValueError("Scoped lock refresh requires at least one repo id.")
    normalized_baseline_ref = baseline_ref.strip().lower()
    if len(normalized_baseline_ref) != 40 or any(
        character not in "0123456789abcdef" for character in normalized_baseline_ref
    ):
        raise ValueError("Scoped lock refresh requires a full 40-character baseline commit object id.")

    for repo_id, live_component in live_components.items():
        if repo_id in refresh_repo_ids:
            continue
        baseline_component = baseline_components.get(repo_id)
        if not isinstance(live_component, dict) or not isinstance(baseline_component, dict):
            raise ValueError(f"Scoped lock refresh requires a baseline component for '{repo_id}'.")
        missing = [field for field in SCOPED_PIN_FIELDS if field not in baseline_component]
        if missing:
            raise ValueError(f"Baseline component '{repo_id}' is missing scoped pin fields: {', '.join(missing)}")
        for field in SCOPED_PIN_FIELDS:
            live_component[field] = baseline_component[field]

    normalized_live["refresh_scope"] = {
        "mode": "scoped",
        "baseline_ref": normalized_baseline_ref,
        "repo_ids": {repo_id: True for repo_id in sorted(refresh_repo_ids)},
    }
    return normalize_lock_payload(normalized_live)


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


def lock_source_pin_field_drift(
    locked: dict[str, Any],
    generated: dict[str, Any],
) -> list[str]:
    return [field for field in SOURCE_PIN_FIELDS if locked.get(field) != generated.get(field)]


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

    source_pin_drift: dict[str, dict[str, Any]] = {}
    locked_source_pins = locked.get("source_pins") if isinstance(locked.get("source_pins"), dict) else {}
    generated_source_pins = generated.get("source_pins") if isinstance(generated.get("source_pins"), dict) else {}
    for pin_id in sorted(set(locked_source_pins) | set(generated_source_pins)):
        locked_pin = locked_source_pins.get(pin_id)
        generated_pin = generated_source_pins.get(pin_id)
        if not isinstance(locked_pin, dict) or not isinstance(generated_pin, dict):
            source_pin_drift[pin_id] = {"kind": "membership", "fields": []}
            continue
        drift_fields = lock_source_pin_field_drift(locked_pin, generated_pin)
        if drift_fields:
            source_pin_drift[pin_id] = {
                "kind": "worktree" if drift_fields == ["dirty"] else "pin",
                "fields": drift_fields,
            }

    metadata_fields = [field for field in LOCK_METADATA_FIELDS if locked.get(field) != generated.get(field)]
    return {
        "locked": locked,
        "generated": generated,
        "components": component_drift,
        "excluded_surfaces": excluded_surface_drift,
        "source_pins": source_pin_drift,
        "metadata_fields": metadata_fields,
        "has_drift": bool(component_drift or excluded_surface_drift or source_pin_drift or metadata_fields),
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
        coordinate, repo_path = resolve_declared_root_path(
            repo_info["path"],
            root=base,
            label=f"repo_registry.{repo_id}.path",
        )
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
            # The manifest path is the contract. Resolved filesystem targets
            # are local implementation details and must not leak into output.
            "path": coordinate,
            "role": str(repo_info.get("role", "")),
            "playbook_adoption_status": str(repo_info.get("playbook_adoption_status", "")),
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
        "source_pins": build_source_pins(stack_config, base),
    }
    return normalize_lock_payload(payload)


def load_lockfile(path: Path) -> dict[str, Any]:
    payload = load_stack_config(path)
    if not isinstance(payload, dict):
        raise ValueError("Lockfile must deserialize to a mapping.")
    return normalize_lock_payload(payload)


def load_lockfile_from_git_ref(*, root: Path, git_ref: str, lockfile_path: Path) -> dict[str, Any]:
    lockfile_ref = atlas_relative(lockfile_path, root=root)
    code, text = git_output(root, "show", f"{git_ref}:{lockfile_ref}")
    if code != 0 or not text:
        raise ValueError(f"Unable to load scoped lock baseline '{git_ref}:{lockfile_ref}'.")
    try:
        import yaml  # type: ignore

        payload = yaml.safe_load(text)
    except ModuleNotFoundError:
        payload = parse_simple_yaml(text)
    if not isinstance(payload, dict):
        raise ValueError("Scoped lock baseline must deserialize to a mapping.")
    return normalize_lock_payload(payload)


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
    *,
    baseline_payload: dict[str, Any] | None = None,
    refresh_repo_ids: set[str] | None = None,
    refresh_baseline_ref: str | None = None,
) -> dict[str, Any]:
    base = (root or atlas_root()).resolve()
    stack_config = config or load_stack_config(base / "stack.yaml")
    dirty_state = stack_root_dirty_state(stack_config, root=base)
    dirty_overrides: dict[str, bool] | None = None
    repo_id = dirty_state.get("repo_id")
    if dirty_state.get("self_refresh_only") and isinstance(repo_id, str):
        dirty_overrides = {repo_id: bool(dirty_state["dirty_effective"])}
    payload = build_lock_payload(config=stack_config, root=base, dirty_overrides=dirty_overrides)
    if refresh_repo_ids is not None:
        if not isinstance(baseline_payload, dict):
            raise ValueError("Scoped lock refresh requires the existing lockfile as its baseline.")
        payload = apply_scoped_component_refresh(
            payload,
            baseline_payload=baseline_payload,
            refresh_repo_ids=refresh_repo_ids,
            baseline_ref=refresh_baseline_ref or "",
        )
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
    parser.add_argument(
        "--refresh-repo-id",
        action="append",
        default=[],
        help="Refresh only the named component pin while preserving unselected pins from the existing lockfile.",
    )
    parser.add_argument(
        "--baseline-git-ref",
        help="Object-addressed git ref supplying unselected component pins for a scoped refresh.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    stack_file = resolve_atlas_path(args.stack_file)
    root = stack_file.parent.resolve()
    config = load_stack_config(stack_file)
    output_path = resolve_atlas_path(args.output_path, root=root) if args.output_path else default_lockfile_path(config, root)
    refresh_repo_ids = {str(repo_id).strip() for repo_id in args.refresh_repo_id if str(repo_id).strip()}
    baseline_payload = None
    if refresh_repo_ids:
        if not args.baseline_git_ref:
            raise ValueError("Scoped lock refresh requires --baseline-git-ref.")
        baseline_payload = load_lockfile_from_git_ref(
            root=root,
            git_ref=args.baseline_git_ref,
            lockfile_path=output_path,
        )
    elif args.baseline_git_ref:
        raise ValueError("--baseline-git-ref is valid only with --refresh-repo-id.")
    artifacts = build_canonical_lockfile_artifacts(
        config=config,
        root=root,
        baseline_payload=baseline_payload,
        refresh_repo_ids=refresh_repo_ids or None,
        refresh_baseline_ref=args.baseline_git_ref,
    )
    payload = artifacts["payload"]
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
                "source_pin_count": payload["source_pin_count"],
                "refresh_repo_ids": sorted(refresh_repo_ids),
                "baseline_git_ref": args.baseline_git_ref,
                "lock_digest": payload["lock_digest"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
