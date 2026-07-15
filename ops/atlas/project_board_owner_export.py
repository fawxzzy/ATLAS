from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_REF = "docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json"
MARKER_BOOK_REF = "docs/atlas-book/02-lanes-and-markers.md"
OUTPUT_ROOT_REF = "docs/registry/project-board-owner-exports"
ATLAS_OUTPUT_NAME = "atlas.project-board.owner-export.v1.json"
CORTEX_OUTPUT_NAME = "cortex.project-board.owner-export.v1.json"

CONTRACT_VERSION = "atlas.project-board.owner-export.v1"
CARD_CONTRACT_VERSION = "atlas.card-record.v2"
ADAPTER_ID = "atlas-full-system-registry-v1"

ATLAS_GOVERNANCE_BACKLOG_OWNERS = frozenset(
    {
        "stack-root",
        "repository-owners",
        "operator-security",
        "github-governance",
        "project-owners",
    }
)
CORTEX_RECORD_IDS = (
    "lane-cortex-context-synthesis",
    "lane-cortex-boundary-decision",
)
NON_EXECUTABLE_LIFECYCLES = frozenset({"intake", "planning", "completed", "archived", "blocked"})


class ProjectBoardOwnerExportError(RuntimeError):
    pass


def _read_normalized_bytes(path: Path) -> bytes:
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _utc_timestamp(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProjectBoardOwnerExportError(f"{field_name} must be a non-empty ISO 8601 timestamp.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProjectBoardOwnerExportError(f"{field_name} must be an ISO 8601 timestamp.") from exc
    if parsed.tzinfo is None:
        raise ProjectBoardOwnerExportError(f"{field_name} must include a timezone.")
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _load_registry(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(_read_normalized_bytes(path))
    except json.JSONDecodeError as exc:
        raise ProjectBoardOwnerExportError(f"Malformed registry JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ProjectBoardOwnerExportError("The full-system registry must be a JSON object.")
    if payload.get("schema") != "atlas.full_system_reevaluation.lanes.v1":
        raise ProjectBoardOwnerExportError("Unexpected full-system registry schema.")
    if not isinstance(payload.get("lanes"), list) or not isinstance(payload.get("backlog_candidates"), list):
        raise ProjectBoardOwnerExportError("The full-system registry must contain lanes and backlog_candidates arrays.")
    return payload


def _index_records(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = [*registry["lanes"], *registry["backlog_candidates"]]
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id:
            raise ProjectBoardOwnerExportError("Every registry record must have a non-empty id.")
        if record_id in indexed:
            raise ProjectBoardOwnerExportError(f"Duplicate registry record id: {record_id}")
        indexed[record_id] = record
    return indexed


def _verify_marker_reconciliation(registry: dict[str, Any], marker_text: str) -> None:
    github = _index_records(registry).get("lane-github-control-plane-integration")
    if github is None:
        raise ProjectBoardOwnerExportError("The GitHub control-plane lane is missing.")
    marker_match = re.search(r"^- GitHub Control-Plane Integration: `(?P<percentage>[0-9.]+)%`$", marker_text, re.MULTILINE)
    if marker_match is None:
        raise ProjectBoardOwnerExportError("The GitHub control-plane marker is missing from the Atlas Book.")
    if marker_match.group("percentage") != "100":
        raise ProjectBoardOwnerExportError("The Atlas Book GitHub marker is not closed at 100%.")
    if github.get("status") != "complete" or github.get("percentage") != 100 or github.get("completed_units") != 8:
        raise ProjectBoardOwnerExportError("The machine registry conflicts with the accepted GitHub 8/8 closeout.")
    denominator = github.get("denominator")
    if not isinstance(denominator, dict) or denominator.get("value") != 8:
        raise ProjectBoardOwnerExportError("The GitHub lane denominator must remain 8.")


def _source_revision(registry_bytes: bytes, marker_bytes: bytes) -> str:
    digest_input = b"registry\0" + registry_bytes + b"\0marker-book\0" + marker_bytes
    return f"sha256:{_sha256(digest_input)}"


def _record_card_type(record: dict[str, Any]) -> str:
    classification = str(record.get("classification", "")).lower()
    if "architecture" in classification or "control-plane" in classification or "runtime" in classification:
        return "architecture"
    if "doc" in classification:
        return "documentation"
    if "automation" in classification or "command" in classification or "adapter" in classification:
        return "automation"
    if "research" in classification or "inventory" in classification:
        return "research"
    if "migration" in classification or "adoption" in classification or "convergence" in classification:
        return "migration"
    if "health" in classification or "security" in classification or "reliability" in classification:
        return "reliability"
    if "hygiene" in classification or "retention" in classification:
        return "technical-debt"
    return "governance"


def _record_status(source_status: str) -> str:
    if source_status == "candidate":
        return "candidate"
    if source_status in {"active", "complete"}:
        return "active"
    raise ProjectBoardOwnerExportError(f"Unsupported registry status: {source_status}")


def _record_lifecycle(source_status: str, *, marker_parent: bool) -> str:
    if source_status == "complete":
        return "completed"
    if marker_parent:
        return "planning"
    if source_status == "active":
        return "in-progress"
    if source_status == "candidate":
        return "planning"
    raise ProjectBoardOwnerExportError(f"Unsupported registry status: {source_status}")


def _as_string_list(record: dict[str, Any], field: str) -> list[str]:
    value = record.get(field, [])
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ProjectBoardOwnerExportError(f"{record.get('id', '<unknown>')}.{field} must be a list of non-empty strings.")
    return list(value)


def _export_card(
    record: dict[str, Any],
    *,
    project_id: str,
    board_id: str,
    generated_at: str,
    source_section: str,
    marker_parent: bool,
    projection_role: str,
) -> dict[str, Any]:
    record_id = str(record["id"])
    source_status = str(record.get("status"))
    lifecycle = _record_lifecycle(source_status, marker_parent=marker_parent)
    if marker_parent and lifecycle not in NON_EXECUTABLE_LIFECYCLES:
        raise ProjectBoardOwnerExportError(f"Marker parent {record_id} became executable without an epic contract.")
    source_ref = f"{REGISTRY_REF}#{record_id}"
    denominator = record.get("denominator")
    if denominator is not None and not isinstance(denominator, dict):
        raise ProjectBoardOwnerExportError(f"{record_id}.denominator must be an object when present.")

    updated_at = _utc_timestamp(record.get("last_audited_at") or generated_at, field_name=f"{record_id}.updated_at")
    return {
        "idempotency_key": f"pbk_{project_id}_{record_id}_v1",
        "record_kind": "marker" if marker_parent else "project-work",
        "record_status": _record_status(source_status),
        "record": {
            "contract_version": CARD_CONTRACT_VERSION,
            "card_id": record_id,
            "project_id": project_id,
            "board_id": board_id,
            "title": str(record["title"]),
            "description": str(record["scope"]),
            "card_type": _record_card_type(record),
            "lifecycle": lifecycle,
            "priority": None,
            "owner": str(record["owner"]),
            "dependencies": _as_string_list(record, "dependencies"),
            "board_version": 1,
            "updated_at": updated_at,
            "source_ref": source_ref,
            "extensions": {
                "source_section": source_section,
                "source_classification": str(record["classification"]),
                "source_status": source_status,
                "measurement_unit": record.get("measurement_unit"),
                "percentage": record.get("percentage"),
                "completed_units": record.get("completed_units"),
                "denominator": denominator,
                "projection_role": projection_role,
                "seed_disposition": "completed" if lifecycle == "completed" else "current",
            },
        },
        "source": {
            "source_id": "atlas-full-system-registry",
            "source_ref": source_ref,
            "source_status": "current",
            "source_updated_at": updated_at,
        },
        "content": {
            "summary": str(record["scope"]),
            "objective": str(record["scope"]),
            "acceptance_criteria": _as_string_list(record, "definition_of_done"),
            "discoveries": [
                "Priority is unresolved in the owner source and remains explicitly null.",
                *(["This record is a non-executable marker parent; child outcomes remain separate."] if marker_parent else []),
            ],
            "next_actions": [],
            "blockers": [],
            "evidence": _as_string_list(record, "evidence_sources"),
        },
        "relationships": {
            "parent_card_id": record.get("parent_lane_id"),
            "duplicate_of": None,
            "superseded_by": None,
        },
    }


def _build_envelope(
    *,
    project_id: str,
    records: list[tuple[str, dict[str, Any]]],
    marker_parent_ids: set[str],
    generated_at: str,
    source_revision: str,
    registry_revision: str,
    marker_revision: str,
    projection_role: str,
    extensions: dict[str, Any],
) -> dict[str, Any]:
    board_id = f"discordos:project-feedback:{project_id}"
    digest_prefix = source_revision.removeprefix("sha256:")[:12]
    cards = [
        _export_card(
            record,
            project_id=project_id,
            board_id=board_id,
            generated_at=generated_at,
            source_section=section,
            marker_parent=record["id"] in marker_parent_ids,
            projection_role=projection_role,
        )
        for section, record in records
    ]
    cards.sort(key=lambda card: card["record"]["card_id"])
    return {
        "contract_version": CONTRACT_VERSION,
        "export_id": f"pbe_{project_id}_{digest_prefix}",
        "project_id": project_id,
        "board_id": board_id,
        "owner": "stack-root",
        "adapter_id": ADAPTER_ID,
        "source_revision": source_revision,
        "generated_at": generated_at,
        "sources": [
            {
                "source_id": "atlas-full-system-registry",
                "kind": "json",
                "repository": "atlas-root",
                "path": REGISTRY_REF,
                "revision": f"sha256:{registry_revision}",
                "observed_at": generated_at,
            },
            {
                "source_id": "atlas-marker-book",
                "kind": "markdown",
                "repository": "atlas-root",
                "path": MARKER_BOOK_REF,
                "revision": f"sha256:{marker_revision}",
                "observed_at": generated_at,
            },
        ],
        "cards": cards,
        "extensions": extensions,
    }


def build_project_board_owner_exports(
    *,
    registry_path: Path | None = None,
    marker_book_path: Path | None = None,
) -> dict[str, dict[str, Any]]:
    registry_path = registry_path or ROOT / REGISTRY_REF
    marker_book_path = marker_book_path or ROOT / MARKER_BOOK_REF
    registry_bytes = _read_normalized_bytes(registry_path)
    marker_bytes = _read_normalized_bytes(marker_book_path)
    registry = _load_registry(registry_path)
    marker_text = marker_bytes.decode("utf-8")
    _verify_marker_reconciliation(registry, marker_text)
    indexed = _index_records(registry)
    generated_at = _utc_timestamp(registry.get("generated_at"), field_name="registry.generated_at")

    top_lanes = list(registry["lanes"])
    atlas_backlog = [
        record for record in registry["backlog_candidates"] if record.get("owner") in ATLAS_GOVERNANCE_BACKLOG_OWNERS
    ]
    atlas_parent_ids = {str(record["parent_lane_id"]) for record in atlas_backlog if record.get("parent_lane_id")}
    top_ids = {str(record["id"]) for record in top_lanes}
    missing_parents = sorted(atlas_parent_ids - top_ids)
    if missing_parents:
        raise ProjectBoardOwnerExportError(f"Atlas governance backlog references missing parents: {missing_parents}")
    atlas_records = [("lanes", record) for record in top_lanes] + [
        ("backlog_candidates", record) for record in atlas_backlog
    ]

    cortex_records: list[tuple[str, dict[str, Any]]] = []
    for record_id in CORTEX_RECORD_IDS:
        record = indexed.get(record_id)
        if record is None:
            raise ProjectBoardOwnerExportError(f"Missing Cortex record: {record_id}")
        section = "lanes" if record in top_lanes else "backlog_candidates"
        cortex_records.append((section, record))
    cortex_parent_ids = {"lane-cortex-context-synthesis"}

    revision = _source_revision(registry_bytes, marker_bytes)
    registry_revision = _sha256(registry_bytes)
    marker_revision = _sha256(marker_bytes)
    atlas_direct_count = sum(1 for record in top_lanes if record["id"] not in atlas_parent_ids)

    return {
        "atlas": _build_envelope(
            project_id="atlas",
            records=atlas_records,
            marker_parent_ids=atlas_parent_ids,
            generated_at=generated_at,
            source_revision=revision,
            registry_revision=registry_revision,
            marker_revision=marker_revision,
            projection_role="stack-coordination",
            extensions={
                "selection": {
                    "top_level_lane_count": len(top_lanes),
                    "marker_parent_count": len(atlas_parent_ids),
                    "direct_lane_count": atlas_direct_count,
                    "governance_backlog_count": len(atlas_backlog),
                    "total_record_count": len(atlas_records),
                    "backlog_owner_allowlist": sorted(ATLAS_GOVERNANCE_BACKLOG_OWNERS),
                },
                "priority_policy": "preserve-unknown-as-null",
                "discord_mutation_authorized": False,
            },
        ),
        "cortex": _build_envelope(
            project_id="cortex",
            records=cortex_records,
            marker_parent_ids=cortex_parent_ids,
            generated_at=generated_at,
            source_revision=revision,
            registry_revision=registry_revision,
            marker_revision=marker_revision,
            projection_role="root-owned-subsystem",
            extensions={
                "selection": {
                    "record_ids": list(CORTEX_RECORD_IDS),
                    "total_record_count": len(cortex_records),
                },
                "priority_policy": "preserve-unknown-as-null",
                "discord_mutation_authorized": False,
            },
        ),
    }


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"


def write_project_board_owner_exports(
    exports: dict[str, dict[str, Any]],
    *,
    output_root: Path,
    check: bool,
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    outputs = {
        output_root / ATLAS_OUTPUT_NAME: exports["atlas"],
        output_root / CORTEX_OUTPUT_NAME: exports["cortex"],
    }
    drift: list[str] = []
    for path, payload in outputs.items():
        expected = _canonical_json(payload)
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                drift.append(str(path))
        else:
            path.write_text(expected, encoding="utf-8", newline="\n")
    if drift:
        raise ProjectBoardOwnerExportError(f"Owner exports are stale or missing: {', '.join(drift)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic Atlas and Cortex project-board owner exports.")
    parser.add_argument("--registry", type=Path, default=ROOT / REGISTRY_REF)
    parser.add_argument("--marker-book", type=Path, default=ROOT / MARKER_BOOK_REF)
    parser.add_argument("--output-root", type=Path, default=ROOT / OUTPUT_ROOT_REF)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        exports = build_project_board_owner_exports(registry_path=args.registry, marker_book_path=args.marker_book)
        write_project_board_owner_exports(exports, output_root=args.output_root, check=args.check)
    except (OSError, ProjectBoardOwnerExportError) as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True))
        return 1
    print(
        json.dumps(
            {
                "status": "ok",
                "check": args.check,
                "source_revision": exports["atlas"]["source_revision"],
                "atlas_cards": len(exports["atlas"]["cards"]),
                "cortex_cards": len(exports["cortex"]["cards"]),
                "discord_mutation_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
