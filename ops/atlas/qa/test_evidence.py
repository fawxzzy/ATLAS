from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.qa._common import (
    TEST_EVIDENCE_CONTRACT_VERSION,
    build_receipt_origin,
    default_run_root,
    load_adapter_manifest,
    load_json_object,
    payload_with_digest,
    resolve_ref,
    utc_now,
    validate_test_evidence_payload,
    write_manifest,
)

RUNNER_VERSION = "atlas.qa.test-evidence.v1"


def _parse_counts(*, runner: str, stdout: str, stderr: str) -> dict[str, int]:
    text = "\n".join([stdout, stderr])
    patterns = [
        re.compile(r"(?P<passed>\d+)\s+passed(?:,?\s+(?P<failed>\d+)\s+failed)?", re.IGNORECASE),
        re.compile(r"Ran\s+(?P<total>\d+)\s+tests?", re.IGNORECASE),
        re.compile(r"(?P<failed>\d+)\s+failed", re.IGNORECASE),
    ]
    counts: dict[str, int] = {}
    for pattern in patterns:
        match = pattern.search(text)
        if not match:
            continue
        for key, value in match.groupdict().items():
            if value is not None:
                counts[key] = int(value)
    if "total" not in counts and "passed" in counts and "failed" in counts:
        counts["total"] = counts["passed"] + counts["failed"]
    if "passed" not in counts and "total" in counts and "failed" in counts:
        counts["passed"] = max(0, counts["total"] - counts["failed"])
    if runner == "custom" and not counts:
        return {}
    return counts


def collect_test_evidence(
    *,
    root: Path | None = None,
    run_id: str,
    scenario_payload: dict[str, Any] | None = None,
    adapter_payload: dict[str, Any] | None = None,
    output_file: Path | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    run_root = (default_run_root(root=base_root) / run_id).resolve()
    result_payload = load_json_object(run_root / "matrix.result.json")
    scenario = scenario_payload or load_json_object(resolve_ref(str(result_payload["scenario_ref"]), root=base_root))
    if adapter_payload is not None:
        adapter = adapter_payload
    elif isinstance(result_payload.get("adapter_ref"), str) and str(result_payload.get("adapter_ref")).strip():
        adapter = load_json_object(resolve_ref(str(result_payload["adapter_ref"]), root=base_root))
    else:
        adapter = load_adapter_manifest(
            root=base_root,
            adapter_id=str(result_payload["adapter_id"]),
            repo_id=str(result_payload["repo_id"]),
        )[0]
    definitions = scenario.get("test_evidence", []) if isinstance(scenario.get("test_evidence"), list) else []
    repo_root = resolve_ref(str(result_payload["repo_path"]), root=base_root)
    output_root = run_root / "test-evidence"
    output_root.mkdir(parents=True, exist_ok=True)
    dry_run = bool(result_payload.get("mode") == "dry_run")

    receipts: list[dict[str, Any]] = []
    cache: dict[str, dict[str, Any]] = {}
    for definition in definitions:
        if not isinstance(definition, dict):
            continue
        evidence_id = str(definition.get("evidence_id") or "")
        command_ref = str(definition.get("command_ref") or "")
        runner = str(definition.get("runner") or "custom")
        kind = str(definition.get("kind") or "custom")
        required_for = list(definition.get("required_for", [])) if isinstance(definition.get("required_for"), list) else []
        command_def = adapter.get("commands", {}).get(command_ref) if isinstance(adapter.get("commands"), dict) else None
        command = str(command_def.get("command") or "") if isinstance(command_def, dict) else ""
        receipt_root = output_root / evidence_id
        receipt_root.mkdir(parents=True, exist_ok=True)
        receipt: dict[str, Any] = {
            "evidence_id": evidence_id,
            "command_ref": command_ref,
            "runner": runner,
            "kind": kind,
            "required_for": required_for,
            "status": "planned" if dry_run else "missing",
        }
        if not command:
            receipt["status"] = "missing"
            receipt["message"] = f"Adapter command '{command_ref}' is not defined."
            receipts.append(receipt)
            continue
        receipt["command"] = command
        if dry_run:
            receipts.append(receipt)
            continue
        if command not in cache:
            started = time.perf_counter()
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
            duration_ms = int(round((time.perf_counter() - started) * 1000))
            stdout_path = receipt_root / "stdout.log"
            stderr_path = receipt_root / "stderr.log"
            stdout_path.write_text(completed.stdout or "", encoding="utf-8")
            stderr_path.write_text(completed.stderr or "", encoding="utf-8")
            cache[command] = {
                "exit_code": completed.returncode,
                "duration_ms": duration_ms,
                "stdout_ref": atlas_relative(stdout_path, root=base_root),
                "stderr_ref": atlas_relative(stderr_path, root=base_root),
                "counts": _parse_counts(runner=runner, stdout=completed.stdout or "", stderr=completed.stderr or ""),
            }
        cached = cache[command]
        receipt.update(cached)
        receipt["status"] = "passed" if int(cached["exit_code"]) == 0 else "failed"
        receipts.append(receipt)

    required_count = sum(1 for item in receipts if "promotion" in item.get("required_for", []))
    failed_count = sum(1 for item in receipts if item.get("status") == "failed" and "promotion" in item.get("required_for", []))
    missing_count = sum(1 for item in receipts if item.get("status") == "missing" and "promotion" in item.get("required_for", []))
    body = {
        "contract_version": TEST_EVIDENCE_CONTRACT_VERSION,
        "generated_at": utc_now(),
        "runner_version": RUNNER_VERSION,
        "run_id": str(result_payload["run_id"]),
        "scenario_id": str(scenario["scenario_id"]),
        "adapter_id": str(result_payload["adapter_id"]),
        "repo_id": str(result_payload["repo_id"]),
        "git_sha": str(result_payload["git_sha"]),
        "mode": str(result_payload["mode"]),
        "receipts": receipts,
        "summary": {
            "required_count": required_count,
            "failed_count": failed_count,
            "missing_count": missing_count,
            "status": "planned" if dry_run else ("failed" if failed_count else ("missing" if missing_count else ("clean" if required_count else "not_configured"))),
        },
        "receipt_origin": build_receipt_origin(
            root=base_root,
            runner_version=RUNNER_VERSION,
            repo_id=str(result_payload["repo_id"]),
            git_sha=str(result_payload["git_sha"]),
            command="python ops/atlas/qa/test_evidence.py",
        ),
    }
    manifest = payload_with_digest(body, "test_evidence_id")
    errors = validate_test_evidence_payload(manifest)
    if errors:
        raise ValueError("; ".join(errors))
    target = output_file.resolve() if isinstance(output_file, Path) else run_root / "test-evidence.json"
    write_manifest(target, manifest)
    return manifest | {"output_ref": atlas_relative(target, root=base_root)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect root-readable ATLAS QA test evidence receipts.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--run", required=True)
    parser.add_argument("--output-file", type=Path)
    args = parser.parse_args(argv)

    result = collect_test_evidence(
        root=args.root.resolve(),
        run_id=args.run,
        output_file=args.output_file.resolve() if isinstance(args.output_file, Path) else None,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["summary"]["status"] in {"planned", "clean", "not_configured"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
