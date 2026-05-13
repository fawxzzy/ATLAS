from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.qa._common import (
    SCHEMA_IDS,
    compatibility_summary,
    default_scenario_dir,
    load_adapter_manifest,
    load_json_object,
    load_schema,
    validate_adapter_manifest,
    validate_scenario_manifest,
    validate_schema_metadata,
)


def compatibility_report(
    *,
    root: Path,
    adapter: str | None = None,
    scenario: str | None = None,
) -> dict[str, object]:
    adapter_payload = None
    scenario_payload = None
    findings: list[dict[str, object]] = []
    if scenario:
        scenario_path = (default_scenario_dir(root=root) / f"{scenario}.json").resolve()
        scenario_payload = load_json_object(scenario_path)
        for message in validate_scenario_manifest(
            scenario_payload,
            root=root,
            require_repo_path_exists=False,
        ):
            findings.append({"severity": "error", "scope": "scenario", "message": message})
    if adapter or (scenario_payload and isinstance(scenario_payload.get("repo_id"), str)):
        adapter_payload, _ = load_adapter_manifest(
            root=root,
            adapter_id=adapter or (str(scenario_payload["adapter_id"]) if scenario_payload else None),
            repo_id=(str(scenario_payload["repo_id"]) if scenario_payload else None),
        )
        for message in validate_adapter_manifest(
            adapter_payload,
            root=root,
            require_repo_path_exists=False,
        ):
            findings.append({"severity": "error", "scope": "adapter", "message": message})
    schemas: dict[str, dict[str, object]] = {}
    for contract_version in sorted(SCHEMA_IDS):
        schema = load_schema(contract_version, root=root)
        schemas[contract_version] = {
            "path": f"schemas/{contract_version}.json",
            "ok": not bool(validate_schema_metadata(schema, contract_version)),
        }
    summary = compatibility_summary(adapter_payload=adapter_payload, scenario_payload=scenario_payload)
    return {
        **summary,
        "schemas": schemas,
        "status": "compatible" if not findings else "incompatible",
        "finding_count": len(findings),
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report ATLAS QA LLEL v1 compatibility for root contracts and adapters.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--adapter")
    parser.add_argument("--scenario")
    args = parser.parse_args(argv)

    result = compatibility_report(
        root=args.root.resolve(),
        adapter=args.adapter,
        scenario=args.scenario,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "compatible" else 1


if __name__ == "__main__":
    raise SystemExit(main())
