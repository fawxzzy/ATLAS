from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.qa._common import (
    default_run_waiver_dir,
    default_scenario_dir,
    load_adapter_manifest,
    load_json_object,
    utc_now,
    validate_adapter_manifest,
    validate_scenario_manifest,
    validate_waiver_payload,
)
from ops.atlas.qa.providers.base import load_provider_config
from ops.atlas.qa.collect_artifacts import collect_artifacts
from ops.atlas.qa.evidence_index import build_evidence_index
from ops.atlas.qa.evaluate_run import evaluate_run
from ops.atlas.qa.promote_run import promote_run
from ops.atlas.qa.report_run import report_run
from ops.atlas.qa.run_matrix import run_matrix
from ops.atlas.qa.test_evidence import collect_test_evidence
from ops.atlas.qa.validate_artifacts import validate_artifact_manifest_file
from ops.cortex._artifacts import write_json


def _stack_validation(root: Path) -> Path:
    completed = subprocess.run(
        ["python", "ops/validation/validate_stack.py"],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    report_path = root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json"
    if not report_path.exists():
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "validate_stack.py did not produce a report.")
    return report_path


def _wait_for_url(url: str, *, timeout_s: int = 90) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                if 200 <= int(response.status) < 500:
                    return
        except (urllib.error.URLError, TimeoutError, ValueError):
            pass
        time.sleep(1.0)
    raise RuntimeError(f"Timed out waiting for ready URL: {url}")


def _run_adapter_prepare(root: Path, adapter_payload: dict[str, object]) -> dict[str, object] | None:
    prepare = adapter_payload.get("prepare") if isinstance(adapter_payload.get("prepare"), dict) else {}
    if not isinstance(prepare, dict) or prepare.get("kind") not in {None, "command"}:
        return None
    command = prepare.get("command")
    if not isinstance(command, str) or not command.strip():
        return None
    repo_root = root / str(adapter_payload["repo_path"])
    completed = subprocess.run(
        command,
        cwd=str(repo_root),
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "adapter prepare failed").strip()
        raise RuntimeError(detail)
    return {"command": command, "cwd": str(repo_root)}


def _start_adapter_server(root: Path, adapter_payload: dict[str, object]) -> subprocess.Popen[str] | None:
    start = adapter_payload.get("start") if isinstance(adapter_payload.get("start"), dict) else {}
    if not isinstance(start, dict) or start.get("kind") != "command":
        return None
    command = start.get("command")
    default_url = str(start.get("default_url") or "")
    ready_path = str(start.get("ready_path") or "")
    if not isinstance(command, str) or not command.strip():
        return None
    repo_root = root / str(adapter_payload["repo_path"])
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    process = subprocess.Popen(
        command,
        cwd=str(repo_root),
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        creationflags=creationflags,
    )
    if default_url:
        ready_url = f"{default_url.rstrip('/')}/{ready_path.lstrip('/')}" if ready_path else default_url
        _wait_for_url(ready_url)
    return process


def _stop_adapter_server(process: subprocess.Popen[str] | None) -> None:
    if process is None:
        return
    if process.poll() is not None:
        return
    try:
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        process.terminate()


def _load_scenario(
    *,
    root: Path,
    scenario: str | None,
    scenario_file: Path | None,
) -> tuple[dict[str, object], Path]:
    if isinstance(scenario_file, Path):
        path = scenario_file.resolve()
    else:
        if not scenario:
            raise RuntimeError("Provide --scenario or --scenario-file.")
        path = (default_scenario_dir(root=root) / f"{scenario}.json").resolve()
    payload = load_json_object(path)
    return payload, path


def _load_adapter(
    *,
    root: Path,
    adapter: str | None,
    adapter_file: Path | None,
    scenario_payload: dict[str, object],
) -> tuple[dict[str, object], Path]:
    if isinstance(adapter_file, Path):
        path = adapter_file.resolve()
        payload = load_json_object(path)
        return payload, path
    payload, path = load_adapter_manifest(
        root=root,
        adapter_id=adapter or str(scenario_payload["adapter_id"]),
        repo_id=str(scenario_payload["repo_id"]),
    )
    return payload, path


def _provider_override_file(
    *,
    root: Path,
    adapter_payload: dict[str, object],
    adapter_path: Path,
    provider: str | None,
) -> tuple[Path, tempfile.TemporaryDirectory[str]] | tuple[None, None]:
    if not provider:
        return None, None
    override_payload = json.loads(json.dumps(adapter_payload))
    fallback_command_ref = ""
    for item in override_payload.get("lenses", []):
        if not isinstance(item, dict):
            continue
        command_ref = item.get("command_ref")
        if isinstance(command_ref, str) and command_ref.strip():
            fallback_command_ref = command_ref
            break
    mutated = False
    for item in override_payload.get("lenses", []):
        if not isinstance(item, dict) or item.get("proof_kind") != "real":
            continue
        item["execution_mode"] = "provider_capture"
        item["provider_manifest_ref"] = f"ops/atlas/qa/providers/{provider}.json" if not provider.endswith(".json") else provider
        if fallback_command_ref and (not isinstance(item.get("command_ref"), str) or not str(item.get("command_ref")).strip()):
            item["command_ref"] = fallback_command_ref
        mutated = True
    if not mutated:
        return None, None
    temp_dir = tempfile.TemporaryDirectory(prefix="atlas-qa-adapter-override-")
    override_dir = Path(temp_dir.name)
    override_path = override_dir / adapter_path.name
    override_path.write_text(json.dumps(override_payload, indent=2) + "\n", encoding="utf-8")
    return override_path, temp_dir


