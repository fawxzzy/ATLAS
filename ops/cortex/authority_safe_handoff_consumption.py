from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes

SCHEMA_VERSION = "atlas.cortex.authority-safe-handoff-consumption.v1"
SOURCE_SCHEMA_VERSION = "atlas.cortex.authority-safe-interface-handoff.v1"
STATUS_OK = "ok"
STATUS_ADVISORY = "advisory_gap"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"

EXPECTED_SOURCE_FIELDS = (
    "schema_version",
    "status",
    "root",
    "branch",
    "head",
    "source_refs",
    "consumed_surfaces",
    "handoff_payload",
    "authority_denials",
    "forbidden_surfaces",
    "warnings",
    "blockers",
    "safe_to_use",
)
EXPECTED_AUTHORITY_DENIALS = (
    "execution",
    "approval",
    "owner-truth",
    "final-receipt",
    "deploy",
    "secret-handling",
    "transcript-scraping",
    "automatic-_stack-dispatch",
    "repo-mutation",
    "platform-mutation",
)
FORBIDDEN_SURFACES = (
    "repos/**",
    "archive/**",
    ".vercel/**",
    ".playwright-mcp/**",
    "secrets/**",
    ".env*",
    "deployment outputs",
    "owner-repo receipts",
    "runtime latest files by default",
    "final Lifeline receipts",
    "hidden transcript/chat/session state",
)
PROTECTED_PREFIXES = (
    ".playwright-mcp",
    ".vercel",
    "archive",
    "repos",
    "secrets",
)


