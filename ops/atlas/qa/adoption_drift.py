from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.qa._common import (
    default_adoption_drift_path,
    default_evidence_index_path,
    default_release_policy_path,
    load_json_object,
    utc_now,
    validate_adapter_manifest,
    validate_schema_definition,
    validate_scenario_manifest,
)
from ops.cortex._artifacts import write_json


def _parse_utc(value: str) -> datetime | None:
    if not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _root_prototype_repos(base_root: Path) -> dict[str, list[str]]:
    prototype_refs: dict[str, list[str]] = {}
    adapters_root = base_root / "ops" / "atlas" / "qa" / "adapters"
    if not adapters_root.exists():
        return prototype_refs
    for candidate in sorted(adapters_root.glob("*.json")):
        try:
            payload = load_json_object(candidate)
        except Exception:
            continue
        repo_id = str(payload.get("repo_id") or "").strip()
        if not repo_id:
            continue
        prototype_refs.setdefault(repo_id, []).append(atlas_relative(candidate, root=base_root))
    return prototype_refs


def _root_prototype_scenarios(base_root: Path) -> dict[str, list[str]]:
    prototype_refs: dict[str, list[str]] = {}
    scenarios_root = base_root / "ops" / "atlas" / "qa" / "scenarios"
    if not scenarios_root.exists():
        return prototype_refs
    for candidate in sorted(scenarios_root.glob("*.json")):
        try:
            payload = load_json_object(candidate)
        except Exception:
            continue
        repo_id = str(payload.get("repo_id") or "").strip()
        if not repo_id:
            continue
        prototype_refs.setdefault(repo_id, []).append(atlas_relative(candidate, root=base_root))
    return prototype_refs


