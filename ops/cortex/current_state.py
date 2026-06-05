from __future__ import annotations

import argparse
import json
import subprocess
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
from ops.cortex.kernel import load_kernel_state_model
from ops.cortex.rail_state import FAILED_VERIFICATION_STATUS, load_and_classify_rail_state
from ops.stack.generate_lockfile import parse_porcelain_path

CURRENT_STATE_CONTRACT_VERSION = "atlas.cortex.current-state.v1"


def current_state_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "current-state"


def default_current_state_latest_json_path(root: Path | None = None) -> Path:
    return current_state_root(root) / "latest.json"


def default_current_state_latest_markdown_path(root: Path | None = None) -> Path:
    return current_state_root(root) / "latest.md"


def default_validation_receipt_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "receipts" / "validation" / "stack-validation.latest.json"


def default_operator_surface_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "operator-surface" / "latest.json"


@dataclass(frozen=True)
class PersistedCurrentStateArtifact:
    artifact_path: Path
    summary_path: Path | None
    payload_digest: str
    payload: dict[str, Any]
    summary: str

    def to_payload(self, *, root: Path | None = None) -> dict[str, Any]:
        base = (root or atlas_root()).resolve()
        return {
            "artifact_path": atlas_relative(self.artifact_path, root=base),
            "summary_path": atlas_relative(self.summary_path, root=base) if self.summary_path is not None else None,
            "payload_digest": self.payload_digest,
            "summary": self.summary,
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {normalize_slashes(str(path))}.")
    return payload


def _require_validation_receipt(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Stack validation receipt not found: {normalize_slashes(str(resolved))}")
    return _read_json_object(resolved)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    results: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        stripped = item.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        results.append(normalize_slashes(stripped))
    return results


def _normalize_counts(summary: dict[str, Any]) -> dict[str, int]:
    counts = {
        "critical": int(summary.get("critical", 0) or 0),
        "error": int(summary.get("error", 0) or 0),
        "warning": int(summary.get("warning", 0) or 0),
        "info": int(summary.get("info", 0) or 0),
    }
    counts["total"] = int(summary.get("total", sum(counts.values())) or sum(counts.values()))
    return counts


def _git_output(repo_path: Path, *args: str) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return (
        completed.returncode,
        completed.stdout.rstrip("\n").rstrip("\r"),
        completed.stderr.rstrip("\n").rstrip("\r"),
    )


def _load_git_state_from_repo(root: Path) -> dict[str, Any]:
    code, head, _ = _git_output(root, "rev-parse", "HEAD")
    if code != 0 or not head:
        raise ValueError(f"Unable to resolve HEAD for ATLAS root git state: {normalize_slashes(str(root))}")

    branch_code, branch, _ = _git_output(root, "rev-parse", "--abbrev-ref", "HEAD")
    branch_name = branch.strip() if branch_code == 0 and branch.strip() else "HEAD"

    status_code, porcelain, _ = _git_output(root, "status", "--porcelain=v1", "--untracked-files=all")
    status_lines = [line.rstrip("\r") for line in porcelain.splitlines() if line] if status_code == 0 else []
    changed_files: list[str] = []
    untracked_files: list[str] = []
    for line in status_lines:
        path = parse_porcelain_path(line)
        if not path:
            continue
        if line.startswith("??"):
            untracked_files.append(path)
        else:
            changed_files.append(path)

    upstream_code, upstream, _ = _git_output(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    remote_status: dict[str, Any]
    if upstream_code != 0 or not upstream.strip():
        remote_status = {
            "status": "no_upstream",
            "upstream": None,
            "ahead": 0,
            "behind": 0,
        }
    else:
        counts_code, counts_output, _ = _git_output(root, "rev-list", "--left-right", "--count", "HEAD...@{upstream}")
        ahead = 0
        behind = 0
        if counts_code == 0:
            parts = counts_output.strip().split()
            if len(parts) == 2:
                ahead = int(parts[0] or 0)
                behind = int(parts[1] or 0)
        if ahead > 0 and behind > 0:
            status = "diverged"
        elif ahead > 0:
            status = "ahead"
        elif behind > 0:
            status = "behind"
        else:
            status = "in_sync"
        remote_status = {
            "status": status,
            "upstream": upstream.strip(),
            "ahead": ahead,
            "behind": behind,
        }

    worktree_status = "dirty" if changed_files or untracked_files else "clean"
    return {
        "branch": branch_name,
        "head": head.strip(),
        "worktree_status": worktree_status,
        "changed_files": changed_files,
        "untracked_files": untracked_files,
        "remote_status": remote_status,
    }


def _normalize_remote_status(value: Any) -> dict[str, Any]:
    remote = value if isinstance(value, dict) else {}
    return {
        "status": str(remote.get("status", "unknown")).strip() or "unknown",
        "upstream": str(remote.get("upstream")).strip() if isinstance(remote.get("upstream"), str) else None,
        "ahead": int(remote.get("ahead", 0) or 0),
        "behind": int(remote.get("behind", 0) or 0),
    }


def _normalize_git_state(payload: dict[str, Any]) -> dict[str, Any]:
    head = payload.get("head")
    if not isinstance(head, str) or not head.strip():
        raise ValueError("Git-state payload must include a non-empty head value.")
    changed_files = _string_list(payload.get("changed_files"))
    untracked_files = _string_list(payload.get("untracked_files"))
    worktree_status = str(payload.get("worktree_status", "")).strip().lower()
    if worktree_status not in {"clean", "dirty"}:
        worktree_status = "dirty" if changed_files or untracked_files else "clean"
    if worktree_status == "clean" and (changed_files or untracked_files):
        worktree_status = "dirty"
    return {
        "branch": str(payload.get("branch", "HEAD")).strip() or "HEAD",
        "head": head.strip(),
        "worktree_status": worktree_status,
        "changed_files": changed_files,
        "untracked_files": untracked_files,
        "remote_status": _normalize_remote_status(payload.get("remote_status")),
    }


def _load_git_state(
    *,
    root: Path,
    git_state: dict[str, Any] | None = None,
    git_state_path: Path | None = None,
) -> dict[str, Any]:
    if git_state is not None:
        return _normalize_git_state(git_state)
    if git_state_path is not None:
        return _normalize_git_state(_read_json_object(git_state_path.resolve()))
    return _load_git_state_from_repo(root)


def _normalize_publication_state(
    payload: dict[str, Any],
    *,
    fallback_branch: str,
    fallback_head: str,
    fallback_remote_status: dict[str, Any],
) -> dict[str, Any]:
    published = payload.get("published")
    return {
        "status": str(payload.get("status", fallback_remote_status.get("status", "unknown"))).strip() or "unknown",
        "branch": str(payload.get("branch", fallback_branch)).strip() or fallback_branch,
        "head": str(payload.get("head", fallback_head)).strip() or fallback_head,
        "published": bool(published) if published is not None else fallback_remote_status.get("ahead", 0) == 0,
        "upstream": (
            str(payload.get("upstream")).strip()
            if isinstance(payload.get("upstream"), str)
            else fallback_remote_status.get("upstream")
        ),
        "pr_state": str(payload.get("pr_state")).strip() if isinstance(payload.get("pr_state"), str) else None,
        "pr_url": str(payload.get("pr_url")).strip() if isinstance(payload.get("pr_url"), str) else None,
        "notes": _string_list(payload.get("notes")),
    }


def _derive_publication_state(
    *,
    git_state: dict[str, Any],
    publication_state: dict[str, Any] | None = None,
    publication_state_path: Path | None = None,
) -> dict[str, Any]:
    fallback_remote_status = git_state["remote_status"]
    if publication_state_path is not None:
        publication_state = _read_json_object(publication_state_path.resolve())
    if publication_state is not None:
        return _normalize_publication_state(
            publication_state,
            fallback_branch=git_state["branch"],
            fallback_head=git_state["head"],
            fallback_remote_status=fallback_remote_status,
        )
    return {
        "status": str(fallback_remote_status.get("status", "unknown")),
        "branch": git_state["branch"],
        "head": git_state["head"],
        "published": fallback_remote_status.get("ahead", 0) == 0 and bool(fallback_remote_status.get("upstream")),
        "upstream": fallback_remote_status.get("upstream"),
        "pr_state": None,
        "pr_url": None,
        "notes": [],
    }


def _load_rail_state_summary(
    *,
    root: Path,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    state_path = (
        state_model_path.resolve()
        if state_model_path is not None
        else root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json"
    )
    rule_path = (
        rule_registry_path.resolve()
        if rule_registry_path is not None
        else root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json"
    )
    if not state_path.exists() or not rule_path.exists():
        return None, None, []

    posture = load_kernel_state_model(path=state_path)
    assessment = load_and_classify_rail_state(
        root=root,
        state_model_path=state_path,
        rule_registry_path=rule_path,
    )
    latest_clean_step = posture.rail_state.latest_clean_step.to_payload()
    latest_clean_step["source_ref"] = atlas_relative(state_path, root=root)
    rail_state = {
        "posture_id": assessment.posture_id,
        "classification": assessment.posture_classification,
        "rail_id": assessment.rail_id,
        "verification_status": assessment.verification_status,
        "known_validation_debt": list(assessment.known_validation_debt),
        "active_dirty_lane_ids": list(assessment.active_dirty_lane_ids),
        "matched_rule_ids": list(assessment.matched_rule_ids),
        "safe_to_proceed": assessment.safe_to_proceed,
        "next_action": assessment.next_action.to_payload(),
        "boundary_reminders": list(assessment.boundary_reminders),
        "source_refs": [
            atlas_relative(state_path, root=root),
            atlas_relative(rule_path, root=root),
        ],
    }
    return rail_state, latest_clean_step, rail_state["source_refs"]


def _validation_blockers(validation_payload: dict[str, Any], *, validation_ref: str) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    findings = validation_payload.get("findings", [])
    if not isinstance(findings, list):
        return blockers
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        severity = str(finding.get("severity", "")).strip().lower()
        if severity not in {"critical", "error"}:
            continue
        blockers.append(
            {
                "code": str(finding.get("category", "validation-finding")).strip() or "validation-finding",
                "severity": severity,
                "summary": str(finding.get("message", "Blocking validation finding.")).strip() or "Blocking validation finding.",
                "source_kind": "validation_receipt",
                "source_ref": validation_ref,
                "details": {
                    "path": normalize_slashes(str(finding.get("path", ""))),
                    "category": str(finding.get("category", "")).strip() or None,
                },
            }
        )
    return blockers


def _git_blockers(git_state: dict[str, Any]) -> list[dict[str, Any]]:
    if git_state["worktree_status"] != "dirty":
        return []
    return [
        {
            "code": "dirty-worktree",
            "severity": "error",
            "summary": "The ATLAS root worktree is dirty and should be stabilized before new lane claims or publication decisions.",
            "source_kind": "git_status",
            "source_ref": "git status --porcelain=v1 --untracked-files=all",
            "details": {
                "changed_files": git_state["changed_files"],
                "untracked_files": git_state["untracked_files"],
            },
        }
    ]


def _rail_blockers(rail_state: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(rail_state, dict):
        return []
    if rail_state.get("verification_status") != FAILED_VERIFICATION_STATUS:
        return []
    return [
        {
            "code": "rail-verification-failed",
            "severity": "error",
            "summary": "The Cortex rail-state assessment reports a failed verification posture.",
            "source_kind": "cortex_rail_state",
            "source_ref": ", ".join(rail_state.get("source_refs", [])),
            "details": {
                "rail_id": rail_state.get("rail_id"),
                "matched_rule_ids": rail_state.get("matched_rule_ids", []),
            },
        }
    ]


def _fallback_latest_clean_step(validation_payload: dict[str, Any], *, validation_ref: str) -> dict[str, Any]:
    return {
        "step_id": "stack-validation-receipt-captured",
        "owner_layer": "atlas",
        "summary": "Latest explicit stack validation receipt captured current ATLAS posture.",
        "status": "observed",
        "evidence": [validation_ref],
        "source_inputs": ["runtime/receipts/validation/stack-validation.latest.json"],
        "completed_at": str(validation_payload.get("generated_at", "")),
        "source_ref": validation_ref,
    }


def _next_recommended_lane(
    *,
    blockers: list[dict[str, Any]],
    rail_state: dict[str, Any] | None,
    validation_ref: str,
) -> dict[str, Any]:
    blocked_by = [str(item.get("code", "")).strip() for item in blockers if isinstance(item, dict)]
    if any(str(item.get("source_kind")) == "validation_receipt" for item in blockers):
        return {
            "lane_id": "stabilize-stack-validation",
            "owner_layer": "atlas",
            "rationale": "Blocking stack-validation findings are active, so the next lane must stabilize validation before new roadmap work proceeds.",
            "blocked_by": blocked_by,
            "source_refs": [validation_ref],
        }
    if any(str(item.get("code")) == "dirty-worktree" for item in blockers):
        return {
            "lane_id": "stabilize-root-worktree",
            "owner_layer": "atlas",
            "rationale": "The root worktree is dirty, so current posture should be stabilized before new lane routing or publication decisions.",
            "blocked_by": blocked_by,
            "source_refs": ["git status --porcelain=v1 --untracked-files=all"],
        }
    if isinstance(rail_state, dict):
        next_action = rail_state["next_action"]
        return {
            "lane_id": next_action["action_id"],
            "owner_layer": next_action["owner_layer"],
            "rationale": next_action["rationale"],
            "blocked_by": blocked_by,
            "source_refs": rail_state.get("source_refs", []),
        }
    return {
        "lane_id": "capture-current-state",
        "owner_layer": "atlas",
        "rationale": "No Cortex rail-state seed was available, so the next lane is to refresh the explicit root-owned current-state projection.",
        "blocked_by": blocked_by,
        "source_refs": [validation_ref],
    }


def _load_operator_surface_projection(
    *,
    root: Path,
    operator_surface_path: Path | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    resolved = (operator_surface_path or default_operator_surface_path(root)).resolve()
    if not resolved.exists():
        return None, None
    payload = _read_json_object(resolved)
    shadow_agents = payload.get("shadow_agents") if isinstance(payload.get("shadow_agents"), dict) else {}
    shadow_consumption = payload.get("shadow_consumption")
    if not isinstance(shadow_consumption, dict):
        return None, atlas_relative(resolved, root=root)
    consumed_agents = shadow_consumption.get("consumed_agents")
    consumed_payload = consumed_agents if isinstance(consumed_agents, list) else []
    blocked_agents = shadow_agents.get("blocked_agents")
    blocked_payload = blocked_agents if isinstance(blocked_agents, list) else []
    projection = {
        "artifact_ref": atlas_relative(resolved, root=root),
        "artifact_generated_at": str(payload.get("generated_at", "")).strip(),
        "registry_ref": str(shadow_agents.get("registry_ref", "")).strip(),
        "artifact_root": str(shadow_consumption.get("artifact_root", "")).strip(),
        "shadow_contract_ids": _string_list(shadow_agents.get("shadow_contract_ids")),
        "blocked_contract_ids": _string_list(shadow_agents.get("blocked_contract_ids")),
        "blocked_agent_ids": _string_list(shadow_agents.get("blocked_agent_ids")),
        "projected_agent_ids": _string_list(shadow_consumption.get("projected_agent_ids")),
        "projected_contract_ids": _string_list(shadow_consumption.get("projected_contract_ids")),
        "missing_eligible_agent_ids": _string_list(shadow_consumption.get("missing_eligible_agent_ids")),
        "missing_eligible_contract_ids": _string_list(shadow_consumption.get("missing_eligible_contract_ids")),
        "consumed_artifact_refs": _string_list(
            [
                item.get("artifact_ref")
                for item in consumed_payload
                if isinstance(item, dict) and isinstance(item.get("artifact_ref"), str)
            ]
        ),
        "projected_agents": [
            {
                "agent_id": str(item.get("agent_id", "")).strip(),
                "contract_id": str(item.get("contract_id", "")).strip(),
                "family_name": str(item.get("family_name", "")).strip(),
                "trigger": str(item.get("trigger", "")).strip(),
                "admissibility_state": str(item.get("admissibility_state", "")).strip(),
                "authority": item.get("authority") if isinstance(item.get("authority"), dict) else {},
            }
            for item in consumed_payload
            if isinstance(item, dict)
        ],
        "blocked_agents": [
            {
                "agent_id": str(item.get("agent_id", "")).strip(),
                "contract_id": str(item.get("contract_id", "")).strip(),
                "family_name": str(item.get("family_name", "")).strip(),
                "trigger": str(item.get("trigger", "")).strip(),
                "admissibility_state": str(item.get("admissibility_state", "")).strip(),
            }
            for item in blocked_payload
            if isinstance(item, dict)
        ],
    }
    return projection, projection["artifact_ref"]


def build_current_state_payload(
    *,
    root: Path | None = None,
    validation_path: Path | None = None,
    git_state: dict[str, Any] | None = None,
    git_state_path: Path | None = None,
    publication_state: dict[str, Any] | None = None,
    publication_state_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    operator_surface_path: Path | None = None,
) -> dict[str, Any]:
    base = (root or atlas_root()).resolve()
    resolved_validation_path = (validation_path or default_validation_receipt_path(base)).resolve()
    validation_payload = _require_validation_receipt(resolved_validation_path)
    validation_ref = atlas_relative(resolved_validation_path, root=base)
    validation_counts = _normalize_counts(
        validation_payload.get("summary", {}) if isinstance(validation_payload.get("summary"), dict) else {}
    )

    normalized_git_state = _load_git_state(
        root=base,
        git_state=git_state,
        git_state_path=git_state_path,
    )
    remote_publication_state = _derive_publication_state(
        git_state=normalized_git_state,
        publication_state=publication_state,
        publication_state_path=publication_state_path,
    )

    rail_state: dict[str, Any] | None = None
    latest_clean_step: dict[str, Any] | None = None
    rail_source_refs: list[str] = []
    try:
        rail_state, latest_clean_step, rail_source_refs = _load_rail_state_summary(
            root=base,
            state_model_path=state_model_path,
            rule_registry_path=rule_registry_path,
        )
    except ValueError:
        rail_state = None
        latest_clean_step = None
        rail_source_refs = []

    blockers = _validation_blockers(validation_payload, validation_ref=validation_ref)
    blockers.extend(_git_blockers(normalized_git_state))
    blockers.extend(_rail_blockers(rail_state))

    if latest_clean_step is None:
        latest_clean_step = _fallback_latest_clean_step(validation_payload, validation_ref=validation_ref)

    source_refs = [validation_ref, *rail_source_refs]
    if publication_state_path is not None:
        source_refs.append(atlas_relative(publication_state_path.resolve(), root=base))
    if git_state_path is not None:
        source_refs.append(atlas_relative(git_state_path.resolve(), root=base))
    operator_surface_projection, operator_surface_ref = _load_operator_surface_projection(
        root=base,
        operator_surface_path=operator_surface_path,
    )
    if operator_surface_ref is not None:
        source_refs.append(operator_surface_ref)

    next_lane = _next_recommended_lane(
        blockers=blockers,
        rail_state=rail_state,
        validation_ref=validation_ref,
    )

    return {
        "contract_version": CURRENT_STATE_CONTRACT_VERSION,
        "generated_at": _utc_now(),
        "stack_root": normalize_slashes(str(base)),
        "source_refs": list(dict.fromkeys(source_refs)),
        "branch": normalized_git_state["branch"],
        "head": normalized_git_state["head"],
        "worktree_status": normalized_git_state["worktree_status"],
        "changed_files": normalized_git_state["changed_files"],
        "untracked_files": normalized_git_state["untracked_files"],
        "remote_status": normalized_git_state["remote_status"],
        "remote_publication_state": remote_publication_state,
        "validation_receipt": {
            "generated_at": str(validation_payload.get("generated_at", "")),
            "path": validation_ref,
            "counts": validation_counts,
        },
        "validation_counts": validation_counts,
        "active_blockers": blockers,
        "latest_clean_step": latest_clean_step,
        "rail_state": rail_state,
        "operator_surface_projection": operator_surface_projection,
        "next_recommended_lane": next_lane,
    }


def render_current_state_summary(payload: dict[str, Any]) -> str:
    counts = payload["validation_counts"]
    publication = payload["remote_publication_state"]
    latest_clean_step = payload["latest_clean_step"]
    next_lane = payload["next_recommended_lane"]
    blockers = payload.get("active_blockers", [])
    lines = [
        "# Cortex Current State",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Branch: `{payload['branch']}`",
        f"- HEAD: `{payload['head']}`",
        f"- Worktree: `{payload['worktree_status']}`",
        (
            f"- Remote publication: `{publication['status']}`"
            f" (upstream={publication['upstream'] or 'none'}, published={'yes' if publication['published'] else 'no'})"
        ),
        (
            f"- Validation: `critical={counts['critical']} error={counts['error']} "
            f"warning={counts['warning']} info={counts['info']} total={counts['total']}`"
        ),
        (
            f"- Latest clean step: `{latest_clean_step['step_id']}` "
            f"({latest_clean_step['owner_layer']})"
        ),
        f"- Next recommended lane: `{next_lane['lane_id']}` ({next_lane['owner_layer']})",
        "",
        "## Active Blockers",
    ]
    if blockers:
        for blocker in blockers:
            lines.append(f"- `{blocker['code']}` [{blocker['severity']}]: {blocker['summary']}")
    else:
        lines.append("- none")

    projection = payload.get("operator_surface_projection")
    lines.extend(["", "## Operator Surface"])
    if isinstance(projection, dict):
        lines.append(f"- Artifact: `{projection.get('artifact_ref', '')}`")
        lines.append(f"- Generated: `{projection.get('artifact_generated_at', '')}`")
        lines.append(f"- Projected shadow agents: `{', '.join(projection.get('projected_agent_ids', [])) or 'none'}`")
        lines.append(f"- Projected contracts: `{', '.join(projection.get('projected_contract_ids', [])) or 'none'}`")
        lines.append(
            f"- Missing eligible projections: `{', '.join(projection.get('missing_eligible_agent_ids', [])) or 'none'}`"
        )
        lines.append(f"- Blocked shadow agents: `{', '.join(projection.get('blocked_agent_ids', [])) or 'none'}`")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Evidence",
        ]
    )
    for ref in payload.get("source_refs", []):
        lines.append(f"- `{ref}`")
    return "\n".join(lines) + "\n"


def persist_current_state_artifact(
    *,
    root: Path | None = None,
    validation_path: Path | None = None,
    git_state: dict[str, Any] | None = None,
    git_state_path: Path | None = None,
    publication_state: dict[str, Any] | None = None,
    publication_state_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    operator_surface_path: Path | None = None,
    output_json_path: Path | None = None,
    output_markdown_path: Path | None = None,
    write_markdown: bool = True,
) -> PersistedCurrentStateArtifact:
    base = (root or atlas_root()).resolve()
    artifact_path = (output_json_path or default_current_state_latest_json_path(base)).resolve()
    summary_path = (
        (output_markdown_path or default_current_state_latest_markdown_path(base)).resolve() if write_markdown else None
    )
    payload = build_current_state_payload(
        root=base,
        validation_path=validation_path.resolve() if validation_path is not None else None,
        git_state=git_state,
        git_state_path=git_state_path.resolve() if git_state_path is not None else None,
        publication_state=publication_state,
        publication_state_path=publication_state_path.resolve() if publication_state_path is not None else None,
        state_model_path=state_model_path.resolve() if state_model_path is not None else None,
        rule_registry_path=rule_registry_path.resolve() if rule_registry_path is not None else None,
        operator_surface_path=operator_surface_path.resolve() if operator_surface_path is not None else None,
    )
    summary = render_current_state_summary(payload)
    write_json(artifact_path, payload)
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
    return PersistedCurrentStateArtifact(
        artifact_path=artifact_path,
        summary_path=summary_path,
        payload_digest=stable_json_digest(payload),
        payload=payload,
        summary=summary,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Persist the Cortex current-state posture artifact for ATLAS.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--validation-path", type=Path)
    parser.add_argument("--git-state-path", type=Path)
    parser.add_argument("--publication-state-path", type=Path)
    parser.add_argument("--state-model-path", type=Path)
    parser.add_argument("--rule-registry-path", type=Path)
    parser.add_argument("--operator-surface-path", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-markdown", type=Path)
    parser.add_argument("--no-write-markdown", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    try:
        artifact = persist_current_state_artifact(
            root=args.root.resolve(),
            validation_path=args.validation_path.resolve() if args.validation_path else None,
            git_state_path=args.git_state_path.resolve() if args.git_state_path else None,
            publication_state_path=args.publication_state_path.resolve() if args.publication_state_path else None,
            state_model_path=args.state_model_path.resolve() if args.state_model_path else None,
            rule_registry_path=args.rule_registry_path.resolve() if args.rule_registry_path else None,
            operator_surface_path=args.operator_surface_path.resolve() if args.operator_surface_path else None,
            output_json_path=args.output_json.resolve() if args.output_json else None,
            output_markdown_path=args.output_markdown.resolve() if args.output_markdown else None,
            write_markdown=not args.no_write_markdown,
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
            print(f"Markdown summary: {normalize_slashes(str(artifact.summary_path))}")
        print(f"Payload digest: {artifact.payload_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
