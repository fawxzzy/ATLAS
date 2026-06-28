from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.qa._common import (
    default_evidence_index_path,
    default_release_readiness_path,
    default_run_root,
    utc_now,
)
from ops.cortex._artifacts import write_json


def _copy_ref(*, base_root: Path, ref: str, target_dir: Path) -> str:
    source = (base_root / ref).resolve()
    if not source.exists():
        raise FileNotFoundError(f"Snapshot source does not exist: {ref}")
    destination = (target_dir / ref).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return atlas_relative(destination, root=base_root)


def _load_manual_attestation_statuses(*, run_root: Path) -> dict[str, str]:
    result_path = run_root / "manual_attestation.result.json"
    if not result_path.exists():
        return {}
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    statuses: dict[str, str] = {}
    for item in payload.get("attestations", []):
        if not isinstance(item, dict):
            continue
        lens_id = str(item.get("lens_id") or "")
        status = str(item.get("status") or "")
        if lens_id:
            statuses[lens_id] = status
    return statuses


def _manual_evidence_token(lens_id: str) -> str:
    return lens_id if lens_id.endswith(".manual") else f"{lens_id}.manual"


def _derive_evidence_summary(*, run_root: Path, promotion: dict[str, Any], report_summary: dict[str, Any]) -> tuple[list[str], list[str]]:
    evidence_present: set[str] = set()
    for item in report_summary.get("per_lens", []):
        if not isinstance(item, dict):
            continue
        lens_id = str(item.get("lens_id") or "")
        if lens_id and str(item.get("status") or "") == "pass":
            evidence_present.add(lens_id)
    manual_statuses = _load_manual_attestation_statuses(run_root=run_root)
    for lens_id, status in manual_statuses.items():
        if status == "valid":
            evidence_present.add(_manual_evidence_token(lens_id))

    evidence_missing = {
        _manual_evidence_token(str(lens_id))
        for lens_id in promotion.get("manual_required_lanes", [])
        if isinstance(lens_id, str) and lens_id.strip()
    }
    evidence_missing.update(
        _manual_evidence_token(str(lens_id))
        for lens_id in promotion.get("waived_lanes", [])
        if isinstance(lens_id, str) and lens_id.strip()
    )
    return sorted(evidence_present), sorted(evidence_missing)