def _finding(code: str, message: str, **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _git_stdout(root: Path, *args: str) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def collect_git_state(root: Path) -> tuple[str | None, str | None]:
    return _git_stdout(root, "branch", "--show-current"), _git_stdout(root, "rev-parse", "HEAD")


def _normalize_ref(candidate: str | Path, root: Path) -> tuple[str | None, OrderedDict[str, Any] | None]:
    value = Path(candidate)
    if value.is_absolute():
        return None, _finding("absolute_path_forbidden", "Path must be root-relative.", path=normalize_slashes(str(value)))
    ref = normalize_slashes(str(value)).strip("/")
    if not ref or ref.startswith("../") or "/../" in f"/{ref}/":
        return None, _finding("parent_traversal_forbidden", "Path must not use parent traversal.", path=ref)
    first = ref.split("/", 1)[0]
    filename = ref.rsplit("/", 1)[-1]
    if first in PROTECTED_PREFIXES or first.startswith(".env") or filename.startswith(".env"):
        return None, _finding("protected_path_forbidden", "Path targets a protected or forbidden surface.", path=ref)
    resolved = (root / ref).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_path", "Path must stay inside the ATLAS root.", path=ref)
    return ref, None


def resolve_handoff_path(root: Path, handoff: str | None) -> tuple[str | None, Path | None, OrderedDict[str, Any] | None]:
    if not handoff:
        return None, None, _finding("handoff_required", "A root-relative --handoff JSON payload is required for consumption.")
    ref, error = _normalize_ref(handoff, root)
    if error is not None or ref is None:
        return None, None, error
    resolved = (root / ref).resolve()
    if not resolved.exists() or not resolved.is_file():
        return ref, None, _finding("handoff_missing", "Handoff payload does not exist.", path=ref)
    return ref, resolved, None


def validate_output_path(root: Path, output: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    ref, error = _normalize_ref(output, root)
    if error is not None or ref is None:
        return None, error
    if not ref.startswith("tmp/"):
        return None, _finding("non_tmp_output_path", "Output path must be under tmp/** for this helper.", path=ref)
    return (root / ref).resolve(), None


def read_validation(root: Path) -> tuple[OrderedDict[str, int], OrderedDict[str, Any] | None]:
    path = root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json"
    counts = OrderedDict([("critical", 0), ("error", 0), ("warning", 0), ("info", 0)])
    if not path.exists():
        return counts, _finding("validation_missing", "Stack validation receipt is unavailable.", path=atlas_relative(path, root=root))
    payload = json.loads(path.read_text(encoding="utf-8"))
    summary = payload.get("summary") if isinstance(payload, dict) else {}
    if not isinstance(summary, dict):
        return counts, _finding("validation_summary_missing", "Stack validation summary is unavailable.", path=atlas_relative(path, root=root))
    for key in counts:
        counts[key] = int(summary.get(key, 0) or 0)
    return counts, None


def _load_handoff(path: Path) -> tuple[OrderedDict[str, Any] | None, OrderedDict[str, Any] | None, str | None]:
    raw = path.read_bytes()
    digest = f"sha256:{hashlib.sha256(raw).hexdigest()}"
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=OrderedDict)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, _finding("handoff_malformed", "Handoff payload is not valid UTF-8 JSON.", exception=str(exc)), digest
    if not isinstance(payload, OrderedDict):
        return None, _finding("handoff_not_object", "Handoff payload must be a JSON object."), digest
    return payload, None, digest


def _validate_handoff_payload(payload: OrderedDict[str, Any]) -> tuple[OrderedDict[str, Any], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    blockers: list[OrderedDict[str, Any]] = []
    warnings: list[OrderedDict[str, Any]] = []
    missing = [field for field in EXPECTED_SOURCE_FIELDS if field not in payload]
    if missing:
        blockers.append(_finding("handoff_missing_fields", "Handoff payload is missing required fields.", fields=missing))
    if payload.get("schema_version") != SOURCE_SCHEMA_VERSION:
        blockers.append(
            _finding(
                "handoff_schema_mismatch",
                "Handoff payload schema is not the authority-safe interface handoff schema.",
                expected=SOURCE_SCHEMA_VERSION,
                actual=payload.get("schema_version"),
            )
        )
    if payload.get("safe_to_use") is not True:
        warnings.append(_finding("handoff_not_safe_to_use", "Source handoff is not marked safe_to_use=true."))

    denials = payload.get("authority_denials")
    if not isinstance(denials, list):
        blockers.append(_finding("authority_denials_missing", "Handoff payload authority_denials must be a list."))
        consumed_denials: list[str] = []
    else:
        consumed_denials = [str(item) for item in denials]
        missing_denials = [denial for denial in EXPECTED_AUTHORITY_DENIALS if denial not in consumed_denials]
        if missing_denials:
            blockers.append(_finding("authority_denials_incomplete", "Handoff payload is missing required authority denials.", denials=missing_denials))

    result = OrderedDict(
        [
            ("schema_valid", not blockers),
            ("source_status", payload.get("status")),
            ("source_safe_to_use", payload.get("safe_to_use")),
            ("source_warning_count", len(payload.get("warnings", [])) if isinstance(payload.get("warnings"), list) else 0),
            ("source_blocker_count", len(payload.get("blockers", [])) if isinstance(payload.get("blockers"), list) else 0),
        ]
    )
    return result, warnings, blockers


def build_consumption_report(*, root: Path | None = None, handoff: str | None = None) -> OrderedDict[str, Any]:
    base = (root or atlas_root()).resolve()
    branch, head = collect_git_state(base)
    warnings: list[OrderedDict[str, Any]] = []
    blockers: list[OrderedDict[str, Any]] = []

    handoff_ref, handoff_path, handoff_error = resolve_handoff_path(base, handoff)
    handoff_digest: str | None = None
    handoff_payload: OrderedDict[str, Any] | None = None
    consumption_result = OrderedDict(
        [
            ("schema_valid", False),
            ("source_status", None),
            ("source_safe_to_use", None),
            ("source_warning_count", 0),
            ("source_blocker_count", 0),
        ]
    )
    consumed_denials: list[str] = []

    if handoff_error is not None:
        if handoff_error["code"] == "handoff_required":
            warnings.append(handoff_error)
        else:
            blockers.append(handoff_error)
    elif handoff_path is not None:
        handoff_payload, load_error, handoff_digest = _load_handoff(handoff_path)
        if load_error is not None:
            blockers.append(load_error)
        elif handoff_payload is not None:
            consumption_result, payload_warnings, payload_blockers = _validate_handoff_payload(handoff_payload)
            warnings.extend(payload_warnings)
            blockers.extend(payload_blockers)
            raw_denials = handoff_payload.get("authority_denials")
            if isinstance(raw_denials, list):
                consumed_denials = [str(item) for item in raw_denials]

    validation_counts, validation_error = read_validation(base)
    if validation_error is not None:
        warnings.append(validation_error)
    if validation_counts["critical"] or validation_counts["error"]:
        blockers.append(
            _finding(
                "validation_not_safe",
                "Stack validation has critical or error findings; handoff consumption is not safe to use.",
                critical=validation_counts["critical"],
                error=validation_counts["error"],
            )
        )

    status = STATUS_OK
    if blockers:
        status = STATUS_BLOCKER
    elif warnings:
        status = STATUS_ADVISORY
    safe_to_use = status == STATUS_OK

    advisory_payload = OrderedDict(
        [
            ("advisory_only", True),
            ("execution_authorized", False),
            ("approval_authorized", False),
            ("owner_truth_authorized", False),
            ("final_receipt_authorized", False),
            ("deploy_authorized", False),
            ("secret_handling_authorized", False),
            ("stack_dispatch_authorized", False),
            ("repo_mutation_authorized", False),
            ("platform_mutation_authorized", False),
            ("validation", validation_counts),
        ]
    )

    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("root", normalize_slashes(str(base))),
            ("branch", branch),
            ("head", head),
            ("handoff_ref", handoff_ref),
            ("handoff_digest", handoff_digest),
            ("consumption_result", consumption_result),
            ("consumed_authority_denials", consumed_denials),
            ("preserved_authority_denials", consumed_denials),
            ("advisory_payload", advisory_payload),
            ("forbidden_surfaces", list(FORBIDDEN_SURFACES)),
            ("warnings", warnings),
            ("blockers", blockers),
            ("safe_to_use", safe_to_use),
        ]
    )


