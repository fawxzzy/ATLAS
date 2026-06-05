from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes
from ops.cortex._artifacts import stable_json_digest, write_json
from ops.cortex.shadow_agent_registry import load_shadow_agent_registry, resolve_shadow_agent_for_consumption

SHADOW_MARKER_CHECKPOINT_CONTRACT_VERSION = "atlas.cortex.shadow-marker-checkpoint.v1"
MARKER_CHECKPOINT_AGENT_ID = "marker-checkpoint-shadow"
ACTIVE_FRONT_PAGE_HEADER = "## Active Front-Page Marker Table"
SUPPORTING_OPEN_HEADER = "## Supporting Open Markers"
MARKER_LINE_RE = re.compile(r"^- (?P<name>.+?): `(?P<value>\d+%)`$")
NEXT_LANE_LINE_RE = re.compile(r"the exact next lane now routes to `(?P<lane>[^`]+)`", re.IGNORECASE)


def default_marker_checkpoint_json_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "shadow-agent-consumption" / "marker-checkpoint.latest.json"


def default_marker_checkpoint_markdown_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "shadow-agent-consumption" / "marker-checkpoint.latest.md"


@dataclass(frozen=True)
class PersistedShadowMarkerCheckpointArtifact:
    artifact_path: Path
    summary_path: Path | None
    payload_digest: str
    payload: dict[str, Any]
    summary: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _section_lines(text: str, header: str) -> list[str]:
    lines = text.splitlines()
    try:
        start = lines.index(header) + 1
    except ValueError as exc:
        raise ValueError(f"Missing required marker section: {header}") from exc
    results: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        stripped = line.strip()
        if stripped:
            results.append(stripped)
    return results


def _parse_marker_section(text: str, header: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line in _section_lines(text, header):
        match = MARKER_LINE_RE.match(line)
        if match is None:
            continue
        name = match.group("name").strip().replace("`", "")
        entries.append(
            {
                "name": name,
                "value": match.group("value").strip(),
            }
        )
    if not entries:
        raise ValueError(f"No marker entries found under {header}.")
    return entries


def _extract_next_lane(restart_text: str) -> str:
    for line in restart_text.splitlines():
        match = NEXT_LANE_LINE_RE.search(line)
        if match is not None:
            return match.group("lane").strip()
    raise ValueError("Restart surface does not contain the expected next-lane route line.")


def _load_required_text(path: Path, label: str) -> str:
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"{label} not found: {normalize_slashes(str(resolved))}")
    return resolved.read_text(encoding="utf-8")


def build_shadow_marker_checkpoint_payload(
    *,
    root: Path | None = None,
    marker_surface_path: Path | None = None,
    restart_surface_path: Path | None = None,
) -> dict[str, Any]:
    base = (root or atlas_root()).resolve()
    registry = load_shadow_agent_registry(root=base)
    agent = resolve_shadow_agent_for_consumption(MARKER_CHECKPOINT_AGENT_ID, root=base)

    marker_path = (marker_surface_path or (base / "docs" / "atlas-book" / "02-lanes-and-markers.md")).resolve()
    restart_path = (restart_surface_path or (base / "docs" / "atlas-book" / "12-restart-and-handoff-guide.md")).resolve()
    marker_text = _load_required_text(marker_path, "ATLAS marker surface")
    restart_text = _load_required_text(restart_path, "ATLAS restart surface")

    active_front_page = _parse_marker_section(marker_text, ACTIVE_FRONT_PAGE_HEADER)
    supporting_open = _parse_marker_section(marker_text, SUPPORTING_OPEN_HEADER)
    next_lane = _extract_next_lane(restart_text)

    return {
        "contract_version": SHADOW_MARKER_CHECKPOINT_CONTRACT_VERSION,
        "generated_at": _utc_now(),
        "stack_root": normalize_slashes(str(base)),
        "agent": {
            "contract_id": agent.contract_id,
            "id": agent.agent_id,
            "family_name": agent.family_name,
            "trigger": agent.trigger,
            "trigger_family": agent.trigger_family,
            "purpose": agent.purpose,
            "admissibility_state": agent.admissibility_state,
            "stage": agent.stage,
            "runnable": agent.runnable,
            "owner_boundary": agent.owner_boundary,
            "non_claim_boundary": agent.non_claim_boundary,
            "fallback_path": agent.fallback_path,
            "fallback_behavior": agent.fallback_behavior,
        },
        "consumption_status": "shadow-consumed",
        "authority": {
            "has_production_authority": False,
            "can_ratchet_markers": False,
            "can_mutate_truth": False,
        },
        "marker_checkpoint": {
            "active_front_page": active_front_page,
            "supporting_open": supporting_open,
            "next_lane_route": next_lane,
        },
        "source_receipts": list(registry.source_receipts),
        "source_refs": [
            "docs/atlas-book/02-lanes-and-markers.md",
            "docs/atlas-book/12-restart-and-handoff-guide.md",
            "docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-CONTRACT-FIRST-AGENT-SHADOWING-PASS-1-2026-06-01.md",
        ],
    }


