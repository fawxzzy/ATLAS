from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative

CONTRACT_VERSION = "atlas.vercel_hobby_decision.v1"
GUARDRAIL_REPORT_VERSION = "atlas.vercel_hobby_guardrail.v1"
REVIEW_CONTRACT_VERSION = "atlas.vercel_hobby_review.v1"
SNAPSHOT_DATE_PATTERN = re.compile(r"\.(\d{4}-\d{2}-\d{2})\.json$")


class DecisionCheckpointError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DecisionCheckpointError(f"Expected JSON object at {atlas_relative(path)}")
    return payload


def _default_receipt_dir(root: Path) -> Path:
    return root / "runtime" / "receipts" / "vercel-hobby-cost-governance"


def _default_latest_ref(repo_id: str) -> str:
    return f"runtime/receipts/vercel-hobby-cost-governance/{repo_id}-hobby-guardrail.latest.json"


def _default_output_ref(repo_id: str, fmt: str) -> str:
    suffix = "json" if fmt == "json" else "md"
    return f"runtime/receipts/vercel-hobby-cost-governance/{repo_id}-hobby-decision.latest.{suffix}"


def _default_review_ref(repo_id: str) -> str:
    return f"data/atlas/qa/vercel-hobby-cost-governance/{repo_id}-hobby-review.latest.json"


def _discover_preserved_refs(*, root: Path, repo_id: str) -> list[Path]:
    receipt_dir = _default_receipt_dir(root)
    pattern = f"{repo_id}-hobby-guardrail.*.json"
    refs: list[Path] = []
    for candidate in sorted(receipt_dir.glob(pattern)):
        if candidate.name.endswith(".latest.json"):
            continue
        if SNAPSHOT_DATE_PATTERN.search(candidate.name):
            refs.append(candidate.resolve())
    return refs


def _validate_guardrail_payload(*, payload: dict[str, Any], repo_id: str, path: Path) -> None:
    observed_version = str(payload.get("report_version") or "").strip()
    if observed_version != GUARDRAIL_REPORT_VERSION:
        raise DecisionCheckpointError(
            f"Guardrail report at {atlas_relative(path)} must use '{GUARDRAIL_REPORT_VERSION}', found '{observed_version or 'missing'}'."
        )
    observed_repo_id = str(payload.get("repo_id") or "").strip()
    if observed_repo_id != repo_id:
        raise DecisionCheckpointError(
            f"Guardrail report at {atlas_relative(path)} must target repo '{repo_id}', found '{observed_repo_id or 'missing'}'."
        )


def _snapshot_date(path: Path) -> str:
    match = SNAPSHOT_DATE_PATTERN.search(path.name)
    return match.group(1) if match else ""


