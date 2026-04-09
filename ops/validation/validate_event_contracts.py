from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EVENT_TYPES = [
    "session_start",
    "task_start",
    "pre_command",
    "post_command",
    "validation_complete",
    "export_complete",
    "session_stop",
]
REJECTED_LANE = "runtime/receipts/events/_rejected/invalid_input"


@dataclass
class CheckResult:
    event_type: str
    check: str
    ok: bool
    details: str
    command: list[str]


def atlas_root() -> Path:
    return Path(__file__).resolve().parents[2]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def output_dir() -> Path:
    return atlas_root() / "runtime" / "receipts" / "validation"


def schema_dir() -> Path:
    return atlas_root() / "ops" / "events" / "schemas"


def invoke_script() -> Path:
    return atlas_root() / "ops" / "events" / "invoke_event.py"


def validate_required_stack_paths() -> list[CheckResult]:
    stack_path = atlas_root() / "stack.yaml"
    text = stack_path.read_text(encoding="utf-8")
    expectations = [
        "cortex_playbooks: runtime/cortex/catalog/playbooks",
        "events: runtime/receipts/events",
        "playbooks: data/imports/playbooks",
        "playbooks: docs/playbooks",
        "codex: ops/codex",
        "events: ops/events",
    ]
    results: list[CheckResult] = []
    for expected in expectations:
        results.append(
            CheckResult(
                event_type="stack",
                check="stack_path_contract",
                ok=expected in text,
                details=f"Expected stack.yaml to contain '{expected}'.",
                command=["internal-check", expected],
            )
        )
    return results


def base_event(event_type: str) -> dict[str, Any]:
    shared = {
        "contract_version": "atlas.event.v1",
        "event_type": event_type,
        "event_id": f"{event_type}-evt-001",
        "occurred_at": "2026-04-09T12:00:00Z",
        "producer": {
            "kind": "test",
            "name": "validate_event_contracts.py",
            "version": "1",
        },
        "session": {
            "session_id": "session-001",
            "workspace_root": ".",
            "operator": "validator",
        },
    }
    if event_type == "session_start":
        shared["payload"] = {
            "trigger": "wrapper",
            "intent": "Validate the event contract.",
            "workspace_scope": [
                ".",
                "ops/events",
            ],
            "metadata": {
                "mode": "test",
            },
        }
        return shared
    if event_type == "task_start":
        shared["task"] = {
            "task_id": "task-001",
            "task_name": "validate-event-contracts",
            "scope_paths": [
                "ops/events",
                "ops/validation",
            ],
            "repo_ids": [
                "stack",
            ],
            "mutation_mode": "stack_only",
        }
        shared["payload"] = {
            "task_summary": "Validate the stack-owned event contracts.",
            "scoped_paths": [
                "ops/events",
                "ops/validation",
            ],
            "mutation_mode": "stack_only",
            "validation_plan": [
                "python ops/validation/validate_event_contracts.py",
            ],
        }
        return shared
    if event_type == "pre_command":
        shared["task"] = {
            "task_id": "task-001",
            "task_name": "validate-event-contracts",
        }
        shared["payload"] = {
            "command": [
                "python",
                "ops/validation/validate_event_contracts.py",
            ],
            "cwd": ".",
            "timeout_seconds": 30,
            "intent": "Run the validator.",
        }
        return shared
    if event_type == "post_command":
        shared["task"] = {
            "task_id": "task-001",
            "task_name": "validate-event-contracts",
        }
        shared["payload"] = {
            "command": [
                "python",
                "ops/validation/validate_event_contracts.py",
            ],
            "cwd": ".",
            "status": "succeeded",
            "exit_code": 0,
            "duration_ms": 42,
            "stdout_summary": "Validator completed.",
            "stderr_summary": "",
        }
        return shared
    if event_type == "validation_complete":
        shared["task"] = {
            "task_id": "task-001",
            "task_name": "validate-event-contracts",
        }
        shared["payload"] = {
            "validator": "ops/validation/validate_event_contracts.py",
            "status": "passed",
            "summary": "All event schemas validated successfully.",
            "artifacts": [
                "runtime/receipts/validation/event-contract-validation.latest.json",
            ],
            "finding_counts": {
                "critical": 0,
                "error": 0,
                "warning": 0,
                "info": 0,
            },
        }
        return shared
    if event_type == "export_complete":
        shared["task"] = {
            "task_id": "task-001",
            "task_name": "validate-event-contracts",
        }
        shared["payload"] = {
            "export_type": "snapshot",
            "status": "created",
            "artifact_path": "packages/snapshots/example.zip",
            "manifest_path": "packages/snapshots/example/EXPORT-MANIFEST.json",
            "summary": "Example export receipt.",
        }
        return shared
    if event_type == "session_stop":
        shared["payload"] = {
            "status": "completed",
            "summary": "Validator session complete.",
            "task_ids": [
                "task-001",
            ],
            "receipt_count": 7,
        }
        return shared
    raise ValueError(f"Unsupported event type: {event_type}")