def render_shadow_marker_checkpoint(payload: dict[str, Any]) -> str:
    agent = payload["agent"]
    authority = payload["authority"]
    checkpoint = payload["marker_checkpoint"]
    lines = [
        "# Cortex Shadow Marker Checkpoint",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Agent: `{agent['id']}`",
        f"- Contract: `{agent['contract_id']}`",
        f"- Trigger family: {agent['trigger_family']}",
        f"- Admissibility: `{agent['admissibility_state']}`",
        f"- Consumption status: `{payload['consumption_status']}`",
        f"- Next lane route: `{checkpoint['next_lane_route']}`",
        f"- Production authority: `{'yes' if authority['has_production_authority'] else 'no'}`",
        f"- Can ratchet markers: `{'yes' if authority['can_ratchet_markers'] else 'no'}`",
        f"- Can mutate truth: `{'yes' if authority['can_mutate_truth'] else 'no'}`",
        "",
        "## Boundaries",
        f"- Owner boundary: {agent['owner_boundary']}",
        f"- Non-claim boundary: {agent['non_claim_boundary']}",
        f"- Fallback path: `{agent['fallback_path']}`",
        f"- Fallback: {agent['fallback_behavior']}",
        "",
        "## Active Front-Page Markers",
    ]
    for item in checkpoint["active_front_page"]:
        lines.append(f"- `{item['name']}`: `{item['value']}`")
    lines.extend(["", "## Supporting Open Markers"])
    for item in checkpoint["supporting_open"]:
        lines.append(f"- `{item['name']}`: `{item['value']}`")
    return "\n".join(lines) + "\n"


def persist_shadow_marker_checkpoint_artifact(
    *,
    root: Path | None = None,
    output_json_path: Path | None = None,
    output_summary_path: Path | None = None,
    write_summary: bool = True,
    marker_surface_path: Path | None = None,
    restart_surface_path: Path | None = None,
) -> PersistedShadowMarkerCheckpointArtifact:
    base = (root or atlas_root()).resolve()
    artifact_path = (output_json_path or default_marker_checkpoint_json_path(base)).resolve()
    summary_path = (
        (output_summary_path or default_marker_checkpoint_markdown_path(base)).resolve() if write_summary else None
    )
    payload = build_shadow_marker_checkpoint_payload(
        root=base,
        marker_surface_path=marker_surface_path,
        restart_surface_path=restart_surface_path,
    )
    summary = render_shadow_marker_checkpoint(payload)
    write_json(artifact_path, payload)
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
    return PersistedShadowMarkerCheckpointArtifact(
        artifact_path=artifact_path,
        summary_path=summary_path,
        payload_digest=stable_json_digest(payload),
        payload=payload,
        summary=summary,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Persist a deterministic contract-consumption proof artifact for marker-checkpoint-shadow."
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--marker-surface-path", type=Path)
    parser.add_argument("--restart-surface-path", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-summary", type=Path)
    parser.add_argument("--no-write-summary", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    base = args.root.resolve()
    try:
        artifact = persist_shadow_marker_checkpoint_artifact(
            root=base,
            output_json_path=args.output_json.resolve() if args.output_json else None,
            output_summary_path=args.output_summary.resolve() if args.output_summary else None,
            write_summary=not args.no_write_summary,
            marker_surface_path=args.marker_surface_path.resolve() if args.marker_surface_path else None,
            restart_surface_path=args.restart_surface_path.resolve() if args.restart_surface_path else None,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.print_json:
        print(json.dumps(artifact.payload, indent=2))
    elif not args.quiet:
        print(artifact.summary, end="")
        print(f"JSON artifact: {normalize_slashes(str(artifact.artifact_path))}")
        if artifact.summary_path is not None:
            print(f"Summary report: {normalize_slashes(str(artifact.summary_path))}")
        print(f"Payload digest: {artifact.payload_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
