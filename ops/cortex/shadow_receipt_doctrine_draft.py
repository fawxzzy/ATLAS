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

SHADOW_RECEIPT_DOCTRINE_DRAFT_CONTRACT_VERSION = "atlas.cortex.shadow-receipt-doctrine-draft.v1"
RECEIPT_DOCTRINE_DRAFT_AGENT_ID = "receipt-doctrine-draft-shadow"
PLAYBOOK_SECTION_HEADER_RE = re.compile(r"^## (?P<title>.+)$")
BACKTICK_TOKEN_RE = re.compile(r"`([^`]+)`")
RULE_RE = re.compile(r"^- Rule: `(?P<value>[^`]+)`\.")
PATTERN_RE = re.compile(r"^- Pattern: `(?P<value>[^`]+)`\.")
FAILURE_MODE_RE = re.compile(r"^- Failure Mode: `(?P<value>[^`]+)`\.")
FAILURE_SECTION_RE = re.compile(r"^## (?P<number>\d+)\. (?P<title>.+)$")


def default_receipt_doctrine_draft_json_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "shadow-agent-consumption" / "receipt-doctrine-draft.latest.json"


def default_receipt_doctrine_draft_markdown_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "shadow-agent-consumption" / "receipt-doctrine-draft.latest.md"


@dataclass(frozen=True)
class PersistedShadowReceiptDoctrineDraftArtifact:
    artifact_path: Path
    summary_path: Path | None
    payload_digest: str
    payload: dict[str, Any]
    summary: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_required_text(path: Path, label: str) -> str:
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"{label} not found: {normalize_slashes(str(resolved))}")
    return resolved.read_text(encoding="utf-8")


def _collect_latest_playbook_block(playbook_text: str) -> dict[str, Any]:
    lines = playbook_text.splitlines()
    current_title: str | None = None
    current_lines: list[str] = []
    for line in lines:
        match = PLAYBOOK_SECTION_HEADER_RE.match(line)
        if match is not None:
            if current_title is not None:
                break
            current_title = match.group("title").strip()
            current_lines = []
            continue
        if current_title is not None:
            current_lines.append(line.rstrip())
    if current_title is None:
        raise ValueError("Playbook notes do not contain the expected top doctrine section.")
    rules = [match.group("value") for line in current_lines if (match := RULE_RE.match(line))]
    patterns = [match.group("value") for line in current_lines if (match := PATTERN_RE.match(line))]
    failure_modes = [match.group("value") for line in current_lines if (match := FAILURE_MODE_RE.match(line))]
    if not any((rules, patterns, failure_modes)):
        raise ValueError("Playbook notes top doctrine section did not yield any draftable doctrine entries.")
    return {
        "section_title": current_title,
        "rules": rules,
        "patterns": patterns,
        "failure_modes": failure_modes,
    }


def _collect_latest_failure_sections(failure_text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line in failure_text.splitlines():
        match = FAILURE_SECTION_RE.match(line)
        if match is None:
            continue
        entries.append(
            {
                "section_id": match.group("number").strip(),
                "title": match.group("title").strip(),
            }
        )
    if not entries:
        raise ValueError("Failure modes surface did not yield any section headings.")
    return entries[-3:]


def _collect_receipt_focus(receipt_text: str) -> dict[str, Any]:
    tokens = [match.group(1).strip() for match in BACKTICK_TOKEN_RE.finditer(receipt_text)]
    ordered: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if not token or token in seen:
            continue
        seen.add(token)
        ordered.append(token)
    if not ordered:
        raise ValueError("Automation threshold receipt did not yield any backticked focus tokens.")
    return {
        "focus_tokens": ordered[:8],
    }


def build_shadow_receipt_doctrine_draft_payload(
    *,
    root: Path | None = None,
    playbook_notes_path: Path | None = None,
    failure_modes_path: Path | None = None,
    automation_threshold_receipt_path: Path | None = None,
) -> dict[str, Any]:
    base = (root or atlas_root()).resolve()
    registry = load_shadow_agent_registry(root=base)
    agent = resolve_shadow_agent_for_consumption(RECEIPT_DOCTRINE_DRAFT_AGENT_ID, root=base)

    playbook_path = (playbook_notes_path or (base / "docs" / "PLAYBOOK_NOTES.md")).resolve()
    failure_path = (failure_modes_path or (base / "docs" / "atlas-book" / "10-failure-modes-and-recovery.md")).resolve()
    receipt_path = (
        automation_threshold_receipt_path
        or (base / "docs" / "ops" / "AI-REPETITION-TO-AUTOMATION-PIPELINE-AUTOMATION-CANDIDATE-THRESHOLD-PASS-1-2026-06-01.md")
    ).resolve()

    playbook_text = _load_required_text(playbook_path, "Playbook notes")
    failure_text = _load_required_text(failure_path, "Failure modes surface")
    receipt_text = _load_required_text(receipt_path, "Automation threshold receipt")

    latest_playbook = _collect_latest_playbook_block(playbook_text)
    recent_failures = _collect_latest_failure_sections(failure_text)
    receipt_focus = _collect_receipt_focus(receipt_text)

    return {
        "contract_version": SHADOW_RECEIPT_DOCTRINE_DRAFT_CONTRACT_VERSION,
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
            "can_admit_doctrine": False,
            "can_finalize_receipts": False,
            "can_mutate_truth": False,
        },
        "draft_payload": {
            "playbook_section_title": latest_playbook["section_title"],
            "candidate_rules": latest_playbook["rules"],
            "candidate_patterns": latest_playbook["patterns"],
            "candidate_failure_modes": latest_playbook["failure_modes"],
            "recent_failure_sections": recent_failures,
            "receipt_focus_tokens": receipt_focus["focus_tokens"],
            "draft_scope": "bounded-shadow-draft-only",
        },
        "source_receipts": list(registry.source_receipts),
        "source_refs": [
            "docs/PLAYBOOK_NOTES.md",
            "docs/atlas-book/10-failure-modes-and-recovery.md",
            "docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-AUTOMATION-CANDIDATE-THRESHOLD-PASS-1-2026-06-01.md",
            "docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-CONTRACT-FIRST-AGENT-SHADOWING-PASS-1-2026-06-01.md",
        ],
    }


