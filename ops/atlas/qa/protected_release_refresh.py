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
    default_adapter_dir,
    default_release_policy_path,
    default_scenario_dir,
    load_json_object,
    utc_now,
)
from ops.atlas.qa.adoption_drift import build_adoption_drift
from ops.atlas.qa.ci_gate import ci_gate
from ops.atlas.qa.evidence_index import build_evidence_index
from ops.atlas.qa.release_readiness import (
    build_release_readiness,
    default_release_readiness_path,
    enforce_release_repo_readiness,
)
from ops.atlas.qa.release_rehearsal import build_release_rehearsal
from ops.atlas.qa.waiver_monitor import build_waiver_monitor
from ops.cortex._artifacts import write_json


def default_protected_release_refresh_path(*, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "atlas" / "qa" / "protected-release-refresh.latest.json"


def _resolve_release_targets(*, root: Path, repo_ids: list[str] | None = None) -> list[dict[str, str]]:
    policy = load_json_object(default_release_policy_path(root=root))
    repo_overrides = policy.get("repo_overrides", {}) if isinstance(policy.get("repo_overrides"), dict) else {}
    requested = [repo_id.strip() for repo_id in (repo_ids or sorted(repo_overrides)) if repo_id and repo_id.strip()]
    if not requested:
        raise ValueError("No release repos were resolved from release_policy.v1.json.")

    scenarios_by_repo: dict[str, list[dict[str, str]]] = {}
    for path in sorted(default_scenario_dir(root=root).glob("*.json")):
        payload = load_json_object(path)
        repo_id = str(payload.get("repo_id") or "").strip()
        scenario_id = str(payload.get("scenario_id") or "").strip()
        adapter_id = str(payload.get("adapter_id") or "").strip()
        if not repo_id or not scenario_id or not adapter_id:
            continue
        scenarios_by_repo.setdefault(repo_id, []).append(
            {
                "repo_id": repo_id,
                "scenario_id": scenario_id,
                "adapter_id": adapter_id,
            }
        )

    adapter_ids: set[str] = set()
    for path in sorted(default_adapter_dir(root=root).glob("*.json")):
        payload = load_json_object(path)
        adapter_id = str(payload.get("adapter_id") or "").strip()
        if adapter_id:
            adapter_ids.add(adapter_id)

    targets: list[dict[str, str]] = []
    for repo_id in requested:
        matches = scenarios_by_repo.get(repo_id, [])
        if not matches:
            raise ValueError(f"No release scenario was found for repo '{repo_id}'.")
        if len(matches) != 1:
            scenario_ids = ", ".join(sorted(item["scenario_id"] for item in matches))
            raise ValueError(f"Repo '{repo_id}' has multiple release scenarios and needs explicit routing: {scenario_ids}")
        target = matches[0]
        if target["adapter_id"] not in adapter_ids:
            raise ValueError(f"Repo '{repo_id}' points to missing adapter '{target['adapter_id']}'.")
        targets.append(target)
    return targets


def refresh_protected_release_receipts(
    *,
    root: Path | None = None,
    repo_ids: list[str] | None = None,
    mode: str = "promotion",
    provider: str | None = None,
    waiver_specs: list[dict[str, Any]] | None = None,
    max_receipt_age_hours: float = 168.0,
    enforce: bool = False,
    output_file: Path | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    targets = _resolve_release_targets(root=base_root, repo_ids=repo_ids)
    repo_results: list[dict[str, Any]] = []
    provider_value = (provider or "").strip()
    for target in targets:
        result = ci_gate(
            root=base_root,
            mode=mode,
            scenario=target["scenario_id"],
            adapter=target["adapter_id"],
            provider=provider_value or None,
            waiver_specs=list(waiver_specs or []),
            allow_missing_locked_repos=True,
            required_present_repo_ids=[target["repo_id"]],
        )
        promotion = result.get("promotion", {}) if isinstance(result.get("promotion"), dict) else {}
        repo_results.append(
            {
                "repo_id": target["repo_id"],
                "scenario_id": target["scenario_id"],
                "adapter_id": target["adapter_id"],
                "run_id": str(result.get("run_id") or ""),
                "promotion_status": str(promotion.get("promotion_status") or ""),
                "receipt_origin_type": str((promotion.get("receipt_origin") or {}).get("origin_type") or ""),
                "waiver_refs": list(result.get("waivers", [])) if isinstance(result.get("waivers"), list) else [],
            }
        )

    evidence_index = build_evidence_index(root=base_root)
    waiver_monitor = build_waiver_monitor(root=base_root)
    adoption_drift = build_adoption_drift(root=base_root, max_receipt_age_hours=max_receipt_age_hours)
    readiness = build_release_readiness(root=base_root, max_receipt_age_hours=max_receipt_age_hours)
    rehearsal = build_release_rehearsal(root=base_root, max_receipt_age_hours=max_receipt_age_hours)

    if enforce:
        readiness_payload = load_json_object(default_release_readiness_path(root=base_root))
        for target in targets:
            enforce_release_repo_readiness(
                payload=readiness_payload,
                repo_id=target["repo_id"],
                mode="release",
                max_receipt_age_hours=max_receipt_age_hours,
            )

    payload = {
        "contract_version": "atlas.qa.protected_release_refresh.v1",
        "generated_at": utc_now(),
        "mode": mode,
        "provider": provider_value or "none",
        "max_receipt_age_hours": max_receipt_age_hours,
        "enforced": enforce,
        "targets": targets,
        "repo_results": repo_results,
        "artifacts": {
            "evidence_index_ref": evidence_index["evidence_index_ref"],
            "waiver_monitor_ref": waiver_monitor["waiver_monitor_ref"],
            "adoption_drift_ref": adoption_drift["adoption_drift_ref"],
            "release_readiness_ref": readiness["release_readiness_ref"],
            "release_rehearsal_ref": rehearsal["release_rehearsal_ref"],
        },
    }
    target = output_file.resolve() if isinstance(output_file, Path) else default_protected_release_refresh_path(root=base_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, payload)
    md_path = target.with_suffix(".md")
    md_lines = [
        "# ATLAS Protected Release Refresh",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Mode: `{mode}`",
        f"- Provider: `{payload['provider']}`",
        f"- Enforced: `{enforce}`",
        f"- Max receipt age (hours): `{max_receipt_age_hours}`",
        "",
        "| Repo | Scenario | Adapter | Run | Status | Origin | Waivers |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in repo_results:
        md_lines.append(
            f"| {item['repo_id']} | {item['scenario_id']} | {item['adapter_id']} | {item['run_id'] or '-'} | {item['promotion_status'] or '-'} | {item['receipt_origin_type'] or '-'} | {', '.join(item.get('waiver_refs', [])) or '-'} |"
        )
    md_lines += [
        "",
        f"- Evidence index: `{payload['artifacts']['evidence_index_ref']}`",
        f"- Waiver monitor: `{payload['artifacts']['waiver_monitor_ref']}`",
        f"- Adoption drift: `{payload['artifacts']['adoption_drift_ref']}`",
        f"- Release readiness: `{payload['artifacts']['release_readiness_ref']}`",
        f"- Release rehearsal: `{payload['artifacts']['release_rehearsal_ref']}`",
    ]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return {
        "generated_at": payload["generated_at"],
        "protected_release_refresh_ref": atlas_relative(target, root=base_root),
        "protected_release_refresh_md_ref": atlas_relative(md_path, root=base_root),
        "repo_count": len(repo_results),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh trusted protected ATLAS release receipts for one repo or the release set.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--repo", action="append", default=[])
    parser.add_argument("--mode", choices=["evidence", "promotion"], default="promotion")
    parser.add_argument("--provider", default="none")
    parser.add_argument("--waiver-spec", action="append", default=[])
    parser.add_argument("--max-receipt-age-hours", type=float, default=168.0)
    parser.add_argument("--enforce", action="store_true")
    parser.add_argument("--output-file", type=Path)
    args = parser.parse_args(argv)
    waiver_specs: list[dict[str, Any]] = []
    for value in args.waiver_spec:
        payload = json.loads(value)
        if not isinstance(payload, dict):
            raise SystemExit("Each --waiver-spec value must be a JSON object.")
        waiver_specs.append(payload)
    result = refresh_protected_release_receipts(
        root=args.root.resolve(),
        repo_ids=[str(item).strip() for item in args.repo if str(item).strip()],
        mode=args.mode,
        provider=None if args.provider == "none" else args.provider,
        waiver_specs=waiver_specs,
        max_receipt_age_hours=args.max_receipt_age_hours,
        enforce=bool(args.enforce),
        output_file=args.output_file.resolve() if isinstance(args.output_file, Path) else None,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
