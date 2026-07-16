from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ops._atlas import load_stack_config


class OperationalIdentityError(ValueError):
    """Raised when a declared operational identity is absent or malformed."""


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise OperationalIdentityError(f"{field} must be an object.")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OperationalIdentityError(f"{field} must be a non-empty string.")
    return value.strip()


def _strings(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise OperationalIdentityError(f"{field} must be a non-empty string array.")
    items = tuple(_string(item, f"{field}[]") for item in value)
    if len(set(items)) != len(items):
        raise OperationalIdentityError(f"{field} must not contain duplicates.")
    return items


def _https_origin(value: Any, field: str) -> str:
    origin = _string(value, field)
    parsed = urlparse(origin)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise OperationalIdentityError(f"{field} must be an HTTPS origin without a path, query, or fragment.")
    return origin.rstrip("/")


def operational_identity_from_config(config: dict[str, Any], repo_id: str) -> OrderedDict[str, Any]:
    registry = _mapping(config.get("repo_registry"), "repo_registry")
    repo = _mapping(registry.get(repo_id), f"repo_registry.{repo_id}")
    local_path = _string(repo.get("path"), f"repo_registry.{repo_id}.path")
    identity = _mapping(repo.get("identity"), f"repo_registry.{repo_id}.identity")
    github = _mapping(identity.get("github"), f"repo_registry.{repo_id}.identity.github")
    vercel = _mapping(identity.get("vercel"), f"repo_registry.{repo_id}.identity.vercel")
    public = _mapping(identity.get("public"), f"repo_registry.{repo_id}.identity.public")
    board = _mapping(identity.get("board"), f"repo_registry.{repo_id}.identity.board")

    display_name = _string(identity.get("display_name"), f"repo_registry.{repo_id}.identity.display_name")
    legacy_display_names = _strings(
        identity.get("legacy_display_names"),
        f"repo_registry.{repo_id}.identity.legacy_display_names",
    )
    github_repository = _string(github.get("repository"), f"repo_registry.{repo_id}.identity.github.repository")
    if github_repository.count("/") != 1:
        raise OperationalIdentityError(
            f"repo_registry.{repo_id}.identity.github.repository must use owner/repository form."
        )

    vercel_project = _string(vercel.get("project"), f"repo_registry.{repo_id}.identity.vercel.project")
    vercel_project_id = _string(vercel.get("project_id"), f"repo_registry.{repo_id}.identity.vercel.project_id")
    legacy_vercel_projects = _strings(
        vercel.get("legacy_project_aliases"),
        f"repo_registry.{repo_id}.identity.vercel.legacy_project_aliases",
    )
    if vercel_project in legacy_vercel_projects:
        raise OperationalIdentityError("The canonical Vercel project cannot also be a legacy alias.")

    public_origin = _https_origin(public.get("origin"), f"repo_registry.{repo_id}.identity.public.origin")
    www_redirect_origin = _https_origin(
        public.get("www_redirect_origin"),
        f"repo_registry.{repo_id}.identity.public.www_redirect_origin",
    )
    compatibility_origins = tuple(
        _https_origin(item, f"repo_registry.{repo_id}.identity.public.compatibility_origins[]")
        for item in _strings(
            public.get("compatibility_origins"),
            f"repo_registry.{repo_id}.identity.public.compatibility_origins",
        )
    )
    if len(set(compatibility_origins)) != len(compatibility_origins):
        raise OperationalIdentityError("Compatibility origins must not contain duplicates.")
    if public_origin in compatibility_origins or www_redirect_origin in compatibility_origins:
        raise OperationalIdentityError("Canonical and redirect origins cannot also be compatibility origins.")

    board_owner_id = _string(board.get("owner_id"), f"repo_registry.{repo_id}.identity.board.owner_id")
    board_display_name = _string(board.get("display_name"), f"repo_registry.{repo_id}.identity.board.display_name")
    if board_owner_id != repo_id:
        raise OperationalIdentityError(f"Board owner_id must preserve the stable repo id '{repo_id}'.")
    if board_display_name != display_name:
        raise OperationalIdentityError("Board display_name must match the canonical display name.")

    aliases = tuple(
        dict.fromkeys(
            (
                repo_id,
                display_name,
                *legacy_display_names,
                vercel_project,
                *legacy_vercel_projects,
                public_origin,
                www_redirect_origin,
                *compatibility_origins,
                github_repository,
            )
        )
    )
    return OrderedDict(
        [
            ("logical_id", repo_id),
            ("local_path", local_path),
            ("display_name", display_name),
            ("legacy_display_names", legacy_display_names),
            ("github_repository", github_repository),
            ("vercel_project", vercel_project),
            ("vercel_project_id", vercel_project_id),
            ("legacy_vercel_projects", legacy_vercel_projects),
            ("public_origin", public_origin),
            ("www_redirect_origin", www_redirect_origin),
            ("compatibility_origins", compatibility_origins),
            ("board_owner_id", board_owner_id),
            ("board_display_name", board_display_name),
            ("accepted_aliases", aliases),
        ]
    )


def load_operational_identity(root: Path, repo_id: str) -> OrderedDict[str, Any]:
    return operational_identity_from_config(load_stack_config(root / "stack.yaml"), repo_id)


def resolve_operational_identity(identity: dict[str, Any], candidate: str) -> str:
    aliases = identity.get("accepted_aliases")
    if not isinstance(aliases, (list, tuple)) or candidate not in aliases:
        raise OperationalIdentityError(f"Unknown operational identity alias: {candidate}")
    return _string(identity.get("logical_id"), "logical_id")


def canonicalize_vercel_project(identity: dict[str, Any], *, project_id: str, project_name: str) -> str:
    expected_id = _string(identity.get("vercel_project_id"), "vercel_project_id")
    if project_id != expected_id:
        raise OperationalIdentityError(f"Unknown Vercel project id: {project_id}")
    canonical = _string(identity.get("vercel_project"), "vercel_project")
    aliases = identity.get("legacy_vercel_projects")
    accepted = {canonical, *(aliases if isinstance(aliases, (list, tuple)) else ())}
    if project_name not in accepted:
        raise OperationalIdentityError(f"Unknown Vercel project name for {project_id}: {project_name}")
    return canonical


def inventory_identity_projection(identity: dict[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict(
        [
            ("display_name", identity["display_name"]),
            ("legacy_display_names", list(identity["legacy_display_names"])),
            ("github_repository", identity["github_repository"]),
            ("vercel_project", identity["vercel_project"]),
            ("vercel_project_id", identity["vercel_project_id"]),
            ("legacy_vercel_projects", list(identity["legacy_vercel_projects"])),
            ("public_origin", identity["public_origin"]),
            ("www_redirect_origin", identity["www_redirect_origin"]),
            ("compatibility_origins", list(identity["compatibility_origins"])),
            ("board_owner_id", identity["board_owner_id"]),
            ("board_display_name", identity["board_display_name"]),
        ]
    )
