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
from ops.atlas.qa._common import (
    EVIDENCE_INDEX_CONTRACT_VERSION,
    display_promotion_status,
    default_evidence_index_path,
    default_run_root,
    utc_now,
    validate_evidence_index_payload,
)
from ops.cortex._artifacts import write_json


def _repo_contracts(base_root: Path) -> dict[str, dict[str, list[str]]]:
    contracts: dict[str, dict[str, list[str]]] = {}
    repos_root = base_root / "repos"
    if not repos_root.exists():
        return contracts
    for repo_root in repos_root.iterdir():
        if not repo_root.is_dir():
            continue
        adapters = sorted((repo_root / "qa" / "adapters").glob("*.json")) if (repo_root / "qa" / "adapters").exists() else []
        scenarios = sorted((repo_root / "qa" / "scenarios").glob("*.json")) if (repo_root / "qa" / "scenarios").exists() else []
        if not adapters and not scenarios:
            continue
        repo_id = repo_root.name.removeprefix("fawxzzy-")
        contracts[repo_id] = {
            "adapter_refs": [atlas_relative(path, root=base_root) for path in adapters],
            "scenario_refs": [atlas_relative(path, root=base_root) for path in scenarios],
        }
    return contracts


def _adoption_rank(run_entry: dict[str, Any]) -> tuple[int, str]:
    promotion_status = str(run_entry.get("promotion_status") or "")
    mode = str(run_entry.get("mode") or "")
    generated_at = str(run_entry.get("promotion_generated_at") or "")
    meaningful = 0 if promotion_status == "dry_run" or mode == "dry_run" else 1
    return (meaningful, generated_at)


