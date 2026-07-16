from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Any

from ops.atlas.operational_identity import (
    OperationalIdentityError,
    canonicalize_vercel_project,
    load_operational_identity,
)


ROOT = Path(__file__).resolve().parents[2]
FAWXZZYWEB_IDENTITY = load_operational_identity(ROOT, "trove")


GOVERNED_PROJECTS_BY_ID: OrderedDict[str, OrderedDict[str, str]] = OrderedDict(
    [
        (
            "prj_C2RSEa34OblHfhuEpVChRQQZSjuG",
            OrderedDict([("project_name", "fawxzzy-discordos"), ("repo_logical_id", "discordos")]),
        ),
        (
            "prj_rtlFVOMFAWCRoJ3SQjHloi89881K",
            OrderedDict([("project_name", "fawxzzy-fitness"), ("repo_logical_id", "fitness")]),
        ),
        (
            "prj_t3zothbtj9DExrh3FjMsH98hwwSZ",
            OrderedDict([("project_name", "fawxzzy-mazer"), ("repo_logical_id", "mazer")]),
        ),
        (
            str(FAWXZZYWEB_IDENTITY["vercel_project_id"]),
            OrderedDict(
                [
                    ("project_name", str(FAWXZZYWEB_IDENTITY["vercel_project"])),
                    ("repo_logical_id", str(FAWXZZYWEB_IDENTITY["logical_id"])),
                ]
            ),
        ),
        (
            "prj_o37CPLlESB6Zybe8GB74BX3wrkpy",
            OrderedDict([("project_name", "fawxzzy-foundation"), ("repo_logical_id", "foundation")]),
        ),
    ]
)


def accepted_project_names(project_id: str) -> tuple[str, ...]:
    meta = GOVERNED_PROJECTS_BY_ID.get(project_id)
    if meta is None:
        return ()
    canonical = str(meta["project_name"])
    if project_id != FAWXZZYWEB_IDENTITY["vercel_project_id"]:
        return (canonical,)
    return (canonical, *tuple(str(item) for item in FAWXZZYWEB_IDENTITY["legacy_vercel_projects"]))


def normalize_project_name(*, project_id: str, project_name: str) -> str:
    meta = GOVERNED_PROJECTS_BY_ID.get(project_id)
    if meta is None:
        raise OperationalIdentityError(f"Unknown Vercel project id: {project_id}")
    if project_id == FAWXZZYWEB_IDENTITY["vercel_project_id"]:
        return canonicalize_vercel_project(
            FAWXZZYWEB_IDENTITY,
            project_id=project_id,
            project_name=project_name,
        )
    canonical = str(meta["project_name"])
    if project_name != canonical:
        raise OperationalIdentityError(f"Unknown Vercel project name for {project_id}: {project_name}")
    return canonical


GOVERNED_PROJECTS_BY_SLUG: OrderedDict[str, OrderedDict[str, str]] = OrderedDict(
    (
        str(meta["project_name"]),
        OrderedDict([("project_id", project_id), ("repo_logical_id", str(meta["repo_logical_id"]))]),
    )
    for project_id, meta in GOVERNED_PROJECTS_BY_ID.items()
)


PROJECT_SLUG_ALIASES: dict[str, str] = {
    alias: str(FAWXZZYWEB_IDENTITY["vercel_project"])
    for alias in FAWXZZYWEB_IDENTITY["legacy_vercel_projects"]
}


def normalize_project_slug(*, project_slug: str, project_id: str) -> str:
    canonical = PROJECT_SLUG_ALIASES.get(project_slug, project_slug)
    meta = GOVERNED_PROJECTS_BY_SLUG.get(canonical)
    if meta is None:
        raise OperationalIdentityError(f"Unknown Vercel project slug: {project_slug}")
    if str(meta["project_id"]) != project_id:
        raise OperationalIdentityError(
            f"Vercel project slug/id mismatch: {project_slug} does not map to {project_id}"
        )
    return canonical


def identity_for_repo(repo_id: str) -> dict[str, Any] | None:
    return FAWXZZYWEB_IDENTITY if repo_id == FAWXZZYWEB_IDENTITY["logical_id"] else None
