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

SCHEMA_VERSION = "atlas.cortex.second-advisory-substrate-consumption.v1"
STATUS_OK = "ok"
STATUS_ADVISORY = "advisory_gap"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"

AUTHORITY_DENIALS = (
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
    "owner-repo-mutation",
    "protected-surface-mutation",
    "workflow-dispatch",
    "marker-movement",
)

FORBIDDEN_SURFACES = (
    "repos/**",
    "archive/**",
    ".vercel/**",
    ".playwright-mcp/**",
    "secrets/**",
    ".env*",
    ".github/workflows/**",
    "deployment outputs",
    "deploy/platform outputs",
    "owner-repo receipts as truth inputs",
    "runtime latest files by default",
    "final Lifeline receipts",
    "hidden transcript/chat/session state",
)

CONTINUITY_MANIFEST_REFS = {
    "docs/memory/initiatives/continuity-manifest-cortex-readiness.json",
}
RESTART_MIRROR_REFS = {
    "docs/atlas-book/01-current-state.md",
    "docs/atlas-book/02-lanes-and-markers.md",
    "docs/atlas-book/05-receipt-index.md",
    "docs/atlas-book/12-restart-and-handoff-guide.md",
}
RUNTIME_ARTIFACT_REFS = {
    "runtime/cortex/current-state/latest.json",
    "runtime/cortex/operator-surface/latest.json",
    "runtime/cortex/context/latest.json",
    "runtime/cortex/worker-prompts/latest.json",
}
VALIDATION_REFS = {
    "runtime/receipts/validation/stack-validation.latest.json",
}
HELPER_REFERENCE_REFS = {
    "ops/cortex/authority_safe_interface_handoff.py",
    "ops/cortex/authority_safe_handoff_consumption.py",
    "ops/cortex/worker_prompt.py",
    "tests/test_cortex_authority_safe_interface_handoff.py",
    "tests/test_cortex_authority_safe_handoff_consumption.py",
    "tests/test_cortex_worker_prompt.py",
}
RECEIPT_PREFIXES = (
    ("docs/ops/CORTEX-READINESS-", "cortex_readiness_receipt"),
    ("docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-", "playbook_cortex_receipt"),
)