def render_shadow_receipt_doctrine_draft(payload: dict[str, Any]) -> str:
    agent = payload["agent"]
    authority = payload["authority"]
    draft = payload["draft_payload"]
    lines = [
        "# Cortex Shadow Receipt/Doctrine Draft",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Agent: `{agent['id']}`",
        f"- Contract: `{agent['contract_id']}`",
        f"- Trigger family: {agent['trigger_family']}",
        f"- Admissibility: `{agent['admissibility_state']}`",
        f"- Consumption status: `{payload['consumption_status']}`",
        f"- Draft scope: `{draft['draft_scope']}`",
        f"- Production authority: `{'yes' if authority['has_production_authority'] else 'no'}`",
        f"- Can admit doctrine: `{'yes' if authority['can_admit_doctrine'] else 'no'}`",
        f"- Can finalize receipts: `{'yes' if authority['can_finalize_receipts'] else 'no'}`",
        f"- Can mutate truth: `{'yes' if authority['can_mutate_truth'] else 'no'}`",
        "",
        "## Boundaries",
        f"- Owner boundary: {agent['owner_boundary']}",
        f"- Non-claim boundary: {agent['non_claim_boundary']}",
        f"- Fallback path: `{agent['fallback_path']}`",
        f"- Fallback: {agent['fallback_behavior']}",
        "",
        f"## Playbook Section: {draft['playbook_section_title']}",
    ]
    for rule in draft["candidate_rules"]:
        lines.append(f"- Rule draft: `{rule}`")
    for pattern in draft["candidate_patterns"]:
        lines.append(f"- Pattern draft: `{pattern}`")
    for failure_mode in draft["candidate_failure_modes"]:
        lines.append(f"- Failure mode draft: `{failure_mode}`")
    lines.extend(["", "## Recent Failure Sections"])
    for item in draft["recent_failure_sections"]:
        lines.append(f"- `{item['section_id']}`: {item['title']}")
    lines.extend(["", "## Receipt Focus Tokens"])
    for token in draft["receipt_focus_tokens"]:
        lines.append(f"- `{token}`")
    return "\n".join(lines) + "\n"


def persist_shadow_receipt_doctrine_draft_artifact(
    *,
    root: Path | None = None,
    output_json_path: Path | None = None,
    output_summary_path: Path | None = None,
    write_summary: bool = True,
    playbook_notes_path: Path | None = None,
    failure_modes_path: Path | None = None,
    automation_threshold_receipt_path: Path | None = None,
) -> PersistedShadowReceiptDoctrineDraftArtifact:
    base = (root or atlas_root()).resolve()
    artifact_path = (output_json_path or default_receipt_doctrine_draft_json_path(base)).resolve()
    summary_path = (
        (output_summary_path or default_receipt_doctrine_draft_markdown_path(base)).resolve()
        if write_summary
        else None
    )
    payload = build_shadow_receipt_doctrine_draft_payload(
        root=base,
        playbook_notes_path=playbook_notes_path,
        failure_modes_path=failure_modes_path,
        automation_threshold_receipt_path=automation_threshold_receipt_path,
    )
    summary = render_shadow_receipt_doctrine_draft(payload)
    write_json(artifact_path, payload)
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
    return PersistedShadowReceiptDoctrineDraftArtifact(
        artifact_path=artifact_path,
        summary_path=summary_path,
        payload_digest=stable_json_digest(payload),
        payload=payload,
        summary=summary,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Persist a deterministic contract-consumption proof artifact for receipt-doctrine-draft-shadow."
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--playbook-notes-path", type=Path)
    parser.add_argument("--failure-modes-path", type=Path)
    parser.add_argument("--automation-threshold-receipt-path", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-summary", type=Path)
    parser.add_argument("--no-write-summary", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    base = args.root.resolve()
    try:
        artifact = persist_shadow_receipt_doctrine_draft_artifact(
            root=base,
            output_json_path=args.output_json.resolve() if args.output_json else None,
            output_summary_path=args.output_summary.resolve() if args.output_summary else None,
            write_summary=not args.no_write_summary,
            playbook_notes_path=args.playbook_notes_path.resolve() if args.playbook_notes_path else None,
            failure_modes_path=args.failure_modes_path.resolve() if args.failure_modes_path else None,
            automation_threshold_receipt_path=(
                args.automation_threshold_receipt_path.resolve() if args.automation_threshold_receipt_path else None
            ),
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