def build_adoption_drift(
    *,
    root: Path | None = None,
    evidence_index_file: Path | None = None,
    policy_file: Path | None = None,
    output_file: Path | None = None,
    max_receipt_age_hours: float = 168.0,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    evidence_index_path = evidence_index_file.resolve() if isinstance(evidence_index_file, Path) else default_evidence_index_path(root=base_root)
    policy_path = policy_file.resolve() if isinstance(policy_file, Path) else default_release_policy_path(root=base_root)
    evidence_index = load_json_object(evidence_index_path)
    policy = load_json_object(policy_path)
    adoption = evidence_index.get("adoption", []) if isinstance(evidence_index.get("adoption"), list) else []
    runs = evidence_index.get("runs", []) if isinstance(evidence_index.get("runs"), list) else []
    repo_overrides = policy.get("repo_overrides", {}) if isinstance(policy.get("repo_overrides"), dict) else {}
    profiles = policy.get("profiles", {}) if isinstance(policy.get("profiles"), dict) else {}
    valid_profiles = set(profiles)
    expected_profile_by_release_profile = {
        "package_contract": "package_contract",
        "docs_governance": "docs_governance",
        "web_visual": "web_visual",
        "release_critical_web": "web_visual",
    }
    runs_by_repo: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        if not isinstance(run, dict):
            continue
        repo_id = str(run.get("repo_id") or "")
        if not repo_id:
            continue
        runs_by_repo.setdefault(repo_id, []).append(run)

    prototypes = _root_prototype_repos(base_root)
    prototype_scenarios = _root_prototype_scenarios(base_root)
    schema_errors = {
        "adapter": validate_schema_definition("atlas.qa.adapter.v1", root=base_root),
        "scenario": validate_schema_definition("atlas.qa.scenario.v1", root=base_root),
    }
    repos: list[dict[str, Any]] = []
    for item in adoption:
        if not isinstance(item, dict):
            continue
        repo_id = str(item.get("repo_id") or "")
        adapter_refs = [str(value) for value in item.get("adapter_refs", []) if isinstance(value, str)]
        scenario_refs = [str(value) for value in item.get("scenario_refs", []) if isinstance(value, str)]
        docs_ref = f"repos/fawxzzy-{repo_id}/docs/qa.md"
        docs_path = (base_root / docs_ref).resolve()
        receipt_run_id = str(item.get("last_run_id") or "")
        repo_runs = runs_by_repo.get(repo_id, [])
        latest_run = next((run for run in repo_runs if str(run.get("run_id") or "") == receipt_run_id), None)
        latest_generated_at = str((latest_run or {}).get("promotion_generated_at") or "")
        latest_dt = _parse_utc(latest_generated_at)
        receipt_age_hours = None
        if latest_dt is not None:
            receipt_age_hours = round((datetime.now(timezone.utc) - latest_dt).total_seconds() / 3600, 3)
        adapter_validation_errors: list[str] = [*schema_errors["adapter"]]
        for ref in adapter_refs:
            payload = load_json_object((base_root / ref).resolve())
            adapter_validation_errors.extend(validate_adapter_manifest(payload, root=base_root))
        scenario_validation_errors: list[str] = [*schema_errors["scenario"]]
        for ref in scenario_refs:
            payload = load_json_object((base_root / ref).resolve())
            scenario_validation_errors.extend(validate_scenario_manifest(payload, root=base_root))

        evidence_profile = str(item.get("evidence_profile") or "")
        release_profile = str((repo_overrides.get(repo_id) or {}).get("release_profile") or evidence_profile or "package_contract")
        findings: list[str] = []
        if not adapter_refs:
            findings.append("missing child-owned adapter manifest")
        if not scenario_refs:
            findings.append("missing child-owned scenario manifest")
        if not docs_path.exists():
            findings.append("missing docs/qa.md")
        if adapter_validation_errors:
            findings.append("adapter manifest validation failed")
        if scenario_validation_errors:
            findings.append("scenario manifest validation failed")
        if release_profile not in valid_profiles:
            findings.append(f"unknown release profile '{release_profile}'")
        expected_profile = expected_profile_by_release_profile.get(release_profile)
        if expected_profile and evidence_profile and evidence_profile != expected_profile:
            findings.append(
                f"evidence profile '{evidence_profile}' does not match release profile '{release_profile}' expectations"
            )
        if not receipt_run_id:
            findings.append("no meaningful receipt recorded")
        elif latest_run is None:
            findings.append("latest receipt is not present in the evidence index runs list")
        if receipt_age_hours is None:
            findings.append("latest receipt timestamp missing or unreadable")
        elif receipt_age_hours > max_receipt_age_hours:
            findings.append(f"latest meaningful receipt is stale ({receipt_age_hours}h > {max_receipt_age_hours}h)")
        root_only_prototypes = [
            ref for ref in prototypes.get(repo_id, [])
            if not ref.startswith(f"repos/fawxzzy-{repo_id}/")
        ]
        status = "clean" if not findings else "drift"
        repos.append(
            {
                "repo_id": repo_id,
                "status": status,
                "adopted": bool(item.get("adopted")),
                "adapter_refs": adapter_refs,
                "scenario_refs": scenario_refs,
                "docs_ref": docs_ref,
                "docs_present": docs_path.exists(),
                "evidence_profile": evidence_profile,
                "release_profile": release_profile,
                "last_run_id": receipt_run_id,
                "last_promotion_status": str(item.get("last_promotion_status") or ""),
                "last_promotion_display_status": str(item.get("last_promotion_display_status") or ""),
                "last_promotion_generated_at": latest_generated_at,
                "receipt_age_hours": receipt_age_hours,
                "receipt_fresh": isinstance(receipt_age_hours, (int, float)) and receipt_age_hours <= max_receipt_age_hours,
                "adapter_validation_errors": sorted(set(adapter_validation_errors)),
                "scenario_validation_errors": sorted(set(scenario_validation_errors)),
                "root_prototype_refs": root_only_prototypes,
                "findings": findings,
            }
        )

    prototype_only_repo_ids = sorted(
        repo_id for repo_id, refs in prototypes.items()
        if repo_id not in {item["repo_id"] for item in repos} and refs
    )
    prototype_only = [
        {
            "repo_id": repo_id,
            "disposition": "prototype_only_root_config",
            "adapter_refs": prototypes.get(repo_id, []),
            "scenario_refs": prototype_scenarios.get(repo_id, []),
            "reason": "Root-owned prototype config exists without child-owned QA intent or adoption receipts.",
        }
        for repo_id in prototype_only_repo_ids
    ]
    payload = {
        "contract_version": "atlas.qa.adoption_drift.v1",
        "generated_at": utc_now(),
        "evidence_index_ref": atlas_relative(evidence_index_path, root=base_root),
        "release_policy_ref": atlas_relative(policy_path, root=base_root),
        "max_receipt_age_hours": max_receipt_age_hours,
        "repos": repos,
        "summary": {
            "repo_count": len(repos),
            "clean_count": sum(1 for item in repos if item["status"] == "clean"),
            "drift_count": sum(1 for item in repos if item["status"] != "clean"),
            "prototype_only_repo_count": len(prototype_only),
            "prototype_only_repos": prototype_only_repo_ids,
        },
        "prototype_only": prototype_only,
    }
    target = output_file.resolve() if isinstance(output_file, Path) else default_adoption_drift_path(root=base_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, payload)
    md_path = target.with_suffix(".md")
    md_lines = [
        "# ATLAS QA Adoption Drift",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Evidence index: `{payload['evidence_index_ref']}`",
        f"- Release policy: `{payload['release_policy_ref']}`",
        f"- Max receipt age (hours): `{max_receipt_age_hours}`",
        f"- Repos: `{payload['summary']['repo_count']}`",
        f"- Clean: `{payload['summary']['clean_count']}`",
        f"- Drift: `{payload['summary']['drift_count']}`",
        "",
        "| Repo | Status | Profile | Release Tier | Receipt | Fresh | Docs | Promotion |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in repos:
        md_lines.append(
            f"| {item['repo_id']} | {item['status']} | {item['evidence_profile'] or '-'} | {item['release_profile']} | {item['last_run_id'] or '-'} | {item['receipt_fresh']} | {item['docs_present']} | {item['last_promotion_display_status'] or item['last_promotion_status'] or '-'} |"
        )
        for finding in item["findings"]:
            md_lines.append(f"|  |  |  |  |  |  |  | finding: {finding} |")
    if prototype_only:
        md_lines += ["", "## Prototype-Only Root Adapters", ""]
        for item in prototype_only:
            md_lines.append(f"- `{item['repo_id']}`: {item['reason']}")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return {
        "generated_at": payload["generated_at"],
        "adoption_drift_ref": atlas_relative(target, root=base_root),
        "adoption_drift_md_ref": atlas_relative(md_path, root=base_root),
        "repo_count": payload["summary"]["repo_count"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan child-repo QA adoption drift against ATLAS QA LLEL v1.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--evidence-index-file", type=Path)
    parser.add_argument("--policy-file", type=Path)
    parser.add_argument("--output-file", type=Path)
    parser.add_argument("--max-receipt-age-hours", type=float, default=168.0)
    args = parser.parse_args(argv)
    result = build_adoption_drift(
        root=args.root.resolve(),
        evidence_index_file=args.evidence_index_file.resolve() if isinstance(args.evidence_index_file, Path) else None,
        policy_file=args.policy_file.resolve() if isinstance(args.policy_file, Path) else None,
        output_file=args.output_file.resolve() if isinstance(args.output_file, Path) else None,
        max_receipt_age_hours=args.max_receipt_age_hours,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
