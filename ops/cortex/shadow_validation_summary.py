from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes
from ops.cortex._artifacts import stable_json_digest, write_json
from ops.cortex.current_state import default_validation_receipt_path
from ops.cortex.shadow_agent_registry import load_shadow_agent_registry, resolve_shadow_agent_for_consumption

SHADOW_VALIDATION_SUMMARY_CONTRACT_VERSION = "atlas.cortex.shadow-validation-summary.v1"
VALIDATION_SUMMARY_AGENT_ID = "validation-summary-shadow"


def default_shadow_validation_summary_dir(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "shadow-agent-consumption"


def default_shadow_validation_summary_json_path(root: Path | None = None) -> Path:
    return default_shadow_validation_summary_dir(root) / "validation-summary.latest.json"


def default_shadow_validation_summary_markdown_path(root: Path | None = None) -> Path:
    return default_shadow_validation_summary_dir(root) / "validation-summary.latest.md"


@dataclass(frozen=True)
class PersistedShadowValidationSummaryArtifact:
    artifact_path: Path
    summary_path: Path | None
    payload_digest: str
    payload: dict[str, Any]
    summary: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_counts(summary: dict[str, Any]) -> dict[str, int]:
    counts = {
        "critical": int(summary.get("critical", 0) or 0),
        "error": int(summary.get("error", 0) or 0),
        "warning": int(summary.get("warning", 0) or 0),
        "info": int(summary.get("info", 0) or 0),
    }
    counts["total"] = int(summary.get("total", sum(counts.values())) or sum(counts.values()))
    return counts


def _ordered_unique_strings(values: list[Any]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        ordered.append(stripped)
    return ordered


def build_shadow_validation_summary_payload(
    *,
    root: Path | None = None,
    validation_path: Path | None = None,
) -> dict[str, Any]:
    base = (root or atlas_root()).resolve()
    registry = load_shadow_agent_registry(root=base)
    agent = resolve_shadow_agent_for_consumption(VALIDATION_SUMMARY_AGENT_ID, root=base)

    validation_receipt_path = (validation_path or default_validation_receipt_path(base)).resolve()
    if not validation_receipt_path.exists():
        raise FileNotFoundError(
            f"Stack validation receipt not found: {normalize_slashes(str(validation_receipt_path))}"
        )
    payload = json.loads(validation_receipt_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {normalize_slashes(str(validation_receipt_path))}.")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("Stack validation receipt is missing its summary object.")

    counts = _normalize_counts(summary)
    validation_ref = atlas_relative(validation_receipt_path, root=base)
    source_refs = _ordered_unique_strings(list(agent.source_refs) + [validation_ref])

    return {
        "contract_version": SHADOW_VALIDATION_SUMMARY_CONTRACT_VERSION,
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
            "can_waive_findings": False,
            "can_mutate_truth": False,
        },
        "validation_receipt": {
            "ref": validation_ref,
            "counts": counts,
        },
        "source_receipts": list(registry.source_receipts),
        "source_refs": source_refs,
    }


def render_shadow_validation_summary(payload: dict[str, Any]) -> str:
    counts = payload["validation_receipt"]["counts"]
    agent = payload["agent"]
    authority = payload["authority"]
    lines = [
        "# Cortex Shadow Validation Summary",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Agent: `{agent['id']}`",
        f"- Contract: `{agent['contract_id']}`",
        f"- Trigger family: {agent['trigger_family']}",
        f"- Admissibility: `{agent['admissibility_state']}`",
        f"- Consumption status: `{payload['consumption_status']}`",
        (
            f"- Validation counts: `critical={counts['critical']} error={counts['error']} "
            f"warning={counts['warning']} info={counts['info']} total={counts['total']}`"
        ),
        f"- Validation receipt: `{payload['validation_receipt']['ref']}`",
        f"- Production authority: `{'yes' if authority['has_production_authority'] else 'no'}`",
        f"- Can waive findings: `{'yes' if authority['can_waive_findings'] else 'no'}`",
        f"- Can mutate truth: `{'yes' if authority['can_mutate_truth'] else 'no'}`",
        "",
        "## Boundaries",
        f"- Owner boundary: {agent['owner_boundary']}",
        f"- Non-claim boundary: {agent['non_claim_boundary']}",
        f"- Fallback path: `{agent['fallback_path']}`",
        f"- Fallback: {agent['fallback_behavior']}",
        "",
        "## Source Receipts",
    ]
    for ref in payload["source_receipts"]:
        lines.append(f"- `{ref}`")
    lines.extend(["", "## Source Refs"])
    for ref in payload["source_refs"]:
        lines.append(f"- `{ref}`")
    return "\n".join(lines) + "\n"


def persist_shadow_validation_summary_artifact(
    *,
    root: Path | None = None,
    output_json_path: Path | None = None,
    output_summary_path: Path | None = None,
    write_summary: bool = True,
    validation_path: Path | None = None,
) -> PersistedShadowValidationSummaryArtifact:
    base = (root or atlas_root()).resolve()
    artifact_path = (output_json_path or default_shadow_validation_summary_json_path(base)).resolve()
    summary_path = (
        (output_summary_path or default_shadow_validation_summary_markdown_path(base)).resolve() if write_summary else None
    )
    payload = build_shadow_validation_summary_payload(root=base, validation_path=validation_path)
    summary = render_shadow_validation_summary(payload)
    write_json(artifact_path, payload)
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
    return PersistedShadowValidationSummaryArtifact(
        artifact_path=artifact_path,
        summary_path=summary_path,
        payload_digest=stable_json_digest(payload),
        payload=payload,
        summary=summary,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Persist a deterministic contract-consumption proof artifact for validation-summary-shadow."
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--validation-path", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-summary", type=Path)
    parser.add_argument("--no-write-summary", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    base = args.root.resolve()
    try:
        artifact = persist_shadow_validation_summary_artifact(
            root=base,
            output_json_path=args.output_json.resolve() if args.output_json else None,
            output_summary_path=args.output_summary.resolve() if args.output_summary else None,
            write_summary=not args.no_write_summary,
            validation_path=args.validation_path.resolve() if args.validation_path else None,
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
