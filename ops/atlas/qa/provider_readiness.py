from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.qa._common import (
    load_adapter_manifest,
    load_json_object,
    load_provider_manifest,
    load_schema,
    resolve_ref,
    validate_provider_manifest,
    validate_schema_metadata,
)


def provider_readiness(
    *,
    root: Path | None = None,
    provider_manifest_ref: str,
    adapter_id: str | None = None,
    adapter_file: Path | None = None,
    scenario_id: str | None = None,
    scenario_file: Path | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    provider_payload, provider_path = load_provider_manifest(root=base_root, provider_manifest_ref=provider_manifest_ref)
    provider_schema = load_schema("atlas.qa.provider.v1", root=base_root)
    schema_errors = validate_schema_metadata(provider_schema, "atlas.qa.provider.v1")
    provider_errors = validate_provider_manifest(provider_payload)

    adapter_payload: dict[str, Any] = {}
    if isinstance(adapter_file, Path):
        adapter_payload = load_json_object(adapter_file.resolve())
    elif adapter_id:
        adapter_payload, _ = load_adapter_manifest(root=base_root, adapter_id=adapter_id)

    scenario_payload: dict[str, Any] = {}
    if isinstance(scenario_file, Path):
        scenario_payload = load_json_object(scenario_file.resolve())
    elif scenario_id:
        scenario_path = base_root / "ops" / "atlas" / "qa" / "scenarios" / f"{scenario_id}.json"
        if scenario_path.exists():
            scenario_payload = load_json_object(scenario_path)

    requested_physical_lenses = []
    if isinstance(scenario_payload.get("proof"), dict):
        requested_physical_lenses = [
            str(item)
            for item in scenario_payload["proof"].get("certify_lenses", [])
            if isinstance(item, str) and item.strip()
        ]
    elif isinstance(adapter_payload.get("lenses"), list):
        requested_physical_lenses = [
            str(item.get("lens_id"))
            for item in adapter_payload["lenses"]
            if isinstance(item, dict) and item.get("evidence_kind") == "physical_device"
        ]

    required_env = [
        key for key in provider_payload.get("auth_env_vars", [])
        if isinstance(key, str) and key.strip()
    ]
    supported_lenses = [
        str(item)
        for item in provider_payload.get("supported_lenses", [])
        if isinstance(item, str) and item.strip()
    ]
    unsupported_requested_lenses = [
        lens_id
        for lens_id in requested_physical_lenses
        if lens_id not in supported_lenses
    ]
    env_status = {
        key: ("present" if os.environ.get(key) else "missing")
        for key in required_env
    }
    missing_env = [key for key, status in env_status.items() if status == "missing"]
    live_smoke_eligible = (
        not schema_errors
        and not provider_errors
        and not missing_env
        and not unsupported_requested_lenses
        and bool(requested_physical_lenses)
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "provider_id": str(provider_payload.get("provider_id") or ""),
        "provider_manifest_ref": str(provider_manifest_ref),
        "provider_manifest_path": str(provider_path),
        "provider_config_status": "valid" if not schema_errors and not provider_errors else "invalid",
        "provider_schema_errors": schema_errors,
        "provider_manifest_errors": provider_errors,
        "requested_physical_lenses": requested_physical_lenses,
        "supported_lenses": supported_lenses,
        "unsupported_requested_lenses": unsupported_requested_lenses,
        "credentials": env_status,
        "missing_env_vars": missing_env,
        "live_smoke_eligible": live_smoke_eligible,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report whether a QA provider is ready for live smoke usage.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--provider", required=True)
    parser.add_argument("--adapter")
    parser.add_argument("--adapter-file", type=Path)
    parser.add_argument("--scenario")
    parser.add_argument("--scenario-file", type=Path)
    args = parser.parse_args(argv)
    report = provider_readiness(
        root=args.root.resolve(),
        provider_manifest_ref=args.provider,
        adapter_id=args.adapter,
        adapter_file=args.adapter_file.resolve() if isinstance(args.adapter_file, Path) else None,
        scenario_id=args.scenario,
        scenario_file=args.scenario_file.resolve() if isinstance(args.scenario_file, Path) else None,
    )
    print(json.dumps(report, indent=2))
    return 0 if report["live_smoke_eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
