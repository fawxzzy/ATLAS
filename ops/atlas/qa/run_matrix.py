from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes
from ops.atlas.qa._common import (
    RESULT_CONTRACT_VERSION,
    PROOF_KINDS,
    build_receipt_origin,
    default_run_root,
    default_scenario_dir,
    load_adapter_manifest,
    load_json_object,
    load_lens_manifest,
    load_schema,
    payload_with_digest,
    resolve_ref,
    stamp_now,
    utc_now,
    validate_adapter_manifest,
    validate_result_payload,
    validate_scenario_manifest,
    validate_schema_metadata,
    write_manifest,
)

RUNNER_VERSION = "atlas.qa.run-matrix.v2"


def _scenario_path(root: Path, scenario_file: Path | None, scenario_id: str | None) -> Path:
    if scenario_file is not None:
        return scenario_file.resolve()
    if not scenario_id:
        raise ValueError("Provide --scenario-file or --scenario-id.")
    return (default_scenario_dir(root=root) / f"{scenario_id}.json").resolve()


def _run_command(command: str, *, cwd: Path) -> tuple[int, float]:
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=str(cwd), shell=True, check=False)
    elapsed = (time.perf_counter() - started) * 1000
    return completed.returncode, elapsed


def _git_sha(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 and completed.stdout.strip() else "unknown"


def _lens_index(adapter: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in adapter.get("lenses", []):
        if isinstance(item, dict) and isinstance(item.get("lens_id"), str):
            result[str(item["lens_id"])] = item
    return result


def run_matrix(
    *,
    root: Path | None = None,
    scenario_path: Path | None = None,
    scenario_id: str | None = None,
    adapter_id: str | None = None,
    adapter_dir: Path | None = None,
    output_root: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    scenario_target = _scenario_path(base_root, scenario_path, scenario_id)
    scenario_schema = load_schema("atlas.qa.scenario.v1", root=base_root)
    schema_errors = validate_schema_metadata(scenario_schema, "atlas.qa.scenario.v1")
    if schema_errors:
        raise ValueError("; ".join(schema_errors))

    scenario = load_json_object(scenario_target)
    scenario_errors = validate_scenario_manifest(
        scenario,
        root=base_root,
        require_repo_path_exists=not dry_run,
    )
    if scenario_errors:
        raise ValueError("; ".join(scenario_errors))

    adapter, adapter_path = load_adapter_manifest(
        root=base_root,
        adapter_id=adapter_id or str(scenario["adapter_id"]),
        repo_id=str(scenario["repo_id"]),
        adapter_dir=adapter_dir.resolve() if isinstance(adapter_dir, Path) else None,
    )
    adapter_errors = validate_adapter_manifest(
        adapter,
        root=base_root,
        require_repo_path_exists=not dry_run,
    )
    if adapter_errors:
        raise ValueError("; ".join(adapter_errors))

    repo_root = resolve_ref(str(adapter["repo_path"]), root=base_root)
    git_sha = _git_sha(repo_root)
    run_id = f"{str(scenario['scenario_id']).replace('.', '-')}-{stamp_now()}"
    run_root = ((output_root or default_run_root(root=base_root)).resolve() / run_id).resolve()
    lens_index = _lens_index(adapter)
    lens_manifest, lens_manifest_path = load_lens_manifest(root=base_root, lens_manifest_ref=str(scenario["proof"]["lens_manifest_ref"]))
    lens_profiles = {
        str(item["lens_id"]): item
        for item in lens_manifest.get("lenses", [])
        if isinstance(item, dict) and isinstance(item.get("lens_id"), str)
    }
    matrix: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []

    preflight_commands = scenario.get("execution", {}).get("preflight_command_sequence", [])
    if not isinstance(preflight_commands, list):
        preflight_commands = []
    command_cache: dict[str, tuple[int, float]] = {}

    command_failures = False
    if not dry_run:
        for command_ref in preflight_commands:
            command_def = adapter.get("commands", {}).get(command_ref)
            if not isinstance(command_def, dict) or not isinstance(command_def.get("command"), str):
                findings.append(
                    {
                        "severity": "error",
                        "code": "missing_preflight_command",
                        "message": f"Adapter is missing preflight command '{command_ref}'.",
                    }
                )
                command_failures = True
                continue
            exit_code, duration_ms = _run_command(str(command_def["command"]), cwd=repo_root)
            if exit_code != 0:
                findings.append(
                    {
                        "severity": "error",
                        "code": "preflight_failed",
                        "message": f"Preflight command '{command_ref}' failed with exit code {exit_code}.",
                    }
                )
                command_failures = True

    lane_specs: list[tuple[str, str, list[str]]] = [
        ("pr", "emulated", list(scenario["proof"]["pr_lenses"])),
        ("certify", "real", list(scenario["proof"]["certify_lenses"])),
    ]
    for lane_name, proof_kind, lens_ids in lane_specs:
        command_refs = scenario["execution"]["pr_command_sequence"] if lane_name == "pr" else scenario["execution"]["certify_command_sequence"]
        for lens_id in lens_ids:
            lens = lens_index.get(lens_id)
            if not isinstance(lens, dict):
                findings.append(
                    {
                        "severity": "error",
                        "code": "missing_lens",
                        "message": f"Adapter does not declare lens '{lens_id}'.",
                        "lens_id": lens_id,
                    }
                )
                matrix.append(
                    {
                        "lens_id": lens_id,
                        "proof_kind": proof_kind,
                        "execution_mode": "repo_command",
                        "status": "fail" if not dry_run else "planned",
                    }
                )
                continue

            execution_mode = str(lens["execution_mode"])
            provider_hint = lens.get("provider_hint")
            command_ref = lens.get("command_ref")
            profile_id = str(lens.get("profile_id") or "")
            profile = lens_profiles.get(profile_id, {})
            command_value = None
            if execution_mode in {"repo_command", "browser_capture", "provider_capture"}:
                selected_ref = str(command_ref or command_refs[-1] if command_refs else "")
                command_def = adapter.get("commands", {}).get(selected_ref)
                if isinstance(command_def, dict):
                    command_value = str(command_def["command"])
                else:
                    findings.append(
                        {
                            "severity": "error",
                            "code": "missing_command_ref",
                            "message": f"Adapter command '{selected_ref}' is not defined for lens '{lens_id}'.",
                            "lens_id": lens_id,
                        }
                    )
            status = "planned" if dry_run else "not_run"
            exit_code = None
            duration_ms = None
            if not dry_run:
                if command_failures:
                    status = "skipped"
                elif execution_mode == "manual_external":
                    status = "manual_required"
                elif command_value:
                    if command_value in command_cache:
                        exit_code, duration_ms = command_cache[command_value]
                    else:
                        exit_code, duration_ms = _run_command(command_value, cwd=repo_root)
                        command_cache[command_value] = (exit_code, duration_ms)
                    status = "pass" if exit_code == 0 else "fail"
                    if exit_code != 0:
                        findings.append(
                            {
                                "severity": "error",
                                "code": "command_failed",
                                "message": f"Command '{command_ref or lens.get('command_ref')}' failed with exit code {exit_code}.",
                                "lens_id": lens_id,
                            }
                        )
                else:
                    status = "fail"
            matrix_entry = {
                "lens_id": lens_id,
                "lens_profile_id": profile_id,
                "proof_kind": proof_kind if proof_kind in PROOF_KINDS else str(lens["proof_kind"]),
                "evidence_kind": str(lens.get("evidence_kind") or ("physical_device" if proof_kind == "real" else "emulated_browser")),
                "promotion_tier": str(lens.get("promotion_tier") or ("physical_device" if proof_kind == "real" else "emulated_browser")),
                "fallback_behavior": str(lens.get("fallback_behavior") or ("manual_review" if proof_kind == "real" else "blocked")),
                "execution_mode": execution_mode,
                "status": status,
                "url_target": str(lens.get("url_target") or adapter.get("start", {}).get("default_url") or ""),
                "git_sha": git_sha,
            }
            if command_ref:
                matrix_entry["command_ref"] = str(command_ref)
            if command_value:
                matrix_entry["command"] = command_value
            if provider_hint:
                matrix_entry["provider_hint"] = str(provider_hint)
            if isinstance(lens.get("required_for"), list):
                matrix_entry["required_for"] = list(lens["required_for"])
            if isinstance(lens.get("provider_manifest_ref"), str):
                matrix_entry["provider_manifest_ref"] = str(lens["provider_manifest_ref"])
            if isinstance(profile, dict):
                matrix_entry["browser_engine"] = str(profile.get("browser_engine") or "")
                viewport = profile.get("viewport")
                if isinstance(viewport, dict):
                    matrix_entry["viewport"] = viewport
            if isinstance(exit_code, int):
                matrix_entry["exit_code"] = exit_code
            if isinstance(duration_ms, float):
                matrix_entry["duration_ms"] = int(round(duration_ms))
            matrix.append(matrix_entry)

    failing_lens_count = sum(1 for item in matrix if item["status"] == "fail")
    dry = dry_run
    overall_status = "dry_run" if dry else ("blocked" if failing_lens_count or any(f["severity"] == "error" for f in findings) else "ready")
    executable_status = "planned" if dry else ("failed" if failing_lens_count or command_failures else "clean")
    body = {
        "contract_version": RESULT_CONTRACT_VERSION,
        "generated_at": utc_now(),
        "runner_version": RUNNER_VERSION,
        "stage": "planned" if dry else "executed",
        "run_id": run_id,
        "scenario_ref": atlas_relative(scenario_target, root=base_root),
        "repo_id": str(scenario["repo_id"]),
        "repo_path": normalize_slashes(str(scenario["repo_path"])),
        "git_sha": git_sha,
        "adapter_id": str(adapter["adapter_id"]),
        "adapter_ref": atlas_relative(adapter_path, root=base_root),
        "lens_manifest_ref": atlas_relative(lens_manifest_path, root=base_root),
        "mode": "dry_run" if dry else "execute",
        "summary": {
            "overall_status": overall_status,
            "executable_status": executable_status,
            "artifact_status": "planned" if dry else "not_collected",
            "certification_status": "planned" if dry else ("manual_required" if any(item["status"] == "manual_required" for item in matrix) else "missing"),
            "lens_count": len(matrix),
            "failing_lens_count": failing_lens_count,
            "finding_count": len(findings),
        },
        "matrix": matrix,
        "findings": findings,
        "artifact_manifest_refs": [],
        "receipt_origin": build_receipt_origin(
            root=base_root,
            runner_version=RUNNER_VERSION,
            repo_id=str(scenario["repo_id"]),
            git_sha=git_sha,
            command="python ops/atlas/qa/run_matrix.py",
        ),
    }
    result = payload_with_digest(body, "result_id")
    payload_errors = validate_result_payload(result)
    if payload_errors:
        raise ValueError("; ".join(payload_errors))
    run_root.mkdir(parents=True, exist_ok=True)
    output_path = run_root / "matrix.result.json"
    write_manifest(output_path, result)
    return result | {"output_root": atlas_relative(run_root, root=base_root), "output_ref": atlas_relative(output_path, root=base_root)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan or execute an ATLAS QA scenario matrix.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--scenario-file", type=Path)
    parser.add_argument("--scenario-id")
    parser.add_argument("--scenario")
    parser.add_argument("--adapter")
    parser.add_argument("--adapter-dir", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    result = run_matrix(
        root=args.root.resolve(),
        scenario_path=args.scenario_file.resolve() if isinstance(args.scenario_file, Path) else None,
        scenario_id=args.scenario or args.scenario_id,
        adapter_id=args.adapter,
        adapter_dir=args.adapter_dir.resolve() if isinstance(args.adapter_dir, Path) else None,
        output_root=args.output_root.resolve() if isinstance(args.output_root, Path) else None,
        dry_run=bool(args.dry_run),
    )
    print(json.dumps(result, indent=2))
    return 0 if result["summary"]["overall_status"] in {"dry_run", "ready"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
