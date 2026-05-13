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
from ops.atlas.qa._common import default_run_root, load_json_object, utc_now, validate_waiver_payload
from ops.cortex._artifacts import write_json


def _parse_utc(value: str) -> datetime | None:
    if not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def build_waiver_monitor(
    *,
    root: Path | None = None,
    output_file: Path | None = None,
    expiring_within_days: float = 7.0,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    run_root = default_run_root(root=base_root)
    entries: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    for waiver_path in sorted(run_root.glob("*/waivers/*.json")):
        rel = atlas_relative(waiver_path, root=base_root)
        try:
            payload = load_json_object(waiver_path)
        except Exception as exc:
            entries.append(
                {
                    "waiver_ref": rel,
                    "status": "invalid",
                    "findings": [f"Waiver file could not be loaded: {exc}"],
                }
            )
            continue
        findings = validate_waiver_payload(payload)
        expires_at_raw = str(payload.get("expires_at") or "")
        expires_at = _parse_utc(expires_at_raw)
        days_until_expiry = None
        status = "active"
        if expires_at is None:
            findings.append("expires_at is missing or invalid.")
            status = "invalid"
        else:
            days_until_expiry = round((expires_at - now).total_seconds() / 86400, 3)
            if days_until_expiry < 0:
                status = "expired"
            elif days_until_expiry <= expiring_within_days:
                status = "expiring_soon"
        if findings and status not in {"expired", "expiring_soon"}:
            status = "invalid"
        entries.append(
            {
                "waiver_ref": rel,
                "waiver_id": str(payload.get("waiver_id") or ""),
                "repo_id": str(payload.get("repo_id") or ""),
                "scenario_id": str(payload.get("scenario_id") or ""),
                "run_id": str(payload.get("run_id") or ""),
                "waived_lane": str(payload.get("waived_lane") or ""),
                "operator": str(payload.get("operator") or ""),
                "created_at": str(payload.get("created_at") or ""),
                "expires_at": expires_at_raw,
                "days_until_expiry": days_until_expiry,
                "reason": str(payload.get("reason") or ""),
                "limitation": str(payload.get("limitation") or ""),
                "evidence_present": list(payload.get("evidence_present", [])) if isinstance(payload.get("evidence_present"), list) else [],
                "status": status,
                "findings": findings,
            }
        )
    payload = {
        "contract_version": "atlas.qa.waiver_monitor.v1",
        "generated_at": utc_now(),
        "expiring_within_days": expiring_within_days,
        "waivers": entries,
        "summary": {
            "waiver_count": len(entries),
            "active_count": sum(1 for item in entries if item.get("status") == "active"),
            "expiring_soon_count": sum(1 for item in entries if item.get("status") == "expiring_soon"),
            "expired_count": sum(1 for item in entries if item.get("status") == "expired"),
            "invalid_count": sum(1 for item in entries if item.get("status") == "invalid"),
        },
    }
    target = output_file.resolve() if isinstance(output_file, Path) else (base_root / "runtime" / "atlas" / "qa" / "waiver-monitor.latest.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, payload)
    md_path = target.with_suffix(".md")
    md_lines = [
        "# ATLAS QA Waiver Monitor",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Waivers: `{payload['summary']['waiver_count']}`",
        f"- Active: `{payload['summary']['active_count']}`",
        f"- Expiring soon: `{payload['summary']['expiring_soon_count']}`",
        f"- Expired: `{payload['summary']['expired_count']}`",
        f"- Invalid: `{payload['summary']['invalid_count']}`",
        "",
        "| Repo | Run | Lane | Status | Expires | Days | Reason |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in entries:
        md_lines.append(
            f"| {item.get('repo_id') or '-'} | {item.get('run_id') or '-'} | {item.get('waived_lane') or '-'} | {item.get('status') or '-'} | {item.get('expires_at') or '-'} | {item.get('days_until_expiry') if item.get('days_until_expiry') is not None else '-'} | {item.get('reason') or '-'} |"
        )
        for finding in item.get("findings", []):
            md_lines.append(f"|  |  |  |  |  | finding: {finding} |  |")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return {
        "generated_at": payload["generated_at"],
        "waiver_monitor_ref": atlas_relative(target, root=base_root),
        "waiver_monitor_md_ref": atlas_relative(md_path, root=base_root),
        "waiver_count": payload["summary"]["waiver_count"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report active and expiring ATLAS QA waivers.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--output-file", type=Path)
    parser.add_argument("--expiring-within-days", type=float, default=7.0)
    args = parser.parse_args(argv)
    result = build_waiver_monitor(
        root=args.root.resolve(),
        output_file=args.output_file.resolve() if isinstance(args.output_file, Path) else None,
        expiring_within_days=args.expiring_within_days,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
