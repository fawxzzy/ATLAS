from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative
from ops.memory._common import CATALOG_NAME, MEMORY_SCHEMA_VERSION, discover_memory_sources, resolve_atlas_path


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(arguments: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        arguments,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part).strip()
    return completed.returncode, output


def validate_memory_shapes(memory_root: Path) -> list[str]:
    errors: list[str] = []
    catalog_path = memory_root / CATALOG_NAME
    if not catalog_path.exists():
        return [f"Memory catalog is missing: {atlas_relative(catalog_path)}"]
    catalog = load_json(catalog_path)
    if catalog.get("schema_version") != "atlas.memory.catalog.v1":
        errors.append("Memory catalog schema_version must be 'atlas.memory.catalog.v1'.")

    artifact_files = [path for path in memory_root.glob("*.json") if path.name != CATALOG_NAME]
    if not artifact_files:
        errors.append("No memory artifacts were found to validate.")
    for path in artifact_files:
        payload = load_json(path)
        if payload.get("schema_version") != MEMORY_SCHEMA_VERSION:
            errors.append(f"{atlas_relative(path)} has an unexpected schema_version.")
        source = payload.get("source", {})
        provenance = payload.get("provenance", {})
        memory = payload.get("memory", {})
        if not isinstance(source.get("path"), str):
            errors.append(f"{atlas_relative(path)} is missing source.path.")
        if source.get("path") != provenance.get("source_file"):
            errors.append(f"{atlas_relative(path)} has mismatched source.path and provenance.source_file.")
        if not isinstance(memory.get("overview"), str) or not memory["overview"].strip():
            errors.append(f"{atlas_relative(path)} is missing memory.overview.")
        key_points = memory.get("key_points")
        if not isinstance(key_points, list):
            errors.append(f"{atlas_relative(path)} has invalid memory.key_points.")
        else:
            for index, item in enumerate(key_points):
                if not isinstance(item, dict) or not isinstance(item.get("text"), str) or not isinstance(item.get("line"), int):
                    errors.append(f"{atlas_relative(path)} has invalid key_points[{index}].")
    return errors


def write_validation_report(output_dir: Path, payload: dict[str, Any]) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "memory-validation.latest.json"
    md_path = output_dir / "memory-validation.latest.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [
        "# Memory Validation Report",
        "",
        f"- Generated: `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- Passed: {payload['passed']}",
        f"- Findings: {len(payload['errors'])}",
        "",
    ]
    if payload["checks"]:
        lines.extend(["## Checks", ""])
        for check in payload["checks"]:
            lines.append(f"- `{check['name']}`: {check['status']}")
        lines.append("")
    if payload["errors"]:
        lines.extend(["## Errors", ""])
        for error in payload["errors"]:
            lines.append(f"- {error}")
        lines.append("")
    md_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ATLAS memory artifacts and repo-targeted handoff previews.")
    parser.add_argument("--memory-dir", default="runtime/cortex/catalog/memory")
    parser.add_argument("--output-dir", default="runtime/receipts/validation")
    args = parser.parse_args(argv)

    memory_dir = resolve_atlas_path(args.memory_dir)
    output_dir = resolve_atlas_path(args.output_dir)
    errors: list[str] = []
    checks: list[dict[str, str]] = []

    shape_errors = validate_memory_shapes(memory_dir)
    errors.extend(shape_errors)
    checks.append({"name": "memory_artifact_shape", "status": "passed" if not shape_errors else "failed"})

    root_handoff_path = ROOT / "tmp" / "scratch" / "memory-validation.stack-root.handoff.json"
    child_handoff_path = ROOT / "tmp" / "scratch" / "memory-validation.child-repo.handoff.json"
    root_handoff_path.parent.mkdir(parents=True, exist_ok=True)

    root_handoff = {
        "contract_version": "atlas.codex.handoff.v1",
        "handoff_id": "handoff-memory-validation-stack-root",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "producer": {"kind": "test", "name": "memory-validation", "capture_mode": "explicit_json_file"},
        "task_name": "memory-validation-stack-root",
        "workspace_root": ".",
        "repo_ids": ["stack"],
        "summary": "Synthetic stack-root handoff for validation.",
        "changed_files": [
            {"path": "docs/architecture/STACK-STANDARDS.md", "summary": "Validate root repo detection.", "status": "modified"}
        ],
        "validation": {"status": "passed", "summary": "Synthetic validation.", "commands": []},
        "commit_title": "test: validate repo detection",
        "commit_body": "Synthetic commit body for validation.",
        "pr_title": "Test repo detection",
        "pr_body": "Synthetic PR body for validation."
    }
    child_handoff = {
        **root_handoff,
        "handoff_id": "handoff-memory-validation-child",
        "task_name": "memory-validation-child-repo",
        "workspace_root": "repos/fawxzzy-atlas",
        "repo_ids": ["atlas"],
        "changed_files": [
            {"path": "repos/fawxzzy-atlas/AGENTS.md", "summary": "Validate deepest-match repo detection.", "status": "modified"}
        ],
    }
    root_handoff_path.write_text(json.dumps(root_handoff, indent=2), encoding="utf-8")
    child_handoff_path.write_text(json.dumps(child_handoff, indent=2), encoding="utf-8")

    detect_script = [sys.executable, str(ROOT / "ops" / "codex" / "detect_target_repo.py")]
    code, output = run_command(detect_script + ["--handoff-file", str(root_handoff_path)])
    detection_payload = json.loads(output)
    if code != 0 or detection_payload.get("status") != "resolved" or detection_payload.get("repo_id") != "stack":
        errors.append("Stack-root handoff did not resolve to repo id 'stack'.")
    checks.append({"name": "repo_target_detection_stack_root", "status": "passed" if detection_payload.get("status") == "resolved" and detection_payload.get("repo_id") == "stack" else "failed"})

    code, output = run_command(detect_script + ["--handoff-file", str(child_handoff_path)])
    child_repo_payload = json.loads(output)
    if code != 0 or child_repo_payload.get("status") != "resolved" or child_repo_payload.get("repo_id") != "atlas":
        errors.append("Child-repo handoff did not resolve to repo id 'atlas'.")
    checks.append({"name": "repo_target_detection_child_repo", "status": "passed" if child_repo_payload.get("status") == "resolved" and child_repo_payload.get("repo_id") == "atlas" else "failed"})

    preview_script = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ROOT / "ops" / "codex" / "commit_from_handoff.ps1"),
        "-HandoffFile",
        str(root_handoff_path),
        "-Mode",
        "preview",
    ]
    code, output = run_command(preview_script)
    preview_path = ROOT / "tmp" / "previews" / "memory-validation.stack-root.stack.commit-preview.json"
    if code != 0 or not preview_path.exists():
        errors.append("Commit preview path validation failed; expected preview artifact under tmp/previews.")
    checks.append({"name": "handoff_commit_preview_path", "status": "passed" if code == 0 and preview_path.exists() else "failed"})

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "memory_dir": atlas_relative(memory_dir),
        "source_count": len(discover_memory_sources()),
        "checks": checks,
        "errors": errors,
        "passed": not errors,
    }
    json_path, md_path = write_validation_report(output_dir, payload)

    print(f"Validation json : {atlas_relative(json_path)}")
    print(f"Validation md   : {atlas_relative(md_path)}")
    print(f"Passed          : {payload['passed']}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