def _watch_target_signature(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = payload.get("watch_targets")
    if not isinstance(records, list):
        return []
    signature: list[dict[str, Any]] = []
    for item in records:
        if not isinstance(item, dict):
            continue
        target = str(item.get("target") or "").strip()
        references = item.get("references")
        if not target or not isinstance(references, int):
            continue
        signature.append(
            {
                "target": target,
                "references": references,
                "files": sorted(
                    str(file_ref)
                    for file_ref in item.get("files", [])
                    if isinstance(file_ref, str) and file_ref.strip()
                ),
            }
        )
    return sorted(signature, key=lambda item: item["target"])


def _comparison_signature(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    fetch_inventory = summary.get("fetch_inventory") if isinstance(summary.get("fetch_inventory"), dict) else {}
    guardrail_posture = payload.get("guardrail_posture") if isinstance(payload.get("guardrail_posture"), dict) else {}
    middleware_inventory = payload.get("middleware_inventory") if isinstance(payload.get("middleware_inventory"), dict) else {}
    project_link = payload.get("project_link") if isinstance(payload.get("project_link"), dict) else {}

    return {
        "project_name": str(project_link.get("project_name") or ""),
        "project_id": str(project_link.get("project_id") or ""),
        "deployment_enabled": payload.get("vercel_config", {}).get("deployment_enabled")
        if isinstance(payload.get("vercel_config"), dict)
        else None,
        "total_routes": summary.get("total_routes"),
        "api_routes": summary.get("api_routes"),
        "auth_routes": summary.get("auth_routes"),
        "dev_routes": summary.get("dev_routes"),
        "force_dynamic_routes": summary.get("force_dynamic_routes"),
        "nodejs_route_count": summary.get("nodejs_routes"),
        "total_fetch_sites": fetch_inventory.get("total_fetch_sites"),
        "internal_fetch_sites": fetch_inventory.get("internal_fetch_sites"),
        "external_or_dynamic_fetch_sites": fetch_inventory.get("external_or_dynamic_fetch_sites"),
        "deployment_posture": str(guardrail_posture.get("deployment_posture") or ""),
        "route_pressure_posture": str(guardrail_posture.get("route_pressure_posture") or ""),
        "middleware_pressure_posture": str(guardrail_posture.get("middleware_pressure_posture") or ""),
        "integration_pressure_posture": str(guardrail_posture.get("integration_pressure_posture") or ""),
        "hot_route_watch_posture": str(guardrail_posture.get("hot_route_watch_posture") or ""),
        "middleware_present": middleware_inventory.get("present"),
        "middleware_refresh_session_call_present": middleware_inventory.get("refresh_session_call_present"),
        "middleware_public_authless_paths": sorted(
            str(path_ref)
            for path_ref in middleware_inventory.get("public_authless_paths", [])
            if isinstance(path_ref, str) and path_ref.strip()
        ),
        "nodejs_routes": sorted(
            str(route)
            for route in payload.get("nodejs_routes", [])
            if isinstance(route, str) and route.strip()
        ),
        "watch_targets": _watch_target_signature(payload),
    }


def _signature_digest(signature: dict[str, Any]) -> str:
    encoded = json.dumps(signature, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _diff_signatures(*, left_label: str, left: dict[str, Any], right_label: str, right: dict[str, Any]) -> list[dict[str, Any]]:
    diffs: list[dict[str, Any]] = []
    for key in sorted(set(left) | set(right)):
        left_value = left.get(key)
        right_value = right.get(key)
        if left_value != right_value:
            diffs.append(
                {
                    "field": key,
                    left_label: left_value,
                    right_label: right_value,
                }
            )
    return diffs


def _load_matching_review(
    *,
    root: Path,
    repo_id: str,
    latest_signature: dict[str, Any],
    latest_alignment_drift: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, list[str]]:
    review_path = (root / _default_review_ref(repo_id)).resolve()
    if not review_path.exists():
        return None, []
    findings: list[str] = []
    try:
        review = _load_json(review_path)
    except Exception as exc:
        return None, [f"Hobby review '{atlas_relative(review_path, root=root)}' could not be loaded: {exc}"]

    if str(review.get("contract_version") or "").strip() != REVIEW_CONTRACT_VERSION:
        findings.append(
            f"Hobby review '{atlas_relative(review_path, root=root)}' must use contract '{REVIEW_CONTRACT_VERSION}'."
        )
    if str(review.get("repo_id") or "").strip() != repo_id:
        findings.append(f"Hobby review '{atlas_relative(review_path, root=root)}' targets the wrong repo.")
    if str(review.get("checkpoint_status") or "").strip() != "ready":
        findings.append(f"Hobby review '{atlas_relative(review_path, root=root)}' is not ready.")
    if str(review.get("decision") or "").strip() != "keep_hobby":
        findings.append(f"Hobby review '{atlas_relative(review_path, root=root)}' does not approve keep_hobby.")
    observed_digest = _signature_digest(latest_signature)
    expected_digest = str(review.get("accepted_signature_digest") or "").strip()
    if expected_digest != observed_digest:
        findings.append(
            f"Hobby review '{atlas_relative(review_path, root=root)}' signature digest does not match current guardrail signature."
        )
    reviewed_fields = {
        str(value)
        for value in review.get("accepted_drift_fields", [])
        if isinstance(value, str) and value.strip()
    }
    current_fields = {str(item.get("field") or "") for item in latest_alignment_drift if isinstance(item, dict)}
    missing_fields = sorted(current_fields - reviewed_fields)
    if missing_fields:
        findings.append(
            f"Hobby review '{atlas_relative(review_path, root=root)}' does not cover current drift fields: {', '.join(missing_fields)}."
        )
    if findings:
        return None, findings
    review["review_ref"] = atlas_relative(review_path, root=root)
    review["observed_signature_digest"] = observed_digest
    return review, []


def build_checkpoint(
    *,
    root: Path,
    repo_id: str,
    latest_ref: str | Path | None = None,
    preserved_refs: list[str | Path] | None = None,
) -> dict[str, Any]:
    latest_path = Path(latest_ref) if latest_ref is not None else root / _default_latest_ref(repo_id)
    if not latest_path.is_absolute():
        latest_path = (root / latest_path).resolve()
    if not latest_path.exists():
        raise DecisionCheckpointError(f"Missing latest guardrail report: {atlas_relative(latest_path, root=root)}")

    resolved_preserved_paths: list[Path]
    if preserved_refs:
        resolved_preserved_paths = []
        for ref in preserved_refs:
            candidate = Path(ref)
            if not candidate.is_absolute():
                candidate = (root / candidate).resolve()
            resolved_preserved_paths.append(candidate)
    else:
        resolved_preserved_paths = _discover_preserved_refs(root=root, repo_id=repo_id)

    if len(resolved_preserved_paths) < 2:
        raise DecisionCheckpointError(
            f"Need at least two preserved dated guardrail snapshots for repo '{repo_id}' to build a decision checkpoint."
        )

    latest_payload = _load_json(latest_path)
    _validate_guardrail_payload(payload=latest_payload, repo_id=repo_id, path=latest_path)
    latest_signature = _comparison_signature(latest_payload)

    preserved_snapshots: list[dict[str, Any]] = []
    for path in sorted(resolved_preserved_paths, key=lambda item: item.name):
        if not path.exists():
            raise DecisionCheckpointError(f"Missing preserved guardrail snapshot: {atlas_relative(path, root=root)}")
        payload = _load_json(path)
        _validate_guardrail_payload(payload=payload, repo_id=repo_id, path=path)
        preserved_snapshots.append(
            {
                "path": path,
                "local_date": _snapshot_date(path),
                "generated_at": str(payload.get("generated_at") or ""),
                "signature": _comparison_signature(payload),
            }
        )

    preserved_drift: list[dict[str, Any]] = []
    baseline_snapshot = preserved_snapshots[0]
    for snapshot in preserved_snapshots[1:]:
        preserved_drift.extend(
            _diff_signatures(
                left_label="baseline",
                left=baseline_snapshot["signature"],
                right_label="observed",
                right=snapshot["signature"],
            )
        )

    latest_alignment_drift = _diff_signatures(
        left_label="preserved_latest",
        left=preserved_snapshots[-1]["signature"],
        right_label="rolling_latest",
        right=latest_signature,
    )
    matching_review, review_findings = _load_matching_review(
        root=root,
        repo_id=repo_id,
        latest_signature=latest_signature,
        latest_alignment_drift=latest_alignment_drift,
    )

    upgrade_review_reasons: list[str] = []
    if preserved_drift:
        upgrade_review_reasons.append("preserved dated guardrail snapshots drifted across the compared operating window")
    if latest_alignment_drift and matching_review is None:
        upgrade_review_reasons.append("rolling latest guardrail report no longer matches the newest preserved checkpoint")
    if latest_signature.get("deployment_posture") != "ok":
        upgrade_review_reasons.append("deployment posture is no longer ok")
    upgrade_review_reasons.extend(review_findings)

    if upgrade_review_reasons:
        decision = "upgrade_review_required"
        checkpoint_status = "blocked"
        decision_reason = "; ".join(upgrade_review_reasons)
        next_action = "open one explicit upgrade or pressure-review checkpoint before relying on Hobby by default"
    elif latest_alignment_drift and matching_review is not None:
        decision = "keep_hobby"
        checkpoint_status = "ready"
        decision_reason = str(matching_review.get("decision_reason") or "").strip() or (
            "current drift is covered by a matching no-secret Hobby pressure review and deployment posture remains ok"
        )
        next_action = str(matching_review.get("next_action") or "").strip() or (
            "stay on Hobby by default and refresh the checkpoint on the next governed cadence"
        )
    else:
        decision = "keep_hobby"
        checkpoint_status = "ready"
        decision_reason = (
            "preserved snapshots stayed stable across the compared window, the rolling latest report still aligns with "
            "the newest preserved checkpoint, and deployment posture remains ok"
        )
        next_action = "stay on Hobby by default and refresh the checkpoint on the next governed cadence"

    return {
        "contract_version": CONTRACT_VERSION,
        "checkpoint_id": f"vercel-hobby-decision-{repo_id}",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "repo_id": repo_id,
        "checkpoint_status": checkpoint_status,
        "decision": decision,
        "decision_reason": decision_reason,
        "next_action": next_action,
        "latest_guardrail_ref": atlas_relative(latest_path, root=root),
        "preserved_guardrail_refs": [atlas_relative(snapshot["path"], root=root) for snapshot in preserved_snapshots],
        "preserved_local_dates": [snapshot["local_date"] for snapshot in preserved_snapshots if snapshot["local_date"]],
        "latest_guardrail_generated_at": str(latest_payload.get("generated_at") or ""),
        "approved_review_ref": str((matching_review or {}).get("review_ref") or ""),
        "accepted_signature_digest": str((matching_review or {}).get("accepted_signature_digest") or ""),
        "guardrail_posture": latest_payload.get("guardrail_posture", {}),
        "comparison": {
            "baseline_preserved_ref": atlas_relative(baseline_snapshot["path"], root=root),
            "latest_preserved_ref": atlas_relative(preserved_snapshots[-1]["path"], root=root),
            "preserved_snapshot_count": len(preserved_snapshots),
            "stable_field_count": len(latest_signature) - len({diff["field"] for diff in preserved_drift + latest_alignment_drift}),
            "preserved_snapshot_drift": preserved_drift,
            "latest_alignment_drift": latest_alignment_drift,
            "current_signature": latest_signature,
            "current_signature_digest": _signature_digest(latest_signature),
        },
        "notes": [
            "This checkpoint is repo-local and no-secret by design; it does not read live Vercel billing counters.",
            "keep_hobby means current preserved repo-state pressure does not justify a default upgrade decision.",
            "upgrade_review_required means route, fetch, posture, or preserved-trend drift needs an explicit operator review before leaning on Hobby by default.",
            "A matching no-secret Hobby review may approve a bounded baseline reset only when its signature digest matches the current guardrail signature.",
        ],
    }


def render_markdown(checkpoint: dict[str, Any]) -> str:
    lines = [
        "# Vercel Hobby Decision Checkpoint",
        "",
        f"- checkpoint id: `{checkpoint['checkpoint_id']}`",
        f"- generated at: `{checkpoint['generated_at']}`",
        f"- repo id: `{checkpoint['repo_id']}`",
        f"- checkpoint status: `{checkpoint['checkpoint_status']}`",
        f"- decision: `{checkpoint['decision']}`",
        f"- reason: {checkpoint['decision_reason']}",
        f"- next action: {checkpoint['next_action']}",
        f"- latest guardrail ref: `{checkpoint['latest_guardrail_ref']}`",
        f"- approved review ref: `{checkpoint.get('approved_review_ref') or '-'}`",
        f"- current signature digest: `{checkpoint['comparison'].get('current_signature_digest') or '-'}`",
        "",
        "## Preserved Trend Window",
        "",
        f"- preserved snapshot count: `{checkpoint['comparison']['preserved_snapshot_count']}`",
        f"- preserved local dates: `{', '.join(checkpoint.get('preserved_local_dates', [])) or 'n/a'}`",
        f"- baseline preserved ref: `{checkpoint['comparison']['baseline_preserved_ref']}`",
        f"- latest preserved ref: `{checkpoint['comparison']['latest_preserved_ref']}`",
        "",
        "## Guardrail Posture",
        "",
    ]
    posture = checkpoint.get("guardrail_posture", {})
    if isinstance(posture, dict) and posture:
        for key, value in sorted(posture.items()):
            lines.append(f"- {key.replace('_', ' ')}: `{value}`")
    else:
        lines.append("- `(none)`")

    lines.extend(["", "## Drift Review", ""])
    preserved_drift = checkpoint["comparison"].get("preserved_snapshot_drift", [])
    latest_alignment_drift = checkpoint["comparison"].get("latest_alignment_drift", [])
    if not preserved_drift and not latest_alignment_drift:
        lines.append("- no preserved-trend drift detected")
        lines.append("- rolling latest guardrail still matches the newest preserved checkpoint")
    else:
        for diff in preserved_drift:
            lines.append(
                f"- preserved drift `{diff['field']}`: baseline=`{diff.get('baseline')}` observed=`{diff.get('observed')}`"
            )
        for diff in latest_alignment_drift:
            lines.append(
                f"- latest-alignment drift `{diff['field']}`: preserved=`{diff.get('preserved_latest')}` rolling=`{diff.get('rolling_latest')}`"
            )

    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in checkpoint.get("notes", []))
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a no-secret Vercel Hobby keep-Hobby vs upgrade-review checkpoint from preserved guardrail snapshots."
    )
    parser.add_argument("--root", default=str(ROOT), help="ATLAS root path")
    parser.add_argument("--repo-id", default="fitness", help="Repo id from stack.yaml")
    parser.add_argument("--latest-ref", help="ATLAS-relative or absolute ref to the rolling latest guardrail JSON")
    parser.add_argument(
        "--preserved-ref",
        action="append",
        default=[],
        help="ATLAS-relative or absolute ref to a preserved dated guardrail JSON; may be repeated",
    )
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--output", help="Optional ATLAS-relative or absolute output path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    checkpoint = build_checkpoint(
        root=root,
        repo_id=args.repo_id,
        latest_ref=args.latest_ref,
        preserved_refs=args.preserved_ref,
    )
    rendered = json.dumps(checkpoint, indent=2) + "\n" if args.format == "json" else render_markdown(checkpoint)
    output = args.output or _default_output_ref(args.repo_id, args.format)
    output_path = Path(output)
    if not output_path.is_absolute():
        output_path = root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    if not args.output:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