def build_evidence_index(*, root: Path | None = None, output_file: Path | None = None) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    run_root = default_run_root(root=base_root)
    runs: list[dict[str, Any]] = []
    latest_by_repo: dict[str, dict[str, Any]] = {}
    for candidate in sorted(run_root.glob("*/promotion.record.json")):
        promotion = json.loads(candidate.read_text(encoding="utf-8"))
        run_dir = candidate.parent
        matrix_path = run_dir / "matrix.result.json"
        evaluated_path = run_dir / "evaluated.result.json"
        report_summary_path = run_dir / "report.summary.json"
        matrix = json.loads(matrix_path.read_text(encoding="utf-8")) if matrix_path.exists() else {}
        evaluated = json.loads(evaluated_path.read_text(encoding="utf-8")) if evaluated_path.exists() else {}
        summary = evaluated.get("summary", {}) if isinstance(evaluated.get("summary"), dict) else {}
        run_entry = {
            "run_id": str(promotion.get("run_id") or run_dir.name),
            "scenario_id": str(promotion.get("scenario_id") or ""),
            "adapter_id": str(matrix.get("adapter_id") or ""),
            "repo_id": str(promotion.get("repo_id") or matrix.get("repo_id") or ""),
            "git_sha": str(matrix.get("git_sha") or ""),
            "mode": str(matrix.get("mode") or ""),
            "promotion_status": str(promotion.get("promotion_status") or ""),
            "evidence_profile": str(promotion.get("evidence_profile") or summary.get("evidence_profile") or ""),
            "highest_satisfied_tier": str(promotion.get("highest_satisfied_tier") or ""),
            "visual_status": str(summary.get("visual_status") or "not_configured"),
            "report_summary_ref": atlas_relative(report_summary_path, root=base_root) if report_summary_path.exists() else "",
            "artifact_manifest_ref": atlas_relative(run_dir / "artifacts.manifest.json", root=base_root),
            "missing_evidence_tiers": list(promotion.get("missing_evidence_tiers", [])),
            "waived_lanes": list(promotion.get("waived_lanes", [])),
            "waiver_refs": list(promotion.get("waiver_refs", [])),
            "waiver_reasons": list(promotion.get("waiver_reasons", [])),
            "blocking_reasons": list(promotion.get("blocking_reasons", [])),
            "manual_gaps": list(promotion.get("manual_gaps", [])),
            "promotion_generated_at": str(promotion.get("generated_at") or ""),
            "promotion_contract_version": str(promotion.get("contract_version") or ""),
            "runner_version": str(evaluated.get("runner_version") or ""),
            "receipt_origin": promotion.get("receipt_origin") if isinstance(promotion.get("receipt_origin"), dict) else {},
        }
        run_entry["promotion_display_status"] = display_promotion_status(
            promotion_status=str(run_entry["promotion_status"]),
            evidence_profile=str(run_entry["evidence_profile"]),
        )
        runs.append(run_entry)
        repo_id = run_entry["repo_id"]
        previous = latest_by_repo.get(repo_id)
        if previous is None or _adoption_rank(run_entry) > _adoption_rank(previous):
            latest_by_repo[repo_id] = run_entry
    contracts = _repo_contracts(base_root)
    adoption: list[dict[str, Any]] = []
    for repo_id in sorted(contracts):
        latest = latest_by_repo.get(repo_id, {})
        contract_refs = contracts[repo_id]
        adoption.append(
            {
                "repo_id": repo_id,
                "adopted": True,
                "owner": repo_id,
                "adapter_refs": contract_refs["adapter_refs"],
                "scenario_refs": contract_refs["scenario_refs"],
                "evidence_profile": str(latest.get("evidence_profile") or ""),
                "last_run_id": str(latest.get("run_id") or ""),
                "last_git_sha": str(latest.get("git_sha") or ""),
                "last_promotion_status": str(latest.get("promotion_status") or ""),
                "last_promotion_display_status": str(latest.get("promotion_display_status") or latest.get("promotion_status") or ""),
                "root_runner_version": str(latest.get("runner_version") or ""),
                "contract_version": str(latest.get("promotion_contract_version") or EVIDENCE_INDEX_CONTRACT_VERSION),
                "receipt_origin_type": str((latest.get("receipt_origin") or {}).get("origin_type") or ""),
                "waived_lanes": list(latest.get("waived_lanes", [])) if isinstance(latest, dict) else [],
            }
        )
    payload = {
        "contract_version": EVIDENCE_INDEX_CONTRACT_VERSION,
        "generated_at": utc_now(),
        "runs": runs,
        "adoption": adoption,
        "summary": {
            "run_count": len(runs),
            "promoted_count": sum(1 for item in runs if str(item["promotion_status"]).startswith("promoted")),
            "manual_review_count": sum(1 for item in runs if item["promotion_status"] == "manual_review"),
            "blocked_count": sum(1 for item in runs if item["promotion_status"] == "blocked"),
            "dry_run_count": sum(1 for item in runs if item["promotion_status"] == "dry_run"),
            "waived_count": sum(1 for item in runs if item["promotion_status"] == "waived_promoted"),
            "adopted_repo_count": len(adoption),
        },
        "retention": {
            "keep_latest_n": 20,
            "keep_promoted": True,
            "keep_failed_for_days": 30,
            "keep_manual_review_for_days": 30,
            "mode": "report_only",
        },
    }
    errors = validate_evidence_index_payload(payload)
    if errors:
        raise ValueError("; ".join(errors))
    target = output_file.resolve() if isinstance(output_file, Path) else default_evidence_index_path(root=base_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, payload)
    md_path = target.with_suffix(".md")
    md_lines = [
        "# ATLAS QA Evidence Index",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Runs: `{payload['summary']['run_count']}`",
        f"- Promoted: `{payload['summary']['promoted_count']}`",
        f"- Manual review: `{payload['summary']['manual_review_count']}`",
        f"- Blocked: `{payload['summary']['blocked_count']}`",
        f"- Adopted repos: `{payload['summary']['adopted_repo_count']}`",
        "",
        "| Run | Repo | Scenario | Status | Display | Profile | Tier | Origin | Visual | Waived Lanes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in runs:
        md_lines.append(
            f"| {item['run_id']} | {item['repo_id']} | {item['scenario_id']} | {item['promotion_status']} | {item['promotion_display_status'] or '-'} | {item['evidence_profile'] or '-'} | {item['highest_satisfied_tier'] or '-'} | {str((item.get('receipt_origin') or {}).get('origin_type') or '-')} | {item['visual_status']} | {', '.join(item.get('waived_lanes', [])) or '-'} |"
        )
    if adoption:
        md_lines += ["", "## Adoption", "", "| Repo | Status | Display | Profile | Origin | Waived Lanes | Last Run | Root Runner |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        for item in adoption:
            md_lines.append(
                f"| {item['repo_id']} | {item['last_promotion_status'] or 'adopted'} | {item['last_promotion_display_status'] or item['last_promotion_status'] or 'adopted'} | {item['evidence_profile'] or '-'} | {item['receipt_origin_type'] or '-'} | {', '.join(item.get('waived_lanes', [])) or '-'} | {item['last_run_id'] or '-'} | {item['root_runner_version'] or '-'} |"
            )
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return {
        "generated_at": payload["generated_at"],
        "run_count": len(runs),
        "evidence_index_ref": atlas_relative(target, root=base_root),
        "evidence_index_md_ref": atlas_relative(md_path, root=base_root),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the ATLAS QA evidence index.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--output-file", type=Path)
    args = parser.parse_args(argv)
    result = build_evidence_index(
        root=args.root.resolve(),
        output_file=args.output_file.resolve() if isinstance(args.output_file, Path) else None,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