PROTECTED_PREFIXES = (
    ".github/workflows",
    ".playwright-mcp",
    ".vercel",
    "archive",
    "repos",
    "secrets",
)
DEPLOY_OR_PLATFORM_PREFIXES = (
    "deploy",
    "deployment",
    "platform",
    "vercel",
)
HIDDEN_CONTEXT_PREFIXES = (
    ".codex",
    "runtime/sessions",
    "runtime/session",
    "runtime/transcripts",
    "runtime/chats",
    "runtime/atlas/conversations",
    "runtime/atlas/sessions",
    "tmp/transcripts",
    "tmp/chats",
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


def _has_env_component(ref: str) -> bool:
    return any(part.startswith(".env") for part in ref.split("/"))


def _is_prefix_match(ref: str, prefixes: tuple[str, ...]) -> bool:
    return any(ref == prefix or ref.startswith(f"{prefix}/") for prefix in prefixes)


def _normalize_ref(candidate: str | Path, root: Path) -> tuple[str | None, OrderedDict[str, Any] | None]:
    value = Path(candidate)
    if value.is_absolute():
        return None, _finding("absolute_path_forbidden", "Path must be root-relative.", path=normalize_slashes(str(value)))
    ref = normalize_slashes(str(value)).strip("/")
    if not ref or ref.startswith("../") or "/../" in f"/{ref}/":
        return None, _finding("parent_traversal_forbidden", "Path must not use parent traversal.", path=ref)
    if _has_env_component(ref):
        return None, _finding("secret_path_forbidden", "Path targets an .env secret surface.", path=ref)
    if _is_prefix_match(ref, PROTECTED_PREFIXES):
        return None, _finding("protected_path_forbidden", "Path targets a protected or owner surface.", path=ref)
    if _is_prefix_match(ref, DEPLOY_OR_PLATFORM_PREFIXES):
        return None, _finding("deploy_platform_path_forbidden", "Deploy and platform outputs are not admitted source surfaces.", path=ref)
    if _is_prefix_match(ref, HIDDEN_CONTEXT_PREFIXES) or any(token in ref.lower() for token in ("transcript", "chat", "session")):
        return None, _finding("hidden_context_path_forbidden", "Hidden transcript, chat, or session state is not admitted.", path=ref)
    resolved = (root / ref).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_path", "Path must stay inside the ATLAS root.", path=ref)
    return ref, None


def classify_source_ref(ref: str) -> str | None:
    if ref in CONTINUITY_MANIFEST_REFS:
        return "cortex_continuity_manifest"
    if ref in RESTART_MIRROR_REFS:
        return "cortex_restart_mirror"
    if ref in RUNTIME_ARTIFACT_REFS:
        return "cortex_runtime_artifact"
    if ref in VALIDATION_REFS:
        return "validation_receipt"
    if ref in HELPER_REFERENCE_REFS:
        return "cortex_contract_reference"
    for prefix, substrate_class in RECEIPT_PREFIXES:
        if ref.startswith(prefix) and ref.endswith(".md"):
            return substrate_class
    return None


def resolve_source_path(root: Path, source: str | None) -> tuple[str | None, Path | None, str | None, OrderedDict[str, Any] | None]:
    if not source:
        return None, None, None, _finding("source_required", "A root-relative --source is required for advisory substrate consumption.")
    ref, error = _normalize_ref(source, root)
    if error is not None or ref is None:
        return None, None, None, error
    substrate_class = classify_source_ref(ref)
    if substrate_class is None:
        return ref, None, None, _finding("source_not_admitted", "Source path is outside the admitted second advisory substrate classes.", path=ref)
    resolved = (root / ref).resolve()
    if not resolved.exists() or not resolved.is_file():
        return ref, None, substrate_class, _finding("source_missing", "Source path does not exist.", path=ref)
    return ref, resolved, substrate_class, None


def validate_output_path(root: Path, output: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    ref, error = _normalize_ref(output, root)
    if error is not None or ref is None:
        return None, error
    if not ref.startswith("tmp/") or not ref.endswith(".json"):
        return None, _finding("non_tmp_json_output_path", "Output path must be under tmp/** and end with .json.", path=ref)
    return (root / ref).resolve(), None


def read_validation(root: Path) -> tuple[OrderedDict[str, int], OrderedDict[str, Any] | None]:
    path = root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json"
    counts = OrderedDict([("critical", 0), ("error", 0), ("warning", 0), ("info", 0)])
    if not path.exists():
        return counts, _finding("validation_missing", "Stack validation receipt is unavailable.", path=atlas_relative(path, root=root))
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return counts, _finding("validation_malformed", "Stack validation receipt is not valid JSON.", path=atlas_relative(path, root=root), exception=str(exc))
    summary = payload.get("summary") if isinstance(payload, dict) else {}
    if not isinstance(summary, dict):
        return counts, _finding("validation_summary_missing", "Stack validation summary is unavailable.", path=atlas_relative(path, root=root))
    for key in counts:
        counts[key] = int(summary.get(key, 0) or 0)
    return counts, None


def _load_source(path: Path) -> tuple[bytes | None, OrderedDict[str, Any] | None]:
    try:
        return path.read_bytes(), None
    except OSError as exc:
        return None, _finding("source_read_failed", "Source could not be read.", path=normalize_slashes(str(path)), exception=str(exc))


def _json_payload(raw: bytes, *, source_ref: str) -> tuple[OrderedDict[str, Any] | None, OrderedDict[str, Any] | None]:
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=OrderedDict)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, _finding("source_malformed", "Source is not valid UTF-8 JSON.", path=source_ref, exception=str(exc))
    if not isinstance(payload, OrderedDict):
        return None, _finding("source_not_object", "Source JSON must be an object.", path=source_ref)
    return payload, None


def _validate_json_fields(payload: OrderedDict[str, Any], *, required: tuple[str, ...], code: str) -> list[OrderedDict[str, Any]]:
    missing = [field for field in required if field not in payload]
    if not missing:
        return []
    return [_finding(code, "Source JSON is missing required fields.", fields=missing)]


def validate_source_shape(*, source_ref: str, substrate_class: str, raw: bytes) -> tuple[OrderedDict[str, Any], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    warnings: list[OrderedDict[str, Any]] = []
    blockers: list[OrderedDict[str, Any]] = []
    result: OrderedDict[str, Any] = OrderedDict(
        [
            ("source_exists", True),
            ("source_type", None),
            ("schema_valid", False),
            ("source_status", None),
            ("source_safe_to_use", None),
            ("source_warning_count", 0),
            ("source_blocker_count", 0),
        ]
    )

    if substrate_class == "cortex_continuity_manifest":
        payload, error = _json_payload(raw, source_ref=source_ref)
        if error is not None or payload is None:
            blockers.append(error or _finding("source_malformed", "Source JSON is unavailable.", path=source_ref))
        else:
            result["source_type"] = str(payload.get("contract_version") or payload.get("schema_version") or "json")
            result["source_status"] = payload.get("status")
            metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
            blockers.extend(_validate_json_fields(payload, required=("contract_version", "id", "metadata"), code="manifest_missing_fields"))
            if "next_package_ladder" not in metadata:
                blockers.append(_finding("manifest_next_package_missing", "Cortex manifest must expose metadata.next_package_ladder."))
            if "current_checkpoint_receipt" not in metadata:
                blockers.append(_finding("manifest_checkpoint_missing", "Cortex manifest must expose metadata.current_checkpoint_receipt."))
            result["source_warning_count"] = len(payload.get("warnings", [])) if isinstance(payload.get("warnings"), list) else 0
            result["source_blocker_count"] = len(payload.get("blockers", [])) if isinstance(payload.get("blockers"), list) else 0
    elif substrate_class in {"cortex_runtime_artifact", "validation_receipt"}:
        payload, error = _json_payload(raw, source_ref=source_ref)
        if error is not None or payload is None:
            blockers.append(error or _finding("source_malformed", "Source JSON is unavailable.", path=source_ref))
        else:
            result["source_type"] = str(payload.get("schema_version") or payload.get("contract_version") or "json")
            result["source_status"] = payload.get("status")
            result["source_safe_to_use"] = payload.get("safe_to_use")
            if substrate_class == "validation_receipt":
                blockers.extend(_validate_json_fields(payload, required=("summary",), code="validation_source_missing_fields"))
            else:
                blockers.extend(_validate_json_fields(payload, required=("schema_version",), code="runtime_source_missing_fields"))
    else:
        text = raw.decode("utf-8", errors="replace")
        result["source_type"] = "markdown" if source_ref.endswith(".md") else "python"
        if not text.strip():
            blockers.append(_finding("source_empty", "Source text is empty.", path=source_ref))
        if source_ref.endswith(".md") and not text.lstrip().startswith("#"):
            warnings.append(_finding("markdown_heading_missing", "Markdown advisory substrate does not start with a heading.", path=source_ref))

    result["schema_valid"] = not blockers
    return result, warnings, blockers


def build_consumption_report(*, root: Path | None = None, source: str | None = None) -> OrderedDict[str, Any]:
    base = (root or atlas_root()).resolve()
    branch, head = collect_git_state(base)
    warnings: list[OrderedDict[str, Any]] = []
    blockers: list[OrderedDict[str, Any]] = []
    source_ref, source_path, substrate_class, source_error = resolve_source_path(base, source)
    source_digest: str | None = None
    consumption_result: OrderedDict[str, Any] = OrderedDict(
        [
            ("source_exists", False),
            ("source_type", None),
            ("schema_valid", False),
            ("source_status", None),
            ("source_safe_to_use", None),
            ("source_warning_count", 0),
            ("source_blocker_count", 0),
        ]
    )

    if source_error is not None:
        if source_error["code"] == "source_required":
            warnings.append(source_error)
        else:
            blockers.append(source_error)
    elif source_path is not None and substrate_class is not None:
        raw, read_error = _load_source(source_path)
        if read_error is not None or raw is None:
            blockers.append(read_error or _finding("source_read_failed", "Source could not be read.", path=source_ref))
        else:
            source_digest = f"sha256:{hashlib.sha256(raw).hexdigest()}"
            consumption_result, shape_warnings, shape_blockers = validate_source_shape(source_ref=source_ref or "", substrate_class=substrate_class, raw=raw)
            warnings.extend(shape_warnings)
            blockers.extend(shape_blockers)

    validation_counts, validation_error = read_validation(base)
    if validation_error is not None:
        warnings.append(validation_error)
    if validation_counts["critical"] or validation_counts["error"]:
        blockers.append(
            _finding(
                "validation_not_safe",
                "Stack validation has critical or error findings; second advisory substrate consumption is not safe to use.",
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
            ("workflow_dispatch_authorized", False),
            ("stack_dispatch_authorized", False),
            ("repo_mutation_authorized", False),
            ("platform_mutation_authorized", False),
            ("owner_repo_mutation_authorized", False),
            ("protected_surface_mutation_authorized", False),
            ("marker_movement_authorized", False),
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
            ("source_ref", source_ref),
            ("source_digest", source_digest),
            ("substrate_class", substrate_class),
            ("consumption_result", consumption_result),
            ("preserved_authority_denials", list(AUTHORITY_DENIALS)),
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
            "Cortex Second Advisory Substrate Consumption",
            f"Status: {report['status']}",
            f"Branch: {report.get('branch') or 'unknown'}",
            f"Head: {report.get('head') or 'unknown'}",
            f"Source: {report.get('source_ref') or 'none'}",
            f"Substrate class: {report.get('substrate_class') or 'none'}",
            f"Safe to use: {str(report.get('safe_to_use')).lower()}",
            "Authority: advisory only; no execution, approval, owner-truth, deploy, secret, workflow dispatch, _stack dispatch, mutation, marker movement, or final-receipt authority.",
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
    parser = argparse.ArgumentParser(description="Consume a second Cortex advisory substrate as advisory-only context.")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON only.")
    parser.add_argument("--source", help="Root-relative admitted source ref to consume.")
    parser.add_argument("--output", help="Optional root-relative tmp/**.json output path.")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    root = atlas_root().resolve()
    try:
        report = build_consumption_report(root=root, source=args.source)
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
                ("source_ref", None),
                ("source_digest", None),
                ("substrate_class", None),
                ("consumption_result", OrderedDict()),
                ("preserved_authority_denials", list(AUTHORITY_DENIALS)),
                ("advisory_payload", OrderedDict([("advisory_only", True)])),
                ("forbidden_surfaces", list(FORBIDDEN_SURFACES)),
                ("warnings", []),
                ("blockers", [_finding("internal_error", "Second advisory substrate consumption failed before completion.", exception=str(exc))]),
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