def _provider_status(*, root: Path, provider: str | None) -> dict[str, object]:
    if not provider:
        return {"requested": False, "status": "not_requested"}
    provider_ref = f"ops/atlas/qa/providers/{provider}.json" if not provider.endswith(".json") else provider
    payload, _ = load_provider_config(root=root, provider_manifest_ref=provider_ref)
    missing = []
    for key in payload.get("auth_env_vars", []):
        if isinstance(key, str) and key.strip() and not str(__import__("os").environ.get(key, "")).strip():
            missing.append(key)
    if missing:
        return {
            "requested": True,
            "status": "provider_unavailable",
            "provider_ref": provider_ref,
            "missing_env_vars": missing,
        }
    return {
        "requested": True,
        "status": "ready",
        "provider_ref": provider_ref,
        "missing_env_vars": [],
    }


def _parse_waiver_specs(values: list[str], *, root: Path) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for value in values:
        candidate = Path(value)
        if candidate.exists():
            payload = load_json_object(candidate.resolve())
        else:
            try:
                payload = json.loads(value)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Waiver spec must be valid JSON or an existing file path: {exc}") from exc
            if not isinstance(payload, dict):
                raise RuntimeError("Waiver spec JSON must deserialize to an object.")
        specs.append(payload)
    return specs


def _materialize_runtime_waivers(
    *,
    root: Path,
    run_id: str,
    repo_id: str,
    scenario_id: str,
    waiver_specs: list[dict[str, Any]],
) -> list[str]:
    if not waiver_specs:
        return []
    actor = (
        str(os.environ.get("GITHUB_ACTOR", "")).strip()
        or str(os.environ.get("USERNAME", "")).strip()
        or str(os.environ.get("USER", "")).strip()
        or "unknown"
    )
    operator_identity = (
        f"github:{actor}"
        if str(os.environ.get("GITHUB_ACTIONS", "")).lower() == "true"
        else f"local:{actor}"
    )
    waiver_dir = default_run_waiver_dir(root=root, run_id=run_id)
    waiver_dir.mkdir(parents=True, exist_ok=True)
    created_refs: list[str] = []
    for spec in waiver_specs:
        spec_repo_id = str(spec.get("repo_id") or "").strip()
        spec_scenario_id = str(spec.get("scenario_id") or "").strip()
        if spec_repo_id and spec_repo_id != repo_id:
            continue
        if spec_scenario_id and spec_scenario_id != scenario_id:
            continue
        waived_lane = str(spec.get("waived_lane") or "").strip()
        if not waived_lane:
            raise RuntimeError("Waiver spec must include waived_lane.")
        payload = {
            "contract_version": "atlas.qa.waiver.v1",
            "waiver_id": f"{run_id}:{waived_lane}:waiver",
            "repo_id": repo_id,
            "scenario_id": scenario_id,
            "run_id": run_id,
            "waived_lane": waived_lane,
            "reason": str(spec.get("reason") or "").strip(),
            "operator": str(spec.get("operator") or actor).strip(),
            "operator_identity": str(spec.get("operator_identity") or operator_identity).strip(),
            "created_at": utc_now(),
            "expires_at": str(spec.get("expires_at") or "").strip(),
            "evidence_present": [
                str(item).strip()
                for item in spec.get("evidence_present", [])
                if isinstance(item, str) and str(item).strip()
            ],
            "limitation": str(spec.get("limitation") or "").strip(),
            "notes": [
                str(item).strip()
                for item in spec.get("notes", [])
                if isinstance(item, str) and str(item).strip()
            ],
        }
        errors = validate_waiver_payload(payload)
        if errors:
            raise RuntimeError("; ".join(errors))
        target = waiver_dir / f"{waived_lane}.waiver.json"
        write_json(target, payload)
        created_refs.append(str(target))
    return created_refs


