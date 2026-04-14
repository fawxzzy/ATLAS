from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ops._atlas import atlas_relative, atlas_root
from ops.cortex._artifacts import stable_json_digest, write_json

OBSERVATION_CONTRACT_VERSION = "atlas.observation.v1"
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
