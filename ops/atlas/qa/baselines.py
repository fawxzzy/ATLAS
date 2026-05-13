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
    VISUAL_BASELINE_CONTRACT_VERSION,
    baseline_manifest_path,
    default_run_root,
    load_json_object,
    payload_with_digest,
    resolve_ref,
    stamp_now,
    utc_now,
    validate_visual_baseline_payload,
    write_manifest,
)
from ops.cortex._artifacts import sha256_bytes

RUNNER_VERSION = "atlas.qa.baselines.v1"


def _proposal_dir(run_root: Path) -> Path:
    target = run_root / "baseline-proposals"
    target.mkdir(parents=True, exist_ok=True)
    return target


def propose_baselines(*, root: Path | None = None, run_id: str) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    run_root = (default_run_root(root=base_root) / run_id).resolve()
    evaluated = load_json_object(run_root / "evaluated.result.json")
    artifacts = load_json_object(run_root / "artifacts.manifest.json")
    scenario = load_json_object(resolve_ref(str(evaluated["scenario_ref"]), root=base_root))
    if evaluated.get("mode") == "dry_run":
        raise ValueError("Dry-run screenshots may not create proposed baselines.")
    proposal_dir = _proposal_dir(run_root)
    proposals: list[dict[str, Any]] = []
    visual_by_lens = {
        str(item.get("lens_id")): item
        for item in evaluated.get("visual_diffs", [])
        if isinstance(item, dict) and isinstance(item.get("lens_id"), str)
    }
    assertions = scenario.get("visual_assertions", []) if isinstance(scenario.get("visual_assertions"), list) else []
    screenshot_by_lens = {
        str(item.get("lens_id")): str(item.get("path_ref") or "")
        for item in artifacts.get("artifacts", [])
        if isinstance(item, dict) and item.get("artifact_kind") == "screenshot" and item.get("status") == "present"
    }
    for assertion in assertions:
        if not isinstance(assertion, dict):
            continue
        lens_id = str(assertion.get("lens_id") or "")
        diff = visual_by_lens.get(lens_id)
        candidate_ref = str((diff or {}).get("candidate_image_ref") or screenshot_by_lens.get(lens_id) or "")
        baseline_ref = str(assertion.get("baseline_ref") or "")
        if not candidate_ref or not baseline_ref:
            continue
        candidate_path = resolve_ref(candidate_ref, root=base_root)
        if not candidate_path.exists():
            continue
        baseline_path = resolve_ref(baseline_ref, root=base_root)
        proposal_body = {
            "contract_version": VISUAL_BASELINE_CONTRACT_VERSION,
            "generated_at": utc_now(),
            "runner_version": RUNNER_VERSION,
            "scenario_id": str(evaluated["scenario_ref"]).rsplit("/", 1)[-1].replace(".json", ""),
            "adapter_id": str(evaluated["adapter_id"]),
            "lens_id": lens_id,
            "evidence_tier": str(evaluated.get("summary", {}).get("highest_satisfied_tier") or "emulated_browser"),
            "source_run_id": run_id,
            "git_sha": str(evaluated["git_sha"]),
            "artifact_hash": sha256_bytes(candidate_path.read_bytes()),
            "state": "proposed",
            "baseline_ref": atlas_relative(baseline_path, root=base_root),
            "candidate_image_ref": candidate_ref,
            "approved_by": "",
            "approved_at": "",
        }
        proposal = payload_with_digest(proposal_body, "baseline_id")
        errors = validate_visual_baseline_payload(proposal)
        if errors:
            raise ValueError("; ".join(errors))
        proposal_path = proposal_dir / f"{lens_id}.baseline.json"
        write_manifest(proposal_path, proposal)
        proposals.append(
            {
                "lens_id": lens_id,
                "proposal_ref": atlas_relative(proposal_path, root=base_root),
                "baseline_ref": atlas_relative(baseline_path, root=base_root),
            }
        )
    return {
        "generated_at": utc_now(),
        "run_id": run_id,
        "proposal_count": len(proposals),
        "proposals": proposals,
    }


def bless_baseline(*, root: Path | None = None, run_id: str, lens_id: str, approved_by: str) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    run_root = (default_run_root(root=base_root) / run_id).resolve()
    evaluated = load_json_object(run_root / "evaluated.result.json")
    if evaluated.get("mode") == "dry_run":
        raise ValueError("Dry-run screenshots may not be blessed as baselines.")
    proposal_path = _proposal_dir(run_root) / f"{lens_id}.baseline.json"
    proposal = load_json_object(proposal_path)
    errors = validate_visual_baseline_payload(proposal)
    if errors:
        raise ValueError("; ".join(errors))
    candidate_path = resolve_ref(str(proposal["candidate_image_ref"]), root=base_root)
    baseline_path = resolve_ref(str(proposal["baseline_ref"]), root=base_root)
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    existing_manifest_path = baseline_manifest_path(baseline_path)
    superseded_ref = ""
    if baseline_path.exists() and existing_manifest_path.exists():
        existing_manifest = load_json_object(existing_manifest_path)
        existing_hash = str(existing_manifest.get("artifact_hash") or "")
        candidate_hash = sha256_bytes(candidate_path.read_bytes())
        if existing_hash and existing_hash != candidate_hash:
            superseded_manifest = dict(existing_manifest)
            superseded_manifest["state"] = "superseded"
            archive_path = baseline_path.parent / f"{lens_id}.superseded.{stamp_now()}.baseline.json"
            write_manifest(archive_path, superseded_manifest)
            superseded_ref = atlas_relative(archive_path, root=base_root)
    shutil.copyfile(candidate_path, baseline_path)
    blessed_body = {
        **proposal,
        "state": "blessed",
        "approved_by": approved_by,
        "approved_at": utc_now(),
        "artifact_hash": sha256_bytes(candidate_path.read_bytes()),
    }
    blessed = payload_with_digest({key: value for key, value in blessed_body.items() if key != "baseline_id"}, "baseline_id")
    errors = validate_visual_baseline_payload(blessed)
    if errors:
        raise ValueError("; ".join(errors))
    write_manifest(existing_manifest_path, blessed)
    return {
        "run_id": run_id,
        "lens_id": lens_id,
        "baseline_ref": atlas_relative(baseline_path, root=base_root),
        "baseline_manifest_ref": atlas_relative(existing_manifest_path, root=base_root),
        "superseded_manifest_ref": superseded_ref,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Propose or bless governed ATLAS QA visual baselines.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    propose_parser = subparsers.add_parser("propose")
    propose_parser.add_argument("--root", type=Path, default=atlas_root())
    propose_parser.add_argument("--run", required=True)

    bless_parser = subparsers.add_parser("bless")
    bless_parser.add_argument("--root", type=Path, default=atlas_root())
    bless_parser.add_argument("--run", required=True)
    bless_parser.add_argument("--lens", required=True)
    bless_parser.add_argument("--approved-by", required=True)

    args = parser.parse_args(argv)
    if args.command == "propose":
        result = propose_baselines(root=args.root.resolve(), run_id=args.run)
    else:
        result = bless_baseline(
            root=args.root.resolve(),
            run_id=args.run,
            lens_id=args.lens,
            approved_by=args.approved_by,
        )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
