from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.qa._common import default_run_root, load_json_object, utc_now
from ops.atlas.qa.github_secret_readiness import (
    default_github_secret_readiness_path,
    github_secret_readiness,
)
from ops.atlas.qa.manual_attestation import (
    build_manual_attestation_packet_prep,
)
from ops.atlas.qa.provider_readiness import provider_readiness
from ops.cortex._artifacts import write_json


def build_release_gate_packet(
    *,
    root: Path | None = None,
    run_id: str,
    repo: str,
    provider_manifest_ref: str,
    adapter_id: str,
    scenario_id: str,
    required_secret_names: list[str],
    output_path: Path | None = None,
    token: str | None = None,
    secret_names_fetcher: Callable[[str, str], list[str]] | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    run_root = (default_run_root(root=base_root) / run_id).resolve()
    promotion_path = run_root / "promotion.record.json"
    promotion = load_json_object(promotion_path) if promotion_path.exists() else {}
    attestation_packet = build_manual_attestation_packet_prep(root=base_root, run_id=run_id)
    provider = provider_readiness(
        root=base_root,
        provider_manifest_ref=provider_manifest_ref,
        adapter_id=adapter_id,
        scenario_id=scenario_id,
    )

    secret_latest = default_github_secret_readiness_path(root=base_root)
    if secret_latest.exists():
        secret_payload = load_json_object(secret_latest)
        if (
            str(secret_payload.get("repo") or "") != repo
            or sorted(str(item) for item in secret_payload.get("required_secret_names", [])) != sorted(required_secret_names)
        ):
            secret_report = github_secret_readiness(
                root=base_root,
                repo=repo,
                required_secret_names=required_secret_names,
                token=token,
                secret_names_fetcher=secret_names_fetcher,
            )
            secret_payload = load_json_object(base_root / secret_report["github_secret_readiness_ref"])
    else:
        secret_report = github_secret_readiness(
            root=base_root,
            repo=repo,
            required_secret_names=required_secret_names,
            token=token,
            secret_names_fetcher=secret_names_fetcher,
        )
        secret_payload = load_json_object(base_root / secret_report["github_secret_readiness_ref"])

    manual_required_lanes = [
        str(item)
        for item in promotion.get("manual_required_lanes", [])
        if isinstance(item, str) and item.strip()
    ]
    output = (run_root / "release-gate.packet-prep.md") if output_path is None else output_path.resolve()

    lines = [
        "# ATLAS QA Release Gate Packet",
        "",
        f"- Generated: `{utc_now()}`",
        f"- Run: `{run_id}`",
        f"- Repo: `{repo}`",
        f"- Scenario: `{scenario_id}`",
        f"- Promotion status: `{promotion.get('promotion_status', 'unknown')}`",
        f"- Manual-required lanes: `{', '.join(manual_required_lanes) or 'none'}`",
        "",
        "## Manual Attestation",
        "",
        f"- Packet: `{attestation_packet['output_ref']}`",
        f"- Validation status: `{attestation_packet['validation_status']}`",
        f"- Manual-required lanes still open: `{', '.join(attestation_packet['manual_required_lanes']) or 'none'}`",
        "",
        "## Provider Readiness",
        "",
        f"- Provider manifest: `{provider_manifest_ref}`",
        f"- Requested physical lenses: `{', '.join(provider.get('requested_physical_lenses', [])) or 'none'}`",
        f"- Unsupported requested lenses: `{', '.join(provider.get('unsupported_requested_lenses', [])) or 'none'}`",
        f"- Missing local provider env vars: `{', '.join(provider.get('missing_env_vars', [])) or 'none'}`",
        f"- Live-smoke eligible on this machine: `{provider.get('live_smoke_eligible')}`",
        "",
        "## GitHub Secret Readiness",
        "",
        f"- Secret audit ref: `{atlas_relative(secret_latest, root=base_root)}`",
        f"- Repo status: `{secret_payload.get('status', 'unknown')}`",
        f"- Missing required secrets: `{', '.join(secret_payload.get('missing_required_secret_names', [])) or 'none'}`",
        "",
        "## Next Honest Move",
        "",
    ]

    if secret_payload.get("missing_required_secret_names"):
        lines.append(
            f"1. Restore GitHub Actions secrets: `{', '.join(secret_payload['missing_required_secret_names'])}`."
        )
        lines.append(
            "2. If protected credentials are restored first, rerun provider-backed release proof instead of manual mobile capture."
        )
    else:
        lines.append("1. Protected BrowserStack credentials appear ready; run the provider-backed protected smoke.")
    lines.append(
        f"3. If BrowserStack credentials remain unavailable, finish manual mobile proof via `{attestation_packet['output_ref']}`."
    )
    lines.append(
        f"4. Re-run promotion after either provider proof or valid manual capture: `python ops/atlas/qa/promote_run.py --root . --run {run_id} --scenario-file ops/atlas/qa/scenarios/{scenario_id}.json --stack-validation-file runtime/receipts/validation/stack-validation.latest.json`"
    )
    lines.append("")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    report = {
        "runner_version": "atlas.qa.release-gate-packet.v1",
        "generated_at": utc_now(),
        "run_id": run_id,
        "repo": repo,
        "scenario_id": scenario_id,
        "promotion_status": str(promotion.get("promotion_status") or "unknown"),
        "manual_required_lanes": manual_required_lanes,
        "manual_attestation_packet_ref": attestation_packet["output_ref"],
        "provider_live_smoke_eligible": bool(provider.get("live_smoke_eligible")),
        "missing_provider_env_vars": list(provider.get("missing_env_vars", [])),
        "github_secret_status": str(secret_payload.get("status") or "unknown"),
        "missing_required_secret_names": list(secret_payload.get("missing_required_secret_names", [])),
        "output_ref": atlas_relative(output, root=base_root),
    }
    write_json(run_root / "release-gate.packet-prep.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render one operator packet for an ATLAS QA release gate.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--run", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--require-secret",
        dest="required_secret_names",
        action="append",
        default=[],
        help="Required GitHub Actions secret name. Repeat for multiple names.",
    )
    args = parser.parse_args(argv)
    report = build_release_gate_packet(
        root=args.root.resolve(),
        run_id=args.run,
        repo=str(args.repo).strip(),
        provider_manifest_ref=str(args.provider).strip(),
        adapter_id=str(args.adapter).strip(),
        scenario_id=str(args.scenario).strip(),
        required_secret_names=[str(item).strip() for item in args.required_secret_names if str(item).strip()],
        output_path=args.output.resolve() if isinstance(args.output, Path) else None,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