def render_summary(report: OrderedDict[str, Any]) -> str:
    return "\n".join(
        [
            "Authority-Safe Cortex Handoff Consumption",
            f"Status: {report['status']}",
            f"Branch: {report.get('branch') or 'unknown'}",
            f"Head: {report.get('head') or 'unknown'}",
            f"Handoff: {report.get('handoff_ref') or 'none'}",
            f"Safe to use: {str(report.get('safe_to_use')).lower()}",
            "Authority: advisory only; no execution, approval, owner-truth, deploy, secret, _stack dispatch, repo mutation, platform mutation, or final-receipt authority.",
        ]
    ) + "\n"


def exit_code(status: str, *, strict: bool) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_ADVISORY:
        return 1 if strict else 0
    if status == STATUS_BLOCKER:
        return 2
    return 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Consume an authority-safe Cortex interface handoff as advisory substrate.")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON only.")
    parser.add_argument("--handoff", help="Root-relative JSON handoff payload produced by authority_safe_interface_handoff.py.")
    parser.add_argument("--output", help="Optional root-relative tmp/** output path.")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    root = atlas_root().resolve()
    try:
        report = build_consumption_report(root=root, handoff=args.handoff)
        if args.output:
            resolved_output, output_error = validate_output_path(root, args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKER
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
                report["safe_to_use"] = False
            elif resolved_output is not None:
                resolved_output.parent.mkdir(parents=True, exist_ok=True)
                resolved_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(render_summary(report), end="")
        return exit_code(str(report.get("status") or STATUS_INTERNAL_ERROR), strict=args.strict)
    except Exception as exc:
        report = OrderedDict(
            [
                ("schema_version", SCHEMA_VERSION),
                ("status", STATUS_INTERNAL_ERROR),
                ("root", normalize_slashes(str(root))),
                ("branch", None),
                ("head", None),
                ("handoff_ref", None),
                ("handoff_digest", None),
                ("consumption_result", OrderedDict()),
                ("consumed_authority_denials", []),
                ("preserved_authority_denials", []),
                ("advisory_payload", OrderedDict([("advisory_only", True)])),
                ("forbidden_surfaces", list(FORBIDDEN_SURFACES)),
                ("warnings", []),
                ("blockers", [_finding("internal_error", "Authority-safe handoff consumption failed before completion.", exception=str(exc))]),
                ("safe_to_use", False),
            ]
        )
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(render_summary(report), end="")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