def ci_gate(
    *,
    root: Path | None = None,
    mode: str,
    scenario: str | None = None,
    adapter: str | None = None,
    scenario_file: Path | None = None,
    adapter_file: Path | None = None,
    provider: str | None = None,
    attestation_files: list[str] | None = None,
    waiver_specs: list[dict[str, Any]] | None = None,
) -> dict[str, object]:
    base_root = (root or atlas_root()).resolve()
    scenario_payload, scenario_path = _load_scenario(root=base_root, scenario=scenario, scenario_file=scenario_file)
    scenario_errors = validate_scenario_manifest(scenario_payload, root=base_root)
    if scenario_errors:
        raise RuntimeError("; ".join(scenario_errors))
    adapter_payload, adapter_path = _load_adapter(
        root=base_root,
        adapter=adapter,
        adapter_file=adapter_file,
        scenario_payload=scenario_payload,
    )
    adapter_errors = validate_adapter_manifest(adapter_payload, root=base_root)
    if adapter_errors:
        raise RuntimeError("; ".join(adapter_errors))
    provider_status = _provider_status(root=base_root, provider=provider)
    override_path, override_handle = _provider_override_file(
        root=base_root,
        adapter_payload=adapter_payload,
        adapter_path=adapter_path,
        provider=provider if provider_status["status"] == "ready" else None,
    )
    if isinstance(override_path, Path):
        adapter_payload = load_json_object(override_path)
        adapter_path = override_path
        adapter_errors = validate_adapter_manifest(adapter_payload, root=base_root)
        if adapter_errors:
            raise RuntimeError("; ".join(adapter_errors))

    dry_run = mode == "dry-run"
    server_process: subprocess.Popen[str] | None = None
    prepare_result: dict[str, object] | None = None
    run_id = ""
    result: dict[str, object] = {}
    artifact_report: dict[str, object] = {}
    test_evidence: dict[str, object] = {}
    evaluated: dict[str, object] = {}
    promotion: dict[str, object] = {}
    report: dict[str, object] = {}
    evidence_index: dict[str, object] = {}
    stack_validation_path: Path | None = None
    materialized_waivers: list[str] = []
    try:
        if not dry_run:
            prepare_result = _run_adapter_prepare(base_root, adapter_payload)
            server_process = _start_adapter_server(base_root, adapter_payload)
        result = run_matrix(
            root=base_root,
            scenario_path=scenario_path,
            scenario_id=scenario,
            adapter_id=str(adapter_payload["adapter_id"]),
            adapter_dir=adapter_path.parent,
            dry_run=dry_run,
        )
        run_id = str(result["run_id"])
        test_evidence = collect_test_evidence(root=base_root, run_id=run_id)
        collect_artifacts(root=base_root, run_id=run_id, dry_run=dry_run, attestation_files=list(attestation_files or []))
        artifact_path = base_root / "runtime" / "atlas" / "qa" / "runs" / run_id / "artifacts.manifest.json"
        artifact_report = validate_artifact_manifest_file(
            root=base_root,
            artifact_path=artifact_path,
            promotion_strict=mode == "promotion",
        )
        (artifact_path.parent / "artifact.validation.json").write_text(json.dumps(artifact_report, indent=2) + "\n", encoding="utf-8")
        evaluated = evaluate_run(root=base_root, run_id=run_id)
        materialized_waivers = _materialize_runtime_waivers(
            root=base_root,
            run_id=run_id,
            repo_id=str(scenario_payload["repo_id"]),
            scenario_id=str(scenario_payload["scenario_id"]),
            waiver_specs=list(waiver_specs or []),
        )
        stack_validation_path = _stack_validation(base_root) if mode == "promotion" else None
        promotion = promote_run(
            root=base_root,
            run_id=run_id,
            scenario_path=scenario_path,
            stack_validation_path=stack_validation_path,
        )
        report = report_run(root=base_root, run_id=run_id)
        evidence_index = build_evidence_index(root=base_root)
    finally:
        _stop_adapter_server(server_process)
        if override_handle is not None:
            override_handle.cleanup()
    return {
        "mode": mode,
        "run_id": run_id,
        "prepare": prepare_result,
        "result": result,
        "artifact_validation": artifact_report,
        "test_evidence": test_evidence,
        "evaluated": evaluated,
        "promotion": promotion,
        "report": report,
        "evidence_index": evidence_index,
        "provider_status": provider_status,
        "waivers": materialized_waivers,
        "stack_validation_ref": None if stack_validation_path is None else str(stack_validation_path),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the root ATLAS QA CI gate.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--mode", choices=["dry-run", "evidence", "promotion"], required=True)
    parser.add_argument("--scenario")
    parser.add_argument("--scenario-file", type=Path)
    parser.add_argument("--adapter")
    parser.add_argument("--adapter-file", type=Path)
    parser.add_argument("--provider")
    parser.add_argument("--attestation-file", action="append", default=[])
    parser.add_argument("--waiver-spec", action="append", default=[])
    args = parser.parse_args(argv)

    result = ci_gate(
        root=args.root.resolve(),
        mode=args.mode,
        scenario=args.scenario,
        adapter=args.adapter,
        scenario_file=args.scenario_file.resolve() if isinstance(args.scenario_file, Path) else None,
        adapter_file=args.adapter_file.resolve() if isinstance(args.adapter_file, Path) else None,
        provider=args.provider,
        attestation_files=list(args.attestation_file),
        waiver_specs=_parse_waiver_specs(list(args.waiver_spec), root=args.root.resolve()),
    )
    print(json.dumps(result, indent=2))
    promotion_status = result["promotion"]["promotion_status"]
    if args.mode == "dry-run":
        return 0 if promotion_status == "dry_run" else 1
    if args.mode == "evidence":
        return 0 if result["artifact_validation"]["status"] == "clean" else 1
    return 0 if promotion_status in {"promoted_emulated", "promoted_physical", "promoted_physical_manual", "waived_promoted"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