def build_release_snapshot(
    *,
    root: Path | None = None,
    repo_id: str,
    run_id: str = "",
    output_dir: Path | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    readiness_path = default_release_readiness_path(root=base_root)
    evidence_index_path = default_evidence_index_path(root=base_root)
    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    evidence_index = json.loads(evidence_index_path.read_text(encoding="utf-8"))
    repos = readiness.get("repos", []) if isinstance(readiness.get("repos"), list) else []
    repo_entry = next((item for item in repos if isinstance(item, dict) and str(item.get("repo_id") or "") == repo_id), None)
    if repo_entry is None:
        raise ValueError(f"Repo '{repo_id}' is not present in release readiness.")
    selected_run_id = run_id.strip() or str(repo_entry.get("readiness_source_run_id") or "")
    if not selected_run_id:
        raise ValueError(f"Repo '{repo_id}' has no selected readiness run.")
    run_root = default_run_root(root=base_root) / selected_run_id
    promotion_payload = json.loads((run_root / "promotion.record.json").read_text(encoding="utf-8"))
    report_summary_payload = json.loads((run_root / "report.summary.json").read_text(encoding="utf-8"))
    timestamp = selected_run_id if output_dir is None else ""
    snapshot_root = output_dir.resolve() if isinstance(output_dir, Path) else (base_root / "runtime" / "atlas" / "releases" / repo_id / timestamp).resolve()
    snapshot_root.mkdir(parents=True, exist_ok=True)

    copied_refs = {
        "promotion_ref": _copy_ref(base_root=base_root, ref=atlas_relative(run_root / "promotion.record.json", root=base_root), target_dir=snapshot_root),
        "report_summary_ref": _copy_ref(base_root=base_root, ref=atlas_relative(run_root / "report.summary.json", root=base_root), target_dir=snapshot_root),
        "release_readiness_ref": _copy_ref(base_root=base_root, ref=atlas_relative(readiness_path, root=base_root), target_dir=snapshot_root),
        "evidence_index_ref": _copy_ref(base_root=base_root, ref=atlas_relative(evidence_index_path, root=base_root), target_dir=snapshot_root),
        "stack_validation_ref": _copy_ref(base_root=base_root, ref="runtime/receipts/validation/stack-validation.latest.json", target_dir=snapshot_root),
        "stack_warning_budget_ref": _copy_ref(base_root=base_root, ref="runtime/receipts/validation/stack-warning-budget.latest.json", target_dir=snapshot_root),
    }
    waiver_refs = [str(value) for value in repo_entry.get("waiver_refs", []) if isinstance(value, str) and value.strip()]
    copied_waivers = [_copy_ref(base_root=base_root, ref=ref, target_dir=snapshot_root) for ref in waiver_refs]
    evidence_present, evidence_missing = _derive_evidence_summary(
        run_root=run_root,
        promotion=promotion_payload,
        report_summary=report_summary_payload,
    )

    summary = {
        "contract_version": "atlas.qa.release_snapshot.v1",
        "generated_at": utc_now(),
        "repo_id": repo_id,
        "run_id": selected_run_id,
        "target_sha": str(repo_entry.get("target_sha") or ""),
        "receipt_sha": str(repo_entry.get("receipt_sha") or ""),
        "promotion_status": str(repo_entry.get("promotion_status") or ""),
        "promotion_display_status": str(repo_entry.get("promotion_display_status") or ""),
        "release_ready": bool(repo_entry.get("release_ready")),
        "release_ready_with_waiver": bool(repo_entry.get("release_ready_with_waiver")),
        "trusted_origin_status": str(repo_entry.get("trusted_origin_status") or ""),
        "origin_enforcement_stage": str(repo_entry.get("origin_enforcement_stage") or ""),
        "waived_lanes": list(repo_entry.get("validated_waived_lanes", [])),
        "waiver_expires_at": str(repo_entry.get("waiver_expires_at") or ""),
        "days_until_expiry": repo_entry.get("days_until_expiry"),
        "evidence_present": evidence_present,
        "evidence_missing": evidence_missing,
        "copied_refs": copied_refs,
        "waiver_refs": copied_waivers,
    }
    summary_path = snapshot_root / "release-snapshot.json"
    write_json(summary_path, summary)

    md_lines = [
        f"# ATLAS Release Snapshot: `{repo_id}`",
        "",
        f"- Generated at: `{summary['generated_at']}`",
        f"- Run id: `{selected_run_id}`",
        f"- Promotion status: `{summary['promotion_status']}`",
        f"- Promotion display: `{summary['promotion_display_status']}`",
        f"- Release ready: `{summary['release_ready']}`",
        f"- Release ready with waiver: `{summary['release_ready_with_waiver']}`",
        f"- Target SHA: `{summary['target_sha'] or '-'}`",
        f"- Receipt SHA: `{summary['receipt_sha'] or '-'}`",
        f"- Trusted origin status: `{summary['trusted_origin_status']}`",
        f"- Origin enforcement stage: `{summary['origin_enforcement_stage']}`",
        f"- Waived lanes: `{', '.join(summary['waived_lanes']) or 'none'}`",
        f"- Waiver expiry: `{summary['waiver_expires_at'] or 'none'}`",
        f"- Evidence present: `{', '.join(summary['evidence_present']) or 'n/a'}`",
        f"- Evidence missing: `{', '.join(summary['evidence_missing']) or 'none'}`",
        "",
        "## Included Receipts",
        "",
    ]
    for key, value in copied_refs.items():
        md_lines.append(f"- `{key}`: `{value}`")
    for value in copied_waivers:
        md_lines.append(f"- `waiver_ref`: `{value}`")
    md_path = snapshot_root / "release-snapshot.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    return {
        "generated_at": summary["generated_at"],
        "snapshot_root": atlas_relative(snapshot_root, root=base_root),
        "snapshot_summary_ref": atlas_relative(summary_path, root=base_root),
        "snapshot_md_ref": atlas_relative(md_path, root=base_root),
        "repo_id": repo_id,
        "run_id": selected_run_id,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture a release snapshot pack for a repo's current ATLAS QA readiness state.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--repo", required=True)
    parser.add_argument("--run")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    result = build_release_snapshot(
        root=args.root.resolve(),
        repo_id=args.repo,
        run_id=str(args.run or ""),
        output_dir=args.output_dir.resolve() if isinstance(args.output_dir, Path) else None,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