def run_invocation(payload: dict[str, Any]) -> tuple[int, str]:
    temp_dir = atlas_root() / "tmp" / "scratch" / "event-validation"
    temp_dir.mkdir(parents=True, exist_ok=True)
    payload_path = temp_dir / f"{payload['event_type']}.json"
    payload_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    command = [
        sys.executable,
        str(invoke_script()),
        "--payload-file",
        str(payload_path),
        "--skip-handler",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False, cwd=atlas_root())
    output = completed.stdout.strip()
    if completed.stderr.strip():
        output = f"{output}\n{completed.stderr.strip()}".strip()
    return completed.returncode, output


def collect_results() -> list[CheckResult]:
    results = validate_required_stack_paths()
    unsupported_payload = {
        "contract_version": "atlas.event.v1",
        "event_type": "unsupported_event",
        "event_id": "unsupported-evt-001",
        "occurred_at": "2026-04-09T12:00:00Z",
        "producer": {
            "kind": "test",
            "name": "validate_event_contracts.py",
            "version": "1",
        },
        "session": {
            "session_id": "session-001",
            "workspace_root": ".",
            "operator": "validator",
        },
        "payload": {
            "summary": "This should be rejected before event schema validation.",
        },
    }
    unsupported_code, unsupported_output = run_invocation(unsupported_payload)
    results.append(
        CheckResult(
            event_type="rejected_input",
            check="unsupported_event_routes_to_rejected_lane",
            ok=unsupported_code != 0 and REJECTED_LANE in unsupported_output,
            details=unsupported_output or "No output.",
            command=[sys.executable, str(invoke_script()), "--payload-file", "tmp/scratch/event-validation/unsupported_event.json", "--skip-handler"],
        )
    )
    for event_type in EVENT_TYPES:
        schema_path = schema_dir() / f"{event_type}.schema.json"
        results.append(
            CheckResult(
                event_type=event_type,
                check="schema_exists",
                ok=schema_path.exists(),
                details=f"Schema path checked: {schema_path.relative_to(atlas_root()).as_posix()}",
                command=["internal-check", str(schema_path)],
            )
        )
        valid_payload = base_event(event_type)
        valid_code, valid_output = run_invocation(valid_payload)
        results.append(
            CheckResult(
                event_type=event_type,
                check="valid_payload_accepts",
                ok=valid_code == 0,
                details=valid_output or "No output.",
                command=[sys.executable, str(invoke_script()), "--payload-file", f"tmp/scratch/event-validation/{event_type}.json", "--skip-handler"],
            )
        )

        invalid_payload = json.loads(json.dumps(valid_payload))
        if event_type == "session_start":
            del invalid_payload["payload"]["intent"]
        elif event_type == "session_stop":
            invalid_payload["payload"]["status"] = "not-valid"
        else:
            del invalid_payload["task"]
        invalid_code, invalid_output = run_invocation(invalid_payload)
        results.append(
            CheckResult(
                event_type=event_type,
                check="invalid_payload_rejects",
                ok=invalid_code != 0,
                details=(invalid_output or "No output.").replace("Event rejected:", "Event rejected (supported lifecycle type):"),
                command=[sys.executable, str(invoke_script()), "--payload-file", f"tmp/scratch/event-validation/{event_type}.json", "--skip-handler"],
            )
        )
    return results


def build_report(results: list[CheckResult]) -> dict[str, Any]:
    failures = [result for result in results if not result.ok]
    return {
        "generated_at": utc_now(),
        "stack_root": ".",
        "summary": {
            "total_checks": len(results),
            "passed": len(results) - len(failures),
            "failed": len(failures),
            "event_types": len(EVENT_TYPES),
        },
        "results": [asdict(item) for item in results],
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Event Contract Validation Report",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Stack root: `{report['stack_root']}`",
        f"- Total checks: {report['summary']['total_checks']}",
        f"- Passed: {report['summary']['passed']}",
        f"- Failed: {report['summary']['failed']}",
        "",
    ]
    for result in report["results"]:
        status = "PASS" if result["ok"] else "FAIL"
        command = " ".join(result["command"])
        lines.append(f"- [{status}] `{result['event_type']}` / `{result['check']}`")
        lines.append(f"  command: `{command}`")
        lines.append(f"  details: {result['details'] or 'n/a'}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    out_dir = output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    results = collect_results()
    report = build_report(results)
    json_path = out_dir / "event-contract-validation.latest.json"
    md_path = out_dir / "event-contract-validation.latest.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, md_path)
    print(
        "Event contract validation complete: "
        f"passed={report['summary']['passed']} "
        f"failed={report['summary']['failed']}"
    )
    print(f"Markdown report: {md_path.relative_to(atlas_root()).as_posix()}")
    print(f"JSON report: {json_path.relative_to(atlas_root()).as_posix()}")
    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
