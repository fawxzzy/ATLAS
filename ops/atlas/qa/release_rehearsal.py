from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.qa._common import load_json_object, utc_now
from ops.atlas.qa.release_readiness import build_release_readiness
from ops.cortex._artifacts import write_json


def default_release_rehearsal_path(*, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "atlas" / "qa" / "release-rehearsal.latest.json"


def build_release_rehearsal(
    *,
    root: Path | None = None,
    output_file: Path | None = None,
    max_receipt_age_hours: float = 168.0,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    readiness_result = build_release_readiness(root=base_root, max_receipt_age_hours=max_receipt_age_hours)
    readiness_payload = load_json_object((base_root / readiness_result["release_readiness_ref"]).resolve())
    repos = readiness_payload.get("repos", []) if isinstance(readiness_payload.get("repos"), list) else []

    rehearsals: list[dict[str, Any]] = []
    for item in repos:
        if not isinstance(item, dict):
            continue
        repo_id = str(item.get("repo_id") or "")
        release_gate_status = str(item.get("release_gate_status") or "blocked")
        rehearsals.append(
            {
                "repo_id": repo_id,
                "release_profile": str(item.get("release_profile") or ""),
                "trigger_mode": "push-release-branch",
                "target_sha": str(item.get("target_sha") or ""),
                "receipt_sha": str(item.get("receipt_sha") or ""),
                "sha_match": bool(item.get("sha_match")),
                "readiness_status": "pass" if bool(item.get("release_ready")) else "fail",
                "release_gate_status": release_gate_status,
                "receipt_origin_type": str(item.get("receipt_origin_type") or ""),
                "trusted_origin_status": str(item.get("trusted_origin_status") or ""),
                "origin_enforcement_stage": str(item.get("origin_enforcement_stage") or ""),
                "waived_lanes": list(item.get("validated_waived_lanes", [])) if isinstance(item.get("validated_waived_lanes"), list) else [],
                "waiver_valid": bool(item.get("waiver_valid")),
                "waiver_expires_at": str(item.get("waiver_expires_at") or ""),
                "days_until_expiry": item.get("days_until_expiry"),
                "blocker_summary": list(item.get("release_blockers", [])),
                "receipt_used": str(item.get("readiness_source_run_id") or ""),
                "selection_reason": str(item.get("selection_reason") or ""),
                "stack_lock_pin": str(item.get("stack_lock_pin") or ""),
            }
        )

    payload = {
        "contract_version": "atlas.qa.release_rehearsal.v1",
        "generated_at": utc_now(),
        "release_readiness_ref": readiness_result["release_readiness_ref"],
        "repos": rehearsals,
        "summary": {
            "repo_count": len(rehearsals),
            "pass_count": sum(1 for item in rehearsals if item["readiness_status"] == "pass"),
            "fail_count": sum(1 for item in rehearsals if item["readiness_status"] == "fail"),
        },
    }
    target = output_file.resolve() if isinstance(output_file, Path) else default_release_rehearsal_path(root=base_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, payload)
    md_path = target.with_suffix(".md")
    md_lines = [
        "# ATLAS QA Release Rehearsal",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Release readiness: `{payload['release_readiness_ref']}`",
        f"- Repos: `{payload['summary']['repo_count']}`",
        f"- Pass: `{payload['summary']['pass_count']}`",
        f"- Fail: `{payload['summary']['fail_count']}`",
        "",
        "| Repo | Release Tier | Trigger | Target SHA | Receipt SHA | Origin | Origin Status | Waiver | Status | Receipt |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in rehearsals:
        md_lines.append(
            f"| {item['repo_id']} | {item['release_profile']} | {item['trigger_mode']} | {item['target_sha'] or '-'} | {item['receipt_sha'] or '-'} | {item['receipt_origin_type'] or '-'} | {item['trusted_origin_status'] or '-'} | {', '.join(item.get('waived_lanes', [])) or '-'} | {item['readiness_status']} | {item['receipt_used'] or '-'} |"
        )
        if item.get("selection_reason"):
            md_lines.append(f"|  |  |  |  |  |  | selection: {item['selection_reason']} |  |  |")
        if item.get("waiver_expires_at"):
            md_lines.append(f"|  |  |  |  |  |  | waiver expires: {item['waiver_expires_at']} ({item.get('days_until_expiry')}) |  |  |")
        for blocker in item["blocker_summary"]:
            md_lines.append(f"|  |  |  |  |  | blocker: {blocker} |  |")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return {
        "generated_at": payload["generated_at"],
        "release_rehearsal_ref": atlas_relative(target, root=base_root),
        "release_rehearsal_md_ref": atlas_relative(md_path, root=base_root),
        "repo_count": payload["summary"]["repo_count"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rehearse ATLAS repo-tier release gates without mutating repo state.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--output-file", type=Path)
    parser.add_argument("--max-receipt-age-hours", type=float, default=168.0)
    args = parser.parse_args(argv)
    result = build_release_rehearsal(
        root=args.root.resolve(),
        output_file=args.output_file.resolve() if isinstance(args.output_file, Path) else None,
        max_receipt_age_hours=args.max_receipt_age_hours,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
